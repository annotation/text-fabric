import collections
import re
from copy import deepcopy

from .helpers import normalize, toSmallId, toTokens
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

        self.instructions = None
        """Will contain the information in a spreadsheet for marking up entities."""

    def readXls(self, sheetRela):
        loadXls = self.loadXls
        defaultKind = self.defaultKind
        transform = self.transform
        sheetDir = self.sheetDir

        sheetPath = f"{sheetDir}/{sheetRela}.xlsx"

        wb = loadXls(sheetPath, data_only=True)
        ws = wb.active

        (headRow, subHeadRow, *rows) = list(ws.rows)
        rows = [row for row in rows if any(c.value for c in row)]

        sheet = {}

        nameFirstRow = {}
        eidFirstRow = {}

        for r, row in enumerate(ws.rows):
            if r in {0, 1}:
                continue
            if not any(c.value for c in row):
                continue

            (name, kind, synonymStr) = (normalize(row[i].value or "") for i in range(3))
            synonyms = (
                set()
                if not synonymStr
                else {y for x in synonymStr.split(";") if (y := normalize(x)) != ""}
            )
            if not name:
                name = synonyms[0] if synonyms else ""
                if name == "":
                    if kind:
                        console(
                            f"{sheetRela} row {r + 1:>3}: {kind}: "
                            "no entity name and no synonyms"
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

            fr = nameFirstRow.get(name, None)
            nameFirstRow[name] = r + 1

            if fr is not None:
                console(
                    f"{sheetRela} row {r + 1:>3}: "
                    f"Name already seen in row {fr}: {name}"
                )
                continue

            eid = toSmallId(name, transform=transform)
            fr = eidFirstRow.get(eid, None)

            if fr is not None:
                console(
                    f"{sheetRela} row {r + 1:>3}: "
                    f"Eid already seen in row {fr}: {eid}"
                )
                continue

            sheet[eid] = dict(name=name, kind=kind, occspecs=synonyms)

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

        self.rawInfo = dict(main=sheetMain, sdr=sheetSubdirs)
        self.compile()

    def compile(self):
        spaceEscaped = self.spaceEscaped
        rawInfo = self.rawInfo
        sheetName = self.sheetName

        sheetMain = rawInfo["main"]
        sheetTweaked = rawInfo["sdr"]

        compiled = {"": dict(sheet=sheetMain)}
        self.compiled = compiled
        instructions = {}
        self.instructions = instructions

        def compileDir(parentSheet, sdr, dest):
            ranged = sdr.get("rng", {})
            single = sdr.get("sng", {})
            subdirs = sdr.get("sdr", {})

            for (start, end), sheet in sorted(ranged.items()):
                for i in range(start, end + 1):
                    dest.setdefault("tweaks", {}).setdefault(
                        i, dict(sheet=deepcopy(parentSheet))
                    )
                    parentCopy = dest["tweaks"][i]["sheet"]

                    for eid, info in sheet.items():
                        parentCopy[eid] = info

            for i, sheet in single.items():
                dest.setdefault("tweaks", {}).setdefault(
                    i, dict(sheet=deepcopy(parentSheet))
                )
                parentCopy = dest["tweaks"][i]["sheet"]

                for eid, info in sheet.items():
                    parentCopy[eid] = info

            for i, tweaks in subdirs.items():
                dest.setdefault("tweaks", {}).setdefault(
                    i, dict(sheet=deepcopy(parentSheet))
                )
                parentCopy = dest["tweaks"][i]["sheet"]
                compileDir(parentCopy, tweaks, dest["tweaks"][i])

        compileDir(sheetMain, sheetTweaked, compiled)

        diags = set()

        def prepareSheet(path, sheet):
            sheetRep = sheetName if path == () else ".".join(path)
            console(f"Checking {sheetRep}")

            namesByOcc = collections.defaultdict(list)
            qSeqs = set()
            qMap = collections.defaultdict(lambda: collections.defaultdict(set))
            idMap = {}
            nameMap = {}

            data = dict(
                sheet=sheet, qSeqs=qSeqs, qMap=qMap, idMap=idMap, nameMap=nameMap
            )

            instructions[path] = data

            for eid, info in sheet.items():
                name = info["name"]
                kind = info["kind"]
                occspecs = info["occspecs"]

                nameMap[(eid, kind)] = name

                for occspec in occspecs:
                    namesByOcc[occspec].append(name)
                    qTokens = toTokens(occspec, spaceEscaped=spaceEscaped)
                    qSeqs.add(qTokens)
                    idMap[qTokens] = (eid, kind)

            for qTokens in qSeqs:
                for i, qToken in enumerate(qTokens):
                    qMap[i][qToken].add(qTokens)

            nEid = len(sheet)
            nOcc = sum(len(info["occspecs"]) for info in sheet.values())
            noOccs = sum(1 for info in sheet.values() if len(info["occspecs"]) == 0)
            console(f"  {nEid} entities with {nOcc} occurrence specs")
            console(f"  {noOccs} entities do not have occurrence specifiers")

            nm = 0

            for occSpec, names in sorted(namesByOcc.items()):
                if len(names) == 1:
                    continue

                diag = (occSpec, tuple(names))
                if diag not in diags:
                    diags.add(diag)
                    console(f""""{occSpec}" used for:""")
                    for name in names:
                        console(f"\t{name}")
                nm += 1

            if nm == 0:
                console("  All occurrence specifiers are unambiguous")
            else:
                console(f"  {nm} occurrence specifiers are ambiguous")

        def prepareTweaks(path, tweaks):
            for i in sorted(tweaks):
                newPath = path + (str(i),)
                subTweaks = tweaks[i]
                prepareSheet(newPath, subTweaks["sheet"])

                if "tweaks" in subTweaks:
                    prepareTweaks(newPath, subTweaks["tweaks"])

        prepareSheet((), compiled[""]["sheet"])
        prepareTweaks((), compiled.get("tweaks", {}))

    def showInheritance(self):
        compiled = self.compiled

        def showSheet(parentSheet, sheet, tab):
            allKeys = set(sheet) | set(parentSheet)

            console(f"{tab}  sheet with {len(allKeys)} keys")

            for eid in allKeys:
                info = sheet.get(eid, {})
                parentInfo = parentSheet.get(eid, {})
                name = info.get("name", None)
                parentName = parentInfo.get("name", None)
                kind = info.get("kind", None)
                parentKind = parentInfo.get("kind", None)
                occspecs = info.get("occspecs", None)
                parentOccspecs = parentInfo.get("occspecs", None)

                diffName = parentName != name
                diffKind = parentKind != kind
                diffOccspecs = parentOccspecs != occspecs

                if diffName or diffKind or diffOccspecs:
                    nameRep = (
                        f"{parentName or 'ø'} => {name or 'ø'}"
                        if diffName
                        else f"{name}"
                    )
                    kindRep = (
                        f"{parentKind or 'ø'} => {kind or 'ø'}"
                        if diffKind
                        else f"{kind}"
                    )
                    occspecsRep = (
                        f"{parentOccspecs or 'ø'} => {occspecs or 'ø'}"
                        if diffOccspecs
                        else f"{occspecs}"
                    )

                    console(f"{tab}  '{eid}': {nameRep}, {kindRep}, {occspecsRep}")

        def showDir(parentSheet, tweaks, level):
            tab = "  " * level

            for i in sorted(tweaks):
                console(f"{tab}{i}")

                data = tweaks[i]

                thisSheet = data["sheet"]
                showSheet(parentSheet, thisSheet, tab)

                if "tweaks" in data:
                    showDir(thisSheet, data["tweaks"], level + 1)

        mainSheet = compiled[""]["sheet"]
        showSheet(mainSheet, mainSheet, "")
        showDir(mainSheet, compiled["tweaks"], 0)

    def showRawInfo(self, main=False):
        rawInfo = self.rawInfo

        def showSheet(sheet, tab):
            for eid in sorted(sheet):
                info = sheet[eid]
                name = info["name"]
                kind = info["kind"]
                occspecs = info["occspecs"]
                occspecsRep = "|".join(
                    c for c in sorted(occspecs, key=lambda x: (-len(x), x))
                )
                console(f"{tab}  {eid} {kind} {name} T {occspecsRep}")
            console(f"{tab}  ---")

        def showDir(head, tweaks, level):
            console("\n")

            tab = "  " * level
            console(f"{tab}{head}")

            sng = tweaks.get("sng", {})
            for k in sorted(sng):
                console(f"{tab}{k}.xslx")
                showSheet(sng[k], tab)

            rng = tweaks.get("rng", {})
            for b, e in sorted(rng):
                console(f"{tab}{b}-{e}.xslx")
                showSheet(rng[(b, e)], tab)

            sdr = tweaks.get("sdr", {})
            for k in sorted(sdr):
                showDir(k, sdr[k], level + 1)

            console("\n")

        if main:
            showSheet(rawInfo["main"], "")

        showDir("", rawInfo["sdr"], 0)
