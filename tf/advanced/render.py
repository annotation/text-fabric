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

import re
from textwrap import dedent

from .helpers import htmlSafe, NB, dh
from .highlight import getEdgeHlAtt
from .unravel import _unravel
from ..core.helpers import NBSP, TO_SYM, FROM_SYM, htmlEsc, flattenToSet


def render(app, isPretty, n, _inTuple, _asString, explain, **options):
    """Renders a node, in plain or pretty mode.

    We take care that when a node has graphics, and the node is split into several
    chunks / fragments, the graphics only occurs on the first fragment.
    """

    graphicsFetched = set()
    inNb = app.inNb
    display = app.display

    if not display.check("pretty" if isPretty else "plain", options):
        return ""

    _browse = app._browse

    dContext = display.distill(options)

    if isPretty:
        tupleFeatures = dContext.tupleFeatures
        extraFeatures = dContext.extraFeatures
        multiFeatures = dContext.multiFeatures
        queryFeatures = dContext.queryFeatures

        dContext.set(
            "features",
            sorted(
                flattenToSet(extraFeatures[0])
                | (flattenToSet(tupleFeatures) if queryFeatures else set())
            ),
        )
        dContext.set("featuresIndirect", extraFeatures[1])
        if multiFeatures:
            api = app.api
            Fall = api.Fall
            Eall = api.Eall
            dContext.set(
                "featuresAll", tuple(Fall(warp=False)) + tuple(Eall(warp=False))
            )

    tree = _unravel(app, isPretty, dContext, n, _inTuple=_inTuple, explain=explain)
    (chunk, info, subTrees) = tree
    settings = info.settings

    passage = _getPassage(isPretty, info, n)

    html = []

    for subTree in subTrees:
        _render(isPretty, subTree, True, True, 0, passage, html, graphicsFetched)

    rep = "".join(html)
    ltr = settings.ltr

    elem = "span" if _inTuple else "div"
    ubd = " ubd" if _inTuple else ""
    kindRep = "pr-mode" if isPretty else "pl-mode"
    result = (
        f"""{passage}<{elem} class="{ltr} children {kindRep}">{rep}</{elem}>"""
        if isPretty
        else f"""<{elem} class="{ltr}{ubd} {kindRep}">{passage}{rep}</{elem}>"""
    )

    if _browse or _asString:
        return result
    dh(result, inNb=inNb)


def _render(
    isPretty,
    tree,
    first,
    last,
    level,
    passage,
    html,
    graphicsFetched,
    switched=False,
    _asString=False,
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
                False,
                tree,
                first,
                last,
                level,
                "",
                [],
                graphicsFetched,
                switched=True,
                _asString=True,
            )
        (label, featurePart) = _prettyTree(tree, outer, first, last, level, nodePlain)
        (containerB, containerE) = _prettyPre(
            tree,
            outer,
            label,
            featurePart,
            boundaryCls,
            html,
            graphicsFetched,
        )
        cls = props.cls
        childCls = cls["children"]

        if children and not isBaseNonSlot:
            html.append(f'<div class="{childCls} {ltr}">')
            after = props.after
    else:
        (contribB, contribE) = _plainPre(info, n, boundaryCls, outer, switched)
        contrib = _plainTree(
            contribB,
            contribE,
            tree,
            outer,
            first,
            last,
            level,
            boundaryCls,
            passage,
            graphicsFetched,
        )
        if contrib:
            html.append(contrib)

    lastCh = len(children) - 1

    if not ((isPretty and isBaseNonSlot) or (not isPretty and plainCustom)):
        for i, subTree in enumerate(children):
            thisFirst = first and i == 0
            thisLast = last and i == lastCh
            _render(
                isPretty,
                subTree,
                thisFirst,
                thisLast,
                level + 1,
                "",
                html,
                graphicsFetched,
            )
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


SPAN_RE = re.compile(r"^(<span\b[^>]*>)(.*)(</span>)$", re.S)


def _plainTree(
    contribB,
    contribE,
    tree,
    outer,
    first,
    last,
    level,
    boundaryCls,
    passage,
    graphicsFetched,
):
    (chunk, info, subTrees) = tree

    options = info.options
    isHtml = options.isHtml
    fmt = options.fmt
    showGraphics = options.showGraphics
    showMath = options.showMath

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

    if showGraphics and hasGraphics and n not in graphicsFetched:
        graphics = getGraphics(False, n, nType, outer)
        graphicsFetched.add(n)
    else:
        graphics = ""

    contrib = ""

    if plainCustom is not None:
        contrib = plainCustom(options, chunk, nType, outer)
        return contribB + contrib + graphics

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
            material = htmlSafe(text, isHtml, math=showMath)
            cb = f'<span class="{textCls}">'
            ce = "</span>"

            # a <br> in flex box has no effect
            # so we create a "breaking" span by setting the width to 100% and
            # the height to 0
            # See https://tobiasahlin.com/blog/flexbox-break-to-new-row/
            # We might have to dig one level of spans deeper if contribB is not empty
            if "<br>" in material:
                match = SPAN_RE.match(material)
                if match:
                    (start, content, end) = match.group(1, 2, 3)
                else:
                    (start, content, end) = ("", material, "")
                parts = content.split("<br>")
                joinerBase = '<span class="break"><br></span>'
                joiner = (
                    joinerBase
                    if contribB == ""
                    else f"{contribE}{joinerBase}{contribB}"
                )
                material = joiner.join(
                    f"{cb}{start}{part}{end}{ce}" for part in parts
                )
                contrib = material
            else:
                contrib = f"{cb}{material}{ce}"
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

    return contribB + contrib + graphics


# PRETTY LOW-LEVEL


def _prettyPre(tree, outer, label, featurePart, boundaryCls, html, graphicsFetched):
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

    if showGraphics and hasGraphics and n not in graphicsFetched:
        html.append(getGraphics(True, n, nType, outer))
        graphicsFetched.add(n)

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
    return (
        f"""<{wrap} class="tfsechead {ltr}">"""
        f"""<span class="ltr">{passage}</span></{wrap}>{sep}"""
    )


def _getNodePart(isPretty, info, n, outer, switched):
    options = info.options
    withNodes = options.withNodes and not switched
    withTypes = options.withTypes and not switched
    prettyTypes = options.prettyTypes and not switched
    lineNumbers = options.lineNumbers and not switched

    settings = info.settings
    browsing = settings.browsing
    fLookupMethod = settings.fLookupMethod

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
            line = fLookupMethod(lineNumberFeature).v(n)
        if line:
            line = f"@{line}" if line else ""

    elemb = 'a href="#"' if browsing else "span"
    eleme = "a" if browsing else "span"
    sep = ":" if ntp and num else ""

    return (
        f'<{elemb} class="nd">{ntp}{sep}{num}{line} </{eleme}>'
        if ntp or num or line
        else ""
    )


TO_SYM_WRAPPED = f'<span class="etfx">{TO_SYM}</span>'
FROM_SYM_WRAPPED = f'<span class="etfx">{FROM_SYM}</span>'


def _getEdge(e, n, kv, withNodes, right, highlights):
    (m, val) = kv if type(kv) is tuple else (kv, None)
    pair = (n, m) if right else (m, n)

    (hlCls, hlStyle) = getEdgeHlAtt(e, pair, highlights)

    nodeRep = f'<span class="nde">{m}</span>' if withNodes else ""
    valRep = "" if val is None else htmlEsc(val)
    plainValue = (
        f"{valRep}{TO_SYM_WRAPPED}{nodeRep}"
        if right
        else f"{nodeRep}{FROM_SYM_WRAPPED}{valRep}"
    )
    arrow = "right" if right else "left"
    sep = " " if hlCls else ""

    return dedent(
        f"""
        <span
            ef="{e}"
            nd="{n}"
            md="{m}"
            arrow="{arrow}"
            class="etf{sep}{hlCls}" {hlStyle}
        >{plainValue}</span>
        """
    )


def _getFeatures(info, n, nType):
    """Feature fetcher.

    Helper for `pretty` that wraps the requested features and their values for
    *node* in HTML for pretty display.
    """

    options = info.options
    dFeatures = options.features
    dFeaturesIndirect = options.featuresIndirect
    edgeFeatures = options.edgeFeatures
    forceEdges = options.forceEdges
    multiFeatures = options.multiFeatures

    if multiFeatures:
        featuresAll = options.featuresAll

    # queryFeatures = options.queryFeatures
    tupleFeatures = options.tupleFeatures
    standardFeatures = options.standardFeatures
    suppress = options.suppress
    noneValues = options.noneValues
    showMath = options.showMath
    withNodes = options.withNodes
    edgeHighlights = options.edgeHighlights

    settings = info.settings
    upMethod = settings.upMethod
    fLookupMethod = settings.fLookupMethod
    eLookupMethod = settings.eLookupMethod
    allEFeats = settings.allEFeats

    props = info.props
    (features, indirect) = props.features
    (featuresBare, indirectBare) = props.featuresBare

    if forceEdges:
        newDFeatures = []
        seen = set()
        for f in dFeatures + list(allEFeats):
            if f in allEFeats:
                if f in edgeFeatures:
                    if f not in seen:
                        newDFeatures.append(f)
                        seen.add(f)
                else:
                    continue
            else:
                newDFeatures.append(f)
        dFeatures = newDFeatures

    # a feature can be nType:feature
    # do a upMethod(n, otype=nType)[0] and take the feature from there

    givenFeatureSet = set(features) | set(featuresBare)
    xFeatures = tuple(
        f for f in dFeatures if not standardFeatures or f not in givenFeatureSet
    )
    featureList = tuple(featuresBare + features) + xFeatures
    if multiFeatures:
        featureList += featuresAll
    bFeatures = len(featuresBare)
    nbFeatures = len(featuresBare) + len(features)

    featurePart = ""

    # if standardFeatures or queryFeatures or multiFeatures or forceEdges:
    if standardFeatures or tupleFeatures or multiFeatures or forceEdges:
        seen = set()

        for i, name in enumerate(featureList):
            if name not in suppress and name not in seen:
                seen.add(name)

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

                value = None

                if refNode is not None:
                    if name in allEFeats:
                        esObj = eLookupMethod(name, warn=False)
                        valueF = esObj.f(refNode)
                        valueT = esObj.t(refNode)
                        eHighlights = (
                            None
                            if edgeHighlights is None
                            else edgeHighlights.get(name, None)
                        )
                        if len(valueF):
                            valueF = " ".join(
                                _getEdge(
                                    name, refNode, it, withNodes, True, eHighlights
                                )
                                for it in valueF
                            )
                        if len(valueT):
                            valueT = " ".join(
                                _getEdge(
                                    name, refNode, it, withNodes, False, eHighlights
                                )
                                for it in valueT
                            )
                        value = (
                            None
                            if not len(valueF) and not len(valueT)
                            else (valueT or "") + (valueF or "")
                        )
                    else:
                        fsObj = fLookupMethod(name, warn=False)
                        value = fsObj.v(refNode)
                        if value in noneValues:
                            value = None
                        else:
                            value = htmlEsc(value, math=showMath)

                if value is not None:
                    if name not in allEFeats:
                        value = value.replace("\n", "\\n<br>")
                        if value.endswith(" "):
                            value = value[0:-1] + NBSP
                    isBare = i < bFeatures
                    isExtra = i >= nbFeatures
                    if (
                        not multiFeatures
                        and not (isExtra and forceEdges and name in edgeFeatures)
                        and (
                            # (isExtra and not queryFeatures)
                            # isExtra
                            # or (
                            not isExtra
                            and (not standardFeatures and name not in dFeatures)
                            # )
                        )
                    ):
                        continue
                    nameRep = (
                        ""
                        if isBare
                        else (
                            (
                                f'<span class="e" edge="{name}" nd="{refNode}">'
                                f"{name}•</span>"
                            )
                            if name in allEFeats
                            else f'<span class="f">{name}=</span>'
                        )
                    )
                    titleRep = f'title="{name}"' if isBare else ""
                    xCls = "xft" if isExtra else ""
                    featurePart += (
                        f'<span class="{name.lower()} {xCls}" {titleRep}>'
                        f"{nameRep}{value}</span>"
                    )
    if not featurePart:
        return ""

    return f"""<div class="features">{featurePart}</div>"""
