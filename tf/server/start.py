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
    argNoweb,
    argDocker,
    argCheckout,
    argModules,
    argSets,
    argParam,
)
from .kernel import TF_DONE, TF_ERROR

HELP = '''
USAGE

text-fabric --help
text-fabric --version
text-fabric -k [datasource]

text-fabric datasource[:specifier] args

where all args are optional and args have one of these forms:

  -d
  -noweb
  -docker
  --checkout=specifier
  --mod=modules
  --set=file

EFFECT

If a datasource is given and the -k flag is not passed,
a TF kernel for that data source is started.
When the TF kernel is ready, a web server is started
serving a website that exposes the data through
a query interface.

The website can be served or on the internet.
The default browser will be opened, except when -noweb is passed.

:specifier (after the datasource)
--checkout=specifier

The TF app itself can be downloaded on the fly from GitHub.
The main data can be downloaded on the fly from GitHub.
The specifier indicates a point in the history from where the app should be retrieved.
  ;specifier is for the TF app code.
  --checkout=specifier is for the main data.

Specifiers may be:
  local                 - get the data from your local text-fabric-data directory
  clone                 - get the data from your local github clone
  latest                - get the latest release
  hot                   - get the latest commit
  tag (e.g. v1.3)       - get specific release
  hash (e.g. 78a03b...) - get specific commit

No specifier or the empty string means: latest release if there is one, else latest commit.

--mod=modules

Optionally, you can pass a comma-separated list of modules.
Modules are extra sets of features on top op the chosen data source.
You specify a module by giving the github repository where it is created,
in the form

  {org}/{repo}/{path}
  {org}/{repo}/{path}:specifier

where
  {org} is the github organization,
  {repo} the name of the repository in that organization
  {path} the path to the data within that repo.
  {specifier} points to a release or commit in the history

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
    -d
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
  checkout = ''
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
        if part.startswith('--checkout='):
          checkout = part[11:]
        if part.startswith('--mod='):
          modules = part[7:]
        elif part.startswith('--sets='):
          sets = part[6:]
        else:
          dataSource = part
          subParts = part.split(':', maxsplit=1)
          if len(subParts) == 1:
            subParts.append('')
          (dataSource, checkoutApp) = subParts
        good = True
    if good:
      found = True
  if found:
    return (kind, dataSource, checkoutApp, checkout, modules, sets)
  return False


def killProcesses(dataSource, checkoutApp, checkout, modules, sets, kill=False):
  tfProcs = {}
  for proc in psutil.process_iter(attrs=['pid', 'name']):
    test = filterProcess(proc)
    if test:
      (kind, ds, chkA, chk, mods, sts) = test
      tfProcs.\
          setdefault((ds, (chkA, chk, mods, sts)), {}).\
          setdefault(kind, []).append(proc.info['pid'])

  item = 'killed' if kill else 'terminated'
  myself = os.getpid()
  for ((ds, (chkA, chk, mods, sets)), kinds) in tfProcs.items():
    if (
        dataSource is None or
        (
            ds == dataSource and
            chkA == checkoutApp and
            chk == checkout and
            mods == modules and
            sts == sets
        )
    ):
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
  (dataSource, checkoutApp) = argParam(cargs=cargs, interactive=not kill)

  checkout = argCheckout(cargs=cargs)
  modules = argModules(cargs=cargs)
  sets = argSets(cargs=cargs)

  # This start script needs the app, so it downloads it.
  # It cqlls the TF kernel and the TF webserver.
  # Both kernel and webserver can be called stand alone,
  # and both can find and download the app as well.
  # Now, if this start script has found and downloaded the
  # app, the kernel and web server can use the local app
  # So we call them both with a datasource argument extended with
  # a checkout value that is either 'local' or 'clone',
  # depending on the original checkoutApp.
  # Similarly, the kernel will download the data.
  # The webserver does not have to do that.

  localCheckout = 'clone' if checkout == 'clone' else 'local'
  localCheckoutApp = 'clone' if checkoutApp == 'clone' else 'local'
  localDataSource = f'{dataSource}:{localCheckoutApp}'

  if kill:
    if dataSource is False:
      return
    killProcesses(dataSource, checkoutApp, checkout, modules, sets)
    return

  if dataSource is None:
    return

  noweb = argNoweb(cargs=cargs)

  debug = argDebug(cargs=cargs)
  docker = argDocker(cargs=cargs)

  kdataSource = (localDataSource,)
  kdataSource = kdataSource if checkout is None else (f'--checkout={checkout}', *kdataSource)
  kdataSource = (f'--mod={modules}', *kdataSource) if modules else kdataSource
  kdataSource = (f'--sets={sets}', *kdataSource) if sets else kdataSource

  ddataSource = (localDataSource,)
  ddataSource = ('-d', *ddataSource) if debug else ddataSource
  ddataSource = ('-docker', *ddataSource) if docker else ddataSource
  ddataSource = (f'--checkout={localCheckout}', *ddataSource)
  ddataSource = (f'--mod={modules}', *ddataSource) if modules else ddataSource

  if dataSource is not None:
    (commit, release, local, appBase, appDir) = findApp(dataSource, checkoutApp)
    if not appBase:
      return

    appPath = f'{appBase}/{appDir}'
    config = findAppConfig(dataSource, appPath)
    pKernel = None
    pWeb = None
    if config is None:
      return

    console(f'Cleaning up remnant processes, if any ...')
    killProcesses(dataSource, checkoutApp, checkout, modules, sets, kill=True)
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
      sleep(2)
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
