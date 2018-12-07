from tf.core.helpers import htmlEsc, mdEsc
from tf.applib.helpers import dm, dh
from tf.applib.display import prettyPre, getBoundary, getFeatures
from tf.applib.highlight import getHlAtt, hlText, hlRep
from tf.applib.api import setupApi
from tf.applib.links import outLink

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

  def webLink(app, n, text=None, className=None, _asString=False, _noUrl=False):
    api = app.api
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
      if _asString:
        return result
      dh(result)
      return

    (bookLa, chapter, verse) = T.sectionFromNode(n, lang='la', fillup=True)
    passageText = app.sectionStrFromNode(n)
    href = '#' if _noUrl else SHEBANQ.format(
        version=version,
        book=bookLa,
        chapter=chapter,
        verse=verse,
    )
    if text is None:
      text = passageText
      title = 'show this passage in SHEBANQ'
    else:
      title = passageText
    if _noUrl:
      title = None
    target = '' if _noUrl else None
    result = outLink(
        text,
        href,
        title=title,
        className=className,
        target=target,
        passage=passageText,
    )
    if _asString:
      return result
    dh(result)

  def _plain(
      app,
      n,
      passage,
      isLinked,
      _asString,
      secLabel,
      **options,
  ):
    display = app.display
    d = display.get(options)

    _asApp = app._asApp
    api = app.api
    L = api.L
    T = api.T
    F = api.F

    nType = F.otype.v(n)
    result = passage
    if _asApp:
      nodeRep = f' <a href="#" class="nd">{n}</a> ' if d.withNodes else ''
    else:
      nodeRep = f' *{n}* ' if d.withNodes else ''

    isText = d.fmt is None or '-orig-' in d.fmt
    if nType == 'word':
      rep = hlText(app, [n], d.highlights, fmt=d.fmt)
    elif nType in SECTION:
      if secLabel:
        label = ('{}' if nType == 'book' else '{} {}' if nType == 'chapter' else '{} {}:{}')
        rep = label.format(*T.sectionFromNode(n))
      else:
        rep = ''
      isText = False
      if nType == 'half_verse':
        rep += F.label.v(n)
      rep = mdEsc(htmlEsc(rep))
      rep = hlRep(app, rep, n, d.highlights)
      if nType in VERSE:
        if isLinked:
          rep = app.webLink(n, text=rep, className='vn', _asString=True)
        else:
          rep = f'<span class="vn">{rep}</span>'
        rep += hlText(app, L.d(n, otype="word"), d.highlights, fmt=d.fmt)
        isText = True
    elif nType == 'lex':
      rep = mdEsc(htmlEsc(F.voc_lex_utf8.v(n)))
      rep = hlRep(app, rep, n, d.highlights)
    else:
      rep = hlText(app, L.d(n, otype='word'), d.highlights, fmt=d.fmt)

    if isLinked and nType not in VERSE:
      rep = app.webLink(n, text=rep, _asString=True)

    tClass = display.formatClass[d.fmt].lower() if isText else 'trb'
    rep = f'<span class="{tClass}">{rep}</span>'
    result += f'{rep}{nodeRep}'

    if _asString or _asApp:
      return result
    dm((result))

  def _pretty(
      app,
      n,
      outer,
      html,
      firstSlot,
      lastSlot,
      **options,
  ):
    display = app.display
    d = display.get(options)

    goOn = prettyPre(
        app,
        n,
        firstSlot,
        lastSlot,
        d.withNodes,
        d.highlights,
    )
    if not goOn:
      return
    (
        slotType,
        nType,
        className,
        boundaryClass,
        hlAtt,
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
    if d.condenseType is not None and otypeRank[nType] > otypeRank[d.condenseType]:
      bigType = True

    if nType == 'book':
      html.append(app.webLink(n, _asString=True))
      return
    if nType == 'chapter':
      html.append(app.webLink(n, _asString=True))
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

    (hlClass, hlStyle) = hlAtt

    superType = ATOMS.get(nType, None)
    if superType:
      (superNode, superStart, superEnd) = app._getSuper(n, superType)
      if superStart < myStart:
        boundaryClass += ' r'
      if superEnd > myEnd:
        boundaryClass += ' l'
      nodePart = (f'<a href="#" class="nd">{superNode}</a>' if d.withNodes else '')
      (shlClass, shlStyle) = getHlAtt(app, superNode, d.highlights)
      if shlClass:
        if not hlClass:
          hlClass = shlClass
        if not hlStyle:
          hlStyle = shlStyle

    doOuter = outer and nType in {slotType, 'lex'}
    if doOuter:
      html.append('<div class="outeritem">')

    html.append(
        f'<div class="{className} {boundaryClass} {hlClass}" {hlStyle}>')

    if nType in {'verse', 'half_verse'}:
      passage = app.webLink(n, _asString=True)
      html.append(
          f'''
    <div class="vl">
        <div class="vrs">{passage}</div>
        {nodePart}
    </div>
'''
      )
    elif superType:
      typePart = app.webLink(superNode, text=superType, _asString=True)
      featurePart = ''
      if superType == 'sentence':
        featurePart = getFeatures(
            app,
            superNode,
            ('number', ),
            o=n,
            plain=True,
            **options,
        )
      elif superType == 'clause':
        featurePart = getFeatures(
            app,
            superNode,
            ('rela', 'typ'),
            o=n,
            plain=True,
            **options,
        )
      elif superType == 'phrase':
        featurePart = getFeatures(
            app,
            superNode,
            ('function', 'typ'),
            o=n,
            plain=True,
            **options,
        )
      html.append(
          f'''
    <div class="{superType.lower()} {shlClass}" {shlStyle}>
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
        lexLink = (app.webLink(lx, text=htmlEsc(T.text([n], fmt=d.fmt)), _asString=True))
        tClass = 'h' if d.fmt is None or '-orig-' in d.fmt else 'tr'
        heading = f'<div class="{tClass}">{lexLink}</div>'
        featurePart = getFeatures(
            app,
            n,
            ('pdp', 'gloss', 'vs', 'vt'),
            givenValue=dict(
                pdp=app.webLink(n, text=htmlEsc(F.pdp.v(n)), _asString=True),
                gloss=htmlEsc(F.gloss.v(lx)),
            ),
            **options,
        )
      elif nType == 'lex':
        extremeOccs = getBoundary(api, n)
        linkOccs = ' - '.join(app.webLink(lo, _asString=True) for lo in extremeOccs)
        heading = f'<div class="h">{htmlEsc(F.voc_lex_utf8.v(n))}</div>'
        occs = f'<div class="occs">{linkOccs}</div>'
        featurePart = getFeatures(
            app,
            n,
            ('voc_lex', 'gloss'),
            givenValue=dict(voc_lex=app.webLink(n, text=htmlEsc(F.voc_lex.v(n)), _asString=True)),
            **options,
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
          **options,
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
