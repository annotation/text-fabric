from ..core.helpers import itemize, splitModRef, expandDir
from .repo import RepoData
from .links import liveText, liveUrl


def getData(
    app,
    org,
    repo,
    relative,
    version,
    checkoutData,
    lgc,
    check,
    commit=None,
    withPaths=False,
    keep=False,
    silent=False,
):
  rData = RepoData(
      org,
      repo,
      relative,
      checkoutData,
      lgc,
      check,
      keep,
      withPaths,
      silent,
      version=version,
  )
  rData.makeSureLocal()
  base = rData.base
  return (rData.commitOff, rData.releaseOff, base) if base else (None, None, False)


# GET DATA FOR MAIN SOURCE AND ALL MODULES

def getModulesData(
    app,
    moduleRefs,
    locations,
    modules,
    version,
    checkoutData,
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
      checkoutData,
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
    (org, repo, relative, thisCheckoutData) = (
        m['org'],
        m['repo'],
        m['relative'],
        m.get('checkoutData', ''),
    )
    if not _getModuleData(
        app,
        org,
        repo,
        relative,
        version,
        thisCheckoutData,
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

    (org, repo, relative, thisCheckoutData) = parts

    if not _getModuleData(
        app,
        org,
        repo,
        relative,
        version,
        thisCheckoutData,
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
    checkoutData,
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

  (commit, release, base) = getData(
      app,
      org,
      repo,
      relative,
      version,
      checkoutData,
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
          ('commit', commit or '??'),
          ('release', release or 'none'),
          ('live', (
              liveText(org, repo, version, commit, release),
              liveUrl(org, repo, version, commit, release, relative)
          )),
          ('doi', (info['doiText'], info['doiUrl'])),
      )
  )
  return True
