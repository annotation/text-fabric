"""Main controller for Flask

This module contains the main controller that Flask invokes when serving
the annotation tool.
"""

from flask import render_template

from .servelib import initTemplate, findSetup, adaptValSelect
from .mutate import delEntity, addEntity, setHandling
from .tables import (
    composeE,
    composeS,
    filterS,
)
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
        web.console("START controller")

        kernelApi = web.kernelApi

        self.web = web

        templateData = initTemplate(web)
        findSetup(web, templateData)
        wrapActive(web, templateData)

        self.templateData = templateData

        wrapCss(web, templateData, kernelApi.css())

    def actions(self):
        web = self.web
        templateData = self.templateData

        setHandling(web, templateData)

        self.getSentences()
        self.updateHandling()

    def getSentences(self, noFind=False):
        web = self.web
        templateData = self.templateData

        (self.sentences, self.nFind, self.nVisible, self.nEnt) = filterS(
            web, templateData, noFind=noFind
        )

    def updateHandling(self):
        web = self.web
        templateData = self.templateData

        delData = templateData.deldata
        addData = templateData.adddata
        tokenStart = templateData.tokenstart
        tokenEnd = templateData.tokenend
        submitter = templateData.submitter
        excludedTokens = templateData.excludedtokens
        sFindRe = templateData.sfindre
        scope = templateData.scope

        if (
            submitter in {"delgo", "addgo"}
            and (delData or addData)
            and tokenStart
            and tokenEnd
        ):
            if sFindRe and scope == "a":
                self.getSentences(noFind=True)

            if submitter == "delgo" and delData:
                report = delEntity(web, delData.deletions, self.sentences, excludedTokens)
                wrapReport(templateData, report, "del")
            if submitter == "addgo" and addData:
                report = addEntity(web, addData.additions, self.sentences, excludedTokens)
                wrapReport(templateData, report, "add")

            adaptValSelect(templateData)

            self.getSentences()

    def wrap(self):
        web = self.web
        templateData = self.templateData
        nFind = self.nFind
        nEnt = self.nEnt
        nVisible = self.nVisible
        sentences = self.sentences

        wrapQuery(web, templateData, nFind, nEnt, nVisible)
        composeE(web, templateData)
        wrapEntityOverview(web, templateData)
        wrapEntityHeaders(web, templateData)
        composeS(web, templateData, sentences)

        return render_template("ner/index.html", **templateData)


def serveNer(web):
    """Serves the NE annotation tool.

    Parameters
    ----------
    web: object
        The flask web app
    """

    serve = Serve(web)
    serve.actions()
    return serve.wrap()
