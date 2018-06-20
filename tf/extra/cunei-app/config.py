import os
from tf.extra.cunei import Cunei

BASE = '~/github'
ORG = 'Nino-cunei'
REPO = 'uruk'
VERSION = '1.0'
DATABASE = f'{BASE}/{ORG}'
TF = f'{REPO}/tf/uruk/{VERSION}'

locations = [DATABASE]
modules = [TF]

localDir = os.path.expanduser(f'{DATABASE}/{REPO}/_temp')

protocol = 'http://'
host = 'localhost'
port = 18982
webport = 8002

options = (
    ('lineart', 'lineart', 'checkbox', 'linea', 'show lineart'),
    ('linenumbers', 'lineNumbers', 'checkbox', 'linen', 'show line numbers'),
)

condenseType = 'tablet'


def extraApi(locations, modules):
  return Cunei(BASE, f'{ORG}/{REPO}', None, asApi=True)
