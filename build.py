import sys
import os
import re

from time import sleep
from shutil import rmtree
from subprocess import run, Popen

import psutil

from tf.core.helpers import console
from tf.applib.appmake import findAppConfig
from tf.applib.zipdata import zipData

HELP = '''
python3 build.py command

command:

-h
--help
help  : print help and exit

docs  : serve docs locally
clean : clean local develop build
l     : local develop build
i     : local non-develop build
g     : push to github, code and docs
r     : build for shipping, leave version as is
r1    : build for shipping, version becomes r1+1.0.0
r2    : build for shipping, version becomes r1.r2+1.0
r3    : build for shipping, version becomes r1.r2.r3+1
a     : open text-fabric browser on specific dataset (bhsa, peshitta, syrnt, uruk)
t     : run test suite (relations)
data  : build data files for github release

For g and the r-commands you need to pass a commit message as well.
For data you need to pass an app argument: bhsa, peshitta, syrnt or uruk
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
    parameters=dict(
        file='tf/parameters.py',
        re=re.compile(
            r'''VERSION\s*=\s*['"]([^'"]*)['"]'''
        ),
        mask="VERSION = '{}'",
    ),
)

TEST_BASE = os.path.expanduser('~/github/Dans-labs/text-fabric/test')
APP_BASE = f'{TEST_BASE}/apps'
PACKAGE = 'text-fabric'
SCRIPT = '/Library/Frameworks/Python.framework/Versions/3.7/bin/text-fabric'

currentVersion = None
newVersion = None


def readArgs():
  args = sys.argv[1:]
  if not len(args) or args[0] in {'-h', '--help', 'help'}:
    console(HELP)
    return (False, None, [])
  arg = args[0]
  if arg not in {'a', 't', 'docs', 'clean', 'l', 'i', 'g', 'data', 'r', 'r1', 'r2', 'r3'}:
    console(HELP)
    return (False, None, [])
  if arg in {'g', 'r', 'r1', 'r2', 'r3'}:
    if len(args) < 2:
      console('Provide a commit message')
      return (False, None, [])
    return (arg, args[1], args[2:])
  if arg in {'a', 't', 'data'}:
    if len(args) < 2:
      if arg in {'a', 'data'}:
        console('Provide a data source [bhsa|peshitta|syrnt|uruk]')
      elif arg in {'t'}:
        console('Provide a test suite [relations]')
      return (False, None, [])
    return (arg, args[1], args[2:])
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
      console(f'Adjusting version in {c["file"]}')
      with open(c['file']) as fh:
        text = fh.read()
      text = c['re'].sub(
          replaceVersion(task, c['mask']),
          text,
      )
      with open(c['file'], 'w') as fh:
        fh.write(text)
    if currentVersion == newVersion:
      console(f'Rebuilding version {newVersion}')
    else:
      console(f'Replacing version {currentVersion} by {newVersion}')


def makeDist(pypi=True):
    distFile = "{}-{}".format(PACKAGE, newVersion)
    distFileCompressed = f'{distFile}.tar.gz'
    distPath = f'{DIST}/{distFileCompressed}'
    rmtree(DIST)
    os.makedirs(DIST, exist_ok=True)
    run(['python3', 'setup.py', 'sdist'])
    if pypi:
      run(['twine', 'upload', '-u', 'dirkroorda', distPath])
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
  config = findAppConfig(app)
  if not config:
    console('Data not shipped')
    return
  seen = set()
  for r in config.ZIP:
    (org, repo, relative) = r if type(r) is tuple else (config.ORG, r, config.RELATIVE)
    keep = (org, repo) in seen
    zipData(org, repo, relative=relative, tf=relative.endswith('tf'), keep=keep)
    seen.add((org, repo))


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
        console(f'mkdocs [{pid}] terminated')
      except psutil.NoSuchProcess:
        console(f'mkdocs [{pid}] already terminated')


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
  xdtf = xd + ',applib,apps,convert,core,search,server,writing'
  xdtest = xd + ',tf'
  rfFmt = 'docs/Code/Stats{}.md'
  cmdLine = (
      'cloc'
      ' --no-autogen'
      ' --exclude_dir={}'
      ' --exclude-list-file={}'
      f' --report-file={rfFmt}'
      ' --md'
      ' {}'
  )
  nex = 'cloc_exclude.lst'
  tex = 'cloc_exclude_t.lst'
  run(cmdLine.format(xd, nex, '', '.'), shell=True)
  run(cmdLine.format(xdtf, nex, 'Toplevel', 'tf'), shell=True)
  run(cmdLine.format(xd, nex, 'Applib', 'tf/applib'), shell=True)
  run(cmdLine.format(xd, nex, 'Apps', 'tf/apps'), shell=True)
  run(cmdLine.format(xd, nex, 'Convert', 'tf/convert'), shell=True)
  run(cmdLine.format(xd, nex, 'Core', 'tf/core'), shell=True)
  run(cmdLine.format(xd, nex, 'Search', 'tf/search'), shell=True)
  run(cmdLine.format(xd, nex, 'Server', 'tf/server'), shell=True)
  run(cmdLine.format(xd, nex, 'Writing', 'tf/writing'), shell=True)
  run(cmdLine.format(xdtest, tex, 'Test', 'test/generic'), shell=True)


def tfbrowse(dataset, remaining):
  datadir = f'{APP_BASE}/{dataset}'
  good = True
  try:
    os.chdir(datadir)
  except Exception:
    good = False
    console(f'Cannot find TF app directory "{datadir}"')
  if not good:
    return
  rargs = ' '.join(remaining)
  cmdLine = f'text-fabric {dataset} {rargs}'
  try:
    run(cmdLine, shell=True)
  except KeyboardInterrupt:
    pass


def tftest(suite, remaining):
  suiteDir = f'{TEST_BASE}/generic'
  suiteFile = f'{suite}.py'
  good = True
  try:
    os.chdir(suiteDir)
  except Exception:
    good = False
    console(f'Cannot find TF test directory "{suiteDir}"')
  if not good:
    return
  if not os.path.exists(suiteFile):
    console(f'Cannot find TF test suite "{suite}"')
    return
  rargs = ' '.join(remaining)
  cmdLine = f'python3 {suiteFile} -v {rargs}'
  try:
    run(cmdLine, shell=True)
  except KeyboardInterrupt:
    pass


def clean():
  run(['python3', 'setup.py', 'develop', '-u'])
  os.unlink(SCRIPT)
  run([
      'pip3',
      'uninstall',
      '-y',
      'text-fabric'
  ])


def main():
  (task, msg, remaining) = readArgs()
  if not task:
    return
  elif task == 'a':
    tfbrowse(msg, remaining)
  elif task == 't':
    tftest(msg, remaining)
  elif task == 'docs':
    serveDocs()
  elif task == 'clean':
    clean()
  elif task == 'l':
    clean()
    run(['python3', 'setup.py', 'develop'])
  elif task == 'i':
    clean
    makeDist(pypi=False)
    run([
        'pip3',
        'install',
        '--upgrade',
        '--no-index',
        '--find-links',
        f'file://{os.path.expanduser("~/github/Dans-labs/text-fabric/dist")}',
        'text-fabric'
    ])
  elif task == 'g':
    shipDocs()
    commit(task, msg)
  elif task == 'data':
    shipData(msg, remaining)
  elif task in {'r', 'r1', 'r2', 'r3'}:
    adjustVersion(task)
    shipDocs()
    makeDist()
    commit(task, msg)


main()
