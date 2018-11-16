from tf.applib.appmake import configureNames

protocol = 'http://'
host = 'localhost'
port = 18984
webport = 8004

options = ()

ORG = 'etcbc'
REPO = 'syrnt'
CORPUS = 'SyrNT'
VERSION = '0.1'
RELATIVE = 'tf'

DOI = '10.5281/zenodo.1464787'
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
.sy,.sy a:visited,.sy a:link {
    font-family: "Estrangelo Edessa", sans-serif;
    font-size: large;
    color: #000044;
    direction: rtl;
    text-decoration: none;
}
.syb,.syb a:visited,.syb a:link {
    font-family: "Estrangelo Edessa", sans-serif;
    font-size: large;
    direction: rtl;
    text-decoration: none;
}
.vn {
  font-size: small !important;
  padding-right: 1em;
}
.sp,.sp a:visited,.sp a:link {
    font-family: monospace;
    font-size: medium;
    color: #0000bb;
    text-decoration: none;
}
.lexeme {
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
