import os
from tf.extra.bhsa import Bhsa

BASE = '~/github'
ORG = 'etcbc'
REPO = 'bhsa'
VERSION = '2017'
DATABASE = f'{BASE}/{ORG}'
BHSA = f'{REPO}/tf/{VERSION}'
PHONO = f'phono/tf/{VERSION}'
PARALLELS = f'parallels/tf/{VERSION}'

locations = [DATABASE]
modules = [BHSA, PHONO, PARALLELS]

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
