import sys
import os
import re
from shutil import rmtree

from .parameters import PACK_VERSION

TFD = 'text-fabric-data'
GH = 'github'

ROOTS = [TFD, GH]

binRe = re.compile(r'/\.tf$')
binvRe = re.compile(r'/\.tf/([^/]+)$')


def out(msg):
  sys.stdout.write(msg)
  sys.stdout.flush()


def err(msg):
  sys.stderr.write(msg)
  sys.stderr.flush()


def clean(tfd=True, gh=False, dry=True, specific=None, current=False):
  if specific is not None:
    bases = [os.path.expanduser(specific)]
  else:
    for root in ROOTS:
      if root == TFD and not tfd or root == GH and not gh:
        sys.stdout.write(f'skipped {root}\n')
        continue
      bases.append(os.path.expanduser(f'~/{root}'))

  for base in bases:
    for triple in os.walk(base):
      d = triple[0]
      if binRe.search(d):
        files = triple[2]
        if files:
          err(f'{d} legacy: delete {len(files)} files ... ')
          if dry:
            err('dry\n')
          else:
            for f in files:
              os.unlink(f'{d}/{f}')
            err('done\n')
          continue
      match = binvRe.search(d)
      if match:
        binv = match.group(1)
        if not current and binv == PACK_VERSION:
          out(f'{d} version {binv}: keep\n')
        else:
          files = triple[2]
          err(f'{d} version {binv}: delete it and its {len(files)} files ...')
          if dry:
            err('dry\n')
          else:
            rmtree(d)
            err('done\n')
  if dry:
    sys.stdout.write('\n')
    sys.stderr.write('This was a dry run\n')
    sys.stderr.write('Say clean(dry=False) to perform the cleaning\n')
