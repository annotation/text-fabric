import sys
import os
import io
from shutil import rmtree
import requests
from zipfile import ZipFile

from importlib import util

from ..parameters import (
    ORG,
    APP_EXPRESS, APP_GITHUB, APP_CODE, APP_INFO,
    URL_GH_API,
)
from ..core.helpers import console


def findApp(dataSource, lgc, check, silent=False):
  (onGH, appDir, xAppDir) = hasApp(dataSource, lgc)
  if onGH:
    if not silent:
      console(f'''
Using TF app {dataSource} in {appDir}
''')
    return (None, appDir)

  currentCommit = None

  expressInfoFile = f'{appDir}/{APP_INFO}'

  if not onGH:
    if appDir is not None:
      if os.path.exists(expressInfoFile):
        with open(expressInfoFile) as eh:
          for line in eh:
            currentCommit = line.strip()
      if not check:
        currentCommitRep = currentCommit if currentCommit else '??'
        if not silent or not currentCommit:
          console(
              f'''
Using {dataSource} commit {currentCommitRep}
  in {appDir}
'''
          )

        return (currentCommit, appDir)

  urlLatest = f'{URL_GH_API}/{ORG}/app-{dataSource}/commits/master'

  latestCommit = None

  online = False
  try:
    r = requests.get(urlLatest, allow_redirects=True).json()
    online = True
  except Exception:
    console(
        f'''
Cannot check online for commits. No results from:
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
Cannot find app-{dataSource} commits on GitHub by the url:
    {urlLatest}
''',
          error=not check,
      )
      online = False
  if online:
    latestCommit = r.get('sha', None)

  if not latestCommit:
    console(
        f'''
Cannot find out what the latest commit of {ORG}/app-{dataSource} on GitHub is:
    {urlLatest}
''',
        error=not check,
    )
    online = False

  if not online:
    currentCommitRep = currentCommit if currentCommit else '??'
    if check:
      if not silent or not currentCommit:
        console(
            f'''
Still Using {ORG}/app-{dataSource} commit {currentCommitRep}
  in {appDir}
'''
        )
      return (currentCommit, appDir)
    else:
      console(
          f'''
Could not find data in {ORG}/app-{dataSource}
  in {appDir}
''',
          error=not check,
      )
    return (None, False)

  if latestCommit == currentCommit:
    if not silent:
      console(
          f'''
App is up-to-date.
Using {ORG}/app-{dataSource} commit {currentCommit} (=latest)
  in {appDir}.
'''
      )
    return (currentCommit, appDir)

  if appDir is None:
    appDir = xAppDir

  if _getAppFile(
      dataSource,
      latestCommit,
      appDir,
      silent=silent,
  ):
    if not silent:
      console(
          f'''
Using {ORG}/app-{dataSource} commit {latestCommit} (=latest)
  in {appDir}
'''
      )
      return (latestCommit, appDir)

  if currentCommit:
    if not silent:
      console(
          f'''
Still Using {ORG}/app-{dataSource} commit {currentCommit}
  in {appDir}
'''
      )
    return (currentCommit, appDir)

  console(
      f'''
No TF app {ORG}/app-{dataSource}
''',
      error=True,
  )
  return (None, False)


def findAppConfig(dataSource, appDir):
  config = None
  appPath = f'{appDir}/config.py'

  try:
    spec = util.spec_from_file_location(f'tf.apps.{dataSource}.config', appPath)
    config = util.module_from_spec(spec)
    spec.loader.exec_module(config)
  except Exception as e:
    console(f'findAppConfig: {str(e)}', error=True)
    console(f'findAppConfig: Configuration for "{dataSource}" not found', error=True)
  return config


def findAppClass(dataSource, appDir):
  appClass = None
  moduleName = f'tf.apps.{dataSource}.app'

  try:
    spec = util.spec_from_file_location(
        moduleName,
        f'{appDir}/app.py',
    )
    code = util.module_from_spec(spec)
    sys.path.insert(0, appDir)
    spec.loader.exec_module(code)
    sys.path.pop(0)
    appClass = code.TfApp
  except Exception as e:
    console(f'findAppClass: {str(e)}', error=True)
    console(f'findAppClass: Api for "{dataSource}" not found')
  return appClass


def hasApp(dataSource, lgc):
  if lgc:
    ghBase = os.path.expanduser(APP_GITHUB)
    ghTarget = f'{ghBase}/app-{dataSource}/{APP_CODE}'
    if os.path.exists(ghTarget):
      return (True, ghTarget, None)

  expressBase = os.path.expanduser(APP_EXPRESS)
  expressTarget = f'{expressBase}/{dataSource}'
  if os.path.exists(expressTarget):
    return (False, expressTarget, None)
  return (False, None, expressTarget)


def _getAppFile(dataSource, commit, appDir, silent=False):
  appUrl = f'{URL_GH_API}/{ORG}/app-{dataSource}/zipball'

  if not silent:
    console(f'''
\tdownloading latest {ORG}/app-{dataSource}
\tfrom {appUrl} ...
''')
  try:
    r = requests.get(appUrl, allow_redirects=True)
    if not silent:
      console(f'''
\tunzipping ...
''')
    zf = io.BytesIO(r.content)
  except Exception as e:
    console(
        f'''
{str(e)}
\tcould not download latest app-{dataSource} from {appUrl}
  to {appDir}
''',
        error=True,
    )
    return False

  if not silent:
    console(f'''
\tsaving {ORG}/app-{dataSource} commit {commit}
''')

  cwd = os.getcwd()
  try:
    z = ZipFile(zf)
    if os.path.exists(appDir):
      rmtree(appDir)
    os.makedirs(appDir, exist_ok=True)
    os.chdir(appDir)
    prefix1 = f'{ORG}-app-{dataSource}-'
    lPrefix1 = len(prefix1)
    prefix2 = 'code/'
    lPrefix2 = len(prefix2)
    for zInfo in z.infolist():
      fileName = zInfo.filename
      if fileName.startswith(prefix1):
        fileName = fileName[lPrefix1:]
        skip = fileName.find('/')
        if skip >= 0:
          fileName = fileName[skip + 1:]
          if fileName.startswith(prefix2):
            fileName = fileName[lPrefix2:]
            if fileName:
              zInfo.filename = fileName
              z.extract(zInfo)
  except Exception as e:
    console(
        f'''
{str(e)}
\tcould not save {ORG}/app-{dataSource}  commit {commit}
''',
        error=True,
    )
    os.chdir(cwd)
    return False

  expressInfoFile = f'{appDir}/{APP_INFO}'
  with open(expressInfoFile, 'w') as rh:
    rh.write(f'{commit}')
  if not silent:
    console(f'''
\tsaved {ORG}/app-{dataSource} commit {commit}
''')
  os.chdir(cwd)
  return True
