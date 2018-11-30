from importlib import import_module
from ..core.helpers import console

RESULT = 'result'

# FIND AN APP


def findAppConfig(dataSource):
  config = None

  try:
    config = import_module('.config', package=f'tf.apps.{dataSource}')
  except Exception as e:
    console(f'findAppConfig: {str(e)}', error=True)
    console(f'findAppConfig: Configuration for "{dataSource}" not found', error=True)
  return config


def findAppClass(dataSource):
  appClass = None

  try:
    code = import_module(f'.app', package=f'tf.apps.{dataSource}')
    appClass = code.TfApp
  except Exception as e:
    console(f'findAppClass: {str(e)}', error=True)
    console(f'findAppClass: Api for "{dataSource}" not found')
  return appClass
