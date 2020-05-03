INTERFACE_OPTIONS = (
    ("withTypes", False, "witht", "show types"),
    ("prettyTypes", True, "withtp", "always show types when expanded"),
    ("withNodes", False, "withn", "show nodes"),
    ("showFeatures", True, "showf", "show features"),
    ("showChunks", False, "showc", "show chunks"),
    ("lineNumbers", False, "linen", "source lines"),
    ("showGraphics", True, "graphics", "graphic elements"),
)

DISPLAY_OPTIONS = dict(
    baseType=None,
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
            value = v
            appDefault = aContext.get(k, None)
            if appDefault is not None:
                value = appDefault
            if k in interfaceDefaults:
                value = interfaceDefaults[k]

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
        return (True, value)

    def check(self, msg, options):
        api = self.app.api
        sectionTypeSet = api.T.sectionTypeSet
        error = api.error

        good = True
        for (option, value) in options.items():
            if option not in self.displaySettings:
                error(f'ERROR in {msg}(): unknown display option "{option}={value}"')
                good = False
            if option in {"baseType", "condenseType"}:
                legalValues = set(api.F.otype.all)
                if option == "baseType":
                    legalValues -= sectionTypeSet
                if value is not None and value not in legalValues:
                    error(f'ERROR in {msg}(): unknown node type in "{option}={value}"')
                    good = False
        return good

    def get(self, options):
        displayDefaults = self.displayDefaults

        normOptions = {}

        for option in displayDefaults:
            value = (
                options[option]
                if option in options
                else self.displayDefaults.get(option, None)
            )
            normValue = self.normalize(option, value)
            if normValue:
                normOptions[option] = normValue[1]

        return DisplayCurrent(normOptions)

    def consume(self, options, *remove):
        return {o: options[o] for o in options if o not in remove}
