"""Main controller for Flask

This module contains the main controller that Flask invokes when serving
the annotation tool.
"""

from flask import render_template

from ...core.generic import AttrDict

from .settings import TOOLKEY
from .kernel import Annotate
from .servelib import initTemplate, findSetup, adaptValSelect
from .wrap import wrapCss, wrapQuery, wrapActive, wrapReport, wrapMessages, wrapAnnoSets


class Serve:
    def __init__(self, web):
        self.web = web
        self.debug = web.debug
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
        app = self.app
        debug = self.debug

        templateData = initTemplate(app)
        self.templateData = templateData

        annoSet = templateData.annoset

        annotate = Annotate(app, annoSet=annoSet, data=data, debug=debug, browse=True)
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
        sortKey = templateData.sortKey
        sortDir = templateData.sortDir
        activeEntity = templateData.activeentity
        tokenStart = templateData.tokenstart
        tokenEnd = templateData.tokenend
        excludedTokens = templateData.excludedtokens

        nFind = self.nFind
        nEnt = self.nEnt
        nVisible = self.nVisible
        buckets = self.buckets

        wrapQuery(annotate, templateData, nFind, nEnt, nVisible)
        templateData.entitytable = annotate.entityTable(activeEntity, sortKey, sortDir)
        templateData.entityoverview = annotate.wrapEntityOverview()
        templateData.entityheaders = annotate.wrapEntityHeaders(sortKey, sortDir)
        templateData.buckets = annotate.bucketTable(
            buckets, activeEntity, tokenStart, tokenEnd, excludedTokens
        )

        return render_template(f"{TOOLKEY}/index.html", **templateData)

    def wrapLean(self):
        annotate = self.annotate
        templateData = self.templateData
        activeEntity = templateData.activeentity
        tokenStart = templateData.tokenstart
        tokenEnd = templateData.tokenend
        excludedTokens = templateData.excludedtokens
        buckets = self.buckets

        return annotate.bucketTable(
            buckets, activeEntity, tokenStart, tokenEnd, excludedTokens
        )

    def getBuckets(self, noFind=False, node=None):
        annotate = self.annotate
        templateData = self.templateData

        bFindRe = None if noFind else templateData.bfindre
        activeEntity = templateData.activeentity
        tokenStart = templateData.tokenstart
        tokenEnd = templateData.tokenend
        valSelect = templateData.valselect
        freeState = templateData.freestate

        (self.buckets, self.nFind, self.nVisible, self.nEnt) = annotate.filterBuckets(
            bFindRe=bFindRe,
            activeEntity=activeEntity,
            tokenStart=tokenStart,
            tokenEnd=tokenEnd,
            valSelect=valSelect,
            freeState=freeState,
            noFind=noFind,
            node=node,
        )

    def setHandling(self, templateData):
        annotate = self.annotate
        annoDir = annotate.annoDir

        chosenAnnoSet = templateData.annoset
        dupAnnoSet = templateData.duannoset
        renamedAnnoSet = templateData.rannoset
        deleteAnnoSet = templateData.dannoset

        messages = []

        if deleteAnnoSet:
            messages.extend(annotate.setDel(deleteAnnoSet))
            templateData.dannoset = ""
            templateData.annoset = ""

        if dupAnnoSet:
            messages.extend(annotate.setDup(dupAnnoSet))
            templateData.annoset = dupAnnoSet
            templateData.duannoset = ""

        if renamedAnnoSet and chosenAnnoSet:
            messages.extend(annotate.setMove(renamedAnnoSet))
            templateData.annoset = renamedAnnoSet
            templateData.rannoset = ""

        chosenAnnoSet = templateData.annoset
        annotate.setSet(chosenAnnoSet)
        setNames = annotate.setNames

        templateData.annosets = wrapAnnoSets(annoDir, chosenAnnoSet, setNames)
        templateData.messages = wrapMessages(messages)

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
        bFindRe = templateData.bfindre
        scope = templateData.scope

        hasEnt = activeEntity is not None
        hasOcc = tokenStart is not None and tokenEnd is not None

        if (
            submitter in {"delgo", "addgo"}
            and (delData or addData)
            and (hasEnt or hasOcc)
        ):
            if bFindRe and scope == "a":
                self.getBuckets(noFind=True)

            if submitter == "delgo" and delData:
                report = annotate.delEntity(
                    delData.deletions, self.buckets, excludedTokens
                )
                annotate.loadData()
                wrapReport(templateData, report, "del")
                if hasEnt:
                    templateData.activeentity = None
                    templateData.evals = None
            if submitter == "addgo" and addData:
                report = annotate.addEntity(
                    addData.additions, self.buckets, excludedTokens
                )
                annotate.loadData()
                wrapReport(templateData, report, "add")

            adaptValSelect(templateData)

            self.getBuckets()


def serveNer(web):
    serve = Serve(web)
    serve.setupFull()
    serve.actionsAnnotate()
    return serve.wrapAnnotate()


def serveNerContext(web, node):
    serve = Serve(web)
    serve.setupLean()
    serve.actionsLean(node)
    return serve.wrapLean()
