import os

from tf.core.helpers import htmlEsc, mdEsc
from tf.applib.helpers import dm, dh
from tf.applib.display import prettyPre, getFeatures
from tf.applib.highlight import hlRep
from tf.applib.api import setupApi
from tf.applib.links import outLink
from tf.apps.uruk.atf import Atf
from tf.apps.uruk.image import wrapLink, URL_FORMAT, imageClass, getImages, getImagery

TEMP_DIR = '_temp'
REPORT_DIR = 'reports'

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


class TfApp(Atf):

  def __init__(app, *args, _asApp=False, lgc=False, check=False, silent=False, **kwargs):
    setupApi(app, *args, _asApp=_asApp, lgc=lgc, check=check, silent=silent, **kwargs)

    getImagery(app, lgc, check, silent)

    app.tempDir = f'{app.repoLocation}/{TEMP_DIR}'
    app.reportDir = f'{app.repoLocation}/{REPORT_DIR}'

    if not _asApp:
      for cdir in (app.tempDir, app.reportDir):
        os.makedirs(cdir, exist_ok=True)

  def webLink(app, n, text=None, className=None, _asString=False, _noUrl=False):
    api = app.api
    L = api.L
    F = api.F
    if type(n) is str:
      pNum = n
    else:
      refNode = n if F.otype.v(n) == 'tablet' else L.u(n, otype='tablet')[0]
      pNum = F.catalogId.v(refNode)

    title = None if _noUrl else ('to CDLI main page for this tablet')
    linkText = pNum if text is None else text
    url = '#' if _noUrl else URL_FORMAT['tablet']['main'].format(pNum)
    target = '' if _noUrl else None

    result = outLink(
        linkText,
        url,
        title=title,
        className=className,
        target=target,
        passage=pNum,
    )
    if _asString:
      return result
    dh(result)

  def cdli(app, n, linkText=None, asString=False):
    (nType, objectType, identifier) = imageClass(app, n)
    if linkText is None:
      linkText = identifier
    result = wrapLink(linkText, objectType, 'main', identifier)
    if asString:
      return result
    else:
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
    F = api.F

    nType = F.otype.v(n)
    result = passage
    if _asApp:
      nodeRep = f' <a href="#" class="nd">{n}</a> ' if d.withNodes else ''
    else:
      nodeRep = f' *{n}* ' if d.withNodes else ''

    if nType in ATF_TYPES:
      isSign = nType == 'sign'
      isQuad = nType == 'quad'
      rep = (
          app.atfFromSign(n) if isSign else app.atfFromQuad(n) if isQuad else app.atfFromCluster(n)
      )
      rep = hlRep(app, rep, n, d.highlights)
      if isLinked:
        rep = app.webLink(n, text=rep, _asString=True)
      theLineart = ''
      if d.lineart:
        if isSign or isQuad:
          width = '2em' if isSign else '4em'
          height = '4em' if isSign else '6em'
          theLineart = getImages(
              app,
              n, kind='lineart', width=width, height=height, _asString=True, withCaption=False,
              warning=False
          )
          theLineart = f' {theLineart}'
      result = (f'{rep}{nodeRep}{theLineart}') if theLineart else f'{rep}{nodeRep}'
    elif nType == 'comment':
      rep = mdEsc(F.type.v(n))
      rep = hlRep(app, rep, n, d.highlights)
      if isLinked:
        rep = app.webLink(n, text=rep, _asString=True)
      result = f'{rep}{nodeRep}: {mdEsc(F.text.v(n))}'
    else:
      lineNumbersCondition = d.lineNumbers
      if nType == 'line' or nType == 'case':
        src = F.srcLn.v(n) or ''
        rep = (
            src
            if src else (
                mdEsc(f'{nType} {F.number.v(n)}')
                if secLabel or nType == 'case' else
                ''
            )
        )
        lineNumbersCondition = d.lineNumbers and F.terminal.v(n)
      elif nType == 'column':
        rep = mdEsc(f'{nType} {F.number.v(n)}') if secLabel else ''
      elif nType == 'face':
        rep = mdEsc(f'{nType} {F.type.v(n)}')
      elif nType == 'tablet':
        rep = mdEsc(f'{nType} {F.catalogId.v(n)}') if secLabel else ''
      rep = hlRep(app, rep, n, d.highlights)
      result = app._addLink(
          n,
          rep,
          nodeRep,
          isLinked=isLinked,
          lineNumbers=lineNumbersCondition,
      )

    if _asString or _asApp:
      return result
    dm(result)

  def _addLink(app, n, rep, nodeRep, isLinked=True, lineNumbers=True):
    F = app.api.F
    if isLinked:
      rep = app.webLink(n, text=rep, _asString=True)
    theLine = ''
    if lineNumbers:
      theLine = mdEsc(f' @{F.srcLnNum.v(n)} ')
    return f'{rep}{nodeRep}{theLine}'

  def _pretty(
      app,
      n,
      outer,
      html,
      firstSlot,
      lastSlot,
      seen=set(),
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
    E = api.E
    sortNodes = api.sortNodes
    otypeRank = api.otypeRank

    bigType = False
    if d.condenseType is not None and otypeRank[nType] > otypeRank[d.condenseType]:
      bigType = True

    if outer:
      seen = set()

    (hlClass, hlStyle) = hlAtt

    heading = ''
    featurePart = ''
    commentsPart = app._getComments(
        n,
        firstSlot,
        lastSlot,
        seen,
        **options,
    ) if nType in COMMENT_TYPES else ''
    children = ()

    if bigType:
      children = ()
    elif nType == 'tablet':
      children = L.d(n, otype='face')
    elif nType == 'face':
      children = L.d(n, otype='column')
    elif nType == 'column':
      children = L.d(n, otype='line')
    elif nType == 'line' or nType == 'case':
      if F.terminal.v(n):
        children = sortNodes(
            set(L.d(n, otype='cluster'))
            | set(L.d(n, otype='quad'))
            | set(L.d(n, otype='sign'))
        )
      else:
        children = E.sub.f(n)
    elif nType == 'cluster':
      children = sortNodes(
          set(L.d(n, otype='cluster'))
          | set(L.d(n, otype='quad'))
          | set(L.d(n, otype='sign'))
      )
    elif nType == 'quad':
      children = E.sub.f(n)

    if nType == 'tablet':
      heading = htmlEsc(F.catalogId.v(n))
      heading += ' '
      heading += getFeatures(
          app,
          n,
          ('name', 'period', 'excavation'),
          plain=True,
          **options,
      )
    elif nType == 'face':
      heading = htmlEsc(F.type.v(n))
      featurePart = getFeatures(
          app,
          n,
          ('identifier', 'fragment'),
          **options,
      )
    elif nType == 'column':
      heading = htmlEsc(F.number.v(n))
      if F.prime.v(n):
        heading += "'"
    elif nType == 'line' or nType == 'case':
      heading = htmlEsc(F.number.v(n))
      if F.prime.v(n):
        heading += "'"
      if F.terminal.v(n):
        className = 'trminal'
        theseFeats = ('srcLnNum', ) if d.lineNumbers else ()
        featurePart = getFeatures(
            app,
            n,
            theseFeats,
            **options,
        )
    elif nType == 'comment':
      heading = htmlEsc(F.type.v(n))
      featurePart = getFeatures(
          app,
          n,
          ('text', ),
          **options,
      )
    elif nType == 'cluster':
      seen.add(n)
      heading = htmlEsc(CLUSTER_TYPES.get(F.type.v(n), ''))
    elif nType == 'quad':
      seen.add(n)
    elif nType == slotType:
      featurePart = app._getAtf(n) + getFeatures(app, n, (), **options)
      seen.add(n)
      if not outer and F.type.v(n) == 'empty':
        return

    if outer:
      typePart = app.webLink(n, text=f'{nType} {heading}', _asString=True)
    else:
      typePart = heading

    isCluster = nType == 'cluster'
    extra = 'b' if isCluster else ''
    label = f'''
    <div class="lbl {className}{extra}">
        {typePart}
        {nodePart}
    </div>
''' if typePart or nodePart else ''

    if isCluster:
      if outer:
        html.append(f'<div class="contnr {className} {hlClass}" {hlStyle}>')
      html.append(label)
      if outer:
        html.append(f'<div class="children {className}">')
    else:
      html.append(
          f'''
<div class="contnr {className} {hlClass}" {hlStyle}>
    {label}
    <div class="meta">
        {featurePart}
        {commentsPart}
    </div>
'''
      )
    if d.lineart:
      isQuad = nType == 'quad'
      isSign = nType == 'sign'
      if isQuad or isSign:
        isOuter = outer or (all(F.otype.v(parent) != 'quad' for parent in E.sub.t(n)))
        if isOuter:
          width = '2em' if isSign else '4em'
          height = '4em' if isSign else '6em'
          theLineart = getImages(
              app,
              n, kind='lineart', width=width, height=height, _asString=True, withCaption=False,
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
        app._pretty(
            ch,
            False,
            html,
            firstSlot,
            lastSlot,
            seen=seen,
            **options,
        )
        if nType == 'quad':
          nextChildren = E.op.f(ch)
          if nextChildren:
            op = nextChildren[0][1]
            html.append(f'<div class="op">{op}</div>')
    if isCluster:
      html.append(
          f'''
    <div class="lbl {className}e {hlClass}" {hlStyle}>
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

  def lineart(app, ns, key=None, asLink=False, withCaption=None, **options):
    return getImages(
        app,
        ns, kind='lineart', key=key, asLink=asLink, withCaption=withCaption, **options
    )

  def photo(app, ns, key=None, asLink=False, withCaption=None, **options):
    return getImages(
        app,
        ns, kind='photo', key=key, asLink=asLink, withCaption=withCaption, **options
    )

  def imagery(app, objectType, kind):
    return set(app._imagery.get(objectType, {}).get(kind, {}))

  def _getComments(
      app,
      n,
      firstSlot,
      lastSlot,
      seen,
      **options,
  ):
    display = app.display

    api = app.api
    E = api.E
    cns = E.comments.f(n)
    if len(cns):
      html = ['<div class="comments">']
      for c in cns:
        app._pretty(
            c,
            False,
            html,
            firstSlot,
            lastSlot,
            condenseType=None,
            lineart=False,
            seen=seen,
            **display.consume(options, 'lineart', 'condenseType')
        )
      html.append('</div>')
      commentsPart = ''.join(html)
    else:
      commentsPart = ''
    return commentsPart

  def _getAtf(app, n):
    atf = app.atfFromSign(n, flags=True)
    featurePart = f' <span class="srcln">{atf}</span>'
    return featurePart
