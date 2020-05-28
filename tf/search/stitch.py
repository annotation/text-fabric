import types
from itertools import chain
from inspect import signature
from .spin import estimateSpreads
from .graph import multiEdges

# STITCHING: STRATEGIES ###

STRATEGY = """
    small_choice_multi
    small_choice_first
    by_yarn_size
    spread_1_first
    big_choice_first
""".strip().split()


def setStrategy(searchExe, strategy, keep=False):
    error = searchExe.api.TF.error
    _msgCache = searchExe._msgCache
    if strategy is None:
        if keep:
            return
        strategy = STRATEGY[0]
    if strategy not in STRATEGY:
        error(f'Strategy not defined: "{strategy}"', cache=_msgCache)
        error(
            "Allowed strategies:\n{}".format("\n".join(f"    {s}" for s in STRATEGY)),
            tm=False,
            cache=_msgCache,
        )
        searchExe.good = False

    func = globals().get(f"_{strategy}", None)
    if not func:
        error(f'Strategy is defined, but not implemented: "{strategy}"', cache=_msgCache)
        searchExe.good = False
    searchExe.strategy = types.MethodType(func, searchExe)
    searchExe.strategyName = strategy


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
        key=lambda e: (
            searchExe.spreads[e[0]] if e[1] == 1 else searchExe.spreadsC[e[0]]
        ),
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
    searchExe.removedEdges = set()


def _small_choice_first(searchExe):

    # This strategy does not try to make a big subgraph of
    # edges with spread 1.
    # The problem is that before the edges work,
    # the initial yarn may have an enormous spread.
    # Here we try out the strategy of postponing
    # broad choices as long as possible.
    # The intuition is that while we are making smaller choices,
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
        key=lambda e: (
            searchExe.spreads[e[0]] if e[1] == 1 else searchExe.spreadsC[e[0]]
        ),
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
    searchExe.removedEdges = set()


def _small_choice_multi(searchExe):

    # This strategy is like small_choice_first
    # but it tries to combine multi-edges as much as possible.

    # A multi edge is a collection of half-bound edges from the same node,
    # some of wich provide an upper bound for that node, and some a lower bound.
    # So, a multi edge constrains choices much more than each of the individual edges.

    qedges = searchExe.qedges
    qnodes = searchExe.qnodes
    converse = searchExe.converse
    spreads = searchExe.spreads
    spreadsC = searchExe.spreadsC
    yarns = searchExe.yarns

    # add the multiedges to the qedges and determine their spreads

    firstMulti = searchExe.firstMulti  # has been set to len(qedges)

    multiEdges(searchExe)
    medges = searchExe.medges
    isMulti = {}
    inMulti = {}

    for (i, me) in enumerate(medges):
        curE = firstMulti + i
        fs = []
        relas = []
        ts = set()  # should end up as a singleton
        minSpread = None
        for (e, dir) in me:
            isMulti.setdefault(curE, []).append((e, dir))
            inMulti[e] = curE
            (a, ru, b) = qedges[e]
            (f, t) = (a, b) if dir == 1 else (b, a)
            spread = spreads[e] if dir == 1 else spreadsC[e]
            if minSpread is None or spread < minSpread:
                minSpread = spread
            r = ru if dir == 1 else converse[ru]
            fs.append(f)
            relas.append(r)
            ts.add(t)
        qedges.append((tuple(fs), tuple(relas), sorted(ts)[0]))
        spreads[curE] = minSpread / 10
        curE += 1

    newNodes = {sorted(range(len(qnodes)), key=lambda x: len(yarns[x]))[0]}
    newEdges = []
    doneEdges = set()

    remainingEdges = set()
    for e in range(len(qedges)):
        remainingEdges.add((e, 1))
        if e < firstMulti:
            remainingEdges.add((e, -1))
    remainingEdgesO = sorted(
        remainingEdges,
        key=lambda e: (
            searchExe.spreads[e[0]] if e[1] == 1 else searchExe.spreadsC[e[0]]
        ),
    )
    removedEdges = set()

    while 1:
        added = False
        for (e, dir) in remainingEdgesO:
            if e in doneEdges:
                continue
            (f, rela, t) = qedges[e]
            if dir == -1:
                (f, t) = (t, f)
            if e in isMulti:
                if all(x in newNodes for x in chain(f, (t,))):
                    newEdges.append((e, dir))
                    doneEdges.add(e)
                    for ed in isMulti[e]:
                        ex = ed[0]
                        if ex not in doneEdges:
                            removedEdges.add(ex)
                        doneEdges.add(ex)
                    added = True
            else:
                if f in newNodes and t in newNodes:
                    newEdges.append((e, dir))
                    doneEdges.add(e)
                    if e in inMulti:
                        ex = inMulti[e]
                        if ex not in doneEdges:
                            removedEdges.add(ex)
                        doneEdges.add(ex)
                    added = True
        for (e, dir) in remainingEdgesO:
            if e in doneEdges:
                continue
            (f, rela, t) = qedges[e]
            if dir == -1:
                (f, t) = (t, f)
            if e in isMulti:
                if all(x in newNodes for x in f):
                    newNodes.add(t)
                    newEdges.append((e, dir))
                    doneEdges.add(e)
                    for ed in isMulti[e]:
                        ex = ed[0]
                        if ex not in doneEdges:
                            removedEdges.add(ex)
                        doneEdges.add(ex)
                    added = True
                    break
            else:
                if f in newNodes:
                    newNodes.add(t)
                    newEdges.append((e, dir))
                    doneEdges.add(e)
                    if e in inMulti:
                        ex = inMulti[e]
                        if ex not in doneEdges:
                            removedEdges.add(ex)
                        doneEdges.add(ex)
                    added = True
                    break
        if not added:
            break

    searchExe.newNodes = newNodes
    searchExe.newEdges = newEdges
    searchExe.removedEdges = removedEdges


def _by_yarn_size(searchExe):

    # This strategy is like small choice first,
    # but we measure the choices differently,
    # namely by yarn size and spread.

    # So, we pick the yarn with the least amount of nodes
    # as our starting point.
    # The corresponding node is our singleton start set.
    # In every iteration we do the following:
    # - we pick all edges of which from- and to-nodes
    #   are already in the node set
    # - we pick the edge with biggest yarn ratio
    #   that has a starting point in the set
    # Until nothing changes anymore

    qedges = searchExe.qedges
    qnodes = searchExe.qnodes
    yarns = searchExe.yarns
    spreads = searchExe.spreads
    spreadsC = searchExe.spreadsC

    def eKey(e, dr):
        (f, rela, t) = qedges[e]
        spr = spreads
        if dr == -1:
            (t, f) = (f, t)
            spr = spreadsC
        yFl = len(yarns[f])
        yTl = len(yarns[t])
        spre = spr[e]
        return spre * yFl * yTl

    newNodes = {sorted(range(len(qnodes)), key=lambda x: len(searchExe.yarns[x]))[0]}
    newEdges = []
    doneEdges = set()

    remainingEdges = set()
    for e in range(len(qedges)):
        remainingEdges.add((e, 1))
        remainingEdges.add((e, -1))
    remainingEdgesO = sorted(remainingEdges, key=lambda e: eKey(*e))

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
    searchExe.removedEdges = set()


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
        key=lambda e: (
            -searchExe.spreads[e[0]] if e[1] == 1 else -searchExe.spreadsC[e[0]]
        ),
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
    searchExe.removedEdges = set()


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
    error = searchExe.api.TF.error
    _msgCache = searchExe._msgCache

    setStrategy(searchExe, strategy, keep=True)
    if not searchExe.good:
        return

    good = True

    # Apply the chosen strategy
    searchExe.firstMulti = len(qedges)
    searchExe.strategy()

    # remove spurious edges:
    # if we have both the 1 and -1 version of an edge,
    # we can leave out the one that we encounter in the second place

    newNodes = searchExe.newNodes
    newEdges = searchExe.newEdges
    removedEdges = searchExe.removedEdges

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
            f"""Object mismatch in plan:
In template: {qnodesO}
In plan    : {newNodesO}""",
            tm=False,
            cache=_msgCache,
        )
        good = False

    qedgesO = tuple(range(len(qedges)))
    newCedgesO = tuple(sorted(chain(newCedges, removedEdges)))
    if newCedgesO != qedgesO:
        error(
            f"""Relation mismatch in plan:
In template: {qedgesO}
In plan    : {newCedgesO}""",
            tm=False,
            cache=_msgCache,
        )
        # good = False

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
    firstMulti = searchExe.firstMulti

    planEdges = plan[1]
    if len(planEdges) == 0:
        # no edges, hence a single node (because of connectedness,
        # hence we must deliver everything of its yarn
        yarn = yarns[0]

        def deliver(remap=True):
            for n in yarn:
                yield (n,)

        if searchExe.shallow:
            results = yarn
        else:
            results = deliver
        searchExe.results = results
        return

    # The next function is optimized, and the lookup of functions and data
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
    qPermutedPos = (
        {}
    )  # mapping from original q node number to index in the permuted order

    for (i, (e, dir)) in enumerate(planEdges):
        isMulti = e >= firstMulti
        (f, rela, t) = qedges[e]
        if dir == -1:
            relai = tuple(converse[r] for r in rela) if isMulti else converse[rela]
            (f, rela, t) = (t, relai, f)
        r = (
            tuple(
                relations[r]["func"](qnodes[f[i]][0], qnodes[t][0])
                for (i, r) in enumerate(rela)
            )
            if isMulti
            else relations[rela]["func"](qnodes[f][0], qnodes[t][0])
        )

        # in case of a multi edge, we use the following implementation detail:
        # the function that computes the relation takes two parameters, not one.
        # Multi-edges are combinations of edges based on < > << >>,
        # and these all have arity 2.

        nparams = 2 if isMulti else len(signature(r).parameters)
        if i == 0:
            # we cannot have a multi-edge here
            # because they are only in play if all its from nodes
            # have been stitched
            qPermuted.append(f)
            qPermutedPos[f] = len(qPermuted) - 1
        if t not in qPermuted:
            qPermuted.append(t)
            qPermutedPos[t] = len(qPermuted) - 1

        compiledF = tuple(qPermutedPos[x] for x in f) if isMulti else qPermutedPos[f]
        compiledT = qPermutedPos[t]

        edgesCompiled.append((compiledF, compiledT, r, nparams, isMulti))

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
                    yield tuple(stitch[qPermutedPos[q]] for q in qs)
                else:
                    yield tuple(stitch)
                return
            (f, t, r, nparams, isMulti) = edgesC[e]
            yarnT = yarnsP[t]
            if e == 0 and stitch[f] is None:
                # this cannot happen for a multi-edge
                yarnF = yarnsP[f]
                for sN in yarnF:
                    stitch[f] = sN
                    for s in stitchOn(e):
                        yield s
                return

            sM = stitch[t]

            # case where sM is already in the graph: just check the conditions

            if sM is not None:
                if isMulti:
                    satisfied = True
                    for (i, x) in enumerate(f):
                        if not r[i](stitch[x], sM):
                            satisfied = False
                            break
                    if satisfied:
                        for s in stitchOn(e + 1):
                            yield s
                else:
                    sN = stitch[f]
                    if nparams == 1:
                        if sM in r(sN):
                            for s in stitchOn(e + 1):
                                yield s
                    else:
                        if r(sN, sM):
                            for s in stitchOn(e + 1):
                                yield s
                return

            # case where we have to visit all choices in the target yarn

            if isMulti:
                for m in yarnT:
                    satisfied = True
                    for (i, x) in enumerate(f):
                        if not r[i](stitch[x], m):
                            satisfied = False
                            break
                    if satisfied:
                        stitch[t] = m
                        for s in stitchOn(e + 1):
                            yield s
            else:
                sN = stitch[f]
                if nparams == 1:
                    for m in r(sN):
                        if m in yarnT:
                            stitch[t] = m
                            for s in stitchOn(e + 1):
                                yield s
                else:
                    for m in yarnT:
                        if r(sN, m):
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
        resultQ = qPermutedPos[0]
        resultQmax = max(qPermutedPos[q] for q in range(shallowTupleSize))
        resultSet = set()
        qs = tuple(range(shallow))

        def stitchOn(e):
            if e >= len(edgesC):
                yield tuple(stitch)
                return
            (f, t, r, nparams, isMulti) = edgesC[e]
            yarnT = yarnsP[t]
            if e == 0 and stitch[f] is None:
                # this cannot happen for a multi-edge
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

            if isMulti and resultQmax in f or not isMulti and resultQmax == f:
                result = tuple(stitch[qPermutedPos[q]] for q in qs)
                if result in resultSet:
                    return

            sM = stitch[t]

            # case where sM is already in the graph: just check the conditions

            if sM is not None:
                if t == resultQmax:
                    result = tuple(stitch[qPermutedPos[q]] for q in qs)
                    if result in resultSet:
                        return

                if isMulti:
                    satisfied = True
                    for (i, x) in enumerate(f):
                        if not r[i](stitch[x], sM):
                            satisfied = False
                            break
                    if satisfied:
                        for s in stitchOn(e + 1):
                            yield s
                else:
                    sN = stitch[f]
                    if nparams == 1:
                        if sM in r(sN):
                            for s in stitchOn(e + 1):
                                yield s
                    else:
                        if r(sN, sM):
                            for s in stitchOn(e + 1):
                                yield s
                return

            # case where we have to visit all choices in the target yarn

            if isMulti:
                for m in yarnT:
                    satisfied = True
                    for (i, x) in enumerate(f):
                        if not r[i](stitch[x], m):
                            satisfied = False
                            break
                    if satisfied:
                        stitch[t] = m
                        for s in stitchOn(e + 1):
                            yield s
            else:
                sN = stitch[f]
                if nparams == 1:
                    for m in r(sN):
                        if m in yarnT:
                            stitch[t] = m
                            for s in stitchOn(e + 1):
                                yield s
                else:
                    for m in yarnT:
                        if r(sN, m):
                            stitch[t] = m
                            for s in stitchOn(e + 1):
                                yield s

            stitch[t] = None

        if shallow == 1:
            for s in stitchOn(0):
                result = s[resultQ]
                resultSet.add(result)
        else:  # shallow > 1
            for s in stitchOn(0):
                result = tuple(s[qPermutedPos[q]] for q in qs)
                resultSet.add(result)

        return resultSet

    if shallow:
        searchExe.results = delivered()
    else:
        searchExe.results = deliver
