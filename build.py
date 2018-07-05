import sys
import os
import re

from shutil import rmtree
from subprocess import run


HELP = '''
python3 build.py command

command:

-h --help help: print help and exit

l   : local develop build
c   : clean local develop build
r   : build for shipping, leave version as is
r1  : build for shiping, version becomes r1+1.0.0
r2  : build for shiping, version becomes r1.r2+1.0
r3  : build for shiping, version becomes r1.r2.r3+1

For r-commands you need to pass a commit message as well.
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

PACKAGE = 'text-fabric'
SCRIPT = '/Library/Frameworks/Python.framework/Versions/3.7/bin/text-fabric'

currentVersion = None
newVersion = None


def readArgs():
  args = sys.argv[1:]
  if not len(args) or args[0] in {'-h', '--help', 'help'}:
    print(HELP)
    return (False, None)
  else:
    arg = args[0]
    if arg in {'l', 'c', 'r', 'r1', 'r2', 'r3'}:
      if arg in {'r', 'r1', 'r2', 'r3'}:
        if len(args) < 2:
          print('Provide a commit message')
          return (False, None)
        return (arg, args[1])
      return (arg, None)
    print(HELP)
    return (False, None)


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
      if key == 'setup':
        print(text[586:607])
      if key == 'fabric':
        print(text[516:534])
      continue
      with open(c['file'], 'w') as fh:
        fh.write(text)
    if currentVersion == newVersion:
      print(f'Rebuilding version {newVersion}')
    else:
      print(f'Replacing version {currentVersion} by {newVersion}')


def makeDist():
    distFile = "{}-{}".format(PACKAGE, newVersion)
    distFileCompressed = f'{distFile}.tar.gz'
    distPath = f'{DIST}/{distFileCompressed}'
    rmtree(DIST)
    os.makedirs(DIST, exist_ok=True)
    run(['python3', 'setup.py', 'sdist'])
    # run(['twine', 'upload', distPath])
    print(f'twine upload {distPath}')


def commit(task, msg):
  commitMessage = f'Release {newVersion}: {msg}'
  tagVersion = f'v{newVersion}'
  run(['git', 'add', '--all', '.'])
  run(['git', 'commit', '-m', f'"{commitMessage}"'])
  run(['git', 'tag', '-a', tagVersion, '-m', f'"{commitMessage}"'])


def main():
  (task, msg) = readArgs()
  if not task:
    return
  adjustVersion(task)
  if task == 'l':
    run(['python3', 'setup.py', 'develop'])
  elif task == 'c':
    run(['python3', 'setup.py', 'develop', '-u'])
    os.unlink(SCRIPT)
  elif task in {'r', 'r1', 'r2', 'r3'}:
    makeDist()
    commit(task, msg)


main()
