"""Main controller for Flask

This module contains the controllers that Flask invokes when serving
the annotation tool in the TF browser.
"""

from flask import render_template

from ...ner.settings import TOOLKEY

from .websettings import SC_ALL
from .request import Request
from .fragments import Fragments


class Serve(Request, Fragments):
    def __init__(self, web):
        """Object that implements the controller functions for the annotation tool.

        Parameters
        ----------
        web: object
            This represents the Flask website that is the TF browser.
            It has initialized a `tf.ner.ner.NER` object,
            and has stored it under attribute `ner`.
            See `tf.browser.ner.web.factory` and `tf.browser.web.factory`.

        """
        self.web = web

        ner = web.ner
        self.ner = ner

        Request.__init__(self)

        self.initVars()

    def setupFull(self):
        """Prepares to serve a complete page.

        *   Sets up the find widget;
        *   Encodes the active entity in hidden `input` elements;
        *   Collects and generates the specific CSS styles needed for this corpus.
        """
        ner = self.ner
        v = self.v

        self.findSetup()
        self.wrapActive()

        v.css = ner.css

    def setupLean(self):
        """Prepares to update a portion of the page.

        *   Encodes the active entity in hidden `input` elements.
        """
        self.wrapActive()

    def actionsFull(self):
        """Carries out requested actions before building the full page.

        *   annotation set management actions;
        *   fetch selected buckets from the whole corpus;
        *   modification actions in the selected set.
        """
        self.setHandling()
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
        actions.
        """
        ner = self.ner
        v = self.v
        sortKey = v.sortkey
        sortDir = v.sortdir
        subtleFilter = v.subtlefilter
        activeEntity = v.activeentity
        activeTrigger = v.activetrigger
        tokenStart = v.tokenstart
        tokenEnd = v.tokenend
        excludedTokens = v.excludedtokens

        buckets = self.buckets

        self.wrapQuery()
        v.entitytable = (
            ner.showEntities(
                activeEntity=activeEntity, sortKey=sortKey, sortDir=sortDir
            )
            if ner.sheetName is None
            else ner.showTriggers(
                activeEntity=activeEntity,
                activeTrigger=activeTrigger,
                sortKey=sortKey,
                sortDir=sortDir,
                subtleFilter=subtleFilter,
            )
        )
        v.entityoverview = ner.showEntityOverview()
        v.entityheaders = self.wrapEntityHeaders()
        v.buckets = ner.showContent(
            buckets,
            activeEntity=activeEntity,
            activeTrigger=activeTrigger,
            excludedTokens=excludedTokens,
            mayLimit=not (tokenStart and tokenEnd),
        )

        return render_template(f"{TOOLKEY}/index.html", **v)

    def wrapLean(self):
        """Builds a portion of the page.

        No need to build user controls, because they are already on the page.

        Returns
        -------
        The generated HTML for the portion of the page.
        """
        ner = self.ner
        v = self.v
        activeEntity = v.activeentity
        activeTrigger = v.activetrigger
        excludedTokens = v.excludedtokens
        buckets = self.buckets

        return ner.showContent(
            buckets,
            activeEntity=activeEntity,
            activeTrigger=activeTrigger,
            excludedTokens=excludedTokens,
            mayLimit=False,
        )

    def getBuckets(self, noFind=False, node=None):
        """Fetch a selection of buckets from the corpus.

        The selection is defined in the `v`.

        We further modify the selection by two additional parameters.

        The resulting list of buckets is obtained by
        `tf.ner.corpus.Corpus.filterContent`, and each member in the bucket
        list is a tuple as indicated in the `filterContent` function.
        The list is stored in the `Serve` object.
        Additionally, statistics about these buckets and how many entity values
        occur in it, are delivered in the `v`.

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
        ner = self.ner
        v = self.v

        bFindRe = None if noFind else v.bfindre
        anyEnt = v.anyent
        activeEntity = v.activeentity
        activeTrigger = v.activetrigger
        tokenStart = v.tokenstart
        tokenEnd = v.tokenend
        valSelect = v.valselect
        freeState = v.freestate

        setData = ner.getSetData()
        entityIdent = setData.entityIdent

        if activeEntity not in entityIdent:
            activeEntity = None
            v.activeentity = None
            v.activetrigger = None

        if activeTrigger is None:
            activeTrigger = None
            v.activetrigger = None

        qTokens = (
            ner.stringsFromTokens(tokenStart, tokenEnd)
            if tokenStart and tokenEnd
            else None
        )

        (
            self.buckets,
            v.nfind,
            v.nvisible,
            v.nent,
        ) = ner.filterContent(
            node=node,
            bFindRe=bFindRe,
            anyEnt=anyEnt,
            eVals=activeEntity,
            trigger=activeTrigger,
            qTokens=qTokens,
            valSelect=valSelect,
            freeState=freeState,
        )

    def setHandling(self):
        """Carries out the set-related actions before composing the page.

        These actions are:

        *   read the list of sets again
        *   switch to an other set than the current set
            and create it if it does not yet exist;
        *   duplicate the current set;
        *   rename the current set;
        *   delete a set.

        The results of the actions are wrapped in messages and stored in the
        `v`.
        """
        ner = self.ner
        ner.readSets()
        ner.readSheets()

        v = self.v
        chosenTask = v.task
        dupSet = v.duset
        renamedSet = v.rset
        deleteSet = v.dset

        messages = []

        if deleteSet:
            messages.extend(ner.setDel(deleteSet))
            v.dset = ""
            v.task = ""

        if dupSet:
            messages.extend(ner.setDup(dupSet))
            v.task = dupSet
            v.duset = ""

        if renamedSet and chosenTask:
            messages.extend(ner.setMove(renamedSet))
            v.task = renamedSet
            v.rset = ""

        v.messagesrc = messages

        chosenTask = v.task
        sheetCase = v.sheetcase
        ner.setTask(chosenTask, caseSensitive=sheetCase)
        ner.loadSetData()

        self.wrapSets()
        self.wrapMessages()
        self.wrapCaption()
        self.wrapLogs()

    def updateHandling(self):
        """Carries out modification actions in the current annotation set.

        Modification actions are:

        *   deletion of an entity;
        *   addition of an entity.

        The results of the actions are wrapped in a report and stored in the
        `v`.
        """
        ner = self.ner
        v = self.v

        delData = v.deldata
        addData = v.adddata
        activeEntity = v.activeentity
        tokenStart = v.tokenstart
        tokenEnd = v.tokenend
        submitter = v.submitter
        excludedTokens = v.excludedtokens
        bFindRe = v.bfindre
        scope = v.scope

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
                report = ner.delEntityRich(
                    delData.deletions, self.buckets, excludedTokens=excludedTokens
                )
                ner.loadSetData()
                self.wrapReport(report, "del")
                if hasEnt:
                    setData = ner.getSetData()
                    entityIdent = setData.entityIdent

                    stillExists = activeEntity in entityIdent
                    if not stillExists:
                        v.activeentity = None
                        v.activetrigger = None

            if submitter == "addgo" and addData:
                report = ner.addEntityRich(
                    addData.additions, self.buckets, excludedTokens=excludedTokens
                )
                ner.loadSetData()
                self.wrapReport(report, "add")

            self.adaptValSelect()

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
