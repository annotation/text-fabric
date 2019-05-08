import os
import types

from ..parameters import URL_TFDOC, DOWNLOADS
from ..core.helpers import mdEsc, htmlEsc, flattenToSet
from .app import findAppConfig
from .helpers import configure, RESULT, dh
from .links import outLink
from .condense import condense, condenseSet
from .highlight import getTupleHighlights, getHlAtt

LIMIT_SHOW = 100
LIMIT_TABLE = 2000

FONT_BASE = 'https://github.com/annotation/text-fabric/blob/master/tf/server/static/fonts'

CSS_FONT = '''
    <link rel="stylesheet" href="/server/static/fonts.css"/>
'''

CSS_FONT_API = f'''
@font-face {{{{
  font-family: "{{fontName}}";
  src:
    local("{{font}}"),
    url("{FONT_BASE}/{{fontw}}?raw=true");
}}}}
'''


def displayApi(app, silent, hoist):
  app.export = types.MethodType(export, app)
  app.table = types.MethodType(table, app)
  app.plainTuple = types.MethodType(plainTuple, app)
  app.plain = types.MethodType(plain, app)
  app.show = types.MethodType(show, app)
  app.prettyTuple = types.MethodType(prettyTuple, app)
  app.pretty = types.MethodType(pretty, app)
  app.loadCss = types.MethodType(loadCss, app)

  api = app.api

  app.classNames = (
      {nType[0]: nType[0] for nType in api.C.levels.data}
      if app.classNames is None else
      app.classNames
  )

  if not app._asApp:
    app.loadCss()
    if hoist:
      docs = api.makeAvailableIn(hoist)
      if not silent:
        dh(
            '<details open><summary><b>API members</b>:</summary>\n' + '<br/>\n'.join(
                ', '.join(
                    outLink(
                        entry,
                        f'{URL_TFDOC}/Api/{head}/#{ref}',
                        title='doc',
                    ) for entry in entries
                ) for (head, ref, entries) in docs
            ) + '</details>'
        )


def export(
    app,
    tuples,
    toDir=None,
    toFile='results.tsv',
    **options,
):
  display = app.display
  if not display.check('table', options):
    return ''
  d = display.get(options)

  if toDir is None:
    toDir = os.path.expanduser(DOWNLOADS)
    if not os.path.exists(toDir):
      os.makedirs(toDir, exist_ok=True)
  toPath = f'{toDir}/{toFile}'

  resultsX = getResultsX(
      app,
      tuples,
      d.tupleFeatures,
      d.condenseType or app.condenseType,
      app.noDescendTypes,
      fmt=d.fmt,
  )

  with open(toPath, 'w', encoding='utf_16_le') as fh:
    fh.write(
        '\ufeff' + ''.join(
            ('\t'.join('' if t is None else str(t) for t in tup) + '\n')
            for tup in resultsX
        )
    )


def table(
    app,
    tuples,
    _asString=False,
    **options,
):
  display = app.display
  if not display.check('table', options):
    return ''
  d = display.get(options)

  api = app.api
  F = api.F

  item = d.condenseType if d.condensed else RESULT

  if d.condensed:
    tuples = condense(api, tuples, d.condenseType, multiple=True)

  passageHead = '</th><th class="tf">p' if d.withPassage else ''

  html = []
  one = True
  for (i, tup) in _tupleEnum(tuples, d.start, d.end, LIMIT_TABLE, item):
    if one:
      heads = '</th><th>'.join(F.otype.v(n) for n in tup)
      html.append(
          f'''
<tr class="tf">
  <th class="tf">n{passageHead}</th>
  <th class="tf">{heads}</th>
</tr>
'''
      )
      one = False
    html.append(
        plainTuple(
            app,
            tup,
            i,
            item=item,
            position=None,
            opened=False,
            _asString=True,
            **options,
        )
    )
  html = '<table>' + '\n'.join(html) + '</table>'
  if _asString:
    return html
  dh(html)


def plainTuple(
    app,
    tup,
    seq,
    item=RESULT,
    position=None,
    opened=False,
    _asString=False,
    **options,
):
  display = app.display
  if not display.check('plainTuple', options):
    return ''
  d = display.get(options)

  _asApp = app._asApp
  api = app.api
  F = api.F
  T = api.T

  if d.withPassage:
    passageNode = _getRefMember(app, tup, d.linked, d.condensed)
    passageRef = (
        '' if passageNode is None else
        app._sectionLink(passageNode)
        if _asApp else
        app.webLink(passageNode, _asString=True)
    )
    if passageRef:
      passageRef = f' {passageRef}'
  else:
    passageRef = ''

  newOptions = display.consume(options, 'withPassage')
  newOptionsH = display.consume(options, 'withPassage', 'highlights')

  highlights = (
      getTupleHighlights(api, tup, d.highlights, d.colorMap, d.condenseType)
  )

  if _asApp:
    prettyRep = prettyTuple(
        app,
        tup,
        seq,
        withPassage=False,
        **newOptions,
    ) if opened else ''

    current = ' focus' if seq == position else ''
    attOpen = ' open ' if opened else ''
    tupSeq = ','.join(str(n) for n in tup)
    if d.withPassage:
      sParts = T.sectionFromNode(passageNode, fillup=True)
      passageAtt = ' '.join(
          f'sec{i}="{sParts[i] if i < len(sParts) else ""}"'
          for i in range(3)
      )
    else:
      passageAtt = ''

    plainRep = ''.join(
        f'''<span>{mdEsc(app.plain(
                    n,
                    isLinked=i == d.linked - 1,
                    withPassage=False,
                    highlights=highlights,
                    **newOptionsH,
                  ))
                }
            </span>
        ''' for (i, n) in enumerate(tup)
    )
    html = (
        f'''
  <details
    class="pretty dtrow{current}"
    seq="{seq}"
    {attOpen}
  >
    <summary>
      <a href="#" class="pq fa fa-solar-panel fa-xs" title="show in context" {passageAtt}></a>
      <a href="#" class="sq" tup="{tupSeq}">{seq}</a>
      {passageRef}
      {plainRep}
    </summary>
    <div class="pretty">{prettyRep}</div>
  </details>
'''
    )
    return html

  html = [str(seq)]
  if passageRef:
    html.append(passageRef)
  for (i, n) in enumerate(tup):
    html.append(
        app.plain(
            n,
            isLinked=i == d.linked - 1,
            _asString=True,
            withPassage=False,
            highlights=highlights,
            **newOptionsH,
        )
    )
  html = '<tr class="tf"><td class="tf">' + ('</td><td class="tf">'.join(html)) + '</td></tr>'
  if _asString:
    return html
  head = [
      '<tr class="tf"><th class="tf">n</th><th class="tf">' +
      ('</th><th class="tf">'.join(F.otype.v(n) for n in tup)) +
      '</th></tr>'
  ]
  head.append(html)

  dh('\n'.join(head))


def plain(
    app,
    n,
    isLinked=True,
    _asString=False,
    secLabel=True,
    **options,
):
  display = app.display
  if not display.check('plain', options):
    return ''
  d = display.get(options)

  api = app.api
  F = api.F
  T = api.T
  sectionTypes = T.sectionTypes

  nType = F.otype.v(n)
  passage = ''

  if d.withPassage:
    if nType not in sectionTypes:
      passage = app.webLink(n, _asString=True)

  passage = f'{passage}&nbsp;' if passage else ''

  highlights = (
      {m: '' for m in d.highlights}
      if type(d.highlights) is set else
      d.highlights
  )

  return app._plain(
      n,
      passage,
      isLinked,
      _asString,
      secLabel,
      highlights=highlights,
      **display.consume(options, 'highlights'),
  )


def show(
    app,
    tuples,
    **options,
):
  display = app.display
  if not display.check('show', options):
    return ''
  d = display.get(options)

  api = app.api
  F = api.F

  item = d.condenseType if d.condensed else RESULT

  if d.condensed:
    rawHighlights = getTupleHighlights(
        api, tuples, d.highlights, d.colorMap, d.condenseType, multiple=True
    )
    highlights = {}
    colorMap = None
    tuples = condense(api, tuples, d.condenseType, multiple=True)
  else:
    highlights = d.highlights
    rawHighlights = None
    colorMap = d.colorMap

  for (i, tup) in _tupleEnum(tuples, d.start, d.end, LIMIT_SHOW, item):
    item = F.otype.v(tup[0]) if d.condensed and d.condenseType else RESULT
    prettyTuple(
        app,
        tup,
        i,
        item=item,
        highlights=highlights,
        colorMap=colorMap,
        rawHighlights=rawHighlights,
        **display.consume(options, 'highlights', 'colorMap'),
    )


def prettyTuple(
    app,
    tup,
    seq,
    item=RESULT,
    rawHighlights=None,
    **options,
):
  display = app.display
  if not display.check('prettyTuple', options):
    return ''
  d = display.get(options)

  _asApp = app._asApp

  if len(tup) == 0:
    if _asApp:
      return ''
    else:
      return

  api = app.api
  sortKey = api.sortKey

  containers = {tup[0]} if d.condensed else condenseSet(api, tup, d.condenseType)
  highlights = (
      getTupleHighlights(api, tup, d.highlights, d.colorMap, d.condenseType)
      if rawHighlights is None else rawHighlights
  )

  if not _asApp:
    dh(f'<p><b>{item}</b> <i>{seq}</i></p>')
  if _asApp:
    html = []
  for t in sorted(containers, key=sortKey):
    h = app.pretty(
        t,
        highlights=highlights,
        **display.consume(options, 'highlights'),
    )
    if _asApp:
      html.append(h)
  if _asApp:
    return '\n'.join(html)


def pretty(
    app,
    n,
    **options,
):
  display = app.display
  if not display.check('pretty', options):
    return ''
  d = display.get(options)

  _asApp = app._asApp
  api = app.api
  F = api.F
  L = api.L
  T = api.T
  otypeRank = api.otypeRank
  sectionTypes = T.sectionTypes

  containerN = None

  nType = F.otype.v(n)
  if d.condensed and d.condenseType:
    if nType == d.condenseType:
      containerN = n
    elif otypeRank[nType] < otypeRank[d.condenseType]:
      ups = L.u(n, otype=d.condenseType)
      if ups:
        containerN = ups[0]

  (firstSlot, lastSlot) = (
      getBoundary(api, n) if not d.condensed or not d.condenseType else
      (None, None) if containerN is None else getBoundary(api, containerN)
  )

  html = []

  if d.withPassage:
    if nType not in sectionTypes:
      html.append(app.webLink(n, _asString=True))

  highlights = (
      {m: '' for m in d.highlights}
      if type(d.highlights) is set else
      d.highlights
  )

  extraFeatures = sorted(flattenToSet(d.extraFeatures) | flattenToSet(d.tupleFeatures))

  app._pretty(
      n,
      True,
      html,
      firstSlot,
      lastSlot,
      extraFeatures=extraFeatures,
      highlights=highlights,
      **display.consume(options, 'extraFeatures', 'highlights'),
  )
  htmlStr = '\n'.join(html)
  if _asApp:
    return htmlStr
  dh(htmlStr)


def prettyPre(
    app,
    n,
    firstSlot,
    lastSlot,
    withNodes,
    highlights,
):
  api = app.api
  F = api.F

  slotType = F.otype.slotType
  nType = F.otype.v(n)
  boundaryClass = ''
  myStart = None
  myEnd = None

  (myStart, myEnd) = getBoundary(api, n)

  if firstSlot is not None:
    if myEnd < firstSlot:
      return False
    if myStart < firstSlot:
      boundaryClass += ' rno'
  if lastSlot is not None:
    if myStart > lastSlot:
      return False
    if myEnd > lastSlot:
      boundaryClass += ' lno'

  hlAtt = getHlAtt(app, n, highlights)

  nodePart = (f'<a href="#" class="nd">{n}</a>' if withNodes else '')
  className = app.classNames.get(nType, None)

  return (
      slotType,
      nType,
      className.lower() if className else className,
      boundaryClass.lower() if boundaryClass else boundaryClass,
      hlAtt,
      nodePart,
      myStart,
      myEnd,
  )


# COMPOSE TABLES FOR CSV EXPORT

def getResultsX(app, results, features, condenseType, noDescendTypes, fmt=None):
  api = app.api
  F = api.F
  Fs = api.Fs
  T = api.T
  otypeRank = api.otypeRank
  sectionTypes = set(T.sectionTypes)
  sectionDepth = len(sectionTypes)
  if len(results) == 0:
    return ()
  firstResult = results[0]
  nTuple = len(firstResult)
  refColumns = [i for (i, n) in enumerate(firstResult) if F.otype.v(n) not in sectionTypes]
  refColumn = refColumns[0] if refColumns else nTuple - 1
  header = ['R'] + [f'S{i}' for i in range(1, sectionDepth + 1)]
  emptyA = []

  featureDict = {i: tuple(f.split()) if type(f) is str else f for (i, f) in features}

  def withText(nodeType):
    return (
        condenseType is None and nodeType not in sectionTypes
        or
        otypeRank[nodeType] <= otypeRank[condenseType]
    )

  for j in range(nTuple):
    i = j + 1
    n = firstResult[j]
    nType = F.otype.v(n)
    header.extend([f'NODE{i}', f'TYPE{i}'])
    if withText(nType):
      header.append(f'TEXT{i}')
    header.extend(f'{feature}{i}' for feature in featureDict.get(j, emptyA))
  rows = [tuple(header)]
  for (rm, r) in enumerate(results):
    rn = rm + 1
    row = [rn]
    refN = r[refColumn]
    sParts = T.sectionFromNode(refN)
    nParts = len(sParts)
    section = sParts + ((None, ) * (sectionDepth - nParts))
    row.extend(section)
    for j in range(nTuple):
      n = r[j]
      nType = F.otype.v(n)
      row.extend((n, nType))
      if withText(nType):
        text = T.text(n, fmt=fmt, descend=nType not in noDescendTypes)
        row.append(text)
      row.extend(Fs(feature).v(n) for feature in featureDict.get(j, emptyA))
    rows.append(tuple(row))
  return tuple(rows)


def getBoundary(api, n):
  F = api.F
  slotType = F.otype.slotType
  if F.otype.v(n) == slotType:
    return (n, n)
  E = api.E
  maxSlot = F.otype.maxSlot
  slots = E.oslots.data[n - maxSlot - 1]
  return (slots[0], slots[-1])


def getFeatures(
    app,
    n,
    features,
    withName=None,
    o=None,
    givenValue={},
    plain=False,
    **options,
):
  display = app.display
  d = display.get(options)

  api = app.api
  Fs = api.Fs

  featurePartB = '<div class="features">'
  featurePartE = '</div>'

  givenFeatureSet = set(features)
  xFeatures = tuple(f for f in d.extraFeatures if f not in givenFeatureSet)
  extraSet = set(xFeatures)
  featureList = tuple(features) + xFeatures
  nFeatures = len(features)

  showWithName = extraSet

  if not plain:
    featurePart = featurePartB
    hasB = True
  else:
    featurePart = ''
    hasB = False
  for (i, name) in enumerate(featureList):
    if name not in d.suppress:
      if name in givenValue:
        value = givenValue[name]
      else:
        if Fs(name) is None:
          continue
        value = Fs(name).v(n)
        oValue = None if o is None else Fs(name).v(o)
        valueRep = None if value in d.noneValues else htmlEsc(value)
        oValueRep = None if o is None or oValue in d.noneValues else htmlEsc(oValue)
        if valueRep is None and oValueRep is None:
          value = None
        else:
          sep = '' if valueRep is None or oValueRep is None else '|'
          valueRep = '' if valueRep is None else valueRep
          oValueRep = '' if oValueRep is None else oValueRep
          value = valueRep if valueRep == oValueRep else f'{valueRep}{sep}{oValueRep}'
      if value is not None:
        value = value.replace('\n', '<br/>')
        showName = withName or (withName is None and name in showWithName)
        nameRep = f'<span class="f">{name}=</span>' if showName else ''
        xClass = ' xft' if name in extraSet else ''
        featureRep = f' <span class="{name.lower()}{xClass}">{nameRep}{value}</span>'

        if i >= nFeatures:
          if not hasB:
            featurePart += featurePartB
            hasB = True
        featurePart += featureRep
  if hasB:
    featurePart += featurePartE
  return featurePart


def loadCss(app, reload=False):
  '''
  The CSS is looked up and then loaded into a notebook if we are not
  running in the TF browser,
  else the CSS is returned.

  With reload=True, the app-specific display.css will be read again from disk
  '''
  _asApp = app._asApp
  if _asApp:
    return app.css

  if reload:
    config = findAppConfig(app.appName, app.appPath)
    cfg = configure(config, app.version)
    app.css = cfg['css']

  hlCssFile = (
      f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}'
      '/server/static/highlight.css'
  )
  with open(hlCssFile) as fh:
    hlCss = fh.read()

  cssFont = (
      '' if app.fontName is None else CSS_FONT_API.format(
          fontName=app.fontName,
          font=app.font,
          fontw=app.fontw,
      )
  )
  tableCss = '''
tr.tf, td.tf, th.tf {
  text-align: left;
}

'''
  dh(f'<style>{cssFont + app.css + tableCss + hlCss}</style>')


def _getRefMember(app, tup, linked, condensed):
  api = app.api
  T = api.T
  sectionTypes = T.sectionTypes

  ln = len(tup)
  return (
      None
      if not tup or any(n in sectionTypes for n in tup) else
      tup[0] if condensed else
      tup[min((linked, ln - 1))] if linked else
      tup[0]
  )


def _tupleEnum(tuples, start, end, limit, item):
  if start is None:
    start = 1
  i = -1
  if not hasattr(tuples, '__len__'):
    if end is None or end - start + 1 > limit:
      end = start - 1 + limit
    for tup in tuples:
      i += 1
      if i < start - 1:
        continue
      if i >= end:
        break
      yield (i + 1, tup)
  else:
    if end is None or end > len(tuples):
      end = len(tuples)
    rest = 0
    if end - (start - 1) > limit:
      rest = end - (start - 1) - limit
      end = start - 1 + limit
    for i in range(start - 1, end):
      yield (i + 1, tuples[i])
    if rest:
      dh(
          f'<b>{rest} more {item}s skipped</b> because we show a maximum of'
          f' {limit} {item}s at a time'
      )
