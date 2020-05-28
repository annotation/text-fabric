"""
.. include:: ../../docs/server/kernel.md
"""

import sys
import pickle
from functools import reduce

import rpyc
from rpyc.utils.server import ThreadedServer

from ..core.helpers import console
from ..applib.app import findApp
from ..applib.highlight import getPassageHighlights
from ..applib.search import runSearch, runSearchCondensed
from ..applib.helpers import getResultsX
from ..applib.tables import compose, composeP, composeT

from .command import argKernel

TF_DONE = "TF setup done."
TF_ERROR = "Could not set up TF"


# KERNEL CREATION


def makeTfKernel(app, appName, port):
    if not app.api:
        console(f"{TF_ERROR}")
        return False
    TF = app.api.TF
    reset = TF.reset
    cache = TF.cache

    reset()
    cache = {}
    console(f"{TF_DONE}\nKernel listening at port {port}")

    class TfKernel(rpyc.Service):
        def on_connect(self, conn):
            self.app = app
            pass

        def on_disconnect(self, conn):
            self.app = None
            pass

        def exposed_monitor(self):
            """A utility function that spits out some information from the kernel
            to the outside world.

            At this moment it is only used for debugging, but later it can be useful
            to monitor the kernel or manage it while it remains running.
            """

            app = self.app
            api = app.api
            S = api.S

            searchExe = getattr(S, "exe", None)
            if searchExe:
                searchExe = searchExe.outerTemplate

            _msgCache = cache(_asString=True)

            data = dict(searchExe=searchExe, _msgCache=_msgCache)
            return data

        def exposed_header(self):
            """Fetches all the stuff to create a header.

            This is shown after loading a data set.
            It contains links to data and documentation of the data source.
            """

            app = self.app
            return app.header()

        def exposed_provenance(self):
            """Fetches provenance metadata to be shown on exported data pages.
            """

            app = self.app
            aContext = app.context
            commit = aContext.commit
            appProvenance = ((("name", appName), ("commit", commit)),)
            return (appProvenance, app.provenance)

        def exposed_setNames(self):
            """Gets the names of the custom sets that the kernel has loaded.

            The kernel can load additional sets of data triggered by the
            `--sets=` command line argument with which the kernel
            was started.

            A web server kan use this informatiomn to write out provenance info.
            """

            app = self.app
            return (
                tuple(sorted(app.sets.keys()))
                if hasattr(app, "sets") and type(app.sets) is dict
                else ()
            )

        def exposed_css(self):
            """Delivers the CSS code to be inserted on the browser page.
            """

            app = self.app
            return f'<style type="text/css">{app.loadCss()}</style>'

        def exposed_context(self):
            """Fetches the TF app context settings for the corpus.
            """

            return pickle.dumps(app.context)

        def exposed_passage(
            self,
            features,
            query,
            sec0,
            sec1=None,
            sec2=None,
            opened=set(),
            getx=None,
            **options,
        ):
            """Gets passages, i.e. sections of level 1 (chapter-like).

            The material will be displayed as a sequence of plain
            representations of the sec2s (verse-like), which can be expanded to pretty
            displays when the user chooses to do so.

            Parameters
            ----------
            features: string | iterable
                The features that should be displayed in pretty displays when expanding
                a plain representation of a sec2 into a pretty display

            query: string
                The query whose results should be highlighted in the passage display.

            sec0: string | int
                The level 0 section (book)-like label in which the passage occurs

            sec1: string | int, optional `None`
                The level 1 section (chapter)-like label to fetch

            sec2: string | int, optional `None`
                The level 2 section (verse-like) label that should get focus

            opened: set, optional, `set()`
                The set of items that are currently expanded into pretty display

            getx: string | int, optional `None`
                If given, only a single sec2 (verse) will be fetched, but in pretty
                display.
                `getx` is the identifier (section label, verse number) of the item/

            options: dict
                Additional, optional display options, see `tf.applib.displaysettings`.
            """

            app = self.app
            api = app.api
            F = api.F
            L = api.L
            T = api.T

            aContext = app.context
            browseNavLevel = aContext.browseNavLevel
            browseContentPretty = aContext.browseContentPretty

            sectionFeatureTypes = T.sectionFeatureTypes
            sec0Type = T.sectionTypes[0]
            sec1Type = T.sectionTypes[1]
            sectionDepth = len(T.sectionTypes)
            browseNavLevel = min((sectionDepth, browseNavLevel))
            finalSecType = T.sectionTypes[browseNavLevel]
            finalSec = (sec0, sec1, sec2)[browseNavLevel]

            if sec0:
                if sectionFeatureTypes[0] == "int":
                    sec0 = int(sec0)
            if sec1 and browseNavLevel == 2:
                if sectionFeatureTypes[1] == "int":
                    sec1 = int(sec1)

            sec0Node = T.nodeFromSection((sec0,)) if sec0 else None
            sec1Node = T.nodeFromSection((sec0, sec1)) if sec0 and sec1 else None

            contentNode = (sec0Node, sec1Node)[browseNavLevel - 1]

            if getx is not None:
                if sectionFeatureTypes[browseNavLevel] == "int":
                    getx = int(getx)

            sec0s = tuple(T.sectionFromNode(s)[0] for s in F.otype.s(sec0Type))
            sec1s = ()
            if browseNavLevel == 2:
                sec1s = (
                    ()
                    if sec0Node is None
                    else tuple(
                        T.sectionFromNode(s)[1] for s in L.d(sec0Node, otype=sec1Type)
                    )
                )

            items = (
                contentNode
                if browseContentPretty
                else L.d(contentNode, otype=finalSecType)
                if contentNode
                else []
            )

            highlights = (
                getPassageHighlights(app, contentNode, query, cache) if items else set()
            )

            passage = ""

            if items:
                passage = composeP(
                    app,
                    browseNavLevel,
                    finalSecType,
                    features,
                    items,
                    opened,
                    finalSec,
                    getx=getx,
                    highlights=highlights,
                    **options,
                )

            return (passage, sec0Type, pickle.dumps((sec0s, sec1s)), browseNavLevel)

        def exposed_rawSearch(self, query):
            app = self.app
            rawSearch = app.api.S.search

            (results, messages) = rawSearch(query, _msgCache=True)
            if messages:
                # console(messages, error=True)
                results = ()
            else:
                results = tuple(sorted(results))
                # console(f'{len(results)} results')
            return (results, messages)

        def exposed_table(
            self, kind, task, features, opened=set(), getx=None, **options,
        ):
            """Fetches material corresponding to a list of sections or tuples of nodes.

            Parameters
            ----------
            kind: string
                Either `sections` or `tuples`:
                whether to find section material or tuple material.

            task: iterable
                The list of things (sections or tuples) to retrieve the material for;
                Typically coming from the *section pad* / *node pad* in the browser.

            features: string | iterable
                The features that should be displayed in pretty displays when expanding
                a plain representation of a sec2 into a pretty display

            opened: set, optional, `set()`
                The set of items that are currently expanded into pretty display

            getx: string | int, optional `None`
                If given, only a single sec2 (verse) will be fetched, but in pretty
                display.
                `getx` is the identifier (section label, verse number) of the item/

            options: dict
                Additional, optional display options, see `tf.applib.displaysettings`.
            """

            app = self.app

            if kind == "sections":
                results = []
                messages = []
                if task:
                    lines = task.split("\n")
                    for (i, line) in enumerate(lines):
                        line = line.strip()
                        node = app.nodeFromSectionStr(line)
                        if type(node) is not int:
                            messages.append(str(node))
                        else:
                            results.append((i + 1, (node,)))
                results = tuple(results)
                messages = "\n".join(messages)
            elif kind == "tuples":
                results = ()
                messages = ""
                if task:
                    lines = task.split("\n")
                    try:
                        results = tuple(
                            (i + 1, tuple(int(n) for n in t.strip().split(",")))
                            for (i, t) in enumerate(lines)
                            if t.strip()
                        )
                    except Exception as e:
                        messages = f"{e}"

            allResults = ((None, kind),) + results
            table = composeT(app, features, allResults, opened, getx=getx, **options)
            return (table, messages)

        def exposed_search(
            self, query, batch, position=1, opened=set(), getx=None, **options,
        ):
            """Executes a TF search template, retrieves formatted results.

            The very work horse of this API.

            Formatted results for additional nodes and sections are also retrieved.

            Parameters
            ----------
            query: string
                The query whose results should be highlighted in the passage display.
                Typically coming from the *search pad* in the browser.

            batch: int
                The number of table rows to show on one page in the browser.

            position: integer, optional `1`
                The position that is in focus in the browser.
                The navigation links take this position as the central point,
                and enable the user to navigate to neighbouring results,
                in ever bigger strides.

            opened: set, optional, `set()`
                The set of items that are currently expanded into pretty display.
                Normally, only the information to provide a *plain*
                representation of a result is being fetched,
                but for the opened ones information is gathered for
                pretty displays.

            getx: string | int, optional `None`
                If given, only a single sec2 (verse) will be fetched, but in pretty
                display.
                `getx` is the identifier (section label, verse number) of the item/
            """

            app = self.app
            display = app.display
            dContext = display.get(options)
            condensed = dContext.condensed
            condenseType = dContext.condenseType

            total = 0

            results = ()
            messages = ""
            if query:
                (results, messages, features) = (
                    runSearchCondensed(app, query, cache, condenseType)
                    if condensed and condenseType
                    else runSearch(app, query, cache)
                )

                if messages:
                    results = ()
                total += len(results)

            (start, end) = _batchAround(total, position, batch)

            selectedResults = results[start - 1 : end]
            opened = set(opened)

            before = {n for n in opened if n > 0 and n < start}
            after = {n for n in opened if n > end and n <= len(results)}
            beforeResults = tuple((n, results[n - 1]) for n in sorted(before))
            afterResults = tuple((n, results[n - 1]) for n in sorted(after))

            allResults = (
                ((None, "results"),)
                + beforeResults
                + tuple((i + start, r) for (i, r) in enumerate(selectedResults))
                + afterResults
            )
            features = set(reduce(set.union, (x[1] for x in features), set()))
            featureStr = " ".join(sorted(features))
            table = compose(
                app,
                allResults,
                featureStr,
                position,
                opened,
                start=start,
                getx=getx,
                **options,
            )
            return (table, messages, featureStr, start, total)

        def exposed_csvs(self, query, tuples, sections, **options):
            """Gets query results etc. in plain csv format.

            The query results, tuples, and sections are retrieved, as in
            `exposed_search`, but this function only needs some features per node.
            """

            app = self.app
            display = app.display
            dContext = display.get(options)
            fmt = dContext.fmt
            condensed = dContext.condensed
            condenseType = dContext.condenseType

            sectionResults = []
            if sections:
                sectionLines = sections.split("\n")
                for sectionLine in sectionLines:
                    sectionLine = sectionLine.strip()
                    node = app.nodeFromSectionStr(sectionLine)
                    if type(node) is int:
                        sectionResults.append((node,))
            sectionResults = tuple(sectionResults)

            tupleResults = ()
            if tuples:
                tupleLines = tuples.split("\n")
                try:
                    tupleResults = tuple(
                        tuple(int(n) for n in t.strip().split(","))
                        for t in tupleLines
                        if t.strip()
                    )
                except Exception:
                    pass

            queryResults = ()
            queryMessages = ""
            features = ()
            if query:
                (queryResults, queryMessages, features) = runSearch(app, query, cache)
                (queryResultsC, queryMessagesC, featuresC) = (
                    runSearchCondensed(app, query, cache, condenseType)
                    if not queryMessages and condensed and condenseType
                    else (None, None, None)
                )

                if queryMessages:
                    queryResults = ()
                if queryMessagesC:
                    queryResultsC = ()

            csvs = (
                ("sections", sectionResults),
                ("nodes", tupleResults),
                ("results", queryResults),
            )
            if condensed and condenseType:
                csvs += ((f"resultsBy{condenseType}", queryResultsC),)
            resultsX = getResultsX(app, queryResults, features, condenseType, fmt=fmt,)
            return (queryMessages, pickle.dumps(csvs), pickle.dumps(resultsX))

    return TfKernel()
    return ThreadedServer(
        TfKernel(),
        port=int(port),
        protocol_config={
            # 'allow_pickle': True,
            # 'allow_public_attrs': True,
        },
    )


# KERNEL CONNECTION


def makeTfConnection(host, port, timeout):
    class TfConnection(object):
        def connect(self):
            try:
                connection = rpyc.connect(
                    host, port, config=dict(sync_request_timeout=timeout)
                )
                self.connection = connection
            except ConnectionRefusedError as e:
                self.connection = None
                return str(e)
            return connection.root

    return TfConnection()


# TOP LEVEL


def main(cargs=sys.argv):
    args = argKernel(cargs)
    if not args:
        return

    (dataSource, portKernel) = args
    appName = dataSource["appName"]
    checkout = dataSource["checkout"]
    checkoutApp = dataSource["checkoutApp"]
    moduleRefs = dataSource["moduleRefs"]
    locations = dataSource["locations"]
    modules = dataSource["modules"]
    setFile = dataSource["setFile"]

    if checkout is None:
        checkout = ""

    console(f"Setting up TF kernel for {appName} {moduleRefs} {setFile}")
    app = findApp(
        appName,
        checkoutApp,
        checkout=checkout,
        mod=moduleRefs,
        locations=locations,
        modules=modules,
        setFile=setFile,
        _browse=True,
    )
    if app is None:
        return

    kernel = makeTfKernel(app, appName, portKernel)
    if kernel:
        server = ThreadedServer(
            kernel,
            port=int(portKernel),
            protocol_config={
                # 'allow_pickle': True,
                # 'allow_public_attrs': True,
            },
        )
        server.start()


# LOWER LEVEL


def _batchAround(nResults, position, batch):
    halfBatch = int((batch + 1) / 2)
    left = min(max(position - halfBatch, 1), nResults)
    right = max(min(position + halfBatch, nResults), 1)
    discrepancy = batch - (right - left + 1)
    if discrepancy != 0:
        right += discrepancy
    if right > nResults:
        right = nResults
    return (left, right)


if __name__ == "__main__":
    main()
