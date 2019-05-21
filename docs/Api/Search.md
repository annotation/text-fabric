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

??? abstract "S.tweakPerformance()"
    ??? explanation "Theory"
        Before the search engine retrieves result tuples of nodes,
        there is a process to narrow down the search space.

        See 
        [search design](../Model/Search.md#spinning-thin-yarns)
        and remember that we use the term *yarn* for
        the sets of candidate nodes from which
        we stitch our results together.

        *Edge spinning* is the process of
        transferring constraints on one node via edges to constraints on 
        another node. The one node has a yarn, i.e. a set of candidate nodes, 
        and the node at the other side of the edge has a yarn.

        If the first yarn is small, and candidates in the first yarn must be related
        to candidates in the second yarn, then we might be able to
        reduce the second yarn by computing the relation for the nodes in the small yarn
        and seeing which nodes you get in the second yarn.
        The relation corresponds to the edge, hence the term edge spinning.

        The success of edge spinning depends mainly on two factors:
        
        ??? info "Size difference"
            Edge spinning works best if there is a big difference in size
            between the candidate
            sets for the nodes at both sides of an edge.

        ??? info "Spread"
            The spread of a relation is the number of different edges
            that can start from the same node or end at the same node.

            For example, the spread of the `equality` operator is just 1, but
            the spread of the `inequality` operator is virtually as big
            as the relevant yarn.

            If there are constraints on a node in one yarn, and if there is an edge
            between that yarn and another one, and if the spread is big,
            not much of the constraint can be transferred to the other yarn.

        ???+ example "Example"
            Suppose both yarns are words, the first yarn has been constrained
            to verbs, and the equality relation holds must hold between the yarns.
            Then in all results the node from the second yarn is also a verb.
            So we can constrain the second yarn to verbs too.
        
            But if the relation is inequality, we cannot impose any additional
            restriction on nodes in the second yarn. All nodes in the second
            yarn are unequal to at least one verb.
         
        If there is a big size difference between the two yarns, and the spread is
        small, a the bigger yarn will be restricted considerably.

        ??? info "Estimating the spread"
            We estimate the spreads of edges over and over again, in a series
            of iterations where we reduce yarns.
            
            An exhaustive computation would be too expensive, so we take
            a sample of a limited amount of relation computations. 

    ```python
    S.tweakPerformance(yarnRatio=None, tryLimitFrom=None, tryLimitTo=None)
    ```

    Tweaks parameters that influence the performance of the search engine.

    If you do not pass a parameter, its value will not be changed.

    If you pass `None`, its value will be reset to the default value.

    Or you can pass a value of your choosing.

    ??? info "yarnRatio"

        The `yarnRatio` is the minimal factor between the sizes of
        the smallest and the biggest set of candidates of the nodes at both ends of
        the edge. And that divided by the spread of the relation as estimated
        by a sample.

        ???+ example "Example"
            Suppose we set the yarnRatio to 1.5.
            Then, if we have yarns of 100,000 and 10,000 members,
            with a relation between them with spread 5,
            then 100,000 / 10,000 / 5 = 2.
            This is higher than the yarnRatio of 1.5,
            so the search engine decides that edge spinning is worth it.

            The reasoning is that the 10,000 nodes in the smallest yarn are expected
            to reach only 10,000 * 5 nodes in the other yarn by the relation,
            and so we can achieve a significant reduction.

        If you have a very slow query, and you think that a bit more edge spinning
        helps, decrease the yarnRatio towards 0.

        If you find that a lot of queries spend too much time in edge spinning,
        increase the yarnRatio.

    ??? info "tryLimitFrom, tryLimitTo"
        In order to determine the spreads of the relations, TF takes
        random samples and extrapolates the results. It takes some nodes
        from the set at the *from* side of an edge, and some nodes at the
        *to* side of the same edge, and computes in how many cases the relation
        holds. That is a measure for the spread.

        The parameters `tryLimitFrom` and `tryLimitTo` dictate how big these
        samples are. The bigger, the better the estimation of the spread.
        But also the more work it is.

        If you find that your queries take consistently a tad too much time,
        consider lowering these parameters to 10.

        If you find that the times your queries take varies a lot,
        increase these values to 10000.

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

