"""TF backend processing.

This module is for functions that extract data from the corpus
and put it in various dedicated data structures.
"""

import collections
import re
import time

from ...core.generic import AttrDict
from ...core.files import mTime, fileExists, annotateDir

WHITE_RE = re.compile(r"""\s{2,}""", re.S)


def mergeEntities(web, newEntities):
    kernelApi = web.kernelApi
    app = kernelApi.app
    annoSet = web.annoSet
    annoDir = annotateDir(app, "ner")

    dataFile = f"{annoDir}/{annoSet}/entities.tsv"

    for entity in newEntities:
        with open(dataFile, "a") as fh:
            fh.write("\t".join(str(x) for x in entity) + "\n")

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
            kind = fields[0]
            matches = tuple(int(f) for f in fields[1:])
            data = (kind, *matches)
            if data in delEntities:
                continue
            newEntities.append(line)

    with open(dataFile, "w") as fh:
        fh.write("".join(newEntities))

    loadData(web)


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

        *   `entitiesByKind`: the dictionary of entities by kind
        *   `entityKindFreq`: the frequency list of entity kinds
        *   `entityTextFreq`: the frequency list of entity texts
        *   `entityTextKind`: the set of kinds that the entities with a given text may
            have
        *   `entitiesSlotIndex`: the index of entities by slot
        *   `entityIndex`: the index of entities by tuple of slot positions; the values
            are the set of kinds of the entities at that position.
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
    T = api.T
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
                        entities[e] = (fields[0], *(int(f) for f in fields[1:]))

            setData.entities = entities
            setData.dateLoaded = time.time()
            web.console(f"LOAD '{annoSet}' DONE")
        else:
            web.console(f"LOAD '{annoSet}' REUSED")
    else:
        if "entities" not in setData:
            setData.entities = {
                e: (F.kind.v(e),) + L.d(e, otype=slotType) for e in F.otype.s("ent")
            }

    # processing stage (a bit different for annoset == "")

    entitiesByKind = {}
    entityText = {}
    entityTextFreq = collections.Counter()
    entityTextKind = collections.defaultdict(set)
    entitiesSlotIndex = {}
    entityIndex = {}

    dateLoaded = setData.dateLoaded
    dateProcessed = setData.dateProcessed

    def addToIndex(e, kind, slots):
        firstSlot = slots[0]
        lastSlot = slots[-1]
        txt = entityText[e]
        textFreq = entityTextFreq[txt]

        for slot in slots:
            isFirst = slot == firstSlot
            isLast = slot == lastSlot
            if isFirst or isLast:
                if isFirst:
                    entitiesSlotIndex.setdefault(slot, []).append(
                        [True, kind, textFreq]
                    )
                if isLast:
                    entitiesSlotIndex.setdefault(slot, []).append(
                        [False, kind, textFreq]
                    )
            else:
                entitiesSlotIndex.setdefault(slot, []).append(None)

    if (
        changed
        or "dateProcessed" not in setData
        or "entitiesByKind" not in setData
        or "entityKindFreq" not in setData
        or "entityText" not in setData
        or "entityTextFreq" not in setData
        or "entityTextKind" not in setData
        or "entitiesSlotIndex" not in setData
        or "entityIndex" not in setData
        or dateLoaded is not None and dateProcessed < dateLoaded
    ):
        web.console(f"PROCESS '{annoSet}' START")

        if annoSet:
            entityKindFreq = collections.Counter()

            for (e, eData) in setData.entities.items():
                (kind, *slots) = eData
                txt = WHITE_RE.sub(" ", T.text(slots).strip())

                entityText[e] = txt
                entityKindFreq[kind] += 1
                entityTextFreq[txt] += 1
                entityTextKind[txt].add(kind)

                entitiesByKind.setdefault((kind, txt), []).append(e)

            for (e, eData) in setData.entities.items():
                (kind, *slots) = eData
                slots = tuple(slots)
                entityIndex.setdefault(slots, set()).add(kind)
                addToIndex(e, kind, slots)

            setData.entityKindFreq = sorted(entityKindFreq.items())
        else:
            for e in F.otype.s("ent"):
                kind = F.kind.v(e)
                txt = WHITE_RE.sub(" ", T.text(e).strip())

                entityText[e] = txt
                entityTextFreq[txt] += 1
                entityTextKind[txt].add(kind)

                entitiesByKind.setdefault((kind, txt), []).append(e)

            for e in F.otype.s("ent"):
                kind = F.kind.v(e)
                slots = tuple(L.d(e, otype=slotType))
                entityIndex.setdefault(slots, set()).add(kind)
                addToIndex(e, kind, slots)

            setData.entityKindFreq = sorted(F.kind.freqList(nodeTypes={"ent"}))

        setData.entityText = entityText
        setData.entitiesByKind = entitiesByKind
        setData.entityTextFreq = entityTextFreq
        setData.entityTextKind = entityTextKind
        setData.entitiesSlotIndex = entitiesSlotIndex
        setData.entityIndex = entityIndex
        setData.dateProcessed = time.time()

        web.console(f"PROCESS '{annoSet}' DONE")

    else:
        web.console(f"PROCESS '{annoSet}' REUSED")
