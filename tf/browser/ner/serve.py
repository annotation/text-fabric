"""Main controller for Flask

This module contains the main controller that Flask invokes when serving
the annotation tool.
"""

import re

from flask import render_template

from ...core.files import initTree, annotateDir, dirMove, dirRemove, dirExists

from .servelib import getFormData, annoSets
from .kernel import loadData
from .tables import (
    composeE,
    composeS,
    composeQ,
    saveEntity,
    delEntity,
    filterS,
)
from .wrap import wrapAnnoSets, wrapEntityHeaders, wrapEntityKinds, wrapMessages


def serveNer(web):
    """Serves the NE annotation tool.

    Parameters
    ----------
    web: object
        The flask web app
    """

    web.console("START controller")
    aContext = web.context
    appName = aContext.appName.replace("/", " / ")

    kernelApi = web.kernelApi
    app = kernelApi.app
    api = app.api
    F = api.F
    slotType = F.otype.slotType

    annoDir = annotateDir(app, "ner")
    initTree(annoDir, fresh=False)
    sets = annoSets(annoDir)

    form = getFormData(web)
    resetForm = form["resetForm"]

    css = kernelApi.css()

    templateData = {}
    messages = []

    for (k, v) in form.items():
        if not resetForm or k not in templateData:
            templateData[k] = v

    eKindSelect = templateData["eKindSelect"]
    chosenAnnoSet = templateData["annoset"]
    renamedAnnoSet = templateData["rannoset"]
    deleteAnnoSet = templateData["dannoset"]

    if deleteAnnoSet:
        annoPath = f"{annoDir}/{deleteAnnoSet}"
        dirRemove(annoPath)
        if dirExists(annoPath):
            messages.append(("error", f"""Could not remove {deleteAnnoSet}"""))
        else:
            chosenAnnoSet = ""
            sets -= {deleteAnnoSet}

    if renamedAnnoSet and chosenAnnoSet:
        if not dirMove(f"{annoDir}/{chosenAnnoSet}", f"{annoDir}/{renamedAnnoSet}"):
            messages.append(
                ("error", f"""Could not rename {chosenAnnoSet} to {renamedAnnoSet}""")
            )
        else:
            sets = (sets | {renamedAnnoSet}) - {chosenAnnoSet}
            chosenAnnoSet = renamedAnnoSet

    if chosenAnnoSet and chosenAnnoSet not in sets:
        initTree(f"{annoDir}/{chosenAnnoSet}", fresh=False)
        sets += {chosenAnnoSet}

    templateData["annoSets"] = wrapAnnoSets(annoDir, chosenAnnoSet, sets)

    web.annoSet = chosenAnnoSet

    loadData(web)

    sortKey = None
    sortDir = None

    for key in ("freqsort", "kindsort", "etxtsort"):
        currentState = templateData[key]
        if currentState:
            sortDir = "u" if currentState == "d" else "d"
            sortKey = key
            break

    sFind = templateData["sfind"]
    sFind = (sFind or "").strip()
    sFindRe = None
    errorMsg = ""

    if sFind:
        try:
            sFindRe = re.compile(sFind)
        except Exception as e:
            errorMsg = str(e)

    activeEntity = templateData["activeentity"]
    activeKind = templateData["activekind"]

    templateData["appName"] = appName
    templateData["slotType"] = slotType
    templateData["resetForm"] = ""
    tSelectStart = templateData["tselectstart"]
    tSelectEnd = templateData["tselectend"]
    scope = templateData["scope"]

    savEKind = templateData["savEKind"]
    delEKind = templateData["delEKind"]

    (sentences, nFind, nVisible, nEnt) = filterS(
        web, sFindRe, tSelectStart, tSelectEnd, eKindSelect
    )

    report = None

    if (savEKind or delEKind) and tSelectStart and tSelectEnd:
        saveSentences = (
            filterS(web, None, tSelectStart, tSelectEnd, eKindSelect)[0]
            if sFindRe and scope == "a"
            else sentences
        )
        if savEKind or delEKind:
            report = []

            if savEKind:
                report.append(saveEntity(web, savEKind, saveSentences))
            if delEKind:
                report.append(delEntity(web, delEKind, saveSentences))
            (sentences, nFind, nVisible, nEnt) = filterS(
                web, sFindRe, tSelectStart, tSelectEnd, eKindSelect
            )

    templateData["q"] = composeQ(
        web,
        sFind,
        sFindRe,
        errorMsg,
        tSelectStart,
        tSelectEnd,
        eKindSelect,
        nFind,
        nEnt,
        nVisible,
        scope,
        report,
    )

    hasEntity = tSelectStart and tSelectEnd
    limited = not hasEntity

    templateData["entities"] = composeE(web, activeEntity, activeKind, sortKey, sortDir)
    templateData["entitykinds"] = wrapEntityKinds(web)
    templateData["entityheaders"] = wrapEntityHeaders(sortKey, sortDir)

    web.console("start compose sentences")
    templateData["sentences"] = composeS(web, sentences, limited)
    web.console("end compose sentences")
    templateData["messages"] = wrapMessages(messages)

    result = render_template(
        "ner/index.html",
        css=css,
        **templateData,
    )
    web.console("END controller")
    with open("/Users/me/Downloads/test.html", "w") as fh:
        fh.write(result)
    return result
