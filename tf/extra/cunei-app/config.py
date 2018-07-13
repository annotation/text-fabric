import os
from tf.extra.cunei import Cunei
from tf.apphelpers import hasData, GH_BASE

ORG = 'Nino-cunei'
REPO = 'uruk'
VERSION = '1.0'

base = hasData(f'{ORG}/{REPO}/tf/{REPO}', GH_BASE, VERSION)
if not base:
  base = '~/text-fabric-data'

DATABASE = f'{base}/{ORG}'

PROVENANCE = dict(
    corpus=f'Uruk IV/III: Proto-cuneiform tablets ({VERSION})',
    corpusDoi=('10.5281/zenodo.1193841', 'https://doi.org/10.5281/zenodo.1193841'),
)

locations = [f'{DATABASE}/{REPO}/tf/{REPO}/{VERSION}']
modules = ['']

localDir = os.path.expanduser(f'{DATABASE}/{REPO}/_temp')

protocol = 'http://'
host = 'localhost'
port = 18982
webport = 8002

options = (
    ('lineart', 'checkbox', 'linea', 'show lineart'),
    ('lineNumbers', 'checkbox', 'linen', 'show line numbers'),
)


def extraApi(locations, modules):
  return Cunei(None, asApi=True)
