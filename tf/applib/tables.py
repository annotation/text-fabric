from .helpers import RESULT
from .display import plain, plainTuple, prettyTuple


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

  if getx is not None:
    itemType = T.sectionTypes[2]
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
        condenseType=itemType,
        extraFeatures=features,
        **display.consume(options, 'condensed', 'condenseType', 'extraFeatures')
    ) if tup is not None else ''

  passageHtml = []

  for item in items:
    passageHtml.append(
        _plainTextS2(
            app,
            item,
            opened,
            sec2,
            extraFeatures=features,
            **display.consume(options, 'extraFeatures')
        )
    )

  return '\n'.join(passageHtml)


def _plainTextS2(
    app,
    sNode,
    opened,
    sec2,
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

  prettyRep = prettyTuple(
      app,
      (sNode, ),
      seqNumber,
      condensed=False,
      condenseType=itemType,
      **display.consume(options, 'condensed', 'condenseType'),
  ) if isOpened else ''
  current = ' focus' if str(seqNumber) == str(sec2) else ''
  attOpen = ' open ' if isOpened else ''

  textRep = plain(app, sNode, secLabel=False, **options)
  html = (
      f'''
<details
  class="pretty{current}"
  seq="{seqNumber}"
  {attOpen}
>
  <summary class="{tClass}">
    {app._sectionLink(sNode, text=seqNumber)}
    {textRep}
  </summary>
  <div class="pretty">{prettyRep}</div>
</details>
'''
  )
  return html
