"""Auxiliary functions for serving the web page.
"""

import re
import json
from urllib.parse import unquote

from flask import request

from ...core.generic import AttrDict, deepAttrDict
from ...core.files import dirContents
from .settings import TOOLKEY, FEATURES, EMPTY, NONE, BUCKET_TYPE


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

    fget = request.form.get

    form = {}

    form["resetForm"] = fget("resetForm", "")
    submitter = fget("submitter", "")
    form["submitter"] = submitter

    form["sec0"] = fget("sec0", "")
    form["sec1"] = fget("sec1", "")
    form["sec2"] = fget("sec2", "")
    form["annoset"] = fget("annoset", "")
    form["duannoset"] = fget("duannoset", "")
    form["rannoset"] = fget("rannoset", "")
    form["dannoset"] = fget("dannoset", "")
    form["sortkey"] = fget("sortkey", "") or "freqsort"
    form["sortdir"] = fget("sortdir", "") or "u"
    form["formattingdo"] = fget("formattingdo", "x") == "v"
    form["formattingstate"] = {
        feat: fget(f"{feat}_appearance", "v") == "v"
        for feat in FEATURES + ("_stat_", "_entity_")
    }
    form["sfind"] = fget("sfind", "")
    form["sfindc"] = fget("sfindc", "x") == "v"
    form["sfinderror"] = fget("sfinderror", "")

    form["freestate"] = fget("freestate", "all")
    activeEntity = fget("activeentity", "")
    form["activeentity"] = int(activeEntity) if activeEntity else None
    form["efind"] = fget("efind", "")
    tokenStart = fget("tokenstart", "")
    form["tokenstart"] = int(tokenStart) if tokenStart else None
    tokenEnd = fget("tokenend", "")
    form["tokenend"] = int(tokenEnd) if tokenEnd else None
    form["activeval"] = tuple((feat, fget(f"{feat}_active", "")) for feat in FEATURES)
    makeValSelect(form)

    form["scope"] = fget("scope", "a")
    excludedTokens = fget("excludedtokens", "")
    form["excludedtokens"] = (
        {int(t) for t in excludedTokens.split(",")} if excludedTokens else set()
    )
    addData = fget("adddata", "")
    form["adddata"] = (
        AttrDict() if addData == "" else deepAttrDict(json.loads(unquote(addData)))
    )
    delData = fget("deldata", "")
    form["deldata"] = (
        AttrDict() if delData == "" else deepAttrDict(json.loads(unquote(delData)))
    )
    form["reportdel"] = fget("reportdel", "")
    form["reportadd"] = fget("reportadd", "")
    form["modwidgetstate"] = fget("modwidgetstate", "add")

    return form


def makeValSelect(form):
    fget = request.form.get

    submitter = form["submitter"]
    valSelectProto = {feat: fget(f"{feat}_select", "") for feat in FEATURES}
    valSelect = {}

    startSearch = submitter in {"lookupq", "lookupn", "freebutton"}

    for feat in FEATURES:
        valProto = valSelectProto[feat]
        valSelect[feat] = (
            set("" if x == EMPTY else x for x in valProto.split(","))
            if valProto
            else set()
        )
        if startSearch:
            valSelect[feat].add(NONE)

    form["valselect"] = valSelect


def adaptValSelect(templateData):
    submitter = templateData.submitter
    valSelect = templateData.valselect

    if submitter == "addgo":
        addData = templateData.adddata
        additions = addData.additions
        freeVals = addData.freeVals

        freeState = templateData.freestate

        for (i, (feat, values)) in enumerate(zip(FEATURES, additions)):
            for val in values:
                valSelect.setdefault(feat, set()).add(val)
                if val == freeVals[i]:
                    freeVals[i] = None

        if freeState == "free":
            templateData.freestate = "all"

    elif submitter == "delgo":
        for feat in FEATURES:
            valSelect.setdefault(feat, set()).add(NONE)

    templateData.submitter = ""


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
    templateData.toolkey = TOOLKEY
    templateData.featurelist = ",".join(FEATURES)

    for (k, v) in form.items():
        if not resetForm or k not in templateData:
            templateData[k] = v

    templateData.appname = appName
    templateData.slottype = slotType
    templateData.buckettype = BUCKET_TYPE
    templateData.resetform = ""

    return templateData


def findSetup(web, templateData):
    sFind = templateData.sfind
    sFindC = templateData.sfindc

    sFind = (sFind or "").strip()
    sFindFlag = [] if sFindC else [re.I]
    sFindRe = None
    errorMsg = ""

    if sFind:
        try:
            sFindRe = re.compile(sFind, *sFindFlag)
        except Exception as e:
            errorMsg = str(e)

    templateData.sfind = sFind
    templateData.sfindre = sFindRe
    templateData.errormsg = errorMsg
