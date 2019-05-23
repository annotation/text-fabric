import sys

from importlib import util

from ..parameters import (
    ORG,
    APP_CODE
)
from ..core.helpers import console
from .repo import checkoutRepo


def findApp(dataSource, checkoutApp, silent=False):
  return checkoutRepo(
      org=ORG,
      repo=f'app-{dataSource}',
      folder=APP_CODE,
      checkout=checkoutApp,
      withPaths=True,
      keep=False,
      silent=silent,
      label='TF-app',
  )


def findAppConfig(dataSource, appPath):
  config = None
  appPath = f'{appPath}/config.py'

  try:
    spec = util.spec_from_file_location(f'tf.apps.{dataSource}.config', appPath)
    config = util.module_from_spec(spec)
    spec.loader.exec_module(config)
  except Exception as e:
    console(f'findAppConfig: {str(e)}', error=True)
    console(f'findAppConfig: Configuration for "{dataSource}" not found', error=True)
  return config


def findAppClass(dataSource, appPath):
  appClass = None
  moduleName = f'tf.apps.{dataSource}.app'

  try:
    spec = util.spec_from_file_location(
        moduleName,
        f'{appPath}/app.py',
    )
    code = util.module_from_spec(spec)
    sys.path.insert(0, appPath)
    spec.loader.exec_module(code)
    sys.path.pop(0)
    appClass = code.TfApp
  except Exception as e:
    console(f'findAppClass: {str(e)}', error=True)
    console(f'findAppClass: Api for "{dataSource}" not found')
  return appClass


def loadModule(dataSource, appPath, moduleName):
  try:
    spec = util.spec_from_file_location(
        f'tf.apps.{dataSource}.{moduleName}',
        f'{appPath}/{moduleName}.py',
    )
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
  except Exception as e:
    console(f'loadModule: {str(e)}', error=True)
    console(f'loadModule: {moduleName} in "{dataSource}" not found')
  return module
