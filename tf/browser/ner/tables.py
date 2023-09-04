"""Module to compose tables of result data.
"""

from itertools import chain
from textwrap import dedent

from .kernel import mergeEntities


def composeE(web, activeEntity, sortKey, sortDir):
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
            <p class="e {active}" enm="{i}" tstart="{eFirst}" tend="{eLast}">
                <code class="w">{x:>5}</code>
                x
                <b>{kind}</b>
                <span class="et">{txt}</span>
            </p>"""
        )
        html.append(item)

    return "\n".join(html)


def tokenMatch(L, F, T, s, sFindPatternRe, words):
    """Checks whether a sentence matches a sequence of words.

    When we do the checking, we ignore empty words in the sentence.

    Parameters
    ----------
    L, F, T: object
        The TF APIs `F` and `L` for feature lookup and level-switching, and text
        extraction
    s: integer
        The node of the sentence in question
    words: list of string
        The sequence of words that must be matched. They are all non-empty and stripped
        from white space.
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
            return (fits, None)

        nSTokens = len(sTokens)

        for (i, (t, w)) in enumerate(sTokens):
            if w != words[0]:
                continue
            if i + nWords - 1 >= nSTokens:
                return (fits, None)

            match = True

            for (j, w) in enumerate(words[1:]):
                if sTokens[i + j + 1][1] != w:
                    match = False
                    break

            if match:
                lastT = sTokens[i + nWords - 1][0]
                matches.append(list(range(t, lastT + 1)))

        if len(matches) == 0:
            return (fits, None)

    return (fits, (sTokensAll, matches, positions))


def filterS(web, sFindPatternRe, tokenStart, tokenEnd):
    """Filter the sentences.

    Will filter the sentences by tokens if the `tokenStart` and `tokenEnd` parameters
    are both filled in.
    In that case, we look up the text between those tokens and including.
    All sentences that contain that text of those slots will show up,
    all other sentences will be left out.
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

    if tokenStart and tokenEnd:
        for t in range(tokenStart, tokenEnd + 1):
            word = (F.str.v(t) or "").strip()
            if word:
                words.append(word)

    nFind = 0
    nQuery = 0
    nVisible = 0

    for s in setData.sentences:
        (fits, result) = tokenMatch(L, F, T, s, sFindPatternRe, words)
        if fits:
            nFind += 1

        if result is None:
            continue

        nQuery += 1

        if fits is not None and not fits:
            continue

        nVisible += 1

        results.append((s, *result))

    return (results, nFind, nVisible, nQuery)


def saveEntity(web, kind, sentences):
    setData = web.toolData.ner.sets[web.annoSet]

    oldEntities = setData.entities
    oldEntitySet = oldEntities.values()
    newEntities = []

    for (s, sTokens, allMatches, positions) in sentences:
        for matches in allMatches:
            data = (kind, *matches)
            if data not in oldEntitySet:
                newEntities.append(data)

    if len(newEntities):
        mergeEntities(web, newEntities)


def composeStat(web, nFind, nVisible, nQuery, hasPattern, hasQuery):
    findStat = f"""<span class="stat">{nFind}</span>""" if hasPattern else ""

    if hasQuery:
        n = f"{nVisible} of {nQuery}" if hasPattern else f"{nQuery}"
        queryStat = f"""<span class="stat">{n}</span>"""
    else:
        queryStat = ""

    return (findStat, queryStat)


def composeS(web, sentences):
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

    setData = web.toolData.ner.sets[web.annoSet]

    kernelApi = web.kernelApi
    app = kernelApi.app
    api = app.api
    F = api.F

    entitiesSlotIndex = setData.entitiesSlotIndex

    html = []

    for (s, sTokens, matches, positions) in sentences:
        ht = []
        ht.append(f"""<span class="sh">{app.sectionStrFromNode(s)}</span> """)

        charPos = 0
        allMatches = set(chain.from_iterable(matches))

        for (t, w) in sTokens:
            after = F.after.v(t) or ""
            lenW = len(w)
            lenWa = len(w) + len(after)
            found = any(charPos + i in positions for i in range(lenW))
            queried = t in allMatches
            hlClasses = (" found " if found else "") + (" queried " if queried else "")
            info = entitiesSlotIndex.get(t, None)
            inEntity = False

            if info is not None:
                inEntity = True
                for item in info:
                    if item is not None:
                        (status, kind, freq) = item
                        if status:
                            ht.append(
                                dedent(
                                    f"""
                                    <span class="es"
                                    >[{kind} <span class="n">{freq}</span
                                    ></span>"""
                                )
                            )

            hlClasses += " ei " if inEntity else ""
            hlClass = f""" class="{hlClasses}" """ if hlClasses else ""
            ht.append(f"""<span {hlClass} t="{t}">{w}</span>{after}""")

            if info is not None:
                for item in reversed(info):
                    if item is not None:
                        (status, kind, freq) = item
                        if not status:
                            ht.append(dedent("""<span class="ee">]</span>"""))

            charPos += lenWa

        ht = "".join(ht)
        html.append(f"""<div class="s">{ht}</div>""")

    return "".join(html)


def composeQ(web, sFind, tokenStart, tokenEnd, nQuery, nVisible, saveVisible):
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

    html = []

    words = (
        [
            f"""{F.str.v(t) or ""}{F.after.v(t) or ""}""".strip()
            for t in range(tokenStart, tokenEnd + 1)
        ]
        if tokenStart and tokenEnd
        else []
    )
    wordHtml = " ".join(f"""<span>{w}</span>""" for w in words if w)

    html.append(
        dedent(
            f"""
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
            """
        )
    )

    queryCtrl = dedent(
        """
            <button type="submit" id="queryClear">✖️</button>
            """
    )

    annoSet = web.annoSet
    editCtrl = ""

    if annoSet:
        setData = web.toolData.ner.sets[annoSet]
        kinds = sorted(x[0] for x in setData.entityKindFreq)
        editHtml = []

        web.console(f"composeQ {saveVisible=}")
        editHtml.append(
            dedent(
                f"""
                 Save result as entity
                <button type="button"
                    id="saveVisibleX"
                    nv="{nVisible}"
                    na="{nQuery}"
                >
                </button>
                <input type="hidden"
                    id="saveVisible"
                    name="savevisible"
                    value="{saveVisible}"
                >
                of existing kind
                """
            )
        )
        for kind in kinds:
            editHtml.append(
                dedent(
                    f"""
                    <button type="submit"
                        name="ekindbutton"
                        value="{kind}"
                        class="ekind"
                    >
                        {kind}
                    </button>
                    """
                )
            )

        editHtml.append(
            dedent(
                """
                or new kind
                <input type="text" id="eKindX" name="ekindx" value="">
                <button type="submit"
                    id="eKindSave"
                    name="ekindsave"
                    value="v"
                >
                    ✅
                </button>
                """
            )
        )

        editCtrl = " ".join(editHtml)

    queryHtml = "\n".join(html)
    return (queryHtml, queryCtrl, editCtrl)
