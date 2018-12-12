import sys
from zipfile import ZIP_DEFLATED


VERSION = '7.2.2'
NAME = 'Text-Fabric'

URL_GH_API = 'https://api.github.com/repos'
URL_GH = 'https://github.com'
URL_NB = 'https://nbviewer.jupyter.org/github'
GH_BASE = '~/github'
EXPRESS_BASE = '~/text-fabric-data'
EXPRESS_INFO = '__release.txt'
URL_TFDOC = 'https://dans-labs.github.io/text-fabric'

DOI_TEXT = '10.5281/zenodo.592193'
DOI_URL = 'https://doi.org/10.5281/zenodo.592193'

APIREF = 'https://dans-labs.github.io/text-fabric/Api/General/'
TUTORIAL = 'https://github.com/Dans-labs/text-fabric/blob/master/docs/tutorial.ipynb'

DATA = 'https://github.com/Dans-labs/text-fabric-data'

LOCATIONS = [
    '~/Downloads/text-fabric-data',
    '~/text-fabric-data',
    '~/github/text-fabric-data',
    '~/Dropbox/text-fabric-data',
    '/mnt/shared/text-fabric-data',
]

GZIP_LEVEL = 2
PICKLE_PROTOCOL = 4

ZIP_OPTIONS = dict(
    compression=ZIP_DEFLATED,
)
if sys.version_info[1] >= 7:
  ZIP_OPTIONS['compresslevel'] = 6
