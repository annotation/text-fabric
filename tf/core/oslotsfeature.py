"""
# Access to *oslots* feature data.

In general, features are stored as dictionaries, but this specific feature
has an optimized representation. Since it is a large feature and present
in any TF dataset, this pays off.
"""


class OslotsFeature(object):
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
            (`tf.core.nodes`)

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
