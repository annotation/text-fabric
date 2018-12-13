import os
import io
from shutil import rmtree
import requests
from zipfile import ZipFile

from ..parameters import (
    URL_GH_API,
    URL_GH,
    GH_BASE,
    EXPRESS_BASE,
    EXPRESS_INFO,
)

from ..core.helpers import itemize, console, splitModRef, expandDir
from .helpers import hasData
from .links import liveText, liveUrl


def getData(org, repo, relative, version, lgc, check, withPaths=False, keep=False, silent=False):
  versionRep = f'/{version}' if version else ''
  versionRep2 = f' - {version}' if version else ''
  versionRep3 = f'-{version}' if version else ''
  relativeRep = f'/{relative}' if relative else ''
  dataRel = f'{org}/{repo}{relativeRep}'
  expressBase = os.path.expanduser(EXPRESS_BASE)
  expressTargetAll = f'{expressBase}/{dataRel}'
  expressTarget = f'{expressTargetAll}{versionRep}'
  expressInfoFile = f'{expressTarget}/{EXPRESS_INFO}'
  ghBase = os.path.expanduser(GH_BASE)

  dataBase = hasData(lgc, org, repo, version, relative)
  if dataBase == ghBase:
    if not silent:
      console(f'''
Using {org}/{repo}{relativeRep}{versionRep2} in {ghBase}
''')
    return (None, dataBase)

  currentRelease = None

  if dataBase == expressBase:
    if os.path.exists(expressInfoFile):
      with open(expressInfoFile) as eh:
        for line in eh:
          currentRelease = line.strip()
    if not check:
      currentReleaseRep = currentRelease if currentRelease else '??'
      if not silent or not currentRelease:
        console(
            f'''
Using {org}/{repo}{relativeRep}{versionRep2} r{currentReleaseRep} in {expressBase}
'''
        )
      return (currentReleaseRep, dataBase)

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
        error=not check,
    )
    online = False
  if online:
    message = r.get('message', '').strip().replace(' ', '').lower()
    if message == 'notfound':
      console(
          f'''
Cannot find {org}/{repo} releases on GitHub by the url:
    {urlLatest}
''',
          error=not check,
      )
      online = False
  if online:
    latestRelease = r.get('tag_name', None)
    assets = {a['name'] for a in r.get('assets', {})}
  if not latestRelease:
    console(
        f'''
Cannot find out what the latest release of {org}/{repo} on GitHub is:
    {urlLatest}
''',
        error=not check,
    )
    online = False
  if not assets:
    console(
        f'''
The latest release {latestRelease} of {org}/{repo} on GitHub is {latestRelease}.
But it does not have manually added attachments.
Use
  text-fabric-zip {org}/{repo}/{relative}
to create zip files in your Downloads/{org}-releases folder.
Then upload and attach them to this release manually.
''',
        error=not check,
    )
    online = False
  if online and dataFile not in assets:
    dataFiles = ', '.join(x[0:-4] if x.endswith('.zip') else x for x in sorted(assets))
    console(
        f'''
In {org}/{repo}: newest release is {latestRelease}
This release has no data file {dataFile}.
Available data files: {dataFiles}
''',
        error=not check,
    )
    online = False
  if not online:
    currentReleaseRep = currentRelease if currentRelease else '??'
    if check:
      if not silent or not currentRelease:
        console(
            f'''
Still Using {org}/{repo}{relativeRep}{versionRep2} r{currentReleaseRep} in {expressBase}
'''
        )
      return (currentRelease, expressBase)
    else:
      console(
          f'''
Could not find data in {org}/{repo}{relativeRep}{versionRep2} in {expressBase}
''',
          error=not check,
      )
    return (None, False)

  if latestRelease == currentRelease:
    if not silent:
      console(
          f'''
No new data release available online.
Using {org}/{repo}{relativeRep}{versionRep2} r{currentRelease} (=latest) in {expressBase}.
'''
      )
    return (currentRelease, expressBase)

  if _getDataFile(
      org,
      repo,
      relative,
      latestRelease,
      version,
      keep=keep,
      withPaths=withPaths,
      silent=silent,
  ):
    if not silent:
      console(
          f'''
Using {org}/{repo}{relativeRep}{versionRep2} r{latestRelease} (=latest) in {expressBase}
'''
      )
      return (latestRelease, expressBase)

  if currentRelease:
    if not silent:
      console(
          f'''
Still Using {org}/{repo}{relativeRep}{versionRep2} r{currentRelease} in {expressBase}
'''
      )
    return (currentRelease, expressBase)

  console(
      f'''
No data for {org}/{repo}{relativeRep}{versionRep2}
''',
      error=True,
  )
  return (None, False)


# GET DATA FOR MAIN SOURCE AND ALL MODULES


def getModulesData(
    app,
    moduleRefs,
    locations,
    modules,
    version,
    lgc,
    check,
    silent,
):
  provenance = []
  mLocations = []

  # GET DATA for main dataset

  good = True
  seen = set()

  if not _getModuleData(
      app,
      app.org,
      app.repo,
      app.relative,
      version,
      lgc,
      check,
      silent,
      seen,
      mLocations,
      provenance,
      isBase=True,
  ):
    good = False

  # GET DATA for standard modules

  for m in (app.moduleSpecs or []):
    (org, repo, relative) = (m['org'], m['repo'], m['relative'])
    if not _getModuleData(
        app,
        org,
        repo,
        relative,
        version,
        lgc,
        check,
        silent,
        seen,
        mLocations,
        provenance,
        specs=m,
    ):
      good = False

  # GET DATA for modules on-the-fly modules

  for moduleRef in (moduleRefs.split(',') if moduleRefs else []):
    if moduleRef in seen:
      continue

    parts = splitModRef(moduleRef)
    if not parts:
      good = False
      continue

    (org, repo, relative) = parts

    if not _getModuleData(
        app,
        org,
        repo,
        relative,
        version,
        lgc,
        check,
        silent,
        seen,
        mLocations,
        provenance,
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

  givenLocations = ([] if locations is None else
                    [expandDir(app, x.strip())
                     for x in itemize(locations, '\n')] if type(locations) is str else locations)
  givenModules = ([] if modules is None else
                  [x.strip() for x in itemize(modules, '\n')] if type(modules) is str else modules)

  locations = mLocations + givenLocations
  modules = mModules + givenModules

  return (locations, modules)


# GET DATA FOR A SINGLE MODULE


def _getModuleData(
    app,
    org,
    repo,
    relative,
    version,
    lgc,
    check,
    silent,
    seen,
    mLocations,
    provenance,
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
      ('doiText', 'unknown DOI'),
      ('doiUrl', ''),
      ('corpus', f'{org}/{repo}/{relative}'),
  ):
    (key, default) = item
    info[key] = (getattr(app, key) if isBase else specs[key] if specs and key in specs else default)
  provenance.append(
      (
          ('corpus', info['corpus']),
          ('version', version),
          ('release', release),
          ('live', (
              liveText(org, repo, version, release),
              liveUrl(org, repo, version, release, relative)
          )),
          ('doi', (info['doiText'], info['doiUrl'])),
      )
  )
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
  dest = (f'{destBase}{versionRep}' if withPaths else destInfoFile)
  if fileName is None:
    relativeFlat = relative.replace('/', '-')
    fileName = (f'{relativeFlat}{versionRep3}.zip' if version else f'{relativeFlat}.zip')
  dataUrl = f'{URL_GH}/{org}/{repo}/releases/download/{release}/{fileName}'

  if not silent:
    console(f'''
\tdownloading {org}/{repo}{versionRep2} r{release}
\tfrom {dataUrl} ...
''')
  try:
    r = requests.get(dataUrl, allow_redirects=True)
    if not silent:
      console(f'''
\tunzipping ...
''')
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
    console(f'''
\tsaving {org}/{repo}{versionRep2} r{release}
''')

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
    console(f'''
\tsaved {org}/{repo}{versionRep2} r{release}
''')
  os.chdir(cwd)
  return True
