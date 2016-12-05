import array,collections,functools
from .helpers import *

def getOtypeInfo(info, otype):
    result = (otype[-2], otype[-1], len(otype) - 2 + otype[-1])
    info('slot={}-{};node-{}'.format(*result))
    return result

def levels(info, error, otype, oslots):
    (slotType, maxSlot, maxNode) = getOtypeInfo(info, otype)
    info('max node = {}'.format(maxNode))
    otypeCount = collections.Counter()
    otypeMin = {}
    otypeMax = {}
    slotSetLengths = collections.Counter()
    info('get ranking of otypes')
    for n in range(len(oslots) - 1):
        ntp = otype[n]
        otypeCount[ntp] += 1
        slotSetLengths[ntp] += len(oslots[n])
        rn = n + maxSlot + 1
        if ntp not in otypeMin: otypeMin[ntp] = rn
        if ntp not in otypeMax or otypeMax[ntp] < rn: otypeMax[ntp] = rn
    result = tuple(sorted(
        ((ntp, slotSetLengths[ntp]/otypeCount[ntp], otypeMin[ntp], otypeMax[ntp]) for ntp in otypeCount),
        key=lambda x: -x[1],
    )+[(slotType, 1, 0, maxSlot)])
    info('results:')
    for (otp, av, omin, omax) in result:
        info('{:<15}: {:>8} {{{}-{}}}'.format(otp, round(av, 2), omin, omax), tm=False)
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

def levDown(info, error, otype, levUp, rank):
    (slotType, maxSlot, maxNode) = getOtypeInfo(info, otype)
    info('inverting embedders')
    inverse = {}
    for n in range(maxSlot+1, maxNode+1):
        for m in levUp[n]:
            inverse.setdefault(m, set()).add(n)
    info('turning embeddees into list')
    embeddees = []
    for n in range(maxSlot+1, maxNode+1):
        embeddees.append(tuple(sorted(
            inverse.get(n, []),
            key=lambda m: rank[m],
        )))
    return tuple(embeddees)

def sections(info, error, otype, oslots, otext, levUp, levels, *sFeats):
    (slotType, maxSlot, maxNode) = getOtypeInfo(info, otype)
    support = dict(((o[0], (o[2], o[3])) for o in levels))
    sTypes = itemize(otext['sectionTypes'], ',')
    sec1 = {}
    sec2 = {}
    c1 = 0
    c2 = 0
    for n2 in range(*support[sTypes[2]]):
        n0 = tuple(x for x in levUp[n2] if otype[x - maxSlot - 1] == sTypes[0])[0]
        n1 = tuple(x for x in levUp[n2] if otype[x - maxSlot - 1] == sTypes[1])[0]
        n1s = sFeats[1][n1]
        n2s = sFeats[2][n2]
        if n0 not in sec1: sec1[n0] = {}
        if n1s not in sec1[n0]:
            sec1[n0][n1s] = n1
            c1 += 1
        sec2.setdefault(n0, {}).setdefault(n1s, {})[n2s] = n2
        c2 += 1
    info('{} {}s and {} {}s indexed'.format(c1, sTypes[1], c2, sTypes[2]))
    return (sec1, sec2)
