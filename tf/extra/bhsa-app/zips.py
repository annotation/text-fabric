# create the zips of the BHSA tf data by version
# in order to attach them to a new release in the BHSA github repository

import os
from shutil import rmtree
from zipfile import ZipFile, ZIP_DEFLATED


SOURCE_BASE = os.path.expanduser('~/github/etcbc')
DEST_BASE = os.path.expanduser('~/Downloads/etcbc-release')
TEMP = '_temp'


def zipData(source):
  sourceDir = f'{SOURCE_BASE}/{source}/tf'
  destDir = f'{DEST_BASE}/{source}'
  dataFiles = {}

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

  if os.path.exists(destDir):
    rmtree(destDir)
  os.makedirs(destDir, exist_ok=True)

  for (version, features) in sorted(dataFiles.items()):
    print(f'zipping {source:<8} {version:>4} with {len(features)} features')
    with ZipFile(
        f'{destDir}/{version}.zip',
        'w',
        compression=ZIP_DEFLATED,
        compresslevel=6,
    ) as zipFile:
      for featureFile in sorted(features):
        zipFile.write(
            f'{sourceDir}/{version}/{featureFile}',
            arcname=featureFile,
        )


zipData('bhsa')
zipData('phono')
zipData('parallels')
