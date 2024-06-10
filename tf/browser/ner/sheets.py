import collections
import re
import time

from ...capable import CheckImport
from .helpers import tnorm, normalize, toId, toSmallId, toTokens, log
from ...core.generic import AttrDict
from ...core.helpers import console
from ...core.files import dirContents, extNm, fileExists, mTime, initTree


DS_STORE = ".DS_Store"
SHEET_RE = re.compile(r"""^([0-9]+)((?:-[0-9]+)?)\.xlsx$""", re.I)


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

        browse = self.browse
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

        self.nameMap = {}
        """Will contain a mapping from entities to names.

        The entities are keyed by their (eid, kind) tuple.
        The values are names plus the sheet where they are first defined.
        """

        if not browse:
            self.loadSheetData()

    def getSheetData(self):
        """Deliver the current sheet.
        """
        sheetName = self.sheetName

        if sheetName is None:
            return None

        sheetsData = self.sheets
        sheetData = sheetsData.setdefault(sheetName, AttrDict())
        return sheetData

    def setSheet(self, newSheet):
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

        if not newSheet:
            self.sheetName = None
            return

        sheetNames = self.sheetNames
        sheetDir = self.sheetDir
        sheetFile = f"{sheetDir}/{newSheet}.xlsx"

        if newSheet not in sheetNames or not fileExists(sheetFile):
            if not browse:
                self.console(f"Ner sheet {newSheet} ({sheetFile}) does not exist")
            return

        if newSheet != sheetName:
            sheetName = newSheet
            self.sheetName = sheetName
            self.loadSheetData()

    def loadSheetData(self):
        """Loads the current ner sheet into memory, if there is one.
        """
        if not self.properlySetup:
            return

        sheets = self.sheets
        sheetName = self.sheetName

        if sheetName is None:
            return

        if sheetName not in sheets:
            sheets[sheetName] = AttrDict()

        changed = self.fromSourceSheet()
        self.processSheet(changed)

    def fromSourceSheet(self):
        """Loads a ner sheet from source.

        If the current ner sheet is None, nothing has to be done.

        Otherwise, we read the corresponding excel sheet(s) from disk and compile them
        into instructions.

        After collection of the sheet it is stored under the following keys:

        *   `dateLoaded`: datetime when the sheet was last loaded from disk;
        *   `instructions`: the list of instructions as loaded and compiled
            from the source.
        """
        if not self.properlySetup:
            return None

        sheetName = self.sheetName

        if sheetName is None:
            return

        if sheetName not in self.sheets:
            self.sheets[sheetName] = AttrDict()

        sheetData = self.sheets[sheetName]
        sheetDir = self.sheetDir
        sheetFile = f"{sheetDir}/{sheetName}.xlsx"

        reportBase = self.reportBase
        reportDir = f"{reportBase}/{sheetName}"
        initTree(reportDir, fresh=False)

        def timeXls(sheetRela):
            sep = "/" if sheetRela else ""
            sheetPath = f"{sheetDir}/{sheetName}{sep}{sheetRela}.xlsx"
            return mTime(sheetPath)

        def timeDir(sheetRela):
            sep = "/" if sheetRela else ""
            dirPath = f"{sheetDir}/{sheetName}{sep}{sheetRela}"

            (files, dirs) = dirContents(f"{sheetDir}/{sheetName}{sep}{sheetRela}")
            mFiles = max((mTime(f"{dirPath}/{fl}") for fl in files), default=0)
            mDirs = max((timeDir(f"{sheetRela}{sep}{dr}") for dr in dirs), default=0)

            return max((mFiles, mDirs))

        mT = max((timeXls(""), timeDir("")))

        changed = False

        if (
            "instructions" not in sheetData
            or "dateLoaded" not in sheetData
            or (len(sheetData.instructions) > 0 and not fileExists(sheetFile))
            or (fileExists(sheetFile) and sheetData.dateLoaded < mT)
        ):
            changed = True
            self._readSheets(sheetData)
            self._combineSheets(sheetData)
            self._compileSheets(sheetData)
            self._prepareSheets(sheetData)
            sheetData.dateLoaded = time.time()

        return changed

    def processSheet(self, changed):
        """Generates derived data structures out of the source sheet.

        After loading we process the set into derived data structures.

        We try to be lazy. We only load a set from disk if it is not
        already in memory, or if the set on disk has been updated since the last load.

        The resulting data is stored in the current set under the various keys.

        After processing, the time of processing is recorded, so that it can be
        observed if the processed set is no longer up to date w.r.t. the source.

        For each such set we produce several data structures, which we store
        under the following keys:

        *   `dateProcessed`: datetime when the set was last processed
        *   `entityText`: dict, text of entity by entity node or line number in
            TSV file;
        *   `inventory`: result of looking up all triggers

        Parameters
        ----------
        changed: boolean
            Whether the set has changed since last processing.
        """
        if not self.properlySetup:
            return

        browse = self.browse
        sheetName = self.sheetName
        sheetData = self.sheets[sheetName]

        dateLoaded = sheetData.dateLoaded
        dateProcessed = sheetData.dateProcessed

        if (
            changed
            or "dateProcessed" not in sheetData
            or "inventory" not in sheetData
            or dateLoaded is not None
            and dateProcessed < dateLoaded
        ):

            if not browse:
                app = self.app
                app.indent(reset=True)
                app.info("Looking up occurrences of many candidates ...")

            self.findOccs()
            self.markEntities()
            sheetData.dateProcessed = time.time()

            if not browse:
                app.info("done")
                self.reportHits()

    def readSheets(self):
        """Read the list current ner sheets (again).

        Use this when you change ner sheets outside the NER browser, e.g.
        by editing the spreadsheets in Excel.
        """
        sheetDir = self.sheetDir
        self.sheetNames = {
            x.removesuffix(".xlsx")
            for x in dirContents(sheetDir)[0]
            if extNm(x) == "xlsx"
        }

    def _readSheets(self, sheetData):
        """Read all the spreadsheets, the main one and the tweaks.

        Store the results in a hierarchy that mimicks the way they are organized in the
        file system.
        """
        sheetName = self.sheetName
        sheetDir = self.sheetDir
        loadXls = self.loadXls
        defaultKind = self.defaultKind
        transform = self.transform
        nameMap = self.nameMap
        spaceEscaped = self.spaceEscaped

        reportBase = self.reportBase
        reportDir = f"{reportBase}/{sheetName}"
        reportFile = f"{reportDir}/read.txt"
        rh = open(reportFile, "w")
        log(rh, "Reading the spreadsheets")

        def readXls(sheetRela):
            sep = "/" if sheetRela else ""
            sheetRep = f"[{sheetRela}]"

            sheetPath = f"{sheetDir}/{sheetName}{sep}{sheetRela}.xlsx"

            wb = loadXls(sheetPath, data_only=True)
            ws = wb.active

            (headRow, subHeadRow, *rows) = list(ws.rows)
            rows = [row for row in rows if any(c.value for c in row)]

            sheet = {}

            idFirstRow = {}

            for r, row in enumerate(ws.rows):
                if r in {0, 1}:
                    continue
                if not any(c.value for c in row):
                    continue

                (name, kind, triggerStr) = (
                    normalize(row[i].value or "") for i in range(3)
                )
                triggers = (
                    set()
                    if not triggerStr
                    else {
                        y
                        for x in triggerStr.split(";")
                        if (y := tnorm(x, spaceEscaped=spaceEscaped)) != ""
                    }
                )
                if not name:
                    name = list(triggers)[0] if triggers else ""
                    if name == "":
                        if kind:
                            log(
                                rh,
                                f"{sheetRep} row {r + 1:>3}: {kind}: "
                                "no entity name and no triggers",
                            )
                        continue
                    else:
                        log(
                            rh,
                            f"{sheetRep} row {r + 1:>3}: {kind}: "
                            f"no entity name, supplied synonym {name}",
                        )

                if not kind:
                    kind = defaultKind
                    log(
                        rh,
                        f"{sheetRep} row {r + 1:>3}: "
                        f"no kind name, supplied {defaultKind}",
                    )

                eid = toSmallId(name, transform=transform)
                eidkind = (eid, kind)
                firstRowEid = idFirstRow.get((eidkind), None)

                if firstRowEid is None:
                    idFirstRow[eidkind] = (r, name)
                    sheet[eidkind] = triggers

                    prev = nameMap.get(eidkind, None)

                    if prev is None:
                        nameMap[eidkind] = (name, sheetRela)
                    else:
                        (prevName, prevSheet) = prev

                        if prevName != name:
                            if toId(prevName) == toId(name):
                                severity = "minor"
                                error = False
                            else:
                                severity = "major"
                                error = True

                            log(
                                rh,
                                f"{sheetRep} {severity} name variant for {eidkind}:\n"
                                f"  in {prevSheet:<30} : '{prevName}'\n"
                                f"  in {sheetRep:<30} : '{name}'",
                                error=error,
                            )
                            log(rh, f"  will use '{prevName}' for {eidkind}")

                else:
                    (firstRow, firstName) = firstRowEid
                    if firstName == name:
                        severity = "identical"
                        error = False
                    elif toId(firstName) == toId(name):
                        severity = "minor variant in"
                        error = False
                    else:
                        severity = "major variant in"
                        error = True

                    log(
                        rh,
                        f"{sheetRep} {severity} name for {eidkind}:\n"
                        f"  in {firstRow + 1:<3} : '{firstName}'\n"
                        f"  in {r + 1:<3} : '{name}'\n",
                        error=error,
                    )
                    log(rh, f"  will merge triggers {triggers} with {sheet[eidkind]}")
                    sheet[eidkind] |= triggers

            return sheet

        def readDir(sheetRela, level):
            sheetRep = f"[{sheetRela}]"
            sep = "/" if sheetRela else ""

            (files, dirs) = dirContents(f"{sheetDir}/{sheetName}{sep}{sheetRela}")

            sheetSingle = {}
            sheetRange = {}

            for file in files:
                if file == DS_STORE:
                    continue

                match = SHEET_RE.match(file)
                if not match:
                    log(rh, f"{sheetRep} contains unrecognized file {file}")
                    continue

                (start, end) = match.group(1, 2)
                fileBase = f"{start}{end}"

                start = int(start)
                end = int(end[1:]) if end else None
                key = start if end is None else (start, end)

                sheetDest = sheetSingle if end is None else sheetRange
                sheetDest[key] = readXls(f"{sheetRela}/{fileBase}")

            sheetSubdirs = {}

            for dr in dirs:
                if level >= 3:
                    log(rh, f"{sheetRep} is at max depth, yet contains subdir {dr}")
                    continue

                if not dr.isdecimal():
                    log(rh, f"{sheetRep} contains non-numeric subdir {dr}")
                    continue

                sheetSubdirs[int(dr)] = readDir(f"{sheetRela}{sep}{dr}", level + 1)

            return dict(sng=sheetSingle, rng=sheetRange, sdr=sheetSubdirs)

        sheetMain = readXls("")
        sheetSubdirs = readDir("", 1)
        sheetData.raw = dict(main=sheetMain, sdr=sheetSubdirs)
        rh.close()

    def _combineSheets(self, sheetData):
        """Combines the spreadsheet info in single-section spreadsheets.

        Among the tweaks, there may be *ranged* spreadsheets, i.e. having the name
        *start*`-`*end*, which indicate that they contain tweaks for sections
        *start* to *end*. These will be converted to individual spreadsheet
        *start*, *start + 1*, ..., *end - 1*, *end*.
        """
        raw = sheetData.raw

        sheetMain = raw["main"]
        sheetTweaked = raw["sdr"]

        # combine the info in ranged sheets into single number sheets

        combined = dict(sheet=sheetMain, tweaks={})
        sheetData.combined = combined

        console("Combining the spreadsheets")

        def combineDir(info, dest):
            ranged = info.get("rng", {})
            single = info.get("sng", {})
            subdirs = info.get("sdr", {})

            for (start, end), sheet in sorted(ranged.items()):
                for i in range(start, end + 1):
                    updateDest = dest.setdefault(i, {}).setdefault("sheet", {})
                    for eidkind, triggers in sheet.items():
                        updateDest[eidkind] = triggers

            for i, sheet in single.items():
                updateDest = dest.setdefault(i, {}).setdefault("sheet", {})
                for eidkind, triggers in sheet.items():
                    updateDest[eidkind] = triggers

            for i, tweaks in subdirs.items():
                updateDest = dest.setdefault(i, {}).setdefault("tweaks", {})
                combineDir(tweaks, updateDest)

        combineDir(sheetTweaked, combined["tweaks"])

    def _compileSheets(self, sheetData):
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

        combined = sheetData.combined

        compiled = {}
        sheetData.compiled = compiled

        console("Compiling the spreadsheets")

        def compileSheet(path, parentData, info, dest):
            parentSheet = parentData["sheet"]
            sheet = info["sheet"]
            newSheet = {}
            dest["sheet"] = newSheet
            parentTMap = parentData.get("tMap", {})
            newTMap = {}
            dest["tMap"] = newTMap

            for eidkind, triggers in parentSheet.items():
                newSheet[eidkind] = triggers

            for eidkind, triggers in sheet.items():
                newSheet[eidkind] = triggers

                for trigger in triggers:
                    newTMap[trigger] = tuple(str(k) for k in path)

            for eidkind, triggers in newSheet.items():
                for trigger in triggers:
                    if trigger not in newTMap:
                        newTMap[trigger] = parentTMap[trigger]

        def compileDir(path, parentData, info, dest):
            if "sheet" in info:
                compileSheet(path, parentData, info, dest)
                parentData = dict(sheet=dest["sheet"], tMap=dest["tMap"])

            tweaks = info.get("tweaks", {})
            tweakDest = dest.setdefault("tweaks", {})

            for k in sorted(tweaks):
                compileDir(
                    path + (k,), parentData, tweaks[k], tweakDest.setdefault(k, {})
                )

        compileDir((), combined, combined, compiled)

    def _prepareSheets(self, sheetData):
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
        nameMap = self.nameMap
        compiled = sheetData.compiled

        sheetName = self.sheetName

        instructions = {}
        sheetData.instructions = instructions

        reportBase = self.reportBase
        reportDir = f"{reportBase}/{sheetName}"
        reportFile = f"{reportDir}/check.tsv"

        console("Checking the spreadsheets")

        checkData = ["sheet\tentities\tnotriggers\ttriggers\tambiguous\n"]
        ambiData = []
        notrigData = []

        mainNotrigData = set()

        def prepareSheet(path, info):
            isMain = len(path) == 0
            sheet = info["sheet"]
            tMap = info["tMap"]
            sheetR = ".".join(path)
            sheetRep = f"[{sheetR}]"

            triggerSet = set()
            tPos = collections.defaultdict(lambda: collections.defaultdict(set))
            idMap = collections.defaultdict(list)

            prepared = dict(tPos=tPos, tMap=tMap)

            instructions[path] = prepared

            for eidkind, triggers in sheet.items():
                if len(triggers) == 0:
                    name = nameMap[eidkind][0]

                    if isMain:
                        mainNotrigData.add(name)
                    else:
                        if name not in mainNotrigData:
                            notrigData.append((name, sheetR))

                for trigger in triggers:
                    triggerT = toTokens(trigger, spaceEscaped=spaceEscaped)
                    triggerSet.add(triggerT)
                    idMap[trigger].append(eidkind)

            for triggerT in triggerSet:
                for i, token in enumerate(triggerT):
                    tPos[i][token].add(triggerT)

            prepared["idMap"] = {
                trigger: eidkinds[0] for (trigger, eidkinds) in idMap.items()
            }

            nEnt = len(sheet)
            nTriggers = sum(len(triggers) for triggers in sheet.values())
            noTriggers = sum(1 for triggers in sheet.values() if len(triggers) == 0)
            noTrigMsg = "" if noTriggers == 0 else f", {noTriggers} without triggers;"

            ambi = 0
            msgs = []

            for trigger, eidkinds in sorted(idMap.items()):
                if len(eidkinds) <= 1:
                    continue

                tPath = tMap[trigger]

                if path != tPath:
                    continue

                msgs.append(f"""  trigger '{trigger}' used for:""")

                for eidkind in eidkinds:
                    name = nameMap[eidkind][0]
                    msgs.append(f"\t{name}")

                    ambiData.append((trigger, sheetR, name))

                ambi += 1

            ambiMsg = "" if ambi == 0 else f", {ambi} ambiguous"

            entMsg = f"entities: {nEnt} {noTrigMsg}"
            triggerMsg = f"triggers: {nTriggers} {ambiMsg}"

            console(f"{sheetRep:<25}: {entMsg:<35} {triggerMsg}")

            if len(msgs):
                console("\n".join(msgs))

            checkData.append(f"{sheetR}\t{nEnt}\t{noTriggers}\t{nTriggers}\t{ambi}\n")

        def prepareDir(path, info):
            if "sheet" in info:
                prepareSheet(path, info)

            tweaks = info.get("tweaks", {})

            for k in sorted(tweaks):
                prepareDir(path + (str(k),), tweaks[k])

        prepareDir((), compiled)

        with open(reportFile, "w") as rh:
            for c in checkData:
                rh.write(c)

        notrigFile = f"{reportDir}/notriggers.tsv"

        with open(notrigFile, "w") as nh:
            nh.write("name\tsheet\n")

            for name in sorted(mainNotrigData):
                nh.write(f"{name}\t\n")
            for name, sheet in sorted(notrigData):
                nh.write(f"{name}\t{sheet}\n")

        ambiFile = f"{reportDir}/ambitriggers.tsv"

        with open(ambiFile, "w") as ah:
            ah.write("trigger\tname\tsheet\n")

            for trigger, sheet, name in sorted(ambiData):
                ah.write(f"{trigger}\t{sheet}\t{name}\n")

    def showSheetsRaw(self, main=False):
        src = self.getSheetData()

        if src is None:
            console("Nothing to show")

        src = src.raw

        nameMap = self.nameMap

        def showSheet(sheet, tab):
            for eidkind, triggers in sorted(sheet.items()):
                (name, sheetRela) = nameMap[eidkind]
                triggerRep = "|".join(
                    t for t in sorted(triggers, key=lambda x: (-len(x), x))
                )
                console(f"{tab}  '{name}' {eidkind} : {triggerRep}")
            console(f"{tab}  ---")

        def showDir(head, tweaks, level):
            tab = "  " * level
            console(f"{tab}{head}")

            rng = tweaks.get("rng", {})
            for b, e in sorted(rng):
                console(f"{tab}  {b}-{e}.xslx")
                showSheet(rng[(b, e)], tab)

            sng = tweaks.get("sng", {})
            for k in sorted(sng):
                console(f"{tab}  {k}.xslx")
                showSheet(sng[k], tab)

            sdr = tweaks.get("sdr", {})

            for k in sorted(sdr):
                showDir(k, sdr[k], level + 1)

        if main:
            showSheet(src["main"], "")

        showDir("", src["sdr"], 0)

    def showSheetsCombined(self, main=False):
        src = self.getSheetData()

        if src is None:
            console("Nothing to show")

        src = src.combined

        nameMap = self.nameMap

        def showSheet(sheet, tab):
            for eidkind, triggers in sorted(sheet.items()):
                (name, sheetRela) = nameMap[eidkind]
                triggerRep = "|".join(
                    t for t in sorted(triggers, key=lambda x: (-len(x), x))
                )
                console(f"{tab}  '{name}' {eidkind} : {triggerRep}")
            console(f"{tab}  ---")

        def showDir(head, info, level):
            tab = "  " * level
            console(f"{tab}{head}")

            if "sheet" in info:
                if main or level > 0:
                    showSheet(info["sheet"], tab)

            tweaks = info.get("tweaks", {})

            for k in sorted(tweaks):
                showDir(k, tweaks[k], level + 1)

        showDir("", src, 0)

    def showSheetsCompiled(self, main=False):
        nameMap = self.nameMap
        src = self.compiled

        def showSheet(info, tab):
            sheet = info["sheet"]
            tMap = info["tMap"]

            for eidkind, triggers in sorted(sheet.items()):
                triggerSources = {tMap[t] for t in triggers}
                nTriggers = len(triggers)

                if not main and (nTriggers == 0 or triggerSources == {()}):
                    continue

                (name, sheetRela) = nameMap[eidkind]

                if nTriggers == 0:
                    triggerInfo = "X"
                else:
                    sourceRep = (
                        "X"
                        if len(triggerSources) == 0
                        else list(list(triggerSources)[0])
                    )
                    triggerRep = "|".join(
                        t for t in sorted(triggers, key=lambda x: (-len(x), x))
                    )
                    triggerInfo = f"{sourceRep} => {triggerRep}"

                console(f"{tab}  '{name}' {eidkind} : {triggerInfo}")
            console(f"{tab}  ---")

        def showDir(head, info, level):
            tab = "  " * level
            console(f"{tab}{head}")

            if "sheet" in info:
                if main or level > 0:
                    showSheet(info, tab)

            tweaks = info.get("tweaks", {})

            for k in sorted(tweaks):
                showDir(k, tweaks[k], level + 1)

        showDir("", src, 0)

    def showInstructions(self):
        src = self.getSheetData()

        if src is None:
            console("Nothing to show")

        instructions = src.instructions

        console("\n".join(f"{path}" for path in instructions))
