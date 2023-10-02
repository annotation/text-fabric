import collections

from .settings import FEATURES, NONE


def entityMatch(
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
):
    """Checks whether a bucket matches a sequence of words.

    When we do the checking, we ignore empty words in the bucket.

    Parameters
    ----------
    entitySlotVal: dict
        Dictionary from tuples of slots to sets of feature values that such
        entities can have.
    L, F, T: object
        The TF APIs `F` and `L` for feature lookup and level-switching, and text
        extraction
    b: integer
        The node of the bucket in question
    words: list of string
        The sequence of words that must be matched. They are all non-empty and stripped
        from white space.
    valSelect: string
        The entity values that the matched words should have
    """
    positions = set()

    fits = None

    if sFindRe:
        fits = False
        sText = T.text(b)

        for match in sFindRe.finditer(sText):
            positions |= set(range(match.start(), match.end()))
            fits = True

    bTokensAll = [(t, F.str.v(t)) or "" for t in L.d(b, otype="t")]
    bTokens = [x for x in bTokensAll if x[1].strip()]

    matches = []

    fValStats = {feat: collections.Counter() for feat in ("",) + FEATURES}

    if eVals is not None:
        for (i, (t, w)) in enumerate(bTokens):
            lastT = eStarts.get(t, None)
            if lastT is None:
                continue

            slots = tuple(range(t, lastT + 1))

            if requireFree is None:
                freeOK = True
            else:
                bound = any(slot in entitySlotIndex for slot in slots)
                freeOK = requireFree and not bound or not requireFree and bound

            if not freeOK:
                continue

            for feat in FEATURES:
                stats = fValStats[feat]

                for val in eVals:
                    stats[val] += 1

            valOK = True

            for (feat, val) in zip(FEATURES, eVals):
                selectedVals = valSelect[feat]
                if val not in selectedVals:
                    valOK = False
                    break

            if valOK:
                matches.append(slots)
                fValStats[""][None] += 1

    elif words is not None:
        nWords = len(words)

        if nWords:
            sWords = {w for (t, w) in bTokens}

            if any(w not in sWords for w in words):
                return (fits, fValStats, (bTokensAll, matches, positions), False)

            nSTokens = len(bTokens)

            for (i, (t, w)) in enumerate(bTokens):
                if w != words[0]:
                    continue
                if i + nWords - 1 >= nSTokens:
                    return (
                        fits,
                        fValStats,
                        (bTokensAll, matches, positions),
                        len(matches) != 0,
                    )

                match = True

                for (j, w) in enumerate(words[1:]):
                    if bTokens[i + j + 1][1] != w:
                        match = False
                        break

                if match:
                    lastT = bTokens[i + nWords - 1][0]
                    slots = tuple(range(t, lastT + 1))

                    if requireFree is None:
                        freeOK = True
                    else:
                        bound = any(slot in entitySlotIndex for slot in slots)
                        freeOK = requireFree and not bound or not requireFree and bound

                    if not freeOK:
                        continue

                    for feat in FEATURES:
                        vals = entityIndex[feat].get(slots, set())
                        stats = fValStats[feat]

                        if len(vals) == 0:
                            stats[NONE] += 1
                        else:
                            for val in vals:
                                stats[val] += 1

                    valTuples = entitySlotVal.get(slots, set())

                    if len(valTuples):
                        valOK = False

                        for valTuple in valTuples:
                            thisOK = True

                            for (feat, val) in zip(FEATURES, valTuple):
                                selectedVals = valSelect[feat]
                                if val not in selectedVals:
                                    thisOK = False
                                    break

                            if thisOK:
                                valOK = True
                                break
                    else:
                        valOK = all(NONE in valSelect[feat] for feat in FEATURES)

                    if valOK:
                        matches.append(slots)
                        fValStats[""][None] += 1

    else:
        return (None, fValStats, (bTokensAll, matches, positions), True)

    return (fits, fValStats, (bTokensAll, matches, positions), len(matches) != 0)
