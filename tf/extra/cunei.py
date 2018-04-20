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

LIMIT = 20

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
        extraLink = f'https://github.com/Dans-labs/text-fabric/wiki/Cunei'
        dataLink = _outLink(
            self.corpusFull, f'{docLink}/about.md', 'provenance of this corpus'
        )
        featureLink = _outLink(
            'Feature docs', f'{docLink}/transcription.md',
            'feature documentation'
        )
        cuneiLink = _outLink('Cunei API', extraLink, 'cunei api documentation')
        tfLink = _outLink(
            'Text-Fabric API',
            'https://github.com/Dans-labs/text-fabric/wiki/api',
            'text-fabric-api'
        )
        dm(f'**Documentation:** {dataLink} {featureLink} {cuneiLink} {tfLink}')
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
            parents = self.casesByLevel(lev - 1, terminal=False)
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
    def casesByLevel(self, lev, terminal=True):
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
        **options
    ):
        if type(ns) is int or type(ns) is str:
            ns = [ns]
        result = []
        attStr = ' '.join(
            f'{opt}="{value}"'
            for (opt, value) in options.items()
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
            f'{opt}: {value};'
            for (opt, value) in cssProps.items()
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
                            theImage = self._useImage(image, kind, n)
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
        resultStr = f'</div>\n<div style="{ITEM_STYLE}">'.join(result)
        html = f'''
        <div style="{FLEX_STYLE}">
            <div style="{ITEM_STYLE}">
                {resultStr}
            </div>
        </div>
        '''.replace('\n', '')

        return HTML(html)

    def cdli(self, n, linkText=None):
        (nType, objectType, identifier) = self._imageClass(n)
        if linkText is None:
            linkText = identifier
        return _wrapLink(linkText, objectType, 'main', identifier)

    def _useImage(self, image, kind, node):
        (imageDir, imageName) = os.path.split(image)
        (base, ext) = os.path.splitext(imageName)
        localDir = f'{self.cwd}/{LOCAL_DIR}'
        if not os.path.exists(localDir):
            os.makedirs(localDir, exist_ok=True)
        localImageName = f'node{node}{kind}{ext}'
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
