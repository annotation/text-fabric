import sys
from importlib import import_module

from service import makeTfServer

try:
  dataSource = sys.argv[1]
except Exception:
  print('Pass a data source as first argument')
  sys.exit(1)

try:
  config = import_module(f'.{dataSource}', package='config')
except Exception as e:
  print(f'Data source "{dataSource}" not found')
  sys.exit(1)

# print(f'makeTfServer({config.locations}, {config.modules}, {config.port}).start()')

makeTfServer(config.locations, config.modules, config.port).start()
