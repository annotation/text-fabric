import types
from inspect import signature
from .spin import estimateSpreads

# STITCHING: STRATEGIES ###

STRATEGY = '''
    small_choice_first
    spread_1_first
    big_choice_first
'''.strip().split()


def setStrategy(searchExe, strategy, keep=False):
  error = searchExe.api.error
  msgCache = searchExe.msgCache
  if strategy is None:
    if keep:
      return
    strategy = STRATEGY[0]
  if strategy not in STRATEGY:
    error(f'Strategy not defined: "{strategy}"', cache=msgCache)
    error(
        'Allowed strategies:\n{}'.format('\n'.join(f'    {s}' for s in STRATEGY)),
        tm=False,
        cache=msgCache,
    )
    searchExe.good = False

  func = globals().get(f'_{strategy}', None)
  if not func:
    error(f'Strategy is defined, but not implemented: "{strategy}"', cache=msgCache)
    searchExe.good = False
  searchExe.strategy = types.MethodType(func, searchExe)


def _spread_1_first(searchExe):
  qedges = searchExe.qedges
  qnodes = searchExe.qnodes

  s1Edges = []
  for (e, (f, rela, t)) in enumerate(qedges):
    if searchExe.spreads[e] <= 1:
      s1Edges.append((e, 1))
    if searchExe.spreadsC[e] <= 1:
      s1Edges.append((e, -1))
# s1Edges contain all edges with spread <= 1, or whose converse has spread <= 1
# now we want to build the largest graph
# with the original nodes and these edges,
# such that you can walk from a starting point
# over directed s1 edges to every other point
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
        if dir == -1:
          (t, f) = (f, t)
        if f in cnodes:
          if t not in cnodes:
            cnodes.add(t)
            added = True
          if (e, dir) not in cedges:
            cedges.add((e, dir))
            cedgesOrder.append((e, dir))
            added = True
      if not added:
        break
    candidates.append((cnodes, cedgesOrder))


# pick the biggest graph (nodes and edges count for 1)
  startS1 = sorted(candidates, key=lambda x: len(x[0]) + len(x[1]))[-1]

  newNodes = startS1[0]
  newEdges = startS1[1]
  doneEdges = set(e[0] for e in newEdges)

  # we add all edges that are not yet in our startS1.
  # we add them two-fold: also with converse,
  # and we sort the result by spread
  # then we start a big loop:
  # in every iteration, we take the edge with smallest spread
  # that can be connected
  # to the graph under construction
  # then we start a new iteration, because the graph has grown,
  # and and new edges might
  # have become connectable by that

  # in order to fail early, we can also add edges
  # if their from-nodes and to-nodes both have been
  # targeted.
  # That means: an earlier edge went to f,
  # an other earlier edge went to t, and if we
  # have an edge from f to t, we'd better add it now,
  # since it is an extra constraint
  # and by testing it here we can avoid a lot of work.

  remainingEdges = set()
  for e in range(len(qedges)):
    if e not in doneEdges:
      remainingEdges.add((e, 1))
      remainingEdges.add((e, -1))
  remainingEdgesO = sorted(
      remainingEdges,
      key=lambda e: (searchExe.spreads[e[0]] if e[1] == 1 else searchExe.spreadsC[e[0]]),
  )

  while 1:
    added = False
    for (e, dir) in remainingEdgesO:
      if e in doneEdges:
        continue
      (f, rela, t) = qedges[e]
      if dir == -1:
        (f, t) = (t, f)
      if f in newNodes and t in newNodes:
        newEdges.append((e, dir))
        doneEdges.add(e)
        added = True
    for (e, dir) in remainingEdgesO:
      if e in doneEdges:
        continue
      (f, rela, t) = qedges[e]
      if dir == -1:
        (f, t) = (t, f)
      if f in newNodes:
        newNodes.add(t)
        newEdges.append((e, dir))
        doneEdges.add(e)
        added = True
        break
    if not added:
      break

  results = {}
  results['newNodes'] = newNodes
  results['newEdges'] = newEdges
  return results


def _small_choice_first(searchExe):

  # This strategy does not try to make a big subgraph of
  # edges with spread 1.
  # The problem is that before the edges work,
  # the initial yarn may have an enormous spread.
  # Here we try out the strategy of postponing
  # broad choices as long as possible.
  # The inituition is that while we are making smaller choices,
  # constraints are encountered,
  # severely limiting the broader choices later on.

  # So, we pick the yarn with the least amount of nodes
  # as our starting point.
  # The corresponding node is our singleton start set.
  # In every iteration we do the following:
  # - we pick all edges of which from- and to-nodes
  #   are already in the node set
  # - we pick the edge with least spread
  #   that has a starting point in the set
  # Until nothing changes anymore

  qedges = searchExe.qedges
  qnodes = searchExe.qnodes

  newNodes = {sorted(range(len(qnodes)), key=lambda x: len(searchExe.yarns[x]))[0]}
  newEdges = []
  doneEdges = set()

  remainingEdges = set()
  for e in range(len(qedges)):
    remainingEdges.add((e, 1))
    remainingEdges.add((e, -1))
  remainingEdgesO = sorted(
      remainingEdges,
      key=lambda e: (searchExe.spreads[e[0]] if e[1] == 1 else searchExe.spreadsC[e[0]]),
  )

  while 1:
    added = False
    for (e, dir) in remainingEdgesO:
      if e in doneEdges:
        continue
      (f, rela, t) = qedges[e]
      if dir == -1:
        (f, t) = (t, f)
      if f in newNodes and t in newNodes:
        newEdges.append((e, dir))
        doneEdges.add(e)
        added = True
    for (e, dir) in remainingEdgesO:
      if e in doneEdges:
        continue
      (f, rela, t) = qedges[e]
      if dir == -1:
        (f, t) = (t, f)
      if f in newNodes:
        newNodes.add(t)
        newEdges.append((e, dir))
        doneEdges.add(e)
        added = True
        break
    if not added:
      break

  searchExe.newNodes = newNodes
  searchExe.newEdges = newEdges


def _big_choice_first(searchExe):

  # For comparison: the opposite of _small_choice_first.
  # Just to see what the performance difference is.

  qedges = searchExe.qedges
  qnodes = searchExe.qnodes

  newNodes = {sorted(range(len(qnodes)), key=lambda x: -len(searchExe.yarns[x]))[0]}
  newEdges = []
  doneEdges = set()

  remainingEdges = set()
  for e in range(len(qedges)):
    remainingEdges.add((e, 1))
    remainingEdges.add((e, -1))
  remainingEdgesO = sorted(
      remainingEdges,
      key=lambda e: (-searchExe.spreads[e[0]] if e[1] == 1 else -searchExe.spreadsC[e[0]]),
  )

  while 1:
    added = False
    for (e, dir) in remainingEdgesO:
      if e in doneEdges:
        continue
      (f, rela, t) = qedges[e]
      if dir == -1:
        (f, t) = (t, f)
      if f in newNodes and t in newNodes:
        newEdges.append((e, dir))
        doneEdges.add(e)
        added = True
    for (e, dir) in remainingEdgesO:
      if e in doneEdges:
        continue
      (f, rela, t) = qedges[e]
      if dir == -1:
        (f, t) = (t, f)
      if f in newNodes:
        newNodes.add(t)
        newEdges.append((e, dir))
        doneEdges.add(e)
        added = True
        break
    if not added:
      break

  results = {}
  results['newNodes'] = newNodes
  results['newEdges'] = newEdges
  return results


# STITCHING ###


def stitch(searchExe):
  estimateSpreads(searchExe, both=True)
  _stitchPlan(searchExe)
  if searchExe.good:
    _stitchResults(searchExe)


# STITCHING: PLANNING ###


def _stitchPlan(searchExe, strategy=None):
  qnodes = searchExe.qnodes
  qedges = searchExe.qedges
  error = searchExe.api.error
  msgCache = searchExe.msgCache

  setStrategy(searchExe, strategy, keep=True)
  if not searchExe.good:
    return

  good = True

  # Apply the chosen strategy
  searchExe.strategy()

  # remove spurious edges:
  # if we have both the 1 and -1 version of an edge,
  # we can leave out the one that we encounter in the second place

  newNodes = searchExe.newNodes
  newEdges = searchExe.newEdges

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
    error(
        f'''Object mismatch in plan:
In template: {qnodesO}
In plan    : {newNodesO}''', tm=False, cache=msgCache
    )
    good = False

  qedgesO = tuple(range(len(qedges)))
  newCedgesO = tuple(sorted(newCedges))
  if newCedgesO != qedgesO:
    error(
        f'''Relation mismatch in plan:
In template: {qedgesO}
In plan    : {newCedgesO}''', tm=False, cache=msgCache
    )
    good = False

  if not good:
    searchExe.good = False
  else:
    searchExe.stitchPlan = (newNodes, newCedgesOrder)


# STITCHING: DELIVERING ###


def _stitchResults(searchExe):
  qnodes = searchExe.qnodes
  qedges = searchExe.qedges
  plan = searchExe.stitchPlan
  relations = searchExe.relations
  converse = searchExe.converse
  yarns = searchExe.yarns

  planEdges = plan[1]
  if len(planEdges) == 0:
    # no edges, hence a single node (because of connectedness,
    # hence we must deliver everything of its yarn
    yarn = yarns[0]

    def deliver(remap=True):
      for n in yarn:
        yield (n, )

    if searchExe.shallow:
      results = yarn
    else:
      results = deliver
    searchExe.results = results
    return

# The next function must be optimized, and the lookup of functions and data
# should be as direct as possible.
# Because deliver() below fetches the results,
# of wich there are unpredictably many.

# We are going to build-up and deliver stitches,
# which are instantiations of all the query nodes
# by text nodes in a specific sequence
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
# And if the stitch is ordered in the right way,
# the -1's are always at the end.

# We start compiling and permuting

  edgesCompiled = []
  qPermuted = []  # row of nodes in the order as will be created during stitching
  qPermutedInv = {}  # mapping from original q node number to index in the permuted order
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

  shallow = searchExe.shallow

  def deliver(remap=True):
    stitch = [None for q in range(len(qPermuted))]
    lStitch = len(stitch)
    qs = tuple(range(lStitch))
    edgesC = edgesCompiled
    yarnsP = yarnsPermuted

    def stitchOn(e):
      if e >= len(edgesC):
        if remap:
          yield tuple(stitch[qPermutedInv[q]] for q in qs)
        else:
          yield tuple(stitch)
        return
      (f, t, r, nparams) = edgesC[e]
      yarnT = yarnsP[t]
      if e == 0 and stitch[f] is None:
        yarnF = yarnsP[f]
        for sN in yarnF:
          stitch[f] = sN
          for s in stitchOn(e):
            yield s
        return
      sN = stitch[f]
      sM = stitch[t]
      if sM is not None:
        if nparams == 1:
          if sM in set(r(sN)):  # & yarnT:
            for s in stitchOn(e + 1):
              yield s
        else:
          if r(sN, sM):
            for s in stitchOn(e + 1):
              yield s
        return
      mFromN = tuple(set(r(sN)) & yarnT) if nparams == 1 else tuple(m for m in yarnT if r(sN, m))
      for m in mFromN:
        stitch[t] = m
        for s in stitchOn(e + 1):
          yield s
      stitch[t] = None

    for s in stitchOn(0):
      yield s

  def delivered():
    tupleSize = len(qPermuted)
    shallowTupleSize = max(tupleSize, shallow)
    stitch = [None for q in range(tupleSize)]
    edgesC = edgesCompiled
    yarnsP = yarnsPermuted
    resultQ = qPermutedInv[0]
    resultQmax = max(qPermutedInv[q] for q in range(shallowTupleSize))
    resultSet = set()

    def stitchOn(e):
      if e >= len(edgesC):
        yield tuple(stitch)
        return
      (f, t, r, nparams) = edgesC[e]
      yarnT = yarnsP[t]
      if e == 0 and stitch[f] is None:
        yarnF = yarnsP[f]
        if f == resultQmax:
          for sN in yarnF:
            if sN in resultSet:
              continue
            stitch[f] = sN
            for s in stitchOn(e):
              yield s
        else:
          for sN in yarnF:
            stitch[f] = sN
            for s in stitchOn(e):
              yield s
        return
      sN = stitch[f]
      if f == resultQmax:
        if sN in resultSet:
          return
      sM = stitch[t]
      if sM is not None:
        if t == resultQmax:
          if sM in resultSet:
            return
        if nparams == 1:
          if sM in set(r(sN)):  # & yarnT:
            for s in stitchOn(e + 1):
              yield s
        else:
          if r(sN, sM):
            for s in stitchOn(e + 1):
              yield s
        return
      mFromN = tuple(set(r(sN)) & yarnT) if nparams == 1 else tuple(m for m in yarnT if r(sN, m))
      for m in mFromN:
        stitch[t] = m
        for s in stitchOn(e + 1):
          yield s
      stitch[t] = None

    if shallow == 1:
      for s in stitchOn(0):
        result = s[resultQ]
        resultSet.add(result)
    else:  # shallow > 1
      qs = tuple(range(shallow))
      for s in stitchOn(0):
        result = tuple(s[qPermutedInv[q]] for q in qs)
        resultSet.add(result)

    return resultSet

  if shallow:
    searchExe.results = delivered()
  else:
    searchExe.results = deliver
