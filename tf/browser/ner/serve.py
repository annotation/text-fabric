"""Main controller for Flask

This module contains the main controller that Flask invokes when serving
the annotation tool.
"""

from flask import render_template

from .servelib import getFormData
from .kernel import entities, entityKinds
from .wrap import wrapEntityHeaders, wrapEntityKinds


def serveNer(web):
    """Serves the NE annotation tool.

    Parameters
    ----------
    web: object
        The flask web app
    """

    aContext = web.context
    appName = aContext.appName
    kernelApi = web.kernelApi
    app = kernelApi.app

    form = getFormData()
    resetForm = form["resetForm"]

    css = kernelApi.css()

    templateData = {}

    for (k, v) in form.items():
        if not resetForm or k not in templateData:
            templateData[k] = v

    sortKey = None
    sortDir = None

    for key in ("freqsort", "kindsort", "etxtsort"):
        currentState = templateData[key]
        if currentState:
            sortDir = "u" if currentState == "d" else "d"
            sortKey = key
            break

    templateData["appName"] = appName
    templateData["resetForm"] = ""
    templateData["entities"] = entities(app, sortKey, sortDir)
    templateData["entitykinds"] = wrapEntityKinds(entityKinds(app))
    templateData["entityheaders"] = wrapEntityHeaders(sortKey, sortDir)

    return render_template(
        "ner.html",
        css=css,
        **templateData,
    )
