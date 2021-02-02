"""
# Access to *otype* feature data.

In general, features are stored as dictionaries, but this specific feature
has an optimized representation. Since it is a large feature and present
in any TF dataset, this pays off.

"""


class OtypeFeature(object):
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
        """As in `tf.core.nodefeature.NodeFeature.items`.
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

        This is an other way to walk through nodes than using
        `tf.core.nodes.Nodes.walk`.

        Parameters
        ----------
        val: int | string
            The node type that all resulting nodes have.

        Returns
        -------
        tuple of int
            All nodes that have this node type, sorted in the canonical order.
            (`tf.core.nodes`)
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
