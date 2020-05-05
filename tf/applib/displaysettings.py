INTERFACE_OPTIONS = (
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
        "withNodes",
        False,
        "withn",
        "show nodes",
        "Show the node number for every node in the results."
        " The node number is your access to all information about that node."
        " If you click on it, it will be copied to the <i>node pad</i>",
    ),
    (
        "showFeatures",
        True,
        "showf",
        "show features",
        "Show the relevant feature values for every node in the results",
    ),
    (
        "showChunks",
        False,
        "showc",
        "show chunks",
        "Show chunk types fully. Only if the TF data has node types and companion chunked node types",
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
    extraFeatures=(),
    full=False,
    fmt=None,
    highlights={},
    noneValues={None},
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
        api = self.app.api
        error = api.error

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
        api = self.app.api
        error = api.error
        slotType = api.F.otype.slotType

        if option not in self.displayDefaults:
            error(f'WARNING: unknown display option "{option}" will be ignored')
            return None
        if option in {"extraFeatures", "tupleFeatures"}:
            api.ensureLoaded(value)
            if type(value) is str:
                value = value.split() if value else []
        elif option in {"suppress"}:
            if type(value) is str:
                value = set(value.split()) if value else set()
        elif option == "highlights":
            if value is not None and type(value) is not dict:
                value = {m: "" for m in value}
        elif option == "baseTypes":
            value = (
                set()
                if value is None
                else value
                if type(value) is set
                else {value}
                if type(value) is str
                else set(value)
            )
            value.discard(slotType)
        return (True, value)

    def check(self, msg, options):
        api = self.app.api
        Fotype = api.F.otype
        slotType = Fotype.slotType
        sectionTypeSet = api.T.sectionTypeSet
        error = api.error

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
                        legalValues -= {slotType}
                        isLegal = all(v in legalValues for v in value)
                    else:
                        isLegal = value in legalValues
                    if not isLegal:
                        error(
                            f'ERROR in {msg}(): illegal node type in "{option}={value}"'
                        )
                        good = False
        return good

    def get(self, options):
        displayDefaults = self.displayDefaults

        normOptions = {}

        for option in displayDefaults:
            value = options.get(option, None)
            if value is None:
                value = self.displayDefaults.get(option, None)
            normValue = self.normalize(option, value)
            if normValue:
                normOptions[option] = normValue[1]

        return DisplayCurrent(normOptions)

    def consume(self, options, *remove):
        return {o: options[o] for o in options if o not in remove}
