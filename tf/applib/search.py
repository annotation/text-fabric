import types

from ..core.helpers import console
from .condense import condense


def searchApi(app):
  app.search = types.MethodType(search, app)


def search(app, query, silent=False, sets=None, shallow=False, sort=True):
  api = app.api
  info = api.info
  isSilent = api.isSilent
  setSilent = api.setSilent
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

    features = ()
    if S.exe:
      qnodes = getattr(S.exe, 'qnodes', [])
      nodeMap = getattr(S.exe, 'nodeMap', {})
      features = tuple(
          (i, tuple(sorted(set(q[1].keys()) | nodeMap.get(i, set()))))
          for (i, q) in enumerate(qnodes)
      )
      app.displaySetup(tupleFeatures=features)

  nResults = len(results)
  plural = '' if nResults == 1 else 's'
  wasSilent = isSilent
  setSilent(silent)
  info(f'{nResults} result{plural}')
  setSilent(wasSilent)
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
    nodeMap = getattr(S.exe, 'nodeMap', {})
    features = tuple(
        (i, tuple(sorted(set(q[1].keys()) | nodeMap.get(i, set()))))
        for (i, q) in enumerate(qnodes)
    )
  queryResults = tuple(sorted(queryResults))
  cache[cacheKey] = (queryResults, messages, features)
  return (queryResults, messages, features)


def runSearchCondensed(app, query, cache, condenseType):
  api = app.api
  cacheKey = (query, True, condenseType)
  if cacheKey in cache:
    return cache[cacheKey]
  (queryResults, messages, features) = runSearch(app, query, cache)
  queryResults = condense(api, queryResults, condenseType, multiple=True)
  cache[cacheKey] = (queryResults, messages, features)
  return (queryResults, messages, features)
