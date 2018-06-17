from tf.extra.cunei import Cunei

BASE = '~/github'
ORG = 'Nino-cunei'
REPO = 'uruk'
VERSION = '1.0'
DATABASE = f'{BASE}/{ORG}'
TF = f'{REPO}/tf/uruk/{VERSION}'

locations = [DATABASE]
modules = [TF]

protocol = 'http://'
host = 'localhost'
port = 18982
webport = 8002


def maxiApi(locations, modules):
  return Cunei(BASE, f'{ORG}/{REPO}', None, asApi=True)
