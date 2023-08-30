"""TF backend processing.

This module is for functions that extract data from the corpus
and put it in various dedicated data structures.
"""

import collections
import re
from datetime import datetime

from ...core.generic import AttrDict
from ...core.files import mTime, fileExists, annotateDir

WHITE_RE = re.compile(r"""\s{2,}""", re.S)


def loadData(web, annoSet):
    """Loads data of the given annotation set from disk into memory.

    The data of an annotation set consists of:

    *   a list of entities, each entity specifies a kind and a list of slots
        that are part of the entity.

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

    annoSet: string
        The name of the annotation set whose data should be loaded.
        If empty, we use entity data that is already present in the TF data source.
        We do not have to load that, but we do the processing, if the processed data
        is not yet available.
        We consider this static data.

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
        *   `entitiesByKind`: the dictionary of entities by kind, text as a result
            of processing;
        *   `entityKindFreq`: the frequency list of entity kinds as a result of processing
        *   `entityTextFreq`: the frequency list of entity texts as a result
            of processing
        *   `entitiesSlot`: the index of entities by slot
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

    if annoSet not in setsData:
        setsData[annoSet] = AttrDict()

    setData = setsData[annoSet]

    kernelApi = web.kernelApi
    app = kernelApi.app
    api = app.api
    F = api.F
    T = api.T
    L = api.L

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
            entities = []

            if fileExists(dataFile):
                with open(dataFile) as df:
                    for line in df:
                        entities.append(line.rstrip("\n").split("\t"))

            setData.entities = entities
            setData.dateLoaded = datetime.utcnow()
            web.console(f"LOAD '{annoSet}' DONE")
        else:
            web.console(f"LOAD '{annoSet}' REUSED")

    # processing stage (a bit different for annoset == "")

    if annoSet:
        if (
            changed
            or "dateProcessed" not in setData
            or "entitiesByKind" not in setData
            or "entityKindFreq" not in setData
            or "entityText" not in setData
            or "entityTextFreq" not in setData
            or "entitiesSlotIndex" not in setData
            or setData.dateProcessed < setData.dateLoaded
        ):
            web.console(f"PROCESS '{annoSet}' START")
            entitiesByKind = {}
            entityText = {}
            entityKindFreq = collections.Counter()
            entityTextFreq = collections.Counter()
            entitiesSlotIndex = {}

            for (e, eData) in enumerate(setData.entities):
                (kind, *slots) = eData
                txt = WHITE_RE.sub(" ", T.text(slots).strip())
                entityText[e] = txt
                entitiesByKind.setdefault((kind, txt), []).append(e)
                entityKindFreq[kind] += 1
                entityTextFreq[txt] += 1

            for (e, eData) in enumerate(setData.entities):
                (kind, *slots) = eData
                firstSlot = slots[0]
                lastSlot = slots[-1]
                txt = entityText[e]
                textFreq = entityTextFreq[txt]

                for slot in slots:
                    entitiesSlotIndex.setdefault(slot, []).append(
                        [slot == firstSlot, kind, textFreq]
                        if slot == firstSlot or slot == lastSlot
                        else None
                    )

            setData.entityText = entityText
            setData.entitiesByKind = entitiesByKind
            setData.entityKindFreq = sorted(entityKindFreq.items())
            setData.entityTextFreq = entityTextFreq
            setData.entitiesSlotIndex = entitiesSlotIndex
            setData.dateProcessed = datetime.utcnow()
            web.console(f"PROCESS '{annoSet}' DONE")
        else:
            web.console(f"PROCESS '{annoSet}' REUSED")
    else:
        if (
            "dateProcessed" not in setData
            or "entitiesByKind" not in setData
            or "entityKindFreq" not in setData
            or "entityText" not in setData
            or "entityTextFreq" not in setData
            or "entitiesSlotIndex" not in setData
        ):
            web.console(f"PROCESS '{annoSet}' START")
            entitiesByKind = {}
            entityText = {}
            entityTextFreq = collections.Counter()
            entitiesSlotIndex = {}

            for e in F.otype.s("ent"):
                kind = F.kind.v(e)
                txt = WHITE_RE.sub(" ", T.text(e).strip())
                entityText[e] = txt
                entitiesByKind.setdefault((kind, txt), []).append(e)
                entityTextFreq[txt] += 1

            for e in F.otype.s("ent"):
                slots = L.d(e, otype="t")
                firstSlot = slots[0]
                lastSlot = slots[-1]
                txt = entityText[e]
                textFreq = entityTextFreq[txt]

                for slot in slots:
                    entitiesSlotIndex.setdefault(slot, []).append(
                        [slot == firstSlot, kind, textFreq]
                        if slot == firstSlot or slot == lastSlot
                        else None
                    )

            entityKindFreq = sorted(F.kind.freqList(nodeTypes={"ent"}))

            setData.entityText = entityText
            setData.entitiesByKind = entitiesByKind
            setData.entityKindFreq = entityKindFreq
            setData.entityTextFreq = entityTextFreq
            setData.dateProcessed = datetime.utcnow()
            setData.entitiesSlotIndex = entitiesSlotIndex
            web.console(f"PROCESS '{annoSet}' DONE")
        else:
            web.console(f"PROCESS '{annoSet}' REUSED")
