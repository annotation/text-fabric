"""
.. include:: ../../docs/applib/displaysettings.md
"""

from ..core.helpers import setFromValue
from .helpers import parseFeatures, SEQ_TYPES1, SEQ_TYPES2


INTERFACE_OPTIONS = (
    (
        "withNodes",
        False,
        "withn",
        "show nodes",
        "Show the node number for every node in the results."
        " The node number is your access to all information about that node."
        " If you click on it, it will be copied to the <i>node pad</i>",
    ),
    (
        "withTypes",
        False,
        "witht",
        "show types",
        "Show the node type for every node in the results",
    ),
    (
        "prettyTypes",
        True,
        "withtp",
        "always show types when expanded",
        "Show the node type for every node in the expanded view, even if <b>show types</b> is off",
    ),
    (
        "standardFeatures",
        False,
        "showf",
        "show standard features",
        "Show the standard feature values for every node in the results",
    ),
    (
        "queryFeatures",
        True,
        "showf",
        "show query features",
        "Show the features mentioned in the last query for every node in the results",
    ),
    (
        "showHidden",
        False,
        "showc",
        "show hidden",
        "Show hidden types. Only if the TF data has hidden node types",
    ),
    (
        "lineNumbers",
        False,
        "linen",
        "source lines",
        "Show source line numbers with the nodes. Only if the TF data has a feature for line numbers.",
    ),
    (
        "showGraphics",
        True,
        "graphics",
        "graphic elements",
        "Show graphical companion elements with the nodes."
        " Only if the data set implements the logic for it",
    ),
)


# <p><b title="withTypes">Show types</b>{longDesc}</p>

DISPLAY_OPTIONS = dict(
    baseTypes=None,
    colorMap=None,
    condensed=False,
    condenseType=None,
    end=None,
    extraFeatures=((), {}),
    full=False,
    fmt=None,
    highlights={},
    noneValues={None},
    skipCols=set(),
    start=None,
    suppress=set(),
    tupleFeatures=(),
    withPassage=True,
)

DISPLAY_OPTIONS.update({o[0]: o[1] for o in INTERFACE_OPTIONS})


class DisplayCurrent:
    def __init__(self, options):
        for (k, v) in options.items():
            setattr(self, k, v)


class DisplaySettings:

    def __init__(self, app):
        self.app = app

        aContext = app.context
        interfaceDefaults = aContext.interfaceDefaults

        self.displayDefaults = {}
        displayDefaults = self.displayDefaults

        for (k, v) in DISPLAY_OPTIONS.items():
            value = (
                interfaceDefaults[k] if k in interfaceDefaults else aContext.get(k, v)
            )
            displayDefaults[k] = value

        self.reset()

    def reset(self, *options):
        app = self.app
        error = app.error

        for option in options:
            if option not in self.displayDefaults:
                error(f'WARNING: unknown display option "{option}" will be ignored')
                continue
            self.displaySettings[option] = self.displayDefaults[option]
        if not options:
            self.displaySettings = {k: v for (k, v) in self.displayDefaults.items()}

    def setup(self, **options):
        for (option, value) in options.items():
            normValue = self.normalize(option, value)
            if not normValue:
                continue
            self.displaySettings[option] = normValue[1]

    def normalize(self, option, value):
        app = self.app
        api = app.api
        error = app.error

        if option not in self.displayDefaults:
            error(f'WARNING: unknown display option "{option}" will be ignored')
            return None

        if option == "extraFeatures":
            (bare, indirect) = parseFeatures(value)
            api.ensureLoaded(bare)
            value = (bare, indirect)
        elif option == "tupleFeatures":
            api.ensureLoaded(value)
            if type(value) is str:
                value = value.split() if value else []
        elif option in {"suppress"}:
            if type(value) is str:
                value = set(value.split()) if value else set()
        elif option in {"skipCols"}:
            if not value:
                value = set()
            elif type(value) is str:
                value = set(int(v) for v in value.split()) if value else set()
            elif type(value) not in {set, frozenset}:
                value = set(value)
        elif option in {"withPassage"}:
            if not value:
                value = False
            elif type(value) is str:
                value = set(int(v) for v in value.split()) if value else set()
            elif type(value) in {list, tuple, dict}:
                value = set(value)
            else:
                value = True
        elif option == "highlights":
            if value is not None and type(value) is not dict:
                value = {m: "" for m in value}
        elif option == "baseTypes":
            value = setFromValue(value)
        return (True, value)

    def check(self, msg, options):
        app = self.app
        api = app.api
        Fotype = api.F.otype
        sectionTypeSet = api.T.sectionTypeSet
        error = app.error

        good = True
        for (option, value) in options.items():
            if option not in self.displaySettings:
                error(f'ERROR in {msg}(): unknown display option "{option}={value}"')
                good = False
            if option in {"baseTypes", "condenseType"}:
                if value is not None:
                    legalValues = set(Fotype.all)
                    if option == "baseTypes":
                        legalValues -= sectionTypeSet
                        testVal = setFromValue(value)
                        isLegal = all(v in legalValues for v in testVal)
                    else:
                        isLegal = value in legalValues
                    if not isLegal:
                        error(
                            f'ERROR in {msg}(): illegal node type in "{option}={value}"'
                        )
                        good = False
            elif option == "extraFeatures":
                if value is not None:
                    if (
                        type(value) in SEQ_TYPES1
                        and len(value) == 2
                        and type(value[0]) in SEQ_TYPES2
                        and type(value[1]) is dict
                    ):
                        indirect = value[1]
                        legalValues = set(Fotype.all)
                        isLegal = all(v in legalValues for v in indirect)
                        if not isLegal:
                            error(
                                f"ERROR in {msg}(): illegal node type in"
                                f' "{option}={value}"'
                            )
                            good = False
        return good

    def get(self, options):
        displayDefaults = self.displayDefaults
        displaySettings = self.displaySettings

        normOptions = {}

        for option in displayDefaults:
            value = options.get(
                option, displaySettings.get(option, displayDefaults[option])
            )
            normValue = self.normalize(option, value)
            if normValue:
                normOptions[option] = normValue[1]

        return DisplayCurrent(normOptions)

    def consume(self, options, *remove):
        return {o: options[o] for o in options if o not in remove}
