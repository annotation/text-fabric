from flask import Blueprint, send_file

from ...core.files import abspath, fileExists, dirNm
from .settings import TOOLKEY
from .serve import serveNer, serveNerContext


MY_DIR = dirNm(abspath(__file__))


def factory(web):
    app = Blueprint(
        TOOLKEY,
        __name__,
        url_prefix=f"/{TOOLKEY}",
        template_folder="templates",
    )

    @app.route("/static/<path:filepath>")
    def serveStatic(filepath):
        theFile = f"{MY_DIR}/static/{filepath}"
        return send_file(theFile) if fileExists(theFile) else ""

    @app.route("/index", methods=["GET", "POST"])
    def serveNerX():
        return serveNer(web)

    @app.route("/context/<int:node>", methods=["GET", "POST"])
    def serveNerContextX(node):
        return serveNerContext(web, node)

    @app.route("/<path:anything>", methods=["GET", "POST"])
    def serveAllX(anything=None):
        return f"path={anything}"

    return app
