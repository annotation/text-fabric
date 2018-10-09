import os
from tf.extra.cunei import Cunei
from tf.apphelpers import hasData

ORG = 'Nino-cunei'
REPO = 'uruk'
VERSION = '1.0'

protocol = 'http://'
host = 'localhost'
port = 18982
webport = 8002

options = (
    ('lineart', 'checkbox', 'linea', 'show lineart'),
    ('lineNumbers', 'checkbox', 'linen', 'show line numbers'),
)


def configure(lgc, version=VERSION):
  base = hasData(lgc, f'{ORG}/{REPO}/tf/{REPO}', version)
  if not base:
    base = '~/text-fabric-data'

  DATABASE = f'{base}/{ORG}'
  locations = [f'{DATABASE}/{REPO}/tf/{REPO}/{version}']
  modules = ['']
  localDir = os.path.expanduser(f'{DATABASE}/{REPO}/_temp')

  return dict(
      locations=locations,
      modules=modules,
      localDir=localDir,
      provenance=dict(
          corpus=f'Uruk IV/III: Proto-cuneiform tablets ({version})',
          corpusDoi=('10.5281/zenodo.1193841', 'https://doi.org/10.5281/zenodo.1193841'),
      )
  )


def extraApi(lgc=None):
  return Cunei(None, asApi=True, version=VERSION, lgc=lgc)
