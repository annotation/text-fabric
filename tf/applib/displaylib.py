from collections import namedtuple

from .helpers import getText, htmlSafe
from ..core.text import DEFAULT_FORMAT
from ..core.helpers import htmlEsc
from .settings import ORIG

QUAD = "  "

__pdoc__ = {}


class OuterContext:
    """Common properties during plain() and pretty().
    """

    pass


OuterContext = namedtuple(  # noqa: F811
    "OuterContext",
    """
    slotType
    ltr
    fmt
    textCls
""".strip().split(),
)
__pdoc__["OuterContext.slotType"] = "The slot type of the dataset."
__pdoc__["OuterContext.ltr"] = "writing direction."
__pdoc__["OuterContext.fmt"] = "the currently selected text format."
__pdoc__["OuterContext.textCls"] = "Css class for full text."


class NodeContext:
    """Node properties during plain() or pretty().
    """

    pass


NodeContext = namedtuple(  # noqa: F811
    "NodeContext",
    """
    nType
    isSlot
    isSlotOrDescend
    descend
    isBaseNonSlot
    textCls
    hlCls
    hlStyle
    cls
    hasGraphics
    after
""".strip().split(),
)
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
)
__pdoc__["NodeContext.textCls"] = "The text Css class of the current node."
__pdoc__["NodeContext.hlCls"] = "The highlight Css class of the current node."
__pdoc__["NodeContext.hlStyle"] = "The highlight style attribute of the current node."
__pdoc__["NodeContext.cls"] = (
    "A dict of several classes for the display of the node:"
    " for the container, the label, and the children of the node;"
    " might be set by prettyCustom"
)
__pdoc__["NodeContext.hasGraphics"] = "Whether this node type has graphics."
__pdoc__[
    "NodeContext.after"
] = "Whether the app defines a custom method to generate material after a child."


# RENDER and  FRIENDS


def _render(
    app,
    isPretty,
    tree,
    first,
    last,
    level,
    passage,
    html,
    switched=False,
    _asString=False,
):
    aContext = app.context

    outer = level == 0
    (chunk, info, children) = tree
    (n, (b, e)) = chunk
    dContext = info["dContext"]
    oContext = info["oContext"]
    nContext = info["nContext"]
    boundaryCls = info["boundaryCls"]

    plainCustom = aContext.plainCustom
    ltr = oContext.ltr
    nType = nContext.nType
    isBaseNonSlot = nContext.isBaseNonSlot

    custom = plainCustom and nType in plainCustom

    if isPretty:
        nodePlain = None
        if isBaseNonSlot:
            nodePlain = _render(
                app,
                False,
                tree,
                first,
                last,
                level,
                "",
                [],
                switched=True,
                _asString=True,
            )
        (label, featurePart) = _doPrettyNode(
            app,
            dContext,
            oContext,
            nContext,
            tree,
            outer,
            first,
            last,
            level,
            nodePlain,
        )
        (containerB, containerE) = _doPrettyWrapPre(
            app,
            tree,
            outer,
            label,
            featurePart,
            boundaryCls,
            html,
            dContext,
            nContext,
            ltr,
        )
        cls = nContext.cls
        childCls = cls["children"]

        if children and not isBaseNonSlot:
            html.append(f'<div class="{childCls} {ltr}">')
            after = nContext.after
    else:
        contrib = _doPlainNode(
            app,
            dContext,
            oContext,
            nContext,
            tree,
            outer,
            first,
            last,
            level,
            boundaryCls,
            passage,
        )
        _doPlainWrapPre(
            app, dContext, nContext, n, boundaryCls, outer, switched, ltr, html
        )
        html.append(contrib)

    lastCh = len(children) - 1

    if not ((isPretty and isBaseNonSlot) or (not isPretty and custom)):
        for (i, subTree) in enumerate(children):
            thisFirst = first and i == 0
            thisLast = last and i == lastCh
            _render(app, isPretty, subTree, thisFirst, thisLast, level + 1, "", html)
            if isPretty and after:
                html.append(after(subTree[0][0]))

    if isPretty:
        if children and not isBaseNonSlot:
            html.append("</div>")
        _doPrettyWrapPost(label, featurePart, html, containerB, containerE)
    else:
        _doPlainWrapPost(html)

    return "".join(html) if outer or _asString else None


# PLAIN LOW-LEVEL


def _doPlainWrapPre(
    app, dContext, nContext, n, boundaryCls, outer, switched, ltr, html
):
    plainGaps = dContext.plainGaps

    hlCls = nContext.hlCls
    hlStyle = nContext.hlStyle

    nodePart = _getNodePart(app, False, dContext, nContext, n, outer, switched)

    outerCls = f"outer" if outer else ""
    boundary = boundaryCls if plainGaps else ""
    clses = f"plain {outerCls} {ltr} {boundary} {hlCls}"
    html.append(f'<span class="{clses}" {hlStyle}>{nodePart}')


def _doPlainWrapPost(html):
    html.append("</span>")


def _doPlainNode(
    app,
    dContext,
    oContext,
    nContext,
    tree,
    outer,
    first,
    last,
    level,
    boundaryCls,
    passage,
):
    api = app.api
    T = api.T

    aContext = app.context
    plainCustom = aContext.plainCustom

    isHtml = dContext.isHtml
    fmt = dContext.fmt
    showGraphics = dContext.showGraphics

    ltr = oContext.ltr

    hasGraphics = nContext.hasGraphics
    textCls = nContext.textCls
    nType = nContext.nType
    isSlotOrDescend = nContext.isSlotOrDescend
    descend = nContext.descend

    chunk = tree[0]
    n = chunk[0]

    graphics = (
        app.getGraphics(False, n, nType, outer) if showGraphics and hasGraphics else ""
    )

    if nType in plainCustom:
        method = plainCustom[nType]
        contrib = method(app, dContext, chunk, nType, outer)
        return contrib + graphics

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

    return contrib + graphics


# PRETTY LOW-LEVEL


def _doPrettyWrapPre(
    app, tree, outer, label, featurePart, boundaryCls, html, dContext, nContext, ltr,
):
    showGraphics = dContext.showGraphics
    hasGraphics = nContext.hasGraphics
    nType = nContext.nType
    cls = nContext.cls
    isBaseNonSlot = nContext.isBaseNonSlot
    contCls = cls["container"]
    hlCls = nContext.hlCls
    hlStyle = nContext.hlStyle
    label0 = label.get("", None)
    labelB = label.get("b", None)

    n = tree[0][0]
    children = tree[2]

    containerB = f'<div class="{contCls} {{}} {ltr} {boundaryCls} {hlCls}" {hlStyle}>'
    containerE = f"</div>"

    terminalCls = "trm"
    material = featurePart
    if labelB is not None:
        trm = terminalCls
        html.append(f"{containerB.format(trm)}{labelB}{material}{containerE}")
    if label0 is not None:
        trm = terminalCls if isBaseNonSlot or not children else ""
        html.append(f"{containerB.format(trm)}{label0}{material}")

    if showGraphics and hasGraphics:
        html.append(app.getGraphics(True, n, nType, outer))

    return (containerB, containerE)


def _doPrettyWrapPost(label, featurePart, html, containerB, containerE):
    label0 = label.get("", None)
    labelE = label.get("e", None)

    if label0 is not None:
        html.append(containerE)
    if labelE is not None:
        html.append(f"{containerB}{labelE} {featurePart}{containerE}")


def _doPrettyNode(
    app, dContext, oContext, nContext, tree, outer, first, last, level, nodePlain
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

    n = tree[0][0]
    children = tree[2]

    nodePart = _getNodePart(app, True, dContext, nContext, n, outer, False)
    labelHlCls = hlCls
    labelHlStyle = hlStyle

    if isBaseNonSlot:
        heading = nodePlain
    else:
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
            terminalCls = "trm" if x or isBaseNonSlot or not children else ""
            sep = " " if nodePart and heading else ""
            material = f"{nodePart}{sep}{heading}" if nodePart or heading else ""
            label[x] = (
                f'<div class="{val} {terminalCls} {labelHlCls}" {labelHlStyle}>'
                f"{material}</div>"
                if material
                else ""
            )

    return (label, featurePart)


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


def _getPassage(app, dContext, oContext, n):
    withPassage = dContext.withPassage

    if not withPassage:
        return ""

    passage = app.webLink(n, _asString=True)
    return f'<span class="section ltr">{passage}</span>'


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


def _getBigType(app, isPretty, dContext, nType):
    api = app.api
    T = api.T
    N = api.N

    sectionTypeSet = T.sectionTypeSet
    structureTypeSet = T.structureTypeSet
    otypeRank = N.otypeRank

    aContext = app.context
    bigTypes = aContext.bigTypes
    isBigOverride = nType in bigTypes

    full = dContext.full
    condenseType = dContext.condenseType

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


def _getNodePart(app, isPretty, dContext, nContext, n, outer, switched):
    _browse = app._browse
    nType = nContext.nType
    isSlot = nContext.isSlot
    hlCls = nContext.hlCls

    Fs = app.api.Fs

    aContext = app.context
    lineNumberFeature = aContext.lineNumberFeature
    allowInfo = isPretty or (outer and not switched) or hlCls != ""

    withNodes = dContext.withNodes and not switched
    withTypes = dContext.withTypes and not switched
    prettyTypes = dContext.prettyTypes and not switched
    lineNumbers = dContext.lineNumbers and not switched

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
