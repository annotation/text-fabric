import sys
import os
from glob import glob

from importlib import import_module

from tf.server.service import makeTfServer


def getParam():
  myDir = os.path.dirname(os.path.abspath(__file__))
  dataSourcesPre = glob(f'{myDir}/config/*.py')
  dataSources = set()
  for p in dataSourcesPre:
    d = os.path.splitext(os.path.basename(p))[0]
    if d != '__init__':
      dataSources.add(d)
  dPrompt = '/'.join(dataSources)

  dataSource = None
  for arg in sys.argv[1:]:
    if arg.startswith('-'):
      continue
    dataSource = arg
    break

  if dataSource is None:
    dataSource = input(f'specify data source [{dPrompt}] > ')
  if dataSource not in dataSources:
    dataSource = None
  if dataSource is None:
    print(f'Pass a data source [{dPrompt}] as first argument')
  return dataSource


def getDebug():
  for arg in sys.argv[1:]:
    if arg == '-d':
      return True
  return False


def tfService(dataSource):
  try:
    config = import_module(f'.{dataSource}', package='tf.server.config')
  except Exception as e:
    print(e)
    print(f'Data source "{dataSource}" not found')
    return None

  return makeTfServer(config.locations, config.modules, config.port)


if __name__ == "__main__":
  dataSource = getParam()
  if dataSource is not None:
    service = tfService(dataSource)
    if service:
      service.start()
