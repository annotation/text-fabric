import sys
import re

from ..parameters import APP_URL
from ..core.helpers import console

# COMMAND LINE ARGS

appPat = '^([a-zA-Z0-9_-]+)$'
appRe = re.compile(appPat)


def argDebug(cargs=sys.argv):
  for arg in cargs[1:]:
    if arg == '-d':
      return True
  return False


def argCheckout(cargs=sys.argv):
  for arg in cargs[1:]:
    if arg.startswith('--checkout='):
      return arg[11:]
  return None


def argNoweb(cargs=sys.argv):
  for arg in cargs[1:]:
    if arg == '-noweb':
      return True
  return False


def argDocker(cargs=sys.argv):
  for arg in cargs[1:]:
    if arg == '-docker':
      return True
  return False


def argModules(cargs=sys.argv):
  for arg in cargs[1:]:
    if arg.startswith('--mod='):
      return arg[6:]
  return ''


def argSets(cargs=sys.argv):
  for arg in cargs[1:]:
    if arg.startswith('--sets='):
      return arg[7:]
  return ''


def argParam(cargs=sys.argv, interactive=False):
  dPrompt = f'see {APP_URL} for app-xxxx choices. xxxx = ? '
  dataSource = None
  checkoutApp = None

  for arg in cargs[1:]:
    if arg.startswith('-'):
      continue
    dataSource = arg
    break

  if interactive:
    if dataSource is None:
      dataSource = input(f'specify data source[:checkout] [{dPrompt}] > ')
    if dataSource is None:
      console(
          f'Pass a data source[:checkout] [{dPrompt}] as first argument',
          error=True,
      )

  if dataSource is None:
    return (None, None)

  parts = dataSource.split(':', maxsplit=1)
  if len(parts) == 1:
    parts.append('')
  (dataSource, checkoutApp) = parts
  return (dataSource, checkoutApp)
