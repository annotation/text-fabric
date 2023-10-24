"""Auxiliary functions for managing request data.

To see how this fits among all the modules of this package, see
`tf.browser.ner.annotate` .
"""

import json
from urllib.parse import unquote

from flask import request

from ...core.generic import AttrDict, deepAttrDict
from .settings import TOOLKEY, EMPTY, NONE, SORTKEY_DEFAULT, SORTDIR_DEFAULT, SC_ALL
from .helpers import findCompile


def getFormData(self):
    """Get form data.

    The TF browser user interacts with the app by clicking and typing,
    as a result of which a HTML form gets filled in.
    This form as regularly submitted to the server with a request
    for a new incarnation of the page: a response.

    The values that come with a request, must be peeled out of the form,
    and stored as logical values.

    Parameters
    ----------
    self: object
        A `tf.browser.ner.annotate.Annotate` object is expected.
    """
    settings = self.settings
    features = settings.features

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
    form["sortkey"] = fget("sortkey", "") or SORTKEY_DEFAULT
    form["sortdir"] = fget("sortdir", "") or SORTDIR_DEFAULT
    form["formattingdo"] = fget("formattingdo", "x") == "v"
    form["formattingstate"] = {
        feat: fget(f"{feat}_appearance", "v") == "v"
        for feat in features + ("_stat_", "_entity_")
    }
    form["bfind"] = fget("bfind", "")
    form["bfindc"] = fget("bfindc", "x") == "v"
    form["bfinderror"] = fget("bfinderror", "")

    anyEnt = fget("anyent", "")
    form["anyent"] = True if anyEnt == "v" else False if anyEnt == "x" else None

    form["freestate"] = fget("freestate", "all")
    activeEntity = fget("activeentity", None)
    form["activeentity"] = tuple(activeEntity.split("⊙")) if activeEntity else None
    form["efind"] = fget("efind", "")
    tokenStart = fget("tokenstart", "")
    form["tokenstart"] = int(tokenStart) if tokenStart else None
    tokenEnd = fget("tokenend", "")
    form["tokenend"] = int(tokenEnd) if tokenEnd else None
    form["activeval"] = tuple((feat, fget(f"{feat}_active", "")) for feat in features)
    makeValSelect(self, form)

    form["scope"] = fget("scope", SC_ALL)
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


def makeValSelect(self, form):
    """Set values for the entity features, based on the request.

    On the web page, there are hidden input fields for these values.
    These values are picked up and put in the form, under key `valselect`.
    Depending on which button caused the submit, the NONE value is added
    to each feature.

    The idea is that when the user is still engaged in filtering buckets,
    and there is an occurrence selected, the user should have the option
    to sub-select occurrences that do not yet have an entity assigned.

    Parameters
    ----------
    self: object
        A `tf.browser.ner.annotate.Annotate` object is expected.
    form: dict
        Contains the fields of the request data, in logical form.
    """
    settings = self.settings
    features = settings.features

    fget = request.form.get

    submitter = form["submitter"]
    valSelectProto = {feat: fget(f"{feat}_select", "") for feat in features}
    valSelect = {}

    startSearch = submitter in {"lookupq", "lookupn", "freebutton"}

    for feat in features:
        valProto = valSelectProto[feat]
        valSelect[feat] = (
            set("" if x == EMPTY else x for x in valProto.split(","))
            if valProto
            else set()
        )
        if startSearch:
            valSelect[feat].add(NONE)

    form["valselect"] = valSelect


def adaptValSelect(self, templateData):
    """Adapts the values contained in `valSelect` after a modification action.

    After the addition or deletion of an entity, the values contained in `valSelect`
    may have become obsolete or inconvenient for further actions.

    This function adapts those values before having them rendered on the page.

    Parameters
    ----------
    self: object
        A `tf.browser.ner.annotate.Annotate` object is expected.
    templateData: dict
        Contains the intermediate results of computing the new page.
    """
    settings = self.settings
    features = settings.features

    submitter = templateData.submitter
    valSelect = templateData.valselect

    if submitter == "addgo":
        addData = templateData.adddata
        additions = addData.additions
        freeVals = addData.freeVals

        freeState = templateData.freestate

        for i, (feat, values) in enumerate(zip(features, additions)):
            for val in values:
                valSelect.setdefault(feat, set()).add(val)
                if val == freeVals[i]:
                    freeVals[i] = None

        if freeState == "free":
            templateData.freestate = "all"

    elif submitter == "delgo":
        for feat in features:
            valSelect.setdefault(feat, set()).add(NONE)

    templateData.submitter = ""


def initTemplate(self, app):
    """Initializes the computation of the new page.

    It collects the request data, gleans some info from the configuration
    settings and the TF app, and initializes some data structures that
    will collect further information for the page.

    All bits and pieces that are needed during processing
    the request and filling in the final HTML template find a place under
    some key in the `templateData` dict which is stored in `self`.

    Parameters
    ----------
    self: object
        A `tf.browser.ner.annotate.Annotate` object is expected.
    app: object
        The TF app that represents the loaded corpus.
    """
    settings = self.settings
    bucketType = settings.bucketType
    features = settings.features

    aContext = app.context
    appName = aContext.appName.replace("/", " / ")
    api = app.api
    F = api.F
    slotType = F.otype.slotType

    form = getFormData(self)
    resetForm = form["resetForm"]

    templateData = AttrDict()
    templateData.toolkey = TOOLKEY
    templateData.buckettype = bucketType
    templateData.featurelist = ",".join(features)

    for k, v in form.items():
        if not resetForm or k not in templateData:
            templateData[k] = v

    templateData.appname = appName
    templateData.slottype = slotType
    templateData.resetform = ""

    self.templateData = templateData


def findSetup(templateData):
    """Compiles the filter pattern into a regular expression.

    When the user enters a search pattern in the box meant to filter the buckets,
    the pattern will be interpreted as a regular expression.

    We do the compilation here.
    If there are errors in the pattern they will be reported.
    Whether or not the search is case sensitive or not is under user control,
    and it will influence the compilation of the pattern.

    All input and output data is in `templateData` .
    """
    bFind = templateData.bfind
    bFindC = templateData.bfindc

    (bFind, bFindRe, errorMsg) = findCompile(bFind, bFindC)

    templateData.bfind = bFind
    templateData.bfindre = bFindRe
    templateData.errormsg = errorMsg
