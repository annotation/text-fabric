"""Module to compose tables of result data.
"""

import collections
from itertools import chain
from textwrap import dedent

from .kernel import FEATURES, KEYWORD_FEATURES, mergeEntities, weedEntities, WHITE_RE


def repIdent(vals):
    return " ".join(
        f"""<span class="{feat}">{val}</span>"""
        for (feat, val) in zip(FEATURES[1:], vals)
    )


def composeE(web, activeEntity, activeKind, sortKey, sortDir):
    """Compose a table of entities with selection and sort controls.

    Parameters
    ----------
    web: object
        The web app object
    sortKey: string
        Indicates how to sort the table:

        *   `freqsort`: by the frequency of the entities
        *   `textsort`: by the text of the entities
        *   `idsort`: by the kind of the entities
        *   `kindsort`: by the kind of the entities

    sortDir: string
        Indicates the direction of the sort:

        *   `u`: up, i.e. ascending
        *   `d`: down, i.e. descending

    Returns
    -------
    html string
        The finished HTML of the table, ready to put into the Flask template.
    """

    setData = web.toolData.ner.sets[web.annoSet]

    html = []

    entities = setData.entities
    entries = setData.entityBy.items()

    if sortKey == "sort":
        entries = sorted(entries, key=lambda x: (len(x[1]), x[0]))
    else:
        index = int(sortKey[4:])
        entries = sorted(entries, key=lambda x: (x[0][index], -len(x[1])))

    if sortDir == "d":
        entries = reversed(entries)

    for (i, (vals, es)) in enumerate(entries):
        x = len(es)
        e1 = es[0]
        ent1 = entities[e1]
        (eFirst, eLast) = (ent1[2], ent1[-1])

        active = " queried " if activeEntity is not None and i == activeEntity else ""

        item = dedent(
            f"""
            <p
                class="e {active}"
                enm="{i}"
                tstart="{eFirst}" tend="{eLast}"
            >
                <code class="w">{x:>5}</code>
                x
                {repIdent(vals)}>
            </p>"""
        )
        html.append(item)

    return "\n".join(html)


def composeQ(
    web,
    templateData,
    sFind,
    sFindRe,
    sFindError,
    valSelect,
    nFind,
    nEnt,
    nVisible,
    scope,
    report,
):
    """HTML for the query line.

    Parameters
    ----------
    web: object
        The web app object

    Returns
    -------
    html string
        The finished HTML of the query parameters
    """

    kernelApi = web.kernelApi
    app = kernelApi.app
    api = app.api
    F = api.F
    T = api.T

    annoSet = web.annoSet
    setData = web.toolData.ner.sets[annoSet]
    nSent = len(setData.sentences)

    tokenStart = templateData["tokenstart"]
    tokenEnd = templateData["tokenend"]

    hasFind = sFindRe is not None
    hasEntity = tokenStart and tokenEnd

    html = []

    # FILTER SECTION

    findStat = composeFindStat(nSent, nFind, hasFind)

    html.append(
        dedent(
            f"""
            <p>
                <b>Filter:</b>
                <input type="text" name="sfind" id="sfind" value="{sFind}">
                {findStat}
                <button type="submit" id="findclear">✖️</button>
                <span id="sfinderror" class="error">{sFindError}</span>
                <button type="submit" id="lookupf">🔎</button>
            </p>
            """
        )
    )

    # ENTITY SECTION
    # The entity text

    words = (
        [
            f"""{F.str.v(t) or ""}{F.after.v(t) or ""}""".strip()
            for t in range(tokenStart, tokenEnd + 1)
        ]
        if hasEntity
        else []
    )

    wordHtml = " ".join(f"""<span>{w}</span>""" for w in words if w)

    html.append(
        dedent(
            f"""
            <p>
                <b>Entity:</b>
                <input type="hidden"
                    name="tokenstart"
                    id="tokenstart"
                    value="{tokenStart or ""}"
                >
                <input type="hidden"
                    name="tokenend"
                    id="tokenend"
                    value="{tokenEnd or ""}"
                >
                <span id="qwordshow">{wordHtml}</span>
                <button type="submit" id="queryclear">✖️</button>
                <button type="submit" id="lookupq">🔎</button>
            """
        )
    )

    # ENTITY SECTION
    # The entity features

    txt = (
        WHITE_RE.sub(" ", T.text(range(tokenStart, tokenEnd + 1)).strip())
        if hasEntity
        else ""
    )
    features = setData.entityTextVal[txt]

    for feat in FEATURES[1:]:
        theseVals = features.get(feat, set())
        thisValSelect = valSelect[feat]

        html.append(
            dedent(
                f"""
                <input type="hidden"
                    name="{feat}select"
                    id="{feat}select"
                    value="{",".join(thisValSelect)}"
                >
                """
            )
        )
        for val in ["⌀"] + sorted(theseVals):
            status = "v" if val in thisValSelect else "x"
            entityStat = composeEntityStat(
                val, nVisible[feat], nEnt[feat], hasFind, hasEntity
            )
            title = f"{feat} not marked" if val == "⌀" else f"{feat} marked as {val}"

            html.append(
                dedent(
                    f"""
                    <button type="button"
                        name="{val}"
                        class="{feat}sel"
                        st="{status}"
                        title="{title}"
                    >
                        {val}
                        {entityStat}
                    </button>
                    """
                )
            )

        html.append(
            dedent(
                """
                </p>
                """
            )
        )

    # MODIFY SECTION

    html.append(
        dedent(
            f"""
            <input type="hidden"
                id="scope"
                name="scope"
                value="{scope}"
            >
            """
        )
    )

    if annoSet and hasEntity:
        html.append(
            dedent(
                """
                <p><b>Target:</b>
                """
            )
        )
        # Scope of modification

        if hasFind:
            html.append(
                dedent(
                    """
                    <button type="button"
                        id="scopefiltered"
                        title="act on filtered sentences only"
                    >filtered
                    </button>
                    <button type="button"
                        id="scopeall"
                        title="act on all sentences"
                    >all
                    </button>
                    """
                )
            )
        html.append(
            dedent(
                """
                <button type="button"
                    id="selectall"
                    title="select all occurences in filtered sentences"
                >🆗</button>
                <button type="button"
                    id="selectnone"
                    title="deselect all occurences in filtered sentences"
                >⭕️</button>
                """
            )
        )
        html.append(
            dedent(
                """
                </p>
                """
            )
        )
        html.append(
            dedent(
                """
                <p><b>Assignment:</b>
                """
            )
        )

        for feat in FEATURES[1:]:
            theseVals = sorted(setData.entityTextVal[feat].get(txt, set()))
            allVals = (
                sorted(x[0] for x in setData.entityFreq[feat])
                if feat in KEYWORD_FEATURES
                else theseVals
            )
            for kind in allVals:
                occurs = kind in theseVals
                occurCls = " occurs " if occurs else ""

                html.append(
                    dedent(
                        f"""
                        <span class="{feat}_w">
                        """
                    )
                )
                if occurs:
                    html.append(
                        dedent(
                            f"""
                            <button type="submit"
                                name="{feat}_xbutton"
                                value="{val}"
                                class="{feat}_min"
                            >
                                -
                            </button>
                            """
                        )
                    )
                html.append(
                    dedent(
                        f"""
                        <span
                            class="{feat}_sel {occurCls}"
                        >
                            {val}
                        </span>
                        """
                    )
                )
                html.append(
                    dedent(
                        f"""
                        <button type="submit"
                            name="{feat}_pbutton"
                            value="{val}"
                            class="{feat}_plus"
                        >
                            +
                        </button>
                        """
                    )
                )

                html.append(
                    dedent(
                        """
                        </span>
                        """
                    )
                )

            html.append(
                dedent(
                    """
                    <input type="text" id="{feat}_v" name="{feat}_v" value="">
                    <button type="submit"
                        id="{feat}_save"
                        name="{feat}_save"
                        value="v"
                        class="{feat}_plus"
                    >
                        +
                    </button>
                    """
                )
            )

        html.append(
            dedent(
                """
                </p>
                """
            )
        )

    # REPORT SECTION

    if report is not None:
        for line in report:
            html.append(
                dedent(
                    f"""
                    <p><span class="report">{line}</span></p>
                    """
                )
            )

    templateData["q"] = "\n".join(html)


def entityMatch(entityIndex, L, F, T, s, sFindPatternRe, words, valSelect):
    """Checks whether a sentence matches a sequence of words.

    When we do the checking, we ignore empty words in the sentence.

    Parameters
    ----------
    entityIndex: dict
        Dictionary from tuples of slots to sets of kinds, being the kinds that
        entities occupying those slot tuples have
    L, F, T: object
        The TF APIs `F` and `L` for feature lookup and level-switching, and text
        extraction
    s: integer
        The node of the sentence in question
    words: list of string
        The sequence of words that must be matched. They are all non-empty and stripped
        from white space.
    valSelect: string
        The entity kind that the matched words should have
    """
    nWords = len(words)

    positions = set()

    fits = None

    if sFindPatternRe:
        fits = False
        sText = T.text(s)

        for match in sFindPatternRe.finditer(sText):
            positions |= set(range(match.start(), match.end()))
            fits = True

    sTokensAll = [(t, F.str.v(t)) or "" for t in L.d(s, otype="t")]
    sTokens = [x for x in sTokensAll if x[1].strip()]

    matches = []

    if nWords:
        sWords = {w for (t, w) in sTokens}

        if any(w not in sWords for w in words):
            return (fits, {}, None)

        nSTokens = len(sTokens)
        fValStats = {feat: collections.Counter() for feat in FEATURES[1:]}

        for (i, (t, w)) in enumerate(sTokens):
            if w != words[0]:
                continue
            if i + nWords - 1 >= nSTokens:
                return (
                    (fits, fValStats, None)
                    if len(matches) == 0
                    else (fits, fValStats, (sTokensAll, matches, positions))
                )

            match = True

            for (j, w) in enumerate(words[1:]):
                if sTokens[i + j + 1][1] != w:
                    match = False
                    break

            if match:
                lastT = sTokens[i + nWords - 1][0]
                slots = tuple(range(t, lastT + 1))

                valOK = True

                for feat in FEATURES[1:]:
                    theseVals = entityIndex[feat].get(slots, set())
                    theseStats = fValStats[feat]
                    theseValSelect = valSelect[feat]

                    for val in theseVals:
                        theseStats[val] += 1

                    if len(theseVals) == 0:
                        theseStats["⌀"] += 1
                    if (
                        "⌀" in theseValSelect
                        and len(theseVals) == 0
                        or len(theseValSelect & theseVals) != 0
                    ):
                        continue

                    valOK = False

                if valOK:
                    matches.append(slots)

        if len(matches) == 0:
            return (fits, fValStats, None)
    else:
        eKinds = {}

    return (fits, eKinds, (sTokensAll, matches, positions))


def filterS(web, sFindPatternRe, tokenStart, tokenEnd, valSelect):
    """Filter the sentences.

    Will filter the sentences by tokens if the `tokenStart` and `tokenEnd` parameters
    are both filled in.
    In that case, we look up the text between those tokens and including.
    All sentences that contain that text of those slots will show up,
    all other sentences will be left out.
    However, if `valSelect` is non-empty, then there is a further filter: only if the
    text corresponds to an entity with that kind, the sentence is passed through.
    The matching slots will be highlighted.

    Parameters
    ----------
    web: object
        The web app object

    sFindPattern: string
        A search string that filters the sentences, before applying the search
        for a word sequence.

    tokenStart, tokenEnd: int or None
        Specify the start slot number and the end slot number of a sequence of tokens.
        Only sentences that contain this token sentence will be passed through,
        all other sentences will be filtered out.

    valSelect: set
        The entity kinds to filter on.

    Returns
    -------
    list of tuples
        For each sentence that passes the filter, a tuple with the following
        members is added to the list:

        *   tokens: the tokens of the sentence
        *   matches: the match positions of the found text
        *   positions: the token positions where a targeted token sequence starts
    """

    setData = web.toolData.ner.sets[web.annoSet]

    kernelApi = web.kernelApi
    app = kernelApi.app
    api = app.api
    L = api.L
    F = api.F
    T = api.T

    results = []
    words = []

    hasEntity = tokenStart and tokenEnd

    if hasEntity:
        for t in range(tokenStart, tokenEnd + 1):
            word = (F.str.v(t) or "").strip()
            if word:
                words.append(word)

    nFind = 0
    nEnt = {feat: collections.Counter() for feat in FEATURES[1:]}
    nVisible = {feat: collections.Counter() for feat in FEATURES[1:]}

    entityIndex = setData.entityIndex

    for s in setData.sentences:
        (fits, fValStats, result) = entityMatch(
            entityIndex, L, F, T, s, sFindPatternRe, words, valSelect
        )
        blocked = fits is not None and not fits

        if not blocked:
            nFind += 1

        for feat in FEATURES[1:]:
            theseStats = fValStats[feat]
            if len(theseStats):
                theseNEnt = nEnt[feat]
                theseNVisible = nVisible[feat]

                for (ek, n) in theseStats.items():
                    theseNEnt[ek] += n
                    if not blocked:
                        theseNVisible[ek] += n

        if result is None:
            continue

        if fits is not None and not fits:
            continue

        results.append((s, *result))

    return (results, nFind, nVisible, nEnt)


def saveEntity(web, fVals, sentences, excludedTokens):
    setData = web.toolData.ner.sets[web.annoSet]

    oldEntities = setData.entities
    oldEntitySet = oldEntities.values()
    newEntities = []
    excl = 0

    for (s, sTokens, allMatches, positions) in sentences:
        for matches in allMatches:
            data = (fVals, matches)
            if data not in oldEntitySet:
                if matches[-1] in excludedTokens:
                    excl += 1
                    continue
                newEntities.append(data)

    if len(newEntities):
        mergeEntities(web, newEntities)

    nEntities = len(newEntities)
    pl = "y" if nEntities == 1 else "ies"
    valRep = ", ".join(f"{feat}={val}" for (feat, val) in zip(FEATURES[1:], fVals))

    return f"Added {nEntities} entit{pl} with {valRep}; " f"{excl} excluded"


def delEntity(web, fVals, sentences, excludedTokens):
    setData = web.toolData.ner.sets[web.annoSet]

    oldEntities = setData.entities
    oldEntitySet = [x for x in oldEntities.values() if x[0] == fVals]
    delEntities = set()
    excl = 0

    for (s, sTokens, allMatches, positions) in sentences:
        for matches in allMatches:
            data = (fVals, matches)
            if data in oldEntitySet:
                if matches[-1] in excludedTokens:
                    excl += 1
                    continue
                delEntities.add(data)

    if len(delEntities):
        weedEntities(web, delEntities)

    nEntities = len(delEntities)
    pl = "y" if nEntities == 1 else "ies"
    valRep = ", ".join(f"{feat}={val}" for (feat, val) in zip(FEATURES[1:], fVals))

    return f"Deleted {nEntities} entit{pl} with {valRep}; {excl} excluded'"


def composeFindStat(nSent, nFind, hasFind):
    n = f"{nFind} of {nSent}" if hasFind else nSent
    return f"""<span class="stat">{n}</span>"""


def composeEntityStat(val, thisNVisible, thisNEnt, hasPattern, hasQuery):
    if hasQuery:
        na = thisNEnt[val]
        n = f"{thisNVisible[val]} of {na}" if hasPattern else f"{na}"
        entityStat = f"""<span class="stat">{n}</span>"""
    else:
        entityStat = ""

    return entityStat


def composeS(web, sentences, limited, excludedTokens):
    """Compose a table of sentences.

    In that case, we look up the text between those tokens and including.
    All sentences that contain that text of those slots will show up,
    all other sentences will be left out.
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
    setData = web.toolData.ner.sets[annoSet]

    kernelApi = web.kernelApi
    app = kernelApi.app
    api = app.api
    F = api.F

    entityBy = setData.entityBy
    entitySlotIndex = setData.entitySlotIndex

    html = []
    html.append(
        dedent(
            f"""
            <input type="hidden"
                name="excludedtokens"
                id="excludedtokens"
                value="{",".join(str(t) for t in excludedTokens)}"
            >
            """
        )
    )

    i = 0

    for (s, sTokens, matches, positions) in sentences:
        ht = []
        ht.append(f"""<span class="sh">{app.sectionStrFromNode(s)}</span> """)

        charPos = 0
        if annoSet:
            allMatches = set()
            endMatches = set()
            for match in matches:
                allMatches |= set(match)
                endMatches.add(match[-1])

        else:
            allMatches = set(chain.from_iterable(matches))

        for (t, w) in sTokens:
            after = F.after.v(t) or ""
            lenW = len(w)
            lenWa = len(w) + len(after)
            found = any(charPos + i in positions for i in range(lenW))
            queried = t in allMatches
            endQueried = annoSet and t in endMatches
            hlClasses = (" found " if found else "") + (" queried " if queried else "")
            excl = "x" if t in excludedTokens else "v"
            checkbox = f"""<span te="{t}" st="{excl}"></span>""" if endQueried else ""
            info = entitySlotIndex.get(t, None)
            inEntity = False

            if info is not None:
                inEntity = True
                for item in sorted(
                    (x for x in info if x is not None), key=lambda z: z[1]
                ):
                    (status, lg, ident) = item
                    freq = len(entityBy[ident])
                    eInfo = repIdent(ident)

                    if status:
                        lgRep = f"""<span class="lgb">{abs(lg)}</span>"""
                        ht.append(
                            dedent(
                                f"""
                                <span class="es"
                                >{lgRep}{eInfo} <span class="n">{freq}</span
                                ></span>"""
                            )
                        )

            hlClasses += " ei " if inEntity else ""
            hlClass = f""" class="{hlClasses}" """ if hlClasses else ""
            ht.append(f"""<span {hlClass} t="{t}">{w}</span>{checkbox}{after}""")

            if info is not None:
                for item in sorted(
                    (x for x in info if x is not None), key=lambda z: z[1]
                ):
                    (status, lg, ident) = item
                    if not status:
                        lgRep = f"""<span class="lge">{abs(lg)}</span>"""
                        ht.append(dedent(f"""<span class="ee">{lgRep}</span>"""))

            charPos += lenWa

        ht = "".join(ht)
        html.append(f"""<div class="s">{ht}</div>""")

        i += 1

        if limited and i > 100:
            html.append(
                dedent(
                    f"""
                    <div class="report">
                        Showing only the first 100 sentences
                        of all {len(sentences)} ones.
                    </div>
                    """
                )
            )
            break

    return "".join(html)
