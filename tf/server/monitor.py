import sys

from tf.core.helpers import console
from tf.applib.helpers import findAppConfig
from tf.server.kernel import makeTfConnection
from tf.server.common import getParam

TIMEOUT = 180

dataSource = None
config = None


def getStuff(lgc):
  global TF
  global appDir

  config = findAppConfig(dataSource)
  if config is None:
    return None

  TF = makeTfConnection(config.HOST, config.PORT['kernel'], TIMEOUT)
  return config


if __name__ == "__main__":
  dataSource = getParam(interactive=True)

  if dataSource is None:
    sys.exit()
  getStuff(False)

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
