import sys
import os
from platform import system

import psutil
import webbrowser
from time import sleep
from subprocess import PIPE, Popen

from ..core.helpers import console
from ..parameters import NAME, VERSION
from ..applib.appmake import (
    findAppConfig,
)
from .common import (getParam, getModules, getDebug, getCheck, getNoweb, getDocker, getLocalClones)
from .kernel import TF_DONE, TF_ERROR

HELP = '''
USAGE

text-fabric --help
text-fabric --version

text-fabric datasource
text-fabric [-lgc] [-d] [-c] [-noweb] [-docker] datasource [--mod=modules]

text-fabric -k
text-fabric -k datasource

EFFECT

If a datasource is given and the -k flag is not passed,
a TF kernel for that data source is started.
When the TF kernel is ready, a webserver is started
serving a local website that exposes the data through
a query interface.
It will open in the default browser.

--mod=modules

Optionally, you can pass a comma-separated list of modules.
Modules are extra sets of features on top op the chosen data source.
You specify a module by giving the github repository where it is created,
in the form

  {org}/{repo}/{path}

where
  {org} is the github organization,
  {repo} the name of the repository in that organization
  {path} the path to the data within that repo.

It is assumed that the data is stored in directories under {path},
where the directories are named as the versions that exists in the main data source.

DATA LOADING

Text-Fabric looks for data in ~/text-fabric-data.
If data is not found there, it first downloads the relevant data from
github.

-lgc Look for data first in local github clones under ~/github.
  If data is not found there, get data in the normal way.

-c   Check for data updates online. If a newer release of the data is found,
     it will be downloaded.


MISCELLANEOUS

-d  Debug mode. For developers of Text-Fabric itself.
    The webserver reloads when its code changes.
    The webserver is a bottle instance, started with reload=True.

-noweb Do not start the default browser

-docker Assume you are on docker. The local webserver is passed 0.0.0.0 as host.


CLEAN UP

If you press Ctrl-C the webserver is stopped, and after that the TF kernel
as well.
Normally, you do not have to do any clean up.
But if the termination is done in an irregular way, you may end up with
stray processes.

-k  Kill mode. If a data source is given, the TF kernel and webserver for that
    data source are killed.
    Without a data source, all local webinterface related processes are killed.
'''

FLAGS = set('''
    -c
    -d
    -lgc
    -noweb
    -docker
'''.strip().split())

BANNER = f'This is {NAME} {VERSION}'


def filterProcess(proc):
  procName = proc.info['name']
  commandName = '' if procName is None else procName.lower()
  # commandName = proc.info['name'].lower()

  found = False
  kind = None
  modules = ''
  dataSource = None

  trigger = 'python'
  if commandName.endswith(trigger) or commandName.endswith(f'{trigger}.exe'):
    good = False
    parts = proc.cmdline()
    for part in parts:
      part = part.lower()
      if part in FLAGS:
        continue
      trigger = 'text-fabric'
      if part.endswith(trigger) or part.endswith(f'{trigger}.exe'):
        kind = 'tf'
        continue
      if part == 'tf.server.kernel':
        kind = 'data'
        good = True
        continue
      if part == 'tf.server.local':
        kind = 'local'
        good = True
        continue
      if part.endswith('local.py'):
        kind = 'local'
        good = True
        continue
      if kind in {'data', 'local', 'tf'}:
        if kind == 'tf' and part == '-k':
          break
        if part.startswith('--mod='):
          modules = part
        else:
          dataSource = part
        good = True
    if good:
      found = True
  if found:
    return (kind, dataSource, modules)
  return False


def killProcesses(dataSource, modules, kill=False):
  tfProcs = {}
  for proc in psutil.process_iter(attrs=['pid', 'name']):
    test = filterProcess(proc)
    if test:
      (kind, ds, mods) = test
      tfProcs.setdefault((ds, mods), {}).setdefault(kind, []).append(proc.info['pid'])

  item = 'killed' if kill else 'terminated'
  myself = os.getpid()
  for ((ds, mods), kinds) in tfProcs.items():
    if dataSource is None or (ds == dataSource and mods == modules):
      for kind in ('local', 'data', 'tf'):
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
            console(f'Process {kind} server for {ds}: {item}')
          except psutil.NoSuchProcess:
            console(f'Process {kind} server for {ds}: already {item}', error=True)


def getKill(cargs=sys.argv):
  for arg in cargs[1:]:
    if arg == '-k':
      return True
  return False


def main(cargs=sys.argv):
  console(BANNER)
  if len(cargs) >= 2 and any(arg in {'--help', '-help', '-h', '?', '-?'} for arg in cargs[1:]):
    console(HELP)
    return
  if len(cargs) >= 2 and any(arg in {'--version', '-version', '-v'} for arg in cargs[1:]):
    return

  isWin = system().lower().startswith('win')

  kill = getKill(cargs=cargs)

  if kill:
    dataSource = getParam(cargs=cargs, interactive=False)
    if dataSource is False:
      return
    modules = getModules(cargs=cargs)
    killProcesses(dataSource, modules)
    return

  dataSource = getParam(cargs=cargs, interactive=True)

  noweb = getNoweb(cargs=cargs)

  debug = getDebug(cargs=cargs)
  docker = getDocker(cargs=cargs)
  check = getCheck(cargs=cargs)
  lgc = getLocalClones(cargs=cargs)
  modules = getModules(cargs=cargs)

  ddataSource = ('-d', dataSource) if debug else (dataSource, )
  ddataSource = ('-docker', *ddataSource) if docker else ddataSource
  ddataSource = ('-lgc', *ddataSource) if lgc else ddataSource
  ddataSource = (modules, *ddataSource) if modules else ddataSource

  kdataSource = ('-lgc', dataSource) if lgc else (dataSource, )
  kdataSource = ('-c', *kdataSource) if check else kdataSource
  kdataSource = (modules, *kdataSource) if modules else kdataSource

  if dataSource is not None:
    config = findAppConfig(dataSource)
    pKernel = None
    pWeb = None
    if config is not None:
      console(f'Cleaning up remnant processes, if any ...')
      killProcesses(dataSource, modules, kill=True)
      pythonExe = 'python' if isWin else 'python3'

      pKernel = Popen(
          [pythonExe, '-m', 'tf.server.kernel', *kdataSource],
          stdout=PIPE,
          bufsize=1,
          encoding='utf-8',
      )

      console(f'Loading data for {dataSource}. Please wait ...')
      for line in pKernel.stdout:
        sys.stdout.write(line)
        if line.rstrip() == TF_ERROR:
          return
        if line.rstrip() == TF_DONE:
          break
      sleep(1)

      pWeb = Popen(
          [pythonExe, '-m', 'tf.server.local', *ddataSource],
          bufsize=0,
      )

      if not noweb:
        sleep(1)
        console(f'Opening {dataSource} in browser')
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
          console('')
          if pWeb:
            pWeb.terminate()
            console('TF webserver has stopped')
          if pKernel:
            pKernel.terminate()
            for line in pKernel.stdout:
              sys.stdout.write(line)
            console('TF kernel has stopped')


if __name__ == "__main__":
  main()
