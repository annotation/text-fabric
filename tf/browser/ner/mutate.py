import collections

from ...core.files import (
    annotateDir,
    initTree,
    fileExists,
    dirExists,
    dirMake,
    dirCopy,
    dirMove,
    dirRemove,
)

from .settings import TOOLKEY, FEATURES, NF, ERROR
from .kernel import loadData
from .servelib import annoSets
from .wrap import wrapMessages, wrapAnnoSets


def valRep(fVals):
    return ", ".join(f"<i>{feat}</i>={val}" for (feat, val) in zip(FEATURES, fVals))


def setSetup(web, templateData):
    chosenAnnoSet = templateData.annoset
    web.annoSet = chosenAnnoSet
    loadData(web)


def setHandling(web, templateData):
    kernelApi = web.kernelApi
    app = kernelApi.app
    annoDir = annotateDir(app, TOOLKEY)
    web.annoDir = annoDir

    initTree(annoDir, fresh=False)
    sets = annoSets(annoDir)

    chosenAnnoSet = templateData.annoset
    dupAnnoSet = templateData.duannoset
    renamedAnnoSet = templateData.rannoset
    deleteAnnoSet = templateData.dannoset

    messages = []

    if deleteAnnoSet:
        annoPath = f"{annoDir}/{deleteAnnoSet}"
        dirRemove(annoPath)
        if dirExists(annoPath):
            messages.append((ERROR, f"""Could not remove {deleteAnnoSet}"""))
        else:
            chosenAnnoSet = ""
            sets -= {deleteAnnoSet}
        templateData.dannoset = ""

    if dupAnnoSet:
        if dupAnnoSet in sets:
            messages.append((ERROR, f"""Set {dupAnnoSet} already exists"""))
        else:
            if chosenAnnoSet:
                if not dirCopy(
                    f"{annoDir}/{chosenAnnoSet}",
                    f"{annoDir}/{dupAnnoSet}",
                    noclobber=True,
                ):
                    messages.append(
                        (ERROR, f"""Could not copy {chosenAnnoSet} to {dupAnnoSet}""")
                    )
                else:
                    sets = sets | {dupAnnoSet}
                    chosenAnnoSet = dupAnnoSet
            else:
                annoPath = f"{annoDir}/{dupAnnoSet}"
                dataFile = f"{annoPath}/entities.tsv"

                if fileExists(dataFile):
                    messages.append((ERROR, f"""Set {dupAnnoSet} already exists"""))
                else:
                    dirMake(annoPath)
                    saveEntitiesAs(web, dataFile)
                    chosenAnnoSet = dupAnnoSet
            templateData.duannoset = ""

    if renamedAnnoSet and chosenAnnoSet:
        if renamedAnnoSet in sets:
            messages.append((ERROR, f"""Set {renamedAnnoSet} already exists"""))
        else:
            if not dirMove(f"{annoDir}/{chosenAnnoSet}", f"{annoDir}/{renamedAnnoSet}"):
                messages.append(
                    (
                        ERROR,
                        f"""Could not rename {chosenAnnoSet} to {renamedAnnoSet}""",
                    )
                )
            else:
                sets = (sets | {renamedAnnoSet}) - {chosenAnnoSet}
                chosenAnnoSet = renamedAnnoSet
        templateData.rannoset = ""

    if chosenAnnoSet and chosenAnnoSet not in sets:
        initTree(f"{annoDir}/{chosenAnnoSet}", fresh=False)
        sets |= {chosenAnnoSet}

    templateData.annosets = wrapAnnoSets(annoDir, chosenAnnoSet, sets)
    templateData.messages = wrapMessages(messages)

    web.annoSet = chosenAnnoSet
    loadData(web)


def delEntity(web, deletions, buckets, excludedTokens):
    setData = web.toolData[TOOLKEY].sets[web.annoSet]

    oldEntities = setData.entities

    report = []

    delEntities = set()
    delEntitiesByE = set()

    if any(len(x) > 0 for x in deletions):
        oldEntitiesBySlots = collections.defaultdict(set)

        for (e, data) in oldEntities.items():
            oldEntitiesBySlots[data[1]].add(e)

        excl = 0

        stats = collections.Counter()

        fValTuples = [()]

        for vals in deletions:
            delTuples = []
            for val in vals:
                delTuples.extend([ft + (val,) for ft in fValTuples])
            fValTuples = delTuples

        for (b, bTokens, allMatches, positions) in buckets:
            for matches in allMatches:
                if matches[-1] in excludedTokens:
                    excl += 1
                    continue

                candidates = oldEntitiesBySlots.get(matches, set())

                for e in candidates:
                    toBeDeleted = False
                    fVals = oldEntities[e][0]

                    if fVals in fValTuples:
                        toBeDeleted = True

                    if toBeDeleted:
                        if e not in delEntitiesByE:
                            delEntitiesByE.add(e)
                            delEntities.add((fVals, matches))
                            stats[fVals] += 1

        report.extend(
            [f"Deletion: {n} x {valRep(fVals)}" for (fVals, n) in sorted(stats.items())]
            if len(stats) else ["Nothing deleted"]
        )
        if excl:
            report.append(f"Deletion: occurences excluded: {excl}")

    if len(delEntities):
        weedEntities(web, delEntities)

    loadData(web)
    return report


def addEntity(web, additions, buckets, excludedTokens):
    setData = web.toolData[TOOLKEY].sets[web.annoSet]

    oldEntities = setData.entities

    report = []

    # additions

    addEntities = set()

    if all(len(x) > 0 for x in additions):
        oldEntitiesBySlots = collections.defaultdict(set)

        for (e, (fVals, slots)) in oldEntities.items():
            oldEntitiesBySlots[slots].add(fVals)

        excl = 0

        fValTuples = [()]

        for vals in additions:
            newTuples = []
            for val in vals:
                newTuples.extend([ft + (val,) for ft in fValTuples])
            fValTuples = newTuples

        stats = collections.Counter()

        for (b, bTokens, allMatches, positions) in buckets:
            for matches in allMatches:
                if matches[-1] in excludedTokens:
                    excl += 1
                    continue

                existing = oldEntitiesBySlots.get(matches, set())

                for fVals in fValTuples:
                    if fVals in existing:
                        continue
                    data = (fVals, matches)
                    if data not in addEntities:
                        addEntities.add(data)
                        stats[fVals] += 1

        report.extend(
            [f"Addition: {n} x {valRep(fVals)}" for (fVals, n) in sorted(stats.items())]
            if len(stats) else ["Nothing added"]
        )
        if excl:
            report.append(f"Addition: occurences excluded: {excl}")

    if len(addEntities):
        mergeEntities(web, addEntities)

    loadData(web)
    return report


def weedEntities(web, delEntities):
    annoSet = web.annoSet
    annoDir = web.annoDir

    dataFile = f"{annoDir}/{annoSet}/entities.tsv"

    newEntities = []

    with open(dataFile) as fh:
        for line in fh:
            fields = tuple(line.rstrip("\n").split("\t"))
            fVals = tuple(fields[0:NF])
            matches = tuple(int(f) for f in fields[NF:])
            data = (fVals, matches)
            if data in delEntities:
                continue
            newEntities.append(line)

    with open(dataFile, "w") as fh:
        fh.write("".join(newEntities))


def mergeEntities(web, newEntities):
    annoSet = web.annoSet
    annoDir = web.annoDir

    dataFile = f"{annoDir}/{annoSet}/entities.tsv"

    with open(dataFile, "a") as fh:
        for (fVals, matches) in newEntities:
            fh.write("\t".join(str(x) for x in (*fVals, *matches)) + "\n")


def saveEntitiesAs(web, dataFile):
    entities = web.toolData[TOOLKEY].sets[""].entities

    with open(dataFile, "a") as fh:
        for (fVals, matches) in entities.values():
            fh.write("\t".join(str(x) for x in (*fVals, *matches)) + "\n")
