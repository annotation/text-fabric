# Search
 
For a description of Text-Fabric search, go to [Search](../Use/Search.md)

???+ info "S"
    The Search API is exposed as `S` or `Search`.

    It's main method, `search`, takes a [search template](../Use/Search.md#search-templates)
    as argument.
    A template consists of elements that specify nodes with conditions and
    relations between them.
    The results of a search are instantiations of the search template.
    More precisely, each instantiation is a tuple of nodes
    that instantiate the elements in the template,
    in such a way that the relational pattern expressed in the template
    holds between the nodes of the result tuple.

## Search API

The API for searching is a bit richer than the `search()` functions.
Here is the whole interface.

??? abstract "S.relationsLegend()"
    ```python
    S.relationsLegend()
    ```

    ???+ info "Description"
        Gives dynamic help about the basic relations that you can use in your search
        template. It includes the edge features that are available in your dataset.


??? abstract "S.search()"
    ```python
    S.search(query, limit=None, shallow=False, sets=None, withContext=None)
    ```

    ???+ info "Description"
        Searches for combinations of nodes that together match a search template.
        This method returns a *generator* which yields the results one by one. One result
        is a tuple of nodes, where each node corresponds to an *atom*-line in your
        [search template](../Use/Search.md#search-template-reference).
        
    ??? info "query"
        The query is a search template, i.e. a string that conforms to the rules described above.
        
    ??? info "shallow"
        If `True` or `1`, the result is a set of things that match the top-level element
        of the `query`.

        If `2` or a bigger number *n*, return the set of truncated result tuples: only
        the first *n* members of each tuple is retained.

        If `False` or `0`, a sorted list of all result tuples will be returned.

    ??? info "sets"
        If not `None`, it should be a dictionary of sets, keyed by a names.
        In `query` you can refer to those names to invoke those sets.

    ??? info "limit"
        If `limit` is a number, it will fetch only that many results.

    ??? hint "TF as Database"
        By means of `S.search(query)` you can use one `TF` instance as a
        database that multiple clients can use without the need for each client to call the 
        costly `load` methods.
        You have to come up with a process that runs TF, has all features loaded, and
        that can respond to queries from other processes.
        We call such a process a **TF kernel**.

        Web servers can use such a daemonized TF to build efficient controllers.

        A TF kernel and web server are included in the Text-Fabric code base.
        See [kernel](../Server/Kernel.md) and [web](../Server/Web.md).

    ??? note "Generator versus tuple"
        If `limit` is specified, the result is not a generator but a tuple of results.

    ??? explanation "More info on the search plan"
        Searching is complex. The search template must be parsed, interpreted, and
        translated into a search plan. The following methods expose parts of the search
        process, and may provide you with useful information in case the search does not
        deliver what you expect.

    ??? hint "see the plan"
        the method `S.showPlan()` below shows you at a glance the correspondence
        between the nodes in each result tuple and your search template.

??? abstract "S.study()"
    ```python
    S.study(searchTemplate, strategy=None, silent=False, shallow=False, sets=None)
    ```

    ???+ info "Description"
        Your search template will be checked, studied, the search
        space will be narrowed down, and a plan for retrieving the results will be set
        up.

        If your query has quantifiers, the asscociated search templates will be constructed
        and executed. These searches will be reported clearly.

    ??? info "searchTemplate"
        The search template is a string that conforms to the rules described above.

    ??? danger "strategy"
        In order to tame the performance of search, the strategy by which results are fetched
        matters a lot.
        The search strategy is an implementation detail, but we bring
        it to the surface nevertheless.

        To see the names of the available strategies, just call
        `S.study('', strategy='x')` and you will get a list of options reported to
        choose from.

        Feel free to experiment. To see what the strategies do,
        see the [code]({{tfghb}}/{{c_search}}).

    ??? info "silent"
        If you want to suppress most of the output, say `silent=True`.

    ??? info "shallow, sets"
        As in `S.search()`.

??? abstract "S.showPlan()"
    ```python
    S.showPlan(details=False)
    ```

    ???+ info "Description"
        Search results are tuples of nodes and the plan shows which part of the tuple
        corresponds to which part of the search template.

    ??? info "details"
        If you say `details=True`, you also get an overview of the search space and a
        description of how the results will be retrieved.

    ??? note "after S.study()"
        This function is only meaningful after a call to `S.study()`.

## Search results

??? info "Preparation versus result fetching"
    The method `S.search()` above combines the interpretation of a given
    template, the setting up of a plan, the constraining of the search space
    and the fetching of results.

    Here are a few methods that do actual result fetching.
    They must be called after a previous `S.search()` or `S.study()`.

??? abstract "S.count()"
    ```python
    S.count(progress=None, limit=None)
    ```

    ??? info "Description"
        Counts the results, with progress messages, optionally up to a limit.
        
    ??? info "progress"
        Every so often it shows a progress message.
        The frequency is `progress` results, default every 100.

    ??? info "limit"
        Fetch results up to a given `limit`, default 1000.
        Setting `limit` to 0 or a negative value means no limit: all results will be
        counted.

    ??? note "why needed"
        You typically need this in cases where result fetching turns out to
        be (very) slow.

    ??? caution "generator versus list"
        `len(S.results())` does not work, because `S.results()` is a generator
        that delivers its results as they come.

??? abstract "S.fetch()"
    ```python
    S.fetch(limit=None)
    ```

    ???+ info "Description"
        Finally, you can retrieve the results. The result of `fetch()` is not a list of
        all results, but a *generator*. It will retrieve results as long as they are
        requested and their are still results.

    ??? info "limit"
        Tries to get that many results and collects them in a tuple.
        So if limit is not `None`, the result is a tuple with a known length.

    ??? example "Iterating over the `fetch()` generator"
        You typically fetch results by saying:

        ```python
        i = 0
        for r in S.results():
            do_something(r[0])
            do_something_else(r[1])
        ```

        Alternatively, you can set the `limit` parameter, to ask for just so many
        results. They will be fetched, and when they are all collected, returned as a
        tuple.

    ??? example "Fetching a limited amount of results"
        ```python
        S.fetch(limit=10)
        ```

        gives you the first bunch of results quickly.

??? abstract "S.glean()"
    ```python
    S.glean(r)
    ```

    ???+ info "Description"
        A search result is just a tuple of nodes that correspond to your template, as
        indicated by `showPlan()`. Nodes give you access to all information that the
        corpus has about it.

        The `glean()` function is here to just give you a first impression quickly.  

    ??? info "r"
        Pass a raw result tuple `r`, and you get a string indicating where it occurs,
        in terms of sections, 
        and what text is associated with the results.

    ??? example "Inspecting results"
        ```python
        for result in S.fetch(limit=10):
            print(S.glean(result))
        ```

        is a handy way to get an impression of the first bunch of results.

    ??? hint "Universal"
        This function works on all tuples of nodes, whether they have been
        obtained by search or not.

    ??? hint "More ways of showing results"
        If you work in one of the [corpora](../About/Corpora.md) for which there is a TF app,
        you will be provided with more powerful methods `show()` and `table()`
        to display your results.

