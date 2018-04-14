import os
import re
from IPython.display import display, Markdown, HTML

URL_GH = 'https://github.com'
URL_NB = 'http://nbviewer.jupyter.org/github'

CORPUS = 'BHSA'

SHEBANQ = (
    'https://shebanq.ancient-data.org/hebrew/text'
    '?book={book}&chapter={chapter}&verse={verse}&version={version}'
    '&mr=m&qw=q&tp=txt_p&tr=hb&wget=v&qget=v&nget=vt'
)

LIMIT = 100

CSS = '''
<style>
.verse {
    display: flex;
    flex-flow: row wrap;
    direction: rtl;
}
.vl {
    display: flex;
    flex-flow: column nowrap;
    direction: ltr;
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
.h {
    font-family: "Ezra SIL", "SBL Hebrew", sans-serif;
    font-size: large;
    direction: rtl;
}
.rela,.function,.typ {
    font-family: monospace;
    font-size: small;
    color: #0000bb;
}
.sp {
    font-family: monospace;
    font-size: medium;
    color: #0000bb;
}
.gl {
    font-family: sans-serif;
    font-size: small;
    color: #aaaaaa;
}
.vs {
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
)

ATOMS = dict(
    sentence_atom='sentence',
    clause_atom='clause',
    phrase_atom='phrase',
)
SUPER = dict((y, x) for (x, y) in ATOMS.items())

SECTION = {'book', 'chapter', 'verse', 'half_verse'}


def _dm(md):
    display(Markdown(md))


def _outLink(text, href, title=None):
    titleAtt = '' if title is None else f' title="{title}"'
    return f'<a target="_blank" href="{href}"{titleAtt}>{text}</a>'


class Bhsa(object):
    def __init__(
        self, api, name,
        version='c',
    ):
        self.version = version
        api.TF.load(
            '''
            sp gloss
            function typ rela
            number label book
        ''',
            add=True,
            silent=True
        )
        self.api = api
        self.cwd = os.getcwd()
        cwdPat = re.compile(f'^.*/github/([^/]+)/([^/]+)((?:/.+)?)$', re.I)
        cwdRel = cwdPat.findall(self.cwd)
        if cwdRel:
            (thisOrg, thisRepo, thisPath) = cwdRel[0]
        else:
            cwdRel = None
        onlineTail = (
            f'{thisOrg}/{thisRepo}'
            f'/blob/master{thisPath}/{name}.ipynb'
        )
        nbLink = (
            None
            if name is None or cwdRel is None else f'{URL_NB}/{onlineTail}'
        )
        ghLink = (
            None
            if name is None or cwdRel is None else f'{URL_GH}/{onlineTail}'
        )
        docLink = f'https://etcbc.github.io/bhsa'
        extraLink = f'https://github.com/Dans-labs/text-fabric/wiki/Bhsa'
        dataLink = _outLink(CORPUS, docLink, '{provenance of this corpus}')
        featureLink = _outLink(
            'Feature docs',
            f'{docLink}/features/hebrew/{self.version}/0_home.html',
            '{CORPUS} feature documentation'
        )
        bhsaLink = _outLink(
            'BHSA API', extraLink, 'BHSA API documentation'
        )
        tfLink = _outLink(
            'Text-Fabric API',
            'https://github.com/Dans-labs/text-fabric/wiki/api',
            'text-fabric-api'
        )
        _dm(f'**Documentation:** {dataLink} {featureLink} {bhsaLink} {tfLink}')
        if nbLink:
            _dm(
                f'''
This notebook online:
{_outLink('NBViewer', nbLink)}
{_outLink('GitHub', ghLink)}
'''
            )
        self._loadCSS()

    def shbLink(self, n, text=None):
        api = self.api
        L = api.L
        T = api.T
        F = api.F
        version = self.version
        nType = F.otype.v(n)
        (bookE, chapter, verse) = T.sectionFromNode(n)
        bookNode = n if nType == 'book' else L.u(n, otype='book')[0]
        book = F.book.v(bookNode)
        passageText = (
            bookE if nType == 'book' else '{} {}'.format(bookE, chapter) if
            nType == 'chapter' else '{} {}:{}'.format(bookE, chapter, verse)
        )
        href = SHEBANQ.format(
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
        return _outLink(text, href, title=title)

    def pretty(self, n, withNodes=True, suppress=set(), highlights=set()):
        html = []
        self._pretty(
            n,
            html,
            firstWord=None,
            lastWord=None,
            withNodes=withNodes,
            suppress=suppress,
            highlights=highlights,
        )
        htmlStr = '\n'.join(html)
        # print(htmlStr)
        display(HTML(htmlStr))

    def prettyTuple(self, ns, seqNumber, withNodes=True, suppress=set()):
        api = self.api
        L = api.L
        T = api.T
        F = api.F
        sortNodes = api.sortNodes
        heading = []
        verses = set()
        highlights = set()
        for n in ns:
            nType = F.otype.v(n)
            nodeRep = None
            if nType == 'book':
                nodeRep = f'**{T.sectionFromNode(n)[0]}**'
            elif nType == 'chapter':
                nodeRep = '**{} {}**'.format(*T.sectionFromNode(n))
            elif nType == 'verse':
                nodeRep = '**{} {}:{}**'.format(*T.sectionFromNode(n))
            elif nType == 'half_verse':
                nodeRep = '**{} {}:{}{}**'.format(
                    *T.sectionFromNode(n),
                    F.label.v(n),
                )
            else:
                nodePart = f' `{n}`' if withNodes else ''
                nodeRep = f'**{nType}**{nodePart}'
                firstWord = n if nType == 'word' else L.d(n, otype='word')[0]
                verses.add(L.u(firstWord, otype='verse')[0])
                atomType = SUPER.get(nType, None)
                if atomType:
                    highlights |= set(L.d(n, otype=atomType))
                else:
                    highlights.add(n)
            heading.append(nodeRep)
        _dm(f'''
## Result {seqNumber}
({", ".join(heading)})
''')
        for v in sortNodes(verses):
            self.pretty(
                v,
                withNodes=withNodes,
                suppress=suppress,
                highlights=highlights
            )

    def search(self, query):
        api = self.api
        S = api.S
        return list(S.search(query))

    def show(
        self, results, start=None, end=None, withNodes=True, suppress=set()
    ):
        if start is None:
            start = 0
        if end is None:
            end = len(results)
        rest = 0
        if end - start > LIMIT:
            rest = end - start - LIMIT
            end = start + LIMIT
        for i in range(start, end):
            self.prettyTuple(
                results[i], i, withNodes=withNodes, suppress=suppress
            )
        if rest:
            _dm(
                f'**{rest} more results skipped**'
                f' because we show a maximum of {LIMIT} results at a time'
            )

    def _pretty(
        self,
        n,
        html,
        firstWord=None,
        lastWord=None,
        withNodes=True,
        suppress=set(),
        highlights=set()
    ):
        api = self.api
        L = api.L
        T = api.T
        F = api.F
        sortNodes = api.sortNodes
        hl = ' hl' if n in highlights else ''
        nType = F.otype.v(n)
        className = CLASS_NAMES.get(nType, None)
        superType = ATOMS.get(nType, None)
        boundaryClass = ''
        (myStart, myEnd) = (n, n) if nType == 'word' else self._getBoundary(n)
        if superType:
            (superNode, superStart, superEnd) = self._getSuper(n, superType)
            if superStart < myStart:
                boundaryClass += ' r'
            if superEnd > myEnd:
                boundaryClass += ' l'
        if ((firstWord and myEnd < firstWord)
            or (lastWord and myStart > lastWord)):  # noqa 129
            return
        if firstWord and (myStart < firstWord):
            boundaryClass += ' R'
        if lastWord and (myEnd > lastWord):
            boundaryClass += ' L'
        if nType == 'book':
            return self.shbLink(n)
        elif nType == 'chapter':
            return self.shbLink(n)
        elif nType == 'verse':
            label = self.shbLink(n)
            (firstWord, lastWord) = self._getBoundary(n)
            children = sortNodes(
                set(L.d(n, otype='sentence_atom')) | {
                    L.u(firstWord, otype='sentence_atom')[0],
                    L.u(lastWord, otype='sentence_atom')[0],
                }
            )
        elif nType == 'sentence':
            children = L.d(n, otype='sentence_atom')
        elif nType == 'sentence_atom' or nType == 'clause':
            children = L.d(n, otype='clause_atom')
        elif nType == 'clause_atom' or nType == 'phrase':
            children = L.d(n, otype='phrase_atom')
        elif nType == 'phrase_atom' or nType == 'subphrase':
            children = L.d(n, otype='word')
        elif nType == 'word':
            children = ()
            lx = L.u(n, otype='lex')[0]
        html.append(f'''<div class="{className} {boundaryClass} {hl}">''')
        if nType == 'verse':
            nodePart = f'<div class="nd">{n}</div>' if withNodes else ''
            html.append(
                f'''
    <div class="vl">
        <div class="vs">{label}</div>{nodePart}
    </div>
'''
            )
        elif nType == 'word':
            html.append(f'<div class="h">{T.text([n])}</div>')
            if 'sp' not in suppress:
                html.append(
                    f'<div class="sp">{self.shbLink(n, text=F.sp.v(n))}</div>'
                )
            if 'gloss' not in suppress:
                html.append(
                    f'<div class="gl">'
                    f'{F.gloss.v(lx).replace("<", "&lt;")}</div>'
                )
        elif superType:
            nodePart = (
                f'<span class="nd">{superNode}</span>' if withNodes else ''
            )
            typePart = self.shbLink(superNode, text=superType)
            featurePart = ''
            if superType == 'clause':
                if 'rela' not in suppress:
                    featurePart += (
                        f' <span class="rela">{F.rela.v(superNode)}</span>'
                    )
                if 'typ' not in suppress:
                    featurePart += (
                        f' <span class="typ">{F.typ.v(superNode)}</span>'
                    )
            elif superType == 'phrase':
                if 'function' not in suppress:
                    featurePart += (
                        f' <span class="function">'
                        f'{F.function.v(superNode)}</span>'
                    )
                if 'typ' not in suppress:
                    featurePart += (
                        f' <span class="typ">{F.typ.v(superNode)}</span>'
                    )
            html.append(
                f'''
    <div class="{superType}">{typePart} {nodePart} {featurePart}
    </div>
    <div class="atoms">
'''
            )
        for ch in children:
            self._pretty(
                ch,
                html,
                firstWord=firstWord,
                lastWord=lastWord,
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

    def _getBoundary(self, n):
        api = self.api
        L = api.L
        words = L.d(n, otype='word')
        return (words[0], words[-1])

    def _getSuper(self, n, tp):
        api = self.api
        L = api.L
        superNode = L.u(n, otype=tp)[0]
        return (superNode, *self._getBoundary(superNode))

    def _loadCSS(self):
        display(HTML(CSS))
