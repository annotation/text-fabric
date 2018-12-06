from os.path import dirname, abspath

PROTOCOL = 'http://'
HOST = 'localhost'
PORT = dict(
    kernel=18981,
    web=8101,
)

OPTIONS = ()

ORG = 'etcbc'
REPO = 'bhsa'
CORPUS = 'BHSA = Biblia Hebraica Stuttgartensia Amstelodamensis'
VERSION = 'c'
RELATIVE = 'tf'

DOI_TEXT = '10.5281/zenodo.1007624'
DOI_URL = 'https://doi.org/10.5281/zenodo.1007624'

DOC_URL = f'https://{ORG}.github.io/{REPO}'
DOC_INTRO = '0_home'
CHAR_URL = '{tfDoc}/Writing/Hebrew'
CHAR_TEXT = 'Hebrew characters and transcriptions',

FEATURE_URL = f'{DOC_URL}/features/hebrew/{{version}}/{{feature}}.html'

MODULE_SPECS = (
    dict(
        org=ORG,
        repo='phono',
        relative=RELATIVE,
        corpus='Phonetic Transcriptions',
        docUrl=(
            'https://nbviewer.jupyter.org/github/etcbc/phono'
            '/blob/master/programs/phono.ipynb'
        ),
        doiText='10.5281/zenodo.1007636',
        doiUrl='https://doi.org/10.5281/zenodo.1007636',
    ),
    dict(
        org=ORG,
        repo='parallels',
        relative=RELATIVE,
        corpus='Parallel Passages',
        docUrl=(
            'https://nbviewer.jupyter.org/github/etcbc/parallels'
            '/blob/master/programs/parallels.ipynb'
        ),
        doiText='10.5281/zenodo.1007642',
        doiUrl='https://doi.org/10.5281/zenodo.1007642',
    ),
)
ZIP = [REPO] + [m['repo'] for m in MODULE_SPECS]

CONDENSE_TYPE = 'verse'

NONE_VALUES = {None, 'NA', 'none', 'unknown'}

STANDARD_FEATURES = '''
    pdp vs vt
    lex language gloss voc_lex voc_lex_utf8
    function typ rela
    number label book
'''
if VERSION in {'4', '4b'}:
  STANDARD_FEATURES.replace('voc_', 'g_')
STANDARD_FEATURES = STANDARD_FEATURES.strip().split()

EXCLUDED_FEATURES = set(
    '''
    crossrefLCS
    crossrefSET
    dist
    dist_unit
    distributional_parent
    domain
    freq_occ
    functional_parent
    g_cons
    g_cons_utf8
    g_lex
    g_lex_utf8
    g_nme
    g_nme_utf8
    g_pfm
    g_pfm_utf8
    g_prs
    g_prs_utf8
    g_uvf
    g_uvf_utf8
    g_vbe
    g_vbe_utf8
    g_vbs
    g_vbs_utf8
    instruction
    is_root
    kind
    kq_hybrid
    kq_hybrid_utf8
    languageISO
    lex0
    lexeme_count
    mother_object_type
    nme
    pargr
    pfm
    prs
    rank_occ
    root
    suffix_gender
    suffix_number
    suffix_person
    tab
    uvf
    vbe
    vbs
'''.strip().split()
)

NO_DESCEND_TYPES = {'lex'}

EXAMPLE_SECTION = (
    f'<code>Genesis 1:1</code> (use'
    f' <a href="https://github.com/{ORG}/{REPO}'
    f'/blob/master/tf/{VERSION}/book%40en.tf" target="_blank">'
    f'English book names</a>)'
)
EXAMPLE_SECTION_TEXT = 'Genesis 1:1'

SECTION_SEP1 = ' '
SECTION_SEP2 = ':'

DEFAULT_CLS = 'trb'
DEFAULT_CLS_ORIG = 'hb'
FORMAT_CSS = dict(
    orig=DEFAULT_CLS_ORIG,
    trans=DEFAULT_CLS,
    phono='prb',
)

CLASS_NAMES = dict(
    verse='verse',
    sentence='atoms',
    sentence_atom='satom',
    clause='atoms',
    clause_atom='catom',
    phrase='atoms',
    phrase_atom='patom',
    subphrase='subphrase',
    word='word',
    lex='lextp',
)

FONT_NAME = 'Ezra SIL'
FONT = 'SILEOT.ttf'
FONTW = 'SILEOT.woff'


def deliver():
  return (globals(), dirname(abspath(__file__)))
