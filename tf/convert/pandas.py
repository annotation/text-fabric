import os
import math
import pandas as pd

from ..parameters import TEMP_DIR, OTYPE, OSLOTS
from ..core.helpers import unexpanduser as ux


HELP = """
Transforms TF dataset into Pandas
"""

INT = "Int64"
STR = "str"
NA = [""]


def exportPandas(app):
    api = app.api
    Fall = api.Fall
    Fs = api.Fs
    F = api.F
    N = api.N
    L = api.L
    T = api.T
    TF = api.TF

    sectionTypes = T.sectionTypes
    sectionFeats = T.sectionFeats

    sectionTypeSet = set(sectionTypes)
    sectionFeatIndex = {}

    for (i, f) in enumerate(sectionFeats):
        sectionFeatIndex[f] = i

    textFeatures = [x[0][0] for x in TF.cformats[T.defaultFormat][2]]
    features = sorted(set(Fall()) - {OTYPE, OSLOTS} - set(textFeatures))

    dtype = dict(nd=INT, element=STR)

    for f in sectionTypes:
        dtype[f"in.{f}"] = INT

    for f in features:
        dtype[f] = INT if Fs(f).meta["valueType"] == "int" else STR

    naValues = dict((x, set() if dtype[x] == STR else {""}) for x in dtype)

    baseDir = f"{app.repoLocation}"
    tempDir = f"{baseDir}/{TEMP_DIR}"
    resultDir = f"{baseDir}/pandas"

    if not os.path.exists(tempDir):
        os.makedirs(tempDir)
    if not os.path.exists(resultDir):
        os.makedirs(resultDir)

    tableFile = f"{tempDir}/data-{app.version}.tsv"
    tableFilePd = f"{resultDir}/data-{app.version}.pd"

    chunkSize = max((10, 10 ** int(round(math.log(F.otype.maxNode / 100, 10)))))

    with open(tableFile, "w") as hr:
        hr.write(
            "{}\t{}\t{}\t{}\t{}\n".format(
                "nd",
                "element",
                "\t".join(textFeatures),
                "\t".join(f"in.{x}" for x in sectionTypes),
                "\t".join(features),
            )
        )
        chunkSize = 10000
        i = 0
        s = 0

        for n in N.walk():
            nType = F.otype.v(n)
            textValues = [str(Fs(f).v(n) or "") for f in textFeatures]
            sectionValues = [
                n if nType == section else (L.u(n, otype=section) or NA)[0]
                for section in sectionTypes
            ]
            nodeValues = [
                str(
                    (Fs(f).v(sectionValues[sectionFeatIndex[f]]) or "")
                    if f in sectionFeatIndex and nType in sectionTypeSet
                    else Fs(f).v(n) or ""
                )
                for f in features
            ]
            hr.write(
                "{}\t{}\t{}\t{}\t{}\n".format(
                    n,
                    F.otype.v(n),
                    ("\t".join(textValues)).replace("\n", "\\n"),
                    ("\t".join(str(x) for x in sectionValues)),
                    ("\t".join(nodeValues)),
                )
            )
            i += 1
            s += 1
            if s == chunkSize:
                s = 0
                app.info("{:>7} nodes written".format(i))

    app.info("{:>7} nodes written and done".format(i))

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
    app.info(f"PD  in {ux(tableFilePd)}")
