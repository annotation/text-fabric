"""
# Unravel

Unraveling means to transform a neighbourhood of nodes into a tree of node fragment.
That sounds simple, but quite a few ideas have to work together to make it work.

It is described at length in `tf.about.displaydesign`.
"""

from collections import namedtuple
from itertools import chain
from ..core.helpers import rangesFromList, console, QUAD
from ..core.text import DEFAULT_FORMAT
from ..parameters import OMAP
from .highlight import getHlAtt
from .helpers import _getLtr


__pdoc__ = {}


class OuterSettings:
    """Common properties during plain() and pretty().
    """

    pass


OuterSettings = namedtuple(  # noqa: F811
    "OuterSettings",
    """
    slotType
    ltr
    fmt
    textClsDefault
    textMethod
    getText
    upMethod
    slotsMethod
    fLookupMethod
    eLookupMethod
    allEFeats
    browsing
    webLink
    getGraphics
""".strip().split(),
)
__pdoc__["OuterSettings.slotType"] = "The slot type of the dataset."
__pdoc__["OuterSettings.ltr"] = "writing direction."
__pdoc__["OuterSettings.fmt"] = "the currently selected text format."
__pdoc__["OuterSettings.textClsDefault"] = "Default CSS class for full text."
__pdoc__["OuterSettings.textMethod"] = (
    "Method to print text of a node according to a text format: "
    "`tf.core.text.Text.text`"
)
__pdoc__["OuterSettings.getText"] = (
    "Method to get the text for a node according to a template: "
    "`tf.advanced.helpers.getText`"
)
__pdoc__[
    "OuterSettings.upMethod"
] = "Method to move from a node to its first embedder: `tf.core.locality.Locality.u`"
__pdoc__[
    "OuterSettings.slotsMethod"
] = "Method to get the slots of a node: `tf.core.oslotsfeature.OslotsFeature.s`"
__pdoc__[
    "OuterSettings.fLookupMethod"
] = "Method to get the value of a node feature: `tf.core.api.Api.Fs`"
__pdoc__[
    "OuterSettings.eLookupMethod"
] = "Method to get the value of an edge feature: `tf.core.api.Api.Es`"
__pdoc__[
    "OuterSettings.allEFeats"
] = "Set of all edge features: `tf.core.api.Api.Eall(warp=False)`"
__pdoc__[
    "OuterSettings.browsing"
] = "whether we work for the TF browser or for a Jupyter notebook"
__pdoc__[
    "OuterSettings.webLink"
] = "Method to produce a web link to a node: `tf.advanced.links.webLink`"
__pdoc__["OuterSettings.getGraphics"] = (
    "Method to fetch graphics for a node. App-dependent."
    "See `tf.advanced.settings` under **graphics**."
)


class NodeProps:
    """Node properties during plain() or pretty().
    """

    pass


NodeProps = namedtuple(  # noqa: F811
    "NodeProps",
    """
    nType
    isSlot
    isSlotOrDescend
    descend
    isBaseNonSlot
    isLexType
    lexType
    lineNumberFeature
    featuresBare
    features
    textCls
    hlCls
    hlStyle
    cls
    hasGraphics
    after
    plainCustom
""".strip().split(),
)
__pdoc__["NodeProps.nType"] = "The node type of the current node."
__pdoc__["NodeProps.isSlot"] = "Whether the current node is a slot node."
__pdoc__["NodeProps.isSlotOrDescend"] = (
    "Whether the current node is a slot node or"
    " has a type to which the current text format should descend."
    " This type is determined by the current text format."
)
__pdoc__["NodeProps.descend"] = (
    "When calling T.text(n, descend=??) for this node, what should we"
    " substitute for the ?? ?"
)
__pdoc__["NodeProps.isBaseNonSlot"] = (
    "Whether the current node has a type that is currently a baseType,"
    " i.e. a type where a pretty display should stop unfolding."
)
__pdoc__["NodeProps.isLexType"] = "Whether nodes of type are lexemes."
__pdoc__[
    "NodeProps.lexType"
] = "If nodes of this type have lexemes in another type, this is that type."
__pdoc__[
    "NodeProps.lineNumberFeature"
] = "Feature with source line numbers of nodes of this type."
__pdoc__[
    "NodeProps.featuresBare"
] = "Features to display in the labels of pretty displays without their names"
__pdoc__[
    "NodeProps.features"
] = "Features to display in the labels of pretty displays with their names"
__pdoc__["NodeProps.textCls"] = "The text Css class of the current node."
__pdoc__["NodeProps.hlCls"] = (
    "The highlight Css class of the current node, "
    "both for pretty and plain modes, keyed by boolean 'is pretty'"
)
__pdoc__["NodeProps.hlStyle"] = (
    "The highlight Css color style of the current node, "
    "both for pretty and plain modes, keyed by boolean 'is pretty'"
)
__pdoc__["NodeProps.cls"] = (
    "A dict of several classes for the display of the node:"
    " for the container, the label, and the children of the node;"
    " might be set by prettyCustom"
)
__pdoc__["NodeProps.hasGraphics"] = "Whether this node type has graphics."
__pdoc__["NodeProps.after"] = (
    "Whether the app defines a custom method to generate material after a child."
    "It is a dict keyed by node type whose values are the custom methods."
)
__pdoc__[
    "NodeProps.plainCustom"
] = "Whether the app defines a custom method to plain displays for this node type."


class TreeInfo:
    """Tree properties during plain() or pretty().

    Collects `NodeProps`, `OuterSettings`, and `tf.advanced.options`.
    """

    def __init__(self, **specs):
        self.update(**specs)

    def update(self, **specs):
        for (k, v) in specs.items():
            setattr(self, k, v)

    def get(self, k, v):
        return getattr(self, k, v)


def unravel(app, n, isPlain=True, _inTuple=False, explain=False, **options):
    """Unravels a node and its graph-neighbourhood into a tree of fragments.

    Parameters
    ----------
    n: integer
        The node to unravel.
    isPlain: boolean, optional True
        Whether to unravel for plain display. Otherwise it is for pretty display.
        The tree structure is the same for both, but the tree is also dressed up
        with formatting information, which may differ for both modes.
    explain: boolean or `'details'`:
        Whether to pretty-print the tree.
        If the value `details` is passed, most of the dressing information of the tree
        is also shown.
    **options:
        Any amount of legal display options.
        These will influence the dressing information.

    Returns
    -------
    chunk: tuple
        `(node, (begin slot, end slot))`
        The top of the tree has `None`
    info: object
        dressing information in the form of key value pairs, among which:
        `options` (the display options that are in force), `settings` (properties
        of node independent properties), `props` (properties
        of the node of the chunk), `boundaryCls` (CSS info for the boundaries of
        the chunk). The top of the tree has only has options and settings.
    children: list
        subtrees where each subtree is again a tuple of chunk, info and children.
    """

    display = app.display
    dContext = display.distill(options)
    return _unravel(app, not isPlain, dContext, n, _inTuple=_inTuple, explain=explain)


def _unravel(app, isPretty, options, n, _inTuple=False, explain=False):
    """Unravels a node in a tree of fragments dressed up with formatting properties.
    """

    _browse = app._browse
    webLink = app.webLink
    getText = app.getText
    getGraphics = getattr(app, "getGraphics", None)

    api = app.api
    N = api.N
    E = api.E
    Es = api.Es
    Eall = api.Eall
    F = api.F
    Fs = api.Fs
    L = api.L
    T = api.T

    eOslots = E.oslots.s
    fOtype = F.otype
    fOtypeV = fOtype.v
    fOtypeAll = fOtype.all
    slotType = fOtype.slotType
    nType = fOtypeV(n)

    aContext = app.context
    lexTypes = aContext.lexTypes
    lexMap = aContext.lexMap
    lineNumberFeature = aContext.lineNumberFeature
    featuresBare = aContext.featuresBare
    features = aContext.features
    descendantType = aContext.descendantType
    levelCls = aContext.levelCls
    styles = aContext.styles
    formatHtml = aContext.formatHtml
    hasGraphics = aContext.hasGraphics

    customMethods = app.customMethods
    afterChild = customMethods.afterChild
    plainCustom = customMethods.plainCustom
    prettyCustom = customMethods.prettyCustom

    baseTypes = options.baseTypes
    highlights = options.highlights
    fmt = options.fmt
    options.set("isHtml", fmt in formatHtml)
    ltr = _getLtr(app, options)
    textClsDefault = _getTextCls(app, fmt)
    descendType = T.formats.get(fmt, slotType)
    textMethod = T.text
    upMethod = L.u

    subBaseTypes = set()

    if baseTypes and baseTypes != {slotType}:
        for bt in baseTypes:
            if bt in descendantType:
                subBaseTypes |= descendantType[bt]

    settings = OuterSettings(
        slotType,
        ltr,
        fmt,
        textClsDefault,
        textMethod,
        getText,
        upMethod,
        eOslots,
        Fs,
        Es,
        {e for e in Eall(warp=False) if not e.startswith(OMAP)},
        _browse,
        webLink,
        getGraphics,
    )

    nodeInfo = {}

    def distillChunkInfo(m, chunkInfo):
        """Gather all the dressing info for a chunk.
        """

        mType = fOtypeV(m)
        isSlot = mType == slotType
        isBaseNonSlot = not isSlot and (mType in baseTypes or mType in subBaseTypes)
        (hlCls, hlStyle) = getHlAtt(app, m, highlights, isSlot)
        cls = {}
        if mType in levelCls:
            cls.update(levelCls[mType])
        if mType in prettyCustom:
            prettyCustom[mType](m, mType, cls)
        textCls = styles.get(mType, settings.textClsDefault)
        nodeInfoM = nodeInfo.setdefault(
            m,
            NodeProps(
                mType,
                isSlot,
                isSlot or mType == descendType,
                False if descendType == mType or mType in lexTypes else None,
                isBaseNonSlot,
                mType in lexTypes,
                lexMap.get(mType, None),
                lineNumberFeature.get(mType, None),
                featuresBare.get(mType, ((), {})),
                features.get(mType, ((), {})),
                textCls,
                hlCls,
                hlStyle,
                cls,
                mType in hasGraphics,
                afterChild.get(mType, None),
                plainCustom.get(mType, None) if plainCustom else None,
            ),
        )
        chunkInfo.update(
            options=options,
            settings=settings,
            props=nodeInfoM,
            boundaryCls=chunkBoundaries[chunk],
        )

    # determine intersecting nodes

    hideTypes = options.hideTypes
    hiddenTypes = options.hiddenTypes
    verseTypes = aContext.verseTypes
    showVerseInTuple = aContext.showVerseInTuple
    full = options.full

    isBigType = (
        _inTuple
        if not isPretty and nType in verseTypes and not showVerseInTuple
        else _getBigType(app, isPretty, options, nType)
    )

    if isBigType and not full:
        iNodes = set()
    elif nType in descendantType:
        myDescendantType = descendantType[nType]
        iNodes = set(L.i(n, otype=myDescendantType))
    elif nType in lexTypes:
        iNodes = {n}
    else:
        iNodes = set(L.i(n))

    if hideTypes:
        iNodes -= {m for m in iNodes if fOtypeV(m) in hiddenTypes}

    iNodes.add(n)

    # chunkify all nodes and determine all true boundaries:
    # of nodes and of their maximal contiguous chunks

    exclusions = aContext.exclusions
    nSlots = eOslots(n)
    if nType in lexTypes:
        nSlots = (nSlots[0],)
    nSlots = set(nSlots)

    chunks = {}
    boundaries = {}

    for m in iNodes:
        mType = fOtypeV(m)
        if mType in exclusions:
            skip = False
            conditions = exclusions[mType]
            for (feat, value) in conditions.items():
                if Fs(feat).v(m) == value:
                    skip = True
                    break
            if skip:
                continue

        slots = eOslots(m)
        if nType in lexTypes:
            slots = (slots[0],)
        if m != n and mType == nType and nSlots <= set(slots):
            continue
        ranges = rangesFromList(slots)
        bounds = {}
        minSlot = min(slots)
        maxSlot = max(slots)

        # for each node m the boundaries value is a dict keyed by slots
        # and valued by a tuple: (left bound, right bound)
        # where bound is:
        # None if there is no left resp. right boundary there
        # True if the left resp. right node boundary is there
        # False if a left resp. right inner chunk boundary is there

        for r in ranges:
            (b, e) = r
            chunks.setdefault(mType, set()).add((m, r))
            bounds[b] = ((b == minSlot), (None if b != e else e == maxSlot))
            bounds[e] = ((b == minSlot if b == e else None), (e == maxSlot))
        boundaries[m] = bounds

    # fragmentize all chunks

    sortKeyChunk = N.sortKeyChunk
    sortKeyChunkLength = N.sortKeyChunkLength

    typeLen = len(fOtypeAll) - 1  # exclude the slot type

    for (p, pType) in enumerate(fOtypeAll):
        pChunks = chunks.get(pType, ())
        if not pChunks:
            continue

        # fragmentize nodes of the same type, largest first

        splits = {}

        pChunksLen = len(pChunks)
        pSortedChunks = sorted(pChunks, key=sortKeyChunkLength)
        for (i, pChunk) in enumerate(pSortedChunks):
            for j in range(i + 1, pChunksLen):
                p2Chunk = pSortedChunks[j]
                splits.setdefault(p2Chunk, set()).update(
                    _getSplitPoints(pChunk, p2Chunk)
                )

        # apply the splits for nodes of this type

        _applySplits(pChunks, splits)

        # fragmentize nodes of other types

        for q in range(p + 1, typeLen):
            qType = fOtypeAll[q]
            qChunks = chunks.get(qType, ())
            if not qChunks:
                continue
            splits = {}
            for qChunk in qChunks:
                for pChunk in pChunks:
                    splits.setdefault(qChunk, set()).update(
                        _getSplitPoints(pChunk, qChunk)
                    )
            _applySplits(qChunks, splits)

    # collect all fragments for all types in one list, ordered canonically
    # theorem: each fragment is either contained in the top node or completely
    # outside the top node.
    # We leave out the fragments that are outside the top node.
    # In order to test that, it is sufficient to test only one slot of
    # the fragment. We take the begin slot/

    chunks = sorted(
        (c for c in chain.from_iterable(chunks.values()) if c[1][0] in nSlots),
        key=sortKeyChunk,
    )

    # determine boundary classes

    startCls = "r" if ltr == "rtl" else "l"
    endCls = "l" if ltr == "rtl" else "r"

    chunkBoundaries = {}

    for (m, (b, e)) in chunks:
        bounds = boundaries[m]
        css = []
        code = bounds[b][0] if b in bounds else None
        cls = f"{startCls}no" if code is None else "" if code else startCls
        if cls:
            css.append(cls)
        code = bounds[e][1] if e in bounds else None
        cls = f"{endCls}no" if code is None else "" if code else endCls
        if cls:
            css.append(cls)

        chunkBoundaries[(m, (b, e))] = " ".join(css)

    # stack the chunks hierarchically

    tree = (None, TreeInfo(options=options, settings=settings), [])
    parent = {}
    rightmost = tree

    for chunk in chunks:
        rightnode = rightmost
        added = False
        m = chunk[0]
        e = chunk[1][1]
        chunkInfo = TreeInfo()

        while rightnode is not tree:
            (br, er) = rightnode[0][1]
            cr = rightnode[2]
            if e <= er:
                rightmost = (chunk, chunkInfo, [])
                cr.append(rightmost)
                parent[chunk] = rightnode
                added = True
                break

            rightnode = parent[rightnode[0]]

        if not added:
            rightmost = (chunk, chunkInfo, [])
            tree[2].append(rightmost)
            parent[chunk] = tree

        distillChunkInfo(m, chunkInfo)

    if explain:
        details = False if explain is True else True if explain == "details" else None
        if details is None:
            console(
                "Illegal value for parameter explain: `{explain}`.\n"
                "Must be `True` or `'details'`",
                error=True,
            )
        _showTree(tree, 0, details=details)
    return tree


def _getSplitPoints(pChunk, qChunk):
    """Determines where the boundaries of one chunk cut through another chunk.

    The splitting point is the index where the second part starts.
    So the split point is always greater than the start point.
    """

    (b1, e1) = pChunk[1]
    (b2, e2) = qChunk[1]
    if b2 == e2 or (b1 <= b2 and e1 >= e2):
        return []
    splitPoints = set()
    if b2 < b1 <= e2:
        splitPoints.add(b1)
    if b2 <= e1 < e2:
        splitPoints.add(e1 + 1)
    return splitPoints


def _applySplits(chunks, splits):
    """Splits a chunk in multiple pieces marked by a given sets of points.
    """

    if not splits:
        return

    for (target, splitPoints) in splits.items():
        if not splitPoints:
            continue
        chunks.remove(target)
        (m, (b, e)) = target
        prevB = b
        # invariant: sp > prevB
        # initially true because it is the result of _getSPlitPoint
        # after each iteration: the new split point cannot be the old one
        # and the new start is the old split point.
        for sp in sorted(splitPoints):
            chunks.add((m, (prevB, sp - 1)))
            prevB = sp
        chunks.add((m, (prevB, e)))


def _getTextCls(app, fmt):
    aContext = app.context
    formatCls = aContext.formatCls
    defaultClsOrig = aContext.defaultClsOrig

    return formatCls.get(fmt or DEFAULT_FORMAT, defaultClsOrig)


def _getBigType(app, isPretty, options, nType):
    api = app.api
    T = api.T
    N = api.N

    sectionTypeSet = T.sectionTypeSet
    structureTypeSet = T.structureTypeSet
    otypeRank = N.otypeRank

    aContext = app.context
    bigTypes = aContext.bigTypes
    isBigOverride = nType in bigTypes

    full = options.full
    condenseType = options.condenseType

    isBig = False
    if not full:
        if not isPretty and isBigOverride:
            isBig = True
        elif sectionTypeSet and nType in sectionTypeSet | structureTypeSet:
            if condenseType is None or otypeRank[nType] > otypeRank[condenseType]:
                isBig = True
        elif condenseType is not None and otypeRank[nType] > otypeRank[condenseType]:
            isBig = True
    return isBig


def _showTree(tree, level, details=False):
    indent = QUAD * level
    (chunk, info, subTrees) = tree
    if chunk is None:
        console(f"{indent}<{level}> TOP")
        settings = info.settings
        options = info.options
        if details:
            _showItems(
                indent,
                settings._asdict().items(),
                ((k, options.get(k)) for k in options.allKeys),
            )
    else:
        (n, (b, e)) = chunk
        rangeRep = "{" + (str(b) if b == e else f"{b}-{e}") + "}"
        props = info.props
        nType = props.nType
        isBaseNonSlot = props.isBaseNonSlot
        base = "*" if isBaseNonSlot else ""
        boundaryCls = info.boundaryCls
        console(f"{indent}<{level}> {nType}{base} {n} {rangeRep} {boundaryCls}")
        if details:
            _showItems(indent, props._asdict().items())
    for subTree in subTrees:
        _showTree(subTree, level + 1, details=details)


def _showItems(indent, *iterables):
    for (k, v) in sorted(chain(*iterables), key=lambda x: x[0],):
        if (
            k == "nType"
            or v is None
            or v == []
            or v == ""
            or v == {}
            or v == ()
            or v == set()
        ):
            continue
        console(f"{indent}{QUAD * 4}{k:<20} = {v}")
