import sys
import os
from platform import system

import psutil
import webbrowser
from time import sleep
from subprocess import PIPE, Popen

from ..core.helpers import console
from ..parameters import NAME, VERSION
from ..applib.app import findApp, findAppConfig

from .command import (
    argDebug,
    argCheck,
    argNoweb,
    argDocker,
    argLocalClones,
    argModules,
    argSets,
    argParam,
)
from .kernel import TF_DONE, TF_ERROR

HELP = '''
USAGE

text-fabric --help
text-fabric --version

text-fabric datasource [-lgc] [-d] [-c] [-noweb] [-docker] [--mod=modules] [--set=file]

text-fabric -k [datasource]

EFFECT

If a datasource is given and the -k flag is not passed,
a TF kernel for that data source is started.
When the TF kernel is ready, a web server is started
serving a website that exposes the data through
a query interface.

The website can be served or on the internet.
The default browser will be opened, except when -noweb is passed.

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

--set=file

Optionally, you can pass a file name with the definition of custom sets in it.
This must be a dictionary were the keys are names of sets, and the values
are node sets.
This dictionary will be passed to the TF kernel, which will use it when it runs
queries.

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
    The web server reloads when its code changes.
    The web server is a Flask instance, started with reload=True.

-noweb Do not start the default browser

-docker Assume you are on docker. The local web server is passed 0.0.0.0 as host.


CLEAN UP

If you press Ctrl-C the web server is stopped, and after that the TF kernel
as well.
Normally, you do not have to do any clean up.
But if the termination is done in an irregular way, you may end up with
stray processes.

-k  Kill mode. If a data source is given, the TF kernel and web server for that
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
  sets = ''
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
        if part.startswith('--mod='):
          modules = part
        elif part.startswith('--sets='):
          sets = part
        else:
          dataSource = part
        good = True
    if good:
      found = True
  if found:
    return (kind, dataSource, modules, sets)
  return False


def killProcesses(dataSource, modules, sets, kill=False):
  tfProcs = {}
  for proc in psutil.process_iter(attrs=['pid', 'name']):
    test = filterProcess(proc)
    if test:
      (kind, ds, mods, sts) = test
      tfProcs.setdefault((ds, (mods, sts)), {}).setdefault(kind, []).append(proc.info['pid'])

  item = 'killed' if kill else 'terminated'
  myself = os.getpid()
  for ((ds, (mods, sets)), kinds) in tfProcs.items():
    if dataSource is None or (ds == dataSource and mods == modules and sts == sets):
      checkKinds = ('data', 'web', 'tf')
      for kind in checkKinds:
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
  dataSource = argParam(cargs=cargs, interactive=not kill)

  modules = argModules(cargs=cargs)
  sets = argSets(cargs=cargs)

  if kill:
    if dataSource is False:
      return
    killProcesses(dataSource, modules, sets)
    return

  noweb = argNoweb(cargs=cargs)

  debug = argDebug(cargs=cargs)
  docker = argDocker(cargs=cargs)
  check = argCheck(cargs=cargs)
  lgc = argLocalClones(cargs=cargs)

  kdataSource = ('-lgc', dataSource) if lgc else (dataSource, )
  kdataSource = ('-c', *kdataSource) if check else kdataSource
  kdataSource = (modules, *kdataSource) if modules else kdataSource
  kdataSource = (sets, *kdataSource) if sets else kdataSource

  ddataSource = ('-d', dataSource) if debug else (dataSource, )
  ddataSource = ('-docker', *ddataSource) if docker else ddataSource
  ddataSource = ('-lgc', *ddataSource) if lgc else ddataSource
  ddataSource = (modules, *ddataSource) if modules else ddataSource

  if dataSource is not None:
    (commit, appDir) = findApp(dataSource, lgc, check)
    if appDir is None:
      return

    config = findAppConfig(dataSource, appDir)
    pKernel = None
    pWeb = None
    if config is None:
      return

    console(f'Cleaning up remnant processes, if any ...')
    killProcesses(dataSource, modules, sets, kill=True)
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
        [pythonExe, '-m', f'tf.server.web', *ddataSource],
        bufsize=0,
    )

    if not noweb:
      sleep(1)
      console(f'Opening {dataSource} in browser')
      webbrowser.open(
          f'{config.PROTOCOL}{config.HOST}:{config.PORT["web"]}',
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
          console('TF web server has stopped')
        if pKernel:
          pKernel.terminate()
          for line in pKernel.stdout:
            sys.stdout.write(line)
          console('TF kernel has stopped')


if __name__ == "__main__":
  main()
