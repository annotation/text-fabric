import os
import pandas as pd

from ..parameters import TEMP_DIR
from ..core.helpers import unexpanduser as ux


HELP = """
Transforms TF dataset into Pandas
"""

INT = "Int64"
STR = "str"
NA = [""]
CHAPTER = "chapter"
CHUNK = "chunk"


def makeTable(
    app,
    textFeatures=("str", "after"),
    levelTypes=(CHAPTER, CHUNK),
    levelFeatures=(CHAPTER, CHUNK),
):
    api = app.api
    Fall = api.Fall
    Fs = api.Fs
    F = api.F
    N = api.N
    L = api.L

    (levelType1, levelType2) = levelTypes
    (levelFeat1, levelFeat2) = levelFeatures

    baseDir = f"{app.repoLocation}"
    tempDir = f"{baseDir}/{TEMP_DIR}"
    resultDir = f"{baseDir}/pandas"

    if not os.path.exists(tempDir):
        os.makedirs(tempDir)
    if not os.path.exists(resultDir):
        os.makedirs(resultDir)

    tableFile = f"{tempDir}/data-{app.version}.tsv"
    tableFilePd = f"{resultDir}/data-{app.version}.pd"

    features = sorted(set(Fall()) - {"otype", "oslots"} - set(textFeatures))

    dtype = dict(nd=INT, element=STR)

    for f in textFeatures:
        dtype[f] = STR

    for f in levelTypes:
        dtype[f"in.{f}"] = INT

    for f in features:
        if f.startswith("empty_"):
            parts = f.split("_", 2)
            tp = INT if len(parts) == 2 else STR
            dtype[f] = tp
        elif f.startswith("is_") or f.startswith("rend_") or f == levelFeat2:
            dtype[f] = INT
        else:
            dtype[f] = STR

    naValues = dict((x, set() if dtype[x] == STR else {""}) for x in dtype)

    with open(tableFile, "w") as hr:
        hr.write(
            "{}\t{}\t{}\t{}\t{}\n".format(
                "nd",
                "element",
                "\t".join(textFeatures),
                "\t".join(f"in.{x}" for x in levelTypes),
                "\t".join(features),
            )
        )
        chunkSize = 10000
        i = 0
        s = 0

        for n in N.walk():
            textValues = [str(Fs(f).v(n) or "") for f in textFeatures]
            levelValues = [(L.u(n, otype=level) or NA)[0] for level in levelTypes]
            nodeValues = [
                (
                    Fs(levelFeat1).v(L.u(n, otype=levelType1)[0])
                    if f == levelFeat1 and F.otype.v(n) == levelType2
                    else str(Fs(f).v(n) or "")
                )
                for f in features
            ]
            hr.write(
                "{}\t{}\t{}\t{}\t{}\n".format(
                    n,
                    F.otype.v(n),
                    ("\t".join(textValues)).replace("\n", "\\n"),
                    ("\t".join(str(x) for x in levelValues)),
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
