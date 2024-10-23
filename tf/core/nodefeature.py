"""
# Mappings from nodes to values.

Every node feature is logically a mapping from nodes to values,
string or integer.

A feature object gives you methods that you can pass a node and that returns
its value for that node.

It is easiest to think of all node features as a dictionary keyed by nodes.

However, some features have an optimised representation, and do not have
a dictionary underneath.

But you can still iterate over the data of a feature as if it were a
dictionary: `tf.core.nodefeature.NodeFeature.items`
"""


import collections


class NodeFeatures:
    pass


class NodeFeature:
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

           data = dict(F.fff.items())

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

        This is an other way to walk through nodes than using
        `tf.core.nodes.Nodes.walk`.

        Parameters
        ----------
        value: integer | string
            The feature value that all resulting nodes have.

        Returns
        -------
        tuple of integer
            All nodes that have this value for this feature,
            sorted in the canonical order.
            (`tf.core.nodes`)
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
        nodeTypes: set of string, optional None
            If you pass a set of node types, only the values for nodes
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
