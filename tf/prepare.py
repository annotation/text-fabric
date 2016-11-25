import array,collections,functools

def getOtypeInfo(info, otype):
    info('get monad type, max monad, max node')
    result = (otype[-2], otype[-1], len(otype) - 2 + otype[-1])
    info('monad type = {}; max monad = {}; max node = {}'.format(*result))
    return result

def levels(info, error, otype, monads):
    (monadType, maxMonad, maxNode) = getOtypeInfo(info, otype)
    info('max node = {}'.format(maxNode))
    otypeCount = collections.Counter()
    monadSetLengths = collections.Counter()
    info('get ranking of otypes')
    for n in range(len(monads) - 1):
        ntp = otype[n]
        otypeCount[ntp] += 1
        monadSetLengths[ntp] += len(monads[n])
    result = tuple(sorted(
        ((otp, monadSetLengths[otp]/otypeCount[otp]) for otp in otypeCount),
        key=lambda x: -x[1],
    )+[(monadType, 1)])
    info('results:')
    for (otp, av) in result:
        info('{:<15}: {:>4}'.format(otp, round(av, 2)), tm=False)
    return result

def order(info, error, otype, monads, levels):
    (monadType, maxMonad, maxNode) = getOtypeInfo(info, otype)
    info('assigning otype levels to nodes')
    otypeLevels = dict(((x[0], i) for (i, x) in enumerate(levels)))
    otypeRank = lambda n: otypeLevels[monadType if n < maxMonad+1 else otype[n-maxMonad-1]]
    def before(na,nb):
        if na > maxMonad:
            a = na - maxMonad - 1
            sa = set(monads[a])
        else:
            a = na
            sa = {a}
        if nb > maxMonad:
            b = nb - maxMonad - 1
            sb = set(monads[b])
        else:
            b = nb
            sb = {b}
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
    (monadType, maxMonad, maxNode) = getOtypeInfo(info, otype)
    info('ranking nodes')
    nodesRank = dict(((n,i) for (i,n) in enumerate(order)))
    return array.array('I', (nodesRank[n] for n in range(maxNode+1)))

def levUp(info, error, otype, monads, rank):
    (monadType, maxMonad, maxNode) = getOtypeInfo(info, otype)
    info('making inverse of edge feature monads')
    monadsInv = {}
    for (n, mapList) in enumerate(monads[0:-1]):
        for m in mapList:
            monadsInv.setdefault(m, set()).add(n+maxMonad+1)
    info('listing embedders of all nodes')
    embedders = []
    for n in range(maxMonad+1):
        contentEmbedders = monadsInv[n]
        embedders.append(tuple(sorted([m for m in contentEmbedders if rank[m] < rank[n]], key=lambda m: -rank[m])))
    for n in range(maxMonad+1, maxNode+1):
        mList = monads[n-maxMonad-1]
        if len(mList) == 0:
            embedders.append(tuple())
        else:
            contentEmbedders = functools.reduce(lambda x,y: x & monadsInv[y], mList[1:], monadsInv[mList[0]])
            embedders.append(tuple(sorted([m for m in contentEmbedders if rank[m] < rank[n]], key=lambda m: -rank[m])))
    return tuple(embedders)

def levDown(info, error, otype, embedders, rank):
    (monadType, maxMonad, maxNode) = getOtypeInfo(info, otype)
    info('inverting embedders')
    inverse = {}
    for n in range(maxMonad+1, maxNode+1):
        for m in embedders[n]:
            inverse.setdefault(m, set()).add(n)
    info('turning embeddees into list')
    embeddees = []
    for n in range(maxMonad+1, maxNode+1):
        embeddees.append(tuple(sorted(inverse.get(n, []), key=lambda m: rank[m])))
    return embeddees

