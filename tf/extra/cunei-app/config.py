import os
from tf.extra.cunei import Cunei
from tf.apphelpers import hasData

ORG = 'Nino-cunei'
REPO = 'uruk'
VERSION = '1.0'
RELATIVE = f'tf/{REPO}'

CORPUS = 'Uruk IV/III: Proto-cuneiform tablets '
CORPUS_SHORT = 'Uruk IV-III'
SOURCE_DIR = 'sources/cdli'
LOCAL_IMAGE_DIR = 'cdli-imagery'

DOI = '10.5281/zenodo.1193841'
DOI_URL = 'https://doi.org/10.5281/zenodo.1193841'

TEMP_DIR = '_temp'
REPORT_DIR = 'reports'

CONDENSE_TYPE = 'tablet'

CHAR_URL = ''

protocol = 'http://'
host = 'localhost'
port = 18982
webport = 8002

options = (
    ('lineart', 'checkbox', 'linea', 'show lineart'),
    ('lineNumbers', 'checkbox', 'linen', 'show line numbers'),
)


def configure(lgc, version=VERSION):
  base = hasData(lgc, ORG, REPO, version, RELATIVE)
  if not base:
    base = '~/text-fabric-data'

  DATABASE = f'{base}/{ORG}'
  locations = [f'{DATABASE}/{REPO}/{RELATIVE}/{version}']
  modules = ['']
  localDir = os.path.expanduser(f'{DATABASE}/{REPO}/_temp')

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
      charUrl=CHAR_URL,
      corpusShort=CORPUS_SHORT,
      sourceDir=SOURCE_DIR,
      version=VERSION,
      tempDir=TEMP_DIR,
      reportDir=REPORT_DIR,
      condenseType=CONDENSE_TYPE,
      localImageDir=LOCAL_IMAGE_DIR,
  )


def extraApi(lgc=None, check=False):
  return Cunei(None, asApp=True, version=VERSION, lgc=lgc, check=check)
