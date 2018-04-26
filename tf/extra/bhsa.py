import os
import re
from IPython.display import display, Markdown, HTML

URL_GH = 'https://github.com'
URL_NB = 'http://nbviewer.jupyter.org/github'

CORPUS = 'BHSA'

SHEBANQ_URL = 'https://shebanq.ancient-data.org/hebrew'
SHEBANQ = (
    f'{SHEBANQ_URL}/text'
    '?book={book}&chapter={chapter}&verse={verse}&version={version}'
    '&mr=m&qw=q&tp=txt_p&tr=hb&wget=v&qget=v&nget=vt'
)
SHEBANQ_LEX = (f'{SHEBANQ_URL}/word' '?version={version}' '&id={lid}')

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
.lex {
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
.vl {
    font-family: monospace;
    font-size: medium;
    color: #0000bb;
}
.vvs {
    font-family: monospace;
    font-size: medium;
    font-weight: bold;
    color: #0000bb;
}
.vvt {
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
    lex='lex',
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
        self,
        api,
        name,
        version='c',
    ):
        self.version = version
        api.TF.load(
            '''
            sp vs vt
            lex language gloss voc_lex voc_lex_utf8
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
        docLink = f'https://etcbc.github.io/bhsa'
        extraLink = f'https://github.com/Dans-labs/text-fabric/wiki/Bhsa'
        dataLink = _outLink(CORPUS, docLink, '{provenance of this corpus}')
        featureLink = _outLink(
            'Feature docs',
            f'{docLink}/features/hebrew/{self.version}/0_home.html',
            '{CORPUS} feature documentation'
        )
        bhsaLink = _outLink('BHSA API', extraLink, 'BHSA API documentation')
        tfLink = _outLink(
            'Text-Fabric API',
            'https://github.com/Dans-labs/text-fabric/wiki/api',
            'text-fabric-api'
        )
        tfsLink = _outLink(
            'Search Reference',
            (
                'https://github.com/Dans-labs/text-fabric/wiki/api'
                '#search-template-introduction'
            ),
            'Search Templates Introduction and Reference'
        )
        _dm(
            '**Documentation:**'
            f' {dataLink} {featureLink} {bhsaLink} {tfLink} {tfsLink}'
        )
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
        if nType == 'lex':
            lex = F.lex.v(n)
            lan = F.language.v(n)
            lexId = '{}{}'.format(
                '1' if lan == 'Hebrew' else '2',
                lex.replace('>', 'A').replace('<',
                                              'O').replace('[', 'v').replace(
                                                  '/', 'n'
                                              ).replace('=', 'i'),
            )
            href = SHEBANQ_LEX.format(
                version=version,
                lid=lexId,
            )
            title = 'show this lexeme in SHEBANQ'
            if text is None:
                text = F.voc_lex_utf8.v(n)
            return _outLink(text, href, title=title)

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
            firstSlot=None,
            lastSlot=None,
            withNodes=withNodes,
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
        withNodes=True,
        suppress=set(),
    ):
        api = self.api
        L = api.L
        F = api.F
        sortNodes = api.sortNodes
        verses = set()
        lexemes = set()
        highlights = set()
        for n in ns:
            nType = F.otype.v(n)
            if nType not in SECTION:
                firstSlot = n if nType == 'word' else L.d(n, otype='word')[0]
                if nType == 'lex':
                    lexemes.add(n)
                    highlights.add(n)
                else:
                    verses.add(L.u(firstSlot, otype='verse')[0])
                    atomType = SUPER.get(nType, None)
                    if atomType:
                        highlights |= set(L.d(n, otype=atomType))
                    else:
                        highlights.add(n)
        _dm(f'''
##### {item} {seqNumber}
''')
        for l in sortNodes(lexemes):
            self.pretty(
                l,
                withNodes=withNodes,
                suppress=suppress,
                highlights=highlights,
            )
        for v in sortNodes(verses):
            self.pretty(
                v,
                withNodes=withNodes,
                suppress=suppress,
                highlights=highlights,
            )

    def search(self, query):
        api = self.api
        S = api.S
        return list(S.search(query))

    def show(
        self,
        results,
        condensed=False,
        start=None,
        end=None,
        withNodes=True,
        suppress=set(),
    ):
        if condensed:
            results = self._condense(results)
        if start is None:
            start = 0
        i = -1
        if not hasattr(results, 'len'):
            if end is None or end > LIMIT:
                end = LIMIT
            for result in results:
                i += 1
                if i < start:
                    continue
                if i > end:
                    break
                self.prettyTuple(
                    result,
                    i,
                    item='Passage' if condensed else 'Result',
                    withNodes=withNodes,
                    suppress=suppress,
                )
        else:
            if end is None:
                end = len(results)
            rest = 0
            if end - start > LIMIT:
                rest = end - start - LIMIT
                end = start + LIMIT
            for i in range(start, end):
                self.prettyTuple(
                    results[i],
                    i,
                    item='Passage' if condensed else 'Result',
                    withNodes=withNodes,
                    suppress=suppress,
                )
            if rest:
                _dm(
                    f'**{rest} more results skipped**'
                    f' because we show a maximum of {LIMIT} results at a time'
                )

    def _condense(self, results):
        api = self.api
        F = api.F
        L = api.L
        sortNodes = api.sortNodes
        passages = {}
        for ns in results:
            for n in ns:
                nType = F.otype.v(n)
                if nType in SECTION:
                    passages.setdefault(n, set())
                    if nType != 'verse':
                        passages[n].add(n)
                else:
                    fw = n if nType == 'word' else L.d(n, otype='word')[0]
                    v = L.u(fw, otype='verse')[0]
                    passages.setdefault(v, set()).add(n)
        return tuple((p,) + tuple(passages[p]) for p in sortNodes(passages))

    def _pretty(
        self,
        n,
        html,
        firstSlot=None,
        lastSlot=None,
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
        if ((firstSlot and myEnd < firstSlot)
            or (lastSlot and myStart > lastSlot)):  # noqa 129
            return
        if firstSlot and (myStart < firstSlot):
            boundaryClass += ' R'
        if lastSlot and (myEnd > lastSlot):
            boundaryClass += ' L'
        if nType == 'book':
            html.append(self.shbLink(n))
            return
        elif nType == 'chapter':
            html.append(self.shbLink(n))
            return
        elif nType == 'half_verse':
            html.append(self.shbLink(n))
            return
        elif nType == 'verse':
            label = self.shbLink(n)
            (firstSlot, lastSlot) = self._getBoundary(n)
            children = sortNodes(
                set(L.d(n, otype='sentence_atom')) | {
                    L.u(firstSlot, otype='sentence_atom')[0],
                    L.u(lastSlot, otype='sentence_atom')[0],
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
        elif nType == 'lex':
            children = ()
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
            if F.sp.v(n) == 'verb':
                if 'vs' not in suppress:
                    html.append(f'<div class="vvs">' f'{F.vs.v(n)}</div>')
                if 'vt' not in suppress:
                    html.append(f'<div class="vvt">' f'{F.vt.v(n)}</div>')
        elif nType == 'lex':
            html.append(f'<div class="h">{F.voc_lex_utf8.v(n)}</div>')
            if 'voc_lex' not in suppress:
                llink = self.shbLink(
                    n, text=F.voc_lex.v(n).replace("<", "&lt;")
                )
                html.append(f'<div class="vl">{llink}</div>')
            if 'gloss' not in suppress:
                html.append(
                    f'<div class="gl">'
                    f'{F.gloss.v(n).replace("<", "&lt;")}</div>'
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
                firstSlot=firstSlot,
                lastSlot=lastSlot,
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
