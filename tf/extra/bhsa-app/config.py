import os
from tf.extra.bhsa import Bhsa
from tf.apphelpers import hasData, TFDOC_URL

ORG = 'etcbc'
REPO = 'bhsa'
CORPUS = 'BHSA = Biblia Hebraica Stuttgartensia Amstelodamensis'
VERSION = 'c'
RELATIVE = 'tf'

DOI = '10.5281/zenodo.1007624'
DOI_URL = 'https://doi.org/10.5281/zenodo.1007624'

DOC_URL = f'https://{ORG}.github.io/{REPO}'
CHAR_URL = TFDOC_URL('/Writing/Hebrew/')
DOC_INTRO = '0_home'


MODULES = (
    dict(
        org=ORG,
        repo='phono',
        relative=RELATIVE,
        corpus='Phonetic Transcriptions',
        doi=('10.5281/zenodo.1007636', 'https://doi.org/10.5281/zenodo.1007636'),
    ),
    dict(
        org=ORG,
        repo='parallels',
        relative=RELATIVE,
        corpus='Parallel Passages',
        doi=('10.5281/zenodo.1007642', 'https://doi.org/10.5281/zenodo.1007642'),
    ),
)
ZIP = [REPO] + [m['repo'] for m in MODULES]


def VMODULES(version):
  vmodules = []
  for mod in MODULES:
    vmod = {}
    vmod.update(mod)
    vmod['version'] = version
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
  base = hasData(lgc, ORG, REPO, version, RELATIVE)

  if not base:
    base = '~/text-fabric-data'
  base = f'{base}/{ORG}'

  baseModules = []
  for module in MODULES:
    repo = module['repo']
    relative = module['relative']
    baseModule = hasData(lgc, ORG, repo, version, relative)
    if not baseModule:
      baseModule = '~/text-fabric-data'
    baseModule = f'{baseModule}/{ORG}'
    baseModules.append(f'{baseModule}/{repo}')

  locations = [f'{base}/{REPO}'] + baseModules
  modules = [f'{RELATIVE}/{version}']
  localDir = os.path.expanduser(f'{base}/{REPO}/_temp')

  vModules = VMODULES(version)

  return dict(
      locations=locations,
      modules=modules,
      moduleSpecs=tuple(
          {
              k: v
              for (k, v) in m.items()
              if k in {'url', 'org', 'repo', 'relative'}
          }
          for m in vModules
      ),
      localDir=localDir,
      provenance=(dict(
          corpus=CORPUS,
          version=version,
          doi=(DOI, DOI_URL),
      ),) + vModules,
      org=ORG,
      repo=REPO,
      relative=RELATIVE,
      version=VERSION,
      charUrl=CHAR_URL,
      docUrl=DOC_URL,
      docIntro=DOC_INTRO,
      condenseType=CONDENSE_TYPE,
      shebanq=SHEBANQ,
      shebanqLex=SHEBANQ_LEX,
  )


def extraApi(lgc=None, check=False):
  cfg = configure(lgc, version=VERSION)
  result = Bhsa(
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
