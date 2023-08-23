"""Main controller for Flask

This module contains the main controller that Flask invokes when serving
the annotation tool.
"""

from flask import render_template

from ...core.helpers import console
from ...core.files import initTree, annotateDir, dirMove, dirRemove, dirExists

from .servelib import getFormData, annoSets
from .kernel import entities, entityKinds, sentences
from .wrap import wrapAnnoSets, wrapEntityHeaders, wrapEntityKinds, wrapMessages


def serveNer(web):
    """Serves the NE annotation tool.

    Parameters
    ----------
    web: object
        The flask web app
    """

    aContext = web.context
    appName = aContext.appName.replace("/", " / ")
    kernelApi = web.kernelApi
    app = kernelApi.app

    annoDir = annotateDir(app, "ner")
    initTree(annoDir, fresh=False)
    sets = annoSets(annoDir)

    form = getFormData()
    resetForm = form["resetForm"]

    css = kernelApi.css()

    templateData = {}
    messages = []

    for (k, v) in form.items():
        if not resetForm or k not in templateData:
            templateData[k] = v

    chosenAnnoSet = templateData["annoset"]
    renamedAnnoSet = templateData["rannoset"]
    deleteAnnoSet = templateData["dannoset"]
    console(f"{deleteAnnoSet=}")

    if deleteAnnoSet:
        annoPath = f"{annoDir}/{deleteAnnoSet}"
        dirRemove(annoPath)
        if dirExists(annoPath):
            messages.append(
                ("error", f"""Could not remove {deleteAnnoSet}""")
            )
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

    sortKey = None
    sortDir = None

    for key in ("freqsort", "kindsort", "etxtsort"):
        currentState = templateData[key]
        if currentState:
            sortDir = "u" if currentState == "d" else "d"
            sortKey = key
            break

    templateData["appName"] = appName
    templateData["resetForm"] = ""
    templateData["entities"] = entities(app, sortKey, sortDir)
    templateData["entitykinds"] = wrapEntityKinds(entityKinds(app))
    templateData["entityheaders"] = wrapEntityHeaders(sortKey, sortDir)
    templateData["sentences"] = sentences(app)
    templateData["messages"] = wrapMessages(messages)

    return render_template(
        "ner.html",
        css=css,
        **templateData,
    )
