import os
import sys
from shutil import rmtree
from zipfile import ZipFile, ZIP_DEFLATED

GH_BASE = os.path.expanduser(f'~/github')
DW_BASE = os.path.expanduser(f'~/Downloads')
TEMP = '_temp'
RELATIVE = 'tf'


HELP = '''
USAGE

text-fabric-zip --help

text-fabric-zip org repo [relative]

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
and the are named tf-{version}.zip

If you have passed a relative argument, it will replace the tf,
and / in relative will be replaced by -.

In the example where relative is phrases/head/tf, the zip files are called
phrases-head-tf-{version}.zip

'''


def zipData(org, repo, relative=RELATIVE, tf=True, keep=False):
  print(f'Create release data for {org}/{repo}/{relative}')
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
            if not featureFile.endswith('.tf'):
              print(f'WARNING: non feature file "{version}/{featureFile}"')
              continue
            dataFiles.setdefault(version, set()).add(featureFile)

    for (version, features) in sorted(dataFiles.items()):
      item = f'{org}/{repo}'
      print(f'zipping {item:<25} {version:>4} with {len(features):>3} features')
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
      with os.scandir(thisPath) as dr:
        for entry in dr:
          name = entry.name
          if name == '.DS_Store':
            continue
          if entry.is_file():
            results.append((f'{path}/{name}', f'{base}/{path}/{name}'))
          elif entry.is_dir():
            collectFiles(base, f'{path}/{name}', results)

    results = []
    collectFiles(sourceDir, '', results)
    print(f'zipping {org}/{repo}/{relative} with {len(results)} files')
    with ZipFile(
        f'{destDir}/{relativeDest}.zip',
        'w',
        compression=ZIP_DEFLATED,
        compresslevel=6,
    ) as zipFile:
      for (name, path) in sorted(results):
        zipFile.write(
            path,
            arcname=name,
        )


def main(cargs=sys.argv):
  if len(cargs) >= 2 and any(arg in {'--help', '-help', '-h', '?', '-?'} for arg in cargs[1:]):
    print(HELP)
    return

  toBeAsked = ()
  if len(cargs) < 2:
    toBeAsked = (1, 2, 3)
  elif len(cargs) < 3:
    org = cargs[1]
    toBeAsked = (2, 3)
  elif len(cargs) < 4:
    org = cargs[1]
    repo = cargs[2]
    relative = RELATIVE
  elif len(cargs) < 5:
    org = cargs[1]
    repo = cargs[2]
    relative = cargs[3]
  else:
    print(HELP)
    return

  for i in toBeAsked:
    if i == 1:
      org = input('github organization = ')
      if not org:
        return
    elif i == 2:
      repo = input('github repo = ')
      if not repo:
        return
    elif i == 3:
      relative = input(f'relative path [default: {RELATIVE}] = ')
      if not relative:
        relative = RELATIVE

  zipData(org, repo, relative=relative)


if __name__ == "__main__":
  main()
