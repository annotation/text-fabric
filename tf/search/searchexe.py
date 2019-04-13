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
    self.showQuantifiers = showQuantifiers
    self.msgCache = msgCache if type(msgCache) is list else -1 if msgCache else 0
    self.good = True
    self.setInfo = setInfo
    basicRelations(self, api, silent)

# API METHODS ###

  def search(self, limit=None):
    self.silent = True
    self.study()
    return self.fetch(limit=limit)

  def study(self, strategy=None):
    info = self.api.info
    msgCache = self.msgCache
    self.api.indent(level=0, reset=True)
    self.good = True

    setStrategy(self, strategy)
    if not self.good:
      return

    if not self.silent:
      info('Checking search template ...', cache=msgCache)

    self._parse()
    self._prepare()
    if not self.good:
      return
    if not self.silent:
      info(f'Setting up search space for {len(self.qnodes)} objects ...', cache=msgCache)
    spinAtoms(self)
    if not self.silent:
      info(f'Constraining search space with {len(self.qedges)} relations ...', cache=msgCache)
    spinEdges(self)
    if not self.silent:
      info('Setting up retrieval plan ...', cache=msgCache)
    stitch(self)
    if self.good:
      if not self.silent:
        yarnContent = sum(len(y) for y in self.yarns.values())
        info(f'Ready to deliver results from {yarnContent} nodes', cache=msgCache)
      if not self.silent:
        info('Iterate over S.fetch() to get the results', tm=False, cache=msgCache)
      if not self.silent:
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
    if not self.good:
      return
    info = self.api.info
    msgCache = self.msgCache
    nodeLine = self.nodeLine
    qedges = self.qedges
    (qs, es) = self.stitchPlan
    offset = self.offset
    if details:
      info(f'Search with {len(qs)} objects and {len(es)} relations', tm=False, cache=msgCache)
      info('Results are instantiations of the following objects:', tm=False)
      for q in qs:
        self._showNode(q)
      if len(es) != 0:
        info('Instantiations are computed along the following relations:', tm=False, cache=msgCache)
        (firstE, firstDir) = es[0]
        (f, rela, t) = qedges[firstE]
        if firstDir == -1:
          (f, t) = (t, f)
        self._showNode(f, pos2=True)
        for e in es:
          self._showEdge(*e)
    info('The results are connected to the original search template as follows:', cache=msgCache)

    resultNode = {}
    for q in qs:
      resultNode[nodeLine[q]] = q
    for (i, line) in enumerate(self.searchLines):
      rNode = resultNode.get(i, '')
      prefix = '' if rNode == '' else 'R'
      info(f'{i + offset:>2} {prefix:<1}{rNode:<2} {line}', tm=False, cache=msgCache)

  def showOuterTemplate(self, msgCache):
    error = self.api.error
    offset = self.offset
    outerTemplate = self.outerTemplate
    quKind = self.quKind
    if offset and outerTemplate is not None:
      for (i, line) in enumerate(outerTemplate.split('\n')):
        error(f'{i:>2} {line}', tm=False, cache=msgCache)
      error(f'line {offset:>2}: Error under {quKind}:', tm=False, cache=msgCache)

  def _showNode(self, q, pos2=False):
    info = self.api.info
    msgCache = self.msgCache
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
    info(nodeInfo, tm=False, cache=msgCache)

  def _showEdge(self, e, dir):
    info = self.api.info
    msgCache = self.msgCache
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
        ), tm=False, cache=msgCache
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
