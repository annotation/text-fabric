import os
import io
import re
import types
from shutil import rmtree
import requests
from zipfile import ZipFile

from tf.helpers import itemize, camel, console
from tf.apphelpers import (
    search,
    table, plainTuple,
    show, pretty, prettyTuple, prettySetup,
    nodeFromDefaultSection,
    dm, dh, header,
    CSS_FONT, CSS_FONT_API,
)
from tf.server.common import getAppConfig, getAppClass
from tf.fabric import Fabric
from tf.notebook import location
from tf.parameters import (
    URL_GH_API,
    URL_GH,
    URL_NB,
    URL_TFDOC,
    GH_BASE,
    EXPRESS_BASE,
    EXPRESS_INFO,
)


# START AN APP

def use(appName, *args, **kwargs):
  appClass = getAppClass(appName)
  if not appClass:
    return None
  return appClass(*args, **kwargs)


# SET UP A TF API FOR AN APP

def setupApi(
    app,
    name,
    appName,
    moduleRefs,
    locations,
    modules,
    asApp,
    api,
    version,
    lgc,
    check,
    silent,
    hoist,
):
  for (key, value) in dict(
      appName=appName,
      asApp=asApp,
      api=api,
      version=version,
      silent=silent,
  ).items():
    setattr(app, key, value)

  config = getAppConfig(appName)
  if version is None:
    version = config.VERSION
  cfg = config.configure(lgc=lgc, version=version)
  for (key, value) in cfg.items():
    setattr(app, key, value)

  app.cwd = os.getcwd()

  if app.api:
    if app.standardFeatures is None:
      allFeatures = app.api.TF.explore(silent=True, show=True)
      loadableFeatures = allFeatures['nodes'] + allFeatures['edges']
      app.standardFeatures = loadableFeatures
    app.api.TF.load(app.standardFeatures, add=True, silent=True)
  else:
    specs = _getModulesData(
        app,
        moduleRefs,
        locations, modules,
        version,
        lgc, check, silent,
    )
    if specs:
      (locations, modules) = specs
      TF = Fabric(locations=locations, modules=modules, silent=True)
      api = TF.load('', silent=True)
      if api:
        app.api = api
        allFeatures = TF.explore(silent=True, show=True)
        loadableFeatures = allFeatures['nodes'] + allFeatures['edges']
        if app.standardFeatures is None:
          app.standardFeatures = loadableFeatures
        useFeatures = [f for f in loadableFeatures if f not in app.excludedFeatures]
        result = TF.load(useFeatures, add=True, silent=True)
        if result is False:
          app.api = None
    else:
      app.api = None

  if app.api:
    _addLinksApi(app, name, appName, silent)
    _addFormatApi(app, silent, hoist)
    _addMethods(app)
  else:
    if not asApp:
      console(
          f'''
There were problems with loading data.
The Text-Fabric API has not been loaded!
The app "{appName}" will not work!
''',
          error=True,
      )


# COLLECT CONFIG SETTINGS IN A DICT

def configureNames(names, lgc, version):
  '''
  Collect the all-uppercase globals from a config file
  and put them in a dict in camel case.
  '''
  org = names['ORG']
  repo = names['REPO']
  relative = names['RELATIVE']
  base = _hasData(lgc, org, repo, version, relative)

  if not base:
    base = EXPRESS_BASE

  localDir = os.path.expanduser(f'{base}/{org}/{repo}/_temp')

  result = {camel(key): value for (key, value) in names.items() if key == key.upper()}

  result.update(dict(
      localDir=localDir,
      version=version,
  ))

  return result


# GENERATE LINK TO A PASSAGE IN THE CORPUS IN AN EXTERNAL WEBSITE

def outLink(text, href, title=None, passage=None, className=None, target='_blank'):
  titleAtt = '' if title is None else f' title="{title}"'
  classAtt = f' class="{className}"' if className else ''
  targetAtt = f' target="{target}"' if target else ''
  passageAtt = f' sec="{passage}"' if passage else ''
  return f'<a{classAtt}{targetAtt} href="{href}"{titleAtt}{passageAtt}>{text}</a>'


# DOWNLOAD URL TO LIVE DATA ON GITHUB

def liveText(org, repo, version, release):
  return f'{org}/{repo} v:{version} (r{release})'


def liveUrl(org, repo, version, release, relative):
  relativeFlat = relative.replace('/', '-')
  return f'{URL_GH}/{org}/{repo}/releases/download/{release}/{relativeFlat}-{version}.zip'


# CHECK AND DOWNLOAD DATA FOR A GIVEN LOCATION

def getData(
    org,
    repo,
    relative,
    version,
    lgc,
    check,
    withPaths=False,
    keep=False,
    silent=False
):
  versionRep = f'/{version}' if version else ''
  versionRep2 = f' - {version}' if version else ''
  versionRep3 = f'-{version}' if version else ''
  relativeRep = f'/{relative}' if relative else ''
  dataRel = f'{org}/{repo}{relativeRep}'
  expressBase = os.path.expanduser(EXPRESS_BASE)
  expressTargetAll = f'{expressBase}/{dataRel}'
  expressTarget = f'{expressTargetAll}{versionRep}'
  expressInfoFile = f'{expressTarget}/{EXPRESS_INFO}'
  exTarget = f'{EXPRESS_BASE}/{dataRel}{versionRep}'
  ghBase = os.path.expanduser(GH_BASE)
  ghTarget = f'{GH_BASE}/{dataRel}{versionRep}'

  dataBase = _hasData(lgc, org, repo, version, relative)
  if dataBase == ghBase:
    if not silent:
      console(
          f'''
Using {repo}{versionRep2} local in {ghTarget}
'''
      )
    return (None, dataBase)

  currentRelease = None

  if dataBase == expressBase:
    if os.path.exists(expressInfoFile):
      with open(expressInfoFile) as eh:
        for line in eh:
          currentRelease = line.strip()
    if currentRelease and not check:
      if not silent:
        console(
            f'''
Using {org}/{repo}{versionRep2} r{currentRelease} in {exTarget}
'''
        )
      return (currentRelease, dataBase)

  urlLatest = f'{URL_GH_API}/{org}/{repo}/releases/latest'

  latestRelease = None
  assets = ()
  relativeFlat = relative.replace('/', '-')
  dataFile = f'{relativeFlat}{versionRep3}.zip'

  online = False
  try:
    r = requests.get(urlLatest, allow_redirects=True).json()
    online = True
  except Exception:
    console(
        f'''
Cannot check online for data releases. No results from:
    {urlLatest}
''',
        error=True,
    )
  if online:
    message = r.get('message', '').strip().replace(' ', '').lower()
    if message == 'notfound':
      console(
          f'''
Cannot find {org}/{repo} releases on GitHub by the url:
    {urlLatest}
''',
          error=True,
      )
      online = False
  if online:
    latestRelease = r.get('tag_name', None)
    assets = {a['name'] for a in r.get('assets', {})}
  if not latestRelease or not assets:
    online = False
  if online and dataFile not in assets:
    dataFiles = ', '.join(x[0:-4] if x.endswith('.zip') else x for x in sorted(assets))
    console(
        f'''
In {org}/{repo}: newest release is {latestRelease}
This release has no data file {dataFile}.
Available data files: {dataFiles}
''',
        error=True,
    )
    online = False
  if not online:
    if currentRelease:
      if not silent:
        console(
            f'''
Still Using {org}/{repo}{versionRep2} r{currentRelease} in {exTarget}
'''
        )
      return (currentRelease, expressBase)
    else:
        console(
            f'''
Could not find data in {org}/{repo}{versionRep2} in {exTarget}
''',
            error=True,
        )
    return (None, False)

  if latestRelease == currentRelease:
    if not silent:
      console(
          f'''
No new data release available online.
Using {repo}{versionRep2} r{currentRelease} (=latest) in {exTarget}.
'''
      )
    return (currentRelease, expressBase)

  if _getDataFile(
      org, repo, relative, latestRelease, version,
      keep=keep,
      withPaths=withPaths,
      silent=silent,
  ):
    if not silent:
      console(
          f'''
Using {org}/{repo}{versionRep2} r{latestRelease} (=latest) in {exTarget}
'''
      )
      return (latestRelease, expressBase)

  if currentRelease:
    if not silent:
      console(
          f'''
Still Using {org}/{repo}{versionRep2} r{currentRelease} in {exTarget}
'''
      )
    return (currentRelease, expressBase)

  console(
      f'''
No data for {org}/{repo}{versionRep2}
''',
      error=True,
  )
  return (None, False)


# GET DATA FOR MAIN SOURCE AND ALL MODULES

def _getModulesData(
    app,
    moduleRefs,
    locations, modules,
    version,
    lgc, check, silent,
):
  provenance = []
  mLocations = []

  # GET DATA for main dataset

  good = True
  seen = set()

  if not _getModuleData(
      app,
      app.org, app.repo, app.relative,
      version,
      lgc, check, silent,
      seen, mLocations, provenance,
      isBase=True,
  ):
    good = False

  # GET DATA for standard modules

  for m in (app.moduleSpecs or []):
    (org, repo, relative) = (m['org'], m['repo'], m['relative'])
    if not _getModuleData(
        app,
        org, repo, relative,
        version,
        lgc, check, silent,
        seen, mLocations, provenance,
        specs=m,
    ):
      good = False

  # GET DATA for modules on-the-fly modules

  for moduleRef in (moduleRefs.split(',') if moduleRefs else []):
    if moduleRef in seen:
      continue

    parts = moduleRef.split('/', 2)
    if len(parts) < 2:
      console(
          f'''
Module ref "{moduleRef}" is not "org/repo/path"
''',
          error=True,
      )
      good = False
      continue
    if len(parts) == 2:
      parts.append('')

    (org, repo, relative) = parts
    if not _getModuleData(
        app,
        org, repo, relative,
        version,
        lgc, check, silent,
        seen, mLocations, provenance,
    ):
      good = False

  if good:
    app.mLocations = mLocations
    app.provenance = provenance
  else:
    return None

  mModules = []
  if mLocations:
    mModules.append(version)

  givenLocations = itemize(locations, sep='\n')
  givenModules = itemize(modules, sep='\n')
  locations = mLocations + givenLocations
  modules = mModules + givenModules

  return (locations, modules)


# GET DATA FOR A SINGLE MODULE

def _getModuleData(
    app,
    org, repo, relative,
    version,
    lgc, check, silent,
    seen, mLocations, provenance,
    isBase=False,
    specs=None,
):
  moduleRef = f'{org}/{repo}/{relative}'
  if moduleRef in seen:
    return True

  (release, base) = getData(
      org,
      repo,
      relative,
      version,
      lgc,
      check,
      silent=silent,
  )
  if not base:
    return False

  seen.add(moduleRef)
  repoLocation = f'{base}/{org}/{repo}'
  mLocations.append(f'{repoLocation}/{relative}')
  if isBase:
    app.repoLocation = repoLocation

  info = {}
  for item in (
      ('doi', 'unknown DOI'),
      ('doiUrl', ''),
      ('corpus', f'{org}/{repo}/{relative}'),
  ):
    (key, default) = item
    info[key] = (
        getattr(app, key)
        if isBase else
        specs[key]
        if specs and key in specs else
        default
    )
  provenance.append(dict(
      corpus=info['corpus'],
      version=version,
      release=release,
      live=(
          liveText(org, repo, version, release),
          liveUrl(org, repo, version, release, relative)
      ),
      doi=(
          info['doi'],
          info['doiUrl']
      ),
  ))
  return True


# DOWNLOAD A SINGLE ZIP FILE

def _getDataFile(
    org,
    repo,
    relative,
    release,
    version,
    fileName=None,
    withPaths=False,
    keep=False,
    silent=False,
):
  expressBase = os.path.expanduser(EXPRESS_BASE)
  versionRep = '' if not version else f'/{version}'
  versionRep2 = '' if not version else f' - {version}'
  versionRep3 = '' if not version else f'-{version}'
  relativeRep = f'/{relative}' if relative else ''
  destBase = f'{expressBase}/{org}/{repo}'
  destInfoFile = f'{destBase}{relativeRep}{versionRep}'
  dest = (
      f'{destBase}{versionRep}'
      if withPaths else
      destInfoFile
  )
  if fileName is None:
    relativeFlat = relative.replace('/', '-')
    fileName = (
        f'{relativeFlat}{versionRep3}.zip'
        if version else
        f'{relativeFlat}.zip'
    )
  dataUrl = f'{URL_GH}/{org}/{repo}/releases/download/{release}/{fileName}'

  if not silent:
    console(
        f'''
\tdownloading {org}/{repo}{versionRep2} r{release}
\tfrom {dataUrl} ...
'''
    )
  try:
    r = requests.get(dataUrl, allow_redirects=True)
    if not silent:
      console(
          f'''
\tunzipping ...
'''
      )
    zf = io.BytesIO(r.content)
  except Exception as e:
    console(
        f'''
{str(e)}
\tcould not download {repo}{versionRep2} r{release} from {dataUrl} to {dest}
''',
        error=True,
    )
    return False

  if not silent:
    console(
        f'''
\tsaving {org}/{repo}{versionRep2} r{release}
'''
    )

  cwd = os.getcwd()
  try:
    z = ZipFile(zf)
    if not keep:
      if os.path.exists(dest):
        rmtree(dest)
    os.makedirs(dest, exist_ok=True)
    os.chdir(dest)
    if withPaths:
      z.extractall()
      if os.path.exists('__MACOSX'):
        rmtree('__MACOSX')
    else:
      for zInfo in z.infolist():
        if zInfo.filename[-1] == '/':
          continue
        if zInfo.filename.startswith('__MACOS'):
          continue
        zInfo.filename = os.path.basename(zInfo.filename)
        z.extract(zInfo)
  except Exception as e:
    console(
        f'''
{str(e)}
\tcould not save {org}/{repo}{versionRep2} r{release}
''',
        error=True,
    )
    os.chdir(cwd)
    return False

  expressInfoFile = f'{destInfoFile}/{EXPRESS_INFO}'
  with open(expressInfoFile, 'w') as rh:
    rh.write(f'{release}')
  if not silent:
    console(
        f'''
\tsaved {org}/{repo}{versionRep2} r{release}
'''
    )
  os.chdir(cwd)
  return True


# LOWER LEVEL API FUNCTIONS

def _addLinksApi(
    app,
    name,
    appName,
    silent,
):
    api = app.api
    app.inNb = False
    if not app.asApp:
      (inNb, repoLoc) = location(app.cwd, name)
      app.inNb = inNb
      if inNb:
        (nbDir, nbName, nbExt) = inNb
      if repoLoc:
        (nbOrg, nbRepo, nbRrelative, nbUrl, ghUrl) = repoLoc
    tutUrl = f'{URL_NB}/{app.org}/{app.repo}/blob/master/tutorial/search.ipynb'
    extraUrl = f'{URL_TFDOC}/Api/{app.repo.capitalize()}/'
    dataLink = outLink(
        app.repo.upper(),
        app.docUrl,
        f'provenance of {app.corpus}',
    )
    charLink = (
        outLink(
            'Character table',
            app.charUrl.format(tfDoc=URL_TFDOC),
            app.charText,
        )
        if app.charUrl else
        ''
    )
    featureLink = outLink(
        'Feature docs', app.featureUrl.format(
            version=app.version,
            feature=app.docIntro,
        ),
        f'{app.repo.upper()} feature documentation'
    )
    appLink = outLink(f'{appName} API', extraUrl, f'{appName} API documentation')
    tfLink = outLink(
        f'Text-Fabric API {api.TF.version}', f'{URL_TFDOC}/Api/General/',
        'text-fabric-api'
    )
    tfsLink = outLink(
        'Search Reference',
        f'{URL_TFDOC}/Api/General/#search-templates',
        'Search Templates Introduction and Reference'
    )
    tutLink = outLink(
        'Search tutorial', tutUrl,
        'Search tutorial in Jupyter Notebook'
    )
    if app.asApp:
      app.dataLink = dataLink
      app.charLink = charLink
      app.featureLink = featureLink
      app.tfsLink = tfsLink
      app.tutLink = tutLink
    else:
      if inNb is not None:
        if not silent:
          dm(
              '**Documentation:**'
              f' {dataLink} {charLink} {featureLink} {appLink} {tfLink} {tfsLink}'
          )
          dh(
              '<details open><summary><b>Loaded features</b>:</summary>\n'
              + _featuresPerModule(app)
              + '</details>'
          )
          if repoLoc:
            dm(
                f'''
This notebook online:
{outLink('NBViewer', f'{nbUrl}/{nbName}{nbExt}')}
{outLink('GitHub', f'{ghUrl}/{nbName}{nbExt}')}
'''
            )


def _addFormatApi(
    app,
    silent,
    hoist,
):
  api = app.api
  inNb = app.inNb
  if app.classNames is None:
    app.classNames = {nType[0]: nType[0] for nType in api.C.levels.data}
  app.prettyFeaturesLoaded = {f for f in app.standardFeatures}
  app.prettyFeatures = ()
  _compileFormatClass(app)

  if not app.asApp:
    if inNb is not None:
      _loadCss(app)
    if hoist:
      docs = api.makeAvailableIn(hoist)
      if inNb is not None:
        if not silent:
          dh(
              '<details open><summary><b>API members</b>:</summary>\n'
              + '<br/>\n'.join(
                  ', '.join(
                      outLink(
                          entry,
                          f'{URL_TFDOC}/Api/General/#{ref}',
                          title='doc',
                      )
                      for entry in entries
                  )
                  for (ref, entries) in docs
              )
              + '</details>'
          )


def _addMethods(app):
  app.table = types.MethodType(table, app)
  app.plainTuple = types.MethodType(plainTuple, app)
  app.show = types.MethodType(show, app)
  app.prettyTuple = types.MethodType(prettyTuple, app)
  app.pretty = types.MethodType(pretty, app)
  app.prettySetup = types.MethodType(prettySetup, app)
  app.search = types.MethodType(search, app)
  app.header = types.MethodType(header, app)
  app.nodeFromDefaultSection = types.MethodType(nodeFromDefaultSection, app)
  app.sectionLink = types.MethodType(_sectionLink, app)
  app.loadCss = types.MethodType(_loadCss, app)


# LOWER LEVEL UTILITY FUNCTIONS

def _sectionLink(app, n, text=None):
  return app.webLink(n, className='rwh', text=text, asString=True, noUrl=True)


def _loadCss(app):
  '''
  The CSS is looked up and then loades into a notebook if we are not
  running in the TF browser,
  else the CSS is returned.
  '''
  asApp = app.asApp
  if asApp:
    return CSS_FONT + app.css
  cssFont = (
      '' if app.fontName is None else
      CSS_FONT_API.format(
          fontName=app.fontName,
          font=app.font,
          fontw=app.fontw,
      )
  )
  dh(cssFont + app.css)


def _deLang(languages, features):
  '''
  features is a set of feature names that may contain names of shape

    {name}@{ll}

  where {ll} is a language.

  We want to replace the set of {name}@{ll} for {ll} in T.languages
  by a single name

    {name}@ll

  so, the literal string 'll'

  This is used when generating links to feature docs,
  where we want to generate one link to a language dependent feature.
  '''
  results = set()
  for f in features:
    parts = f.rsplit('@', 1)
    if len(parts) == 1:
      results.add(f)
    else:
      (fx, ll) = parts
      if ll in languages:
        results.add(fx)
        results.add(f'{fx}@ll')
  return sorted(results)


pathPat = re.compile(
    r'^(.*/(?:github|text-fabric-data))/([^/]+)/([^/]+)/(.*)$',
    flags=re.I
)


def _featuresPerModule(app):
  api = app.api
  features = api.Fall() + api.Eall()
  languages = api.T.languages

  fixedModuleIndex = {}
  for m in app.moduleSpecs:
    fixedModuleIndex[(m['org'], m['repo'], m['relative'])] = m['corpus']

  moduleIndex = {}
  mLocations = app.mLocations
  baseLoc = mLocations[0]

  for mLoc in mLocations:
    match = pathPat.fullmatch(mLoc)
    if not match:
      console(f'Strange module location "{mLoc}"', error=True)
      continue
    (base, org, repo, relative) = match.groups()
    mId = (org, repo, relative)
    corpus = (
        app.corpus
        if mLoc == baseLoc else
        fixedModuleIndex[mId] if mId in fixedModuleIndex else
        f'{org}/{repo}/{relative}'
    )
    moduleIndex[mLoc] = (org, repo, relative, corpus)

  featureCat = {}

  for feature in features:
    featurePath = app.api.TF.features[feature].path
    for mLoc in mLocations:
      if featurePath.startswith(mLoc):
        featureCat.setdefault(mLoc, []).append(feature)

  featureLangCat = {
      mLoc: _deLang(languages, catFeats) for (mLoc, catFeats) in featureCat.items()
  }

  html = ''
  for mLoc in mLocations:
    catFeats = featureLangCat.get(mLoc, None)
    if not catFeats:
      continue
    modInfo = moduleIndex.get(mLoc, None)
    if modInfo:
      (org, repo, relative, corpus) = modInfo
      url = (
          app.featureUrl.format(version=app.version, feature=feature)
          if mLoc == baseLoc else
          f'{URL_GH}/{org}/{repo}/tree/master/{relative}'
      )
      html += (
          f'<p><b>{corpus}</b>: '
          + ' '.join(
              outLink(feature, url, title='info')
              for feature in catFeats
          )
          + '</p>'
      )
  return html


def _compileFormatClass(app):
  result = {None: app.defaultClsOrig}
  formats = app.api.T.formats
  for fmt in formats:
    for (key, cls) in app.formatCss.items():
      if f'-{key}-' in fmt:
        result[fmt] = cls
  for fmt in formats:
    if fmt not in result:
      result[fmt] = app.defaultCls
  app.formatClass = result


def _hasData(lgc, org, repo, version, relative):
  versionRep = f'/{version}' if version else ''
  if lgc:
    ghBase = os.path.expanduser(GH_BASE)
    ghTarget = f'{ghBase}/{org}/{repo}/{relative}{versionRep}'
    if os.path.exists(ghTarget):
      return ghBase

  expressBase = os.path.expanduser(EXPRESS_BASE)
  expressTarget = f'{expressBase}/{org}/{repo}/{relative}{versionRep}'
  if os.path.exists(expressTarget):
    return expressBase
  return False
