import sys
import os
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


def argCheck(cargs=sys.argv):
  for arg in cargs[1:]:
    if arg == '-c':
      return True
  return False


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


def argLocalClones(cargs=sys.argv):
  for arg in cargs[1:]:
    if arg == '-lgc':
      return True
  return False


def argModules(cargs=sys.argv):
  for arg in cargs[1:]:
    if arg.startswith('--mod='):
      return arg
  return ''


def argSets(cargs=sys.argv):
  for arg in cargs[1:]:
    if arg.startswith('--sets='):
      return arg
  return ''


def argParam(cargs=sys.argv, interactive=False):
  dPrompt = f'see {APP_URL} for app-xxxx choices. xxxx = ? '

  dataSource = None
  for arg in cargs[1:]:
    if arg.startswith('-'):
      continue
    dataSource = arg
    break

  if interactive:
    if dataSource is None:
      dataSource = input(f'specify data source [{dPrompt}] > ')
    if dataSource is None:
      console(f'Pass a data source [{dPrompt}] as first argument', error=True)
    return dataSource

  if dataSource is None:
    return None
  return dataSource
