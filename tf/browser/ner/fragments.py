"""Wraps various pieces into HTML.

This module generates HTML for various controls that appear in the TF browser.

To see how this fits among all the modules of this package, see
`tf.browser.ner.annotate` .
"""

from .settings import EMPTY, NONE, SORTDIR_ASC
from ..html import H
from .helpers import repIdent, valRep


class Fragments:
    def wrapMessages(self):
        """HTML for messages."""
        v = self.v
        messageSrc = v.messagesrc

        v.messages = H.p((H.span(text, cls=lev) + H.br() for (lev, text) in messageSrc))

    def wrapAnnoSets(self):
        """HTML for the annotation set chooser.

        It is a list of buttons, each corresponding to an existing annotation set.
        A click on the button selects that set.
        There is also a control to delete the set.

        Apart from these buttons there is a button to switch to the entities that are
        present in the TF dataset as nodes of the entity type specified
        in the YAML file with corresponding
        features.

        Finally, it is possible to create a new, empty annotation set.
        """
        annotate = self.annotate
        setNames = annotate.setNames
        settings = annotate.settings
        entitySet = settings.entitySet

        v = self.v
        chosenAnnoSet = v.annoset

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
                    for annoSet in [""] + sorted(setNames)
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

        v.annosets = H.p(content1, content2)

    def wrapQuery(self):
        """HTML for all control widgets on the page."""
        self.wrapAppearance()
        self.wrapFilter()
        self.wrapEntity()
        self.wrapEntityText()
        self.wrapScope()
        self.wrapEntityFeats()
        self.wrapEntityModReport()
        self.wrapEntityModify()

    def wrapAppearance(self):
        """HTML for the appearance widget.

        The appearance widget lets the user choose how inline entities should
        appear: with or without underlining, identifier, kind, frequency.
        """
        v = self.v
        annotate = self.annotate
        settings = annotate.settings
        features = settings.features

        formattingDo = v.formattingdo
        formattingState = v.formattingstate
        v.formattingbuttons = H.join(
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

    def wrapFilter(self):
        """HTML for the filter widget.

        The filter widget lets the user filter the buckets by a search pattern
        or the condition that the buckets contains entities (and the even more useful
        condition that the buckets do *not* contain entities).
        """
        v = self.v
        annotate = self.annotate
        setData = annotate.getSetData()

        bFind = v.bfind
        bFindC = v.bfindc
        bFindRe = v.bfindre
        bFindError = v.bfinderror
        anyEnt = v.anyent

        v.hasfilter = bFindRe is not None or anyEnt is not None
        v.nbuckets = len(setData.buckets or [])

        v.filterwidget = H.join(
            H.span(
                H.input(type="text", name="bfind", id="bfind", value=bFind),
                H.input(
                    type="hidden",
                    name="bfindc",
                    id="bfindc",
                    value="v" if bFindC else "x",
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
                self.wrapFindStat(),
                cls="filtercomponent",
            ),
        )

    def wrapEntity(self):
        """Basic data for the selected entity widget.

        The entity widget shows the occurrence or entity that is selected.
        This function computed the relevant values and stores them in
        hidden input elements.
        """
        v = self.v
        annotate = self.annotate
        settings = annotate.settings
        features = settings.features

        activeEntity = v.activeentity
        tokenStart = v.tokenstart
        tokenEnd = v.tokenend

        hasEnt = activeEntity is not None
        hasOcc = tokenStart is not None and tokenEnd is not None

        if hasEnt:
            v.tokenstart = None
            v.tokenend = None
            txt = ""
            eTxt = repIdent(features, activeEntity, active="active")
        elif hasOcc:
            v.activeentity = None
            txt = (
                annotate.getText(range(tokenStart, tokenEnd + 1))
                if tokenStart and tokenEnd
                else ""
            )
            eTxt = ""
        else:
            v.activeentity = None
            v.tokenstart = None
            v.tokenend = None
            txt = ""
            eTxt = ""

        v.activeentityrep = "⊙".join(activeEntity) if activeEntity else ""
        tokenStart = v.tokenstart
        tokenEnd = v.tokenend

        startRep = H.input(
            type="hidden", name="tokenstart", id="tokenstart", value=tokenStart or ""
        )
        endRep = H.input(
            type="hidden", name="tokenend", id="tokenend", value=tokenEnd or ""
        )
        v.entityinit = startRep + endRep

        v.txt = txt
        v.etxt = eTxt

    def wrapEntityHeaders(self):
        """HTML for the header of the entity table, dependent on the state of sorting."""
        v = self.v
        sortKey = v.sortkey
        sortDir = v.sortdir
        annotate = self.annotate
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
                        cls=f"alt{hl}",
                    ),
                    " ",
                ]
            )

        return H.p(content)

    def wrapEntityText(self):
        """HTML for the selected entity widget."""
        v = self.v

        freeState = v.freestate
        txt = v.txt
        eTxt = v.etxt

        title = "choose: free, intersecting with other entities, or all"
        v.entitytext = H.join(
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

    def wrapEntityFeats(self):
        """HTML for the entity feature value selection.

        All feature values of entities that occupy the selected occurrences are
        shown, with the possibility that the user selects some of these values,
        thereby selecting a subset of the original set of occurrences.
        """
        v = self.v
        annotate = self.annotate
        settings = annotate.settings
        bucketType = settings.bucketType
        features = settings.features

        setData = annotate.getSetData()

        txt = v.txt
        eTxt = v.etxt
        valSelect = v.valselect
        scopeInit = v.scopeinit
        scopeFilter = v.scopefilter

        hasOcc = txt != ""
        hasEnt = eTxt != ""

        featuresW = {
            feat: valSelect[feat]
            if hasEnt
            else setData.entityTextVal[feat].get(txt, set())
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
                            self.wrapEntityStat(val, feat),
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

        total = self.wrapEntityStat(None, "")
        v.selectentities = (
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

    def wrapScope(self):
        """HTML for the scope widget.

        The scope widget lets the user choose whether the add / del actions should
        be applied to all relevant buckets, or only to the filtered buckets.
        """
        v = self.v
        annotate = self.annotate
        annoSet = annotate.annoSet
        scope = v.scope
        hasFilter = v.hasfilter
        txt = v.txt
        eTxt = v.etxt
        hasOcc = txt != ""
        hasEnt = eTxt != ""

        scopeInit = H.input(type="hidden", id="scope", name="scope", value=scope)
        scopeFilter = ""

        if annoSet and (hasOcc or hasEnt):
            # Scope of modification

            scopeFilter = (
                H.span(
                    H.button("", type="button", id="scopebutton", title="", cls="alt")
                )
                if hasFilter
                else ""
            )

        v.scopeinit = scopeInit
        v.scopefilter = scopeFilter

    def wrapExceptions(self):
        """HTML for the select / deselect buttons.

        These buttons appear at the end of selected occurrences in the text displayed
        in the buckets.
        The user can select or deselect individual entities for the application of
        the add / del operations.
        """
        v = self.v
        txt = v.txt
        eTxt = v.etxt
        annotate = self.annotate
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
                    title=f"select all occurrences in filtered {bucketType}s",
                    cls="icon",
                ),
                " ",
                H.button(
                    "❌",
                    type="button",
                    id="selectnone",
                    title=f"deselect all occurrences in filtered {bucketType}s",
                    cls="icon",
                ),
            )

        return scopeExceptions

    def wrapEntityModify(self):
        """HTML for the add / del widget.

        This widget contains controls to specify which entity feature values
        should be added or deleted.

        Considerable effort is made to prefill these components with ergonomic
        values.
        """
        v = self.v
        annotate = self.annotate
        settings = annotate.settings
        features = settings.features
        keywordFeatures = settings.keywordFeatures

        featureDefault = annotate.featureDefault

        setData = annotate.getSetData()
        annoSet = annotate.annoSet

        txt = v.txt
        eTxt = v.etxt
        submitter = v.submitter
        activeEntity = v.activeentity
        tokenStart = v.tokenstart
        tokenEnd = v.tokenend
        delData = v.adddata
        addData = v.adddata
        modWidgetState = v.modwidgetstate
        excludedTokens = v.excludedtokens

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
            instances = self.wrapExceptions()

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
                    additions[i]
                    if additions is not None and len(additions) > i
                    else set()
                )
                delVals = (
                    deletions[i]
                    if deletions is not None and len(deletions) > i
                    else set()
                )
                freeVal = (
                    freeVals[i] if freeVals is not None and len(freeVals) > i else None
                )
                default = (
                    activeEntity[i]
                    if hasEnt
                    else featureDefault[feat](range(tokenStart, tokenEnd + 1))
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
                                        val or H.nb,
                                        cls=f"{feat}_sel",
                                        st=delSt,
                                        val=val,
                                    ),
                                ],
                                cls=f"{feat}_w modval",
                            )
                        )
                        hasSomeVals = True

                    addValuesContent.append(
                        H.div(
                            [
                                H.span(
                                    val or H.nb, cls=f"{feat}_sel", st=addSt, val=val
                                ),
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
            v.modifyentity = H.div(
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

    def wrapFindStat(self):
        """HTML for statistics.

        This is about totals of occurrences in all buckets versus in filtered
        buckets.
        """
        v = self.v
        nBuckets = v.nbuckets
        nFind = v.nfind
        hasFilter = v.hasfilter

        n = f"{nFind} of {nBuckets}" if hasFilter else nBuckets
        return H.span(n, cls="stat")

    def wrapEntityStat(self, val, feat):
        """HTML for statistics of feature values.

        This is about totals of occurrences of feature values in all buckets
        versus in filtered buckets.
        """
        v = self.v
        nVisible = v.nvisible
        nEnt = v.nent
        hasFilter = v.hasfilter

        thisNVisible = nVisible[feat]
        thisNEnt = nEnt[feat]

        na = thisNEnt[val]
        n = (
            (H.span(f"{thisNVisible[val]} of ", cls="filted") + f"{na}")
            if hasFilter
            else f"{na}"
        )
        return H.span(n, cls="stat")

    def wrapActive(self):
        """HTML for the active entity."""
        v = self.v

        activeVal = v.activeval

        v.activevalrep = H.join(
            H.input(
                type="hidden",
                id=f"{feat}_active",
                name=f"{feat}_active",
                value=val or "",
            )
            for (feat, val) in activeVal.items()
        )

    def wrapEntityModReport(self):
        """HTML for the combined report of add / del actions."""
        v = self.v
        reportDel = v.reportdel
        reportAdd = v.reportadd
        v.modifyreport = H.join(
            H.div(reportDel, id="delreport", cls="report"),
            H.div(reportAdd, id="addreport", cls="report"),
        )

    def wrapReport(self, report, kind):
        """HTML for the report of add / del actions."""
        v = self.v
        annotate = self.annotate
        settings = annotate.settings
        features = settings.features

        label = "Deletion" if kind == "del" else "Addition" if kind == "add" else ""
        v[f"report{kind}"] = H.join(
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
