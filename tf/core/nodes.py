"""
# Node organization

This module is about ordering nodes in terms of the slot nodes they are attached to.

## Canonical Order

Nodes are linked to subsets of slots, and there is a canonical ordering
on subsets of integers that is inherited by the nodes.

The canonical order is a way to sort the nodes in your corpus in such a way
that you can enumerate all nodes in the order you encounter them if you
walk through your corpus.

Formally
:   A node *A* comes before a node *B* if *A* contains the smallest slot
    that occurs in only one of *A* and *B*.

Briefly this means:

*   embedder nodes come before the nodes that lie embedded in them;
*   earlier stuff comes before later stuff,
*   if a verse coincides with a sentence, the verse comes before the sentence,
    because verses generally contain sentences and not the other way round;
*   if two objects are intersecting, but none embeds the other, the one with the
    smallest slot that does not occur in the other, comes first.

!!! note "first things first, big things first"
    That means, roughly, that you start with a
    book node (Genesis), then a chapter node (Genesis 1), then a verse node, Genesis
    1:1, then a sentence node, then a clause node, a phrase node, and the first word
    node. Then follow all word nodes in the first phrase, then the phrase node of
    the second phrase, followed by the word nodes in that phrase. When ever you
    enter a higher structure, you will first get the node corresponding to that
    structure, and after that the nodes corresponding to the building blocks of that
    structure.

This concept follows the intuition that slot sets with smaller elements come
before slot set with bigger elements, and embedding slot sets come before
embedded slot sets. Hence, if you enumerate a set of nodes that happens to
constitute a tree hierarchy based on slot set embedding, and you enumerate those
nodes in the slot set order, you will walk the tree in pre-order.

This order is a modification of the one as described in (Doedens 1994, 3.6.3).

![fabric](../images/DoedensLO.png)

> Doedens, Crist-Jan (1994), *Text Databases. One Database Model and Several
> Retrieval Languages*, number 14 in Language and Computers, Editions Rodopi,
> Amsterdam, Netherlands and Atlanta, USA. ISBN: 90-5183-729-1,
> https://books.google.nl/books?id=9ggOBRz1dO4C. The order as defined by
> Doedens corresponds to walking trees in post-order.

For a lot of processing, it is handy to have a the stack of embedding elements
available when working with an element. That is the advantage of pre-order over
post-order. It is very much like SAX parsing in the XML world.
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
