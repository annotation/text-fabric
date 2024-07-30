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
    parseScopes,
    partitionScopes,
    repScope,
)
from ...core.generic import AttrDict
from ...core.helpers import console
from ...core.files import fileOpen, dirContents, extNm, fileExists, mTime


DS_STORE = ".DS_Store"
SHEET_RE = re.compile(r"""^([0-9]+)((?:-[0-9]+)?)\.xlsx$""", re.I)

SHEET_KEYS = """
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

    def setSheet(self, newSheet, force=False):
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

        if newSheet not in sheetNames or not fileExists(sheetFile):
            if not browse:
                console(f"NER sheet {newSheet} ({sheetFile}) does not exist")
            if newSheet is not None:
                return

        if not browse:
            self.setSet("" if newSheet is None else f".{newSheet}")

        if newSheet != sheetName:
            sheetName = newSheet
            self.sheetName = sheetName

        self.loadSheetData(force=force)

    def loadSheetData(self, force=False):
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
        needReload = force or sheetData.get("time", 0) < sheetUpdated

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

                    for k in CLEAR_KEYS:
                        if k in sheetData:
                            sheetData[k].clear()

                    for k in SHEET_KEYS:
                        v = data.get(k, None)

                        if v is None:
                            if k in sheetData:
                                sheetData[k].clear()
                        else:
                            sheetData[k] = v

                    sheetData.time = tm
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

                self._readSheet(sheetData)
                tm = time.time()
                sheetData.time = tm

                self._compileSheet(sheetData)
                self._prepareSheet(sheetData)
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

    def _readSheet(self, sheetData):
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

        nameMap = {}
        sheetData.nameMap = nameMap
        """Will contain a mapping from entities to names.

        The entities are keyed by their (eid, kind) tuple.
        The values are names plus the sheet where they are first defined.
        """

        rowMap = {}
        sheetData.rowMap = rowMap

        for k in CLEAR_KEYS:
            if k in sheetData:
                sheetData[k].clear()

        for k in SHEET_KEYS:
            if k in sheetData:
                sheetData[k].clear()

        spec("Reading sheets")

        scopeMap = {}
        sheetData.scopeMap = scopeMap

        sheetPath = f"{sheetDir}/{sheetName}.xlsx"

        wb = loadXls(sheetPath, data_only=True)
        ws = wb.active

        raw = {}
        sheetData.raw = raw

        multiNames = {}
        noNames = set()
        noTrigs = set()
        emptyLines = set()
        scopeMistakes = {}

        def myNormalize(x):
            return normalize(x if normalizeChars is None else normalizeChars(x))

        for r, row in enumerate(ws.rows):
            if r in {0, 1}:
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
                if (y := tnorm(x, spaceEscaped=spaceEscaped)) != ""
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
                # if eidkind in nameMap:
                multiNames[r + 1] = f"({normScopeStr}) {nameMap[eidkind]}"
                continue
            else:
                nameMap[eidkind] = name

            raw.setdefault(eidkind, {})[normScopeStr] = (r + 1, triggers)

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

    def _compileSheet(self, sheetData):
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
        compiled = AttrDict()
        sheetData.compiled = compiled

        def spec(msg):
            self.log(None, 0, msg)

        def log(msg):
            self.log(False, 0, msg)

        def err(msg):
            self.log(True, 0, msg)

        spec("Checking scopes ...")

        raw = sheetData.raw
        scopeMap = sheetData.scopeMap
        intervals = partitionScopes(scopeMap)

        clashes = set()

        for b, e, scopeStrs in [[None, None, None]] + intervals:
            scopeStrSet = {""} if scopeStrs is None else set(scopeStrs)
            intv = (b, e) if b is not None and e is not None else ()

            thisCompiled = AttrDict()
            compiled[intv] = thisCompiled

            newSheet = {}
            thisCompiled.sheet = newSheet

            tMap = {}
            thisCompiled.tMap = tMap

            tFullMap = {}

            for eidkind, info in raw.items():
                if "" in info:
                    (r, triggers) = info[""]
                    newSheet[eidkind] = triggers

                    for trigger in triggers:
                        tFullMap.setdefault(trigger, {}).setdefault(eidkind, set()).add(
                            (r, "")
                        )
                        tMap[trigger] = ""

                for scopeStr, (r, triggers) in info.items():
                    if scopeStr == "":
                        continue

                    if scopeStr in scopeStrSet:
                        newSheet[eidkind] = triggers

                        for trigger in triggers:
                            tFullMap.setdefault(trigger, {}).setdefault(
                                eidkind, set()
                            ).add((r, scopeStr))
                            tMap[trigger] = scopeStr

            hasTriggerConflicts = any(len(x) > 1 for x in tFullMap.values())
            hasScopeConflicts = any(
                any(sum(1 for z in y if z[1] != "") > 1 for y in x.values())
                for x in tFullMap.values()
            )
            if not (hasTriggerConflicts or hasScopeConflicts):
                continue

            scopeRep = "all" if b is None else repScope((b, e))
            spec(f"Interval {scopeRep}")

            specificClashes = 0

            for trigger, info in tFullMap.items():
                ambiTrigger = len(info) > 1
                conflictScope = any(
                    sum(1 for z in y if z[1] != "") > 1 for y in info.values()
                )

                if not (ambiTrigger or conflictScope):
                    continue

                msg = f"Clash: {trigger}"
                emsgs = []

                for eidkind, scopeInfo in info.items():

                    for r, scopeStr in scopeInfo:
                        scopeRep = " (scopeStr)" if scopeStr else ""
                        emsgs.append(f"r{r}{scopeRep}")

                clash = f"{msg}: {' vs '.join(emsgs)}"

                if clash not in clashes:
                    clashes.add(clash)
                    err(clash)
                    specificClashes += 1

            if specificClashes == 0:
                log("no context-specific clashes")

    def _prepareSheet(self, sheetData):
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
        compiled = sheetData.compiled

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
                    triggerT = toTokens(trigger, spaceEscaped=spaceEscaped)
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

        sheetName = self.sheetName
        sheetData = self.sheets[sheetName]

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

                occs = inventory.get(eidkind, {}).get(trigger, {}).get(scope, {})
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

        sheetName = self.sheetName
        sheetData = self.sheets[sheetName]
        inventory = sheetData.inventory

        newEntities = []
        triggerFromMatch = {}
        sheetData.triggerFromMatch = triggerFromMatch

        for eidkind, entData in inventory.items():
            for trigger, triggerData in entData.items():
                for scope, matches in triggerData.items():
                    newEntities.append((eidkind, matches))
                    for match in matches:
                        triggerFromMatch[match] = (trigger, scope)

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
