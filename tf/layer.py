class Layer(object):
    def __init__(self, api):
        self.api = api

    def u(self, n, otype=None):
        if n <= 0: return tuple()
        Fotype = self.api.F.otype
        maxNode = Fotype.maxNode
        if n > maxNode: return tuple()
        levUp = self.api.C.levUp.data

        if otype == None:
            return levUp[n-1]
        else:
            return tuple(m for m in levUp[n-1] if Fotype.v(m) == otype) 

    def d(self, n, otype=None):
        Fotype = self.api.F.otype
        maxSlot = Fotype.maxSlot
        if n <= maxSlot: return tuple()
        maxNode = Fotype.maxNode
        if n > maxNode: return tuple()

        Eoslots = self.api.E.oslots
        Crank = self.api.C.rank.data
        levDown = self.api.C.levDown.data
        slotType = Fotype.slotType
        if otype == None:
            return sorted(
                levDown[n-maxSlot-1]+Eoslots.s(n),
                key=lambda m: Crank[m-1],
            )
        elif otype == slotType:
            return sorted(
                Eoslots.s(n),
                key=lambda m: Crank[m-1],
            )
        else:
            return tuple(m for m in levDown[n-maxSlot-1] if Fotype.v(m) == otype)


