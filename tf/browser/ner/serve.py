"""Main controller for Flask

This module contains the main controller that Flask invokes when serving
the annotation tool.
"""

import re

from flask import render_template

from ...core.generic import AttrDict
from ...core.files import initTree, annotateDir, dirCopy, dirMove, dirRemove, dirExists

from .settings import FEATURES, NF
from .servelib import getFormData, annoSets
from .kernel import loadData
from .mutate import saveEntity, delEntity
from .tables import (
    composeE,
    composeS,
    filterS,
)
from .wrap import (
    wrapAnnoSets,
    wrapEntityHeaders,
    wrapEntityOverview,
    wrapQ,
    wrapMessages,
    wrapActive,
    wrapReport,
)


def serveNer(web):
    """Serves the NE annotation tool.

    Parameters
    ----------
    web: object
        The flask web app
    """

    web.console("START controller")

    kernelApi = web.kernelApi

    css = kernelApi.css()

    templateData = initTemplate(web)
    setHandling(web, templateData)
    loadData(web)
    sortSetup(templateData)
    findSetup(templateData)
    wrapActive(templateData)

    (sentences, nFind, nVisible, nEnt) = filterS(web, templateData)

    updateHandling(web, templateData, sentences)

    wrapQ(web, templateData, nFind, nEnt, nVisible)

    composeE(web, templateData)
    wrapEntityOverview(web)
    wrapEntityHeaders(templateData)

    composeS(web, sentences)

    return render_template("ner/index.html", css=css, **templateData)


def initTemplate(web):
    kernelApi = web.kernelApi
    app = kernelApi.app
    aContext = web.context
    appName = aContext.appName.replace("/", " / ")
    api = app.api
    F = api.F
    slotType = F.otype.slotType

    form = getFormData(web)
    resetForm = form["resetForm"]

    templateData = AttrDict()
    templateData.featurelist = ",".join(FEATURES)

    for (k, v) in form.items():
        if not resetForm or k not in templateData:
            templateData[k] = v

    templateData.appname = appName
    templateData.slottype = slotType
    templateData.resetform = ""

    return templateData


def setHandling(web, templateData):
    kernelApi = web.kernelApi
    app = kernelApi.app
    annoDir = annotateDir(app, "ner")
    web.annoDir = annoDir

    initTree(annoDir, fresh=False)
    sets = annoSets(annoDir)

    chosenAnnoSet = templateData.annoset
    dupAnnoSet = templateData.duannoset
    renamedAnnoSet = templateData.rannoset
    deleteAnnoSet = templateData.dannoset

    messages = []

    if deleteAnnoSet:
        annoPath = f"{annoDir}/{deleteAnnoSet}"
        dirRemove(annoPath)
        if dirExists(annoPath):
            messages.append(("error", f"""Could not remove {deleteAnnoSet}"""))
        else:
            chosenAnnoSet = ""
            sets -= {deleteAnnoSet}
        templateData.dannoset = ""

    if dupAnnoSet and chosenAnnoSet:
        if not dirCopy(
            f"{annoDir}/{chosenAnnoSet}", f"{annoDir}/{dupAnnoSet}", noclobber=True
        ):
            messages.append(
                ("error", f"""Could not copy {chosenAnnoSet} to {dupAnnoSet}""")
            )
        else:
            sets = sets | {dupAnnoSet}
            chosenAnnoSet = dupAnnoSet
        templateData.duannoset = ""

    if renamedAnnoSet and chosenAnnoSet:
        if not dirMove(f"{annoDir}/{chosenAnnoSet}", f"{annoDir}/{renamedAnnoSet}"):
            messages.append(
                ("error", f"""Could not rename {chosenAnnoSet} to {renamedAnnoSet}""")
            )
        else:
            sets = (sets | {renamedAnnoSet}) - {chosenAnnoSet}
            chosenAnnoSet = renamedAnnoSet
        templateData.rannoset = ""

    if chosenAnnoSet and chosenAnnoSet not in sets:
        initTree(f"{annoDir}/{chosenAnnoSet}", fresh=False)
        sets |= {chosenAnnoSet}

    templateData.annosets = wrapAnnoSets(annoDir, chosenAnnoSet, sets)
    templateData.messages = wrapMessages(messages)

    web.annoSet = chosenAnnoSet


def updateHandling(web, templateData, sentences):
    savDo = templateData.savdo
    delDo = templateData.deldo
    tokenStart = templateData.tokenstart
    tokenEnd = templateData.tokenend
    excludedTokens = templateData.excludedtokens
    sFindRe = templateData.sfindre
    scope = templateData.scope

    savDoAny = any(savDo)
    delDoAny = any(delDo)

    report = []

    if (savDoAny or delDoAny) and tokenStart and tokenEnd:
        saveSentences = (
            filterS(web, templateData, noFind=True)[0]
            if sFindRe and scope == "a"
            else sentences
        )

        if savDoAny:
            report.append(saveEntity(web, savDo, saveSentences, excludedTokens))
        if delDoAny:
            report.append(delEntity(web, delDo, saveSentences, excludedTokens))

        (sentences, nFind, nVisible, nEnt) = filterS(web, templateData)

    wrapReport(templateData, report)
    templateData.report = report


def sortSetup(templateData):
    sortKey = None
    sortDir = None

    for key in ("freqsort", *(f"sort_{i}" for i in range(NF))):
        currentState = templateData[key]
        if currentState:
            sortDir = "u" if currentState == "d" else "d"
            sortKey = key
            break

    templateData.sortkey = sortKey
    templateData.sortdir = sortDir


def findSetup(templateData):
    sFind = templateData.sfind
    sFind = (sFind or "").strip()
    sFindRe = None
    errorMsg = ""

    if sFind:
        try:
            sFindRe = re.compile(sFind)
        except Exception as e:
            errorMsg = str(e)

    templateData.sfind = sFind
    templateData.sfindre = sFindRe
    templateData.errormsg = errorMsg
