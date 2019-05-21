from array import array
import collections
import functools
from .helpers import itemize


def levels(info, error, otype, oslots, otext):
  (otype, maxSlot, maxNode, slotType) = otype
  oslots = oslots[0]
  levelOrder = otext.get('levels', None)
  if levelOrder is not None:
    levelRank = {level: i for (i, level) in enumerate(levelOrder.split(','))}
  otypeCount = collections.Counter()
  otypeMin = {}
  otypeMax = {}
  slotSetLengths = collections.Counter()
  info('get ranking of otypes')
  for k in range(len(oslots)):
    ntp = otype[k]
    otypeCount[ntp] += 1
    slotSetLengths[ntp] += len(oslots[k])
    tfn = k + maxSlot + 1
    if ntp not in otypeMin:
      otypeMin[ntp] = tfn
    if ntp not in otypeMax or otypeMax[ntp] < tfn:
      otypeMax[ntp] = tfn
  sortKey = ((lambda x: -x[1]) if levelOrder is None else (lambda x: levelRank[x[0]]))
  result = tuple(
      sorted(
          ((ntp, slotSetLengths[ntp] / otypeCount[ntp], otypeMin[ntp], otypeMax[ntp])
           for ntp in otypeCount),
          key=sortKey,
      ) + [(slotType, 1, 1, maxSlot)]
  )
  info('results:')
  for (otp, av, omin, omax) in result:
    info(f'{otp:<15}: {round(av, 2):>8} {{{omin}-{omax}}}', tm=False)
  return result


def order(info, error, otype, oslots, levels):
  (otype, maxSlot, maxNode, slotType) = otype
  oslots = oslots[0]
  info('assigning otype levels to nodes')
  otypeLevels = dict(((x[0], i) for (i, x) in enumerate(levels)))

  def otypeRank(n):
    return otypeLevels[slotType if n < maxSlot + 1 else otype[n - maxSlot - 1]]

  def before(na, nb):
    if na < maxSlot + 1:
      a = na
      sa = {a}
    else:
      a = na - maxSlot
      sa = set(oslots[a - 1])
    if nb < maxSlot + 1:
      b = nb
      sb = {b}
    else:
      b = nb - maxSlot
      sb = set(oslots[b - 1])
    oa = otypeRank(na)
    ob = otypeRank(nb)
    if sa == sb:
      return 0 if oa == ob else -1 if oa < ob else 1
    if sa > sb:
      return -1
    if sa < sb:
      return 1
    am = min(sa - sb)
    bm = min(sb - sa)
    return -1 if am < bm else 1 if bm < am else None

  canonKey = functools.cmp_to_key(before)
  info('sorting nodes')
  nodes = sorted(range(1, maxNode + 1), key=canonKey)
  return array('I', nodes)


def rank(info, error, otype, order):
  (otype, maxSlot, maxNode, slotType) = otype
  info('ranking nodes')
  nodesRank = dict(((n, i) for (i, n) in enumerate(order)))
  return array('I', (nodesRank[n] for n in range(1, maxNode + 1)))


def levUp(info, error, otype, oslots, rank):
  (otype, maxSlot, maxNode, slotType) = otype
  oslots = oslots[0]
  info('making inverse of edge feature oslots')
  oslotsInv = {}
  for (k, mList) in enumerate(oslots):
    for m in mList:
      oslotsInv.setdefault(m, set()).add(k + 1 + maxSlot)
  info('listing embedders of all nodes')
  embedders = []
  for n in range(1, maxSlot + 1):
    contentEmbedders = oslotsInv[n]
    embedders.append(
        tuple(
            sorted(
                [m for m in contentEmbedders if m != n],
                key=lambda k: -rank[k - 1],
            )
        )
    )
  for n in range(maxSlot + 1, maxNode + 1):
    mList = oslots[n - maxSlot - 1]
    if len(mList) == 0:
      embedders.append(tuple())
    else:
      contentEmbedders = functools.reduce(
          lambda x, y: x & oslotsInv[y],
          mList[1:],
          oslotsInv[mList[0]],
      )
      embedders.append(
          tuple(
              sorted(
                  [m for m in contentEmbedders if m != n],
                  key=lambda k: -rank[k - 1],
              )
          )
      )
  # reuse embedder tuples, because lots of nodes share embedders
  seen = {}
  embeddersx = []
  for t in embedders:
    if t not in seen:
      seen[t] = array('I', t)
    embeddersx.append(seen[t])
  return tuple(embeddersx)


def levDown(info, error, otype, levUp, rank):
  (otype, maxSlot, maxNode, slotType) = otype
  info('inverting embedders')
  inverse = {}
  for n in range(maxSlot + 1, maxNode + 1):
    for m in levUp[n - 1]:
      inverse.setdefault(m, set()).add(n)
  info('turning embeddees into list')
  embeddees = []
  for n in range(maxSlot + 1, maxNode + 1):
    embeddees.append(array('I', sorted(
        inverse.get(n, []),
        key=lambda m: rank[m - 1],
    )))
  return tuple(embeddees)


def boundary(info, error, otype, oslots, rank):
  (otype, maxSlot, maxNode, slotType) = otype
  oslots = oslots[0]
  firstSlotsD = {}
  lastSlotsD = {}
  for (k, mList) in enumerate(oslots):
    firstSlotsD.setdefault(mList[0], []).append(k + 1 + maxSlot)
    lastSlotsD.setdefault(mList[-1], []).append(k + 1 + maxSlot)
  firstSlots = []
  lastSlots = []
  for n in range(1, maxSlot + 1):
    firstSlots.append(array('I', sorted(firstSlotsD.get(n, []), key=lambda k: -rank[k - 1])))
    lastSlots.append(array('I', sorted(lastSlotsD.get(n, []), key=lambda k: rank[k - 1])))
  return (tuple(firstSlots), tuple(lastSlots))


def sections(info, error, otype, oslots, otext, levUp, levels, *sFeats):
  (otype, maxSlot, maxNode, slotType) = otype
  oslots = oslots[0]
  support = dict(((o[0], (o[2], o[3])) for o in levels))
  sTypes = itemize(otext['sectionTypes'], ',')
  sec1 = {}
  sec2 = {}
  nestingProblems = collections.Counter()

  if len(sTypes) < 2:
    pass

  elif len(sTypes) < 3:
    c1 = 0
    support1 = support[sTypes[1]]
    for n1 in range(support1[0], support1[1] + 1):
      n0s = tuple(x for x in levUp[n1 - 1] if otype[x - maxSlot - 1] == sTypes[0])
      if not n0s:
        nestingProblems[f'section {sTypes[1]} without containing {sTypes[0]}'] += 1
        continue
      n0 = n0s[0]
      n1s = sFeats[1][n1]
      if n0 not in sec1:
        sec1[n0] = {}
      if n1s not in sec1[n0]:
        sec1[n0][n1s] = n1
        c1 += 1
    info(f'{c1} {sTypes[1]}s indexed')

  else:
    c1 = 0
    c2 = 0
    support2 = support[sTypes[2]]
    for n2 in range(support2[0], support2[1] + 1):
      n0s = tuple(x for x in levUp[n2 - 1] if otype[x - maxSlot - 1] == sTypes[0])
      if not n0s:
        nestingProblems[f'section {sTypes[2]} without containing {sTypes[0]}'] += 1
        continue
      n0 = n0s[0]
      n1s = tuple(x for x in levUp[n2 - 1] if otype[x - maxSlot - 1] == sTypes[1])
      if not n1s:
        nestingProblems[f'section {sTypes[2]} without containing {sTypes[1]}'] += 1
        continue
      n1 = n1s[0]
      n1s = sFeats[1][n1]
      n2s = sFeats[2][n2]
      if n0 not in sec1:
        sec1[n0] = {}
      if n1s not in sec1[n0]:
        sec1[n0][n1s] = n1
        c1 += 1
      sec2.setdefault(n0, {}).setdefault(n1s, {})[n2s] = n2
      c2 += 1
    info(f'{c1} {sTypes[1]}s and {c2} {sTypes[2]}s indexed')

  if nestingProblems:
    for (msg, amount) in sorted(nestingProblems.items()):
      error(f'WARNING: {amount:>4} x {msg}')

  return (sec1, sec2)


def structure(info, error, otype, oslots, otext, rank, levUp, *sFeats):
  (otype, maxSlot, maxNode, slotType) = otype
  oslots = oslots[0]
  sTypeList = itemize(otext['structureTypes'], ',')
  nsTypes = len(sTypeList)
  nsFeats = len(sFeats)

  if nsTypes != nsFeats:
    error(f'WARNING: {nsTypes} structure levels but {nsFeats} corresponding features')
    return ({}, {})

  sTypes = set(sTypeList)
  if len(sTypes) != nsTypes:
    error(f'WARNING: duplicate structure levels')
    return ({}, {})

  higherTypes = collections.defaultdict(set)
  for (i, highType) in enumerate(sTypeList):
    for lowType in sTypeList[i:]:
      higherTypes[lowType].add(highType)

  featFromType = {sTypeList[i]: sFeats[i] for i in range(nsTypes)}

  multiple = collections.defaultdict(list)
  headingFromNode = {}
  nodeFromHeading = {}

  for n in range(maxSlot + 1, maxNode + 1):
    nType = otype[n - maxSlot - 1]
    if nType not in sTypes:
      continue
    ups = (u for u in levUp[n - 1] if otype[u - maxSlot - 1] in higherTypes[nType])
    sKey = tuple(reversed(tuple(
        (
            otype[x - maxSlot - 1],
            featFromType[otype[x - maxSlot - 1]].get(x, None),
        )
        for x in (n, *ups)
    )))

    if sKey in nodeFromHeading:
      if sKey not in multiple:
        multiple[sKey].append(nodeFromHeading[sKey])
      multiple[sKey].append(n)
    nodeFromHeading[sKey] = n
    headingFromNode[n] = sKey
  multiple = {
      sKey: tuple(sorted(
          ns,
          key=lambda n: rank[n - 1],
      ))
      for (sKey, ns) in multiple.items()
  }

  top = tuple(sorted(
      (n for (n, h) in headingFromNode.items() if len(h) == 1),
      key=lambda n: rank[n - 1],
  ))

  up = {}
  for (n, heading) in headingFromNode.items():
    lHeading = len(heading)
    if lHeading == 1:
      continue
    upNode = None
    for i in range(lHeading - 1, 0, -1):
      upHeading = heading[0:i]
      upNode = nodeFromHeading.get(upHeading, None)
      if upNode is not None:
        up[n] = upNode
        break

  down = {}
  for (n, heading) in headingFromNode.items():
    if len(heading) == 1:
      continue
    down.setdefault(up[n], []).append(n)

  down = {
      n: tuple(sorted(ms, key=lambda m: rank[m - 1]))
      for (n, ms) in down.items()
  }

  return (headingFromNode, nodeFromHeading, multiple, top, up, down)
