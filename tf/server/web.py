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


class Setup(object):
    def __init__(self, portKernel):
        TF = makeTfConnection(HOST, portKernel, TIMEOUT)
        kernelApi = TF.connect()
        self.kernelApi = kernelApi

        context = pickle.loads(kernelApi.context())
        self.context = context

        self.wildQueries = set()


def factory(setup):
    app = Flask(__name__)
    aContext = setup.context
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
        return serveTable(setup, "sections", None)

    @app.route("/sections/<int:getx>", methods=["GET", "POST"])
    def serveSections(getx):
        return serveTable(setup, "sections", getx)

    @app.route("/tuples", methods=["GET", "POST"])
    def serveTuplesBare():
        return serveTable(setup, "tuples", None)

    @app.route("/tuples/<int:getx>", methods=["GET", "POST"])
    def serveTuples(getx):
        return serveTable(setup, "tuples", getx)

    @app.route("/query", methods=["GET", "POST"])
    def serveQueryBare():
        return serveQuery(setup, None)

    @app.route("/query/<int:getx>", methods=["GET", "POST"])
    def serveQueryX(getx):
        return serveQuery(setup, getx)

    @app.route("/passage", methods=["GET", "POST"])
    def servePassageBare():
        return servePassage(setup, None)

    @app.route("/passage/<getx>", methods=["GET", "POST"])
    def servePassageX(getx):
        return servePassage(setup, getx)

    @app.route("/export", methods=["GET", "POST"])
    def serveExportX():
        return serveExport(setup)

    @app.route("/download", methods=["GET", "POST"])
    def serveDownloadX():
        return serveDownload(setup)

    @app.route("/", methods=["GET", "POST"])
    @app.route("/<path:anything>", methods=["GET", "POST"])
    def serveAllX(anything=None):
        return serveAll(setup, anything)

    return app


def main(cargs=sys.argv):
    args = argWeb(cargs)
    if not args:
        return

    (dataSource, portKernel, portWeb) = args

    try:
        setup = Setup(portKernel)
        webapp = factory(setup)
        run_simple(
            HOST, portWeb, webapp, use_reloader=False, use_debugger=False,
        )
    except OSError as e:
        console(str(e))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
