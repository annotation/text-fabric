from collections import namedtuple

from .helpers import getText, htmlSafe, NB
from ..core.helpers import htmlEsc

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
    textClsDefault
    textMethod
    upMethod
    slotsMethod
    lookupMethod
    browsing
    webLink
    getGraphics
""".strip().split(),
)
__pdoc__["OuterContext.slotType"] = "The slot type of the dataset."
__pdoc__["OuterContext.ltr"] = "writing direction."
__pdoc__["OuterContext.fmt"] = "the currently selected text format."
__pdoc__["OuterContext.textClsDefault"] = "Default css class for full text."
__pdoc__["OuterContext.textMethod"] = (
    "Method to print text of a node according to a text format: "
    "`tf.core.text.Text.text`"
)
__pdoc__[
    "OuterContext.upMethod"
] = "Method to move from a node to its first embedder: `tf.core.locality.Locality.u`"
__pdoc__[
    "OuterContext.slotsMethod"
] = "Method to get the slots of a node: `tf.core.oslotsfeature.OslotsFeature.s`"
__pdoc__[
    "OuterContext.lookupMethod"
] = "Method to get the value of a node feature: `tf.core.api.Api.Fs`"
__pdoc__[
    "OuterContext.browsing"
] = "whether we work for the Text-Fabric browser or for a Jupyter notebook"
__pdoc__[
    "OuterContext.webLink"
] = "Method to produce a web link to a node: `tf.applib.links.webLink`"
__pdoc__["OuterContext.getGraphics"] = (
    "Method to fetch graphics for a node. App-dependent."
    "See `tf.applib.settings` under **graphics**."
)


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
__pdoc__["NodeContext.isLexType"] = "Whether nodes of type are lexemes."
__pdoc__[
    "NodeContext.lexType"
] = "If nodes of this type have lexemes in another type, this is that type."
__pdoc__[
    "NodeContext.lineNumberFeature"
] = "Feature with source line numbers of nodes of this type."
__pdoc__[
    "NodeContext.featuresBare"
] = "Features to display in the labels of pretty displays without their names"
__pdoc__[
    "NodeContext.features"
] = "Features to display in the labels of pretty displays with their names"
__pdoc__["NodeContext.textCls"] = "The text Css class of the current node."
__pdoc__["NodeContext.hlCls"] = "The highlight Css class of the current node."
__pdoc__["NodeContext.hlStyle"] = "The highlight style attribute of the current node."
__pdoc__["NodeContext.cls"] = (
    "A dict of several classes for the display of the node:"
    " for the container, the label, and the children of the node;"
    " might be set by prettyCustom"
)
__pdoc__["NodeContext.hasGraphics"] = "Whether this node type has graphics."
__pdoc__["NodeContext.after"] = (
    "Whether the app defines a custom method to generate material after a child."
    "It is a dict keyed by node type whose values are the custom methods."
)
__pdoc__["NodeContext.plainCustom"] = (
    "Whether the app defines a custom method to plain displays."
)


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
    outer = level == 0
    (chunk, info, children) = tree
    (n, (b, e)) = chunk
    dContext = info["dContext"]
    oContext = info["oContext"]
    nContext = info["nContext"]
    boundaryCls = info["boundaryCls"]

    ltr = oContext.ltr
    isBaseNonSlot = nContext.isBaseNonSlot
    plainCustom = nContext.plainCustom

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
        (label, featurePart) = _prettyNode(
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
        (containerB, containerE) = _prettyPre(
            app,
            tree,
            outer,
            label,
            featurePart,
            boundaryCls,
            html,
            dContext,
            oContext,
            nContext,
            ltr,
        )
        cls = nContext.cls
        childCls = cls["children"]

        if children and not isBaseNonSlot:
            html.append(f'<div class="{childCls} {ltr}">')
            after = nContext.after
    else:
        (contribB, contribE) = _plainPre(
            app, dContext, oContext, nContext, n, boundaryCls, outer, switched, ltr
        )
        contrib = _plainNode(
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
        if contribB:
            html.append(contribB)
        if contrib:
            html.append(contrib)

    lastCh = len(children) - 1

    if not ((isPretty and isBaseNonSlot) or (not isPretty and plainCustom)):
        for (i, subTree) in enumerate(children):
            thisFirst = first and i == 0
            thisLast = last and i == lastCh
            _render(app, isPretty, subTree, thisFirst, thisLast, level + 1, "", html)
            if isPretty and after:
                html.append(after(subTree[0][0]))

    if isPretty:
        if children and not isBaseNonSlot:
            html.append("</div>")
        _prettyPost(label, featurePart, html, containerB, containerE)
    else:
        _plainPost(contribE, html)

    return "".join(html) if outer or _asString else None


# PLAIN LOW-LEVEL


def _plainPre(app, dContext, oContext, nContext, n, boundaryCls, outer, switched, ltr):
    plainGaps = dContext.plainGaps

    hlCls = nContext.hlCls
    hlStyle = nContext.hlStyle

    nodePart = _getNodePart(
        app, False, dContext, oContext, nContext, n, outer, switched
    )

    boundary = boundaryCls if plainGaps else ""
    if boundary in {"r", "l"} or hlCls or hlStyle or nodePart:
        clses = f"plain {ltr} {boundary} {hlCls}"
        contribB = f'<span class="{clses}" {hlStyle}>'
        contribE = "</span>"
    else:
        contribB = ""
        contribE = ""
    if nodePart:
        contribB += nodePart
    return (contribB, contribE)


def _plainPost(contribE, html):
    if contribE:
        html.append(contribE)


def _plainNode(
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
    isHtml = dContext.isHtml
    fmt = dContext.fmt
    showGraphics = dContext.showGraphics

    textMethod = oContext.textMethod
    ltr = oContext.ltr
    getGraphics = oContext.getGraphics

    hasGraphics = nContext.hasGraphics
    textCls = nContext.textCls
    nType = nContext.nType
    isSlotOrDescend = nContext.isSlotOrDescend
    descend = nContext.descend
    plainCustom = nContext.plainCustom

    chunk = tree[0]
    n = chunk[0]

    graphics = (
        getGraphics(False, n, nType, outer) if showGraphics and hasGraphics else ""
    )
    contrib = ""

    if plainCustom is not None:
        contrib = plainCustom(app, dContext, chunk, nType, outer)
        return contrib + graphics

    if isSlotOrDescend:
        text = textMethod(
            n,
            fmt=fmt,
            descend=descend,
            outer=outer,
            first=first,
            last=last,
            level=level,
        )
        if text:
            contrib = f'<span class="{textCls}">{htmlSafe(text, isHtml)}</span>'
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
        if tplFilled:
            contrib = f'<span class="{textCls} {ltr}">{tplFilled}</span>'

    return contrib + graphics


# PRETTY LOW-LEVEL


def _prettyPre(
    app,
    tree,
    outer,
    label,
    featurePart,
    boundaryCls,
    html,
    dContext,
    oContext,
    nContext,
    ltr,
):
    getGraphics = oContext.getGraphics

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
        html.append(getGraphics(True, n, nType, outer))

    return (containerB, containerE)


def _prettyPost(label, featurePart, html, containerB, containerE):
    label0 = label.get("", None)
    labelE = label.get("e", None)

    if label0 is not None:
        html.append(containerE)
    if labelE is not None:
        html.append(f"{containerB}{labelE} {featurePart}{containerE}")


def _prettyNode(
    app, dContext, oContext, nContext, tree, outer, first, last, level, nodePlain
):

    upMethod = oContext.upMethod
    slotsMethod = oContext.slotsMethod
    webLink = oContext.webLink

    nType = nContext.nType
    cls = nContext.cls
    hlCls = nContext.hlCls
    hlStyle = nContext.hlStyle
    descend = nContext.descend
    isBaseNonSlot = nContext.isBaseNonSlot
    isLexType = nContext.isLexType
    lexType = nContext.lexType
    textCls = nContext.textCls

    n = tree[0][0]
    children = tree[2]

    nodePart = _getNodePart(app, True, dContext, oContext, nContext, n, outer, False)
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

    featurePart = _getFeatures(app, dContext, oContext, nContext, n, nType)

    if isLexType:
        slots = slotsMethod(n)
        extremeOccs = (slots[0],) if len(slots) == 1 else (slots[0], slots[-1])
        linkOccs = " - ".join(webLink(lo, _asString=True) for lo in extremeOccs)
        featurePart += f'<div class="occs">{linkOccs}</div>'
    if lexType:
        lx = upMethod(n, otype=lexType)
        if lx:
            heading = webLink(lx[0], heading, _asString=True)

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


def _doPassage(dContext, i):
    withPassage = dContext.withPassage
    return withPassage is not True and withPassage and i + 1 in withPassage


def _getPassage(app, isPretty, dContext, oContext, n):
    withPassage = dContext.withPassage

    webLink = oContext.webLink

    if not withPassage:
        return ""

    ltr = oContext.ltr

    passage = webLink(n, _asString=True)
    wrap = "div" if isPretty else "span"
    sep = "" if isPretty else NB * 2
    return f'<{wrap} class="section {ltr}">{passage}</{wrap}>{sep}'


def _getNodePart(app, isPretty, dContext, oContext, nContext, n, outer, switched):
    browsing = oContext.browsing
    lookupMethod = oContext.lookupMethod

    nType = nContext.nType
    isSlot = nContext.isSlot
    hlCls = nContext.hlCls
    lineNumberFeature = nContext.lineNumberFeature

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
        if lineNumberFeature:
            line = lookupMethod(lineNumberFeature).v(n)
        if line:
            line = f"@{line}" if line else ""

    elemb = 'a href="#"' if browsing else "span"
    eleme = "a" if browsing else "span"
    sep = ":" if ntp and num else ""

    return (
        f'<{elemb} class="nd">{ntp}{sep}{num}{line}</{eleme}>'
        if ntp or num or line
        else ""
    )


def _getFeatures(app, dContext, oContext, nContext, n, nType):
    """Feature fetcher.

    Helper for `pretty` that wraps the requested features and their values for
    *node* in HTML for pretty display.
    """

    upMethod = oContext.upMethod
    lookupMethod = oContext.lookupMethod

    dFeatures = dContext.features
    dFeaturesIndirect = dContext.featuresIndirect
    queryFeatures = dContext.queryFeatures
    standardFeatures = dContext.standardFeatures
    suppress = dContext.suppress
    noneValues = dContext.noneValues

    (features, indirect) = nContext.features
    (featuresBare, indirectBare) = nContext.featuresBare

    # a feature can be nType:feature
    # do a upMethod(n, otype=nType)[0] and take the feature from there

    givenFeatureSet = set(features) | set(featuresBare)
    xFeatures = tuple(
        f for f in dFeatures if not standardFeatures or f not in givenFeatureSet
    )
    featureList = tuple(featuresBare + features) + xFeatures
    bFeatures = len(featuresBare)
    nbFeatures = len(featuresBare) + len(features)

    featurePart = ""

    if standardFeatures or queryFeatures:
        for (i, name) in enumerate(featureList):
            if name not in suppress:
                fsName = lookupMethod(name)
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
                    refNode = upMethod(n, otype=refType)
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


def _getRefMember(otypeRank, fOtypev, tup, dContext):
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
