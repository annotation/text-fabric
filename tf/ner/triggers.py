import collections
from textwrap import dedent

from ..core.files import fileOpen
from ..core.helpers import console

from .helpers import hasCommon, toTokens
from .match import occMatch
from .scopes import locInScopes


def makePartitions(triggers, myToTokens):
    """Partition a set of triggers into groups where triggers are pairwise disjoint.

    The intention is to explore all triggers that apparently do not have hits.
    We need to look them up in isolation, because then they might have hits.

    But searching per trigger is expensive. We want to group triggers together
    that can not interact with each other: triggers whose tokens are pairwise
    disjoint. A hit of one trigger can then never be part of a hit of any other
    trigger in the group.
    """

    triggerTokens = {}
    nTriggerTokens = {}

    for trigger in triggers:
        tokens = myToTokens(trigger)
        triggerTokens[trigger] = tokens
        nTriggerTokens.setdefault(len(tokens), {})[trigger] = tokens

    singleTokenTriggers = list(nTriggerTokens[1]) if 1 in nTriggerTokens else []

    partition = [singleTokenTriggers]

    for n in sorted(nTriggerTokens):
        if n == 1:
            continue
        for triggerA, tokensA in nTriggerTokens[n].items():
            added = False

            for part in partition:
                common = False

                for triggerB in part:
                    tokensB = triggerTokens[triggerB]

                    if hasCommon(tokensA, tokensB):
                        common = True
                        break

                if common:
                    continue

                part.append(triggerA)
                added = True
                break

            if not added:
                partition.append([triggerA])

    return (triggerTokens, partition)


class Triggers:
    def partitionTriggers(self, triggers):
        return makePartitions(triggers, self.getToTokensFunc())[1]

    def reportHits(self, silent=None, showNoHits=False):
        """Reports the inventory."""
        if not self.properlySetup:
            return

        silent = self.silent if silent is None else silent
        sectionHead = self.sectionHead
        sheetData = self.getSheetData()
        allTriggers = sheetData.allTriggers
        inventory = sheetData.inventory

        setName = self.setName
        annoDir = self.annoDir
        setDir = f"{annoDir}/{setName}"
        reportFile = f"{setDir}/hits.tsv"
        reportTriggerBySlotFile = f"{setDir}/triggerBySlot.tsv"

        hitData = []
        names = set()
        noHits = set()
        triggersBySlot = {}

        for e in sorted(allTriggers):
            (name, eidkind, trigger, scope) = e

            names.add(name)

            entry = (name, trigger, scope)
            section = ""
            hits = ""

            entInfo = inventory.get(eidkind, None)

            if entInfo is None:
                hitData.append(("!E", *entry, "", 0))
                noHits.add(trigger)
                continue

            triggerInfo = entInfo.get(trigger, None)

            if triggerInfo is None:
                hitData.append(("!T", *entry, "", 0))
                noHits.add(trigger)
                continue

            occs = triggerInfo.get(scope, None)

            if occs is None or len(occs) == 0:
                hitData.append(("!P", *entry, "", 0))
                noHits.add(trigger)
                continue

            sectionInfo = collections.Counter()

            for slots in occs:
                for slot in slots:
                    triggersBySlot.setdefault(slot, set()).add(trigger)

                section = sectionHead(slots[0])
                sectionInfo[section] += 1

            for section, hits in sorted(sectionInfo.items()):
                hitData.append(("OK", *entry, section, hits))

        multipleTriggers = {}
        triggerBySlot = {}
        self.triggerBySlot = triggerBySlot

        for slot, triggers in triggersBySlot.items():
            if len(triggers) > 1:
                multipleTriggers[slot] = triggers

            triggerBySlot[slot] = list(triggers)[0]

        if len(multipleTriggers) == 0:
            self.console("No slot is covered by more than one trigger")
        else:
            console(
                f"Slots covered by multiple triggers: {len(multipleTriggers)}",
                error=True,
            )
            for slot, triggers in multipleTriggers.items():
                triggersRep = ", ".join(f"«{trigger}»" for trigger in sorted(triggers))
                self.console(f"{slot:>7}: {triggersRep}", error=True)

        trigWithout = len(noHits)

        if showNoHits and (trigWithout > 0):
            uncovered = 0
            console(
                "Triggers without hits: " f"{trigWithout}x:",
                error=True,
            )

            if len(noHits):
                uncovered = self.diagnoseTriggers(noHits, detail=False)

        with fileOpen(reportFile, "w") as rh:
            rh.write("label\tname\ttrigger\tscope\tsection\thits\n")

            for h in sorted(hitData):
                line = "\t".join(str(c) for c in h)
                rh.write(f"{line}\n")

        with fileOpen(reportTriggerBySlotFile, "w") as rh:
            rh.write("slot\ttrigger\n")

            for slot, trigger in sorted(
                triggerBySlot.items(), key=lambda x: (x[1], x[0])
            ):
                rh.write(f"{slot}\t{trigger}\n")

        nEnt = len(names)
        nTriggers = len(allTriggers)
        nHits = sum(e[-1] for e in hitData)

        msg = (
            f"\t{nEnt} entities targeted with {nHits} occurrences. See {reportFile}"
            if silent
            else dedent(
                f"""
                Entities targeted:          {nEnt:>5}
                Triggers searched for:      {nTriggers:>5}
                Triggers without hits:      {trigWithout:>5}
                 - completely covered:      {trigWithout - uncovered:>5}
                 - missing hits:            {uncovered:>5}
                Triggers with hits:         {nTriggers - trigWithout:>5}
                Total hits:                 {nHits:>5}

                All hits in report file:      {reportFile}
                Triggers by slot in file:     {reportTriggerBySlotFile}
                """
            )
        )
        console(msg)

    def triggerInterference(self, alsoInternal=False, alsoExpected=False):
        """Produce a report of interferences between triggers.

        Triggers interfere if they have matches that intersect, i.e. there is a match
        m1 of trigger t1 and a match m2 of trigger t2 such that m1 and m2 intersect.

        Triggers may interfere *potentially*: if the triggers overlap they can have
        intersecting matches. But it does not mean that the corpus contains overlapping
        matches, i.e. that the triggers conflict actually.

        We report *actually* interfering triggers.

        Triggers within one row are associated to the same entity and work in the same
        row. It is not bad if they are conflicting with each other. If there
        are conflicting matches, the trigger that wins still flags the same entity.
        The worst thing is that some of these triggers are superfluous, but there is
        no reason to be picky on superfluous triggers.

        When one trigger is a proper part of another, this is mostly intentional.
        If the longer trigger matches, it wins it from the shorter trigger, unless
        the shorter trigger's match starts before the longer trigger's match.

        We think the user expects the longer trigger to win, but it may surprise him
        if the shorter triggers wins because it starts earlier.

        Parameters
        ----------
        alsoInternal: boolean, optional False
            Also report interference between triggers on the same row.
        alsoExpected: boolean, optional False
            Also report expected interferences.
        """
        setName = self.setName
        annoDir = self.annoDir
        setDir = f"{annoDir}/{setName}"
        reportFile = f"{setDir}/interference.txt"

        app = self.app
        L = app.api.L
        T = app.api.T
        sheetData = self.getSheetData()
        rowMap = sheetData.rowMap
        triggerScopes = sheetData.triggerScopes

        interferences, parts = self.interference(
            rowMap,
            triggerScopes,
            self.getToTokensFunc(),
            self.seqFromStr,
            alsoInternal=alsoInternal,
            alsoExpected=alsoExpected,
        )

        messages = []
        witnessed = {}

        nParts = len(parts)
        plural = "" if nParts == 1 else "es"
        self.console(
            f"Looking up {len(interferences)} potential interferences "
            f"in {len(parts)} pass{plural} over the corpus ",
            newline=False,
        )

        for part in parts:
            self.console(".", newline=False)
            inventory = self.findTriggers(part)

            for trigger, data in inventory.items():
                occs = data.get(trigger, {}).get("", [])
                nOccs = len(occs)

                if nOccs:
                    witnessed[trigger] = occs

        self.console("")

        msg = (
            f"{len(witnessed)} potential conflicting trigger pairs with "
            f"{sum(len(x) for x in witnessed.values())} conflicts"
        )
        console(msg)
        messages.append(msg)

        conflicts = {}

        for (
            triggerA,
            triggerB,
            triggerC,
            scopeRepA,
            scopeRepB,
            commonScopes,
        ) in interferences:
            if triggerC not in witnessed:
                continue

            rowA = sorted(set(rowMap[triggerA]))
            rowB = sorted(set(rowMap[triggerB]))
            key = "same row" if rowA == rowB else "different rows"
            conflicts.setdefault(key, []).append(
                (
                    rowA,
                    rowB,
                    triggerA,
                    triggerB,
                    witnessed[triggerC],
                    scopeRepA,
                    scopeRepB,
                    commonScopes,
                )
            )

        for key, confls in conflicts.items():
            newConfls = []

            for (
                rowA,
                rowB,
                triggerA,
                triggerB,
                occs,
                scopeRepA,
                scopeRepB,
                commonScopes,
            ) in confls:
                hits = {}

                for occ in sorted(occs):
                    sectionNode = L.u(occ[0], otype="chunk")[0]
                    heading = tuple(
                        int(x if type(x) is int else x.lstrip("0") or "0")
                        for x in T.sectionFromNode(sectionNode, fillup=True)
                    )

                    if not locInScopes(heading, commonScopes):
                        continue

                    heading = app.sectionStrFromNode(sectionNode)
                    hits.setdefault(heading, []).append(occ)

                if len(hits) == 0:
                    continue

                newConfls.append(
                    (rowA, rowB, triggerA, triggerB, hits, scopeRepA, scopeRepB)
                )

            msg = f"{key} ({len(newConfls)} pairs)"
            msg = f"----------\n{msg}\n----------"
            console(msg)
            messages.append(msg)

            for (
                rowA,
                rowB,
                triggerA,
                triggerB,
                hits,
                scopeRepA,
                scopeRepB,
            ) in newConfls:
                rowRepA = ",".join(str(r) for r in rowA)
                rowRepB = ",".join(str(r) for r in rowB)
                msg = (
                    f"{rowRepA:<12} ({scopeRepA:<12}): «{triggerA}»\n"
                    f"{rowRepB:<12} ({scopeRepB:<12}): «{triggerB}»"
                )
                console(msg)
                messages.append(msg)
                console(f"{hits=}")

                diags = []

                i = 0

                for heading, occs in sorted(hits.items()):
                    nOccs = len(occs)

                    if i == 0:
                        diags.append([])

                    diags[-1].append(f"{heading} x {nOccs}")
                    i += 1

                    if i == 5:
                        i = 0

                first = True

                for batch in diags:
                    label = f"{'occurrences':>25}: " if first else (" " * 27)
                    first = False
                    msg = f"{label} {', '.join(batch)}"
                    console(msg)
                    messages.append(msg)

        with fileOpen(reportFile, "w") as fh:
            for msg in messages:
                fh.write(f"{msg}\n")

        console(f"Diagnostic trigger interferences written to {reportFile}")

    def diagnoseTriggers(self, triggers, detail=True):
        sheetData = self.getSheetData()
        triggerScopes = sheetData.triggerScopes

        parts = self.partitionTriggers(triggers)

        uncovered = 0

        nParts = len(parts)
        plural = "" if nParts == 1 else "es"
        self.console(
            f"Looking up {len(triggers)} triggers "
            f"in {len(parts)} pass{plural} over the corpus ",
            newline=False,
        )

        items = []

        for part in parts:
            self.console(".", newline=False)
            inventory = self.findTriggers(part)

            for trigger, data in inventory.items():
                occs = data.get(trigger, {}).get("", [])
                items.append((trigger, occs))

        for trigger, occs in sorted(
            items,
            key=lambda x: (", ".join(sorted(triggerScopes[x[0]])), x[0].lower()),
        ):
            uncovered += 0 if self.diagnoseTrigger(trigger, occs, detail=detail) else 1

        self.console("")

        return uncovered

    def diagnoseTrigger(self, trigger, occs, detail=True):
        app = self.app
        L = app.api.L
        triggerBySlot = self.triggerBySlot
        sheetData = self.getSheetData()
        triggerScopes = sheetData.triggerScopes

        uncoveredSlots = set()
        coveredBy = {}

        for slots in occs:
            for slot in slots:
                cTrigger = triggerBySlot.get(slot, None)

                if cTrigger is None:
                    uncoveredSlots.add(slot)
                else:
                    coveredBy.setdefault(cTrigger, set()).add(slot)

        properHits = {}

        nUncoveredSlots = len(uncoveredSlots)
        ok = nUncoveredSlots == 0

        if nUncoveredSlots:
            for slot in sorted(uncoveredSlots):
                heading = app.sectionStrFromNode(L.u(slot, otype="chunk")[0])
                occ = properHits.setdefault(heading, [[]])

                if len(occ[-1]) == 0 or occ[-1][-1] + 1 == slot:
                    occ[-1].append(slot)
                else:
                    occ.append([slot])

        nMissedHits = 0
        properOccsDiag = []
        properOccsDiagCompact = []

        for heading, occs in properHits.items():
            nOccs = len(occs)
            nMissedHits += nOccs
            properOccsDiag.append(f"\t\t{heading}: {nOccs} x")
            properOccsDiagCompact.append(f"{heading} x {nOccs}")

        properOccsDiag[0:0] = [f"\tuncovered: {nMissedHits} x"]

        coveredOccsDiag = []

        for cTrigger in sorted(coveredBy, key=lambda x: x.lower()):
            thisCoveredOccsDiag = []
            coveredSlots = sorted(coveredBy[cTrigger])

            coveredHits = {}

            for slot in sorted(coveredSlots):
                heading = app.sectionStrFromNode(L.u(slot, otype="chunk")[0])
                occ = coveredHits.setdefault(heading, [[]])

                if len(occ[-1]) == 0 or occ[-1][-1] + 1 == slot:
                    occ[-1].append(slot)
                else:
                    occ.append([slot])

            nCoveredHits = 0

            for heading, occs in coveredHits.items():
                nOccs = len(occs)
                nCoveredHits += nOccs
                thisCoveredOccsDiag.append(f"\t\t{heading}: {nOccs} x")

            thisCoveredOccsDiag[0:0] = [f"\tcovered by: {cTrigger}: {nCoveredHits} x"]

            coveredOccsDiag.extend(thisCoveredOccsDiag)

        scopeRep = f"({', '.join(sorted(triggerScopes[trigger]))})"

        if detail:
            console(f"{trigger} {scopeRep}:")

            for line in properOccsDiag:
                console(line)

            for line in coveredOccsDiag:
                console(line)

        else:
            if nUncoveredSlots == 0:
                if False:
                    console(f"{trigger} {scopeRep}: covered by other triggers")
            else:
                missedHits = []

                i = 0
                for occRep in properOccsDiagCompact:
                    if i == 0:
                        missedHits.append([occRep])
                    else:
                        missedHits[-1].append(occRep)

                    i += 1
                    if i == 5:
                        i = 0

                missedHitsRep = ", ".join(missedHits[0])
                console(f"{trigger:<40} {scopeRep:<12}: {missedHitsRep}", error=True)

                for m in missedHits[1:]:
                    missedHitsRep = ", ".join(m)
                    console(f"{' ' * 55}{missedHitsRep}", error=True)

        return ok

    def interference(
        self,
        rowMap,
        triggerScopes,
        myToTokens,
        seqFromStr,
        alsoInternal=False,
        alsoExpected=False,
    ):
        triggers = list(rowMap)

        triggerTokens, parts = makePartitions(triggers, myToTokens)

        nParts = len(parts)

        interferences = []

        intersections = {}

        for i, part in enumerate(parts):
            if i == nParts - 1:
                break

            for otherPart in parts[i + 1 : nParts]:
                for triggerA in part:
                    for triggerB in otherPart:
                        tokensA = triggerTokens[triggerA]
                        tokensB = triggerTokens[triggerB]

                        if not alsoInternal:
                            rowsA = set(rowMap[triggerA])
                            rowsB = set(rowMap[triggerB])
                            if rowsA == rowsB:
                                continue

                        scopesA = ",".join(sorted(triggerScopes[triggerA]))
                        scopesB = ",".join(sorted(triggerScopes[triggerB]))
                        commonScopes = intersections.get((triggerA, triggerB), None)

                        if commonScopes is None:
                            commonScopes = self.intersectScopes(scopesA, scopesB)
                            intersections[(triggerA, triggerB)] = commonScopes

                        if len(commonScopes) == 0:
                            continue

                        common = hasCommon(tokensA, tokensB)

                        if common is None:
                            continue

                        ref, pos, length = common
                        nTokensA = len(tokensA)
                        nTokensB = len(tokensB)

                        nTokensLatter = nTokensB if ref == 1 else nTokensA

                        expected = length == nTokensLatter

                        if expected and not alsoExpected:
                            continue

                        if ref == 1:
                            nB = len(tokensB)
                            union = tokensA

                            if length < nB:
                                union += tokensB[length:]
                        else:
                            nA = len(tokensA)
                            union = tokensB

                            if length < nA:
                                union += tokensA[length:]

                        interferences.append(
                            (
                                triggerA,
                                triggerB,
                                " ".join(union),
                                scopesA,
                                scopesB,
                                commonScopes,
                            )
                        )

        parts = makePartitions([x[2] for x in interferences], myToTokens)[1]

        return interferences, parts

    def findTriggers(self, triggers):
        if not self.properlySetup:
            return []

        settings = self.settings
        spaceEscaped = settings.spaceEscaped

        setData = self.getSetData()
        getTokens = self.getTokens
        seqFromNode = self.seqFromNode

        buckets = setData.buckets or ()
        sheetData = self.getSheetData()

        caseSensitive = sheetData.caseSensitive

        idMap = {trigger: trigger for trigger in triggers}
        tMap = {trigger: "" for trigger in triggers}
        tPos = {}
        triggerSet = set()
        instructions = {(): dict(tPos=tPos, tMap=tMap, idMap=idMap)}

        for trigger in triggers:
            triggerT = toTokens(
                trigger, spaceEscaped=spaceEscaped, caseSensitive=caseSensitive
            )
            triggerSet.add(triggerT)

        for triggerT in triggerSet:
            for i, token in enumerate(triggerT):
                tPos.setdefault(i, {}).setdefault(token, set()).add(triggerT)

        inventory = occMatch(
            getTokens,
            seqFromNode,
            buckets,
            instructions,
            spaceEscaped,
            caseSensitive=caseSensitive,
        )

        return inventory

    def findTrigger(self, trigger, show=True):
        if not self.properlySetup:
            return []

        app = self.app
        L = app.api.L

        settings = self.settings
        spaceEscaped = settings.spaceEscaped

        setData = self.getSetData()
        getTokens = self.getTokens
        seqFromNode = self.seqFromNode

        buckets = setData.buckets or ()
        sheetData = self.getSheetData()

        caseSensitive = sheetData.caseSensitive

        triggerT = toTokens(
            trigger, spaceEscaped=spaceEscaped, caseSensitive=caseSensitive
        )
        idMap = {trigger: trigger}
        tMap = {trigger: ""}
        tPos = {}

        for i, token in enumerate(triggerT):
            tPos.setdefault(i, {}).setdefault(token, set()).add(triggerT)

        instructions = {(): dict(tPos=tPos, tMap=tMap, idMap=idMap)}

        inventory = occMatch(
            getTokens,
            seqFromNode,
            buckets,
            instructions,
            spaceEscaped,
            caseSensitive=caseSensitive,
        )

        occs = inventory.get(trigger, {}).get(trigger, {}).get("", [])

        if show:
            nOccs = len(occs)
            plural = "" if nOccs == 1 else "s"
            app.dm(f"**{nOccs} occurrence{plural}**\n")

            if nOccs:
                headings = set()
                highlights = set()

                for occ in occs:
                    headings.add(L.u(occ[0], otype="chunk")[0])

                    for slot in occ:
                        highlights.add(slot)

                for hd in sorted(headings):
                    app.plain(hd, highlights=highlights)
        else:
            return occs
