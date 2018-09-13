import os
import re
import types
from IPython.display import display, HTML

from tf.fabric import Fabric
from tf.apphelpers import (
    search,
    table, plainTuple,
    show, prettyPre, pretty, prettyTuple, prettySetup,
    hasData, getData,
    getBoundary, getFeatures,
    htmlEsc, mdEsc,
    dm, header, outLink,
    GH_BASE,
    URL_GH, URL_NB,
)

ORG = 'etcbc'
CORPUS = 'bhsa'

RELEASE = '1.3'

PHONO = 'phono'
PHONO_RL = '1.0.1'
PARA = 'parallels'
PARA_RL = '1.0.1'


SHEBANQ_URL = 'https://shebanq.ancient-data.org/hebrew'
SHEBANQ = (
    f'{SHEBANQ_URL}/text'
    '?book={book}&chapter={chapter}&verse={verse}&version={version}'
    '&mr=m&qw=q&tp=txt_p&tr=hb&wget=v&qget=v&nget=vt'
)
SHEBANQ_LEX = (f'{SHEBANQ_URL}/word' '?version={version}&id={lid}')

CONDENSE_TYPE = 'verse'

CSS = '''
<style type="text/css">
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
    direction: rtl;
    text-decoration: none;
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
.features .f {
    font-family: sans-serif;
    font-size: x-small;
    font-weight: normal;
    color: #5555bb;
}
.word .features div,.word .features span {
    padding: 0;
    margin: -0.1rem 0;
}

.hl {
    background-color: #ffee66;
}
</style>
'''

CSS_FONT = '<link rel="stylesheet" href="/data/static/fonts.css"/>'

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

ATOMS = dict(
    sentence_atom='sentence',
    clause_atom='clause',
    phrase_atom='phrase',
)
SUPER = dict((y, x) for (x, y) in ATOMS.items())

SECTION = {'book', 'chapter', 'verse', 'half_verse'}
VERSE = {'verse', 'half_verse'}

NONE_VALUES = {None, 'NA', 'none', 'unknown'}

STANDARD_FEATURES = '''
    pdp vs vt
    lex language gloss voc_lex voc_lex_utf8
    function typ rela
    number label book
'''

EXCLUDED_FEATURES = set('''
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
'''.strip().split())

# for 4, 4b: voc_lex => g_lex, voc_lex_utf8 => g_lex_utf8

PASSAGE_RE = re.compile('^([A-Za-z0-9_ -]+)\s+([0-9]+)\s*:\s*([0-9]+)$')


def getTf(source='bhsa', release='1.3', version='c', relative='{}/tf'):
  dataUrl = f'https://github.com/{ORG}/{source}/releases/download/{release}/{version}.zip'
  dataRel = f'{ORG}/' + relative.format(source)
  getData(dataUrl, dataRel, GH_BASE, version)


def hasTf(source='bhsa', version='c', relative='{}/tf'):
  dataRel = f'{ORG}/' + relative.format(source)
  return hasData(dataRel, GH_BASE, version)


class Bhsa(object):
  def __init__(
      self,
      api,
      name,
      version='c',
      locations=None,
      modules=None,
      asApi=False,
  ):
    self.asApi = asApi
    self.version = version
    self.condenseType = CONDENSE_TYPE
    self.exampleSection = 'Genesis 1:1'

    standardFeatures = (
        STANDARD_FEATURES.replace('voc_', 'g_') if version in {'4', '4b'} else STANDARD_FEATURES
    )
    self.standardFeatures = set(standardFeatures.strip().split())

    if asApi:
      getTf(source=CORPUS, release=RELEASE, version=version)
      getTf(source=PHONO, release=PHONO_RL, version=version)
      getTf(source=PARA, release=PARA_RL, version=version)
      TF = Fabric(locations=locations, modules=modules, silent=True)
      api = TF.load('', silent=True)
      self.api = api
      if api is False:
        return
      allFeatures = TF.explore(silent=True, show=True)
      loadableFeatures = allFeatures['nodes'] + allFeatures['edges']
      useFeatures = [f for f in loadableFeatures if f not in EXCLUDED_FEATURES]
      result = TF.load(useFeatures, add=True, silent=True)
      if result is False:
        self.api = False
        return
    else:
      api.TF.load(self.standardFeatures, add=True, silent=True)
    self.prettyFeaturesLoaded = self.standardFeatures
    self.prettyFeatures = ()
    self.api = api
    self.cwd = os.getcwd()
    cwdPat = re.compile(f'^.*/github/([^/]+)/([^/]+)((?:/.+)?)$', re.I)
    cwdRel = cwdPat.findall(self.cwd)

    if not asApi:
      if cwdRel:
        (thisOrg, thisRepo, thisPath) = cwdRel[0]
        onlineTail = (f'{thisOrg}/{thisRepo}' f'/blob/master{thisPath}/{name}.ipynb')
      else:
        cwdRel = None
      nbUrl = (None if name is None or cwdRel is None else f'{URL_NB}/{onlineTail}')
      ghUrl = (None if name is None or cwdRel is None else f'{URL_GH}/{onlineTail}')
    docUrl = f'https://etcbc.github.io/bhsa'
    tutUrl = f'{URL_NB}/{ORG}/{CORPUS}/blob/master/tutorial/search.ipynb'
    extraUrl = f'https://dans-labs.github.io/text-fabric/Api/Bhsa/'
    dataLink = outLink(CORPUS.upper(), docUrl, '{provenance of this corpus}')
    featureLink = outLink(
        'Feature docs', f'{docUrl}/features/hebrew/{self.version}/0_home.html',
        '{CORPUS.upper()} feature documentation'
    )
    bhsaLink = outLink('BHSA API', extraUrl, 'BHSA API documentation')
    tfLink = outLink(
        f'Text-Fabric API {api.TF.version}', 'https://dans-labs.github.io/text-fabric/Api/General/',
        'text-fabric-api'
    )
    tfsLink = outLink(
        'Search Reference',
        'https://dans-labs.github.io/text-fabric/Api/General/#search-templates',
        'Search Templates Introduction and Reference'
    )
    tutLink = outLink(
        'Search tutorial', tutUrl,
        'Search tutorial in Jupyter Notebook'
    )
    if asApi:
      self.dataLink = dataLink
      self.featureLink = featureLink
      self.tfsLink = tfsLink
      self.tutLink = tutLink
    else:
      dm('**Documentation:**' f' {dataLink} {featureLink} {bhsaLink} {tfLink} {tfsLink}')
      if nbUrl:
        dm(
            f'''
This notebook online:
{outLink('NBViewer', nbUrl)}
{outLink('GitHub', ghUrl)}
'''
        )

    self.classNames = CLASS_NAMES
    self.noneValues = NONE_VALUES

    if not asApi:
      self.loadCSS()
    self.table = types.MethodType(table, self)
    self.plainTuple = types.MethodType(plainTuple, self)
    self.show = types.MethodType(show, self)
    self.prettyTuple = types.MethodType(prettyTuple, self)
    self.pretty = types.MethodType(pretty, self)
    self.prettySetup = types.MethodType(prettySetup, self)
    self.search = types.MethodType(search, self)
    self.header = types.MethodType(header, self)

  def loadCSS(self):
    asApi = self.asApi
    if asApi:
      return CSS_FONT + CSS
    display(HTML(CSS))

  def shbLink(self, n, text=None, className=None, asString=False, noUrl=False):
    api = self.api
    L = api.L
    T = api.T
    F = api.F
    version = self.version
    nType = F.otype.v(n)
    if nType == 'lex':
      lex = F.lex.v(n)
      lan = F.language.v(n)
      lexId = '{}{}'.format(
          '1' if lan == 'Hebrew' else '2',
          lex.replace('>', 'A').replace('<', 'O').replace('[', 'v').replace('/',
                                                                            'n').replace('=', 'i'),
      )
      href = SHEBANQ_LEX.format(
          version=version,
          lid=lexId,
      )
      title = 'show this lexeme in SHEBANQ'
      if text is None:
        text = htmlEsc(F.voc_lex_utf8.v(n))
      result = outLink(text, href, title=title, className=className)
      if asString:
        return result
      display(HTML(result))
      return

    (bookE, chapter, verse) = T.sectionFromNode(n)
    bookNode = n if nType == 'book' else L.u(n, otype='book')[0]
    book = F.book.v(bookNode)
    passageText = (
        bookE if nType == 'book' else '{} {}'.format(bookE, chapter)
        if nType == 'chapter' else '{} {}:{}{}'.format(bookE, chapter, verse, F.label.v(n))
        if nType == 'half_verse' else '{} {}:{}'.format(bookE, chapter, verse)
    )
    href = '#' if noUrl else SHEBANQ.format(
        version=version,
        book=book,
        chapter=chapter,
        verse=verse,
    )
    if text is None:
      text = passageText
      title = 'show this passage in SHEBANQ'
    else:
      title = passageText
    if noUrl:
      title = None
    target = '' if noUrl else None
    result = outLink(text, href, title=title, className=className, target=target)
    if asString:
      return result
    display(HTML(result))

  def webLink(self, n):
    return self.shbLink(n, className='rwh', asString=True, noUrl=True)

  def nodeFromDefaultSection(self, sectionStr):
    api = self.api
    T = api.T
    match = PASSAGE_RE.match(sectionStr)
    if not match:
      return (f'Wrong shape: "{sectionStr}". Must be "book chapter:verse"', None)
    (book, chapter, verse) = match.groups()
    verseNode = T.nodeFromSection((book, int(chapter), int(verse)))
    if verseNode is None:
      return (f'Not a valid verse: "{sectionStr}"', None)
    return ('', verseNode)

  def plain(
      self,
      n,
      linked=True,
      withNodes=False,
      asString=False,
  ):
    asApi = self.asApi
    api = self.api
    L = api.L
    T = api.T
    F = api.F

    nType = F.otype.v(n)
    result = ''
    if asApi:
      nodeRep = f' <a href="#" class="nd">{n}</a> ' if withNodes else ''
    else:
      nodeRep = f' *{n}* ' if withNodes else ''

    hebrew = True
    if nType == 'word':
      rep = mdEsc(htmlEsc(T.text([n])))
    elif nType in SECTION:
      fmt = ('{}' if nType == 'book' else '{} {}' if nType == 'chapter' else '{} {}:{}')
      rep = fmt.format(*T.sectionFromNode(n))
      hebrew = False
      if nType == 'half_verse':
        rep += F.label.v(n)
      rep = mdEsc(htmlEsc(rep))
      if nType in VERSE:
        if linked:
          rep = self.shbLink(n, text=rep, asString=True)
        rep += ' <span class="hb">' + T.text(L.d(n, otype="word")) + '</span>'
    elif nType == 'lex':
      rep = mdEsc(htmlEsc(F.voc_lex_utf8.v(n)))
    else:
      rep = mdEsc(htmlEsc(T.text(L.d(n, otype='word'))))

    if linked and nType not in VERSE:
      rep = self.shbLink(n, text=rep, asString=True)

    if hebrew:
      rep = f'<span class="hb">{rep}</span>'
    result = f'{rep}{nodeRep}'

    if asString or asApi:
      return result
    dm((result))

  def _pretty(
      self,
      n,
      outer,
      html,
      firstSlot,
      lastSlot,
      condenseType=None,
      withNodes=True,
      suppress=set(),
      highlights={},
  ):
    goOn = prettyPre(
        self,
        n,
        firstSlot,
        lastSlot,
        withNodes,
        highlights,
    )
    if not goOn:
      return
    (
        slotType, nType,
        className, boundaryClass, hlClass, hlStyle,
        nodePart,
        myStart, myEnd,
    ) = goOn

    api = self.api
    F = api.F
    L = api.L
    T = api.T
    sortNodes = api.sortNodes
    otypeRank = api.otypeRank

    bigType = False
    if condenseType is not None and otypeRank[nType] > otypeRank[condenseType]:
      bigType = True

    if nType == 'book':
      html.append(self.shbLink(n, asString=True))
      return
    if nType == 'chapter':
      html.append(self.shbLink(n, asString=True))
      return

    if bigType:
      children = ()
    elif nType in {'verse', 'half_verse'}:
      (thisFirstSlot, thisLastSlot) = getBoundary(api, n)
      children = sortNodes(
          set(L.d(n, otype='sentence_atom')) | {
              L.u(thisFirstSlot, otype='sentence_atom')[0],
              L.u(thisLastSlot, otype='sentence_atom')[0],
          }
      )
    elif nType == 'sentence':
      children = L.d(n, otype='sentence_atom')
    elif nType == 'sentence_atom' or nType == 'clause':
      children = L.d(n, otype='clause_atom')
    elif nType == 'clause_atom' or nType == 'phrase':
      children = L.d(n, otype='phrase_atom')
    elif nType == 'phrase_atom' or nType == 'subphrase':
      children = L.d(n, otype=slotType)
    elif nType == 'lex':
      children = ()
    elif nType == slotType:
      children = ()
      lx = L.u(n, otype='lex')[0]

    superType = ATOMS.get(nType, None)
    if superType:
      (superNode, superStart, superEnd) = self._getSuper(n, superType)
      if superStart < myStart:
        boundaryClass += ' r'
      if superEnd > myEnd:
        boundaryClass += ' l'
      nodePart = (f'<a href="#" class="nd">{superNode}</a>' if withNodes else '')
      shl = highlights.get(superNode, None)
      shlClass = ''
      shlStyle = ''
      if shl is not None:
        if shl == '':
          shlClass = ' hl'
        else:
          shlStyle = f' style="background-color: {shl};"'
        if not hlClass:
          hlClass = shlClass
          hlStyle = shlStyle

    doOuter = outer and nType in {slotType, 'lex'}
    if doOuter:
      html.append('<div class="outeritem">')

    html.append(f'<div class="{className} {boundaryClass}{hlClass}"{hlStyle}>')

    if nType in {'verse', 'half_verse'}:
      passage = self.shbLink(n, asString=True)
      html.append(
          f'''
    <div class="vl">
        <div class="vrs">{passage}</div>
        {nodePart}
    </div>
'''
      )
    elif superType:
      typePart = self.shbLink(superNode, text=superType, asString=True)
      featurePart = ''
      if superType == 'sentence':
        featurePart = getFeatures(
            self,
            superNode,
            suppress,
            ('number',),
            plain=True,
        )
      elif superType == 'clause':
        featurePart = getFeatures(
            self,
            superNode,
            suppress,
            ('rela', 'typ'),
            plain=True,
        )
      elif superType == 'phrase':
        featurePart = getFeatures(
            self,
            superNode,
            suppress,
            ('function', 'typ'),
            plain=True,
        )
      html.append(
          f'''
    <div class="{superType}{shlClass}"{shlStyle}>
        {typePart} {nodePart} {featurePart}
    </div>
    <div class="atoms">
'''
      )
    else:
      if nodePart:
        html.append(nodePart)

      heading = ''
      featurePart = ''
      occs = ''
      if nType == slotType:
        lx = L.u(n, otype='lex')[0]
        lexLink = (self.shbLink(lx, text=htmlEsc(T.text([n])), asString=True))
        heading = f'<div class="h">{lexLink}</div>'
        featurePart = getFeatures(
            self,
            n,
            suppress,
            ('pdp', 'gloss', 'vs', 'vt'),
            givenValue=dict(
                pdp=self.shbLink(n, text=htmlEsc(F.pdp.v(n)), asString=True),
                gloss=htmlEsc(F.gloss.v(lx)),
            ),
        )
      elif nType == 'lex':
        occs = L.d(n, otype='word')
        extremeOccs = sorted({occs[0], occs[-1]})
        linkOccs = ' - '.join(self.shbLink(lo, asString=True) for lo in extremeOccs)
        heading = f'<div class="h">{htmlEsc(F.voc_lex_utf8.v(n))}</div>'
        occs = f'<div class="occs">{linkOccs}</div>'
        featurePart = getFeatures(
            self,
            n,
            suppress,
            ('voc_lex', 'gloss'),
            givenValue=dict(
                voc_lex=self.shbLink(n, text=htmlEsc(F.voc_lex.v(n)), asString=True)
            ),
        )
      html.append(heading)
      html.append(featurePart)
      html.append(occs)

    for ch in children:
      self._pretty(
          ch,
          False,
          html,
          firstSlot,
          lastSlot,
          condenseType=condenseType,
          withNodes=withNodes,
          suppress=suppress,
          highlights=highlights,
      )
    if superType:
      html.append('''
    </div>
''')
    html.append('''
</div>
''')
    if doOuter:
      html.append('</div>')

  def _getSuper(self, n, tp):
    api = self.api
    L = api.L
    superNode = L.u(n, otype=tp)[0]
    return (superNode, *getBoundary(api, superNode))
