# from functools import reduce

from ..core.helpers import mathEsc, mdhtmlEsc
from .search import runSearch


def getHlAtt(app, n, highlights):

  if highlights is None:
    return ('', '')

  color = (
      highlights.get(n, None)
      if type(highlights) is dict else
      '' if n in highlights else
      None
  )

  if color is None:
    return ('', '')

  hlClass = 'hl'
  hlStyle = (
      f' style="background-color: {color};" '
      if color != '' else
      ''
  )

  return (hlClass, hlStyle)


def getHlAttPlain(app, n, highlights):
  api = app.api
  F = api.F
  L = api.L
  T = api.T
  sectionTypes = T.sectionTypes

  if highlights is None:
    return ''

  color = (
      highlights.get(n, None)
      if type(highlights) is dict else
      '' if n in highlights else
      None
  )
  upColors = tuple(
      highlights[u]
      for u in L.u(n)
      if u in highlights and F.otype.v(u) not in sectionTypes
  )
  upColor = upColors[0] if upColors else None

  if color is None and upColor is None:
    return ''

  isSection = F.otype.v(n) in sectionTypes
  hlClass = []
  hlStyle = []

  if color is not None:
    hlClass.append('hldot' if isSection else 'hl')
    if color != '':
      hlStyle.append(f'background-color: {color};')
      if isSection:
        hlStyle.append(f'border-color: {color};')

  if upColor is not None:
    hlClass.append('hlup')
    if upColor != '':
      hlStyle.append(f'border-color: {upColor};')

  hlClassAtt = ' '.join(hlClass)
  if hlClassAtt:
    hlClassAtt = f' class="{hlClassAtt}" '
  hlStyleAtt = ''.join(hlStyle)
  if hlStyleAtt:
    hlStyleAtt = f' style="{hlStyleAtt}" '

  return f'{hlClassAtt}{hlStyleAtt}'


def hlRep(app, rep, n, highlights):
  att = getHlAttPlain(app, n, highlights)
  return f'<span {att}>{rep}</span>' if att else rep


def hlText(app, nodes, highlights, **options):
  api = app.api
  T = api.T
  isHtml = hasattr(app, 'textFormats') and options.get('fmt', None) in app.textFormats

  if not highlights:
    text = T.text(nodes, **options)
    return mathEsc(text) if isHtml else mdhtmlEsc(text)

  result = ''
  for node in nodes:
    text = T.text([node], **options)
    result += hlRep(
        app,
        mathEsc(text) if isHtml else mdhtmlEsc(text),
        node,
        highlights,
    )
  return result


def getTupleHighlights(api, tuples, highlights, colorMap, condenseType, multiple=False):
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


def getPassageHighlights(app, node, query, cache):
  if not query:
    return None

  (queryResults, messages, features) = runSearch(app, query, cache)
  if messages:
    return None

  api = app.api
  L = api.L
  passageNodes = L.d(node)

  highlights = set()
  for tup in queryResults:
    for t in tup:
      if t in passageNodes:
        highlights.add(t)
  return highlights

  # return reduce(
  #     set.union,
  #     (set(tup) for tup in queryResults),
  #     set()
  # )
