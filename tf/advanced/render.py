"""
# Render

Rendering is the process of generating HTML for a node, taking into account
display options (`tf.advanced.options`) and app settings (`tf.advanced.settings`).

It is organized as an *unravel* step (`tf.advanced.unravel`),
that generates a tree of node fragments
followed by an HTML generating step, that generates HTML for a tree in a recursive way.

The *unravel* step retrieves all relevant settings and options and stores them
in the tree in such a way that the essential information for rendering a subtree
is readily available at the top of that subtree.

## Information shielding

The recursive render step does not have to consult the `app` object anymore,
because all information it needs from the `app` object is stored in the tree,
and all methods that need to be invoked on the `app` object are also accessible
directly from an attribute in the tree.
"""

from .helpers import htmlSafe, NB, dh
from .unravel import _unravel
from ..core.helpers import htmlEsc, flattenToSet


def render(app, isPretty, n, _inTuple, _asString, explain, **options):
    """Renders a node, in plain or pretty mode.
    """

    display = app.display

    if not display.check("pretty" if isPretty else "plain", options):
        return ""

    _browse = app._browse

    dContext = display.distill(options)
    if isPretty:
        tupleFeatures = dContext.tupleFeatures
        extraFeatures = dContext.extraFeatures

        dContext.set(
            "features",
            sorted(flattenToSet(extraFeatures[0]) | flattenToSet(tupleFeatures)),
        )
        dContext.set("featuresIndirect", extraFeatures[1])

    tree = _unravel(app, isPretty, dContext, n, _inTuple=_inTuple, explain=explain)
    (chunk, info, subTrees) = tree
    settings = info.settings

    passage = _getPassage(isPretty, info, n)

    html = []

    for subTree in subTrees:
        _render(isPretty, subTree, True, True, 0, passage, html)

    rep = "".join(html)
    ltr = settings.ltr

    elem = "span" if _inTuple else "div"
    ubd = " ubd" if _inTuple else ""
    result = (
        f"""{passage}<{elem} class="{ltr} children">{rep}</{elem}>"""
        if isPretty
        else f"""<{elem} class="{ltr}{ubd}">{passage}{rep}</{elem}>"""
    )

    if _browse or _asString:
        return result
    dh(result)


def _render(
    isPretty, tree, first, last, level, passage, html, switched=False, _asString=False
):
    outer = level == 0
    (chunk, info, children) = tree
    (n, (b, e)) = chunk
    settings = info.settings
    props = info.props
    boundaryCls = info.boundaryCls

    ltr = settings.ltr
    isBaseNonSlot = props.isBaseNonSlot
    plainCustom = props.plainCustom

    if isPretty:
        nodePlain = None
        if isBaseNonSlot:
            nodePlain = _render(
                False, tree, first, last, level, "", [], switched=True, _asString=True
            )
        (label, featurePart) = _prettyTree(tree, outer, first, last, level, nodePlain)
        (containerB, containerE) = _prettyPre(
            tree, outer, label, featurePart, boundaryCls, html,
        )
        cls = props.cls
        childCls = cls["children"]

        if children and not isBaseNonSlot:
            html.append(f'<div class="{childCls} {ltr}">')
            after = props.after
    else:
        (contribB, contribE) = _plainPre(info, n, boundaryCls, outer, switched)
        contrib = _plainTree(tree, outer, first, last, level, boundaryCls, passage)
        if contribB:
            html.append(contribB)
        if contrib:
            html.append(contrib)

    lastCh = len(children) - 1

    if not ((isPretty and isBaseNonSlot) or (not isPretty and plainCustom)):
        for (i, subTree) in enumerate(children):
            thisFirst = first and i == 0
            thisLast = last and i == lastCh
            _render(isPretty, subTree, thisFirst, thisLast, level + 1, "", html)
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


def _plainPre(info, n, boundaryCls, outer, switched):
    isPretty = False
    options = info.options
    plainGaps = options.plainGaps

    settings = info.settings
    ltr = settings.ltr

    props = info.props
    hlCls = props.hlCls[isPretty]
    hlStyle = props.hlStyle[isPretty]

    nodePart = _getNodePart(False, info, n, outer, switched)

    boundary = boundaryCls if plainGaps else ""
    theHlCls = "" if switched else hlCls
    theHlStyle = "" if switched else hlStyle
    if boundary in {"r", "l"} or theHlCls or theHlStyle or nodePart or switched:
        clses = f"plain {ltr} {boundary} {theHlCls}"
        contribB = f'<span class="{clses}" {theHlStyle}>'
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


def _plainTree(
    tree, outer, first, last, level, boundaryCls, passage,
):
    (chunk, info, subTrees) = tree

    options = info.options
    isHtml = options.isHtml
    fmt = options.fmt
    showGraphics = options.showGraphics

    settings = info.settings
    textMethod = settings.textMethod
    ltr = settings.ltr
    getText = settings.getText
    getGraphics = settings.getGraphics

    props = info.props
    hasGraphics = props.hasGraphics
    textCls = props.textCls
    nType = props.nType
    isSlotOrDescend = props.isSlotOrDescend
    descend = props.descend
    plainCustom = props.plainCustom

    chunk = tree[0]
    n = chunk[0]

    graphics = (
        getGraphics(False, n, nType, outer) if showGraphics and hasGraphics else ""
    )
    contrib = ""

    if plainCustom is not None:
        contrib = plainCustom(options, chunk, nType, outer)
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
            False,
            n,
            nType,
            outer,
            first,
            last,
            level,
            passage if outer else "",
            descend,
            options=options,
        )
        if tplFilled:
            contrib = f'<span class="{textCls} {ltr}">{tplFilled}</span>'

    return contrib + graphics


# PRETTY LOW-LEVEL


def _prettyPre(tree, outer, label, featurePart, boundaryCls, html):
    isPretty = True
    (chunk, info, subTrees) = tree
    n = chunk[0]

    options = info.options
    showGraphics = options.showGraphics

    settings = info.settings
    getGraphics = settings.getGraphics
    ltr = settings.ltr

    props = info.props
    hasGraphics = props.hasGraphics
    nType = props.nType
    cls = props.cls
    isBaseNonSlot = props.isBaseNonSlot
    hlCls = props.hlCls[isPretty]
    hlStyle = props.hlStyle[isPretty]

    contCls = cls["container"]
    label0 = label.get("", None)
    labelB = label.get("b", None)

    n = tree[0][0]

    containerB = f'<div class="{contCls} {{}} {ltr} {boundaryCls} {hlCls}" {hlStyle}>'
    containerE = "</div>"

    terminalCls = "trm"
    material = featurePart
    if labelB is not None:
        trm = terminalCls
        html.append(f"{containerB.format(trm)}{labelB}{material}{containerE}")
    if label0 is not None:
        trm = terminalCls if isBaseNonSlot or not subTrees else ""
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


def _prettyTree(tree, outer, first, last, level, nodePlain):
    isPretty = True
    (chunk, info, subTrees) = tree
    n = chunk[0]

    options = info.options

    settings = info.settings
    upMethod = settings.upMethod
    slotsMethod = settings.slotsMethod
    webLink = settings.webLink
    getText = settings.getText

    props = info.props
    nType = props.nType
    cls = props.cls
    hlCls = props.hlCls[isPretty]
    hlStyle = props.hlStyle[isPretty]
    descend = props.descend
    isBaseNonSlot = props.isBaseNonSlot
    isLexType = props.isLexType
    lexType = props.lexType
    textCls = props.textCls

    nodePart = _getNodePart(True, info, n, outer, False)
    labelHlCls = hlCls
    labelHlStyle = hlStyle

    if isBaseNonSlot:
        heading = nodePlain
    else:
        heading = getText(
            True, n, nType, outer, first, last, level, "", descend, options=options
        )

    heading = f'<span class="{textCls}">{heading}</span>' if heading else ""

    featurePart = _getFeatures(info, n, nType)

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
            terminalCls = "trm" if x or isBaseNonSlot or not subTrees else ""
            sep = " " if nodePart and heading else ""
            material = f"{nodePart}{sep}{heading}" if nodePart or heading else ""
            label[x] = (
                f'<div class="{val} {terminalCls} {labelHlCls}" {labelHlStyle}>'
                f"{material}</div>"
                if material
                else ""
            )

    return (label, featurePart)


def _getPassage(isPretty, info, n):
    options = info.options
    withPassage = options.withPassage

    settings = info.settings
    webLink = settings.webLink

    if not withPassage:
        return ""

    ltr = settings.ltr

    passage = webLink(n, _asString=True)
    wrap = "div" if isPretty else "span"
    sep = "" if isPretty else NB * 2
    return f'<{wrap} class="tfsechead {ltr}">{passage}</{wrap}>{sep}'


def _getNodePart(isPretty, info, n, outer, switched):
    options = info.options
    withNodes = options.withNodes and not switched
    withTypes = options.withTypes and not switched
    prettyTypes = options.prettyTypes and not switched
    lineNumbers = options.lineNumbers and not switched

    settings = info.settings
    browsing = settings.browsing
    lookupMethod = settings.lookupMethod

    props = info.props
    nType = props.nType
    isSlot = props.isSlot
    hlCls = props.hlCls[isPretty]
    lineNumberFeature = props.lineNumberFeature

    allowInfo = isPretty or (outer and not switched) or hlCls != ""

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


def _getFeatures(info, n, nType):
    """Feature fetcher.

    Helper for `pretty` that wraps the requested features and their values for
    *node* in HTML for pretty display.
    """

    options = info.options
    dFeatures = options.features
    dFeaturesIndirect = options.featuresIndirect
    queryFeatures = options.queryFeatures
    standardFeatures = options.standardFeatures
    suppress = options.suppress
    noneValues = options.noneValues

    settings = info.settings
    upMethod = settings.upMethod
    lookupMethod = settings.lookupMethod

    props = info.props
    (features, indirect) = props.features
    (featuresBare, indirectBare) = props.featuresBare

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
