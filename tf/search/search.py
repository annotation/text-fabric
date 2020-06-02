"""
.. include:: ../../docs/search/search.md
"""

from ..core.helpers import console, wrapMessages
from .searchexe import SearchExe
from ..parameters import YARN_RATIO, TRY_LIMIT_FROM, TRY_LIMIT_TO


class Search(object):
    """

    """

    def __init__(self, api, silent):
        self.api = api
        self.silent = silent
        self.exe = None
        self.perfDefaults = dict(
            yarnRatio=YARN_RATIO, tryLimitFrom=TRY_LIMIT_FROM, tryLimitTo=TRY_LIMIT_TO,
        )
        self.perfParams = {}
        self.perfParams.update(self.perfDefaults)
        SearchExe.setPerfParams(self.perfParams)

    def tweakPerformance(self, silent=False, **kwargs):
        """Tweak parameters that influence the search process.

        !!! explanation "Theory"
            Before the search engine retrieves result tuples of nodes,
            there is a process to narrow down the search space.

            See `tf.about.searchdesign` and and remember that we use the term *yarn* for
            the sets of candidate nodes from which we stitch our results together.

            *Edge spinning* is the process of
            transferring constraints on one node via edges to constraints on
            another node. The one node lives in a yarn, i.e. a set of candidate nodes,
            and the node at the other side of the edge lives in a yarn.

            If the first yarn is small then we might be able to reduce the second yarn
            by computing the counterparts of the nodes in the small yarn in the second
            yarn. We can leave out all other nodes from the second yarn.
            A big reduction!

            The success of edge spinning depends mainly on two factors:

            !!! info "Size difference"
                Edge spinning works best if there is a big difference in size
                between the candidate
                sets for the nodes at both sides of an edge.

            !!! info "Spread"
                The spread of a relation is the number of different edges
                that can start from the same node or end at the same node.

                For example, the spread of the `equality` operator is just 1, but
                the spread of the `inequality` operator is virtually as big
                as the relevant yarn.

                If there are constraints on a node in one yarn, and if there is an edge
                between that yarn and another one, and if the spread is big,
                not much of the constraint can be transferred to the other yarn.

            !!! example "Example"
                Suppose both yarns are words, the first yarn has been constrained
                to verbs, and the equality relation holds must hold between the yarns.
                Then in all results the node from the second yarn is also a verb.
                So we can constrain the second yarn to verbs too.

                But if the relation is inequality, we cannot impose any additional
                restriction on nodes in the second yarn. All nodes in the second
                yarn are unequal to at least one verb.

            !!! info "Estimating the spread"
                We estimate the spreads of edges over and over again, in a series
                of iterations where we reduce yarns.

                An exhaustive computation would be too expensive, so we take
                a sample of a limited amount of relation computations.


        If you do not pass a parameter, its value will not be changed.
        If you pass `None` for a parameter, its value will be reset to the default value.

        Here are the parameters that you can tweak:

        Parameters
        ----------

        yarnRatio: float
            The `yarnRatio` is the minimal factor between the sizes of
            the smallest and the biggest set of candidates of the nodes at both ends of
            the edge. And that divided by the spread of the relation as estimated
            by a sample.

            !!! example "Example"
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

        tryLimitFrom: integer
            In order to determine the spreads of the relations, TF takes
            random samples and extrapolates the results. We grab some nodes
            from the set at the *from* side of an edge, and some nodes at the
            *to* side of the same edge, Then we compute in how many cases the relation
            holds. That is a measure for the spread.

            The parameters `tryLimitFrom` and `tryLimitTo` dictate how big these
            samples are. The bigger, the better the estimation of the spread.
            But also the more work it is.

            If you find that your queries take consistently a tad too much time,
            consider lowering these parameters to 10.

            If you find that the times your queries take varies a lot,
            increase these values to 10000.
        tryLimitTo: integer
            See `tryLimitFrom`
        """

        api = self.api
        TF = api.TF
        error = TF.error
        info = TF.info
        isSilent = TF.isSilent
        setSilent = TF.setSilent
        defaults = self.perfDefaults

        wasSilent = isSilent()
        setSilent(silent)
        for (k, v) in kwargs.items():
            if k not in defaults:
                error(f'No such performance parameter: "{k}"', tm=False)
                continue
            if v is None:
                v = defaults[k]
            elif type(v) is not int and k != "yarnRatio":
                error(
                    f'Performance parameter "{k}" must be set to an integer, not to "{v}"',
                    tm=False,
                )
                continue
            self.perfParams[k] = v
        info("Performance parameters, current values:", tm=False)
        for (k, v) in sorted(self.perfParams.items()):
            info(f"\t{k:<20} = {v:>7}", tm=False)
        SearchExe.setPerfParams(self.perfParams)
        setSilent(wasSilent)

    def search(
        self,
        searchTemplate,
        limit=None,
        sets=None,
        shallow=False,
        silent=True,
        here=True,
        _msgCache=False,
    ):
        """Searches for combinations of nodes that together match a search template.

        If you can, you should use `tf.applib.search.search` instead.

        Parameters
        ----------
        searchTemplate: string
            A string that conforms to the rules described in `tf.about.searchusage`.

        shallow: set | tuple
            If `True` or `1`, the result is a set of things that match the
            top-level element of the `query`.

            If `2` or a bigger number *n*, return the set of truncated result tuples:
            only the first *n* members of each tuple is retained.

            If `False` or `0`, a sorted list of all result tuples will be returned.

        sets: dict
            If not `None`, it should be a dictionary of sets, keyed by a names.

        limit: integer, optional `None`
            If `limit` is a number, it will fetch only that many results.
        Returns
        -------
        generator | tuple
            Each result is a tuple of nodes, where each node corresponds to an
            *atom*-line in your search template.about.searchusage`).

            If `limit` is not `None`, a *generator* is returned,
            which yields the results one by one.

            Otherwise, the results will be fetched up till `limit`
            and delivered as a tuple.

        Notes
        -----
        !!! hint "More info on the search plan"
            Searching is complex. The search template must be parsed, interpreted,
            and translated into a search plan. See `tf.search.search.Search.study`.
        """

        exe = SearchExe(
            self.api,
            searchTemplate,
            outerTemplate=searchTemplate,
            quKind=None,
            offset=0,
            sets=sets,
            shallow=shallow,
            silent=silent,
            _msgCache=_msgCache,
            setInfo={},
        )
        if here:
            self.exe = exe
        queryResults = exe.search(limit=limit)
        if type(_msgCache) is list:
            messages = wrapMessages(_msgCache)
            return (queryResults, messages) if here else (queryResults, messages, exe)
        return queryResults

    def study(
        self, searchTemplate, strategy=None, sets=None, shallow=False, here=True,
    ):
        """Studies a template to prepare for searching with it.

        The search space will be narrowed down and a plan for retrieving the results
        will be set up.

        If the search template query has quantifiers, the asscociated search templates
        will be constructed and executed. These searches will be reported clearly.

        The resulting plan can be viewd by `tf.search.search.Search.showPlan`.

        Parameters
        ----------
        searchTemplate: string
            A string that conforms to the rules described in `tf.about.searchusage`.

        strategy: string
            In order to tame the performance of search, the strategy by which results
            are fetched matters a lot.  The search strategy is an implementation detail,
            but we bring it to the surface nevertheless.

            To see the names of the available strategies, just call
            `S.study('', strategy='x')` and you will get a list of options reported to
            choose from.

            Feel free to experiment. To see what the strategies do, see the
            code in `tf.search.stitch`.

        shallow: set | tuple
            If `True` or `1`, the result is a set of things that match the
            top-level element of the search template.

            If `2` or a bigger number *n*, return the set of truncated result tuples:
            only the first *n* members of each tuple is retained.

            If `False` or `0`, a sorted list of all result tuples will be returned.

        sets: dict
            If not `None`, it should be a dictionary of sets, keyed by a names.
            In the search template you can refer to those names to invoke those sets.

        silent: boolean, optional `None`
            If you want to suppress most of the output, say `silent=True`.

        See Also
        --------
        tf.about.searchusage: Search guide
        """

        exe = SearchExe(
            self.api,
            searchTemplate,
            outerTemplate=searchTemplate,
            quKind=None,
            offset=0,
            sets=sets,
            shallow=shallow,
            silent=False,
            showQuantifiers=True,
            setInfo={},
        )
        if here:
            self.exe = exe
        return exe.study(strategy=strategy)

    def fetch(self, limit=None, _msgCache=False):
        """Retrieves query results, up to a limit.

        Must be called after a previous `tf.search.search.Search.search()` or
        `tf.search.search.Search.study()`.

        Parameters
        ----------

        limit: integer, optional `None`
            If `limit` is a number, it will fetch only that many results.
        Returns
        -------
        generator | tuple
            Each result is a tuple of nodes, where each node corresponds to an
            *atom*-line in your search template.about.searchusage`).

            If `limit` is not `None`, a *generator* is returned,
            which yields the results one by one.

            Otherwise, the results will be fetched up till `limit`
            and delivered as a tuple.

        Notes
        -----
        !!! example "Iterating over the `fetch()` generator"
            You typically fetch results by saying:

                i = 0
                for tup in S.results():
                    do_something(tup[0])
                    do_something_else(tup[1])

            Alternatively, you can set the `limit` parameter, to ask for just so many
            results. They will be fetched, and when they are all collected,
            returned as a tuple.

        !!! example "Fetching a limited amount of results"
            This

                S.fetch(limit=10)

            gives you the first 10 results without further ado.
        """

        exe = self.exe
        TF = self.api.TF

        if exe is None:
            error = TF.error
            error('Cannot fetch if there is no previous "study()"')
        else:
            queryResults = exe.fetch(limit=limit)
            if type(_msgCache) is list:
                messages = TF.cache(_asString=True)
                return (queryResults, messages)
            return queryResults

    def count(self, progress=None, limit=None):
        """Counts the results, with progress messages, optionally up to a limit.

        Must be called after a previous `tf.search.search.Search.search()` or
        `tf.search.search.Search.study()`.

        Parameters
        ----------
        progress: integer, optional, default `100`
            Every once for every `progress` results a progress message is shown
            when fetching results.

        limit: integer, optional, default `1000`
            Fetch results up to this `limit`.
            Setting `limit` to 0 or a negative value means no limit: all results will be
            counted.

        !!! note "why needed"
            You typically need this in cases where result fetching turns out to
            be (very) slow.

        !!! caution "generator versus list"
            `len(S.results())` does not work in general, because `S.results()` is
            usually a generator that delivers its results as they come.

        Returns
        -------
        None
            The point of this function is to show the counting of the results
            on the screen in a series of timed messages.
        """

        exe = self.exe
        if exe is None:
            error = self.api.TF.error
            error('Cannot count if there is no previous "study()"')
        else:
            exe.count(progress=progress, limit=limit)

    def showPlan(self, details=False):
        """Show the result of the latest study of a template.

        Search results are tuples of nodes and the plan shows which part of the tuple
        corresponds to which part of the search template.

        Only meaningful after a previous `tf.search.search.Search.study`.

        Parameters
        ----------
        details: boolean, optional `False`
            If `True`, more information will be provided:
            an overview of the search space and a description of how the results
            will be retrieved.

        !!! note "after S.study()"
            This function is only meaningful after a call to `S.study()`.
        """

        exe = self.exe
        if exe is None:
            error = self.api.TF.error
            error('Cannot show plan if there is no previous "study()"')
        else:
            exe.showPlan(details=details)

    def relationsLegend(self):
        """Dynamic info about the basic relations that can be used in templates.

        It includes the edge features that are available in your dataset.

        Returns
        -------
        None
            The legend will be shown in the output.
        """

        exe = self.exe
        if exe is None:
            exe = SearchExe(self.api, "")
        console(exe.relationLegend)

    def glean(self, tup):
        """Renders a single result into something human readable.

        A search result is just a tuple of nodes that correspond to your template, as
        indicated by `showPlan()`. Nodes give you access to all information that the
        corpus has about it.

        This function is meant to just give you a quick first impression.

        Parameters
        ----------
        tup: tuple of int
            The tuple of nodes in question.

        Returns
        -------
        string
            The result indicats where the tuple occurs in terms of sections,
            and what text is associated with the tuple.

        Notes
        -----
        !!! example "Inspecting results"
            This

                for result in S.fetch(limit=10):
                    print(S.glean(result))

            is a handy way to get an impression of the first bunch of results.

        !!! hint "Universal"
            This function works on all tuples of nodes, whether they have been
            obtained by search or not.

        !!! hint "More ways of showing results"
            The advanced API offers much better ways of showing results.
            See `tf.applib.display.show` and `tf.applib.display.table`.
        """

        T = self.api.T
        F = self.api.F
        E = self.api.E
        fOtype = F.otype.v
        slotType = F.otype.slotType
        maxSlot = F.otype.maxSlot
        eoslots = E.oslots.data

        lR = len(tup)
        if lR == 0:
            return ""
        fields = []
        for (i, n) in enumerate(tup):
            otype = fOtype(n)
            words = [n] if otype == slotType else eoslots[n - maxSlot - 1]
            if otype == T.sectionTypes[2]:
                field = "{} {}:{}".format(*T.sectionFromNode(n))
            elif otype == slotType:
                field = T.text(words)
            elif otype in T.sectionTypes[0:2]:
                field = ""
            else:
                field = "{}[{}{}]".format(
                    otype, T.text(words[0:5]), "..." if len(words) > 5 else "",
                )
            fields.append(field)
        return " ".join(fields)
