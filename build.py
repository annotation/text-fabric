import sys
import os
import re

from time import sleep
from shutil import rmtree
from subprocess import run, Popen

import psutil

HELP = '''
python3 build.py command

command:

-h
--help
help  : print help and exit

docs  : serve docs locally
clean : clean local develop build
l     : local develop build
g     : push to github, code and docs
r     : build for shipping, leave version as is
r1    : build for shipping, version becomes r1+1.0.0
r2    : build for shipping, version becomes r1.r2+1.0
r3    : build for shipping, version becomes r1.r2.r3+1
t     : open text-fabric browser on specific dataset (bhsa, cunei)
data  : build data files for github release

For g and the r-commands you need to pass a commit message as well.
For data you need to pass an app argument: bhsa or cunei
'''

DIST = 'dist'

VERSION_CONFIG = dict(
    setup=dict(
        file='setup.py',
        re=re.compile(
            r'''version\s*=\s*['"]([^'"]*)['"]'''
        ),
        mask="version='{}'",
    ),
    fabric=dict(
        file='tf/fabric.py',
        re=re.compile(
            r'''VERSION\s*=\s*['"]([^'"]*)['"]'''
        ),
        mask="VERSION = '{}'",
    ),
)

TEST_BASE = os.path.expanduser('~/github/Dans-labs/text-fabric/test')
PACKAGE = 'text-fabric'
SCRIPT = '/Library/Frameworks/Python.framework/Versions/3.7/bin/text-fabric'

currentVersion = None
newVersion = None


def readArgs():
  args = sys.argv[1:]
  if not len(args) or args[0] in {'-h', '--help', 'help'}:
    print(HELP)
    return (False, None, [])
  arg = args[0]
  if arg not in {'t', 'docs', 'clean', 'l', 'g', 'data', 'r', 'r1', 'r2', 'r3'}:
    print(HELP)
    return (False, None, [])
  if arg in {'g', 'r', 'r1', 'r2', 'r3'}:
    if len(args) < 2:
      print('Provide a commit message')
      return (False, None, [])
    return (arg, args[1], args[1:])
  if arg in {'t', 'data'}:
    if len(args) < 2:
      print('Provide a data source [bhsa|cunei]')
      return (False, None, [])
    return (arg, args[1], args[1:])
  return (arg, None, [])


def incVersion(version, task):
  comps = [int(c) for c in version.split('.')]
  (major, minor, update) = comps
  if task == 'r1':
    major += 1
    minor = 0
    update = 0
  elif task == 'r2':
    minor += 1
    update = 0
  elif task == 'r3':
    update += 1
  return '.'.join(str(c) for c in (major, minor, update))


def replaceVersion(task, mask):
  def subVersion(match):
    global currentVersion
    global newVersion
    currentVersion = match.group(1)
    newVersion = incVersion(currentVersion, task)
    return mask.format(newVersion)
  return subVersion


def adjustVersion(task):
    for (key, c) in VERSION_CONFIG.items():
      print(f'Adjusting version in {c["file"]}')
      with open(c['file']) as fh:
        text = fh.read()
      text = c['re'].sub(
          replaceVersion(task, c['mask']),
          text,
      )
      with open(c['file'], 'w') as fh:
        fh.write(text)
    if currentVersion == newVersion:
      print(f'Rebuilding version {newVersion}')
    else:
      print(f'Replacing version {currentVersion} by {newVersion}')


def makeDist(task):
    distFile = "{}-{}".format(PACKAGE, newVersion)
    distFileCompressed = f'{distFile}.tar.gz'
    distPath = f'{DIST}/{distFileCompressed}'
    rmtree(DIST)
    os.makedirs(DIST, exist_ok=True)
    run(['python3', 'setup.py', 'sdist'])
    if task != 'r':
      run(['twine', 'upload', distPath])
      run('./purge.sh', shell=True)


def commit(task, msg):
  run(['git', 'add', '--all', '.'])
  run(['git', 'commit', '-m', msg])
  run(['git', 'push', 'origin', 'master'])
  if task in {'r1', 'r2', 'r3'}:
    tagVersion = f'v{newVersion}'
    commitMessage = f'Release {newVersion}: {msg}'
    run(['git', 'tag', '-a', tagVersion, '-m', commitMessage])
    run(['git', 'push', 'origin', '--tags'])


def shipDocs():
  codestats()
  run(['mkdocs', 'gh-deploy'])


def shipData(app, remaining):
  dataBuildScript = f'tf/extra/{app}-app/zips.py'
  if not os.path.exists(dataBuildScript):
    print(f'No data build script {dataBuildScript}')
    return
  run(['python3', dataBuildScript] + remaining)


def serveDocs():
  codestats()
  killProcesses()
  proc = Popen(['mkdocs', 'serve'])
  sleep(3)
  run('open http://127.0.0.1:8000', shell=True)
  try:
    proc.wait()
  except KeyboardInterrupt:
    pass
  proc.terminate()


def killProcesses():
  myself = os.getpid()
  for proc in psutil.process_iter(attrs=['pid', 'name']):
    pid = proc.info['pid']
    if pid == myself:
      continue
    if filterProcess(proc):
      try:
        proc.terminate()
        print(f'mkdocs [{pid}] terminated')
      except psutil.NoSuchProcess:
        print(f'mkdocs [{pid}] already terminated')


def filterProcess(proc):
  procName = proc.info['name']
  commandName = '' if procName is None else procName.lower()
  found = False
  if commandName.endswith('python'):
    parts = proc.cmdline()
    if len(parts) >= 3:
      if parts[1].endswith('mkdocs') and parts[2] == 'serve':
        found = True
      if parts[1] == 'build.py' and parts[2] == 'docs':
        found = True
  return found


def codestats():
  xd = (
      '__pycache__,node_modules,.tmp,.git,_temp,'
      '.ipynb_checkpoints,images,fonts,favicons,compiled'
  )
  xdtf = xd + ',search,server,extra'
  rfFmt = 'docs/Code/Stats{}.md'
  cmdLine = (
      'cloc'
      ' --no-autogen'
      ' --exclude_dir={}'
      f' --exclude-list-file=cloc_exclude.lst'
      f' --report-file={rfFmt}'
      ' --md'
      ' {}'
  )
  run(cmdLine.format(xd, '', '.'), shell=True)
  run(cmdLine.format(xdtf, 'Base', 'tf'), shell=True)
  run(cmdLine.format(xd, 'Search', 'tf/search'), shell=True)
  run(cmdLine.format(xd, 'Server', 'tf/server'), shell=True)
  run(cmdLine.format(xd, 'Apps', 'tf/extra'), shell=True)


def tfbrowse(dataset, remaining):
  datadir = f'{TEST_BASE}/{dataset}'
  good = True
  try:
    os.chdir(datadir)
  except Exception:
    good = False
    print(f'Cannot find TF test directory "{datadir}"')
  if not good:
    return
  rargs = ' '.join(remaining)
  cmdLine = f'text-fabric {dataset} {rargs}'
  try:
    run(cmdLine, shell=True)
  except KeyboardInterrupt:
    pass


def main():
  (task, msg, remaining) = readArgs()
  if not task:
    return
  elif task == 't':
    tfbrowse(msg, remaining)
  elif task == 'docs':
    serveDocs()
  elif task == 'clean':
    run(['python3', 'setup.py', 'develop', '-u'])
    os.unlink(SCRIPT)
  elif task == 'l':
    run(['python3', 'setup.py', 'develop'])
  elif task == 'g':
    shipDocs()
    commit(task, msg)
  elif task == 'data':
    shipData(msg, remaining)
  elif task in {'r', 'r1', 'r2', 'r3'}:
    adjustVersion(task)
    shipDocs()
    makeDist(task)
    commit(task, msg)


main()
