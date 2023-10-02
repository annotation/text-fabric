"""Main controller for Flask

This module contains the main controller that Flask invokes when serving
the annotation tool.
"""

from flask import render_template

from ...generic import AttrDict
from ...core.files import initTree

from .settings import TOOLKEY
from .kernel import Annotate
from .servelib import initTemplate, findSetup, adaptValSelect
from .wrap import (
    wrapCss,
    wrapEntityHeaders,
    wrapEntityOverview,
    wrapQuery,
    wrapActive,
    wrapReport,
    wrapEntityTable,
    wrapBuckets,
    wrapMessages,
    wrapAnnoSets,
)


class Serve:
    def __init__(self, web):
        self.web = web
        kernelApi = web.kernelApi
        self.app = kernelApi.app
        self.css = kernelApi.css()

        if not hasattr(web, "toolData"):
            setattr(web, "toolData", AttrDict())
        toolData = web.toolData

        if TOOLKEY not in toolData:
            toolData[TOOLKEY] = AttrDict()

        self.data = toolData[TOOLKEY]

    def setupAnnotate(self):
        data = self.data
        kernelApi = self.kernelApi
        app = kernelApi.app

        templateData = initTemplate(app)
        self.templateData = templateData

        annoSet = templateData.annoset

        annotate = Annotate(app, data, annoSet)
        self.annotate = annotate
        annotate.loadData()

    def setupFull(self):
        css = self.css
        self.setupAnnotate()
        templateData = self.templateData

        findSetup(templateData)
        wrapActive(templateData)

        wrapCss(templateData, css)

    def setupLean(self):
        self.setupAnnotate()
        templateData = self.templateData

        wrapActive(templateData)

    def actionsAnnotate(self):
        templateData = self.templateData

        self.setHandling(templateData)

        self.getBuckets()
        self.updateHandling()

    def actionsLean(self, node):
        self.getBuckets(node=node)

    def wrapAnnotate(self):
        annotate = self.annotate
        templateData = self.templateData
        nFind = self.nFind
        nEnt = self.nEnt
        nVisible = self.nVisible
        buckets = self.buckets

        wrapQuery(annotate, templateData, nFind, nEnt, nVisible)
        wrapEntityTable(annotate, templateData)
        wrapEntityOverview(annotate, templateData)
        wrapEntityHeaders(templateData)
        wrapBuckets(annotate, templateData, buckets)

        return render_template(f"{TOOLKEY}/index.html", **templateData)

    def wrapLean(self):
        annotate = self.annotate
        templateData = self.templateData
        buckets = self.buckets

        return wrapBuckets(annotate, templateData, buckets, asHtml=True)

    def getBuckets(self, noFind=False, node=None):
        annotate = self.annotate
        templateData = self.templateData

        sFindRe = None if noFind else templateData.sfindre
        activeEntity = templateData.activeEntity
        tokenStart = templateData.tokenstart
        tokenEnd = templateData.tokenend
        valSelect = templateData.valselect
        freeState = templateData.freestate

        (self.buckets, self.nFind, self.nVisible, self.nEnt) = annotate.filterBuckets(
            sFindRe,
            activeEntity,
            tokenStart,
            tokenEnd,
            valSelect,
            freeState,
            noFind=noFind,
            node=node,
        )

    def updateHandling(self):
        annotate = self.annotate
        templateData = self.templateData

        delData = templateData.deldata
        addData = templateData.adddata
        activeEntity = templateData.activeentity
        tokenStart = templateData.tokenstart
        tokenEnd = templateData.tokenend
        submitter = templateData.submitter
        excludedTokens = templateData.excludedtokens
        sFindRe = templateData.sfindre
        scope = templateData.scope

        hasEnt = activeEntity is not None
        hasOcc = tokenStart is not None and tokenEnd is not None

        if (
            submitter in {"delgo", "addgo"}
            and (delData or addData)
            and (hasEnt or hasOcc)
        ):
            if sFindRe and scope == "a":
                self.getBuckets(noFind=True)

            if submitter == "delgo" and delData:
                report = annotate.delEntity(
                    delData.deletions, self.buckets, excludedTokens
                )
                annotate.loadData()
                wrapReport(templateData, report, "del")
                if hasEnt:
                    templateData.activeentity = None
                    templateData.eVals = None
            if submitter == "addgo" and addData:
                report = annotate.addEntity(
                    addData.additions, self.buckets, excludedTokens
                )
                annotate.loadData()
                wrapReport(templateData, report, "add")

            adaptValSelect(templateData)

            self.getBuckets()

    def setHandling(self, templateData):
        annoDir = self.annoDir

        initTree(annoDir, fresh=False)

        chosenAnnoSet = templateData.annoset
        dupAnnoSet = templateData.duannoset
        renamedAnnoSet = templateData.rannoset
        deleteAnnoSet = templateData.dannoset

        messages = []

        if deleteAnnoSet:
            messages.extend(self.setDel(deleteAnnoSet))
            templateData.dannoset = ""

        if dupAnnoSet:
            messages.extend(self.setDup(dupAnnoSet))
            templateData.duannoset = ""

        if renamedAnnoSet and chosenAnnoSet:
            messages.extend(self.setMove(renamedAnnoSet))
            templateData.rannoset = ""

        sets = self.sets

        if chosenAnnoSet and chosenAnnoSet not in sets:
            initTree(f"{annoDir}/{chosenAnnoSet}", fresh=False)
            sets.add(chosenAnnoSet)
            self.loadData()

        templateData.annosets = wrapAnnoSets(annoDir, chosenAnnoSet, sets)
        templateData.messages = wrapMessages(messages)


def serveNer(serve):
    serve.setupAnnotate()
    serve.actionsAnnotate()
    return serve.wrapAnnotate()


def serveNerContext(serve, node):
    serve.setupLean()
    serve.actionsLean(node)
    return serve.wrapLean()
