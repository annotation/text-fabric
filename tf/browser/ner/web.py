"""Flask sub web app in the TF browser.
"""

from flask import Blueprint, send_file

from ...core.generic import AttrDict
from ...core.files import abspath, fileExists, dirNm
from ...ner.settings import TOOLKEY
from ...ner.ner import NER

from .serve import serveNer, serveNerContext


MY_DIR = dirNm(abspath(__file__))

METHODS = ["GET", "POST"]


def factory(web):
    """A sub web app, to be inserted into the TF browser web app.

    The way of connecting this sub app to the main app is by way of the concept
    of [BluePrint](https://flask.palletsprojects.com/en/2.3.x/blueprints/),
    which is built into Flask itself.

    Before starting the actual serving of pages, we initialize a
    `tf.ner.ner.NER` object, and store it under attribute `ner`.

    In order to do so, we pick up a handle to the loaded TF corpus,
    and a handle to the tool data, both present in the `web` object (see parameters
    below).


    Parameters
    ----------
    web: object
        This represents the Flask website that is the TF browser.

        We may assume that an API for a loaded TF corpus is present under attribute
        `kernelApi`.

        Possibly there is also an attribute `toolData`, which is the store for all
        tool specific data.
        If not, we create an empty store. Inside that store we create an empty
        sub-store for this specific tool.
        The initialization of the `NER` object makes sure this store is
        populated by the tool data as it is read from disk.

        This way, the annotation data is preserved between requests.
    """
    app = Blueprint(
        TOOLKEY,
        __name__,
        url_prefix=f"/{TOOLKEY}",
        template_folder="templates",
    )
    kernelApi = web.kernelApi
    tfApp = kernelApi.app

    if not hasattr(web, "toolData"):
        setattr(web, "toolData", AttrDict())

    toolData = web.toolData

    if TOOLKEY not in toolData:
        toolData[TOOLKEY] = AttrDict()

    data = toolData[TOOLKEY]
    web.ner = NER(tfApp, data=data, browse=True)

    if not web.ner.properlySetup:
        return app

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
