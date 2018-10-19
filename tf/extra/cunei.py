import os
import re
import types
from glob import glob
from shutil import copyfile

from tf.fabric import Fabric
from tf.apphelpers import (
    search,
    table, plainTuple,
    show, prettyPre, pretty, prettyTuple, prettySetup,
    getData, getDataCustom, getFeatures,
    htmlEsc, mdEsc,
    dm, dh, header, outLink,
    URL_GH, URL_NB, API_URL, TFDOC_URL
)

from tf.server.common import getConfig
from tf.notebook import location


def IMAGE_URL(org, source, release):
  return f'https://github.com/{org}/{source}/releases/download/{release}/images.zip'


def IMAGE_DIR(sourceDir, version):
  return f'{sourceDir}/{version}/images'


PHOTO_TO = '{}/tablets/photos'
PHOTO_EXT = 'jpg'

TABLET_TO = '{}/tablets/lineart'
IDEO_TO = '{}/ideographs/lineart'
LINEART_EXT = 'jpg'

URL_FORMAT = dict(
    tablet=dict(
        photo=f'https://cdli.ucla.edu/dl/photo/{{}}_d.{PHOTO_EXT}',
        lineart=f'https://cdli.ucla.edu/dl/lineart/{{}}_l.{LINEART_EXT}',
        main='https://cdli.ucla.edu/search/search_results.php?SearchMode=Text&ObjectID={}',
    ),
    ideograph=dict(
        lineart=(
            f'https://cdli.ucla.edu/tools/SignLists/protocuneiform/archsigns/{{}}.{LINEART_EXT}'
        ),
        main='https://cdli.ucla.edu/tools/SignLists/protocuneiform/archsigns.html',
    ),
)

FLAGS = (
    ('damage', '#'),
    ('remarkable', '!'),
    ('written', ('!(', ')')),
    ('uncertain', '?'),
)

OUTER_QUAD_TYPES = {'sign', 'quad'}

CLUSTER_BEGIN = {'[': ']', '<': '>', '(': ')'}
CLUSTER_END = {y: x for (x, y) in CLUSTER_BEGIN.items()}
CLUSTER_KIND = {'[': 'uncertain', '(': 'properName', '<': 'supplied'}
CLUSTER_BRACKETS = dict((name, (bOpen, CLUSTER_BEGIN[bOpen]))
                        for (bOpen, name) in CLUSTER_KIND.items())

FLEX_STYLE = (
    'display: flex;'
    'flex-flow: row nowrap;'
    'justify-content: flex-start;'
    'align-items: center;'
    'align-content: flex-start;'
)
CAPTION_STYLE = dict(
    top=(
        'display: flex;'
        'flex-flow: column-reverse nowrap;'
        'justify-content: space-between;'
        'align-items: center;'
        'align-content: space-between;'
    ),
    bottom=(
        'display: flex;'
        'flex-flow: column nowrap;'
        'justify-content: space-between;'
        'align-items: center;'
        'align-content: space-between;'
    ),
    left=(
        'display: flex;'
        'flex-flow: row-reverse nowrap;'
        'justify-content: space-between;'
        'align-items: center;'
        'align-content: space-between;'
    ),
    right=(
        'display: flex;'
        'flex-flow: row nowrap;'
        'justify-content: space-between;'
        'align-items: center;'
        'align-content: space-between;'
    ),
)

ITEM_STYLE = ('padding: 0.5rem;')

SIZING = {'height', 'width'}

COMMENT_TYPES = set('''
    tablet
    face
    column
    line
    case
'''.strip().split())

CLUSTER_TYPES = dict(
    uncertain='?',
    properName='=',
    supplied='&gt;',
)

ATF_TYPES = set('''
    sign
    quad
    cluster
'''.strip().split())

CSS = '''
<style type="text/css">
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


class Atf(object):
  def __init__(self, api=None):
    if api:
      self.api = api

  def getSource(self, node, nodeType=None, lineNumbers=False):
    api = self.api
    F = api.F
    L = api.L
    sourceLines = []
    lineNumber = ''
    if lineNumbers:
      lineNo = F.srcLnNum.v(node)
      lineNumber = f'{lineNo:>5} ' if lineNo else ''
    sourceLine = F.srcLn.v(node)
    if sourceLine:
      sourceLines.append(f'{lineNumber}{sourceLine}')
    for child in L.d(node, nodeType):
      sourceLine = F.srcLn.v(child)
      lineNumber = ''
      if sourceLine:
        if lineNumbers:
          lineNumber = f'{F.srcLnNum.v(child):>5}: '
        sourceLines.append(f'{lineNumber}{sourceLine}')
    return sourceLines

  def atfFromSign(self, n, flags=False):
    F = self.api.F
    Fs = self.api.Fs
    if F.otype.v(n) != 'sign':
      return '«no sign»'

    grapheme = F.grapheme.v(n)
    if grapheme == '…':
      grapheme = '...'
    primeN = F.prime.v(n)
    prime = ("'" * primeN) if primeN else ''

    variantValue = F.variant.v(n)
    variant = f'~{variantValue}' if variantValue else ''

    modifierValue = F.modifier.v(n)
    modifier = f'@{modifierValue}' if modifierValue else ''
    modifierInnerValue = F.modifierInner.v(n)
    modifierInner = f'@{modifierInnerValue}' if modifierInnerValue else ''

    modifierFirst = F.modifierFirst.v(n)

    repeat = F.repeat.v(n)
    if repeat is None:
      varmod = (f'{modifier}{variant}' if modifierFirst else f'{variant}{modifier}')
      result = f'{grapheme}{prime}{varmod}'
    else:
      if repeat == -1:
        repeat = 'N'
      varmod = (f'{modifierInner}{variant}' if modifierFirst else f'{variant}{modifierInner}')
      result = f'{repeat}({grapheme}{prime}{varmod}){modifier}'

    if flags:
      for (flag, char) in FLAGS:
        value = Fs(flag).v(n)
        if value:
          if type(char) is tuple:
            result += f'{char[0]}{value}{char[1]}'
          else:
            result += char

    return result

  def atfFromQuad(self, n, flags=False, outer=True):
    api = self.api
    E = api.E
    F = api.F
    Fs = api.Fs
    if F.otype.v(n) != 'quad':
      return '«no quad»'

    children = E.sub.f(n)
    if not children or len(children) < 2:
      return f'«quad with less than two sub-quads»'
    result = ''
    for child in children:
      nextChildren = E.op.f(child)
      if nextChildren:
        op = nextChildren[0][1]
      else:
        op = ''
      childType = F.otype.v(child)

      thisResult = (
          self.atfFromQuad(child, flags=flags, outer=False)
          if childType == 'quad' else self.atfFromSign(child, flags=flags)
      )
      result += f'{thisResult}{op}'

    variant = F.variantOuter.v(n)
    variantStr = f'~{variant}' if variant else ''

    flagStr = ''
    if flags:
      for (flag, char) in FLAGS:
        value = Fs(flag).v(n)
        if value:
          if type(char) is tuple:
            flagStr += f'{char[0]}{value}{char[1]}'
          else:
            flagStr += char

    if variant:
      if flagStr:
        if outer:
          result = f'|({result}){variantStr}|{flagStr}'
        else:
          result = f'(({result}){variantStr}){flagStr}'
      else:
        if outer:
          result = f'|({result}){variantStr}|'
        else:
          result = f'({result}){variantStr}'
    else:
      if flagStr:
        if outer:
          result = f'|{result}|{flagStr}'
        else:
          result = f'({result}){flagStr}'
      else:
        if outer:
          result = f'|{result}|'
        else:
          result = f'({result})'

    return result

  def atfFromOuterQuad(self, n, flags=False):
    api = self.api
    F = api.F
    nodeType = F.otype.v(n)
    if nodeType == 'sign':
      return self.atfFromSign(n, flags=flags)
    elif nodeType == 'quad':
      return self.atfFromQuad(n, flags=flags, outer=True)
    else:
      return '«no outer quad»'

  def atfFromCluster(self, n, seen=None):
    api = self.api
    F = api.F
    E = api.E
    if F.otype.v(n) != 'cluster':
      return '«no cluster»'

    typ = F.type.v(n)
    (bOpen, bClose) = CLUSTER_BRACKETS[typ]
    if bClose == ')':
      bClose = ')a'
    children = api.sortNodes(E.sub.f(n))

    if seen is None:
      seen = set()
    result = []
    for child in children:
      if child in seen:
        continue
      childType = F.otype.v(child)

      thisResult = (
          self.atfFromCluster(child, seen=seen)
          if childType == 'cluster' else self.atfFromQuad(child, flags=True)
          if childType == 'quad' else self.atfFromSign(child, flags=True)
          if childType == 'sign' else None
      )
      seen.add(child)
      if thisResult is None:
        dm(f'TF: child of cluster has type {childType}:' ' should not happen')
      result.append(thisResult)
    return f'{bOpen}{" ".join(result)}{bClose}'

  def getOuterQuads(self, n):
    api = self.api
    F = api.F
    E = api.E
    L = api.L
    return [
        quad for quad in L.d(n) if (
            F.otype.v(quad) in OUTER_QUAD_TYPES
            and all(F.otype.v(parent) != 'quad' for parent in E.sub.t(quad))
        )
    ]


class Cunei(Atf):
  def __init__(self, name=None, asApi=False, version='1.0', lgc=False, hoist=False):
    config = getConfig('cunei')
    cfg = config.configure(lgc=lgc, version=version)
    self.asApi = asApi
    repoBase = getData(
        cfg['source'],
        cfg['release'],
        cfg['firstRelease'],
        cfg['url'],
        f'{cfg["org"]}/{cfg["source"]}/tf/{cfg["source"]}',
        version,
        lgc,
    )
    if not repoBase:
      return
    repoRel = f'{cfg["org"]}/{cfg["source"]}'
    repo = f'{repoBase}/{repoRel}'
    self.repo = repo
    self.version = version
    self.charUrl = cfg['charUrl']
    self.sourceDir = f'{repo}/{cfg["sourceDir"]}'
    self.imageDir = f'{repo}/{IMAGE_DIR(cfg["sourceDir"], version)}'
    self.localImageDir = cfg['localImageDir']
    if not os.path.exists(self.imageDir):
      getDataCustom(
          cfg['source'],
          cfg['release'],
          IMAGE_URL(cfg['org'], cfg['source'], cfg['release']),
          self.sourceDir,
          version,
          withPaths=True,
      )
    self.repoTempDir = f'{repo}/{cfg["tempDir"]}'
    self._imagery = {}
    self.corpus = f'{repo}/tf/{cfg["source"]}/{version}'
    self.corpusFull = f'{cfg["sourceFull"]} (v:{version})'
    self.condenseType = cfg['condenseType']
    self.exampleSection = '<code>P005381</code>'
    self.exampleSectionText = 'P005381'
    TF = Fabric(locations=[self.corpus], modules=[''], silent=True)
    api = TF.load('', silent=True)
    self.api = api
    if api is False:
      return
    allFeatures = TF.explore(silent=True, show=True)
    loadableFeatures = allFeatures['nodes'] + allFeatures['edges']
    result = TF.load(loadableFeatures, add=True, silent=True)
    if result is False:
      self.api = False
      return
    self.prettyFeaturesLoaded = loadableFeatures
    self.prettyFeatures = ()
    self.api = api
    self._getImagery()
    self.cwd = os.getcwd()
    (inNb, repoLoc) = location(self.cwd, name)
    if inNb:
      (nbDir, nbName, nbExt) = inNb
    if repoLoc:
      (thisOrg, thisRepo, thisPath, nbUrl, ghUrl) = repoLoc
    docUrl = f'{URL_GH}/{repoRel}/blob/master/docs'
    tutUrl = f'{URL_NB}/{cfg["org"]}/tutorials/blob/master/search.ipynb'
    extraUrl = TFDOC_URL(f'/Api/{cfg["repo"].capitalize()}/')
    dataLink = outLink(self.corpusFull, f'{docUrl}/about.md', 'provenance of this corpus')
    charLink = (
        outLink('Character table', self.charUrl, 'Cuneiform characters and transcriptions')
        if self.charUrl else
        ''
    )
    featureLink = outLink('Feature docs', f'{docUrl}/transcription.md', 'feature documentation')
    cuneiLink = outLink('Cunei API', extraUrl, 'cunei api documentation')
    tfLink = outLink(
        f'Text-Fabric API {api.TF.version}', API_URL(''),
        'text-fabric-api'
    )
    tfsLink = outLink(
        'Search help', API_URL('search-templates'),
        'Search Templates Introduction and Reference'
    )
    tutLink = outLink(
        'Search tutorial', tutUrl,
        'Search tutorial in Jupyter Notebook'
    )
    if asApi:
      self.dataLink = dataLink
      self.charLink = charLink
      self.featureLink = featureLink
      self.tfsLink = tfsLink
      self.tutLink = tutLink
    else:
      if inNb:
        dm(
            '**Documentation:**'
            f' {dataLink} {charLink} {featureLink} {cuneiLink} {tfLink} {tfsLink}'
        )
        if repoLoc:
          dm(f'''
  This notebook online:
  {outLink('NBViewer', f'{nbUrl}/{nbName}{nbExt}')}
  {outLink('GitHub', f'{ghUrl}/{nbName}{nbExt}')}
''')
    thisRepoDir = None
    self.tempDir = None
    self.reportDir = None
    if repoLoc:
      thisRepoDir = f'{repoBase}/{thisOrg}/{thisRepo}'
      self.tempDir = f'{thisRepoDir}/{cfg["tempDir"]}'
      self.reportDir = f'{thisRepoDir}/{cfg["reportDir"]}'
    if not asApi:
      for cdir in (self.tempDir, self.reportDir):
        if cdir:
          os.makedirs(cdir, exist_ok=True)

    self.classNames = {nType[0]: nType[0] for nType in api.C.levels.data}
    self.noneValues = set()

    if not asApi:
      if inNb:
        self.loadCSS()
      if hoist:
        docs = api.makeAvailableIn(hoist)
        if inNb:
          dh(
              '<details open><summary><b>API members</b>:</summary>\n'
              +
              '<br/>\n'.join(
                  ', '.join(
                      outLink(entry, API_URL(ref), title='doc')
                      for entry in entries
                  )
                  for (ref, entries) in docs
              )
              +
              '</details>'
          )
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
      return CSS
    dh(CSS)

  def nodeFromDefaultSection(self, sectionStr):
    api = self.api
    T = api.T
    tabletNode = T.nodeFromSection((sectionStr,))
    if tabletNode is None:
      return (f'Not a valid tablet number: "{sectionStr}"', None)
    return ('', tabletNode)

  def lineFromNode(self, n):
    api = self.api
    F = api.F
    L = api.L
    caseOrLineUp = [m for m in L.u(n) if F.terminal.v(m)]
    return caseOrLineUp[0] if caseOrLineUp else None

  def nodeFromCase(self, passage):
    api = self.api
    F = api.F
    L = api.L
    T = api.T
    section = passage[0:2]
    caseNum = passage[2].replace('.', '')
    column = T.nodeFromSection(section)
    if column is None:
      return None
    casesOrLines = [c for c in L.d(column) if F.terminal.v(c) and F.number.v(c) == caseNum]
    if not casesOrLines:
      return None
    return casesOrLines[0]

  def caseFromNode(self, n):
    api = self.api
    F = api.F
    T = api.T
    L = api.L
    section = T.sectionFromNode(n)
    if section is None:
      return None
    nodeType = F.otype.v(n)
    if nodeType in {'sign', 'quad', 'cluster', 'case'}:
      if nodeType == 'case':
        caseNumber = F.number.v(n)
      else:
        caseOrLine = [m for m in L.u(n) if F.terminal.v(m)][0]
        caseNumber = F.number.v(caseOrLine)
      return (section[0], section[1], caseNumber)
    else:
      return section

  def casesByLevel(self, lev, terminal=True):
    api = self.api
    F = api.F
    lkey = 'line' if lev == 0 else 'case'
    if lev == 0:
      return (
          tuple(c for c in F.otype.s(lkey) if F.terminal.v(c))
          if terminal else
          F.otype.s(lkey)
      )
    return (
        tuple(c for c in F.otype.s(lkey) if F.depth.v(c) == lev and F.terminal.v(c))
        if terminal else
        tuple(c for c in F.otype.s(lkey) if F.depth.v(c) == lev)
    )

  def lineart(self, ns, key=None, asLink=False, withCaption=None, **options):
    return self._getImages(
        ns, kind='lineart', key=key, asLink=asLink, withCaption=withCaption, **options
    )

  def photo(self, ns, key=None, asLink=False, withCaption=None, **options):
    return self._getImages(
        ns, kind='photo', key=key, asLink=asLink, withCaption=withCaption, **options
    )

  def imagery(self, objectType, kind):
    return set(self._imagery.get(objectType, {}).get(kind, {}))

  def cdli(self, n, linkText=None, asString=False):
    (nType, objectType, identifier) = self._imageClass(n)
    if linkText is None:
      linkText = identifier
    result = _wrapLink(linkText, objectType, 'main', identifier)
    if asString:
      return result
    else:
      dh(result)

  def tabletLink(self, t, text=None, className=None, asString=False, noUrl=False):
    api = self.api
    L = api.L
    F = api.F
    if type(t) is str:
      pNum = t
    else:
      n = t if F.otype.v(t) == 'tablet' else L.u(t, otype='tablet')[0]
      pNum = F.catalogId.v(n)

    title = None if noUrl else ('to CDLI main page for this tablet')
    linkText = pNum if text is None else text
    url = '#' if noUrl else URL_FORMAT['tablet']['main'].format(pNum)
    target = '' if noUrl else None

    result = outLink(linkText, url, title=title, className=className, target=target)
    if asString:
      return result
    dh(result)

  def webLink(self, n):
    return self.tabletLink(n, className='rwh', asString=True, noUrl=True)

  def plain(
      self,
      n,
      linked=True,
      fmt=None,
      withNodes=False,
      asString=False,
      lineart=True,
      lineNumbers=False,
  ):
    asApi = self.asApi
    api = self.api
    F = api.F

    nType = F.otype.v(n)
    result = ''
    if asApi:
      nodeRep = f' <a href="#" class="nd">{n}</a> ' if withNodes else ''
    else:
      nodeRep = f' *{n}* ' if withNodes else ''

    if nType in ATF_TYPES:
      isSign = nType == 'sign'
      isQuad = nType == 'quad'
      rep = (
          self.atfFromSign(n) if isSign else self.atfFromQuad(n)
          if isQuad else self.atfFromCluster(n)
      )
      if linked:
        rep = self.tabletLink(n, text=rep, asString=True)
      theLineart = ''
      if lineart:
        if isSign or isQuad:
          width = '2em' if isSign else '4em'
          height = '4em' if isSign else '6em'
          theLineart = self._getImages(
              n,
              kind='lineart',
              width=width,
              height=height,
              asString=True,
              withCaption=False,
              warning=False
          )
          theLineart = f' {theLineart}'
      result = (f'{rep}{nodeRep}{theLineart}') if theLineart else f'{rep}{nodeRep}'
    elif nType == 'comment':
      rep = mdEsc(F.type.v(n))
      if linked:
        rep = self.tabletLink(n, text=rep, asString=True)
      result = f'{rep}{nodeRep}: {mdEsc(F.text.v(n))}'
    else:
      lineNumbersCondition = lineNumbers
      if nType == 'line' or nType == 'case':
        rep = mdEsc(f'{nType} {F.number.v(n)}')
        lineNumbersCondition = lineNumbers and F.terminal.v(n)
      elif nType == 'column':
        rep = mdEsc(f'{nType} {F.number.v(n)}')
      elif nType == 'face':
        rep = mdEsc(f'{nType} {F.type.v(n)}')
      elif nType == 'tablet':
        rep = mdEsc(f'{nType} {F.catalogId.v(n)}')
      result = self._addLink(
          n, rep, nodeRep,
          linked=linked, lineNumbers=lineNumbersCondition,
      )

    if asString or asApi:
      return result
    dm(result)

  def _addLink(self, n, rep, nodeRep, linked=True, lineNumbers=True):
    F = self.api.F
    if linked:
      rep = self.tabletLink(n, text=rep, asString=True)
    theLine = ''
    if lineNumbers:
      theLine = mdEsc(f' @{F.srcLnNum.v(n)} ')
    return f'{rep}{nodeRep}{theLine}'

  def _pretty(
      self,
      n,
      outer,
      html,
      firstSlot,
      lastSlot,
      condenseType=None,
      fmt=None,
      withNodes=False,
      suppress=set(),
      highlights={},
      seen=set(),
      lineNumbers=False,
      lineart=True,
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
    E = api.E
    sortNodes = api.sortNodes

    if outer:
      seen = set()

    heading = ''
    featurePart = ''
    commentsPart = self._getComments(
        n,
        firstSlot,
        lastSlot,
        withNodes,
        suppress,
        highlights,
        lineNumbers,
        seen,
    ) if nType in COMMENT_TYPES else ''
    children = ()

    if nType == 'tablet':
      heading = htmlEsc(F.catalogId.v(n))
      heading += ' '
      heading += getFeatures(
          self,
          n,
          suppress,
          ('name', 'period', 'excavation'),
          plain=True,
      )
      children = L.d(n, otype='face')
    elif nType == 'face':
      heading = htmlEsc(F.type.v(n))
      featurePart = getFeatures(
          self,
          n,
          suppress,
          ('identifier', 'fragment'),
      )
      children = L.d(n, otype='column')
    elif nType == 'column':
      heading = htmlEsc(F.number.v(n))
      if F.prime.v(n):
        heading += "'"
      children = L.d(n, otype='line')
    elif nType == 'line' or nType == 'case':
      heading = htmlEsc(F.number.v(n))
      if F.prime.v(n):
        heading += "'"
      if F.terminal.v(n):
        className = 'trminal'
        theseFeats = ('srcLnNum', ) if lineNumbers else ()
        featurePart = getFeatures(
            self,
            n,
            suppress,
            theseFeats,
        )
        children = sortNodes(
            set(L.d(n, otype='cluster'))
            | set(L.d(n, otype='quad'))
            | set(L.d(n, otype='sign'))
        )
      else:
        children = E.sub.f(n)
    elif nType == 'comment':
      heading = htmlEsc(F.type.v(n))
      featurePart = getFeatures(
          self,
          n,
          suppress,
          ('text', ),
      )
    elif nType == 'cluster':
      seen.add(n)
      heading = htmlEsc(CLUSTER_TYPES.get(F.type.v(n), ''))
      children = sortNodes(
          set(L.d(n, otype='cluster'))
          | set(L.d(n, otype='quad'))
          | set(L.d(n, otype='sign'))
      )
    elif nType == 'quad':
      seen.add(n)
      children = E.sub.f(n)
    elif nType == slotType:
      featurePart = self._getAtf(n)
      seen.add(n)
      if not outer and F.type.v(n) == 'empty':
        return

    if outer:
      typePart = self.tabletLink(n, text=f'{nType} {heading}', asString=True)
    else:
      typePart = heading

    isCluster = nType == 'cluster'
    extra = 'B' if isCluster else ''
    label = f'''
    <div class="lbl {className}{extra}">
        {typePart}
        {nodePart}
    </div>
''' if typePart or nodePart else ''

    if isCluster:
      if outer:
        html.append(f'<div class="contnr {className}{hlClass}"{hlStyle}>')
      html.append(label)
      if outer:
        html.append(f'<div class="children {className}">')
    else:
      html.append(
          f'''
<div class="contnr {className}{hlClass}"{hlStyle}>
    {label}
    <div class="meta">
        {featurePart}
        {commentsPart}
    </div>
'''
      )
    if lineart:
      isQuad = nType == 'quad'
      isSign = nType == 'sign'
      if isQuad or isSign:
        isOuter = outer or (all(F.otype.v(parent) != 'quad' for parent in E.sub.t(n)))
        if isOuter:
          width = '2em' if isSign else '4em'
          height = '4em' if isSign else '6em'
          theLineart = self._getImages(
              n,
              kind='lineart',
              width=width,
              height=height,
              asString=True,
              withCaption=False,
              warning=False
          )
          if theLineart:
            html.append(f'<div>{theLineart}</div>')
    caseDir = ''
    if not isCluster:
      if children:
        if nType == 'case':
          depth = F.depth.v(n)
          caseDir = 'v' if depth & 1 else 'h'
        html.append(f'''
    <div class="children {className}{caseDir}">
''')

    for ch in children:
      if ch not in seen:
        self._pretty(
            ch,
            False,
            html,
            firstSlot,
            lastSlot,
            condenseType=condenseType,
            fmt=fmt,
            withNodes=withNodes,
            suppress=suppress,
            highlights=highlights,
            lineart=lineart,
            lineNumbers=lineNumbers,
            seen=seen,
        )
        if nType == 'quad':
          nextChildren = E.op.f(ch)
          if nextChildren:
            op = nextChildren[0][1]
            html.append(f'<div class="op">{op}</div>')
    if isCluster:
      html.append(
          f'''
    <div class="lbl {className}E{hlClass}"{hlStyle}>
        {typePart}
        {nodePart}
    </div>
'''
      )
      if outer:
        html.append('</div></div>')
    else:
      if children:
        html.append('''
    </div>
''')
      html.append('''
</div>
''')

  def _getComments(
      self,
      n,
      firstSlot,
      lastSlot,
      withNodes,
      suppress,
      highlights,
      lineNumbers,
      seen,
  ):
    api = self.api
    E = api.E
    cns = E.comments.f(n)
    if len(cns):
      html = ['<div class="comments">']
      for c in cns:
        self._pretty(
            c,
            False,
            html,
            firstSlot,
            lastSlot,
            condenseType=None,
            fmt=None,
            withNodes=withNodes,
            suppress=suppress,
            highlights=highlights,
            lineart=False,
            lineNumbers=lineNumbers,
            seen=seen,
        )
      html.append('</div>')
      commentsPart = ''.join(html)
    else:
      commentsPart = ''
    return commentsPart

  def _getAtf(self, n):
    atf = self.atfFromSign(n, flags=True)
    featurePart = f' <span class="srcLn">{atf}</span>'
    return featurePart

  def _imageClass(self, n):
    api = self.api
    F = api.F
    if type(n) is str:
      identifier = n
      if n == '':
        identifier = None
        objectType = None
        nType = None
      elif len(n) == 1:
        objectType = 'ideograph'
        nType = 'sign/quad'
      else:
        if n[0] == 'P' and n[1:].isdigit():
          objectType = 'tablet'
          nType = 'tablet'
        else:
          objectType = 'ideograph'
          nType = 'sign/quad'
    else:
      nType = F.otype.v(n)
      if nType in OUTER_QUAD_TYPES:
        identifier = self.atfFromOuterQuad(n)
        objectType = 'ideograph'
      elif nType == 'tablet':
        identifier = F.catalogId.v(n)
        objectType = 'tablet'
      else:
        identifier = None
        objectType = None
    return (nType, objectType, identifier)

  def _getImages(
      self,
      ns,
      kind=None,
      key=None,
      asLink=False,
      withCaption=None,
      warning=True,
      asString=False,
      **options
  ):
    if type(ns) is int or type(ns) is str:
      ns = [ns]
    result = []
    attStr = ' '.join(f'{opt}="{value}"' for (opt, value) in options.items() if opt not in SIZING)
    cssProps = {}
    for (opt, value) in options.items():
      if opt in SIZING:
        if type(value) is int:
          force = False
          realValue = f'{value}px'
        else:
          if value.startswith('!'):
            force = True
            realValue = value[1:]
          else:
            force = False
            realValue = value
          if realValue.isdecimal():
            realValue += 'px'
        cssProps[f'max-{opt}'] = realValue
        if force:
          cssProps[f'min-{opt}'] = realValue
    cssStr = ' '.join(f'{opt}: {value};' for (opt, value) in cssProps.items())
    if withCaption is None:
      withCaption = None if asLink else 'bottom'
    for n in ns:
      caption = None
      (nType, objectType, identifier) = self._imageClass(n)
      if objectType:
        imageBase = self._imagery.get(objectType, {}).get(kind, {})
        images = imageBase.get(identifier, None)
        if withCaption:
          caption = _wrapLink(identifier, objectType, 'main', identifier)
        if images is None:
          thisImage = (
              f'<span><b>no {kind}</b> for {objectType} <code>{identifier}</code></span>'
          ) if warning else ''
        else:
          image = images.get(key or '', None)
          if image is None:
            imgs = "</code> <code>".join(sorted(images.keys()))
            thisImage = f'<span><b>try</b> key=<code>{imgs}</code></span>' if warning else ''
          else:
            if asLink:
              thisImage = identifier
            else:
              theImage = self._useImage(image, kind, key or '', n)
              thisImage = (f'<img src="{theImage}" style="display: inline;{cssStr}" {attStr} />')
        thisResult = _wrapLink(
            thisImage, objectType, kind, identifier, pos=withCaption, caption=caption
        ) if thisImage else None
      else:
        thisResult = (f'<span><b>no {kind}</b> for <code>{nType}</code>s</span>') if warning else ''
      result.append(thisResult)
    if not warning:
      result = [image for image in result if image]
    if not result:
      return ''
    if asString:
      return ''.join(result)
    resultStr = f'</div><div style="{ITEM_STYLE}">'.join(result)
    html = (f'<div style="{FLEX_STYLE}">'
            f'<div style="{ITEM_STYLE}">'
            f'{resultStr}</div></div>').replace('\n', '')
    dh(html)
    if not warning:
      return True

  def _useImage(self, image, kind, key, node):
    asApi = self.asApi
    api = self.api
    F = api.F
    (imageDir, imageName) = os.path.split(image)
    (base, ext) = os.path.splitext(imageName)
    localBase = self.repoTempDir if asApi else self.cwd
    localDir = f'{localBase}/{self.localImageDir}'
    if not os.path.exists(localDir):
      os.makedirs(localDir, exist_ok=True)
    if type(node) is int:
      nType = F.otype.v(node)
      if nType == 'tablet':
        nodeRep = F.catalogId.v(node)
      elif nType in OUTER_QUAD_TYPES:
        nodeRep = self.atfFromOuterQuad(node)
      else:
        nodeRep = str(node)
    else:
      nodeRep = node
    nodeRep = (
        nodeRep.lower()
        .replace('|', 'q')
        .replace('~', '-')
        .replace('@', '(a)')
        .replace('&', '(e)')
        .replace('+', '(p)')
        .replace('.', '(d)')
    )
    keyRep = '' if key == '' else f'-{key}'
    localImageName = f'{kind}-{nodeRep}{keyRep}{ext}'
    localImagePath = f'{localDir}/{localImageName}'
    if (
        not os.path.exists(localImagePath)
        or os.path.getmtime(image) > os.path.getmtime(localImagePath)
    ):
      copyfile(image, localImagePath)
    base = '/local/' if asApi else ''
    return f'{base}{self.localImageDir}/{localImageName}'

  def _getImagery(self):
    for (dirFmt, ext, kind, objectType) in (
        (IDEO_TO, LINEART_EXT, 'lineart', 'ideograph'),
        (TABLET_TO, LINEART_EXT, 'lineart', 'tablet'),
        (PHOTO_TO, PHOTO_EXT, 'photo', 'tablet'),
    ):
      srcDir = dirFmt.format(self.imageDir)
      filePaths = glob(f'{srcDir}/*.{ext}')
      images = {}
      idPat = re.compile('P[0-9]+')
      for filePath in filePaths:
        (fileDir, fileName) = os.path.split(filePath)
        (base, thisExt) = os.path.splitext(fileName)
        if kind == 'lineart' and objectType == 'tablet':
          ids = idPat.findall(base)
          if not ids:
            print(f'skipped non-{objectType} "{fileName}"')
            continue
          identifier = ids[0]
          key = base.replace('_l', '').replace(identifier, '')
        else:
          identifier = base
          if identifier.startswith('['):
            identifier = '|' + identifier[1:]
          if identifier.endswith(']'):
            identifier = identifier[0:-1] + '|'
          key = ''
        images.setdefault(identifier, {})[key] = filePath
      self._imagery.setdefault(objectType, {})[kind] = images
      print(f'Found {len(images)} {objectType} {kind}s')


def _wrapLink(piece, objectType, kind, identifier, pos='bottom', caption=None):
  title = (
      'to CDLI main page for this item'
      if kind == 'main' else f'to higher resolution {kind} on CDLI'
  )
  url = URL_FORMAT.get(objectType, {}).get(kind, '').format(identifier)

  result = outLink(piece, url, title=title) if url else piece
  if caption:
    result = (
        f'<div style="{CAPTION_STYLE[pos]}">'
        f'<div>{result}</div>'
        f'<div>{caption}</div>'
        '</div>'
    )
  return result
