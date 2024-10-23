"""
# TF kernel

This is a set of higher level methods by which the TF browser can obtain chunks
of TF data for display on the website.

## Kernel API

The API of the TF kernel is created by the function `makeTfKernel`.

It returns a class `TfKernel` with a number of methods that are useful
for a web server.
"""

from functools import reduce

from ..advanced.highlight import getPassageHighlights
from ..advanced.search import runSearch, runSearchCondensed
from ..advanced.helpers import getRowsX
from ..advanced.tables import compose, composeP, composeT
from .servelib import batchAround


# KERNEL CREATION


def makeTfKernel(app, appName):
    if not app.api:
        return False

    TF = app.api.TF
    reset = TF.reset
    cache = TF.cache

    reset()
    cache = {}

    class TfKernel:
        def __init__(self):
            self.app = app

        def provenance(self):
            """Fetches provenance metadata to be shown on exported data pages."""

            app = self.app
            aContext = app.context
            backend = app.backend
            org = aContext.org
            repo = aContext.repo
            commit = aContext.commit
            appProvenance = (
                (
                    ("backend", backend),
                    ("name", appName),
                    ("org", org),
                    ("repo", repo),
                    ("commit", commit),
                ),
            )
            return (appProvenance, app.provenance)

        def setNames(self):
            """Gets the names of the custom sets that the app has loaded.

            The app can load additional sets of data triggered by the
            `--sets=` command-line argument with which the app
            was started.

            A web server can use this information to write out provenance info.
            """

            app = self.app
            return (
                tuple(sorted(app.sets.keys()))
                if hasattr(app, "sets") and type(app.sets) is dict
                else ()
            )

        def css(self):
            """Delivers the CSS code to be inserted on the browser page."""

            app = self.app
            return f'<style type="text/css">{app.loadCss()}</style>'

        def passage(
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
            representations of the `sec2` (verse-like), which can be expanded to pretty
            displays when the user chooses to do so.

            Parameters
            ----------
            features: string | iterable
                The features that should be displayed in pretty displays when expanding
                a plain representation of a `sec2` into a pretty display.

            query: string
                The query whose results should be highlighted in the passage display.

            sec0: string | integer
                The level 0 section (book)-like label in which the passage occurs.

            sec1: string | integer, optional None
                The level 1 section (chapter)-like label to fetch

            sec2: string | integer, optional None
                The level 2 section (verse-like) label that should get focus.

            opened: set, optional, `set()`
                The set of items that are currently expanded into pretty display.

            getx: string | integer, optional None
                If given, only a single `sec2` (verse) will be fetched, but in pretty
                display.
                `getx` is the identifier (section label, verse number) of the item.

            options: dict
                Additional, optional display options, see `tf.advanced.options`.
            """

            app = self.app
            api = app.api
            F = api.F
            L = api.L
            T = api.T

            aContext = app.context
            browseNavLevel = aContext.browseNavLevel
            browseContentPretty = aContext.browseContentPretty
            display = app.display
            dContext = display.distill(options)
            colorMap = dContext.colorMap

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
                getPassageHighlights(app, contentNode, query, colorMap, cache)
                if items
                else set()
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

            return (passage, sec0Type, (sec0s, sec1s), browseNavLevel)

        def rawSearch(self, query):
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

        def table(
            self,
            kind,
            task,
            features,
            opened=set(),
            getx=None,
            **options,
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
                a plain representation of a `sec2` into a pretty display.

            opened: set, optional, `set()`
                The set of items that are currently expanded into pretty display.

            getx: string | integer, optional None
                If given, only a single `sec2` (verse) will be fetched, but in pretty
                display.
                `getx` is the identifier (section label, verse number) of the item.

            options: dict
                Additional, optional display options, see `tf.advanced.options`.
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

        def search(
            self,
            query,
            batch,
            position=1,
            opened=set(),
            getx=None,
            **options,
        ):
            """Executes a TF search template, retrieves formatted results.

            The very work horse of this API.

            Formatted results for additional nodes and sections are also retrieved.

            Parameters
            ----------
            query: string
                The query whose results should be highlighted in the passage display.
                Typically coming from the *search pad* in the browser.

            batch: integer
                The number of table rows to show on one page in the browser.

            position: integer, optional 1
                The position that is in focus in the browser.
                The navigation links take this position as the central point,
                and enable the user to navigate to neighbouring results,
                in ever bigger strides.

            opened: set, optional set()
                The set of items that are currently expanded into pretty display.
                Normally, only the information to provide a *plain*
                representation of a result is being fetched,
                but for the opened ones information is gathered for
                pretty displays.

            getx: string | integer, optional None
                If given, only a single `sec2` (verse) will be fetched, but in pretty
                display.
                `getx` is the identifier (section label, verse number) of the item.
            """

            app = self.app
            display = app.display
            dContext = display.distill(options)
            condensed = dContext.condensed
            condenseType = dContext.condenseType

            total = 0

            results = ()
            status = True
            messages = ("", "")
            if query:
                (results, status, messages, nodeFeatures, edgeFeatures) = (
                    runSearchCondensed(app, query, cache, condenseType)
                    if condensed and condenseType
                    else runSearch(app, query, cache)
                )

                status = status[0] and status[1]
                if not status:
                    results = ()
                total += len(results)

            (start, end) = batchAround(total, position, batch)

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
            nodeFeatures = set(reduce(set.union, (x[1] for x in nodeFeatures), set()))
            featureStr = " ".join(sorted(nodeFeatures | set(edgeFeatures)))
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
            return (table, status, " ".join(messages), featureStr, start, total)

        def csvs(self, query, tuples, sections, **options):
            """Gets query results etc. in plain CSV format.

            The query results, tuples, and sections are retrieved, as in
            `exposed_search`, but this function only needs some features per node.
            """

            app = self.app
            display = app.display
            dContext = display.distill(options)
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
            queryMessages = ("", "")
            features = ()

            if query:
                (
                    queryResults,
                    queryStatus,
                    queryMessages,
                    nodeFeatures,
                    edgeFeatures,
                ) = runSearch(app, query, cache)
                (
                    queryResultsC,
                    queryStatusC,
                    queryMessagesC,
                    nodeFeaturesC,
                    edgeFeaturesC,
                ) = (
                    runSearchCondensed(app, query, cache, condenseType)
                    if queryStatus[0] and queryStatus[1] and condensed and condenseType
                    else (None, (False, False), ("", ""), None, None)
                )

                queryStatus = queryStatus[0] and queryStatus[1]
                queryStatusC = queryStatusC[0] and queryStatusC[1]

                if not queryStatus:
                    queryResults = ()
                if not queryStatusC:
                    queryResultsC = ()

            csvData = (
                ("sections", sectionResults),
                ("nodes", tupleResults),
                ("results", queryResults),
            )
            if condensed and condenseType:
                csvData += ((f"resultsBy{condenseType}", queryResultsC),)

            tupleResultsX = getRowsX(
                app,
                tupleResults,
                features,
                condenseType,
                fmt=fmt,
            )
            queryResultsX = getRowsX(
                app,
                queryResults,
                nodeFeatures,
                condenseType,
                fmt=fmt,
            )
            return (
                queryStatus,
                " ".join(queryMessages[0]),
                csvData,
                tupleResultsX,
                queryResultsX,
            )

    return TfKernel()
