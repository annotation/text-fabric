"""Module to compose tables of result data.
"""

import collections
from itertools import chain
from textwrap import dedent

from .kernel import mergeEntities, weedEntities, WHITE_RE


def composeE(web, activeEntity, activeKind, sortKey, sortDir):
    """Compose a table of entities with selection and sort controls.

    Parameters
    ----------
    web: object
        The web app object
    sortKey: string
        Indicates how to sort the table:

        *   `freqsort`: by the frequency of the entities
        *   `kindsort`: by the kind of the entities
        *   `etxtsort`: by the text of the entities

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
    entries = setData.entitiesByKind.items()

    if sortKey == "freqsort":
        if sortDir == "u":
            entries = sorted(entries, key=lambda x: (len(x[1]), x[0][1], x[0][0]))
        else:
            entries = sorted(entries, key=lambda x: (-len(x[1]), x[0][1], x[0][0]))
    elif sortKey == "kindsort":
        entries = sorted(entries, key=lambda x: (x[0][0], x[0][1], -len(x[1])))
        if sortDir == "d":
            entries = reversed(entries)
    elif sortKey == "etxtsort":
        entries = sorted(entries, key=lambda x: (x[0][1], x[0][0], -len(x[1])))
        if sortDir == "d":
            entries = reversed(entries)

    for (i, ((kind, txt), es)) in enumerate(entries):
        x = len(es)
        e1 = es[0]
        ent1 = entities[e1]
        (eFirst, eLast) = (ent1[1], ent1[-1])

        active = " queried " if activeEntity is not None and i == activeEntity else ""

        item = dedent(
            f"""
            <p
                class="e {active}"
                enm="{i}"
                tstart="{eFirst}" tend="{eLast}"
                kind="{kind}"
            >
                <code class="w">{x:>5}</code>
                x
                <b>{kind}</b>
                <span class="et">{txt}</span>
            </p>"""
        )
        html.append(item)

    return "\n".join(html)


def composeQ(
    web,
    sFind,
    sFindRe,
    sFindError,
    tokenStart,
    tokenEnd,
    eKindSelect,
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

    tokenStart, tokenEnd: int or None
        Specify the start slot number and the end slot number of a sequence of tokens.
        Only sentences that contain this token sentence will be passed through,
        all other sentences will be filtered out.

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
                <input type="text" name="sfind" id="sFind" value="{sFind}">
                {findStat}
                <button type="submit" id="findClear">✖️</button>
                <span id="sFindError" class="error">{sFindError}</span>
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
                    name="tselectstart"
                    id="tSelectStart"
                    value="{tokenStart or ""}"
                >
                <input type="hidden"
                    name="tselectend"
                    id="tSelectEnd"
                    value="{tokenEnd or ""}"
                >
                <span id="qWordShow">{wordHtml}</span>
                <button type="submit" id="queryClear">✖️</button>
                <button type="submit" id="lookupq">🔎</button>
            """
        )
    )

    # ENTITY SECTION
    # The entity kind(s)

    txt = (
        WHITE_RE.sub(" ", T.text(range(tokenStart, tokenEnd + 1)).strip())
        if hasEntity
        else ""
    )
    theseKinds = set(setData.entityTextKind[txt])

    html.append(
        dedent(
            f"""
            <input type="hidden"
                name="ekindselect"
                id="eKindSelect"
                value="{",".join(eKindSelect)}"
            >
            """
        )
    )
    for kind in ["⌀"] + sorted(theseKinds):
        status = "v" if kind in eKindSelect else "x"
        entityStat = composeEntityStat(kind, nVisible, nEnt, hasFind, hasEntity)
        title = "not yet marked as entity" if kind == "⌀" else f"marked as {kind}"

        html.append(
            dedent(
                f"""
                <button type="button"
                    name="{kind}"
                    class="ekindsel"
                    st="{status}"
                    title="{title}"
                >
                    {kind}
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
        allKinds = sorted(x[0] for x in setData.entityKindFreq)

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
                        id="scopeFiltered"
                        title="act on filtered sentences only"
                    >filtered
                    </button>
                    <button type="button"
                        id="scopeAll"
                        title="act on all sentences only"
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
        for kind in allKinds:
            occurs = kind in theseKinds
            occurCls = " occurs " if occurs else ""

            html.append(
                dedent(
                    """
                    <span class="ekindw">
                    """
                )
            )
            if occurs:
                html.append(
                    dedent(
                        f"""
                        <button type="submit"
                            name="ekindxbutton"
                            value="{kind}"
                            class="ekindmin"
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
                        class="ekindsel {occurCls}"
                    >
                        {kind}
                    </span>
                    """
                )
            )
            html.append(
                dedent(
                    f"""
                    <button type="submit"
                        name="ekindpbutton"
                        value="{kind}"
                        class="ekindplus"
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
                <input type="text" id="eKindV" name="ekindv" value="">
                <button type="submit"
                    id="eKindSave"
                    name="ekindsave"
                    value="v"
                    class="ekindplus"
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

    html = "\n".join(html)
    return html


def entityMatch(entityIndex, L, F, T, s, sFindPatternRe, words, eKindSelect):
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
    eKindSelect: string
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
        eKinds = collections.Counter()

        for (i, (t, w)) in enumerate(sTokens):
            if w != words[0]:
                continue
            if i + nWords - 1 >= nSTokens:
                return (
                    (fits, eKinds, None)
                    if len(matches) == 0
                    else (fits, eKinds, (sTokensAll, matches, positions))
                )

            match = True

            for (j, w) in enumerate(words[1:]):
                if sTokens[i + j + 1][1] != w:
                    match = False
                    break

            if match:
                lastT = sTokens[i + nWords - 1][0]
                slots = tuple(range(t, lastT + 1))
                theseEKinds = entityIndex.get(slots, set())
                for ek in theseEKinds:
                    eKinds[ek] += 1
                if len(theseEKinds) == 0:
                    eKinds["⌀"] += 1
                if (
                    "⌀" in eKindSelect
                    and len(theseEKinds) == 0
                    or len(eKindSelect & theseEKinds) != 0
                ):
                    matches.append(slots)

        if len(matches) == 0:
            return (fits, eKinds, None)
    else:
        eKinds = {}

    return (fits, eKinds, (sTokensAll, matches, positions))


def filterS(web, sFindPatternRe, tokenStart, tokenEnd, eKindSelect):
    """Filter the sentences.

    Will filter the sentences by tokens if the `tokenStart` and `tokenEnd` parameters
    are both filled in.
    In that case, we look up the text between those tokens and including.
    All sentences that contain that text of those slots will show up,
    all other sentences will be left out.
    However, if `eKindSelect` is non-empty, then there is a further filter: only if the
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

    eKindSelect: set
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
    nEnt = collections.Counter()
    nVisible = collections.Counter()

    entityIndex = setData.entityIndex

    for s in setData.sentences:
        (fits, eKinds, result) = entityMatch(
            entityIndex, L, F, T, s, sFindPatternRe, words, eKindSelect
        )
        blocked = fits is not None and not fits

        if not blocked:
            nFind += 1

        if len(eKinds):
            for (ek, n) in eKinds.items():
                nEnt[ek] += n
                if not blocked:
                    nVisible[ek] += n

        if result is None:
            continue

        if fits is not None and not fits:
            continue

        results.append((s, *result))

    return (results, nFind, nVisible, nEnt)


def saveEntity(web, kind, sentences, excludedTokens):
    setData = web.toolData.ner.sets[web.annoSet]

    oldEntities = setData.entities
    oldEntitySet = oldEntities.values()
    newEntities = []
    excl = 0

    for (s, sTokens, allMatches, positions) in sentences:
        for matches in allMatches:
            data = (kind, *matches)
            if data not in oldEntitySet:
                if matches[-1] in excludedTokens:
                    excl += 1
                    continue
                newEntities.append(data)

    if len(newEntities):
        mergeEntities(web, newEntities)

    nEntities = len(newEntities)
    pl = "y" if nEntities == 1 else "ies"
    return f"Added {nEntities} entit{pl} with kind '{kind}; {excl} excluded'"


def delEntity(web, kind, sentences, excludedTokens):
    setData = web.toolData.ner.sets[web.annoSet]

    oldEntities = setData.entities
    oldEntitySet = [x for x in oldEntities.values() if x[0] == kind]
    delEntities = set()
    excl = 0

    for (s, sTokens, allMatches, positions) in sentences:
        for matches in allMatches:
            data = (kind, *matches)
            if data in oldEntitySet:
                if matches[-1] in excludedTokens:
                    excl += 1
                    continue
                delEntities.add(data)

    if len(delEntities):
        weedEntities(web, delEntities)

    nEntities = len(delEntities)
    pl = "y" if nEntities == 1 else "ies"
    return f"Deleted {nEntities} entit{pl} with kind '{kind}'; {excl} excluded'"


def composeFindStat(nSent, nFind, hasFind):
    n = f"{nFind} of {nSent}" if hasFind else nSent
    return f"""<span class="stat">{n}</span>"""


def composeEntityStat(kind, nVisible, nEnt, hasPattern, hasQuery):
    if hasQuery:
        n = f"{nVisible[kind]} of {nEnt[kind]}" if hasPattern else f"{nEnt[kind]}"
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

    entitiesSlotIndex = setData.entitiesSlotIndex

    html = []
    html.append(
        dedent(
            f"""
            <input type="hidden"
                name="excludedtokens"
                id="excludedTokens"
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

        web.console(allMatches)
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
            info = entitiesSlotIndex.get(t, None)
            inEntity = False

            if info is not None:
                inEntity = True
                for item in sorted(
                    (x for x in info if x is not None), key=lambda z: z[1]
                ):
                    (status, lg, kind, freq) = item
                    lgRep = f"""<span class="lgb">{abs(lg)}</span>"""
                    if status:
                        ht.append(
                            dedent(
                                f"""
                                <span class="es"
                                >{lgRep}{kind} <span class="n">{freq}</span
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
                    (status, lg, kind, freq) = item
                    lgRep = f"""<span class="lge">{abs(lg)}</span>"""
                    if not status:
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
