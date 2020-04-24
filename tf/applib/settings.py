import re

from ..parameters import URL_GH, URL_NB, URL_TFDOC


VAR_PATTERN = re.compile(r"\{([^}]+)\}")

WRITING_DEFAULTS = dict(
    akk=dict(
        language="Akkadian",
        fontName="Santakku",
        font="Santakk.ttf",
        fontw="Santakku.woff",
        direction="ltr",
    ),
    hbo=dict(
        language="Hebrew",
        fontName="Ezra SIL",
        font="SILEOT.ttf",
        fontw="SILEOT.woff",
        direction="rtl",
    ),
    syc=dict(
        language="Syriac",
        fontName="Estrangelo Edessa",
        font="SyrCOMEdessa.otf",
        fontw="SyrCOMEdessa.woff",
        direction="rtl",
    ),
    ara=dict(
        language="Arabic",
        fontName="AmiriQuran",
        font="AmiriQuran.ttf",
        fontw="AmiriQuran.woff2",
        direction="rtl",
    ),
    grc=dict(
        language="Greek",
        fontName="Gentium",
        font="GentiumPlus-R.ttf",
        fontw="GentiumPlus-R.woff",
        direction="ltr",
    ),
    cld=dict(
        language="Aramaic",
        fontName="CharisSIL-R",
        font="CharisSIL-R.otf",
        fontw="CharisSIL-R.woff",
        direction="ltr",
    ),
)
WRITING_DEFAULTS[""] = dict(
    language="",
    fontName="Gentium",
    font="GentiumPlus-R.ttf",
    fontw="GentiumPlus-R.woff",
    direction="ltr",
)

DEFAULT_CLS = "txtn"
DEFAULT_CLS_SRC = "txto"
DEFAULT_CLS_ORIG = "txtu"
DEFAULT_CLS_TRANS = "txtt"
DEFAULT_CLS_PHONO = "txtp"

FORMAT_CSS = dict(
    orig=DEFAULT_CLS_ORIG,
    trans=DEFAULT_CLS_TRANS,
    source=DEFAULT_CLS_SRC,
    phono=DEFAULT_CLS_PHONO,
)

LEVEL_DEFAULTS = dict(
    level={
        3: dict(flow="col"),
        2: dict(flow="row"),
        1: dict(flow="row"),
        0: dict(flow="col"),
    },
    flow=dict(col=dict(wrap=False, stretch=False), row=dict(wrap=True, stretch=True)),
    wrap=None,
    stretch=None,
)


PROVENANCE_DEFAULTS = (
    ("org", "annotation"),
    ("repo", "default"),
    ("relative", "tf"),
    ("graphics", None),
    ("version", "0.1"),
    ("moduleSpecs", None),
    ("zip", None),
    ("corpus", "TF dataset (unspecified)"),
    ("doi", None),
)

DOC_DEFAULTS = (
    ("docRoot", "{urlGh}"),
    ("docExt", ".md"),
    ("docBase", "{docRoot}/{org}/{repo}/blob/master/docs"),
    ("docPage", "home"),
    ("docUrl", "{docBase}/{docPage}{docExt}"),
    ("featureBase", None),
    ("featurePage", "home"),
    ("charUrl", "{tfDoc}/Writing/Transcription/{language}"),
    ("charText", "How TF features represent text"),
    ("webBase", None),
    ("webLang", None),
    ("webUrl", None),
    ("webUrlLex", None),
    ("webLexId", None),
    ("webHint", None),
)

DATA_DISPLAY_DEFAULTS = (
    ("noneValues", {None}),
    ("sectionSep1", " "),
    ("sectionSep2", ":"),
    ("writing", ""),
    ("writingDir", None),
    ("language", None),
    ("fontName", None),
    ("font", None),
    ("fontw", None),
    ("textFormats", {}),
    ("browseNavLevel", None),
    ("browseContentPretty", False),
    ("exampleSection", None),
    ("exampleSectionHtml", None),
)


class AppCurrent:
    def update(self, options):
        for (k, v) in options.items():
            setattr(self, k, v)


def setAppSpecs(app, cfg):
    for (key, value) in cfg.items():
        setattr(app, key, value)

    dKey = "interfaceDefaults"
    setattr(app, dKey, getattr(app, dKey, ()))

    specs = dict(urlGh=URL_GH, urlNb=URL_NB, tfDoc=URL_TFDOC,)
    app.specs = specs

    for (dKey, defaults, source) in (
        ("provenanceSpecs", PROVENANCE_DEFAULTS),
        ("dataDisplay", getDataDefaults),
        ("typeDisplay", getTypeDefaults),
        ("docs", DOC_DEFAULTS, None),
    ):
        if type(source) is dict:
            dSource = cfg.get(dKey, {})
            for (k, v) in defaults:
                val = dSource.get(k, v)
                val = val.format(**specs)
                specs[k] = val
        else:
            source(app, dKey)

    app.context = AppCurrent(specs)


def getDataDefaults(app, dKey):
    api = app.api
    F = api.F
    T = api.T
    sectionTypes = T.sectionTypes

    givenInfo = getattr(app, dKey, None) or {}

    specs = app.specs

    for (attr, default) in DATA_DISPLAY_DEFAULTS:
        if attr == "browseNavLevel":
            default = len(sectionTypes) - 1 if sectionTypes else 1

        value = givenInfo.get(attr, specs.get(attr, default))
        if attr in specs and attr not in givenInfo:
            continue

        if attr == "writing":
            if value not in WRITING_DEFAULTS:
                value = ""
            for (k, v) in WRITING_DEFAULTS[value].items():
                specs[k] = v
            extension = f" {value}" if value else ""
            defaultClsOrig = f"{DEFAULT_CLS_ORIG}{extension}"
            formatCls = compileFormatCls(app, defaultClsOrig)
            specs.update(
                extension=extension, defaultClsOrig=defaultClsOrig, formatCls=formatCls
            )
        elif attr == "exampleSection":
            if not value:
                if sectionTypes:
                    verseType = sectionTypes[-1]
                    firstVerse = F.otype.s(verseType)[0]
                    value = app.sectionStrFromNode(firstVerse)
                else:
                    value = "passage"
            specs["exampleSectionHtml"] = f"<code>{value}</code>"
        else:
            specs[attr] = value


def getTypeDefaults(app, dKey):
    api = app.api
    F = api.F
    T = api.T
    slotType = F.otype.slotType
    nTypes = F.otype.all
    structureTypes = T.structureTypes
    structureTypeSet = T.structureTypeSet
    sectionTypes = T.sectionTypes
    sectionTypeSet = T.sectionTypeSet

    sectionalTypeSet = sectionTypeSet | structureTypeSet

    givenInfo = getattr(app, dKey, None) or {}

    specs = app.specs

    noChildren = set()
    hasSuper = {}
    featuresBare = {}
    features = {}
    lineNumberFeature = {}
    hasGraphics = set()
    verseTypes = {sectionTypes[-1]} if sectionTypes else set()
    lexMap = {}
    baseType = slotType
    condenseType = None
    templates = dict(plain={}, pretty={})
    givenLevels = {}

    for (nType, info) in givenInfo.items():
        if info.get("verselike", False):
            verseTypes.add(nType)

        lOcc = info.get("lexOcc", None)
        if lOcc is not None:
            lexMap[lOcc] = nType

        if "base" in info:
            baseType = info["base"]

        if "condense" in info:
            condenseType = info["condense"]

    for (nType, info) in givenInfo.items():
        template = info.get(
            "template", True if nType == slotType or nType in sectionalTypeSet else ""
        )
        templateFeatures = (
            VAR_PATTERN.findall(template) if type(template) is str else ()
        )
        templates[nType] = (template, templateFeatures)
        featsBare = info.get("featuresBare", "")
        feats = info.get("features", "")
        featuresBare[nType] = parseFeatures(featsBare)
        features[nType] = parseFeatures(feats)

        lineNumber = info.get("lineNumber", None)
        if lineNumber is not None:
            lineNumberFeature[nType] = lineNumber

        graphics = info.get("graphics", False)
        if graphics:
            hasGraphics.add(nType)

        if not info.get("childrenPlain", True):
            noChildren.add(nType)

        supr = info.get("super", None)
        if supr is not None:
            hasSuper[nType] = supr

        verselike = info.get("verselike", False)
        if verselike:
            verseTypes.add(nType)

        transform = info.get("transform", None)
        if transform is not None:
            transform[nType] = transform

        if "level" in info:
            givenLevels[nType] = {
                k: v for (k, v) in info.items() if k in LEVEL_DEFAULTS
            }

    lexTypes = set(lexMap.values())

    levelTypes = [set(), set(), set(), set()]
    levelTypes[3] = sectionalTypeSet - verseTypes
    levelTypes[0] = {slotType} | lexTypes

    remainingTypeSet = set(nTypes) - levelTypes[3] - levelTypes[0]
    remainingTypes = tuple(x for x in nTypes if x in remainingTypeSet)
    nRemaining = len(remainingTypes)

    children = {
        nType: nTypes[i + 1]
        for (i, nType) in enumerate(nTypes)
        if nType in levelTypes[2] | levelTypes[1]
    }
    children.update(
        {
            nType: nTypes[i + 1]
            for (i, nType) in enumerate(structureTypes)
            if i < len(structureTypes) - 1
        }
    )
    children.update(
        {
            nType: nTypes[i + 1]
            for (i, nType) in enumerate(sectionTypes)
            if i < len(sectionTypes) - 1
        }
    )

    lowestSectionalTypes = set()
    if sectionTypes:
        lowestSectionalTypes.add(sectionTypes[-1])
    if structureTypes:
        lowestSectionalTypes.add(structureTypes[-1])

    biggestOtherType = remainingTypes[0] if remainingTypes else slotType
    smallestOtherType = remainingTypes[-1] if remainingTypes else None

    for lexType in lexTypes:
        if lexType in children:
            del children[lexType]

    for lowestSectionalType in lowestSectionalTypes:
        children[lowestSectionalType] = biggestOtherType

    if smallestOtherType is not None:
        children[smallestOtherType] = slotType

    if nRemaining == 0:
        midType = slotType
    elif nRemaining == 1:
        midType = remainingTypes[0]
        levelTypes[1] = {midType}
    else:
        mid = len(remainingTypes) // 2
        midType = remainingTypes[mid]
        levelTypes[1] = set(remainingTypes[0:mid])
        levelTypes[2] = set(remainingTypes[mid:])

    if condenseType is None:
        condenseType = sectionTypes[-1] if sectionTypes else midType

    levels = {
        nType: getLevel(i, givenLevels.get(nType, {}), nType in verseTypes)
        for (i, nType) in enumerate(levelTypes)
    }

    levelCls = {}
    childType = {}

    for (nType, nTypeInfo) in levels.items():
        level = nTypeInfo["level"]
        flow = nTypeInfo["flow"]
        wrap = nTypeInfo["wrap"]
        children = nTypeInfo["children"]

        containerCls = f"contnr c{level}"
        labelCls = f"lbl c{level}"
        childrenCls = f"children {flow} {'wrap' if wrap else ''}"

        levelCls[nType] = dict(
            container=containerCls, label=labelCls, children=childrenCls,
        )
        childType[nType] = children

    specs.update(
        templates=templates,
        levelCls=levelCls,
        featuresBare=featuresBare,
        features=features,
        lineNumberFeature=lineNumberFeature,
        hasGraphics=hasGraphics,
        childType=childType,
        noChildren=noChildren,
        hasSuper=hasSuper,
        superTypes=set(hasSuper.values()),
        verseTypes=verseTypes,
        lexTypes=lexTypes,
        lexMap=lexMap,
        baseType=baseType,
        condenseType=condenseType,
        plainCustom={},
        prettyCustom={},
        afterChild={},
        childrenCustom={},
        transform=transform,
        noDescendTypes=lexTypes,
    )


def getLevel(defaultLevel, givenInfo, isVerse):
    level = givenInfo.get("level", defaultLevel)
    flow = givenInfo.get("flow", "row" if isVerse else LEVEL_DEFAULTS[level]["flow"])
    wrap = givenInfo.get("wrap", LEVEL_DEFAULTS["flow"]["wrap"])
    stretch = givenInfo.get("stretch", LEVEL_DEFAULTS["flow"]["stretch"])
    return dict(level=level, flow=flow, wrap=wrap, stretch=stretch)


def compileFormatCls(app, defaultClsOrig):
    api = app.api
    T = api.T

    result = {None: defaultClsOrig}
    for fmt in T.formats:
        for (key, cls) in FORMAT_CSS.items():
            if (
                f"-{key}-" in fmt
                or fmt.startswith(f"{key}-")
                or fmt.endswith(f"-{key}")
            ):
                result[fmt] = cls
    for fmt in T.formats:
        if fmt not in result:
            result[fmt] = DEFAULT_CLS
    return result


def parseFeatures(features):
    bare = []
    indirect = {}
    for feat in features.split(" "):
        if not feat:
            continue
        parts = feat.split(":", 1)
        feat = parts[-1]
        bare.append(feat)
        if len(parts) > 1:
            indirect[feat] = parts[0]
    return (bare, indirect)
