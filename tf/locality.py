class Locality(object):
  def __init__(self, api):
    self.api = api

  def u(self, n, otype=None):
    if n <= 0:
      return tuple()
    Fotype = self.api.F.otype
    maxNode = Fotype.maxNode
    if n > maxNode:
      return tuple()
    levUp = self.api.C.levUp.data

    if otype is None:
      return levUp[n - 1]
    else:
      return tuple(m for m in levUp[n - 1] if Fotype.v(m) == otype)

  def d(self, n, otype=None):
    Fotype = self.api.F.otype
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
      return sorted(
          levDown[n - maxSlot - 1] + Eoslots.s(n),
          key=lambda m: Crank[m - 1],
      )
    elif otype == slotType:
      return sorted(
          Eoslots.s(n),
          key=lambda m: Crank[m - 1],
      )
    else:
      return tuple(m for m in levDown[n - maxSlot - 1] if Fotype.v(m) == otype)

  def p(self, n, otype=None):
    if n <= 1:
      return tuple()
    Fotype = self.api.F.otype
    maxNode = Fotype.maxNode
    if n > maxNode:
      return tuple()

    maxSlot = Fotype.maxSlot
    Eoslots = self.api.E.oslots.data
    (firstNode, lastNode) = self.api.C.boundary.data

    myPrev = n - 1 if n <= maxSlot else Eoslots[n - maxSlot - 1][0] - 1
    if myPrev <= 0:
      return ()

    result = lastNode[myPrev - 1] + (myPrev, )

    if otype is None:
      return result
    else:
      return tuple(m for m in result if Fotype.v(m) == otype)

  def n(self, n, otype=None):
    if n <= 0:
      return tuple()
    Fotype = self.api.F.otype
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

    result = (myNext, ) + firstNode[myNext - 1]

    if otype is None:
      return result
    else:
      return tuple(m for m in result if Fotype.v(m) == otype)
