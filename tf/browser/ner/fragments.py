"""Wraps various pieces into HTML.

This module generates HTML for various controls that appear in the TF browser.
"""

from ...ner.settings import EMPTY, NONE

from ..html import H

from .websettings import (
    SORTDIR_ASC,
    SORTDIR_DEFAULT,
    SORTKEY_DEFAULT,
    SORT_DEFAULT,
    repIdent,
    valRep,
)


class Fragments:
    def wrapMessages(self):
        """HTML for messages."""
        v = self.v
        messageSrc = v.messagesrc

        v.messages = H.p((H.span(text, cls=lev) + H.br() for (lev, text) in messageSrc))

    def wrapSets(self):
        """HTML for the annotation task chooser.

        It is a dropdown with options, each corresponding to an existing annotation task.
        There is also a control to delete the task.

        Apart from these buttons there is a button to switch to the entities that are
        present in the TF dataset as nodes of the entity type specified
        in the YAML file with corresponding
        features.

        Finally, it is possible to create a new, empty annotation task.
        """
        ner = self.ner
        taskNames = ner.getTasks()

        v = self.v
        chosenTask = v.task
        sheetCase = v.sheetcase

        content1 = [
            H.input(
                type="hidden",
                name="task",
                value=chosenTask,
                id="seth",
            ),
            H.input(
                type="hidden",
                name="duset",
                value="",
                id="duseth",
            ),
            H.input(
                type="hidden",
                name="rset",
                value="",
                id="rseth",
            ),
            H.button(
                "+",
                type="submit",
                id="anew",
                title="create a new annotation task",
                cls="mono",
            ),
            " ",
            H.button(
                "++",
                type="submit",
                id="adup",
                title="duplicate this annotation task",
                cls="mono",
            ),
            " ",
            H.select(
                (
                    H.option(
                        ner.setInfo(taskName)[0],
                        value=taskName,
                        selected=taskName == chosenTask,
                    )
                    for taskName in [""] + sorted(taskNames)
                ),
                cls="selinp",
                id="achange",
            ),
            " ",
            H.input(
                type="hidden",
                id="sheetcase",
                name="sheetcase",
                value="v" if sheetCase else "x",
            ),
            H.button(
                "C" if sheetCase else "¢",
                type="submit",
                id="sheetcasebutton",
                title="toggle case-sensitivity",
                cls="mono",
            ),
        ]

        content2 = (
            [
                H.input(
                    type="hidden",
                    name="dset",
                    value="",
                    id="dseth",
                ),
                H.button(
                    "→",
                    type="submit",
                    id="arename",
                    title="rename current annotation task",
                    cls="mono",
                ),
                " ",
                H.button(
                    "-",
                    type="submit",
                    id="adelete",
                    title="delete current annotation task",
                    cls="mono",
                ),
            ]
            if not (chosenTask == "" or chosenTask.startswith("."))
            else []
        )

        v.tasks = H.p(content1, content2)

    def wrapCaption(self):
        """HTML for the caption of the entity list."""
        v = self.v
        ner = self.ner
        setNameRep = ner.setNameRep
        setIsSrc = ner.setIsSrc
        setIsRo = ner.setIsRo
        v.caption = H.p(H.b(setNameRep)) + H.p(
            "Entities as "
            + (
                "given in the source"
                if setIsSrc
                else "specified by a spreadsheet" if setIsRo else "marked up by hand"
            )
        )

    def wrapLogs(self):
        """HTML for the log messages produced when processing a sheet."""
        v = self.v
        ner = self.ner
        sheetData = ner.getSheetData()
        logData = sheetData.logData or []

        v.logs = "\n".join(
            H.p(
                H.nb * indent + msg,
                cls="msg "
                + ("special" if isError is None else "error" if isError else "info"),
            )
            for (isError, indent, msg) in logData
        )

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
        ner = self.ner
        settings = ner.settings
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
                            (
                                "stats"
                                if feat == "_stat_"
                                else "underlining" if feat == "_entity_" else feat
                            ),
                            feat=feat,
                            type="button",
                            title=(
                                "toggle display of statistics"
                                if feat == "_stat_"
                                else (
                                    "toggle formatting of entities"
                                    if feat == "_entity"
                                    else f"toggle formatting for feature {feat}"
                                )
                            ),
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
        ner = self.ner
        setData = ner.getSetData()

        bFind = v.bfind
        bFindC = v.bfindc
        bFindRe = v.bfindre
        bFindError = v.bfinderror
        anyEnt = v.anyent

        v.hasfilter = bFindRe is not None or anyEnt is not None
        v.nbuckets = len(setData.buckets or [])

        v.filterwidget = H.div(
            (
                H.b("Filter"),
                H.join(
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
                            title=(
                                "using case SENSITIVE search"
                                if bFindC
                                else "using case INSENSITIVE search"
                            ),
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
                            (
                                "with or without"
                                if anyEnt is None
                                else "with" if anyEnt else "without"
                            ),
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
                ),
            ),
            id="filterwidget",
        )

    def wrapEntity(self):
        """Basic data for the selected entity widget.

        The entity widget shows the occurrence or entity that is selected.
        This function computed the relevant values and stores them in
        hidden input elements.
        """
        v = self.v
        ner = self.ner
        settings = ner.settings
        features = settings.features

        activeEntity = v.activeentity
        activeTrigger = v.activetrigger
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
            v.activetrigger = None
            txt = (
                ner.textFromSlots(range(tokenStart, tokenEnd + 1))
                if tokenStart and tokenEnd
                else ""
            )
            eTxt = ""
        else:
            v.activeentity = None
            v.activetrigger = None
            v.tokenstart = None
            v.tokenend = None
            txt = ""
            eTxt = ""

        v.activeentityrep = "⊙".join(activeEntity) if activeEntity else ""
        v.activetriggerrep = "⊙".join(activeTrigger) if activeTrigger else ""
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

        if not sortKey and not sortDir:
            (sortKey, sortDir) = SORT_DEFAULT
        else:
            if not sortKey:
                sortKey = SORTKEY_DEFAULT
            if not sortDir:
                sortDir = SORTDIR_DEFAULT

        ner = self.ner
        settings = ner.settings
        features = settings.features
        setIsX = ner.setIsX

        sortKeys = (
            (("name", "sort_0"),)
            if setIsX
            else ((feat, f"sort_{i}") for (i, feat) in enumerate(features))
        )

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

        content.append(self.wrapSubtle())

        return H.p(content)

    def wrapSubtle(self):
        """HTML for the button to filter the entity list by scoped/nonscoped triggers."""
        v = self.v
        subtleFilter = v.subtlefilter
        ner = self.ner
        setIsX = ner.setIsX

        return H.span(
            H.input(
                type="hidden",
                name="subtlefilter",
                id="subtlefilter",
                value="" if subtleFilter is None else "v" if subtleFilter else "x",
            ),
            (
                ""
                if not setIsX
                else H.button(
                    (
                        "all scopes"
                        if subtleFilter is None
                        else "scoped" if subtleFilter else "unscoped"
                    ),
                    type="submit",
                    id="subtlefilterbutton",
                    cls="mono",
                )
            ),
            cls="subtlefilter",
        )

    def wrapEntityText(self):
        """HTML for the selected entity widget."""
        v = self.v
        ner = self.ner
        setIsX = ner.setIsX

        freeState = v.freestate
        txt = v.txt
        eTxt = v.etxt

        title = "choose: free, intersecting with other entities, or all"
        v.entitytext = (
            ""
            if setIsX
            else H.div(
                (
                    H.b("Mark"),
                    H.span(
                        H.join(
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
                            H.input(
                                type="hidden",
                                name="freestate",
                                id="freestate",
                                value=freeState,
                            ),
                            H.button(
                                (
                                    "⚭ intersecting"
                                    if freeState == "bound"
                                    else "⚯ free" if freeState == "free" else "⚬ all"
                                ),
                                type="submit",
                                id="freebutton",
                                cls="mono",
                                title=title,
                            ),
                        ),
                        id="etextwidget",
                    ),
                ),
                id="markwidget",
            )
        )

    def wrapEntityFeats(self):
        """HTML for the entity feature value selection.

        All feature values of entities that occupy the selected occurrences are
        shown, with the possibility that the user selects some of these values,
        thereby selecting a subset of the original set of occurrences.
        """
        v = self.v
        ner = self.ner
        setIsX = ner.setIsX
        bucketType = ner.bucketType
        settings = ner.settings
        features = settings.features

        setData = ner.getSetData()

        txt = v.txt
        eTxt = v.etxt
        valSelect = v.valselect
        scopeInit = v.scopeinit
        scopeFilter = v.scopefilter

        hasOcc = txt != ""
        hasEnt = eTxt != ""

        featuresW = {
            feat: (
                valSelect[feat]
                if hasEnt
                else setData.entityTextVal[feat].get(txt, set())
            )
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
                            title=(
                                f"{feat} not marked"
                                if val == NONE
                                else f"{feat} marked as {val}"
                            ),
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
                (
                    H.div(
                        H.span("" if setIsX else H.b("Select"), scopeInit, scopeFilter),
                        H.span(H.span(f"{total} {bucketType}(s)")),
                    )
                    if hasEnt
                    else H.join(
                        H.div(
                            H.p(H.b("Select"), scopeInit, scopeFilter),
                            H.p(H.span(f"{total} {bucketType}(s)")),
                        ),
                        H.div(content, id="selectsubwidget"),
                    )
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
        ner = self.ner
        setIsRo = ner.setIsRo
        scope = v.scope
        hasFilter = v.hasfilter
        txt = v.txt
        eTxt = v.etxt
        hasOcc = txt != ""
        hasEnt = eTxt != ""

        scopeInit = H.input(type="hidden", id="scope", name="scope", value=scope)
        scopeFilter = ""

        if (not setIsRo) and (hasOcc or hasEnt):
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
        ner = self.ner
        bucketType = ner.bucketType
        setIsRo = ner.setIsRo
        hasOcc = txt != ""
        hasEnt = eTxt != ""

        scopeExceptions = ""

        if (not setIsRo) and (hasOcc or hasEnt):
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
        ner = self.ner
        settings = ner.settings
        features = settings.features
        keywordFeatures = settings.keywordFeatures

        featureDefault = ner.featureDefault

        setData = ner.getSetData()
        setIsRo = ner.setIsRo

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

        if (not setIsRo) and (hasOcc or hasEnt):
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
                    else (
                        featureDefault[feat](range(tokenStart, tokenEnd + 1))
                        if hasOcc
                        else {}
                    )
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
                        else "plus" if val == default and freeVal != default else "x"
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
                    else (
                        init
                        if submitter == "lookupq"
                        else freeVal if freeVal is not None else init
                    )
                )
                addSt = (
                    "plus"
                    if val and len(addVals) and submitter in {"lookupn", "freebutton"}
                    else (
                        "plus"
                        if submitter == "lookupq" and val
                        else (
                            "plus"
                            if val == freeVal
                            else "plus" if init and len(theseVals) == 0 else "x"
                        )
                    )
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
        ner = self.ner
        settings = ner.settings
        features = settings.features

        label = "Deletion" if kind == "del" else "Addition" if kind == "add" else ""
        v[f"report{kind}"] = H.join(
            H.div(
                (
                    H.join(
                        H.div(f"{label}: {n} x {valRep(features, fVals)}")
                        for (fVals, n) in line
                    )
                    if type(line) is tuple
                    else line
                ),
                cls="report",
            )
            for line in report
        )
        report.clear()
