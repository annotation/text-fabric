"""
.. include:: ../../docs/core/nodes.md
"""

import functools


class Nodes:
    def __init__(self, api):
        self.api = api
        C = api.C
        Crank = C.rank.data

        self.otypeRank = {d[0]: i for (i, d) in enumerate(reversed(C.levels.data))}
        """Dictionary that provides a ranking of the node types.

        The node types are ordered in `C.levels.data`, and if you reverse that list,
        you get the rank of a type by looking at the position in which that type occurs.

        The *slotType* has rank 0 (`otypeRank[F.otype.slotType] == 0`),
        and the more comprehensive a type is, the higher its rank.
        """

        self.sortKey = lambda n: Crank[n - 1]
        """Sort key function for the canonical ordering between nodes.


        !!! hint "usage"
            The following two pieces of code do the same thing:
            `sortNodes(nodeSet)` and `sorted(nodeSet, key=sortKey)`.

        See Also
        --------
        tf.core.nodes: canonical ordering
        tf.core.nodes.Nodes.sortNodes: sorting nodes
        """

        self.sortKeyTuple = lambda tup: tuple(Crank[n - 1] for n in tup)
        """Sort key function for the canonical ordering between tuples of nodes.
        It applies `sortKey` to each member of the tuple.
        Handy to sort search results. We can sort them in canonical order like this:

            sorted(results, key=lambda tup: tuple(sortKey(n) for n in tup))

        This is exactly what `sortKeyTuple` does, but then a bit more efficient:

            sorted(results, key=sortKeyTuple)

        See Also
        --------
        tf.core.nodes: canonical ordering
        """

        (sortKeyChunk, sortKeyChunkLength) = self.makeSortKeyChunk()

        self.sortKeyChunk = sortKeyChunk
        """Sort key function for the canonical ordering between chunks of nodes.

            sorted(chunks, key=sortKeyChunk)

        A chunk is a tuple consisting of a node and a subset of its slots.
        Mostly, this subset of slots is contiguous (no gaps), and mostly it is
        maximal: the slots immediately before and after the chunk do not belong to the node.

        But the sortkey also works if these conditions are not met.

        Notes
        -----
        The use case for this function is that we have a bunch of nodes,
        each linked to a set of slots.
        For each node, we have split its slot set in maximal contiguous parts, its chunks.
        Now we want to order those chunks in the canonical ordering.

        See Also
        --------
        tf.core.nodes: canonical ordering
        """

        self.sortKeyChunkLength = sortKeyChunkLength

    def makeSortKeyChunk(self):
        api = self.api

        fOtype = api.F.otype
        otypeRank = self.otypeRank
        fOtypev = fOtype.v

        def beforePosition(chunk1, chunk2):
            (n1, (b1, e1)) = chunk1
            (n2, (b2, e2)) = chunk2
            if b1 < b2:
                return -1
            elif b1 > b2:
                return 1

            r1 = otypeRank[fOtypev(n1)]
            r2 = otypeRank[fOtypev(n2)]

            if r1 > r2:
                return -1
            elif r1 < r2:
                return 1

            return (
                -1
                if e1 > e2
                else 1
                if e1 < e2
                else -1
                if n1 < n2
                else 1
                if n1 > n2
                else 0
            )

        def beforeLength(chunk1, chunk2):
            (n1, (b1, e1)) = chunk1
            (n2, (b2, e2)) = chunk2

            size1 = e1 - b1
            size2 = e2 - b2

            if size1 > size2:
                return -1
            elif size2 > size1:
                return 1
            elif b1 < b2:
                return -1
            elif b1 > b2:
                return 1

            r1 = otypeRank[fOtypev(n1)]
            r2 = otypeRank[fOtypev(n2)]

            if r2 > r1:
                return -1
            elif r1 > r2:
                return 1

            return (
                -1
                if n1 < n2
                else 1
                if n1 > n2
                else 0
            )

        return (
            functools.cmp_to_key(beforePosition),
            functools.cmp_to_key(beforeLength),
        )

    def sortNodes(self, nodeSet):
        """Delivers a tuple of nodes sorted by the *canonical ordering*.

        nodeSet: iterable
            An iterable of nodes to be sorted.

        See Also
        --------
        tf.core.nodes: canonical ordering
        """

        api = self.api

        Crank = api.C.rank.data
        return sorted(nodeSet, key=lambda n: Crank[n - 1])

    def walk(self):
        """Generates all nodes in the *canonical order*.
        (`tf.core.nodes`)

        By `walk()` you traverse all nodes of your corpus
        in a very natural order. See `tf.core.nodes`.

        !!! hint "More ways of walking"
            Under `tf.core.nodefeature.NodeFeatures` there is another convenient way
            to walk through subsets of nodes.

        Returns
        -------
        nodes: int
            One at a time.
        """

        api = self.api

        for n in api.C.order.data:
            yield n
