"""
Calls from the advanced API to the Search API.
"""

import types

from ..core.helpers import console, wrapMessages
from ..core.timestamp import SILENT_D, silentConvert
from .condense import condense


def searchApi(app):
    app.search = types.MethodType(search, app)


def getQueryFeatures(exe):
    qnodes = getattr(exe, "qnodes", [])
    nodeMap = getattr(exe, "nodeMap", {})
    nodeFeatures = tuple(
        (i, tuple(sorted(set(q[1].keys()) | nodeMap.get(i, set()))))
        for (i, q) in enumerate(qnodes)
    )

    qedges = getattr(exe, "qedges", [])
    edgeMap = getattr(exe, "edgeMap", {})

    edgeFeatures = set()

    for (f, rela, t) in qedges:
        edgeName = edgeMap.get(rela, (None,))[0]
        if edgeName is not None:
            edgeFeatures.add(edgeName)
    edgeFeatures = tuple(sorted(edgeFeatures))

    return (nodeFeatures, edgeFeatures)


def search(
    app, query, silent=SILENT_D, sets=None, shallow=False, sort=True, limit=None
):
    """Search with some high-level features.

    This function calls the lower level `tf.search.search.Search` facility aka `S`.
    But whereas the `S` version returns a generator which yields the results
    one by one, the `A` version collects all results and sorts them in the
    canonical order (`tf.core.nodes`).
    (but you can change the sorting, see the `sort` parameter).
    It then reports the number of results.

    It will also set the display parameter `tupleFeatures` and `extraFeatures`
    in such a way that subsequent calls to `tf.advanced.display.export` emit
    the features that have been used in the query.

    The node features used in the query go into the `tupleFeatures`, the edge
    features go into the `extraFeatures`.

    Parameters
    ----------

    query: dict
        the search template (`tf.about.searchusage`)
        that has to be searched for.

    silent: string, optional `tf.core.timestamp.SILENT_D`
        See `tf.core.timestamp.Timestamp`

    shallow: boolean, optional False
        If `True` or `1`, the result is a set of things that match the top-level element
        of the `query`.

        If `2` or a bigger number `n`, return the set of truncated result tuples: only
        the first `n` members of each tuple are retained.

        If `False` or `0`, a list of all result tuples will be returned.

    sets: dict, optional None
        If not `None`, it should be a dictionary of sets, keyed by a names.
        In `query` you can refer to those names to invoke those sets.

        For example, if you have a set `gappedPhrases` of all phrase nodes
        that have a gap, you can pass `sets=dict(gphrase=gappedPhrases)`,
        and then in your query you can say

            gphrase function=Pred
              word sp=verb

        etc.

        This is handy when you need node sets that cannot be conveniently queried.
        You can produce them by hand-coding.
        Once you got them, you can use them over and over again in queries.
        Or you can save them with `tf.lib.writeSets`
        and use them in the TF browser.

        If the app has been loaded with the `setFile` parameter,
        the sets found in that file will automatically be added to the sets passed
        in this argument.
        If you pass sets with a name that also occur in the sets from the app,
        then the sets you pass override the sets of the app.

    sort: boolean, optional True
        If `True` (default), search results will be returned in
        canonical order (`tf.core.nodes`).

        !!! note "canonical sort key for tuples"
            This sort is achieved by using the function

                tf.core.nodes.Nodes.sortKeyTuple

            as sort key.

        If it is a *sort key*, i.e. function that can be applied to tuples of nodes
        returning values, then this key will be used to sort the results.

        If it is a `False` value, no sorting will be applied.

    limit: integer, optional None
        If `limit` is a positive number, it will fetch only that many results.
        If it is negative, 0, None, or absent, it will fetch arbitrary many results.

        !!! caution "there is an upper *fail limit* for safety reasons.
            The limit is a factor times the max node in your corpus.
            See `tf.parameters.SEARCH_FAIL_FACTOR`.
            If this *fail limit* is exceeded in cases where no positive `limit`
            has been passed, you get a warning message.

    !!! hint "search template reference"
        See the search template reference (`tf.about.searchusage`)

    !!! note "Context Jupyter"
        The intended context of this function is: an ordinary Python program (including
        the Jupyter notebook).
        Web apps can better use `tf.advanced.search.runSearch`.
    """

    warning = app.warning
    isSilent = app.isSilent
    setSilent = app.setSilent
    api = app.api
    S = api.S
    N = api.N
    sortKeyTuple = N.sortKeyTuple

    wasSilent = isSilent()

    silent = silentConvert(silent)

    passSets = {**app.sets} if app.sets else {}
    if sets:
        for (name, s) in sets.items():
            passSets[name] = s

    results = S.search(query, sets=passSets, shallow=shallow, limit=limit)

    if not shallow:
        if not sort:
            results = list(results)
        elif sort is True:
            results = sorted(results, key=sortKeyTuple)
        else:
            try:
                sortedResults = sorted(results, key=sort)
            except Exception as e:
                console(
                    (
                        "WARNING: your sort key function caused an error\n"
                        f"{str(e)}"
                        "\nYou get unsorted results"
                    ),
                    error=True,
                )
                sortedResults = list(results)
            results = sortedResults

        nodeFeatures = ()
        edgeFeatures = ()

        if S.exe:
            (nodeFeatures, edgeFeatures) = getQueryFeatures(S.exe)
            app.displaySetup(
                tupleFeatures=nodeFeatures, extraFeatures=(edgeFeatures, {})
            )

    nResults = len(results)
    plural = "" if nResults == 1 else "s"
    setSilent(silent)
    warning(f"{nResults} result{plural}")
    setSilent(wasSilent)
    return results


def runSearch(app, query, cache):
    """A wrapper around the generic search interface of TF.

    Before running the TF search, the *query* will be looked up in the *cache*.
    If present, its cached results / error messages will be returned.
    If not, the query will be run, results / error messages collected, put in the *cache*,
    and returned.

    !!! note "Context web app"
        The intended context of this function is: web app.
    """

    api = app.api
    S = api.S
    N = api.N
    sortKeyTuple = N.sortKeyTuple
    plainSearch = S.search

    cacheKey = (query, False)
    if cacheKey in cache:
        return cache[cacheKey]
    options = dict(_msgCache=[])
    if app.sets is not None:
        options["sets"] = app.sets
    (queryResults, status, messages, exe) = plainSearch(query, here=False, **options)
    queryResults = tuple(sorted(queryResults, key=sortKeyTuple))
    nodeFeatures = ()
    edgeFeatures = set()

    if exe:
        (nodeFeatures, edgeFeatures) = getQueryFeatures(exe)

    (runStatus, runMessages) = wrapMessages(S._msgCache)
    cache[cacheKey] = (
        queryResults,
        (status, runStatus),
        (messages, runMessages),
        nodeFeatures,
        edgeFeatures,
    )
    return (
        queryResults,
        (status, runStatus),
        (messages, runMessages),
        nodeFeatures,
        edgeFeatures,
    )


def runSearchCondensed(app, query, cache, condenseType):
    """A wrapper around the generic search interface of TF.

    When query results need to be condensed into a container,
    this function takes care of that.
    It first tries the *cache* for condensed query results.
    If that fails,
    it collects the bare query results from the cache or by running the query.
    Then it condenses the results, puts them in the *cache*, and returns them.

    !!! note "Context web app"
        The intended context of this function is: web app.
    """

    api = app.api
    cacheKey = (query, True, condenseType)
    if cacheKey in cache:
        return cache[cacheKey]
    (queryResults, status, messages, nodeFeatures, edgeFeatures) = runSearch(
        app, query, cache
    )
    queryResults = condense(api, queryResults, condenseType, multiple=True)
    cache[cacheKey] = (queryResults, status, messages, nodeFeatures, edgeFeatures)
    return (queryResults, status, messages, nodeFeatures, edgeFeatures)
