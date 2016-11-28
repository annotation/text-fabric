import array,collections,functools

def getOtypeInfo(info, otype):
    result = (otype[-2], otype[-1], len(otype) - 2 + otype[-1])
    info('slot type = {}; max slot = {}; max node = {}'.format(*result))
    return result

def levels(info, error, otype, oslots):
    (slotType, maxSlot, maxNode) = getOtypeInfo(info, otype)
    info('max node = {}'.format(maxNode))
    otypeCount = collections.Counter()
    slotSetLengths = collections.Counter()
    info('get ranking of otypes')
    for n in range(len(oslots) - 1):
        ntp = otype[n]
        otypeCount[ntp] += 1
        slotSetLengths[ntp] += len(oslots[n])
    result = tuple(sorted(
        ((otp, slotSetLengths[otp]/otypeCount[otp]) for otp in otypeCount),
        key=lambda x: -x[1],
    )+[(slotType, 1)])
    info('results:')
    for (otp, av) in result:
        info('{:<15}: {:>4}'.format(otp, round(av, 2)), tm=False)
    return result

def order(info, error, otype, oslots, levels):
    (slotType, maxSlot, maxNode) = getOtypeInfo(info, otype)
    info('assigning otype levels to nodes')
    otypeLevels = dict(((x[0], i) for (i, x) in enumerate(levels)))
    otypeRank = lambda n: otypeLevels[slotType if n < maxSlot+1 else otype[n-maxSlot-1]]
    def before(na,nb):
        if na > maxSlot:
            a = na - maxSlot - 1
            sa = set(oslots[a])
        else:
            a = na
            sa = {a}
        if nb > maxSlot:
            b = nb - maxSlot - 1
            sb = set(oslots[b])
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
    (slotType, maxSlot, maxNode) = getOtypeInfo(info, otype)
    info('ranking nodes')
    nodesRank = dict(((n,i) for (i,n) in enumerate(order)))
    return array.array('I', (nodesRank[n] for n in range(maxNode+1)))

def levUp(info, error, otype, oslots, rank):
    (slotType, maxSlot, maxNode) = getOtypeInfo(info, otype)
    info('making inverse of edge feature oslots')
    oslotsInv = {}
    for (n, mapList) in enumerate(oslots[0:-1]):
        for m in mapList:
            oslotsInv.setdefault(m, set()).add(n+maxSlot+1)
    info('listing embedders of all nodes')
    embedders = []
    for n in range(maxSlot+1):
        contentEmbedders = oslotsInv[n]
        embedders.append(tuple(sorted(
            [m for m in contentEmbedders if rank[m] < rank[n]],
            key=lambda m: -rank[m],
        )))
    for n in range(maxSlot+1, maxNode+1):
        mList = oslots[n-maxSlot-1]
        if len(mList) == 0:
            embedders.append(tuple())
        else:
            contentEmbedders = functools.reduce(
                lambda x,y: x & oslotsInv[y],
                mList[1:], oslotsInv[mList[0]],
            )
            embedders.append(tuple(sorted(
                [m for m in contentEmbedders if rank[m] < rank[n]],
                key=lambda m: -rank[m],
            )))
    return tuple(embedders)

def levDown(info, error, otype, embedders, rank):
    (slotType, maxSlot, maxNode) = getOtypeInfo(info, otype)
    info('inverting embedders')
    inverse = {}
    for n in range(maxSlot+1, maxNode+1):
        for m in embedders[n]:
            inverse.setdefault(m, set()).add(n)
    info('turning embeddees into list')
    embeddees = []
    for n in range(maxSlot+1, maxNode+1):
        embeddees.append(tuple(sorted(
            inverse.get(n, []),
            key=lambda m: rank[m],
        )))
    return tuple(embeddees)

