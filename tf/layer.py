class Layer(object):
    def __init__(self, api):
        self.api = api

    def u(self, n, otype=None):
        Fotype = self.api.F.otype
        levUp = self.api.C.levUp.data
        if otype == None:
            return levUp[n]
        else:
            return tuple(m for m in levUp[n] if Fotype.v(m) == otype) 

    def d(self, n, otype=None):
        Fotype = self.api.F.otype
        Eoslots = self.api.E.oslots
        Crank = self.api.C.rank.data
        levDown = self.api.C.levDown.data
        slotType = Fotype.slotType
        maxSlot = Fotype.maxSlot
        if n < maxSlot+1: return tuple()
        if otype == None:
            return sorted(
                levDown[n-maxSlot-1]+Eoslots.s(n),
                key=lambda n: Crank[n],
            )
        elif otype == slotType:
            return sorted(
                Eoslots.s(n),
                key=lambda n: Crank[n],
            )
        else:
            return tuple(m for m in levDown[n-maxSlot-1] if Fotype.v(m) == otype)


