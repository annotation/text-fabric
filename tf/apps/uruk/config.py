from os.path import dirname, abspath

PROTOCOL = 'http://'
HOST = 'localhost'
PORT = dict(
    kernel=18984,
    web=8104,
)

OPTIONS = (
    ('lineart', True, 'checkbox', 'linea', 'show lineart'),
    ('lineNumbers', False, 'checkbox', 'linen', 'show line numbers'),
)

ORG = 'Nino-cunei'
REPO = 'uruk'
CORPUS = 'Uruk IV/III: Proto-cuneiform tablets '
VERSION = '1.0'
RELATIVE = f'tf/{REPO}'
RELATIVE_IMAGES = 'sources/cdli/images'

DOI_TEXT = '10.5281/zenodo.1193841'
DOI_URL = 'https://doi.org/10.5281/zenodo.1193841'

DOC_URL = f'https://github.com/{ORG}/{REPO}/blob/master/docs/'
DOC_INTRO = 'about.md'
CHAR_URL = f'https://github.com/{ORG}/{REPO}/blob/master/docs/transcription.md'
CHAR_TEXT = 'How TF features represent ATF'

FEATURE_URL = f'{DOC_URL}/transcription.md'

MODULE_SPECS = ()

ZIP = [REPO, (ORG, REPO, RELATIVE_IMAGES)]

CONDENSE_TYPE = 'tablet'

NONE_VALUES = {None}

STANDARD_FEATURES = None  # meaning all loadable features

EXCLUDED_FEATURES = set()

NO_DESCEND_TYPES = {'lex'}

EXAMPLE_SECTION = '<code>P005381</code>'
EXAMPLE_SECTION_TEXT = 'P005381'

SECTION_SEP1 = ' '
SECTION_SEP2 = ':'

DEFAULT_CLS = ''
DEFAULT_CLS_ORIG = ''
FORMAT_CSS = dict(
    orig=DEFAULT_CLS_ORIG,
    trans=DEFAULT_CLS,
)

CLASS_NAMES = None

FONT_NAME = None
FONT = None
FONTW = None


def deliver():
  return (globals(), dirname(abspath(__file__)))
