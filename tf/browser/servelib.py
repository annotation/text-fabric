"""
# Common Server Related Functions

## About

Here are functions that are being used by various parts of the
TF browser infrastructure, such as

*   `tf.browser.web`
*   `tf.browser.start`
"""

from io import BytesIO
from zipfile import ZipFile

from flask import request

from ..parameters import ZIP_OPTIONS
from ..core.files import writeJson


DEFAULT_NAME = "default"

BATCH = 20


def getInt(x, default=1):
    if len(x) > 15:
        return default
    if not x.isdecimal():
        return default
    return int(x)


def batchAround(nResults, position, batch):
    halfBatch = int((batch + 1) / 2)
    left = min(max(position - halfBatch, 1), nResults)
    right = max(min(position + halfBatch, nResults), 1)
    discrepancy = batch - (right - left + 1)
    if discrepancy != 0:
        right += discrepancy
    if right > nResults:
        right = nResults
    return (left, right)


def getFormData(interfaceDefaults):
    """Get form data.

    The TF browser user interacts with the web app by clicking and typing,
    as a result of which a HTML form gets filled in.
    This form as regularly submitted to the web server with a request
    for a new incarnation of the page: a response.

    The values that come with a request, must be peeled out of the form,
    and stored as logical values.

    Most of the data has a known function to the web server,
    but there is also a list of web app dependent options.
    """

    form = {}
    jobName = request.form.get("jobName", "").strip()
    resetForm = request.form.get("resetForm", "")
    form["resetForm"] = resetForm

    if jobName:
        form["jobName"] = jobName
        form["loadJob"] = ""
    else:
        form["jobName"] = DEFAULT_NAME
        form["loadJob"] = "1"
        form["resetForm"] = "1"

    form["query"] = request.form.get("query", "").replace("\r", "")
    form["messages"] = request.form.get("messages", "") or ""
    form["features"] = request.form.get("features", "") or ""
    form["tuples"] = request.form.get("tuples", "").replace("\r", "")
    form["sections"] = request.form.get("sections", "").replace("\r", "")
    form["appName"] = request.form.get("appName", "")
    form["side"] = request.form.get("side", "")
    form["dstate"] = request.form.get("dstate", "")
    form["metaopen"] = request.form.get("metaopen", "")
    form["author"] = request.form.get("author", "").strip()
    form["title"] = request.form.get("title", "").strip()
    form["description"] = request.form.get("description", "").replace("\r", "")
    form["forceEdges"] = request.form.get("forceEdges", None)
    form["hideTypes"] = request.form.get("hideTypes", None)
    form["condensed"] = request.form.get("condensed", "")
    form["baseTypes"] = tuple(request.form.getlist("baseTypes"))
    form["hiddenTypes"] = tuple(request.form.getlist("hiddenTypes"))
    form["edgeFeatures"] = tuple(request.form.getlist("edgeFeatures"))
    form["condenseType"] = request.form.get("condenseType", "")
    form["textFormat"] = request.form.get("textFormat", "")
    form["sectionsExpandAll"] = request.form.get("sectionsExpandAll", "")
    form["tuplesExpandAll"] = request.form.get("tuplesExpandAll", "")
    form["queryExpandAll"] = request.form.get("queryExpandAll", "")
    form["passageOpened"] = request.form.get("passageOpened", "")
    form["sectionsOpened"] = request.form.get("sectionsOpened", "")
    form["tuplesOpened"] = request.form.get("tuplesOpened", "")
    form["queryOpened"] = request.form.get("queryOpened", "")
    form["mode"] = request.form.get("mode", "") or "passage"
    form["position"] = getInt(request.form.get("position", ""), default=1)
    form["batch"] = getInt(request.form.get("batch", ""), default=BATCH)
    form["sec0"] = request.form.get("sec0", "")
    form["sec1"] = request.form.get("sec1", "")
    form["sec2"] = request.form.get("sec2", "")
    form["s0filter"] = request.form.get("s0filter", "")

    for k in ["colormapn", "ecolormapn"]:
        form[k] = request.form.get(k, "")
    colorMapN = getInt(form["colormapn"], default=0)
    eColorMapN = getInt(form["ecolormapn"], default=0)

    colorMap = {}

    for i in range(1, colorMapN + 1):
        colorKey = f"colormap_{i}"
        form[colorKey] = request.form.get(colorKey, "")
        color = form[colorKey]
        colorMap[i] = color

    form["colorMap"] = colorMap

    edgeHighlights = {}

    for i in range(1, eColorMapN + 1):
        for k in [f"ecolormap_{i}", f"edge_name_{i}", f"edge_from_{i}", f"edge_to_{i}"]:
            form[k] = request.form.get(k, "")
        color = form[f"ecolormap_{i}"]
        name = form[f"edge_name_{i}"]
        fRep = form[f"edge_from_{i}"]
        tRep = form[f"edge_to_{i}"]
        if name == "" or fRep == "" or tRep == "":
            continue
        f = (
            0
            if fRep == ""
            else None
            if fRep == "any"
            else int(fRep)
            if fRep.isdecimal()
            else 0
        )
        t = (
            0
            if tRep == ""
            else None
            if tRep == "any"
            else int(tRep)
            if tRep.isdecimal()
            else 0
        )
        edgeHighlights.setdefault(name, {})[(f, t)] = color

    for i in range(1, 4):
        for k in [
            f"ecolormap_new_{i}",
            f"edge_name_new_{i}",
            f"edge_from_new_{i}",
            f"edge_to_new_{i}",
        ]:
            form[k] = request.form.get(k, "")
        color = form[f"ecolormap_new_{i}"]
        name = form[f"edge_name_new_{i}"]
        fRep = form[f"edge_from_new_{i}"]
        tRep = form[f"edge_to_new_{i}"]
        if name != "" and fRep != "" and tRep != "":
            f = (
                0
                if fRep == ""
                else None
                if fRep == "any"
                else int(fRep)
                if fRep.isdecimal()
                else 0
            )
            t = (
                0
                if tRep == ""
                else None
                if tRep == "any"
                else int(tRep)
                if tRep.isdecimal()
                else 0
            )
            edgeHighlights.setdefault(name, {})[(f, t)] = color

    form["edgeHighlights"] = edgeHighlights

    for (k, v) in interfaceDefaults.items():
        if v is None:
            continue
        form[k] = request.form.get(k, None)
    return form


def getAbout(colophon, header, provenance, form):
    return f"""
{colophon}

{provenance}

Job: {form['jobName']}

# {form['title']}

## {form['author']}

{form['description']}

## Information requests:

### Sections

``` python
{form['sections']}
```

### Nodes

``` python
{form['tuples']}
```

### Search

``` python
{form['query']}
```
"""


def zipTables(csvs, tupleResultsX, queryResultsX, about, form):
    appName = form["appName"]
    jobName = form["jobName"]

    zipBuffer = BytesIO()
    with ZipFile(zipBuffer, "w", **ZIP_OPTIONS) as zipFile:

        zipFile.writestr("job.json", writeJson(form).encode("utf8"))
        zipFile.writestr("job.json", writeJson.dumps(
            {k: v for (k, v) in form.items() if k not in {"edgeHighlights", "colorMap"}}
        ).encode("utf8"))
        zipFile.writestr("about.md", about)
        if csvs is not None:
            for (csv, data) in csvs:
                contents = "".join(
                    ("\t".join(str(t) for t in tup) + "\n") for tup in data
                )
                zipFile.writestr(f"{csv}.tsv", contents.encode("utf8"))
            for (name, data) in (
                ("nodesx.tsv", tupleResultsX),
                ("resultsx.tsv", queryResultsX),
            ):
                if data is not None:
                    contents = "\ufeff" + "".join(
                        ("\t".join("" if t is None else str(t) for t in tup) + "\n")
                        for tup in data
                    )
                    zipFile.writestr(name, contents.encode("utf_16_le"))
    return (f"{appName}-{jobName}.zip", zipBuffer.getvalue())
