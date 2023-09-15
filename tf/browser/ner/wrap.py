"""Wraps various pieces into HTML.
"""

from .settings import (
    FEATURES,
    KEYWORD_FEATURES,
    SUMMARY_FEATURES,
    STYLES,
    getText,
    featureDefault,
)
from .html import H


def wrapCss(web, templateData, genericCss):
    propMap = dict(
        ff="font-family",
        fz="font-size",
        fw="font-weight",
        fg="color",
        bg="background-color",
        bw="border-width",
        bs="border-style",
        bc="border-color",
        br="border-radius",
        p="padding",
        m="margin",
    )

    def makeBlock(manner):
        props = STYLES[manner]
        defs = [f"\t{propMap[abb]}: {val};\n" for (abb, val) in props.items()]
        return H.join(defs)

    def makeCssDef(selector, *blocks):
        return selector + " {\n" + H.join(blocks) + "}\n"

    css = []

    for feat in FEATURES:
        manner = "keyword" if feat in KEYWORD_FEATURES else "free"

        plain = makeBlock(manner)
        bordered = makeBlock(f"{manner}_bordered")
        active = makeBlock(f"{manner}_active")
        borderedActive = makeBlock(f"{manner}_bordered_active")

        css.extend(
            [
                makeCssDef(f".{feat}", plain),
                makeCssDef(f".{feat}.active", active),
                makeCssDef(f"#{feat}_v", plain),
                makeCssDef(f"span.{feat}_w", plain, bordered),
                makeCssDef(f"span.{feat}_w.active", borderedActive, active),
                makeCssDef(f"button.{feat}_sel", plain, bordered),
                makeCssDef(f"button.{feat}_sel[st=v]", borderedActive, active),
            ]
        )

    featureCss = H.join(css, sep="\n")
    allCss = genericCss + H.style(featureCss, type="text/css")
    templateData.css = allCss


def wrapMessages(messages):
    """HTML for messages."""
    return H.p((H.span(text, cls=lev) + H.br() for (lev, text) in messages))


def wrapAnnoSets(annoDir, chosenAnnoSet, annoSets):
    """HTML for the annoset chooser.

    It is a list of buttons, each corresponding to an existing annoset.
    A click on the button selects that annoset.
    There is also a control to delete the annoset.

    Apart from these buttons there is a button to switch to the entities that are
    present in the TF dataset as nodes of type "ent" with corresponding features.

    Finally, it is possible to create a new, empty annoset.

    Parameters
    ----------
    chosenAnnoSet: string
        The name of the chosen annoset.
        If empty, it refers to the entities already present in the dataset as TF nodes
        and features.
    annoSets: list
        The list of existing annosets.
    """
    content1 = [
        H.input(
            type="hidden",
            name="annoset",
            value=chosenAnnoSet,
            id="annoseth",
        ),
        H.input(
            type="hidden",
            name="duannoset",
            value="",
            id="duannoseth",
        ),
        H.input(
            type="hidden",
            name="rannoset",
            value="",
            id="rannoseth",
        ),
        H.button(
            "+",
            type="submit",
            cls="medium active",
            id="anew",
            title="create a new annotation set",
        ),
        " ",
        H.button(
            "++",
            type="submit",
            cls="medium active",
            id="adup",
            title="duplicate this annotation set",
        ),
        " ",
        H.select(
            (
                H.option(
                    "generated entities" if annoSet == "" else annoSet,
                    value=annoSet,
                    selected=annoSet == chosenAnnoSet,
                )
                for annoSet in [""] + sorted(annoSets)
            ),
            cls="selinp",
            id="achange",
        ),
    ]

    content2 = (
        [
            H.input(
                type="hidden",
                name="dannoset",
                value="",
                id="dannoseth",
            ),
            H.button(
                "→",
                type="submit",
                cls="medium active",
                id="arename",
                title="rename current annotation set",
            ),
            " ",
            H.button(
                "-",
                type="submit",
                cls="medium active",
                id="adelete",
                title="delete current annotation set",
            ),
        ]
        if chosenAnnoSet
        else []
    )

    return H.p(content1, content2)


def wrapEntityOverview(web, templateData):
    """HTML for the feature values of entities.

    Parameters
    ----------
    setData: dict
        The entity data for the chosen set.

    Returns
    -------
    HTML string
    """

    setData = web.toolData.ner.sets[web.annoSet]

    templateData.entityoverview = H.p(
        H.span(H.code(f"{len(es):>5}"), " x ", H.span(repSummary(fVals))) + H.br()
        for (fVals, es) in sorted(
            setData.entitySummary.items(), key=lambda x: (-len(x[1]), x[0])
        )
    )


def wrapEntityHeaders(web, templateData):
    """HTML for the header of the entity table.

    Dependent on the state of sorting.

    Parameters
    ----------
    sortKey: string
        Indicator of how the table is sorted.
    sortDir:
        Indicator of the direction of the sorting.

    Returns
    -------
    HTML string

    """
    sortKey = templateData.sortkey
    sortDir = templateData.sortdir
    sortKeys = ((feat, f"sort_{i}") for (i, feat) in enumerate(FEATURES))

    content = [
        H.input(type="hidden", name="sortkey", id="sortkey", value=sortKey),
        H.input(type="hidden", name="sortdir", id="sortdir", value=sortDir),
    ]

    for (label, key) in (("frequency", "freqsort"), *sortKeys):
        web.console(f"{key=} {sortKey=} {sortDir=}")
        hl = " active " if key == sortKey else ""
        theDir = sortDir if key == sortKey else "u"
        theArrow = "↑" if theDir == "u" else "↓"
        content.extend(
            [
                H.button(
                    f"{label} {theArrow}",
                    type="button",
                    tp="sort",
                    sk=key,
                    sd=theDir,
                    cls=f"medium{hl}",
                ),
                " ",
            ]
        )

    templateData.entityheaders = H.p(content)


def wrapQuery(web, templateData, nFind, nEnt, nVisible):
    """HTML for the query line.

    Parameters
    ----------
    web: object
        The web app object

    Returns
    -------
    html string
        The finished HTML of the query parameters
    """

    hasFind = wrapFilter(web, templateData, nFind)
    txt = wrapEntityInit(web, templateData)
    wrapEntityText(templateData, txt)
    features = wrapEntityFeats(web, templateData, nEnt, nVisible, hasFind, txt)
    wrapEntityModify(web, templateData, hasFind, txt, features)


def wrapFilter(web, templateData, nFind):
    annoSet = web.annoSet
    setData = web.toolData.ner.sets[annoSet]

    sFind = templateData.sfind
    sFindRe = templateData.sfindre
    sFindError = templateData.sfinderror

    hasFind = sFindRe is not None

    nSent = len(setData.sentences)

    templateData["find"] = H.p(
        H.b("Filter:"),
        H.input(type="text", name="sfind", id="sfind", value=sFind),
        " ",
        wrapFindStat(nSent, nFind, hasFind),
        " ",
        H.button("✖️", type="submit", id="findclear"),
        " ",
        H.span(sFindError, id="sfinderror", cls="error"),
        " ",
        H.button("🔎", type="submit", id="lookupf"),
    )
    return hasFind


def wrapEntityInit(web, templateData):
    kernelApi = web.kernelApi
    app = kernelApi.app
    api = app.api
    F = api.F

    tokenStart = templateData.tokenstart
    tokenEnd = templateData.tokenend
    hasEntity = tokenStart and tokenEnd

    startRep = H.input(
        type="hidden", name="tokenstart", id="tokenstart", value=tokenStart or ""
    )
    endRep = H.input(
        type="hidden", name="tokenend", id="tokenend", value=tokenEnd or ""
    )
    templateData.entityinit = startRep + endRep

    return getText(F, range(tokenStart, tokenEnd + 1)) if hasEntity else ""


def wrapEntityText(templateData, txt):
    templateData.entitytext = H.join(
        H.b("Entity:"),
        H.span(txt, id="qwordshow"),
        " ",
        H.button("✖️", type="submit", id="queryclear"),
        " ",
        H.button("🔎", type="submit", id="lookupq"),
    )


def wrapEntityFeats(web, templateData, nEnt, nVisible, hasFind, txt):
    if txt == "":
        templateData.entityfeats = ""
        return

    annoSet = web.annoSet
    setData = web.toolData.ner.sets[annoSet]

    valSelect = templateData.valselect

    features = {feat: setData.entityTextVal[feat].get(txt, set()) for feat in FEATURES}

    html = []

    for (feat, theseVals) in features.items():
        thisValSelect = valSelect[feat]

        html.extend(
            [
                H.input(
                    type="hidden",
                    name=f"{feat}_select",
                    id=f"{feat}_select",
                    value=",".join(thisValSelect),
                ),
                H.i(feat),
                ": ",
            ]
        )
        for val in ["⌀"] + sorted(theseVals):
            html.append(
                H.button(
                    val,
                    wrapEntityStat(val, nVisible[feat], nEnt[feat], hasFind),
                    type="button",
                    name=val,
                    cls=f"{feat}_sel",
                    st="v" if val in thisValSelect else "x",
                    title=f"{feat} not marked"
                    if val == "⌀"
                    else f"{feat} marked as {val}",
                )
            )

    templateData.entityfeats = H.join(html, sep=" ")
    return features


def wrapEntityModify(web, templateData, hasFind, txt, features):
    kernelApi = web.kernelApi
    app = kernelApi.app
    api = app.api
    F = api.F

    annoSet = web.annoSet
    setData = web.toolData.ner.sets[annoSet]

    tokenStart = templateData.tokenstart
    tokenEnd = templateData.tokenend
    scope = templateData.scope
    scope = templateData.scope

    hasEntity = txt != ""

    html1 = H.input(type="hidden", id="scope", name="scope", value=scope)

    html2 = ""
    html3 = ""

    if annoSet and hasEntity:
        # Scope of modification

        content = [H.b("Target:")]

        if hasFind:
            content.extend(
                [
                    H.button(
                        "filtered",
                        type="button",
                        id="scopefiltered",
                        title="act on filtered sentences only",
                    ),
                    " ",
                    H.button(
                        "all",
                        type="button",
                        id="scopeall",
                        title="act on all sentences",
                    ),
                ]
            )
        content.extend(
            [
                H.button(
                    "🆗",
                    type="button",
                    id="selectall",
                    title="select all occurences in filtered sentences",
                ),
                " ",
                H.button(
                    "⭕️",
                    type="button",
                    id="selectnone",
                    title="deselect all occurences in filtered sentences",
                ),
            ]
        )
        html2 = H.p(content)

        # Assigment of feature values

        content = [H.b("Assignment:")]

        for feat in FEATURES:
            theseVals = sorted(setData.entityTextVal[feat].get(txt, set()))
            allVals = (
                sorted(x[0] for x in setData.entityFreq[feat])
                if feat in KEYWORD_FEATURES
                else theseVals
            )
            content.extend([H.i(feat), ": "])

            for val in allVals:
                occurs = val in theseVals
                occurCls = " occurs " if occurs else ""

                subContent = []

                if occurs:
                    subContent.append(
                        H.button(
                            "-",
                            type="submit",
                            name=f"{feat}_xbutton",
                            value=val,
                            cls="min",
                        )
                    )
                subContent.append(H.span(val, cls=f"{feat}_sel {occurCls}"))
                subContent.append(
                    H.button(
                        "+",
                        type="submit",
                        name=f"{feat}_pbutton",
                        value=val,
                        cls="plus",
                    )
                )

                content.append(H.span(subContent, cls=f"{feat}_w"))

            default = featureDefault[feat](F, range(tokenStart, tokenEnd + 1))
            init = "" if default in theseVals else default

            content.extend(
                [
                    H.input(
                        type="text",
                        id=f"{feat}_v",
                        name=f"{feat}_v",
                        value=init,
                    ),
                    H.button(
                        "+",
                        type="submit",
                        id=f"{feat}_save",
                        name=f"{feat}_save",
                        value="v",
                        cls="plus",
                    ),
                ]
            )

        html3 = H.p(content)

    templateData.entitymodify = html1 + html2 + html3


def wrapFindStat(nSent, nFind, hasFind):
    n = f"{nFind} of {nSent}" if hasFind else nSent
    return H.span(n, cls="stat")


def wrapEntityStat(val, thisNVisible, thisNEnt, hasPattern):
    na = thisNEnt[val]
    n = f"{thisNVisible[val]} of {na}" if hasPattern else f"{na}"
    return H.span(n, cls="stat")


def wrapActive(web, templateData):
    activeVal = templateData.activeval

    templateData.activevalrep = H.join(
        H.input(
            type="hidden", id=f"{feat}_active", name=f"{feat}_active", value=val or ""
        )
        for (feat, val) in activeVal
    )


def wrapReport(templateData, report):
    templateData.report = H.join(H.p(H.span(line, cls="report")) for line in report)


def repIdent(vals, active=""):
    return H.join(
        (H.span(val, cls=f"{feat} {active}") for (feat, val) in zip(FEATURES, vals)),
        sep=" ",
    )


def repSummary(vals, active=""):
    return H.join(
        (
            H.span(val, cls=f"{feat} {active}")
            for (feat, val) in zip(SUMMARY_FEATURES, vals)
        ),
        sep=" ",
    )
