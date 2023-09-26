"""Wraps various pieces into HTML.
"""

from .settings import (
    TOOLKEY,
    FEATURES,
    KEYWORD_FEATURES,
    SUMMARY_FEATURES,
    STYLES,
    EMPTY,
    NONE,
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
                makeCssDef(f"span.{feat}_sel,button.{feat}_sel", plain, bordered),
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
            id="anew",
            title="create a new annotation set",
        ),
        " ",
        H.button(
            "++",
            type="submit",
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
                id="arename",
                title="rename current annotation set",
            ),
            " ",
            H.button(
                "-",
                type="submit",
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

    setData = web.toolData[TOOLKEY].sets[web.annoSet]

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
                    cls=hl,
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

    wrapAppearance(web, templateData)
    hasFind = wrapFilter(web, templateData, nFind)
    txt = wrapEntityInit(web, templateData)
    wrapEntityText(templateData, txt)
    scope = wrapScope(web, templateData, hasFind, txt)
    features = wrapEntityFeats(web, templateData, nEnt, nVisible, hasFind, txt, scope)
    wrapEntityModify(web, templateData, hasFind, txt, features)


def wrapAppearance(web, templateData):
    formattingDo = templateData.formattingdo
    formattingState = templateData.formattingstate
    templateData.formattingButtons = H.join(
        H.span(
            H.input(
                type="hidden",
                name="formattingdo",
                value="v" if formattingDo else "x",
            ),
            H.button(
                "decorated" if formattingDo else "plain",
                type="button",
                main="v",
                title="toggle plain or decorated formatting of entities",
                cls="alt active",
            ),
        ),
        H.span(
            [
                H.span(
                    H.input(
                        type="hidden",
                        name=f"{feat}_appearance",
                        value="v" if formattingState[feat] else "x",
                    ),
                    H.button(
                        "stats"
                        if feat == "_stat_"
                        else "underlining"
                        if feat == "_entity_"
                        else feat,
                        feat=feat,
                        type="button",
                        title="toggle display of statistics"
                        if feat == "_stat_"
                        else "toggle formatting of entities"
                        if feat == "_entity"
                        else f"toggle formatting for feature {feat}",
                        cls="alt " + ("active" if formattingState[feat] else ""),
                    ),
                )
                for feat in FEATURES + ("_stat_", "_entity_")
            ],
            id="decoratewidget"
        ),
        sep=" ",
    )


def wrapFilter(web, templateData, nFind):
    annoSet = web.annoSet
    setData = web.toolData[TOOLKEY].sets[annoSet]

    sFind = templateData.sfind
    sFindC = templateData.sfindc
    sFindRe = templateData.sfindre
    sFindError = templateData.sfinderror

    hasFind = sFindRe is not None

    nSent = len(setData.sentences)

    templateData.find = H.join(
        H.input(type="text", name="sfind", id="sfind", value=sFind),
        H.input(
            type="hidden", name="sfindc", id="sfindc", value="v" if sFindC else "x"
        ),
        H.button(
            "C" if sFindC else "¢",
            type="submit",
            id="sfindb",
            title="using case SENSITIVE search"
            if sFindC
            else "using case INSENSITIVE search",
            cls="alt",
        ),
        " ",
        wrapFindStat(nSent, nFind, hasFind),
        " ",
        H.button("❌", type="submit", id="findclear", cls="altm"),
        " ",
        H.span(sFindError, id="sfinderror", cls="error"),
        " ",
        H.button("🔎", type="submit", id="lookupf", cls="altm"),
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
    freeState = templateData.freestate
    title = "choose: free, intersecting with other entities, or all"
    templateData.entitytext = H.join(
        H.i("occurrence") if txt else "",
        H.span(txt, id="qwordshow"),
        " ",
        H.button("❌", type="submit", id="queryclear", cls="altm"),
        " ",
        H.button(
            "✅",
            type="submit",
            id="lookupq",
            cls="altm",
            title="look up and fill in green fields",
        ),
        H.button(
            "❎",
            type="submit",
            id="lookupn",
            cls="altm",
            title="look up and keep green fields as is",
        ),
        H.input(type="hidden", name="freestate", id="freestate", value=freeState),
        H.button(
            "⚭ intersecting"
            if freeState == "bound"
            else "⚯ free"
            if freeState == "free"
            else "⚬ all",
            type="submit",
            id="freebutton",
            cls="alt",
            title=title,
        ),
    )


def wrapEntityFeats(web, templateData, nEnt, nVisible, hasFind, txt, scope):
    annoSet = web.annoSet
    setData = web.toolData[TOOLKEY].sets[annoSet]

    valSelect = templateData.valselect
    (scopeInit, scopeFilter, scopeExceptions) = scope

    features = {feat: setData.entityTextVal[feat].get(txt, set()) for feat in FEATURES}
    content = []

    for (feat, theseVals) in features.items():
        thisValSelect = valSelect[feat]

        valuesContent = []

        valuesContent.append(
            H.input(
                type="hidden",
                name=f"{feat}_select",
                id=f"{feat}_select",
                value=",".join(thisValSelect),
            )
        )

        if txt != "":
            for val in [NONE] + sorted(theseVals):
                valuesContent.append(
                    H.button(
                        val,
                        wrapEntityStat(val, nVisible[feat], nEnt[feat], hasFind),
                        type="button",
                        name=val or EMPTY,
                        cls=f"{feat}_sel",
                        st="v" if val in thisValSelect else "x",
                        title=f"{feat} not marked"
                        if val == NONE
                        else f"{feat} marked as {val}",
                    )
                )
            titleContent = H.div(H.i(f"{feat}:"), cls="feattitle")
        else:
            titleContent = ""

        content.append(H.div(titleContent, valuesContent, cls="featwidget"))

    total = wrapEntityStat(None, nVisible[""], nEnt[""], hasFind)
    templateData.selectentities = H.div(
        H.div(
            H.p(H.b("Select"), scopeInit, scopeFilter),
            H.p(H.span(f"{total} sentence(s)")),
            scopeExceptions,
        ),
        H.div(content, id="selectsubwidget"),
        id="selectwidget",
    )
    return features


def wrapScope(web, templateData, hasFind, txt):
    annoSet = web.annoSet
    scope = templateData.scope
    hasEntity = txt != ""

    scopeInit = H.input(type="hidden", id="scope", name="scope", value=scope)
    scopeFilter = ""
    scopeExceptions = ""

    if annoSet and hasEntity:
        # Scope of modification

        scopeFilter = (
            H.span(
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
            )
            if hasFind
            else ""
        )
        scopeExceptions = H.span(
            H.nb,
            H.button(
                "✅",
                type="button",
                id="selectall",
                title="select all occurences in filtered sentences",
                cls="alt",
            ),
            " ",
            H.button(
                "❌",
                type="button",
                id="selectnone",
                title="deselect all occurences in filtered sentences",
                cls="alt",
            ),
        )

    return (scopeInit, scopeFilter, scopeExceptions)


def wrapEntityModify(web, templateData, hasFind, txt, features):
    kernelApi = web.kernelApi
    app = kernelApi.app
    api = app.api
    F = api.F

    annoSet = web.annoSet
    setData = web.toolData[TOOLKEY].sets[annoSet]

    submitter = templateData.submitter
    tokenStart = templateData.tokenstart
    tokenEnd = templateData.tokenend
    delData = templateData.adddata
    addData = templateData.adddata
    reportDel = templateData.reportdel
    reportAdd = templateData.reportadd
    modWidgetState = templateData.modwidgetstate

    deletions = delData.deletions
    additions = addData.additions
    freeVals = addData.freeVals

    hasEntity = txt != ""

    delButtonHtml = ""
    addButtonHtml = ""
    delContentHtml = []
    addContentHtml = []

    # Assigment of feature values

    if annoSet and hasEntity:
        for (i, feat) in enumerate(FEATURES):
            theseVals = sorted(setData.entityTextVal[feat].get(txt, set()))
            allVals = (
                sorted(x[0] for x in setData.entityFreq[feat])
                if feat in KEYWORD_FEATURES
                else theseVals
            )
            addVals = (
                additions[i] if additions is not None and len(additions) > i else set()
            )
            delVals = (
                deletions[i] if deletions is not None and len(deletions) > i else set()
            )
            freeVal = (
                freeVals[i] if freeVals is not None and len(freeVals) > i else None
            )
            default = featureDefault[feat](F, range(tokenStart, tokenEnd + 1))

            titleContent = H.div(
                H.i(f"{feat}:"),
                cls="feattitle",
            )

            delValuesContent = []
            addValuesContent = []

            for val in allVals:
                occurs = val in theseVals
                delSt = "minus" if val in delVals else "x"
                addSt = (
                    "plus"
                    if val in addVals
                    else "plus"
                    if val == default and freeVal != default
                    else "x"
                )

                if occurs:
                    delValuesContent.append(
                        H.div(
                            [
                                H.span(
                                    val or H.nb, cls=f"{feat}_sel", st=delSt, val=val
                                ),
                            ],
                            cls=f"{feat}_w modval",
                        )
                    )
                addValuesContent.append(
                    H.div(
                        [
                            H.span(val or H.nb, cls=f"{feat}_sel", st=addSt, val=val),
                        ],
                        cls=f"{feat}_w modval",
                    )
                )

            init = "" if default in theseVals else default
            val = (
                init
                if submitter == "lookupq"
                else freeVal
                if freeVal is not None and freeVal not in theseVals
                else init
            )
            addSt = (
                "plus"
                if submitter == "lookupq" and val
                else "plus"
                if val == freeVal
                else "plus"
                if init and len(theseVals) == 0
                else "x"
            )

            addValuesContent.append(
                H.div(
                    [H.input(type="text", st=addSt, value=val, origval=val)],
                    cls="modval",
                )
            )

            delContentHtml.append(
                H.div(
                    titleContent,
                    H.div(delValuesContent, cls="modifyvalues"),
                    cls="delfeat",
                    feat=feat,
                )
            )
            addContentHtml.append(
                H.div(
                    titleContent,
                    H.div(addValuesContent, cls="modifyvalues"),
                    cls="addfeat",
                    feat=feat,
                )
            )

        delButtonHtml = H.span(
            H.button("Delete", type="button", id="delgo", value="v", cls="special"),
            H.input(type="hidden", id="deldata", name="deldata", value=""),
        )
        addButtonHtml = H.span(
            H.button("Add", type="button", id="addgo", value="v", cls="special"),
            H.input(type="hidden", id="adddata", name="adddata", value=""),
        )

        templateData.modifyentity = H.join(
            H.input(
                type="hidden",
                id="modwidgetstate",
                name="modwidgetstate",
                value=modWidgetState,
            ),
            H.div(
                H.div(reportDel, id="delreport", cls="report"),
                H.div(
                    H.button(
                        "↓",
                        type="button",
                        id="delwidgetswitch",
                        title="show controls for adding items",
                        cls="altm",
                    ),
                    delButtonHtml,
                    H.span("", id="delfeedback", cls="feedback"),
                    H.button(
                        "⌫",
                        type="button",
                        id="delresetbutton",
                        title="clear values in form",
                        cls="altm",
                    ),
                    id="modifyhead",
                ),
                H.div(
                    delContentHtml,
                    cls="assignwidget",
                ),
                id="delwidget",
            ),
            H.div(
                H.div(reportAdd, id="addreport", cls="report"),
                H.div(
                    H.button(
                        "↑",
                        type="button",
                        id="addwidgetswitch",
                        title="show controls for deleting items",
                        cls="altm",
                    ),
                    addButtonHtml,
                    H.span("", id="addfeedback", cls="feedback"),
                    H.button(
                        "⌫",
                        type="button",
                        id="addresetbutton",
                        title="clear values in form",
                        cls="altm",
                    ),
                    id="modifyhead",
                ),
                H.div(
                    addContentHtml,
                    cls="assignwidget",
                ),
                id="addwidget",
            ),
        )


def wrapFindStat(nSent, nFind, hasFind):
    n = f"{nFind} of {nSent}" if hasFind else nSent
    return H.span(n, cls="stat")


def wrapEntityStat(val, thisNVisible, thisNEnt, hasFind):
    na = thisNEnt[val]
    n = (
        (H.span(f"{thisNVisible[val]} of ", cls="filted") + f"{na}")
        if hasFind
        else f"{na}"
    )
    return H.span(n, cls="stat")


def wrapActive(web, templateData):
    activeVal = templateData.activeval

    templateData.activevalrep = H.join(
        H.input(
            type="hidden", id=f"{feat}_active", name=f"{feat}_active", value=val or ""
        )
        for (feat, val) in activeVal
    )


def wrapReport(templateData, report, kind):
    templateData[f"report{kind}"] = H.join(
        H.span(line, cls="report") for line in report
    )
    report.clear()


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
