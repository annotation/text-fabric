import os
from tf.extra.peshitta import Peshitta
from tf.apphelpers import hasData, TFDOC_URL

ORG = 'etcbc'
REPO = 'peshitta'
CORPUS = 'Peshitta'
VERSION = '0.1'
RELATIVE = 'tf'

DOI = '10.5281/zenodo.1463675'
DOI_URL = 'https://doi.org/10.5281/zenodo.1463675'
DOC_URL = f'https://github.com/{ORG}/{REPO}/blob/master/docs'
CHAR_URL = '{}/Writing/Syriac/'
CHAR_URL = TFDOC_URL('/Writing/Syriac/')
ZIP = [REPO]

CONDENSE_TYPE = 'verse'

PLAIN_LINK = (
    f'https://github.com/{ORG}/{REPO}/blob/master'
    '/source/{version}/{book}'
)


protocol = 'http://'
host = 'localhost'
port = 18983
webport = 8003

options = ()


def configure(lgc, version=VERSION):
  base = hasData(lgc, ORG, REPO, version, RELATIVE)

  if not base:
    base = '~/text-fabric-data'
  base = f'{base}/{ORG}'

  locations = [f'{base}/{REPO}/{RELATIVE}']
  modules = [version]
  localDir = os.path.expanduser(f'{base}/{REPO}/_temp')

  return dict(
      locations=locations,
      modules=modules,
      localDir=localDir,
      provenance=(dict(
          corpus=CORPUS,
          version=version,
          doi=(DOI, DOI_URL),
      ),),
      org=ORG,
      repo=REPO,
      relative=RELATIVE,
      version=VERSION,
      charUrl=CHAR_URL,
      docUrl=DOC_URL,
      condenseType=CONDENSE_TYPE,
      plainLink=PLAIN_LINK,
  )


def extraApi(lgc=None, check=False):
  cfg = configure(lgc, version=VERSION)
  result = Peshitta(
      None,
      None,
      version=VERSION,
      locations=cfg['locations'],
      modules=cfg['modules'],
      asApp=True,
      lgc=lgc,
      check=check,
  )
  if result.api:
    return result
  return False
