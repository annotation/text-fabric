from collections import namedtuple

from .helpers import getText, htmlSafe, NB
from .highlight import getHlAtt
from ..core.text import DEFAULT_FORMAT
from ..core.nodes import GAP_START, GAP_END
from ..core.helpers import (
    htmlEsc,
    rangesFromList,
    rangesFromSet,
    console,
)
from .settings import ORIG

QUAD = "  "
LIMIT_DISPLAY_DEPTH = 100

__pdoc__ = {}


class OuterContext:
    """Outer node properties during plain() and pretty().
    Only the properties of the node for which the outer call
    plain() or pretty() has been made, not the nodes encountered
    during recursion."
    """

    pass


OuterContext = namedtuple(  # noqa: F811
    "OuterContext",
    """
    ltr
    textCls
    slots
    inTuple
    explain
""".strip().split(),
)
__pdoc__["OuterContext.ltr"] = "writing direction."
__pdoc__["OuterContext.textCls"] = "Css class for full text."
__pdoc__["OuterContext.slots"] = "Set of slots under the outer node."
__pdoc__[
    "OuterContext.inTuple"
] = "Whether the outer node is displayed as part of a tuple of nodes."


class NodeContext:
    """Node properties during plain() or pretty().
    """

    pass


NodeContext = namedtuple(  # noqa: F811
    "NodeContext",
    """
    slotType
    nType
    isSlot
    isSlotOrDescend
    descend
    isBaseNonSlot
    chunks
    chunkBoundaries
    textCls
    hlCls
    hlStyle
    nodePart
    cls
""".strip().split(),
)
__pdoc__["NodeContext.slotType"] = "The slot type of the data set."
__pdoc__["NodeContext.nType"] = "The node type of the current node."
__pdoc__["NodeContext.isSlot"] = "Whether the current node is a slot node."
__pdoc__["NodeContext.isSlotOrDescend"] = (
    "Whether the current node is a slot node or"
    " has a type to which the current text format should descend."
    " This type is determined by the current text format."
)
__pdoc__["NodeContext.descend"] = (
    "When calling T.text(n, descend=??) for this node, what should we"
    " substitute for the ?? ?"
)
__pdoc__["NodeContext.isBaseNonSlot"] = (
    "Whether the current node has a type that is currently a baseType,"
    " i.e. a type where a pretty display should stop unfolding."
    " No need to put the slot type in this set."
)
__pdoc__["NodeContext.chunks"] = (
    "The chunks of the current node."
    " They result from unraveling the node into child pieces."
)
__pdoc__["NodeContext.chunkBoundaries"] = (
    "The boundary Css classes of the chunks of the current node."
    " Nodes can have a firm of dotted left/right boundary, or no boundary at all."
)
__pdoc__["NodeContext.textCls"] = "The text Css class of the current node."
__pdoc__["NodeContext.hlCls"] = "The highlight Css class of the current node."
__pdoc__["NodeContext.hlStyle"] = "The highlight style attribute of the current node."
__pdoc__[
    "NodeContext.nodePart"
] = "The node type/number insofar it has to be displayed for the current node"
__pdoc__["NodeContext.cls"] = (
    "A dict of several classes for the display of the node:"
    " for the container, the label, and the children of the node;"
    " might be set by prettyCustom"
)


# PLAIN LOW-LEVEL


def _doPlain(
    app,
    dContext,
    oContext,
    n,
    slots,
    boundaryCls,
    outer,
    first,
    last,
    level,
    passage,
    html,
    done,
    called,
):
    if _depthExceeded(level):
        return

    if type(n) is str:
        html.append(f'<span class="{boundaryCls}"> </span>')
        return

    origOuter = outer
    if outer is None:
        outer = True

    nContext = _prepareDisplay(
        app, False, dContext, oContext, n, slots, origOuter, done=done, called=called
    )
    if type(nContext) is str:
        _note(
            app,
            False,
            oContext,
            n,
            nContext,
            slots,
            first,
            last,
            level,
            None,
            "nothing to do",
        )
        return "".join(html) if outer else None

    nCalled = called.setdefault(n, set())

    finished = slots <= done
    calledBefore = slots <= nCalled
    if finished or calledBefore:
        _note(
            app,
            False,
            oContext,
            n,
            nContext.nType,
            slots,
            first,
            last,
            level,
            "already " + ("finished" if finished else "called"),
            task=slots,
            done=done,
            called=nCalled,
        )
        return "".join(html) if outer else None

    ltr = oContext.ltr

    hlCls = nContext.hlCls
    hlStyle = nContext.hlStyle
    nodePart = nContext.nodePart

    outerCls = f"outer" if outer else ""

    clses = f"plain {outerCls} {ltr} {boundaryCls} {hlCls}"
    html.append(f'<span class="{clses}" {hlStyle}>')

    if nodePart:
        html.append(nodePart)

    contrib = _doPlainNode(
        app, dContext, oContext, nContext, n, outer, first, last, level, passage, done,
    )
    _note(
        app, False, oContext, n, nContext.nType, slots, first, last, level, contrib,
    )
    html.append(contrib)

    nCalled.update(slots)

    chunks = nContext.chunks
    chunkBoundaries = nContext.chunkBoundaries
    lastCh = len(chunks) - 1

    _note(
        app,
        False,
        oContext,
        n,
        nContext.nType,
        slots,
        first,
        last,
        level,
        None,
        "start subchunks" if chunks else "bottom node",
        chunks=chunks,
        chunkBoundaries=chunkBoundaries,
        task=slots,
        done=done,
        called=nCalled,
    )

    for (i, ch) in enumerate(chunks):
        (chN, chSlots) = ch
        chBoundaryCls = chunkBoundaries[ch]
        thisFirst = first and i == 0
        thisLast = last and i == lastCh
        _doPlain(
            app,
            dContext,
            oContext,
            chN,
            chSlots,
            chBoundaryCls,
            False,
            thisFirst,
            thisLast,
            level + 1,
            "",
            html,
            done,
            called,
        )

    html.append("</span>")

    done |= slots

    if chunks:
        _note(
            app,
            False,
            oContext,
            n,
            nContext.nType,
            slots,
            first,
            last,
            level,
            None,
            "end subchunks",
            done=done,
        )

    return "".join(html) if outer else None


def _doPlainNode(
    app, dContext, oContext, nContext, n, outer, first, last, level, passage, done
):
    api = app.api
    T = api.T

    aContext = app.context
    plainCustom = aContext.plainCustom

    isHtml = dContext.isHtml
    fmt = dContext.fmt

    ltr = oContext.ltr
    textCls = nContext.textCls

    nType = nContext.nType

    isSlotOrDescend = nContext.isSlotOrDescend
    descend = nContext.descend

    if nType in plainCustom:
        method = plainCustom[nType]
        contrib = method(app, dContext, oContext, nContext, n, outer, done=done)
        return contrib
    if isSlotOrDescend:
        text = htmlSafe(
            T.text(
                n,
                fmt=fmt,
                descend=descend,
                outer=outer,
                first=first,
                last=last,
                level=level,
            ),
            isHtml,
        )
        contrib = f'<span class="{textCls}">{text}</span>'
    else:
        tplFilled = getText(
            app,
            False,
            n,
            nType,
            outer,
            first,
            last,
            level,
            passage if outer else "",
            descend,
            dContext=dContext,
        )
        contrib = f'<span class="plain {textCls} {ltr}">{tplFilled}</span>'

    return contrib


# PRETTY LOW-LEVEL


def _doPretty(
    app,
    dContext,
    oContext,
    n,
    slots,
    boundaryCls,
    outer,
    first,
    last,
    level,
    html,
    done,
    called,
):
    if _depthExceeded(level):
        return

    if type(n) is str:
        html.append(f'<div class="{boundaryCls}"> </div>')
        return

    nContext = _prepareDisplay(
        app, True, dContext, oContext, n, slots, outer, done=done, called=called
    )
    if type(nContext) is str:
        _note(
            app, True, oContext, n, nContext, slots, first, last, level, "nothing to do"
        )
        return "".join(html) if outer else None

    nCalled = called.setdefault(n, set())

    finished = slots <= done
    calledBefore = slots <= nCalled
    if finished or calledBefore:
        _note(
            app,
            True,
            oContext,
            n,
            nContext.nType,
            slots,
            first,
            last,
            level,
            "already " + ("finished" if finished else "called"),
            task=slots,
            done=done,
            called=nCalled,
        )
        return "".join(html) if outer else None

    aContext = app.context
    afterChild = aContext.afterChild
    hasGraphics = aContext.hasGraphics

    showGraphics = dContext.showGraphics

    ltr = oContext.ltr

    isBaseNonSlot = nContext.isBaseNonSlot
    nType = nContext.nType

    nodePlain = None
    if isBaseNonSlot:
        nodePlain = _doPlain(
            app,
            dContext,
            oContext,
            n,
            slots,
            boundaryCls,
            None,
            first,
            last,
            level,
            "",
            [],
            done,
            called,
        )

    (label, featurePart) = _doPrettyNode(
        app, dContext, oContext, nContext, n, outer, first, last, level, nodePlain
    )
    (containerB, containerE) = _doPrettyWrapPre(
        app,
        n,
        outer,
        label,
        featurePart,
        boundaryCls,
        html,
        nContext,
        showGraphics,
        hasGraphics,
        ltr,
    )

    nCalled.update(slots)

    cls = nContext.cls
    childCls = cls["children"]
    chunks = nContext.chunks
    chunkBoundaries = nContext.chunkBoundaries

    if chunks:
        html.append(f'<div class="{childCls} {ltr}">')

    lastCh = len(chunks) - 1

    _note(
        app,
        True,
        oContext,
        n,
        nContext.nType,
        slots,
        first,
        last,
        level,
        None,
        "start subchunks" if chunks else "bottom node",
        chunks=chunks,
        chunkBoundaries=chunkBoundaries,
        task=slots,
        done=done,
        called=nCalled,
    )

    for (i, ch) in enumerate(chunks):
        (chN, chSlots) = ch
        chBoundaryCls = chunkBoundaries[ch]
        thisFirst = first and i == 0
        thisLast = last and i == lastCh
        _doPretty(
            app,
            dContext,
            oContext,
            chN,
            chSlots,
            chBoundaryCls,
            False,
            thisFirst,
            thisLast,
            level + 1,
            html,
            done,
            called,
        )
        after = afterChild.get(nType, None)
        if after:
            html.append(after(ch))

    done |= slots

    if chunks:
        _note(
            app,
            True,
            oContext,
            n,
            nContext.nType,
            slots,
            first,
            last,
            level,
            None,
            "end subchunks",
            task=slots,
        )

    if chunks:
        html.append("</div>")

    _doPrettyWrapPost(label, featurePart, html, containerB, containerE)

    return "".join(html) if outer else None


def _doPrettyWrapPre(
    app,
    n,
    outer,
    label,
    featurePart,
    boundaryCls,
    html,
    nContext,
    showGraphics,
    hasGraphics,
    ltr,
):
    nType = nContext.nType
    cls = nContext.cls
    contCls = cls["container"]
    hlCls = nContext.hlCls
    hlStyle = nContext.hlStyle
    chunks = nContext.chunks
    label0 = label.get("", None)
    labelB = label.get("b", None)

    containerB = f'<div class="{contCls} {{}} {ltr} {boundaryCls} {hlCls}" {hlStyle}>'
    containerE = f"</div>"

    terminalCls = "trm"
    material = featurePart
    if labelB is not None:
        trm = terminalCls
        html.append(f"{containerB.format(trm)}{labelB}{material}{containerE}")
    if label0 is not None:
        trm = "" if chunks else terminalCls
        html.append(f"{containerB.format(trm)}{label0}{material}")

    if showGraphics and nType in hasGraphics:
        html.append(app.getGraphics(n, nType, outer))

    return (containerB, containerE)


def _doPrettyWrapPost(label, featurePart, html, containerB, containerE):
    label0 = label.get("", None)
    labelE = label.get("e", None)

    if label0 is not None:
        html.append(containerE)
    if labelE is not None:
        html.append(f"{containerB}{labelE} {featurePart}{containerE}")


def _doPrettyNode(
    app, dContext, oContext, nContext, n, outer, first, last, level, nodePlain
):
    api = app.api
    L = api.L
    E = api.E

    aContext = app.context
    lexTypes = aContext.lexTypes
    lexMap = aContext.lexMap

    textCls = nContext.textCls

    nType = nContext.nType
    cls = nContext.cls
    hlCls = nContext.hlCls
    hlStyle = nContext.hlStyle
    descend = nContext.descend
    isBaseNonSlot = nContext.isBaseNonSlot
    chunks = nContext.chunks
    nodePart = nContext.nodePart

    labelHlCls = ""
    labelHlStyle = ""

    if isBaseNonSlot:
        heading = nodePlain
    else:
        labelHlCls = hlCls
        labelHlStyle = hlStyle
        heading = getText(
            app,
            True,
            n,
            nType,
            outer,
            first,
            last,
            level,
            "",
            descend,
            dContext=dContext,
        )

    heading = f'<span class="{textCls}">{heading}</span>' if heading else ""

    featurePart = _getFeatures(app, dContext, n, nType)

    if nType in lexTypes:
        slots = E.oslots.s(n)
        extremeOccs = (slots[0],) if len(slots) == 1 else (slots[0], slots[-1])
        linkOccs = " - ".join(app.webLink(lo, _asString=True) for lo in extremeOccs)
        featurePart += f'<div class="occs">{linkOccs}</div>'
    if nType in lexMap:
        lx = L.u(n, otype=lexMap[nType])
        if lx:
            heading = app.webLink(lx[0], heading, _asString=True)

    label = {}
    for x in ("", "b", "e"):
        key = f"label{x}"
        if key in cls:
            val = cls[key]
            terminalCls = "trm" if x or not chunks else ""
            sep = " " if nodePart and heading else ""
            material = f"{nodePart}{sep}{heading}" if nodePart or heading else ""
            label[x] = (
                f'<div class="{val} {terminalCls} {labelHlCls}" {labelHlStyle}>'
                f"{material}</div>"
                if material
                else ""
            )

    return (label, featurePart)


def _prepareDisplay(
    app, isPretty, dContext, oContext, n, slots, outer, done=set(), called={},
):
    api = app.api
    F = api.F
    T = api.T
    slotType = F.otype.slotType
    nType = F.otype.v(n)

    aContext = app.context
    levelCls = aContext.levelCls
    noChildren = aContext.noChildren
    prettyCustom = aContext.prettyCustom
    lexTypes = aContext.lexTypes
    styles = aContext.styles

    fmt = dContext.fmt
    baseTypes = dContext.baseTypes
    _setSubBaseTypes(aContext, dContext, slotType)

    highlights = dContext.highlights

    descendType = T.formats.get(fmt, slotType)
    bottomTypes = baseTypes if isPretty else {descendType}

    isSlot = nType == slotType

    isBaseNonSlot = nType != slotType and nType in baseTypes

    (chunks, chunkBoundaries) = (
        ((), {})
        if isSlot
        or nType in bottomTypes
        or nType in lexTypes
        or (not isPretty and nType in noChildren)
        else _getChildren(
            app, isPretty, dContext, oContext, n, nType, slots, called, done
        )
    )

    (hlCls, hlStyle) = getHlAtt(app, n, highlights, baseTypes, not isPretty)

    isSlotOrDescend = isSlot or nType == descendType
    descend = False if descendType == slotType else None

    nodePart = _getNodePart(
        app, isPretty, dContext, n, nType, isSlot, outer, hlCls != ""
    )
    cls = {}
    if isPretty:
        if nType in levelCls:
            cls.update(levelCls[nType])
        if nType in prettyCustom:
            prettyCustom[nType](app, n, nType, cls)

    textCls = styles.get(nType, oContext.textCls)

    return NodeContext(
        slotType,
        nType,
        isSlot,
        isSlotOrDescend,
        descend,
        isBaseNonSlot,
        chunks,
        chunkBoundaries,
        textCls,
        hlCls,
        hlStyle,
        nodePart,
        cls,
    )


def _depthExceeded(level):
    if level > LIMIT_DISPLAY_DEPTH:
        console("DISPLAY: maximal depth exceeded: {LIMIT_DISPLAY_DEPTH}", error=True)
        return True
    return False


def _note(
    app,
    isPretty,
    oContext,
    n,
    nType,
    slots,
    first,
    last,
    level,
    contributes,
    *labels,
    **info,
):
    if not oContext.explain:
        return
    block = QUAD * level
    kindRep = "pretty" if isPretty else "plain"
    labelRep = " ".join(str(lab) for lab in labels)
    slotsRep = "{" + ",".join(str(s) for s in sorted(slots)) + "}"
    console(
        f"{block}<{level}>{kindRep}({nType} {n} {slotsRep}): {labelRep}", error=True
    )
    if contributes is not None:
        console(f"{block}<{level}> * {contributes}", error=True)

    for (k, v) in info.items():
        if k == "chunks":
            _noteFmt(app, level, v, info.get("chunkBoundaries", {}))
        elif k == "chunkBoundaries":
            continue
        else:
            console(f"{block}<{level}>      {k:<10} = {repr(v)}", error=True)


def _noteFmt(app, level, chunks, chunkBoundaries):
    fOtypev = app.api.F.otype.v

    block = QUAD * level
    for ch in chunks:
        boundaryCls = chunkBoundaries.get(ch, "")
        (n, slots) = ch
        nType = n if type(n) is str else fOtypev(n)
        slotsRep = "{" + ",".join(str(s) for s in sorted(slots)) + "}"
        console(
            f"{block}<{level}> / {nType} {n} cls='{boundaryCls}' {slotsRep}",
            error=True,
        )


def _setSubBaseTypes(aContext, dContext, slotType):
    descendantType = aContext.descendantType
    baseTypes = dContext.baseTypes

    subBaseTypes = set()

    if baseTypes and baseTypes != {slotType}:
        for bt in baseTypes:
            if bt in descendantType:
                subBaseTypes |= descendantType[bt]
    dContext.subBaseTypes = subBaseTypes - baseTypes


def _doPassage(dContext, i):
    withPassage = dContext.withPassage
    return withPassage is not True and withPassage and i + 1 in withPassage


def _getPassage(app, isPretty, dContext, oContext, n):
    withPassage = dContext.withPassage

    if not withPassage:
        return ""

    passage = app.webLink(n, _asString=True)
    return f'<span class="section ltr">{passage}{NB}</span>'


def _getTextCls(app, fmt):
    aContext = app.context
    formatCls = aContext.formatCls
    defaultClsOrig = aContext.defaultClsOrig

    return formatCls.get(fmt or DEFAULT_FORMAT, defaultClsOrig)


def _getLtr(app, dContext):
    aContext = app.context
    direction = aContext.direction

    fmt = dContext.fmt or DEFAULT_FORMAT

    return (
        "rtl"
        if direction == "rtl" and (f"{ORIG}-" in fmt or f"-{ORIG}" in fmt)
        else ("" if direction == "ltr" else "ltr")
    )


def _getBigType(app, dContext, nType):
    api = app.api
    T = api.T
    N = api.N

    sectionTypeSet = T.sectionTypeSet
    structureTypeSet = T.structureTypeSet
    otypeRank = N.otypeRank

    full = dContext.full
    condenseType = dContext.condenseType

    isBig = False
    if not full:
        if sectionTypeSet and nType in sectionTypeSet | structureTypeSet:
            if condenseType is None or otypeRank[nType] > otypeRank[condenseType]:
                isBig = True
        elif condenseType is not None and otypeRank[nType] > otypeRank[condenseType]:
            isBig = True
    return isBig


def _getChildren(app, isPretty, dContext, oContext, n, nType, slots, called, done):
    api = app.api
    L = api.L
    F = api.F
    E = api.E
    slotType = F.otype.slotType
    fOtypev = F.otype.v
    eOslots = E.oslots.s

    aContext = app.context
    verseTypes = aContext.verseTypes
    descendantType = aContext.descendantType
    isHidden = aContext.isHidden
    baseTypes = dContext.baseTypes
    subBaseTypes = dContext.subBaseTypes
    showHidden = dContext.showHidden
    childrenCustom = aContext.childrenCustom
    showVerseInTuple = aContext.showVerseInTuple

    inTuple = oContext.inTuple
    substrate = slots - done
    ltr = oContext.ltr

    full = dContext.full

    isBigType = (
        inTuple
        if not isPretty and nType in verseTypes and not showVerseInTuple
        else _getBigType(app, dContext, nType)
    )

    if isBigType and not full:
        children = ()
    elif nType in descendantType:
        myDescendantType = descendantType[nType]
        children = tuple(
            c
            for c in L.i(n, otype=myDescendantType)
            if fOtypev(c) != nType or not slots <= frozenset(eOslots(c))
        )
        if nType in childrenCustom:
            (condition, method, add) = childrenCustom[nType]
            if condition(n):
                others = method(n)
                if add:
                    children += others
                else:
                    children = others

            children = set(children) - {n}
    else:
        children = L.i(n)
    if isPretty and baseTypes and baseTypes != {slotType}:
        refSet = set(children)
        children = tuple(
            ch
            for ch in children
            if (fOtypev(ch) not in subBaseTypes)
            and not (set(L.u(ch, otype=baseTypes)) & refSet)
        )
    if not showHidden:
        toHide = isHidden - baseTypes
        children = tuple(ch for ch in children if fOtypev(ch) not in toHide)

    return chunkify(
        app, ltr, ((n, eOslots(n)) for n in children), substrate, called,
    )


def chunkify(app, ltr, protoChunks, substrate, called):
    """Divides and filters nodes into contiguous chunks.

    Only nodes are retained that have slots in a given set of slots,
    and for those nodes, all slots outside that set will be removed.

    Moreover, if a chunk is member of the set `called`, it will be excluded.

    Parameters
    ----------
    ltr: string
        Writing direction of the corpus

    protoChunks: iterable of tuple (int, tuple)
        A proto chunk is a 2-tuple: a node and the tuple of its slots
        in canonical ordering.

    substrate: set of int
        Set of slots that acts as a substrate: we are only interested in nodes
        insofar they occupy these slots.
        If there are gaps in the substrate, they will be added as a chunk with node
        `None`.

    called: dict
        A mapping of nodes to the slots in the chunk with which they are in progress.
        We skip chunks whose slots are already called before.

    Returns
    -------
    2-tuple of set, dict
        The first part is the set of real chunks (n, slots) of the nodes
        where the slots are contiguous frozen sets of slots in so far as they are part
        of the substrate.

        The second part is a dict, where the real chunks are keys, and the values
        are pairs of boundary types:

        `lno` `rno`
        : no left resp. right boundary

        `ln` `rn`
        : left resp. right node boundary

        `lc` `rc`
        : left resp.right chunk  boundary

    Notes
    -----
    The real chunks are returned as a tuple in the canonical order.

    Node and chunk boundaries are indicated if they occur within the substrate.
    A node boundary is typically a left or right solid border of a box.
    A chunk boundary is typically a left or right dotted border of a box.

    If a boundary occurs at a slot which is not in the substrate, the box of that
    chunk does not have corresponding left or right border.

    See Also
    --------
    tf.core.nodes: canonical ordering
    """

    api = app.api
    N = api.N
    sortKeyChunk = N.sortKeyChunk

    startCls = "r" if ltr == "rtl" else "l"
    endCls = "l" if ltr == "rtl" else "r"

    chunks = set()
    boundaries = {}

    for (n, slots) in protoChunks:
        ranges = list(rangesFromList(slots))
        nR = len(ranges) - 1
        for (i, (b, e)) in enumerate(ranges):
            protoChunkSlots = frozenset(range(b, e + 1)) & substrate
            if not protoChunkSlots:
                continue
            substrateRanges = rangesFromList(sorted(protoChunkSlots))
            for (bS, eS) in substrateRanges:
                chunkSlots = frozenset(range(bS, eS + 1))
                if n in called and chunkSlots <= called[n]:
                    continue
                boundaryL = f"{startCls}no" if bS != b else "" if i == 0 else startCls
                boundaryR = f"{endCls}no" if eS != e else "" if i == nR else endCls
                chunkKey = (n, chunkSlots)
                chunks.add(chunkKey)
                boundaries[chunkKey] = f"{boundaryL} {boundaryR}"
    sortedChunks = sorted(chunks, key=sortKeyChunk)
    gaps = set()
    covered = set()
    for (n, slots) in sortedChunks:
        covered |= slots
    coveredRanges = rangesFromSet(covered)
    prevEnd = None
    for (b, e) in coveredRanges:
        if prevEnd is not None and b != prevEnd + 1:
            gsKey = (GAP_START, frozenset([prevEnd]))
            geKey = (GAP_END, frozenset([b]))
            gaps.add(gsKey)
            gaps.add(geKey)
            boundaries[gsKey] = "g" + startCls
            boundaries[geKey] = "g" + endCls
        prevEnd = e
    sortedChunks = sorted(sortedChunks + list(gaps), key=sortKeyChunk)
    return (sortedChunks, boundaries)


def _getNodePart(app, isPretty, dContext, n, nType, isSlot, outer, isHl):
    _browse = app._browse

    Fs = app.api.Fs

    aContext = app.context
    lineNumberFeature = aContext.lineNumberFeature
    allowInfo = isPretty or outer is None or outer or isHl

    withNodes = dContext.withNodes and outer is not None
    withTypes = dContext.withTypes and outer is not None
    prettyTypes = dContext.prettyTypes and outer is not None
    lineNumbers = dContext.lineNumbers and outer is not None

    num = ""
    if withNodes and allowInfo:
        num = n

    ntp = ""
    if (withTypes or isPretty and prettyTypes) and not isSlot and allowInfo:
        ntp = nType

    line = ""
    if lineNumbers and allowInfo:
        feat = lineNumberFeature.get(nType, None)
        if feat:
            line = Fs(feat).v(n)
        if line:
            line = f"@{line}" if line else ""

    elemb = 'a href="#"' if _browse else "span"
    eleme = "a" if _browse else "span"
    sep = ":" if ntp and num else ""

    return (
        f'<{elemb} class="nd">{ntp}{sep}{num}{line}</{eleme}>'
        if ntp or num or line
        else ""
    )


def _getFeatures(app, dContext, n, nType):
    """Feature fetcher.

    Helper for `pretty` that wraps the requested features and their values for
    *node* in HTML for pretty display.
    """

    api = app.api
    L = api.L
    Fs = api.Fs

    aContext = app.context
    featuresBare = aContext.featuresBare
    features = aContext.features

    dFeatures = dContext.features
    dFeaturesIndirect = dContext.featuresIndirect
    queryFeatures = dContext.queryFeatures
    standardFeatures = dContext.standardFeatures
    suppress = dContext.suppress
    noneValues = dContext.noneValues

    (theseFeatures, indirect) = features.get(nType, ((), {}))
    (theseFeaturesBare, indirectBare) = featuresBare.get(nType, ((), {}))

    # a feature can be nType:feature
    # do a L.u(n, otype=nType)[0] and take the feature from there

    givenFeatureSet = set(theseFeatures) | set(theseFeaturesBare)
    xFeatures = tuple(
        f for f in dFeatures if not standardFeatures or f not in givenFeatureSet
    )
    featureList = tuple(theseFeaturesBare + theseFeatures) + xFeatures
    bFeatures = len(theseFeaturesBare)
    nbFeatures = len(theseFeaturesBare) + len(theseFeatures)

    featurePart = ""

    if standardFeatures or queryFeatures:
        for (i, name) in enumerate(featureList):
            if name not in suppress:
                fsName = Fs(name)
                if fsName is None:
                    continue
                fsNamev = fsName.v

                value = None
                if (
                    name in dFeaturesIndirect
                    or name in indirectBare
                    or name in indirect
                ):
                    refType = (
                        dFeaturesIndirect[name]
                        if name in dFeaturesIndirect
                        else indirectBare[name]
                        if name in indirectBare
                        else indirect[name]
                    )
                    refNode = L.u(n, otype=refType)
                    refNode = refNode[0] if refNode else None
                else:
                    refNode = n
                if refNode is not None:
                    value = fsNamev(refNode)

                value = None if value in noneValues else htmlEsc(value or "")
                if value is not None:
                    value = value.replace("\n", "<br/>")
                    isBare = i < bFeatures
                    isExtra = i >= nbFeatures
                    if (
                        isExtra
                        and not queryFeatures
                        or not isExtra
                        and not standardFeatures
                    ):
                        continue
                    nameRep = "" if isBare else f'<span class="f">{name}=</span>'
                    titleRep = f'title="{name}"' if isBare else ""
                    xCls = "xft" if isExtra else ""
                    featurePart += (
                        f'<span class="{name.lower()} {xCls}" {titleRep}>'
                        f"{nameRep}{value}</span>"
                    )
    if not featurePart:
        return ""

    return f"<div class='features'>{featurePart}</div>"


def _getRefMember(app, tup, dContext):
    api = app.api
    N = api.N
    otypeRank = N.otypeRank
    fOtypev = api.F.otype.v

    minRank = None
    minN = None
    for n in tup:
        nType = fOtypev(n)
        rank = otypeRank[nType]
        if minRank is None or rank < minRank:
            minRank = rank
            minN = n
            if minRank == 0:
                break

    return (tup[0] if tup else None) if minN is None else minN
