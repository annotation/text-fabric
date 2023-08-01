"""Auxiliary functions for serving the web page.
"""

from flask import request


def getFormData():
    """Get form data.

    The TF browser user interacts with the web app by clicking and typing,
    as a result of which a HTML form gets filled in.
    This form as regularly submitted to the web server with a request
    for a new incarnation of the page: a response.

    The values that come with a request, must be peeled out of the form,
    and stored as logical values.

    Most of the data has a known function to the web server,
    but there is also a list of webapp dependent options.
    """

    form = {}
    resetForm = request.form.get("resetForm", "")
    form["resetForm"] = resetForm

    form["sec0"] = request.form.get("sec0", "")
    form["sec1"] = request.form.get("sec1", "")
    form["sec2"] = request.form.get("sec2", "")
    form["freqsort"] = request.form.get("freqsort", "")
    form["kindsort"] = request.form.get("kindsort", "")
    form["etxtsort"] = request.form.get("etxtsort", "")

    return form
