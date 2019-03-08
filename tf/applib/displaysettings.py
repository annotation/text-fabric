import types

DISPLAY_OPTIONS = dict(
    colorMap=None,
    condensed=False,
    condenseType=None,
    end=None,
    extraFeatures=(),
    full=False,
    tupleFeatures=(),
    fmt=None,
    highlights={},
    linked=1,
    noneValues=None,
    start=None,
    suppress=set(),
    withNodes=False,
    withPassage=True,
)


def displaySettingsApi(app):
  app.display = DisplaySettings(app)
  app.displaySetup = types.MethodType(displaySetup, app)
  app.displayReset = types.MethodType(displayReset, app)


class DisplayCurrent(object):
  def __init__(self, options):
    for (k, v) in options.items():
      setattr(self, k, v)


class DisplaySettings(object):
  def __init__(self, app):
    self.app = app

    self._compileFormatClass()

    self.displayDefaults = {k: v for (k, v) in DISPLAY_OPTIONS.items()}
    self.displayDefaults = {}
    for (k, v) in DISPLAY_OPTIONS.items():
      self.displayDefaults[k] = (
          v if v is not None else
          getattr(app, k, None)
      )
    self.displayDefaults.update({o[0]: o[1] for o in app.options})
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
    api = self.app.api
    error = api.error
    for (option, value) in options.items():
      if option not in self.displayDefaults:
        error(f'WARNING: unknown display option "{option}" will be ignored')
        continue
      if option in {'extraFeatures', 'tupleFeatures'}:
        api.ensureLoaded(value)
        if type(value) is str:
          value = value.split() if value else []
      self.displaySettings[option] = value

  def check(self, msg, options):
    api = self.app.api
    error = api.error
    good = True
    for (option, value) in options.items():
      if option not in self.displaySettings:
        error(f'ERROR in {msg}(): unknown display option "{option}={value}"')
        good = False
      if option == 'condenseType':
        if value is not None:
          if value not in api.F.otype.all:
            error(f'ERROR in {msg}(): unknown node type in "{option}={value}"')
            good = False
    return good

  def get(self, options):
    return DisplayCurrent({
        o: options[o] if o in options else self.displaySettings.get(o, None)
        for o in self.displaySettings
    })

  def consume(self, options, *remove):
    return {o: options[o] for o in options if o not in remove}

  def _compileFormatClass(self):
    app = self.app
    api = app.api
    T = api.T

    result = {None: app.defaultClsOrig}
    for fmt in T.formats:
      for (key, cls) in app.formatCss.items():
        if f'-{key}-' in fmt or fmt.startswith(f'{key}-') or fmt.endswith(f'-{key}'):
          result[fmt] = cls
    for fmt in T.formats:
      if fmt not in result:
        result[fmt] = app.defaultCls
    self.formatClass = result


def displaySetup(app, **options):
  app.display.setup(**options)


def displayReset(app, *options):
  app.display.reset(*options)
