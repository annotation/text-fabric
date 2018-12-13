import os
import requests

from importlib import util

from ..parameters import (
    ORG,
    APP_EXPRESS, APP_GITHUB, APP_INFO,
    URL_GH_API,
)
from ..core.helpers import console


def findApp(dataSource, lgc, check, silent=False):
  (onGH, appDir) = hasApp(lgc)
  if onGH:
    if not silent:
      console(f'''
Using TF app {dataSource} in {appDir}
''')
    return (None, appDir)

  currentCommit = None

  if appDir:
    expressInfoFile = f'{appDir}/{APP_INFO}'

  if not onGH:
    if os.path.exists(expressInfoFile):
      with open(expressInfoFile) as eh:
        for line in eh:
          currentCommit = line.strip()
    if not check:
      currentCommitRep = currentCommit if currentCommit else '??'
      if not silent or not currentCommit:
        console(
            f'''
Using {dataSource} commit {currentCommitRep} in {appDir}
'''
        )

      return (currentCommitRep, appDir)

  urlLatest = f'{URL_GH_API}/{ORG}/app-{dataSource}/git/commits/master'

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
    latestCommit = r.get('tag_name', None)
    assets = {a['name'] for a in r.get('assets', {})}
  if not latestCommit:
    console(
        f'''
Cannot find out what the latest commit of {ORG}/app-{dataSource} on GitHub is:
    {urlLatest}
''',
        error=not check,
    )
    online = False
  if not assets:
    console(
        f'''
The latest commit {latestCommit} of {ORG}/app-{dataSource} on GitHub is {latestCommit}.
But it does not have manually added attachments.
Use
  text-fabric-zip org/repo/relative
to create zip files in your Downloads/org-commits folder.
Then upload and attach them to this commit manually.
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
Still Using {ORG}/app-{dataSource} commit {currentCommitRep} in {appDir}
'''
        )
      return (currentCommit, appDir)
    else:
      console(
          f'''
Could not find data in {ORG}/app-{dataSource} in {appDir}
''',
          error=not check,
      )
    return (None, False)

  return (False, appDir)


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
  appPath = f'{appDir}/app.py'

  try:
    spec = util.spec_from_file_location(f'tf.apps.{dataSource}.app', appPath)
    code = util.module_from_spec(spec)
    spec.loader.exec_module(code)
    appClass = code.TfApp
  except Exception as e:
    console(f'findAppClass: {str(e)}', error=True)
    console(f'findAppClass: Api for "{dataSource}" not found')
  return appClass


def hasApp(dataSource, lgc):
  if lgc:
    ghBase = os.path.expanduser(APP_GITHUB)
    ghTarget = f'{ghBase}/app-{dataSource}'
    if os.path.exists(ghTarget):
      return (True, ghTarget)

  expressBase = os.path.expanduser(APP_EXPRESS)
  expressTarget = f'{expressBase}/__apps_/{dataSource}'
  if os.path.exists(expressTarget):
    return (False, expressTarget)
  return (False, None)
