from ..fabric import Fabric
from ..parameters import TEMP_DIR
from ..lib import readSets
from ..core.helpers import console, setDir
from .app import findAppConfig
from .helpers import getLocalDir, configure
from .links import linksApi
from .text import textApi
from .sections import sectionsApi
from .displaysettings import displaySettingsApi
from .display import displayApi
from .search import searchApi
from .data import getModulesData


# SET UP A TF API FOR AN APP

def setupApi(
    app,
    appName,
    appPath,
    commit,
    release,
    local,
    hoist=False,
    version=None,
    checkout='',
    mod=None,
    locations=None,
    modules=None,
    api=None,
    setFile='',
    silent=False,
    _asApp=False,
):
  for (key, value) in dict(
      appName=appName,
      _asApp=_asApp,
      api=api,
      version=version,
      silent=silent,
  ).items():
    setattr(app, key, value)

  app.appPath = appPath
  app.commit = commit

  config = findAppConfig(appName, appPath)
  cfg = configure(config, version)
  version = cfg['version']
  cfg['localDir'] = getLocalDir(cfg, local, version)
  for (key, value) in cfg.items():
    setattr(app, key, value)

  setDir(app)

  if app.api:
    if app.standardFeatures is None:
      allFeatures = app.api.TF.explore(silent=silent or True, show=True)
      loadableFeatures = allFeatures['nodes'] + allFeatures['edges']
      app.standardFeatures = loadableFeatures
  else:
    app.sets = None
    if setFile:
      sets = readSets(setFile)
      if sets:
        app.sets = sets
        console(f'Sets from {setFile}: {", ".join(sets)}')
    specs = getModulesData(
        app,
        mod,
        locations,
        modules,
        version,
        checkout,
        silent,
    )
    if specs:
      (locations, modules) = specs
      app.tempDir = f'{app.repoLocation}/{TEMP_DIR}'
      TF = Fabric(locations=locations, modules=modules, silent=silent or True)
      api = TF.load('', silent=silent or True)
      if api:
        app.api = api
        allFeatures = TF.explore(silent=silent or True, show=True)
        loadableFeatures = allFeatures['nodes'] + allFeatures['edges']
        if app.standardFeatures is None:
          app.standardFeatures = loadableFeatures
        useFeatures = [f for f in loadableFeatures if f not in app.excludedFeatures]
        result = TF.load(useFeatures, add=True, silent=silent or True)
        if result is False:
          app.api = None
    else:
      app.api = None

  if app.api:
    linksApi(app, appName, silent)
    textApi(app)
    searchApi(app)
    sectionsApi(app)
    displaySettingsApi(app)
    displayApi(app, silent, hoist)
  else:
    if not _asApp:
      console(
          f'''
There were problems with loading data.
The Text-Fabric API has not been loaded!
The app "{appName}" will not work!
''',
          error=True,
      )
