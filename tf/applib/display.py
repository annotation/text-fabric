import os
import re
import types
from collections import namedtuple

from ..parameters import DOWNLOADS
from ..core.helpers import mdEsc, htmlEsc, flattenToSet
from .app import findAppConfig
from .helpers import configure, RESULT, dh, NB
from .condense import condense, condenseSet
from .highlight import getTupleHighlights, getHlAtt

LIMIT_SHOW = 100
LIMIT_TABLE = 2000

FONT_BASE = (
    "https://github.com/annotation/text-fabric/blob/master/tf/server/static/fonts"
)

CSS_FONT = """
    <link rel="stylesheet" href="/server/static/fonts.css"/>
"""

CSS_FONT_API = f"""
@font-face {{{{
  font-family: "{{fontName}}";
  src:
    local("{{font}}"),
    url("{FONT_BASE}/{{fontw}}?raw=true");
}}}}
"""

VAR_PATTERN = re.compile(r"\{([^}]+)\}")

ORIG = "orig"

GRender = namedtuple(
    "GRender",
    """
    sectionTypeSet
    ltr
    textClass
    firstSlot
    lastSlot
    inTuple
""".strip().split(),
)

Render = namedtuple(
    "Render",
    """
    slotType
    nType
    isSlot
    isSlotOrDescend
    descend
    isBaseNonSlot
    children
    boundaryClass
    hlClass
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
    else:
        return

    for (attr, default) in (
        ("writing", None),
        ("writingDir", "ltr"),
        ("verseTypes", None),
        ("lex", None),
        ("transform", {}),
        ("childType", {}),
        ("superType", None),
        ("plainTypes", {}),
        ("prettyTypes", {}),
        ("levels", {}),
        ("interfaceDefaults", {}),
        ("lineNumbers", None),
        ("graphics", None),
    ):
        setattr(app, attr, getattr(app, attr, None) or default)

    app.afterChild = {}

    levelClass = {}

    for (nType, nTypeInfo) in app.levels.items():
        level = nTypeInfo["level"]
        flow = nTypeInfo["flow"]
        wrap = nTypeInfo["wrap"]
        containerCss = f"contnr c{level}"
        labelCss = f"lbl c{level}"
        childrenCss = f"children {flow} {'wrap' if wrap else ''}"
        levelClass[nType] = dict(
            container=containerCss, label=labelCss, children=childrenCss,
        )

    app.levelClass = levelClass

    if not app._browse:
        app.loadCss()

    verseType = app.api.T.sectionTypes[-1]
    if app.verseTypes is None:
        app.verseTypes = {verseType}
    else:
        app.verseTypes |= {verseType}

    lexInfo = (
        None
        if app.lex is None
        else dict(
            typ=app.lex, feat=app.lex, cls=app.lex, target=app.api.F.otype.slotType
        )
        if type(app.lex) is str
        else app.lex
    )
    app.lexType = None
    app.lexFeature = None
    app.lexCls = None
    app.lexTarget = None

    if lexInfo is not None:
        app.lexType = lexInfo.get("typ", None)
        app.lexFeature = lexInfo.get("feat", None)
        app.lexType = lexInfo.get("cls", None)
        app.lexTarget = lexInfo.get("target", None)

    for attr in ("plain", "pretty"):
        templates = {}
        noChildren = set()
        dFeaturesText = {}
        dFeatures = {}

        for (tp, info) in getattr(app, f"{attr}Types", {}).items():
            if attr == "plain":
                (template, withChildren) = info
                if template is None:
                    continue
                if not withChildren:
                    noChildren.add(tp)
            else:
                (template, featuresText, features) = info
                dFeaturesText[nType] = parseFeatures(featuresText)
                dFeatures[nType] = parseFeatures(features)

            templateFeatures = (
                VAR_PATTERN.findall(template) if type(template) is str else ()
            )
            templates[tp] = (template, templateFeatures)

        setattr(app, f"{attr}Custom", {})
        setattr(app, f"{attr}Templates", templates)
        if attr == "plain":
            setattr(app, f"{attr}NoChildren", noChildren)
        else:
            setattr(app, f"{attr}dFeaturesText", dFeaturesText)
            setattr(app, f"{attr}dFeatures", dFeatures)
            setattr(app, f"{attr}PreCustom", {})
            setattr(app, f"{attr}PostCustom", {})

    app.childrenCustom = {}

    app.superTypes = None if app.superType is None else app.superType.values()


def export(app, tuples, toDir=None, toFile="results.tsv", **options):
    display = app.display
    if not display.check("table", options):
        return ""
    d = display.get(options)

    if toDir is None:
        toDir = os.path.expanduser(DOWNLOADS)
        if not os.path.exists(toDir):
            os.makedirs(toDir, exist_ok=True)
    toPath = f"{toDir}/{toFile}"

    resultsX = getResultsX(
        app,
        tuples,
        d.tupleFeatures,
        d.condenseType or app.condenseType,
        app.noDescendTypes,
        fmt=d.fmt,
    )

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
    d = display.get(options)

    api = app.api
    F = api.F
    fOtype = F.otype.v

    item = d.condenseType if d.condensed else RESULT

    if d.condensed:
        tuples = condense(api, tuples, d.condenseType, multiple=True)

    passageHead = '</th><th class="tf">p' if d.withPassage else ""

    html = []
    one = True

    for (i, tup) in _tupleEnum(tuples, d.start, d.end, LIMIT_TABLE, item):
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
    d = display.get(options)

    api = app.api
    F = api.F
    T = api.T
    fOtype = F.otype.v
    _browse = app._browse

    if d.withPassage:
        passageNode = getRefMember(app, tup, d)
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

    highlights = getTupleHighlights(api, tup, d.highlights, d.colorMap, d.condenseType)

    if _browse:
        prettyRep = (
            prettyTuple(app, tup, seq, withPassage=False, **newOptions)
            if opened
            else ""
        )
        current = "focus" if seq == position else ""
        attOpen = "open " if opened else ""
        tupSeq = ",".join(str(n) for n in tup)
        if d.withPassage:
            sParts = T.sectionFromNode(passageNode, fillup=True)
            passageAtt = " ".join(
                f'sec{i}="{sParts[i] if i < len(sParts) else ""}"' for i in range(3)
            )
        else:
            passageAtt = ""

        plainRep = "".join(
            f"""<span>{mdEsc(app.plain(
                    n,
                    isLinked=i == d.linked - 1,
                    withPassage=False,
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
    if d.withPassage:
        html.append(passageRef)
    for (i, n) in enumerate(tup):
        html.append(
            app.plain(
                n,
                isLinked=not passageRef and i == d.linked - 1,
                _inTuple=True,
                _asString=True,
                withPassage=False,
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

    passageHead = '</th><th class="tf">p' if d.withPassage else ""
    head = (
        f"""<tr class="tf"><th class="tf">n{passageHead}</th><th class="tf">"""
        f"""{'</th><th class="tf">'.join(fOtype(n) for n in tup)}"""
        f"""</th></tr>"""
    )
    html = f"""<table>{head}{"".join(html)}</table>"""

    dh(html)


def plain(app, n, isLinked=True, _inTuple=False, _asString=False, **options):
    display = app.display
    if not display.check("plain", options):
        return ""

    d = display.get(options)
    if type(d.highlights) is set:
        d.highlights = {m: "" for m in d.highlights}
    d.isHtml = d.fmt in app.textFormats

    _browse = app._browse
    api = app.api
    T = api.T

    ltr = getLtr(app.writingDir, d)
    textClass = display.formatClass[d.fmt].lower()
    (firstSlot, lastSlot) = getBoundary(api, n)

    g = GRender(T.sectionTypeSet, ltr, textClass, firstSlot, lastSlot, _inTuple)
    passage = getPassage(app, True, d, g, n)
    rep = _doPlain(app, d, g, n, True, [])

    if isLinked and not passage:
        rep = app.webLink(n, text=rep, _asString=True)

    if _browse or _asString:
        return rep
    dh(passage + rep)


def _doPlain(app, d, g, n, outer, html, done=set()):
    done.add(n)

    r = _prepareDisplay(app, False, d, g, n, outer)
    if not r:
        return

    ltr = g.ltr
    nType = r.nType

    outerCls = f"outer {ltr}" if outer else ""

    isSuperType = False
    superType = app.superType
    didSuper = False

    if not outer and superType is not None:
        superTypes = app.superTypes
        isSuperType = nType in superTypes

        if not isSuperType:
            sType = superType.get(nType, None)
            if sType:
                (sn, sStart, sEnd) = getSuper(app, n, sType)
                gr = getSuperBounds(g, r)
                sr = _prepareDisplay(app, False, d, gr, n, False)
                if sr and sr.hlClass:
                    sClasses = f"plain {sr.boundaryClass} {sr.hlClass}"
                    html.append(f'<span class="{sClasses}" {sr.hlStyle}>')
                    if sr.nodePart:
                        html.append(sr.nodePart)
                    didSuper = True

    classes = (
        f"plain {'' if didSuper else outerCls} {ltr} {r.boundaryClass} {r.hlClass}"
    )
    html.append(f'<span class="{classes}" {r.hlStyle}>')

    if r.nodePart:
        html.append(r.nodePart)

    html.append(_doPlainNode(app, d, g, r, n, outer, done=done))

    for ch in r.children:
        _doPlain(app, d, g, ch, False, html, done=done)
    html.append("""</span>""")
    if didSuper:
        html.append("""</span>""")
    return "".join(html) if outer else None


def _doPlainNode(app, d, g, r, n, outer, done=set()):
    api = app.api
    Fs = api.Fs
    T = api.T

    verseTypes = app.verseTypes
    isHtml = d.isHtml
    ltr = g.ltr
    textClass = g.textClass
    sectionTypeSet = g.sectionTypeSet
    inTuple = g.inTuple
    nType = r.nType

    plainCustom = app.plainCustom
    if nType in plainCustom:
        method = plainCustom[nType]
        contrib = method(app, d, g, r, n, outer, done=done)
        return contrib
    if r.isSlotOrDescend:
        text = T.text(n, fmt=d.fmt, descend=r.descend)
        if not isHtml:
            text = htmlEsc(text)
        contrib = f'<span class="{textClass}">{text}</span>'
    elif nType in app.plainTemplates:
        (tpl, feats) = app.plainTemplates[nType]
        tplFilled = tpl.format(
            **{feat: getValue(app, n, nType, feat) for feat in feats}
        )
        contrib = f"""<span class="plain {ltr}">{tplFilled}</span>"""
    elif nType == app.lexType:
        lexeme = htmlEsc(Fs(app.lexFeature).v(n))
        contrib = f'<span class="plain {ltr} {app.lexCls}">{lexeme}</span>'
    elif nType in verseTypes | sectionTypeSet:
        if not inTuple and nType in verseTypes:
            contrib = ""
        else:
            heading = app.webLink(n, _asString=True)
            contrib = f'<span class="plain {ltr}">{heading}</span>'
    else:
        contrib = ""
    return contrib


# PRETTY and FRIENDS


def show(app, tuples, **options):
    display = app.display
    if not display.check("show", options):
        return ""
    d = display.get(options)

    api = app.api
    F = api.F

    item = d.condenseType if d.condensed else RESULT

    if d.condensed:
        tuples = condense(api, tuples, d.condenseType, multiple=True)

    for (i, tup) in _tupleEnum(tuples, d.start, d.end, LIMIT_SHOW, item):
        item = F.otype.v(tup[0]) if d.condensed and d.condenseType else RESULT
        prettyTuple(
            app, tup, i, item=item, **options,
        )


def prettyTuple(app, tup, seq, item=RESULT, **options):
    display = app.display
    if not display.check("prettyTuple", options):
        return ""
    d = display.get(options)

    _browse = app._browse

    if len(tup) == 0:
        if _browse:
            return ""
        else:
            return

    api = app.api
    sortKey = api.sortKey

    containers = {tup[0]} if d.condensed else condenseSet(api, tup, d.condenseType)
    highlights = getTupleHighlights(api, tup, d.highlights, d.colorMap, d.condenseType)

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

    d = display.get(options)
    if type(d.highlights) is set:
        d.highlights = {m: "" for m in d.highlights}
    d.isHtml = d.fmt in app.textFormats
    d.features = sorted(flattenToSet(d.extraFeatures) | flattenToSet(d.tupleFeatures))

    _browse = app._browse
    api = app.api
    F = api.F
    L = api.L
    T = api.T
    otypeRank = api.otypeRank

    ltr = getLtr(app.writingDir, d)
    textClass = display.formatClass[d.fmt].lower()
    (firstSlot, lastSlot) = getBoundary(api, n)

    g = GRender(T.sectionTypeSet, ltr, textClass, firstSlot, lastSlot, True)
    passage = getPassage(app, False, d, g, n)

    containerN = None

    nType = F.otype.v(n)
    if d.condensed and d.condenseType:
        if nType == d.condenseType:
            containerN = n
        elif otypeRank[nType] < otypeRank[d.condenseType]:
            ups = L.u(n, otype=d.condenseType)
            if ups:
                containerN = ups[0]

    (firstSlot, lastSlot) = (
        getBoundary(api, n)
        if not d.condensed or not d.condenseType
        else (None, None)
        if containerN is None
        else getBoundary(api, containerN)
    )

    html = []

    _doPretty(app, d, g, n, True, html)

    htmlStr = passage + "".join(html)
    if _browse:
        return htmlStr
    dh(htmlStr)


def _doPretty(app, d, g, n, outer, html, seen=set()):
    if n in seen:
        return

    if outer:
        seen = set()

    seen.add(n)

    r = _prepareDisplay(app, True, d, g, n, outer)
    if not r:
        return

    ltr = g.ltr
    nType = r.nType

    nodePlain = None
    if r.isBaseNonSlot:
        done = set()
        nodePlain = _doPlain(app, d, g, n, True, [], done=done)
        seen |= done

    isSuperType = False
    superType = app.superType
    didSuper = False

    if not outer and superType is not None:
        superTypes = app.superTypes
        isSuperType = nType in superTypes

        if not isSuperType:
            sType = superType.get(nType, None)
            if sType:
                (sn, sStart, sEnd) = getSuper(app, n, sType)
                gr = getSuperBounds(g, r)
                sr = _prepareDisplay(app, True, d, gr, sn, False)
                if sr:
                    sNodePlain = None
                    if sr.isBaseNonSlot:
                        sNodePlain = _doPlain(app, d, gr, sn, True, [])
                    (sLabel, sFeaturePart) = _doPrettyNode(
                        app, d, gr, sr, sn, False, sNodePlain
                    )
                    html.append(
                        f"""
<div class="{sr.cls['container']} {ltr} {sr.boundaryClass} {sr.hlClass}" {sr.hlStyle}>
{sLabel}{sFeaturePart}
<div class="{sr.cls['children']} {ltr}">
"""
                    )
                    didSuper = True

    (label, featurePart) = _doPrettyNode(app, d, g, r, n, outer, nodePlain)

    containerB = f"""
<div class="{r.cls['container']} {ltr} {r.boundaryClass} {r.hlClass}" {r.hlStyle}>
"""
    containerE = f"""</div>"""

    if "b" in label:
        html.append(f"{containerB}{label['b']} {featurePart}{containerE}")
    if "" in label:
        html.append(f"{containerB}{label['']} {featurePart}")

    if d.graphics and nType in app.graphics:
        html.append(app.getGraphics(n, nType, outer))

    if r.children:
        html.append(f"""<div class="{r.cls['children']} {ltr}">""")

    afterChild = app.afterChild

    for ch in r.children:
        if ch in seen:
            continue
        _doPretty(app, d, g, ch, False, html, seen=seen)
        after = afterChild.get(nType, None)
        if after:
            html.append(after(ch))

    if r.children:
        html.append("""</div>""")

    if "" in label:
        html.append(f"{containerE}")
    if "e" in label:
        html.append(f"{containerB}{label['e']} {featurePart}{containerE}")

    if didSuper:
        html.append("""</div></div>""")
    return "".join(html) if outer else None


def _doPrettyNode(app, d, g, r, n, outer, nodePlain):
    nType = r.nType

    api = app.api
    Fs = api.Fs
    T = api.T
    L = api.L

    isHtml = d.isHtml
    textClass = g.textClass

    isText = False

    if r.isBaseNonSlot:
        heading = nodePlain
    else:
        prettyTemplates = app.prettyTemplates
        (tpl, feats) = prettyTemplates[nType] if nType in prettyTemplates else ("", {})
        if tpl is True:
            isText = True
            text = T.text(n, fmt=d.fmt)
        else:
            text = tpl.format(**{feat: getValue(app, n, nType, feat) for feat in feats})
        heading = text if isHtml else htmlEsc(text)

    dFeaturesText = app.prettydFeaturesText
    dFeatures = app.prettydFeatures
    featuresText = dFeaturesText.get(nType, ((), {}))
    features = dFeatures.get(nType, ((), {}))

    fp = getFeatures(app, d, n, *featuresText, withName=False, asText=True)
    featurePPart = fp if isHtml else htmlEsc(fp)
    featurePart = getFeatures(app, d, n, *features, withName=True, asText=False)

    if nType == app.lexType:
        extremeOccs = getBoundary(api, n)
        linkOccs = " - ".join(app.webLink(lo, _asString=True) for lo in extremeOccs)
        lexeme = htmlEsc(Fs(app.lexFeature).v(n))
        heading = f'<div class="{app.lexCls}">{lexeme}</div>'
        featurePart += f'<div class="occs">{linkOccs}</div>'
    elif nType == app.lexTarget:
        lx = L.u(n, otype=app.lexType)[0]
        heading = app.webLink(lx, heading, _asString=True)

    if featurePart:
        featurePart = f"""<div class="meta">{featurePart}</div>"""

    textClass = textClass if isText else app.defaultCls
    heading = f'<span class="{textClass}">{heading}</span>'

    if outer:
        heading = app.webLink(n, text=f"{heading}", _asString=True)

    label = {}
    for x in ("", "b", "e"):
        key = f"label{x}"
        if key in r.cls:
            val = r.cls[key]
            label[x] = (
                f"""<div class="{val}">{r.nodePart} {heading} {featurePPart}</div>"""
                if heading or r.nodePart or featurePPart
                else ""
            )

    return (label, featurePart)


def _prepareDisplay(app, isPretty, d, g, n, outer):
    api = app.api
    F = api.F
    T = api.T
    slotType = F.otype.slotType
    nType = F.otype.v(n)

    descendType = T.formats.get(d.fmt, slotType)
    bottomType = d.baseType if isPretty else descendType

    isSlot = nType == slotType

    children = (
        ()
        if isSlot
        or nType == bottomType
        or (not isPretty and nType in app.plainNoChildren)
        else getChildren(app, d, g, n, nType)
    )

    boundaryResult = getBoundaryResult(api, g, n)
    if boundaryResult is None:
        return False

    (boundaryClass, myStart, myEnd) = boundaryResult

    (hlClass, hlStyle) = getHlAtt(app, n, d.highlights, d.baseType, not isPretty)

    isSlotOrDescend = isSlot or nType == descendType
    descend = False if descendType == slotType else None
    isBaseNonSlot = nType == d.baseType and not isSlot

    nodePart = getNodePart(app, isPretty, d, n, nType, isSlot, outer, hlClass)
    cls = {}
    if isPretty:
        if nType in app.levelClass:
            cls.update(app.levelClass[nType])
        prettyCustom = app.prettyCustom
        if nType in prettyCustom:
            prettyCustom[nType](app, n, nType, cls)

    return Render(
        slotType,
        nType,
        isSlot,
        isSlotOrDescend,
        descend,
        isBaseNonSlot,
        children,
        boundaryClass,
        hlClass,
        hlStyle,
        nodePart,
        cls,
        myStart,
        myEnd,
    )


def parseFeatures(features):
    bare = []
    indirect = {}
    for feat in features.split(" "):
        if not feat:
            continue
        parts = feat.split(":", 1)
        bare.append(parts[0])
        if len(parts) > 1:
            indirect[parts[1]] = parts[0]
    return (bare, indirect)


def getPassage(app, isPretty, d, g, n):
    verseTypes = app.verseTypes
    sectionTypeSet = g.sectionTypeSet
    nType = app.api.F.otype.v(n)

    if not d.withPassage or nType in sectionTypeSet - verseTypes:
        return ""

    passage = app.webLink(n, _asString=True)
    return f"""<span class="psg ltr">{passage}{NB}</span>"""


def getSuperBounds(g, r):
    return g._replace(
        firstSlot=max((g.firstSlot, r.myStart)), lastSlot=min((g.lastSlot, r.myEnd)),
    )


def getValue(app, n, nType, feat):
    Fs = app.api.Fs
    val = Fs(feat).v(n)
    modifier = app.transform.get(nType, {}).get(feat, None)
    return modifier(val) if modifier else val


def getLtr(direction, d):
    return (
        "rtl"
        if direction == "rtl" and (f"{ORIG}-" in d or f"-{ORIG}" in d)
        else ("" if direction == "ltr" else "ltr")
    )


def getBigType(nType, otypeRank, d, g):
    sectionTypeSet = g.sectionTypeSet
    isBig = False
    if not d.full:
        if sectionTypeSet and nType in sectionTypeSet:
            if d.condenseType is None or otypeRank[nType] > otypeRank[d.condenseType]:
                isBig = True
        elif (
            d.condenseType is not None and otypeRank[nType] > otypeRank[d.condenseType]
        ):
            isBig = True
    return isBig


def getBoundaryResult(api, g, n):
    boundaryClass = ""
    myStart = None
    myEnd = None
    firstSlot = g.firstSlot
    lastSlot = g.lastSlot

    (myStart, myEnd) = getBoundary(api, n)

    if firstSlot is not None:
        if myEnd < firstSlot:
            return None
        if myStart < firstSlot:
            boundaryClass += " rno"
    if lastSlot is not None:
        if myStart > lastSlot:
            return None
        if myEnd > lastSlot:
            boundaryClass += " lno"
    return (boundaryClass, myStart, myEnd)


def getSuper(app, n, tp):
    api = app.api
    L = api.L
    sn = L.u(n, otype=tp)[0]
    return (sn, *getBoundary(api, sn))


def getChildren(app, d, g, n, nType):
    verseTypes = app.verseTypes
    childType = app.childType
    api = app.api
    F = api.F
    L = api.L
    otypeRank = api.otypeRank
    sortNodes = api.sortNodes

    slotType = F.otype.slotType

    isBigType = (
        g.inTuple if nType in app.verseTypes else getBigType(nType, otypeRank, d, g)
    )

    if isBigType and not d.full:
        children = ()
    elif nType in childType:
        childType = childType[nType]
        children = L.d(n, otype=childType)
        childrenCustom = app.childrenCustom
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


def getNodePart(app, isPretty, d, n, nType, isSlot, outer, highlight):
    _browse = app._browse

    allowInfo = isPretty or outer or highlight

    num = ""
    if d.withNodes and allowInfo:
        num = n

    ntp = ""
    if (d.withTypes or isPretty and d.prettyTypes) and not isSlot and allowInfo:
        ntp = nType

    line = ""
    if d.lineNumbers and allowInfo:
        feat = app.lineNumbers.get(nType, None)
        if feat:
            line = app.api.Fs(feat).v(n)
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


def getResultsX(app, results, features, condenseType, noDescendTypes, fmt=None):
    api = app.api
    F = api.F
    Fs = api.Fs
    T = api.T
    fOtype = F.otype.v
    otypeRank = api.otypeRank
    sectionTypeSet = T.sectionTypeSet
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


def getFeatures(app, d, n, features, indirect, withName=None, asText=False):
    api = app.api
    L = api.L
    Fs = api.Fs

    featurePartB = '<div class="features">'
    featurePartE = "</div>"

    # a feature can be nType:feature
    # do a L.u(n, otype=nType)[0] and take the feature from there

    givenFeatureSet = set(features)
    xFeatures = tuple(f for f in d.extraFeatures if f not in givenFeatureSet)
    extraSet = set(xFeatures)
    featureList = tuple(features) + xFeatures
    nFeatures = len(features)

    showWithName = extraSet

    featurePart = ""

    if asText:
        hasB = False
    else:
        hasB = True
    if d.showFeatures:
        for (i, name) in enumerate(featureList):
            if name not in d.suppress:
                fsName = Fs(name)
                if fsName is None:
                    continue
                fsNamev = fsName.v
                value = (
                    fsNamev(L.u(n, otype=indirect[name])[0])
                    if name in indirect
                    else fsNamev(n)
                )
                value = None if value in d.noneValues else htmlEsc(value or "")
                if value is not None:
                    value = value.replace("\n", "<br/>")
                    showName = withName or (withName is None and name in showWithName)
                    nameRep = f'<span class="f">{name}=</span>' if showName else ""
                    xClass = "xft" if name in extraSet else ""
                    featureRep = (
                        f' <span class="{name.lower()} {xClass}">'
                        f"{nameRep}{value}</span>"
                    )

                    if i >= nFeatures:
                        if not hasB:
                            featurePart += featurePartB
                            hasB = True
                    featurePart += featureRep
    if not featurePart:
        return ""

    if not asText:
        featurePart = f"{featurePartB}{featurePart}"
    if hasB:
        featurePart += featurePartE
    return featurePart


def loadCss(app, reload=False):
    """
  The CSS is looked up and then loaded into a notebook if we are not
  running in the TF browser,
  else the CSS is returned.

  With reload=True, the app-specific display.css will be read again from disk
  """
    _browse = app._browse
    if _browse:
        return app.css

    if reload:
        config = findAppConfig(app.appName, app.appPath)
        cfg = configure(config, app.version)
        app.css = cfg["css"]

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
        if app.fontName is None
        else CSS_FONT_API.format(fontName=app.fontName, font=app.font, fontw=app.fontw)
    )
    tableCss = """
tr.tf, td.tf, th.tf {
  text-align: left ! important;
}

"""
    dh(f"<style>{cssFont + tableCss + genericCss + app.css}</style>")


def getRefMember(app, tup, d):
    api = app.api
    T = api.T
    sectionTypeSet = T.sectionTypeSet
    linked = d.linked
    condensed = d.condensed

    ln = len(tup)
    return (
        None
        if not tup or any(n in sectionTypeSet for n in tup)
        else tup[0]
        if condensed
        else tup[min((linked, ln - 1))]
        if linked
        else tup[0]
    )


def _tupleEnum(tuples, start, end, limit, item):
    if start is None:
        start = 1
    i = -1
    if not hasattr(tuples, "__len__"):
        if end is None or end - start + 1 > limit:
            end = start - 1 + limit
        for tup in tuples:
            i += 1
            if i < start - 1:
                continue
            if i >= end:
                break
            yield (i + 1, tup)
    else:
        if end is None or end > len(tuples):
            end = len(tuples)
        rest = 0
        if end - (start - 1) > limit:
            rest = end - (start - 1) - limit
            end = start - 1 + limit
        for i in range(start - 1, end):
            yield (i + 1, tuples[i])
        if rest:
            dh(
                f"<b>{rest} more {item}s skipped</b> because we show a maximum of"
                f" {limit} {item}s at a time"
            )
