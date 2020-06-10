"""
.. include:: ../../docs/advanced/options.md
"""

from ..core.helpers import setFromValue
from .helpers import parseFeatures, SEQ_TYPES1, SEQ_TYPES2


INTERFACE_OPTIONS = (
    (
        "condensed",
        False,
        "cond",
        "condense results",
        "Group query results into containers of the selected type.",
        True,
    ),
    (
        "hideTypes",
        True,
        "hidet",
        "hide types",
        "Do not show the outer structure of nodes of the selected types."
        "The contents of those nodes are still shown.",
        True,
    ),
    (
        "withNodes",
        False,
        "withn",
        "show nodes",
        "Show the node number for every node in the results."
        " The node number is your access to all information about that node."
        " If you click on it, it will be copied to the <i>node pad</i>.",
        False,
    ),
    (
        "withTypes",
        False,
        "witht",
        "show types",
        "Show the node type for every node in the results.",
        False,
    ),
    (
        "prettyTypes",
        True,
        "withtp",
        "always show types when expanded",
        "Show the node type for every node in the expanded view, even if <b>show types</b> is off.",
        False,
    ),
    (
        "plainGaps",
        True,
        "plaing",
        "show gaps",
        "In plain displays, show the gaps in nodes by means of dotted lines.",
        False,
    ),
    (
        "standardFeatures",
        False,
        "showf",
        "show standard features",
        "Show the standard feature values for every node in the results.",
        False,
    ),
    (
        "queryFeatures",
        True,
        "showf",
        "show query features",
        "Show the features mentioned in the last query for every node in the results.",
        False,
    ),
    (
        "lineNumbers",
        False,
        "linen",
        "source lines",
        "Show source line numbers with the nodes."
        " Only if the TF data has a feature for line numbers.",
        False,
    ),
    (
        "showGraphics",
        True,
        "graphics",
        "graphic elements",
        "Show graphical companion elements with the nodes."
        " Only if the data set implements the logic for it.",
        False,
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
    hideTypes=True,
    hiddenTypes=None,
    highlights={},
    noneValues={None},
    skipCols=set(),
    start=None,
    suppress=set(),
    tupleFeatures=(),
    withPassage=True,
)

DISPLAY_OPTIONS.update({o[0]: o[1] for o in INTERFACE_OPTIONS})


class OptionsCurrent:
    def __init__(self, options):
        self.allKeys = set(options)
        for (k, v) in options.items():
            setattr(self, k, v)

    def get(self, k, v=None):
        return getattr(self, k, v)

    def set(self, k, v):
        self.allKeys.add(k)
        setattr(self, k, v)


class Options:
    def __init__(self, app):
        self.app = app

        aContext = app.context
        interfaceDefaults = aContext.interfaceDefaults

        self.defaults = {}
        defaults = self.defaults

        for (k, v) in DISPLAY_OPTIONS.items():
            value = (
                interfaceDefaults[k] if k in interfaceDefaults else aContext.get(k, v)
            )
            defaults[k] = value

        self.reset()

    def reset(self, *options):
        app = self.app
        error = app.error
        defaults = self.defaults

        if options:
            current = self.current
            for option in options:
                if option not in defaults:
                    error(f'WARNING: unknown display option "{option}" will be ignored')
                    continue
                current[option] = defaults[option]
        else:
            self.current = {k: v for (k, v) in defaults.items()}

    def setup(self, *options, **overrides):
        current = self.current

        for (option, value) in overrides.items():
            normValue = self.normalize(option, value)
            if not normValue:
                continue
            current[option] = normValue[1]

    def normalize(self, option, value):
        app = self.app
        api = app.api
        aContext = app.context
        allowedValues = aContext.allowedValues
        error = app.error
        defaults = self.defaults

        if option not in defaults:
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
            elif type(value) is not set:
                value = True
        elif option == "highlights":
            if value is not None and type(value) is not dict:
                value = {m: "" for m in value}
        elif option in {"baseTypes", "hiddenTypes"}:
            legalValues = set(allowedValues[option])
            values = setFromValue(value)
            value = {tp for tp in values if tp in legalValues}
        return (True, value)

    def check(self, msg, options):
        app = self.app
        api = app.api
        Fotype = api.F.otype
        aContext = app.context
        allowedValues = aContext.allowedValues
        error = app.error
        current = self.current

        good = True
        for (option, value) in options.items():
            if option not in current:
                error(f'ERROR in {msg}(): unknown display option "{option}={value}"')
                good = False
            if option in {"baseTypes", "condenseType", "hiddenTypes"}:
                legalValues = set(allowedValues[option])
                if value is not None:
                    if option in {"baseTypes", "hiddenTypes"}:
                        testVal = setFromValue(value)
                        isLegal = all(v in legalValues for v in testVal)
                    else:
                        isLegal = value in legalValues
                    if not isLegal:
                        error(
                            f'ERROR in {msg}(): illegal node type in "{option}={value}"'
                        )
                        legalRep = ", ".join(sorted(legalValues))
                        error(f"Legal values are: {legalRep}")
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

    def distill(self, options):
        defaults = self.defaults
        current = self.current

        normOptions = {}

        for option in defaults:
            value = options.get(
                option, current.get(option, defaults[option])
            )
            normValue = self.normalize(option, value)
            if normValue:
                normOptions[option] = normValue[1]

        return OptionsCurrent(normOptions)

    def consume(self, options, *remove):
        return {o: options[o] for o in options if o not in remove}
