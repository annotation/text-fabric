from IPython.display import display, Markdown, HTML

from .helpers import console, RESULT

LIMIT_SHOW = 100
LIMIT_TABLE = 2000

FONT_BASE = 'https://github.com/Dans-labs/text-fabric/blob/master/tf/server/static/fonts'

CSS_FONT = '''
    <link rel="stylesheet" href="/server/static/fonts.css"/>
'''

CSS_FONT_API = f'''
<style>
@font-face {{{{
  font-family: "{{fontName}}";
  src: url('{FONT_BASE}/{{font}}?raw=true');
  src: url('{FONT_BASE}/{{fontw}}?raw=true') format('woff');
}}}}
</style>
'''


def search(app, query, silent=False, sets=None, shallow=False, sort=True):
  api = app.api
  info = api.info
  S = api.S
  sortKeyTuple = api.sortKeyTuple

  results = S.search(query, sets=sets, shallow=shallow)
  if not shallow:
    if not sort:
      results = list(results)
    elif sort is True:
      results = sorted(results, key=sortKeyTuple)
    else:
      try:
        sortedResults = sorted(results, key=sort)
      except Exception as e:
        console(
            (
                'WARNING: your sort key function caused an error\n'
                f'{str(e)}'
                '\nYou get unsorted results'
            ),
            error=True
        )
        sortedResults = list(results)
      results = sortedResults

  nResults = len(results)
  plural = '' if nResults == 1 else 's'
  if not silent:
    info(f'{nResults} result{plural}')
  return results


def runSearch(app, query, cache):
  api = app.api
  S = api.S
  plainSearch = S.search

  cacheKey = (query, False)
  if cacheKey in cache:
    return cache[cacheKey]
  options = dict(msgCache=[])
  if app.sets is not None:
    options['sets'] = app.sets
  (queryResults, messages, exe) = plainSearch(query, here=False, **options)
  features = ()
  if exe:
    qnodes = getattr(exe, 'qnodes', [])
    features = tuple((i, tuple(sorted(q[1].keys()))) for (i, q) in enumerate(qnodes))
  queryResults = tuple(sorted(queryResults))
  cache[cacheKey] = (queryResults, messages, features)
  return (queryResults, messages, features)


def runSearchCondensed(app, query, cache, condenseType):
  api = app.api
  cacheKey = (query, True, condenseType)
  if cacheKey in cache:
    return cache[cacheKey]
  (queryResults, messages, features) = runSearch(app, query, cache)
  queryResults = _condense(api, queryResults, condenseType, multiple=True)
  cache[cacheKey] = (queryResults, messages, features)
  return (queryResults, messages, features)


def getPassageHighlights(app, node, query, cache, cacheSlots):
  if not query:
    return (set(), set(), set(), set())
  cacheSlotsKey = (query, node)
  if cacheSlotsKey in cacheSlots:
    return cacheSlots[cacheSlotsKey]

  hlNodes = getHlNodes(app, node, query, cache)
  cacheSlots[cacheSlotsKey] = hlNodes
  return hlNodes


def getHlNodes(app, node, query, cache):
  (queryResults, messages, features) = runSearch(app, query, cache)
  if messages:
    return (set(), set(), set(), set())

  api = app.api
  E = api.E
  F = api.F
  maxSlot = F.otype.maxSlot
  eoslots = E.oslots.data

  nodeSlots = eoslots[node - maxSlot - 1]
  first = nodeSlots[0]
  last = nodeSlots[-1]

  (sec2s, nodes, plainSlots, prettySlots) = nodesFromTuples(app, first, last, queryResults)
  return (sec2s, nodes, plainSlots, prettySlots)


def nodesFromTuples(app, first, last, results):
  api = app.api
  E = api.E
  F = api.F
  T = api.T
  L = api.L
  maxSlot = F.otype.maxSlot
  slotType = F.otype.slotType
  eoslots = E.oslots.data
  sectionTypes = T.sectionTypes
  sec2Type = sectionTypes[2]

  sec2s = set()
  nodes = set()
  plainSlots = set()
  prettySlots = set()

  for tup in results:
    for n in tup:
      nType = F.otype.v(n)

      if nType == slotType:
        if first <= n <= last:
          plainSlots.add(n)
          prettySlots.add(n)
      elif nType == sec2Type:
        sec2s.add(n)
      elif nType != sectionTypes[0] and nType != sectionTypes[1]:
        mySlots = eoslots[n - maxSlot - 1]
        myFirst = mySlots[0]
        myLast = mySlots[-1]
        if first <= myFirst <= last or first <= myLast <= last:
          nodes.add(n)
          for s in mySlots:
            if first <= s <= last:
              plainSlots.add(s)
  for s in plainSlots:
    sec2s.add(L.u(s, otype=sec2Type)[0])

  return (sec2s, nodes, plainSlots, prettySlots)


def composeP(
    app,
    features,
    items,
    opened,
    sec2,
    highlights,
    getx=None,
    **options,
):
  display = app.display

  api = app.api
  T = api.T

  if features:
    api.ensureLoaded(features)
    features = features.split()
  else:
    features = []

  (hlSec2s, hlNodes, hlPlainSlots, hlPrettySlots) = (
      highlights if highlights else
      (set(), set(), set(), set())
  )

  if getx is not None:
    tup = None
    for s2 in items:
      i = T.sectionFromNode(s2)[2]
      if i == getx:
        tup = (s2, )
        break
    return prettyTuple(
        app,
        tup,
        getx,
        condensed=False,
        extraFeatures=features,
        highlights=hlNodes | hlPrettySlots,
        **display.consume(options, 'condensed', 'extraFeatures', 'highlights')
    ) if tup is not None else ''

  passageHtml = []

  for item in items:
    passageHtml.append(
        plainTextS2(
            app,
            item,
            opened,
            sec2,
            highlights,
            extraFeatures=features,
            **display.consume(options, 'extraFeatures')
        )
    )

  return '\n'.join(passageHtml)


def composeT(
    app,
    features,
    tuples,
    opened,
    getx=None,
    **options,
):
  display = app.display

  api = app.api
  F = api.F

  if features:
    api.ensureLoaded(features)
    features = features.split()
  else:
    features = []

  if getx is not None:
    tup = None
    for (i, tp) in tuples:
      if i == getx:
        tup = tp
        break
    return prettyTuple(
        app,
        tup,
        getx,
        condensed=False,
        extraFeatures=features,
        **display.consume(options, 'condensed', 'extraFeatures')
    ) if tup is not None else ''

  tuplesHtml = []
  doHeader = False
  for (i, tup) in tuples:
    if i is None:
      if tup == 'results':
        doHeader = True
      else:
        tuplesHtml.append(
            f'''
<div class="dtheadrow">
  <span>n</span><span>{tup}</span>
</div>
'''
        )
      continue

    if doHeader:
      doHeader = False
      tuplesHtml.append(
          f'''
<div class="dtheadrow">
  <span>n</span><span>{"</span><span>".join(F.otype.v(n) for n in tup)}</span>
</div>
'''
      )
    tuplesHtml.append(
        plainTuple(
            app,
            tup,
            i,
            condensed=False,
            extraFeatures=features,
            opened=i in opened,
            asString=True,
            **display.consume(options, 'condensed', 'extraFeatures')
        )
    )

  return '\n'.join(tuplesHtml)


def compose(
    app,
    tuples,
    features,
    position,
    opened,
    getx=None,
    **options,
):
  display = app.display
  d = display.get(options)

  api = app.api
  F = api.F

  item = d.condenseType if d.condensed else RESULT

  if features:
    api.ensureLoaded(features)
    features = features.split()
  else:
    features = []

  if getx is not None:
    tup = None
    for (i, tp) in tuples:
      if i == getx:
        tup = tp
        break
    return prettyTuple(
        app,
        tup,
        getx,
        extraFeatures=features,
        **display.consume(options, 'extraFeatures')
    ) if tup is not None else ''

  tuplesHtml = []
  doHeader = False
  for (i, tup) in tuples:
    if i is None:
      if tup == 'results':
        doHeader = True
      else:
        tuplesHtml.append(
            f'''
<div class="dtheadrow">
  <span>n</span><span>{tup}</span>
</div>
'''
        )
      continue

    if doHeader:
      doHeader = False
      tuplesHtml.append(
          f'''
<div class="dtheadrow">
  <span>n</span><span>{"</span><span>".join(F.otype.v(n) for n in tup)}</span>
</div>
'''
      )
    tuplesHtml.append(
        plainTuple(
            app,
            tup,
            i,
            item=item,
            position=position,
            opened=i in opened,
            asString=True,
            extraFeatures=features,
            **display.consume(options, 'extraFeatures')
        )
    )

  return '\n'.join(tuplesHtml)


def table(
    app,
    tuples,
    asString=False,
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
    tuples = _condense(api, tuples, d.condenseType, multiple=True)

  passageHead = ' | p' if d.withPassage else ''

  markdown = []
  one = True
  for (i, tup) in _tupleEnum(tuples, d.start, d.end, LIMIT_TABLE, item):
    if one:
      nColumns = len(tup) + (1 if d.withPassage else 0)
      markdown.append(f'n{passageHead} | ' + (' | '.join(F.otype.v(n) for n in tup)))
      markdown.append(' | '.join('---' for n in range(nColumns + 1)))
      one = False
    markdown.append(
        plainTuple(
            app,
            tup,
            i,
            item=item,
            position=None,
            opened=False,
            asString=True,
            **options,
        )
    )
  markdown = '\n'.join(markdown)
  if asString:
    return markdown
  dm(markdown)


def plainTuple(
    app,
    tup,
    seqNumber,
    item=RESULT,
    position=None,
    opened=False,
    asString=False,
    **options,
):
  display = app.display
  if not display.check('plainTuple', options):
    return ''
  d = display.get(options)

  asApp = app.asApp
  api = app.api
  F = api.F
  T = api.T

  if d.withPassage:
    passageNode = getRefMember(app, tup, d.linked, d.condensed)
    passageRef = (
        '' if passageNode is None else
        app.sectionLink(passageNode)
        if asApp else
        app.webLink(passageNode, asString=True)
    )
    if passageRef:
      passageRef = f' {passageRef}'
  else:
    passageRef = ''

  newOptions = display.consume(options, 'withPassage')

  if asApp:
    prettyRep = prettyTuple(
        app,
        tup,
        seqNumber,
        withPassage=False,
        **newOptions,
    ) if opened else ''

    current = ' focus' if seqNumber == position else ''
    attOpen = ' open ' if opened else ''
    tupSeq = ','.join(str(n) for n in tup)
    if d.withPassage:
      sParts = T.sectionFromNode(passageNode, fillup=True)
      passageAtt = ' '.join(
          f'sec{i}="{sParts[i] if i < len(sParts) else ""}"' for i in range(3)
      )
    else:
      passageAtt = ''

    plainRep = ''.join(
        f'''<span>{mdEsc(app.plain(
                    n,
                    isLinked=i == d.linked - 1,
                    withPassage=False,
                    **newOptions,
                  ))
                }
            </span>
        ''' for (i, n) in enumerate(tup)
    )
    html = (
        f'''
  <details
    class="pretty dtrow{current}"
    seq="{seqNumber}"
    {attOpen}
  >
    <summary>
      <a href="#" class="pq fa fa-solar-panel fa-xs" title="show in context" {passageAtt}></a>
      <a href="#" class="sq" tup="{tupSeq}">{seqNumber}</a>
      {passageRef}
      {plainRep}
    </summary>
    <div class="pretty">{prettyRep}</div>
  </details>
'''
    )
    return html

  markdown = [str(seqNumber)]
  if passageRef:
    markdown.append(passageRef)
  for (i, n) in enumerate(tup):
    markdown.append(
        mdEsc(
            app.plain(
                n,
                isLinked=i == d.linked - 1,
                asString=True,
                withPassage=False,
                **newOptions,
            )
        )
    )
  markdown = '|'.join(markdown)
  if asString:
    return markdown
  head = ['n | ' + (' | '.join(F.otype.v(n) for n in tup))]
  head.append(' | '.join('---' for n in range(len(tup) + 1)))
  head.append(markdown)

  dm('\n'.join(head))


def plain(
    app,
    n,
    isLinked=True,
    asString=False,
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
      passage = app.webLink(n, asString=True)

  return app._plain(
      n,
      passage,
      isLinked,
      asString,
      **options,
  )


def plainTextS2(
    app,
    sNode,
    opened,
    sec2,
    highlights,
    **options,
):
  display = app.display
  d = display.get(options)

  api = app.api
  T = api.T
  seqNumber = T.sectionFromNode(sNode)[2]
  itemType = T.sectionTypes[2]
  isOpened = str(seqNumber) in opened
  tClass = '' if d.fmt is None else display.formatClass[d.fmt]

  (hlSec2s, hlNodes, hlPlainSlots, hlPrettySlots) = (
      highlights if highlights else
      (set(), set(), set(), set())
  )

  sec2Class = ' hl' if sNode in hlSec2s else ''

  prettyRep = prettyTuple(
      app,
      (sNode, ),
      seqNumber,
      condensed=False,
      condenseType=itemType,
      highlights=hlPrettySlots | hlNodes,
      **display.consume(options, 'condensed', 'condenseType'),
  ) if isOpened else ''
  current = ' focus' if str(seqNumber) == str(sec2) else ''
  attOpen = ' open ' if isOpened else ''

  textRep = T.text(sNode, fmt=d.fmt, descend=True, highlights=hlPlainSlots)
  html = (
      f'''
<details
  class="pretty{current}"
  seq="{seqNumber}"
  {attOpen}
>
  <summary class="{tClass}{sec2Class}">
    {app.sectionLink(sNode, text=seqNumber)}
    {textRep}
  </summary>
  <div class="pretty">{prettyRep}</div>
</details>
'''
  )
  return html


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
    rawHighlights = _getHighlights(
        api, tuples, d.highlights, d.colorMap, d.condenseType, multiple=True
    )
    highlights = {}
    colorMap = None
    tuples = _condense(api, tuples, d.condenseType, multiple=True)
  else:
    highlights = d.highlights
    rawHighlights = None
    colorMap = d.colorMap

  for (i, tup) in _tupleEnum(tuples, d.start, d.end, LIMIT_SHOW, item):
    item = F.otype.v(tup[0]) if d.condenseType else RESULT
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
    seqNumber,
    item='Result',
    rawHighlights=None,
    **options,
):
  display = app.display
  if not display.check('prettyTuple', options):
    return ''
  d = display.get(options)

  asApp = app.asApp

  if len(tup) == 0:
    if asApp:
      return ''
    else:
      return

  api = app.api
  sortKey = api.sortKey

  containers = {tup[0]} if d.condensed else _condenseSet(api, tup, d.condenseType)
  highlights = (
      _getHighlights(api, tup, d.highlights, d.colorMap, d.condenseType)
      if rawHighlights is None else rawHighlights
  )

  if not asApp:
    dm(f'''

**{item}** *{seqNumber}*

''')
  if asApp:
    html = []
  for t in sorted(containers, key=sortKey):
    h = app.pretty(
        t,
        highlights=highlights,
        **display.consume(options, 'highlights'),
    )
    if asApp:
      html.append(h)
  if asApp:
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

  asApp = app.asApp
  api = app.api
  F = api.F
  L = api.L
  T = api.T
  otypeRank = api.otypeRank
  sectionTypes = T.sectionTypes

  containerN = None

  nType = F.otype.v(n)
  if d.condenseType:
    if nType == d.condenseType:
      containerN = n
    elif otypeRank[nType] < otypeRank[d.condenseType]:
      ups = L.u(n, otype=d.condenseType)
      if ups:
        containerN = ups[0]

  (firstSlot, lastSlot) = (
      getBoundary(api, n) if d.condenseType is None else
      (None, None) if containerN is None else getBoundary(api, containerN)
  )

  html = []

  if d.withPassage:
    if nType not in sectionTypes:
      html.append(app.webLink(n, asString=True))

  highlights = (
      {m: '' for m in d.highlights}
      if type(d.highlights) is set else
      d.highlights
  )
  app._pretty(
      n,
      True,
      html,
      firstSlot,
      lastSlot,
      highlights=highlights,
      **display.consume(options, 'highlights'),
  )
  htmlStr = '\n'.join(html)
  if asApp:
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
      boundaryClass += ' R'
  if lastSlot is not None:
    if myStart > lastSlot:
      return False
    if myEnd > lastSlot:
      boundaryClass += ' L'

  hl = highlights.get(n, None)
  hlClass = ''
  hlStyle = ''
  if hl == '':
    hlClass = ' hl'
  else:
    hlStyle = f' style="background-color: {hl};"'

  nodePart = (f'<a href="#" class="nd">{n}</a>' if withNodes else '')
  className = app.classNames.get(nType, None)

  return (
      slotType,
      nType,
      className,
      boundaryClass,
      hlClass,
      hlStyle,
      nodePart,
      myStart,
      myEnd,
  )


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

  withName = set(xFeatures)

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
        nameRep = f'<span class="f">{name}=</span>' if name in withName else ''
        xClass = ' xft' if name in extraSet else ''
        featureRep = f' <span class="{name}{xClass}">{nameRep}{value}</span>'

        if i >= nFeatures:
          if not hasB:
            featurePart += featurePartB
            hasB = True
        featurePart += featureRep
  if hasB:
    featurePart += featurePartE
  return featurePart


def getResultsX(api, results, features, noDescendTypes, fmt=None):
  F = api.F
  Fs = api.Fs
  T = api.T
  sectionTypes = set(T.sectionTypes)
  if len(results) == 0:
    return ()
  firstResult = results[0]
  nTuple = len(firstResult)
  refColumns = [i for (i, n) in enumerate(firstResult) if F.otype.v(n) not in sectionTypes]
  refColumn = refColumns[0] if refColumns else nTuple - 1
  header = ['R', 'S1', 'S2', 'S3']
  emptyA = []

  featureDict = dict(features)

  for j in range(nTuple):
    i = j + 1
    n = firstResult[j]
    nType = F.otype.v(n)
    header.extend([f'NODE{i}', f'TYPE{i}'])
    if nType not in sectionTypes:
      header.append(f'TEXT{i}')
    header.extend(f'{feature}{i}' for feature in featureDict.get(j, emptyA))
  rows = [tuple(header)]
  for (rm, r) in enumerate(results):
    rn = rm + 1
    row = [rn]
    refN = r[refColumn]
    sParts = T.sectionFromNode(refN)
    nParts = len(sParts)
    section = sParts + ((None, ) * (3 - nParts))
    row.extend(section)
    for j in range(nTuple):
      n = r[j]
      nType = F.otype.v(n)
      row.extend((n, nType))
      if nType not in sectionTypes:
        text = T.text(n, fmt=fmt, descend=nType not in noDescendTypes)
        row.append(text)
      row.extend(Fs(feature).v(n) for feature in featureDict.get(j, emptyA))
    rows.append(tuple(row))
  return tuple(rows)


def header(app):
  return (
      f'''
<div class="hdlinks">
  {app.dataLink}
  {app.charLink}
  {app.featureLink}
  {app.tfsLink}
  {app.tutLink}
</div>
''',
      f'<img class="hdlogo" src="/data/static/logo.png"/>',
      f'<img class="hdlogo" src="/server/static/icon.png"/>',
  )


def getRefMember(app, tup, linked, condensed):
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


def nodeFromSectionStr(app, sectionStr, lang='en'):
  api = app.api
  T = api.T
  sep1 = app.sectionSep1
  sep2 = app.sectionSep2
  msg = f'Not a valid passage: "{sectionStr}"'
  msgi = '{} "{}" is not a number'
  section = sectionStr.split(sep1)
  if len(section) > 2:
    return msg
  elif len(section) == 2:
    section2 = section[1].split(sep2)
    if len(section2) > 2:
      return msg
    section = [section[0]] + section2
  dataTypes = T.sectionFeatureTypes
  sectionTypes = T.sectionTypes
  sectionTyped = []
  msgs = []
  for (i, sectionPart) in enumerate(section):
    if dataTypes[i] == 'int':
      try:
        part = int(sectionPart)
      except ValueError:
        msgs.append(msgi.format(sectionTypes[i], sectionPart))
        part = None
    else:
      part = sectionPart
    sectionTyped.append(part)
  if msgs:
    return '\n'.join(msgs)

  sectionNode = T.nodeFromSection(sectionTyped, lang=lang)
  if sectionNode is None:
    return msg
  return sectionNode


def sectionStrFromNode(app, n, lang='en', lastSlot=False, fillup=False):
  api = app.api
  T = api.T
  seps = ('', app.sectionSep1, app.sectionSep2)

  section = T.sectionFromNode(n, lang=lang, lastSlot=lastSlot, fillup=fillup)
  return ''.join(
      '' if part is None else f'{seps[i]}{part}'
      for (i, part) in enumerate(section)
  )


def htmlEsc(val):
  return '' if val is None else str(val).replace('&', '&amp;').replace('<', '&lt;')


def mdEsc(val):
  return '' if val is None else str(val).replace('|', '&#124;')


def dm(md):
  display(Markdown(md))


def dh(html):
  display(HTML(html))


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
      dm(
          f'**{rest} more {item}s skipped** because we show a maximum of'
          f' {limit} {item}s at a time'
      )


def _condense(api, tuples, condenseType, multiple=False):
  F = api.F
  E = api.E
  L = api.L
  sortNodes = api.sortNodes
  otypeRank = api.otypeRank
  maxSlot = F.otype.maxSlot
  eoslots = E.oslots.data

  slotType = F.otype.slotType
  condenseRank = otypeRank[condenseType]

  containers = {}

  if not multiple:
    tuples = (tuples, )
  for tup in tuples:
    for n in tup:
      nType = F.otype.v(n)
      if nType == condenseType:
        containers.setdefault(n, set())
      elif nType == slotType:
        up = L.u(n, otype=condenseType)
        if up:
          containers.setdefault(up[0], set()).add(n)
      elif otypeRank[nType] < condenseRank:
        slots = eoslots[n - maxSlot - 1]
        first = slots[0]
        last = slots[-1]
        firstUp = L.u(first, otype=condenseType)
        lastUp = L.u(last, otype=condenseType)
        allUps = set()
        if firstUp:
          allUps.add(firstUp[0])
        if lastUp:
          allUps.add(lastUp[0])
        for up in allUps:
          containers.setdefault(up, set()).add(n)
      else:
        pass
        # containers.setdefault(n, set())
  return tuple((c, ) + tuple(containers[c]) for c in sortNodes(containers))


def _condenseSet(api, tuples, condenseType, multiple=False):
  F = api.F
  E = api.E
  L = api.L
  sortNodes = api.sortNodes
  otypeRank = api.otypeRank
  maxSlot = F.otype.maxSlot
  eoslots = E.oslots.data

  slotType = F.otype.slotType
  condenseRank = otypeRank[condenseType]

  containers = set()

  if not multiple:
    tuples = (tuples, )
  for tup in tuples:
    for n in tup:
      nType = F.otype.v(n)
      if nType == condenseType:
        containers.add(n)
      elif nType == slotType:
        up = L.u(n, otype=condenseType)
        if up:
          containers.add(up[0])
      elif otypeRank[nType] < condenseRank:
        slots = eoslots[n - maxSlot - 1]
        first = slots[0]
        last = slots[-1]
        firstUp = L.u(first, otype=condenseType)
        lastUp = L.u(last, otype=condenseType)
        if firstUp:
          containers.add(firstUp[0])
        if lastUp:
          containers.add(lastUp[0])
      else:
        containers.add(n)
      # we skip nodes with a higher rank than that of the container
  return sortNodes(containers)


def _getHighlights(api, tuples, highlights, colorMap, condenseType, multiple=False):
  F = api.F
  otypeRank = api.otypeRank

  condenseRank = otypeRank[condenseType]
  if type(highlights) is set:
    highlights = {m: '' for m in highlights}
  newHighlights = {}
  if highlights:
    newHighlights.update(highlights)

  if not multiple:
    tuples = (tuples, )
  for tup in tuples:
    for (i, n) in enumerate(tup):
      nType = F.otype.v(n)
      if otypeRank[nType] < condenseRank:
        thisHighlight = None
        if highlights:
          thisHighlight = highlights.get(n, None)
        elif colorMap is not None:
          thisHighlight = colorMap.get(i + 1, None)
        else:
          thisHighlight = ''
        if thisHighlight is not None:
          newHighlights[n] = thisHighlight
  return newHighlights
