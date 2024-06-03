import re
from copy import deepcopy

from .helpers import normalize, toSmallId
from ...core.helpers import console
from ...core.files import dirContents


DS_STORE = ".DS_Store"
SHEET_RE = re.compile(r"""^([0-9]+)((?:-[0-9]+)?)\.xlsx$""", re.I)


class Triggers:
    def __init__(self, Ner):
        self.loadXls = Ner.load_workbook
        self.sheetDir = Ner.sheetDir
        settings = Ner.settings
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

        info = dict(name={}, kind={}, occs={})

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

            info["name"][eid] = name
            info["kind"][eid] = kind
            info["occs"][eid] = synonyms

        return info

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
        rawInfo = self.rawInfo
        sheetName = self.sheetName

        sheetMain = rawInfo["main"]
        sheetTweaked = rawInfo["sdr"]

        compiled = {"": dict(sheet=sheetMain)}
        instructions = {}
        self.instructions = instructions

        def compileDir(parentSheet, sdr, dest):
            ranged = sdr.get("rng", {})
            single = sdr.get("sng", {})
            subdirs = sdr.get("sdr", {})

            for (start, end), info in sorted(ranged.items()):
                for i in range(start, end + 1):
                    dest.setdefault("tweaks", {}).setdefault(
                        i, dict(sheet=deepcopy(parentSheet))
                    )
                    parentCopy = dest["tweaks"][i]["sheet"]

                    for kind, data in info.items():
                        parentCopy.setdefault(kind, {})
                        parentCopy[kind] |= data

            for i, info in single.items():
                dest.setdefault("tweaks", {}).setdefault(
                    i, dict(sheet=deepcopy(parentSheet))
                )
                parentCopy = dest["tweaks"][i]["sheet"]

                for kind, data in info.items():
                    parentCopy.setdefault(kind, {})
                    parentCopy[kind] |= data

            for i, info in subdirs.items():
                dest.setdefault("tweaks", {}).setdefault(
                    i, dict(sheet=deepcopy(parentSheet))
                )
                parentCopy = dest["tweaks"][i]["sheet"]
                compileDir(parentCopy, info, dest["tweaks"][i])

        compileDir(sheetMain, sheetTweaked, compiled)

        diags = set()

        def checkSheet(path, sheet):
            sheetRep = sheetName if path == () else ".".join(str(x) for x in path)
            console(f"Checking {sheetRep}")

            namesByOcc = {}

            name = sheet["name"]
            kind = sheet["kind"]
            occs = sheet["occs"]
            allKeys = set(name) | set(kind) | set(occs)

            instr = {}
            instructions[path] = instr

            for eid in sorted(allKeys):
                nm = name.get(eid, "")
                kd = kind.get(eid, "")
                oc = occs.get(eid, set())

                instr[eid] = dict(name=nm, kind=kd, occSpecs=oc)

                for occSpec in oc:
                    namesByOcc.setdefault(occSpec, []).append(nm)

            nEid = len(instr)
            nOcc = sum(len(x) for x in occs.values())
            noOccs = sum(1 for x in occs.values() if len(x) == 0)
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

        def checkTweaks(path, tweaks):
            for i in sorted(tweaks):
                newPath = path + (i,)
                subTweaks = tweaks[i]
                checkSheet(newPath, subTweaks["sheet"])

                if "tweaks" in subTweaks:
                    checkTweaks(newPath, subTweaks["tweaks"])

        checkSheet((), compiled[""]["sheet"])
        checkTweaks((), compiled.get("tweaks", {}))

    def showInfo(self):
        compiledInfo = self.compiledInfo

        def showSheet(parentInfo, info, tab):
            parentName = parentInfo["name"]
            parentKind = parentInfo["kind"]
            parentOccs = parentInfo["occs"]
            name = info["name"]
            kind = info["kind"]
            occs = info["occs"]
            allParentKeys = set(parentName) | set(parentKind) | set(parentOccs)
            allKeys = set(name) | set(kind) | set(occs)

            console(f"{tab}  sheet with {len(allKeys)} keys")

            for eid in allParentKeys | allKeys:
                parentNm = parentName.get(eid, None)
                nm = name.get(eid, None)
                parentKd = parentKind.get(eid, None)
                kd = kind.get(eid, None)
                parentOc = parentOccs.get(eid, None)
                oc = occs.get(eid, None)

                diffNm = parentNm != nm
                diffKd = parentKd != kd
                diffOc = parentOc != oc

                if diffNm or diffKd or diffOc:
                    nmRep = f"{parentNm or 'ø'} => {nm or 'ø'}" if diffNm else f"{nm}"
                    kdRep = f"{parentKd or 'ø'} => {kd or 'ø'}" if diffKd else f"{kd}"
                    ocRep = f"{parentOc or 'ø'} => {oc or 'ø'}" if diffOc else f"{oc}"

                    console(f"{tab}  {eid:>30} {nmRep}, {kdRep}, {ocRep}")

        def showDir(parentSheet, info, level):
            console("\n")

            tab = "  " * level
            console(f"{tab}")

            for i in sorted(info):
                console(f"{tab}{i}")

                data = info[i]

                thisSheet = data["sheet"]
                showSheet(parentSheet, thisSheet, tab)

                if "tweaks" in data:
                    showDir(thisSheet, data["tweaks"], level + 1)

            console("\n")

        mainSheet = compiledInfo[""]["sheet"]
        showSheet(mainSheet, mainSheet, "")
        showDir(mainSheet, compiledInfo["tweaks"], 0)

    def showRawInfo(self, main=False):
        rawInfo = self.rawInfo

        def showSheet(info, tab):
            name = info["name"]
            kind = info["kind"]
            occs = info["occs"]
            allKeys = set(name) | set(kind) | set(occs)

            for eid in sorted(allKeys):
                nm = name.get(eid, "")
                kd = kind.get(eid, "")
                oc = occs.get(eid, set())
                oc = "|".join(c for c in sorted(oc, key=lambda x: (-len(x), x)))
                console(f"{tab}  {eid:<30} {kd:<5} {nm:<40} T {oc}")
            console(f"{tab}  ---")

        def showDir(head, info, level):
            console("\n")

            tab = "  " * level
            console(f"{tab}{head}")

            sng = info.get("sng", {})
            for k in sorted(sng):
                console(f"{tab}{k}.xslx")
                showSheet(sng[k], tab)

            rng = info.get("rng", {})
            for b, e in sorted(rng):
                console(f"{tab}{b}-{e}.xslx")
                showSheet(rng[(b, e)], tab)

            sdr = info.get("sdr", {})
            for k in sorted(sdr):
                showDir(k, sdr[k], level + 1)

            console("\n")

        if main:
            showSheet(rawInfo["main"], "")

        showDir("", rawInfo["sdr"], 0)
