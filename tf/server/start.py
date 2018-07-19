import sys
import os
from platform import system

import psutil
import webbrowser
from time import sleep
from subprocess import PIPE, Popen

from tf.server.common import getParam, getDebug, getNoweb, getDocker, getConfig
from tf.server.kernel import TF_DONE, TF_ERROR

HELP = '''
USAGE

text-fabric --help

text-fabric datasource
text-fabric [-d] [-noweb] [-docker] datasource

text-fabric -k
text-fabric -k datasource

EFFECT

If a datasource is given and the -k flag is not passed,
a TF kernel for that data source is started.
When the TF kernel is ready, a webserver is started
serving a local website that exposes the data through
a query interface.
It will open in the default browser.

-d  Debug mode. For developers of Text-Fabric itself.
    The webserver reloads when its code changes.
    The webserver is a bottle instance, started with reload=True.

-noweb Do not start the web browser

-docker Assume you are on docker. The web server is passed 0.0.0.0 as host.


CLEAN UP

If you press Ctrl-C the webserver is stopped, and after that the TF kernel
as well.
Normally, you do not have to do any clean up.
But if the termination is done in an irregular way, you may end up with
stray processes.

-k  Kill mode. If a data source is given, the TF kernel and webserver for that
    data source are killed.
    Without a data source, all web-interface related processes are killed.
'''


def filterProcess(proc):
  procName = proc.info['name']
  commandName = '' if procName is None else procName.lower()
  # commandName = proc.info['name'].lower()

  found = False
  kind = None
  dataSource = None

  trigger = 'python'
  if commandName.endswith(trigger) or commandName.endswith(f'{trigger}.exe'):
    good = False
    parts = proc.cmdline()
    for part in parts:
      part = part.lower()
      if part == '-d':
        continue
      trigger = 'text-fabric'
      if part.endswith(trigger) or part.endswith(f'{trigger}.exe'):
        kind = 'tf'
        continue
      if part == 'tf.server.kernel':
        kind = 'data'
        good = True
        continue
      if part == 'tf.server.web':
        kind = 'web'
        good = True
        continue
      if part.endswith('web.py'):
        kind = 'web'
        good = True
        continue
      if kind in {'data', 'web', 'tf'}:
        if kind == 'tf' and part == '-k':
          break
        dataSource = part
        good = True
        break
    if good:
      found = True
  if found:
    return (kind, dataSource)
  return False


def killProcesses(dataSource, kill=False):
  tfProcs = {}
  for proc in psutil.process_iter(attrs=['pid', 'name']):
    test = filterProcess(proc)
    if test:
      (kind, ds) = test
      tfProcs.setdefault(ds, {}).setdefault(kind, []).append(proc.info['pid'])

  item = 'killed' if kill else 'terminated'
  myself = os.getpid()
  for (ds, kinds) in tfProcs.items():
    if dataSource is None or ds == dataSource:
      for kind in ('web', 'data', 'tf'):
        pids = kinds.get(kind, [])
        for pid in pids:
          if pid == myself:
            continue
          try:
            proc = psutil.Process(pid=pid)
            if kill:
              proc.kill()
            else:
              proc.terminate()
            print(f'Process {kind} server for {ds}: {item}')
          except psutil.NoSuchProcess:
            print(f'Process {kind} server for {ds}: already {item}')


def getKill(cargs=sys.argv):
  for arg in cargs[1:]:
    if arg == '-k':
      return True
  return False


def main(cargs=sys.argv):
  if len(cargs) >= 2 and cargs[1] in {'--help', '-help', '-h', '?', '-?'}:
    print(HELP)

  isWin = system().lower().startswith('win')

  kill = getKill(cargs=cargs)

  if kill:
    dataSource = getParam(cargs=cargs, interactive=False)
    if dataSource is False:
      return
    killProcesses(dataSource)
    return

  dataSource = getParam(cargs=cargs, interactive=True)

  noweb = getNoweb(cargs=cargs)

  ddataSource = ('-d', dataSource) if getDebug(cargs=cargs) else (dataSource,)
  ddataSource = ('-docker', *ddataSource) if getDocker(cargs=cargs) else ddataSource
  if dataSource is not None:
    config = getConfig(dataSource)
    pKernel = None
    pWeb = None
    if config is not None:
      print(f'Cleaning up remnant processes, if any ...')
      killProcesses(dataSource, kill=True)
      pythonExe = 'python' if isWin else 'python3'

      pKernel = Popen(
          [pythonExe, '-m', 'tf.server.kernel', dataSource],
          stdout=PIPE, bufsize=1, encoding='utf-8',
      )

      print(f'Loading data for {dataSource}. Please wait ...')
      for line in pKernel.stdout:
        sys.stdout.write(line)
        if line.rstrip() == TF_ERROR:
          return
        if line.rstrip() == TF_DONE:
          break
      sleep(1)

      pWeb = Popen(
          [pythonExe, '-m', 'tf.server.web', *ddataSource],
          bufsize=0,
      )

      if not noweb:
        sleep(1)
        print(f'Opening {dataSource} in browser')
        webbrowser.open(
            f'{config.protocol}{config.host}:{config.webport}',
            new=2,
            autoraise=True,
        )

      if pWeb and pKernel:
        try:
          for line in pKernel.stdout:
            sys.stdout.write(line)
        except KeyboardInterrupt:
          print('')
          if pWeb:
            pWeb.terminate()
            print('TF webserver has stopped')
          if pKernel:
            pKernel.terminate()
            for line in pKernel.stdout:
              sys.stdout.write(line)
            print('TF kernel has stopped')


if __name__ == "__main__":
  main()
