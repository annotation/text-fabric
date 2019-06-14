import collections
from array import array
import types
import re
from itertools import chain

from ..core.data import WARP
from ..core.helpers import makeIndex
from .syntax import reTp

# LOW-LEVEL NODE RELATIONS SEMANTICS ###


OTYPE = WARP[0]
OSLOTS = WARP[1]


def basicRelations(searchExe, api):
  C = api.C
  F = api.F
  Fs = api.Fs
  E = api.E
  Crank = C.rank.data
  ClevDown = C.levDown.data
  ClevUp = C.levUp.data
  (CfirstSlots, ClastSlots) = C.boundary.data
  Eoslots = E.oslots.data
  slotType = F.otype.slotType
  maxSlot = F.otype.maxSlot
  maxSlotP = maxSlot + 1
  sets = searchExe.sets
  setInfo = searchExe.setInfo
  searchExe.featureValueIndex = {}
  Sindex = searchExe.featureValueIndex

  def isSlotType(nType):
    if sets is not None and nType in sets:
      if nType in setInfo:
        return setInfo[nType]
      nodes = sets[nType]
      allSlots = all(n < maxSlotP for n in nodes)
      if allSlots:
        setInfo[nType] = True
        return True
      allNonSlots = all(n > maxSlot for n in nodes)
      if allNonSlots:
        setInfo[nType] = False
        return False
      setInfo[nType] = None
      return None
    return nType == slotType

  # EQUAL

  def spinEqual(fTp, tTp):

    def doyarns(yF, yT):
      x = set(yF) & set(yT)
      return (x, x)

    return doyarns

  def equalR(fTp, tTp):
    return lambda n: (n, )

  # UNEQUAL

  def unequalR(fTp, tTp):
    return lambda n, m: n != m

  # CANONICAL BEFORE

  def canonicalBeforeR(fTp, tTp):
    isSlotF = isSlotType(fTp)
    isSlotT = isSlotType(tTp)
    if isSlotF and isSlotT:
      return lambda n, m: n < m

    return lambda n, m: Crank[n - 1] < Crank[m - 1]

  # CANONICAL AFTER

  def canonicalAfterR(fTp, tTp):
    isSlotF = isSlotType(fTp)
    isSlotT = isSlotType(tTp)
    if isSlotF and isSlotT:
      return lambda n, m: n > m

    return lambda n, m: Crank[n - 1] > Crank[m - 1]

  # SAME SLOTS

  def spinSameSlots(fTp, tTp):
    isSlotF = isSlotType(fTp)
    isSlotT = isSlotType(tTp)
    if isSlotF and isSlotT:

      def doyarns(yF, yT):
        x = set(yF) & set(yT)
        return (x, x)

      return doyarns

    elif isSlotF or isSlotT:

      def doyarns(yS, y2):
        sindex = {}
        for m in y2:
          ss = Eoslots[m - maxSlotP] if m > maxSlot else (m, )
          if len(ss) == 1:
            sindex.setdefault(ss[0], set()).add(m)
        nyS = yS & set(sindex.keys())
        ny2 = set(chain.from_iterable(sindex[s] for s in nyS))
        return (nyS, ny2)

      if isSlotF:
        return doyarns

      else:

        def xx(yF, yT):
          (nyT, nyF) = doyarns(yT, yF)
          return (nyF, nyT)

        return xx

    else:

      def doyarns(yF, yT):
        sindexF = {}
        for n in yF:
          s = frozenset(Eoslots[n - maxSlotP] if n > maxSlot else (n, ))
          sindexF.setdefault(s, set()).add(n)
        sindexT = {}
        for m in yT:
          s = frozenset(Eoslots[m - maxSlotP] if m > maxSlot else (m, ))
          sindexT.setdefault(s, set()).add(m)
        nyS = set(sindexF.keys()) & set(sindexT.keys())
        nyF = set(chain.from_iterable(sindexF[s] for s in nyS))
        nyT = set(chain.from_iterable(sindexT[s] for s in nyS))
        return (nyF, nyT)

      return doyarns

  def sameSlotsR(fTp, tTp):
    isSlotF = isSlotType(fTp)
    isSlotT = isSlotType(tTp)
    if isSlotF and isSlotT:
      return lambda n: (n, )
    else:
      def xx(n):
        nmin = n - 1
        if n < maxSlotP:
          nA = array('I', (n,))
          yield n
          for m in ClevUp[nmin]:
            if Eoslots[m - maxSlotP] == nA:
              yield m
          return
        nSlots = Eoslots[n - maxSlotP]
        if len(nSlots) == 1:
          slot1 = nSlots[0]
          nA = array('I', (slot1,))
          yield n
          yield slot1
          for m in ClevUp[nmin]:
            if Eoslots[m - maxSlotP] == nA:
              yield m
          return
        yield n
        for m in ClevUp[nmin]:
          if n in ClevUp[m - 1]:
            yield m
      return xx

  # OVERLAP

  def spinOverlap(fTp, tTp):
    isSlotF = isSlotType(fTp)
    isSlotT = isSlotType(tTp)

    if isSlotF and isSlotT:

      def doyarns(yF, yT):
        x = set(yF) & set(yT)
        return (x, x)

      return doyarns

    elif isSlotF or isSlotT:

      def doyarns(yS, y2):
        sindex = {}
        for m in y2:
          for s in Eoslots[m - maxSlotP] if m > maxSlot else (m, ):
            sindex.setdefault(s, set()).add(m)
        nyS = yS & set(sindex.keys())
        ny2 = set(chain.from_iterable(sindex[s] for s in nyS))
        return (nyS, ny2)

      if isSlotF:
        return doyarns

      else:

        def xx(yF, yT):
          (nyT, nyF) = doyarns(yT, yF)
          return (nyF, nyT)

        return xx
    else:

      def doyarns(yF, yT):
        REDUCE_FACTOR = 0.4
        SIZE_LIMIT = 10000
        sindexF = {}
        for n in yF:
          for s in Eoslots[n - maxSlotP] if n > maxSlot else (n, ):
            sindexF.setdefault(s, set()).add(n)
        sindexT = {}
        for m in yT:
          for s in Eoslots[m - maxSlotP] if m > maxSlot else (m, ):
            sindexT.setdefault(s, set()).add(m)
        nyS = set(sindexF.keys()) & set(sindexT.keys())

        lsF = len(sindexF)
        lsT = len(sindexT)
        lsI = len(nyS)
        if lsF == lsT:  # spinning is completely useless
          return (yF, yT)
        if lsI > REDUCE_FACTOR * lsT and lsT > SIZE_LIMIT:
          # spinning is not worth it
          return (yF, yT)

        nyF = set(chain.from_iterable(sindexF[s] for s in nyS))
        nyT = set(chain.from_iterable(sindexT[s] for s in nyS))
        return (nyF, nyT)

      return doyarns

  def overlapR(fTp, tTp):
    isSlotF = isSlotType(fTp)
    isSlotT = isSlotType(tTp)
    if isSlotF and isSlotT:
      return lambda n: (n, )
    elif isSlotT:
      return lambda n: (Eoslots[n - maxSlotP] if n > maxSlot else (n, ))
    elif isSlotF:
      return lambda n: chain(ClevUp[n - 1], (n, ))
    else:
      def xx(n):
        nSlots = Eoslots[n - maxSlotP] if n > maxSlot else (n,)
        return chain(nSlots, set(chain.from_iterable(
            ClevUp[s - 1] for s in nSlots
        )))
      return xx

  # DIFFERENT SLOTS

  def diffSlotsR(fTp, tTp):
    isSlotF = isSlotType(fTp)
    isSlotT = isSlotType(tTp)
    if isSlotF and isSlotT:
      return lambda n, m: m != n
    elif isSlotT:
      return lambda n, m: ((Eoslots[m - maxSlotP] if m > maxSlot else (m, )) != (n, ))
    elif isSlotF:
      return lambda n, m: ((Eoslots[n - maxSlotP] if n > maxSlot else (n, )) != (m, ))
    else:
      return (
          lambda n, m: (
              frozenset(Eoslots[n - maxSlotP] if n > maxSlot else (n, )) !=
              frozenset(Eoslots[m - maxSlotP] if m > maxSlot else (m, ))
          )
      )

  # DISJOINT SLOTS

  def disjointSlotsR(fTp, tTp):
    isSlotF = isSlotType(fTp)
    isSlotT = isSlotType(tTp)
    if isSlotF and isSlotT:
      return lambda n, m: m != n
    elif isSlotT:
      return lambda n, m: m not in frozenset(Eoslots[n - maxSlotP] if n > maxSlot else (n, ))
    elif isSlotF:
      return lambda n, m: n not in frozenset(Eoslots[m - maxSlotP] if m > maxSlot else (m, ))
    else:
      return (
          lambda n, m: (
              len(
                  frozenset(Eoslots[n - maxSlotP] if n > maxSlot else (n, ))
                  & frozenset(Eoslots[m - maxSlotP] if m > maxSlot else (m, ))
              ) == 0
          )
      )

  # EMBEDDED IN

  def inR(fTp, tTp):
    isSlotF = isSlotType(fTp)
    isSlotT = isSlotType(tTp)
    if isSlotF and isSlotT:
      return lambda n: ()
    elif isSlotT:
      return lambda n: ()
    elif isSlotF:
      return lambda n: ClevUp[n - 1]
    else:
      return lambda n: ClevUp[n - 1]

  # EMBEDS

  def hasR(fTp, tTp):
    isSlotF = isSlotType(fTp)
    isSlotT = isSlotType(tTp)
    if isSlotF and isSlotT:
      return lambda n: ()
    elif isSlotF:
      return lambda n: ()
    elif isSlotT:
      return lambda n: Eoslots[n - maxSlotP] if n > maxSlot else ()
    else:
      if isSlotT is None:
        return lambda n: (
            chain(ClevDown[n - maxSlotP], Eoslots[n - maxSlotP])
            if n > maxSlot else
            ()
        )
      else:
        return lambda n: (ClevDown[n - maxSlotP] if n > maxSlot else ())

  # BEFORE WRT SLOTS

  def slotBeforeR(fTp, tTp):
    isSlotF = isSlotType(fTp)
    isSlotT = isSlotType(tTp)
    if isSlotF and isSlotT:
      return lambda n, m: n < m
    elif isSlotF:
      return lambda n, m: n < (Eoslots[m - maxSlotP][0] if m > maxSlot else m)
    elif isSlotT:
      return lambda n, m: (Eoslots[n - maxSlotP][-1] if n > maxSlot else n) < m
    else:
      return lambda n, m: ((Eoslots[n - maxSlotP][-1] if n > maxSlot else n) <
                           (Eoslots[m - maxSlotP][0] if m > maxSlot else m))

  # AFTER WRT SLOTS

  def slotAfterR(fTp, tTp):
    isSlotF = isSlotType(fTp)
    isSlotT = isSlotType(tTp)
    if isSlotF and isSlotT:
      return lambda n, m: n > m
    elif isSlotF:
      return lambda n, m: n > (Eoslots[m - maxSlotP][-1] if m > maxSlot else m)
    elif isSlotT:
      return lambda n, m: (Eoslots[n - maxSlotP][0] if n > maxSlot else n) > m
    else:
      return lambda n, m: ((Eoslots[n - maxSlotP][0] if n > maxSlot else n) >
                           (Eoslots[m - maxSlotP][-1] if m > maxSlot else m))

  # START AT SAME SLOT

  def sameFirstSlotR(fTp, tTp):
    isSlotF = isSlotType(fTp)
    isSlotT = isSlotType(tTp)
    if isSlotF and isSlotT:
      return lambda n: (n, )
    elif isSlotF:
      if isSlotT is None:
        return lambda n: chain(CfirstSlots[n - 1], (n, ))
      else:
        return lambda n: CfirstSlots[n - 1]
    elif isSlotT:
      return lambda n: ((Eoslots[n - maxSlotP][0] if n > maxSlot else n), )
    else:

      def xx(n):
        fn = Eoslots[n - maxSlotP][0] if n > maxSlot else n
        fnmin = fn - 1
        if isSlotT is None:
          return chain(CfirstSlots[fnmin], (fn, ))
        else:
          return CfirstSlots[fnmin]

      return xx

  # ENDS AT SAME SLOT

  def sameLastSlotR(fTp, tTp):
    isSlotF = isSlotType(fTp)
    isSlotT = isSlotType(tTp)
    if isSlotF and isSlotT:
      return lambda n: (n, )
    elif isSlotF:
      if isSlotT is None:
        return lambda n: chain(ClastSlots[n - 1], (n, ))
      else:
        return lambda n: ClastSlots[n - 1]
    elif isSlotT:
      return lambda n: ((Eoslots[n - maxSlotP][-1] if n > maxSlot else n), )
    else:

      def xx(n):
        ln = Eoslots[n - maxSlotP][-1] if n > maxSlot else n
        lnmin = ln - 1
        if isSlotT is None:
          return chain(ClastSlots[lnmin], (ln, ))
        else:
          return ClastSlots[lnmin]

      return xx

  # START AND END AT SAME SLOT

  def sameBoundaryR(fTp, tTp):
    isSlotF = isSlotType(fTp)
    isSlotT = isSlotType(tTp)
    if isSlotF and isSlotT:
      return lambda n: (n, )
    elif isSlotF:
      if isSlotT is None:

        def xx(n):
          nmin = n - 1
          fok = set(chain(CfirstSlots[nmin], (n, )))
          lok = set(chain(ClastSlots[nmin], (n, )))
          return fok & lok

      else:

        def xx(n):
          nmin = n - 1
          fok = set(CfirstSlots[nmin])
          lok = set(ClastSlots[nmin])
          return fok & lok

      return xx

    elif isSlotT:

      def xx(n):
        slots = Eoslots[n - maxSlotP] if n > maxSlot else (n, )
        fs = slots[0]
        ls = slots[-1]
        return (fs, ) if fs == ls else ()

      return xx

    else:
      if isSlotT is None:

        def xx(n):
          fn = Eoslots[n - maxSlotP][0] if n > maxSlot else n
          ln = Eoslots[n - maxSlotP][-1] if n > maxSlot else n
          fnmin = fn - 1
          lnmin = ln - 1
          fok = set(chain(CfirstSlots[fnmin], (fn, )))
          lok = set(chain(ClastSlots[lnmin], (ln, )))
          return fok & lok

      else:

        def xx(n):
          fn = Eoslots[n - maxSlotP][0] if n > maxSlot else n
          ln = Eoslots[n - maxSlotP][-1] if n > maxSlot else n
          fnmin = fn - 1
          lnmin = ln - 1
          fok = set(CfirstSlots[fnmin])
          lok = set(ClastSlots[lnmin])
          return fok & lok

      return xx

  # FIRST SLOTS ARE k-CLOSE

  def nearFirstSlotR(k):

    def zz(fTp, tTp):
      isSlotF = isSlotType(fTp)
      isSlotT = isSlotType(tTp)
      if isSlotF and isSlotT:
        return lambda n: range(max((1, n - k)), min((maxSlot, n + k)) + 1)
      elif isSlotF:
        if isSlotT is None:

          def xx(n):
            near = range(max((1, n - k)), min((maxSlot, n + k)) + 1)
            return chain(near, chain.from_iterable(CfirstSlots[l - 1] for l in near))
        else:

          def xx(n):
            near = range(max((1, n - k)), min((maxSlot, n + k)) + 1)
            return chain.from_iterable(CfirstSlots[l - 1] for l in near)

        return xx
      elif isSlotT:

        def xx(n):
          fn = Eoslots[n - maxSlotP][0] if n > maxSlot else n
          return range(max((1, fn - k)), min((maxSlot, fn + k)) + 1)

        return xx

      else:
        if isSlotT is None:

          def xx(n):
            fn = Eoslots[n - maxSlotP][0] if n > maxSlot else n
            near = range(max((1, fn - k)), min((maxSlot, fn + k)) + 1)
            return chain(near, chain.from_iterable(CfirstSlots[l - 1] for l in near))

        else:

          def xx(n):
            fn = Eoslots[n - maxSlotP][0] if n > maxSlot else n
            near = range(max((1, fn - k)), min((maxSlot, fn + k)) + 1)
            return chain.from_iterable(CfirstSlots[l - 1] for l in near)

        return xx

    return zz

  # LAST SLOTS ARE k-CLOSE

  def nearLastSlotR(k):

    def zz(fTp, tTp):
      isSlotF = isSlotType(fTp)
      isSlotT = isSlotType(tTp)
      if isSlotF and isSlotT:
        return lambda n: range(max((1, n - k)), min((maxSlot, n + k)) + 1)
      elif isSlotF:
        if isSlotT is None:

          def xx(n):
            near = range(max((1, n - k)), min((maxSlot, n + k)) + 1)
            return chain(near, chain.from_iterable(ClastSlots[l - 1] for l in near))

        else:

          def xx(n):
            near = range(max((1, n - k)), min((maxSlot, n + k)) + 1)
            return chain.from_iterable(ClastSlots[l - 1] for l in near)

        return xx
      elif isSlotT:

        def xx(n):
          ln = Eoslots[n - maxSlotP][-1] if n > maxSlot else n
          return range(max((1, ln - k)), min((maxSlot, ln + k)) + 1)

        return xx
      else:
        if isSlotT is None:

          def xx(n):
            ln = Eoslots[n - maxSlotP][-1] if n > maxSlot else n
            near = range(max((1, ln - k)), min((maxSlot, ln + k)) + 1)
            return chain(near, chain.from_iterable(ClastSlots[l - 1] for l in near))

        else:

          def xx(n):
            ln = Eoslots[n - maxSlotP][-1] if n > maxSlot else n
            near = range(max((1, ln - k)), min((maxSlot, ln + k)) + 1)
            return chain.from_iterable(ClastSlots[l - 1] for l in near)

        return xx

    return zz

  # FIRST SLOTS ARE k-CLOSE and LAST SLOTS ARE k-CLOSE

  def nearBoundaryR(k):

    def zz(fTp, tTp):
      isSlotF = isSlotType(fTp)
      isSlotT = isSlotType(tTp)
      if isSlotF and isSlotT:
        return lambda n: range(max((1, n - k)), min((maxSlot, n + k)) + 1)
      elif isSlotF:
        if isSlotT is None:

          def xx(n):
            near = set(range(max((1, n - k)), min((maxSlot, n + k)) + 1))
            fok = set(chain.from_iterable(CfirstSlots[l - 1] for l in near))
            lok = set(chain.from_iterable(ClastSlots[l - 1] for l in near))
            return near | (fok & lok)

        else:

          def xx(n):
            near = range(max((1, n - k)), min((maxSlot, n + k)) + 1)
            fok = set(chain.from_iterable(CfirstSlots[l - 1] for l in near))
            lok = set(chain.from_iterable(ClastSlots[l - 1] for l in near))
            return fok & lok

        return xx
      elif isSlotT:

        def xx(n):
          slots = Eoslots[n - maxSlotP] if n > maxSlot else (n, )
          fs = slots[0]
          ls = slots[-1]
          fok = set(range(max((1, fs - k)), min((maxSlot, fs + k)) + 1))
          lok = set(range(max((1, ls - k)), min((maxSlot, ls + k)) + 1))
          return fok & lok

        return xx
      else:
        if isSlotT is None:

          def xx(n):
            fn = Eoslots[n - maxSlotP][0] if n > maxSlot else n
            ln = Eoslots[n - maxSlotP][-1] if n > maxSlot else n
            nearf = range(max((1, fn - k)), min((maxSlot, fn + k)) + 1)
            nearl = range(max((1, ln - k)), min((maxSlot, ln + k)) + 1)
            fok = set(chain(nearf, chain.from_iterable(CfirstSlots[l - 1] for l in nearf)))
            lok = set(chain(nearl, chain.from_iterable(ClastSlots[l - 1] for l in nearl)))
            return fok & lok

        else:

          def xx(n):
            fn = Eoslots[n - maxSlotP][0] if n > maxSlot else n
            ln = Eoslots[n - maxSlotP][-1] if n > maxSlot else n
            nearf = range(max((1, fn - k)), min((maxSlot, fn + k)) + 1)
            nearl = range(max((1, ln - k)), min((maxSlot, ln + k)) + 1)
            fok = set(chain.from_iterable(CfirstSlots[l - 1] for l in nearf))
            lok = set(chain.from_iterable(ClastSlots[l - 1] for l in nearl))
            return fok & lok

        return xx

    return zz

  # FIRST ENDS WHERE SECOND STARTS

  def adjBeforeR(fTp, tTp):
    isSlotF = isSlotType(fTp)
    isSlotT = isSlotType(tTp)
    if isSlotF and isSlotT:
      return lambda n: (n + 1, ) if n < maxSlot else ()
    else:
      if isSlotT:

        def xx(n):
          if n == maxSlot:
            return ()
          myNext = n + 1 if n < maxSlot else Eoslots[n - maxSlotP][-1] + 1
          if myNext > maxSlot:
            return ()
          return (myNext, )

      elif isSlotT is None:

        def xx(n):
          if n == maxSlot:
            return ()
          myNext = n + 1 if n < maxSlot else Eoslots[n - maxSlotP][-1] + 1
          if myNext > maxSlot:
            return ()
          return chain(CfirstSlots[myNext - 1], (myNext, ))

      else:

        def xx(n):
          if n == maxSlot:
            return ()
          myNext = n + 1 if n < maxSlot else Eoslots[n - maxSlotP][-1] + 1
          if myNext > maxSlot:
            return ()
          return CfirstSlots[myNext - 1]

      return xx

  # FIRST STARTS WHERE SECOND ENDS

  def adjAfterR(fTp, tTp):
    isSlotF = isSlotType(fTp)
    isSlotT = isSlotType(tTp)
    if isSlotF and isSlotT:
      return lambda n: (n - 1, ) if n > 1 else ()
    else:

      if isSlotT:

        def xx(n):
          if n <= 1:
            return ()
          myPrev = n - 1 if n < maxSlot else Eoslots[n - maxSlotP][0] - 1
          if myPrev <= 1:
            return ()
          return (myPrev, )

      elif isSlotT is None:

        def xx(n):
          if n <= 1:
            return ()
          myPrev = n - 1 if n < maxSlot else Eoslots[n - maxSlotP][0] - 1
          if myPrev <= 1:
            return ()
          return chain((myPrev, ), ClastSlots[myPrev - 1])

      else:

        def xx(n):
          if n <= 1:
            return ()
          myPrev = n - 1 if n < maxSlot else Eoslots[n - maxSlotP][0] - 1
          if myPrev <= 1:
            return ()
          return ClastSlots[myPrev - 1]

      return xx

  # FIRST ENDS WHERE SECOND STARTS WITHIN k-SLOTS

  def nearBeforeR(k):

    def zz(fTp, tTp):
      isSlotF = isSlotType(fTp)
      isSlotT = isSlotType(tTp)
      if isSlotF and isSlotT:
        return lambda n: range(max((1, n + 1 - k)), min((maxSlot, n + 1 + k)) + 1)
      else:
        if isSlotT:

          def xx(n):
            myNext = n + 1 if n < maxSlot else Eoslots[n - maxSlotP][-1] + 1
            return range(max((1, myNext - k)), min((maxSlot, myNext + k)) + 1)

        elif isSlotT is None:

          def xx(n):
            myNext = n + 1 if n < maxSlot else Eoslots[n - maxSlotP][-1] + 1
            near = range(max((1, myNext - k)), min((maxSlot, myNext + k)) + 1)
            return chain(near, chain.from_iterable(CfirstSlots[ls - 1] for ls in near))

        else:

          def xx(n):
            myNext = n + 1 if n < maxSlot else Eoslots[n - maxSlotP][-1] + 1
            near = range(max((1, myNext - k)), min((maxSlot, myNext + k)) + 1)
            return chain.from_iterable(CfirstSlots[ls - 1] for ls in near)

        return xx

    return zz

  # FIRST STARTS WHERE SECOND ENDS WITHIN k-SLOTS

  def nearAfterR(k):

    def zz(fTp, tTp):
      isSlotF = isSlotType(fTp)
      isSlotT = isSlotType(tTp)
      if isSlotF and isSlotT:
        return lambda n: range(max((1, n - 1 - k)), min((maxSlot, n - 1 + k)) + 1)
      else:
        if isSlotT:

          def xx(n):
            myPrev = n - 1 if n < maxSlot else Eoslots[n - maxSlotP][0] - 1
            return tuple(range(max((1, myPrev - k)), min((maxSlot, myPrev + k)) + 1))

        elif isSlotT is None:

          def xx(n):
            myPrev = n - 1 if n < maxSlot else Eoslots[n - maxSlotP][0] - 1
            near = range(max((1, myPrev - k)), min((maxSlot, myPrev + k)) + 1)
            return chain(near, chain.from_iterable(ClastSlots[l - 1] for l in near))

        else:

          def xx(n):
            myPrev = n - 1 if n < maxSlot else Eoslots[n - maxSlotP][0] - 1
            near = range(max((1, myPrev - k)), min((maxSlot, myPrev + k)) + 1)
            return chain.from_iterable(ClastSlots[l - 1] for l in near)

        return xx

    return zz

  # SAME FEATURE VALUES

  def spinLeftFisRightG(f, g):

    def zz(fTp, tTp):
      print('ZZZ', 'spinning')
      if f not in Sindex:
        Sindex[f] = makeIndex(Fs(f).data)
      if f != g:
        if g not in Sindex:
          Sindex[g] = makeIndex(Fs(g).data)
      indF = Sindex[f]
      indG = Sindex[g]
      commonValues = set(indF) if f == g else set(indF) & set(indG)

      def doyarns(yF, yT):
        fNodes = {n for n in chain.from_iterable(indF[v] for v in commonValues) if n in yF}
        gNodes = {n for n in chain.from_iterable(indG[v] for v in commonValues) if n in yT}
        return (fNodes, gNodes)

      return doyarns

    return zz

  def spinLeftGisRightF(f, g):
    return spinLeftFisRightG(g, f)

  def leftFisRightGR_ORIG(f, g):

    def zz(fTp, tTp):
      fData = Fs(f).v
      gData = Fs(g).v

      def uu(n, m):
        nVal = fData(n)
        return False if nVal is None else nVal == gData(m)
      return uu

    return zz

  def leftFisRightGR_TRY(f, g):
    # very slow, nearly an order slower than the function below

    def zz(fTp, tTp):
      fData = Fs(f).v if f == OTYPE else lambda n: Fs(f).data.get(n, None)
      gData = Fs(g).v if g == OTYPE else lambda n: Fs(g).data.get(n, None)

      def uu(n, m):
        nVal = fData(n)
        return False if nVal is None else nVal == gData(m)
      return uu

    return zz

  def leftFisRightGR(f, g):

    def zz(fTp, tTp):
      fData = Fs(f).v if f == OTYPE else Fs(f).data
      gData = Fs(g).v if g == OTYPE else Fs(g).data

      if f == OTYPE and g == OTYPE:
        def uu(n, m):
          nVal = fData(n)
          return False if nVal is None else nVal == gData(m)
        return uu

      if f == OTYPE:
        def uu(n, m):
          nVal = fData(n)
          return False if nVal is None else nVal == gData.get(m, None)
        return uu

      if g == OTYPE:
        def uu(n, m):
          nVal = fData.get(n, None)
          return False if nVal is None else nVal == gData(m)
        return uu

      def uu(n, m):
        nVal = fData.get(n, None)
        return False if nVal is None else nVal == gData.get(m, None)
      return uu

    return zz

  def leftGisRightFR(g, f):
    return leftFisRightGR(f, g)

  # MATCH FEATURE VALUES

  def spinLeftFmatchRightG(f, rPat, rRe, g):

    def zz(fTp, tTp):
      fR = f'{f}~{rPat}'
      gR = f'{g}~{rPat}'

      if fR not in Sindex:
        if f not in Sindex:
          Sindex[f] = makeIndex(Fs(f).data)
        indFR = {}
        for (v, ns) in Sindex[f].items():
          vR = rRe.sub('', v)
          for n in ns:
            indFR.setdefault(vR, set()).add(n)
        Sindex[fR] = indFR
      if gR not in Sindex:
        if g not in Sindex:
          Sindex[g] = makeIndex(Fs(g).data)
        indGR = {}
        for (v, ns) in Sindex[g].items():
          vR = rRe.sub('', v)
          for n in ns:
            indGR.setdefault(vR, set()).add(n)
        Sindex[gR] = indGR

      indFR = Sindex[fR]
      indGR = Sindex[gR]

      commonValues = set(indFR) & set(indGR)

      def doyarns(yF, yT):
        fNodes = {n for n in chain.from_iterable(indFR[v] for v in commonValues) if n in yF}
        gNodes = {n for n in chain.from_iterable(indGR[v] for v in commonValues) if n in yT}
        return (fNodes, gNodes)

      return doyarns

    return zz

  def spinLeftGmatchRightF(f, rPat, rRe, g):
    return spinLeftFmatchRightG(g, rPat, rRe, f)

  def leftFmatchRightGR(f, rPat, rRe, g):

    def zz(fTp, tTp):
      fData = Fs(f).v if f == OTYPE else Fs(f).data
      gData = Fs(g).v if g == OTYPE else Fs(g).data

      if f == OTYPE and g == OTYPE:
        def uu(n, m):
          nVal = fData(n)
          if nVal is None:
            return False
          nVal = rRe.sub('', nVal)
          mVal = gData(m)
          if mVal is None:
            return False
          mVal = rRe.sub('', mVal)
          return nVal == mVal
        return uu

      if f == OTYPE:
        def uu(n, m):
          nVal = fData(n)
          if nVal is None:
            return False
          nVal = rRe.sub('', nVal)
          mVal = gData.get(m, None)
          if mVal is None:
            return False
          mVal = rRe.sub('', mVal)
          return nVal == mVal
        return uu

      if g == OTYPE:
        def uu(n, m):
          nVal = fData.get(n, None)
          if nVal is None:
            return False
          nVal = rRe.sub('', nVal)
          mVal = gData(m)
          if mVal is None:
            return False
          mVal = rRe.sub('', mVal)
          return nVal == mVal
        return uu

      def uu(n, m):
        nVal = fData.get(n, None)
        if nVal is None:
          return False
        nVal = rRe.sub('', nVal)
        mVal = gData.get(m, None)
        if mVal is None:
          return False
        mVal = rRe.sub('', mVal)
        return nVal == mVal
      return uu

    return zz

  def leftGmatchRightFR(g, rPat, rRe, f):
    return leftFmatchRightGR(f, rPat, rRe, g)

  # UNEQUAL FEATURE VALUES

  def leftFunequalRightGR(f, g):

    def zz(fTp, tTp):
      fData = Fs(f).v if f == OTYPE else Fs(f).data
      gData = Fs(g).v if g == OTYPE else Fs(g).data

      if f == OTYPE and g == OTYPE:
        def uu(n, m):
          nVal = fData(n)
          mVal = gData(m)
          return nVal is None and mVal is None or nVal != mVal
        return uu

      if f == OTYPE:
        def uu(n, m):
          nVal = fData(n)
          mVal = gData.get(m, None)
          return nVal is None and mVal is None or nVal != mVal
        return uu

      if g == OTYPE:
        def uu(n, m):
          nVal = fData.get(n, None)
          mVal = gData(m)
          return nVal is None and mVal is None or nVal != mVal
        return uu

      def uu(n, m):
        nVal = fData.get(n, None)
        mVal = gData.get(m, None)
        return nVal is None and mVal is None or nVal != mVal
      return uu

    return zz

  def leftGunequalRightFR(g, f):
    return leftFunequalRightGR(f, g)

  # GREATER FEATURE VALUES

  def leftFgreaterRightGR(f, g):

    def zz(fTp, tTp):
      fData = Fs(f).v if f == OTYPE else Fs(f).data
      gData = Fs(g).v if g == OTYPE else Fs(g).data

      if f == OTYPE and g == OTYPE:
        def uu(n, m):
          nVal = fData(n)
          mVal = gData(m)
          return nVal is not None and mVal is not None and nVal > mVal
        return uu

      if f == OTYPE:
        def uu(n, m):
          nVal = fData(n)
          mVal = gData.get(m, None)
          return nVal is not None and mVal is not None and nVal > mVal
        return uu

      if g == OTYPE:
        def uu(n, m):
          nVal = fData.get(n, None)
          mVal = gData(m)
          return nVal is not None and mVal is not None and nVal > mVal
        return uu

      def uu(n, m):
        nVal = fData.get(n, None)
        mVal = gData.get(m, None)
        return nVal is not None and mVal is not None and nVal > mVal
      return uu

    return zz

  def leftGlesserRightFR(g, f):
    return leftFgreaterRightGR(f, g)

  # LESSER FEATURE VALUES

  def leftFlesserRightGR(f, g):

    def zz(fTp, tTp):
      fData = Fs(f).v if f == OTYPE else Fs(f).data
      gData = Fs(g).v if g == OTYPE else Fs(g).data

      if f == OTYPE and g == OTYPE:
        def uu(n, m):
          nVal = fData(n)
          mVal = gData(m)
          return nVal is not None and mVal is not None and nVal < mVal
        return uu

      if f == OTYPE:
        def uu(n, m):
          nVal = fData(n)
          mVal = gData.get(m, None)
          return nVal is not None and mVal is not None and nVal < mVal
        return uu

      if g == OTYPE:
        def uu(n, m):
          nVal = fData.get(n, None)
          mVal = gData(m)
          return nVal is not None and mVal is not None and nVal < mVal
        return uu

      def uu(n, m):
        nVal = fData.get(n, None)
        mVal = gData.get(m, None)
        return nVal is not None and mVal is not None and nVal < mVal
      return uu

    return zz

  def leftGgreaterRightFR(g, f):
    return leftFlesserRightGR(f, g)

  # EDGES

  def makeEdgeMaps(efName):

    def edgeAccess(eFunc, doValues, value):
      if doValues:
        if value is None:
          return lambda n: (m[0] for m in eFunc(n) if m[1] is None)
        elif value is True:
          return lambda n: (m[0] for m in eFunc(n))
        elif isinstance(value, types.FunctionType):
          return lambda n: (m[0] for m in eFunc(n) if value(m[1]))
        elif isinstance(value, reTp):
          return lambda n: (m[0] for m in eFunc(n) if value is not None and value.search(m[1]))
        else:
          (ident, value) = value
          if (ident is None and value is True):
            return lambda n: (m[0] for m in eFunc(n))
          elif ident:
            return lambda n: (m[0] for m in eFunc(n) if m[1] in value)
          else:
            return lambda n: (m[0] for m in eFunc(n) if m[1] not in value)
      else:
        return lambda n: eFunc(n)

    def edgeRV(value):

      def edgeR(fTp, tTp):
        Es = api.Es
        Edata = Es(efName)
        doValues = Edata.doValues
        return edgeAccess(Edata.f, doValues, value)

      return edgeR

    def edgeIRV(value):

      def edgeIR(fTp, tTp):
        Es = api.Es
        Edata = Es(efName)
        doValues = Edata.doValues
        return edgeAccess(Edata.t, doValues, value)

      return edgeIR

    def edgeSRV(value):

      def edgeSR(fTp, tTp):
        Es = api.Es
        Edata = Es(efName)
        doValues = Edata.doValues
        return edgeAccess(Edata.b, doValues, value)

      return edgeSR

    return (edgeRV, edgeIRV, edgeSRV)

  # COLLECT ALL RELATIONS IN A TUPLE

  relations = [
      (
          ('=', spinEqual, equalR, 'left equal to right (as node)'),
          ('=', spinEqual, equalR, None),
      ),
      (
          ('#', 0.999, unequalR, 'left unequal to right (as node)'),
          ('#', 0.999, unequalR, None),
      ),
      (
          ('<', 0.500, canonicalBeforeR, 'left before right (in canonical node ordering)'),
          ('>', 0.500, canonicalAfterR, 'left after right (in canonical node ordering)'),
      ),
      (
          ('==', spinSameSlots, sameSlotsR, 'left occupies same slots as right'),
          ('==', spinSameSlots, sameSlotsR, None),
      ),
      (
          ('&&', spinOverlap, overlapR, 'left has overlapping slots with right'),
          ('&&', spinOverlap, overlapR, None),
      ),
      (
          ('##', 0.990, diffSlotsR, 'left and right do not have the same slot set'),
          ('##', 0.990, diffSlotsR, None),
      ),
      (
          ('||', 0.900, disjointSlotsR, 'left and right do not have common slots'),
          ('||', 0.900, disjointSlotsR, None),
      ),
      (
          ('[[', True, hasR, 'left embeds right'),
          (']]', True, inR, 'left embedded in right'),
      ),
      (
          ('<<', 0.490, slotBeforeR, 'left completely before right'),
          ('>>', 0.490, slotAfterR, 'left completely after right'),
      ),
      (
          ('=:', True, sameFirstSlotR, 'left and right start at the same slot'),
          ('=:', True, sameFirstSlotR, None),
      ),
      (
          (':=', True, sameLastSlotR, 'left and right end at the same slot'),
          (':=', True, sameLastSlotR, None),
      ),
      (
          ('::', True, sameBoundaryR, 'left and right start and end at the same slot'),
          ('::', True, sameBoundaryR, None),
      ),
      (
          ('<:', True, adjBeforeR, 'left immediately before right'),
          (':>', True, adjAfterR, 'left immediately after right'),
      ),
      (
          ('=k:', True, nearFirstSlotR, 'left and right start at k-nearly the same slot'),
          ('=k:', True, nearFirstSlotR, None),
      ),
      (
          (':k=', True, nearLastSlotR, 'left and right end at k-nearly the same slot'),
          (':k=', True, nearLastSlotR, None),
      ),
      (
          (':k:', True, nearBoundaryR, 'left and right start and end at k-near slots'),
          (':k:', True, nearBoundaryR, None),
      ),
      (
          ('<k:', True, nearBeforeR, 'left k-nearly before right'),
          (':k>', True, nearAfterR, 'left k-nearly after right'),
      ),
      (
          ('.f.', spinLeftFisRightG, leftFisRightGR, 'left.f = right.f'),
          ('.f.', spinLeftGisRightF, leftGisRightFR, None),
      ),
      (
          ('.f=g.', spinLeftFisRightG, leftFisRightGR, 'left.f = right.g'),
          ('.g=f.', spinLeftGisRightF, leftGisRightFR, None),
      ),
      (
          ('.f~r~g.', spinLeftFmatchRightG, leftFmatchRightGR, 'left.f matches right.g'),
          ('.g~r~f.', spinLeftGmatchRightF, leftGmatchRightFR, None),
      ),
      (
          ('.f#g.', 0.8, leftFunequalRightGR, 'left.f # right.g'),
          ('.g#f.', 0.8, leftGunequalRightFR, None),
      ),
      (
          ('.f>g.', 0.4, leftFgreaterRightGR, 'left.f > right.g'),
          ('.g<f.', 0.4, leftGlesserRightFR, None),
      ),
      (
          ('.f<g.', 0.4, leftFlesserRightGR, 'left.f > right.g'),
          ('.g>f.', 0.4, leftGgreaterRightFR, None),
      ),
  ]

  # BUILD AND INITIALIZE ALL RELATIONAL FUNCTIONS

  api.TF.explore(silent='deep')
  edgeMap = {}
  nodeMap = {}

  for efName in sorted(api.TF.featureSets['edges']):
    if efName == OSLOTS:
      continue
    r = len(relations)

    (edgeRV, edgeIRV, edgeSRV) = makeEdgeMaps(efName)
    doValues = api.TF.features[efName].edgeValues
    extra = ' with value specification allowed' if doValues else ''
    relations.append((
        (f'-{efName}>', True, edgeRV, f'edge feature "{efName}"{extra}'),
        (f'<{efName}-', True, edgeIRV, f'edge feature "{efName}"{extra} (opposite direction)'),
    ))
    edgeMap[2 * r] = (efName, 1)
    edgeMap[2 * r + 1] = (efName, -1)

    r = len(relations)
    relations.append((
        (f'<{efName}>', True, edgeSRV, f'edge feature "{efName}"{extra} (either direction)'),
        (f'<{efName}>', True, edgeSRV, None),
    ))
    edgeMap[2 * r] = (efName, 0)
    edgeMap[2 * r + 1] = (efName, 0)
  lr = len(relations)

  relationsAll = []
  for (r, rc) in relations:
    relationsAll.extend([r, rc])

  searchExe.relations = [dict(
      acro=r[0],
      spin=r[1],
      func=r[2],
      desc=r[3],
  ) for r in relationsAll]
  searchExe.relationFromName = dict(((r['acro'], i) for (i, r) in enumerate(searchExe.relations)))
  searchExe.relationLegend = '\n'.join(
      f'{r["acro"]:>23} {r["desc"]}' for r in searchExe.relations if r['desc'] is not None
  )
  searchExe.relationLegend += f'''
The warp feature "{OSLOTS}" cannot be used in searches.
One of the above relations on nodes and/or slots will suit you better.
'''
  searchExe.converse = dict(
      tuple((2 * i, 2 * i + 1) for i in range(lr)) + tuple((2 * i + 1, 2 * i) for i in range(lr))
  )
  searchExe.edgeMap = edgeMap
  searchExe.nodeMap = nodeMap


def add_K_Relations(searchExe, varRels):
  relations = searchExe.relations
  tasks = collections.defaultdict(set)
  for (acro, ks) in varRels.items():
    j = searchExe.relationFromName[acro]
    ji = searchExe.converse[j]
    if ji < j:
      (j, ji) = (ji, j)
    acro = relations[j]['acro']
    acroi = relations[ji]['acro']
    tasks[(j, acro, ji, acroi)] |= ks

  for ((j, acro, ji, acroi), ks) in tasks.items():
    for k in ks:
      newAcro = acro.replace('k', str(k))
      newAcroi = acroi.replace('k', str(k))
      r = relations[j]
      ri = relations[ji]
      lr = len(relations)
      relations.extend([
          dict(
              name=acro,
              acro=newAcro,
              spin=r['spin'],
              func=r['func'](k),
              desc=r['desc'],
          ),
          dict(
              name=acroi,
              acro=newAcroi,
              spin=ri['spin'],
              func=ri['func'](k),
              desc=ri['desc'],
          ),
      ])
      searchExe.relationFromName[newAcro] = lr
      searchExe.relationFromName[newAcroi] = lr + 1
      searchExe.converse[lr] = lr + 1
      searchExe.converse[lr + 1] = lr


def add_F_Relations(searchExe, varRels):
  relations = searchExe.relations
  tasks = collections.defaultdict(set)
  for (acro, feats) in varRels.items():
    j = searchExe.relationFromName[acro]
    ji = searchExe.converse[j]
    if ji < j:
      (j, ji) = (ji, j)
    acro = relations[j]['acro']
    acroi = relations[ji]['acro']
    tasks[(j, acro, ji, acroi)] |= feats

  for ((j, acro, ji, acroi), feats) in tasks.items():
    for featInfo in feats:
      if len(featInfo) == 2:
        ((f, fF), (t, gF)) = featInfo
        acroFmt = acro.replace('f', '{f}').replace('g', '{g}')
        acroiFmt = acroi.replace('f', '{f}').replace('g', '{g}')
        newAcro = acroFmt.format(f=fF, g=gF)
        newAcroi = acroiFmt.format(f=fF, g=gF)
        fArgs = (fF, gF)
      else:
        ((f, fF), rPat, (t, gF)) = featInfo
        acroFmt = acro.replace('f', '{f}').replace('r', '{r}').replace('g', '{g}')
        acroiFmt = acroi.replace('f', '{f}').replace('r', '{r}').replace('g', '{g}')
        newAcro = acroFmt.format(f=fF, r=rPat, g=gF)
        newAcroi = acroiFmt.format(f=fF, r=rPat, g=gF)
        rRe = re.compile(rPat)
        fArgs = (fF, rPat, rRe, gF)

      r = relations[j]
      ri = relations[ji]
      lr = len(relations)
      spin = r['spin']
      if isinstance(spin, types.FunctionType):
        spin = spin(*fArgs)
      spini = ri['spin']
      if isinstance(spini, types.FunctionType):
        spini = spini(*fArgs)
      func = r['func'](*fArgs)
      funci = ri['func'](*fArgs)
      relations.extend([
          dict(
              name=acro,
              acro=newAcro,
              spin=spin,
              func=func,
              desc=r['desc'],
          ),
          dict(
              name=acroi,
              acro=newAcroi,
              spin=spini,
              func=funci,
              desc=ri['desc'],
          ),
      ])
      searchExe.relationFromName[newAcro] = lr
      searchExe.relationFromName[newAcroi] = lr + 1
      searchExe.nodeMap.setdefault(f, set()).add(fF)
      searchExe.nodeMap.setdefault(t, set()).add(gF)
      searchExe.converse[lr] = lr + 1
      searchExe.converse[lr + 1] = lr


def add_V_Relations(searchExe, varRels):
  relations = searchExe.relations
  tasks = collections.defaultdict(set)
  for (acro, vals) in sorted(varRels.items()):
    for (eName, val) in vals:
      (b, mid, e) = (acro[0], acro[1:-1], acro[-1])
      norm = b == '-' and e == '>'
      conv = b == '<' and e == '-'
      eRel = f'-{eName}>'
      eReli = f'<{eName}-'
      eRels = f'<{eName}>'
      acroi = f'-{mid}>' if conv else f'<{mid}-' if norm else f'<{mid}>'
      if conv:
        (acro, acroi) = (acroi, acro)
      j = searchExe.relationFromName[eRel]
      ji = searchExe.relationFromName[eReli]
      js = searchExe.relationFromName[eRels]
      if norm or conv:
        tasks[(eName, j, acro, ji, acroi)].add(val)
      else:
        tasks[(eName, js, acro, js, acro)].add(val)

  for ((eName, j, acro, ji, acroi), vals) in sorted(tasks.items()):
    for val in vals:
      r = relations[j]
      ri = relations[ji]
      lr = len(relations)
      relations.extend([
          dict(
              acro=acro,
              spin=r['spin'],
              func=r['func'](val),
              desc=r['desc'],
          ),
          dict(
              acro=acroi,
              spin=ri['spin'],
              func=ri['func'](val),
              desc=ri['desc'],
          ),
      ])
      searchExe.relationFromName[acro] = lr
      searchExe.relationFromName[acroi] = lr + 1
      if j == ji:
        searchExe.edgeMap[lr] = (eName, 0)
        searchExe.edgeMap[lr + 1] = (eName, 0)
      else:
        searchExe.edgeMap[lr] = (eName, 1)
        searchExe.edgeMap[lr + 1] = (eName, -1)
      searchExe.converse[lr] = lr + 1
      searchExe.converse[lr + 1] = lr
