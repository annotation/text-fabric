import sys
from importlib import import_module

from tf.service import makeTfServer


def getParam():
  try:
    dataSource = sys.argv[1]
  except Exception as e:
    print(e)
    dataSource = None
  if dataSource == '':
    dataSource = None
  if dataSource is None:
    print('Pass a data source as first argument')
  return dataSource


def tfService(dataSource):
  try:
    config = import_module(f'.{dataSource}', package='config')
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
