from os.path import dirname, abspath

PROTOCOL = 'http://'
HOST = 'localhost'
PORT = dict(
    kernel=18983,
    web=8103,
)

OPTIONS = ()

ORG = 'etcbc'
REPO = 'syrnt'
CORPUS = 'SyrNT'
VERSION = '0.1'
RELATIVE = 'tf'

DOI_TEXT = '10.5281/zenodo.1464787'
DOI_URL = 'https://doi.org/10.5281/zenodo.1464787'

DOC_URL = f'https://github.com/{ORG}/{REPO}/blob/master/docs'
DOC_INTRO = 'transcription.md'
CHAR_URL = '{tfDoc}/Writing/Syriac'
CHAR_TEXT = 'Syriac characters and transcriptions',

FEATURE_URL = f'{DOC_URL}/transcription-{{version}}.md#{{feature}}'

MODULE_SPECS = ()

ZIP = [REPO]

CONDENSE_TYPE = 'verse'

NONE_VALUES = {None, 'NA', 'none', 'unknown'}

STANDARD_FEATURES = '''
    word word_etcbc
    sp vs vt
    lexeme lexeme_etcbc
    book book@en
    chapter verse
'''.strip().split()

EXCLUDED_FEATURES = set()

NO_DESCEND_TYPES = {'lex'}

EXAMPLE_SECTION = (
    f'<code>Matthew 1:1</code> (use'
    f' <a href="https://github.com/{ORG}/{REPO}'
    f'/blob/master/tf/{VERSION}/book%40en.tf" target="_blank">'
    f'English book names</a>)'
)
EXAMPLE_SECTION_TEXT = 'Matthew 1:1'

SECTION_SEP1 = ' '
SECTION_SEP2 = ':'

DEFAULT_CLS = 'trb'
DEFAULT_CLS_ORIG = 'syb'
FORMAT_CSS = dict(
    orig=DEFAULT_CLS_ORIG,
    trans=DEFAULT_CLS,
)

CLASS_NAMES = dict(
    verse='verse',
    word='word',
    lex='lextp',
)

FONT_NAME = 'Estrangelo Edessa'
FONT = 'SyrCOMEdessa.otf'
FONTW = 'SyrCOMEdessa.woff'


def deliver():
  return (globals(), dirname(abspath(__file__)))
