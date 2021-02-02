"""
Mappings from edges to values.

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
dictionary: `tf.core.edgefeature.EdgeFeature.items`
"""

import collections

from .helpers import makeInverse, makeInverseVal


class EdgeFeatures(object):
    pass


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

           data = dict(E.fff.items())

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

        Notes
        -----
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

                n == value=4 ==> m
                m == value=6 ==> n

            then

                E.b(n) = (m, 4)
                E.b(m) = (n, 6)

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
