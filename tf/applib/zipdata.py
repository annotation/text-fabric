import os
import sys
from shutil import rmtree
from zipfile import ZipFile, ZIP_DEFLATED

from ..helpers import console, splitModRef

GH_BASE = os.path.expanduser(f'~/github')
DW_BASE = os.path.expanduser(f'~/Downloads')
TEMP = '_temp'
RELATIVE = 'tf'


HELP = '''
USAGE

text-fabric-zip --help

text-fabric-zip {org}/{repo}/{relative}

EFFECT

Zips text-fabric data from your local github repository into
a release file, ready to be attached to a github release.

Your repo must sit in ~/github/{org}/{repo}.

Your TF data is assumed to sit in the toplevel tf directory of your repo.
But if it is somewhere else, you can pass relative, e.g phrases/heads/tf

It is assumed that your tf directory contains subdirectories according to
the versions of the main datasource.
The actual .tf files are in those version directories.

Each of these version directories will be zipped into a separate file.

The resulting zip files end up in ~/Downloads/{org}-release/{repo}
and the are named {relative}-{version}.zip
(where the / in relative have been replaced by -)
'''

EXCLUDE = {'.DS_Store'}


def zipData(org, repo, relative=RELATIVE, tf=True, keep=False):
  console(f'Create release data for {org}/{repo}/{relative}')
  sourceBase = f'{GH_BASE}/{org}'
  destBase = f'{DW_BASE}/{org}-release'
  sourceDir = f'{sourceBase}/{repo}/{relative}'
  destDir = f'{destBase}/{repo}'
  dataFiles = {}

  if not keep:
    if os.path.exists(destDir):
      rmtree(destDir)
  os.makedirs(destDir, exist_ok=True)
  relativeDest = relative.replace('/', '-')

  if tf:
    with os.scandir(sourceDir) as versionIt:
      for versionEntry in versionIt:
        if not versionEntry.is_dir():
          continue
        version = versionEntry.name
        if version == TEMP:
          continue
        with os.scandir(f'{sourceDir}/{version}') as tfIt:
          for tfEntry in tfIt:
            if not tfEntry.is_file():
              continue
            featureFile = tfEntry.name
            if featureFile in EXCLUDE:
              continue
            if not featureFile.endswith('.tf'):
              console(f'WARNING: non feature file "{version}/{featureFile}"', error=True)
              continue
            dataFiles.setdefault(version, set()).add(featureFile)

    for (version, features) in sorted(dataFiles.items()):
      item = f'{org}/{repo}'
      console(f'zipping {item:<25} {version:>4} with {len(features):>3} features')
      with ZipFile(
          f'{destDir}/{relativeDest}-{version}.zip',
          'w',
          compression=ZIP_DEFLATED,
          compresslevel=6,
      ) as zipFile:
        for featureFile in sorted(features):
          zipFile.write(
              f'{sourceDir}/{version}/{featureFile}',
              arcname=featureFile,
          )
  else:

    def collectFiles(base, path, results):
      thisPath = f'{base}/{path}' if path else base
      internalBase = f'{relative}/{path}' if path else relative
      with os.scandir(thisPath) as dr:
        for entry in dr:
          name = entry.name
          if name in EXCLUDE:
            continue
          if entry.is_file():
            results.append((f'{internalBase}/{name}', f'{base}/{path}/{name}'))
          elif entry.is_dir():
            collectFiles(base, f'{path}/{name}', results)

    results = []
    collectFiles(sourceDir, '', results)
    console(f'zipping {org}/{repo}/{relative} with {len(results)} files')
    with ZipFile(
        f'{destDir}/{relativeDest}.zip',
        'w',
        compression=ZIP_DEFLATED,
        compresslevel=6,
    ) as zipFile:
      for (internalPath, path) in sorted(results):
        zipFile.write(
            path,
            arcname=internalPath,
        )


def main(cargs=sys.argv):
  if len(cargs) != 2 and any(arg in {'--help', '-help', '-h', '?', '-?'} for arg in cargs):
    console(HELP)
    return

  moduleRef = cargs[1]

  parts = splitModRef(moduleRef)
  if not parts:
    console(HELP)
    return

  (org, repo, relative) = parts

  zipData(org, repo, relative=relative, tf=relative.endswith('tf'))


if __name__ == "__main__":
  main()
