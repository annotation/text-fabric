import os
import types
from collections import namedtuple

from ..parameters import DOWNLOADS
from ..core.text import DEFAULT_FORMAT
from ..core.helpers import mdEsc, htmlEsc, flattenToSet
from .find import findAppConfig
from .helpers import configure, tupleEnum, RESULT, dh, NB
from .condense import condense, condenseSet
from .highlight import getTupleHighlights, getHlAtt
from .displaysettings import DisplaySettings
from .settings import DEFAULT_CLS

LIMIT_SHOW = 100
LIMIT_TABLE = 2000

FONT_BASE = (
    "https://github.com/annotation/text-fabric/blob/master/tf/server/static/fonts"
)

CSS_FONT_API = f"""
@font-face {{{{
  font-family: "{{fontName}}";
  src:
    local("{{font}}"),
    url("{FONT_BASE}/{{fontw}}?raw=true");
}}}}
"""

ORIG = "orig"

OuterContext = namedtuple(
    "OuterContext",
    """
    ltr
    textCls
    firstSlot
    lastSlot
    inTuple
""".strip().split(),
)

NodeContext = namedtuple(
    "NodeContext",
    """
    slotType
    nType
    isSlot
    isSlotOrDescend
    descend
    isBaseNonSlot
    children
    boundaryCls
    hlCls
    hlStyle
    nodePart
    cls
    myStart
    myEnd
""".strip().split(),
)


def displayApi(app, silent):
    if app.isCompatible:
        app.export = types.MethodType(export, app)
        app.table = types.MethodType(table, app)
        app.plainTuple = types.MethodType(plainTuple, app)
        app.plain = types.MethodType(plain, app)
        app.show = types.MethodType(show, app)
        app.prettyTuple = types.MethodType(prettyTuple, app)
        app.pretty = types.MethodType(pretty, app)
        app.loadCss = types.MethodType(loadCss, app)
        app.displaySetup = types.MethodType(displaySetup, app)
        app.displayReset = types.MethodType(displayReset, app)
    else:
        return

    app.display = DisplaySettings(app)
    if not app._browse:
        app.loadCss()


def displaySetup(app, **options):
    display = app.display

    display.setup(**options)


def displayReset(app, *options):
    display = app.display

    display.reset(*options)
    if not app._browse:
        app.loadCss()


def export(app, tuples, toDir=None, toFile="results.tsv", **options):
    display = app.display

    if not display.check("table", options):
        return ""

    dContext = display.get(options)
    fmt = dContext.fmt
    condenseType = dContext.condenseType
    tupleFeatures = dContext.tupleFeatures

    if toDir is None:
        toDir = os.path.expanduser(DOWNLOADS)
        if not os.path.exists(toDir):
            os.makedirs(toDir, exist_ok=True)
    toPath = f"{toDir}/{toFile}"

    resultsX = getResultsX(app, tuples, tupleFeatures, condenseType, fmt=fmt,)

    with open(toPath, "w", encoding="utf_16_le") as fh:
        fh.write(
            "\ufeff"
            + "".join(
                ("\t".join("" if t is None else str(t) for t in tup) + "\n")
                for tup in resultsX
            )
        )


# PLAIN and FRIENDS


def table(app, tuples, _asString=False, **options):
    display = app.display

    if not display.check("table", options):
        return ""

    api = app.api
    F = api.F
    fOtype = F.otype.v

    dContext = display.get(options)
    end = dContext.end
    start = dContext.start
    withPassage = dContext.withPassage
    condensed = dContext.condensed
    condenseType = dContext.condenseType

    item = condenseType if condensed else RESULT

    if condensed:
        tuples = condense(api, tuples, condenseType, multiple=True)

    passageHead = '</th><th class="tf">p' if withPassage is True else ""

    html = []
    one = True

    for (i, tup) in tupleEnum(tuples, start, end, LIMIT_TABLE, item):
        if one:
            heads = '</th><th class="tf">'.join(fOtype(n) for n in tup)
            html.append(
                f"""
<tr class="tf">
  <th class="tf">n{passageHead}</th>
  <th class="tf">{heads}</th>
</tr>
"""
            )
            one = False
        html.append(
            plainTuple(
                app,
                tup,
                i,
                item=item,
                position=None,
                opened=False,
                _asString=True,
                **options,
            )
        )
    html = "<table>" + "\n".join(html) + "</table>"
    if _asString:
        return html
    dh(html)


def plainTuple(
    app, tup, seq, item=RESULT, position=None, opened=False, _asString=False, **options
):
    display = app.display

    if not display.check("plainTuple", options):
        return ""

    api = app.api
    F = api.F
    T = api.T
    fOtype = F.otype.v
    _browse = app._browse

    dContext = display.get(options)
    condenseType = dContext.condenseType
    colorMap = dContext.colorMap
    highlights = dContext.highlights
    withPassage = dContext.withPassage

    if withPassage is True:
        passageNode = getRefMember(app, tup, dContext)
        passageRef = (
            ""
            if passageNode is None
            else app._sectionLink(passageNode)
            if _browse
            else app.webLink(passageNode, _asString=True)
        )
        passageRef = f"""<span class="psg ltr">{passageRef}</span>"""
    else:
        passageRef = ""

    newOptions = display.consume(options, "withPassage")
    newOptionsH = display.consume(options, "withPassage", "highlights")

    highlights = getTupleHighlights(api, tup, highlights, colorMap, condenseType)

    if _browse:
        prettyRep = (
            prettyTuple(app, tup, seq, withPassage=False, **newOptions)
            if opened
            else ""
        )
        current = "focus" if seq == position else ""
        attOpen = "open " if opened else ""
        tupSeq = ",".join(str(n) for n in tup)
        if withPassage is True:
            sParts = T.sectionFromNode(passageNode, fillup=True)
            passageAtt = " ".join(
                f'sec{i}="{sParts[i] if i < len(sParts) else ""}"' for i in range(3)
            )
        else:
            passageAtt = ""

        plainRep = "".join(
            f"""<span>{mdEsc(app.plain(
                    n,
                    _inTuple=True,
                    withPassage=doPassage(dContext, i),
                    highlights=highlights,
                    **newOptionsH,
                  ))
                }</span>"""
            for (i, n) in enumerate(tup)
        )
        html = f"""
  <details class="pretty dtrow {current}" seq="{seq}" {attOpen}>
    <summary>
      <a href="#" class="pq fa fa-solar-panel fa-xs"
        title="show in context" {passageAtt}></a>
      <a href="#" class="sq" tup="{tupSeq}">{seq}</a>
      {passageRef} {plainRep}
    </summary>
    <div class="pretty">{prettyRep}</div>
  </details>
"""
        return html

    html = [str(seq)]
    if withPassage is True:
        html.append(passageRef)
    for (i, n) in enumerate(tup):
        html.append(
            app.plain(
                n,
                _inTuple=True,
                _asString=True,
                withPassage=doPassage(dContext, i),
                highlights=highlights,
                **newOptionsH,
            )
        )
    html = (
        f"""<tr class="tf"><td class="tf">"""
        f"""{'</td><td class="tf">'.join(html)}"""
        """</td></tr>"""
    )
    if _asString:
        return html

    passageHead = '</th><th class="tf">p' if withPassage is True else ""
    head = (
        f"""<tr class="tf"><th class="tf">n{passageHead}</th><th class="tf">"""
        f"""{'</th><th class="tf">'.join(fOtype(n) for n in tup)}"""
        f"""</th></tr>"""
    )
    html = f"""<table>{head}{"".join(html)}</table>"""

    dh(html)


def plain(app, n, _inTuple=False, _asString=False, **options):
    display = app.display

    if not display.check("plain", options):
        return ""

    ac = app.context
    textFormats = ac.textFormats
    formatCls = ac.formatCls

    dContext = display.get(options)
    fmt = dContext.fmt

    dContext.isHtml = fmt in textFormats

    _browse = app._browse
    api = app.api

    ltr = getLtr(app, dContext)
    textCls = formatCls[fmt].lower()
    (firstSlot, lastSlot) = getBoundary(api, n)

    oContext = OuterContext(ltr, textCls, firstSlot, lastSlot, _inTuple)
    passage = getPassage(app, True, dContext, oContext, n)
    rep = _doPlain(app, dContext, oContext, n, True, [])

    if _browse or _asString:
        return rep
    dh(passage + rep)


def _doPlain(app, dContext, oContext, n, outer, html, done=set()):
    done.add(n)

    nContext = _prepareDisplay(app, False, dContext, oContext, n, outer)
    if not nContext:
        return

    ltr = oContext.ltr

    hlCls = nContext.hlCls
    hlStyle = nContext.hlStyle
    boundaryCls = nContext.boundaryCls
    nodePart = nContext.nodePart
    children = nContext.children

    outerCls = f"outer" if outer else ""

    didSuper = False

    sNodeInfo = getSuper(app, oContext, nContext, n, outer)
    if sNodeInfo:
        (soContext, sn, sStart, sEnd) = sNodeInfo
        snContext = _prepareDisplay(app, False, dContext, soContext, n, False)
        shlCls = snContext.hlCls
        shlStyle = snContext.hlStyle
        snodePart = snContext.nodePart
        sboundaryCls = snContext.boundaryCls

        if snContext and shlCls:
            sClses = f"plain {sboundaryCls} {shlCls}"
            html.append(f'<span class="{sClses}" {shlStyle}>')
            if snodePart:
                html.append(snodePart)
            didSuper = True

    clses = f"plain {'' if didSuper else outerCls} {ltr} {boundaryCls} {hlCls}"
    html.append(f'<span class="{clses}" {hlStyle}>')

    if nodePart:
        html.append(nodePart)

    html.append(_doPlainNode(app, dContext, oContext, nContext, n, outer, done=done))

    for ch in children:
        _doPlain(app, dContext, oContext, ch, False, html, done=done)
    html.append("""</span>""")
    if didSuper:
        html.append("""</span>""")
    return "".join(html) if outer else None


def _doPlainNode(app, dContext, oContext, nContext, n, outer, done=set()):
    api = app.api
    T = api.T

    ac = app.context
    plainCustom = ac.plainCustom

    isHtml = dContext.isHtml
    fmt = dContext.fmt

    ltr = oContext.ltr
    textCls = oContext.textCls

    nType = nContext.nType
    isSlotOrDescend = nContext.isSlotOrDescend
    descend = nContext.descend

    if nType in plainCustom:
        method = plainCustom[nType]
        contrib = method(app, dContext, oContext, nContext, n, outer, done=done)
        return contrib
    if isSlotOrDescend:
        text = T.text(n, fmt=fmt, descend=descend)
        if not isHtml:
            text = htmlEsc(text)
        contrib = f'<span class="{textCls}">{text}</span>'
    else:
        (isText, tplFilled) = getText(app, n, nType, fmt=fmt, descend=descend)
        if isText and isHtml:
            tplFilled = htmlEsc(tplFilled)
        if contrib:
            contrib = f"""<span class="plain {ltr}">{tplFilled}</span>"""
    return contrib


# PRETTY and FRIENDS


def show(app, tuples, **options):
    display = app.display

    if not display.check("show", options):
        return ""

    dContext = display.get(options)
    end = dContext.end
    start = dContext.start
    condensed = dContext.condensed
    condenseType = dContext.condenseType

    api = app.api
    F = api.F

    item = condenseType if condensed else RESULT

    if condensed:
        tuples = condense(api, tuples, condenseType, multiple=True)

    for (i, tup) in tupleEnum(tuples, start, end, LIMIT_SHOW, item):
        item = F.otype.v(tup[0]) if condensed and condenseType else RESULT
        prettyTuple(
            app, tup, i, item=item, **options,
        )


def prettyTuple(app, tup, seq, item=RESULT, **options):
    display = app.display

    if not display.check("prettyTuple", options):
        return ""

    dContext = display.get(options)
    colorMap = dContext.colorMap
    highlights = dContext.highlights
    condenseType = dContext.condenseType
    condensed = dContext.condensed

    _browse = app._browse

    if len(tup) == 0:
        if _browse:
            return ""
        else:
            return

    api = app.api
    sortKey = api.sortKey

    containers = {tup[0]} if condensed else condenseSet(api, tup, condenseType)
    highlights = getTupleHighlights(api, tup, highlights, colorMap, condenseType)

    if not _browse:
        dh(f"<p><b>{item}</b> <i>{seq}</i></p>")
    if _browse:
        html = []
    for t in sorted(containers, key=sortKey):
        h = app.pretty(
            t, highlights=highlights, **display.consume(options, "highlights"),
        )
        if _browse:
            html.append(h)
    if _browse:
        return "".join(html)


def pretty(app, n, **options):
    display = app.display

    if not display.check("pretty", options):
        return ""

    _browse = app._browse

    ac = app.context
    textFormats = ac.textFormats
    formatCls = ac.formatCls

    dContext = display.get(options)
    condenseType = dContext.condenseType
    condensed = dContext.condensed
    tupleFeatures = dContext.tupleFeatures
    extraFeatures = dContext.extraFeatures
    fmt = dContext.fmt

    dContext.isHtml = fmt in textFormats
    dContext.features = sorted(
        flattenToSet(extraFeatures) | flattenToSet(tupleFeatures)
    )

    api = app.api
    F = api.F
    L = api.L
    otypeRank = api.otypeRank

    ltr = getLtr(app, dContext)
    textCls = formatCls[fmt].lower()
    (firstSlot, lastSlot) = getBoundary(api, n)

    oContext = OuterContext(ltr, textCls, firstSlot, lastSlot, False)
    passage = getPassage(app, False, dContext, oContext, n)

    containerN = None

    nType = F.otype.v(n)
    if condensed and condenseType:
        if nType == condenseType:
            containerN = n
        elif otypeRank[nType] < otypeRank[condenseType]:
            ups = L.u(n, otype=condenseType)
            if ups:
                containerN = ups[0]

    (firstSlot, lastSlot) = (
        getBoundary(api, n)
        if not condensed or not condenseType
        else (None, None)
        if containerN is None
        else getBoundary(api, containerN)
    )

    html = []

    _doPretty(app, dContext, oContext, n, True, html)

    htmlStr = passage + "".join(html)
    if _browse:
        return htmlStr
    dh(htmlStr)


def _doPretty(app, dContext, oContext, n, outer, html, seen=set()):
    if n in seen:
        return

    if outer:
        seen = set()

    seen.add(n)

    nContext = _prepareDisplay(app, True, dContext, oContext, n, outer)
    if not nContext:
        return

    ac = app.context
    afterChild = ac.afterChild
    hasGraphics = ac.hasGraphics

    graphics = dContext.graphics

    ltr = oContext.ltr

    nType = nContext.nType
    isBaseNonSlot = nContext.isBaseNonSlot
    nType = nContext.nType
    cls = nContext.cls
    hlCls = nContext.hlCls
    hlStyle = nContext.hlStyle
    boundaryCls = nContext.boundaryCls
    children = nContext.children

    nodePlain = None
    if isBaseNonSlot:
        done = set()
        nodePlain = _doPlain(app, dContext, oContext, n, True, [], done=done)
        seen |= done

    didSuper = False

    sNodeInfo = getSuper(app, oContext, nContext, n, outer)
    if sNodeInfo:
        (soContext, sn, sStart, sEnd) = sNodeInfo
        snContext = _prepareDisplay(app, True, dContext, soContext, sn, False)
        if snContext:
            scls = snContext.cls
            shlCls = snContext.hlCls
            shlStyle = snContext.hlStyle
            sboundaryCls = snContext.boundaryCls
            sisBaseNonSlot = snContext.isBaseNonSlot

            sNodePlain = None
            if sisBaseNonSlot:
                sNodePlain = _doPlain(app, dContext, soContext, sn, True, [])
            (sLabel, sFeaturePart) = _doPrettyNode(
                app, dContext, soContext, snContext, sn, False, sNodePlain
            )
            html.append(
                f"""
<div class="{scls['container']} {ltr} {sboundaryCls} {shlCls}" {shlStyle}>
{sLabel}{sFeaturePart}
<div class="{scls['children']} {ltr}">
"""
            )
            didSuper = True

    (label, featurePart) = _doPrettyNode(
        app, dContext, oContext, nContext, n, outer, nodePlain
    )

    containerB = (
        f"""<div class="{cls['container']} {{}} {ltr}"""
        f""" {boundaryCls} {hlCls}" {hlStyle}>"""
    )
    containerE = f"""</div>"""

    terminalCls = "trm"
    if "b" in label:
        trm = terminalCls
        html.append(f"{containerB.format(trm)}{label['b']} {featurePart}{containerE}")
    if "" in label:
        trm = "" if children else terminalCls
        html.append(f"{containerB.format(trm)}{label['']} {featurePart}")

    if graphics and nType in hasGraphics:
        html.append(app.getGraphics(n, nType, outer))

    if children:
        html.append(f"""<div class="{cls['children']} {ltr}">""")

    for ch in children:
        if ch in seen:
            continue
        _doPretty(app, dContext, oContext, ch, False, html, seen=seen)
        after = afterChild.get(nType, None)
        if after:
            html.append(after(ch))

    if children:
        html.append("""</div>""")

    if "" in label:
        html.append(f"{containerE}")
    if "e" in label:
        html.append(f"{containerB}{label['e']} {featurePart}{containerE}")

    if didSuper:
        html.append("""</div></div>""")
    return "".join(html) if outer else None


def _doPrettyNode(app, dContext, oContext, nContext, n, outer, nodePlain):
    api = app.api
    L = api.L

    ac = app.context
    lexTypes = ac.lexTypes
    lexMap = ac.lexMap

    isHtml = dContext.isHtml
    fmt = dContext.fmt

    textCls = oContext.textCls

    nType = nContext.nType
    cls = nContext.cls
    hlCls = nContext.hlCls
    descend = nContext.descend
    isBaseNonSlot = nContext.isBaseNonSlot
    children = nContext.children
    nodePart = nContext.nodePart

    isText = False

    labelHlCls = ""

    if isBaseNonSlot:
        heading = nodePlain
    else:
        labelHlCls = hlCls
        (isText, heading) = getText(app, n, nType, fmt=fmt, descend=descend)
        if isText and isHtml:
            heading = htmlEsc(heading)

    textCls = textCls if isText else DEFAULT_CLS
    heading = f'<span class="{textCls}">{heading}</span>'

    featurePart = getFeatures(app, dContext, n, nType)

    if nType in lexTypes:
        extremeOccs = getBoundary(api, n)
        linkOccs = " - ".join(app.webLink(lo, _asString=True) for lo in extremeOccs)
        featurePart += f'<div class="occs">{linkOccs}</div>'
    if nType in lexMap:
        lx = L.u(n, otype=lexMap[nType])
        if lx:
            heading = app.webLink(lx[0], heading, _asString=True)

    if featurePart:
        featurePart = f"""<div class="meta">{featurePart}</div>"""

    label = {}
    for x in ("", "b", "e"):
        key = f"label{x}"
        if key in cls:
            val = cls[key]
            terminalCls = "trm" if x or not children else ""
            label[x] = (
                (
                    f"""<div class="{val} {terminalCls} {labelHlCls}">"""
                    f"""{nodePart} {heading}</div>"""
                )
                if heading or nodePart
                else ""
            )

    return (label, featurePart)


def _prepareDisplay(app, isPretty, dContext, oContext, n, outer):
    api = app.api
    F = api.F
    T = api.T
    slotType = F.otype.slotType
    nType = F.otype.v(n)

    ac = app.context
    levelCls = ac.levelCls
    noChildren = ac.noChildren
    prettyCustom = ac.prettyCustom

    fmt = dContext.fmt
    baseType = dContext.baseType
    highlights = dContext.highlights

    descendType = T.formats.get(fmt, slotType)
    bottomType = baseType if isPretty else descendType

    isSlot = nType == slotType

    children = (
        ()
        if isSlot or nType == bottomType or (not isPretty and nType in noChildren)
        else getChildren(app, isPretty, dContext, oContext, n, nType)
    )

    boundaryResult = getBoundaryResult(api, oContext, n)
    if boundaryResult is None:
        return False

    (boundaryCls, myStart, myEnd) = boundaryResult

    (hlCls, hlStyle) = getHlAtt(app, n, highlights, baseType, not isPretty)

    isSlotOrDescend = isSlot or nType == descendType
    descend = False if descendType == slotType else None
    isBaseNonSlot = nType == baseType and not isSlot

    nodePart = getNodePart(app, isPretty, dContext, n, nType, isSlot, outer, hlCls)
    cls = {}
    if isPretty:
        if nType in levelCls:
            cls.update(levelCls[nType])
        if nType in prettyCustom:
            prettyCustom[nType](app, n, nType, cls)

    return NodeContext(
        slotType,
        nType,
        isSlot,
        isSlotOrDescend,
        descend,
        isBaseNonSlot,
        children,
        boundaryCls,
        hlCls,
        hlStyle,
        nodePart,
        cls,
        myStart,
        myEnd,
    )


def doPassage(dContext, i):
    withPassage = dContext.withPassage

    return withPassage is not True and withPassage and i + 1 in withPassage


def getPassage(app, isPretty, dContext, oContext, n):
    withPassage = dContext.withPassage

    if not withPassage:
        return ""

    passage = app.webLink(n, _asString=True)
    return f"""<span class="psg ltr">{passage}{NB}</span>"""


def getText(app, n, nType, tpl, feats, fmt=None, descend=None):
    T = app.api.T
    sectionTypeSet = T.sectionTypeSet
    structureTypeSet = T.structureTypeSet

    ac = app.context
    templates = ac.templates

    tpl = templates.get(nType, "")

    tplFilled = (
        (
            app.sectionStrFromNode(n)
            if nType in sectionTypeSet
            else T.structureStrFromNode(n)
            if nType in structureTypeSet
            else T.text(n, fmt=fmt, descend=descend)
        )
        if tpl is True
        else tpl.format(**{feat: getValue(app, n, nType, feat) for feat in feats})
    )
    return (tpl is True, tplFilled)


def getSuperBounds(oContext, nContext):
    firstSlot = oContext.firstSlot
    lastSlot = oContext.lastSlot

    myStart = nContext.myStart
    myEnd = nContext.myEnd

    return oContext._replace(
        firstSlot=max((firstSlot, myStart)), lastSlot=min((lastSlot, myEnd)),
    )


def getValue(app, n, nType, feat):
    Fs = app.api.Fs

    ac = app.context
    transform = ac.transform

    val = Fs(feat).v(n)
    modifier = transform.get(nType, {}).get(feat, None)
    return modifier(val) if modifier else val


def getLtr(app, dContext):
    ac = app.context
    writingDir = ac.writingDir

    fmt = dContext.fmt or DEFAULT_FORMAT

    return (
        "rtl"
        if writingDir == "rtl" and (f"{ORIG}-" in fmt or f"-{ORIG}" in fmt)
        else ("" if writingDir == "ltr" else "ltr")
    )


def getBigType(app, dContext, oContext, nType, otypeRank):
    api = app.api
    T = api.T

    sectionTypeSet = T.sectionTypeSet
    structureTypeSet = T.structureTypeSet

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


def getBoundaryResult(api, oContext, n):
    boundaryCls = ""
    myStart = None
    myEnd = None
    firstSlot = oContext.firstSlot
    lastSlot = oContext.lastSlot

    (myStart, myEnd) = getBoundary(api, n)

    if firstSlot is not None:
        if myEnd < firstSlot:
            return None
        if myStart < firstSlot:
            boundaryCls += " rno"
    if lastSlot is not None:
        if myStart > lastSlot:
            return None
        if myEnd > lastSlot:
            boundaryCls += " lno"
    return (boundaryCls, myStart, myEnd)


def getSuper(app, oContext, nContext, n, outer):
    api = app.api
    L = api.L

    ac = app.context
    hasSuper = ac.hasSuper
    superTypes = ac.superTypes

    nType = nContext.nType

    if not outer and nType not in superTypes and nType in hasSuper:
        sn = L.u(n, otype=nType)[0]
        soContext = getSuperBounds(oContext, nContext)
        return (soContext, sn, *getBoundary(api, sn))

    return None


def getChildren(app, isPretty, dContext, oContext, n, nType):
    api = app.api
    F = api.F
    L = api.L
    otypeRank = api.otypeRank
    sortNodes = api.sortNodes
    slotType = F.otype.slotType

    ac = app.context
    verseTypes = ac.verseTypes
    childType = ac.childType
    childrenCustom = ac.childrenCustom

    inTuple = oContext.inTuple

    full = dContext.full

    isBigType = (
        inTuple
        if not isPretty and nType in verseTypes
        else getBigType(app, dContext, oContext, nType, otypeRank)
    )

    if isBigType and not full:
        children = ()
    elif nType in childType:
        childType = childType[nType]
        children = L.d(n, otype=childType)
        if nType in childrenCustom:
            (condition, method, add) = childrenCustom[nType]
            if condition(n):
                others = method(n)
                if add:
                    children += others
                else:
                    children = others

        children = set(children) - {n}

        if nType in verseTypes:
            (thisFirstSlot, thisLastSlot) = getBoundary(api, n)
            boundaryChildren = set()
            for boundary in (thisFirstSlot, thisLastSlot):
                bchs = L.u(boundary, otype=childType)
                if bchs:
                    boundaryChildren.add(bchs[0])
            children |= boundaryChildren

        children = sortNodes(children - {n})
    else:
        children = L.d(n, otype=slotType)
    return children


def getNodePart(app, isPretty, dContext, n, nType, isSlot, outer, highlight):
    _browse = app._browse

    Fs = app.api.Fs

    ac = app.context
    lineNumberFeature = ac.lineNumberFeature
    allowInfo = isPretty or outer or highlight

    withNodes = dContext.withNodes
    withTypes = dContext.withTypes
    prettyTypes = dContext.prettyTypes
    lineNumbers = dContext.lineNumbers

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


# COMPOSE TABLES FOR CSV EXPORT


def getResultsX(app, results, features, condenseType, fmt=None):
    api = app.api
    F = api.F
    Fs = api.Fs
    T = api.T
    fOtype = F.otype.v
    otypeRank = api.otypeRank
    sectionTypeSet = T.sectionTypeSet

    ac = app.context
    noDescendTypes = ac.descendTypes

    sectionDepth = len(sectionTypeSet)
    if len(results) == 0:
        return ()
    firstResult = results[0]
    nTuple = len(firstResult)
    refColumns = [
        i for (i, n) in enumerate(firstResult) if fOtype(n) not in sectionTypeSet
    ]
    refColumn = refColumns[0] if refColumns else nTuple - 1
    header = ["R"] + [f"S{i}" for i in range(1, sectionDepth + 1)]
    emptyA = []

    featureDict = {i: tuple(f.split()) if type(f) is str else f for (i, f) in features}

    def withText(nodeType):
        return (
            condenseType is None
            and nodeType not in sectionTypeSet
            or otypeRank[nodeType] <= otypeRank[condenseType]
        )

    noDescendTypes = noDescendTypes

    for j in range(nTuple):
        i = j + 1
        n = firstResult[j]
        nType = fOtype(n)
        header.extend([f"NODE{i}", f"TYPE{i}"])
        if withText(nType):
            header.append(f"TEXT{i}")
        header.extend(f"{feature}{i}" for feature in featureDict.get(j, emptyA))
    rows = [tuple(header)]
    for (rm, r) in enumerate(results):
        rn = rm + 1
        row = [rn]
        refN = r[refColumn]
        sParts = T.sectionFromNode(refN)
        nParts = len(sParts)
        section = sParts + ((None,) * (sectionDepth - nParts))
        row.extend(section)
        for j in range(nTuple):
            n = r[j]
            nType = fOtype(n)
            row.extend((n, nType))
            if withText(nType):
                text = T.text(n, fmt=fmt, descend=nType not in noDescendTypes)
                row.append(text)
            row.extend(Fs(feature).v(n) for feature in featureDict.get(j, emptyA))
        rows.append(tuple(row))
    return tuple(rows)


def getBoundary(api, n):
    F = api.F
    fOtype = F.otype.v
    slotType = F.otype.slotType
    if fOtype(n) == slotType:
        return (n, n)
    E = api.E
    maxSlot = F.otype.maxSlot
    slots = E.oslots.data[n - maxSlot - 1]
    return (slots[0], slots[-1])


def getFeatures(app, dContext, n, nType):
    api = app.api
    L = api.L
    Fs = api.Fs

    ac = app.context
    featuresBare = ac.featuresBare
    features = ac.features

    dFeatures = dContext.features
    showFeatures = dContext.showFeatures
    suppress = dContext.suppress
    noneValues = dContext.noneValues

    (theseFeatures, indirect) = features.get(nType, ((), {}))
    (theseFeaturesBare, indirectBare) = featuresBare.get(nType, ((), {}))

    # a feature can be nType:feature
    # do a L.u(n, otype=nType)[0] and take the feature from there

    givenFeatureSet = set(theseFeatures) | set(theseFeaturesBare)
    xFeatures = tuple(f for f in dFeatures if f not in givenFeatureSet)
    featureList = tuple(theseFeaturesBare + theseFeatures) + xFeatures
    bFeatures = len(theseFeaturesBare)
    nbFeatures = len(theseFeaturesBare) + len(theseFeatures)

    featurePart = ""

    if showFeatures:
        for (i, name) in enumerate(featureList):
            if name not in suppress:
                fsName = Fs(name)
                if fsName is None:
                    continue
                fsNamev = fsName.v
                value = (
                    fsNamev(L.u(n, otype=indirect[name])[0])
                    if name in indirect
                    else fsNamev(n)
                )
                value = None if value in noneValues else htmlEsc(value or "")
                if value is not None:
                    value = value.replace("\n", "<br/>")
                    isBare = i < bFeatures
                    isExtra = i >= nbFeatures
                    nameRep = "" if isBare else f'<span class="f">{name}=</span>'
                    xCls = "xft" if isExtra else ""
                    featurePart += (
                        f'<span class="{name.lower()} {xCls}">{nameRep}{value}</span>'
                    )
    if not featurePart:
        return ""

    return f"<div class='features'>{featurePart}</div>"


def loadCss(app, reload=False):
    """
  The CSS is looked up and then loaded into a notebook if we are not
  running in the TF browser,
  else the CSS is returned.

  With reload=True, the app-specific display.css will be read again from disk
  """
    _browse = app._browse
    css = app.css

    if _browse:
        return css

    appName = app.appName
    appPath = app.appPath
    version = app.version

    ac = app.context
    font = ac.font
    fontw = ac.fontw
    fontName = ac.fontName

    if reload:

        cfg = findAppConfig(appName, appPath)
        if version is not None:
            cfg.setdefault('provenanceSpec', {})['version'] = version
        app.setAppSpecs(cfg)

    cssPath = (
        f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}"
        "/server/static"
    )
    cssFiles = ("display.css", "highlight.css")
    genericCss = ""
    for cssFile in cssFiles:
        with open(f"{cssPath}/{cssFile}", encoding="utf8") as fh:
            genericCss += fh.read()

    cssFont = (
        ""
        if fontName is None
        else CSS_FONT_API.format(fontName=fontName, font=font, fontw=fontw)
    )
    tableCss = """
tr.tf, td.tf, th.tf {
  text-align: left ! important;
}

"""
    dh(f"<style>{cssFont + tableCss + genericCss + css}</style>")


def getRefMember(app, tup, dContext):
    api = app.api
    T = api.T
    sectionTypeSet = T.sectionTypeSet

    condensed = dContext.condensed

    return (
        None
        if not tup or any(n in sectionTypeSet for n in tup)
        else tup[0]
        if condensed
        else tup[0]
    )
