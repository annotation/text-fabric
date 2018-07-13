import os
from tf.extra.bhsa import Bhsa, hasTf

ORG = 'etcbc'
REPO = 'bhsa'
VERSION = 'c'

PHONO = 'phono'
PARA = 'parallels'

base = hasTf(source=REPO, version=VERSION)
if not base:
  base = '~/text-fabric-data'
base = f'{base}/{ORG}'

basePhono = hasTf(source=PHONO, version=VERSION)
if not basePhono:
  basePhono = '~/text-fabric-data'
basePhono = f'{basePhono}/{ORG}'

basePara = hasTf(source=PARA, version=VERSION)
if not basePara:
  basePara = '~/text-fabric-data'
basePara = f'{basePara}/{ORG}'

PROVENANCE = dict(
    corpus=f'BHSA = Biblia Hebraica Stuttgartensia Amstelodamensis ({VERSION})',
    corpusDoi=('10.5281/zenodo.1007624', 'https://doi.org/10.5281/zenodo.1007624'),
)


locations = [f'{base}/{REPO}', f'{basePhono}/{PHONO}', f'{basePara}/{PARA}']
modules = [f'tf/{VERSION}']

localDir = os.path.expanduser(f'{base}/{REPO}/_temp')

protocol = 'http://'
host = 'localhost'
port = 18981
webport = 8001

options = ()


def extraApi(locations, modules):
  result = Bhsa(
      None,
      None,
      version=VERSION,
      locations=locations,
      modules=modules,
      asApi=True
  )
  if result.api:
    return result
  return False
