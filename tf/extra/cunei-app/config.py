import os
from tf.extra.cunei import Cunei
from tf.apphelpers import hasData

ORG = 'Nino-cunei'
REPO = 'uruk'
VERSION = '1.0'

PROVENANCE = dict(
    corpus=f'Uruk IV/III: Proto-cuneiform tablets ({VERSION})',
    corpusDoi=('10.5281/zenodo.1193841', 'https://doi.org/10.5281/zenodo.1193841'),
)

protocol = 'http://'
host = 'localhost'
port = 18982
webport = 8002

options = (
    ('lineart', 'checkbox', 'linea', 'show lineart'),
    ('lineNumbers', 'checkbox', 'linen', 'show line numbers'),
)


def configure(lgc):
  base = hasData(lgc, f'{ORG}/{REPO}/tf/{REPO}', VERSION)
  if not base:
    base = '~/text-fabric-data'

  DATABASE = f'{base}/{ORG}'
  locations = [f'{DATABASE}/{REPO}/tf/{REPO}/{VERSION}']
  modules = ['']
  localDir = os.path.expanduser(f'{DATABASE}/{REPO}/_temp')

  return dict(
      locations=locations,
      modules=modules,
      localDir=localDir,
  )


def extraApi(lgc=None):
  return Cunei(None, asApi=True, lgc=lgc)
