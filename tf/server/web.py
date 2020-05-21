"""
.. include:: ../../docs/server/web.md
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
        return send_file(f"{MY_DIR}/static/{filepath}")

    @app.route("/data/static/<path:filepath>")
    def serveData(filepath):
        return send_file(f"{appPath}/static/{filepath}")

    @app.route("/local/<path:filepath>")
    def serveLocal(filepath):
        return send_file(f"{localDir}/{filepath}")

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
            HOST, int(portWeb), webapp, use_reloader=False, use_debugger=False,
        )
    except OSError as e:
        console(str(e))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
