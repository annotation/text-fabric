"""Annotation data module.

This module manages the data of annotation sets.

Annotation sets are either the sets of pre-existing entities in the corpus or the
result of actions by the user of this tool, whether he uses the TF browser, or the API
in his own programs, or the result of looking op the triggers in a spreadsheet.

Annotation sets must be stored on file, must be read from file,
and must be represented in memory in various ways in order to make the
API functions of the tool efficient.

We have set up the functions in such a way that sets are only loaded and
processed if they are needed and out of date.
"""

import collections
import time

from ..core.generic import AttrDict
from ..core.helpers import console
from ..core.files import fileOpen, mTime, fileExists, initTree

from .corpus import Corpus


class Data(Corpus):
    def __init__(self, sets=None):
        """Manages annotation sets and their corresponding data.

        This class is also responsible for adding entities to a set and deleting
        entities from them.

        Both addition and deletion is implemented by first figuring out what has to be
        done, and then applying it to the entity data on disk; after that we
        perform a data load from the update file.

        Parameters
        ----------
        sets: object, optional None
            Entity sets to start with.
            If None, a fresh store of sets will be created.

            When the tool runs in browser context, each request will create a
            `Data` object from scratch. If no sets are passed to the initializer,
            it will need to load the required sets from file.
            This is wasteful.

            We have set up the web server in such a way that it incorporates the
            annotation sets. The web server will pass them to the
            `tf.ner.ner.NER` object initializer, which passes
            it to the initializer here.

            In that way, the `Data` object can start with the sets already in memory.
        """
        Corpus.__init__(self)

        if not self.properlySetup:
            return

        self.sets = sets

        annoDir = self.annoDir
        initTree(annoDir, fresh=False)

    def loadSetData(self):
        """Loads the current annotation set into memory.

        It has two phases:

        *   loading the source set (see `Data.fromSourceSet()`)
        *   processing the loaded set (see `Data.processSet()`)
        """
        if not self.properlySetup:
            return

        sets = self.sets
        setName = self.setName

        if setName not in sets:
            sets[setName] = AttrDict()

        changed = self.fromSourceSet()
        self.processSet(changed)

    def _clearSetData(self):
        """Clears the current annotation set data from memory."""
        if not self.properlySetup:
            return

        sets = self.sets
        setName = self.setName

        setData = AttrDict()
        setData.entities = AttrDict()
        sets[setName] = setData
        self.processSet(True)

    def fromSourceSet(self):
        """Loads an annotation set from source.

        If the current annotation set is `""`, the annotation set is already present in
        the TF data, and we compile it into a dict of entity data keyed
        by entity node.

        Otherwise, we read the corresponding TSV file from disk and compile it
        into a dict of entity data keyed by line number.

        After collection of the set it is stored under the following keys:

        *   `dateLoaded`: datetime when the set was last loaded from disk;
        *   `entities`: the list of entities as loaded from the source;
            it is a dict of entities, keyed by nodes or line numbers;
            each entity specifies a tuple of feature values and a list of slots
            that are part of the entity.
        """
        if not self.properlySetup:
            return None

        settings = self.settings
        setName = self.setName
        setIsSrc = self.setIsSrc
        setData = self.sets[setName]
        annoDir = self.annoDir

        settings = self.settings
        features = settings.features

        featureDefault = self.featureDefault
        nF = len(features)

        checkFeature = self.checkFeature
        fvalFromNode = self.fvalFromNode
        slotsFromNode = self.slotsFromNode

        setFile = f"{annoDir}/{setName}/entities.tsv"

        if "buckets" not in setData:
            setData.buckets = self.getBucketNodes()

        changed = False

        if setIsSrc:
            if "entities" not in setData:
                entities = {}
                hasFeature = {feat: checkFeature(feat) for feat in features}

                for e in self.getEntityNodes():
                    slots = slotsFromNode(e)
                    entities[e] = (
                        tuple(
                            (
                                fvalFromNode(feat, e)
                                if hasFeature[feat]
                                else featureDefault[feat](slots)
                            )
                            for feat in features
                        ),
                        tuple(slots),
                    )

                setData.entities = entities
        else:
            if (
                "entities" not in setData
                or "dateLoaded" not in setData
                or (len(setData.entities) > 0 and not fileExists(setFile))
                or (fileExists(setFile) and setData.dateLoaded < mTime(setFile))
            ):
                changed = True
                entities = {}

                if fileExists(setFile):
                    with fileOpen(setFile) as df:
                        for e, line in enumerate(df):
                            fields = tuple(line.rstrip("\n").split("\t"))
                            entities[e] = (
                                tuple(fields[0:nF]),
                                tuple(int(f) for f in fields[nF:]),
                            )

                setData.entities = entities
                setData.dateLoaded = time.time()

        return changed

    def processSet(self, changed):
        """Generates derived data structures out of the source set.

        After loading we process the set into derived data structures.

        We try to be lazy. We only load a set from disk if it is not
        already in memory, or if the set on disk has been updated since the last load.

        The resulting data is stored in the current set under the various keys.

        After processing, the time of processing is recorded, so that it can be
        observed if the processed set is no longer up to date w.r.t. the source.

        For each such set we produce several data structures, which we store
        under the following keys:

        *   `dateProcessed`: datetime when the set was last processed
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
        *   `entityIdentFirst`: dict, keyed by entity id, and valued by the number
            of that entity in the list. If multiple entities in the list happen to
            have this id, the number of the first entity of them is chosen as value;
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
            Whether the set has changed since last processing.
        """
        if not self.properlySetup:
            return

        settings = self.settings
        textFromSlots = self.textFromSlots
        features = settings.features
        summaryIndices = settings.summaryIndices

        setName = self.setName
        setData = self.sets[setName]

        dateLoaded = setData.dateLoaded
        dateProcessed = setData.dateProcessed

        if (
            changed
            or "dateProcessed" not in setData
            or "entityText" not in setData
            or "entityTextVal" not in setData
            or "entitySummary" not in setData
            or "entityIdent" not in setData
            or "entityIdentFirst" not in setData
            or "entityFreq" not in setData
            or "entityIndex" not in setData
            or "entityVal" not in setData
            or "entitySlotVal" not in setData
            or "entitySlotAll" not in setData
            or "entitySlotIndex" not in setData
            or dateLoaded is not None
            and dateProcessed < dateLoaded
        ):
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
                txt = textFromSlots(slots)
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

    def delEntity(self, vals, allMatches=None, returns=True):
        """Delete entity occurrences from the current set.

        This operation is not allowed if the current set is a read-only set
        (from a spreadsheet or the already baked-in entities).

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
        allMatches: iterable of tuple of integer, optional None
            A number of slot tuples. They are the locations from which the candidate
            entities will be deleted.
            If it is None, the entity candidates will be removed wherever they occur.
        returns: boolean, optional False
            If False, the function reports how many entities have been deleted
            and how many were not present in the specified locations.
            Otherwise, these numbers are returned.

        Returns
        -------
        (int, int) or void
            If `returns`, it returns the number of non-existing entities that were
            asked to be deleted and the number of actually deleted entities.

            If the operation is not allowed, both integers above are set to -1.
        """
        if not self.properlySetup:
            return

        setIsRo = self.setIsRo
        setNameRep = self.setNameRep

        if setIsRo:
            if returns:
                return (-1, -1)
            console(f"Entity deletion not allowed on {setNameRep}", error=True)
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
            self._weedEntities(delEntities)

        self.loadSetData()

        if returns:
            return (missing, deleted)

        self.console(f"Not present: {missing:>5} x")
        self.console(f"Deleted:     {deleted:>5} x")

    def delEntityRich(self, deletions, buckets, excludedTokens=set()):
        """Delete specified entity occurrences from the current set.

        This operation is not allowed if the current set is a read-only set
        (from a spreadsheet or the already baked-in entities).

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
            Restricts the scope where entities should be removed.
            This is typically the result of
            `tf.ner.corpus.Corpus.filterContent()`.
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

        setNameRep = self.setNameRep
        setIsRo = self.setIsRo
        browse = self.browse

        if setIsRo:
            msg = f"Entity deletion not allowed on {setNameRep}"
            if browse:
                return [[msg]]
            else:
                console(msg, error=True)
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
            self._weedEntities(delEntities)

        if browse:
            return report

        self.loadSetData()
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

    def addEntity(self, vals, allMatches, returns=True):
        """Add entity occurrences to the current set.

        This operation is not allowed if the current set is a read-only set
        (from a spreadsheet or the already baked-in entities).

        The entities to add are specified by their feature values.
        So you can use this function to add entities with a certain
        entity id and kind.

        You also have to specify a set of locations where the entities should be added.

        Parameters
        ----------
        vals: tuple
            For each entity feature it has a value of that feature. This specifies
            which entities have will be added.
        allMatches: iterable of tuple of integer
            A number of slot tuples. They are the locations where the entities will be
            added.
        returns: boolean, optional False
            If True, reports how many entities have been added and how many
            were already present in the specified locations.
            Otherwise, these numbers are returned by the function.

        Returns
        -------
        (int, int) or void
            If `returns`, it returns the number of already existing entities that were
            asked to be deleted and the number of actually deleted entities.

            If the operation is not allowed, both integers above are set to -1.
        """
        if not self.properlySetup:
            return

        setNameRep = self.setNameRep
        setIsRo = self.setIsRo

        if setIsRo:
            if returns:
                return (-1, -1)
            console(f"Entity addition not allowed on {setNameRep}", error=True)
            return

        setData = self.getSetData()

        oldEntities = setData.entities

        addE = set()

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
            if info not in addE:
                addE.add(info)
                added += 1

        if len(addE):
            self._mergeEntities(addE)

        self.loadSetData()

        if returns:
            return (present, added)

        self.console(f"Already present: {present:>5} x")
        self.console(f"Added:           {added:>5} x")

    def addEntities(self, newEntities, returns=True, _lowlevel=False):
        """Add multiple entities efficiently to the current set.

        This operation is not allowed if the current set is a read-only set, unless
        `_lowlevel` is True.

        If you have multiple entities to add, it is wasteful to do multiple passes over
        the corpus to find them.

        This method does them all in one fell swoop.

        Parameters
        ----------
        newEntites: iterable of tuples of tuples
            each new entity consists of

            *   a tuple of entity feature values, specifying the entity to add
            *   a list of slot tuples, specifying where to add this entity

        _lowlevel: boolean, optional False
            Whether this function is executed in low-level mode.
            Some calls of this function are done in specific contexts, where certain
            conditions are known to be fulfilled and do not have to be checked.
            The intention is that only this codebase will ever pass `_lowlevel=True`,
            and that outside functions never pass this parameter.

        returns: boolean, optional False
            If True, eports how many entities have been added and how many were
            already present in the specified locations.
            Otherwise it returns these numbers, unless `_lowlevel` is True, in which

            case it returns nothing.

        Returns
        -------
        (int, int) or void
            If `returns`, it returns the number of already existing entities that were
            asked to be deleted and the number of actually deleted entities.

            If the operation is not allowed, both integers above are set to -1.
        """
        if not self.properlySetup:
            return

        setNameRep = self.setNameRep
        setIsRo = self.setIsRo
        setIsX = self.setIsX

        if not _lowlevel and setIsRo:
            if returns:
                return (-1, -1)
            console(f"Entities addition not allowed on {setNameRep}", error=True)
            return

        if _lowlevel and not setIsX:
            return

        setData = self.getSetData()

        oldEntities = set(setData.entities.values())

        addE = set()

        present = 0
        added = 0

        for fVals, allMatches in newEntities:
            for slots in allMatches:
                if (fVals, slots) in oldEntities:
                    present += 1
                elif (fVals, slots) in addE:
                    continue
                else:
                    added += 1
                    addE.add((fVals, slots))

        if len(addE):
            self._mergeEntities(addE, _lowlevel=_lowlevel)

        self.loadSetData()

        if returns:
            return (present, added)

        if _lowlevel:
            return

        self.console(f"Already present: {present:>5} x")
        self.console(f"Added:           {added:>5} x")

    def addEntityRich(self, additions, buckets, excludedTokens=set()):
        """Add specified entity occurrences to the current set.

        This operation is not allowed if the current set is a read-only set
        (from a spreadsheet or the already baked-in entities).

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
            `tf.ner.corpus.Corpus.filterContent()`.
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

        setNameRep = self.setNameRep
        setIsRo = self.setIsRo
        browse = self.browse

        if setIsRo:
            msg = f"Entity addition not allowed on {setNameRep}"
            if browse:
                return [[msg]]
            else:
                console(msg, error=True)
                return

        settings = self.settings
        features = settings.features

        setData = self.getSetData()

        oldEntities = setData.entities

        report = []

        addEnts = set()

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
                        if info not in addEnts:
                            addEnts.add(info)
                            stats[fVals] += 1

            report.append(
                tuple(sorted(stats.items())) if len(stats) else ["Nothing added"]
            )
            if excl:
                report.append(f"Addition: occurrences excluded: {excl}")

        if len(addEnts):
            self._mergeEntities(addEnts)

        if browse:
            return report

        self.loadSetData()
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

    def saveEntitiesAs(self, dataFile):
        """Export an annotation set to a file.

        This function is used when a set has to be duplicated:
        `tf.ner.sets.Sets.setDup()`.

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

    def _weedEntities(self, delEntities):
        """Performs deletions to the current annotation set.

        This operation is not allowed if the current set is a read-only set
        (from a spreadsheet or the already baked-in entities).

        Parameters
        ----------
        delEntities: set
            The set consists of entity specs: a tuple of values of entity features,
            and an iterable of slot tuples where the entity is located.
        """
        if not self.properlySetup:
            return

        setName = self.setName
        setNameRep = self.setNameRep
        setIsRo = self.setIsRo

        if setIsRo:
            console(f"Entity weeding not allowed on {setNameRep}", error=True)
            return

        settings = self.settings
        features = settings.features
        nF = len(features)

        annoDir = self.annoDir

        dataFile = f"{annoDir}/{setName}/entities.tsv"

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

    def _mergeEntities(self, newEntities, _lowlevel=False):
        """Performs additions to the current annotation set.

        This operation is not allowed if the current set is the read-only set with the
        empty name.

        Parameters
        ----------
        newEntities: set
            The set consists of entity specs: a tuple of values of entity features,
            and an iterable of slot tuples where the entity is located.

        _lowlevel: boolean, optional False
            Whether this function is executed in low-level mode.
            Some calls of this function are done in specific contexts, where certain
            conditions are known to be fulfilled and do not have to be checked.
            The intention is that only this codebase will ever pass `_lowlevel=True`,
            and that outside functions never pass this parameter.
        """
        if not self.properlySetup:
            return

        setName = self.setName
        setNameRep = self.setNameRep
        setIsRo = self.setIsRo
        setIsX = self.setIsX

        if not _lowlevel and setIsRo:
            console(f"Entity merging not allowed on {setNameRep}", error=True)
            return

        if _lowlevel and not setIsX:
            return

        annoDir = self.annoDir

        dataFile = f"{annoDir}/{setName}/entities.tsv"

        with fileOpen(dataFile, mode="w" if _lowlevel else "a") as fh:
            for fVals, slots in newEntities:
                fh.write("\t".join(str(x) for x in (*fVals, *slots)) + "\n")
