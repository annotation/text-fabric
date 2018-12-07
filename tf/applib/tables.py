from .helpers import RESULT
from .display import plainTuple, prettyTuple


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
            _asString=True,
            extraFeatures=features,
            **display.consume(options, 'extraFeatures')
        )
    )

  return '\n'.join(tuplesHtml)


# tuples and sections

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
            _asString=True,
            **display.consume(options, 'condensed', 'extraFeatures')
        )
    )

  return '\n'.join(tuplesHtml)


# passages

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
        _plainTextS2(
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


# COMPOSE TABLES FOR CSV EXPORT FOR KERNEL

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


def _plainTextS2(
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
  isOpened = seqNumber in opened
  tClass = '' if d.fmt is None else display.formatClass[d.fmt].lower()

  (hlSec2s, hlNodes, hlPlainSlots, hlPrettySlots) = (
      highlights if highlights else
      (set(), set(), set(), set())
  )

  hlDot = '<span class="hldot"></span>' if sNode in hlSec2s else ''

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
  <summary class="{tClass}">
    {app._sectionLink(sNode, text=seqNumber)}
    {hlDot}
    {textRep}
  </summary>
  <div class="pretty">{prettyRep}</div>
</details>
'''
  )
  return html
