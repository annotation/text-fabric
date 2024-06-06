import collections
import re

from .helpers import tnorm, normalize, toId, toSmallId, toTokens, log
from ...core.helpers import console
from ...core.files import dirContents


DS_STORE = ".DS_Store"
SHEET_RE = re.compile(r"""^([0-9]+)((?:-[0-9]+)?)\.xlsx$""", re.I)


class Triggers:
    def __init__(self, Ner):
        self.loadXls = Ner.load_workbook
        self.sheetDir = Ner.sheetDir
        self.reportDir = Ner.reportDir
        settings = Ner.settings
        self.spaceEscaped = settings.spaceEscaped
        self.transform = settings.transform
        keywordFeatures = settings.keywordFeatures
        kindFeature = keywordFeatures[0]
        self.kindFeature = kindFeature
        defaultValues = settings.defaultValues
        self.defaultKind = defaultValues.get(kindFeature, "")

        self.nameMap = {}
        """Will contain a mapping from entities to names.

        The entities are keyed by their (eid, kind) tuple.
        The values are names plus the sheet where they are first defined.
        """

        self.instructions = None
        """Will contain the information in a spreadsheet for marking up entities."""

    def intake(self, sheetName):
        """Read the spreadsheets and translate them in actionable data for search.

        Parameters
        ----------
        sheetName: string
            The base name of the sheet, without extension.
            It is assume that a spreadsheet with that name and extension `.xlsx` exists
            in the expected location.

            Next to it a subdirectory of the same name may exist, which contains
            additional spreadsheets and subdirectories that contain
            increasingly specific tweaks on top of the base spreadsheet.
        """
        self.sheetName = sheetName
        self.read()
        self.combine()
        self.compile()
        self.prepare()

    def read(self):
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

        reportDir = self.reportDir
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
        self.raw = dict(main=sheetMain, sdr=sheetSubdirs)
        rh.close()

    def combine(self):
        """Combines the spreadsheet info in single-section spreadsheets.

        Among the tweaks, there may be *ranged* spreadsheets, i.e. having the name
        *start*`-`*end*, which indicate that they contain tweaks for sections
        *start* to *end*. These will be converted to individual spreadsheet
        *start*, *start + 1*, ..., *end - 1*, *end*.
        """
        raw = self.raw

        sheetMain = raw["main"]
        sheetTweaked = raw["sdr"]

        # combine the info in ranged sheets into single number sheets

        combined = dict(sheet=sheetMain, tweaks={})
        self.combined = combined

        console("Combining the spreadsheets")

        def combineDir(data, dest):
            ranged = data.get("rng", {})
            single = data.get("sng", {})
            subdirs = data.get("sdr", {})

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

    def compile(self):
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

        combined = self.combined

        compiled = {}
        self.compiled = compiled

        console("Compiling the spreadsheets")

        def compileSheet(path, parentData, data, dest):
            parentSheet = parentData["sheet"]
            sheet = data["sheet"]
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

        def compileDir(path, parentData, data, dest):
            if "sheet" in data:
                compileSheet(path, parentData, data, dest)
                parentData = dict(sheet=dest["sheet"], tMap=dest["tMap"])

            tweaks = data.get("tweaks", {})
            tweakDest = dest.setdefault("tweaks", {})

            for k in sorted(tweaks):
                compileDir(
                    path + (k,), parentData, tweaks[k], tweakDest.setdefault(k, {})
                )

        compileDir((), combined, combined, compiled)

    def prepare(self):
        """Transform the sheets into instructions.

        Now we have complete sheets for every context, the inheritance is resolved.
        Every sheet specifies a mapping from triggers to names, and remembers
        which (possibly other) sheet mapped a specific trigger to its name.

        We perform additional checks on the consistency and completeness of the
        resulting sheets.

        Then we generate instructions out of the sheets: data that the search
        algorithm needs to do its work.

        For each path to tweaked sheet we collect a portion of data:

        *   `tPos`: a compilation of all triggers in the sheet, so that
            we can search for them simultaneously;
        *   `tMap`: a mapping from triggers to the path of the sheet that defined this
            trigger;
        *   `idMap`: a mapping from triggers their corresponding entities.

        So every portion of data is addressed by a `path` key. This key is a tuple
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
        compiled = self.compiled

        instructions = {}
        self.instructions = instructions

        reportDir = self.reportDir
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

            data = dict(tPos=tPos, tMap=tMap)

            instructions[path] = data

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

            data["idMap"] = {
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

        def prepareDir(path, data):
            if "sheet" in data:
                prepareSheet(path, data)

            tweaks = data.get("tweaks", {})

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
            for (name, sheet) in sorted(notrigData):
                nh.write(f"{name}\t{sheet}\n")

        ambiFile = f"{reportDir}/ambitriggers.tsv"

        with open(ambiFile, "w") as ah:
            ah.write("trigger\tname\tsheet\n")

            for (trigger, sheet, name) in sorted(ambiData):
                ah.write(f"{trigger}\t{sheet}\t{name}\n")

    def showRaw(self, main=False):
        nameMap = self.nameMap
        src = self.raw

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

    def showCombined(self, main=False):
        nameMap = self.nameMap
        src = self.combined

        def showSheet(sheet, tab):
            for eidkind, triggers in sorted(sheet.items()):
                (name, sheetRela) = nameMap[eidkind]
                triggerRep = "|".join(
                    t for t in sorted(triggers, key=lambda x: (-len(x), x))
                )
                console(f"{tab}  '{name}' {eidkind} : {triggerRep}")
            console(f"{tab}  ---")

        def showDir(head, data, level):
            tab = "  " * level
            console(f"{tab}{head}")

            if "sheet" in data:
                if main or level > 0:
                    showSheet(data["sheet"], tab)

            tweaks = data.get("tweaks", {})

            for k in sorted(tweaks):
                showDir(k, tweaks[k], level + 1)

        showDir("", src, 0)

    def showCompiled(self, main=False):
        nameMap = self.nameMap
        src = self.compiled

        def showSheet(data, tab):
            sheet = data["sheet"]
            tMap = data["tMap"]

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

        def showDir(head, data, level):
            tab = "  " * level
            console(f"{tab}{head}")

            if "sheet" in data:
                if main or level > 0:
                    showSheet(data, tab)

            tweaks = data.get("tweaks", {})

            for k in sorted(tweaks):
                showDir(k, tweaks[k], level + 1)

        showDir("", src, 0)

    def showInstructions(self):
        instructions = self.instructions
        console("\n".join(f"{path}" for path in instructions))
