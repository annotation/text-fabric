"""
.. include:: ../../docs/core/nodes.md
"""

import functools


GAP_START = "_gapStart_"
GAP_END = "_gapEnd_"


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

        self.sortKeyChunk = self.makeSortKeyChunk()
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

    def makeSortKeyChunk(self):
        api = self.api

        fOtype = api.F.otype
        otypeRank = self.otypeRank
        fOtypev = fOtype.v
        maxNode = fOtype.maxNode
        upperRank = len(otypeRank)

        def before(chunkA, chunkB):
            """Determines the order between two chunks

            Parameters
            ----------
            chunkA: tuple of string, set of int
            chunkB: tuple of string, set of int

            Notes
            -----
            The slot sets in both parameters will be compared.
            If they are equal, then the rank of the types of the nodes
            will be used to force a decision.
            """

            (nodeA, slotsA) = chunkA
            (nodeB, slotsB) = chunkB
            rankA = None
            rankB = None
            if nodeA == GAP_START:
                nodeA = 0
                rankA = -1
            elif nodeA == GAP_END:
                nodeA = maxNode + 1
                rankA = upperRank
            if nodeB == GAP_START:
                nodeB = 0
                rankB = -1
            elif nodeB == GAP_END:
                nodeB = maxNode + 1
                rankB = upperRank

            if rankA is None:
                rankA = otypeRank[fOtypev(nodeA)]
            if rankB is None:
                rankB = otypeRank[fOtypev(nodeB)]

            if slotsA == slotsB:
                return (
                    (-1 if nodeA < nodeB else 1 if nodeA > nodeB else 0)
                    if rankA == rankB
                    else -1
                    if rankA > rankB
                    else 1
                )
            if slotsA > slotsB:
                return -1
            if slotsA < slotsB:
                return 1
            minA = min(slotsA - slotsB)
            minB = min(slotsB - slotsA)
            return -1 if minA < minB else 1 if minB < minA else None

        return functools.cmp_to_key(before)

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
