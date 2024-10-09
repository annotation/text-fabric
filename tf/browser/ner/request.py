"""Auxiliary functions for managing request data.
"""

from ...core.generic import AttrDict
from ...ner.settings import TOOLKEY
from ...ner.helpers import findCompile
from ...ner.settings import EMPTY, NONE

from .websettings import SC_ALL
from .form import Form


class Request(Form):
    def __init__(self):
        """Calculate important values based on form data.

        We define specifications as to how to read form values and which defaults
        should be supplied.

        We categorize the keys in the request form into categories based on their
        interpreted type and organization.

        We provide appropriate empty values as defaults, but it is possible to specify
        other defaults.

        The categories are:

        *   `Str` values are strings;
        *   `Bool` values are booleans (2 possible values);
        *   `Tri` values are booleans (3 possible values, a none value is included);
        *   `Int` values are positive integers;
        *   `Tup` values are tuples of strings;
        *   `SetInt` values are sets of integers;
        *   `Json` values are arbitrary structures encoded in JSON strings;

        We also define a few composed values, where we store the values of
        several related keys in the form as a dictionary value under a new key.
        """
        ner = self.ner
        settings = ner.settings
        features = settings.features

        keysStr = """
            activename
            activetrigger
            activesheet
            activesection
            resetForm
            submitter
            sec0
            sec1
            sec2
            task
            duset
            rset
            dset
            caption
            logs
            sortkey
            sortdir
            bfind
            bfinderror
            freestate
            efind
            scope
            reportdel
            reportadd
            modwidgetstate
        """.strip().split()

        keysBool = """
            formattingdo
            bfindc
            sheetcase
        """.strip().split()

        keysTri = """
            anyent
            subtlefilter
        """.strip().split()

        keysInt = """
            tokenstart
            tokenend
        """.strip().split()

        keysTup = """
            activeentity
            activetrigger
        """.strip().split()

        keysSetInt = """
            excludedtokens
        """.strip().split()

        keysJson = """
            adddata
            deldata
        """.strip().split()

        defaults = dict(
            sortkey=None,
            sortdir=None,
            sheetcase="x",
            freestate="all",
            scope=SC_ALL,
            modwidgetstate="add",
        )

        formattingState = {
            feat: f"{feat}_appearance" for feat in features + ("_stat_", "_entity_")
        }
        self.formattingState = formattingState

        for feat, featStr in formattingState.items():
            keysBool.append(featStr)
            defaults[featStr] = "v"

        activeVal = {feat: f"{feat}_active" for feat in features}
        self.activeVal = activeVal

        for feat, featStr in activeVal.items():
            keysStr.append(featStr)

        valSelectProto = {feat: f"{feat}_select" for feat in features}
        self.valSelectProto = valSelectProto

        for feat, featStr in valSelectProto.items():
            keysStr.append(featStr)

        Form.__init__(
            self,
            features,
            defaults,
            keysStr=keysStr,
            keysBool=keysBool,
            keysTri=keysTri,
            keysInt=keysInt,
            keysTup=keysTup,
            keysSetInt=keysSetInt,
            keysJson=keysJson,
        )

    def getFormData(self):
        """Get form data.

        The TF browser user interacts with the app by clicking and typing,
        as a result of which a HTML form gets filled in.
        This form as regularly submitted to the server with a request
        for a new incarnation of the page: a response.

        The values that come with a request, must be peeled out of the form,
        and stored as logical values.

        Additionally, some business logic is carried out:
        we set values for the entity features, based on the form, especially the
        keys ending in `_active`. We build a value under key `valselect`
        based on the value for key `submitter`.
        Depending on which button caused the submit, the NONE value is added
        to each feature.

        The idea is that when the user is still engaged in filtering buckets,
        and there is an occurrence selected, the user should have the option
        to sub-select occurrences that do not yet have an entity assigned.
        """
        ner = self.ner
        settings = ner.settings
        features = settings.features
        formattingState = self.formattingState
        activeVal = self.activeVal
        valSelectProto = self.valSelectProto

        form = self.fill()

        form.formattingstate = {
            feat: self.fget2(featStr) for (feat, featStr) in formattingState.items()
        }

        form.activeval = {
            feat: self.fgets(featStr) for (feat, featStr) in activeVal.items()
        }

        valSelectProto = {
            feat: self.fgets(featStr) for (feat, featStr) in valSelectProto.items()
        }

        submitter = form.submitter

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

        form.valselect = valSelect

        return form

    def initVars(self):
        """Initializes the computation of the new page.

        It collects the request data, gleans some info from the configuration
        settings and the TF app, and initializes some data structures that
        will collect further information for the page.

        All bits and pieces that are needed during processing
        the request and filling in the final HTML template find a place under
        some key in the `v` dict which is stored in `self`.

        So, this function makes the transition from information that is in the
        `form` dictionary to values that are stored in the `v` dictionary.
        """
        ner = self.ner
        bucketType = ner.bucketType
        settings = ner.settings
        features = settings.features

        appName = ner.appName
        appName = appName.replace("/", " / ")
        slotType = ner.slotType

        form = self.getFormData()
        resetForm = form.resetForm

        v = AttrDict()
        v.toolkey = TOOLKEY
        v.buckettype = bucketType
        v.featurelist = ",".join(features)

        for k, vl in form.items():
            if not resetForm or k not in v:
                v[k] = vl

        v.appname = appName
        v.slottype = slotType
        v.resetform = ""

        self.v = v

    def adaptValSelect(self):
        """Adapts the values contained in `valSelect` after a modification action.

        After the addition or deletion of an entity, the values contained in `valSelect`
        may have become obsolete or inconvenient for further actions.

        This function adapts those values before having them rendered on the page.

        Parameters
        ----------
        v: dict
            Contains the intermediate results of computing the new page.
        """
        v = self.v
        ner = self.ner
        settings = ner.settings
        features = settings.features

        submitter = v.submitter
        valSelect = v.valselect

        if submitter == "addgo":
            addData = v.adddata
            additions = addData.additions
            freeVals = addData.freeVals

            freeState = v.freestate

            for i, (feat, values) in enumerate(zip(features, additions)):
                for val in values:
                    valSelect.setdefault(feat, set()).add(val)
                    if val == freeVals[i]:
                        freeVals[i] = None

            if freeState == "free":
                v.freestate = "all"

        elif submitter == "delgo":
            for feat in features:
                valSelect.setdefault(feat, set()).add(NONE)

        v.submitter = ""

    def findSetup(self):
        """Compiles the filter pattern into a regular expression.

        When the user enters a search pattern in the box meant to filter the buckets,
        the pattern will be interpreted as a regular expression.

        We do the compilation here.
        If there are errors in the pattern they will be reported.
        Whether or not the search is case sensitive or not is under user control,
        and it will influence the compilation of the pattern.

        All input and output data is in `v` .
        """
        v = self.v
        bFind = v.bfind
        bFindC = v.bfindc

        (bFind, bFindRe, errorMsg) = findCompile(bFind, bFindC)

        v.bfind = bFind
        v.bfindre = bFindRe
        v.errormsg = errorMsg
