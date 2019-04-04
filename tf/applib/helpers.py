import os

from IPython.display import display, Markdown, HTML

from ..parameters import EXPRESS_BASE, GH_BASE
from ..core.helpers import camel


RESULT = 'result'


def dm(md):
  display(Markdown(md))


def dh(html):
  display(HTML(html))


# COLLECT CONFIG SETTINGS IN A DICT

def configureNames(names, myDir):
  '''
  Collect the all-uppercase globals from a config file
  and put them in a dict in camel case.
  '''
  result = {camel(key): value for (key, value) in names.items() if key == key.upper()}

  with open(f'{myDir}/static/display.css') as fh:
    result['css'] = fh.read()

  return result


def configure(config, version):
  (names, path) = config.deliver()
  result = configureNames(names, path)
  result['version'] = config.VERSION if version is None else version
  return result


def getLocalDir(names, local, version):
  org = names['org']
  repo = names['repo']
  relative = names['relative']
  version = names['version'] if version is None else version
  base = hasData(local, org, repo, version, relative)

  if not base:
    base = EXPRESS_BASE

  return os.path.expanduser(f'{base}/{org}/{repo}/_temp')


def hasData(local, org, repo, version, relative):
  versionRep = f'/{version}' if version else ''
  if local == 'clone':
    ghBase = os.path.expanduser(GH_BASE)
    ghTarget = f'{ghBase}/{org}/{repo}/{relative}{versionRep}'
    if os.path.exists(ghTarget):
      return ghBase

  expressBase = os.path.expanduser(EXPRESS_BASE)
  expressTarget = f'{expressBase}/{org}/{repo}/{relative}{versionRep}'
  if os.path.exists(expressTarget):
    return expressBase
  return False
