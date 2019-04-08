from ..core.helpers import console
from ..applib.app import findApp, findAppConfig
from ..server.kernel import makeTfConnection
from .command import argParam

TIMEOUT = 180


def setup(dataSource, checkoutApp):
  global TF

  (commit, release, local, appBase, appDir) = findApp(dataSource, checkoutApp)
  if not appBase:
    return
  appPath = f'{appBase}/{appDir}'
  config = findAppConfig(dataSource, appPath)
  if config is None:
    return None

  TF = makeTfConnection(config.HOST, config.PORT['kernel'], TIMEOUT)
  return TF


def main():
  (dataSource, checkoutApp) = argParam(interactive=True)
  if dataSource is None:
    return

  TF = setup(dataSource, checkoutApp)
  if TF is None:
    return

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
    return


if __name__ == "__main__":
  main()
