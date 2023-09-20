import collections

from .settings import FEATURES, NF
from .kernel import loadData


def valRep(fVals):
    return ", ".join(f"<i>{feat}</i>={val}" for (feat, val) in zip(FEATURES, fVals))


def saveEntity(web, modifyData, sentences, excludedTokens):
    setData = web.toolData.ner.sets[web.annoSet]
    deletions = modifyData.deletions
    additions = modifyData.additions

    oldEntities = setData.entities

    report = []

    # deletions

    delEntities = set()
    delEntitiesByE = set()

    if any(len(x) > 0 for x in deletions):
        oldEntitiesBySlots = collections.defaultdict(set)

        for (e, data) in oldEntities.items():
            oldEntitiesBySlots[data[1]].add(e)

        excl = 0

        stats = collections.Counter()

        for (s, sTokens, allMatches, positions) in sentences:
            for matches in allMatches:
                if matches[-1] in excludedTokens:
                    excl += 1
                    continue

                candidates = oldEntitiesBySlots.get(matches, set())

                for e in candidates:
                    toBeDeleted = False
                    fVals = oldEntities[e][0]

                    for (fVal, delVals) in zip(fVals, deletions):
                        if fVal in delVals:
                            toBeDeleted = True
                            break

                    if toBeDeleted:
                        if e not in delEntitiesByE:
                            delEntitiesByE.add(e)
                            delEntities.add((fVals, matches))
                            stats[fVals] += 1

        report.extend(
            [f"Deletion: {n} x {valRep(fVals)}" for (fVals, n) in sorted(stats.items())]
            if len(stats) else ["nothing to delete"]
        )
        if excl:
            report.append(f"Deletion: occurences excluded: {excl}")

    # additions

    addEntities = set()

    if all(len(x) > 0 for x in additions):
        oldEntitiesBySlots = collections.defaultdict(set)

        for (e, (fVals, slots)) in oldEntities.items():
            if e not in delEntitiesByE:
                oldEntitiesBySlots[slots].add(fVals)

        excl = 0

        fValTuples = [()]

        for vals in additions:
            newTuples = []
            for val in vals:
                newTuples.extend([ft + (val,) for ft in fValTuples])
            fValTuples = newTuples

        stats = collections.Counter()

        for (s, sTokens, allMatches, positions) in sentences:
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
            if len(stats) else ["nothing to add"]
        )
        if excl:
            report.append(f"Addition: occurences excluded: {excl}")

    if len(delEntities):
        weedEntities(web, delEntities)
    if len(addEntities):
        mergeEntities(web, addEntities)

    return report


def mergeEntities(web, newEntities):
    annoSet = web.annoSet
    annoDir = web.annoDir

    dataFile = f"{annoDir}/{annoSet}/entities.tsv"

    with open(dataFile, "a") as fh:
        for (fVals, matches) in newEntities:
            fh.write("\t".join(str(x) for x in (*fVals, *matches)) + "\n")

    loadData(web)


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

    loadData(web)


def saveEntitiesAs(web, dataFile):
    entities = web.toolData.ner.sets[""].entities

    with open(dataFile, "a") as fh:
        for (fVals, matches) in entities.values():
            fh.write("\t".join(str(x) for x in (*fVals, *matches)) + "\n")
