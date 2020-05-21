"""
.. include:: ../../docs/server/servelib.md
"""

import json
from io import BytesIO
from zipfile import ZipFile

from flask import request

from ..parameters import ZIP_OPTIONS


DEFAULT_NAME = "default"

BATCH = 20


def getInt(x, default=1):
    if len(x) > 15:
        return default
    if not x.isdecimal():
        return default
    return int(x)


def getFormData(interfaceDefaults):
    """Get form data.

    The TF browser user interacts with the web app by clicking and typing,
    as a result of which a HTML form gets filled in.
    This form as regularly submitted to the web server with a request
    for a new incarnation of the page: a response.

    The values that come with a request, must be peeled out of the form,
    and stored as logical values.

    Most of the data has a known function to the web server,
    but there is also a list of webapp dependent options.
    """

    form = {}
    jobName = request.form.get("jobName", "").strip()
    if jobName:
        form["jobName"] = jobName
        form["loadJob"] = ""
    else:
        form["jobName"] = DEFAULT_NAME
        form["loadJob"] = "1"
    form["query"] = request.form.get("query", "").replace("\r", "")
    form["messages"] = request.form.get("messages", "") or ""
    form["features"] = request.form.get("features", "") or ""
    form["tuples"] = request.form.get("tuples", "").replace("\r", "")
    form["sections"] = request.form.get("sections", "").replace("\r", "")
    form["appName"] = request.form.get("appName", "")
    form["jobName"] = request.form.get("jobName", "").strip() or DEFAULT_NAME
    form["side"] = request.form.get("side", "")
    form["dstate"] = request.form.get("dstate", "")
    form["author"] = request.form.get("author", "").strip()
    form["title"] = request.form.get("title", "").strip()
    form["description"] = request.form.get("description", "").replace("\r", "")
    form["condensed"] = request.form.get("condensed", "")
    form["baseTps"] = tuple(request.form.getlist("baseTps"))
    form["condenseTp"] = request.form.get("condenseTp", "")
    form["textformat"] = request.form.get("textformat", "")
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
    for (k, v) in interfaceDefaults.items():
        if v is None:
            continue
        form[k] = request.form.get(k, None)
    return form


def getAbout(header, provenance, form):
    return f"""
{header}

{provenance}

Job: {form['jobName']}

# {form['title']}

## {form['author']}

{form['description']}

## Information requests:

### Sections

```
{form['sections']}
```

### Nodes

```
{form['tuples']}
```

### Search

```
{form['query']}
```
"""


def zipData(csvs, resultsX, about, form):
    appName = form["appName"]
    jobName = form["jobName"]

    zipBuffer = BytesIO()
    with ZipFile(zipBuffer, "w", **ZIP_OPTIONS) as zipFile:

        zipFile.writestr("job.json", json.dumps(form).encode("utf8"))
        zipFile.writestr("about.md", about)
        if csvs is not None:
            for (csv, data) in csvs:
                contents = "".join(
                    ("\t".join(str(t) for t in tup) + "\n") for tup in data
                )
                zipFile.writestr(f"{csv}.tsv", contents.encode("utf8"))
            for (name, data) in (("resultsx", resultsX),):
                if data is not None:
                    contents = "\ufeff" + "".join(
                        ("\t".join("" if t is None else str(t) for t in tup) + "\n")
                        for tup in data
                    )
                    zipFile.writestr(f"resultsx.tsv", contents.encode("utf_16_le"))
    return (f"{appName}-{jobName}.zip", zipBuffer.getvalue())
