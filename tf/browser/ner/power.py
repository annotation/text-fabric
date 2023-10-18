from openpyxl import load_workbook

from ...core.files import mTime, fileExists, readYaml, writeYaml
from ...core.helpers import console
from .helpers import normalize, toSmallId, toTokens
from .annotate import Annotate


class PowerNER(Annotate):
    def __init__(self, app):
        super().__init__(app)

    def yamlFromSheet(self, fileIn, fileOut):
        settings = self.settings
        transform = settings.transform
        keywordFeatures = settings.keywordFeatures
        kindFeature = keywordFeatures[0]
        defaultValues = settings.defaultValues

        wb = load_workbook(fileIn, data_only=True)
        ws = wb.active

        (headRow, subHeadRow, *rows) = list(ws.rows)
        rows = [row for row in rows if any(c.value for c in row)]

        defaultKind = defaultValues.get(kindFeature, "")

        info = {}

        for r, row in enumerate(ws.rows):
            if r in {0, 1}:
                continue
            if not any(c.value for c in row):
                continue

            (ent, synonyms) = (normalize(row[i].value or "") for i in range(2))
            eid = toSmallId(ent, transform=transform)

            if not ent:
                console(f"Row {r:>3}: no entity name")
                continue

            i = 0
            while eid in info:
                i += 1
                eid = f"{eid}.{i}"
                console(f"Row {r:>3}: multiple instances ({eid})")

            occs = sorted(
                (normalize(x) for x in ([] if not synonyms else synonyms.split(";"))),
                key=lambda x: -len(x),
            )
            info[eid] = {"name": ent, kindFeature: defaultKind, "occs": occs}

        writeYaml(info, asFile=fileOut)

        nEid = len(info)
        nOcc = sum(len(x["occs"]) for x in info.values())
        noOccs = sum(1 for x in info.values() if len(x["occs"]) == 0)
        console(f"{nEid} entities with {nOcc} occurrence specs")
        console(f"{noOccs} entities do not have occurrence specifiers")

    def readInstructions(self, basePath):
        xlsFile = f"{basePath}.xlsx"
        yamlFile = f"{basePath}.yaml"

        doConvert = False

        if not fileExists(yamlFile):
            if not fileExists(xlsFile):
                console(f"no instructions found: {yamlFile} and {xlsFile} don't exist")
                return

            doConvert = True
        else:
            if fileExists(xlsFile) and mTime(yamlFile) < mTime(xlsFile):
                doConvert = True

        if doConvert:
            self.yamlFromSheet(xlsFile, yamlFile)

        self.instructions = readYaml(asFile=yamlFile)

    def makeInventory(self):
        instructions = self.instructions

        qSets = set()

        for info in instructions.values():
            for occ in info.occs:
                qSets.add(toTokens(occ))

        self.inventory = self.findOccs(qSets)
        self.showInventory()

    def showInventory(self):
        instructions = self.instructions
        inventory = self.inventory

        total = 0

        for eid, info in instructions.items():
            name = info.name
            occs = info.occs

            for occ in occs:
                matches = inventory.get(toTokens(occ), None)
                if matches is None:
                    continue
                n = len(matches)
                total += n
                console(f"{eid:<24} {occ:<20} {n:>5} x {name}")

        console(f"Total {total}")

    def markEntities(self):
        instructions = self.instructions
        settings = self.settings
        keywordFeatures = settings.keywordFeatures
        kindFeature = keywordFeatures[0]

        newEntities = []

        qSets = set()
        fValsByQTokens = {}

        for eid, info in instructions.items():
            kind = info[kindFeature]

            occs = info.occs
            if not len(occs):
                continue

            for occ in info.occs:
                qTokens = toTokens(occ)
                fValsByQTokens.setdefault(qTokens, set()).add((eid, kind))
                qSets.add(qTokens)

        results = self.findOccs(qSets)

        for (qTokens, matches) in results.items():
            for fVals in fValsByQTokens[qTokens]:
                newEntities.append((fVals, matches))

        self.addEntities(newEntities, silent=False)
