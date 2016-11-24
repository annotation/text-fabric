import array,collections,functools

def getMaxNode(otype): return max(otype.keys())
def getMonadType(otype): return otype[0]

def levels(otype, monads):
    monadType = getMonadType(otype)
    maxNode = getMaxNode(otype)
    otypeCount = collections.Counter()
    monadSetLengths = collections.Counter()
    for n in otype:
        if maxNode == None or n > maxNode: maxNode = n
        ntp = otype[n]
        otypeCount[ntp] += 1
        monadSetLengths[ntp] += len(monads[n]) if ntp != monadType else 1 
    return sorted(
        ((otype, monadSetLengths[otype]/otypeCount[otype]) for otype in otypeCount),
        key=lambda x: -x[1],
    )

def order(otype, monads, levels):
    maxNode = getMaxNode(otype)
    otypeLevels = dict(((x[0], i) for (i, x) in enumerate(levels)))
    otypeRank = lambda n: otypeLevels[otype[n]]
    def before(a,b):
        sa = monads.get(a, {a})
        sb = monads.get(b, {b})
        oa = otypeRank(a)
        ob = otypeRank(b)
        if sa == sb: return 0 if oa == ob else -1 if oa < ob else 1
        if sa < sb: return 1
        if sa > sb: return -1
        am = min(sa - sb)
        bm = min(sb - sa)
        return -1 if am < bm else 1 if bm < am else None

    canonKey = functools.cmp_to_key(before)
    nodes = sorted(range(maxNode+1), key=canonKey)
    return array.array('I', nodes)

def rank(otype, order):
    maxNode = getMaxNode(otype)
    nodesRank = dict(((n,i) for (i,n) in enumerate(order)))
    return array.array('I', (nodesRank[n] for n in range(maxNode+1)))

