import re
import time
import pickle
import gzip

from ...parameters import GZIP_LEVEL, PICKLE_PROTOCOL
from ...capable import CheckImport
from .helpers import (
    tnorm,
    normalize,
    toSmallId,
    toTokens,
    repScope,
    parseScopes,
    partitionScopes,
)
from ...core.generic import AttrDict
from ...core.helpers import console
from ...core.files import fileOpen, dirContents, extNm, fileExists, mTime


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
    hitData
""".strip().split()

CLEAR_KEYS = """
    raw
    compiled
""".strip().split()


class Sheets:
    def __init__(self, sheets=None):
        CI = CheckImport("openpyxl")
        if CI.importOK(hint=True):
            openpyxl = CI.importGet()
            self.loadXls = openpyxl.load_workbook
            self.Workbook = openpyxl.Workbook
        else:
            self.properlySetup = False
            return None

        self.properlySetup = True

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
        """The current ner sheet."""

        self.sheetNames = set()
        """The set of names of ner sheets that are present on the file system."""

        self.readSheets()

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

    def setSheet(self, newSheet, force=False, caseSensitive=None):
        """Switch to a named ner sheet.

        After the switch, the new sheet will be loaded into memory.

        Parameters
        ----------
        newSheet: string
            The name of the new ner sheet to switch to.
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

        Otherwise, the data will be computed from scratch and saved to disk,
        with a time stamp.
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
                self.console("SHEET data: loaded from disk")
            else:
                # now we really heave to read and compile the spreadsheet
                self.console("SHEET data: computing from scratch ...", newline=False)
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

                self.console("done")
                showLog = False
        else:
            # the compiled spreadsheet data we have in memory is still up to date
            self.console("SHEET data: already in memory and uptodate")

        if showLog and not browse:
            for x in sheetData.logData:
                self.consoleLine(*x)

    def makeSheetOfSingleTokens(self):
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
        ws.append(("name", "kind", "scope", "triggers", "origrow"))
        ws.append(("", "", "", "", ""))

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
            ws.append((eidDis, "x", "", word, rowRep))

        wb.save(sheetPath)

    def _readSheet(self):
        """Read all the spreadsheets, the main one and the tweaks.

        Store the results in a hierarchy that mimicks the way they are organized in the
        file system.
        """
        sheetName = self.sheetName
        sheetDir = self.sheetDir
        loadXls = self.loadXls
        defaultKind = self.defaultKind
        transform = self.transform
        spaceEscaped = self.spaceEscaped
        normalizeChars = self.normalizeChars

        def spec(msg):
            self.log(None, 0, msg)

        def log(msg):
            self.log(False, 0, msg)

        def err(msg):
            self.log(True, 0, msg)

        def err1(msg):
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

        sheetPath = f"{sheetDir}/{sheetName}.xlsx"

        wb = loadXls(sheetPath, data_only=True)
        ws = wb.active
        maxCol = ws.max_column
        maxRow = ws.max_row

        self.console(f"Sheet with {maxRow} rows and {maxCol} columns")

        raw = {}
        sheetData.raw = raw

        multiNames = {}
        noNames = set()
        noTrigs = set()
        emptyLines = set()
        scopeMistakes = {}

        def myNormalize(x):
            return normalize(
                str(x) if normalizeChars is None else normalizeChars(str(x))
            )

        for r, row in enumerate(ws.rows):
            if r == 0:
                metaFields = [
                    myNormalize(row[i].value or "")
                    for i in range(maxCol)
                    if i not in {2, 3}
                ]
                sheetData.metaFields = metaFields

                continue
            if r == 1:
                continue
            if not any(c.value for c in row):
                continue

            triggerStr = row[3].value

            if triggerStr is not None and "\n" in triggerStr:
                triggerRep = triggerStr.replace("\n", "\\n")
                msg = f"r{r + 1:>3}: newline in trigger string: {triggerRep}"
                log(msg)
                continue

            (name, kind, scopeStr, triggerStr) = (
                myNormalize(row[i].value or "") for i in range(4)
            )
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

            info = parseScopes(scopeStr, plain=False)
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
                if i not in {2, 3}
            ]

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
        """Compiles the info in tweaked sheets into complete sheets.

        For every tweak spreadsheet, a copy of its parent sheet will be made,
        and the info of the tweak sheet will be applied to that copy,
        adding to or overriding the parent sheet.

        A sheet is basically a mapping of triggers to names.

        We also maintain a mapping from tweak sheets to triggers, so that we can
        know later on which sheet assigned which trigger to which name.

        The tweak may remove triggers from the sheet. We have to adapt the tMap
        for that.
        """
        sheetData = self.getSheetData()
        compiled = AttrDict()
        sheetData.compiled = compiled
        nameMap = sheetData.nameMap

        def spec(msg):
            self.log(None, 0, msg)

        def log(msg):
            self.log(False, 0, msg)

        def err(msg):
            self.log(True, 0, msg)

        def errProblem(problem):
            for indent, msg in problem:
                self.log(True, indent, msg)

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

        spec("Checking scopes ...")

        raw = sheetData.raw
        scopeMap = sheetData.scopeMap
        intervals = partitionScopes(scopeMap)

        problems = set()

        for b, e, scopeStrs in [[None, None, None]] + intervals:
            scopeStrSet = {""} if scopeStrs is None else set(scopeStrs)
            intv = (b, e) if b is not None and e is not None else ()

            spec(repScope(intv))

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
                            errProblem(problem)

            if ambi > 0:
                err(f"Ambiguous triggers: {ambi} x")

            if clashes > 0:
                err(f"Reused triggers scope: {clashes} x")

    def _prepareSheet(self):
        """Transform the sheets into instructions.

        Now we have complete sheets for every context, the inheritance is resolved.
        Every sheet specifies a mapping from triggers to names, and remembers
        which (possibly other) sheet mapped a specific trigger to its name.

        We perform additional checks on the consistency and completeness of the
        resulting sheets.

        Then we generate instructions out of the sheets: info that the search
        algorithm needs to do its work.

        For each path to tweaked sheet we collect a portion of info:

        *   `tPos`: a compilation of all triggers in the sheet, so that
            we can search for them simultaneously;
        *   `tMap`: a mapping from triggers to the path of the sheet that defined this
            trigger;
        *   `idMap`: a mapping from triggers their corresponding entities.

        So every portion of info is addressed by a `path` key. This key is a tuple
        of section/subsection/subsubsection heading.

        By means of this key we can select the proper search instructions for specific
        parts of the corpus.

        About reporting:

        We report the entities without triggers.
        When we report the tweaks, only those triggerless entities are reported that
        were not already triggerless in the main sheet.

        We report the ambiguus triggers.
        When we report the tweaks, only those triggers that are redefined in that tweak
        are reported.
        """

        spaceEscaped = self.spaceEscaped

        sheetData = self.getSheetData()
        compiled = sheetData.compiled
        caseSensitive = sheetData.caseSensitive

        instructions = {}
        sheetData.instructions = instructions

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

    def _processSheet(self):
        """Generates derived data structures out of the source sheet.

        After loading we process the set into derived data structures.

        For each such set we produce several data structures, which we store
        under the following keys:

        *   `inventory`: result of looking up all triggers

        """
        if not self.properlySetup:
            return

        silent = self.silent
        browse = self.browse

        if not browse and not silent:
            app = self.app
            app.indent(reset=True)
            app.info("Looking up occurrences of many candidates ...")

        self.findOccs()
        self._collectHits()

        if not browse and not silent:
            app.info("done")

        self._markEntities()

    def _collectHits(self):
        """Reports the inventory."""
        if not self.properlySetup:
            return

        sheetData = self.getSheetData()

        inventory = sheetData.inventory
        instructions = sheetData.instructions

        def log(msg):
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
        If there is no inventory yet, it will be created.
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
        """Deliver the current sheet."""
        sheetName = self.sheetName
        sheetsData = self.sheets

        return sheetsData.setdefault(sheetName, AttrDict())

    def log(self, isError, indent, msg):
        silent = self.silent

        if silent and not isError:
            return

        browse = self.browse
        sheetData = self.getSheetData()
        logData = sheetData.logData

        logData.append((isError, indent, msg))

        if not browse:
            self.consoleLine(isError, indent, msg)
