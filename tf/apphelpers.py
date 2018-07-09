import os
import io
from shutil import rmtree
from glob import glob

import requests
from zipfile import ZipFile
from IPython.display import display, Markdown, HTML

LIMIT_SHOW = 100
LIMIT_TABLE = 2000

RESULT = 'result'
GH_BASE = '~/github'
EXPRESS_BASE = '~/text-fabric-data'

URL_GH = 'https://github.com'
URL_NB = 'http://nbviewer.jupyter.org/github'


def hasData(dataRel, ghBase, version):
  ghBase = os.path.expanduser(ghBase)
  expressBase = os.path.expanduser(EXPRESS_BASE)
  expressTfAll = f'{expressBase}/{dataRel}'
  expressTf = f'{expressTfAll}/{version}'
  ghTf = f'{ghBase}/{dataRel}/{version}'
  features = glob(f'{ghTf}/*.tf')
  if len(features):
    return ghBase
  features = glob(f'{expressTf}/*.tf')
  if len(features):
    return expressBase
  return False


def getData(dataUrl, dataRel, ghBase, version):
  expressBase = os.path.expanduser(EXPRESS_BASE)
  expressTfAll = f'{expressBase}/{dataRel}'
  expressTf = f'{expressTfAll}/{version}'
  ghBase = os.path.expanduser(ghBase)
  ghTf = f'{ghBase}/{dataRel}/{version}'

  dataBase = hasData(dataRel, ghBase, version)
  if dataBase == ghBase:
    print(f'Found data in GitHub repo: {ghTf}')
    return dataBase
  if dataBase == expressBase:
    print(f'Found data downloaded from GitHub release: {expressTf}')
    return dataBase

  result = getDataCustom(dataUrl, expressTfAll)
  if result:
    return expressBase
  return False


def getDataCustom(dataUrl, dest):
  print(f'Downloading data from {dataUrl} ...')
  try:
    r = requests.get(dataUrl, allow_redirects=True)
    zf = io.BytesIO(r.content)
  except Exception as e:
    print(str(e))
    print('Could not download data')
    return False

  print(f'Saving data in {dest}')

  try:
    z = ZipFile(zf)
    if not os.path.exists(dest):
      os.makedirs(dest, exist_ok=True)
    cwd = os.getcwd()
    os.chdir(dest)
    z.extractall()
    if os.path.exists(f'{dest}/__MACOSX'):
      rmtree(f'{dest}/__MACOSX')
  except Exception as e:
    print(str(e))
    print('Could not save downloaded data')
    os.chdir(cwd)
    return False

  print('Saved')
  os.chdir(cwd)
  return dest


def search(extraApi, query, silent=False, sets=None, shallow=False):
  api = extraApi.api
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
  plainSearch = api.S.search

  cacheKey = (query, False)
  if cacheKey in cache:
    return cache[cacheKey]
  (queryResults, messages) = plainSearch(query, msgCache=True)
  queryResults = tuple(sorted(queryResults))
  cache[cacheKey] = (queryResults, messages)
  return (queryResults, messages)


def runSearchCondensed(api, query, cache, condenseType):
  cacheKey = (query, True, condenseType)
  if cacheKey in cache:
    return cache[cacheKey]
  (queryResults, messages) = runSearch(api, query, cache)
  queryResults = _condense(api, queryResults, condenseType, multiple=True)
  cache[cacheKey] = (queryResults, messages)
  return (queryResults, messages)


def compose(
    extraApi,
    tuples,
    start,
    position,
    opened,
    condensed,
    condenseType,
    withNodes=False,
    linked=1,
    **options,
):
  api = extraApi.api
  F = api.F

  if condenseType is None:
    condenseType = extraApi.condenseType
  item = condenseType if condensed else RESULT

  tuplesHtml = []
  doHeader = False
  for (i, tup) in tuples:
    if i is None:
      if tup == 'results':
        doHeader = True
      else:
        tuplesHtml.append(f'''
<div class="dtheadrow">
  <span>n</span><span>{tup}</span>
</div>
''')
      continue

    if doHeader:
      doHeader = False
      tuplesHtml.append(f'''
<div class="dtheadrow">
  <span>n</span><span>{"</span><span>".join(F.otype.v(n) for n in tup)}</span>
</div>
''')
    tuplesHtml.append(
        plainTuple(
            extraApi,
            tup,
            i,
            isCondensed=condensed,
            condenseType=condenseType,
            item=item,
            linked=linked,
            withNodes=withNodes,
            position=position,
            opened=i in opened,
            asString=True,
            **options,
        )
    )
  return '\n'.join(tuplesHtml)


def table(
    extraApi,
    tuples,
    condensed=False,
    condenseType=None,
    start=None,
    end=None,
    linked=1,
    withNodes=False,
    asString=False,
    **options,
):
  api = extraApi.api
  F = api.F

  if condenseType is None:
    condenseType = extraApi.condenseType
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
    markdown.append(plainTuple(
        extraApi,
        tup,
        i,
        isCondensed=condensed,
        condenseType=condenseType,
        item=item,
        linked=linked,
        withNodes=withNodes,
        position=None,
        opened=False,
        asString=True,
        **options,
    ))
  markdown = '\n'.join(markdown)
  if asString:
    return markdown
  dm(markdown)


def plainTuple(
    extraApi,
    tup,
    seqNumber,
    isCondensed=False,
    condenseType=None,
    item=RESULT,
    linked=1,
    withNodes=False,
    position=None,
    opened=False,
    asString=False,
    **options,
):
  asApi = extraApi.asApi
  api = extraApi.api
  F = api.F
  if asApi:
    prettyRep = prettyTuple(
        extraApi,
        tup,
        seqNumber,
        isCondensed=isCondensed,
        condenseType=condenseType,
        withNodes=withNodes,
        **options,
    ) if opened else ''
    current = ' focus' if seqNumber == position else ''
    attOpen = ' open ' if opened else ''
    refColumn = 1 if isCondensed else linked
    refNode = tup[refColumn - 1] if refColumn <= len(tup) else None
    refRef = '' if refNode is None else extraApi.webLink(refNode)
    tupSeq = ','.join(str(n) for n in tup)

    plainRep = ''.join(
        f'''<span>{mdEsc(extraApi.plain(
                    n,
                    linked=i == linked - 1,
                    withNodes=withNodes,
                    **options,
                  ))
                }
            </span>
        '''
        for (i, n) in enumerate(tup)
    )
    html = (
        f'''
  <details
    class="pretty dtrow{current}"
    seq="{seqNumber}"
    {attOpen}
  >
    <summary><a href="#" class="sq" tup="{tupSeq}">{seqNumber}</span> {refRef} {plainRep}</summary>
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
        mdEsc(extraApi.plain(
            n,
            linked=i == linked - 1,
            withNodes=withNodes,
            asString=True,
            **options,
        ))
    )
  markdown = '|'.join(markdown)
  if asString:
    return markdown
  head = ['n | ' + (' | '.join(F.otype.v(n) for n in tup))]
  head.append(' | '.join('---' for n in range(len(tup) + 1)))
  head.append(markdown)

  dm('\n'.join(head))


def show(
    extraApi,
    tuples,
    condensed=True,
    condenseType=None,
    start=None,
    end=None,
    withNodes=False,
    suppress=set(),
    colorMap=None,
    highlights={},
    **options,
):
  api = extraApi.api
  F = api.F

  if condenseType is None:
    condenseType = extraApi.condenseType
  item = condenseType if condensed else RESULT

  if condensed:
    rawHighlights = _getHighlights(
        api, tuples, highlights, colorMap, condenseType, multiple=True
    )
    highlights = {}
    colorMap = None
    tuples = _condense(api, tuples, condenseType, multiple=True)
  else:
    rawHighlights = None

  for (i, tup) in _tupleEnum(tuples, start, end, LIMIT_SHOW, item):
    item = F.otype.v(tup[0]) if condenseType else RESULT
    prettyTuple(
        extraApi,
        tup,
        i,
        isCondensed=condensed,
        condenseType=condenseType,
        item=item,
        withNodes=withNodes,
        suppress=suppress,
        colorMap=colorMap,
        highlights=highlights,
        rawHighlights=rawHighlights,
        **options,
    )


def prettyTuple(
    extraApi,
    tup,
    seqNumber,
    item='Result',
    condenseType=None,
    isCondensed=False,
    withNodes=False,
    suppress=set(),
    colorMap=None,
    highlights={},
    rawHighlights=None,
    **options,
):
  asApi = extraApi.asApi

  if len(tup) == 0:
    if asApi:
      return ''
    else:
      return

  api = extraApi.api

  if condenseType is None:
    condenseType = extraApi.condenseType

  containers = {tup[0]} if isCondensed else _condenseSet(api, tup, condenseType)
  newHighlights = (
      _getHighlights(api, tup, highlights, colorMap, condenseType)
      if rawHighlights is None else
      rawHighlights
  )

  if not asApi:
    dm(f'''

**{item}** *{seqNumber}*

''')
  if asApi:
    html = []
  for t in containers:
    h = extraApi.pretty(
        t,
        condenseType=condenseType,
        withNodes=withNodes,
        suppress=suppress,
        highlights=newHighlights,
        **options,
    )
    if asApi:
      html.append(h)
  if asApi:
    return '\n'.join(html)


def pretty(
    extraApi,
    n,
    condenseType=None,
    withNodes=False,
    suppress=set(),
    highlights={},
    **options,
):
  asApi = extraApi.asApi
  api = extraApi.api
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
      getBoundary(api, n)
      if condenseType is None else
      (None, None)
      if containerN is None else
      getBoundary(api, containerN)
  )

  html = []
  if type(highlights) is set:
    highlights = {m: '' for m in highlights}
  extraApi._pretty(
      n,
      True,
      html,
      firstSlot,
      lastSlot,
      condenseType=condenseType,
      withNodes=withNodes,
      suppress=suppress,
      highlights=highlights,
      **options,
  )
  htmlStr = '\n'.join(html)
  if asApi:
    return htmlStr
  display(HTML(htmlStr))


def prettyPre(
    extraApi,
    n,
    firstSlot,
    lastSlot,
    withNodes,
    highlights,
):
  api = extraApi.api
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
  className = extraApi.classNames.get(nType, None)

  return (
      slotType, nType,
      className, boundaryClass, hlClass, hlStyle,
      nodePart,
      myStart, myEnd,
  )


def prettySetup(extraApi, features=None, noneValues=None):
  if features is None:
    extraApi.prettyFeatures = ()
  else:
    featuresRequested = (tuple(features.strip().split()
                               )) if type(features) is str else tuple(features)
    tobeLoaded = set(featuresRequested) - extraApi.prettyFeaturesLoaded
    if tobeLoaded:
      extraApi.api.TF.load(tobeLoaded, add=True, silent=True)
      extraApi.prettyFeaturesLoaded |= tobeLoaded
    extraApi.prettyFeatures = featuresRequested
  if noneValues is None:
    extraApi.noneValues = extraApi.noneValues
  else:
    extraApi.noneValues = noneValues


def getBoundary(api, n):
  F = api.F
  slotType = F.otype.slotType
  if F.otype.v(n) == slotType:
    return (n, n)
  L = api.L
  slots = L.d(n, otype=slotType)
  return (slots[0], slots[-1])


def getFeatures(
    extraApi, n, suppress, features,
    withName=set(),
    givenValue={},
    plain=False,
):
  api = extraApi.api
  Fs = api.Fs

  featurePartB = '<div class="features">'
  featurePartE = '</div>'

  givenFeatureSet = set(features)
  extraFeatures = (
      tuple(f for f in extraApi.prettyFeatures if f not in givenFeatureSet)
  )
  featureList = tuple(features) + extraFeatures
  nFeatures = len(features)

  withName |= set(extraApi.prettyFeatures)

  if not plain:
    featurePart = featurePartB
    hasB = True
  else:
    featurePart = ''
    hasB = False
  for (i, name) in enumerate(featureList):
    if name not in suppress:
      value = (
          givenValue[name]
          if name in givenValue else
          Fs(name).v(n)
      )
      if value not in extraApi.noneValues:
        if name not in givenValue:
          value = htmlEsc(value)
        nameRep = f'<span class="f">{name}=</span>' if name in withName else ''
        featureRep = f' <span class="{name}">{nameRep}{value}</span>'

        if i >= nFeatures:
          if not hasB:
            featurePart += featurePartB
            hasB = True
        featurePart += featureRep
  if hasB:
    featurePart += featurePartE
  return featurePart


def getContext(api, nodes):
  Fs = api.Fs
  Fall = api.Fall

  rows = []
  feats = tuple(sorted(Fall()))
  rows.append(('node',) + feats)
  for n in sorted(nodes):
    rows.append((n,) + tuple(Fs(f).v(n) for f in feats))
  return tuple(rows)


def header(extraApi):
  return (
      f'''
<div class="hdlinks">
  {extraApi.dataLink}
  {extraApi.featureLink}
  {extraApi.tfsLink}
  {extraApi.tutLink}
</div>
''',
      f'<img class="hdlogo" src="/data/static/logo.png"/>',
      f'<img class="hdlogo" src="/server/static/logo.png"/>',
  )


def outLink(text, href, title=None, className=None, target='_blank'):
  titleAtt = '' if title is None else f' title="{title}"'
  classAtt = f' class="{className}"' if className else ''
  targetAtt = f' target="{target}"' if target else ''
  return f'<a{classAtt}{targetAtt} href="{href}"{titleAtt}>{text}</a>'


def htmlEsc(val):
  return '' if val is None else str(val).replace('&', '&amp;').replace('<', '&lt;')


def mdEsc(val):
  return '' if val is None else str(val).replace('|', '&#124;')


def dm(md):
  display(Markdown(md))


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
    tuples = (tuples,)
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
    tuples = (tuples,)
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
    tuples = (tuples,)
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
