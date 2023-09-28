"""Main controller for Flask

This module contains the main controller that Flask invokes when serving
the annotation tool.
"""

from flask import render_template

from .settings import TOOLKEY
from .servelib import initTemplate, findSetup, adaptValSelect
from .mutate import delEntity, addEntity, setHandling, setSetup
from .tables import composeE, composeS, filterS
from .wrap import (
    wrapCss,
    wrapEntityHeaders,
    wrapEntityOverview,
    wrapQuery,
    wrapActive,
    wrapReport,
)


class Serve:
    def __init__(self, web):
        self.web = web
        web.console("START controller")

    def setupLean(self):
        web = self.web
        templateData = initTemplate(web)
        self.templateData = templateData

        wrapActive(web, templateData)

    def setupFull(self):
        web = self.web

        templateData = initTemplate(web)
        self.templateData = templateData

        findSetup(web, templateData)
        wrapActive(web, templateData)

        kernelApi = web.kernelApi
        wrapCss(web, templateData, kernelApi.css())

    def actionsLean(self, node):
        web = self.web
        templateData = self.templateData

        setSetup(web, templateData)
        self.getBuckets(node=node)

    def actionsFull(self):
        web = self.web
        templateData = self.templateData

        setHandling(web, templateData)

        self.getBuckets()
        self.updateHandling()

    def wrapLean(self):
        web = self.web
        templateData = self.templateData
        buckets = self.buckets

        return composeS(web, templateData, buckets, asHtml=True)

    def wrapFull(self):
        web = self.web
        templateData = self.templateData
        nFind = self.nFind
        nEnt = self.nEnt
        nVisible = self.nVisible
        buckets = self.buckets

        wrapQuery(web, templateData, nFind, nEnt, nVisible)
        composeE(web, templateData)
        wrapEntityOverview(web, templateData)
        wrapEntityHeaders(web, templateData)
        composeS(web, templateData, buckets)

        return render_template(f"{TOOLKEY}/index.html", **templateData)

    def getBuckets(self, noFind=False, node=None):
        web = self.web
        templateData = self.templateData

        (self.buckets, self.nFind, self.nVisible, self.nEnt) = filterS(
            web, templateData, noFind=noFind, node=node
        )

    def updateHandling(self):
        web = self.web
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
                report = delEntity(web, delData.deletions, self.buckets, excludedTokens)
                wrapReport(templateData, report, "del")
                if hasEnt:
                    templateData.activeentity = None
                    templateData.eVals = None
            if submitter == "addgo" and addData:
                report = addEntity(web, addData.additions, self.buckets, excludedTokens)
                wrapReport(templateData, report, "add")

            adaptValSelect(templateData)

            self.getBuckets()


def serveNer(web):
    """Serves the NE annotation tool.

    Parameters
    ----------
    web: object
        The flask web app
    """

    serve = Serve(web)
    serve.setupFull()
    serve.actionsFull()
    return serve.wrapFull()


def serveNerContext(web, node):
    serve = Serve(web)
    serve.setupLean()
    serve.actionsLean(node)
    return serve.wrapLean()
