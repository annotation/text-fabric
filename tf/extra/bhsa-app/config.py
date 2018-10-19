import os
from tf.extra.bhsa import Bhsa
from tf.apphelpers import hasData, TFDOC_URL

ORG = 'etcbc'
REPO = 'bhsa'
CORPUS = 'BHSA = Biblia Hebraica Stuttgartensia Amstelodamensis'
VERSION = 'c'
RELEASE = '1.4'
RELEASE_FIRST = '1.3'
DOI = '10.5281/zenodo.1007624'
DOI_URL = 'https://doi.org/10.5281/zenodo.1007624'

DOC_URL = f'https://{ORG}.github.io/{REPO}'
CHAR_URL = TFDOC_URL('/Writing/Hebrew/')
DOC_INTRO = '0_home'

RELATIVE = '{}/tf'


def LIVE(org, repo, version, release):
  return f'{org}/{repo} v:{version} (r{release})'


def LIVE_URL(org, repo, version, release):
  return f'https://github.com/{org}/{repo}/releases/download/{release}/{version}.zip'


MODULES = (
    dict(
        org=ORG,
        repo='phono',
        corpus='Phonetic Transcriptions',
        release='1.1',
        firstRelease='1.0.1',
        doi=('10.5281/zenodo.1007636', 'https://doi.org/10.5281/zenodo.1007636'),
    ),
    dict(
        org=ORG,
        repo='parallels',
        corpus='Parallel Passages',
        release='1.1',
        firstRelease='1.0.1',
        doi=('10.5281/zenodo.1007642', 'https://doi.org/10.5281/zenodo.1007642'),
    ),
)
ZIP = [REPO] + [m['repo'] for m in MODULES]


def VMODULES(version):
  vmodules = []
  for mod in MODULES:
    repo = mod['repo']
    release = mod['release']
    live = LIVE(ORG, repo, version, release)
    liveUrl = LIVE_URL(ORG, repo, version, release)
    vmod = {}
    vmod.update(mod)
    vmod['version'] = version
    vmod['live'] = (live, liveUrl)
    vmod['url'] = liveUrl
    vmodules.append(vmod)
  return tuple(vmodules)


CONDENSE_TYPE = 'verse'

SHEBANQ_URL = 'https://shebanq.ancient-data.org/hebrew'

SHEBANQ = (
    f'{SHEBANQ_URL}/text'
    '?book={book}&chapter={chapter}&verse={verse}&version={version}'
    '&mr=m&qw=q&tp=txt_p&tr=hb&wget=v&qget=v&nget=vt'
)

SHEBANQ_LEX = (
    f'{SHEBANQ_URL}/word'
    '?version={version}&id={lid}'
)

protocol = 'http://'
host = 'localhost'
port = 18981
webport = 8001

options = ()


def configure(lgc, version=VERSION):
  base = hasData(lgc, f'{ORG}/{REPO}/tf', version)

  if not base:
    base = '~/text-fabric-data'
  base = f'{base}/{ORG}'

  baseModules = []
  for module in MODULES:
    repo = module['repo']
    baseModule = hasData(lgc, f'{ORG}/{repo}/tf', version)
    if not baseModule:
      baseModule = '~/text-fabric-data'
    baseModule = f'{baseModule}/{ORG}'
    baseModules.append(f'{baseModule}/{repo}')

  locations = [f'{base}/{REPO}'] + baseModules
  modules = [f'tf/{version}']
  localDir = os.path.expanduser(f'{base}/{REPO}/_temp')

  live = LIVE(ORG, REPO, version, RELEASE)
  liveUrl = LIVE_URL(ORG, REPO, version, RELEASE)

  vModules = VMODULES(version)

  return dict(
      locations=locations,
      modules=modules,
      moduleSpecs=tuple(
          {
              k: v
              for (k, v) in m.items()
              if k in {'url', 'org', 'repo', 'release', 'firstRelease'}
          }
          for m in vModules
      ),
      localDir=localDir,
      provenance=(dict(
          corpus=CORPUS,
          version=version,
          release=RELEASE,
          live=(live, liveUrl),
          doi=(DOI, DOI_URL),
      ),) + vModules,
      url=liveUrl,
      org=ORG,
      repo=REPO,
      version=VERSION,
      release=RELEASE,
      firstRelease=RELEASE_FIRST,
      charUrl=CHAR_URL,
      docUrl=DOC_URL,
      docIntro=DOC_INTRO,
      condenseType=CONDENSE_TYPE,
      shebanq=SHEBANQ,
      shebanqLex=SHEBANQ_LEX,
  )


def extraApi(lgc=None):
  cfg = configure(lgc, version=VERSION)
  result = Bhsa(
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
