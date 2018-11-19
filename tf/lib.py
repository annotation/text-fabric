import os
import pickle
import gzip
from .parameters import PICKLE_PROTOCOL, GZIP_LEVEL
from .core.helpers import console


def writeSets(sets, dest):
  destPath = os.path.expanduser(dest)
  (baseDir, fileName) = os.path.split(destPath)
  if not os.path.exists(baseDir):
    try:
      os.makedirs(baseDir, exist_ok=True)
    except Exception:
      console(f'Cannot create directory "{baseDir}"', error=True)
      return False
  with gzip.open(destPath, "wb", compresslevel=GZIP_LEVEL) as f:
    pickle.dump(sets, f, protocol=PICKLE_PROTOCOL)
  return True


def readSets(source):
  sourcePath = os.path.expanduser(source)
  if not os.path.exists(sourcePath):
    console(f'Sets file "{source}" does not exist.')
    return False
  with gzip.open(sourcePath, "rb") as f:
    sets = pickle.load(f)
  return sets
