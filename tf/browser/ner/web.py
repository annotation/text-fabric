"""Flask sub web app in the TF browser.

To see how this fits among all the modules of this package, see
`tf.browser.ner.annotate` .
"""

from flask import Blueprint, send_file

from ...core.files import abspath, fileExists, dirNm
from .settings import TOOLKEY
from .serve import serveNer, serveNerContext


MY_DIR = dirNm(abspath(__file__))

METHODS = ["GET", "POST"]


def factory(web):
    """A sub webapp, to be inserted into the TF browser webapp.

    The way of connecting this sub app to the main app is by way of the concept
    of [BluePrint](https://flask.palletsprojects.com/en/2.3.x/blueprints/),
    which is built into Flask itself.
    """
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

    @app.route("/index", methods=METHODS)
    def serveNerX():
        return serveNer(web)

    @app.route("/context/<int:node>", methods=METHODS)
    def serveNerContextX(node):
        return serveNerContext(web, node)

    @app.route("/<path:anything>", methods=METHODS)
    def serveAllX(anything=None):
        return f"path={anything}"

    return app
