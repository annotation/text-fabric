from functools import reduce

from IPython.display import display, Markdown, HTML

LIMIT_SHOW = 100
LIMIT_TABLE = 2000

RESULT = 'result'

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


def search(app, query, silent=False, sets=None, shallow=False):
  api = app.api
  info = api.info
  S = api.S
  results = S.search(query, sets=sets, shallow=shallow)
  if not shallow:
    results = sorted(results)
  nResults = len(results)
  plural = '' if nResults == 1 else 's'
  if not silent:
    info(f'{nResults} result{plural}')
  return results


def runSearch(api, query, cache):
  S = api.S
  plainSearch = S.search

  cacheKey = (query, False)
  if cacheKey in cache:
    return cache[cacheKey]
  (queryResults, messages) = plainSearch(query, msgCache=True)
  features = {}
  exe = getattr(S, 'exe', None)
  if exe:
    qnodes = getattr(exe, 'qnodes', [])
    features = tuple((i, tuple(sorted(q[1].keys()))) for (i, q) in enumerate(qnodes))
  queryResults = tuple(sorted(queryResults))
  cache[cacheKey] = (queryResults, messages, features)
  return (queryResults, messages, features)


def runSearchCondensed(api, query, cache, condenseType):
  cacheKey = (query, True, condenseType)
  if cacheKey in cache:
    return cache[cacheKey]
  (queryResults, messages, features) = runSearch(api, query, cache)
  queryResults = _condense(api, queryResults, condenseType, multiple=True)
  cache[cacheKey] = (queryResults, messages, features)
  return (queryResults, messages, features)


def composeP(
    app,
    items,
    textFormat,
    opened,
    sec2,
    withNodes=False,
    **options,
):
  passageHtml = []

  for item in items:
    passageHtml.append(
        _plainTextS2(
            app,
            item,
            opened,
            sec2,
            fmt=textFormat,
            withNodes=withNodes,
            **options,
        )
    )
  return '\n'.join(passageHtml)


def compose(
    app,
    tuples,
    features,
    start,
    position,
    opened,
    condensed,
    condenseType,
    textFormat,
    withNodes=False,
    linked=1,
    **options,
):
  api = app.api
  F = api.F

  if condenseType is None:
    condenseType = app.condenseType
  item = condenseType if condensed else RESULT

  features = set(reduce(
      set.union,
      (x[1] for x in features),
      set(),
  ))
  if features:
    app.prettySetup(features)

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
            isCondensed=condensed,
            condenseType=condenseType,
            item=item,
            linked=linked,
            fmt=textFormat,
            withNodes=withNodes,
            position=position,
            opened=i in opened,
            asString=True,
            **options,
        )
    )
  if features:
    app.prettySetup()
  return '\n'.join(tuplesHtml)


def table(
    app,
    tuples,
    condensed=False,
    condenseType=None,
    start=None,
    end=None,
    linked=1,
    fmt=None,
    withNodes=False,
    asString=False,
    **options,
):
  api = app.api
  F = api.F

  if condenseType is None:
    condenseType = app.condenseType
  item = condenseType if condensed else RESULT

  if condensed:
    tuples = _condense(api, tuples, condenseType, multiple=True)

  markdown = []
  one = True
  for (i, tup) in _tupleEnum(tuples, start, end, LIMIT_TABLE, item):
    if one:
      nColumns = len(tup)
      markdown.append('n | ' + (' | '.join(F.otype.v(n) for n in tup)))
      markdown.append(' | '.join('---' for n in range(nColumns + 1)))
      one = False
    markdown.append(
        plainTuple(
            app,
            tup,
            i,
            isCondensed=condensed,
            condenseType=condenseType,
            item=item,
            linked=linked,
            fmt=fmt,
            withNodes=withNodes,
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
    isCondensed=False,
    condenseType=None,
    item=RESULT,
    linked=1,
    fmt=None,
    withNodes=False,
    position=None,
    opened=False,
    asString=False,
    **options,
):
  asApp = app.asApp
  api = app.api
  F = api.F
  T = api.T
  if asApp:
    prettyRep = prettyTuple(
        app,
        tup,
        seqNumber,
        isCondensed=isCondensed,
        condenseType=condenseType,
        fmt=fmt,
        withNodes=withNodes,
        **options,
    ) if opened else ''
    current = ' focus' if seqNumber == position else ''
    attOpen = ' open ' if opened else ''
    refColumn = 1 if isCondensed else linked
    refNode = tup[refColumn - 1] if refColumn <= len(tup) else None
    refRef = '' if refNode is None else app.sectionLink(refNode)
    tupSeq = ','.join(str(n) for n in tup)
    sParts = T.sectionFromNode(refNode)
    passageAtt = ' '.join(f'sec{i}="{sParts[i] if i < len(sParts) else ""}"' for i in range(3))

    plainRep = ''.join(
        f'''<span>{mdEsc(app.plain(
                    n,
                    linked=i == linked - 1,
                    fmt=fmt,
                    withNodes=withNodes,
                    **options,
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
      {refRef}
      {plainRep}
    </summary>
    <div class="pretty">
      {prettyRep}
    </div>
  </details>
'''
    )
    return html
  markdown = [str(seqNumber)]
  for (i, n) in enumerate(tup):
    markdown.append(
        mdEsc(
            app.plain(
                n,
                linked=i == linked - 1,
                fmt=fmt,
                withNodes=withNodes,
                asString=True,
                **options,
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


def _plainTextS2(
    app,
    sNode,
    opened,
    sec2,
    fmt=None,
    withNodes=False,
    **options,
):
  api = app.api
  T = api.T
  seqNumber = T.sectionFromNode(sNode)[2]
  itemType = T.sectionTypes[2]
  isOpened = str(seqNumber) in opened
  tClass = '' if fmt is None else app.formatClass[fmt]
  prettyRep = prettyTuple(
      app,
      (sNode, ),
      seqNumber,
      isCondensed=False,
      condenseType=itemType,
      fmt=fmt,
      withNodes=withNodes,
      **options,
  ) if isOpened else ''
  current = ' focus' if str(seqNumber) == str(sec2) else ''
  attOpen = ' open ' if isOpened else ''

  textRep = T.text(sNode, fmt=fmt, descend=True)
  html = (
      f'''
<details
  class="pretty {current}"
  seq="{seqNumber}"
  {attOpen}
>
  <summary class="{tClass}">
    {app.sectionLink(sNode, text=seqNumber)}
    {textRep}
  </summary>
  <div class="pretty">
    {prettyRep}
  </div>
</details>
'''
  )
  return html


def show(
    app,
    tuples,
    condensed=True,
    condenseType=None,
    start=None,
    end=None,
    fmt=None,
    withNodes=False,
    suppress=set(),
    colorMap=None,
    highlights={},
    **options,
):
  api = app.api
  F = api.F

  if condenseType is None:
    condenseType = app.condenseType
  item = condenseType if condensed else RESULT

  if condensed:
    rawHighlights = _getHighlights(api, tuples, highlights, colorMap, condenseType, multiple=True)
    highlights = {}
    colorMap = None
    tuples = _condense(api, tuples, condenseType, multiple=True)
  else:
    rawHighlights = None

  for (i, tup) in _tupleEnum(tuples, start, end, LIMIT_SHOW, item):
    item = F.otype.v(tup[0]) if condenseType else RESULT
    prettyTuple(
        app,
        tup,
        i,
        isCondensed=condensed,
        condenseType=condenseType,
        item=item,
        fmt=fmt,
        withNodes=withNodes,
        suppress=suppress,
        colorMap=colorMap,
        highlights=highlights,
        rawHighlights=rawHighlights,
        **options,
    )


def prettyTuple(
    app,
    tup,
    seqNumber,
    item='Result',
    condenseType=None,
    isCondensed=False,
    fmt=None,
    withNodes=False,
    suppress=set(),
    colorMap=None,
    highlights={},
    rawHighlights=None,
    **options,
):
  asApp = app.asApp

  if len(tup) == 0:
    if asApp:
      return ''
    else:
      return

  api = app.api

  if condenseType is None:
    condenseType = app.condenseType

  containers = {tup[0]} if isCondensed else _condenseSet(api, tup, condenseType)
  newHighlights = (
      _getHighlights(api, tup, highlights, colorMap, condenseType)
      if rawHighlights is None else rawHighlights
  )

  if not asApp:
    dm(f'''

**{item}** *{seqNumber}*

''')
  if asApp:
    html = []
  for t in containers:
    h = app.pretty(
        t,
        condenseType=condenseType,
        fmt=fmt,
        withNodes=withNodes,
        suppress=suppress,
        highlights=newHighlights,
        **options,
    )
    if asApp:
      html.append(h)
  if asApp:
    return '\n'.join(html)


def pretty(
    app,
    n,
    condenseType=None,
    fmt=None,
    withNodes=False,
    suppress=set(),
    highlights={},
    **options,
):
  asApp = app.asApp
  api = app.api
  F = api.F
  L = api.L
  otypeRank = api.otypeRank

  containerN = None

  if condenseType:
    nType = F.otype.v(n)
    if nType == condenseType:
      containerN = n
    elif otypeRank[nType] < otypeRank[condenseType]:
      ups = L.u(n, otype=condenseType)
      if ups:
        containerN = ups[0]

  (firstSlot, lastSlot) = (
      getBoundary(api, n) if condenseType is None else
      (None, None) if containerN is None else getBoundary(api, containerN)
  )

  html = []
  if type(highlights) is set:
    highlights = {m: '' for m in highlights}
  app._pretty(
      n,
      True,
      html,
      firstSlot,
      lastSlot,
      condenseType=condenseType,
      fmt=fmt,
      withNodes=withNodes,
      suppress=suppress,
      highlights=highlights,
      **options,
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


def prettySetup(app, features=None, noneValues=None):
  if features is None:
    app.prettyFeatures = ()
  else:
    featuresRequested = tuple(features.strip().split()
                              ) if type(features) is str else tuple(sorted(features))
    tobeLoaded = set(featuresRequested) - app.prettyFeaturesLoaded
    if tobeLoaded:
      app.api.TF.load(tobeLoaded, add=True, silent=True)
      app.prettyFeaturesLoaded |= tobeLoaded
    app.prettyFeatures = featuresRequested
  if noneValues is None:
    app.noneValues = app.noneValues
  else:
    app.noneValues = noneValues


def getBoundary(api, n):
  F = api.F
  slotType = F.otype.slotType
  if F.otype.v(n) == slotType:
    return (n, n)
  L = api.L
  slots = L.d(n, otype=slotType)
  return (slots[0], slots[-1])


def getFeatures(
    app,
    n,
    suppress,
    features,
    o=None,
    withName=set(),
    givenValue={},
    plain=False,
):
  api = app.api
  Fs = api.Fs

  featurePartB = '<div class="features">'
  featurePartE = '</div>'

  givenFeatureSet = set(features)
  extraFeatures = (tuple(f for f in app.prettyFeatures if f not in givenFeatureSet))
  extraSet = set(extraFeatures)
  featureList = tuple(features) + extraFeatures
  nFeatures = len(features)

  withName |= set(app.prettyFeatures)

  if not plain:
    featurePart = featurePartB
    hasB = True
  else:
    featurePart = ''
    hasB = False
  for (i, name) in enumerate(featureList):
    if name not in suppress:
      if name in givenValue:
        value = givenValue[name]
      else:
        value = Fs(name).v(n)
        oValue = None if o is None else Fs(name).v(o)
        valueRep = None if value in app.noneValues else htmlEsc(value)
        oValueRep = None if o is None or oValue in app.noneValues else htmlEsc(oValue)
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


def getContext(api, nodes):
  F = api.F
  Fs = api.Fs
  Fall = api.Fall
  T = api.T
  # L = api.L
  # slotType = F.otype.slotType
  sectionTypes = set(T.sectionTypes)

  rows = []
  feats = tuple(sorted(Fall()))
  rows.append(('node', ) + tuple(T.sectionTypes) + feats + ('text', ))
  for n in sorted(nodes):
    nType = F.otype.v(n)
    sParts = T.sectionFromNode(n)
    nParts = len(sParts)
    section = sParts + ((None, ) * (3 - nParts))
    if nType in sectionTypes:
      text = ''
    else:
      # sns = [n] if nType == slotType else L.d(n, otype=slotType)
      # text = T.text(sns)
      text = T.text(n)
    rows.append((n, ) + section + tuple(Fs(f).v(n) for f in feats) + (text, ))
  return tuple(rows)


def getResultsX(api, results, features, noDescendTypes, fmt=None):
  F = api.F
  Fs = api.Fs
  T = api.T
  # L = api.L
  # slotType = F.otype.slotType
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
      # sns = [n] if nType == slotType else L.d(n, otype=slotType)
      row.extend((n, nType))
      if nType not in sectionTypes:
        text = T.text(n, fmt=fmt, descend=nType not in noDescendTypes)
        # text = T.text(sns)
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


def nodeFromDefaultSection(app, sectionStr):
  api = app.api
  T = api.T
  sep1 = app.sectionSep1
  sep2 = app.sectionSep2
  msg = f'Not a valid passage: "{sectionStr}"'
  msgi = '{} "{}" is not a number'
  section = sectionStr.split(sep1)
  if len(section) > 2:
    return (msg, None)
  elif len(section) == 2:
    section2 = section[1].split(sep2)
    if len(section2) > 2:
      return (msg, None)
  if len(section) != 1:
    section = [section[0]] + section2
  dataTypes = T.sectionFeatureTypes
  sectionTypes = T.sectionTypes
  sectionTyped = []
  for (i, sectionPart) in enumerate(section):
    if dataTypes[i] == 'int':
      try:
        part = int(sectionPart)
      except ValueError:
        return (msgi.format(sectionTypes[i], sectionPart))
    else:
      part = sectionPart
    sectionTyped.append(part)

  sectionNode = T.nodeFromSection(sectionTyped)
  if sectionNode is None:
    return (msg, None)
  return ('', sectionNode)


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
  L = api.L
  sortNodes = api.sortNodes
  otypeRank = api.otypeRank

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
        slots = L.d(n, otype=slotType)
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
  L = api.L
  sortNodes = api.sortNodes
  otypeRank = api.otypeRank

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
        slots = L.d(n, otype=slotType)
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
