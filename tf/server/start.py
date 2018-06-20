import webbrowser
from time import sleep
from subprocess import PIPE, Popen

from tf.server.common import getParam, getDebug, getConfig
from tf.server.data import TF_DONE


def main():
  dataSource = getParam()
  ddataSource = ('-d', dataSource) if getDebug() else (dataSource,)
  if dataSource is not None:
    config = getConfig(dataSource)
    pService = None
    pWeb = None
    if config is not None:
      try:
        pService = Popen(
            ['python3', '-m', 'tf.server.service', dataSource],
            stdout=PIPE, encoding='utf-8',
        )
        print(f'Loading data for {dataSource}. Please wait ...')
        with pService.stdout as ph:
          for line in ph:
            print(line)
            if line.rstrip() == TF_DONE:
              break
        sleep(1)
        print(f'Opening {dataSource} in browser')
        pWeb = Popen(['python3', '-m', 'tf.server.web', *ddataSource])
        sleep(1)
        webbrowser.open(
            f'{config.protocol}{config.host}:{config.webport}',
            new=2,
            autoraise=True,
        )
        if pWeb:
          pWeb.wait()
      except KeyboardInterrupt:
        if pWeb:
          pWeb.terminate()
          print('Web server has stopped')
        if pService:
          pService.terminate()
          print('TF service has stopped')


if __name__ == "__main__":
  main()
