"""Management of triggers in NER spreadsheets.

Triggers in NER spreadsheets may have unexpected interactions with each other, and
with the scopes in which they are defined.

When NER sheets grow large, we need extra tooling to diagnose these interactions,
so that the user gets the proper feedback on for improving the sheet.
"""

import collections
from textwrap import dedent

from ..core.files import fileOpen
from ..core.helpers import console

from .helpers import toTokens
from .match import occMatch
from .scopes import locInScope


def hasCommon(tokensA, tokensB):
    """Whether one sequence of tokens interferes with another.

    The idea is: we want to determine whether matches for `tokensA` may interfere
    with matches for `tokensB`.

    This happens if `tokensB` is a sublist of `tokensA`, or if an initial segment of
    `tokensB` coincides with a final segment of `tokensA`.

    Or the same with `tokensA` and `tokensB` reversed.

    **Proposition:** *`tokensA` en `tokensB` have something in common (in the above sense)
    if and only if you can make a text where `tokensA` and `tokensB` have overlapping
    matches.*

    $$Proof**:

    (direction `=>`)

    Suppose `tokensA` and `tokensB` have something in common.

    Let `i`, `j` be the start-end position of the (part of) `tokensB` that occur in
    `tokensA`.  Construct a match for the combination of `tokensA` and
    `tokensB` as follows:

    ```
    tokensA[0:i] + tokensA[i:j] + xxx
    ```

    Two cases:

    1.  `tokensB` is fully contained in `tokensA`.
        Then take for `xxx`: `tokensA[j:]`.
        The result is a match for `tokensA` and hence for `tokensB`.
    2.  `tokensB` is only contained in `tokensA` up to index `k`. By definition
        of common, this means that `tokensB[0:k]` is equal to `tokensA[-k:]` and hence
        that `j == len(tokensA)`.
        Then take for `xxx`: `tokensB[k:]`.

        We then have:

        ```
        tokensA + tokensB[k:] =
        tokensA[0:i] + tokensA[i:] + tokensB[k:]
        tokensA[0:i] + tokensA[i:j] + tokensB[k:] =
        ```

        because `j == len(tokensA)` :

        ```
        tokensA[0:i] + tokensA[i:j] + tokensB[k:] =
        tokensA[0:i] + tokensB[0:k] + tokensB[k:] =
        tokensA[0:i] + tokensB
        ```

        So, this text is a match for `tokensA` and for `tokensB`

        (direction `<=`)

        Suppose we have a text `T` with an overlapping match for `tokensA` and
        `tokensB`.

        Suppose `T[i:j]` is a match for `tokensA` and `T[n:m]` is a match for
        `tokensB`, and `T[i:j]` and `T[m:n]` overlap.

        Two cases:

        1.  one match is contained in the other. We consider `T[m:n]` is
            contained in `T[i:j]`. For the reverse case, the argument is the same
            with `tokensA` and `tokensB` interchanged.

            `T[m:n]` is part of a match of `tokensA`, so `T[m:n]` occurs in `tokensA`.
            `T[m:n]` is also a match for `tokensB`, so `tokensB == T[m:n]`, so `tokensB`
            is a part of `tokensA`, hence, by definition: `tokensA` and `tokensB`
            have something in common.
        2.  the two matches have a region in common, but none is contained in the
            other.
            We consider the case where m is between i and j. The case where i is
            between m and n is analogous, with `tokensA` and `tokensB` interchanged.

            Now `T[m:j]` is part of a match for `tokensA` and for `tokensB`.
            Then `T[m:j]` is at the end of `T[i:j]`, so an initial part of
            `tokensB` is a final part of `tokensA`.

    Parameters
    ----------
    tokensA: iterable of string
        first operand
    tokensB: iterable of string
        second operand

    Returns
    -------
    tuple of integer
        We return a result consisting of 3 integers: `ref`, `pos`, `length`

        `ref`: 0 if the two operands are identical; 1 if the first operand
        properly contains the second one or if the second one starts somewhere
        in the first one; -1 otherwise.

        `pos`: the position in the one operand where the other starts.

        `length`: the length of the common part of the two operands.
    """
    nA = len(tokensA)
    nB = len(tokensB)

    if tokensA == tokensB:
        return (0, 0, nA)

    for i in range(nA - 1, -1, -1):
        end = min((nB, nA - i))

        if tokensA[i : i + end] == tokensB[0:end]:
            ref = 1 if i > 0 else 1 if nA >= nB else -1
            return (ref, i, end)

    for i in range(nB - 1, -1, -1):
        end = min((nA, nB - i))

        if tokensB[i : i + end] == tokensA[0:end]:
            ref = -1 if i > 0 else -1 if nB >= nA else 1
            return (ref, i, end)

    return None


def testCommon():
    """Test suite for testing the `hasCommon()` function."""

    tokensA = list("abcd")
    tokensB = list("cdef")
    tokensC = list("defg")
    tokensD = list("bc")
    tokensE = list("ab")
    tokensF = list("cd")
    tokensG = list("a")
    assert hasCommon(tokensA, tokensA) == (0, 0, 4), hasCommon(tokensA, tokensA)
    assert hasCommon(tokensA, tokensB) == (1, 2, 2), hasCommon(tokensA, tokensB)
    assert hasCommon(tokensB, tokensA) == (-1, 2, 2), hasCommon(tokensB, tokensA)
    assert hasCommon(tokensA, tokensC) == (1, 3, 1), hasCommon(tokensA, tokensC)
    assert hasCommon(tokensC, tokensA) == (-1, 3, 1), hasCommon(tokensC, tokensA)
    assert hasCommon(tokensA, tokensD) == (1, 1, 2), hasCommon(tokensA, tokensD)
    assert hasCommon(tokensD, tokensA) == (-1, 1, 2), hasCommon(tokensD, tokensA)
    assert hasCommon(tokensA, tokensE) == (1, 0, 2), hasCommon(tokensA, tokensE)
    assert hasCommon(tokensE, tokensA) == (-1, 0, 2), hasCommon(tokensE, tokensA)
    assert hasCommon(tokensA, tokensF) == (1, 2, 2), hasCommon(tokensA, tokensF)
    assert hasCommon(tokensF, tokensA) == (-1, 2, 2), hasCommon(tokensF, tokensA)
    assert hasCommon(tokensE, tokensG) == (1, 0, 1), hasCommon(tokensE, tokensG)
    assert hasCommon(tokensG, tokensE) == (-1, 0, 1), hasCommon(tokensG, tokensE)

    tokensA = list("abcd")
    tokensB = list("cef")
    tokensC = list("efg")
    tokensD = list("bd")
    tokensE = list("ac")
    tokensF = list("ad")

    assert hasCommon(tokensA, tokensB) is None, hasCommon(tokensA, tokensB)
    assert hasCommon(tokensB, tokensA) is None, hasCommon(tokensB, tokensA)
    assert hasCommon(tokensA, tokensC) is None, hasCommon(tokensA, tokensC)
    assert hasCommon(tokensC, tokensA) is None, hasCommon(tokensC, tokensA)
    assert hasCommon(tokensA, tokensD) is None, hasCommon(tokensA, tokensD)
    assert hasCommon(tokensD, tokensA) is None, hasCommon(tokensD, tokensA)
    assert hasCommon(tokensA, tokensE) is None, hasCommon(tokensA, tokensE)
    assert hasCommon(tokensE, tokensA) is None, hasCommon(tokensE, tokensA)
    assert hasCommon(tokensA, tokensF) is None, hasCommon(tokensA, tokensF)
    assert hasCommon(tokensF, tokensA) is None, hasCommon(tokensF, tokensA)


def makePartition(triggers, myToTokens):
    """Partition a set of triggers into groups of pairwise non-interfering triggers.

    The intention is to explore all triggers that apparently do not have hits.
    We need to look them up in isolation, because then they might have hits on
    their own that are overshadowed by other triggers.

    But searching per trigger is expensive. We want to group triggers together
    that can not interact with each other.
    A hit of one trigger can then never be part of a hit of any other trigger
    in the group.

    "Not being able to interact" is captured by the function `hasCommon()`.

    Parameters
    ----------
    triggers: iterable of string
        The triggers that must be partitioned
    myToTokens: function
        Takes a trigger (string) and produces a sequence of tokens.
        Here you can pass a function that corresponds to how the strings in the corpus
        are divided up into tokens.

    Returns
    -------
    tuple
        The first member is a dict, mapping triggers to sequences of the tokens of which
        they consist;

        the second member is the partition itself, which is a list of parts, where each
        part is a list of triggers that do not have conflicting pairs of triggers.
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
        """Wrapper around the partitioning function.

        This function calls `tf.ner.triggers.makePartition()` with the corpus
        dependent parameter for turning strings into tokens.

        Parameters
        ----------
        triggers: iterable of string
            A sequence of triggers.

        Returns
        -------
        tuple
            The same as what `tf.ner.triggers.makePartition()` returns.
        """
        return makePartition(triggers, self.getToTokensFunc())[1]

    def findOccs(self):
        """Finds the occurrences of multiple triggers.

        This is meant to efficiently list all occurrences of many token
        sequences in the corpus.

        The triggers are in member `instructions`, which must first
        be constructed by reading a number of excel files.

        It adds the member `inventory` to the object, which is a dict
        with subdicts:

        `occurrences`: keyed by tuples (eid, kind), the values are
        the occurrences of that entity in the corpus.
        A single occurrence is represented as a tuple of slots.

        `names`: keyed by tuples (eid, kind) and then path,
        the value is the name of that entity in the context indicated by path.

        """
        if not self.properlySetup:
            return

        settings = self.settings
        spaceEscaped = settings.spaceEscaped

        setData = self.getSetData()
        tokensFromNode = self.tokensFromNode
        getSeqFromNode = self.getSeqFromNode

        buckets = setData.buckets or ()
        sheetData = self.getSheetData()
        caseSensitive = sheetData.caseSensitive
        instructions = sheetData.instructions

        sheetData.inventory = occMatch(
            tokensFromNode,
            getSeqFromNode,
            buckets,
            instructions,
            spaceEscaped,
            caseSensitive=caseSensitive,
        )

    def reportHits(self, silent=None, showNoHits=False):
        """Reports the inventory.

        It diagnoses all triggers by means of `diagnoseTriggers()`.

        Parameters
        ----------
        silent: boolean, optional None
            Whether to be silent. If None, it is taken from the corresponding member
            of the instance.
        showNoHits: boolean, optional False
            Whether to show which triggers do not have hits.
        """
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
        `m1` of trigger `t1` and a match `m2` of trigger `t2` such that `m1` and
        `m2` intersect (see `tf.ner.triggers.hasCommon()`.

        Triggers may interfere *potentially*: if the triggers have something in
        common they can have overlapping matches. But it does not mean that
        the corpus contains these overlapping matches, i.e. that the triggers conflict
        *actually*.

        We report the *actually* interfering triggers only.

        Triggers within one row are associated to the same entity and work in the same
        row. It is not bad if they are interfering with each other. If there
        are overlapping matches, the trigger that wins still flags the same entity.
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
        if not self.properlySetup:
            return

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
            self.getSeqFromStr,
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

                    if not locInScope(heading, commonScopes):
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

    def diagnoseTriggers(self, triggers, detail=False):
        """Diagnose triggers individually.

        !!! Caution
            This method will be called by `reportHits()` and should not be called
            on its own, since it expects the instance member `triggerBySlot` which
            is constructed by `reportHits()`

        Here we have a closer look to each trigger individually, not focussing on the
        interaction with other triggers.

        The triggers will be partitioned and each part of the partition will be looked
        up in a separate pass over the corpus.

        Parameters
        ----------
        triggers: iterable of string
            The triggers that must be diagnosed.
        detail: boolean, optional False
            If True, produces more detail per trigger, see `diagnoseTrigger()`

        Returns
        -------
        int
            The number of triggers with uncovered occurrences, see `diagnoseTrigger()`
        """
        if not self.properlySetup:
            return None

        sheetData = self.getSheetData()
        triggerScopes = sheetData.triggerScopes

        parts = self.partitionTriggers(triggers)

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

        uncovered = 0

        for trigger, occs in sorted(
            items,
            key=lambda x: (", ".join(sorted(triggerScopes[x[0]])), x[0].lower()),
        ):
            uncovered += 0 if self.diagnoseTrigger(trigger, occs, detail=detail) else 1

        self.console("")

        return uncovered

    def diagnoseTrigger(self, trigger, occs, detail=False):
        """Diagnoses an individual trigger.

        !!! Caution
            This method will be called by `diagnoseTriggers()` and should not be called
            on its own, since it expects the instance member `triggerBySlot` which
            is constructed by `reportHits()`, which calls `diagnoseTriggers()`.

        All occurrences of the trigger will be checked: is every slot in such
        an occurrence part of a match according to the original spreadsheet?

        If not so, we check whether it is a match of the trigger in question, or of
        another trigger.

        In this way we can detect where the potential but unrealized matches are.

        If there are matches of the trigger in isolation that contain slots that are
        not part of any match of any trigger in the original search, we say that
        the trigger has uncovered occurrences. It will be returned as the result of this
        function whether this is the case.

        These uncovered occurrences are reported as missing hits.

        It can also be the case that the trigger in isolation has matches that
        are completely covered by matches of other triggers in the original search.
        We can also list these, but since these are probably intentional, we suppress
        these cases unless `detail=True` is passed.

        Parameters
        ----------
        trigger: string
            The trigger to be diagnosed.
        occs: iterable of tuple of integer
            The occurrences of this trigger in the whole corpus, irrespective of scope;
        detail: boolean, optional False
            If True, produces complete diagnostics.
            Otherwise, only produces output if there are missed hits.

        Returns
        -------
        boolean
            Whether there are uncovered occurrences.
        """
        if not self.properlySetup:
            return None

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

        uncoveredOccs = {}

        nUncoveredSlots = len(uncoveredSlots)
        ok = nUncoveredSlots == 0

        if nUncoveredSlots:
            for slot in sorted(uncoveredSlots):
                heading = app.sectionStrFromNode(L.u(slot, otype="chunk")[0])
                occ = uncoveredOccs.setdefault(heading, [[]])

                if len(occ[-1]) == 0 or occ[-1][-1] + 1 == slot:
                    occ[-1].append(slot)
                else:
                    occ.append([slot])

        nMissedHits = 0
        uncoveredOccsDiag = []
        uncoveredOccsDiagCompact = []

        for heading, occs in uncoveredOccs.items():
            nOccs = len(occs)
            nMissedHits += nOccs
            uncoveredOccsDiag.append(f"\t\t{heading}: {nOccs} x")
            uncoveredOccsDiagCompact.append(f"{heading} x {nOccs}")

        uncoveredOccsDiag[0:0] = [f"\tuncovered: {nMissedHits} x"]

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

            for line in uncoveredOccsDiag:
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
                for occRep in uncoveredOccsDiagCompact:
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
        getSeqFromStr,
        alsoInternal=False,
        alsoExpected=False,
    ):
        """Workhorse to calculate interference of triggers.

        This function is used by method `triggerInterference()` for calculating the
        *potential* interferences within a set of triggers, irrespective whether
        the corpus contains instances of these interferences.

        When two triggers interfere, you can build a combined trigger out of them
        whose matches are exactly the points of interference. We call this the
        *combined* trigger of the interference.

        Parameters
        ----------
        rowMap: dict
            mapping from triggers to the rows where they occur in the spreadsheet.
            We take the set of triggers from here, so that we can issue proper
            diagnostic information later, i.e. we can mentoin the row in the spreadsheet
            where the offending triggers are.
        triggerScopes: dict
            mapping from triggers to the scopes for which they are defined.
        myToTokens: function
            corpus dependent function for parsing a trigger, which is a string,
            to tokens, in the same way as the text of the corpus is parsed into tokens.
        getSeqfromStr: function
            corpus dependent function that can translate a section heading into a
            tuple of integers that represents the same heading in the "legal" numbering
            system.
        alsoInternal: boolean, optional False
            Whether to report interfering triggers even if they belong to the
            same entity
        alsoExpected: boolean, optional False
            Whether to report interfering triggers even if one is a proper
            initial part of the other.

        Returns
        -------
        tuple
            There are two parts:

            *interferences*: a list of interfering pairs of triggers, where each
            interference has these components:

            *   *triggerA* the first trigger in the pair;
            *   *triggerB* the second trigger in the pair;
            *   *triggerC* the combined trigger of the interference;
            *   *scopeRepA* the scope of the first trigger;
            *   *scopeRepB* the scope of the second trigger;
            *   *commonScopes* the intersection of the scopes of both triggers.

            *parts*: a partition of the combined triggers of all interferences so that
            within each part none of these interfere.
        """
        if not self.properlySetup:
            return (None, None)

        triggers = list(rowMap)

        triggerTokens, parts = makePartition(triggers, myToTokens)

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

        parts = makePartition([x[2] for x in interferences], myToTokens)[1]

        return interferences, parts

    def findTriggers(self, triggers):
        """Looks up occurrences of multiple triggers efficiently.

        This is a lot like `findOccs()`, but where as `findOccs()` finds
        its search instructions in the sheet data and stores its search results in the
        sheet data, this function makes its own instructions and returns the search
        results.

        We use this function when we need to investigate what triggers do in isolation
        and without scope restrictions.

        So, the instructions generated by this functions are derived from the
        spreadsheet, but ignore all scope restrictions.

        Parameters
        ----------
        triggers: iterable of string
            These are the triggers to be looked up. Typically they come from one
            part of a partition of triggers, but not necessarily so.

        Returns
        -------
        dict
            The inventory of occurrences of the triggers, as returned by
            `tf.ner.match.occMatch()`.
        """
        if not self.properlySetup:
            return {}

        settings = self.settings
        spaceEscaped = settings.spaceEscaped

        setData = self.getSetData()
        tokensFromNode = self.tokensFromNode
        getSeqFromNode = self.getSeqFromNode

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
            tokensFromNode,
            getSeqFromNode,
            buckets,
            instructions,
            spaceEscaped,
            caseSensitive=caseSensitive,
        )

        return inventory

    def findTrigger(self, trigger, show=True):
        """Looks up occurrences of a single triggers.

        This is a lot like `findTriggers()`, but where as `findTriggers()` looks up
        multiple triggers, this one looks up a single trigger.

        Like `findTriggers()` the search is done without scope restrictions.

        We use this function when we need to investigate what a single trigger
        does in isolation and without scope restrictions.

        So, the instructions generated by this functions are derived from the
        spreadsheet, but ignore all scope restrictions.

        Parameters
        ----------
        trigger: string
            This is the trigger to be looked up.
        show: boolean, optional True
            If True, it shows the result on the console, otherwise it returns
            the result.

        Returns
        -------
        list or void
            The list of occurrences of the trigger, provided `show=False` is passed,
            else there is no function result.
        """
        if not self.properlySetup:
            return []

        app = self.app
        L = app.api.L

        settings = self.settings
        spaceEscaped = settings.spaceEscaped

        setData = self.getSetData()
        tokensFromNode = self.tokensFromNode
        getSeqFromNode = self.getSeqFromNode

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
            tokensFromNode,
            getSeqFromNode,
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
