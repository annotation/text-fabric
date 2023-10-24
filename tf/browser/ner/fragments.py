"""Wraps various pieces into HTML.

This module generates HTML for various controls that appear in the TF browser.

To see how this fits among all the modules of this package, see
`tf.browser.ner.annotate` .
"""

from .settings import EMPTY, NONE, SORTDIR_ASC
from .html import H
from .helpers import repIdent, valRep


def wrapMessages(messages):
    """HTML for messages."""
    return H.p((H.span(text, cls=lev) + H.br() for (lev, text) in messages))


def wrapAnnoSets(annoDir, chosenAnnoSet, annoSets, entitySet):
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
            cls="mono",
        ),
        " ",
        H.button(
            "++",
            type="submit",
            id="adup",
            title="duplicate this annotation set",
            cls="mono",
        ),
        " ",
        H.select(
            (
                H.option(
                    entitySet if annoSet == "" else annoSet,
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
                cls="mono",
            ),
            " ",
            H.button(
                "-",
                type="submit",
                id="adelete",
                title="delete current annotation set",
                cls="mono",
            ),
        ]
        if chosenAnnoSet
        else []
    )

    return H.p(content1, content2)


def wrapQuery(self, templateData):
    """HTML for the query line.

    Parameters
    ----------

    Returns
    -------
    html string
        The finished HTML of the query parameters
    """
    wrapAppearance(self, templateData)
    wrapFilter(self, templateData)
    wrapEntityInit(self, templateData)
    wrapEntityText(templateData)
    wrapScope(self, templateData)
    wrapEntityFeats(self, templateData)
    wrapEntityModReport(self, templateData)
    wrapEntityModify(self, templateData)


def wrapAppearance(self, templateData):
    settings = self.settings
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
                cls="mono",
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
                        cls="active" if formattingState[feat] else "",
                    ),
                )
                for feat in features + ("_stat_", "_entity_")
            ],
            id="decoratewidget",
        ),
        sep=" ",
    )


def wrapFilter(self, templateData):
    setData = self.getSetData()

    nFind = templateData.nfind
    bFind = templateData.bfind
    bFindC = templateData.bfindc
    bFindRe = templateData.bfindre
    bFindError = templateData.bfinderror
    anyEnt = templateData.anyent

    hasFilter = bFindRe is not None or anyEnt is not None

    nBuckets = len(setData.buckets or [])

    templateData.filterwidget = H.join(
        H.span(
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
                cls="mono",
            ),
            " ",
            H.button("❌", type="submit", id="findclear", cls="icon"),
            " ",
            H.span(bFindError, id="bfinderror", cls="error"),
            cls="filtercomponent",
        ),
        H.span(
            H.input(
                type="hidden",
                name="anyent",
                id="anyent",
                value="" if anyEnt is None else "v" if anyEnt else "x",
            ),
            H.button(
                "with or without"
                if anyEnt is None
                else "with"
                if anyEnt
                else "without",
                type="submit",
                id="anyentbutton",
                cls="mono",
            ),
            H.span(" marked entities"),
            cls="filtercomponent",
        ),
        H.span(
            H.button("🔎", type="submit", id="lookupf", cls="alt"),
            cls="filtercomponent",
        ),
        H.span(
            wrapFindStat(nBuckets, nFind, hasFilter),
            cls="filtercomponent",
        ),
    )
    templateData.hasfilter = hasFilter


def wrapEntityInit(self, templateData):
    settings = self.settings
    features = settings.features
    featureDefault = self.featureDefault
    getText = featureDefault[""]

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
            getText(range(tokenStart, tokenEnd + 1))
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

    templateData.txt = txt
    templateData.etxt = eTxt


def wrapEntityHeaders(self, sortKey, sortDir):
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
    settings = self.settings
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
                    cls=f"alt{hl}",
                ),
                " ",
            ]
        )

    return H.p(content)


def wrapEntityText(templateData):
    freeState = templateData.freestate
    txt = templateData.txt
    eTxt = templateData.etxt

    title = "choose: free, intersecting with other entities, or all"
    templateData.entitytext = H.join(
        H.span(txt if txt else eTxt or "", id="qtextentshow"),
        " ",
        H.button("❌", type="submit", id="queryclear", cls="icon"),
        " ",
        H.button(
            "✅",
            type="submit",
            id="lookupq",
            cls="icon",
            title="look up and fill in green fields",
        ),
        H.button(
            "❎",
            type="submit",
            id="lookupn",
            cls="icon",
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
            cls="mono",
            title=title,
        ),
    )


def wrapEntityFeats(self, templateData):
    settings = self.settings
    bucketType = settings.bucketType
    features = settings.features

    setData = self.getSetData()

    txt = templateData.txt
    eTxt = templateData.etxt
    hasFilter = templateData.hasfilter
    nEnt = templateData.nent
    nVisible = templateData.nvisible
    valSelect = templateData.valselect
    scopeInit = templateData.scopeinit
    scopeFilter = templateData.scopefilter

    hasOcc = txt != ""
    hasEnt = eTxt != ""

    featuresW = {
        feat: valSelect[feat] if hasEnt else setData.entityTextVal[feat].get(txt, set())
        for feat in features
    }
    content = []
    inputContent = []

    for feat, theseVals in featuresW.items():
        thisValSelect = valSelect[feat]

        valuesContent = []

        inputContent.append(
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
                        wrapEntityStat(val, nVisible[feat], nEnt[feat], hasFilter),
                        type="button",
                        name=val or EMPTY,
                        cls=f"{feat}_sel alt",
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

    total = wrapEntityStat(None, nVisible[""], nEnt[""], hasFilter)
    templateData.selectentities = (
        H.div(
            H.join(inputContent),
            H.div(
                H.span(H.b("Select"), scopeInit, scopeFilter),
                H.span(H.span(f"{total} {bucketType}(s)")),
            )
            if hasEnt
            else H.join(
                H.div(
                    H.p(H.b("Select"), scopeInit, scopeFilter),
                    H.p(H.span(f"{total} {bucketType}(s)")),
                ),
                H.div(content, id="selectsubwidget"),
            ),
            id="selectwidget",
        )
        if hasEnt or hasOcc
        else H.join(inputContent)
    )


def wrapScope(self, templateData):
    annoSet = self.annoSet
    scope = templateData.scope
    hasFilter = templateData.hasfilter
    txt = templateData.txt
    eTxt = templateData.etxt
    hasOcc = txt != ""
    hasEnt = eTxt != ""

    scopeInit = H.input(type="hidden", id="scope", name="scope", value=scope)
    scopeFilter = ""

    if annoSet and (hasOcc or hasEnt):
        # Scope of modification

        scopeFilter = (
            H.span(H.button("", type="button", id="scopebutton", title="", cls="alt"))
            if hasFilter
            else ""
        )

    templateData.scopeinit = scopeInit
    templateData.scopefilter = scopeFilter


def wrapExceptions(self, txt, eTxt):
    settings = self.settings
    bucketType = settings.bucketType
    annoSet = self.annoSet
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
                cls="icon",
            ),
            " ",
            H.button(
                "❌",
                type="button",
                id="selectnone",
                title=f"deselect all occurences in filtered {bucketType}s",
                cls="icon",
            ),
        )

    return scopeExceptions


def wrapEntityModReport(self, templateData):
    reportDel = templateData.reportdel
    reportAdd = templateData.reportadd
    templateData.modifyreport = H.join(
        H.div(reportDel, id="delreport", cls="report"),
        H.div(reportAdd, id="addreport", cls="report"),
    )


def wrapEntityModify(self, templateData):
    settings = self.settings
    features = settings.features
    keywordFeatures = settings.keywordFeatures

    setData = self.getSetData()
    annoSet = self.annoSet

    txt = templateData.txt
    eTxt = templateData.etxt
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

    somethingToDelete = True

    if annoSet and (hasOcc or hasEnt):
        instances = wrapExceptions(self, txt, eTxt)

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
                else self.featureDefault[feat](range(tokenStart, tokenEnd + 1))
                if hasOcc
                else {}
            )

            titleContent = H.div(
                H.i(f"{feat}:"),
                cls="feattitle",
            )

            delValuesContent = []
            addValuesContent = []

            hasSomeVals = False

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
                    hasSomeVals = True

                addValuesContent.append(
                    H.div(
                        [
                            H.span(val or H.nb, cls=f"{feat}_sel", st=addSt, val=val),
                        ],
                        cls=f"{feat}_w modval",
                    )
                )

            if not hasSomeVals:
                somethingToDelete = False

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
            H.button("Delete", type="button", id="delgo", value="v", cls="special"),
            H.input(type="hidden", id="deldata", name="deldata", value=""),
        )
        addButtonHtml = H.span(
            H.button("Add", type="button", id="addgo", value="v", cls="special"),
            H.input(type="hidden", id="adddata", name="adddata", value=""),
        )
        delResetHtml = H.button(
            "⌫",
            type="button",
            id="delresetbutton",
            title="clear values in form",
            cls="icon",
        )
        addResetHtml = H.button(
            "⌫",
            type="button",
            id="addresetbutton",
            title="clear values in form",
            cls="icon",
        )

        delWidgetContent = (
            H.div(
                H.span(
                    H.span(delButtonHtml, delResetHtml, id="modifyhead"),
                    H.span(delContentHtml, cls="assignwidget"),
                ),
                H.span("", id="delfeedback", cls="feedback"),
                id="delwidget",
            )
            if somethingToDelete
            else ""
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
            H.b("Modify"),
            instances,
            delWidgetContent,
            H.div(
                H.span(
                    H.span(addButtonHtml, addResetHtml, id="modifyhead"),
                    H.span(addContentHtml, cls="assignwidget"),
                ),
                H.span("", id="addfeedback", cls="feedback"),
                id="addwidget",
            ),
            id="modwidget",
        )


def wrapFindStat(nBuckets, nFind, hasFilter):
    n = f"{nFind} of {nBuckets}" if hasFilter else nBuckets
    return H.span(n, cls="stat")


def wrapEntityStat(val, thisNVisible, thisNEnt, hasFilter):
    na = thisNEnt[val]
    n = (
        (H.span(f"{thisNVisible[val]} of ", cls="filted") + f"{na}")
        if hasFilter
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


def wrapReport(self, templateData, report, kind):
    settings = self.settings
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
