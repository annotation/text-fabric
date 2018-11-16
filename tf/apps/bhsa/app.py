from tf.applib.apphelpers import (
    prettyPre,
    getBoundary,
    getFeatures,
    htmlEsc,
    mdEsc,
    dm,
    dh,
)
from tf.applib.appmake import setupApi, outLink

SHEBANQ_URL = 'https://shebanq.ancient-data.org/hebrew'

SHEBANQ = (
    f'{SHEBANQ_URL}/text'
    '?book={book}&chapter={chapter}&verse={verse}&version={version}'
    '&mr=m&qw=q&tp=txt_p&tr=hb&wget=v&qget=v&nget=vt'
)

SHEBANQ_LEX = (f'{SHEBANQ_URL}/word' '?version={version}&id={lid}')

ATOMS = dict(
    sentence_atom='sentence',
    clause_atom='clause',
    phrase_atom='phrase',
)
SECTION = {'book', 'chapter', 'verse', 'half_verse'}
VERSE = {'verse', 'half_verse'}


class TfApp(object):

  def __init__(*args, **kwargs):
    setupApi(*args, **kwargs)

  def webLink(app, n, text=None, className=None, asString=False, noUrl=False):
    api = app.api
    L = api.L
    T = api.T
    F = api.F
    version = app.version
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
      dh(result)
      return

    (bookE, chapter, verse) = T.sectionFromNode(n)
    bookNode = n if nType == 'book' else L.u(n, otype='book')[0]
    book = F.book.v(bookNode)
    passageText = (
        bookE if nType == 'book' else
        f'{bookE} {chapter}' if nType == 'chapter' else f'{bookE} {chapter}:{verse}{F.label.v(n)}'
        if nType == 'half_verse' else f'{bookE} {chapter}:{verse}'
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
    result = outLink(
        text,
        href,
        title=title,
        className=className,
        target=target,
        passage=passageText,
    )
    if asString:
      return result
    dh(result)

  def plain(
      app,
      n,
      linked=True,
      fmt=None,
      withNodes=False,
      asString=False,
  ):
    asApp = app.asApp
    api = app.api
    L = api.L
    T = api.T
    F = api.F

    nType = F.otype.v(n)
    result = ''
    if asApp:
      nodeRep = f' <a href="#" class="nd">{n}</a> ' if withNodes else ''
    else:
      nodeRep = f' *{n}* ' if withNodes else ''

    isText = fmt is None or '-orig-' in fmt
    if nType == 'word':
      rep = mdEsc(htmlEsc(T.text([n], fmt=fmt)))
    elif nType in SECTION:
      label = ('{}' if nType == 'book' else '{} {}' if nType == 'chapter' else '{} {}:{}')
      rep = label.format(*T.sectionFromNode(n))
      isText = False
      if nType == 'half_verse':
        rep += F.label.v(n)
      rep = mdEsc(htmlEsc(rep))
      if nType in VERSE:
        if linked:
          rep = app.webLink(n, text=rep, className='vn', asString=True)
        else:
          rep = f'<span class="vn">{rep}</span>'
        rep += mdEsc(htmlEsc(T.text(L.d(n, otype="word"), fmt=fmt)))
        isText = True
    elif nType == 'lex':
      rep = mdEsc(htmlEsc(F.voc_lex_utf8.v(n)))
    else:
      rep = mdEsc(htmlEsc(T.text(L.d(n, otype='word'), fmt=fmt)))

    if linked and nType not in VERSE:
      rep = app.webLink(n, text=rep, asString=True)

    tClass = app.formatClass[fmt] if isText else 'trb'
    rep = f'<span class="{tClass}">{rep}</span>'
    result = f'{rep}{nodeRep}'

    if asString or asApp:
      return result
    dm((result))

  def _pretty(
      app,
      n,
      outer,
      html,
      firstSlot,
      lastSlot,
      condenseType=None,
      fmt=None,
      withNodes=True,
      suppress=set(),
      highlights={},
  ):
    goOn = prettyPre(
        app,
        n,
        firstSlot,
        lastSlot,
        withNodes,
        highlights,
    )
    if not goOn:
      return
    (
        slotType,
        nType,
        className,
        boundaryClass,
        hlClass,
        hlStyle,
        nodePart,
        myStart,
        myEnd,
    ) = goOn

    api = app.api
    F = api.F
    L = api.L
    T = api.T
    sortNodes = api.sortNodes
    otypeRank = api.otypeRank

    bigType = False
    if condenseType is not None and otypeRank[nType] > otypeRank[condenseType]:
      bigType = True

    if nType == 'book':
      html.append(app.webLink(n, asString=True))
      return
    if nType == 'chapter':
      html.append(app.webLink(n, asString=True))
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
      (superNode, superStart, superEnd) = app._getSuper(n, superType)
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
      passage = app.webLink(n, asString=True)
      html.append(
          f'''
    <div class="vl">
        <div class="vrs">{passage}</div>
        {nodePart}
    </div>
'''
      )
    elif superType:
      typePart = app.webLink(superNode, text=superType, asString=True)
      featurePart = ''
      if superType == 'sentence':
        featurePart = getFeatures(
            app,
            superNode,
            suppress,
            ('number', ),
            plain=True,
        )
      elif superType == 'clause':
        featurePart = getFeatures(
            app,
            superNode,
            suppress,
            ('rela', 'typ'),
            plain=True,
        )
      elif superType == 'phrase':
        featurePart = getFeatures(
            app,
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
        lexLink = (app.webLink(lx, text=htmlEsc(T.text([n], fmt=fmt)), asString=True))
        tClass = 'h' if fmt is None or '-orig-' in fmt else 'tr'
        heading = f'<div class="{tClass}">{lexLink}</div>'
        featurePart = getFeatures(
            app,
            n,
            suppress,
            ('pdp', 'gloss', 'vs', 'vt'),
            givenValue=dict(
                pdp=app.webLink(n, text=htmlEsc(F.pdp.v(n)), asString=True),
                gloss=htmlEsc(F.gloss.v(lx)),
            ),
        )
      elif nType == 'lex':
        occs = L.d(n, otype='word')
        extremeOccs = sorted({occs[0], occs[-1]})
        linkOccs = ' - '.join(app.webLink(lo, asString=True) for lo in extremeOccs)
        heading = f'<div class="h">{htmlEsc(F.voc_lex_utf8.v(n))}</div>'
        occs = f'<div class="occs">{linkOccs}</div>'
        featurePart = getFeatures(
            app,
            n,
            suppress,
            ('voc_lex', 'gloss'),
            givenValue=dict(voc_lex=app.webLink(n, text=htmlEsc(F.voc_lex.v(n)), asString=True)),
        )
      html.append(heading)
      html.append(featurePart)
      html.append(occs)

    for ch in children:
      app._pretty(
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

  def _getSuper(app, n, tp):
    api = app.api
    L = api.L
    superNode = L.u(n, otype=tp)[0]
    return (superNode, *getBoundary(api, superNode))
