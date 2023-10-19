from .settings import NONE


def occMatch(L, F, b, qTokenSet, results):
    bTokensAll = [(t, F.str.v(t)) or "" for t in L.d(b, otype="t")]
    bTokens = [x for x in bTokensAll if x[1].strip()]
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
    L,
    F,
    T,
    b,
    bFindRe,
    anyEnt,
    eVals,
    qTokens,
    valSelect,
    requireFree,
    fValStats,
):
    """Checks whether a bucket matches a sequence of tokens.

    When we do the checking, we ignore empty tokens in the bucket.

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
    anyEnt: boolean or None
        If `None`: no effect
        If True: overrides qTokens and eVals: looks for any entity annotation
        If False: lets the bucket through only if it has no annotations.
    qTokens: list of string
        The sequence of tokens that must be matched. They are all non-empty and stripped
        from white space.
    valSelect: string
        The entity values that the matched tokens should have
    """
    positions = set()

    fits = None

    if bFindRe:
        fits = False
        sText = T.text(b)

        for match in bFindRe.finditer(sText):
            positions |= set(range(match.start(), match.end()))
            fits = True

    bTokensAll = [(t, F.str.v(t)) or "" for t in L.d(b, otype="t")]
    bTokens = [x for x in bTokensAll if x[1].strip()]

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

            if requireFree is None:
                freeOK = True
            else:
                bound = any(slot in entitySlotIndex for slot in slots)
                freeOK = requireFree and not bound or not requireFree and bound

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

                    if requireFree is None:
                        freeOK = True
                    else:
                        bound = any(slot in entitySlotIndex for slot in slots)
                        freeOK = requireFree and not bound or not requireFree and bound

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
                                    if valSelect is None:
                                        continue
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
