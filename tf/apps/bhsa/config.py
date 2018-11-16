from tf.applib.appmake import configureNames

protocol = 'http://'
host = 'localhost'
port = 18981
webport = 8001

options = ()

ORG = 'etcbc'
REPO = 'bhsa'
CORPUS = 'BHSA = Biblia Hebraica Stuttgartensia Amstelodamensis'
VERSION = 'c'
RELATIVE = 'tf'

DOI = '10.5281/zenodo.1007624'
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
        doi=('10.5281/zenodo.1007636', 'https://doi.org/10.5281/zenodo.1007636'),
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
        doi=('10.5281/zenodo.1007642', 'https://doi.org/10.5281/zenodo.1007642'),
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
    kq_hybrid
    kq_hybrid_utf8
    languageISO
    lex0
    lexeme_count
    mother_object_type
    suffix_gender
    suffix_number
    suffix_person
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

CSS = '''
<style type="text/css">
.features {
    font-family: monospace;
    font-size: medium;
    font-weight: bold;
    color: #0a6611;
    display: flex;
    flex-flow: column nowrap;
    padding: 0.1em;
    margin: 0.1em;
    direction: ltr;
}
.features div,.features span {
    padding: 0;
    margin: -0.1rem 0;
}
.features .f {
    font-family: sans-serif;
    font-size: x-small;
    font-weight: normal;
    color: #5555bb;
}
.features .xft {
  color: #000000;
  background-color: #eeeeee;
  font-size: medium;
  margin: 0.1em 0em;
}
.features .xft .f {
  color: #000000;
  background-color: #eeeeee;
  font-style: italic;
  font-size: small;
  font-weight: normal;
}
.verse {
    display: flex;
    flex-flow: row wrap;
    direction: rtl;
}
.vl {
    display: flex;
    flex-flow: column nowrap;
    justify-content: flex-end;
    align-items: flex-end;
    direction: ltr;
    width: 100%;
}
.outeritem {
    display: flex;
    flex-flow: row wrap;
    direction: rtl;
}
.sentence,.clause,.phrase {
    margin-top: -1.2em;
    margin-left: 1em;
    background: #ffffff none repeat scroll 0 0;
    padding: 0 0.3em;
    border-style: solid;
    border-radius: 0.2em;
    font-size: small;
    display: block;
    width: fit-content;
    max-width: fit-content;
    direction: ltr;
}
.atoms {
    display: flex;
    flex-flow: row wrap;
    margin: 0.3em;
    padding: 0.3em;
    direction: rtl;
    background-color: #ffffff;
}
.satom,.catom,.patom {
    margin: 0.3em;
    padding: 0.3em;
    border-radius: 0.3em;
    border-style: solid;
    display: flex;
    flex-flow: column nowrap;
    direction: rtl;
    background-color: #ffffff;
}
.sentence {
    border-color: #aa3333;
    border-width: 1px;
}
.clause {
    border-color: #aaaa33;
    border-width: 1px;
}
.phrase {
    border-color: #33aaaa;
    border-width: 1px;
}
.satom {
    border-color: #aa3333;
    border-width: 4px;
}
.catom {
    border-color: #aaaa33;
    border-width: 3px;
}
.patom {
    border-color: #33aaaa;
    border-width: 3px;
}
.word {
    padding: 0.1em;
    margin: 0.1em;
    border-radius: 0.1em;
    border: 1px solid #cccccc;
    display: flex;
    flex-flow: column nowrap;
    direction: rtl;
    background-color: #ffffff;
}
.lextp {
    padding: 0.1em;
    margin: 0.1em;
    border-radius: 0.1em;
    border: 2px solid #888888;
    width: fit-content;
    display: flex;
    flex-flow: column nowrap;
    direction: rtl;
    background-color: #ffffff;
}
.occs {
    font-size: x-small;
}
.satom.l,.catom.l,.patom.l {
    border-left-style: dotted
}
.satom.r,.catom.r,.patom.r {
    border-right-style: dotted
}
.satom.L,.catom.L,.patom.L {
    border-left-style: none
}
.satom.R,.catom.R,.patom.R {
    border-right-style: none
}
.tr,.tr a:visited,.tr a:link {
    font-family: sans-serif;
    font-size: large;
    color: #000044;
    direction: ltr;
    text-decoration: none;
}
.trb,.trb a:visited,.trb a:link {
    font-family: sans-serif;
    font-size: normal;
    direction: ltr;
    text-decoration: none;
}
.prb,.prb a:visited,.prb a:link {
    font-family: sans-serif;
    font-size: large;
    direction: ltr;
    text-decoration: none;
}
.h,.h a:visited,.h a:link {
    font-family: "Ezra SIL", "SBL Hebrew", sans-serif;
    font-size: large;
    color: #000044;
    direction: rtl;
    text-decoration: none;
}
.hb,.hb a:visited,.hb a:link {
    font-family: "Ezra SIL", "SBL Hebrew", sans-serif;
    font-size: large;
    line-height: 1.8;
    direction: rtl;
    text-decoration: none;
}
.vn {
  font-size: small !important;
  padding-right: 1em;
}
.rela,.function,.typ {
    font-family: monospace;
    font-size: small;
    color: #0000bb;
}
.pdp,.pdp a:visited,.pdp a:link {
    font-family: monospace;
    font-size: medium;
    color: #0000bb;
    text-decoration: none;
}
.voc_lex {
    font-family: monospace;
    font-size: medium;
    color: #0000bb;
}
.vs {
    font-family: monospace;
    font-size: medium;
    font-weight: bold;
    color: #0000bb;
}
.vt {
    font-family: monospace;
    font-size: medium;
    font-weight: bold;
    color: #0000bb;
}
.gloss {
    font-family: sans-serif;
    font-size: small;
    font-weight: normal;
    color: #444444;
}
.vrs {
    font-family: sans-serif;
    font-size: small;
    font-weight: bold;
    color: #444444;
}
.nd {
    font-family: monospace;
    font-size: x-small;
    color: #999999;
}
.hl {
    background-color: #ffee66;
}
</style>
'''


def configure(lgc, version=VERSION):
  return configureNames(globals(), lgc, version)
