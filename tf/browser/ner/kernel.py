"""TF backend processing.

This module is for functions that extract data from the corpus
and put it in various dedicated data structures.
"""

import collections
import re
import time

from ...core.generic import AttrDict
from ...core.files import mTime, fileExists, annotateDir

GENERIC = "any"
FEATURES = ("txt", "eid", "kind")
KEYWORD_FEATURES = set(FEATURES[2])

NF = len(FEATURES)


WHITE_RE = re.compile(r"""\s{2,}""", re.S)


def mergeEntities(web, newEntities):
    kernelApi = web.kernelApi
    app = kernelApi.app
    annoSet = web.annoSet
    annoDir = annotateDir(app, "ner")

    dataFile = f"{annoDir}/{annoSet}/entities.tsv"

    for (fVals, matches) in newEntities:
        with open(dataFile, "a") as fh:
            fh.write("\t".join(str(x) for x in (*fVals, *matches)) + "\n")

    loadData(web)


def weedEntities(web, delEntities):
    kernelApi = web.kernelApi
    app = kernelApi.app
    annoSet = web.annoSet
    annoDir = annotateDir(app, "ner")

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


def ucFirst(x):
    return x[0].upper() + x[1:].lower()


def getText(F, slots):
    return WHITE_RE.sub(
        " ",
        "".join(f"{F.str.v(s)}{F.after.v(s)}" for s in slots).strip(),
    )


def getEid(F, slots):
    return WHITE_RE.sub(
        "",
        "".join(ucFirst(x) for s in slots if (x := F.str.v(s).strip())).strip(),
    )


def getKind(F, slots):
    return GENERIC


featureDefault = {
    "": getText,
    FEATURES[0]: getKind,
    FEATURES[1]: getEid,
}


def loadData(web):
    """Loads data of the given annotation set from disk into memory.

    The data of an annotation set consists of:

    *   a dict of entities, keyed by nodes or line numbers;
        each entity specifies a kind and a list of slots that are part of the entity.

    If `annoSet` is empty, the annotation data is already in the TF data, and we do not
    do anything.

    After loading we process the data into a sligthly other shape:

    *   a dictionary keyed by pairs of kind and text and valued by the sequence numbers
        of the entities that have that kind and text
    *   a frequency list of the entity kinds
    *   a frequency list of the entity texts
    *   a dictionary, keyed by slot number, and valued by the following information:
        *   If the slot is outside any entity, it is not in the dictionary
        *   Otherwise, the value is a list of items, each item holds information
            about a specific entity wrt to that slot:
        *   If an entity starts or ends there, the item is a tuple
            (status, kind, number of occurrences)
        *   If the slot is inside an entity, the item is True

    We try to be lazy. We only load data from disk if the data is not already in memory,
    or the data on disk has been updated since the last load.

    Likewise, we only process the data if the data has been loaded again.

    Parameters
    ----------
    web: object
        The web application object, which has a handle to the TF app object.

    Returns
    -------
    void
        The resulting data is stored on the `web` object, under the key `toolData`
        and then under the key `ner` and then `sets` and then the name of the
        annotation set.

        For each set we produce the keys:

        *   `dateLoaded`: datetime when the data was last loaded from disk
        *   `dateProcessed`: datetime when the data was last processed
        *   `entities`: the list of entities as loaded from a tsv file

        We then process this into the following data structures:

        *   `entityKindFreq`: the frequency list of entity kinds
        *   `entityTextFreq`: the frequency list of entity texts
        *   `entityTextKind`: the set of kinds that the entities with a given text may
            have
        *   `entitySlotIndex`: the index of entities by slot
        *   `entityIndexKind`: the index of entities by tuple of slot positions; the values
            are the set of kinds of the entities at that position.

        *   `entityById`
        *   `entityId`
        *   `entityIdFreq`
        *   `entityIndexId`
    """
    if not hasattr(web, "toolData"):
        setattr(web, "toolData", AttrDict())

    toolData = web.toolData

    if "ner" not in toolData:
        toolData.ner = AttrDict()

    nerData = toolData.ner

    if "sets" not in nerData:
        nerData.sets = AttrDict()

    setsData = nerData.sets

    annoSet = web.annoSet

    if annoSet not in setsData:
        setsData[annoSet] = AttrDict()

    setData = setsData[annoSet]

    kernelApi = web.kernelApi
    app = kernelApi.app
    api = app.api
    F = api.F
    Fs = api.Fs
    L = api.L
    slotType = F.otype.slotType

    annoDir = annotateDir(app, "ner")
    dataFile = f"{annoDir}/{annoSet}/entities.tsv"

    # load sentence nodes

    if "sentences" not in setData:
        setData.sentences = F.otype.s("sentence")

    # loading stage (only for real annosets)

    changed = False

    if annoSet:
        if (
            "entities" not in setData
            or "dateLoaded" not in setData
            or (len(setData.entities) > 0 and not fileExists(dataFile))
            or (fileExists(dataFile) and setData.dateLoaded < mTime(dataFile))
        ):
            web.console(f"LOAD '{annoSet}' START")
            changed = True
            entities = {}

            if fileExists(dataFile):
                with open(dataFile) as df:
                    for (e, line) in enumerate(df):
                        fields = tuple(line.rstrip("\n").split("\t"))
                        entities[e] = (
                            tuple(fields[0:NF]),
                            tuple(int(f) for f in fields[NF:]),
                        )

            setData.entities = entities
            setData.dateLoaded = time.time()
            web.console(f"LOAD '{annoSet}' DONE")
        else:
            web.console(f"LOAD '{annoSet}' REUSED")
    else:
        if "entities" not in setData:
            entities = {}
            hasFeature = {
                feat: api.isLoaded("entid")["entid"] is not None for feat in FEATURES
            }

            for e in F.otype.s("ent"):
                slots = L.d(e, otype=slotType)
                entities[e] = (
                    tuple(
                        Fs(feat).v(e)
                        if hasFeature[feat]
                        else featureDefault[feat](F, slots)
                        for feat in FEATURES
                    ),
                    tuple(slots),
                )

            setData.entities = entities

    # processing stage (a bit different for annoset == "")

    dateLoaded = setData.dateLoaded
    dateProcessed = setData.dateProcessed

    if (
        changed
        or "dateProcessed" not in setData
        or "entityVal" not in setData
        or "entityTextVal" not in setData
        or "entityBy" not in setData
        or "entityFreq" not in setData
        or "entityIndex" not in setData
        or "entitySlotIndex" not in setData
        or dateLoaded is not None
        and dateProcessed < dateLoaded
    ):
        web.console(f"PROCESS '{annoSet}' START")

        entityItems = setData.entities.items()

        entityVal = {feat: {} for feat in FEATURES}
        entityTextVal = {feat: collections.defaultdict(set) for feat in FEATURES[1:]}
        entityBy = {}
        entityFreq = {feat: collections.Counter() for feat in FEATURES}
        entityIndex = {feat: {} for feat in FEATURES}
        entitySlotIndex = {}

        for (e, (fVals, slots)) in entityItems:
            txt = fVals[0]
            ident = fVals[1:]

            for (feat, val) in zip(FEATURES, fVals):
                entityVal[feat][e] = val
                entityFreq[feat][val] += 1
                entityIndex[feat].setdefault(slots, set()).add(val)
                entityTextVal[feat][txt].add(val)

            entityBy.setdefault(ident, []).append(e)

            firstSlot = slots[0]
            lastSlot = slots[-1]

            for slot in slots:
                isFirst = slot == firstSlot
                isLast = slot == lastSlot
                if isFirst or isLast:
                    if isFirst:
                        entitySlotIndex.setdefault(slot, []).append(
                            [True, firstSlot - lastSlot - 1, ident]
                        )
                    if isLast:
                        entitySlotIndex.setdefault(slot, []).append(
                            [False, lastSlot - firstSlot + 1, ident]
                        )
                else:
                    entitySlotIndex.setdefault(slot, []).append(None)

        setData.entityVal = entityVal
        setData.entityTextVal = entityTextVal
        setData.entityBy = entityBy
        setData.entityFreq = sorted(entityFreq.items())
        setData.entityIndex = entityIndex
        setData.entitySlotIndex = entitySlotIndex

        setData.dateProcessed = time.time()

        web.console(f"PROCESS '{annoSet}' DONE")

    else:
        web.console(f"PROCESS '{annoSet}' REUSED")
