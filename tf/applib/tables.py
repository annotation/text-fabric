from .helpers import RESULT
from .display import plain, plainTuple, pretty, prettyTuple


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
    browseNavLevel,
    finalSecType,
    features,
    items,
    opened,
    secFinal,
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

  if not items:
    return ''

  if type(items) is int:
    return pretty(app, items)

  if getx is not None:
    tup = None
    for sFinal in items:
      i = T.sectionFromNode(sFinal)[browseNavLevel]
      if i == getx:
        tup = (sFinal, )
        break
    return prettyTuple(
        app,
        tup,
        getx,
        condensed=False,
        condenseType=finalSecType,
        extraFeatures=features,
        **display.consume(options, 'condensed', 'condenseType', 'extraFeatures')
    ) if tup is not None else ''

  passageHtml = []

  for item in items:
    passageHtml.append(
        _plainTextSFinal(
            app,
            browseNavLevel,
            finalSecType,
            item,
            opened,
            secFinal,
            extraFeatures=features,
            **display.consume(options, 'extraFeatures')
        )
    )

  return '\n'.join(passageHtml)


def _plainTextSFinal(
    app,
    browseNavLevel,
    finalSecType,
    sNode,
    opened,
    secFinal,
    **options,
):
  display = app.display
  d = display.get(options)

  api = app.api
  T = api.T
  secStr = str(T.sectionFromNode(sNode)[browseNavLevel])
  isOpened = secStr in opened
  tClass = '' if d.fmt is None else display.formatClass[d.fmt].lower()

  prettyRep = prettyTuple(
      app,
      (sNode, ),
      secStr,
      condensed=False,
      condenseType=finalSecType,
      **display.consume(options, 'condensed', 'condenseType'),
  ) if isOpened else ''
  current = ' focus' if secStr == str(secFinal) else ''
  attOpen = ' open ' if isOpened else ''

  textRep = plain(
      app, sNode, secLabel=False, withPassage=False, **display.consume(options, 'withPassage')
  )
  html = (
      f'''
<details
  class="pretty{current}"
  seq="{secStr}"
  {attOpen}
>
  <summary class="{tClass}">
    {app._sectionLink(sNode, text=secStr)}
    {textRep}
  </summary>
  <div class="pretty">{prettyRep}</div>
</details>
'''
  )
  return html
