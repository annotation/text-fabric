from itertools import chain

# INSPECTING WITH THE SEARCH GRAPH ###


HALFBOUNDED = {
    "<": 1,
    ">": -1,
    "<<": 1,
    ">>": -1,
}
BOUNDED = {
    "=",
    "==",
    "&&",
    "[[",
    "]]",
    "=:",
    ":=",
    "::",
    ":>",
    "<:",
    "=k:",
    ":k=",
    ":k:",
    ":k>",
    "<k:",
}


def connectedness(searchExe):
    error = searchExe.api.TF.error
    qnodes = searchExe.qnodes
    qedges = searchExe.qedges
    _msgCache = searchExe._msgCache

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
        error("Search without instructions. Tell me what to look for.", cache=_msgCache)
        searchExe.good = False
    elif lComps > 1:
        error(
            f"More than one connected components ({len(searchExe.components)}):",
            cache=_msgCache,
        )
        error(
            "Either run the subqueries one by one, or connect the components by a relation",
            tm=False,
            cache=_msgCache,
        )
        searchExe.good = False


def multiEdges(searchExe):
    relations = searchExe.relations
    qedges = searchExe.qedges
    _msgCache = searchExe._msgCache
    api = searchExe.api
    error = api.TF.error

    medgesIndex = {}
    # will be a dict keyed by edge destination, then by upper/lower bound
    # and then the values are directed edges
    for (e, (f, rela, t)) in enumerate(qedges):
        relInfo = relations[rela]
        acro = relInfo.get("name", relInfo["acro"])
        if acro in HALFBOUNDED:
            dir = HALFBOUNDED[acro]
            # edge e,1 arrives at t which acts as an upper bound
            medgesIndex.setdefault(t, {}).setdefault(dir, set()).add((e, 1))
            # edge e,-1 arrives at f which acts as a lower bound
            medgesIndex.setdefault(f, {}).setdefault(-dir, set()).add((e, -1))

    medges = []
    for eInfo in medgesIndex.values():
        if 1 in eInfo and -1 in eInfo:
            es = eInfo[1] | eInfo[-1]
            ts = {qedges[e][2 if dir == 1 else 0] for (e, dir) in es}
            if len(ts) != 1:
                # if this happens, it is a fault in the business logic, not caused by the user
                eRep = " | ".join(str(qedges[e]) for (e, dir) in es)
                error(
                    f"Multi-edge with {len(ts)} destinations: {eRep}",
                    tm=False,
                    cache=_msgCache,
                )
            medges.append(es)

    # so medges is a collection sets of edges
    # each set consists of directed edges that have the same qnode as destination
    searchExe.medges = medges


def displayPlan(searchExe, details=False):
    if not searchExe.good:
        return
    api = searchExe.api
    TF = api.TF
    setSilent = TF.setSilent
    isSilent = TF.isSilent
    info = TF.info
    wasSilent = isSilent()
    setSilent(False)
    _msgCache = searchExe._msgCache
    nodeLine = searchExe.nodeLine
    qedges = searchExe.qedges
    (qs, es) = searchExe.stitchPlan
    offset = searchExe.offset

    if details:
        info(
            f"Search with {len(qs)} objects and {len(es)} relations",
            tm=False,
            cache=_msgCache,
        )
        info(
            "Results are instantiations of the following objects:",
            tm=False,
            cache=_msgCache,
        )
        for q in qs:
            displayNode(searchExe, q)
        if len(es) != 0:
            info("Performance parameters:", tm=False, cache=_msgCache)
            for (k, v) in searchExe.perfParams.items():
                info(f"\t{k:<20} = {v:>7}", tm=False, cache=_msgCache)
            info(
                "Instantiations are computed along the following relations:",
                tm=False,
                cache=_msgCache,
            )
            (firstE, firstDir) = es[0]
            (f, rela, t) = qedges[firstE]
            if firstDir == -1:
                (f, t) = (t, f)
            displayNode(searchExe, f, pos2=True)

            nodesSeen = {f}
            for e in es:
                nodesSeen |= displayEdge(searchExe, *e, nodesSeen)
    info(
        "The results are connected to the original search template as follows:",
        cache=_msgCache,
    )

    resultNode = {}
    for q in qs:
        resultNode[nodeLine[q]] = q
    for (i, line) in enumerate(searchExe.searchLines):
        rNode = resultNode.get(i, "")
        prefix = "" if rNode == "" else "R"
        info(f"{i + offset:>2} {prefix:<1}{rNode:<2} {line}", tm=False, cache=_msgCache)

    setSilent(wasSilent)


def displayNode(searchExe, q, pos2=False):
    info = searchExe.api.TF.info
    _msgCache = searchExe._msgCache
    qnodes = searchExe.qnodes
    yarns = searchExe.yarns
    space = " " * 31
    nodeInfo = (
        "node {} {:>2}-{:<13} {:>6}   choices".format(
            space, q, qnodes[q][0], len(yarns[q]),
        )
        if pos2
        else "node {:>2}-{:<13} {} {:>6}   choices".format(
            q, qnodes[q][0], space, len(yarns[q]),
        )
    )
    info(nodeInfo, tm=False, cache=_msgCache)


def displayEdge(searchExe, e, dir, nodesSeen):
    info = searchExe.api.TF.info
    _msgCache = searchExe._msgCache
    qnodes = searchExe.qnodes
    qedges = searchExe.qedges
    converse = searchExe.converse
    relations = searchExe.relations
    spreads = searchExe.spreads
    spreadsC = searchExe.spreadsC
    thinned = getattr(searchExe, "thinned", set())
    (f, rela, t) = qedges[e]
    if type(f) is not tuple:
        f = (f,)
    if type(t) is not tuple:
        t = (t,)
    if type(rela) is not tuple:
        rela = (rela,)
    if dir == -1:
        (f, rela, t) = (t, tuple(converse[r] for r in rela), f)

    nodesInvolved = set(chain(f, t))
    seen = all(q in nodesSeen for q in nodesInvolved)
    thinRep = "" if seen else " (thinned)" if e in thinned else ""
    spread = (
        f"{0:>6}  "
        if seen
        else f"{spreads.get(e, -1) if dir == 1 else spreadsC.get(e, -1):8.1f}"
    )
    info(
        "edge {:>8}-{:<13} {:^8} {:>2}-{:<13} {} choices{}".format(
            ",".join(str(x) for x in f),
            ",".join(set(qnodes[x][0] for x in f)),
            ",".join(relations[x]["acro"] for x in rela),
            ",".join(str(x) for x in set(t)),
            ",".join(qnodes[x][0] for x in set(t)),
            spread,
            thinRep,
        ),
        tm=False,
        cache=_msgCache,
    )
    return nodesInvolved
