"""Module to compose tables of result data.
"""

from textwrap import dedent


def composeE(app, setData, sortKey, sortDir):
    """Compose a table of entities with selection and sort controls.

    Parameters
    ----------
    app: object
        The TF app of the corpus in question.
    setData: dict
        The entity data of the chosen set.
        We only need the `entitiesByKind` member.
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

    html = []

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

    for ((kind, txt), es) in entries:
        x = len(es)
        item = (
            f"""<span><code class="w">{x:>5}</code> x <b>{kind}</b> {txt}</span><br>"""
        )
        html.append(item)

    return "\n".join(html)


def tokenMatch(L, F, s, words):
    nWords = len(words)

    sTokens = {t: F.str.v(t) or "" for t in L.d(s, otype="t")}
    matches = set()

    if nWords:
        sWords = set(sTokens.values())

        if any(w not in sWords for w in words):
            return None

        nSTokens = len(sTokens)

        for (i, (t, w)) in enumerate(sTokens.items()):
            if w != words[0]:
                continue
            if nSTokens < i + nWords:
                return None

            match = True

            for (j, w) in enumerate(words[1:]):
                if sTokens[t + j + 1] != w:
                    match = False
                    break

            if match:
                matches |= set(range(t, t + nWords))

        if len(matches) == 0:
            return None

    return (sTokens, matches)


def composeS(app, setData, tokenStart, tokenEnd):
    """Compose a table of sentences.

    Will filter the sentences by tokens if the `tokens` parameter is not None.
    In that case, `tokens` should be an array of slots.
    All sentences that contain the words of those slots will show up,
    all other sentences will be left out.
    The matching slots will be highlighted.

    Parameters
    ----------
    app: object
        The TF app of the corpus in question.

    setData: dict
        The entity data of the chosen set.

    tokenStart, tokenEnd: int or None
        Specify the start slot number and the end slot number of a sequence of tokens.
        Only sentences that contain this token sentence will be passed through,
        all other sentences will be filtered out.

    Returns
    -------
    html string
        The finished HTML of the table, ready to put into the Flask template.
    """

    api = app.api
    L = api.L
    F = api.F

    html = []
    words = []

    if tokenStart and tokenEnd:
        for t in range(tokenStart, tokenEnd + 1):
            words.append(F.str.v(t) or "")

    entitiesSlotIndex = setData.entitiesSlotIndex

    for s in setData.sentences:
        result = tokenMatch(L, F, s, words)
        if result is None:
            continue

        (sTokens, matches) = result
        ht = []

        for (t, w) in sTokens.items():
            queried = 'class="queried"' if t in matches else ""
            after = F.after.v(t) or ""
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
                                    >{kind} <span class="n">{freq}</span
                                    ></span>"""
                                )
                            )
            inside = 'class="ei"' if inEntity else ""
            ht.append(f"""<span {queried} {inside} t="{t}">{w}</span>{after}""")

            if info is not None:
                for item in info:
                    if item is not None:
                        (status, kind, freq) = item
                        if not status:
                            ht.append(
                                dedent(
                                    f"""<span class="ee">{kind}</span></span>"""
                                )
                            )

        ht = "".join(ht)
        html.append(f"""<div class="s">{ht}</div>""")

    return "".join(html)


def composeQ(app, tokenStart, tokenEnd):
    """HTML for the query tokens.

    Parameters
    ----------
    app: object
        The TF app of the corpus in question.

    tokenStart, tokenEnd: int or None
        Specify the start slot number and the end slot number of a sequence of tokens.
        Only sentences that contain this token sentence will be passed through,
        all other sentences will be filtered out.

    Returns
    -------
    html string
        The finished HTML of the query parameters
    """

    api = app.api
    F = api.F

    html = []

    wordHtml = (
        " ".join(
            f"""<span>{F.str.v(t) or ""}</span> """
            for t in range(tokenStart, tokenEnd + 1)
        )
        if tokenStart and tokenEnd
        else ""
    )

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

    html.append(
        dedent(
            """
            <button type="submit" id="queryFilter">filter</button>
            <button type="submit" id="queryClear">clear</button>
            """
        )
    )

    return "\n".join(html)
