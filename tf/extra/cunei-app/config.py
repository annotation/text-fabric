import os
from tf.extra.cunei import Cunei
from tf.apphelpers import hasData

ORG = 'Nino-cunei'
REPO = 'uruk'
CORPUS = 'Uruk IV/III: Proto-cuneiform tablets '
SOURCE = 'uruk'
SOURCE_FULL = 'Uruk IV-III'
SOURCE_DIR = 'sources/cdli'
LOCAL_IMAGE_DIR = 'cdli-imagery'
VERSION = '1.0'
RELEASE = '1.1.0'
RELEASE_FIRST = '1.1.0'

TEMP_DIR = '_temp'
REPORT_DIR = 'reports'

CONDENSE_TYPE = 'tablet'

CHAR_URL = ''


def LIVE(org, repo, version, release):
  return f'{org}/{repo} v:{version} (r{release})'


def LIVE_URL(org, repo, version, release):
  return f'https://github.com/{org}/{repo}/releases/download/{release}/{version}.zip'


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

  live = LIVE(ORG, REPO, version, RELEASE)
  liveUrl = LIVE_URL(ORG, REPO, version, RELEASE)

  return dict(
      locations=locations,
      modules=modules,
      localDir=localDir,
      provenance=(dict(
          corpus=CORPUS,
          version=version,
          release=RELEASE,
          live=(live, liveUrl),
          doi=('10.5281/zenodo.1193841', 'https://doi.org/10.5281/zenodo.1193841'),
      ),),
      url=liveUrl,
      org=ORG,
      repo=REPO,
      charUrl=CHAR_URL,
      source=SOURCE,
      sourceFull=SOURCE_FULL,
      sourceDir=SOURCE_DIR,
      version=VERSION,
      release=RELEASE,
      firstRelease=RELEASE_FIRST,
      tempDir=TEMP_DIR,
      reportDir=REPORT_DIR,
      condenseType=CONDENSE_TYPE,
      localImageDir=LOCAL_IMAGE_DIR,
  )


def extraApi(lgc=None):
  return Cunei(None, asApi=True, version=VERSION, lgc=lgc)
