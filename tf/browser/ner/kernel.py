"""TF backend processing.

This module is for functions that extract data from the corpus
and put it in various dedicated data structures.
"""

import collections
import time

from ...core.generic import AttrDict
from ...core.files import mTime, fileExists, annotateDir

from .settings import (
    FEATURES,
    SUMMARY_INDICES,
    NF,
    featureDefault,
    getText,
)


def loadData(web):
    """Loads data of the given annotation set from disk into memory.

    The data of an annotation set consists of:

    *   a dict of entities, keyed by nodes or line numbers;
        each entity specifies a tuple of feature values and a list of slots
        that are part of the entity.

    If `annoSet` is empty, the annotation data is already in the TF data, and we do not
    do anything.

    After loading we process the data into derived datastructures.

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

        For each such set we produce the following keys:

        *   `dateLoaded`: datetime when the data was last loaded from disk
        *   `dateProcessed`: datetime when the data was last processed
        *   `entities`: the list of entities as loaded from a tsv file

        We then process this into several data structures, each identified
        by a different key.
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

    # load sentence nodes

    changed = fromSource(web)
    process(web, changed)


def fromSource(web):
    annoSet = web.annoSet
    setData = web.toolData.ner.sets[annoSet]
    kernelApi = web.kernelApi

    app = kernelApi.app
    api = app.api
    F = api.F
    Fs = api.Fs
    L = api.L

    slotType = F.otype.slotType

    annoDir = annotateDir(app, "ner")
    dataFile = f"{annoDir}/{annoSet}/entities.tsv"

    if "sentences" not in setData:
        setData.sentences = F.otype.s("sentence")

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
                feat: api.isLoaded(feat, pretty=False)[feat] is not None
                for feat in FEATURES
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

    return changed


def process(web, changed):
    annoSet = web.annoSet
    setData = web.toolData.ner.sets[annoSet]
    kernelApi = web.kernelApi

    app = kernelApi.app
    api = app.api
    F = api.F

    dateLoaded = setData.dateLoaded
    dateProcessed = setData.dateProcessed

    if (
        changed
        or "dateProcessed" not in setData
        or "entityText" not in setData
        or "entityTextVal" not in setData
        or "entitySummary" not in setData
        or "entityIdent" not in setData
        or "entityFreq" not in setData
        or "entityIndex" not in setData
        or "entitySlotVal" not in setData
        or "entitySlotIndex" not in setData
        or dateLoaded is not None
        and dateProcessed < dateLoaded
    ):
        web.console(f"PROCESS '{annoSet}' START")

        entityItems = setData.entities.items()

        entityText = {}
        entityTextVal = {feat: collections.defaultdict(set) for feat in FEATURES}
        entitySummary = {}
        entityIdent = {}
        entityIdentFirst = {}
        entityFreq = {feat: collections.Counter() for feat in FEATURES}
        entityIndex = {feat: {} for feat in FEATURES}
        entitySlotVal = {}
        entitySlotIndex = {}

        for (e, (fVals, slots)) in entityItems:
            txt = getText(F, slots)
            ident = fVals
            summary = tuple(fVals[i] for i in SUMMARY_INDICES)

            entityText[e] = txt

            for (feat, val) in zip(FEATURES, fVals):
                entityFreq[feat][val] += 1
                entityIndex[feat].setdefault(slots, set()).add(val)
                entityTextVal[feat][txt].add(val)

            entityIdent.setdefault(ident, []).append(e)
            if ident not in entityIdentFirst:
                entityIdentFirst[ident] = e

            entitySummary.setdefault(summary, []).append(e)
            entitySlotVal.setdefault(slots, set()).add(fVals)

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

        setData.entityText = entityText
        setData.entityTextVal = entityTextVal
        setData.entitySummary = entitySummary
        setData.entityIdent = entityIdent
        setData.entityIdentFirst = entityIdentFirst
        setData.entityFreq = {
            feat: sorted(entityFreq[feat].items()) for feat in FEATURES
        }
        setData.entityIndex = entityIndex
        setData.entitySlotVal = entitySlotVal
        setData.entitySlotIndex = entitySlotIndex

        setData.dateProcessed = time.time()
        web.console(f"PROCESS '{annoSet}' DONE")

    else:
        web.console(f"PROCESS '{annoSet}' REUSED")
