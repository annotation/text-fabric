from .relations import basicRelations
from .syntax import syntax
from .semantics import semantics
from .graph import connectedness, displayPlan
from .spin import spinAtoms, spinEdges
from .stitch import setStrategy, stitch


class SearchExe(object):
  perfParams = {}

  @classmethod
  def setPerfParams(cls, info):
    cls.perfParams = info

  def __init__(
      self,
      api,
      searchTemplate,
      outerTemplate=None,
      quKind=None,
      offset=0,
      level=0,
      sets=None,
      shallow=False,
      silent=True,
      showQuantifiers=False,
      msgCache=False,
      setInfo={},
  ):
    self.api = api
    self.searchTemplate = searchTemplate
    self.outerTemplate = outerTemplate
    self.quKind = quKind
    self.level = level
    self.offset = offset
    self.sets = sets
    self.shallow = 0 if not shallow else 1 if shallow is True else shallow
    self.silent = silent
    api.setSilent(silent)
    self.showQuantifiers = showQuantifiers
    self.msgCache = msgCache if type(msgCache) is list else -1 if msgCache else 0
    self.good = True
    self.setInfo = setInfo
    basicRelations(self, api)

# API METHODS ###

  def search(self, limit=None):
    api = self.api
    isSilent = api.isSilent
    setSilent = api.setSilent
    wasSilent = isSilent()
    setSilent(True)
    self.study()
    setSilent(wasSilent)
    return self.fetch(limit=limit)

  def study(self, strategy=None):
    api = self.api
    info = api.info
    msgCache = self.msgCache
    self.api.indent(level=0, reset=True)
    self.good = True

    setStrategy(self, strategy)
    if not self.good:
      return

    info('Checking search template ...', cache=msgCache)

    self._parse()
    self._prepare()
    if not self.good:
      return
    info(f'Setting up search space for {len(self.qnodes)} objects ...', cache=msgCache)
    spinAtoms(self)
    info(f'Constraining search space with {len(self.qedges)} relations ...', cache=msgCache)
    spinEdges(self)
    info(f'\t{len(self.thinned)} edges thinned', cache=msgCache)
    info(f'Setting up retrieval plan with strategy {self.strategyName} ...', cache=msgCache)
    stitch(self)
    if self.good:
      yarnContent = sum(len(y) for y in self.yarns.values())
      info(f'Ready to deliver results from {yarnContent} nodes', cache=msgCache)
      info('Iterate over S.fetch() to get the results', tm=False, cache=msgCache)
      info('See S.showPlan() to interpret the results', tm=False, cache=msgCache)

  def fetch(self, limit=None):
    if not self.good:
      queryResults = set() if self.shallow else []
    elif self.shallow:
      queryResults = self.results
    else:
      if limit is None:
        queryResults = self.results()
      else:
        queryResults = []
        for r in self.results():
          queryResults.append(r)
          if len(queryResults) == limit:
            break
        queryResults = tuple(queryResults)
    return queryResults

  def count(self, progress=None, limit=None):
    info = self.api.info
    error = self.api.error
    msgCache = self.msgCache
    indent = self.api.indent
    indent(level=0, reset=True)

    if not self.good:
      error('This search has problems. No results to count.', tm=False, cache=msgCache)
      return

    PROGRESS = 100
    LIMIT = 1000

    if progress is None:
      progress = PROGRESS
    if limit is None:
      limit = LIMIT

    info(
        'Counting results per {} up to {} ...'.format(
            progress,
            limit if limit > 0 else ' the end of the results',
        ), cache=msgCache
    )
    indent(level=1, reset=True)

    i = 0
    j = 0
    for r in self.results(remap=False):
      i += 1
      j += 1
      if j == progress:
        j = 0
        info(i, cache=msgCache)
      if limit > 0 and i >= limit:
        break

    indent(level=0)
    info(f'Done: {i} results')

# SHOWING WITH THE SEARCH GRAPH ###

  def showPlan(self, details=False):
    displayPlan(self, details=details)

  def showOuterTemplate(self, msgCache):
    error = self.api.error
    offset = self.offset
    outerTemplate = self.outerTemplate
    quKind = self.quKind
    if offset and outerTemplate is not None:
      for (i, line) in enumerate(outerTemplate.split('\n')):
        error(f'{i:>2} {line}', tm=False, cache=msgCache)
      error(f'line {offset:>2}: Error under {quKind}:', tm=False, cache=msgCache)

# TOP-LEVEL IMPLEMENTATION METHODS

  def _parse(self):
    syntax(self)
    semantics(self)

  def _prepare(self):
    if not self.good:
      return
    self.yarns = {}
    self.spreads = {}
    self.spreadsC = {}
    self.uptodate = {}
    self.results = None
    connectedness(self)
