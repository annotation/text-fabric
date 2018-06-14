# INSPECTING WITH THE SEARCH GRAPH ###


def connectedness(searchExe):
  error = searchExe.api.error
  qnodes = searchExe.qnodes
  qedges = searchExe.qedges
  msgCache = searchExe.msgCache

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
        'Either run the subqueries one by one, or connect the components by a relation',
        tm=False, cache=msgCache
    )
    searchExe.good = False
