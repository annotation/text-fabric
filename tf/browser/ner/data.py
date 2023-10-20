import collections
import time

from ...core.generic import AttrDict
from ...core.files import (
    mTime,
    fileExists,
    initTree,
)
from .settings import Settings, getText


class Data(Settings):
    def __init__(self, data=None):
        super().__init__()

        if data is None:
            data = AttrDict()
            data.sets = AttrDict()

        self.data = data

        annoDir = self.annoDir
        initTree(annoDir, fresh=False)

    def loadData(self):
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

        The resulting data is stored on the object
        and then under the key `sets` and then the name of the annotation set.

        For each such set we produce the following keys:

        *   `dateLoaded`: datetime when the data was last loaded from disk
        *   `dateProcessed`: datetime when the data was last processed
        *   `entities`: the list of entities as loaded from a tsv file

        We then process this into several data structures, each identified
        by a different key.
        """
        data = self.data
        annoSet = self.annoSet

        if "sets" not in data:
            data.sets = AttrDict()

        sets = data.sets

        if annoSet not in sets:
            sets[annoSet] = AttrDict()

        # load bucket nodes

        changed = self.fromSource()
        self.process(changed)

    def fromSource(self):
        settings = self.settings
        bucketType = settings.bucketType
        app = self.app
        data = self.data
        annoSet = self.annoSet
        # annoSetRep = self.annoSetRep
        setData = data.sets[annoSet]
        annoDir = self.annoDir

        settings = self.settings
        entityType = settings.entityType
        features = settings.features
        nF = len(features)

        api = app.api
        F = api.F
        Fs = api.Fs
        L = api.L

        slotType = F.otype.slotType

        dataFile = f"{annoDir}/{annoSet}/entities.tsv"

        if "buckets" not in setData:
            setData.buckets = F.otype.s(bucketType)

        changed = False

        if annoSet:
            if (
                "entities" not in setData
                or "dateLoaded" not in setData
                or (len(setData.entities) > 0 and not fileExists(dataFile))
                or (fileExists(dataFile) and setData.dateLoaded < mTime(dataFile))
            ):
                # self.console(f"Loading data for {annoSet} ... ", newline=False)
                changed = True
                entities = {}

                if fileExists(dataFile):
                    with open(dataFile) as df:
                        for e, line in enumerate(df):
                            fields = tuple(line.rstrip("\n").split("\t"))
                            entities[e] = (
                                tuple(fields[0:nF]),
                                tuple(int(f) for f in fields[nF:]),
                            )

                setData.entities = entities
                setData.dateLoaded = time.time()
                # self.console("done.")
            else:
                # self.console(f"Data for {annoSetRep} already loaded")
                pass
        else:
            if "entities" not in setData:
                entities = {}
                hasFeature = {
                    feat: api.isLoaded(feat, pretty=False)[feat] is not None
                    for feat in features
                }

                for e in F.otype.s(entityType):
                    slots = L.d(e, otype=slotType)
                    entities[e] = (
                        tuple(
                            Fs(feat).v(e)
                            if hasFeature[feat]
                            else self.featureDefault[feat](F, slots)
                            for feat in features
                        ),
                        tuple(slots),
                    )

                setData.entities = entities

        return changed

    def process(self, changed):
        settings = self.settings
        features = settings.features
        summaryIndices = settings.summaryIndices

        app = self.app
        data = self.data
        annoSet = self.annoSet
        # annoSetRep = self.annoSetRep
        setData = data.sets[annoSet]

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
            or "entityVal" not in setData
            or "entitySlotVal" not in setData
            or "entitySlotAll" not in setData
            or "entitySlotIndex" not in setData
            or dateLoaded is not None
            and dateProcessed < dateLoaded
        ):
            # self.console(f"Processing data of {annoSetRep} ... ", newline=False)

            entityItems = setData.entities.items()

            entityText = {}
            entityTextVal = {feat: collections.defaultdict(set) for feat in features}
            entitySummary = {}
            entityIdent = {}
            entityIdentFirst = {}
            entityFreq = {feat: collections.Counter() for feat in features}
            entityIndex = {feat: {} for feat in features}
            entityVal = {}
            entitySlotVal = {}
            entitySlotAll = {}
            entitySlotIndex = {}

            for e, (fVals, slots) in entityItems:
                txt = getText(F, slots)
                ident = fVals
                summary = tuple(fVals[i] for i in summaryIndices)

                entityText[e] = txt
                entityVal.setdefault(fVals, set()).add(slots)

                for feat, val in zip(features, fVals):
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

                entitySlotAll.setdefault(firstSlot, set()).add(lastSlot)

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
                feat: sorted(entityFreq[feat].items()) for feat in features
            }
            setData.entityIndex = entityIndex
            setData.entityVal = entityVal
            setData.entitySlotVal = entitySlotVal
            setData.entitySlotAll = entitySlotAll
            setData.entitySlotIndex = entitySlotIndex

            setData.dateProcessed = time.time()
            # self.console("done.")

        else:
            # self.console(f"Data of {annoSetRep} already processed.")
            pass

    def delEntity(self, vals, allMatches=None, silent=True):
        setData = self.getSetData()

        oldEntities = setData.entities

        delEntities = set()

        oldEntitiesBySlots = set()

        for e, (fVals, slots) in oldEntities.items():
            if fVals == vals:
                oldEntitiesBySlots.add(slots)

        missing = 0
        deleted = 0

        delSlots = oldEntitiesBySlots if allMatches is None else allMatches

        for slots in delSlots:
            if slots not in oldEntitiesBySlots:
                missing += 1
                continue

            delEntities.add((vals, slots))
            deleted += 1

        if len(delEntities):
            self.weedEntities(delEntities)

        self.loadData()
        if not silent:
            self.console(f"Not present: {missing:>5} x")
            self.console(f"Deleted:     {deleted:>5} x")

    def delEntityRich(self, deletions, buckets, excludedTokens=set()):
        settings = self.settings
        features = settings.features
        browse = self.browse
        setData = self.getSetData()

        oldEntities = setData.entities

        report = []

        delEntities = set()
        delEntitiesByE = set()

        deletions = tuple([x] if type(x) is str else x for x in deletions)

        if any(len(x) > 0 for x in deletions):
            oldEntitiesBySlots = collections.defaultdict(set)

            for e, info in oldEntities.items():
                oldEntitiesBySlots[info[1]].add(e)

            excl = 0

            fValTuples = [()]

            for vals in deletions:
                delTuples = []
                for val in vals:
                    delTuples.extend([ft + (val,) for ft in fValTuples])
                fValTuples = delTuples

            stats = collections.Counter()

            for b, bTokens, allMatches, positions in buckets:
                for slots in allMatches:
                    if slots[-1] in excludedTokens:
                        excl += 1
                        continue

                    candidates = oldEntitiesBySlots.get(slots, set())

                    for e in candidates:
                        toBeDeleted = False
                        fVals = oldEntities[e][0]

                        if fVals in fValTuples:
                            toBeDeleted = True

                        if toBeDeleted:
                            if e not in delEntitiesByE:
                                delEntitiesByE.add(e)
                                delEntities.add((fVals, slots))
                                stats[fVals] += 1

            report.append(
                tuple(sorted(stats.items())) if len(stats) else ["Nothing deleted"]
            )
            if excl:
                report.append(f"Deletion: occurences excluded: {excl}")

        if len(delEntities):
            self.weedEntities(delEntities)

        if browse:
            return report

        self.loadData()
        (stats, *rest) = report
        if type(stats) is list:
            self.console("\n".join(stats))
        else:
            for vals, freq in stats:
                repVals = " ".join(
                    f"{feat}={val}" for (feat, val) in zip(features, vals)
                )
                self.console(f"Deleted {freq:>5} x {repVals}")
        if len(rest):
            self.console("\n".join(rest))

    def addEntity(self, vals, allMatches, silent=True):
        setData = self.getSetData()

        oldEntities = setData.entities

        addEntities = set()

        oldEntitiesBySlots = set()

        for e, (fVals, slots) in oldEntities.items():
            if fVals == vals:
                oldEntitiesBySlots.add(slots)

        present = 0
        added = 0

        for slots in allMatches:
            if slots in oldEntitiesBySlots:
                present += 1
                continue

            info = (vals, slots)
            if info not in addEntities:
                addEntities.add(info)
                added += 1

        if len(addEntities):
            self.mergeEntities(addEntities)

        self.loadData()
        if not silent:
            self.console(f"Already present: {present:>5} x")
            self.console(f"Added:           {added:>5} x")
        return (present, added)

    def addEntities(self, newEntities, silent=True):
        setData = self.getSetData()

        oldEntities = set(setData.entities.values())

        addEntities = set()

        present = 0
        added = 0

        for fVals, allMatches in newEntities:
            for slots in allMatches:
                if (fVals, slots) in oldEntities:
                    present += 1
                elif (fVals, slots) in addEntities:
                    continue
                else:
                    added += 1
                    addEntities.add((fVals, slots))

        if len(addEntities):
            self.mergeEntities(addEntities)

        self.loadData()
        if not silent:
            self.console(f"Already present: {present:>5} x")
            self.console(f"Added:           {added:>5} x")
        return (present, added)

    def addEntityRich(self, additions, buckets, excludedTokens=set()):
        settings = self.settings
        features = settings.features

        browse = self.browse
        setData = self.getSetData()

        oldEntities = setData.entities

        report = []

        addEntities = set()

        additions = tuple([x] if type(x) is str else x for x in additions)

        if all(len(x) > 0 for x in additions):
            oldEntitiesBySlots = collections.defaultdict(set)

            for e, (fVals, slots) in oldEntities.items():
                oldEntitiesBySlots[slots].add(fVals)

            excl = 0

            fValTuples = [()]

            for vals in additions:
                newTuples = []
                for val in vals:
                    newTuples.extend([ft + (val,) for ft in fValTuples])
                fValTuples = newTuples

            stats = collections.Counter()

            for b, bTokens, allMatches, positions in buckets:
                for slots in allMatches:
                    if slots[-1] in excludedTokens:
                        excl += 1
                        continue

                    existing = oldEntitiesBySlots.get(slots, set())

                    for fVals in fValTuples:
                        if fVals in existing:
                            continue
                        info = (fVals, slots)
                        if info not in addEntities:
                            addEntities.add(info)
                            stats[fVals] += 1

            report.append(
                tuple(sorted(stats.items())) if len(stats) else ["Nothing added"]
            )
            if excl:
                report.append(f"Addition: occurences excluded: {excl}")

        if len(addEntities):
            self.mergeEntities(addEntities)

        if browse:
            return report

        self.loadData()
        (stats, *rest) = report
        if type(stats) is list:
            self.console("\n".join(stats))
        else:
            for vals, freq in stats:
                repVals = " ".join(
                    f"{feat}={val}" for (feat, val) in zip(features, vals)
                )
                self.console(f"Added {freq:>5} x {repVals}")
        if len(rest):
            self.console("\n".join(rest))

    def weedEntities(self, delEntities):
        settings = self.settings
        features = settings.features
        nF = len(features)

        annoSet = self.annoSet
        annoDir = self.annoDir

        dataFile = f"{annoDir}/{annoSet}/entities.tsv"

        newEntities = []

        with open(dataFile) as fh:
            for line in fh:
                fields = tuple(line.rstrip("\n").split("\t"))
                fVals = tuple(fields[0:nF])
                slots = tuple(int(f) for f in fields[nF:])
                info = (fVals, slots)
                if info in delEntities:
                    continue
                newEntities.append(line)

        with open(dataFile, "w") as fh:
            fh.write("".join(newEntities))

    def mergeEntities(self, newEntities):
        annoSet = self.annoSet
        annoDir = self.annoDir

        dataFile = f"{annoDir}/{annoSet}/entities.tsv"

        with open(dataFile, "a") as fh:
            for fVals, slots in newEntities:
                fh.write("\t".join(str(x) for x in (*fVals, *slots)) + "\n")

    def saveEntitiesAs(self, dataFile):
        setData = self.getSetData()
        entities = setData.entities

        with open(dataFile, "a") as fh:
            for fVals, slots in entities.values():
                fh.write("\t".join(str(x) for x in (*fVals, *slots)) + "\n")
