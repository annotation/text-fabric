import os
from tf.extra.bhsa import Bhsa
from tf.apphelpers import hasData

ORG = 'etcbc'
REPO = 'bhsa'
VERSION = 'c'

GH_BASE = '~/github'

base = hasData(f'{ORG}/{REPO}/tf', GH_BASE, VERSION)
if not base:
  base = '~/text-fabric-data'

DATABASE = f'{base}/{ORG}'
BHSA = f'{REPO}/tf/{VERSION}'
PHONO = f'phono/tf/{VERSION}'
PARALLELS = f'parallels/tf/{VERSION}'

PROVENANCE = dict(
    corpus=f'BHSA = Biblia Hebraica Stuttgartensia Amstelodamensis ({VERSION})',
    corpusDoi=('10.5281/zenodo.1007624', 'https://doi.org/10.5281/zenodo.1007624'),
)

locations = [f'{DATABASE}/{BHSA}', f'{GH_BASE}/{ORG}/{PHONO}', f'{GH_BASE}/{ORG}/{PARALLELS}']
modules = ['']

localDir = os.path.expanduser(f'{DATABASE}/{REPO}/_temp')

protocol = 'http://'
host = 'localhost'
port = 18981
webport = 8001

options = ()

condenseType = 'verse'


def extraApi(locations, modules):
  return Bhsa(
      None,
      None,
      version=VERSION,
      locations=locations,
      modules=modules,
      asApi=True
  )
