from itertools import chain

from .search import runSearch


def getHlAtt(app, n, highlights, baseTypes, isPlain):
    """Get the highlight attribute for a node.

    Parameters
    ----------
    app: obj
        The high-level API object
    n: int
        The node to be highlighted
    highlights: set|dict
        The nodes to be highlighted.
        Keys/elements are the nodes to be highlighted.
        This function is only interested in whether `n` is in it,
        and if so, what the value is (in case of a dict).
        If given as set: use the default highlight color.
        If given as dict: use the value as color.
    baseTypes: set
        Which node types acts as a base type.
    isPlain:
        Whether we are highlighting for plain() or for pretty().
    """

    if highlights is None:
        return ("", "")

    color = (
        highlights.get(n, None)
        if type(highlights) is dict
        else ""
        if n in highlights
        else None
    )

    if color is None:
        return ("", "")

    api = app.api
    F = api.F

    isBaseType = F.otype.v(n) in baseTypes

    hlCls = ("hl" if isBaseType else "hlbx") if isPlain else "hl"
    hlObject = ("background" if isBaseType else "border") if isPlain else "background"
    hlStyle = f' style="{hlObject}-color: {color};" ' if color != "" else ""

    return (hlCls, hlStyle)


def getTupleHighlights(api, tup, highlights, colorMap, condenseType):
    """Get the highlights for a tuple of nodes.

    The idea is to mark the elements of a tuple of nodes with highlights,
    respecting a given  set or dict of highlights and  a color map.

    This is a bit of an intricate merging operation.

    Parameters
    ----------
    app: obj
        The high-level API object
    tup: tuple of int
        The tuple of nodes to be highlighted
    colorMap: dict
        A mapping of tuple positions to colors.
        Member `i` of `tup` should be highlighted with color `colorMap[i]`.
    condenseType: string
        The type of node that acts as the basis of a pretty display.
        The nodes in the given `tup` will be distributed over as many nodes of
        `condenseType` as they occur in.
    highlights: set|dict
        The nodes to be highlighted.
        Keys/elements are the nodes to be highlighted.
        This function is only interested in whether the members of `tup` are in it,
        and if so, what the values are (in case of a dict).
        If given as set: use the default highlight color.
        If given as dict: use the value as color.
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


def getPassageHighlights(app, node, query, cache):
    """Get the highlights for a whole passage.

    Parameters
    ----------
    app: obj
        The high-level API object
    node: int
        The node of a passage (typically a chapter, or something that is occupies a
        page in the browser)
    query: string
        A query to run, and whose results will be highlighted (as far they occur
        in the passage)
    cache:  dict
        A cache that holds run queries and their results.
        Useful when we browse many chapters and want to show the highlights of
        the same query.
    """

    if not query:
        return None

    (queryResults, messages, features) = runSearch(app, query, cache)
    if messages:
        return None

    api = app.api
    L = api.L
    passageNodes = L.d(node)

    resultSet = set(chain.from_iterable(queryResults))
    passageSet = set(passageNodes)
    return resultSet & passageSet
