import os
from tf.extra.syrnt import Syrnt
from tf.apphelpers import hasData, TFDOC_URL

ORG = 'etcbc'
REPO = 'syrnt'
CORPUS = 'SyrNT'
VERSION = '0.1'
RELEASE = '0.2'
RELEASE_FIRST = '0.1'
DOI = '10.5281/zenodo.1464787'
DOI_URL = 'https://doi.org/10.5281/zenodo.1464787'
DOC_URL = f'https://github.com/{ORG}/{REPO}/blob/master/docs'
CHAR_URL = TFDOC_URL('/Writing/Syriac/')
ZIP = [REPO]


def LIVE(org, repo, version, release):
  return f'{org}/{repo} v:{version} (r{release})'


def LIVE_URL(org, repo, version, release):
  return f'https://github.com/{org}/{repo}/releases/download/{release}/{version}.zip'


CONDENSE_TYPE = 'verse'

PLAIN_LINK = (
    f'https://github.com/{ORG}/{REPO}/blob/master'
    '/plain/{version}/{book}.txt'
)


protocol = 'http://'
host = 'localhost'
port = 18984
webport = 8004

options = ()


def configure(lgc, version=VERSION):
  base = hasData(lgc, f'{ORG}/{REPO}/tf', version)

  if not base:
    base = '~/text-fabric-data'
  base = f'{base}/{ORG}'

  locations = [f'{base}/{REPO}/tf']
  modules = [version]
  localDir = os.path.expanduser(f'{base}/{REPO}/_temp')

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
          doi=(DOI, DOI_URL),
      ),),
      url=liveUrl,
      org=ORG,
      repo=REPO,
      version=VERSION,
      release=RELEASE,
      firstRelease=RELEASE_FIRST,
      charUrl=CHAR_URL,
      docUrl=DOC_URL,
      condenseType=CONDENSE_TYPE,
      plainLink=PLAIN_LINK,
  )


def extraApi(lgc=None):
  cfg = configure(lgc, version=VERSION)
  result = Syrnt(
      None,
      None,
      version=VERSION,
      locations=cfg['locations'],
      modules=cfg['modules'],
      asApi=True,
      lgc=lgc,
  )
  if result.api:
    return result
  return False
