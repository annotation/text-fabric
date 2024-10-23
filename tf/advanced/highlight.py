from .search import runSearch


def getHlAtt(app, n, highlights, isSlot):
    """Get the highlight attribute and style for a node for both pretty and plain modes.

    Parameters
    ----------
    app: obj
        The high-level API object
    n: integer
        The node to be highlighted
    highlights: set|dict
        The nodes to be highlighted.
        Keys / elements are the nodes to be highlighted.
        This function is only interested in whether `n` is in it,
        and if so, what the value is (in case of a dict).
        If given as set: use the default highlight colour.
        If given as dict: use the value as colour.
    isSlot: boolean
        Whether the node has the slot type

    Returns
    -------
    hlCls: dict
        Highlight attribute, keyed by boolean 'is pretty'
    hlStyle: dict
        Highlight colour as CSS style, keyed by boolean 'is pretty'
    """

    noResult = ({True: "", False: ""}, {True: "", False: ""})

    if highlights is None:
        return noResult

    color = (
        highlights.get(n, None)
        if type(highlights) is dict
        else ""
        if n in highlights
        else None
    )

    if color is None:
        return noResult

    hlCls = {True: "hl", False: "hl" if isSlot else "hlbx"}
    hlObject = {True: "background", False: "background" if isSlot else "border"}
    hlCls = {b: hlCls[b] for b in (True, False)}
    hlStyle = {
        b: f' style="{hlObject[b]}-color: {color};" ' if color != "" else ""
        for b in (True, False)
    }

    return (hlCls, hlStyle)


def getEdgeHlAtt(e, pair, highlights):
    """Get the edge highlight attribute and style for an edge, only for pretty mode.

    Parameters
    ----------
    e: string
        The edge feature to be highlighted
    pair: tuple
        The *from* node of the edge to be highlighted and
        the *to* node of the edge to be highlighted
    highlights: dict
        A dict or set of pairs of nodes belonging to edge feature `e` that must
        be highlighted.
        This function is only interested in whether the value `(f, t)` is in
        `highlights`, and if so, what the value is (in case of a dict).
        If given as set: use the default highlight colour.
        If given as dict: use the value as colour.

    Returns
    -------
    hlCls: string
        Highlight attribute
    hlStyle: string
        Highlight colour as CSS style
    """

    if highlights is None:
        return ("", "")

    hKey = (
        pair
        if pair in highlights
        else (pair[0], None)
        if (pair[0], None) in highlights
        else (None, pair[1])
        if (None, pair[1]) in highlights
        else None
    )

    if hKey is None:
        return ("", "")

    color = highlights[hKey] if type(highlights) is dict else ""

    return ("ehl", f' style="background-color: {color};" ' if color != "" else "")


def getTupleHighlights(api, tup, highlights, colorMap, condenseType):
    """Get the highlights for a tuple of nodes.

    The idea is to mark the elements of a tuple of nodes with highlights,
    respecting a given set or dict of highlights and a colour map.

    This is a bit of an intricate merging operation.

    Parameters
    ----------
    app: obj
        The high-level API object
    tup: tuple of integer
        The tuple of nodes to be highlighted
    colorMap: dict
        A mapping of tuple positions to colours.
        Member `i` of `tup` should be highlighted with colour `colorMap[i]`.
    condenseType: string
        The type of node that acts as the basis of a pretty display.
        The nodes in the given `tup` will be distributed over as many nodes of
        `condenseType` as they occur in.
    highlights: set|dict
        The nodes to be highlighted.
        Keys / elements are the nodes to be highlighted.
        This function is only interested in whether the members of `tup` are in it,
        and if so, what the values are (in case of a dict).
        If given as set: use the default highlight colour.
        If given as dict: use the value as colour.
    """

    F = api.F
    N = api.N
    fOtype = F.otype.v
    otypeRank = N.otypeRank

    condenseRank = otypeRank[condenseType]
    if highlights is None:
        highlights = {}
    elif type(highlights) is set:
        highlights = {m: "" for m in highlights}
    newHighlights = {n: h for (n, h) in highlights.items()}

    for (i, n) in enumerate(tup):
        nType = fOtype(n)
        if newHighlights.get(n, None):
            continue
        if otypeRank[nType] < condenseRank:
            newHighlights[n] = (
                highlights[n]
                if n in highlights
                else colorMap[i + 1]
                if colorMap is not None and i + 1 in colorMap
                else ""
            )
    return newHighlights


def getPassageHighlights(app, node, query, colorMap, cache):
    """Get the highlights for a whole passage.

    Parameters
    ----------
    app: obj
        The high-level API object
    node: integer
        The node of a passage (typically a chapter, or something that is occupies a
        page in the browser)
    query: string
        A query to run, and whose results will be highlighted (as far they occur
        in the passage)
    colorMap: dict
        A mapping of tuple positions to colours.
        Member `i` of a query result should be highlighted with colour `colorMap[i]`.
    cache:  dict
        A cache that holds run queries and their results.
        Useful when we browse many chapters and want to show the highlights of
        the same query.

    Returns
    -------
    dict
        Keys are the nodes to be highlighted, values are the highlight colours.
    """

    if not query:
        return None

    (queryResults, status, messages, nodeFeatures, edgeFeatures) = runSearch(
        app, query, cache
    )
    if not status[0] or not status[1]:
        return None

    api = app.api
    L = api.L

    passageNodes = L.d(node)
    passageSet = set(passageNodes)

    newHighlights = {}

    for tup in queryResults:
        for (i, n) in enumerate(tup):
            if n not in passageSet:
                continue
            if newHighlights.get(n, None):
                continue
            newHighlights[n] = (
                colorMap[i + 1]
                if colorMap is not None and i + 1 in colorMap
                else ""
            )

    return newHighlights
