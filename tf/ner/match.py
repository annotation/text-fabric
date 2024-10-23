"""Match functions.

In this module we define an efficient search for multiple strings in one pass
over the corpus.
We also define a search for a single entity.

All corpus-specific functions that we need must be passed as arguments.
And the portions of the corpus in which we search must be given by a set of nodes.
"""

from .settings import NONE
from .scopes import getIntvIndex
from .helpers import fromTokens, xstrip


def occMatch(
    tokensFromNode,
    getSeqFromNode,
    buckets,
    instructions,
    spaceEscaped,
    caseSensitive=False,
):
    """Finds the occurrences of multiple sequences of tokens in a single bucket.

    Parameters
    ----------
    tokensFromNode: function
        See `tf.ner.corpus.Corpus.tokensFromNode`
    getSeqFromNode: function
        See `tf.ner.corpus.Corpus.getSeqFromNode`
    buckets: tuple of integer
        The bucket nodes in question
    instructions: dict, optional None
        Datastructure that encodes the trigger information in a spreadsheet.
        The structure is described in `tf.ner.sheets.SHEET_KEYS`.
    spaceEscaped: boolean
        A corpus property indicating whether tokens in the corpus may contain
        escaped spaces

    Returns
    -------
    dict
        A multiply nested dict, first keyed by entity identifier/kind tuples,
        then by its triggers then by the scope of such a trigger, and then
        the value is a list of occurrences, where each occurrence is a tuple of slots.

    """

    # compile the token sequences that we search for into data to optimize search
    # we produce dicts, keyed by a postion number and valued by a dict whose
    # keys are tokens and whose values are the token sequences that have that token
    # at that position

    LONGEST_ONLY = True

    # We can switch between two behaviours:
    #
    # 1. once a match is found, stop looking for smaller matches that start at the same place
    #    of that match, or somewhere inside that match
    #
    # 2. find all matches, irrespective of overlap

    results = {}

    intvIndex = getIntvIndex(buckets, instructions, getSeqFromNode)

    for b in buckets:
        intv = intvIndex[b]
        data = instructions[intv]

        tPos = data["tPos"]
        tMap = data["tMap"]
        idMap = data["idMap"]

        # compile the bucket into logical tokens
        (lineEnds, bTokensAll) = tokensFromNode(b, lineBoundaries=True)
        # bTokensAll = tokensFromNode(b, lineBoundaries=False)
        bTokens = [x for x in bTokensAll if xstrip(x[1] or "")]
        bStrings = []
        bStringFirst = {}
        bStringLast = {}

        for t, s in bTokens:
            # if len(bStrings) > 1 and bStrings[-1] == "-":
            if t - 1 in lineEnds and len(bStrings) > 1 and bStrings[-1] == "-":
                bStrings.pop()
                bStrings[-1] += s
                bStringLast[len(bStrings) - 1] = t
            else:
                bStrings.append(s)
                bStringFirst[len(bStrings) - 1] = t
                bStringLast[len(bStrings) - 1] = t

        bStrings = tuple(bStrings)

        if not caseSensitive:
            bStrings = tuple(t.lower() for t in bStrings)

        nBStrings = len(bStrings)

        # perform the search
        i = 0

        while i < nBStrings:
            j = 0

            candidateMatches = None
            matches = {}

            while i + j < nBStrings:
                k = i + j
                sj = bStrings[k]
                newCandidates = tPos.get(j, {}).get(sj, set())

                if candidateMatches is None:
                    candidateMatches = newCandidates
                else:
                    candidateMatches = candidateMatches & newCandidates

                matches[j] = [qt for qt in candidateMatches if len(qt) == j + 1]
                j += 1

                if len(candidateMatches) == 0:
                    break

            for m in range(j - 1, -1, -1):
                resultMatches = matches[m]

                if len(resultMatches):
                    resultMatch = resultMatches[0]

                    trigger = fromTokens(resultMatch, spaceEscaped=spaceEscaped)
                    scope = tMap[trigger]

                    firstT = bStringFirst[i]
                    lastT = bStringLast[i + m]
                    slots = tuple(range(firstT, lastT + 1))
                    eidkind = idMap[trigger]

                    dest = (
                        results.setdefault(eidkind, {})
                        .setdefault(trigger, {})
                        .setdefault(scope, [])
                    )
                    dest.append(slots)

                    if LONGEST_ONLY:
                        break

            i += m + 1 if LONGEST_ONLY else 1

    return results


def entityMatch(
    entityIndex,
    eStarts,
    entitySlotVal,
    entitySlotAll,
    entitySlotIndex,
    triggerFromMatch,
    textFromNode,
    tokensFromNode,
    b,
    bFindRe,
    anyEnt,
    eVals,
    trigger,
    qTokens,
    valSelect,
    freeState,
    fValStats,
):
    """Checks whether a bucket satisfies a variety of criteria.

    When we do the checking, we ignore empty tokens in the bucket.

    Parameters
    ----------
    entityIndex, eStarts, entitySlotVal, entitySlotAll, entitySlotIndex: object
        Various kinds of processed entity data, see `tf.ner.data.Data.processSet()`
    triggerFromMatch: dict
        Mapping from matches to triggers, part of sheet data,
        see `tf.ner.sheets.SHEET_KEYS`
    textFromNode: function
        See `tf.ner.corpus.Corpus.textFromNode`
    tokensFromNode: function
        See `tf.ner.corpus.Corpus.tokensFromNode`
    b: integer
        The node of the bucket in question
    bFindRe, anyEnt, eVals, trigger, qTokens, valSelect, freeState: object
        As in `tf.ner.corpus.Corpus.filterContent`
    fValStats: dict
        Dictionary to collect statistics of entities that are encountered;
        this is a result of the function!

    Returns
    -------
    tuple
        Members:

        *   `fits`: boolean, whether the bucket passes the filter
        *   `(tokens, matches, positions)`:
            *   `tokens` all tokens of the bucket, each token is a tuple consisting
                of its slot number (position) and string value;
            *   `matches`: a list of the positions of the found occurrences for the
                `qTokens` and / or `eVals` possibly with `trigger` in the bucket;
            *   `positions`: a set of positions in the bucket where the
                `bFindRe` starts to match;

    """
    positions = set()

    fits = None

    if bFindRe:
        fits = False
        sText = textFromNode(b)

        for match in bFindRe.finditer(sText):
            positions |= set(range(match.start(), match.end()))
            fits = True

    bTokensAll = tokensFromNode(b)
    bTokens = [x for x in bTokensAll if xstrip(x[1] or "")]

    if fits is None or fits:
        if anyEnt is not None:
            containsEntities = False

            for i, (t, w) in enumerate(bTokens):
                if t in entitySlotAll:
                    containsEntities = True
                    break

            fits = anyEnt and containsEntities or not anyEnt and not containsEntities

    matches = []

    if eVals is not None:
        for i, (t, w) in enumerate(bTokens):
            lastT = eStarts.get(t, None)
            if lastT is None:
                continue

            slots = tuple(range(t, lastT + 1))

            if freeState is None:
                freeOK = True
            else:
                bound = any(slot in entitySlotIndex for slot in slots)
                freeOK = freeState and not bound or not freeState and bound

            if not freeOK:
                continue

            for feat, stats in fValStats.items():
                for val in eVals:
                    stats[val] += 1

            valOK = True

            for feat, val in zip(fValStats, eVals):
                if valSelect is None:
                    continue
                selectedVals = valSelect[feat]
                if val not in selectedVals:
                    valOK = False
                    break

            if valOK:
                matches.append(slots)

        if trigger is not None:
            triggerMatches = [
                slots
                for slots in matches
                if triggerFromMatch.get(slots, None) == trigger
            ]

            if len(triggerMatches) == 0:
                matches = []

    elif qTokens is not None:
        nTokens = len(qTokens)

        if nTokens:
            bStrings = {s for (t, s) in bTokens}

            if any(s not in bStrings for s in qTokens):
                return (fits, (bTokensAll, matches, positions))

            nBTokens = len(bTokens)

            for i, (t, w) in enumerate(bTokens):
                if w != qTokens[0]:
                    continue
                if i + nTokens - 1 >= nBTokens:
                    return (fits, (bTokensAll, matches, positions))

                match = True

                for j, w in enumerate(qTokens[1:]):
                    if bTokens[i + j + 1][1] != w:
                        match = False
                        break

                if match:
                    lastT = bTokens[i + nTokens - 1][0]
                    slots = tuple(range(t, lastT + 1))

                    if freeState is None:
                        freeOK = True
                    else:
                        bound = any(slot in entitySlotIndex for slot in slots)
                        freeOK = freeState and not bound or not freeState and bound

                    if not freeOK:
                        continue

                    for feat, stats in fValStats.items():
                        vals = entityIndex[feat].get(slots, set())

                        if len(vals) == 0:
                            stats[NONE] += 1
                        else:
                            for val in vals:
                                stats[val] += 1

                    valTuples = entitySlotVal.get(slots, set())

                    if len(valTuples):
                        valOK = False

                        if valSelect is not None:
                            for valTuple in valTuples:
                                thisOK = True

                                for feat, val in zip(fValStats, valTuple):
                                    selectedVals = valSelect[feat]
                                    if val not in selectedVals:
                                        thisOK = False
                                        break

                                if thisOK:
                                    valOK = True
                                    break
                    else:
                        valOK = valSelect is None or all(
                            NONE in valSelect[feat] for feat in fValStats
                        )

                    if valOK:
                        matches.append(slots)

    else:
        return (fits, (bTokensAll, matches, positions))

    return (fits, (bTokensAll, matches, positions))
