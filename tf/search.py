import re, types, collections
from functools import reduce
from random import randrange
from inspect import signature

from .data import GRID, SECTIONS

STRATEGY = '''
    small_choice_first
    spread_1_first
    big_choice_first
'''.strip().split()

escapes = (
    '\\\\',
    '\\ ',
    '\\t',
    '\\n',
    '\\|',
    '\\=',
)

def esc(x):
    for (i, c) in enumerate(escapes):
        x = x.replace(c, chr(i))
    return x

def unesc(x):
    for (i, c) in enumerate(escapes):
        x = x.replace(chr(i), c[1])
    return x

class Search(object):
    def __init__(self, api, tf, silent):
        self.api = api
        self.tf = tf
        self.good = True
        self.silent = silent
        self._basicRelations()

### API METHODS ###

    def search(self, searchTemplate, limit=None):
        self.silent = True
        self.study(searchTemplate, silent=True)
        return self.fetch(limit=limit)

    def study(self, searchTemplate, strategy=None, silent=False):
        indent = self.api.indent
        info = self.api.info
        error = self.api.error
        self.silent = silent
        self.api.indent(level=0, reset=True)
        self.good = True

        self._setStrategy(strategy)
        if not self.good: return

        if not self.silent: info('Checking search template ...')
        self.searchTemplate = searchTemplate

        self._parse()
        self._prepare()
        if not self.good: return
        if not self.silent: info('Setting up search space for {} objects ...'.format(len(self.qnodes)))
        self._spinAtoms()
        if not self.silent: info('Constraining search space with {} relations ...'.format(len(self.qedges)))
        self._spinEdges()
        if not self.silent: info('Setting up retrieval plan ...')
        self._stitch()
        if self.good:
            if not self.silent:
                info('Ready to deliver results from {} nodes'.format(
                    sum(len(y) for y in self.yarns.values()),
                ))
            if not self.silent: info('Iterate over S.fetch() to get the results', tm=False)
            if not self.silent: info('See S.showPlan() to interpret the results', tm=False)

    def fetch(self, limit=None):
        if not self.good: return []
        if limit == None: return self.results()
        results = []
        for r in self.results():
            results.append(r)
            if len(results) == limit: break
        return tuple(results)

    def glean(self, r):
        T = self.api.T
        F = self.api.F
        L = self.api.L
        slotType = F.otype.slotType
        lR = len(r)
        if lR == 0: return ''
        fields = []
        for (i, n) in enumerate(r):
            otype = F.otype.v(n)
            words = [n] if otype == slotType else L.d(n, otype=slotType)
            if otype == SECTIONS[2]:
                field = '{} {}:{}'.format(*T.sectionFromNode(n))
            elif otype == slotType:
                field = T.text(words)
            elif otype in SECTIONS[0:2]:
                field = ''
            else:
                field = '{}[{}{}]'.format(
                    otype,
                    T.text(words[0:5]),
                    '...' if len(words) > 5 else '',
                )
            fields.append(field)
        return ' '.join(fields)

    def count(self, progress=None, limit=None):
        info = self.api.info
        error = self.api.error
        indent = self.api.indent
        indent(level=0, reset=True)

        if not self.good:
            self.error('This search has problems. No results to count.', tm=False)
            return

        PROGRESS = 100
        LIMIT = 1000

        if progress == None: progress = PROGRESS
        if limit == None: limit = LIMIT

        info('Counting results per {} up to {} ...'.format(
            progress,
            limit if limit > 0 else ' the end of the results',
        ))
        indent(level=1, reset=True)

        i = 0
        j = 0
        for r in self.results(remap=False):
            i += 1
            j += 1
            if j == progress:
                j = 0
                info(i)
            if limit > 0 and i >= limit: break

        indent(level=0)
        info('Done: {} results'.format(i))

    def showPlan(self, details=False):
        if not self.good: return
        info = self.api.info
        nodeLine = self.nodeLine
        qedges = self.qedges
        (qs, es) = self.stitchPlan
        if details:
            info('Search with {} objects and {} relations'.format(len(qs), len(es)), tm=False)
            info('Results are instantiations of the following objects:', tm=False)
            for q in qs: self._showNode(q)
            if len(es) != 0:
                info('Instantiations are computed along the following relations:', tm=False)
                (firstE, firstDir) = es[0]
                (f, rela, t) = qedges[firstE]
                if firstDir == -1: (f, t) = (t, f)
                self._showNode(f, pos2=True)
                for e in es: self._showEdge(*e)
        info('The results are connected to the original search template as follows:')

        resultNode = {}
        for q in qs:
            resultNode[nodeLine[q]] = q
        for (i, line) in enumerate(self.searchLines):
            rNode = resultNode.get(i, '')
            info('{:>2} {:<1}{:<2} {}'.format(
                i,
                'R' if rNode != '' else '',
                rNode,
                line,
            ), tm=False)
                   
### LOW-LEVEL NODE RELATIONS SEMANTICS ###

    def _basicRelations(self):
        C = self.api.C
        F = self.api.F
        E = self.api.E
        L = self.api.L
        Crank = C.rank.data
        ClevDown = C.levDown.data
        ClevUp = C.levUp.data
        (CfirstSlots, ClastSlots) = C.boundary.data
        Eoslots = E.oslots.data
        slotType = F.otype.slotType
        maxSlot = F.otype.maxSlot

        def equalR(fTp, tTp):
            return lambda n: (n,)

        def spinEqual(fTp, tTp):
            def doyarns(yF, yT):
                x = set(yF) & set(yT)
                return (x, x)
            return doyarns

        def unequalR(fTp, tTp):
            return lambda n, m: n != m

        def canonicalBeforeR(fTp, tTp):
            return lambda n, m: Crank[n-1] < Crank[m-1]
        
        def canonicalAfterR(fTp, tTp):
            return lambda n, m: Crank[n-1] > Crank[m-1]
        
        def spinSameSlots(fTp, tTp):
            if fTp == slotType and tTp == slotType:
                def doyarns(yF, yT):
                    x = set(yF) & set(yT)
                    return (x, x)
                return doyarns
            elif fTp == slotType or tTp == slotType:
                def doyarns(yS, y2):
                    sindex = {}
                    for m in y2:
                        ss = Eoslots[m-maxSlot-1]
                        if len(ss) == 1:
                            sindex.setdefault(ss[0], set()).add(m)
                    nyS = yS & set(sindex.keys())
                    ny2 = reduce(
                        set.union,
                        (sindex[s] for s in nyS),
                        set(),
                    )
                    return (nyS, ny2)
                if fTp == slotType:
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
                        s = frozenset(Eoslots[n-maxSlot-1])
                        sindexF.setdefault(s, set()).add(n)
                    sindexT = {}
                    for m in yT:
                        s = frozenset(Eoslots[m-maxSlot-1])
                        sindexT.setdefault(s, set()).add(m)
                    nyS = set(sindexF.keys()) & set(sindexT.keys())
                    nyF = reduce(
                        set.union,
                        (sindexF[s] for s in nyS),
                        set(),
                    )
                    nyT = reduce(
                        set.union,
                        (sindexT[s] for s in nyS),
                        set(),
                    )
                    return (nyF, nyT)
                return doyarns

        def sameSlotsR(fTp, tTp):
            if fTp == slotType and tTp == slotType:
                return lambda n: (n,)
            elif tTp == slotType:
                return lambda n, m: Eoslots[n-maxSlot-1] == (m,)
            elif fTp == slotType:
                return lambda n, m: Eoslots[m-maxSlot-1] == (n,)
            else:
                return lambda n, m: frozenset(Eoslots[n-maxSlot-1]) == frozenset(Eoslots[m-maxSlot-1])

        def spinOverlap(fTp, tTp):
            if fTp == slotType and tTp == slotType:
                def doyarns(yF, yT):
                    x = set(yF) & set(yT)
                    return (x, x)
                return doyarns
            elif fTp == slotType or tTp == slotType:
                def doyarns(yS, y2):
                    sindex = {}
                    for m in y2:
                        for s in Eoslots[m-maxSlot-1]:
                            sindex.setdefault(s, set()).add(m)
                    nyS = yS & set(sindex.keys())
                    ny2 = reduce(
                        set.union,
                        (sindex[s] for s in nyS),
                        set(),
                    )
                    return (nyS, ny2)
                if fTp == slotType:
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
                        for s in Eoslots[n-maxSlot-1]:
                            sindexF.setdefault(s, set()).add(n)
                    sindexT = {}
                    for m in yT:
                        for s in Eoslots[m-maxSlot-1]:
                            sindexT.setdefault(s, set()).add(m)
                    nyS = set(sindexF.keys()) & set(sindexT.keys())

                    lsF = len(sindexF)
                    lsT = len(sindexT)
                    lsI = len(nyS)
                    if lsF == lsT: # spinning is completely useless
                        return (yF, yT)
                    if lsI > REDUCE_FACTOR * lsT and lsT > SIZE_LIMIT: # spinning is not worth it
                        return (yF, yT)

                    if not self.silent: self.api.info('1. reducing over {} elements'.format(len(nyS)))
                    nyF = reduce(
                        set.union,
                        (sindexF[s] for s in nyS),
                        set(),
                    )
                    if not self.silent: self.api.info('2. reducing over {} elements'.format(len(nyS)))
                    nyT = reduce(
                        set.union,
                        (sindexT[s] for s in nyS),
                        set(),
                    )
                    return (nyF, nyT)
                return doyarns

        def overlapR(fTp, tTp):
            if fTp == slotType and tTp == slotType:
                return lambda n: (n,)
            elif tTp == slotType:
                return lambda n: Eoslots[n-maxSlot-1]
            elif fTp == slotType:
                return lambda n, m: n in frozenset(Eoslots[m-maxSlot-1])
            else:
                return lambda n, m: len(frozenset(Eoslots[n-maxSlot-1]) & frozenset(Eoslots[m-maxSlot-1])) != 0

        def diffSlotsR(fTp, tTp):
            if fTp == slotType and tTp == slotType:
                return lambda n, m: m != n
            elif tTp == slotType:
                return lambda n, m: Eoslots[m-maxSlot-1] != (n,)
            elif fTp == slotType:
                return lambda n, m: Eoslots[n-maxSlot-1] != (m,)
            else:
                return lambda n, m: frozenset(Eoslots[n-maxSlot-1]) != frozenset(Eoslots[m-maxSlot-1])

        def disjointSlotsR(fTp, tTp):
            if fTp == slotType and tTp == slotType:
                return lambda n, m: m != n
            elif tTp == slotType:
                return lambda n, m: n not in frozenset(Eoslots[m-maxSlot-1])
            elif fTp == slotType:
                return lambda n, m: m not in frozenset(Eoslots[n-maxSlot-1])
            else:
                return lambda n, m: len(frozenset(Eoslots[n-maxSlot-1]) & frozenset(Eoslots[m-maxSlot-1])) == 0

        def inR(fTp, tTp):
            if fTp == slotType and tTp == slotType:
                return lambda n: ()
            elif tTp == slotType:
                return lambda n: ()
            elif fTp == slotType:
                return lambda n: ClevUp[n-1]
            else:
                return lambda n: ClevUp[n-1]

        def hasR(fTp, tTp):
            if fTp == slotType and tTp == slotType:
                return lambda n: ()
            elif fTp == slotType:
                return lambda n: ()
            elif tTp == slotType:
                return lambda n: Eoslots[n-maxSlot-1]
            else:
                return lambda n: ClevDown[n-maxSlot-1]

        def slotBeforeR(fTp, tTp):
            if fTp == slotType and tTp == slotType:
                return lambda n, m: n < m
            elif fTp == slotType:
                return lambda n, m: n < Eoslots[m-maxSlot-1][0]
            elif tTp == slotType:
                return lambda n, m: Eoslots[n-maxSlot-1][-1] < m
            else:
                return lambda n, m: Eoslots[n-maxSlot-1][-1] < Eoslots[m-maxSlot-1][0]

        def slotAfterR(fTp, tTp):
            if fTp == slotType and tTp == slotType:
                return lambda n, m: n > m
            elif fTp == slotType:
                return lambda n, m: n > Eoslots[m-maxSlot-1][-1]
            elif tTp == slotType:
                return lambda n, m: Eoslots[n-maxSlot-1][0] > m
            else:
                return lambda n, m: Eoslots[n-maxSlot-1][0] > Eoslots[m-maxSlot-1][-1]

        def sameFirstSlotR(fTp, tTp):
            if fTp == slotType and tTp == slotType:
                return lambda n: (n,)
            elif fTp == slotType:
                return lambda n: CfirstSlots[n-1]
            elif tTp == slotType:
                return lambda n: (Eoslots[n-maxSlot-1][0],)
            else:
                def xx(n):
                    fn = Eoslots[n-maxSlot-1][0]
                    return CfirstSlots[fn-1]
                return xx

        def sameLastSlotR(fTp, tTp):
            if fTp == slotType and tTp == slotType:
                return lambda n: (n,)
            elif fTp == slotType:
                return lambda n: ClastSlots[n-1]
            elif tTp == slotType:
                return lambda n: (Eoslots[n-maxSlot-1][-1],)
            else:
                def xx(n):
                    ln = Eoslots[n-maxSlot-1][-1]
                    return ClastSlots[ln-1]
                return xx

        def sameBoundaryR(fTp, tTp):
            if fTp == slotType and tTp == slotType:
                return lambda n: (n,)
            elif fTp == slotType:
                def xx(n):
                    fok =  set(CfirstSlots[n-1])
                    lok =  set(ClastSlots[n-1])
                    return tuple(fok & lok)
                return xx
            elif tTp == slotType:
                def xx(n):
                    slots = Eoslots[n-maxSlot-1]
                    f = slots[0]
                    l = slots[-1]
                    return (f,) if f == l else ()
                return xx
            else:
                def xx(n):
                    fn = Eoslots[n-maxSlot-1][0]
                    ln = Eoslots[n-maxSlot-1][-1]
                    fok =  set(CfirstSlots[fn-1])
                    lok =  set(ClastSlots[ln-1])
                    return tuple(fok & lok)
                return xx

        def nearFirstSlotR(k):
            def zz(fTp, tTp):
                if fTp == slotType and tTp == slotType:
                    return lambda n: tuple(m for m in range(max((1, n-k)), min((maxSlot, n+k+1))))
                elif fTp == slotType:
                    def xx(n):
                        near = set(l for l in range(max((1, n-k)), min((maxSlot, n+k+1))))
                        return tuple(reduce(
                            set.union,
                            (set(CfirstSlots[l-1]) for l in near),
                            set(),
                        ))
                    return xx
                elif tTp == slotType:
                    def xx(n):
                        fn = Eoslots[n-maxSlot-1][0]
                        return tuple(m for m in range(max((1, fn-k)), min((maxSlot, fn+k+1))))
                    return xx
                else:
                    def xx(n):
                        fn = Eoslots[n-maxSlot-1][0]
                        near = set(l for l in range(max((1, fn-k)), min((maxSlot, fn+k+1))))
                        return tuple(reduce(
                            set.union,
                            (set(CfirstSlots[l-1]) for l in near),
                            set(),
                        ))
                    return xx
            return zz

        def nearLastSlotR(k):
            def zz(fTp, tTp):
                if fTp == slotType and tTp == slotType:
                    return lambda n: tuple(m for m in range(max((1, n-k)), min((maxSlot, n+k+1))))
                elif fTp == slotType:
                    def xx(n):
                        near = set(l for l in range(max((1, n-k)), min((maxSlot, n+k+1))))
                        return tuple(reduce(
                            set.union,
                            (set(ClastSlots[l-1]) for l in near),
                            set(),
                        ))
                    return xx
                elif tTp == slotType:
                    def xx(n):
                        ln = Eoslots[n-maxSlot-1][-1]
                        return tuple(m for m in range(max((1, ln-k)), min((maxSlot, ln+k+1))))
                    return xx
                else:
                    def xx(n):
                        ln = Eoslots[n-maxSlot-1][-1]
                        near = set(l for l in range(max((1, ln-k)), min((maxSlot, ln+k+1))))
                        return tuple(reduce(
                            set.union,
                            (set(ClastSlots[l-1]) for l in near),
                            set(),
                        ))
                    return xx
            return zz

        def nearBoundaryR(k):
            def zz(fTp, tTp):
                if fTp == slotType and tTp == slotType:
                    return lambda n: tuple(m for m in range(max((1, n-k)), min((maxSlot, n+k+1))))
                elif fTp == slotType:
                    def xx(n):
                        near = set(l for l in range(max((1, n-k)), min((maxSlot, n+k+1))))
                        fok = set(reduce(
                            set.union,
                            (set(CfirstSlots[l-1]) for l in near),
                            set(),
                        ))
                        lok = set(reduce(
                            set.union,
                            (set(ClastSlots[l-1]) for l in near),
                            set(),
                        ))
                        return tuple(fok & lok)
                    return xx
                elif tTp == slotType:
                    def xx(n):
                        slots = Eoslots[n-maxSlot-1]
                        f = slots[0]
                        l = slots[-1]
                        fok = set(m for m in range(max((1, f-k)), min((maxSlot, f+k+1))))
                        lok = set(m for m in range(max((1, l-k)), min((maxSlot, l+k+1))))
                        return tuple(fok & lok)
                    return xx
                else:
                    def xx(n):
                        fn = Eoslots[n-maxSlot-1][0]
                        ln = Eoslots[n-maxSlot-1][-1]
                        nearf = set(l for l in range(max((1, fn-k)), min((maxSlot, fn+k+1))))
                        nearl = set(l for l in range(max((1, ln-k)), min((maxSlot, ln+k+1))))
                        fok =  set(CfirstSlots[fn-1])
                        lok =  set(ClastSlots[ln-1])
                        fok = set(reduce(
                            set.union,
                            (set(CfirstSlots[l-1]) for l in nearf),
                            set(),
                        ))
                        lok = set(reduce(
                            set.union,
                            (set(ClastSlots[l-1]) for l in nearl),
                            set(),
                        ))
                        return tuple(fok & lok)
                    return xx
            return zz

        def adjBeforeR(fTp, tTp):
            if fTp == slotType and tTp == slotType:
                return lambda n: (n+1,) if n < maxSlot else () 
            else:
                def xx(n):
                    if n == maxSlot: return ()
                    myNext = n+1 if n < maxSlot else Eoslots[n-maxSlot-1][-1] + 1
                    if myNext > maxSlot: return ()
                    return CfirstSlots[myNext-1] + (myNext,)
                return xx

        def adjAfterR(fTp, tTp):
            if fTp == slotType and tTp == slotType:
                return lambda n: (n-1,) if n > 1 else () 
            else:
                def xx(n):
                    if n <= 1: return ()
                    myPrev = n-1 if n < maxSlot else Eoslots[n-maxSlot-1][0]-1
                    if myPrev <= 1: return ()
                    return (myPrev,) + ClastSlots[myPrev-1]
                return xx

        def nearBeforeR(k):
            def zz(fTp, tTp):
                if fTp == slotType and tTp == slotType:
                    return lambda n: tuple(m for m in range(max((1, n+1-k)), min((maxSlot, n+1+k+1))))
                else:
                    def xx(n):
                        myNext = n+1 if n < maxSlot else Eoslots[n-maxSlot-1][-1] + 1
                        myNextNear = tuple(l for l in range(max((1, myNext-k)), min((maxSlot, myNext+k+1))))
                        nextSet = set(reduce(
                            set.union,
                            (set(CfirstSlots[l-1]) for l in myNextNear),
                            set(),
                        ))
                        return tuple(nextSet)+myNextNear
                    return xx
            return zz

        def nearAfterR(k):
            def zz(fTp, tTp):
                if fTp == slotType and tTp == slotType:
                    return lambda n: tuple(m for m in range(max((1, n-1-k)), min((maxSlot, n-1+k+1))))
                else:
                    def xx(n):
                        myPrev = n-1 if n < maxSlot else Eoslots[n-maxSlot-1][0] - 1
                        myPrevNear = tuple(l for l in range(max((1, myPrev-k)), min((maxSlot, myPrev+k+1))))
                        prevSet = set(reduce(
                            set.union,
                            (set(ClastSlots[l-1]) for l in myPrevNear),
                            set(),
                        ))
                        return tuple(prevSet)+myPrevNear
                    return xx
            return zz

        def makeEdgeMaps(efName):
            def edgeR(ftP, tTp):
                Es = self.api.Es
                return lambda n: Es(efName).f(n)

            def edgeIR(ftP, tTp):
                Es = self.api.Es
                return lambda n: Es(efName).t(n)
            return (edgeR, edgeIR)

        relations = [
            (
                ( '='  , spinEqual,     equalR           , 'left equal to right (as node)'),
                ( '='  , spinEqual,     equalR           , None),
            ),
            (
                ( '#'  , 0.999,         unequalR         , 'left unequal to right (as node)'),
                ( '#'  , 0.999,         unequalR         , None),
            ),
            (
                ( '<'  , 0.500,         canonicalBeforeR , 'left before right (in canonical node ordering)'),
                ( '>'  , 0.500,         canonicalAfterR  , 'left after right (in canonical node ordering)'),
            ),
            (
                ( '==' , spinSameSlots, sameSlotsR       , 'left occupies same slots as right'),
                ( '==' , spinSameSlots, sameSlotsR       , None),
            ),
            (
                ( '&&' , spinOverlap,   overlapR         , 'left has overlapping slots with right'),
                ( '&&' , spinOverlap,   overlapR         , None),
            ),
            (
                ( '##' , 0.990,         diffSlotsR       , 'left and right do not have the same slot set'),
                ( '##' , 0.990,         diffSlotsR       , None),
            ),
            (
                ( '||' , 0.900,         disjointSlotsR   , 'left and right do not have common slots'),
                ( '||' , 0.900,         disjointSlotsR   , None),
            ),
            (
                ( '[[' , True,          hasR             , 'left embeds right'),
                ( ']]' , True,          inR              , 'left embedded in right'),
            ),
            (
                ( '<<' , 0.490,         slotBeforeR      , 'left completely before right'),
                ( '>>' , 0.490,         slotAfterR       , 'left completely after right'),
            ),
            (
                ( '=:' , True,          sameFirstSlotR   , 'left and right start at the same slot'),
                ( '=:' , True,          sameFirstSlotR   , None),
            ),
            (
                ( ':=' , True,          sameLastSlotR    , 'left and right end at the same slot'),
                ( ':=' , True,          sameLastSlotR    , None),
            ),
            (
                ( '::' , True,          sameBoundaryR    , 'left and right start and end at the same slot'),
                ( '::' , True,          sameBoundaryR    , None),
            ),
            (
                ( '<:' , True,          adjBeforeR       , 'left immediately before right'),
                ( ':>' , True,          adjAfterR        , 'left immediately after right'),
            ),
            (
                ( '=k:' , True,         nearFirstSlotR   , 'left and right start at k-nearly the same slot'),
                ( '=k:' , True,         nearFirstSlotR   , None),
            ),
            (
                ( ':k=' , True,         nearLastSlotR    , 'left and right end at k-nearly the same slot'),
                ( ':k=' , True,         nearLastSlotR    , None),
            ),
            (
                ( ':k:' , True,         nearBoundaryR    , 'left and right start and end at k-near slots'),
                ( ':k:' , True,         nearBoundaryR    , None),
            ),
            (
                ( '<k:' , True,         nearBeforeR      , 'left k-nearly before right'),
                ( ':k>' , True,         nearAfterR       , 'left k-nearly after right'),
            ),
        ]

        self.tf.explore(silent=self.silent)
        edgeMap = {}

        for efName in sorted(self.tf.featureSets['edges']):
            if efName == GRID[1]: continue
            r = len(relations)

            (edgeR, edgeIR) = makeEdgeMaps(efName)
            relations.append((
                ('-{}>'.format(efName), True, edgeR,  'edge feature "{}"'.format(efName)),
                ('<{}-'.format(efName), True, edgeIR, 'edge feature "{}" (opposite direction)'.format(efName)),
            ))
            edgeMap[2*r] = (efName, 1)
            edgeMap[2*r+1] = (efName, -1)
        lr = len(relations)

        relationsAll = []
        for (r, rc) in relations: relationsAll.extend([r, rc])

        self.relations = [dict(
            acro=r[0],
            spin=r[1],
            func=r[2],
            desc=r[3],
        ) for r in relationsAll]
        self.relationFromName = dict(((r['acro'], i) for (i, r) in enumerate(self.relations)))
        self.relationLegend = '\n'.join('{:>23} {}'.format(r['acro'], r['desc']) for r in self.relations if r['desc'] != None)
        self.relationLegend += '''
The grid feature "{}" cannot be used in searches.
Surely, one of the above relations on nodes and/or slots will suit you better!'''.format(GRID[1])
        self.converse = dict(tuple((2*i, 2*i + 1) for i in range(lr)) + tuple((2*i+1, 2*i) for i in range(lr))) 
        self.edgeMap = edgeMap

    def _addRelations(self, varRels):
        relations = self.relations
        tasks = collections.defaultdict(set)
        for (acro, ks) in varRels.items():
            j = self.relationFromName[acro]
            ji = self.converse[j]
            if ji < j: (j, ji) = (ji, j)
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
                        acro=newAcro,
                        spin=r['spin'],
                        func=r['func'](k),
                        desc=r['desc'],
                    ),
                    dict(
                        acro=newAcroi,
                        spin=ri['spin'],
                        func=ri['func'](k),
                        desc=ri['desc'],
                    ),
                ])
                self.relationFromName[newAcro] = lr
                self.relationFromName[newAcroi] = lr+1
                self.converse[lr] = lr + 1
                self.converse[lr + 1] = lr

### SYNTACTIC ANALYSIS OF SEARCH TEMPLATE ###

    def _tokenize(self):            
        if not self.good: return

        opPat = '(?:[#&|\[\]<>:=-]+\S*)'
        atomPat = '(\s*)([^ \t=]+)(?:(?:\s*\Z)|(?:\s+(.*)))$'
        atomOpPat = '(\s*)({op})\s+([^ \t=]+)(?:(?:\s*\Z)|(?:\s+(.*)))$'.format(op=opPat)
        opLinePat = '(\s*)({op})\s*$'.format(op=opPat)
        namePat = '[A-Za-z0-9_-]+'
        relPat = '^\s*({nm})\s+({op})\s+({nm})\s*$'.format(nm=namePat, op=opPat)
        
        atomOpRe = re.compile(atomOpPat)
        atomRe = re.compile(atomPat)
        opLineRe = re.compile(opLinePat)
        nameRe = re.compile('^{}$'.format(namePat))
        relRe = re.compile(relPat)
        whiteRe = re.compile('^\s*$')
        
        def getFeatures(x):
            features = {}
            wrongs = []
            featureList = (x if x != None else '').split()
            for feat in featureList:
                featComps = feat.split('=', 1)
                if len(featComps) != 2:
                    wrongs.append(unesc(feat))
                    continue
                featName = unesc(featComps[0])
                featValList = featComps[1]
                featVals = set(unesc(featVal) for featVal in featValList.split('|'))
                features[featName] = featVals
            return (features, wrongs)
        
        searchLines = self.searchLines
        tokens = []
        allGood = True
        for (i, line) in enumerate(searchLines):
            if line.startswith('#') or whiteRe.match(line): continue
            good = False
            for x in [True]:
                match = opLineRe.match(line)
                if match:
                    (indent, op) = match.groups()
                    tokens.append((i, 'atom', len(indent), op))
                    good = True
                    break
                match = relRe.match(line)
                if match:
                    tokens.append((i, 'rel', match.group(1), match.group(2), match.group(3)))
                    good = True
                    break
                matchOp = atomOpRe.match(esc(line))
                if not matchOp:
                    match = atomRe.match(esc(line))
                if matchOp:
                    (indent, op, atom, features) = matchOp.groups()
                elif match:
                    op = None
                    (indent, atom, features) = match.groups()
                if matchOp or match:
                    atomComps = atom.split(':', 1)
                    if len(atomComps) == 1:
                        name = ''
                    else:
                        name = unesc(atomComps[0])
                        atom = unesc(atomComps[1])
                        mt = nameRe.match(name)
                        if not mt:
                            self.badSyntax.append('Illegal name at line {}: "{}"'.format(i, name))
                            good = False
                    (features, wrongs) = getFeatures(features)
                    if len(wrongs):
                        for wrong in wrongs:
                            self.badSyntax.append('Illegal feature specification at line {}: "{}"'.format(i, wrong))
                        good = False
                        break                
                    tokens.append((i, 'atom', len(indent), op, name, atom, features))
                    good = True
                    break
                (features, wrongs) = getFeatures(esc(line))
                if len(wrongs):
                    for wrong in wrongs:
                        self.badSyntax.append('Illegal feature specification at line {}: "{}"'.format(i, wrong))
                    good = False
                    break                
                tokens.append((i, 'feat', features))
                good = True
                break
            if not good: allGood = False
        if allGood:
            self.tokens = tokens
        else:
            self.good = False
        
    def _syntax(self):
        error = self.api.error
        self.good = True
        self.badSyntax = []
        self.searchLines = self.searchTemplate.split('\n')
        self._tokenize()
        if not self.good:
            for (i, line) in enumerate(self.searchLines):
                error('{:>2} {}'.format(i, line), tm=False)
            for eline in self.badSyntax:
                error(eline, tm=False)

### SEMANTIC ANALYSIS OF SEARCH TEMPLATE ###

    def _grammar(self):
        if not self.good: return

        prevKind = None
        good = True
        meaning = []
        qnames = {}
        qnodes = []
        qedges = []
        edgeLine = {}
        nodeLine = {}
        tokens = sorted(self.tokens, key=lambda t: (len(self.tokens)+t[0]) if t[1] == 'rel' else t[0])

        # atomStack is a stack of qnodes with their indent levels
        # such that every next member is one level deeper
        # and every member is the last qnode encountered at that level
        # The stack is implemented as a dict, keyed by the indent, and valued by the qnode
        atomStack = {}
        
        for (i, kind, *fields) in tokens:
            if kind == 'atom':
                if len(fields) == 2:
                    (indent, op) = fields
                else:
                    (indent, op, name, otype, features) = fields
                    qnodes.append((otype, features))
                    q = len(qnodes) - 1
                    nodeLine[q] = i
                    name = ':{}'.format(i) if name == '' else name
                    qnames[name] = q
                if len(atomStack) == 0:
                    if indent > 0:
                        self.badSemantics.append('Unexpected indent at line {}: {}, expected {}'.format(i, indent, 0))
                        good = False
                    if op != None:
                        self.badSemantics.append('Lonely relation at line {}: not allowed at outermost level'.format(i))
                        good = False
                    if len(fields) > 2:
                        atomStack[0] = q
                else:
                    atomNest = sorted(atomStack.items(), key=lambda x: x[0])
                    top = atomNest[-1]
                    if indent == top[0]:  
                        # sibling of previous atom
                        if len(atomNest) > 1:
                            if len(fields) == 2:
                                # lonely operator: left is previous atom, right is parent atom
                                qedges.append((top[1], op, atomNest[-2][1]))
                                edgeLine[len(qedges) - 1] = i
                            else:
                                # take the qnode of the subtop of the atomStack, if there is one
                                qedges.append((q, ']]', atomNest[-2][1]))
                                edgeLine[len(qedges) - 1] = i
                                if op != None:
                                    qedges.append((top[1], op, q))
                                    edgeLine[len(qedges) - 1] = i
                    elif indent > top[0]:
                        if len(fields) == 2:
                            self.badSemantics.append('Lonely relation at line {}: not allowed as first child'.format(i))
                            good = False
                        else:
                            # child of previous atom
                            qedges.append((q, ']]', top[1]))
                            edgeLine[len(qedges) - 1] = i
                            if op != None:
                                qedges.append((top[1], op, q))
                                edgeLine[len(qedges) - 1] = i
                    else:
                        # outdent action: look up the proper parent in the stack
                        if indent not in atomStack:
                            # parent cannot be found: indentation error
                            self.badSemantics.append('Unexpected indent at line {}: {}, expected one of {}'.format(
                                i, indent,
                                ','.join(str(at[0]) for at in atomNest if at[0] < indent),
                            ))
                            good = False
                        else:
                            parents = [at[1] for at in atomNest if at[0] < indent]
                            if len(parents) != 0: # if not already at outermost level
                                if len(fields) == 2: # connect previous sibling to parent
                                    qedges.append((atomStack[indent], op, parents[-1]))
                                    edgeLine[len(qedges) - 1] = i
                                else:
                                    qedges.append((q, ']]', parents[-1]))
                                    edgeLine[len(qedges) - 1] = i
                                    if op != None:
                                        qedges.append((atomStack[indent], op, q))
                                        edgeLine[len(qedges) - 1] = i
                            removeKeys = [at[0] for at in atomNest if at[0] > indent]
                            for rk in removeKeys: del atomStack[rk]
                    atomStack[indent] = q
            elif kind == 'feat':
                features = fields[0]
                if prevKind != None and prevKind != 'atom':
                    self.badSemantics.append('Features without atom at line {}: "{}"'.format(i, features))
                    good = False
                else:
                    qnodes[-1][1].update(features)
            elif kind == 'rel':
                (fName, opName, tName) = fields
                f = qnames.get(fName, None)
                t = qnames.get(tName, None)
                namesGood = True
                for (q, n) in ((f, fName), (t, tName)):
                    if q == None:
                        self.badSemantics.append('Relation with undefined name at line {}: "{}"'.format(i, n))
                        namesGood = False
                if not namesGood:
                    good = False
                else:
                    qedges.append((f, opName, t))                
                    edgeLine[len(qedges) - 1] = i
            prevKind = kind
        if good:
            self.qnames = qnames
            self.qnodes = qnodes
            self.qedgesRaw = qedges
            self.nodeLine = nodeLine
            self.edgeLine = edgeLine
        else:
            self.good = False

    def _validation(self):
        if not self.good: return

        levels = self.api.C.levels.data
        otypes = set(x[0] for x in levels)
        qnodes = self.qnodes
        nodeLine = self.nodeLine
        edgeMap = self.edgeMap

        edgeLine = self.edgeLine
        relationFromName = self.relationFromName


        # check the object types of atoms

        otypesGood = True
        for (q, (otype, xx)) in enumerate(qnodes):
            if otype not in otypes:
                self.badSemantics.append('Unknown object type in line {}: "{}"'.format(nodeLine[q], otype))
                otypesGood = False
        if not otypesGood:
            self.badSemantics.append('Valid object types are: {}'.format(
                ','.join(x[0] for x in levels),
            ))
            self.good = False

        # check the feature names of feature specs and check the types of their values

        missingFeatures = {}
        wrongValues = {}
        for (q, (xx, features)) in enumerate(qnodes):
            for (fName, values) in features.items():
                if fName not in self.tf.featureSets['nodes']:
                    missingFeatures.setdefault(fName, []).append(q)
                else:
                    valuesCast = set()
                    requiredType = self.tf.features[fName].dataType
                    if requiredType == 'int':
                        for val in values:
                            try:
                                valCast = int(val)
                            except:
                                valCast = val
                                wrongValues.setdefault(fName, {}).setdefault(val, []).append(q)
                            valuesCast.add(valCast)
                        features[fName] = valuesCast

        if len(missingFeatures):
            for (fName, qs) in sorted(missingFeatures.items()):
                self.badSemantics.append('Missing feature "{}" in line(s) {}'.format(
                    fName, ','.join(str(nodeLine[q]) for q in qs),
                ))
            self.good = False

        if len(wrongValues):
            for (fName, wrongs) in sorted(wrongValues.items()):
                self.badSemantics.append('Feature "{}" has wrong values:'.format(fName))
                for (val, qs) in sorted(wrongs.items()):
                    self.badSemantics.append('    "{}" is not a number: line(s) {}'.format(
                        val, ','.join(str(nodeLine[q]) for q in qs),
                    ))
            self.good = False

        # check the relational operator token in edges and replace them by an index
        # in the relations array of known relations
        qedges = []
        edgesGood = True
        kRe = re.compile('^([^0-9]*)([0-9]+)([^0-9]*)$')
        addRels = {}
        for (e, (f, opName, t)) in enumerate(self.qedgesRaw):
            match = kRe.findall(opName)
            if len(match):
                (pre, k, post) = match[0]
                opNameK = '{}{}{}'.format(pre, 'k', post)
                addRels.setdefault(opNameK, set()).add(int(k))
        self._addRelations(addRels)
        for (e, (f, opName, t)) in enumerate(self.qedgesRaw):
            match = kRe.findall(opName)
            if len(match):
                (pre, k, post) = match[0]
                opNameK = '{}{}{}'.format(pre, 'k', post)
            rela = relationFromName.get(opName, None)
            if rela == None:
                self.badSemantics.append('Unknown relation in line {}: "{}"'.format(edgeLine[e], opName))
                edgesGood = False
            qedges.append((f, rela, t))
        if not edgesGood:
            self.badSemantics.append('Allowed relations:\n{}'.format(self.relationLegend))
            self.good = False
        self.qedges = qedges

        # determine which node and edge features are not yet loaded, and load them
        eFeatsUsed = set()
        for (f, rela, t) in qedges:
            efName = edgeMap.get(rela, (None,))[0]
            if efName != None:
                eFeatsUsed.add(efName)
        nFeatsUsed = set()
        for (xx, features) in qnodes:
            for nfName in features:
                nFeatsUsed.add(nfName)

        if self.good:
            needToLoad = []
            for fName in sorted(eFeatsUsed | nFeatsUsed):
                fObj = self.tf.features[fName]
                if not fObj.dataLoaded or not hasattr(self.api.F, fName):
                    needToLoad.append((fName, fObj))
            if len(needToLoad):
                self.tf.load([x[0] for x in needToLoad], add=True, silent=True)

    def _semantics(self):
        self.badSemantics = []
        if not self.good: return
        error = self.api.error

        self._grammar()
        if not self.good:
            for (i, line) in enumerate(self.searchLines):
                error('{:>2} {}'.format(i, line), tm=False)
            for eline in self.badSemantics:
                error(eline, tm=False)
            return
        self._validation()
        if not self.good:
            for (i, line) in enumerate(self.searchLines):
                error('{:>2} {}'.format(i, line), tm=False)
            for eline in self.badSemantics:
                error(eline, tm=False)

### WORKING WITH THE SEARCH GRAPH ###

    def _connectedness(self):
        info = self.api.info
        error = self.api.error
        qnodes = self.qnodes
        qedges = self.qedges

        componentIndex = dict(((q, {q}) for q in range(len(qnodes))))
        for (f, rela, t) in qedges:
            if f != t:
                componentIndex[f] |= componentIndex[t]
                for u in componentIndex[f] - {f}:
                    componentIndex[u] = componentIndex[f]
        components = sorted(set(frozenset(c) for c in componentIndex.values()))
        componentIndex = {}
        for c in components:
            for q in c:
                componentIndex[q] = c
        componentEdges = {}
        for (e, (f, rela, t)) in enumerate(qedges):
            c = componentIndex[f]
            componentEdges.setdefault(c, []).append(e)
        self.components = []
        for c in components:
            self.components.append([
                sorted(c),
                componentEdges.get(c, [])
            ])
        lComps = len(self.components)
        if lComps == 0:
            error('Search without instructions. Tell me what to look for.')
            self.good = False
        elif lComps > 1:
            error('More than one connected components ({}):'.format(len(self.components)))
            error('Either run the subqueries one by one, or connect the components by a relation',tm=False)
            self.good = False

    def _showNode(self, q, pos2=False):
        qnodes = self.qnodes
        yarns = self.yarns
        space = ' ' * 19
        nodeInfo =     'node {} {:>2}-{:<13} ({:>6}   choices)'.format(
            space, q, qnodes[q][0], len(yarns[q]),
        ) if pos2 else 'node {:>2}-{:<13} {} ({:>6}   choices)'.format(
            q, qnodes[q][0], space, len(yarns[q]),
        )
        self.api.info(nodeInfo, tm=False)


    def _showEdge(self, e, dir):
        qnodes = self.qnodes
        qedges = self.qedges
        converse = self.converse
        relations = self.relations
        spreads = self.spreads
        spreadsC = self.spreadsC
        (f, rela, t) = qedges[e]
        if dir == -1: (f, rela, t) = (t, converse[rela], f)
        self.api.info('edge {:>2}-{:<13} {:^2} {:>2}-{:<13} ({:8.1f} choices)'.format(
            f, qnodes[f][0], relations[rela]['acro'], t, qnodes[t][0],
            spreads.get(e, -1) if dir == 1 else spreadsC.get(e, -1),
        ), tm=False)

    def _showYarns(self):
        for q in range(len(self.qnodes)): self._showNode(q)

### SPINNING ###

    def _spinAtom(self, q):
        F = self.api.F
        Fs = self.api.Fs
        qnodes = self.qnodes

        (otype, features) = qnodes[q]
        featureList = sorted(features.items())
        yarn = set()
        for n in F.otype.s(otype):
            good = True
            for (ft, val) in featureList:
                fval = Fs(ft).v(n)
                if type(val) is str or type(val) is int:
                    if fval != val:
                        good = False
                        break
                else:
                    if fval not in val:
                        good = False
                        break
            if good: yarn.add(n)
        self.yarns[q] = yarn

    def _spinAtoms(self):
        qnodes = self.qnodes
        for q in range(len(qnodes)): self._spinAtom(q)

    def _estimateSpreads(self, both=False):
        TRY_LIMIT_F = 10
        TRY_LIMIT_T = 10
        qnodes = self.qnodes
        relations = self.relations
        converse = self.converse
        qedges = self.qedges
        yarns = self.yarns

        self.spreadsC = {}
        self.spreads = {}

        for (e, (f, rela, t)) in enumerate(qedges):
            tasks = [(f, rela, t, 1)]
            if both:
                tasks.append((t, converse[rela], f, -1))
            for (tf, trela, tt, dir) in tasks:
                s = relations[trela]['spin']
                yarnF = yarns[tf]
                yarnT = yarns[tt]
                dest = self.spreads if dir == 1 else self.spreadsC
                if type(s) is float:
                    # fixed estimates
                    dest[e] = len(yarnT) * s
                    continue
                yarnF = list(yarnF)
                yarnT = yarns[tt]
                totalSpread = 0
                yarnFl = len(yarnF)
                if yarnFl < TRY_LIMIT_F:
                    triesn = yarnF
                else:
                    triesn = set(yarnF[randrange(yarnFl)] for n in range(TRY_LIMIT_F))
                if len(triesn) == 0:
                    dest[e] = 0
                else:
                    r = relations[trela]['func'](qnodes[tf][0], qnodes[tt][0])
                    nparams = len(signature(r).parameters)
                    if nparams == 1:
                        for n in triesn:
                            mFromN = set(r(n)) & yarnT
                            totalSpread += len(mFromN)
                    else:
                        for n in triesn:
                            thisSpread = 0
                            yarnTl = len(yarnT)
                            if yarnTl < TRY_LIMIT_T:
                                triesm = yarnT
                            else:
                                triesm = set(list(yarnT)[randrange(yarnTl)] for m in range(TRY_LIMIT_T))
                            if len(triesm) == 0:
                                thisSpread = 0
                            else:
                                for m in triesm:
                                    if r(n, m) : thisSpread += 1
                            totalSpread += yarnTl * thisSpread / len(triesm)
                    dest[e] = totalSpread / len(triesn)

    def _chooseEdge(self):
        F = self.api.F
        yarnFractionNode = {}
        qnodes = self.qnodes
        qedges = self.qedges
        spreads = self.spreads
        for (q, (otype, xx)) in enumerate(qnodes):
            (begin, end) = F.otype.sInterval(otype)
            nOtype = 1 + end - begin
            nYarn = len(self.yarns[q])
            yf = nYarn / nOtype
            yarnFractionNode[q] = yf * yf
        yarnFractionEdge = {}
        for (e, (f, rela, t)) in enumerate(qedges):
            if self.uptodate[e]: continue
            yarnFractionEdge[e] = yarnFractionNode[f] + yarnFractionNode[t] + spreads[e]
        firstEdge = sorted(yarnFractionEdge.items(), key=lambda x: x[1])[0][0]
        return firstEdge
            
    def _spinEdge(self, e):
        SPIN_LIMIT = 1000
        qnodes = self.qnodes
        relations = self.relations
        yarns = self.yarns
        spreads = self.spreads
        qedges = self.qedges
        uptodate = self.uptodate
        
        (f, rela, t) = qedges[e]
        yarnF = yarns[f]
        yarnT = yarns[t]
        uptodate[e] = True

        # if the yarns around an edge are big, and the spread of the relation is
        # also big, spinning costs an enormous amount of time, and will not help in
        # reducing the search space.
        # condition for skipping: spread times length from-yarn >= SPIN_LIMIT
        if spreads[e] * len(yarnF) >= SPIN_LIMIT: return

        # for some basic relations we know that spinning is useless
        s = relations[rela]['spin']
        if type(s) is float: return

        # for other basic realtions we have an optimized spin function
        if type(s) is types.FunctionType:
            (newYarnF, newYarnT) = s(qnodes[f][0], qnodes[t][0])(yarnF, yarnT)
        else:
            r = relations[rela]['func'](qnodes[f][0], qnodes[t][0])
            nparams = len(signature(r).parameters)
            newYarnF = set()
            newYarnT = set()
            
            if nparams == 1:
                for n in yarnF:
                    mFromN = set(r(n)) & yarnT
                    if len(mFromN):
                        newYarnT |= mFromN
                        newYarnF.add(n)
            else:
                for n in yarnF:
                    mFromN = set(m for m in yarnT if r(n, m))
                    if len(mFromN):
                        newYarnT |= mFromN
                        newYarnF.add(n)

        affectedF = len(newYarnF) != len(yarns[f])
        affectedT = len(newYarnT) != len(yarns[t])

        uptodate[e] = True
        for (oe, (of, orela, ot)) in enumerate(qedges):
            if oe == e: continue
            if (affectedF and f in {of, ot}) or (affectedT and t in {of, ot}):
                self.uptodate[oe] = False
        self.yarns[f] = newYarnF
        self.yarns[t] = newYarnT      

    def _spinEdges(self):
        qnodes = self.qnodes
        qedges = self.qedges
        yarns = self.yarns
        uptodate = self.uptodate

        self._estimateSpreads()

        for e in range(len(qedges)):
            uptodate[e] = False
        it = 0
        while 1:
            if min(len(yarns[q]) for q in range(len(qnodes))) == 0: break
            #if reduce(
            #    lambda y,z: y and z, 
            #    (uptodate[e] for e in range(len(qedges))),
            #    True,
            #): break
            if all(uptodate[e] for e in range(len(qedges))): break
            e = self._chooseEdge()
            (f, rela, t) = qedges[e]
            self._spinEdge(e)
            it += 1

### STITCHING: STRATEGIES ###

    def _spread_1_first(self):
        qedges = self.qedges
        qnodes = self.qnodes

        s1Edges = []
        for (e, (f, rela, t)) in enumerate(qedges):
            if self.spreads[e] <= 1:
                s1Edges.append((e, 1))
            if self.spreadsC[e] <= 1:
                s1Edges.append((e, -1))
# s1Edges contain all edges with spread <= 1, or whose converse has spread <= 1
# now we want to build the largest graph with the original nodes and these edges,
# such that you can walk from a starting point over directed s1 edges to every other point
# we initialize candidate graphs: for each node: singletons graph, no edges.
        candidates = []
# add s1 edges and nodes to all candidates
        for q in range(len(qnodes)): 
            cnodes = {q}
            cedges = set()
            cedgesOrder = []
            while 1:
                added = False
                for (e, dir) in s1Edges:
                    (f, rela, t) = qedges[e]
                    if dir == -1: (t,f) = (f,t)
                    if f in cnodes:
                        if t not in cnodes:
                            cnodes.add(t)
                            added = True
                        if (e, dir) not in cedges:
                            cedges.add((e, dir))
                            cedgesOrder.append((e, dir))
                            added = True
                if not added: break
            candidates.append((cnodes, cedgesOrder))

# pick the biggest graph (nodes and edges count for 1)
        startS1 = sorted(candidates, key=lambda x: len(x[0])+len(x[1]))[-1]

        newNodes = startS1[0]
        newEdges = startS1[1]
        doneEdges = set(e[0] for e in newEdges)

# we add all edges that are not yet in our startS1.
# we add them two-fold: also with converse, and we sort the result by spread
# then we start a big loop:
# in every iteration, we take the edge with smallest spread that can be connected
# to the graph under construction
# then we start a new iteration, because the graph has grown, and and new edges might
# have become connectable by that

# in order to fail early, we can also add edges if their from-nodes and to-nodes both have been
# targeted. 
# That means: an earlier edge went to f, an other earlier edge went to t, and if we
# have an edge from f to t, we'd better add it now, since it is an extra constraint
# and by testing it here we can avoid a lot of work.

        remainingEdges = set()
        for e in range(len(qedges)):
            if e not in doneEdges:
                remainingEdges.add((e, 1))
                remainingEdges.add((e, -1))
        remainingEdgesO = sorted(
            remainingEdges,
            key=lambda e: self.spreads[e[0]] if e[1] == 1 else self.spreadsC[e[0]],
        )

        while 1:
            added = False
            for (e, dir) in remainingEdgesO:
                if e in doneEdges: continue
                (f, rela, t) = qedges[e]
                if dir == -1: (f, t) = (t, f)
                if f in newNodes and t in newNodes:
                    newEdges.append((e, dir))
                    doneEdges.add(e)
                    added = True
            for (e, dir) in remainingEdgesO:
                if e in doneEdges: continue
                (f, rela, t) = qedges[e]
                if dir == -1: (f, t) = (t, f)
                if f in newNodes:
                    newNodes.add(t)
                    newEdges.append((e, dir))
                    doneEdges.add(e)
                    added = True
                    break
            if not added: break

        self.newNodes = newNodes
        self.newEdges = newEdges

    def _small_choice_first(self):

# This strategy does not try to make a big subgraph of edges with spread 1.
# The problem is that before the edges work, the initial yarn may have an enormous
# spread.
# Here we try out the strategy of postponing broad choices as long as possible.
# The inituition is that while we are making smaller choices, constraints are encountered,
# severely limiting the broader choices later on.

# So, we pick the yarn with the least amount of nodes as our starting point.
# The corresponding node is our singleton start set.
# In every iteration we do the following:
# - we pick all edges of which from- and to-nodes are already in the node set
# - we pick the edge with least spread that has a starting point in the set
# Until nothing changes anymore

        qedges = self.qedges
        qnodes = self.qnodes

        newNodes = {sorted(range(len(qnodes)), key=lambda x: len(self.yarns[x]))[0]}
        newEdges = []
        doneEdges = set()

        remainingEdges = set()
        for e in range(len(qedges)):
            remainingEdges.add((e, 1))
            remainingEdges.add((e, -1))
        remainingEdgesO = sorted(
            remainingEdges,
            key=lambda e: self.spreads[e[0]] if e[1] == 1 else self.spreadsC[e[0]],
        )

        while 1:
            added = False
            for (e, dir) in remainingEdgesO:
                if e in doneEdges: continue
                (f, rela, t) = qedges[e]
                if dir == -1: (f, t) = (t, f)
                if f in newNodes and t in newNodes:
                    newEdges.append((e, dir))
                    doneEdges.add(e)
                    added = True
            for (e, dir) in remainingEdgesO:
                if e in doneEdges: continue
                (f, rela, t) = qedges[e]
                if dir == -1: (f, t) = (t, f)
                if f in newNodes:
                    newNodes.add(t)
                    newEdges.append((e, dir))
                    doneEdges.add(e)
                    added = True
                    break
            if not added: break

        self.newNodes = newNodes
        self.newEdges = newEdges

    def _big_choice_first(self):

# For comparison: the opposite of _small_choice_first.
# Just to see what the performance difference is.

        qedges = self.qedges
        qnodes = self.qnodes

        newNodes = {sorted(range(len(qnodes)), key=lambda x: -len(self.yarns[x]))[0]}
        newEdges = []
        doneEdges = set()

        remainingEdges = set()
        for e in range(len(qedges)):
            remainingEdges.add((e, 1))
            remainingEdges.add((e, -1))
        remainingEdgesO = sorted(
            remainingEdges,
            key=lambda e: -self.spreads[e[0]] if e[1] == 1 else -self.spreadsC[e[0]],
        )

        while 1:
            added = False
            for (e, dir) in remainingEdgesO:
                if e in doneEdges: continue
                (f, rela, t) = qedges[e]
                if dir == -1: (f, t) = (t, f)
                if f in newNodes and t in newNodes:
                    newEdges.append((e, dir))
                    doneEdges.add(e)
                    added = True
            for (e, dir) in remainingEdgesO:
                if e in doneEdges: continue
                (f, rela, t) = qedges[e]
                if dir == -1: (f, t) = (t, f)
                if f in newNodes:
                    newNodes.add(t)
                    newEdges.append((e, dir))
                    doneEdges.add(e)
                    added = True
                    break
            if not added: break

        self.newNodes = newNodes
        self.newEdges = newEdges

### STITCHING ###

    def _stitch(self):
        yarns = self.yarns

        self._estimateSpreads(both=True)
        self._stitchPlan()
        if not self.good: return
        self._stitchResults()
        
### STITCHING: PLANNING ###

    def _stitchPlan(self, strategy=None):
        qnodes = self.qnodes
        qedges = self.qedges
        error = self.api.error

        self._setStrategy(strategy, keep=True)
        if not self.good: return

# Apply the chosen strategy
        self.strategy()

# remove spurious edges: if we have both the 1 and -1 version of an edge,
# we can leave out the one that we encounter in the second place

        newNodes = self.newNodes
        newEdges = self.newEdges

        newCedges = set()
        newCedgesOrder = []
        for (e, dir) in newEdges:
             if e not in newCedges:
                 newCedgesOrder.append((e, dir))
                 newCedges.add(e)

# conjecture: we have all edges and all nodes now
# reason: we work in a connected component, so all nodes are reachable
# by edges or inverses
# we check nevertheless

        qnodesO = tuple(range(len(qnodes)))
        newNodesO = tuple(sorted(newNodes))
        if newNodesO != qnodesO:
            error('''Object mismatch in plan:
In template: {}
In plan    : {}'''.format(qnodesO, newNodesO), tm=False)
            self.good = False

        qedgesO = tuple(range(len(qedges)))
        newCedgesO = tuple(sorted(newCedges))
        if newCedgesO != qedgesO:
            error('''Relation mismatch in plan:
In template: {}
In plan    : {}'''.format(qedgesO, newCedgesO), tm=False)
            self.good = False

        self.stitchPlan = (newNodes, newCedgesOrder)
        
### STITCHING: DELIVERING ###

    def _stitchResults(self):
        qnodes = self.qnodes
        qedges = self.qedges
        plan = self.stitchPlan
        relations = self.relations
        converse = self.converse
        yarns = self.yarns
        lqnodes = len(qnodes)

        planEdges = plan[1]
        if len(planEdges) == 0:
            # no edges, hence a single node (because of connectedness,
            # hence we must deliver everything of its yarn
            yarn = yarns[0]
            def deliver(remap=True):
                for n in yarn: yield (n,)
            self.results = deliver
            return
                
# The next function must be optimized, and the lookup of functions and data
# should be as direct as possible.
# Because deliver() below fetches the results, of wich there are unpredictably many.

# We are going to build-up and deliver stitches,
# which are instantiations of all the query nodes by text nodes in a specific sequence
# which is the same for all stitches.
# We can compile stitching in such a way, that the stitcher thinks it is
# instantiating q node 0, then 1, and so on.
# I.e. we are going to permute every thing that the stitching process sees,
# so that it happens in this order.

# We build up the stitch in a recursive process.
# When there is choice between a and b, we essentially say
#
# def build(stitch)
#     if there is choice
#        build(stitch+a)
#        build(stitch+b)
#   
# But we do not have to pass on the stitch as an immutable data structure.
# We can just keep it as one single mutable datastructure, provided we 
# do something between the two recursive calls above.
# Suppose stitch is an array, and in the outer build n elements are filled
# (the rest contains -1)
#
# Then we say
#     if there is choice
#        build(stitch+a)
#        for k in range(n, len(stitch)): stitch[k] = -1
#        build(stitch+b)
#
# It turns out that the data in stitch that is shared between calls
# is not modified by them.
# The only thing that happens, is that -1 values get new values.
# So coming out calls only requires us to restore -1's.
# And if the stitch is ordered in the right way, the -1's are always at the end.

# We start compiling and permuting

        edgesCompiled = []
        qPermuted = []          # row of nodes in the order as will be created during stitching
        qPermutedInv = {}       # mapping from original q node number to index in the permuted order
        for (i, (e, dir)) in enumerate(planEdges):
            (f, rela, t) = qedges[e]
            if dir == -1:
                (f, rela, t) = (t, converse[rela], f)
            r = relations[rela]['func'](qnodes[f][0], qnodes[t][0])
            nparams = len(signature(r).parameters)
            if i == 0:
                qPermuted.append(f)
                qPermutedInv[f] = len(qPermuted) - 1
            if t not in qPermuted:
                qPermuted.append(t)
                qPermutedInv[t] = len(qPermuted) - 1

            edgesCompiled.append((qPermutedInv[f], qPermutedInv[t], r, nparams))

# now permute the yarns

        yarnsPermuted = [yarns[q] for q in qPermuted] 

        def deliver(remap=True):
            stitch = [None for q in range(len(qPermuted))]
            lStitch = len(stitch)
            edgesC = edgesCompiled
            yarnsP = yarnsPermuted

            def stitchOn(e):
                if e >= len(edgesC):
                    if remap:
                        yield tuple(stitch[qPermutedInv[q]] for q in range(lStitch))
                    else:
                        yield tuple(stitch)
                    return
                (f, t, r, nparams) = edgesC[e]
                yarnT = yarnsP[t]
                if e == 0 and stitch[f] == None:
                    yarnF = yarnsP[f]
                    for sN in yarnF:
                        stitch[f] = sN
                        for s in stitchOn(e): yield s
                    return
                sN = stitch[f]
                sM = stitch[t]
                if sM != None:
                    if nparams == 1:
                        if sM in set(r(sN)): # & yarnT:
                            for s in stitchOn(e+1): yield s
                    else:
                        if r(sN, sM):
                            for s in stitchOn(e+1): yield s
                    return
                mFromN = tuple(set(r(sN)) & yarnT) if nparams == 1 else tuple(m for m in yarnT if r(sN, m))
                for m in mFromN:
                    stitch[t] = m
                    for s in stitchOn(e+1): yield s
                stitch[t] = None
            
            for s in stitchOn(0): yield s

        self.results = deliver

### TOP-LEVEL IMPLEMENTATION METHODS

    def _parse(self):
        self._syntax()
        self._semantics()

    def _prepare(self):
        if not self.good: return
        self.yarns = {}
        self.spreads = {}
        self.spreadsC = {}
        self.uptodate = {}
        self.results = None
        self._connectedness()

    def _setStrategy(self, strategy, keep=False):
        error = self.api.error
        if strategy == None:
            if keep: return
            strategy = STRATEGY[0]
        if strategy not in STRATEGY:
            error('Strategy not defined: "{}"'.format(strategy))
            error('Allowed strategies:\n{}'.format('\n'.join('    {}'.format(s) for s in STRATEGY)), tm=False)
            self.good = False
            return

        method = '_{}'.format(strategy)
        if not hasattr(self, method):
            error('Strategy is defined, but not implemented: "{}"'.format(strategy))
            self.good = False
            return
        self.strategy = getattr(self, method)

