"""TF backend processing.

This module is for functions that extract data from the corpus
and put it in various dedicated data structures.
"""

import collections
import time
from itertools import chain


from ...core.helpers import console as cs
from ...core.generic import AttrDict
from ...core.files import (
    mTime,
    fileExists,
    annotateDir,
    dirRemove,
    dirExists,
    dirContents,
    dirCopy,
    dirMake,
    dirMove,
)

from .settings import (
    TOOLKEY,
    ENTITY_TYPE,
    FEATURES,
    SUMMARY_INDICES,
    NF,
    BUCKET_TYPE,
    ERROR,
    featureDefault,
    getText,
)

from .match import entityMatch


class Annotate:
    def __init__(self, app, data, annoSet, debug=True):
        self.app = app
        self.F = app.api.F
        self.data = data
        self.annoSet = annoSet
        self.debug = debug
        annoDir = annotateDir(app, TOOLKEY)
        self.annoDir = annoDir

    def console(self, msg):
        if self.debug:
            cs(msg)

    def getSetsFS(self):
        """Get the existing annotation sets.

        Parameters
        ----------
        annoDir: string
            The directory under which the distinct annotation sets can be found.
            The names of these subdirectories are the names of the annotation sets.

        Returns
        -------
        set
            The annotation sets, sorted by name.
        """
        annoDir = self.annoDir
        return set(dirContents(annoDir)[1])

    def setDel(self, delSet):
        data = self.data
        setsData = data.sets
        annoDir = self.annoDir
        annoPath = f"{annoDir}/{delSet}"
        sets = self.getSetsFS()
        self.sets = self.sets

        messages = []

        dirRemove(annoPath)

        if dirExists(annoPath):
            messages.append((ERROR, f"""Could not remove {delSet}"""))
        else:
            sets.remove(delSet)
            del setsData[delSet]
            self.annoSet = ""

        return messages

    def setDup(self, dupSet):
        data = self.data
        setsData = data.sets
        annoSet = self.annoSet
        annoDir = self.annoDir
        annoPath = f"{annoDir}/{dupSet}"

        sets = self.getSetsFS()
        self.sets = sets

        messages = []

        if dupSet in sets:
            messages.append((ERROR, f"""Set {dupSet} already exists"""))
        else:
            if annoSet:
                if not dirCopy(
                    f"{annoDir}/{annoSet}",
                    annoPath,
                    noclobber=True,
                ):
                    messages.append(
                        (ERROR, f"""Could not copy {annoSet} to {dupSet}""")
                    )
                else:
                    sets.add(dupSet)
                    setsData[dupSet] = setsData[annoSet]
                    self.annoSet = dupSet
            else:
                dataFile = f"{annoPath}/entities.tsv"

                if fileExists(dataFile):
                    messages.append((ERROR, f"""Set {dupSet} already exists"""))
                else:
                    dirMake(annoPath)
                    self.saveEntitiesAs(dataFile)
                    setsData[dupSet] = setsData[annoSet]
                    self.annoSet = dupSet

        return messages

    def setMove(self, moveSet):
        data = self.data
        setsData = data.sets
        annoSet = self.annoSet
        annoDir = self.annoDir
        annoPath = f"{annoDir}/{moveSet}"

        sets = self.getSetsFS()
        self.sets = sets

        messages = []

        if dirExists(annoPath):
            messages.append((ERROR, f"""Set {moveSet} already exists"""))
        else:
            if not dirMove(f"{annoDir}/{annoSet}", annoPath):
                messages.append(
                    (
                        ERROR,
                        f"""Could not rename {annoSet} to {moveSet}""",
                    )
                )
            else:
                sets.add(moveSet)
                sets.remove(annoSet)
                setsData[moveSet] = setsData[annoSet]
                del setsData[annoSet]
                self.annoSet = moveSet

        return messages

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

        setsData = data.sets

        if annoSet not in setsData:
            setsData[annoSet] = AttrDict()

        # load bucket nodes

        changed = self.fromSource()
        self.process(changed)

    def fromSource(self):
        app = self.app
        data = self.data
        annoSet = self.annoSet
        setData = data.sets[annoSet]
        annoDir = self.annoDir

        api = app.api
        F = api.F
        Fs = api.Fs
        L = api.L

        slotType = F.otype.slotType

        dataFile = f"{annoDir}/{annoSet}/entities.tsv"

        if "buckets" not in setData:
            setData.buckets = F.otype.s(BUCKET_TYPE)

        changed = False

        if annoSet:
            if (
                "entities" not in setData
                or "dateLoaded" not in setData
                or (len(setData.entities) > 0 and not fileExists(dataFile))
                or (fileExists(dataFile) and setData.dateLoaded < mTime(dataFile))
            ):
                self.console(f"LOAD '{annoSet}' START")
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
                self.console(f"LOAD '{annoSet}' DONE")
            else:
                self.console(f"LOAD '{annoSet}' REUSED")
        else:
            if "entities" not in setData:
                entities = {}
                hasFeature = {
                    feat: api.isLoaded(feat, pretty=False)[feat] is not None
                    for feat in FEATURES
                }

                for e in F.otype.s(ENTITY_TYPE):
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

    def process(self, changed):
        app = self.app
        data = self.data
        annoSet = self.annoSet
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
            or "entitySlotIndex" not in setData
            or dateLoaded is not None
            and dateProcessed < dateLoaded
        ):
            self.console(f"PROCESS '{annoSet}' START")

            entityItems = setData.entities.items()

            entityText = {}
            entityTextVal = {feat: collections.defaultdict(set) for feat in FEATURES}
            entitySummary = {}
            entityIdent = {}
            entityIdentFirst = {}
            entityFreq = {feat: collections.Counter() for feat in FEATURES}
            entityIndex = {feat: {} for feat in FEATURES}
            entityVal = {}
            entitySlotVal = {}
            entitySlotIndex = {}

            for (e, (fVals, slots)) in entityItems:
                txt = getText(F, slots)
                ident = fVals
                summary = tuple(fVals[i] for i in SUMMARY_INDICES)

                entityText[e] = txt
                entityVal.setdefault(fVals, set()).add(slots)

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
            setData.entityVal = entityVal
            setData.entitySlotVal = entitySlotVal
            setData.entitySlotIndex = entitySlotIndex

            setData.dateProcessed = time.time()
            self.console(f"PROCESS '{annoSet}' DONE")

        else:
            self.console(f"PROCESS '{annoSet}' REUSED")

    def getCurData(self):
        data = self.data
        setsData = data.sets
        annoSet = self.annoSet
        return setsData[annoSet]

    def delEntity(self, deletions, buckets, excludedTokens):
        setData = self.getCurData()

        oldEntities = setData.entities

        report = []

        delEntities = set()
        delEntitiesByE = set()

        if any(len(x) > 0 for x in deletions):
            oldEntitiesBySlots = collections.defaultdict(set)

            for (e, info) in oldEntities.items():
                oldEntitiesBySlots[info[1]].add(e)

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

            report.append(
                tuple(sorted(stats.items())) if len(stats) else ["Nothing deleted"]
            )
            if excl:
                report.append(f"Deletion: occurences excluded: {excl}")

        if len(delEntities):
            self.weedEntities(delEntities)

        return report

    def addEntity(self, additions, buckets, excludedTokens):
        setData = self.getCurData()

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
                        info = (fVals, matches)
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

        return report

    def weedEntities(self, delEntities):
        annoSet = self.annoSet
        annoDir = self.annoDir

        dataFile = f"{annoDir}/{annoSet}/entities.tsv"

        newEntities = []

        with open(dataFile) as fh:
            for line in fh:
                fields = tuple(line.rstrip("\n").split("\t"))
                fVals = tuple(fields[0:NF])
                matches = tuple(int(f) for f in fields[NF:])
                info = (fVals, matches)
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
            for (fVals, matches) in newEntities:
                fh.write("\t".join(str(x) for x in (*fVals, *matches)) + "\n")

    def saveEntitiesAs(self, dataFile):
        setData = self.getCurData()
        entities = setData.entities

        with open(dataFile, "a") as fh:
            for (fVals, matches) in entities.values():
                fh.write("\t".join(str(x) for x in (*fVals, *matches)) + "\n")

    def filterBuckets(
        self,
        sFindRe,
        activeEntity,
        tokenStart,
        tokenEnd,
        valSelect,
        freeState,
        noFind=False,
        node=None,
    ):
        """Filter the buckets.

        Will filter the buckets by tokens if the `tokenStart` and `tokenEnd` parameters
        are both filled in.
        In that case, we look up the text between those tokens and including.
        All buckets that contain that text of those slots will show up,
        all other buckets will be left out.
        However, if `valSelect` is non-empty, then there is a further filter: only if the
        text corresponds to an entity with those feature values, the bucket is
        passed through.
        The matching slots will be highlighted.

        Parameters
        ----------
        sFindPattern: string
            A search string that filters the buckets, before applying the search
            for a word sequence.

        tokenStart, tokenEnd: int or None
            Specify the start slot number and the end slot number of a sequence of tokens.
            Only buckets that contain this token bucket will be passed through,
            all other buckets will be filtered out.

        valSelect: set
            The feature values to filter on.

        Returns
        -------
        list of tuples
            For each bucket that passes the filter, a tuple with the following
            members is added to the list:

            *   tokens: the tokens of the bucket
            *   matches: the match positions of the found text
            *   positions: the token positions where a targeted token sequence starts
        """
        app = self.app
        setData = self.getCurData()
        entities = setData.entities
        api = app.api
        L = api.L
        F = api.F
        T = api.T

        results = []
        words = []

        hasEnt = activeEntity is not None
        hasOcc = not hasEnt and tokenStart and tokenEnd

        words = (
            tuple(
                word
                for t in range(tokenStart, tokenEnd + 1)
                if (word := (F.str.v(t) or "").strip())
            )
            if hasOcc
            else None
        )

        eVals = entities[activeEntity][0] if hasEnt else None

        nFind = 0
        nEnt = {feat: collections.Counter() for feat in ("",) + FEATURES}
        nVisible = {feat: collections.Counter() for feat in ("",) + FEATURES}

        entityIndex = setData.entityIndex
        entityVal = setData.entityVal
        entitySlotVal = setData.entitySlotVal
        entitySlotIndex = setData.entitySlotIndex

        requireFree = (
            True if freeState == "free" else False if freeState == "bound" else None
        )

        buckets = (
            setData.buckets
            if node is None
            else L.d(T.sectionTuple(node)[1], otype=BUCKET_TYPE)
        )

        if hasEnt:
            eSlots = entityVal[eVals]
            eStarts = {s[0]: s[-1] for s in eSlots}
        else:
            eStarts = None

        for b in buckets:
            (fits, fValStats, result, occurs) = entityMatch(
                entityIndex,
                eStarts,
                entitySlotVal,
                entitySlotIndex,
                L,
                F,
                T,
                b,
                sFindRe,
                words,
                eVals,
                valSelect,
                requireFree,
            )

            blocked = fits is not None and not fits

            if not blocked:
                nFind += 1

            for feat in ("",) + FEATURES:
                theseStats = fValStats[feat]
                if len(theseStats):
                    theseNEnt = nEnt[feat]
                    theseNVisible = nVisible[feat]

                    for (ek, n) in theseStats.items():
                        theseNEnt[ek] += n
                        if not blocked:
                            theseNVisible[ek] += n

            if node is None:
                if not occurs:
                    continue

                if fits is not None and not fits:
                    continue

            results.append((b, *result))

        return (results, nFind, nVisible, nEnt)

    def entityTable(self, activeEntity, sortKey, sortDir, H, repIdent):
        setData = self.getCurData()

        hasEnt = activeEntity is not None

        entries = setData.entityIdent.items()
        eFirst = setData.entityIdentFirst

        if sortKey == "freqsort":
            entries = sorted(entries, key=lambda x: (len(x[1]), x[0]))
        else:
            index = int(sortKey[5:])
            entries = sorted(entries, key=lambda x: (x[0][index], -len(x[1])))

        if sortDir == "d":
            entries = reversed(entries)

        content = []

        for (vals, es) in entries:
            x = len(es)
            e1 = eFirst[vals]

            active = " queried " if hasEnt and e1 == activeEntity else ""

            content.append(
                H.p(
                    H.code(f"{x:>5}", cls="w"),
                    " x ",
                    repIdent(vals, active=active),
                    cls=f"e {active}",
                    enm=e1,
                )
            )

        return H.join(content)

    def bucketTable(
        self, buckets, activeEntity, tokenStart, tokenEnd, excludedTokens, H, repIdent
    ):
        app = self.app
        setData = self.getCurData()
        annoSet = self.annoSet
        api = app.api
        F = api.F

        entityIdent = setData.entityIdent
        eFirst = setData.entityIdentFirst
        entitySlotIndex = setData.entitySlotIndex

        hasOcc = tokenStart and tokenEnd
        hasEnt = activeEntity is not None

        limited = not (hasOcc or hasEnt)

        content = []

        i = 0

        for (b, bTokens, matches, positions) in buckets:
            charPos = 0
            if annoSet:
                allMatches = set()
                endMatches = set()
                for match in matches:
                    allMatches |= set(match)
                    endMatches.add(match[-1])

            else:
                allMatches = set(chain.from_iterable(matches))

            subContent = [
                H.span(
                    app.sectionStrFromNode(b), node=b, cls="bh", title="show context"
                )
            ]

            for (t, w) in bTokens:
                info = entitySlotIndex.get(t, None)
                inEntity = False

                if info is not None:
                    inEntity = True
                    for item in sorted(
                        (x for x in info if x is not None), key=lambda z: z[1]
                    ):
                        (status, lg, ident) = item
                        e = eFirst[ident]

                        if status:
                            active = " queried " if hasEnt and e == activeEntity else ""
                            subContent.append(
                                H.span(
                                    H.span(abs(lg), cls="lgb"),
                                    repIdent(ident, active=active),
                                    " ",
                                    H.span(len(entityIdent[ident]), cls="n"),
                                    cls="es",
                                    enm=e,
                                )
                            )

                endQueried = annoSet and t in endMatches
                excl = "x" if t in excludedTokens else "v"

                after = F.after.v(t) or ""
                lenW = len(w)
                lenWa = len(w) + len(after)
                found = any(charPos + i in positions for i in range(lenW))
                queried = t in allMatches

                hlClasses = (" found " if found else "") + (
                    " queried " if queried else ""
                )
                hlClasses += " ei " if inEntity else ""
                hlClass = dict(cls=hlClasses) if hlClasses else {}

                subContent.append(
                    H.join(
                        H.span(w, **hlClass, t=t),
                        H.span(te=t, st=excl) if endQueried else "",
                        after,
                    )
                )

                if info is not None:
                    for item in sorted(
                        (x for x in info if x is not None), key=lambda z: z[1]
                    ):
                        (status, lg, ident) = item
                        if not status:
                            subContent.append(
                                H.span(H.span(abs(lg), cls="lge"), cls="ee")
                            )

                charPos += lenWa

            content.append(H.div(subContent, cls="b"))

            i += 1

            if limited and i > 100:
                content.append(
                    H.div(
                        f"Showing only the first 100 {BUCKET_TYPE}s of all "
                        f"{len(buckets)} ones.",
                        cls="report",
                    )
                )
                break

        return content
