"""Main controller for Flask

This module contains the controllers that Flask invokes when serving
the annotation tool in the TF browser.

To see how this fits among all the modules of this package, see
`tf.browser.ner.annotate` .
"""

from flask import render_template

from ...core.generic import AttrDict

from .settings import TOOLKEY, SC_ALL
from .helpers import makeCss
from .annotate import Annotate
from .servelib import initTemplate, findSetup, adaptValSelect
from .fragments import (
    wrapEntityHeaders,
    wrapQuery,
    wrapActive,
    wrapReport,
    wrapMessages,
    wrapAnnoSets,
)


class Serve:
    def __init__(self, web):
        """Object that implements the controller functions for the annotatation tool.

        Parameters
        ----------
        web: object
            This represents the Flask website that is the TF browser.
            It has access to the TF-app that represents a loaded TF corpus.
            See `tf.browser.ner.web.factory` and `tf.browser.web.factory`.

            It picks up a handle to the loaded TF corpus, stores it in the `Serve`
            object, and uses it to fetch the CSS code for this tool, which is
            also stored in the `Serve` object.

            Finally, it creates a pointer to the annotation data in memory, as stored
            in the `web` object, if there is already such data from a previous request.
            If not, it initializes an empty dict in the `web` object, with the purpose
            of storing incoming annotation data there.

            This way, the annotation data is preserved between requests.
        """
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
        """Initialize the Annotate object.

        Before doing anything else, we create a
        `tf.browser.ner.annotate.Annotate` object and store it for use
        by the actual controllers.

        Based on the information in the request, we switch to a particular annotation
        set and load its data.

        This method will be invoked via two routes:

        *   `Serve.setupFull()`: for the main page, after a normal request;
        *   `Serve.setupLean()`: in response to an Ajax call when context to a
            specific line in the corpus is needed.

        !!! note "`templateData`"
            We use the dict `templateData` as the collector of

            *   the request information;
            *   selections of corpus material;
            *   HTML fragments under construction;
            *   template variables.
        """
        data = self.data
        app = self.app

        annotate = Annotate(app, data=data, browse=True)

        initTemplate(annotate, app)
        templateData = annotate.templateData

        annoSet = templateData.annoset

        annotate.setSet(annoSet)
        self.annotate = annotate
        annotate.loadData()

    def setupFull(self):
        """Prepares to serve a complete page.

        *   Creates an `tf.browser.ner.annotate.Annotate` object;
        *   Sets up the find widget;
        *   Encodes the active entity in hidden `input` elements;
        *   Collects and generates the specific CSS styles needed for this corpus.
        """
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
        """Prepares to update a portion of the page.

        *   Creates an `tf.browser.ner.annotate.Annotate` object;
        *   Encodes the active entity in hidden `input` elements.
        """
        self.setupAnnotate()
        templateData = self.templateData

        wrapActive(templateData)

    def actionsFull(self):
        """Carries out requested actions before building the full page.

        *   annotation set management actions;
        *   fetch selected buckets from the whole corpus;
        *   modification actions in the selected set.
        """
        templateData = self.templateData

        self.setHandling(templateData)

        self.getBuckets()
        self.updateHandling()

    def actionsLean(self, node):
        """Carries out requested actions before building a portion of the page.

        *   fetch all buckets from a section of the corpus.
        """
        self.getBuckets(node=node)

    def wrapFull(self):
        """Builds the full page.

        This includes the controls by which the user makes selections and triggers
        axctions.
        """
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
        """Builds a portion of the page.

        No need to build user controls, because they are already on the page.

        Returns
        -------
        The generated HTML for the portion of the page.
        """
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
        """Fetch a selection of buckets from the corpus.

        The selection is defined in the `templateData`.

        We further modify the selection by two additional parameters.

        The resulting list of buckets is obtained by
        `tf.browser.ner.annotate.Annotate.filterContent`, and each member in the bucket
        list is a tuple as indicated in the `filterContent` function.
        The list is stored in the `Serve` object.
        Additionally, statistics about these buckets and how many entity values
        occur in het, are delivered in the `templateData`.

        Parameters
        ----------
        noFind: boolean, optional False
            If `noFind` we override the filtering by the filter widget on the interface.

            We use this when the user has indicated that he wants to apply an action
            on all buckets instead of the filtered ones.

        node: integer, optional None
            If passed, it is a TF node, probably for a top-level section.
            The effect is that it restricts the result to those buttons that fall
            under that TF node.

            We use this when we retrieve the context for a given bucket.
        """
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
            self.getStrings(tokenStart, tokenEnd) if tokenStart and tokenEnd else None
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
        )

    def setHandling(self):
        """Carries out the set-related actions before composing the page.

        These actions are:

        *   switch to an other set than the current set
            and create it if it does not yet exist;
        *   duplicate the current set;
        *   rename the current set;
        *   delete a set.

        The results of the actions are wrapped in messages and stored in the
        `templateData`.
        """
        annotate = self.annotate
        annoDir = annotate.annoDir
        settings = annotate.settings
        entitySet = settings.entitySet

        templateData = self.templateData
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

        templateData.annosets = wrapAnnoSets(
            annoDir, chosenAnnoSet, setNames, entitySet
        )
        templateData.messages = wrapMessages(messages)

    def updateHandling(self):
        """Carries out modification actions in the current annotation set.

        Modification actions are:

        *   deletion of an entity;
        *   addition of an entity.

        The results of the actions are wrapped in a report and stored in the
        `templateData`.
        """
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
    """Main controller to render a full page.

    Parameters
    ----------
    web: object
        The TF browser object, a Flask web app.
    """
    serve = Serve(web)
    serve.setupFull()
    serve.actionsFull()
    return serve.wrapFull()


def serveNerContext(web, node):
    """Controller to render a portion of a page.

    More specifically: the context around a single bucket.

    Parameters
    ----------
    web: object
        The TF browser object, a Flask web app.
    node: integer
        The TF node that contain the bucket nodes that form the context.
    """
    serve = Serve(web)
    serve.setupLean()
    serve.actionsLean(node)
    return serve.wrapLean()
