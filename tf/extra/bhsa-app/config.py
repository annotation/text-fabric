import os
from tf.extra.bhsa import Bhsa, hasTf

ORG = 'etcbc'
REPO = 'bhsa'
VERSION = 'c'

PHONO = 'phono'
PARA = 'parallels'


protocol = 'http://'
host = 'localhost'
port = 18981
webport = 8001

options = ()


def configure(lgc, version=VERSION):
  base = hasTf(lgc, source=REPO, version=version)
  if not base:
    base = '~/text-fabric-data'
  base = f'{base}/{ORG}'

  basePhono = hasTf(lgc, source=PHONO, version=version)
  if not basePhono:
    basePhono = '~/text-fabric-data'
  basePhono = f'{basePhono}/{ORG}'

  basePara = hasTf(lgc, source=PARA, version=version)
  if not basePara:
    basePara = '~/text-fabric-data'
  basePara = f'{basePara}/{ORG}'

  locations = [f'{base}/{REPO}', f'{basePhono}/{PHONO}', f'{basePara}/{PARA}']
  modules = [f'tf/{version}']
  localDir = os.path.expanduser(f'{base}/{REPO}/_temp')

  return dict(
      locations=locations,
      modules=modules,
      localDir=localDir,
      provenance=dict(
          corpus=f'BHSA = Biblia Hebraica Stuttgartensia Amstelodamensis ({version})',
          corpusDoi=('10.5281/zenodo.1007624', 'https://doi.org/10.5281/zenodo.1007624'),
      ),
  )


def extraApi(lgc=None):
  cfg = configure(lgc, version=VERSION)
  result = Bhsa(
      None,
      None,
      version=VERSION,
      locations=cfg['locations'],
      modules=cfg['modules'],
      asApi=True,
      lgc=lgc,
  )
  if result.api:
    return result
  return False
