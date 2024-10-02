"""
# Export a TF dataset to a `pandas` data frame.

There is a natural mapping of a TF dataset with its nodes, edges and features to a
rectangular data frame with rows and columns:

*   the *nodes* correspond to *rows*;
*   the node *features* correspond to *columns*;
*   the *value* of a feature for a node is in the row that corresponds with the node
    and the column that corresponds with the feature.
*   the *edge* features correspond to columns, in that column you find for each row
    the nodes where edges arrive, i.e. the edges from the node that correspond with
    the row.

We also write the data that says which nodes are contained in which other nodes.
To each row we add the following columns:

*   for each node type, except the slot type, there is a column with named
    `in_nodeType`, that contains the node of the smallest object that
    contains the node of the row;

We compose the big table and save it as a tab delimited file.
This temporary result can be processed by `R` and `pandas`.

It turns out that for this size of the data `pandas` is a bit
quicker than R. It is also more Pythonic, which is a pro if you use other Python
programs, such as TF, to process the same data.

# Examples

*   [BHSA](https://nbviewer.org/github/ETCBC/bhsa/blob/master/tutorial/export.ipynb)
*   [Moby Dick](https://nbviewer.org/github/annotation/mobydick/blob/main/tutorial/exportPandas.ipynb)
*   [Ferdinand Huyck](https://nbviewer.org/github/CLARIAH/wp6-ferdinandhuyck/blob/main/tutorial/export.ipynb)
"""

from ..capable import CheckImport
from ..parameters import OTYPE, OSLOTS
from ..core.files import TEMP_DIR, fileOpen, unexpanduser as ux, expandDir, dirMake
from ..core.helpers import fitemize, pandasEsc, PANDAS_QUOTE, PANDAS_ESCAPE


HELP = """
Transforms TF dataset into `pandas`
"""

INT = "Int64"
STR = "str"
NA = [""]


def exportPandas(app, inTypes=None, exportDir=None):
    """Export a currently loaded TF dataset to `pandas`.

    The function proceeds by first producing a TSV file as an intermediate result.
    This is usually too big for GitHub, to it is produced in a `/_temp` directory
    that is usually in the `.gitignore` of the repo.

    This file serves as the basis for the export to a `pandas` data frame.

    !!! hint "R"
        You can import this file in other programs as well, e.g.
        [R](https://www.r-project.org)

    !!! note "Quotation, newlines, tabs, backslashes and escaping"
        If the data as it comes from TF contains newlines or tabs or
        double quotes, we put them escaped into the TSV, as follows:

        *   *newline* becomes *backslash* plus `n`;
        *   *tab* becomes a single space;
        *   *double quote* becomes *Control-A* plus *double quote*;
        *   *backslash* remains *backslash*.

        In this way, the TSV file is not disturbed by non-delimiting tabs, i.e.
        tabs that are part of the content of a field. No field will contain a tab!

        Also, no field will contain a newline, so the lines are not disturbed by
        newlines that are part of the content of a field. No field will contain a
        newline!

        Double quotes in a TSV file might pose a problem. Several programs interpret
        double quotes as a way to include tabs and newlines in the content of a field,
        especially if the quote occurs at the beginning of a field.
        That's why we escape it by putting a character in front of it that is very
        unlikely to occur in the text of a corpus: Ctrl A, which is ASCII character 1.

        Backslashes are no problem, but programs might interpret them in a special
        way in combination with specific following characters.

        Now what happens to these characters when `pandas` reads the file?

        We instruct the `pandas` table reading function to use the Control-A as
        escape char and the double quote as quote char.

        **Backslash**

        `pandas` has two special behaviours:

        *   *backslash* `n` becomes a *newline*;
        *   *backslash* *backslash* becomes a single *backslash*.

        This is almost what we want: the newline behaviour is desired; the
        reducing of backslashes not, but we leave it as it is.

        **Double quote**

        *Ctrl-A* plus *double quote* becomes *double quote*.

        That is exactly what we want.

    Parameters
    ----------
    app: object
        A `tf.advanced.app.App` object that represent a loaded corpus, together with
        all its loaded data modules.
    inTypes: string | iterable, optional None
        A bunch of node types for which columns should be made that contain nodes
        in which the row node is contained.
        If `None`, all node types will have such columns. But for certain TEI corpora
        this might lead to overly many columns.
        So, if you specify `""` or `{}`, there will only be columns for sectional
        node types.
        But you can also specify the list of such node types explicitly.
        In all cases, there will be columns for sectional node types.
    exportDir: string, optional None
        The directory to which the `pandas` file will be exported.
        If `None`, it is the `/pandas` directory in the repo of the app.
    """
    CI = CheckImport("pandas", "pyarrow")
    if CI.importOK(hint=True):
        (pandas, pyarrow) = CI.importGet()
    else:
        return

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

    for i, f in enumerate(sectionFeats):
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

    dtype = dict(nd=INT, otype=STR)

    for f in sectionTypes:
        dtype[f"in_{f}"] = INT

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

    with fileOpen(tableFile, mode="w") as hr:
        cells = (
            "nd",
            "otype",
            *textFeatures,
            *[f"in_{x}" for x in sectionTypes],
            *[f"in_{x}" for x in inTypes],
            *edgeFeatures,
            *nodeFeatures,
        )
        hr.write("\t".join(cells) + "\n")
        i = 0
        s = 0
        perc = 0

        for n in N.walk():
            nType = F.otype.v(n)
            textValues = [pandasEsc(str(Fs(f).v(n) or "")) for f in textFeatures]
            sectionNodes = [
                n if nType == section else (L.u(n, otype=section) or NA)[0]
                for section in sectionTypes
            ]
            inValues = [(L.u(n, otype=inType) or NA)[0] for inType in inTypes]
            edgeValues = [pandasEsc(str((Es(f).f(n) or NA)[0])) for f in edgeFeatures]
            nodeValues = [
                pandasEsc(
                    str(
                        (Fs(f).v(sectionNodes[sectionFeatIndex[f]]) or NA[0])
                        if f in sectionFeatIndex and nType in sectionTypeSet
                        else Fs(f).v(n) or ""
                    )
                )
                for f in nodeFeatures
            ]
            cells = (
                str(n),
                F.otype.v(n),
                *textValues,
                *[str(x) for x in sectionNodes],
                *[str(x) for x in inValues],
                *edgeValues,
                *nodeValues,
            )
            hr.write("\t".join(cells).replace("\n", "\\n") + "\n")
            i += 1
            s += 1
            if s == chunkSize:
                s = 0
                perc = int(round(i * 100 / F.otype.maxNode))
                app.info(f"{perc:>3}% {i:>7} nodes written")

    app.info(f"{perc:>3}% {i:>7} nodes written and done")
    app.indent(level=False)

    app.info(f"TSV file is {ux(tableFile)}")

    with fileOpen(tableFile, mode="r") as hr:
        rows = 0
        chars = 0
        columns = 0
        for i, line in enumerate(hr):
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

    dataFrame = pandas.read_table(
        tableFile,
        delimiter="\t",
        quotechar=PANDAS_QUOTE.encode("utf-8"),
        escapechar=PANDAS_ESCAPE.encode("utf-8"),
        doublequote=False,
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
