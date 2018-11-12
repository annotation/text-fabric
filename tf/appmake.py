import sys
import os
import io
import types
from glob import glob
from shutil import rmtree
import requests
from zipfile import ZipFile

from tf.helpers import itemize, camel
from tf.apphelpers import (
    search,
    table, plainTuple,
    show, pretty, prettyTuple, prettySetup,
    nodeFromDefaultSection,
    dm, dh, header,
    CSS_FONT_API,
)
from tf.server.common import getConfig
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
  ).items():
    setattr(app, key, value)

  config = getConfig(appName)
  cfg = config.configure(lgc=lgc, version=version)
  for (key, value) in cfg.items():
    setattr(app, key, value)

  app.cwd = os.getcwd()

  if not app.api:
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
        useFeatures = [f for f in loadableFeatures if f not in app.excludedFeatures]
        result = TF.load(useFeatures, add=True, silent=True)
        if result is False:
          app.api = None
  else:
    app.api.TF.load(app.standardFeatures, add=True, silent=True)

  if app.api:
    _addLinksApi(app, name, appName, silent)
    _addFormatApi(app, silent, hoist)
    _addMethods(app)


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


# DOWNLOAD A SINGLE ZIP FILE

def getDataFile(
    org,
    repo,
    relative,
    release,
    version,
    dest,
    fileName=None,
    withPaths=False,
    silent=False,
    keep=False,
):
  versionDest = f'{dest}/{version}' if version else dest
  if fileName is None:
    relativeFlat = relative.replace('/', '-')
    fileName = (
        f'{relativeFlat}-{version}.zip'
        if version else
        f'{relativeFlat}.zip'
    )
  dataUrl = f'{URL_GH}/{org}/{repo}/releases/download/{release}/{fileName}'

  if not silent:
    print(f'\tdownloading {org}/{repo} - {version} r{release}')
    print(f'\tfrom {dataUrl} ... ')
    sys.stdout.flush()
  try:
    r = requests.get(dataUrl, allow_redirects=True)
    if not silent:
      print(f'\tunzipping ... ')
    zf = io.BytesIO(r.content)
  except Exception as e:
    print(str(e))
    print(f'\tcould not download {repo}-{version} r{release} from {dataUrl} to {versionDest}')
    sys.stdout.flush()
    return False

  if not silent:
    print(f'\tsaving {org}/{repo} - {version} r{release}')
    sys.stdout.flush()

  cwd = os.getcwd()
  try:
    z = ZipFile(zf)
    if not keep:
      if os.path.exists(versionDest):
        rmtree(versionDest)
    os.makedirs(versionDest, exist_ok=True)
    os.chdir(versionDest)
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
    print(str(e))
    print(f'\tcould not save {org}/{repo} - {version} r{release}')
    sys.stdout.flush()
    os.chdir(cwd)
    return False

  expressInfoFile = f'{versionDest}/{EXPRESS_INFO}'
  with open(expressInfoFile, 'w') as rh:
    rh.write(f'{release}')
  if not silent:
    print(f'\tsaved {org}/{repo} - {version} r{release}')
    sys.stdout.flush()
  os.chdir(cwd)
  return True


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

  for moduleRef in (moduleRefs or []):
    if moduleRef in seen:
      continue

    parts = moduleRef.split('/', 2)
    if len(parts) != 2:
      print('Module ref "{moduleRef}" is not "org/repo/path"')
      good = False
      continue

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

  (release, base) = _getData(
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
  mLocations.append(f'{base}/{org}/{repo}/{relative}')

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


# CHECK AND DOWNLOAD DATA FOR A SINGLE MODULE

def _getData(
    org,
    repo,
    relative,
    version,
    lgc,
    check,
    silent=False
):
  dataRel = f'{org}/{repo}/{relative}'
  expressBase = os.path.expanduser(EXPRESS_BASE)
  expressTfAll = f'{expressBase}/{dataRel}'
  expressTf = f'{expressTfAll}/{version}'
  expressInfoFile = f'{expressTf}/{EXPRESS_INFO}'
  exTf = f'{EXPRESS_BASE}/{dataRel}/{version}'
  ghBase = os.path.expanduser(GH_BASE)
  ghTf = f'{GH_BASE}/{dataRel}/{version}'

  dataBase = _hasData(lgc, org, repo, version, relative)
  if dataBase == ghBase:
    if not silent:
      print(f'Using {repo}-{version} local in {ghTf}')
      sys.stdout.flush()
    return (None, dataBase)

  currentRelease = None

  if dataBase == expressBase:
    if os.path.exists(expressInfoFile):
      with open(expressInfoFile) as eh:
        for line in eh:
          currentRelease = line.strip()
    if currentRelease and not check:
      if not silent:
        print(f'Using {org}/{repo} - {version} r{currentRelease} in {exTf}')
        sys.stdout.flush()
      return (currentRelease, dataBase)

  urlLatest = f'{URL_GH_API}/{org}/{repo}/releases/latest'

  latestRelease = None
  assets = ()
  relativeFlat = relative.replace('/', '-')
  dataFile = f'{relativeFlat}-{version}.zip'

  online = False
  try:
    r = requests.get(urlLatest, allow_redirects=True).json()
    online = True
  except Exception:
    print('Cannot check online for data releases. No results from:')
    print(f'   {urlLatest}')
  if online:
    latestRelease = r.get('tag_name', None)
    assets = {a['name'] for a in r.get('assets', {})}
  if not latestRelease or not assets:
    online = False
  if online and dataFile not in assets:
    versions = ', '.join(x[0:-4] if x.endswith('.zip') else x for x in sorted(assets))
    print(
        f'In {org}/{repo}: newest release is {latestRelease}\n'
        f'This release has no data for version {version}.\n'
        f'Available versions: {versions}'
    )
    online = False
  if not online:
    if currentRelease:
      if not silent:
        print(f'Still Using {org}/{repo} - {version} r{currentRelease} in {exTf}')
        sys.stdout.flush()
      return (currentRelease, expressBase)
    else:
        print(f'Could not find data in {repo}-{version} r{latestRelease} in {exTf}')
        sys.stdout.flush()
    return (None, False)

  if latestRelease == currentRelease:
    if not silent:
      print(
          f'No new data release available online\n'
          f'Using {repo} - {version} r{currentRelease} (=latest) in {exTf}'
      )
      sys.stdout.flush()
    return (currentRelease, expressBase)

  if getDataFile(
      org, repo, relative, latestRelease, version, expressTfAll, silent=silent
  ):
    if not silent:
      print(f'Using {org}/{repo} - {version} r{latestRelease} (=latest) in {exTf}')
      return (latestRelease, expressBase)

  if currentRelease:
    if not silent:
      print(f'Still Using {org}/{repo} - {version} r{currentRelease} in {exTf}')
      sys.stdout.flush()
    return (currentRelease, expressBase)

  print(f'No data for {org}/{repo} - {version}')
  sys.stdout.flush()
  return (None, False)


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
        (app.org, app.repo, app.relative, nbUrl, ghUrl) = repoLoc
    tutUrl = f'{URL_NB}/{app.org}/{app.repo}/blob/master/tutorial/search.ipynb'
    extraUrl = f'{URL_TFDOC}/Api/{app.repo.capitalize()}/'
    dataLink = outLink(
        app.repo.upper(),
        app.docUrl,
        'provenance of this corpus',
    )
    charLink = (
        outLink(
            'Character table',
            f'{URL_TFDOC}/{app.charUrl}',
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
        languages = api.T.languages
        deLangFeatures = (
            _deLang(languages, api.Fall())
            + _deLang(languages, api.Eall())
        )
        if not silent:
          dm(
              '**Documentation:**'
              f' {dataLink} {charLink} {featureLink} {appLink} {tfLink} {tfsLink}'
          )
          dh(
              '<details open><summary><b>Loaded features</b>:</summary>\n'
              + ' '.join(
                  outLink(
                      feature,
                      app.featureUrl.format(
                          version=app.version,
                          feature=feature,
                      ),
                      title='info',
                  )
                  for feature in deLangFeatures
              )
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
    return app.cssFont + app.css
  dh(CSS_FONT_API.format(
      fontName=app.fontName,
      font=app.font,
      fontw=app.fontw,
  ) + app.css)


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
  if lgc:
    ghBase = os.path.expanduser(GH_BASE)
    ghTf = f'{ghBase}/{org}/{repo}/{relative}/{version}'
    features = glob(f'{ghTf}/*.tf')
    if len(features):
      return ghBase

  expressBase = os.path.expanduser(EXPRESS_BASE)
  expressTf = f'{expressBase}/{org}/{repo}/{relative}/{version}'
  features = glob(f'{expressTf}/*.tf')
  if len(features):
    return expressBase
  return False
