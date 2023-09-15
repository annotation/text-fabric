"""Main controller for Flask

This module contains the main controller that Flask invokes when serving
the annotation tool.
"""

from flask import render_template

from ...core.files import (
    initTree,
    annotateDir,
    dirCopy,
    dirMove,
    dirRemove,
    dirExists,
    dirMake,
    fileExists,
)

from .servelib import annoSets, initTemplate, findSetup
from .kernel import loadData
from .mutate import saveEntity, delEntity, saveEntitiesAs
from .tables import (
    composeE,
    composeS,
    filterS,
)
from .wrap import (
    wrapCss,
    wrapAnnoSets,
    wrapEntityHeaders,
    wrapEntityOverview,
    wrapQuery,
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

    templateData = initTemplate(web)
    wrapCss(web, templateData, kernelApi.css())
    setHandling(web, templateData)
    loadData(web)
    findSetup(web, templateData)
    wrapActive(web, templateData)

    (sentences, nFind, nVisible, nEnt) = filterS(web, templateData)

    updateHandling(web, templateData, sentences)

    wrapQuery(web, templateData, nFind, nEnt, nVisible)

    composeE(web, templateData)
    wrapEntityOverview(web, templateData)
    wrapEntityHeaders(web, templateData)

    composeS(web, templateData, sentences)

    return render_template("ner/index.html", **templateData)


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

    if dupAnnoSet:
        if dupAnnoSet in sets:
            messages.append(("error", f"""Set {dupAnnoSet} already exists"""))
        else:
            if chosenAnnoSet:
                if not dirCopy(
                    f"{annoDir}/{chosenAnnoSet}",
                    f"{annoDir}/{dupAnnoSet}",
                    noclobber=True,
                ):
                    messages.append(
                        ("error", f"""Could not copy {chosenAnnoSet} to {dupAnnoSet}""")
                    )
                else:
                    sets = sets | {dupAnnoSet}
                    chosenAnnoSet = dupAnnoSet
            else:
                annoPath = f"{annoDir}/{dupAnnoSet}"
                dataFile = f"{annoPath}/entities.tsv"

                if fileExists(dataFile):
                    messages.append(("error", f"""Set {dupAnnoSet} already exists"""))
                else:
                    dirMake(annoPath)
                    saveEntitiesAs(web, dataFile)
                    chosenAnnoSet = dupAnnoSet
            templateData.duannoset = ""

    if renamedAnnoSet and chosenAnnoSet:
        if renamedAnnoSet in sets:
            messages.append(("error", f"""Set {renamedAnnoSet} already exists"""))
        else:
            if not dirMove(f"{annoDir}/{chosenAnnoSet}", f"{annoDir}/{renamedAnnoSet}"):
                messages.append(
                    (
                        "error",
                        f"""Could not rename {chosenAnnoSet} to {renamedAnnoSet}""",
                    )
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
