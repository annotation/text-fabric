import os
import re
import operator
from glob import glob
from shutil import copyfile
from functools import reduce
from IPython.display import display, Markdown, HTML

from tf.fabric import Fabric

SOURCE = 'uruk'
SOURCE_FULL = 'Uruk IV-III'
VERSION = '1.0'
CORPUS = f'tf/{SOURCE}/{VERSION}'
CORPUS_FULL = f'{SOURCE_FULL} (v{VERSION})'
SOURCE_DIR = 'sources/cdli'
IMAGE_DIR = f'{SOURCE_DIR}/images'
TEMP_DIR = '_temp'
REPORT_DIR = 'reports'

LIMIT_SHOW = 100
LIMIT_TABLE = 2000

PHOTO_TO = '{}/tablets/photos'
PHOTO_EXT = 'jpg'

TABLET_TO = '{}/tablets/lineart'
IDEO_TO = '{}/ideographs/lineart'
LINEART_EXT = 'jpg'

LOCAL_DIR = 'cdli-imagery'

URL_GH = 'https://github.com'
URL_NB = 'http://nbviewer.jupyter.org/github'

URL_FORMAT = dict(
    tablet=dict(
        photo=f'https://cdli.ucla.edu/dl/photo/{{}}_d.{PHOTO_EXT}',
        lineart=f'https://cdli.ucla.edu/dl/lineart/{{}}_l.{LINEART_EXT}',
        main=(
            'https://cdli.ucla.edu/search/search_results.php?'
            'SearchMode=Text&ObjectID={}'
        ),
    ),
    ideograph=dict(
        lineart=(
            'https://cdli.ucla.edu/tools/SignLists'
            f'/protocuneiform/archsigns/{{}}.{LINEART_EXT}'
        ),
        main=(
            'https://cdli.ucla.edu/tools/SignLists'
            '/protocuneiform/archsigns.html'
        ),
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

COMMENT_TYPES = set(
    '''
    tablet
    face
    column
    line
    case
'''.strip().split()
)

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
<style>
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


def dm(md):
    display(Markdown(md))


def _outLink(text, href, title=None):
    titleAtt = '' if title is None else f' title="{title}"'
    return f'<a target="_blank" href="{href}"{titleAtt}>{text}</a>'


def _wrapLink(piece, objectType, kind, identifier, pos='bottom', caption=None):
    title = (
        'to CDLI main page for this item'
        if kind == 'main' else f'to higher resolution {kind} on CDLI'
    )
    url = URL_FORMAT.get(objectType, {}).get(kind, '').format(identifier)

    result = _outLink(piece, url, title=title) if url else piece
    if caption:
        result = (
            f'<div style="{CAPTION_STYLE[pos]}">'
            f'<div>{result}</div>'
            f'<div>{caption}</div>'
            '</div>'
        )
    return result


class Cunei(object):
    def __init__(self, repoBase, repoRel, name):
        repoBase = os.path.expanduser(repoBase)
        repo = f'{repoBase}/{repoRel}'
        self.repo = repo
        self.version = VERSION
        self.sourceDir = f'{repo}/{SOURCE_DIR}'
        self.imageDir = f'{repo}/{IMAGE_DIR}'
        self._imagery = {}
        self.corpus = f'{repo}/{CORPUS}'
        self.corpusFull = CORPUS_FULL
        TF = Fabric(locations=[self.corpus], modules=[''], silent=True)
        api = TF.load('', silent=True)
        allFeatures = TF.explore(silent=True, show=True)
        loadableFeatures = allFeatures['nodes'] + allFeatures['edges']
        TF.load(loadableFeatures, add=True, silent=True)
        self.api = api
        self._getImagery()
        self.cwd = os.getcwd()
        cwdPat = re.compile(f'^.*/github/([^/]+)/([^/]+)((?:/.+)?)$', re.I)
        cwdRel = cwdPat.findall(self.cwd)
        if cwdRel:
            (thisOrg, thisRepo, thisPath) = cwdRel[0]
            onlineTail = (
                f'{thisOrg}/{thisRepo}'
                f'/blob/master{thisPath}/{name}.ipynb'
            )
        else:
            cwdRel = None
        nbLink = (
            None
            if name is None or cwdRel is None else f'{URL_NB}/{onlineTail}'
        )
        ghLink = (
            None
            if name is None or cwdRel is None else f'{URL_GH}/{onlineTail}'
        )
        docLink = f'https://github.com/{repoRel}/blob/master/docs'
        extraLink = f'https://dans-labs.github.io/text-fabric/Api/Cunei/'
        dataLink = _outLink(
            self.corpusFull, f'{docLink}/about.md', 'provenance of this corpus'
        )
        featureLink = _outLink(
            'Feature docs', f'{docLink}/transcription.md',
            'feature documentation'
        )
        cuneiLink = _outLink('Cunei API', extraLink, 'cunei api documentation')
        tfLink = _outLink(
            f'Text-Fabric API {api.TF.version}',
            'https://dans-labs.github.io/text-fabric/Api/General/',
            'text-fabric-api'
        )
        tfsLink = _outLink(
            'Search Reference',
            (
                'https://dans-labs.github.io/text-fabric/Api/General/'
                '#search-templates'
            ),
            'Search Templates Introduction and Reference'
        )
        dm(
            '**Documentation:**'
            f' {dataLink} {featureLink} {cuneiLink} {tfLink} {tfsLink}'
        )
        if nbLink:
            dm(
                f'''
This notebook online:
{_outLink('NBViewer', nbLink)}
{_outLink('GitHub', ghLink)}
'''
            )
        thisRepoDir = (
            None if cwdRel is None else f'{repoBase}/{thisOrg}/{thisRepo}'
        )
        self.tempDir = (
            None if cwdRel is None else f'{thisRepoDir}/{TEMP_DIR}'
        )
        self.reportDir = (
            None if cwdRel is None else f'{thisRepoDir}/{REPORT_DIR}'
        )
        for cdir in (self.tempDir, self.reportDir):
            if cdir:
                os.makedirs(cdir, exist_ok=True)

        self._loadCSS()

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
            varmod = (
                f'{modifier}{variant}'
                if modifierFirst else f'{variant}{modifier}'
            )
            result = f'{grapheme}{prime}{varmod}'
        else:
            if repeat == -1:
                repeat = 'N'
            varmod = (
                f'{modifierInner}{variant}'
                if modifierFirst else f'{variant}{modifierInner}'
            )
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
                self.atfFromQuad(child, flags=flags, outer=False) if
                childType == 'quad' else self.atfFromSign(child, flags=flags)
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
                self.atfFromCluster(child, seen=seen) if childType == 'cluster'
                else self.atfFromQuad(child, flags=True) if childType == 'quad'
                else self.atfFromSign(child, flags=True)
                if childType == 'sign' else None
            )
            seen.add(child)
            if thisResult is None:
                dm(
                    f'TF: child of cluster has type {childType}:'
                    ' should not happen'
                )
            result.append(thisResult)
        return f'{bOpen}{" ".join(result)}{bClose}'

    def getOuterQuads(self, n):
        api = self.api
        F = api.F
        E = api.E
        L = api.L
        return [
            quad for quad in L.d(n)
            if (
                F.otype.v(quad) in OUTER_QUAD_TYPES and
                all(F.otype.v(parent) != 'quad' for parent in E.sub.t(quad))
            )
        ]

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
        casesOrLines = [
            c for c in L.d(column)
            if F.terminal.v(c) and F.number.v(c) == caseNum
        ]
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

    # this is a slow implementation!
    def _casesByLevelM(self, lev, terminal=True):
        api = self.api
        E = api.E
        F = api.F
        if lev == 0:
            results = F.otype.s('line')
        else:
            parents = self._casesByLevelM(lev - 1, terminal=False)
            results = reduce(
                operator.add,
                [
                    tuple(s for s in E.sub.f(p) if F.otype.v(s) == 'case')
                    for p in parents
                ],
                (),
            )
        return (
            tuple(r for r in results if F.terminal.v(r))
            if terminal else results
        )

    # this is a fast implementation!
    def _casesByLevelS(self, lev, terminal=True):
        api = self.api
        S = api.S
        sortNodes = api.sortNodes
        query = ''
        for i in range(lev + 1):
            extra = (' terminal' if i == lev and terminal else '')
            nodeType = 'line' if i == 0 else 'case'
            query += ('  ' * i) + f'w{i}:{nodeType}{extra}\n'
        for i in range(lev):
            query += f'w{i} -sub> w{i+1}\n'
        results = list(S.search(query))
        return sortNodes(tuple(r[-1] for r in results))

    def casesByLevel(self, lev, terminal=True):
        api = self.api
        F = api.F
        return ((
            tuple(c for c in F.otype.s('line') if F.terminal.v(c))
            if terminal else F.otype.s('line')
        ) if lev == 0 else (
            tuple(c for c in F.depth.s(lev) if F.terminal.v(c))
            if terminal else F.depth.s(lev)
        ))

    def lineart(self, ns, key=None, asLink=False, withCaption=None, **options):
        return self._getImages(
            ns,
            kind='lineart',
            key=key,
            asLink=asLink,
            withCaption=withCaption,
            **options
        )

    def photo(self, ns, key=None, asLink=False, withCaption=None, **options):
        return self._getImages(
            ns,
            kind='photo',
            key=key,
            asLink=asLink,
            withCaption=withCaption,
            **options
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
            display(HTML(result))

    def tabletLink(self, t, text=None, asString=False):
        api = self.api
        L = api.L
        F = api.F
        if type(t) is str:
            pNum = t
        else:
            n = t if F.otype.v(t) == 'tablet' else L.u(t, otype='tablet')[0]
            pNum = F.catalogId.v(n)

        title = ('to CDLI main page for this tablet')
        linkText = pNum if text is None else text
        url = URL_FORMAT['tablet']['main'].format(pNum)

        result = _outLink(linkText, url, title=title)
        if asString:
            return result
        display(HTML(result))

    def plain(
        self,
        n,
        linked=True,
        lineart=True,
        withNodes=False,
        lineNumbers=False,
        asString=False,
    ):
        api = self.api
        F = api.F

        nType = F.otype.v(n)
        markdown = ''
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
            markdown = (
                f'{rep}{nodeRep}{theLineart}'
            ) if theLineart else f'{rep}{nodeRep}'
        elif nType == 'comment':
            rep = F.type.v(n)
            if linked:
                rep = self.tabletLink(n, text=rep, asString=True)
            markdown = f'{rep}{nodeRep}: {F.text.v(n)}'
        elif nType == 'line' or nType == 'case':
            rep = f'{nType} {F.number.v(n)}'
            if linked:
                rep = self.tabletLink(n, text=rep, asString=True)
            theLine = ''
            if lineNumbers:
                if F.terminal.v(n):
                    theLine = f' @{F.srcLnNum.v(n)} '
            markdown = f'{rep}{nodeRep}{theLine}'
        elif nType == 'column':
            rep = f'{nType} {F.number.v(n)}'
            if linked:
                rep = self.tabletLink(n, text=rep, asString=True)
            theLine = ''
            if lineNumbers:
                theLine = f' @{F.srcLnNum.v(n)} '
            markdown = f'{rep}{nodeRep}{theLine}'
        elif nType == 'face':
            rep = f'{nType} {F.type.v(n)}'
            if linked:
                rep = self.tabletLink(n, text=rep, asString=True)
            theLine = ''
            if lineNumbers:
                theLine = f' @{F.srcLnNum.v(n)} '
            markdown = f'{rep}{nodeRep}{theLine}'
        elif nType == 'tablet':
            rep = f'{nType} {F.catalogId.v(n)}'
            if linked:
                rep = self.tabletLink(n, text=rep, asString=True)
            theLine = ''
            if lineNumbers:
                theLine = f' @{F.srcLnNum.v(n)} '
            markdown = f'{rep}{nodeRep}{theLine}'

        if asString:
            return markdown
        dm(markdown)

    def plainTuple(
        self,
        ns,
        seqNumber,
        linked=1,
        lineart=True,
        withNodes=False,
        lineNumbers=False,
        asString=False,
    ):
        markdown = [str(seqNumber)]
        for (i, n) in enumerate(ns):
            markdown.append(
                self.plain(
                    n,
                    linked=i == linked - 1,
                    lineart=lineart,
                    withNodes=withNodes,
                    lineNumbers=lineNumbers,
                    asString=True,
                ).replace('|', '&#124;')
            )
        markdown = '|'.join(markdown)
        if asString:
            return markdown
        api = self.api
        F = api.F
        head = ['n | ' + (' | '.join(F.otype.v(n) for n in ns))]
        head.append(' | '.join('---' for n in range(len(ns) + 1)))
        head.append(markdown)

        dm('\n'.join(head))

    def table(
        self,
        results,
        start=None,
        end=None,
        linked=1,
        lineart=True,
        withNodes=False,
        lineNumbers=False,
        asString=False,
    ):
        api = self.api
        F = api.F

        collected = []
        if start is None:
            start = 1
        i = -1
        rest = 0
        if not hasattr(results, 'len'):
            if end is None or end > LIMIT_TABLE:
                end = LIMIT_TABLE
            for result in results:
                i += 1
                if i < start - 1:
                    continue
                if i >= end:
                    break
                collected.append((i + 1, result))
        else:
            if end is None:
                end = len(results)
            rest = 0
            if end - (start - 1) > LIMIT_TABLE:
                rest = end - (start - 1) - LIMIT_TABLE
                end = start - 1 + LIMIT_TABLE
            for i in range(start - 1, end):
                collected.append((i + 1, results[i]))

        if len(collected) == 0:
            return
        (firstSeq, firstResult) = collected[0]
        nColumns = len(firstResult)
        markdown = ['n | ' + (' | '.join(F.otype.v(n) for n in firstResult))]
        markdown.append(' | '.join('---' for n in range(nColumns + 1)))
        for (seqNumber, ns) in collected:
            markdown.append(
                self.plainTuple(
                    ns,
                    seqNumber,
                    linked=linked,
                    lineart=lineart,
                    withNodes=withNodes,
                    lineNumbers=lineNumbers,
                    asString=True,
                )
            )
        markdown = '\n'.join(markdown)
        if asString:
            return markdown
        dm(markdown)
        if rest:
            dm(
                f'**{rest} more results skipped**'
                f' because we show a maximum of'
                f' {LIMIT_TABLE} results at a time'
            )

    def pretty(
        self,
        n,
        lineart=True,
        withNodes=False,
        lineNumbers=False,
        suppress=set(),
        highlights={},
    ):
        html = []
        if type(highlights) is set:
            highlights = {m: '' for m in highlights}
        self._pretty(
            n,
            True,
            html,
            seen=set(),
            lineart=lineart,
            withNodes=withNodes,
            lineNumbers=lineNumbers,
            suppress=suppress,
            highlights=highlights,
        )
        htmlStr = '\n'.join(html)
        display(HTML(htmlStr))

    def prettyTuple(
        self,
        ns,
        seqNumber,
        item='Result',
        lineart=True,
        withNodes=False,
        lineNumbers=False,
        suppress=set(),
        colorMap=None,
        highlights=None,
    ):
        api = self.api
        L = api.L
        F = api.F
        sortNodes = api.sortNodes
        tablets = set()
        newHighlights = {}
        for (i, n) in enumerate(ns):
            thisHighlight = None
            if highlights is not None:
                thisHighlight = highlights.get(n, None)
            elif colorMap is not None:
                thisHighlight = colorMap.get(i + 1, None)
            else:
                thisHighlight = ''

            nType = F.otype.v(n)
            if nType == 'tablet':
                tablets.add(n)
            else:
                t = L.u(n, otype='tablet')[0]
                tablets.add(t)
                if thisHighlight is not None:
                    newHighlights[n] = thisHighlight
        dm(f'''
##### {item} {seqNumber}
''')
        for t in sortNodes(tablets):
            self.pretty(
                t,
                lineart=lineart,
                withNodes=withNodes,
                lineNumbers=lineNumbers,
                suppress=suppress,
                highlights=newHighlights,
            )

    def show(
        self,
        results,
        condensed=True,
        start=None,
        end=None,
        lineart=True,
        withNodes=False,
        lineNumbers=False,
        suppress=set(),
        colorMap=None,
        highlights=None,
    ):
        newHighlights = highlights
        if condensed:
            if colorMap is not None:
                newHighlights = {}
                for ns in results:
                    for (i, n) in enumerate(ns):
                        thisHighlight = None
                        if highlights is not None:
                            thisHighlight = highlights.get(n, None)
                        elif colorMap is not None:
                            thisHighlight = colorMap.get(i + 1, None)
                        else:
                            thisHighlight = ''
                        newHighlights[n] = thisHighlight

            results = self._condense(results)

        if start is None:
            start = 1
        i = -1
        if not hasattr(results, 'len'):
            if end is None or end > LIMIT_SHOW:
                end = LIMIT_SHOW
            for result in results:
                i += 1
                if i < start - 1:
                    continue
                if i >= end:
                    break
                self.prettyTuple(
                    result,
                    i + 1,
                    item='Tablet' if condensed else 'Result',
                    lineart=lineart,
                    withNodes=withNodes,
                    lineNumbers=lineNumbers,
                    suppress=suppress,
                    colorMap=colorMap,
                    highlights=newHighlights,
                )
        else:
            if end is None:
                end = len(results)
            rest = 0
            if end - (start - 1) > LIMIT_SHOW:
                rest = end - (start - 1) - LIMIT_SHOW
                end = start - 1 + LIMIT_SHOW
            for i in range(start - 1, end):
                self.prettyTuple(
                    results[i],
                    i + 1,
                    item='Tablet' if condensed else 'Result',
                    lineart=lineart,
                    withNodes=withNodes,
                    lineNumbers=lineNumbers,
                    suppress=suppress,
                    colorMap=colorMap,
                    highlights=newHighlights,
                )
            if rest:
                dm(
                    f'**{rest} more results skipped**'
                    f' because we show a maximum of'
                    f' {LIMIT_SHOW} results at a time'
                )

    def search(self, query, silent=False, sets=None, shallow=False):
        api = self.api
        S = api.S
        results = S.search(query, sets=sets, shallow=shallow)
        if not shallow:
            results = sorted(results)
        nResults = len(results)
        plural = '' if nResults == 1 else 's'
        if not silent:
            print(f'{nResults} result{plural}')
        return results

    def _condense(self, results):
        api = self.api
        F = api.F
        L = api.L
        sortNodes = api.sortNodes
        tablets = {}
        for ns in results:
            for n in ns:
                if F.otype.v(n) == 'tablet':
                    tablets.setdefault(n, set())
                else:
                    t = L.u(n, otype='tablet')[0]
                    tablets.setdefault(t, set()).add(n)
        return tuple((t, ) + tuple(tablets[t]) for t in sortNodes(tablets))

    def _pretty(
        self,
        n,
        outer,
        html,
        lineart=True,
        withNodes=False,
        lineNumbers=False,
        seen=set(),
        suppress=set(),
        highlights={},
    ):
        api = self.api
        L = api.L
        F = api.F
        E = api.E
        sortNodes = api.sortNodes
        hl = highlights.get(n, None)
        hlClass = ''
        hlStyle = ''
        if hl == '':
            hlClass = ' hl'
        else:
            hlStyle = f' style="background-color: {hl};"'

        nType = F.otype.v(n)
        className = nType
        nodePart = (f'<span class="nd">{n}</span>' if withNodes else '')
        heading = ''
        featurePart = ''
        commentsPart = self._getComments(
            n, withNodes=withNodes, lineNumbers=lineNumbers
        ) if nType in COMMENT_TYPES else ''
        children = ()

        if nType == 'tablet':
            heading = F.catalogId.v(n)
            heading += ' '
            heading += self._getFeatures(
                n,
                suppress,
                ('name', 'period', 'excavation'),
                plain=True,
            )
            children = L.d(n, otype='face')
        elif nType == 'face':
            heading = F.type.v(n)
            featurePart = self._getFeatures(
                n,
                suppress,
                ('identifier', 'fragment'),
            )
            children = L.d(n, otype='column')
        elif nType == 'column':
            heading = F.number.v(n)
            if F.prime.v(n):
                heading += "'"
            children = L.d(n, otype='line')
        elif nType == 'line' or nType == 'case':
            heading = F.number.v(n)
            if F.prime.v(n):
                heading += "'"
            if F.terminal.v(n):
                className = 'trminal'
                theseFeats = ('srcLnNum', ) if lineNumbers else ()
                featurePart = self._getFeatures(
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
            heading = F.type.v(n)
            featurePart = self._getFeatures(
                n,
                suppress,
                ('text', ),
            )
        elif nType == 'cluster':
            seen.add(n)
            heading = CLUSTER_TYPES.get(F.type.v(n), '')
            children = sortNodes(
                set(L.d(n, otype='cluster'))
                | set(L.d(n, otype='quad'))
                | set(L.d(n, otype='sign'))
            )
        elif nType == 'quad':
            seen.add(n)
            children = E.sub.f(n)
        elif nType == 'sign':
            featurePart = self._getAtf(n)
            seen.add(n)
            if not outer and F.type.v(n) == 'empty':
                return

        if outer:
            typePart = self.tabletLink(
                n, text=f'{nType} {heading}', asString=True
            )
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
                html.append(
                    f'<div class="contnr {className}{hlClass}"{hlStyle}>'
                )
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
                isOuter = outer or (
                    all(F.otype.v(parent) != 'quad' for parent in E.sub.t(n))
                )
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
                html.append(
                    f'''
    <div class="children {className}{caseDir}">
'''
                )

        for ch in children:
            if ch not in seen:
                self._pretty(
                    ch,
                    False,
                    html,
                    seen=seen,
                    lineart=lineart,
                    withNodes=withNodes,
                    lineNumbers=lineNumbers,
                    suppress=suppress,
                    highlights=highlights,
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

    def _getFeatures(self, n, suppress, features, plain=False):
        api = self.api
        Fs = api.Fs
        featurePart = '' if plain else '<div class="features">'
        for name in features:
            if 'name' not in suppress:
                value = Fs(name).v(n)
                if value is not None:
                    featurePart += (
                        f' <span class="{name}">{Fs(name).v(n)}</span>'
                    )
        if not plain:
            featurePart += '</div>'
        return featurePart

    def _getComments(self, n, withNodes=False, lineNumbers=False):
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
                    lineart=False,
                    withNodes=withNodes,
                    lineNumbers=lineNumbers,
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

    def _loadCSS(self):
        display(HTML(CSS))

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
        attStr = ' '.join(
            f'{opt}="{value}"' for (opt, value) in options.items()
            if opt not in SIZING
        )
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
        cssStr = ' '.join(
            f'{opt}: {value};' for (opt, value) in cssProps.items()
        )
        if withCaption is None:
            withCaption = None if asLink else 'bottom'
        for n in ns:
            caption = None
            (nType, objectType, identifier) = self._imageClass(n)
            if objectType:
                imageBase = self._imagery.get(objectType, {}).get(kind, {})
                images = imageBase.get(identifier, None)
                if withCaption:
                    caption = _wrapLink(
                        identifier, objectType, 'main', identifier
                    )
                if images is None:
                    thisImage = (
                        f'<span><b>no {kind}</b> for {objectType}'
                        f' <code>{identifier}</code></span>'
                    ) if warning else ''
                else:
                    image = images.get(key or '', None)
                    if image is None:
                        thisImage = (
                            '<span><b>try</b>'
                            ' key=<code>'
                            f'{"</code> <code>".join(sorted(images.keys()))}'
                            '</code></span>'
                        ) if warning else ''
                    else:
                        if asLink:
                            thisImage = identifier
                        else:
                            theImage = self._useImage(
                                image, kind, key or '', n
                            )
                            thisImage = (
                                f'<img src="{theImage}"'
                                f' style="display: inline;{cssStr}"'
                                f' {attStr} />'
                            )
                thisResult = _wrapLink(
                    thisImage,
                    objectType,
                    kind,
                    identifier,
                    pos=withCaption,
                    caption=caption
                ) if thisImage else None
            else:
                thisResult = (
                    f'<span><b>no {kind}</b> for'
                    f' <code>{nType}</code>s</span>'
                ) if warning else ''
            result.append(thisResult)
        if not warning:
            result = [image for image in result if image]
        if not result:
            return ''
        if asString:
            return ''.join(result)
        resultStr = f'</div><div style="{ITEM_STYLE}">'.join(result)
        html = (
            f'<div style="{FLEX_STYLE}">'
            f'<div style="{ITEM_STYLE}">'
            f'{resultStr}</div></div>'
        ).replace('\n', '')
        display(HTML(html))
        if not warning:
            return True

    def _useImage(self, image, kind, key, node):
        api = self.api
        F = api.F
        (imageDir, imageName) = os.path.split(image)
        (base, ext) = os.path.splitext(imageName)
        localDir = f'{self.cwd}/{LOCAL_DIR}'
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
            nodeRep.lower().replace('|', 'q').replace('~', '-')
            .replace('@', '(a)').replace('&', '(e)')
            .replace('+', '(p)').replace('.', '(d)')
        )
        keyRep = '' if key == '' else f'-{key}'
        localImageName = f'{kind}-{nodeRep}{keyRep}{ext}'
        localImagePath = f'{localDir}/{localImageName}'
        if (
            not os.path.exists(localImagePath) or
            os.path.getmtime(image) > os.path.getmtime(localImagePath)
        ):
            copyfile(image, localImagePath)
        return f'{LOCAL_DIR}/{localImageName}'

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
                    key = ''
                images.setdefault(identifier, {})[key] = filePath
            self._imagery.setdefault(objectType, {})[kind] = images
            print(f'Found {len(images)} {objectType} {kind}s')
