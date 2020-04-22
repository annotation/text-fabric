from itertools import chain

from .search import runSearch


def getHlAtt(app, n, highlights, baseType, isPlain):
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

    isBaseType = F.otype.v(n) == baseType

    hlCls = ("hl" if isBaseType else "hlbx") if isPlain else "hl"
    hlObject = ("background" if isBaseType else "border") if isPlain else "background"
    hlStyle = f' style="{hlObject}-color: {color};" ' if color != "" else ""

    return (hlCls, hlStyle)


def getTupleHighlights(api, tup, highlights, colorMap, condenseType):
    F = api.F
    fOtype = F.otype.v
    otypeRank = api.otypeRank

    condenseRank = otypeRank[condenseType]
    if type(highlights) is set:
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
