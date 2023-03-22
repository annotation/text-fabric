import pandas as pd

from ..parameters import OTYPE, OSLOTS
from ..core.files import TEMP_DIR, unexpanduser as ux, expandDir, dirMake
from ..core.helpers import fitemize

HELP = """
Transforms TF dataset into Pandas
"""

INT = "Int64"
STR = "str"
NA = [""]


def exportPandas(app, inTypes=None, exportDir=None):
    api = app.api
    Eall = api.Eall
    Fall = api.Fall
    Es = api.Es
    Fs = api.Fs
    F = api.F
    N = api.N
    L = api.L
    T = api.T
    TF = api.TF

    app.indent(reset=True)

    sectionTypes = T.sectionTypes
    sectionFeats = T.sectionFeats

    sectionTypeSet = set(sectionTypes)
    sectionFeatIndex = {}

    for (i, f) in enumerate(sectionFeats):
        sectionFeatIndex[f] = i

    skipFeatures = {f for f in Fall() + Eall() if "@" in f}

    textFeatures = set()
    for textFormatSpec in TF.cformats.values():
        for featGroup in textFormatSpec[2]:
            for feat in featGroup[0]:
                textFeatures.add(feat)
    textFeatures = sorted(textFeatures)

    inTypes = [
        t
        for t in (F.otype.all if inTypes is None else fitemize(inTypes))
        if t not in sectionTypes
    ]
    edgeFeatures = sorted(set(Eall()) - {OSLOTS} - skipFeatures)
    nodeFeatures = sorted(set(Fall()) - {OTYPE} - set(textFeatures) - skipFeatures)

    dtype = dict(nd=INT, element=STR)

    for f in sectionTypes:
        dtype[f"in.{f}"] = INT

    for f in nodeFeatures:
        dtype[f] = INT if Fs(f).meta["valueType"] == "int" else STR

    naValues = dict((x, set() if dtype[x] == STR else {""}) for x in dtype)

    baseDir = f"{app.repoLocation}"
    tempDir = f"{baseDir}/{TEMP_DIR}"
    if exportDir is None:
        exportDir = f"{baseDir}/pandas"
    else:
        exportDir = exportDir
        exportDir = expandDir(app, exportDir)

    dirMake(tempDir)
    dirMake(exportDir)

    tableFile = f"{tempDir}/data-{app.version}.tsv"
    tableFilePd = f"{exportDir}/data-{app.version}.pd"

    chunkSize = max((100, int(round(F.otype.maxNode / 20))))

    app.info("Create tsv file ...")
    app.indent(level=True, reset=True)

    with open(tableFile, "w") as hr:
        hr.write(
            "{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                "nd",
                "element",
                "\t".join(textFeatures),
                "\t".join(f"in.{x}" for x in sectionTypes),
                "\t".join(f"in.{x}" for x in inTypes),
                "\t".join(edgeFeatures),
                "\t".join(nodeFeatures),
            )
        )
        i = 0
        s = 0
        perc = 0

        for n in N.walk():
            nType = F.otype.v(n)
            textValues = [
                str(Fs(f).v(n) or "").replace("\t", "\\t") for f in textFeatures
            ]
            sectionNodes = [
                n if nType == section else (L.u(n, otype=section) or NA)[0]
                for section in sectionTypes
            ]
            inValues = [(L.u(n, otype=inType) or NA)[0] for inType in inTypes]
            edgeValues = [
                str((Es(f).f(n) or NA)[0]).replace("\t", "\\t") for f in edgeFeatures
            ]
            nodeValues = [
                str(
                    (Fs(f).v(sectionNodes[sectionFeatIndex[f]]) or NA[0])
                    if f in sectionFeatIndex and nType in sectionTypeSet
                    else Fs(f).v(n) or ""
                ).replace("\t", "\\t")
                for f in nodeFeatures
            ]
            hr.write(
                "{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                    n,
                    F.otype.v(n),
                    ("\t".join(textValues)),
                    ("\t".join(str(x) for x in sectionNodes)),
                    ("\t".join(str(x) for x in inValues)),
                    ("\t".join(edgeValues)),
                    ("\t".join(nodeValues)),
                ).replace("\n", "\\n")
                + "\n"
            )
            i += 1
            s += 1
            if s == chunkSize:
                s = 0
                perc = int(round(i * 100 / F.otype.maxNode))
                app.info(f"{perc:>3}% {i:>7} nodes written")

    app.info(f"{perc:>3}% {i:>7} nodes written and done")
    app.indent(level=False)

    app.info(f"TSV file is {ux(tableFile)}")

    with open(tableFile, "r") as hr:
        rows = 0
        chars = 0
        columns = 0
        for (i, line) in enumerate(hr):
            if i == 0:
                columns = line.split("\t")
                app.info(f"Columns {len(columns)}:")
                for col in columns:
                    app.info(f"\t{col}")
            rows += 1
            chars += len(line)
    app.info(f"\t{rows} rows")
    app.info(f"\t{chars} characters")

    app.info("Importing into Pandas ...")
    app.indent(level=True, reset=True)
    app.info("Reading tsv file ...")

    dataFrame = pd.read_table(
        tableFile,
        delimiter="\t",
        low_memory=False,
        encoding="utf8",
        keep_default_na=False,
        na_values=naValues,
        dtype=dtype,
    )
    app.info("Done. Size = {}".format(dataFrame.size))
    app.info("Saving as Parquet file ...")
    dataFrame.to_parquet(tableFilePd, engine="pyarrow")
    app.info("Saved")
    app.indent(level=False)
    app.info(f"PD  in {ux(tableFilePd)}")
