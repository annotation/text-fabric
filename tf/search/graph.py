# INSPECTING WITH THE SEARCH GRAPH ###


HALFBOUNDED = {
    '<': 1,
    '>': -1,
    '<<': 1,
    '>>': -1,
}
BOUNDED = {
    '=',
    '==',
    '&&',
    '[[',
    ']]',
    '=:',
    ':=',
    '::',
    ':>',
    '<:',
    '=k:',
    ':k=',
    ':k:',
    ':k>',
    '<k:',
}

OFFSETS = {
    '=': (0, 0, 0, 0),
    '==': (0, 0, None, None),
    '&&': (0, 0, None, None),
}


def connectedness(searchExe):
  error = searchExe.api.error
  qnodes = searchExe.qnodes
  qedges = searchExe.qedges
  msgCache = searchExe.msgCache

  componentIndex = dict(((q, {q}) for q in range(len(qnodes))))
  for (f, rela, t) in qedges:
    if f != t:
      componentIndex[f] |= componentIndex[t]
      componentIndex[t] = componentIndex[f]
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
  searchExe.components = []
  for c in components:
    searchExe.components.append([sorted(c), componentEdges.get(c, [])])
  lComps = len(searchExe.components)
  if lComps == 0:
    error('Search without instructions. Tell me what to look for.', cache=msgCache)
    searchExe.good = False
  elif lComps > 1:
    error(f'More than one connected components ({len(searchExe.components)}):', cache=msgCache)
    error(
        'Either run the subqueries one by one, or connect the components by a relation', tm=False,
        cache=msgCache
    )
    searchExe.good = False


def boundedness(searchExe):
  info = searchExe.api.info
  error = searchExe.api.error
  qnodes = searchExe.qnodes
  qedges = searchExe.qedges
  relations = searchExe.relations
  msgCache = searchExe.msgCache

  componentIndex = dict(((q, {q}) for q in range(len(qnodes))))
  for (f, rela, t) in qedges:
    acro = relations[rela]['acro']
    relInfo = relations[rela]
    acro = relInfo.get('name', relInfo['acro'])
    if f != t:
      if acro in BOUNDED:
        componentIndex[f] |= componentIndex[t]
        componentIndex[t] = componentIndex[f]
        for u in componentIndex[f] - {f}:
          componentIndex[u] = componentIndex[f]
  components = sorted(set(frozenset(c) for c in componentIndex.values()))

  componentIndex = {}
  for c in components:
    for q in c:
      componentIndex[q] = c

  intraEdges = {}
  interEdges = {}
  for (e, (f, rela, t)) in enumerate(qedges):
    relInfo = relations[rela]
    acro = relInfo.get('name', relInfo['acro'])
    cF = componentIndex[f]
    cT = componentIndex[t]
    if acro in BOUNDED:
      if cF == cT:
        intraEdges.setdefault(cF, []).append(e)
      else:
        error(f'bounded inter edge! {cF} {acro} {cT}', cache=msgCache)
    elif acro in HALFBOUNDED:
      interEdges.setdefault((cF, cT), []).append((e, HALFBOUNDED[acro]))

  bounded = []
  complexity = 1
  yarnSize = {}
  for c in components:
    size = sum(len(y) for (n, y) in searchExe.yarns.items() if n in c)
    yarnSize[c] = size
    bounded.append(c)
    complexity *= size

  upperBound = {}
  lowerBound = {}
  for ((cF, cT), es) in interEdges.items():
    for (e, dir) in es:
      (cA, cB) = (cF, cT) if dir == 1 else (cT, cF)
      upperBound.setdefault(cA, {}).setdefault(cB, []).append(e)
      lowerBound.setdefault(cB, {}).setdefault(cA, []).append(e)

  print(upperBound)
  print(lowerBound)

  searchExe.yarnSize = yarnSize
  searchExe.complexity = complexity
  searchExe.bounded = bounded
  searchExe.interEdges = interEdges
  searchExe.intraEdges = intraEdges

  getOffsets(searchExe)

  info(f'complexity: {complexity:.1e}', cache=msgCache)
  displayChunks(searchExe)


def getOffsets(searchExe):
  qedges = searchExe.qedges
  intraEdges = searchExe.intraEdges
  relations = searchExe.relations

  for (c, es) in intraEdges.items():
    for e in es:
      (f, rela, t) = qedges[e]
      relInfo = relations[rela]
      acro = relInfo.get('name', relInfo['acro'])
      param = relInfo.get('param', None)
      print(acro, param)


def displayPlan(searchExe, details=False):
  if not searchExe.good:
    return
  api = searchExe.api
  setSilent = api.setSilent
  isSilent = api.isSilent
  info = api.info
  wasSilent = isSilent()
  setSilent(False)
  msgCache = searchExe.msgCache
  nodeLine = searchExe.nodeLine
  qedges = searchExe.qedges
  (qs, es) = searchExe.stitchPlan
  offset = searchExe.offset
  if details:
    info(f'Search with {len(qs)} objects and {len(es)} relations', tm=False, cache=msgCache)
    info('Results are instantiations of the following objects:', tm=False)
    for q in qs:
      displayNode(searchExe, q)
    if len(es) != 0:
      info('Performance parameters:', tm=False, cache=msgCache)
      for (k, v) in searchExe.perfParams.items():
        info(f'\t{k:<20} = {v:>7}', tm=False, cache=msgCache)
      info('Instantiations are computed along the following relations:', tm=False, cache=msgCache)
      (firstE, firstDir) = es[0]
      (f, rela, t) = qedges[firstE]
      if firstDir == -1:
        (f, t) = (t, f)
      displayNode(searchExe, f, pos2=True)
      for e in es:
        displayEdge(searchExe, *e)
  info('The results are connected to the original search template as follows:', cache=msgCache)

  resultNode = {}
  for q in qs:
    resultNode[nodeLine[q]] = q
  for (i, line) in enumerate(searchExe.searchLines):
    rNode = resultNode.get(i, '')
    prefix = '' if rNode == '' else 'R'
    info(f'{i + offset:>2} {prefix:<1}{rNode:<2} {line}', tm=False, cache=msgCache)

  setSilent(wasSilent)


def displayChunks(searchExe):
  if not searchExe.good:
    return
  api = searchExe.api
  setSilent = api.setSilent
  isSilent = api.isSilent
  info = api.info
  wasSilent = isSilent()
  setSilent(False)
  msgCache = searchExe.msgCache
  chunks = searchExe.bounded
  intraEdges = searchExe.intraEdges
  interEdges = searchExe.interEdges
  yarnSize = searchExe.yarnSize
  info(f'{len(chunks)} internally bounded chunks', tm=False, cache=msgCache)
  for c in chunks:
    size = yarnSize[c]
    cRep = ','.join(str(x) for x in sorted(c))
    info(f'Chunk {cRep} with {size} nodes in its yarns')
    for e in intraEdges.get(c, []):
      displayEdge(searchExe, e, 1)
  info(f'Edges between chunks:')
  for ((cF, cT), es) in (interEdges.items()):
    cFRep = ','.join(sorted(str(x) for x in cF))
    cTRep = ','.join(sorted(str(x) for x in cT))
    info(f'  from {cFRep} to {cTRep}')
    for e in es:
      displayEdge(searchExe, *e)

  setSilent(wasSilent)


def displayNode(searchExe, q, pos2=False):
  info = searchExe.api.info
  msgCache = searchExe.msgCache
  qnodes = searchExe.qnodes
  yarns = searchExe.yarns
  space = ' ' * 19
  nodeInfo = 'node {} {:>2}-{:<13} ({:>6}   choices)'.format(
      space,
      q,
      qnodes[q][0],
      len(yarns[q]),
  ) if pos2 else 'node {:>2}-{:<13} {} ({:>6}   choices)'.format(
      q,
      qnodes[q][0],
      space,
      len(yarns[q]),
  )
  info(nodeInfo, tm=False, cache=msgCache)


def displayEdge(searchExe, e, dir):
  info = searchExe.api.info
  msgCache = searchExe.msgCache
  qnodes = searchExe.qnodes
  qedges = searchExe.qedges
  converse = searchExe.converse
  relations = searchExe.relations
  spreads = searchExe.spreads
  spreadsC = searchExe.spreadsC
  thinned = getattr(searchExe, 'thinned', set())
  (f, rela, t) = qedges[e]
  if dir == -1:
    (f, rela, t) = (t, converse[rela], f)
  info(
      'edge {:>2}-{:<13} {:^2} {:>2}-{:<13} ({:8.1f} choices{})'.format(
          f,
          qnodes[f][0],
          relations[rela]['acro'],
          t,
          qnodes[t][0],
          spreads.get(e, -1) if dir == 1 else spreadsC.get(e, -1),
          ' (thinned)' if e in thinned else '',
      ),
      tm=False, cache=msgCache
  )
