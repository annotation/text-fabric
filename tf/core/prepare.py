"""
# Precompute data.

For Text-Fabric to work efficiently, some  derived data needs to be precomputed.
The precomputed data has a similar function as indexes in a database.

Precomputation is triggered when `tf.fabric.Fabric` loads features, and
the order and nature of the steps is configured in
`tf.core.fabric.PRECOMPUTE`.

The functions in this module implement those tasks.
"""

from array import array
import collections
import functools
from .helpers import itemize


def levels(info, error, otype, oslots, otext):
    """Computes level data.

    For each node type, compute the average number of slots occupied by its nodes,
    and order the node types on that.

    Parameters
    ----------
    info: function
        Method to write informational messages to the console.
    error: function
        Method to write error messages to the console.
    otype: iterable
        The data of the *otype* feature.
    oslots: iterable
        The data of the *oslots* feature.
    otext: iterable
        The data of the *otext* feature.

    Returns
    -------
    tuple
        An ordered tuple, each member with the information of a node type:

        *   node type name
        *   average number of slots contained in the nodes of this type
        *   first node of this type
        *   last node of this type

    The order of the tuple is descending by average number of slots per node of that
    type.

    Notes
    -----
    !!! explanation "Level computation and customization"
        All node types have a level, defined by the average amount of slots object of
        that type usually occupy. The bigger the average object, the lower the levels.
        Books have the lowest level, words the highest level.

        However, this can be overruled. Suppose you have a node type *phrase* and above
        it a node type *cluster*, i.e. phrases are contained in clusters, but not vice
        versa. If all phrases are contained in clusters, and some clusters have more
        than one phrase, the automatic level ranking of node types works out well in
        this case. But if clusters only have very small phrases, and the big phrases do
        not occur in clusters, then the algorithm may assign a lower rank to clusters
        than to phrases.

        In general, it is too expensive to try to compute the levels in a sophisticated
        way. In order to remedy cases where the algorithm assigns wrong levels, you can
        add a `@levels` key to the `otext` config feature.
        See `tf.core.text`.
    """

    (otype, maxSlot, maxNode, slotType) = otype
    oslots = oslots[0]
    levelOrder = otext.get("levels", None)
    if levelOrder is not None:
        levelRank = {level: i for (i, level) in enumerate(levelOrder.split(","))}
    otypeCount = collections.Counter()
    otypeMin = {}
    otypeMax = {}
    slotSetLengths = collections.Counter()
    info("get ranking of otypes")
    for k in range(len(oslots)):
        ntp = otype[k]
        otypeCount[ntp] += 1
        slotSetLengths[ntp] += len(oslots[k])
        tfn = k + maxSlot + 1
        if ntp not in otypeMin:
            otypeMin[ntp] = tfn
        if ntp not in otypeMax or otypeMax[ntp] < tfn:
            otypeMax[ntp] = tfn
    sortKey = (lambda x: -x[1]) if levelOrder is None else (lambda x: levelRank[x[0]])
    result = tuple(
        sorted(
            (
                (
                    ntp,
                    slotSetLengths[ntp] / otypeCount[ntp],
                    otypeMin[ntp],
                    otypeMax[ntp],
                )
                for ntp in otypeCount
            ),
            key=sortKey,
        )
        + [(slotType, 1, 1, maxSlot)]
    )
    info("results:")
    for (otp, av, omin, omax) in result:
        info(f"{otp:<15}: {round(av, 2):>8} {{{omin}-{omax}}}", tm=False)
    return result


def order(info, error, otype, oslots, levels):
    """Computes order data for the canonical ordering.

    The canonical ordering between nodes is defined in terms of the slots that
    nodes contain, and if that is not decisive, the rank of the node type is taken
    into account, and if that is still not decisive, the node itself is taken into
    account.

    Parameters
    ----------
    info: function
        Method to write informational messages to the console.
    error: function
        Method to write error messages to the console.
    otype: iterable
        The data of the *otype* feature.
    oslots: iterable
        The data of the *oslots* feature.
    levels: tuple
        The data of the *levels* precompute step.

    Returns
    -------
    array
        All nodes, slot and nonslot, in canonical order.

    Notes
    -----
    We store the result in an array because it saves a lot of memory, and access
    is still fast.

    See Also
    --------
    tf.core.nodes: canonical ordering
    """

    (otype, maxSlot, maxNode, slotType) = otype
    oslots = oslots[0]
    info("assigning otype levels to nodes")
    otypeLevels = dict(((x[0], i) for (i, x) in enumerate(reversed(levels))))

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
            return (
                (-1 if na < nb else 1 if na > nb else 0)
                if oa == ob
                else -1
                if oa > ob
                else 1
            )
        if sa > sb:
            return -1
        if sa < sb:
            return 1
        am = min(sa - sb)
        bm = min(sb - sa)
        return -1 if am < bm else 1 if bm < am else None

    canonKey = functools.cmp_to_key(before)
    info("sorting nodes")
    nodes = sorted(range(1, maxNode + 1), key=canonKey)
    return array("I", nodes)


def rank(info, error, otype, order):
    """Computes rank data.

    The rank of a node is its place in among the other nodes in the
    canonical order (see `tf.core.nodes`).

    Parameters
    ----------
    info: function
        Method to write informational messages to the console.
    error: function
        Method to write error messages to the console.
    otype: iterable
        The data of the *otype* feature.
    order: array
        The data of the *order* feature.

    Returns
    -------
    array
        The ranks of all nodes, slot and nonslot, with respect to the canonical order.

    Notes
    -----
    We store the result in an array because it saves a lot of memory, and access
    is still fast.
    """

    (otype, maxSlot, maxNode, slotType) = otype
    info("ranking nodes")
    nodesRank = dict(((n, i) for (i, n) in enumerate(order)))
    return array("I", (nodesRank[n] for n in range(1, maxNode + 1)))


def levUp(info, error, otype, oslots, rank):
    """Computes level-up data.

    Level-up data is used by the API function `tf.core.locality.Locality.u`.

    This function computes the embedders of a node by looking them up from
    the level-up data.

    Parameters
    ----------
    info: function
        Method to write informational messages to the console.
    error: function
        Method to write error messages to the console.
    otype: iterable
        The data of the *otype* feature.
    oslots: iterable
        The data of the *oslots* feature.
    rank: array
        The data of the *rank* precompute step.

    Returns
    -------
    tuple
        The n-th member is an array of the embedder nodes of n.
        Those arrays are sorted in canonical order (`tf.core.nodes`).

    Notes
    -----
    !!! hint "Memory efficiency"
        Many nodes have the same array of embedders.
        Those embedder arrays will be reused for those nodes.

    Warnings
    --------
    It is not advisable to this data directly by `C.levUp.data`,
    it is far better to use the `tf.core.locality.Locality.u` function.

    Only when every bit of performance waste has to be squeezed out,
    this raw data might be a deal.
    """

    (otype, maxSlot, maxNode, slotType) = otype
    oslots = oslots[0]
    info("making inverse of edge feature oslots")
    oslotsInv = {}
    for (k, mList) in enumerate(oslots):
        for m in mList:
            oslotsInv.setdefault(m, set()).add(k + 1 + maxSlot)
    info("listing embedders of all nodes")
    embedders = []
    for n in range(1, maxSlot + 1):
        contentEmbedders = oslotsInv[n]
        embedders.append(
            tuple(
                sorted(
                    [m for m in contentEmbedders if m != n], key=lambda k: -rank[k - 1],
                )
            )
        )
    for n in range(maxSlot + 1, maxNode + 1):
        mList = oslots[n - maxSlot - 1]
        if len(mList) == 0:
            embedders.append(tuple())
        else:
            contentEmbedders = functools.reduce(
                lambda x, y: x & oslotsInv[y], mList[1:], oslotsInv[mList[0]],
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
            seen[t] = array("I", t)
        embeddersx.append(seen[t])
    return tuple(embeddersx)


def levDown(info, error, otype, levUp, rank):
    """Computes level-down data.

    Level-down data is used by the API function `tf.core.locality.Locality.d`.

    This function computes the embedded nodes of a node by looking them up from
    the level-down data.

    Parameters
    ----------
    info: function
        Method to write informational messages to the console.
    error: function
        Method to write error messages to the console.
    otype: iterable
        The data of the *otype* feature.
    levUp: iterable
        The data of the *levUp* precompute step.
    rank: array
        The data of the *rank* precompute step.

    Returns
    -------
    tuple
        The *n*-th member is an array of the embedded nodes of *n + maxSlot*.
        Those arrays are sorted in canonical order (`tf.core.nodes`).

    !!! hint "Memory efficiency"
        Slot nodes do not have embedded nodes, so they do not have to occupy
        space in this tuple. Hence the first member are the embedded nodes
        of node *maxSlot + 1*.

    !!! caution "Use with care"
        It is not advisable to this data directly by `C.levDown.data`,
        it is far better to use the `tf.core.locality.Locality.d` function.

        Only when every bit of performance waste has to be squeezed out,
        this raw data might be a deal.
    """

    (otype, maxSlot, maxNode, slotType) = otype
    info("inverting embedders")
    inverse = {}
    for n in range(maxSlot + 1, maxNode + 1):
        for m in levUp[n - 1]:
            inverse.setdefault(m, set()).add(n)
    info("turning embeddees into list")
    embeddees = []
    for n in range(maxSlot + 1, maxNode + 1):
        embeddees.append(
            array("I", sorted(inverse.get(n, []), key=lambda m: rank[m - 1]))
        )
    return tuple(embeddees)


def boundary(info, error, otype, oslots, rank):
    """Computes boundary data.

    For each slot, the nodes that start at that slot and the nodes that end
    at that slot are collected.

    Boundary data is used by the API functions
    `tf.core.locality.Locality.p`.
    and
    `tf.core.locality.Locality.n`.

    Parameters
    ----------
    info: function
        Method to write informational messages to the console.
    error: function
        Method to write error messages to the console.
    otype: iterable
        The data of the *otype* feature.
    oslots: iterable
        The data of the *oslots* feature.
    rank: array
        The data of the *rank* precompute step.

    Returns
    -------
    tuple
        *   first: tuple of array
            The *n*-th member is the array of nodes that start at slot *n*,
            ordered in *reversed* canonical order (`tf.core.nodes`);
        *   last: tuple of array
            The *n*-th member is the array of nodes that end at slot *n*,
            ordered in canonical order;

    Notes
    -----
    !!! hint "why  reversed canonical order?"
        Just for symmetry.
    """

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
        firstSlots.append(
            array("I", sorted(firstSlotsD.get(n, []), key=lambda k: -rank[k - 1]))
        )
        lastSlots.append(
            array("I", sorted(lastSlotsD.get(n, []), key=lambda k: rank[k - 1]))
        )
    return (tuple(firstSlots), tuple(lastSlots))


def sections(info, error, otype, oslots, otext, levUp, levels, *sFeats):
    """Computes section data.

    Text-Fabric datasets may define up to three section levels, roughly corresponding
    with a volume, a chapter, a paragraph.

    If the corpus has a richer section structure, it is also possible
    a different, more flexible and more extensive nest of structural sections.
    See `structure`.

    Text-Fabric must be able to go from sections at one level to the sections
    at one level lower. It must also be able to map section headings
    to nodes. For this, the section features are needed, since they
    contain the section headings.

    Parameters
    ----------
    info: function
        Method to write informational messages to the console.
    error: function
        Method to write error messages to the console.
    otype: iterable
        The data of the *otype* feature.
    oslots: iterable
        The data of the *oslots* feature.
    otext: iterable
        The data of the *otext* feature.
    levUp: array
        The data of the *levUp* precompute step.
    levels: array
        The data of the *levels* precompute step.
    sFeats: iterable
        The names of section features.

    Returns
    -------
    tuple
        *   sec1
            Mapping from section-level-1 nodes to mappings from
            section-level-2 headings to section-level2 nodes.
        *   sec2
            Mapping from section-level-1 nodes to mappings from
            section-level-2 headings to mappings from
            section-level3 headings to section-level-3 nodes.

    Warnings
    --------
    Note that the terms `book`, `chapter`, `verse` are not baked into Text-Fabric.
    It is the corpus data, especially the `otext` config feature that
    spells out the names of the sections.

    """

    (otype, maxSlot, maxNode, slotType) = otype
    oslots = oslots[0]
    support = dict(((o[0], (o[2], o[3])) for o in levels))
    sTypes = itemize(otext["sectionTypes"], ",")
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
                nestingProblems[
                    f"section {sTypes[1]} without containing {sTypes[0]}"
                ] += 1
                continue
            n0 = n0s[0]
            n1s = sFeats[1][n1]
            if n0 not in sec1:
                sec1[n0] = {}
            if n1s not in sec1[n0]:
                sec1[n0][n1s] = n1
                c1 += 1
        info(f"{c1} {sTypes[1]}s indexed")

    else:
        c1 = 0
        c2 = 0
        support2 = support[sTypes[2]]
        for n2 in range(support2[0], support2[1] + 1):
            n0s = tuple(x for x in levUp[n2 - 1] if otype[x - maxSlot - 1] == sTypes[0])
            if not n0s:
                nestingProblems[
                    f"section {sTypes[2]} without containing {sTypes[0]}"
                ] += 1
                continue
            n0 = n0s[0]
            n1s = tuple(x for x in levUp[n2 - 1] if otype[x - maxSlot - 1] == sTypes[1])
            if not n1s:
                nestingProblems[
                    f"section {sTypes[2]} without containing {sTypes[1]}"
                ] += 1
                print(f"{sTypes[2]} {n2} without containing {sTypes[1]}")
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
        info(f"{c1} {sTypes[1]}s and {c2} {sTypes[2]}s indexed")

    if nestingProblems:
        for (msg, amount) in sorted(nestingProblems.items()):
            error(f"WARNING: {amount:>4} x {msg}")

    return (sec1, sec2)


def structure(info, error, otype, oslots, otext, rank, levUp, *sFeats):
    """Computes structure data.

    If the corpus has a rich section structure, it is possible to define
    a flexible and extensive nest of structural sections.

    Independent of this,
    Text-Fabric datasets may also define up to three section levels,
    roughly corresponding with a volume, a chapter, a paragraph.
    See `sections`.

    Text-Fabric must be able to go from sections at one level to the sections
    at one level lower. It must also be able to map section headings
    to nodes. For this, the section features are needed, since they
    contain the section headings.

    Parameters
    ----------
    info: function
        Method to write informational messages to the console.
    error: function
        Method to write error messages to the console.
    otype: iterable
        The data of the *otype* feature.
    oslots: iterable
        The data of the *oslots* feature.
    otext: iterable
        The data of the *otext* feature.
    rank: array
        The data of the *rank* precompute step.
    levUp: array
        The data of the *levUp* precompute step.
    sFeats: iterable
        The names of structural features.

    Returns
    -------
    tuple
        *   headingFromNode
            (Mapping from nodes to section keys)
        *   nodeFromHeading
            (Mapping from section keys to nodes)
        *   multiple
        *   top
        *   up
        *   down

    Notes
    -----
    A section key of a structural node is obtained by going a level up from
    that node, retrieving the heading of that structural node, then going up again,
    and so on till a top node is reached. The tuple of headings obtained in this way
    is the  section key.
    """

    (otype, maxSlot, maxNode, slotType) = otype
    oslots = oslots[0]
    sTypeList = itemize(otext["structureTypes"], ",")
    nsTypes = len(sTypeList)
    nsFeats = len(sFeats)

    if nsTypes != nsFeats:
        error(
            f"WARNING: {nsTypes} structure levels but {nsFeats} corresponding features"
        )
        return ({}, {})

    sTypes = set(sTypeList)
    if len(sTypes) != nsTypes:
        error("WARNING: duplicate structure levels")
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
        sKey = tuple(
            reversed(
                tuple(
                    (
                        otype[x - maxSlot - 1],
                        featFromType[otype[x - maxSlot - 1]].get(x, None),
                    )
                    for x in (n, *ups)
                )
            )
        )

        if sKey in nodeFromHeading:
            if sKey not in multiple:
                multiple[sKey].append(nodeFromHeading[sKey])
            multiple[sKey].append(n)
        nodeFromHeading[sKey] = n
        headingFromNode[n] = sKey
    multiple = {
        sKey: tuple(sorted(ns, key=lambda n: rank[n - 1]))
        for (sKey, ns) in multiple.items()
    }

    top = tuple(
        sorted(
            (n for (n, h) in headingFromNode.items() if len(h) == 1),
            key=lambda n: rank[n - 1],
        )
    )

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

    down = {n: tuple(sorted(ms, key=lambda m: rank[m - 1])) for (n, ms) in down.items()}

    return (headingFromNode, nodeFromHeading, multiple, top, up, down)
