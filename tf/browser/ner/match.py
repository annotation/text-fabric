"""Match functions.

To see how this fits among all the modules of this package, see
`tf.browser.ner.annotate` .
"""

from .settings import NONE


def occMatch(getTokens, b, qTokenSet, results):
    """Finds the occurrences of multiple sequences of tokens in a single bucket.

    Parameters
    ----------
    getTokens: function
        See `tf.browser.ner.corpus.Corpus.getTokens`
    b: integer
        The node of the bucket in question
    qTokenSet: set, optional set()
        A set of sequences of tokens. Each sequence in the set will be used as a
        search pattern, and it occurrences in the bucket are collected.
    result: dict
        A dictionary to collect the results in.
        Keyed by each member of parameter `qTokenSet` the values are
        the occurrences of that member in the corpus.
        A single occurrence is represented as a tuple of slots.
    """
    bTokensAll = getTokens(b)
    bTokens = [x for x in bTokensAll if (x[1] or '').strip()]
    bStrings = {s for (t, s) in bTokens}
    nBTokens = len(bTokens)

    for qTokens in qTokenSet:
        if any(s not in bStrings for s in qTokens):
            continue

        nTokens = len(qTokens)

        for i, (t, w) in enumerate(bTokens):
            if w != qTokens[0]:
                continue
            if i + nTokens - 1 >= nBTokens:
                break

            match = True

            for j, w in enumerate(qTokens[1:]):
                if bTokens[i + j + 1][1] != w:
                    match = False
                    break

            if match:
                lastT = bTokens[i + nTokens - 1][0]
                slots = tuple(range(t, lastT + 1))

                results.setdefault(qTokens, []).append(slots)


def entityMatch(
    entityIndex,
    eStarts,
    entitySlotVal,
    entitySlotAll,
    entitySlotIndex,
    getTextR,
    getTokens,
    b,
    bFindRe,
    anyEnt,
    eVals,
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
        Various kinds of processed entity data, see `tf.browser.ner.data`
    getTextR: function
        See `tf.browser.ner.corpus.Corpus.getTextR`
    getTokens: function
        See `tf.browser.ner.corpus.Corpus.getTokens`
    b: integer
        The node of the bucket in question
    bFindRe, anyEnt, eVals, qTokens, valSelect, freeState: object
        As in `tf.browser.ner.annotate.Annotate.filterContent`

    Returns
    -------
    tuple
        Members:

        *   `fits`: boolean, whether the bucket passes the filter
        *   `(tokens, matches, positions)`:
            *   `tokens` all tokens of the bucket, each token is a tuple consisting
                of its slot number (position) and string value;
            *   `matches`: a list of the positions of the found occurrences for the
                `qTokens` and / or `eVals` in the bucket;
            *   `positions`: a set of positions in the bucket where the
                `bFindRe` starts to match;

    """
    positions = set()

    fits = None

    if bFindRe:
        fits = False
        sText = getTextR(b)

        for match in bFindRe.finditer(sText):
            positions |= set(range(match.start(), match.end()))
            fits = True

    bTokensAll = getTokens(b)
    bTokens = [x for x in bTokensAll if (x[1] or "").strip()]

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
