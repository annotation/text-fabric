import array,collections,functools

def getMaxNode(otype): return max(otype.keys())
def getMonadType(otype): return otype[0]

def levels(info, error, otype, monads):
    info('get monad type')
    monadType = getMonadType(otype)
    info('monad type = {}'.format(monadType))
    info('get max node')
    maxNode = getMaxNode(otype)
    info('max node = {}'.format(maxNode))
    otypeCount = collections.Counter()
    monadSetLengths = collections.Counter()
    info('get ranking of otypes')
    for n in otype:
        if maxNode == None or n > maxNode: maxNode = n
        ntp = otype[n]
        otypeCount[ntp] += 1
        monadSetLengths[ntp] += len(monads[n]) if ntp != monadType else 1 
    result = sorted(
        ((otp, monadSetLengths[otp]/otypeCount[otp]) for otp in otypeCount),
        key=lambda x: -x[1],
    )
    info('results:')
    for (otp, av) in result:
        info('{:<15}: {:>4}'.format(otp, round(av, 2)), tm=False)
    return result

def order(info, error, otype, monads, levels):
    info('get max node')
    maxNode = getMaxNode(otype)
    info('max node = {}'.format(maxNode))
    info('assigning otype levels to nodes')
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
    info('sorting nodes')
    nodes = sorted(range(maxNode+1), key=canonKey)
    return array.array('I', nodes)

def rank(info, error, otype, order):
    info('get max node')
    maxNode = getMaxNode(otype)
    info('max node = {}'.format(maxNode))
    info('ranking nodes')
    nodesRank = dict(((n,i) for (i,n) in enumerate(order)))
    return array.array('I', (nodesRank[n] for n in range(maxNode+1)))

def levUp(info, error, otype, monads, rank):
    info('get monad type')
    monadType = getMonadType(otype)
    info('monad type = {}'.format(monadType))
    info('get max node')
    maxNode = getMaxNode(otype)
    info('max node = {}'.format(maxNode))
    info('making inverse of edge feature monads')
    monadsInv = _makeInverse(monads)
    info('listing embedders of all nodes')
    embedders = {}
    for n in range(maxNode+1):
        if otype[n] == monadType:
            contentEmbedders = monadsInv[n]
        else:
            mList = list(monads.get(n, set()))
            if len(mList) == 0:
                continue
            contentEmbedders = functools.reduce(lambda x,y: x & monadsInv[y], mList[1:], monadsInv[mList[0]])
        embedders[n] = sorted([m for m in contentEmbedders if rank[m] < rank[n]], key=lambda m: -rank[m])
    return embedders

def levDown(info, error, embedders, rank):
    info('listing embeddees of all nodes')
    embeddees = _makeInverse(embedders)
    info('sorting embeddees')
    return _sortedList(embeddees, rank)

def _makeInverse(mapping):
    inverse = {}
    for (n, mapSet) in mapping.items():
        for m in mapSet:
            inverse.setdefault(m, set()).add(n)
    return inverse

def _sortedList(mapping, rank):
    result = {}
    for (n, mapSet) in mapping.items():
        result[n] = sorted(mapSet, key=lambda m: rank[m])
    return result

