"""Module to compose tables of result data.
"""

import collections
from itertools import chain

from .settings import FEATURES, NONE, BUCKET_TYPE, TOOLKEY
from .html import H
from .wrap import repIdent


def composeE(web, templateData):
    """Compose a table of entities with selection and sort controls.

    Parameters
    ----------
    web: object
        The web app object
    sortKey: string
        Indicates how to sort the table:

        *   `freqsort`: by the frequency of the entities
        *   `sort_{i}`: by the i-th additional feature of the entities

    sortDir: string
        Indicates the direction of the sort:

        *   `u`: up, i.e. ascending
        *   `d`: down, i.e. descending

    Returns
    -------
    html string
        The finished HTML of the table, ready to put into the Flask template.
    """

    setData = web.toolData[TOOLKEY].sets[web.annoSet]
    activeEntity = templateData.activeentity
    sortKey = templateData.sortkey
    sortDir = templateData.sortdir

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

    templateData.entitytable = H.join(content)


def composeS(web, templateData, buckets, asHtml=False):
    """Compose a table of buckets.

    In that case, we look up the text between those tokens and including.
    All buckets that contain that text of those slots will show up,
    all other buckets will be left out.
    The matching slots will be highlighted.

    Parameters
    ----------
    web: object
        The web app object

    Returns
    -------
    html string
        The finished HTML of the table, ready to put into the Flask template.
    """

    annoSet = web.annoSet
    setData = web.toolData[TOOLKEY].sets[annoSet]

    kernelApi = web.kernelApi
    app = kernelApi.app
    api = app.api
    F = api.F

    entityIdent = setData.entityIdent
    eFirst = setData.entityIdentFirst
    entitySlotIndex = setData.entitySlotIndex

    activeEntity = templateData.activeentity
    tokenStart = templateData.tokenstart
    tokenEnd = templateData.tokenend
    hasOcc = tokenStart and tokenEnd
    hasEnt = activeEntity is not None

    limited = not (hasOcc or hasEnt)
    excludedTokens = templateData.excludedtokens

    content = []

    if not asHtml:
        content.append(
            H.input(
                type="hidden",
                name="excludedtokens",
                id="excludedtokens",
                value=",".join(str(t) for t in excludedTokens),
            )
        )

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
            H.span(app.sectionStrFromNode(b), node=b, cls="bh", title="show context")
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

            hlClasses = (" found " if found else "") + (" queried " if queried else "")
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
                        subContent.append(H.span(H.span(abs(lg), cls="lge"), cls="ee"))

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

    templateData.buckets = H.join(content)
    if asHtml:
        return templateData.buckets


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


def filterS(web, templateData, noFind=False, node=None):
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
    web: object
        The web app object

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
    setData = web.toolData[TOOLKEY].sets[web.annoSet]
    entities = setData.entities

    kernelApi = web.kernelApi
    app = kernelApi.app
    api = app.api
    L = api.L
    F = api.F
    T = api.T

    sFindRe = None if noFind else templateData.sfindre
    activeEntity = templateData.activeentity
    tokenStart = templateData.tokenstart
    tokenEnd = templateData.tokenend
    valSelect = templateData.valselect
    freeState = templateData.freestate

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
