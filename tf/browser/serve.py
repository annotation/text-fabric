"""
# Dress TF nodes up for serving on the web

When the TF kernel has retrieved data, it comes in the form of nodes.

But the kernel is the one that is able to dress those nodes up with
meaningful data.

That dressing up is happening in this module, it has the higher level
functions for composing tables and passages.
"""

import markdown
from textwrap import dedent

from flask import jsonify, redirect, render_template, make_response

from ..core.helpers import console, wrapMessages
from ..core.files import writeJson
from ..core.text import DEFAULT_FORMAT
from ..advanced.helpers import RESULT
from ..advanced.text import specialCharacters
from .wrap import (
    pageLinks,
    passageLinks,
    wrapColorMap,
    wrapEColorMap,
    wrapOptions,
    wrapSelect,
    wrapProvenance,
)
from .servelib import getAbout, getFormData, zipTables, BATCH


TIMEOUT = 180


def serveTable(web, kind, getx=None, asDict=False):
    kernelApi = web.kernelApi
    aContext = web.context
    interfaceDefaults = aContext.interfaceDefaults

    form = getFormData(interfaceDefaults)
    textFormat = form["textFormat"] or None
    task = form[kind].strip()
    openedKey = f"{kind}Opened"
    openedSet = (
        {int(n) for n in form[openedKey].split(",")} if form[openedKey] else set()
    )

    method = dict if asDict else jsonify

    messages = ""
    table = None
    if task:
        options = {
            k: form.get(k, v) for (k, v) in interfaceDefaults.items() if v is not None
        }
        options["colorMap"] = form.get("colorMap", {})
        options["edgeHighlights"] = form.get("edgeHighlights", {})

        (table, messages) = kernelApi.table(
            kind,
            task,
            form["features"],
            opened=openedSet,
            fmt=textFormat,
            baseTypes=form["baseTypes"],
            hiddenTypes=form["hiddenTypes"],
            edgeFeatures=form["edgeFeatures"],
            getx=int(getx) if getx else None,
            **options,
        )

        if messages:
            (status, messages) = wrapMessages(messages)

    return method(table=table, messages=messages)


def serveQuery(web, getx=None, asDict=False):
    kernelApi = web.kernelApi
    aContext = web.context
    interfaceDefaults = aContext.interfaceDefaults
    wildQueries = web.wildQueries

    kind = "query"
    form = getFormData(interfaceDefaults)
    task = form[kind]
    condenseType = form["condenseType"] or None
    resultKind = condenseType if form["condensed"] else RESULT
    textFormat = form["textFormat"] or None
    openedKey = f"{kind}Opened"
    openedSet = (
        {int(n) for n in form[openedKey].split(",")} if form[openedKey] else set()
    )

    pages = ""
    features = ""

    method = dict if asDict else jsonify
    total = 0

    if task:
        messages = ""
        table = None
        status = True
        if task in wildQueries:
            messages = (
                f"Aborted because query is known to take longer than {TIMEOUT} second"
                + ("" if TIMEOUT == 1 else "s")
            )
            status = False
        else:
            options = {
                k: form.get(k, v)
                for (k, v) in interfaceDefaults.items()
                if v is not None
            }
            options["colorMap"] = form.get("colorMap", {})
            options["edgeHighlights"] = form.get("edgeHighlights", {})

            try:
                (table, status, messages, features, start, total) = kernelApi.search(
                    task,
                    form["batch"],
                    position=form["position"],
                    opened=openedSet,
                    condenseType=condenseType,
                    fmt=textFormat,
                    baseTypes=form["baseTypes"],
                    hiddenTypes=form["hiddenTypes"],
                    edgeFeatures=form["edgeFeatures"],
                    getx=int(getx) if getx else None,
                    **options,
                )
            except TimeoutError:
                messages = (
                    f"Aborted because query takes longer than {TIMEOUT} second"
                    + ("" if TIMEOUT == 1 else "s")
                )
                console(f"{task}\n{messages}", error=True)
                wildQueries.add(task)
                total = 0
                status = False

        if status and table is not None:
            pages = pageLinks(total, form["position"])
    else:
        table = f"no {resultKind}s"
        messages = ""
        status = True

    return method(
        pages=pages,
        table=table,
        nResults=total,
        status=status,
        messages=messages.strip(),
        features=features,
    )


def servePassage(web, getx=None):
    kernelApi = web.kernelApi
    aContext = web.context
    interfaceDefaults = aContext.interfaceDefaults

    form = getFormData(interfaceDefaults)
    textFormat = form["textFormat"] or None

    openedKey = "passageOpened"
    openedSet = set(form[openedKey].split(",")) if form[openedKey] else set()

    sec0 = form["sec0"]
    sec1 = form["sec1"]
    sec2 = form["sec2"]
    options = {
        k: form.get(k, v) for (k, v) in interfaceDefaults.items() if v is not None
    }
    options["colorMap"] = form.get("colorMap", {})
    options["edgeHighlights"] = form.get("edgeHighlights", {})

    (table, sec0Type, passages, browseNavLevel) = kernelApi.passage(
        form["features"],
        form["query"],
        sec0,
        sec1=sec1,
        sec2=sec2,
        opened=openedSet,
        fmt=textFormat,
        baseTypes=form["baseTypes"],
        hiddenTypes=form["hiddenTypes"],
        edgeFeatures=form["edgeFeatures"],
        getx=getx,
        **options,
    )
    passages = passageLinks(passages, sec0Type, sec0, sec1, browseNavLevel)
    return jsonify(table=table, passages=passages)


def serveExport(web):
    aContext = web.context
    interfaceDefaults = aContext.interfaceDefaults
    appName = aContext.appName
    kernelApi = web.kernelApi
    app = kernelApi.app

    sectionsData = serveTable(web, "sections", asDict=True)
    tuplesData = serveTable(web, "tuples", asDict=True)
    queryData = serveQuery(web, asDict=True)

    form = getFormData(interfaceDefaults)

    (colophon, header, appLogo, tfLogo) = app.header()
    css = kernelApi.css()
    provenance = kernelApi.provenance()
    setNames = kernelApi.setNames()
    setNamesRep = ", ".join(setNames)
    setNameHtml = (
        f'<p class="setnames">Sets: <span class="setnames">{setNamesRep}</span></p>'
        if setNames
        else ""
    )
    (provenanceHtml, provenanceMd) = wrapProvenance(form, provenance, setNames)

    descriptionMd = markdown.markdown(
        form["description"],
        extensions=["markdown.extensions.tables", "markdown.extensions.fenced_code"],
    )

    sectionsMessages = sectionsData["messages"]
    sectionsTable = sectionsData["table"]
    tuplesMessages = tuplesData["messages"]
    tuplesTable = tuplesData["table"]
    queryMessages = queryData["messages"]
    queryTable = queryData["table"]

    # maybe this is a hack. Needed to prevent appName from specified twice

    form["appName"] = appName

    return render_template(
        "export.html",
        # appName=appName,
        css=css,
        descriptionMd=descriptionMd,
        sectionsTable=(
            sectionsMessages
            if sectionsMessages or sectionsTable is None
            else sectionsTable
        ),
        tuplesTable=(
            tuplesMessages if tuplesMessages or tuplesTable is None else tuplesTable
        ),
        queryTable=(
            queryMessages if queryMessages or queryTable is None else queryTable
        ),
        colophon=f"{appLogo}{colophon}{tfLogo}",
        provenance=provenanceHtml,
        setNames=setNameHtml,
        **form,
    )


def serveDownload(web, jobOnly):
    aContext = web.context
    interfaceDefaults = aContext.interfaceDefaults
    form = getFormData(interfaceDefaults)

    if jobOnly:
        appName = form["appName"]
        jobName = form["jobName"]
        fileName = f"{appName}-{jobName}.json"

        headers = {
            "Expires": "0",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Content-Type": "application/json",
            "Content-Disposition": f'attachment; filename="{fileName}"',
            "Content-Encoding": "identity",
        }

        buffer = writeJson(
            {k: v for (k, v) in form.items() if k not in {"edgeHighlights", "colorMap"}}
        ).encode("utf8")
        return make_response(buffer, headers)

    kernelApi = web.kernelApi
    app = kernelApi.app
    wildQueries = web.wildQueries

    task = form["query"]
    condensed = form["condensed"]
    condenseType = form["condenseType"] or None
    textFormat = form["textFormat"] or None
    csvs = None
    queryStatus = True
    tupleResultsX = None
    queryResultsX = None
    messages = ""

    if task in wildQueries:
        messages = (
            f"Aborted because query is known to take longer than {TIMEOUT} second"
            + ("" if TIMEOUT == 1 else "s")
        )
    else:
        try:
            (
                queryStatus,
                queryMessages,
                csvs,
                tupleResultsX,
                queryResultsX,
            ) = kernelApi.csvs(
                task,
                form["tuples"],
                form["sections"],
                condensed=condensed,
                condenseType=condenseType,
                fmt=textFormat,
            )
        except TimeoutError:
            queryStatus = False
            messages = f"Aborted because query takes longer than {TIMEOUT} second" + (
                "" if TIMEOUT == 1 else "s"
            )
            console(f"{task}\n{messages}", error=True)
            wildQueries.add(task)
            return jsonify(messages=messages)

    if not queryStatus:
        redirect("/")
        return jsonify(status=queryStatus, messages=queryMessages)

    (colophon, header, appLogo, tfLogo) = app.header()
    provenance = kernelApi.provenance()
    setNames = kernelApi.setNames()
    (provenanceHtml, provenanceMd) = wrapProvenance(form, provenance, setNames)

    about = getAbout(colophon, header, provenanceMd, form)
    (fileName, zipBuffer) = zipTables(csvs, tupleResultsX, queryResultsX, about, form)

    headers = {
        "Expires": "0",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Content-Type": "application/octet-stream",
        "Content-Disposition": f'attachment; filename="{fileName}"',
        "Content-Encoding": "identity",
    }
    return make_response(zipBuffer, headers)


def serveAll(web, anything):
    aContext = web.context
    interfaceDefaults = aContext.interfaceDefaults
    appName = aContext.appName
    defaultCondenseType = aContext.condenseType
    defaultTextFormat = aContext.textFormat
    exampleSection = aContext.exampleSection
    exampleSectionHtml = aContext.exampleSectionHtml
    allowedValues = aContext.allowedValues
    showMath = aContext.interfaceDefaults["showMath"]

    mathjax = (
        dedent(
            """
        <script>
        globalThis.MathJax = {
            tex: {
                inlineMath: [['$', '$']],
                displayMath: [['$$', '$$']],
            }
        };
        </script>
        <script
            src="/browser/static/mathjax/tex-chtml.js"
            id="MathJax-script"
            async
        ></script>
        """
        )
        if showMath
        else ""
    )

    kernelApi = web.kernelApi
    app = kernelApi.app

    form = getFormData(interfaceDefaults)
    resetForm = form["resetForm"]

    pages = ""
    passages = ""

    (colophon, header, appLogo, tfLogo) = app.header()
    css = kernelApi.css()
    provenance = kernelApi.provenance()
    setNames = kernelApi.setNames()
    setNamesRep = ", ".join(setNames)
    setNameHtml = (
        f'<p class="setnames">Sets: <span class="setnames">{setNamesRep}</span></p>'
        if setNames
        else ""
    )
    (provenanceHtml, provenanceMd) = wrapProvenance(form, provenance, setNames)

    chooser = {}
    typeCss = ("cline", "ctype")
    formatCss = ("tfline", "ttext")

    for (option, group, item, multiple) in (
        ("baseTypes", "bcheck", typeCss, True),
        ("condenseType", "cradio", typeCss, False),
        ("hiddenTypes", "hcheck", typeCss, True),
        ("edgeFeatures", "echeck", typeCss, True),
        ("textFormat", "tradio", formatCss, False),
    ):
        value = aContext.get(option, None) if resetForm else form[option]
        options = wrapSelect(option, allowedValues, value, group, item, multiple)
        chooser[option] = options

    (options, optionsMoved, optionsHelp) = wrapOptions(aContext, form)
    colorMapHtml = wrapColorMap(form)
    eColorMapHtml = wrapEColorMap(form)

    characters = specialCharacters(app, fmt=form.get("textFormat", DEFAULT_FORMAT), _browse=True)

    templateData = dict(
        css=css,
        mathjax=mathjax,
        characters=characters,
        colorMapHtml=colorMapHtml,
        eColorMapHtml=eColorMapHtml,
        colophon=f"{appLogo}{colophon}{tfLogo}",
        header=header,
        setNames=setNameHtml,
        options=options,
        optionsHelp=optionsHelp,
        chooser=chooser,
        condensedOption=optionsMoved["condensed"],
        forceEdgesOption=optionsMoved["forceEdges"],
        hideTypesOption=optionsMoved["hideTypes"],
        defaultCondenseType=defaultCondenseType,
        defaultTextFormat=defaultTextFormat,
        exampleSectionHtml=exampleSectionHtml,
        exampleSection=exampleSection,
        pages=pages,
        passages=passages,
        author="",
        title="",
        description="",
        messages="",
        sections="",
        tuples="",
        query="",
        position=1,
        batch=BATCH,
        passageOpened="",
        sectionsOpened="",
        tuplesOpened="",
        queryOpened="",
    )
    for (k, v) in form.items():
        if not resetForm or k not in templateData:
            templateData[k] = v
    templateData["appName"] = appName
    templateData["resetForm"] = ""
    return render_template(
        "index.html",
        **templateData,
    )
