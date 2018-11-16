from tf.applib.appmake import configureNames

protocol = 'http://'
host = 'localhost'
port = 18982
webport = 8002

options = (
    ('lineart', 'checkbox', 'linea', 'show lineart'),
    ('lineNumbers', 'checkbox', 'linen', 'show line numbers'),
)

ORG = 'Nino-cunei'
REPO = 'uruk'
CORPUS = 'Uruk IV/III: Proto-cuneiform tablets '
VERSION = '1.0'
RELATIVE = f'tf/{REPO}'
RELATIVE_IMAGES = 'sources/cdli/images'

DOI = '10.5281/zenodo.1193841'
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
.pnum {
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
.meta {
    display: flex;
    justify-content: flex-start;
    align-items: flex-start;
    align-content: flex-start;
    flex-flow: row nowrap;
}
.features,.comments {
    display: flex;
    justify-content: flex-start;
    align-items: flex-start;
    align-content: flex-start;
    flex-flow: column nowrap;
}
.children {
    display: flex;
    justify-content: flex-start;
    align-items: flex-start;
    align-content: flex-start;
    border: 0;
    background-color: #ffffff;
}
.children.tablet,.children.face {
    flex-flow: row nowrap;
}
.children.column {
    align-items: stretch;
    flex-flow: column nowrap;
}
.children.line,.children.case {
    align-items: stretch;
    flex-flow: row nowrap;
}
.children.caseh,.children.trminalh {
    flex-flow: row nowrap;
}
.children.casev,.children.trminalv {
    flex-flow: column nowrap;
}
.children.trminal {
    flex-flow: row nowrap;
}
.children.cluster {
    flex-flow: row wrap;
}
.children.quad {
    flex-flow: row wrap;
}
.children.sign {
    flex-flow: column nowrap;
}
.contnr {
    width: fit-content;
}
.contnr.tablet,.contnr.face,.contnr.column,
.contnr.line,.contnr.case,.contnr.trminal,
.contnr.comment,
.contnr.cluster,
.contnr.quad,.contnr.sign {
    display: flex;
    justify-content: flex-start;
    align-items: flex-start;
    align-content: flex-start;
    flex-flow: column nowrap;
    background: #ffffff none repeat scroll 0 0;
    padding:  0.5em 0.1em 0.1em 0.1em;
    margin: 0.8em 0.1em 0.1em 0.1em;
    border-radius: 0.2em;
    border-style: solid;
    border-width: 0.2em;
    font-size: small;
}
.contnr.tablet,.contnr.face,.contnr.column {
    border-color: #bb8800;
}
.contnr.line,.contnr.case,.contnr.trminal {
    border-color: #0088bb;
}
.contnr.cluster {
    flex-flow: row wrap;
    border: 0;
}
.contnr.sign,.contnr.quad {
    border-color: #bbbbbb;
}
.contnr.comment {
    background-color: #ffddaa;
    border: 0.2em solid #eecc99;
    border-radius: 0.3em;
}
.contnr.hl {
    background-color: #ffee66;
}
.lbl.tablet,.lbl.face,.lbl.column,
.lbl.line,.lbl.case,.lbl.trminal,
.lbl.comment,
.lbl.cluster,
.lbl.quad,.lbl.sign {
    margin-top: -1.2em;
    margin-left: 1em;
    background: #ffffff none repeat scroll 0 0;
    padding: 0 0.3em;
    border-style: solid;
    font-size: small;
    color: #0000cc;
    display: block;
}
.lbl.tablet,.lbl.face,.lbl.column {
    border-color: #bb8800;
    border-width: 0.2em;
    border-radius: 0.2em;
    color: #bb8800;
}
.lbl.line,.lbl.case,.lbl.trminal {
    border-color: #0088bb;
    border-width: 0.2em;
    border-radius: 0.2em;
    color: #0088bb;
}
.lbl.comment {
    border-color: #eecc99;
    border-width: 0.2em;
    border-radius: 0.2em;
    color: #eecc99;
    background-color: #ffddaa none repeat scroll 0 0;
}
.lbl.clusterB,.lbl.clusterE {
    padding:  0.5em 0.1em 0.1em 0.1em;
    margin: 0.8em 0.1em 0.1em 0.1em;
    color: #888844;
    font-size: x-small;
}
.lbl.clusterB {
    border-left: 0.3em solid #cccc99;
    border-right: 0;
    border-top: 0;
    border-bottom: 0;
    border-radius: 1em;
}
.lbl.clusterE {
    border-left: 0;
    border-right: 0.3em solid #cccc99;
    border-top: 0;
    border-bottom: 0;
    border-radius: 1em;
}
.lbl.quad,.lbl.sign {
    border-color: #bbbbbb;
    border-width: 0.1em;
    border-radius: 0.1em;
    color: #bbbbbb;
}
.op {
    padding:  0.5em 0.1em 0.1em 0.1em;
    margin: 0.8em 0.1em 0.1em 0.1em;
    font-family: monospace;
    font-size: x-large;
    font-weight: bold;
}
.name {
    font-family: monospace;
    font-size: medium;
    color: #0000bb;
}
.period {
    font-family: monospace;
    font-size: medium;
    font-weight: bold;
    color: #0000bb;
}
.excavation {
    font-family: monospace;
    font-size: medium;
    font-style: italic;
    color: #779900;
}
.text {
    font-family: sans-serif;
    font-size: x-small;
    color: #000000;
}
.srcLn {
    font-family: monospace;
    font-size: medium;
    color: #000000;
}
.srcLnNum {
    font-family: monospace;
    font-size: x-small;
    color: #0000bb;
}
</style>
'''


def configure(lgc, version=VERSION):
  return configureNames(globals(), lgc, version)
