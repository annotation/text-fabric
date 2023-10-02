from flask import Blueprint, send_file

from ...core.files import abspath, fileExists, dirNm
from .settings import TOOLKEY
from .serve import Serve, serveNer, serveNerContext


MY_DIR = dirNm(abspath(__file__))

METHODS = ["GET", "POST"]


def factory(web):
    app = Blueprint(
        TOOLKEY,
        __name__,
        url_prefix=f"/{TOOLKEY}",
        template_folder="templates",
    )
    serve = Serve(web)

    @app.route("/static/<path:filepath>")
    def serveStatic(filepath):
        theFile = f"{MY_DIR}/static/{filepath}"
        return send_file(theFile) if fileExists(theFile) else ""

    @app.route("/index", methods=METHODS)
    def serveNerX():
        return serveNer(serve)

    @app.route("/context/<int:node>", methods=METHODS)
    def serveNerContextX(node):
        return serveNerContext(serve, node)

    @app.route("/<path:anything>", methods=METHODS)
    def serveAllX(anything=None):
        return f"path={anything}"

    return app
