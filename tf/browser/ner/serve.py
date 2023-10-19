"""Main controller for Flask

This module contains the main controller that Flask invokes when serving
the annotation tool.
"""

from flask import render_template

from ...core.generic import AttrDict

from .settings import TOOLKEY, SC_ALL
from .helpers import makeCss
from .annotate import Annotate
from .servelib import initTemplate, findSetup, adaptValSelect
from .browserparts import (
    wrapEntityHeaders,
    wrapQuery,
    wrapActive,
    wrapReport,
    wrapMessages,
    wrapAnnoSets,
)


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

        annotate = Annotate(app, data=data, debug=debug, browse=True)

        templateData = initTemplate(annotate, app)
        self.templateData = templateData

        annoSet = templateData.annoset

        annotate.setSet(annoSet)
        self.annotate = annotate
        annotate.loadData()

    def setupFull(self):
        css = self.css

        self.setupAnnotate()
        annotate = self.annotate
        settings = annotate.settings
        features = settings.features
        keywordFeatures = settings.keywordFeatures

        templateData = self.templateData

        findSetup(templateData)
        wrapActive(templateData)
        templateData.css = makeCss(features, keywordFeatures, generic=css)

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
        sortKey = templateData.sortkey
        sortDir = templateData.sortdir
        activeEntity = templateData.activeentity
        tokenStart = templateData.tokenstart
        tokenEnd = templateData.tokenend
        excludedTokens = templateData.excludedtokens

        buckets = self.buckets

        wrapQuery(annotate, templateData)
        templateData.entitytable = annotate.showEntities(
            activeEntity=activeEntity, sortKey=sortKey, sortDir=sortDir
        )
        templateData.entityoverview = annotate.showEntityOverview()
        templateData.entityheaders = wrapEntityHeaders(annotate, sortKey, sortDir)
        templateData.buckets = annotate.showContent(
            buckets,
            activeEntity=activeEntity,
            excludedTokens=excludedTokens,
            mayLimit=not (tokenStart and tokenEnd),
        )

        return render_template(f"{TOOLKEY}/index.html", **templateData)

    def wrapLean(self):
        annotate = self.annotate
        templateData = self.templateData
        activeEntity = templateData.activeentity
        excludedTokens = templateData.excludedtokens
        buckets = self.buckets

        return annotate.showContent(
            buckets,
            activeEntity=activeEntity,
            excludedTokens=excludedTokens,
            mayLimit=False,
        )

    def getBuckets(self, noFind=False, node=None):
        annotate = self.annotate
        templateData = self.templateData

        bFindRe = None if noFind else templateData.bfindre
        anyEnt = templateData.anyent
        activeEntity = templateData.activeentity
        tokenStart = templateData.tokenstart
        tokenEnd = templateData.tokenend
        valSelect = templateData.valselect
        freeState = templateData.freestate

        setData = annotate.getSetData()
        entityIdent = setData.entityIdent

        if activeEntity not in entityIdent:
            activeEntity = None
            templateData.activeentity = None

        qTokens = (
            annotate.getStrings(tokenStart, tokenEnd)
            if tokenStart and tokenEnd
            else None
        )

        (
            self.buckets,
            templateData.nfind,
            templateData.nvisible,
            templateData.nent,
        ) = annotate.filterContent(
            node=node,
            bFindRe=bFindRe,
            anyEnt=anyEnt,
            eVals=activeEntity,
            qTokens=qTokens,
            valSelect=valSelect,
            freeState=freeState,
            noFind=noFind,
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
            if bFindRe and scope == SC_ALL:
                self.getBuckets(noFind=True)

            if submitter == "delgo" and delData:
                report = annotate.delEntityRich(
                    delData.deletions, self.buckets, excludedTokens=excludedTokens
                )
                annotate.loadData()
                wrapReport(annotate, templateData, report, "del")
                if hasEnt:
                    setData = annotate.getSetData()
                    entityIdent = setData.entityIdent

                    stillExists = activeEntity in entityIdent
                    if not stillExists:
                        templateData.activeentity = None

            if submitter == "addgo" and addData:
                report = annotate.addEntityRich(
                    addData.additions, self.buckets, excludedTokens=excludedTokens
                )
                annotate.loadData()
                wrapReport(annotate, templateData, report, "add")

            adaptValSelect(annotate, templateData)

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
