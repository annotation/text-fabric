"""Auxiliary functions for serving the page.
"""

import json
from urllib.parse import unquote

from flask import request

from ...core.generic import AttrDict, deepAttrDict
from .settings import (
    TOOLKEY,
    FEATURES,
    EMPTY,
    NONE,
    BUCKET_TYPE,
    SORTKEY_DEFAULT,
    SORTDIR_DEFAULT,
)
from .kernel import findCompile


def getFormData():
    """Get form data.

    The TF browser user interacts with the app by clicking and typing,
    as a result of which a HTML form gets filled in.
    This form as regularly submitted to the server with a request
    for a new incarnation of the page: a response.

    The values that come with a request, must be peeled out of the form,
    and stored as logical values.

    Most of the data has a known function to the server,
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
    form["sortkey"] = fget("sortkey", "") or SORTKEY_DEFAULT
    form["sortdir"] = fget("sortdir", "") or SORTDIR_DEFAULT
    form["formattingdo"] = fget("formattingdo", "x") == "v"
    form["formattingstate"] = {
        feat: fget(f"{feat}_appearance", "v") == "v"
        for feat in FEATURES + ("_stat_", "_entity_")
    }
    form["bfind"] = fget("bfind", "")
    form["bfindc"] = fget("bfindc", "x") == "v"
    form["bfinderror"] = fget("bfinderror", "")

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


def initTemplate(app):
    aContext = app.context
    appName = aContext.appName.replace("/", " / ")
    api = app.api
    F = api.F
    slotType = F.otype.slotType

    form = getFormData()
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


def findSetup(templateData):
    bFind = templateData.bfind
    bFindC = templateData.bfindc

    (bFind, bFindRe, errorMsg) = findCompile(bFind, bFindC)

    templateData.bfind = bFind
    templateData.bfindre = bFindRe
    templateData.errormsg = errorMsg
