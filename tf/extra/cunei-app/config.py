import os
from tf.extra.cunei import Cunei
from tf.apphelpers import hasData, EXPRESS_BASE

ORG = 'Nino-cunei'
REPO = 'uruk'
VERSION = '1.0'
RELATIVE = f'tf/{REPO}'
RELATIVE_IMAGES = 'sources/cdli/images'

CORPUS = 'Uruk IV/III: Proto-cuneiform tablets '
CORPUS_SHORT = 'Uruk IV-III'
LOCAL_IMAGE_DIR = 'cdli-imagery'

ZIP = [REPO, (REPO, RELATIVE_IMAGES)]

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


def configure(lgc, moduleRefs=(), version=VERSION):
  base = hasData(lgc, ORG, REPO, version, RELATIVE)

  if not base:
    base = EXPRESS_BASE
  base = f'{base}/{ORG}'

  localDir = os.path.expanduser(f'{base}/{REPO}/_temp')

  return dict(
      modules=(),
      localDir=localDir,
      provenance=(dict(
          corpus=CORPUS,
          version=version,
          doi=(DOI, DOI_URL),
      ),),
      org=ORG,
      repo=REPO,
      version=VERSION,
      relative=RELATIVE,
      relativeImages=RELATIVE_IMAGES,
      charUrl=CHAR_URL,
      corpusShort=CORPUS_SHORT,
      tempDir=TEMP_DIR,
      reportDir=REPORT_DIR,
      condenseType=CONDENSE_TYPE,
      localImageDir=LOCAL_IMAGE_DIR,
  )


def extraApi(moduleRefs=(), lgc=None, check=False):
  return Cunei(
      name=None,
      asApp=True,
      moduleRefs=moduleRefs,
      version=VERSION,
      lgc=lgc,
      check=check,
  )
