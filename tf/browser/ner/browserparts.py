"""Wraps various pieces into HTML.
"""

from .settings import EMPTY, NONE, SORTDIR_ASC, getText
from .html import H
from .helpers import repIdent, valRep


def wrapMessages(messages):
    """HTML for messages."""
    return H.p((H.span(text, cls=lev) + H.br() for (lev, text) in messages))


def wrapAnnoSets(annoDir, chosenAnnoSet, annoSets):
    """HTML for the annoset chooser.

    It is a list of buttons, each corresponding to an existing annoset.
    A click on the button selects that annoset.
    There is also a control to delete the annoset.

    Apart from these buttons there is a button to switch to the entities that are
    present in the TF dataset as nodes of the entity type specified
    in the yaml file with corresponding
    features.

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


def wrapQuery(annotate, templateData):
    """HTML for the query line.

    Parameters
    ----------

    Returns
    -------
    html string
        The finished HTML of the query parameters
    """
    wrapAppearance(annotate, templateData)
    hasFind = wrapFilter(annotate, templateData)
    (txt, eTxt) = wrapEntityInit(annotate, templateData)
    wrapEntityText(templateData, txt, eTxt)
    scope = wrapScope(annotate, templateData, hasFind, txt, eTxt)
    wrapEntityFeats(annotate, templateData, hasFind, txt, eTxt, scope)
    wrapEntityModReport(annotate, templateData)
    wrapEntityModify(annotate, templateData, hasFind, txt, eTxt)


def wrapAppearance(annotate, templateData):
    settings = annotate.settings
    features = settings.features

    formattingDo = templateData.formattingdo
    formattingState = templateData.formattingstate
    templateData.formattingbuttons = H.join(
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
                for feat in features + ("_stat_", "_entity_")
            ],
            id="decoratewidget",
        ),
        sep=" ",
    )


def wrapFilter(annotate, templateData):
    setData = annotate.getSetData()

    nFind = templateData.nfind
    bFind = templateData.bfind
    bFindC = templateData.bfindc
    bFindRe = templateData.bfindre
    bFindError = templateData.bfinderror

    hasFind = bFindRe is not None

    nBuckets = len(setData.buckets or [])

    templateData.find = H.join(
        H.input(type="text", name="bfind", id="bfind", value=bFind),
        H.input(
            type="hidden", name="bfindc", id="bfindc", value="v" if bFindC else "x"
        ),
        H.button(
            "C" if bFindC else "¢",
            type="submit",
            id="bfindb",
            title="using case SENSITIVE search"
            if bFindC
            else "using case INSENSITIVE search",
            cls="alt",
        ),
        " ",
        wrapFindStat(nBuckets, nFind, hasFind),
        " ",
        H.button("❌", type="submit", id="findclear", cls="altm"),
        " ",
        H.span(bFindError, id="bfinderror", cls="error"),
        " ",
        H.button("🔎", type="submit", id="lookupf", cls="altm"),
    )
    return hasFind


def wrapEntityInit(annotate, templateData):
    settings = annotate.settings
    features = settings.features

    F = annotate.F

    activeEntity = templateData.activeentity
    tokenStart = templateData.tokenstart
    tokenEnd = templateData.tokenend

    hasEnt = activeEntity is not None
    hasOcc = tokenStart is not None and tokenEnd is not None

    if hasEnt:
        templateData.tokenstart = None
        templateData.tokenend = None
        txt = ""
        eTxt = repIdent(features, activeEntity, active="active")
    elif hasOcc:
        templateData.activeentity = None
        txt = (
            getText(F, range(tokenStart, tokenEnd + 1))
            if tokenStart and tokenEnd
            else ""
        )
        eTxt = ""
    else:
        templateData.activeentity = None
        templateData.tokenstart = None
        templateData.tokenend = None
        txt = ""
        eTxt = ""

    templateData.activeentityrep = "⊙".join(activeEntity) if activeEntity else ""
    tokenStart = templateData.tokenstart
    tokenEnd = templateData.tokenend

    startRep = H.input(
        type="hidden", name="tokenstart", id="tokenstart", value=tokenStart or ""
    )
    endRep = H.input(
        type="hidden", name="tokenend", id="tokenend", value=tokenEnd or ""
    )
    templateData.entityinit = startRep + endRep

    return (txt, eTxt)


def wrapEntityHeaders(annotate, sortKey, sortDir):
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
    settings = annotate.settings
    features = settings.features

    sortKeys = ((feat, f"sort_{i}") for (i, feat) in enumerate(features))

    content = [
        H.input(type="hidden", name="sortkey", id="sortkey", value=sortKey),
        H.input(type="hidden", name="sortdir", id="sortdir", value=sortDir),
    ]

    for label, key in (("frequency", "freqsort"), *sortKeys):
        hl = " active " if key == sortKey else ""
        theDir = sortDir if key == sortKey else SORTDIR_ASC
        theArrow = "↑" if theDir == SORTDIR_ASC else "↓"
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

    return H.p(content)


def wrapEntityText(templateData, txt, eTxt):
    freeState = templateData.freestate

    title = "choose: free, intersecting with other entities, or all"
    templateData.entitytext = H.join(
        H.span(txt if txt else eTxt or "", id="qtextentshow"),
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


def wrapEntityFeats(annotate, templateData, hasFind, txt, eTxt, scope):
    settings = annotate.settings
    bucketType = settings.bucketType
    features = settings.features

    setData = annotate.getSetData()

    nEnt = templateData.nent
    nVisible = templateData.nvisible
    valSelect = templateData.valselect
    (scopeInit, scopeFilter) = scope

    hasOcc = txt != ""
    hasEnt = eTxt != ""

    featuresW = {
        feat: valSelect[feat] if hasEnt else setData.entityTextVal[feat].get(txt, set())
        for feat in features
    }
    content = []

    for feat, theseVals in featuresW.items():
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

        if hasEnt or hasOcc:
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
            H.p(H.span(f"{total} {bucketType}(s)")),
        ),
        H.div(content, id="selectsubwidget"),
        id="selectwidget",
    )


def wrapScope(annotate, templateData, hasFind, txt, eTxt):
    settings = annotate.settings
    bucketType = settings.bucketType
    annoSet = annotate.annoSet
    scope = templateData.scope
    hasOcc = txt != ""
    hasEnt = eTxt != ""

    scopeInit = H.input(type="hidden", id="scope", name="scope", value=scope)
    scopeFilter = ""

    if annoSet and (hasOcc or hasEnt):
        # Scope of modification

        scopeFilter = (
            H.span(
                H.button(
                    "filtered",
                    type="button",
                    id="scopefiltered",
                    title=f"act on filtered {bucketType}s only",
                ),
                " ",
                H.button(
                    "all",
                    type="button",
                    id="scopeall",
                    title=f"act on all {bucketType}s",
                ),
            )
            if hasFind
            else ""
        )

    return (scopeInit, scopeFilter)


def wrapExceptions(annotate, txt, eTxt):
    settings = annotate.settings
    bucketType = settings.bucketType
    annoSet = annotate.annoSet
    hasOcc = txt != ""
    hasEnt = eTxt != ""

    scopeExceptions = ""

    if annoSet and (hasOcc or hasEnt):
        scopeExceptions = H.span(
            H.nb,
            H.button(
                "✅",
                type="button",
                id="selectall",
                title=f"select all occurences in filtered {bucketType}s",
                cls="alt",
            ),
            " ",
            H.button(
                "❌",
                type="button",
                id="selectnone",
                title=f"deselect all occurences in filtered {bucketType}s",
                cls="alt",
            ),
        )

    return scopeExceptions


def wrapEntityModReport(annotate, templateData):
    reportDel = templateData.reportdel
    reportAdd = templateData.reportadd
    templateData.modifyreport = H.join(
        H.div(reportDel, id="delreport", cls="report"),
        H.div(reportAdd, id="addreport", cls="report"),
    )


def wrapEntityModify(annotate, templateData, hasFind, txt, eTxt):
    settings = annotate.settings
    features = settings.features
    keywordFeatures = settings.keywordFeatures

    setData = annotate.getSetData()
    annoSet = annotate.annoSet
    F = annotate.F

    submitter = templateData.submitter
    activeEntity = templateData.activeentity
    tokenStart = templateData.tokenstart
    tokenEnd = templateData.tokenend
    delData = templateData.adddata
    addData = templateData.adddata
    modWidgetState = templateData.modwidgetstate
    excludedTokens = templateData.excludedtokens

    deletions = delData.deletions
    additions = addData.additions
    freeVals = addData.freeVals

    hasOcc = txt != ""
    hasEnt = eTxt != ""

    delButtonHtml = ""
    addButtonHtml = ""
    delContentHtml = []
    addContentHtml = []

    # Assigment of feature values

    if annoSet and (hasOcc or hasEnt):
        instances = wrapExceptions(annotate, txt, eTxt)

        for i, feat in enumerate(features):
            isKeyword = feat in keywordFeatures
            theseVals = (
                {activeEntity[i]}
                if hasEnt
                else sorted(setData.entityTextVal[feat].get(txt, set()))
            )
            allVals = (
                sorted(x[0] for x in setData.entityFreq[feat])
                if isKeyword
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
            default = (
                activeEntity[i]
                if hasEnt
                else annotate.featureDefault[feat](F, range(tokenStart, tokenEnd + 1))
                if hasOcc
                else {}
            )

            titleContent = H.div(
                H.i(f"{feat}:"),
                cls="feattitle",
            )

            delValuesContent = []
            addValuesContent = []

            for val in allVals:
                occurs = val in theseVals
                delSt = "minus" if hasEnt or val in delVals else "x"
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
                addVals[0]
                if len(addVals) and submitter in {"lookupn", "freebutton"}
                else init
                if submitter == "lookupq"
                else freeVal
                if freeVal is not None
                else init
            )
            addSt = (
                "plus"
                if val and len(addVals) and submitter in {"lookupn", "freebutton"}
                else "plus"
                if submitter == "lookupq" and val
                else "plus"
                if val == freeVal
                else "plus"
                if init and len(theseVals) == 0
                else "x"
            )
            if (isKeyword and val in allVals) or val is None:
                val = ""
                addSt = "x"

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
            H.button("x", type="button", id="delgo", value="v", cls="special"),
            H.input(type="hidden", id="deldata", name="deldata", value=""),
        )
        addButtonHtml = H.span(
            H.button("+", type="button", id="addgo", value="v", cls="special"),
            H.input(type="hidden", id="adddata", name="adddata", value=""),
        )
        delResetHtml = H.button(
            "⌫",
            type="button",
            id="delresetbutton",
            title="clear values in form",
            cls="altt",
        )
        addResetHtml = H.button(
            "⌫",
            type="button",
            id="addresetbutton",
            title="clear values in form",
            cls="altt",
        )

        templateData.modifyentity = H.div(
            H.input(
                type="hidden",
                id="modwidgetstate",
                name="modwidgetstate",
                value=modWidgetState,
            ),
            H.input(
                type="hidden",
                id="excludedtokens",
                name="excludedtokens",
                value=",".join(str(t) for t in excludedTokens),
            ),
            H.div(
                H.span(
                    H.span(delButtonHtml, delResetHtml, id="modifyhead"),
                    H.span(delContentHtml, cls="assignwidget"),
                ),
                H.span("", id="delfeedback", cls="feedback"),
                id="delwidget",
            ),
            H.div(
                H.span(
                    H.span(addButtonHtml, addResetHtml, id="modifyhead"),
                    H.span(addContentHtml, cls="assignwidget"),
                ),
                H.span("", id="addfeedback", cls="feedback"),
                id="addwidget",
            ),
            instances,
            id="modwidget",
        )


def wrapFindStat(nBuckets, nFind, hasFind):
    n = f"{nFind} of {nBuckets}" if hasFind else nBuckets
    return H.span(n, cls="stat")


def wrapEntityStat(val, thisNVisible, thisNEnt, hasFind):
    na = thisNEnt[val]
    n = (
        (H.span(f"{thisNVisible[val]} of ", cls="filted") + f"{na}")
        if hasFind
        else f"{na}"
    )
    return H.span(n, cls="stat")


def wrapActive(templateData):
    activeVal = templateData.activeval

    templateData.activevalrep = H.join(
        H.input(
            type="hidden", id=f"{feat}_active", name=f"{feat}_active", value=val or ""
        )
        for (feat, val) in activeVal
    )


def wrapReport(annotate, templateData, report, kind):
    settings = annotate.settings
    features = settings.features

    label = "Deletion" if kind == "del" else "Addition" if kind == "add" else ""
    templateData[f"report{kind}"] = H.join(
        H.div(
            H.join(
                H.div(f"{label}: {n} x {valRep(features, fVals)}")
                for (fVals, n) in line
            )
            if type(line) is tuple
            else line,
            cls="report",
        )
        for line in report
    )
    report.clear()
