from .search import runSearch


def getTupleHighlights(api, tuples, highlights, colorMap, condenseType, multiple=False):
  F = api.F
  otypeRank = api.otypeRank

  condenseRank = otypeRank[condenseType]
  if type(highlights) is set:
    highlights = {m: '' for m in highlights}
  newHighlights = {}
  if highlights:
    newHighlights.update(highlights)

  if not multiple:
    tuples = (tuples, )
  for tup in tuples:
    for (i, n) in enumerate(tup):
      nType = F.otype.v(n)
      if otypeRank[nType] < condenseRank:
        thisHighlight = None
        if highlights:
          thisHighlight = highlights.get(n, None)
        elif colorMap is not None:
          thisHighlight = colorMap.get(i + 1, None)
        else:
          thisHighlight = ''
        if thisHighlight is not None:
          newHighlights[n] = thisHighlight
  return newHighlights


def getPassageHighlights(app, node, query, cache, cacheSlots):
  if not query:
    return (set(), set(), set(), set())
  cacheSlotsKey = (query, node)
  if cacheSlotsKey in cacheSlots:
    return cacheSlots[cacheSlotsKey]

  hlNodes = _getHlNodes(app, node, query, cache)
  cacheSlots[cacheSlotsKey] = hlNodes
  return hlNodes


def _getHlNodes(app, node, query, cache):
  (queryResults, messages, features) = runSearch(app, query, cache)
  if messages:
    return (set(), set(), set(), set())

  api = app.api
  E = api.E
  F = api.F
  maxSlot = F.otype.maxSlot
  eoslots = E.oslots.data

  nodeSlots = eoslots[node - maxSlot - 1]
  first = nodeSlots[0]
  last = nodeSlots[-1]

  (sec2s, nodes, plainSlots, prettySlots) = _nodesFromTuples(app, first, last, queryResults)
  return (sec2s, nodes, plainSlots, prettySlots)


def _nodesFromTuples(app, first, last, results):
  api = app.api
  E = api.E
  F = api.F
  T = api.T
  L = api.L
  maxSlot = F.otype.maxSlot
  slotType = F.otype.slotType
  eoslots = E.oslots.data
  sectionTypes = T.sectionTypes
  sec2Type = sectionTypes[2]

  sec2s = set()
  nodes = set()
  plainSlots = set()
  prettySlots = set()

  for tup in results:
    for n in tup:
      nType = F.otype.v(n)

      if nType == slotType:
        if first <= n <= last:
          plainSlots.add(n)
          prettySlots.add(n)
      elif nType == sec2Type:
        sec2s.add(n)
      elif nType != sectionTypes[0] and nType != sectionTypes[1]:
        mySlots = eoslots[n - maxSlot - 1]
        myFirst = mySlots[0]
        myLast = mySlots[-1]
        if first <= myFirst <= last or first <= myLast <= last:
          nodes.add(n)
          for s in mySlots:
            if first <= s <= last:
              plainSlots.add(s)
  for s in plainSlots:
    sec2s.add(L.u(s, otype=sec2Type)[0])

  return (sec2s, nodes, plainSlots, prettySlots)
