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

PLAIN_LINK = ('https://github.com/{org}/{repo}/blob/master' '/source/{version}/{book}')

SECTION = {'book', 'chapter', 'verse'}
VERSE = {'verse'}


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

    (bookE, chapter, verse) = T.sectionFromNode(n)
    bookNode = n if nType == 'book' else L.u(n, otype='book')[0]
    book = F.book.v(bookNode)
    passageText = (
        bookE if nType == 'book' else
        f'{bookE} {chapter}' if nType == 'chapter' else f'{bookE} {chapter}:{verse}'
    )
    href = '#' if noUrl else PLAIN_LINK.format(
        org=app.org,
        repo=app.repo,
        version=version,
        book=book,
    )
    if text is None:
      text = passageText
      title = 'show this passage in the Peshitta source'
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
      rep = mdEsc(htmlEsc(rep))
      if nType in VERSE:
        if linked:
          rep = app.webLink(n, text=rep, className='vn', asString=True)
        else:
          rep = f'<span class="vn">{rep}</span>'
        rep += mdEsc(htmlEsc(T.text(L.d(n, otype="word"), fmt=fmt)))
        isText = True
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
      fmt=None,
      condenseType=None,
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
    L = api.L
    T = api.T
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
    elif nType == 'verse':
      (thisFirstSlot, thisLastSlot) = getBoundary(api, n)
      children = L.d(n, otype='word')
    elif nType == slotType:
      children = ()

    doOuter = outer and nType == slotType
    if doOuter:
      html.append('<div class="outeritem">')

    html.append(f'<div class="{className} {boundaryClass}{hlClass}"{hlStyle}>')

    if nType == 'verse':
      passage = app.webLink(n, asString=True)
      html.append(
          f'''
    <div class="vl">
        <div class="vrs">{passage}</div>
        {nodePart}
    </div>
'''
      )
    else:
      if nodePart:
        html.append(nodePart)

      heading = ''
      featurePart = ''
      occs = ''
      if nType == slotType:
        text = htmlEsc(T.text([n], fmt=fmt))
        tClass = 'sy' if fmt is None or '-orig-' in fmt else 'tr'
        heading = f'<div class="{tClass}">{text}</div>'
        featurePart = getFeatures(
            app,
            n,
            suppress,
            ('word_etcbc', ),
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
    html.append('''
</div>
''')
    if doOuter:
      html.append('</div>')
