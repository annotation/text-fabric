"""
.. include:: ../../docs/core/api.md
"""

import collections
from .helpers import makeInverse, makeInverseVal, flattenToSet, console
from .locality import Locality
from .text import Text
from ..search.search import Search

API_REFS = dict(
    AllComputeds=("Computed", "computedall", "computed-data"),
    AllEdges=("Features", "edgeall", "edge-features"),
    AllFeatures=("Features", "nodeall", "node-features"),
    C=("Computed", "computed", "computed-data"),
    Call=("Computed", "computedall", "computed-data"),
    Computed=("Computed", "computed", "computed-data"),
    ComputedString=("Computed", "computedstr", "computed-data"),
    Cs=("Computed", "computedstr", "computed-data"),
    E=("Features", "edge", "edge-features"),
    Eall=("Features", "edgeall", "edge-features"),
    Edge=("Features", "edge", "edge-features"),
    EdgeString=("Features", "edgestr", "edge-features"),
    Es=("Features", "edgestr", "edge-features"),
    F=("Features", "node", "node-features"),
    Fall=("Features", "nodeall", "node-features"),
    Feature=("Features", "node", "node-features"),
    FeatureString=("Features", "nodestr", "node-features"),
    Fs=("Features", "nodestr", "node-features"),
    L=("Locality", "locality", "locality"),
    Locality=("Locality", "locality", "locality"),
    N=("Nodes", "generator", "navigating-nodes"),
    Nodes=("Nodes", "generator", "navigating-nodes"),
    S=("Search", "search", "search"),
    Search=("Search", "search", "search"),
    T=("Text", "text", "text"),
    TF=("Fabric", "fabric", "loading"),
    Text=("Text", "text", "text"),
    cache=("Misc", "cache", "messaging"),
    ensureLoaded=("Fabric", "ensure", "loading"),
    error=("Misc", "error", "messaging"),
    ignored=("Fabric", "ignored", "loading"),
    indent=("Misc", "indent", "messaging"),
    info=("Misc", "info", "messaging"),
    warning=("Misc", "warning", "messaging"),
    isSilent=("Misc", "isSilent", "messaging"),
    setSilent=("Misc", "setSilent", "messaging"),
    silentOn=("Misc", "silentOn", "messaging"),
    silentOff=("Misc", "silentOff", "messaging"),
    loadLog=("Fabric", "loadlog", "loading"),
    otypeRank=("Nodes", "rank", "navigating-nodes"),
    reset=("Misc", "reset", "messaging"),
    sortKey=("Nodes", "key", "navigating-nodes"),
    sortKeyTuple=("Nodes", "keyTuple", "navigating-nodes"),
    sortNodes=("Nodes", "sort", "navigating-nodes"),
)


class OtypeFeature(object):
    """Provides access to *otype* feature data.

    In general, features are stored as dictionaries, but this specific feature
    has an optimized representation. Since it is a large feature and present
    in any TF dataset, this pays off.
    """

    def __init__(self, api, metaData, data):
        self.api = api
        self.meta = metaData
        """Metadata of the feature.

        This is the information found in the lines starting with `@`
        in the `.tf` feature file.
        """

        self.data = data[0]
        self.maxSlot = data[1]
        """Last slot node in the corpus."""

        self.maxNode = data[2]
        """Last node node.in the corpus."""

        self.slotType = data[3]
        """The name of the slot type."""

        self.all = None
        """List of all node types from big to small."""

    def items(self):
        """As in `tf.core.api.NodeFeature.items`.
        """

        slotType = self.slotType
        maxSlot = self.maxSlot
        data = self.data

        for n in range(1, maxSlot + 1):
            yield (n, slotType)

        maxNode = self.maxNode

        shift = maxSlot + 1

        for n in range(maxSlot + 1, maxNode + 1):
            yield (n, data[n - shift])

    def v(self, n):
        """Get the node type of a node.

        Parameters
        ----------
        n: integer
            The node in question

        Returns
        -------
        string
            The node type of that node. All nodes have a node type, and it is
            always a string.
        """

        if n == 0:
            return None
        if n < self.maxSlot + 1:
            return self.slotType
        m = n - self.maxSlot
        if m <= len(self.data):
            return self.data[m - 1]
        return None

    def s(self, val):
        """Query all nodes having a specified node type.

        This is an other way to walk through nodes than using `N()`,
        see `tf.core.api.Api.N`.

        Parameters
        ----------
        val: int | string
            The node type that all resulting nodes have.

        Returns
        -------
        tuple of int
            All nodes that have this node type, sorted in the canonical order.
            (`tf.core.api`)
        """

        # NB: the support attribute has been added by precomputing __levels__
        if val in self.support:
            (b, e) = self.support[val]
            return range(b, e + 1)
        else:
            return ()

    def sInterval(self, val):
        """The interval of nodes having a specified node type.

        The nodes are organized in intervals of nodes with the same type.
        For each type there is only one such interval.
        The first interval, `1:maxSlot + 1` is reserved for the slot type.

        Parameters
        ----------
        val: int | string
            The node type in question.

        Returns
        -------
        2-tuple of int
            The start and end node of the interval of nodes with this type.
        """

        # NB: the support attribute has been added by precomputing __levels__
        if val in self.support:
            return self.support[val]
        else:
            return ()


class OslotsFeature(object):
    """Provides access to *oslots* feature data.

    In general, features are stored as dictionaries, but this specific feature
    has an optimized representation. Since it is a large feature and present
    in any TF dataset, this pays off.
    """

    def __init__(self, api, metaData, data):
        self.api = api
        self.meta = metaData
        """Metadata of the feature.

        This is the information found in the lines starting with `@`
        in the `.tf` feature file.
        """

        self.data = data[0]
        self.maxSlot = data[1]
        self.maxNode = data[2]

    def items(self):
        """A generator that yields the non-slot nodes with their slots.
        """

        maxSlot = self.maxSlot
        data = self.data
        maxNode = self.maxNode

        shift = maxSlot + 1

        for n in range(maxSlot + 1, maxNode + 1):
            yield (n, data[n - shift])

    def s(self, n):
        """Get the slots of a (non-slot) node.

        Parameters
        ----------
        node: integer
            The node whose slots must be retrieved.

        Returns
        -------
        tuple
            The slot nodes of the node in question, in canonical order.
            (`tf.core.api`)

            For slot nodes `n` it is the tuple `(n,)`.

            All non-slot nodes are linked to at least one slot.
        """

        if n == 0:
            return ()
        if n < self.maxSlot + 1:
            return (n,)
        m = n - self.maxSlot
        if m <= len(self.data):
            return self.data[m - 1]
        return ()


class NodeFeature(object):
    """Provides access to (node) feature data.

    For feature `fff` it is the result of `F.fff` or `Fs('fff')`.
    """

    def __init__(self, api, metaData, data):
        self.api = api
        self.meta = metaData
        """Metadata of the feature.

        This is the information found in the lines starting with `@`
        in the `.tf` feature file.
        """

        self.data = data

    def items(self):
        """A generator that yields the items of the feature, seen as a mapping.

        It does not yield entries for nodes without values,
        so this gives you a rather efficient way to iterate over
        just the feature data, instead of over all nodes.

        If you need this repeatedly, or you need the whole dictionary,
        you can store the result as follows:

        `data = dict(F.fff.items())`
        """

        return self.data.items()

    def v(self, n):
        """Get the value of a feature for a node.

        Parameters
        ----------
        n: integer
            The node in question

        Returns
        -------
        integer | string | None
            The value of the feature for that node, if it is defined, else `None`.
        """

        if n in self.data:
            return self.data[n]
        return None

    def s(self, val):
        """Query all nodes having a specified feature value.

        This is an other way to walk through nodes than using `N()`,
        see `tf.core.api.Api.N`.

        Parameters
        ----------
        value: int | string
            The feature value that all resulting nodes have.

        Returns
        -------
        tuple of int
            All nodes that have this value for this feature,
            sorted in the canonical order.
            (`tf.core.api`)
        """

        Crank = self.api.C.rank.data
        return tuple(
            sorted(
                [n for n in self.data if self.data[n] == val],
                key=lambda n: Crank[n - 1],
            )
        )

    def freqList(self, nodeTypes=None):
        """Frequency list of the values of this feature.

        Inspect the values of this feature and see how often they occur.

        Parameters
        ----------
        nodeTypes: set of string, optional `None`
            If you pass a set of nodeTypes, only the values for nodes
            within those types will be counted.

        Returns
        -------
        tuple of 2-tuple
            A tuple of `(value, frequency)`, items, ordered by `frequency`,
            highest frequencies first.

        """

        fql = collections.Counter()
        if nodeTypes is None:
            for n in self.data:
                fql[self.data[n]] += 1
        else:
            fOtype = self.api.F.otype.v
            for n in self.data:
                if fOtype(n) in nodeTypes:
                    fql[self.data[n]] += 1
        return tuple(sorted(fql.items(), key=lambda x: (-x[1], x[0])))


class EdgeFeature(object):
    """Provides access to (edge) feature data.

    For feature `fff` it is the result of `E.fff` or `Es('fff')`.
    """

    def __init__(self, api, metaData, data, doValues):
        self.api = api
        self.meta = metaData
        """Metadata of the feature.

        This is the information found in the lines starting with `@`
        in the `.tf` feature file.
        """

        self.doValues = doValues
        if type(data) is tuple:
            self.data = data[0]
            self.dataInv = data[1]
        else:
            self.data = data
            self.dataInv = (
                makeInverseVal(self.data) if doValues else makeInverse(self.data)
            )

    def items(self):
        """A generator that yields the items of the feature, seen as a mapping.

        This gives you a rather efficient way to iterate over
        just the feature data.

        If you need this repeatedly, or you need the whole dictionary,
        you can store the result as follows:

        `data = dict(E.fff.items())`
        """

        return self.data.items()

    def f(self, n):
        """Get outgoing edges *from* a node.

        The edges are those pairs of nodes specified in the feature data,
        whose first node is the `n`.

        Parameters
        ----------
        node: integer
            The node **from** which the edges in question start.

        Returns
        -------
        set | dict
            The nodes reached by the edges **from** a certain node.
            The members of the result are just nodes, if this feature does not
            assign values to edges.
            Otherwise the members are tuples of the destination node and the
            value that the feature assigns to this pair of nodes.

            If there are no edges from the node, the empty tuple is returned,
            rather than `None`.
        """

        if n not in self.data:
            return ()
        Crank = self.api.C.rank.data
        if self.doValues:
            return tuple(sorted(self.data[n].items(), key=lambda mv: Crank[mv[0] - 1]))
        else:
            return tuple(sorted(self.data[n], key=lambda m: Crank[m - 1]))

    def t(self, n):
        """Get incoming edges *to* a node.

        The edges are those pairs of nodes specified in the feature data,
        whose second node is the `n`.

        Parameters
        ----------
        node: integer
            The node **to** which the edges in question connect.

        Returns
        -------
        set | dict
            The nodes where the edges **to** a certain node start.
            The members of the result are just nodes, if this feature does not
            assign values to edges.
            Otherwise the members are tuples of the start node and the
            value that the feature assigns to this pair of nodes.

            If there are no edges to the node, the empty tuple is returned,
            rather than `None`.
        """

        if n not in self.dataInv:
            return ()
        Crank = self.api.C.rank.data
        if self.doValues:
            return tuple(
                sorted(self.dataInv[n].items(), key=lambda mv: Crank[mv[0] - 1])
            )
        else:
            return tuple(sorted(self.dataInv[n], key=lambda m: Crank[m - 1]))

    def b(self, n):
        """Query *both* incoming edges to, and outgoing edges from a node.

        The edges are those pairs of nodes specified in the feature data,
        whose first or second node is the `n`.

        Parameters
        ----------
        node: integer
            The node **from** which the edges in question start or
            **to** which the edges in question connect.

        Returns
        -------
        set | dict
            The nodes where the edges **to** a certain node start.
            The members of the result are just nodes, if this feature does not
            assign values to edges.
            Otherwise the members are tuples of the start node and the
            value that the feature assigns to this pair of nodes.

            If there are no edges to the node, the empty tuple is returned,
            rather than `None`.

        !!! hint "symmetric closure"
            This method gives the *symmetric closure* of a set of edges:
            if there is an edge between *n* and *m*, this method will deliver
            its value, no matter the direction of the edge.

        !!! example "symmetric edges"
            Some edge sets are semantically symmetric, for example *similarity*.
            If *n* is similar to *m*, then *m* is similar to *n*.

            But if you store such an edge feature completely,
            half of the data is redundant.
            By virtue of this method you do not have to do that, you only need to store
            one of the edges between *n* and *m* (it does not matter which one),
            and `E.fff.b(n)` will nevertheless produce the complete results.

        !!! caution "conflicting values"
            If your set of edges is not symmetric, and edges carry values, it might
            very well be the case that edges between the same pair of nodes carry
            different values for the two directions.

            In that case, this method gives precedence to the edges that
            *depart* from the node to those that go *to* the node.

        !!! example "conflicting values"
            Suppose we have

            ```
            n == value=4 ==> m
            m == value=6 ==> n
            ```
            then
            ```
            E.b(n) = (m, 4)
            E.b(m) = (n, 6)
            ```
        """

        if n not in self.data and n not in self.dataInv:
            return ()
        Crank = self.api.C.rank.data
        if self.doValues:
            result = {}
            if n in self.dataInv:
                result.update(self.dataInv[n].items())
            if n in self.data:
                result.update(self.data[n].items())
            return tuple(sorted(result.items(), key=lambda mv: Crank[mv[0] - 1]))
        else:
            result = set()
            if n in self.dataInv:
                result |= self.dataInv[n]
            if n in self.data:
                result |= self.data[n]
            return tuple(sorted(result, key=lambda m: Crank[m - 1]))

    def freqList(self, nodeTypesFrom=None, nodeTypesTo=None):
        """Frequency list of the values of this feature.

        Inspect the values of this feature and see how often they occur.

        If the feature does not assign values, return the number of node pairs
        in this edge.

        If the edge feature does have values, inspect them and see
        how often they occur.
        The result is a list of pairs `(value, frequency)`, ordered by `frequency`,
        highest frequencies first.

        Parameters
        ----------
        nodeTypesFrom: set of string, optional `None`
            If you pass a set of nodeTypes here, only the values for edges
            that start *from* a node with such a type will be counted.
        nodeTypesTo: set of string, optional `None`
            If you pass a set of nodeTypes here, only the values for edges
            that go *to* a node with such a type will be counted.

        Returns
        -------
        tuple of 2-tuple
            A tuple of `(value, frequency)`, items, ordered by `frequency`,
            highest frequencies first.

        """

        if nodeTypesFrom is None and nodeTypesTo is None:
            if self.doValues:
                fql = collections.Counter()
                for (n, vals) in self.data.items():
                    for val in vals.values():
                        fql[val] += 1
                return tuple(sorted(fql.items(), key=lambda x: (-x[1], x[0])))
            else:
                fql = 0
                for (n, ms) in self.data.items():
                    fql += len(ms)
                return fql
        else:
            fOtype = self.api.F.otype.v
            if self.doValues:
                fql = collections.Counter()
                for (n, vals) in self.data.items():
                    if nodeTypesFrom is None or fOtype(n) in nodeTypesFrom:
                        for (m, val) in vals.items():
                            if nodeTypesTo is None or fOtype(m) in nodeTypesTo:
                                fql[val] += 1
                return tuple(sorted(fql.items(), key=lambda x: (-x[1], x[0])))
            else:
                fql = 0
                for (n, ms) in self.data.items():
                    if nodeTypesFrom is None or fOtype(n) in nodeTypesFrom:
                        for m in ms:
                            if nodeTypesTo is None or fOtype(m) in nodeTypesTo:
                                fql += len(ms)
                return fql


class Computed(object):
    """Provides access to precomputed data.

    For component `ccc` it is the result of `C.ccc` or `Cs('ccc')`.
    """

    def __init__(self, api, data):
        self.api = api
        self.data = data


class NodeFeatures(object):
    """Mappings from nodes to values.

    Every node feature is logically a mapping from nodes to values,
    string or integer.

    A feature object gives you methods that you can pass a node and that returns
    its value for that node.

    It is easiest to think of all node features as a dictionary keyed by nodes.

    However, some features have an optimized representation, and do not have
    a dictionary underneath.

    But you can still iterate over the data of a feature as if it were a
    dictionary: `tf.core.api.NodeFeature.items`
    """


class EdgeFeatures(object):
    """Mappings from edges to values.

    Every edge feature is logically a mapping from pairs of nodes to values,
    string or integer.

    A feature object gives you methods that you can pass a node and that returns
    its value for that node.

    It is easiest to think of all edge features as a dictionary keyed by nodes.
    The values are either sets or dictionaries.
    If the value is a set, then the elements are the second node in the pair
    and the value is `None`.
    If the value is a dictionary, then the keys are the second node in the pair,
    and the value is the value that the edge feature assigns to this pair.

    However, some features have an optimized representation, and do not have
    a dictionary underneath.

    But you can still iterate over the data of a feature as if it were a
    dictionary: `tf.core.api.EdgeFeature.items`
    """


class Computeds(object):
    """Precomputed data components.

    In order to make the API work, Text-Fabric prepares some data and saves it in
    quick-load format. Most of this data are the features, but there is some extra
    data needed for the special functions of the `tf.core.data.WARP` features and the
    `tf.core.locality.Locality` API.

    Normally, you do not use this data, but since it is there, it might be valuable,
    so we have made it accessible in the `tf.core.api.Computeds`-api.

    !!! explanation "Pre-computed data storage"
        Pre-computed data is stored in cache directories in a directory `.tf`
        inside the directory where the `otype` feature is encountered.

        After precomputation the result is pickled and gzipped and written to a
        `.tfx` file with the same name as the name of the feature.
        This is done for nromal features and pre-computed features likewise.

        After version 7.7.7 version the memory footprint of some precomputed features
        has been reduced. Because the precomputed features on disk are exact replicas
        of the precomputed features in RAM, older precomputed data does not work with
        versions of TF after 7.7.7.

        But from that version onwards, there is a parameter,
        `tf.parameters.PACK_VERSION` to detect incompatibilities.
    """


class Api(object):
    def __init__(self, TF):
        self.TF = TF
        self.ignored = tuple(sorted(TF.featuresIgnored))
        """Which features were found but ignored.

        Features are ignored if the feature is also present in another location
        that is loaded later.
        """

        self.F = NodeFeatures()
        self.Feature = self.F
        self.E = EdgeFeatures()
        self.Edge = self.E
        self.C = Computeds()
        self.Computed = self.C
        tm = TF.tm
        self.silentOn = tm.silentOn
        self.silentOff = tm.silentOff
        self.isSilent = tm.isSilent
        self.setSilent = tm.setSilent
        self.info = tm.info
        self.warning = tm.warning
        self.error = tm.error
        self.cache = tm.cache
        self.reset = tm.reset
        self.indent = tm.indent
        self.loadLog = tm.cache
        """All messages produced during the feature loading process.

        It also shows the messages that have been suppressed due to the `silent`
        parameter.
        """

        self.sortKey = None
        """Sort key function for the canonical ordering between nodes.

        See `tf.core.api` and `sortNodes`.

        !!! hint "usage"
            The following two pieces of code do the same thing:
            `sortNodes(nodeSet)` and `sorted(nodeSet, key=sortKey)`.
        """

        self.sortKeyTuple = None
        """Sort key function for the canonical ordering between tuples of nodes.
        It applies `sortKey` to each member of the tuple.
        Handy to sort search results. We can sort them in canonical order like this:

        ```python
        sorted(results, key=lambda tup: tuple(sortKey(n) for n in tup))
        ```

        This is exactly what `sortKeyTuple` does, but then a bit more efficient:

        ```python
        sorted(results, key=sortKeyTuple)
        ```
        """

        self.otypeRank = None
        """Dictionary that provides a ranking of the node types.

        The node types are ordered in `C.levels.data`, and if you reverse that list,
        you get the rank of a type by looking at the position in which that type occurs.

        The *slotType* has rank 0 (`otypeRank[F.otype.slotType] == 0`),
        and the more comprehensive a type is, the higher its rank.
        """

        setattr(self, "FeatureString", self.Fs)
        setattr(self, "EdgeString", self.Es)
        setattr(self, "ComputedString", self.Cs)
        setattr(self, "Nodes", self.N)
        setattr(self, "AllFeatures", self.Fall)
        setattr(self, "AllEdges", self.Eall)
        setattr(self, "AllComputeds", self.Call)

    def Fs(self, fName):
        """Get the node feature sub API.

        If feature name is not a valid python identifier,
        or if you do not know its name in advance,
        you can not use `F.feature`, but you should use
        `Fs(feature)`.
        """

        if not hasattr(self.F, fName):
            self.error(f'Node feature "{fName}" not loaded')
            return None
        return getattr(self.F, fName)

    def Es(self, fName):
        """Get the edge feature sub API.

        If feature name is not a valid python identifier,
        or if you do not know its name in advance,
        you can not use `E.feature`, but you should use
        `Es(feature)`.
        """

        if not hasattr(self.E, fName):
            self.error(f'Edge feature "{fName}" not loaded')
            return None
        return getattr(self.E, fName)

    def Cs(self, fName):
        """Get the computed data sub API.

        If component name is not a valid python identifier,
        or if you do not know its name in advance,
        you can not use `C.component`, but you should use
        `Cs(component)`.
        """

        if not hasattr(self.C, fName):
            self.error(f'Computed feature "{fName}" not loaded')
            return None
        return getattr(self.C, fName)

    def N(self):
        """Generates all nodes in the *canonical order*.
        (`tf.core.api`)

        Iterating over `N()` delivers you all nodes of your corpus
        in a very natural order. See `tf.core.api.Api`.

        !!! hint "More ways of walking"
            Under `tf.core.api.NodeFeatures` there is another convenient way
            to walk through subsets of nodes.

        Returns
        -------
        nodes: int
            One at a time.
        """

        for n in self.C.order.data:
            yield n

    def sortNodes(self, nodeSet):
        """Delivers a tuple of nodes sorted by the *canonical ordering*.

        See `tf.core.api`.

        nodeSet: iterable
            An iterable of nodes to be sorted.
        """

        Crank = self.C.rank.data
        return sorted(nodeSet, key=lambda n: Crank[n - 1])

    def Fall(self):
        """Returns a sorted list of all usable, loaded node feature names.
        """

        return sorted(x[0] for x in self.F.__dict__.items())

    def Eall(self):
        """Returns a sorted list of all usable, loaded edge feature names.
        """

        return sorted(x[0] for x in self.E.__dict__.items())

    def Call(self):
        """Returns a sorted list of all usable, loaded computed data names.
        """

        return sorted(x[0] for x in self.C.__dict__.items())

    def makeAvailableIn(self, scope):
        """Exports every member of the API to the global namespace.

        If you are working with a single data source in your program, it is a bit
        tedious to write the initial `TF.api.` or `A.api` all the time.
        By this method you can avoid that.

        !!! explanation "Longer names"
            There are also longer names which can be used as aliases
            to the single capital letters.
            This might or might not improve the readability of your program.

            short name | long name
            --- | ---
            `N` | `Nodes`
            `F` | `Feature`
            `Fs` | `FeatureString`
            `Fall`  `AllFeatures`
            `E` | `Edge`
            `Es` | `EdgeString`
            `Eall`  `AllEdges`
            `C` | `Computed`
            `Cs`  `ComputedString`
            `Call`  `AllComputeds`
            `L` | `Locality`
            `T` | `Text`
            `S` | `Search`

        Parameters
        ----------
        scope: dict
            A dictionary into which the members of the core API will be inserted.
            The only sensible choice is: `globals()`.

        Returns
        -------
        tuple
            A grouped list of API members that has been hoisted to the global
            scope.

        !!! explanation "Why pass `globals()`?"
            Although we know it should always be `globals()`, we cannot
            define a function that looks into the `globals()` of its caller.
            So we have to pass it on.
        """

        for member in dir(self):
            if "_" not in member and member != "makeAvailableIn":
                scope[member] = getattr(self, member)
                if member not in API_REFS:
                    console(f'WARNING: API member "{member}" not documented')

        grouped = {}
        for (member, (head, sub, ref)) in API_REFS.items():
            grouped.setdefault(ref, {}).setdefault((head, sub), []).append(member)

        # grouped
        # node-features=>(Features, node)=>[F, ...]

        docs = []
        for (ref, groups) in sorted(grouped.items()):
            chunks = []
            for ((head, sub), members) in sorted(groups.items()):
                chunks.append(" ".join(sorted(members, key=lambda x: (len(x), x))))
            docs.append((head, ref, tuple(chunks)))
        return docs

    # docs
    # (Features, node-features, ('F ...', ...))

    def ensureLoaded(self, features):
        """Checks if features are loaded and if not loads them.

        All features in question will be made available to the core API.

        Parameters
        ----------
        features: string | iterable of strings
            It is a string containing space separated feature names,
            or an iterable of feature names.
            The feature names are just the names of `.tf` files
            without directory information and without extension.

        Returns
        -------
        set
            The names of the features in question as a set of strings.
        """

        F = self.F
        E = self.E
        TF = self.TF
        warning = self.warning

        needToLoad = set()
        loadedFeatures = set()

        for fName in sorted(flattenToSet(features)):
            fObj = TF.features.get(fName, None)
            if not fObj:
                warning(f'Cannot load feature "{fName}": not in dataset')
                continue
            if fObj.dataLoaded and (hasattr(F, fName) or hasattr(E, fName)):
                loadedFeatures.add(fName)
            else:
                needToLoad.add(fName)
        if len(needToLoad):
            TF.load(
                needToLoad, add=True, silent="deep",
            )
            loadedFeatures |= needToLoad
        return loadedFeatures


def addSortKey(api):
    Crank = api.C.rank.data
    api.sortKey = lambda n: Crank[n - 1]
    api.sortKeyTuple = lambda tup: tuple(Crank[n - 1] for n in tup)


def addOtype(api):
    setattr(api.F.otype, "all", tuple(o[0] for o in api.C.levels.data))
    setattr(
        api.F.otype, "support", dict(((o[0], (o[2], o[3])) for o in api.C.levels.data))
    )


def addLocality(api):
    api.L = Locality(api)
    api.Locality = api.L


def addRank(api):
    C = api.C
    api.otypeRank = {d[0]: i for (i, d) in enumerate(reversed(C.levels.data))}


def addText(api):
    api.T = Text(api)
    api.Text = api.T


def addSearch(api, silent):
    api.S = Search(api, silent)
    api.Search = api.S
