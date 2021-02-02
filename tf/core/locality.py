"""
# Local navigation between nodes.
"""


SET_TYPES = {set, frozenset}


class Locality(object):
    """Methods by which you can navigate from a node to its neighborhood.

    Neighbours are: nodes that have slots in common, embedders and embeddees,
    previous and next siblings.

    !!! note "L"
        The Locality API is exposed as `L` or `Locality`.

    !!! note "otype parameter"
        In all of the following `L`-functions, if the `otype` parameter is passed,
        the result is filtered and only nodes with
        `otype=nodeType` or `otype in nodeTypes` are retained.

        `otype` can be a string (a single node type)  or a (frozen)set of node types.

    !!! caution "Results of the `L.` functions are tuples, not single nodes"
          Even if an `L`-function returns a single node, it is packed in a *tuple*.
          So to get the node itself, you have to dereference the tuple:

              L.u(node)[0]

    !!! caution "Locality and node types"
        When using `tf.core.nodes.Nodes.sortNodes` and the `L` methods,
        note the following.

        Suppose you have node types `verse` and `sentence`, and usually a
        verse has multiple sentences, but not vice versa. Then you expect that

        *   `L.d(verseNode)` will contain sentence nodes,
        *   `L.d(sentenceNode)` will **not** contain verse nodes.

        But if there is a verse with exactly one sentence, and both have exactly the
        same words, then that is a case where:

        *   `L.d(verseNode)` will contain `sentenceNode`,
        *   `L.d(sentenceNode)` will contain `verseNode`.
      """

    def __init__(self, api):
        self.api = api

    def i(self, n, otype=None):
        """Produces an ordered tuple of *intersecting* nodes

        Intersecting nodes of a node have slots in common with that node.

        Parameters
        ----------

        node: dict
            The node whose intersectors will be delivered.
        otype: string or set of strings
            See `Locality`.

        Returns
        -------
        tuple of int
            The tuple nodes is sorted in the
            canonical order (`tf.core.nodes`).

            The result never includes *n* itself.
            But other nodes linked to the same set of slots as *n*
            may count as intersector nodes.

            Slots themselves can be intersectors.
        """

        api = self.api
        N = api.N
        Fotype = api.F.otype
        maxSlot = Fotype.maxSlot
        if n <= maxSlot:
            return tuple()
        maxNode = Fotype.maxNode
        if n > maxNode:
            return tuple()
        sortNodes = N.sortNodes
        if not otype:
            otype = set(Fotype.all)
        elif type(otype) is str:
            otype = {otype}
        elif type(otype) not in SET_TYPES:
            otype = set(otype)

        slotType = Fotype.slotType
        fOtype = Fotype.v
        levUp = api.C.levUp.data
        Eoslots = api.E.oslots

        slots = Eoslots.s(n)
        result = set()
        for slot in slots:
            result |= {m for m in levUp[slot - 1] if fOtype(m) in otype}
            if slotType in otype:
                result.add(slot)
        return sortNodes(result - {n})

    def u(self, n, otype=None):
        """Produces an ordered tuple of *upward* nodes.

        Upward nodes of a node are embedders of that node.
        One node embeds an other if all slots of the latter are contained in the slots
        of the former.

        node: integer
            The node whose embedders will be delivered.
        otype: string or set of strings
            See `Locality`.

        Returns
        -------
        tuple of int
            The tuple nodes is sorted in the canonical order (`tf.core.nodes`),
            but *reversed*: right and small embedders before left and big embedders.

            The result never includes *n* itself.
            But other nodes linked to the same set of slots as *n*
            may count as embedder nodes.

            Slots themselves are never embedders.
        """

        if n <= 0:
            return tuple()
        Fotype = self.api.F.otype
        maxNode = Fotype.maxNode
        if n > maxNode:
            return tuple()
        fOtype = Fotype.v
        levUp = self.api.C.levUp.data

        if otype is None:
            return tuple(levUp[n - 1])
        elif type(otype) is str:
            return tuple(m for m in levUp[n - 1] if fOtype(m) == otype)
        else:
            if type(otype) not in SET_TYPES:
                otype = set(otype)
            return tuple(m for m in levUp[n - 1] if fOtype(m) in otype)

    def d(self, n, otype=None):
        """Produces an ordered tuple of *downward* nodes.

        Downward nodes of a node are embedded nodes in that node.
        One node is embedded in an other if all slots of the former are contained
        in the slots of the latter.

        node: integer
            The node whose embeddees will be delivered.
        otype: string or set of strings
            See `Locality`.

        Returns
        -------
        tuple of int
            The tuple nodes is sorted in the canonical order (`tf.core.nodes`),
            left and big embeddees before right and small embeddees.

            The result never includes *n* itself.
            But other nodes linked to the same set of slots as *n*
            may count as embeddee nodes.
        """

        Fotype = self.api.F.otype
        fOtype = Fotype.v
        maxSlot = Fotype.maxSlot
        if n <= maxSlot:
            return tuple()
        maxNode = Fotype.maxNode
        if n > maxNode:
            return tuple()

        Eoslots = self.api.E.oslots
        Crank = self.api.C.rank.data
        levDown = self.api.C.levDown.data
        slotType = Fotype.slotType
        if otype is None:
            return tuple(
                sorted(
                    levDown[n - maxSlot - 1] + Eoslots.s(n), key=lambda m: Crank[m - 1],
                )
            )
        elif otype == slotType:
            return tuple(sorted(Eoslots.s(n), key=lambda m: Crank[m - 1]))
        elif type(otype) is str:
            return tuple(m for m in levDown[n - maxSlot - 1] if fOtype(m) == otype)
        else:
            if type(otype) not in SET_TYPES:
                otype = set(otype)
            return tuple(
                sorted(
                    (
                        k
                        for k in levDown[n - maxSlot - 1] + Eoslots.s(n)
                        if fOtype(k) in otype
                    ),
                    key=lambda m: Crank[m - 1],
                )
            )

    def p(self, n, otype=None):
        """Produces an ordered tuple of *previous* nodes.

        One node is previous to an other if the last slot of the former just preceeds
        the first slots of the latter.

        node: integer
            The node whose previous nodes will be delivered.
        otype: string or set of strings
            See `Locality`.

        Returns
        -------
        tuple of int
            The tuple nodes is sorted in the canonical order (`tf.core.nodes`),
            but *reversed*: right and small embedders before left and big embedders.
        """

        if n <= 1:
            return tuple()
        Fotype = self.api.F.otype
        fOtype = Fotype.v
        maxNode = Fotype.maxNode
        if n > maxNode:
            return tuple()

        maxSlot = Fotype.maxSlot
        Eoslots = self.api.E.oslots.data
        (firstNode, lastNode) = self.api.C.boundary.data

        myPrev = n - 1 if n <= maxSlot else Eoslots[n - maxSlot - 1][0] - 1
        if myPrev <= 0:
            return ()

        result = tuple(lastNode[myPrev - 1]) + (myPrev,)

        if otype is None:
            return result
        elif type(otype) is str:
            return tuple(m for m in result if fOtype(m) == otype)
        else:
            if type(otype) not in SET_TYPES:
                otype = set(otype)
            return tuple(m for m in result if fOtype(m) in otype)

    def n(self, n, otype=None):
        """Produces an ordered tuple of *next* nodes.

        One node is next to an other if the first slot of the former just follows
        the last slot of the latter.

        node: integer
            The node whose next nodes will be delivered.
        otype: string or set of strings
            See `Locality`.

        Returns
        -------
        tuple of int
            The tuple nodes is sorted in the canonical order (`tf.core.nodes`),
            left and big embeddees before right and small embeddees.
        """

        if n <= 0:
            return tuple()
        Fotype = self.api.F.otype
        fOtype = Fotype.v
        maxNode = Fotype.maxNode
        maxSlot = Fotype.maxSlot
        if n == maxSlot:
            return tuple()
        if n > maxNode:
            return tuple()

        Eoslots = self.api.E.oslots.data
        (firstNode, lastNode) = self.api.C.boundary.data

        myNext = n + 1 if n < maxSlot else Eoslots[n - maxSlot - 1][-1] + 1
        if myNext > maxSlot:
            return ()

        result = (myNext,) + tuple(firstNode[myNext - 1])

        if otype is None:
            return result
        elif type(otype) is str:
            return tuple(m for m in result if fOtype(m) == otype)
        else:
            if type(otype) not in SET_TYPES:
                otype = set(otype)
            return tuple(m for m in result if fOtype(m) in otype)
