"""
# Web interface

## About

TF contains a web interface
in which you can enter a search template and view the results.

This is realized by a web app based on
[Flask](http://flask.pocoo.org/docs/1.0/).

This web app connects to the `tf.server.kernel` and merges the retrieved data
into a set of
[templates](https://github.com/annotation/text-fabric/tree/master/tf/server/views).

## Start up

TF kernel, web server and browser page are started
up by means of a script called `text-fabric`, which will be installed in an executable
directory by the `pip` installer.

## Routes

There are 4 kinds of routes in the web app:

url pattern | effect
--- | ---
`/server/static/...` | serves a static file from the server-wide [static folder](https://github.com/annotation/text-fabric/tree/master/tf/server/static)
`/data/static/...` | serves a static file from the app specific static folder
`/local/static/...` | serves a static file from a local directory specified by the app
anything else | submits the form with user data and return the processed request

## Templates

There are two templates in
[views](https://github.com/annotation/text-fabric/tree/master/tf/server/views)
:

* *index*: the normal template for returning responses
  to user requests;
* *export*: the template used for exporting results; it
  has printer/PDF-friendly formatting: good page breaks.
  Pretty displays always occur on a page by their own.
  It has very few user interaction controls.
  When saved as PDF from the browser, it is a neat record
  of work done, with DOI links to the corpus and to Text-Fabric.

## CSS

We format the web pages with CSS, with extensive use of
[flexbox](https://css-tricks.com/snippets/css/a-guide-to-flexbox).

There are several sources of CSS formatting:

* the CSS loaded from the app dependent extraApi, used
  for pretty displays;
* [index.css](https://github.com/annotation/text-fabric/blob/master/tf/server/static/index.css):
  the formatting of the *index* web page with which the user interacts;
* [export.css](https://github.com/annotation/text-fabric/blob/master/tf/server/views/export.css)
  the formatting of the export page;
* [base.css](https://github.com/annotation/text-fabric/blob/master/tf/server/views/base.css)
  shared formatting between the index and export pages.

## Javascript

We use a
[modest amount of Javascript](https://github.com/annotation/text-fabric/blob/master/tf/server/static/tf.js)
on top of
[JQuery](https://api.jquery.com).

For collapsing and expanding elements we use the
[details](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details)
element. This is a convenient, Javascript-free way to manage
collapsing. Unfortunately it is not supported by the Microsoft
browsers, not even Edge.

!!! caution "On Windows?"
    Windows users should install Chrome of Firefox.
"""

import os
import sys
import pickle

from flask import Flask, send_file
from werkzeug.serving import run_simple

from ..parameters import HOST
from ..core.helpers import console
from ..server.kernel import makeTfConnection
from .command import argWeb
from .serve import (
    TIMEOUT,
    serveTable,
    serveQuery,
    servePassage,
    serveExport,
    serveDownload,
    serveAll,
)


MY_DIR = os.path.dirname(os.path.abspath(__file__))


class Web(object):
    def __init__(self, portKernel):
        TF = makeTfConnection(HOST, int(portKernel), TIMEOUT)
        kernelApi = TF.connect()
        if type(kernelApi) is str:
            console(f"Could not connect to {HOST}:{portKernel}")
            console(kernelApi)
        else:
            self.kernelApi = kernelApi

            context = pickle.loads(kernelApi.context())
            self.context = context

            self.wildQueries = set()


def factory(web):
    app = Flask(__name__)
    aContext = web.context
    appPath = aContext.appPath
    localDir = aContext.localDir

    @app.route("/server/static/<path:filepath>")
    def serveStatic(filepath):
        theFile = f"{MY_DIR}/static/{filepath}"
        return send_file(theFile) if os.path.exists(theFile) else ""

    @app.route("/data/static/<path:filepath>")
    def serveData(filepath):
        theFile = f"{appPath}/static/{filepath}"
        return send_file(theFile) if appPath and os.path.exists(theFile) else ""

    @app.route("/local/<path:filepath>")
    def serveLocal(filepath):
        theFile = f"{localDir}/{filepath}"
        return send_file(theFile) if os.path.exists(theFile) else ""

    @app.route("/sections", methods=["GET", "POST"])
    def serveSectionsBare():
        return serveTable(web, "sections", None)

    @app.route("/sections/<int:getx>", methods=["GET", "POST"])
    def serveSections(getx):
        return serveTable(web, "sections", getx)

    @app.route("/tuples", methods=["GET", "POST"])
    def serveTuplesBare():
        return serveTable(web, "tuples", None)

    @app.route("/tuples/<int:getx>", methods=["GET", "POST"])
    def serveTuples(getx):
        return serveTable(web, "tuples", getx)

    @app.route("/query", methods=["GET", "POST"])
    def serveQueryBare():
        return serveQuery(web, None)

    @app.route("/query/<int:getx>", methods=["GET", "POST"])
    def serveQueryX(getx):
        return serveQuery(web, getx)

    @app.route("/passage", methods=["GET", "POST"])
    def servePassageBare():
        return servePassage(web, None)

    @app.route("/passage/<getx>", methods=["GET", "POST"])
    def servePassageX(getx):
        return servePassage(web, getx)

    @app.route("/export", methods=["GET", "POST"])
    def serveExportX():
        return serveExport(web)

    @app.route("/download", methods=["GET", "POST"])
    def serveDownloadX():
        return serveDownload(web)

    @app.route("/", methods=["GET", "POST"])
    @app.route("/<path:anything>", methods=["GET", "POST"])
    def serveAllX(anything=None):
        return serveAll(web, anything)

    return app


def main(cargs=sys.argv):
    args = argWeb(cargs)
    if not args:
        return

    (dataSource, portKernel, portWeb) = args

    try:
        web = Web(portKernel)
        if not hasattr(web, "kernelApi"):
            return 1

        webapp = factory(web)
        run_simple(
            HOST,
            int(portWeb),
            webapp,
            use_reloader=False,
            use_debugger=False,
        )
    except OSError as e:
        console(str(e))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
