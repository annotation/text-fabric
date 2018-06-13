from .context import gatherContext
from .relations import basicRelations
from .syntax import syntax
from .semantics import semantics
from .graph import connectedness
from .spin import spinAtoms, spinEdges
from .stitch import setStrategy, stitch


class SearchExe(object):
  def __init__(
      self,
      api,
      searchTemplate,
      level=0,
      sets=None,
      shallow=False,
      silent=True,
      showQuantifiers=False,
      withContext=None,
      msgCache=False,
  ):
    self.api = api
    self.searchTemplate = searchTemplate
    self.level = level
    self.sets = sets
    self.shallow = 0 if not shallow else 1 if shallow is True else shallow
    self.silent = silent
    self.showQuantifiers = showQuantifiers
    self.context = withContext
    self.doCache = -1 if msgCache else 0
    self.good = True
    basicRelations(self, api, silent)

# API METHODS ###

  def search(self, limit=None):
    self.silent = True
    self.study()
    return self.fetch(limit=limit)

  def study(self, strategy=None):
    info = self.api.info
    doCache = self.doCache
    self.api.indent(level=0, reset=True)
    self.good = True

    setStrategy(self, strategy)
    if not self.good:
      return

    if not self.silent:
      info('Checking search template ...', cache=doCache)

    self._parse()
    self._prepare()
    if not self.good:
      return
    if not self.silent:
      info(f'Setting up search space for {len(self.qnodes)} objects ...', cache=doCache)
    spinAtoms(self)
    if not self.silent:
      info(f'Constraining search space with {len(self.qedges)} relations ...', cache=doCache)
    spinEdges(self)
    if not self.silent:
      info('Setting up retrieval plan ...', cache=doCache)
    stitch(self)
    if self.good:
      if not self.silent:
        yarnContent = sum(len(y) for y in self.yarns.values())
        info(f'Ready to deliver results from {yarnContent} nodes', cache=doCache)
      if not self.silent:
        info('Iterate over S.fetch() to get the results', tm=False, cache=doCache)
      if not self.silent:
        info('See S.showPlan() to interpret the results', tm=False, cache=doCache)

  def fetch(self, limit=None):
    cache = self.api.cache
    doCache = self.doCache
    if not self.good:
      queryResults = set() if self.shallow else []
    elif self.shallow:
      queryResults = self.results
    elif limit is None:
      queryResults = self.results()
    else:
      queryResults = []
      for r in self.results():
        queryResults.append(r)
        if len(queryResults) == limit:
          break
      queryResults = tuple(queryResults)
    if self.context:
      queryResults = sorted(queryResults)
      context = gatherContext(self.api, self.context, queryResults)
    if doCache:
      messages = cache(asString=True)
    if self.context and doCache:
      return (queryResults, context, messages)
    if self.context:
      return (queryResults, context)
    if doCache:
      return (queryResults, messages)
    return queryResults

  def count(self, progress=None, limit=None):
    info = self.api.info
    error = self.api.error
    doCache = self.doCache
    indent = self.api.indent
    indent(level=0, reset=True)

    if not self.good:
      error('This search has problems. No results to count.', tm=False, cache=doCache)
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
        ),
        cache=doCache
    )
    indent(level=1, reset=True)

    i = 0
    j = 0
    for r in self.results(remap=False):
      i += 1
      j += 1
      if j == progress:
        j = 0
        info(i, cache=doCache)
      if limit > 0 and i >= limit:
        break

    indent(level=0)
    info(f'Done: {i} results')

# SHOWING WITH THE SEARCH GRAPH ###

  def showPlan(self, details=False):
    if not self.good:
      return
    info = self.api.info
    doCache = self.doCache
    nodeLine = self.nodeLine
    qedges = self.qedges
    (qs, es) = self.stitchPlan
    if details:
      info(f'Search with {len(qs)} objects and {len(es)} relations', tm=False, cache=doCache)
      info('Results are instantiations of the following objects:', tm=False)
      for q in qs:
        self._showNode(q)
      if len(es) != 0:
        info('Instantiations are computed along the following relations:', tm=False, cache=doCache)
        (firstE, firstDir) = es[0]
        (f, rela, t) = qedges[firstE]
        if firstDir == -1:
          (f, t) = (t, f)
        self._showNode(f, pos2=True)
        for e in es:
          self._showEdge(*e)
    info('The results are connected to the original search template as follows:', cache=doCache)

    resultNode = {}
    for q in qs:
      resultNode[nodeLine[q]] = q
    for (i, line) in enumerate(self.searchLines):
      rNode = resultNode.get(i, '')
      prefix = '' if rNode == '' else 'R'
      info(f'{i:>2} {prefix:<1}{rNode:<2} {line}', tm=False, cache=doCache)

  def _showNode(self, q, pos2=False):
    info = self.api.info
    doCache = self.doCache
    qnodes = self.qnodes
    yarns = self.yarns
    space = ' ' * 19
    nodeInfo = 'node {} {:>2}-{:<13} ({:>6}   choices)'.format(
        space,
        q,
        qnodes[q][0],
        len(yarns[q]),
    ) if pos2 else 'node {:>2}-{:<13} {} ({:>6}   choices)'.format(
        q,
        qnodes[q][0],
        space,
        len(yarns[q]),
    )
    info(nodeInfo, tm=False, cache=doCache)

  def _showEdge(self, e, dir):
    info = self.api.info
    doCache = self.doCache
    qnodes = self.qnodes
    qedges = self.qedges
    converse = self.converse
    relations = self.relations
    spreads = self.spreads
    spreadsC = self.spreadsC
    (f, rela, t) = qedges[e]
    if dir == -1:
      (f, rela, t) = (t, converse[rela], f)
    info(
        'edge {:>2}-{:<13} {:^2} {:>2}-{:<13} ({:8.1f} choices)'.format(
            f,
            qnodes[f][0],
            relations[rela]['acro'],
            t,
            qnodes[t][0],
            spreads.get(e, -1) if dir == 1 else spreadsC.get(e, -1),
        ),
        tm=False, cache=doCache
    )

  def _showYarns(self):
    for q in range(len(self.qnodes)):
      self._showNode(q)

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
