SET_TYPES = {set, frozenset}


class Locality(object):
    def __init__(self, api):
        self.api = api

    def i(self, n, otype=None):
        api = self.api
        Fotype = api.F.otype
        maxSlot = Fotype.maxSlot
        if n <= maxSlot:
            return tuple()
        maxNode = Fotype.maxNode
        if n > maxNode:
            return tuple()
        sortNodes = api.sortNodes
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
