from flask import Blueprint, send_file

from ...core.files import abspath, fileExists, dirNm
from .serve import serveNer

MY_DIR = dirNm(abspath(__file__))


def factory(web):
    app = Blueprint(
        "ner",
        __name__,
        url_prefix="/ner",
        template_folder="templates",
    )

    @app.route("/static/<path:filepath>")
    def serveStatic(filepath):
        theFile = f"{MY_DIR}/static/{filepath}"
        return send_file(theFile) if fileExists(theFile) else ""

    @app.route("/index", methods=["GET", "POST"])
    def serveNerX():
        return serveNer(web)

    return app
