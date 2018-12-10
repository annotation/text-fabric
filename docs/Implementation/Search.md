### TF search performers

??? abstract "search()"
    ```python
    search(app, query, silent=False, sets=None, shallow=False)
    ```

    This is a thin wrapper around the generic search interface of TF:
    [S.search](../Api/Search.md#search)

    The extra thing it does it collecting the results.
    `S.search()` may yield a generator, and this `search()` makes sure to iterate
    over that generator, collect the results, and return them as a sorted list.

    ??? note "Context Jupyter"
        The intended context of this function is: an ordinary Python program (including
        the Jupyter notebook).
        Web apps can better use `runSearch` below.

??? abstract "runSearch()"
    ```python
    runSearch(app, query, cache)
    ```

    A wrapper around the generic search interface of TF.

    Before running the TF search, the *query* will be looked up in the *cache*.
    If present, its cached results/error messages will be returned.
    If not, the query will be run, results/error messages collected, put in the *cache*,
    and returned.

    ??? note "Context web app"
        The intended context of this function is: web app.

??? abstract "runSearchCondensed()"
    ```python
    runSearchCondensed(api, query, cache, condenseType)
    ```

    When query results need to be condensed into a container,
    this function takes care of that.
    It first tries the *cache* for condensed query results.
    If that fails,
    it collects the bare query results from the cache or by running the query.
    Then it condenses the results, puts them in the *cache*, and returns them.

    ??? note "Context web app"
        The intended context of this function is: web app.
