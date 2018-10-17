import os
from shutil import rmtree
from zipfile import ZipFile, ZIP_DEFLATED

GH_BASE = os.path.expanduser(f'~/github')
DW_BASE = os.path.expanduser(f'~/Downloads')
TEMP = '_temp'


def zipData(org, repo):
  sourceBase = f'{GH_BASE}/{org}'
  destBase = f'{DW_BASE}/{org}-release'
  sourceDir = f'{sourceBase}/{repo}/tf'
  destDir = f'{destBase}/{repo}'
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
    print(f'zipping {repo:<8} {version:>4} with {len(features)} features')
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
