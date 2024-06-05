import collections
import re

from .helpers import tnorm, normalize, toId, toSmallId, toTokens
from ...core.helpers import console
from ...core.files import dirContents


DS_STORE = ".DS_Store"
SHEET_RE = re.compile(r"""^([0-9]+)((?:-[0-9]+)?)\.xlsx$""", re.I)


class Triggers:
    def __init__(self, Ner):
        self.loadXls = Ner.load_workbook
        self.sheetDir = Ner.sheetDir
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

    def readXls(self, sheetRela):
        loadXls = self.loadXls
        defaultKind = self.defaultKind
        transform = self.transform
        sheetDir = self.sheetDir
        nameMap = self.nameMap
        spaceEscaped = self.spaceEscaped

        sheetPath = f"{sheetDir}/{sheetRela}.xlsx"

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

            (name, kind, triggerStr) = (normalize(row[i].value or "") for i in range(3))
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
                        console(
                            f"{sheetRela} row {r + 1:>3}: {kind}: "
                            "no entity name and no triggers"
                        )
                    continue
                else:
                    console(
                        f"{sheetRela} row {r + 1:>3}: {kind}: "
                        f"no entity name, supplied synonym {name}"
                    )

            if not kind:
                kind = defaultKind
                console(
                    f"{sheetRela} row {r + 1:>3}: "
                    f"no kind name, supplied {defaultKind}"
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

                        console(
                            f"{severity} name variant for {eidkind}:\n"
                            f"  in {prevSheet:<30} : '{prevName}'\n"
                            f"  in {sheetRela:<30} : '{name}'",
                            error=error,
                        )
                        console(f"  will use '{prevName}' for {eidkind}")

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

                console(
                    f"{severity} name for {eidkind}:\n"
                    f"  in {firstRow + 1:<3} : '{firstName}'\n"
                    f"  in {r + 1:<3} : '{name}'\n",
                    error=error,
                )
                console(f"  will merge triggers {triggers} with {sheet[eidkind]}")
                sheet[eidkind] |= triggers

        return sheet

    def readDir(self, sheetRela, level):
        sheetDir = self.sheetDir
        (files, dirs) = dirContents(f"{sheetDir}/{sheetRela}")

        sheetSingle = {}
        sheetRange = {}

        for file in files:
            if file == DS_STORE:
                continue

            match = SHEET_RE.match(file)
            if not match:
                console(f"{sheetRela} contains unrecognized file {file}")
                continue

            (start, end) = match.group(1, 2)
            fileBase = f"{start}{end}"

            start = int(start)
            end = int(end[1:]) if end else None
            key = start if end is None else (start, end)

            sheetDest = sheetSingle if end is None else sheetRange
            sheetDest[key] = self.readXls(f"{sheetRela}/{fileBase}")

        sheetSubdirs = {}

        for dr in dirs:
            if level >= 3:
                console(f"{sheetRela} is at max depth, yet contains subdir {dr}")
                continue

            if not dr.isdecimal():
                console(f"{sheetRela} contains non-numeric subdir {dr}")
                continue

            sheetSubdirs[int(dr)] = self.readDir(f"{sheetRela}/{dr}", level + 1)

        return dict(sng=sheetSingle, rng=sheetRange, sdr=sheetSubdirs)

    def read(self, sheetName):
        self.sheetName = sheetName

        sheetMain = self.readXls(sheetName)
        sheetSubdirs = self.readDir(sheetName, 1)

        self.raw = dict(main=sheetMain, sdr=sheetSubdirs)
        self.compile()

    def compile(self):
        spaceEscaped = self.spaceEscaped
        raw = self.raw
        sheetName = self.sheetName
        nameMap = self.nameMap

        sheetMain = raw["main"]
        sheetTweaked = raw["sdr"]

        # combine the info in ranged sheets into single number sheets

        combined = dict(sheet=sheetMain, tweaks={})
        self.combined = combined

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

        # compile the info in tweaked sheets into complete sheets
        # by applying overrides to copies of parent sheets;
        # also collect additional data for the later computations:
        # tMap:
        #   remembers for each trigger the path to the spreadsheet
        #   that provides the definition used in this sheet

        compiled = {}
        self.compiled = compiled

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

            for trigger, p in parentTMap.items():
                newTMap[trigger] = p

            for eidkind, triggers in sheet.items():
                newSheet[eidkind] = triggers

                for trigger in triggers:
                    newTMap[trigger] = tuple(str(k) for k in path)

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

        # Now we have complete sheets for every context, the inheritance is resolved.
        # We perform additional checks.
        # We then generate instructions that will drive the search process.
        # The instructions are stored in a dict, keyed by the path for which
        # the instructions are valid.

        instructions = {}
        self.instructions = instructions

        diags = set()

        def prepareSheet(path, info):
            sheet = info["sheet"]
            tMap = info["tMap"]
            sheetRep = sheetName if path == () else ".".join(path)

            triggerSet = set()
            tPos = collections.defaultdict(lambda: collections.defaultdict(set))
            idMap = collections.defaultdict(list)

            data = dict(sheet=sheet, tPos=tPos, tMap=tMap)

            instructions[path] = data

            for eidkind, triggers in sheet.items():
                for trigger in triggers:
                    triggerT = toTokens(trigger, spaceEscaped=spaceEscaped)
                    triggerSet.add(triggerT)
                    idMap[trigger].append(eidkind)

            for triggerT in triggerSet:
                for i, token in enumerate(triggerT):
                    tPos[i][token].add(triggerT)

            nEnt = len(sheet)
            nTriggers = sum(len(triggers) for triggers in sheet.values())
            noTriggers = sum(1 for triggers in sheet.values() if len(triggers) == 0)
            noTrigMsg = (
                ""
                if noTriggers == 0
                else f", {noTriggers} without triggers;"
            )

            ambi = 0
            msgs = []

            for trigger, eidkinds in sorted(idMap.items()):
                if len(eidkinds) == 1:
                    continue

                diag = (trigger, tuple(eidkinds))

                if diag not in diags:
                    diags.add(diag)
                    msgs.append(f"""  trigger '{trigger}' used for:""")

                    for eidkind in eidkinds:
                        msgs.append(f"\t{nameMap[eidkind][0]}")

                ambi += 1

            ambiMsg = "" if ambi == 0 else f", {ambi} ambiguous"

            sheetMsg = f"Check {sheetRep}"
            entMsg = f"Entities: {nEnt} {noTrigMsg}"
            triggerMsg = f"Triggers: {nTriggers} {ambiMsg}"

            console(f"{sheetMsg:<25}: {entMsg:<35} {triggerMsg}")

            if len(msgs):
                console("\n".join(msgs))

            data["idMap"] = {
                trigger: eidkinds[0] for (trigger, eidkinds) in idMap.items()
            }

        def prepareDir(path, data):
            if "sheet" in data:
                prepareSheet(path, data)

            tweaks = data.get("tweaks", {})

            for k in sorted(tweaks):
                prepareDir(path + (str(k),), tweaks[k])

        prepareDir((), compiled)

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
