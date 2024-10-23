"""Management of NER spreadsheets.

NER spreadsheets contain information about named entities and the
trigger strings by which they can be found in the corpus.
"""

import re
import time
import pickle
import gzip

from ..parameters import GZIP_LEVEL, PICKLE_PROTOCOL
from ..capable import CheckImport
from ..core.generic import AttrDict
from ..core.helpers import console
from ..core.files import fileOpen, dirContents, extNm, fileExists, mTime

from .helpers import tnorm, normalize, toSmallId, toTokens

from .scopes import Scopes, partitionScopes
from .triggers import Triggers


DS_STORE = ".DS_Store"
SHEET_RE = re.compile(r"""^([0-9]+)((?:-[0-9]+)?)\.xlsx$""", re.I)

SHEET_KEYS = """
    caseSensitive
    metaFields
    metaData
    logData
    nameMap
    scopeMap
    rowMap
    instructions
    inventory
    triggerFromMatch
    triggerScopes
    allTriggers
    hitData
""".strip().split()
"""Keys by which the data of a NER sheet is organized.

*   `caseSensitive`: boolean, whether to look for triggers in the corpus in a
    case-sensitive way;
*   `metaFields`: the list of colums in the NER spreadsheet that are not involved
    in entity lookup: this is the metadata of an entity;
*   `metaData`: the metadata of an entity as dictionary;
*   `logData`: the collected messages issues while reading and processing a NER sheet;
*   `nameMap`: mapping from entities to names;
*   `scopeMap`: mapping from scope strings to scope data structures;
*   `rowMap`: mapping from triggers to the rows where they occur;
*   `instructions`: compiled search instructions to search for all triggers
    simultaneously; more precisely, it is a mapping from intervals to tuples of
    three dictionaries:

    *   `tPos`: dictionary that maps positions to tokens that a trigger may
        have in that position to the set of triggers that have that token in
        that position;
    *   `tMap`: a mapping from triggers to scopes; the idea is that in every
        interval all triggers that are active in that interval have exactly one scope
        that includes that interval; the mapping gives that scope;
    *   `idMap`: a mapping from triggers to entities; given a trigger that is
        active in an interval, and given its scope in that interval, there is
        exactly one entity that is triggered; the eid and kind of that entity
        identify it and is the value;

*   `inventory`: complete result of the search for triggers;
*   `triggerFromMatch`: mapping for each match in the corpus which trigger was matched
    in what scope;
*   `triggerScopes`: for each trigger, the set of its scopes where it is used is stored;
*   `allTriggers`: the set of all triggers, more precisely, the set of all
    trigger-entity-scope combinations;
*   `hitData`: overview of the inventory (see above).
"""

CLEAR_KEYS = """
    raw
    compiled
""".strip().split()


class Sheets(Scopes, Triggers):
    def __init__(self, sheets=None):
        """Handling of NER spreadsheets.

        A NER spreadsheet contains entity information; in particular it links
        named entities to triggers by which they can be found in the corpus.

        See `readSheetData()` for the description of the shape of the spreadsheet,
        which is expected to be an Excel sheet.

        Parameters
        ----------
        sheets: dict, optional None
            Sheet data to start with. Relevant for when the TF browser uses this class.
            See `tf.ner.ner.NER`
        """
        CI = CheckImport("openpyxl")

        if CI.importOK(hint=True):
            openpyxl = CI.importGet()
            self.loadXls = openpyxl.load_workbook
            self.Workbook = openpyxl.Workbook
        else:
            self.properlySetup = False
            return None

        self.properlySetup = True
        self.scopeI = 3
        self.trigI = 4
        self.commentI = 0

        # browse = self.browse
        self.sheets = sheets
        settings = self.settings
        self.spaceEscaped = settings.spaceEscaped
        self.transform = settings.transform
        keywordFeatures = settings.keywordFeatures
        kindFeature = keywordFeatures[0]
        self.kindFeature = kindFeature
        defaultValues = settings.defaultValues
        self.defaultKind = defaultValues.get(kindFeature, "")

        self.sheetName = None
        """The current NER sheet."""

        self.sheetNames = set()
        """The set of names of NER sheets that are present on the file system."""

        self.readSheets()

    def getToTokensFunc(self):
        """Make a tokenize function.

        Produce a function that can tokenize strings in the same way as the corpus
        has been tokenized.

        Returns
        -------
        function
            This function takes a string and returns an iterable of tokens.
            The tokenization is aware of whether the current sheet works
            case-sensitively, and whether spaces have been escaped as underscores.
        """
        settings = self.settings
        spaceEscaped = settings.spaceEscaped
        sheetData = self.getSheetData()
        caseSensitive = sheetData.caseSensitive

        def myToTokens(trigger):
            return toTokens(
                trigger, spaceEscaped=spaceEscaped, caseSensitive=caseSensitive
            )

        return myToTokens

    def readSheets(self):
        """Read the list current ner sheets (again).

        Use this when you change ner sheets outside the NER browser, e.g.
        by editing the spreadsheets in Excel.
        """
        sheetDir = self.sheetDir
        setNames = self.setNames

        sheetNames = set()
        self.sheetNames = sheetNames

        for sheetFile in dirContents(sheetDir)[0]:
            if extNm(sheetFile) == "xlsx":
                sheetName = sheetFile.removesuffix(".xlsx")
                sheetNames.add(sheetName)
                setNames.add(f".{sheetName}")

    def setSheet(self, newSheet, force=False, caseSensitive=None, forceSilent=False):
        """Switch to a named ner sheet.

        After the switch, the new sheet will be loaded into memory, processed, and
        executed.

        Parameters
        ----------
        newSheet: string
            The name of the new ner sheet to switch to.
        force: boolean, optional False
            If True, do not load from cached data, but do all computations afresh.
        caseSensitive: boolean, optional None
            Whether to work with the spreadsheet in a case-sensitive way.
            If `None`, the value is taken from the current instance of this class.
        forceSilent: boolean, optional False
            If True, all output is suppressed, irrespective of the `silent` member
            in the instance. Only show stopping error messages are let through.

        """
        if not self.properlySetup:
            return

        browse = self.browse

        sheetName = self.sheetName

        sheetNames = self.sheetNames
        sheetDir = self.sheetDir
        sheetFile = f"{sheetDir}/{newSheet}.xlsx"

        if newSheet not in sheetNames and not fileExists(sheetFile):
            if not browse:
                console(f"NER sheet {newSheet} ({sheetFile}) does not exist")
            if newSheet is not None:
                return

        # if not browse:
        #    self.setSet("" if newSheet is None else f".{newSheet}")

        if newSheet != sheetName:
            sheetName = newSheet
            self.sheetName = sheetName

        if caseSensitive is None:
            caseSensitive = self.caseSensitive

        self.forceSilent = True
        self.loadSheetData(force=force, caseSensitive=caseSensitive)

    def loadSheetData(self, force=False, caseSensitive=False):
        """Loads the current ner sheet into memory, if there is one.

        If the current ner sheet is None, nothing has to be done.

        Otherwise, we read the corresponding excel sheet(s) from disk and compile them
        into instructions, if needed.

        When loading a sheet, it will be checked first whether its data is already
        in memory and uptotdate, in that case nothing will be done.

        Otherwise, it will be checked wether an uptodate version of its data exists
        on disk. If so, it will be loaded.

        Otherwise, or if `force=True` is passed, the data will be computed from
        scratch and saved to disk, with a time stamp.

        Parameters
        ----------
        force: boolean, optional False
            If True, do not load from cached data, but do all computations afresh.
        caseSensitive: boolean, optional False
            Whether to work with the spreadsheet in a case-sensitive way.
        """
        if not self.properlySetup:
            return

        sheetName = self.sheetName
        setName = self.setName
        annoDir = self.annoDir
        setDir = f"{annoDir}/{setName}"
        dataFile = f"{setDir}/data.gz"
        timeFile = f"{setDir}/time.txt"
        timeKey = "time"

        if sheetName is None:
            return None

        forceSilent = self.forceSilent
        sheets = self.sheets

        if sheetName not in sheets:
            sheets[sheetName] = AttrDict()

        browse = self.browse
        sheetData = self.getSheetData()
        sheetDir = self.sheetDir
        sheetFile = f"{sheetDir}/{sheetName}.xlsx"
        sheetExists = fileExists(sheetFile)
        sheetUpdated = mTime(sheetFile) if sheetExists else 0
        needReload = (
            force
            or sheetData.caseSensitive != caseSensitive
            or sheetData.get(timeKey, 0) < sheetUpdated
        )

        showLog = True

        if needReload:
            # try to load from zipped data file first
            tm = 0
            dataUptodate = not force and fileExists(timeFile)

            if dataUptodate:
                with fileOpen(timeFile) as fh:
                    info = fh.read().strip()
                try:
                    tm = float(info)
                    dataUptodate = sheetUpdated < tm
                except Exception:
                    dataUptodate = False

            # only load if that data exists and is still up to date

            if dataUptodate:
                if fileExists(dataFile):
                    with gzip.open(dataFile, mode="rb") as f:
                        data = pickle.load(f)

                    if data["caseSensitive"] != caseSensitive:
                        loaded = False
                    else:
                        for k in CLEAR_KEYS:
                            if k in sheetData:
                                sheetData[k].clear()

                        for k in SHEET_KEYS:
                            v = data.get(k, None)

                            if v is None:
                                if k in sheetData:
                                    if type(sheetData[k]) in {list, dict, set}:
                                        sheetData[k].clear()
                                    else:
                                        sheetData[k] = None
                            else:
                                sheetData[k] = v

                        sheetData[timeKey] = tm
                        loaded = True
                else:
                    loaded = False
            else:
                loaded = False

            if loaded:
                # we have loaded valid, up-to-date, previously compiled spreadsheet data
                if not forceSilent:
                    self.console("SHEET data: loaded from disk")
            else:
                # now we really heave to read and compile the spreadsheet
                if not forceSilent:
                    self.console(
                        "SHEET data: computing from scratch ...", newline=False
                    )
                sheetData.logData = []
                sheetData.caseSensitive = caseSensitive

                self._readSheet()
                tm = time.time()
                sheetData[timeKey] = tm

                self._compileSheet()
                self._prepareSheet()
                self._processSheet()

                with gzip.open(dataFile, mode="wb", compresslevel=GZIP_LEVEL) as f:
                    f.write(
                        pickle.dumps(
                            {k: sheetData[k] for k in SHEET_KEYS},
                            protocol=PICKLE_PROTOCOL,
                        )
                    )

                with fileOpen(timeFile, "w") as fh:
                    fh.write(f"{tm}\n")

                if not forceSilent:
                    self.console("done")
                showLog = False
        else:
            # the compiled spreadsheet data we have in memory is still up to date
            if not forceSilent:
                self.console("SHEET data: already in memory and uptodate")

        if showLog and not browse and not forceSilent:
            for x in sheetData.logData:
                self.consoleLine(*x)

        self.forceSilent = False

    def makeSheetOfSingleTokens(self):
        """Make a derived sheet based on the individual tokens in the triggers.

        The current sheet will be used to make a new sheet with a row for every
        token in every trigger on the original sheet.
        In this way all tokens in triggers will be searched individually.
        Since tokens do not overlap, the tokens as triggers do not interfere with
        each other.
        This can be a convenient debugging tool for the entity spreadsheet in the
        case of triggers without hits.

        Note however, that there are also other functions that help with debugging
        the spreadsheet:

        *   `tf.ner.triggers.Triggers.triggerInterference`
        *   `tf.ner.triggers.Triggers.reportHits`
        """
        Workbook = self.Workbook
        sheetName = self.sheetName
        sheetDir = self.sheetDir
        sheetPath = f"{sheetDir}/{sheetName}-single.xlsx"
        sheetData = self.getSheetData()
        raw = sheetData.raw

        # raw.setdefault(eidkind, {})[normScopeStr] = (r + 1, triggers)
        words = {}

        for eidkind, eData in raw.items():
            for scopeStr, (r, triggers) in eData.items():
                for trigger in triggers:
                    for word in trigger.split():
                        if word.isalpha():
                            words.setdefault(word, {}).setdefault(scopeStr, set()).add(
                                r
                            )

        wb = Workbook()
        ws = wb.active
        ws.append(("comment", "name", "kind", "scope", "triggers", "origrow"))
        ws.append(("", "", "", "", "", ""))

        eids = {}

        for word in sorted(words):
            wordData = words[word]
            eid = toSmallId(word).replace(".", " ")
            n = eids.get(eid, 0)

            eidDis = eid if n == 0 else f"{eid}({n})"

            n += 1
            eids[eid] = n
            rows = set()

            for scopeStr in sorted(wordData):
                rows |= set(wordData[scopeStr])

            rowRep = ",".join(str(r) for r in sorted(rows))
            ws.append(("", eidDis, "x", "", word, rowRep))

        wb.save(sheetPath)

    def writeSheetData(self, rows, asFile=None):
        """Write a spreadsheet.

        When the data for a spreadsheet has been gathered, you can write it to Excel
        by means of this function.

        Parameters
        ----------
        rows: iterable of iterables
            The rows, each row an interable of fields
        asFile: string, optional None
            The path of the file to write the Excel data to.
        """
        if not asFile:
            console("Pass the path of a destination file in param asFile")
            return

        Workbook = self.Workbook
        trigI = self.trigI
        commentI = self.commentI
        wb = Workbook()
        ws = wb.active

        for r, row in enumerate(rows):
            if r <= 1:
                ws.append(row)
                continue

            isCommentRow = row[commentI].startswith("#")

            if not isCommentRow:
                row[trigI] = "; ".join(row[trigI])

            ws.append(row)

        wb.save(asFile)

    def readSheetData(self):
        """Read the data of the spreadsheet and deliver it as a list of field lists.

        Concerning the Excel sheets in `ner/sheets`:

        *   they will be read by `tf.ner.ner.NER.setSheet()`;
        *   you might need to `pip install openpyxl` first;

        Each row in the spreadsheet specifies a set of triggers for a named entity
        in a certain scope. The row may have additional metadata, which will be linked
        to the named entity.
        If you need several scopes for the same named entity, make sure the metadata
        in those rows is identical. Otherwise it is unpredictable from which row the
        metadata will be taken.

        The first row is a header row, but the names are only important for the columns
        marked as metadata columns.

        The second row will be ignored, you can use it as an explanation or subtitle
        of the column titles in the header row.

        Here is a specification of the columns. We only specify the first so many
        columns. The remaining columns are treated as metadata.

        1.  **comment**. If this cell starts with a `#` the whole row will be
            skipped and ignored. Otherwise, the value is taken as a comment, that you
            are free to fill in or leave empty.

        1.  **name**. The full name of the entity, as it occurs in articles and
            reference works.

        1.  **kind**. A label that indicates what type of entity it is, e.g. `PER` for
            person and `LOC` for location and `ORG` for organization. But you are free
            to chose the labels.

        1.  **scope**. A string that indicates portions in the corpus where the
            triggers for this entity are valid. The scope specifies zero or more
            intervals of sections in the corpus, where an empty scope denotes the
            whole corpus. See `tf.ner.scopes.Scopes.parseScope()`
            for the syntax of scope specifiers.

        1.  **triggers**. A list of triggers, i.e. textual strings that occur in the
            corpus and trigger the detection of the entity named in the **name**
            column. The individual triggers must be separated by a `;`. Triggers may
            contain multiple words, and even `,`s. It is recommended not to use
            newlines in the trigger cells. When the triggers are read, white-space
            will be trimmed, and some character replacements will take place, which
            are dependent on the corpus. Think of replacing various kinds of quotes
            by ASCII quotes.

        The remaining columns are metadata columns. This metadata can be retrieved
        by means of the function `tf.ner.ner.NER.getMeta()`

        A good, real-world example of such a spreadsheet is *people.xlsx* in the
        [Suriano corpus](https://gitlab.huc.knaw.nl/suriano/letters/-/tree/main/ner/specs?ref_type=heads)

        Returns
        -------
        list of list
            Rows which are lists of fields.
        """
        sheetName = self.sheetName
        sheetDir = self.sheetDir
        loadXls = self.loadXls
        trigI = self.trigI
        commentI = self.commentI
        normalizeChars = self.normalizeChars
        spaceEscaped = self.spaceEscaped

        sheetData = self.getSheetData()
        caseSensitive = sheetData.caseSensitive

        def myNormalize(x):
            return normalize(
                str(x) if normalizeChars is None else normalizeChars(str(x))
            )

        sheetPath = f"{sheetDir}/{sheetName}.xlsx"

        wb = loadXls(sheetPath, data_only=True)
        ws = wb.active

        result = []

        for r, row in enumerate(ws.rows):
            fields = []
            result.append(fields)

            isCommentRow = (row[commentI].value or "").startswith("#")

            for i, field in enumerate(row):
                value = field.value or ""

                if not isCommentRow and r > 1 and i == trigI:
                    value = myNormalize(value)
                    value = {
                        y
                        for x in value.split(";")
                        if (
                            y := tnorm(
                                x,
                                spaceEscaped=spaceEscaped,
                                caseSensitive=caseSensitive,
                            )
                        )
                        != ""
                    }

                fields.append(value)

        return result

    def getMeta(self):
        """Retrieves the metadata of the current sheet.

        The metadata of each entity is stored in the extra fields in its row.
        The writer of the NER sheet is free to chose additional rows.

        Returns
        -------
        tuple
            The first member is a list of the names of the metadata columns,
            taken from the first row of the spreadsheet.

            The second member is a dict with the metadata itself.
            The keys are strings of the form *entity identifier*`-`*entity kind*.
            The values are tuples, where the i-th member is the value for the i-th
            name in the list of metadata fields.
        """
        sheetData = self.getSheetData()
        return (sheetData.metaFields, sheetData.metaData)

    def _readSheet(self):
        """Read all the spreadsheets, the main one and the tweaks.

        Several checks on the sanity of the data will be performed.

        Store the results in a hierarchy that mimicks the way they are organized in the
        file system.
        """
        forceSilent = self.forceSilent
        sheetName = self.sheetName
        sheetDir = self.sheetDir
        loadXls = self.loadXls
        defaultKind = self.defaultKind
        transform = self.transform
        spaceEscaped = self.spaceEscaped
        normalizeChars = self.normalizeChars
        trigI = self.trigI
        scopeI = self.scopeI

        def spec(msg):
            if forceSilent:
                return
            self.log(None, 0, msg)

        def log(msg):
            if forceSilent:
                return
            self.log(False, 0, msg)

        def err(msg):
            if forceSilent:
                return
            self.log(True, 0, msg)

        def err1(msg):
            if forceSilent:
                return
            self.log(True, 1, msg)

        sheetData = self.getSheetData()
        caseSensitive = sheetData.caseSensitive

        nameMap = {}
        sheetData.nameMap = nameMap
        """Will contain a mapping from entities to names.

        The entities are keyed by their (eid, kind) tuple.
        The values are names plus the sheet where they are first defined.
        """

        metaData = {}
        sheetData.metaData = metaData
        """Will contain the data of most columns in the spreadsheet.

        The scope and triggers columns are not stored.

        For each row, a key is computed (the small eid based on the name in the first
        column). Under this key we store the list of values.
        """

        rowMap = {}
        sheetData.rowMap = rowMap
        """Will contain a mapping from triggers to row.

        For each trigger we store the row in the NER sheet where that trigger occurs.
        """

        for k in CLEAR_KEYS:
            if k in sheetData:
                sheetData[k].clear()

        for k in SHEET_KEYS:
            if k in sheetData:
                if type(sheetData[k]) in {list, dict, set}:
                    sheetData[k].clear()

        spec("Reading sheets")

        scopeMap = {}
        sheetData.scopeMap = scopeMap
        """Will contain a mapping from scope specifiers to logical scopes.

        Scope specifiers are strings, logical scopes are the data structures
        that you get when you parse those strings.
        """

        sheetPath = f"{sheetDir}/{sheetName}.xlsx"

        wb = loadXls(sheetPath, data_only=True)
        ws = wb.active
        maxCol = ws.max_column
        maxRow = ws.max_row

        if not forceSilent:
            self.console(f"Sheet with {maxRow} rows and {maxCol} columns")

        raw = {}
        sheetData.raw = raw

        multiNames = {}
        noNames = set()
        noTrigs = set()
        emptyLines = set()
        scopeMistakes = {}

        def myNormalize(x):
            """Normalization function that performs additional replacements.

            The replacements are coded in the function `normalizeChars()`,
            which can be passed to the instance of this class.
            """
            return normalize(
                str(x) if normalizeChars is None else normalizeChars(str(x))
            )

        for r, row in enumerate(ws.rows):
            if r == 0:
                metaFields = [
                    myNormalize(row[i].value or "")
                    for i in range(maxCol)
                    if i not in {0, scopeI, trigI}
                ]
                sheetData.metaFields = metaFields

                continue
            if r == 1:
                continue
            if not any(c.value for c in row):
                continue

            triggerStr = row[trigI].value

            if triggerStr is not None and "\n" in triggerStr:
                triggerRep = triggerStr.replace("\n", "\\n")
                msg = f"r{r + 1:>3}: newline in trigger string: {triggerRep}"
                log(msg)
                continue

            (comment, name, kind, scopeStr, triggerStr) = (
                myNormalize(row[i].value or "") for i in range(trigI + 1)
            )

            if comment.startswith("#"):
                continue

            if not name or not triggerStr:
                if name:
                    noTrigs.add(r + 1)
                elif triggerStr:
                    noNames.add(r + 1)
                else:
                    emptyLines.add(r + 1)
                continue

            triggers = {
                y
                for x in triggerStr.split(";")
                if (
                    y := tnorm(
                        x, spaceEscaped=spaceEscaped, caseSensitive=caseSensitive
                    )
                )
                != ""
            }

            for trigger in triggers:
                rowMap.setdefault(trigger, []).append(r + 1)

            if len(triggers) == 0:
                noTrigs.add(r + 1)
                continue

            if not kind:
                kind = defaultKind
                msg = f"r{r + 1:>3}: " f"no kind name, supplied {defaultKind}"
                log(msg)

            info = self.parseScope(scopeStr, plain=False)
            warnings = info["warning"]

            if len(warnings):
                scopeMistakes[r + 1] = "; ".join(warnings)
                continue

            normScopeStr = info["normal"]

            if normScopeStr != "":
                scopes = info["result"]

                if normScopeStr not in scopeMap:
                    scopeMap[normScopeStr] = scopes

            eid = toSmallId(name, transform=transform)
            eidkind = (eid, kind)

            if normScopeStr in raw.get(eidkind, {}):
                ar = raw[eidkind][normScopeStr][0]
                multiNames[r + 1] = f"({normScopeStr}) {nameMap[eidkind]} also in r{ar}"
                continue
            else:
                nameMap[eidkind] = name

            raw.setdefault(eidkind, {})[normScopeStr] = (r + 1, triggers)

            metaKey = f"{eid}-{kind}"
            metaData[metaKey] = [
                myNormalize(row[i].value or "")
                for i in range(maxCol)
                if i not in {0, scopeI, trigI}
            ]

        if not forceSilent:
            for diags, isdict, label in (
                (emptyLines, False, "without a name and triggers"),
                (multiNames, True, "with a duplicate name"),
                (noNames, False, "without a name"),
                (scopeMistakes, True, "with scope mistakes"),
                (noTrigs, False, "without triggers"),
            ):
                n = len(diags)

                if n > 0:
                    if isdict:
                        if n > 0:
                            plural = "" if n == 1 else "s"
                            err(f"{n} row{plural} {label}:")

                            for r in sorted(diags):
                                msg = diags[r]
                                err1(f"r{r:>3}: {msg}")
                    else:
                        rep = ", ".join(str(x) for x in sorted(diags)[0:10])
                        plural = "" if n == 1 else "s"
                        err(f"{n} row{plural} {label}:\n\te.g.: {rep}")

    def _compileSheet(self):
        """Compiles the info in tweaked sheets according to the scopes in it.

        On the basis of the scopes that are given for the triggers, we partition
        the corpus in maximal intervals in which no trigger goes into or out of scope.
        During these intervals we have a fixed set of triggers that must be looked up,
        and we can check for the consistency of these triggers.

        In every scope we may find two kinds of problems with triggers and scopes:

        *   ambiguous trigger: a trigger is used by multiple entities in that scope.
        *   clashing triggers: a trigger occurs in more than one row for a specific
            entity and a specific scope.

        These problems are detected and reported.
        """
        forceSilent = self.forceSilent
        sheetData = self.getSheetData()
        compiled = AttrDict()
        sheetData.compiled = compiled
        nameMap = sheetData.nameMap

        def spec(msg, cache=None):
            if forceSilent:
                return
            self.log(None, 0, msg, cache=cache)

        def log(msg, cache=None):
            if forceSilent:
                return
            self.log(False, 0, msg, cache=cache)

        def err(msg, cache=None):
            if forceSilent:
                return
            self.log(True, 0, msg, cache=cache)

        def errProblem(problem, cache):
            if forceSilent:
                return
            for indent, msg in problem:
                self.log(True, indent, msg, cache=cache)

        tFullMap = {}

        def getTriggerRep(tr):
            triggerInfo = tFullMap[tr]

            result = []

            for scope in sorted(triggerInfo):
                scopeRep = "" if not scope else f"({scope})"
                scopeInfo = triggerInfo[scope]

                for eidkind in sorted(scopeInfo):
                    name = sheetData.nameMap[eidkind]
                    rowRep = ",".join(str(r) for r in sorted(scopeInfo[eidkind]))
                    result.append(f"'{tr}'{scopeRep} r{rowRep} for {name}")
            return result

        spec("Checking scopes")

        raw = sheetData.raw
        intvMap = sheetData.scopeMap
        intervals = partitionScopes(intvMap)

        problems = set()

        for b, e, scopeStrs in [[None, None, None]] + intervals:
            scopeStrSet = {""} if scopeStrs is None else set(scopeStrs)
            intv = (b, e) if b is not None and e is not None else ()

            headCache = []
            problemCache = []

            msg = self.repInterval(intv)
            spec(msg, cache=headCache)

            thisCompiled = AttrDict()
            compiled[intv] = thisCompiled

            # check which triggers are a substring in which other triggers
            # these triggers can never be found!

            tFullMap.clear()

            for eidkind, info in raw.items():
                if "" in info:
                    (r, triggers) = info[""]

                    for trigger in triggers:
                        tFullMap.setdefault(trigger, {}).setdefault("", {}).setdefault(
                            eidkind, set()
                        ).add(r)

                for scopeStr, (r, triggers) in info.items():
                    if scopeStr == "":
                        continue

                    if scopeStr in scopeStrSet:
                        for trigger in triggers:
                            tFullMap.setdefault(trigger, {}).setdefault(
                                scopeStr, {}
                            ).setdefault(eidkind, set()).add(r)

            # now compile the result information: tMap, newSheet

            newSheet = {}
            thisCompiled.sheet = newSheet

            tMap = {}
            thisCompiled.tMap = tMap

            for eidkind, info in raw.items():
                if "" in info:
                    (r, triggers) = info[""]
                    newSheet[eidkind] = triggers

                    for trigger in triggers:
                        tMap[trigger] = ""

                for scopeStr, (r, triggers) in info.items():
                    if scopeStr == "":
                        continue

                    if scopeStr in scopeStrSet:
                        newSheet[eidkind] = triggers

                        for trigger in triggers:
                            tMap[trigger] = scopeStr

            # the sheet is now compiled, all compiled data has been created
            # the rest only deals with error reporting

            ambi = 0
            clashes = 0

            for trigger in sorted(tFullMap):
                problem = []
                triggerInfo = tFullMap[trigger]

                for scopeStr in sorted(triggerInfo):
                    scopeInfo = triggerInfo[scopeStr]
                    scopeRep = f" in scope {scopeStr}" if scopeStr else ""

                    thisAmbi = False
                    theseClashes = 0

                    if len(scopeInfo) > 1:
                        problem.append((0, f"Ambi: '{trigger}'{scopeRep}: "))
                        thisAmbi = True

                    for eidkind, rs in scopeInfo.items():
                        name = nameMap[eidkind]
                        rowRep = ",".join(str(r) for r in rs)
                        nRs = len(rs)

                        if nRs > 1:
                            theseClashes += 1

                        if thisAmbi:
                            problem.append((1, f"{name}: {rowRep}"))
                        elif nRs > 1:
                            problem.append(
                                (0, f"Clash: '{trigger}' for {name}: {rowRep}")
                            )

                    clashes += theseClashes

                    if len(problem):
                        problem = tuple(problem)

                        if problem not in problems:
                            if thisAmbi:
                                ambi += 1
                            if theseClashes:
                                clashes += theseClashes

                            problems.add(problem)
                            errProblem(problem, problemCache)

            if ambi > 0:
                err(f"Ambiguous triggers: {ambi} x", cache=problemCache)

            if clashes > 0:
                err(f"Reused triggers scope: {clashes} x", cache=problemCache)

            if len(problemCache) > 0:
                self.flush(headCache)
                self.flush(problemCache)

    def _prepareSheet(self):
        """Transform the sheets into instructions.

        Now we have intervals with fixed sets of triggers,
        we can generate instructions out of the sheets: info that the search
        algorithm needs to do its work.

        This info is such that it supports simultaneous searching for multiple triggers.
        """
        spaceEscaped = self.spaceEscaped

        sheetData = self.getSheetData()
        compiled = sheetData.compiled
        nameMap = sheetData.nameMap
        caseSensitive = sheetData.caseSensitive

        instructions = {}
        sheetData.instructions = instructions

        triggerScopes = {}
        sheetData.triggerScopes = triggerScopes

        allTriggers = set()
        sheetData.allTriggers = allTriggers

        for intv, thisCompiled in compiled.items():
            sheet = thisCompiled.sheet
            tMap = thisCompiled.tMap

            triggerSet = set()
            tPos = {}
            idMap = {}

            theseInstructions = dict(tPos=tPos, tMap=tMap)
            instructions[intv] = theseInstructions

            for eidkind, triggers in sheet.items():
                for trigger in triggers:
                    triggerT = toTokens(
                        trigger, spaceEscaped=spaceEscaped, caseSensitive=caseSensitive
                    )
                    triggerSet.add(triggerT)
                    idMap.setdefault(trigger, []).append(eidkind)

            for triggerT in triggerSet:
                for i, token in enumerate(triggerT):
                    tPos.setdefault(i, {}).setdefault(token, set()).add(triggerT)

            theseInstructions["idMap"] = {
                trigger: eidkinds[0] for (trigger, eidkinds) in idMap.items()
            }

            tMap = theseInstructions["tMap"]
            idMap = theseInstructions["idMap"]

            for trigger, scope in tMap.items():
                eidkind = idMap.get(trigger, None)

                if eidkind is None:
                    continue

                name = nameMap[eidkind]
                allTriggers.add((name, eidkind, trigger, scope))
                triggerScopes.setdefault(trigger, set()).add(scope)

    def _processSheet(self):
        """Carries out the search instructions that have been compiled from the sheet.

        We look up the occurrences, organize the hits of the triggers, and store them
        as entities in the current set.
        """
        if not self.properlySetup:
            return

        forceSilent = self.forceSilent
        silent = self.silent
        browse = self.browse

        if not browse and not silent and not forceSilent:
            app = self.app
            app.indent(reset=True)
            app.info("Looking up occurrences of many candidates ...")

        self.findOccs()
        self._collectHits()

        if not browse and not silent and not forceSilent:
            app.info("done")

        self._markEntities()

    def _collectHits(self):
        """Stores the trigger hits.

        The hits will be stored under the key `hitData` in the sheet data.
        """
        if not self.properlySetup:
            return

        forceSilent = self.forceSilent
        sheetData = self.getSheetData()
        inventory = sheetData.inventory
        instructions = sheetData.instructions

        def log(msg):
            if forceSilent:
                return
            self.log(False, 0, msg)

        hitData = {}
        sheetData.hitData = hitData

        for path, data in instructions.items():
            idMap = data["idMap"]
            tMap = data["tMap"]

            for trigger, scope in tMap.items():
                eidkind = idMap.get(trigger, None)

                if eidkind is None:
                    continue

                occs = inventory.get(eidkind, {}).get(trigger, {}).get(scope, [])
                hitData.setdefault(eidkind, {})[(trigger, scope)] = len(occs)

    def _markEntities(self):
        """Marks up the members of the inventory as entities.

        The instructions contain the entity identifier and the entity kind that
        have to be assigned to the surface forms.

        The inventory knows where the occurrences of the surface forms are.
        All these occurrences will be added to the current entity set.
        """
        if not self.properlySetup:
            return

        sheetData = self.getSheetData()
        inventory = sheetData.inventory

        newEntities = []
        triggerFromMatch = {}
        sheetData.triggerFromMatch = triggerFromMatch

        for eidkind, entData in inventory.items():
            for trigger, triggerData in entData.items():
                for scope, matches in triggerData.items():
                    for match in matches:
                        triggerFromMatch[match] = (trigger, scope)

                    newEntities.append((eidkind, matches))

        self._addToSet(newEntities)

    def getSheetData(self):
        """Deliver the data of current sheet.

        Sheet data is `tf.core.generic.AttrDict` with various kinds of data under
        various keys, which are listed in `tf.ner.sheets.SHEET_KEYS`.

        Returns
        -------
        dict
        """
        sheetName = self.sheetName
        sheetsData = self.sheets

        return sheetsData.setdefault(sheetName, AttrDict())

    def log(self, isError, indent, msg, cache=None):
        """Issue a message to the user.

        Depending on the `silent` member of the instance and on whether the message
        is an error message, it can be inhibited.

        Parameters
        ----------
        isError: boolean
            Whether it is an error message or a normal message
        indent: integer
            How far (in tabs) the message should be indented
        msg: string
            The actual message
        cache: list, optional None
            If it is a list, the output will not be sent to the console,
            but appended to the cache.
            You can save it for later.
        """
        silent = self.silent

        if silent and not isError:
            return

        browse = self.browse
        sheetData = self.getSheetData()
        logData = sheetData.logData

        if cache is None:
            logData.append((isError, indent, msg))

        if not browse:
            if cache is None:
                self.consoleLine(isError, indent, msg)
            else:
                cache.append((isError, indent, msg))

    def flush(self, cache):
        """Flushes the cache of log messages.

        Parameters
        ----------
        cache: list
            The items in the cache
        """
        browse = self.browse
        sheetData = self.getSheetData()
        logData = sheetData.logData

        if not browse:
            for item in cache:
                logData.append(item)
                self.consoleLine(*item)
