import sys

from ..core.helpers import console
from ..applib.app import findAppConfig
from ..server.kernel import makeTfConnection
from .command import argParam

TIMEOUT = 180

dataSource = None
config = None


def setup(lgc, check):
  global TF
  global appDir

  config = findAppConfig(dataSource, appDir)
  if config is None:
    return None

  TF = makeTfConnection(config.HOST, config.PORT['kernel'], TIMEOUT)
  return config


if __name__ == "__main__":
  dataSource = argParam(interactive=True)

  if dataSource is None:
    sys.exit()
  setup(False, False)

  commands = {
      '1': 'searchExe',
      '2': 'msgCache',
  }
  commandText = '\n'.join(f'[{k:>2}] {v}' for (k, v) in commands.items())
  try:
    while True:
      kernelApi = TF.connect()
      number = input(f'{commandText}\nenter number: ')
      command = commands[number]
      data = kernelApi.monitor()
      console(f'{command} = {data[command]}\n')
  except KeyboardInterrupt:
    console('\nquitting')
    sys.exit()
