"""Annotation data module.

This module manages the data of annotations.

To see how this fits among all the modules of this package, see
`tf.browser.ner.annotate` .

Annotation data is either the set of pre-existing data in the corpus or the
result of actions by the user of this tool, whether he uses the TF browser, or the API
in his own programs.

Annotation data must be stored on file, must be read from file,
and must be represented in memory in various ways in order to make the
API functions of the tool efficient.

We have set up the functions in such a way that data is only loaded and
processed if it is needed and out of date.
"""

import collections
import time

from ...core.generic import AttrDict
from ...core.files import (
    fileOpen,
    mTime,
    fileExists,
    initTree,
)
from .corpus import Corpus


class Data(Corpus):
    def __init__(self, data=None):
        """Manages annotation data.

        This class is also responsible for adding entities to a set and deleting
        entities from them.

        Both addition and deletion is implemented by first figuring out what has to be
        done, and then applying it to the entity data on disk; after that we
        perform a data load from the update file.

        Parameters
        ----------
        data: object, optional None
            Entity data to start with.
            If None, a fresh data store will be created.

            When the tool runs in browser context, each request will create a
            `Data` object from scratch. If no data is provided to the initializer,
            it will need to load the required data from file.
            This is wasteful.

            We have set up the web server in such a way that it incorporates the
            annotation data. The web server will pass it to the
            `tf.browser.ner.annotate.Annotate` object initializer, which passes
            it to the initializer here.

            In that way, the `Data` object can start with the data already in memory.
        """
        super().__init__()
        if not self.properlySetup:
            return

        if data is None:
            data = AttrDict()
            data.sets = AttrDict()

        self.data = data

        annoDir = self.annoDir
        initTree(annoDir, fresh=False)

    def loadData(self):
        """Loads data of the current annotation set into memory.

        It has two phases:

        *   loading the source data (see `Data.fromSource()`)
        *   processing the loaded source data (see `Data.process()`)
        """
        if not self.properlySetup:
            return

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
        """Loads annotation data from source.

        If the current annotation set is `""`, the annotation data is already in
        the TF data,
        and we compile that data into a dict of entity data keyed by entity node.

        Otherwise, we read the corresponding TSV file from disk and compile that
        data into a dict of entity data keyed by line number.

        After collection of this data it is stored in the set data; in fact we store
        data under the following keys:

        *   `dateLoaded`: datetime when the data was last loaded from disk;
        *   `entities`: the list of entities as loaded from the source;
            it is a dict of entities, keyed by nodes or line numbers;
            each entity specifies a tuple of feature values and a list of slots
            that are part of the entity.
        """
        if not self.properlySetup:
            return None

        settings = self.settings
        data = self.data
        annoSet = self.annoSet
        setData = data.sets[annoSet]
        annoDir = self.annoDir

        settings = self.settings
        features = settings.features

        featureDefault = self.featureDefault
        nF = len(features)

        checkFeature = self.checkFeature
        getFVal = self.getFVal
        getSlots = self.getSlots

        dataFile = f"{annoDir}/{annoSet}/entities.tsv"

        if "buckets" not in setData:
            setData.buckets = self.getBucketNodes()

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
                    with fileOpen(dataFile) as df:
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
                hasFeature = {feat: checkFeature(feat) for feat in features}

                for e in self.getEntityNodes():
                    slots = getSlots(e)
                    entities[e] = (
                        tuple(
                            getFVal(feat, e)
                            if hasFeature[feat]
                            else featureDefault[feat](slots)
                            for feat in features
                        ),
                        tuple(slots),
                    )

                setData.entities = entities

        return changed

    def process(self, changed):
        """Generated derived data structures out of the source data.

        After loading we process the data into derived data structures.

        We try to be lazy. We only load data from disk if the data is not
        already in memory, or the data on disk has been updated since the last load.

        The resulting data is stored in current set under the various keys.

        After processing, the time of processing is recorded, so that it can be
        observed if the processed data is no longer up to date w.r.t. the data as
        loaded from source.

        For each such set we produce several data structures, which we store
        under the following keys:

        *   `dateProcessed`: datetime when the data was last processed
        *   `entityText`: dict, text of entity by entity node or line number in
            TSV file;
        *   `entityTextVal`: dict of dict, set of feature values of entity, keyed by
            feature name and then by text of the entity;
        *   `entitySummary`: dict, list of entity nodes / line numbers, keyed by value
            of entity kind;
        *   `entityIdent`: dict, list of entity nodes./line numbers, keyed by tuple of
            entity feature values (these tuples are identifying for an entity);
        *   `entityFreq`: dict of counters, a counter for each feature name; the
            counter gives the number of times each value of that feature occurs in an
            entity;
        *   `entityIndex`: dict of dict, a dict for each feature name; the sub-dict
            gives for each position the values that entities occupying that position
            can have; positions are tuples of slots;
        *   `entityVal`: dict, keyed by value tuples gives the set of positions
            that entities with that value tuple occupy;
        *   `entitySlotVal`: dict, keyed by positions gives the set of values
            that entities occupying that position can have;
        *   `entitySlotAll`: dict, keyed by single first slots gives the set of
            ending slots that entities starting at that first slot have;
        *   `entitySlotIndex`: dict, keyed by single slot gives list of items
            corresponding to entities that occupy that slot;

            *   if an entity starts there, an entry `[True, -n, values]` is made;
            *   if an entity ends there, an entry `[False, n, values]` is made;
            *   if an entity occupies that slot without starting or ending there,
                an entry `None` is made;

            Above, `n` is the length of the entity in tokens and `values` is the
            tuple of feature values of that entity.

            This is precisely the information we need if we want to mark up a set of
            entities in the surrounding context of tokens.

        Parameters
        ----------
        changed: boolean
            Whether the data has changed since last processing.
        """
        if not self.properlySetup:
            return

        settings = self.settings
        features = settings.features
        getText = self.getText
        summaryIndices = settings.summaryIndices

        data = self.data
        annoSet = self.annoSet
        # annoSetRep = self.annoSetRep
        setData = data.sets[annoSet]

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
                txt = getText(slots)
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
        """Delete entity occurrences from the current set.

        This operation is not allowed if the current set is the read-only set with the
        empty name.

        The entities to delete are selected by their feature values.
        So you can use this function to delete all entities with a certain
        entity id and kind.

        Moreover, you can also specify a set of locations and restrict the entity
        removal to the entities that occupy those locations.

        Parameters
        ----------
        vals: tuple
            For each entity feature it has a value of that feature. This specifies
            which entities have to go.
        allMatches: iterable of tuple of int, optional None
            A number of slot tuples. They are the locations from which the candidate
            entities will be deleted.
            If it is None, the entity candidates will be removed wherever they occur.
        silent: boolean, optional False
            Reports how many entities have been deleted and how many were not present
            in the specified locations.

        Returns
        -------
        (int, int) or void
            If `silent`, it returns the number of non-existing entities that were
            asked to be deleted and the number of actually deleted entities.

            If the operation is not allowed, both integers above are set to -1.
        """
        if not self.properlySetup:
            return

        annoSet = self.annoSet
        annoSetRep = self.annoSetRep

        if not annoSet:
            if silent:
                return (-1, -1)
            self.console(f"Entity deletion not allowed on {annoSetRep}", error=True)
            return

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

        if silent:
            return (missing, deleted)

        self.console(f"Not present: {missing:>5} x")
        self.console(f"Deleted:     {deleted:>5} x")

    def delEntityRich(self, deletions, buckets, excludedTokens=set()):
        """Delete specified entity occurrences from the current set.

        This operation is not allowed if the current set is the read-only set with the
        empty name.

        This function has more detailed instructions as to which entities
        should be deleted than `Data.delEntity()` .

        It is a handy function for the TF browser to call, but not so much when you
        are manipulating entities yourself in a Jupyter notebook.

        Parameters
        ----------
        deletions: tuple of tuple or string
            Each member of the tuple corresponds to an entity feature.
            It is either a single value of such a feature, or an iterable
            of such values.
            The tuple together specifies a set of entities whose entity features
            have values that are either equal to the corresponding member of
            `deletions` or contained in it.
        buckets: iterable of list
            This is typically the result of
            `tf.browser.ner.annotate.Annotate.filterContent()`.
            The only important thing is that member 2 of each bucket is the list
            of entity matches in that bucket.
            Only entities that occupy these places will be removed.
        excludedTokens: set, optional set()
            This is the set of token positions that define the entities that must be
            skipped from deletion. If the last slot of an entity is in this set,
            the entity will not be deleted.
        """
        if not self.properlySetup:
            return

        annoSet = self.annoSet
        annoSetRep = self.annoSetRep
        browse = self.browse

        if not annoSet:
            msg = f"Entity deletion not allowed on {annoSetRep}"
            if browse:
                return [[msg]]
            else:
                self.console(msg, error=True)
                return

        settings = self.settings
        features = settings.features
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

            for bucket in buckets:
                allMatches = bucket[2]

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
                report.append(f"Deletion: occurrences excluded: {excl}")

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
        """Add entity occurrences to the current set.

        This operation is not allowed if the current set is the read-only set with the
        empty name.

        The entities to add are specified by their feature values.
        So you can use this function to add entities with a certain
        entity id and kind.

        You also have to specify a set of locations where the entities should be added.

        Parameters
        ----------
        vals: tuple
            For each entity feature it has a value of that feature. This specifies
            which entities have will be added.
        allMatches: iterable of tuple of int
            A number of slot tuples. They are the locations where the entities will be
            added.
        silent: boolean, optional False
            Reports how many entities have been added and how many were already present
            in the specified locations.

        Returns
        -------
        (int, int) or void
            If `silent`, it returns the number of already existing entities that were
            asked to be deleted and the number of actually deleted entities.

            If the operation is not allowed, both integers above are set to -1.
        """
        if not self.properlySetup:
            return

        annoSet = self.annoSet
        annoSetRep = self.annoSetRep

        if not annoSet:
            if silent:
                return (-1, -1)
            self.console(f"Entity addition not allowed on {annoSetRep}", error=True)
            return

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

        if silent:
            return (present, added)

        self.console(f"Already present: {present:>5} x")
        self.console(f"Added:           {added:>5} x")

    def addEntities(self, newEntities, silent=True):
        """Add multiple entities efficiently to the current set.

        This operation is not allowed if the current set is the read-only set with the
        empty name.

        If you have multiple entities to add, it is wasteful to do multiple passes over
        the corpus to find them.

        This method does them all in one fell swoop.
        It is used by the method `tf.browser.ner.ner.NER.markEntities()`.

        Parameters
        ----------
        newEntites: iterable of tuples of tuples
            each new entity consists of

            *   a tuple of entity feature values, specifying the entity to add
            *   a list of slot tuples, specifying where to add this entity

        silent: boolean, optional False
            Reports how many entities have been added and how many were already present
            in the specified locations.

        Returns
        -------
        (int, int) or void
            If `silent`, it returns the number of already existing entities that were
            asked to be deleted and the number of actually deleted entities.

            If the operation is not allowed, both integers above are set to -1.
        """
        if not self.properlySetup:
            return

        annoSet = self.annoSet
        annoSetRep = self.annoSetRep

        if not annoSet:
            if silent:
                return (-1, -1)
            self.console(f"Entities addition not allowed on {annoSetRep}", error=True)
            return

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
        if silent:
            return (present, added)

        self.console(f"Already present: {present:>5} x")
        self.console(f"Added:           {added:>5} x")

    def addEntityRich(self, additions, buckets, excludedTokens=set()):
        """Add specified entity occurrences to the current set.

        This operation is not allowed if the current set is the read-only set with the
        empty name.

        This function has more detailed instructions as to which entities
        should be added than `Data.addEntity()` .

        It is a handy function for the TF browser to call, but not so much when you
        are manipulating entities yourself in a Jupyter notebook.

        Parameters
        ----------
        additions: tuple of tuple or string
            Each member of the tuple corresponds to an entity feature.
            It is either a single value of such a feature, or an iterable
            of such values.
            The tuple together specifies a set of entities whose entity features
            have values that are either equal to the corresponding member of
            `additions` or contained in it.
        buckets: iterable of list
            This is typically the result of
            `tf.browser.ner.annotate.Annotate.filterContent()`.
            The only important thing is that member 2 of each bucket is the list
            of entity matches in that bucket.
            Entities will only be added at these places.
        excludedTokens: set, optional set()
            This is the set of token positions that define the locations that must not
            receive new entities. If the last slot of an entity is in this set,
            no entity will be added there.
        """
        if not self.properlySetup:
            return

        annoSet = self.annoSet
        annoSetRep = self.annoSetRep
        browse = self.browse

        if not annoSet:
            msg = f"Entity addition not allowed on {annoSetRep}"
            if browse:
                return [[msg]]
            else:
                self.console(msg, error=True)
                return

        settings = self.settings
        features = settings.features

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

            for bucket in buckets:
                allMatches = bucket[2]
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
                report.append(f"Addition: occurrences excluded: {excl}")

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
        """Performs deletions to the current annotation set.

        This operation is not allowed if the current set is the read-only set with the
        empty name.

        Parameters
        ----------
        delEntities: set
            The set consists of entity specs: a tuple of values of entity features,
            and an iterable of slot tuples where the entity is located.
        """
        if not self.properlySetup:
            return

        annoSet = self.annoSet
        annoSetRep = self.annoSetRep

        if not annoSet:
            self.console(f"Entity weeding not allowed on {annoSetRep}", error=True)
            return

        settings = self.settings
        features = settings.features
        nF = len(features)

        annoDir = self.annoDir

        dataFile = f"{annoDir}/{annoSet}/entities.tsv"

        newEntities = []

        with fileOpen(dataFile) as fh:
            for line in fh:
                fields = tuple(line.rstrip("\n").split("\t"))
                fVals = tuple(fields[0:nF])
                slots = tuple(int(f) for f in fields[nF:])
                info = (fVals, slots)
                if info in delEntities:
                    continue
                newEntities.append(line)

        with fileOpen(dataFile, mode="w") as fh:
            fh.write("".join(newEntities))

    def mergeEntities(self, newEntities):
        """Performs additions to the current annotation set.

        This operation is not allowed if the current set is the read-only set with the
        empty name.

        Parameters
        ----------
        newEntities: set
            The set consists of entity specs: a tuple of values of entity features,
            and an iterable of slot tuples where the entity is located.
        """
        if not self.properlySetup:
            return

        annoSet = self.annoSet
        annoSetRep = self.annoSetRep

        if not annoSet:
            self.console(f"Entity merging not allowed on {annoSetRep}", error=True)
            return

        annoDir = self.annoDir

        dataFile = f"{annoDir}/{annoSet}/entities.tsv"

        with fileOpen(dataFile, mode="a") as fh:
            for fVals, slots in newEntities:
                fh.write("\t".join(str(x) for x in (*fVals, *slots)) + "\n")

    def saveEntitiesAs(self, dataFile):
        """Export the data of an annotation set to a file.

        This function is used when a set has to be duplicated:
        `tf.browser.ner.sets.Sets.setDup()`.

        Parameters
        ----------
        dataFile: string
            The path of the file to write to.
        """
        if not self.properlySetup:
            return

        setData = self.getSetData()
        entities = setData.entities

        with fileOpen(dataFile, mode="a") as fh:
            for fVals, slots in entities.values():
                fh.write("\t".join(str(x) for x in (*fVals, *slots)) + "\n")
