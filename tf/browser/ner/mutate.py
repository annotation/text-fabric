from .settings import FEATURES, NF
from .kernel import loadData


def saveEntity(web, fVals, sentences, excludedTokens):
    setData = web.toolData.ner.sets[web.annoSet]

    oldEntities = setData.entities
    oldEntitySet = oldEntities.values()
    newEntities = []
    excl = 0

    for (s, sTokens, allMatches, positions) in sentences:
        for matches in allMatches:
            data = (fVals, matches)
            if data not in oldEntitySet:
                if matches[-1] in excludedTokens:
                    excl += 1
                    continue
                newEntities.append(data)

    if len(newEntities):
        mergeEntities(web, newEntities)

    nEntities = len(newEntities)
    pl = "y" if nEntities == 1 else "ies"
    valRep = ", ".join(f"{feat}={val}" for (feat, val) in zip(FEATURES, fVals))

    return f"Added {nEntities} entit{pl} with {valRep}; " f"{excl} excluded"


def delEntity(web, fVals, sentences, excludedTokens):
    setData = web.toolData.ner.sets[web.annoSet]

    oldEntities = setData.entities
    oldEntitySet = [x for x in oldEntities.values() if x[0] == fVals]
    delEntities = set()
    excl = 0

    for (s, sTokens, allMatches, positions) in sentences:
        for matches in allMatches:
            data = (fVals, matches)
            if data in oldEntitySet:
                if matches[-1] in excludedTokens:
                    excl += 1
                    continue
                delEntities.add(data)

    if len(delEntities):
        weedEntities(web, delEntities)

    nEntities = len(delEntities)
    pl = "y" if nEntities == 1 else "ies"
    valRep = ", ".join(f"{feat}={val}" for (feat, val) in zip(FEATURES, fVals))

    return f"Deleted {nEntities} entit{pl} with {valRep}; {excl} excluded'"


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
