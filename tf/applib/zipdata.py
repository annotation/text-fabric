import os
import sys
from glob import glob
from shutil import rmtree
from zipfile import ZipFile

from ..parameters import ZIP_OPTIONS
from ..core.helpers import console, splitModRef

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
    versionEntries = []
    for versionEntry in glob(f'{sourceDir}/*'):
      if os.path.isdir(versionEntry):
        (versionDir, version) = os.path.split(versionEntry)
        versionEntries.append((versionDir, version))
    if versionEntries:
      console(f'Found {len(versionEntries)} versions')
    else:
      versionEntries.append((sourceDir, ''))
      console(f'Found unversioned features')
    for (versionDir, version) in versionEntries:
      if version == TEMP:
        continue
      versionRep = f'/{version}' if version else ''
      versionRep2 = f'{version}/' if version else ''
      versionRep3 = f'-{version}' if version else ''
      for tfEntry in glob(f'{versionDir}{versionRep}/*'):
        if not os.path.isfile(tfEntry):
          continue
        (tfDir, featureFile) = os.path.split(tfEntry)
        if featureFile in EXCLUDE:
          continue
        if not featureFile.endswith('.tf'):
          console(f'WARNING: non feature file "{versionRep2}{featureFile}"', error=True)
          continue
        dataFiles.setdefault(version, set()).add(featureFile)

    console(f'zip files end up in {destDir}')
    for (version, features) in sorted(dataFiles.items()):
      item = f'{org}/{repo}'
      versionRep = f'/{version}' if version else ''
      versionRep3 = f'-{version}' if version else ''
      target = f'{relativeDest}{versionRep3}.zip'
      console(f'zipping {item:<25} {version:>4} with {len(features):>3} features ==> {target}')
      with ZipFile(
          f'{destDir}/{target}',
          'w',
          **ZIP_OPTIONS,
      ) as zipFile:
        for featureFile in sorted(features):
          zipFile.write(
              f'{sourceDir}{versionRep}/{featureFile}',
              arcname=featureFile,
          )
  else:

    def collectFiles(base, path, results):
      thisPath = f'{base}/{path}' if path else base
      internalBase = f'{relative}/{path}' if path else relative
      for entry in glob(f'{thisPath}/*'):
        (entryDir, name) = os.path.split(entry)
        if name in EXCLUDE:
          continue
        if os.path.isfile(entry):
          results.append((f'{internalBase}/{name}', f'{base}/{path}/{name}'))
        elif os.path.isdir(entry):
          collectFiles(base, f'{path}/{name}', results)

    results = []
    collectFiles(sourceDir, '', results)
    if not relativeDest:
      relativeDest = '-'
    console(f'zipping {org}/{repo}/{relative} with {len(results)} files')
    console(f'zip file is {destDir}/{relativeDest}.zip')
    with ZipFile(
        f'{destDir}/{relativeDest}.zip',
        'w',
        **ZIP_OPTIONS,
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

  (org, repo, relative, checkout) = parts

  tf = (
      relative.endswith('tf') or
      '/tf/' in relative
  )
  print(tf)

  zipData(org, repo, relative=relative, tf=tf)


if __name__ == "__main__":
  main()
