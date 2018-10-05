# create the zips of the BHSA tf data by version
# in order to attach them to a new release in the BHSA github repository

import os
from shutil import rmtree
from zipfile import ZipFile, ZIP_DEFLATED


SOURCE_DIR = os.path.expanduser('~/github/etcbc/bhsa/tf')
DEST_DIR = os.path.expanduser('~/Downloads/bhsa-release')

dataFiles = {}

with os.scandir(SOURCE_DIR) as versionIt:
  for versionEntry in versionIt:
    if not versionEntry.is_dir():
      continue
    version = versionEntry.name
    with os.scandir(f'{SOURCE_DIR}/{version}') as tfIt:
      for tfEntry in tfIt:
        if not tfEntry.is_file():
          continue
        featureFile = tfEntry.name
        if not featureFile.endswith('.tf'):
          print(f'WARNING: non feature file "{version}/{featureFile}"')
          continue
        dataFiles.setdefault(version, set()).add(featureFile)

if os.path.exists(DEST_DIR):
  rmtree(DEST_DIR)
os.makedirs(DEST_DIR, exist_ok=True)

for (version, features) in sorted(dataFiles.items()):
  print(f'zipping {version:>4} with {len(features)} features')
  with ZipFile(
      f'{DEST_DIR}/{version}.zip',
      'w',
      compression=ZIP_DEFLATED,
      compresslevel=6,
  ) as zipFile:
    for featureFile in sorted(features):
      zipFile.write(
          f'{SOURCE_DIR}/{version}/{featureFile}',
          arcname=featureFile,
      )
