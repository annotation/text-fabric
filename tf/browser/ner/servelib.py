"""Auxiliary functions for serving the web page.
"""

import re
import json
from urllib.parse import unquote

from flask import request

from ...core.generic import AttrDict, deepAttrDict
from ...core.files import dirContents
from .settings import FEATURES


def getFormData(web):
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

    form["resetForm"] = request.form.get("resetForm", "")
    submitter = request.form.get("submitter", "")
    form["submitter"] = submitter

    form["sec0"] = request.form.get("sec0", "")
    form["sec1"] = request.form.get("sec1", "")
    form["sec2"] = request.form.get("sec2", "")
    form["annoset"] = request.form.get("annoset", "")
    form["duannoset"] = request.form.get("duannoset", "")
    form["rannoset"] = request.form.get("rannoset", "")
    form["dannoset"] = request.form.get("dannoset", "")
    form["sortkey"] = request.form.get("sortkey", "") or "freqsort"
    form["sortdir"] = request.form.get("sortdir", "") or "u"
    form["sfind"] = request.form.get("sfind", "")
    form["sfinderror"] = request.form.get("sfinderror", "")
    activeEntity = request.form.get("activeentity", "")
    form["activeentity"] = int(activeEntity) if activeEntity else None
    form["efind"] = request.form.get("efind", "")
    tokenStart = request.form.get("tokenstart", "")
    form["tokenstart"] = int(tokenStart) if tokenStart else None
    tokenEnd = request.form.get("tokenend", "")
    form["tokenend"] = int(tokenEnd) if tokenEnd else None
    valSelectProto = {feat: request.form.get(f"{feat}_select", "") for feat in FEATURES}
    valSelect = {}
    activeVal = []

    for (i, feat) in enumerate(FEATURES):
        valProto = valSelectProto[feat]
        valSelect[feat] = (
            set(valProto.split(","))
            if valProto
            else {"⌀"}
            if submitter == "lookupq"
            else set()
        )
        activeVal.append((feat, request.form.get(f"{feat}_active", "")))

    form["valselect"] = valSelect
    form["activeval"] = tuple(activeVal)

    form["scope"] = request.form.get("scope", "a")
    excludedTokens = request.form.get("excludedtokens", "")
    form["excludedtokens"] = (
        {int(t) for t in excludedTokens.split(",")} if excludedTokens else set()
    )
    modifyData = request.form.get("modifydata", "")
    form["modifydata"] = (
        AttrDict()
        if modifyData == ""
        else deepAttrDict(json.loads(unquote(modifyData)))
    )
    web.console(f"{unquote(modifyData)}")

    return form


def annoSets(annoDir):
    """Get the existing annotation sets.

    Parameters
    ----------
    annoDir: string
        The directory under which the distinct annotation sets can be found.
        The names of these subdirectories are the names of the annotation sets.

    Returns
    -------
    set
        The annotation sets, sorted by name.
    """
    return set(dirContents(annoDir)[1])


def initTemplate(web):
    kernelApi = web.kernelApi
    app = kernelApi.app
    aContext = web.context
    appName = aContext.appName.replace("/", " / ")
    api = app.api
    F = api.F
    slotType = F.otype.slotType

    form = getFormData(web)
    resetForm = form["resetForm"]

    templateData = AttrDict()
    templateData.featurelist = ",".join(FEATURES)

    for (k, v) in form.items():
        if not resetForm or k not in templateData:
            templateData[k] = v

    templateData.appname = appName
    templateData.slottype = slotType
    templateData.resetform = ""

    return templateData


def findSetup(web, templateData):
    sFind = templateData.sfind
    sFind = (sFind or "").strip()
    sFindRe = None
    errorMsg = ""

    if sFind:
        try:
            sFindRe = re.compile(sFind)
        except Exception as e:
            errorMsg = str(e)

    templateData.sfind = sFind
    templateData.sfindre = sFindRe
    templateData.errormsg = errorMsg
