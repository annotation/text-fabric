import pickle
import markdown
from flask import jsonify, redirect, render_template, make_response

from ..core.helpers import console, wrapMessages
from ..advanced.helpers import RESULT
from .wrap import (
    pageLinks,
    passageLinks,
    wrapOptions,
    wrapSelect,
    wrapProvenance,
)
from .servelib import getAbout, getFormData, zipData

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
        (table, messages) = kernelApi.table(
            kind,
            task,
            form["features"],
            opened=openedSet,
            fmt=textFormat,
            baseTypes=form["baseTypes"],
            hiddenTypes=form["hiddenTypes"],
            getx=int(getx) if getx else None,
            **options,
        )

        if messages:
            messages = wrapMessages(messages)

    return method(table=table, messages=messages)


def serveQuery(web, getx, asDict=False):
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
        if task in wildQueries:
            messages = (
                f"Aborted because query is known to take longer than {TIMEOUT} second"
                + ("" if TIMEOUT == 1 else "s")
            )
        else:
            options = {
                k: form.get(k, v)
                for (k, v) in interfaceDefaults.items()
                if v is not None
            }
            try:
                (table, messages, features, start, total) = kernelApi.search(
                    task,
                    form["batch"],
                    position=form["position"],
                    opened=openedSet,
                    condenseType=condenseType,
                    fmt=textFormat,
                    baseTypes=form["baseTypes"],
                    hiddenTypes=form["hiddenTypes"],
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

        if table is not None:
            pages = pageLinks(total, form["position"])
        # messages have already been shaped by search
        # if messages:
        #  messages = wrapMessages(messages)
    else:
        table = f"no {resultKind}s"
        messages = ""

    return method(
        pages=pages, table=table, nResults=total, messages=messages, features=features,
    )


def servePassage(web, getx):
    kernelApi = web.kernelApi
    aContext = web.context
    interfaceDefaults = aContext.interfaceDefaults

    form = getFormData(interfaceDefaults)
    textFormat = form["textFormat"] or None

    passages = ""

    openedKey = "passageOpened"
    openedSet = set(form[openedKey].split(",")) if form[openedKey] else set()

    sec0 = form["sec0"]
    sec1 = form["sec1"]
    sec2 = form["sec2"]
    options = {
        k: form.get(k, v) for (k, v) in interfaceDefaults.items() if v is not None
    }
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
        getx=getx,
        **options,
    )
    passages = pickle.loads(passages)
    passages = passageLinks(passages, sec0Type, sec0, sec1, browseNavLevel)
    return jsonify(table=table, passages=passages)


def serveExport(web):
    aContext = web.context
    interfaceDefaults = aContext.interfaceDefaults
    appName = aContext.appName
    kernelApi = web.kernelApi

    sectionsData = serveTable(web, "sections", None, asDict=True)
    tuplesData = serveTable(web, "tuples", None, asDict=True)
    queryData = serveQuery(web, None, asDict=True)

    form = getFormData(interfaceDefaults)

    (header, appLogo, tfLogo) = kernelApi.header()
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

    return render_template(
        "export.html",
        appName=appName,
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
        colofon=f"{appLogo}{header}{tfLogo}",
        provenance=provenanceHtml,
        setNames=setNameHtml,
        **form,
    )


def serveDownload(web):
    aContext = web.context
    interfaceDefaults = aContext.interfaceDefaults
    form = getFormData(interfaceDefaults)
    kernelApi = web.kernelApi
    wildQueries = web.wildQueries

    task = form["query"]
    condensed = form["condensed"]
    condenseType = form["condenseType"] or None
    textFormat = form["textFormat"] or None
    csvs = None
    resultsX = None
    messages = ""
    if task in wildQueries:
        messages = (
            f"Aborted because query is known to take longer than {TIMEOUT} second"
            + ("" if TIMEOUT == 1 else "s")
        )
    else:
        try:
            (queryMessages, csvs, resultsX) = kernelApi.csvs(
                task,
                form["tuples"],
                form["sections"],
                condensed=condensed,
                condenseType=condenseType,
                fmt=textFormat,
            )
        except TimeoutError:
            messages = f"Aborted because query takes longer than {TIMEOUT} second" + (
                "" if TIMEOUT == 1 else "s"
            )
            console(f"{task}\n{messages}", error=True)
            wildQueries.add(task)
            return jsonify(messages=messages)

    if queryMessages:
        redirect("/")
        return jsonify(messages=queryMessages)

    (header, appLogo, tfLogo) = kernelApi.header()
    provenance = kernelApi.provenance()
    setNames = kernelApi.setNames()
    (provenanceHtml, provenanceMd) = wrapProvenance(form, provenance, setNames)

    csvs = pickle.loads(csvs)
    resultsX = pickle.loads(resultsX)
    about = getAbout(header, provenanceMd, form)
    (fileName, zipBuffer) = zipData(csvs, resultsX, about, form)

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

    kernelApi = web.kernelApi

    form = getFormData(interfaceDefaults)
    resetForm = form["resetForm"]

    pages = ""
    passages = ""

    (header, appLogo, tfLogo) = kernelApi.header()
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
        ("textFormat", "tradio", formatCss, False),
    ):
        value = aContext.get(option, None) if resetForm else form[option]
        options = wrapSelect(option, allowedValues, value, group, item, multiple)
        chooser[option] = options

    (options, optionsMoved, optionsHelp) = wrapOptions(aContext, form)

    templateData = dict(
        css=css,
        header=f"{appLogo}{header}{tfLogo}",
        setNames=setNameHtml,
        options=options,
        optionsHelp=optionsHelp,
        chooser=chooser,
        condensedOption=optionsMoved["condensed"],
        hideTypesOption=optionsMoved["hideTypes"],
        defaultCondenseType=defaultCondenseType,
        defaultTextFormat=defaultTextFormat,
        exampleSectionHtml=exampleSectionHtml,
        exampleSection=exampleSection,
        pages=pages,
        passages=passages,
    )
    for (k, v) in form.items():
        if not (resetForm and k in templateData):
            templateData[k] = v
    templateData["appName"] = appName
    templateData["resetForm"] = ""
    return render_template("index.html", **templateData,)
