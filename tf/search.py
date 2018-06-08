import re
import types
import collections
from functools import reduce
from random import randrange
from inspect import signature

from .data import WARP
from .helpers import project

STRATEGY = '''
    small_choice_first
    spread_1_first
    big_choice_first
'''.strip().split()

escapes = (
    '\\\\',
    '\\ ',
    '\\t',
    '\\n',
    '\\|',
    '\\=',
)

PARENT_REF = '..'

QWHERE = '/where/'
QHAVE = '/have/'
QWITHOUT = '/without/'
QWITH = '/with/'
QOR = '/or/'
QEND = '/-/'

QINIT = {QWHERE, QWITHOUT, QWITH}
QCONT = {QHAVE, QOR}
QTERM = {QEND}

rePat = '^([a-zA-Z0-9-@_]+)~(.*)$'
reRe = re.compile(rePat)
reTp = type(reRe)

compPat = '^([a-zA-Z0-9-@_]+)([<>])(.*)$'
compRe = re.compile(compPat)

identPat = '^([a-zA-Z0-9-@_]+)([=#])(.+)$'
identRe = re.compile(identPat)

numPat = '^-?[0-9]+$'
numRe = re.compile(numPat)

nonePat = '^([a-zA-Z0-9-@_]+)(#?)\s*$'
noneRe = re.compile(nonePat)

indentLinePat = '^(\s*)(.*)'
indentLineRe = re.compile(indentLinePat)

opPat = '(?:[#&|\[\]<>:=-]+\S*)'
quPat = f'(?:{QWHERE}|{QHAVE}|{QWITHOUT}|{QWITH}|{QOR}|{QEND})'
atomPat = '(\s*)([^ \t=#<>~]+)(?:(?:\s*\Z)|(?:\s+(.*)))$'
atomOpPat = ('(\s*)({op})\s+([^ \t=#<>~]+)(?:(?:\s*\Z)|(?:\s+(.*)))$'.format(op=opPat))
opLinePat = '^(\s*)({op})\s*$'.format(op=opPat)
opStripPat = '^\s*{op}\s+(.*)$'.format(op=opPat)
quLinePat = '^(\s*)({qu})\s*$'.format(qu=quPat)
namePat = '[A-Za-z0-9_.-]+'
relPat = '^(\s*)({nm})\s+({op})\s+({nm})\s*$'.format(nm=namePat, op=opPat)
kPat = '^([^0-9]*)([0-9]+)([^0-9]*)$'

namesPat = '^\s*(?:{op}\s+)?([^ \t:=#<>~]+):'

atomRe = re.compile(atomPat)
atomOpRe = re.compile(atomOpPat)
opLineRe = re.compile(opLinePat)
opStripRe = re.compile(opStripPat)
quLineRe = re.compile(quLinePat)
namesRe = re.compile(namesPat)
nameRe = re.compile('^{}$'.format(namePat))
relRe = re.compile(relPat)
kRe = re.compile(kPat)
whiteRe = re.compile('^\s*$')


def _parseLine(line):
  for x in [True]:
    escLine = esc(line)

    match = opLineRe.match(escLine)
    if match:
      (indent, op) = match.groups()
      kind = 'op'
      data = (indent, op)
      break

    match = relRe.match(escLine)
    if match:
      (indent, f, op, t) = match.groups()
      kind = 'rel'
      data = (indent, f, op, t)
      break

    matchOp = atomOpRe.match(escLine)
    if matchOp:
      (indent, op, atom, features) = matchOp.groups()
    else:
      match = atomRe.match(escLine)
      if match:
        op = None
        (indent, atom, features) = match.groups()
    if matchOp or match:
      atomComps = atom.split(':', 1)
      if len(atomComps) == 1:
        name = ''
        otype = atomComps[0]
      else:
        name = atomComps[0]
        otype = atomComps[1]
      kind = 'atom'
      if features is None:
        features = ''
      data = (indent, op, name, otype, features)
      break

    kind = 'feat'
    data = (escLine, )

  return (kind, data)


def _genLine(kind, data):
  result = None

  for x in [True]:
    if kind == 'op':
      (indent, op) = data
      result = f'{indent}{unesc(op)}'
      break

    if kind == 'rel':
      (indent, f, op, t) = data
      result = f'{indent}{f} {unesc(op)} {t}'
      break

    if kind == 'atom':
      (indent, op, name, otype, features) = data
      opRep = '' if op is None else f'{unesc(op)} '
      nameRep = '' if name == '' else f'{name}:'
      featRep = unesc(features)
      if featRep:
        featRep = f' {featRep}'
      result = f'{indent}{opRep}{nameRep}{otype}{featRep}'
      break

    features = data[0]
    result = unesc(features)

  return result


def depLang(feature):
  if '@' not in feature:
    return None
  else:
    return feature.rsplit('@', 1)


def _cleanParent(atom, parentName):
  (kind, data) = _parseLine(atom)
  (indent, op, name, otype, features) = data
  if name == '':
    name = parentName
  return _genLine(kind, (indent, None, name, otype, features))


def _deContext(quantifier, parentName):
  (quKind, quTemplates) = quantifier

  # choose a name for the parent
  # either the given name
  if not parentName:
    # or make a new name
    # collect all used names
    # to avoid choosing a name that is already used
    usedNames = set()
    for template in quTemplates:
      for line in template:
        for name in namesRe.findall(line):
          usedNames.add(name)
    parentName = 'parent'
    while parentName in usedNames:
      parentName += 'x'

  newQuTemplates = []
  newQuantifier = (quKind, newQuTemplates, parentName)

  # replace .. (PARENT_REF) by parentName
  # wherever it is applicable
  for template in quTemplates:
    newLines = []
    for line in template:
      (kind, data) = _parseLine(line)
      newLine = line
      if kind == 'rel':
        (indent, f, op, t) = data
        if f == PARENT_REF or t == PARENT_REF:
          newF = parentName if f == PARENT_REF else f
          newT = parentName if t == PARENT_REF else t
          newData = (indent, newF, op, newT)
          newLine = _genLine(kind, newData)
      elif kind == 'atom':
        (indent, op, name, otype, features) = data
        if name == '' and otype == PARENT_REF:
          newData = (indent, op, name, parentName, features)
          newLine = _genLine(kind, newData)
      newLines.append(newLine)
    templateStr = '\n'.join(newLines)
    newQuTemplates.append(templateStr)
  return newQuantifier


def makeLimit(n, isLower):
  if isLower:
    return lambda x: x > n
  return lambda x: x < n


def esc(x):
  for (i, c) in enumerate(escapes):
    x = x.replace(c, chr(i))
  return x


def unesc(x):
  for (i, c) in enumerate(escapes):
    x = x.replace(chr(i), c[1])
  return x


# Search and SearchExe
#
# HIGH LEVEL description of the roles of Search and SerchExe
#
# SearchExe is the class that runs queries.
# SearchFactory is a class that creates SearchExe instances.
#
# The user is given the factory class as search api S.
#
# The (public) methods of the factory class has methods for searching.
# These methods work on a dedicated instance of SearchExe
# within the factory class.
# The factory class will create this instance when needed.
#
# A reference to the factory class Search is stored in the SearchExe objects.
# This gives the SearchExe objects the possibility to create other
# SearchExe objects to perform auxiliary queries.
# This is needed to run the queries implied by
# quantifiers in the search template.
#
# The search processes done by distinct SearchExe objects do not interfere.
#
# Summarizing: the factory class Search looks to the user like the execution
# class # SearchExe.
# But under the hood, different queries are always performed on different
# instances of SearchExe.

# LOW LEVEL description of the roles of Search and SerchExe
#
# In order to search, you have to create an instance of the SearchExe class.
# This instance contains all parameters and settings relevant to the search.
#
# The factory Search may contain one instance of a SearchExe.
#
# The factory class Search has methods study() and search(),
# which create a SearchExe instance and store it inside the Search.
# After that they call methods with the same name on that SearchExe object.
#
# The factory class Search has methods fetch(), count(), showPlan().
# These call mehtods with the same name on the SearchExe instance stored in
# the factory class Search, if it has been created earlier
# by search() or study().
# If not, an error message is displayed.
#
# All the work involved in searching is performed by the SearchExe object.
# The data of a SearchExe object are tied to a particular search:
# searchTemplate, sets, shallow, silent.
# This also holds for all data that is created during executions of a query:
# qnodes, qedges, results, etc.


class Search(object):
  def __init__(self, api, silent):
    self.api = api
    self.silent = silent
    self.exe = None

  def search(
      self,
      searchTemplate,
      limit=None,
      sets=None,
      shallow=False,
      silent=True,
      here=True,
      withContext=None,
  ):
    exe = SearchExe(
        self.api,
        searchTemplate,
        sets=sets,
        shallow=shallow,
        silent=silent,
        withContext=withContext,
    )
    if here:
      self.exe = exe
    return exe.search(limit=limit)

  def study(
      self,
      searchTemplate,
      strategy=None,
      sets=None,
      shallow=False,
      here=True,
  ):
    exe = SearchExe(
        self.api,
        searchTemplate,
        sets=sets,
        shallow=shallow,
        silent=False,
        showQuantifiers=True,
    )
    if here:
      self.exe = exe
    return exe.study(strategy=strategy)

  def fetch(self, limit=None):
    exe = self.exe
    if exe is None:
      error = self.api.error
      error('Cannot fetch if there is no previous "study()"')
    else:
      return exe.fetch(limit=limit)

  def count(self, progress=None, limit=None):
    exe = self.exe
    if exe is None:
      error = self.api.error
      error('Cannot count if there is no previous "study()"')
    else:
      exe.count(progress=progress, limit=limit)

  def showPlan(self, details=False):
    exe = self.exe
    if exe is None:
      error = self.api.error
      error('Cannot show plan if there is no previous "study()"')
    else:
      exe.showPlan(details=details)

  def relationsLegend(self):
    exe = self.exe
    if exe is None:
      exe = SearchExe(self.api, '')
    print(exe.relationLegend)

  def glean(self, r):
    T = self.api.T
    F = self.api.F
    L = self.api.L
    slotType = F.otype.slotType
    lR = len(r)
    if lR == 0:
      return ''
    fields = []
    for (i, n) in enumerate(r):
      otype = F.otype.v(n)
      words = [n] if otype == slotType else L.d(n, otype=slotType)
      if otype == T.sectionTypes[2]:
        field = '{} {}:{}'.format(*T.sectionFromNode(n))
      elif otype == slotType:
        field = T.text(words)
      elif otype in T.sectionTypes[0:2]:
        field = ''
      else:
        field = '{}[{}{}]'.format(
            otype,
            T.text(words[0:5]),
            '...' if len(words) > 5 else '',
        )
      fields.append(field)
    return ' '.join(fields)


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
  ):
    self.api = api
    self.searchTemplate = searchTemplate
    self.level = level
    self.sets = sets
    self.shallow = 0 if not shallow else 1 if shallow is True else shallow
    self.silent = silent
    self.showQuantifiers = showQuantifiers
    self.context = withContext
    self.good = True
    self._basicRelations()

# API METHODS ###

  def search(self, limit=None):
    self.silent = True
    self.study()
    return self.fetch(limit=limit)

  def study(self, strategy=None):
    info = self.api.info
    self.api.indent(level=0, reset=True)
    self.good = True

    self._setStrategy(strategy)
    if not self.good:
      return

    if not self.silent:
      info('Checking search template ...')

    self._parse()
    self._prepare()
    if not self.good:
      return
    if not self.silent:
      info(f'Setting up search space for {len(self.qnodes)} objects ...')
    self._spinAtoms()
    if not self.silent:
      info(f'Constraining search space with {len(self.qedges)} relations ...')
    self._spinEdges()
    if not self.silent:
      info('Setting up retrieval plan ...')
    self._stitch()
    if self.good:
      if not self.silent:
        yarnContent = sum(len(y) for y in self.yarns.values())
        info(f'Ready to deliver results from {yarnContent} nodes')
      if not self.silent:
        info('Iterate over S.fetch() to get the results', tm=False)
      if not self.silent:
        info('See S.showPlan() to interpret the results', tm=False)

  def fetch(self, limit=None):
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
      context = self._gatherContext(queryResults)
      return (queryResults, context)
    else:
      return queryResults

  def count(self, progress=None, limit=None):
    info = self.api.info
    error = self.api.error
    indent = self.api.indent
    indent(level=0, reset=True)

    if not self.good:
      error('This search has problems. No results to count.', tm=False)
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
        )
    )
    indent(level=1, reset=True)

    i = 0
    j = 0
    for r in self.results(remap=False):
      i += 1
      j += 1
      if j == progress:
        j = 0
        info(i)
      if limit > 0 and i >= limit:
        break

    indent(level=0)
    info(f'Done: {i} results')

  def showPlan(self, details=False):
    if not self.good:
      return
    info = self.api.info
    nodeLine = self.nodeLine
    qedges = self.qedges
    (qs, es) = self.stitchPlan
    if details:
      info(f'Search with {len(qs)} objects and {len(es)} relations', tm=False)
      info('Results are instantiations of the following objects:', tm=False)
      for q in qs:
        self._showNode(q)
      if len(es) != 0:
        info('Instantiations are computed along the following relations:', tm=False)
        (firstE, firstDir) = es[0]
        (f, rela, t) = qedges[firstE]
        if firstDir == -1:
          (f, t) = (t, f)
        self._showNode(f, pos2=True)
        for e in es:
          self._showEdge(*e)
    info('The results are connected to the original search template as follows:')

    resultNode = {}
    for q in qs:
      resultNode[nodeLine[q]] = q
    for (i, line) in enumerate(self.searchLines):
      rNode = resultNode.get(i, '')
      prefix = '' if rNode == '' else 'R'
      info(f'{i:>2} {prefix:<1}{rNode:<2} {line}', tm=False)

# LOW-LEVEL NODE RELATIONS SEMANTICS ###

  def _basicRelations(self):
    C = self.api.C
    F = self.api.F
    E = self.api.E
    Crank = C.rank.data
    ClevDown = C.levDown.data
    ClevUp = C.levUp.data
    (CfirstSlots, ClastSlots) = C.boundary.data
    Eoslots = E.oslots.data
    slotType = F.otype.slotType
    maxSlot = F.otype.maxSlot

    def equalR(fTp, tTp):
      return lambda n: (n, )

    def spinEqual(fTp, tTp):
      def doyarns(yF, yT):
        x = set(yF) & set(yT)
        return (x, x)

      return doyarns

    def unequalR(fTp, tTp):
      return lambda n, m: n != m

    def canonicalBeforeR(fTp, tTp):
      return lambda n, m: Crank[n - 1] < Crank[m - 1]

    def canonicalAfterR(fTp, tTp):
      return lambda n, m: Crank[n - 1] > Crank[m - 1]

    def spinSameSlots(fTp, tTp):
      if fTp == slotType and tTp == slotType:

        def doyarns(yF, yT):
          x = set(yF) & set(yT)
          return (x, x)

        return doyarns
      elif fTp == slotType or tTp == slotType:

        def doyarns(yS, y2):
          sindex = {}
          for m in y2:
            ss = Eoslots[m - maxSlot - 1]
            if len(ss) == 1:
              sindex.setdefault(ss[0], set()).add(m)
          nyS = yS & set(sindex.keys())
          ny2 = reduce(
              set.union,
              (sindex[s] for s in nyS),
              set(),
          )
          return (nyS, ny2)

        if fTp == slotType:
          return doyarns
        else:

          def xx(yF, yT):
            (nyT, nyF) = doyarns(yT, yF)
            return (nyF, nyT)

          return xx
      else:

        def doyarns(yF, yT):
          sindexF = {}
          for n in yF:
            s = frozenset(Eoslots[n - maxSlot - 1])
            sindexF.setdefault(s, set()).add(n)
          sindexT = {}
          for m in yT:
            s = frozenset(Eoslots[m - maxSlot - 1])
            sindexT.setdefault(s, set()).add(m)
          nyS = set(sindexF.keys()) & set(sindexT.keys())
          nyF = reduce(
              set.union,
              (sindexF[s] for s in nyS),
              set(),
          )
          nyT = reduce(
              set.union,
              (sindexT[s] for s in nyS),
              set(),
          )
          return (nyF, nyT)

        return doyarns

    def sameSlotsR(fTp, tTp):
      if fTp == slotType and tTp == slotType:
        return lambda n: (n, )
      elif tTp == slotType:
        return lambda n, m: Eoslots[n - maxSlot - 1] == (m, )
      elif fTp == slotType:
        return lambda n, m: Eoslots[m - maxSlot - 1] == (n, )
      else:
        return (
            lambda n, m: (
                frozenset(Eoslots[n - maxSlot - 1]) ==
                frozenset(Eoslots[m - maxSlot - 1])
            )
        )

    def spinOverlap(fTp, tTp):
      if fTp == slotType and tTp == slotType:

        def doyarns(yF, yT):
          x = set(yF) & set(yT)
          return (x, x)

        return doyarns
      elif fTp == slotType or tTp == slotType:

        def doyarns(yS, y2):
          sindex = {}
          for m in y2:
            for s in Eoslots[m - maxSlot - 1]:
              sindex.setdefault(s, set()).add(m)
          nyS = yS & set(sindex.keys())
          ny2 = reduce(
              set.union,
              (sindex[s] for s in nyS),
              set(),
          )
          return (nyS, ny2)

        if fTp == slotType:
          return doyarns
        else:

          def xx(yF, yT):
            (nyT, nyF) = doyarns(yT, yF)
            return (nyF, nyT)

          return xx
      else:

        def doyarns(yF, yT):
          REDUCE_FACTOR = 0.4
          SIZE_LIMIT = 10000
          sindexF = {}
          for n in yF:
            for s in Eoslots[n - maxSlot - 1]:
              sindexF.setdefault(s, set()).add(n)
          sindexT = {}
          for m in yT:
            for s in Eoslots[m - maxSlot - 1]:
              sindexT.setdefault(s, set()).add(m)
          nyS = set(sindexF.keys()) & set(sindexT.keys())

          lsF = len(sindexF)
          lsT = len(sindexT)
          lsI = len(nyS)
          if lsF == lsT:  # spinning is completely useless
            return (yF, yT)
          if lsI > REDUCE_FACTOR * lsT and lsT > SIZE_LIMIT:
            # spinning is not worth it
            return (yF, yT)

          if not self.silent:
            self.api.info(f'1. reducing over {len(nyS)} elements')
          nyF = reduce(
              set.union,
              (sindexF[s] for s in nyS),
              set(),
          )
          if not self.silent:
            self.api.info(f'2. reducing over {len(nyS)} elements')
          nyT = reduce(
              set.union,
              (sindexT[s] for s in nyS),
              set(),
          )
          return (nyF, nyT)

        return doyarns

    def overlapR(fTp, tTp):
      if fTp == slotType and tTp == slotType:
        return lambda n: (n, )
      elif tTp == slotType:
        return lambda n: Eoslots[n - maxSlot - 1]
      elif fTp == slotType:
        return lambda n, m: n in frozenset(Eoslots[m - maxSlot - 1])
      else:
        return (
            lambda n, m: (
                len(frozenset(Eoslots[n - maxSlot - 1]) &
                    frozenset(Eoslots[m - maxSlot - 1])) != 0
            )
        )

    def diffSlotsR(fTp, tTp):
      if fTp == slotType and tTp == slotType:
        return lambda n, m: m != n
      elif tTp == slotType:
        return lambda n, m: Eoslots[m - maxSlot - 1] != (n, )
      elif fTp == slotType:
        return lambda n, m: Eoslots[n - maxSlot - 1] != (m, )
      else:
        return (
            lambda n, m: (
                frozenset(Eoslots[n - maxSlot - 1]) !=
                frozenset(Eoslots[m - maxSlot - 1])
            )
        )

    def disjointSlotsR(fTp, tTp):
      if fTp == slotType and tTp == slotType:
        return lambda n, m: m != n
      elif tTp == slotType:
        return lambda n, m: m not in frozenset(Eoslots[n - maxSlot - 1])
      elif fTp == slotType:
        return lambda n, m: n not in frozenset(Eoslots[m - maxSlot - 1])
      else:
        return (
            lambda n, m: (
                len(frozenset(Eoslots[n - maxSlot - 1]) &
                    frozenset(Eoslots[m - maxSlot - 1])) == 0
            )
        )

    def inR(fTp, tTp):
      if fTp == slotType and tTp == slotType:
        return lambda n: ()
      elif tTp == slotType:
        return lambda n: ()
      elif fTp == slotType:
        return lambda n: ClevUp[n - 1]
      else:
        return lambda n: ClevUp[n - 1]

    def hasR(fTp, tTp):
      if fTp == slotType and tTp == slotType:
        return lambda n: ()
      elif fTp == slotType:
        return lambda n: ()
      elif tTp == slotType:
        return lambda n: Eoslots[n - maxSlot - 1]
      else:
        return lambda n: ClevDown[n - maxSlot - 1]

    def slotBeforeR(fTp, tTp):
      if fTp == slotType and tTp == slotType:
        return lambda n, m: n < m
      elif fTp == slotType:
        return lambda n, m: n < Eoslots[m - maxSlot - 1][0]
      elif tTp == slotType:
        return lambda n, m: Eoslots[n - maxSlot - 1][-1] < m
      else:
        return (lambda n, m: (Eoslots[n - maxSlot - 1][-1] < Eoslots[m - maxSlot - 1][0]))

    def slotAfterR(fTp, tTp):
      if fTp == slotType and tTp == slotType:
        return lambda n, m: n > m
      elif fTp == slotType:
        return lambda n, m: n > Eoslots[m - maxSlot - 1][-1]
      elif tTp == slotType:
        return lambda n, m: Eoslots[n - maxSlot - 1][0] > m
      else:
        return (lambda n, m: (Eoslots[n - maxSlot - 1][0] > Eoslots[m - maxSlot - 1][-1]))

    def sameFirstSlotR(fTp, tTp):
      if fTp == slotType and tTp == slotType:
        return lambda n: (n, )
      elif fTp == slotType:
        return lambda n: CfirstSlots[n - 1]
      elif tTp == slotType:
        return lambda n: (Eoslots[n - maxSlot - 1][0], )
      else:

        def xx(n):
          fn = Eoslots[n - maxSlot - 1][0]
          return CfirstSlots[fn - 1]

        return xx

    def sameLastSlotR(fTp, tTp):
      if fTp == slotType and tTp == slotType:
        return lambda n: (n, )
      elif fTp == slotType:
        return lambda n: ClastSlots[n - 1]
      elif tTp == slotType:
        return lambda n: (Eoslots[n - maxSlot - 1][-1], )
      else:

        def xx(n):
          ln = Eoslots[n - maxSlot - 1][-1]
          return ClastSlots[ln - 1]

        return xx

    def sameBoundaryR(fTp, tTp):
      if fTp == slotType and tTp == slotType:
        return lambda n: (n, )
      elif fTp == slotType:

        def xx(n):
          fok = set(CfirstSlots[n - 1])
          lok = set(ClastSlots[n - 1])
          return tuple(fok & lok)

        return xx
      elif tTp == slotType:

        def xx(n):
          slots = Eoslots[n - maxSlot - 1]
          fs = slots[0]
          ls = slots[-1]
          return (fs, ) if fs == ls else ()

        return xx
      else:

        def xx(n):
          fn = Eoslots[n - maxSlot - 1][0]
          ln = Eoslots[n - maxSlot - 1][-1]
          fok = set(CfirstSlots[fn - 1])
          lok = set(ClastSlots[ln - 1])
          return tuple(fok & lok)

        return xx

    def nearFirstSlotR(k):
      def zz(fTp, tTp):
        if fTp == slotType and tTp == slotType:
          return lambda n: tuple(m for m in range(max((1, n - k)), min((maxSlot, n + k + 1))))
        elif fTp == slotType:

          def xx(n):
            near = set(l for l in range(max((1, n - k)), min((maxSlot, n + k + 1))))
            return tuple(reduce(
                set.union,
                (set(CfirstSlots[l - 1]) for l in near),
                set(),
            ))

          return xx
        elif tTp == slotType:

          def xx(n):
            fn = Eoslots[n - maxSlot - 1][0]
            return tuple(m for m in range(max((1, fn - k)), min((maxSlot, fn + k + 1))))

          return xx
        else:

          def xx(n):
            fn = Eoslots[n - maxSlot - 1][0]
            near = set(l for l in range(max((1, fn - k)), min((maxSlot, fn + k + 1))))
            return tuple(reduce(
                set.union,
                (set(CfirstSlots[l - 1]) for l in near),
                set(),
            ))

          return xx

      return zz

    def nearLastSlotR(k):
      def zz(fTp, tTp):
        if fTp == slotType and tTp == slotType:
          return lambda n: tuple(m for m in range(max((1, n - k)), min((maxSlot, n + k + 1))))
        elif fTp == slotType:

          def xx(n):
            near = set(l for l in range(max((1, n - k)), min((maxSlot, n + k + 1))))
            return tuple(reduce(
                set.union,
                (set(ClastSlots[l - 1]) for l in near),
                set(),
            ))

          return xx
        elif tTp == slotType:

          def xx(n):
            ln = Eoslots[n - maxSlot - 1][-1]
            return tuple(m for m in range(max((1, ln - k)), min((maxSlot, ln + k + 1))))

          return xx
        else:

          def xx(n):
            ln = Eoslots[n - maxSlot - 1][-1]
            near = set(l for l in range(max((1, ln - k)), min((maxSlot, ln + k + 1))))
            return tuple(reduce(
                set.union,
                (set(ClastSlots[l - 1]) for l in near),
                set(),
            ))

          return xx

      return zz

    def nearBoundaryR(k):
      def zz(fTp, tTp):
        if fTp == slotType and tTp == slotType:
          return lambda n: tuple(m for m in range(max((1, n - k)), min((maxSlot, n + k + 1))))
        elif fTp == slotType:

          def xx(n):
            near = set(l for l in range(max((1, n - k)), min((maxSlot, n + k + 1))))
            fok = set(reduce(
                set.union,
                (set(CfirstSlots[l - 1]) for l in near),
                set(),
            ))
            lok = set(reduce(
                set.union,
                (set(ClastSlots[l - 1]) for l in near),
                set(),
            ))
            return tuple(fok & lok)

          return xx
        elif tTp == slotType:

          def xx(n):
            slots = Eoslots[n - maxSlot - 1]
            fs = slots[0]
            ls = slots[-1]
            fok = set(m for m in range(max((1, fs - k)), min((maxSlot, fs + k + 1))))
            lok = set(m for m in range(max((1, ls - k)), min((maxSlot, ls + k + 1))))
            return tuple(fok & lok)

          return xx
        else:

          def xx(n):
            fn = Eoslots[n - maxSlot - 1][0]
            ln = Eoslots[n - maxSlot - 1][-1]
            nearf = set(ls for ls in range(max((1, fn - k)), min((maxSlot, fn + k + 1))))
            nearl = set(ls for ls in range(max((1, ln - k)), min((maxSlot, ln + k + 1))))
            fok = set(CfirstSlots[fn - 1])
            lok = set(ClastSlots[ln - 1])
            fok = set(reduce(
                set.union,
                (set(CfirstSlots[ls - 1]) for ls in nearf),
                set(),
            ))
            lok = set(reduce(
                set.union,
                (set(ClastSlots[ls - 1]) for ls in nearl),
                set(),
            ))
            return tuple(fok & lok)

          return xx

      return zz

    def adjBeforeR(fTp, tTp):
      if fTp == slotType and tTp == slotType:
        return lambda n: (n + 1, ) if n < maxSlot else ()
      else:

        def xx(n):
          if n == maxSlot:
            return ()
          myNext = n + 1 if n < maxSlot else Eoslots[n - maxSlot - 1][-1] + 1
          if myNext > maxSlot:
            return ()
          return CfirstSlots[myNext - 1] + (myNext, )

        return xx

    def adjAfterR(fTp, tTp):
      if fTp == slotType and tTp == slotType:
        return lambda n: (n - 1, ) if n > 1 else ()
      else:

        def xx(n):
          if n <= 1:
            return ()
          myPrev = n - 1 if n < maxSlot else Eoslots[n - maxSlot - 1][0] - 1
          if myPrev <= 1:
            return ()
          return (myPrev, ) + ClastSlots[myPrev - 1]

        return xx

    def nearBeforeR(k):
      def zz(fTp, tTp):
        if fTp == slotType and tTp == slotType:
          return lambda n: tuple(
              m for m in
              range(max((1, n + 1 - k)), min((maxSlot, n + 1 + k + 1)))
          )
        else:

          def xx(n):
            myNext = n + 1 if n < maxSlot else Eoslots[n - maxSlot - 1][-1] + 1
            myNextNear = tuple(
                ls for ls in range(max((1, myNext - k)), min((maxSlot, myNext + k + 1)))
            )
            nextSet = set(
                reduce(
                    set.union,
                    (set(CfirstSlots[ls - 1]) for ls in myNextNear),
                    set(),
                )
            )
            return tuple(nextSet) + myNextNear

          return xx

      return zz

    def nearAfterR(k):
      def zz(fTp, tTp):
        if fTp == slotType and tTp == slotType:
          return lambda n: tuple(
              m for m in
              range(max((1, n - 1 - k)), min((maxSlot, n - 1 + k + 1)))
          )
        else:

          def xx(n):
            myPrev = n - 1 if n < maxSlot else Eoslots[n - maxSlot - 1][0] - 1
            myPrevNear = tuple(
                l for l in range(max((1, myPrev - k)), min((maxSlot, myPrev + k + 1)))
            )
            prevSet = set(reduce(
                set.union,
                (set(ClastSlots[l - 1]) for l in myPrevNear),
                set(),
            ))
            return tuple(prevSet) + myPrevNear

          return xx

      return zz

    def makeEdgeMaps(efName):
      def edgeAccess(eFunc, doValues, value):
        if doValues:
          if value is None:
            return lambda n: tuple(m[0] for m in eFunc(n) if m[1] is None)
          elif value is True:
            return lambda n: tuple(m[0] for m in eFunc(n))
          elif isinstance(value, types.FunctionType):
            return lambda n: tuple(m[0] for m in eFunc(n) if value(m[1]))
          elif isinstance(value, reTp):
            return lambda n: tuple(
                m[0] for m in eFunc(n)
                if value is not None and value.search(m[1])
            )
          else:
            (ident, value) = value
            if ident:
              return lambda n: tuple(m[0] for m in eFunc(n) if m[1] in value)
            else:
              return lambda n: tuple(m[0] for m in eFunc(n) if m[1] not in value)
        else:
          return lambda n: eFunc(n)

      def edgeRV(value):
        def edgeR(fTp, tTp):
          Es = self.api.Es
          Edata = Es(efName)
          doValues = Edata.doValues
          return edgeAccess(Edata.f, doValues, value)

        return edgeR

      def edgeIRV(value):
        def edgeIR(fTp, tTp):
          Es = self.api.Es
          Edata = Es(efName)
          doValues = Edata.doValues
          return edgeAccess(Edata.t, doValues, value)

        return edgeIR

      return (edgeRV, edgeIRV)

    relations = [
        (
            ('=', spinEqual, equalR, 'left equal to right (as node)'),
            ('=', spinEqual, equalR, None),
        ),
        (
            ('#', 0.999, unequalR, 'left unequal to right (as node)'),
            ('#', 0.999, unequalR, None),
        ),
        (
            ('<', 0.500, canonicalBeforeR, 'left before right (in canonical node ordering)'),
            ('>', 0.500, canonicalAfterR, 'left after right (in canonical node ordering)'),
        ),
        (
            ('==', spinSameSlots, sameSlotsR, 'left occupies same slots as right'),
            ('==', spinSameSlots, sameSlotsR, None),
        ),
        (
            ('&&', spinOverlap, overlapR, 'left has overlapping slots with right'),
            ('&&', spinOverlap, overlapR, None),
        ),
        (
            ('##', 0.990, diffSlotsR, 'left and right do not have the same slot set'),
            ('##', 0.990, diffSlotsR, None),
        ),
        (
            ('||', 0.900, disjointSlotsR, 'left and right do not have common slots'),
            ('||', 0.900, disjointSlotsR, None),
        ),
        (
            ('[[', True, hasR, 'left embeds right'),
            (']]', True, inR, 'left embedded in right'),
        ),
        (
            ('<<', 0.490, slotBeforeR, 'left completely before right'),
            ('>>', 0.490, slotAfterR, 'left completely after right'),
        ),
        (
            ('=:', True, sameFirstSlotR, 'left and right start at the same slot'),
            ('=:', True, sameFirstSlotR, None),
        ),
        (
            (':=', True, sameLastSlotR, 'left and right end at the same slot'),
            (':=', True, sameLastSlotR, None),
        ),
        (
            ('::', True, sameBoundaryR, 'left and right start and end at the same slot'),
            ('::', True, sameBoundaryR, None),
        ),
        (
            ('<:', True, adjBeforeR, 'left immediately before right'),
            (':>', True, adjAfterR, 'left immediately after right'),
        ),
        (
            ('=k:', True, nearFirstSlotR, 'left and right start at k-nearly the same slot'),
            ('=k:', True, nearFirstSlotR, None),
        ),
        (
            (':k=', True, nearLastSlotR, 'left and right end at k-nearly the same slot'),
            (':k=', True, nearLastSlotR, None),
        ),
        (
            (':k:', True, nearBoundaryR, 'left and right start and end at k-near slots'),
            (':k:', True, nearBoundaryR, None),
        ),
        (
            ('<k:', True, nearBeforeR, 'left k-nearly before right'),
            (':k>', True, nearAfterR, 'left k-nearly after right'),
        ),
    ]

    self.api.TF.explore(silent=self.silent)
    edgeMap = {}

    for efName in sorted(self.api.TF.featureSets['edges']):
      if efName == WARP[1]:
        continue
      r = len(relations)

      (edgeRV, edgeIRV) = makeEdgeMaps(efName)
      doValues = self.api.TF.features[efName].edgeValues
      extra = ' with value specification allowed' if doValues else ''
      relations.append((
          (f'-{efName}>', True, edgeRV, f'edge feature "{efName}"{extra}'),
          (f'<{efName}-', True, edgeIRV, f'edge feature "{efName}"{extra} (opposite direction)'),
      ))
      edgeMap[2 * r] = (efName, 1)
      edgeMap[2 * r + 1] = (efName, -1)
    lr = len(relations)

    relationsAll = []
    for (r, rc) in relations:
      relationsAll.extend([r, rc])

    self.relations = [dict(
        acro=r[0],
        spin=r[1],
        func=r[2],
        desc=r[3],
    ) for r in relationsAll]
    self.relationFromName = dict(((r['acro'], i) for (i, r) in enumerate(self.relations)))
    self.relationLegend = '\n'.join(
        f'{r["acro"]:>23} {r["desc"]}' for r in self.relations if r['desc'] is not None
    )
    self.relationLegend += f'''
The warp feature "{WARP[1]}" cannot be used in searches.
One of the above relations on nodes and/or slots will suit you better.
'''
    self.converse = dict(
        tuple((2 * i, 2 * i + 1) for i in range(lr)) + tuple((2 * i + 1, 2 * i) for i in range(lr))
    )
    self.edgeMap = edgeMap

  def _add_K_Relations(self, varRels):
    relations = self.relations
    tasks = collections.defaultdict(set)
    for (acro, ks) in varRels.items():
      j = self.relationFromName[acro]
      ji = self.converse[j]
      if ji < j:
        (j, ji) = (ji, j)
      acro = relations[j]['acro']
      acroi = relations[ji]['acro']
      tasks[(j, acro, ji, acroi)] |= ks

    for ((j, acro, ji, acroi), ks) in tasks.items():
      for k in ks:
        newAcro = acro.replace('k', str(k))
        newAcroi = acroi.replace('k', str(k))
        r = relations[j]
        ri = relations[ji]
        lr = len(relations)
        relations.extend([
            dict(
                acro=newAcro,
                spin=r['spin'],
                func=r['func'](k),
                desc=r['desc'],
            ),
            dict(
                acro=newAcroi,
                spin=ri['spin'],
                func=ri['func'](k),
                desc=ri['desc'],
            ),
        ])
        self.relationFromName[newAcro] = lr
        self.relationFromName[newAcroi] = lr + 1
        self.converse[lr] = lr + 1
        self.converse[lr + 1] = lr

  def _add_V_Relations(self, varRels):
    relations = self.relations
    tasks = collections.defaultdict(set)
    for (acro, vals) in sorted(varRels.items()):
      for (eName, val) in vals:
        conv = acro[0] == '<'
        eRel = f'-{eName}>'
        eReli = f'<{eName}-'
        acroi = f'-{acro[1:-1]}>' if conv else f'<{acro[1:-1]}-'
        if conv:
          (acro, acroi) = (acroi, acro)
        j = self.relationFromName[eRel]
        ji = self.relationFromName[eReli]
        tasks[(eName, j, acro, ji, acroi)].add(val)

    for ((eName, j, acro, ji, acroi), vals) in sorted(tasks.items()):
      for val in vals:
        r = relations[j]
        ri = relations[ji]
        lr = len(relations)
        relations.extend([
            dict(
                acro=acro,
                spin=r['spin'],
                func=r['func'](val),
                desc=r['desc'],
            ),
            dict(
                acro=acroi,
                spin=ri['spin'],
                func=ri['func'](val),
                desc=ri['desc'],
            ),
        ])
        self.relationFromName[acro] = lr
        self.relationFromName[acroi] = lr + 1
        self.edgeMap[lr] = (eName, 1)
        self.edgeMap[lr + 1] = (eName, -1)
        self.converse[lr] = lr + 1
        self.converse[lr + 1] = lr

# SYNTACTIC ANALYSIS OF SEARCH TEMPLATE ###

  def _parseFeatureVals(self, featStr, features, i, asEdge=False):
    if asEdge:
      if not ((featStr[0] == '-' and featStr[-1] == '>') or
              (featStr[0] == '<' and featStr[-1] == '-')):
        return True
      feat = featStr[1:-1]
    else:
      feat = featStr.replace(chr(1), ' ')
    good = True
    for x in [True]:
      match = noneRe.match(feat)
      if match:
        (featN, unequal) = match.groups()
        featName = unesc(featN)
        featVals = None if unequal else True
        break
      match = identRe.match(feat)
      if match:
        (featN, comp, featValStr) = match.groups()
        featName = unesc(featN)
        featValSet = frozenset(unesc(featVal) for featVal in featValStr.split('|'))
        featVals = (comp == '=', featValSet)
        break
      match = compRe.match(feat)
      if match:
        (featN, comp, limit) = match.groups()
        featName = unesc(featN)
        if not numRe.match(limit):
          self.badSyntax.append(f'Limit is non numeric "{limit}" in line {i}')
          good = False
          featVals = None
        else:
          featVals = makeLimit(int(limit), comp == '>')
        break
      match = reRe.match(feat)
      if match:
        (featN, valRe) = match.groups()
        featName = unesc(featN)
        try:
          featVals = re.compile(valRe)
        except Exception() as err:
          self.badSyntax.append(f'Wrong regular expression "{valRe}" in line {i}: "{err}"')
          good = False
          featVals = None
        break
      self.badSyntax.append(f'Unrecognized feature condition "{feat}" in line {i}')
      good = False
      featVals = None
    if good:
      features[featName] = featVals
    return good

  def _tokenize(self):
    if not self.good:
      return

    def getFeatures(x, i):
      features = {}
      featureString = x.replace('\\ ', chr(1)) if x is not None else ''
      featureList = featureString.split()
      good = True
      for featStr in featureList:
        if not self._parseFeatureVals(featStr, features, i):
          good = False
      return features if good else None

    searchLines = self.searchLines
    tokens = []
    allGood = True

    # the template may contain nested quantifiers
    # However, we detect only the outer level of quantifiers.
    # Everything contained in a quantifiers is collected in
    # a new search template, verbatim, without interpretion,
    # because it will be fed to search() on another instance.
    # We only strip the quantified lines of the outermost quantifiers.

    # We can maintain the current quantifier, None if there is none.
    # We also remember the current indentation of the current quantifier
    # We collect the templates within the quantifier in a list of strings.
    # We add all the material into a quantifier token of the shape
    #
    # Because indentation is not indicative of quantifier nesting
    # we need to maintain a stack of inner quantifiers,
    # just to be able to determine wich quantifier words
    # belong to the outerlevel quantifiers.

    curQu = []
    curQuTemplates = None

    for (i, line) in enumerate(searchLines):
      if line.startswith('#') or whiteRe.match(line):
        continue
      opFeatures = {}

      # first check whether we have a line with a quantifier
      # and what the indent on the line is

      match = quLineRe.match(line)
      if match:
        (indent, lineQuKind) = match.groups()
      else:
        lineQuKind = None
        match = indentLineRe.match(line)
        indent = match.group(1)

      lineIndent = len(indent)

      # QUANTIFIER FILTERING
      #
      # now check whether we are in a quantifier or not
      # and determine whether a quantifier starts or ends here

      # we have the following possible situations:
      #
      # UUO no outer              - no q-keyword
      #
      # UBO no outer              - q-keyword
      #     * ES no start keyword
      #     * ET no preceding token
      #     * EA no preceding atom
      #     * EI preceding atom not the same indentation
      #
      # PBI outer                 - q-keyword init
      #
      # PPO outer                 - no q-keyword
      #
      # PPI inner                 - no q-keyword
      #
      # PCO outer                 - q-keyword continue
      #     * EP wrong precursor
      #     * EK preceding keyword not the same indentation
      #
      # PCI inner                 - q-keyword continue
      #     * EP wrong precursor
      #     * EK preceding keyword not the same indentation
      #
      # PEO outer                 - q-keyword end
      #     * EP wrong precursor
      #     * EK preceding keyword not the same indentation
      #
      # PEI inner                 - q-keyword end
      #     * EP wrong precursor
      #     * EK preceding keyword not the same indentation
      #
      # at the end we may have a non-empty quantifier stack:
      #     * generate an unterminated quantifier error for each member
      #       of the stack

      # first we determine what is the case and we store it in booleans

      curQuLine = None
      curQuKind = None
      curQuIndent = None
      curQuDepth = len(curQu)
      if curQuDepth:
        (curQuLine, curQuKind, curQuIndent) = curQu[-1]

      UUO = not curQuDepth and not lineQuKind
      UBO = not curQuDepth and lineQuKind
      PBI = curQuDepth and lineQuKind in QINIT
      PPO = curQuDepth == 1 and not lineQuKind
      PPI = curQuDepth > 1 and not lineQuKind
      PCO = curQuDepth == 1 and lineQuKind in QCONT
      PCI = curQuDepth > 1 and lineQuKind in QCONT
      PEO = curQuDepth == 1 and lineQuKind in QTERM
      PEI = curQuDepth > 1 and lineQuKind in QTERM

      (ES, ET, EA, EI, EP, EK) = (False, ) * 6

      if UBO:
        ES = lineQuKind not in QINIT
        ET = len(tokens) == 0
        EA = (len(tokens) and tokens[-1]['kind'] != 'atom' and 'otype' not in tokens[-1])
        EI = (len(tokens) and tokens[-1]['indent'] != lineIndent)

      if PCO or PCI:
        EP = ((lineQuKind == QHAVE and curQuKind != QWHERE)
              or (lineQuKind == QOR and curQuKind not in {QWITH, QOR}))
        EK = curQu[-1][2] != lineIndent

      if PEO or PEI:
        EP = curQuKind in {QWHERE}
        EK = curQu[-1][2] != lineIndent

      # QUANTIFIER HANDLING
      #
      # Based on what is the case, we take actions.
      # * we swallow quantified templates
      # * we handle quantifier lines
      # * we let all other lines pass through

      good = True

      for x in [True]:
        if UUO:
          # no quantifier business
          continue
        if UBO:
          # start new quantifier from nothing
          if ES:
            self.badSyntax.append(f'Quantifier at line {i}: Can not start with "{lineQuKind}:"')
            good = False
          if ET:
            self.badSyntax.append(f'Quantifier at line {i}: No preceding tokens')
            good = False
          if EA or EI:
            self.badSyntax.append(
                f'Quantifier at line {i}: Does not immediately follow an atom at the same level'
            )
            good = False
          prevAtom = tokens[-1]
          curQu.append((i, lineQuKind, lineIndent))
          curQuTemplates = [[]]
          quantifiers = prevAtom.setdefault('quantifiers', [])
          quantifiers.append((lineQuKind, curQuTemplates))
          continue
        if PBI:
          # start inner quantifier
          # lines are passed with stripped indentation
          # based on the outermost quantifier level
          outerIndent = curQu[0][2]
          strippedLine = line[outerIndent:]
          curQuTemplates[-1].append(strippedLine)
          curQu.append((i, lineQuKind, lineIndent))
        if PPO:
          # inside an outer quantifier
          # lines are passed with stripped indentation
          strippedLine = line[curQuIndent:]
          curQuTemplates[-1].append(strippedLine)
          continue
        if PPI:
          # inside an inner quantifier
          # lines are passed with stripped indentation
          # based on the outermost quantifier level
          outerIndent = curQu[0][2]
          strippedLine = line[outerIndent:]
          curQuTemplates[-1].append(strippedLine)
        if PCO or PCI:
          if EP:
            self.badSyntax.append(
                f'Quantifier at line {i}:'
                f' "{lineQuKind}" can not follow "{curQuKind}" on line {curQuLine}'
            )
            good = False
          if EK:
            self.badSyntax.append(
                f'Quantifier at line {i}:'
                f' "{lineQuKind}" has not same indentation as "{curQuKind}" on line {curQuLine}'
            )
            good = False
          if PCO:
            curQuTemplates.append([])
          else:
            outerIndent = curQu[0][2]
            strippedLine = line[outerIndent:]
            curQuTemplates[-1].append(strippedLine)
          curQu[-1] = (i, lineQuKind, lineIndent)
          continue
        if PEO or PEI:
          if EP:
            self.badSyntax.append(
                f'Quantifier at line {i}:'
                f' "{lineQuKind}": premature end of "{curQuKind}" on line {curQuLine}'
            )
            good = False
          if EK:
            self.badSyntax.append(
                f'Quantifier at line {i}:'
                f' "{lineQuKind}" has not same indentation as "{curQuKind}" on line {curQuLine}'
            )
            good = False
          if PEO:
            curQuTemplates = None
          else:
            outerIndent = curQu[0][2]
            strippedLine = line[outerIndent:]
            curQuTemplates[-1].append(strippedLine)
          curQu.pop()
          continue

      if not good:
        allGood = False

      if UUO:
        # go on with normal template tokenization
        pass
      else:
        # quantifiers stuff has been dealt with
        continue

      # QUANTIFIER FREE HANDLING

      good = False

      for x in [True]:
        (kind, data) = _parseLine(line)

        if kind == 'op':
          (indent, op) = data
          if not self._parseFeatureVals(op, opFeatures, i, asEdge=True):
            good = False
          else:
            if opFeatures:
              op = (op, opFeatures)
            tokens.append(dict(
                ln=i,
                kind='atom',
                indent=len(indent),
                op=op,
            ))
            good = True
          break

        if kind == 'rel':
          (indent, f, op, t) = data
          if not self._parseFeatureVals(op, opFeatures, i, asEdge=True):
            good = False
          else:
            if opFeatures:
              op = (op, opFeatures)
            tokens.append(dict(
                ln=i,
                kind='rel',
                f=f,
                op=op,
                t=t,
            ))
            good = True
          break

        if kind == 'atom':
          (indent, op, name, otype, features) = data
          good = True
          if name != '':
            mt = nameRe.match(name)
            if not mt:
              self.badSyntax.append(f'Illegal name at line {i}: "{name}"')
              good = False
          features = getFeatures(features, i)
          if features is None:
            good = False
          else:
            if op is not None:
              if not self._parseFeatureVals(op, opFeatures, i, asEdge=True):
                good = False
            if good:
              if opFeatures:
                op = (op, opFeatures)
              tokens.append(
                  dict(
                      ln=i,
                      kind='atom',
                      indent=len(indent),
                      op=op,
                      name=name,
                      otype=otype,
                      src=line.lstrip(),
                      features=features,
                  )
              )
          break

        if kind == 'feat':
          features = data[0]
          features = getFeatures(features, i)
          if features is None:
            good = False
          else:
            tokens.append(dict(
                ln=i,
                kind='feat',
                features=features,
            ))
            good = True
          break

        good = False
        self.badSyntax.append(f'Unrecognized line {i}: {line}')

      if not good:
        allGood = False

    if curQu:
      for (curQuLine, curQuKind, curQuIndent) in curQu:
        self.badSyntax.append(f'Quantifier at line {curQuLine}: Unterminated "{curQuKind}"')
      good = False
      allGood = False
    if allGood:
      self.tokens = tokens
    else:
      self.good = False

  def _syntax(self):
    error = self.api.error
    self.good = True
    self.badSyntax = []
    self.searchLines = self.searchTemplate.split('\n')
    self._tokenize()
    if not self.good:
      for (i, line) in enumerate(self.searchLines):
        error(f'{i:>2} {line}', tm=False)
      for eline in self.badSyntax:
        error(eline, tm=False)

# SEMANTIC ANALYSIS OF SEARCH TEMPLATE ###

  def _grammar(self):
    if not self.good:
      return

    prevKind = None
    good = True
    qnames = {}
    qnodes = []
    qedges = []
    edgeLine = {}
    nodeLine = {}
    nTokens = len(self.tokens)

    def tokenSort(t):
      return (nTokens + t['ln']) if t['kind'] == 'rel' else t['ln']

    tokens = sorted(self.tokens, key=tokenSort)

    # atomStack is a stack of qnodes with their indent levels
    # such that every next member is one level deeper
    # and every member is the last qnode encountered at that level
    # The stack is implemented as a dict,
    # keyed by the indent, and valued by the qnode
    atomStack = {}

    for token in tokens:
      i = token['ln']
      kind = token['kind']
      if kind == 'atom':
        if 'quantifiers' in token:
          token['quantifiers'] = [_deContext(q, token['name']) for q in token['quantifiers']]
        indent = token['indent']
        op = token['op']
        if 'name' in token:
          name = token['name']
          otype = token['otype']
          features = token['features']
          src = token.get('src', '')
          quantifiers = token.get('quantifiers', [])
          qnodes.append((otype, features, src, quantifiers))
          q = len(qnodes) - 1
          nodeLine[q] = i
          name = f':{i}' if name == '' else name
          qnames[name] = q
        if len(atomStack) == 0:
          if indent > 0:
            self.badSemantics.append(
                'Unexpected indent at line {}: {}, expected {}'.format(i, indent, 0)
            )
            good = False
          if op is not None:
            self.badSemantics.append(f'Lonely relation at line {i}: not allowed at outermost level')
            good = False
          if 'name' in token:
            atomStack[0] = q
        else:
          atomNest = sorted(atomStack.items(), key=lambda x: x[0])
          top = atomNest[-1]
          if indent == top[0]:
            # sibling of previous atom
            if len(atomNest) > 1:
              if 'name' not in token:
                # lonely operator:
                # left is previous atom, right is parent atom
                qedges.append((top[1], op, atomNest[-2][1]))
                edgeLine[len(qedges) - 1] = i
              else:
                # take the qnode of the subtop of the
                # atomStack, if there is one
                qedges.append((q, ']]', atomNest[-2][1]))
                edgeLine[len(qedges) - 1] = i
                if op is not None:
                  qedges.append((top[1], op, q))
                  edgeLine[len(qedges) - 1] = i
            else:
              if op is not None:
                qedges.append((top[1], op, q))
                edgeLine[len(qedges) - 1] = i
          elif indent > top[0]:
            if 'name' not in token:
              self.badSemantics.append(f'Lonely relation at line {i}: not allowed as first child')
              good = False
            else:
              # child of previous atom
              qedges.append((q, ']]', top[1]))
              edgeLine[len(qedges) - 1] = i
              if op is not None:
                qedges.append((top[1], op, q))
                edgeLine[len(qedges) - 1] = i
          else:
            # outdent action:
            # look up the proper parent in the stack
            if indent not in atomStack:
              # parent cannot be found: indentation error
              self.badSemantics.append(
                  'Unexpected indent at line {}: {}, expected one of {}'.format(
                      i,
                      indent,
                      ','.join(str(at[0]) for at in atomNest if at[0] < indent),
                  )
              )
              good = False
            else:
              parents = [at[1] for at in atomNest if at[0] < indent]
              if len(parents) != 0:  # if not already at outermost level
                if 'name' not in token:
                  # connect previous sibling to parent
                  qedges.append((atomStack[indent], op, parents[-1]))
                  edgeLine[len(qedges) - 1] = i
                else:
                  qedges.append((q, ']]', parents[-1]))
                  edgeLine[len(qedges) - 1] = i
                  if op is not None:
                    qedges.append((atomStack[indent], op, q))
                    edgeLine[len(qedges) - 1] = i
              removeKeys = [at[0] for at in atomNest if at[0] > indent]
              for rk in removeKeys:
                del atomStack[rk]
          atomStack[indent] = q
      elif kind == 'feat':
        features = token['features']
        if prevKind is not None and prevKind != 'atom':
          self.badSemantics.append(f'Features without atom at line {i}: "{features}"')
          good = False
        else:
          qnodes[-1][1].update(features)
      elif kind == 'rel':
        fName = token['f']
        tName = token['t']
        op = token['op']
        f = qnames.get(fName, None)
        t = qnames.get(tName, None)
        namesGood = True
        for (q, n) in ((f, fName), (t, tName)):
          if q is None:
            self.badSemantics.append('Relation with undefined name at line {}: "{}"'.format(i, n))
            namesGood = False
        if not namesGood:
          good = False
        else:
          qedges.append((f, op, t))
          edgeLine[len(qedges) - 1] = i
      prevKind = kind

    # resolve names when used in atoms
    for (q, qdata) in enumerate(qnodes):
      otype = qdata[0]
      referQ = qnames.get(otype, None)
      if referQ is not None:
        referOtype = qnodes[referQ][0]
        qnodes[q] = (referOtype, *qdata[1:])
        qedges.append((q, '=', referQ))

    if good:
      self.qnames = qnames
      self.qnodes = qnodes
      self.qedgesRaw = qedges
      self.nodeLine = nodeLine
      self.edgeLine = edgeLine
    else:
      self.good = False

  def _validateFeature(
      self, q, fName, features, missingFeatures, wrongValues, hasValues={}, asEdge=False
  ):
    values = features[fName]
    fSet = 'edges' if asEdge else 'nodes'
    if fName not in self.api.TF.featureSets[fSet]:
      missingFeatures.setdefault(fName, []).append(q)
    else:
      if asEdge:
        doValues = self.api.TF.features[fName].edgeValues
        if not doValues and values is not True:
          hasValues.setdefault(fName, {}).setdefault(values, []).append(q)
          return
      requiredType = self.api.TF.features[fName].dataType
      if values is True:
        return
      elif values is None:
        return
      elif isinstance(values, types.FunctionType):
        if requiredType == 'str':
          wrongValues.setdefault(fName, {}).setdefault(values, []).append(q)
      elif isinstance(values, reTp):
        if requiredType == 'int':
          wrongValues.setdefault(fName, {}).setdefault(values, []).append(q)
      else:
        valuesCast = set()
        if requiredType == 'int':
          (ident, values) = values
          for val in values:
            try:
              valCast = int(val)
            except Exception:
              valCast = val
              wrongValues.setdefault(fName, {}).setdefault(val, []).append(q)
            valuesCast.add(valCast)
          features[fName] = (ident, frozenset(valuesCast))

  def _validation(self):
    if not self.good:
      return

    levels = self.api.C.levels.data
    otypes = set(x[0] for x in levels)
    qnodes = self.qnodes
    nodeLine = self.nodeLine
    edgeMap = self.edgeMap

    edgeLine = self.edgeLine
    relationFromName = self.relationFromName

    # check the object types of atoms

    otypesGood = True
    sets = self.sets
    for (q, qdata) in enumerate(qnodes):
      otype = qdata[0]
      if sets is not None and otype in sets:
        continue
      if otype not in otypes:
        self.badSemantics.append(f'Unknown object type in line {nodeLine[q]}: "{otype}"')
        otypesGood = False
    if not otypesGood:
      self.badSemantics.append(
          'Valid object types are: {}'.format(','.join(x[0] for x in levels), )
      )
      if sets is not None:
        self.badSemantics.append(
            'Or choose a custom set from: {}'.format(','.join(x for x in sorted(sets)), )
        )
      self.good = False

    # check the feature names of feature specs
    # and check the types of their values

    missingFeatures = {}
    wrongValues = {}
    hasValues = {}
    for (q, qdata) in enumerate(qnodes):
      features = qdata[1]
      for fName in sorted(features):
        self._validateFeature(q, fName, features, missingFeatures, wrongValues)

    # check the relational operator token in edges
    # and replace them by an index
    # in the relations array of known relations
    qedges = []
    edgesGood = True

    # relations may have a variable number k in them (k-nearness, etc.)
    # make an entry in the relation map for each value of k
    addRels = {}
    for (e, (f, op, t)) in enumerate(self.qedgesRaw):
      if (
          type(op) is tuple or (op[0] == '-' and op[-1] == '>') or (op[0] == '<' and op[-1] == '-')
      ):
        continue
      match = kRe.findall(op)
      if len(match):
        (pre, k, post) = match[0]
        opNameK = f'{pre}k{post}'
        addRels.setdefault(opNameK, set()).add(int(k))
    self._add_K_Relations(addRels)

    # edge relations may have a value spec in them
    # make an entry in the relation map for each value spec
    addRels = {}
    for (e, (f, op, t)) in enumerate(self.qedgesRaw):
      if type(op) is not tuple:
        continue
      (opName, opFeatures) = op
      for eName in sorted(opFeatures):
        self._validateFeature(
            e, eName, opFeatures, missingFeatures, wrongValues, hasValues, asEdge=True
        )
        addRels.setdefault(opName, set()).add((eName, opFeatures[eName]))
    self._add_V_Relations(addRels)

    # now look up each particalur relation in the relation map
    for (e, (f, op, t)) in enumerate(self.qedgesRaw):
      theOp = op[0] if type(op) is tuple else op
      rela = relationFromName.get(theOp, None)
      if rela is None:
        self.badSemantics.append(f'Unknown relation in line {edgeLine[e]}: "{theOp}"')
        edgesGood = False
      qedges.append((f, rela, t))
    if not edgesGood:
      self.badSemantics.append(f'Allowed relations:\n{self.relationLegend}')
      self.good = False

    # report error found above
    if len(missingFeatures):
      for (fName, qs) in sorted(missingFeatures.items()):
        self.badSemantics.append(
            'Missing feature "{}" in line(s) {}'.format(
                fName,
                ','.join(str(nodeLine[q]) for q in qs),
            )
        )
      self.good = False

    if len(hasValues):
      for (fName, wrongs) in sorted(hasValues.items()):
        self.badSemantics.append(f'Feature "{fName}" has cannot have values:')
        for (val, qs) in sorted(wrongs.items()):
          self.badSemantics.append(
              '    "{}" superfluous: line(s) {}'.format(
                  val,
                  ','.join(str(nodeLine[q]) for q in qs),
              )
          )
      self.good = False

    if len(wrongValues):
      for (fName, wrongs) in sorted(wrongValues.items()):
        self.badSemantics.append(f'Feature "{fName}" has wrong values:')
        for (val, qs) in sorted(wrongs.items()):
          self.badSemantics.append(
              '    "{}" is not a number: line(s) {}'.format(
                  val,
                  ','.join(str(nodeLine[q]) for q in qs),
              )
          )
      self.good = False

    self.qedges = qedges

    # determine which node and edge features are not yet loaded,
    # and load them
    eFeatsUsed = set()
    for (f, rela, t) in qedges:
      efName = edgeMap.get(rela, (None, ))[0]
      if efName is not None:
        eFeatsUsed.add(efName)
    nFeatsUsed = set()
    for qdata in qnodes:
      features = qdata[1]
      for nfName in features:
        nFeatsUsed.add(nfName)

    if self.good:
      self._ensureLoaded(eFeatsUsed | nFeatsUsed)

  def _ensureLoaded(self, features):
    api = self.api
    F = api.F
    TF = api.TF
    info = api.info

    needToLoad = set()
    loadedFeatures = set()
    for fName in sorted(features):
      fObj = TF.features.get(fName, None)
      if not fObj:
        info(f'Cannot load feature "{fName}": not in dataset')
        continue
      if fObj.dataLoaded and hasattr(F, fName):
        loadedFeatures.add(fName)
      else:
        needToLoad.add(fName)
    if len(needToLoad):
      TF.load(
          needToLoad,
          add=True,
          silent=True,
      )
      loadedFeatures |= needToLoad
    return loadedFeatures

  def _gatherContext(self, results):
    api = self.api
    F = api.F
    Fs = api.Fs
    Es = api.Es
    L = api.L
    T = api.T
    TF = api.TF

    if not self.context:
      return {}

    langs = self.context.get('languages', None)
    if type(langs) is str:
      langs = set(langs.strip().split())
    elif langs is True:
      langs = set(T.languages)

    featureSpec = self.context.get('features', None)
    if type(featureSpec) is str:
      contextFeatures = set(featureSpec.strip().split())
    elif featureSpec is True:
      contextFeatures = {f[0] for f in TF.features.items() if not (f[1].isConfig or f[1].method)}
    else:
      contextFeatures = {fName for fName in featureSpec}

    contextFeatures = {fName for fName in contextFeatures if depLang(fName) in langs}

    loadedFeatures = self._ensureLoaded(contextFeatures)
    allNodes = reduce(
        set.union,
        (set(r) for r in results),
        set(),
    )
    features = {}
    for f in sorted(loadedFeatures):
      fObj = TF.features[f]
      isEdge = fObj.isEdge
      isNode = not (isEdge or fObj.isConfig or fObj.method)
      if isNode:
        data = {}
        for n in allNodes:
          val = Fs(f).v(n)
          if val is not None:
            data[n] = val
        features[f] = data
      elif isEdge:
        if f == 'oslots':
          data = {}
          for n in allNodes:
            vals = tuple(m for m in Es(f).s(n) if m in allNodes)
            if vals:
              data[n] = vals
          features[f] = data
        else:
          hasValues = TF.features[f].edgeValues
          dataF = {}
          dataT = {}
          if hasValues:
            for n in allNodes:
              valsF = tuple(x for x in Es(f).f(n) if x[0] in allNodes)
              valsT = tuple(x for x in Es(f).t(n) if x[0] in allNodes)
              if valsF:
                dataF[n] = valsF
              if valsT:
                dataT[n] = valsT
          else:
            for n in allNodes:
              valsF = tuple(m for m in Es(f).f(n) if m in allNodes)
              valsT = tuple(m for m in Es(f).t(n) if m in allNodes)
              if valsF:
                dataF[n] = valsF
              if valsT:
                dataT[n] = valsT
          features[f] = (dataF, dataT)

    doLocality = self.context.get('locality', None)
    locality = {}
    if doLocality:
      u = {}
      d = {}
      n = {}
      p = {}
      for n in allNodes:
        u[n] = tuple(m for m in L.u(n) if m in allNodes)
        d[n] = tuple(m for m in L.d(n) if m in allNodes)
        n[n] = tuple(m for m in L.n(n) if m in allNodes)
        p[n] = tuple(m for m in L.p(n) if m in allNodes)
      locality['u'] = u
      locality['d'] = d
      locality['n'] = n
      locality['p'] = p

    textFormats = self.context.get('formats', set())
    if type(textFormats) is str:
      textFormats = set(textFormats.strip().split())
    elif textFormats is True:
      textFormats = T.formats
    slotType = F.slotType
    text = {}
    slots = tuple(n for n in allNodes if F.otype.v(n) == slotType)
    for fmt in textFormats:
      data = {}
      for n in slots:
        data[n] = T.text([n], fmt=fmt)
      text[fmt] = data

    return dict(
        features=features,
        locality=locality,
        text=text,
    )

  def _semantics(self):
    self.badSemantics = []
    if not self.good:
      return
    error = self.api.error

    self._grammar()
    if not self.good:
      for (i, line) in enumerate(self.searchLines):
        error(f'{i:>2} {line}', tm=False)
      for eline in self.badSemantics:
        error(eline, tm=False)
      return
    self._validation()
    if not self.good:
      for (i, line) in enumerate(self.searchLines):
        error(f'{i:>2} {line}', tm=False)
      for eline in self.badSemantics:
        error(eline, tm=False)

# WORKING WITH THE SEARCH GRAPH ###

  def _connectedness(self):
    error = self.api.error
    qnodes = self.qnodes
    qedges = self.qedges

    componentIndex = dict(((q, {q}) for q in range(len(qnodes))))
    for (f, rela, t) in qedges:
      if f != t:
        componentIndex[f] |= componentIndex[t]
        for u in componentIndex[f] - {f}:
          componentIndex[u] = componentIndex[f]
    components = sorted(set(frozenset(c) for c in componentIndex.values()))
    componentIndex = {}
    for c in components:
      for q in c:
        componentIndex[q] = c
    componentEdges = {}
    for (e, (f, rela, t)) in enumerate(qedges):
      c = componentIndex[f]
      componentEdges.setdefault(c, []).append(e)
    self.components = []
    for c in components:
      self.components.append([sorted(c), componentEdges.get(c, [])])
    lComps = len(self.components)
    if lComps == 0:
      error('Search without instructions. Tell me what to look for.')
      self.good = False
    elif lComps > 1:
      error(f'More than one connected components ({len(self.components)}):')
      error(
          'Either run the subqueries one by one, or connect the components by a relation',
          tm=False
      )
      self.good = False

  def _showNode(self, q, pos2=False):
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
    self.api.info(nodeInfo, tm=False)

  def _showEdge(self, e, dir):
    qnodes = self.qnodes
    qedges = self.qedges
    converse = self.converse
    relations = self.relations
    spreads = self.spreads
    spreadsC = self.spreadsC
    (f, rela, t) = qedges[e]
    if dir == -1:
      (f, rela, t) = (t, converse[rela], f)
    self.api.info(
        'edge {:>2}-{:<13} {:^2} {:>2}-{:<13} ({:8.1f} choices)'.format(
            f,
            qnodes[f][0],
            relations[rela]['acro'],
            t,
            qnodes[t][0],
            spreads.get(e, -1) if dir == 1 else spreadsC.get(e, -1),
        ),
        tm=False
    )

  def _showYarns(self):
    for q in range(len(self.qnodes)):
      self._showNode(q)

# SPINNING ###

  def _spinAtom(self, q):
    F = self.api.F
    Fs = self.api.Fs
    qnodes = self.qnodes
    sets = self.sets

    (otype, features, src, quantifiers) = qnodes[q]
    featureList = sorted(features.items())
    yarn = set()
    nodeSet = sets[otype] if sets is not None and otype in sets else F.otype.s(otype)
    for n in nodeSet:
      good = True
      for (ft, val) in featureList:
        fval = Fs(ft).v(n)
        if val is None:
          if fval is not None:
            good = False
            break
        elif val is True:
          if fval is None:
            good = False
            break
        elif isinstance(val, types.FunctionType):
          if not val(fval):
            good = False
            break
        elif isinstance(val, reTp):
          if fval is None or not val.search(fval):
            good = False
            break
        else:
          (ident, val) = val
          if ident:
            if fval not in val:
              good = False
              break
          else:
            if fval in val:
              good = False
              break
      if good:
        yarn.add(n)
    if quantifiers:
      for quantifier in quantifiers:
        yarn = self._doQuantifier(yarn, src, quantifier)
    self.yarns[q] = yarn

  def _doQuantifier(self, yarn, atom, quantifier):
    (quKind, quTemplates, parentName) = quantifier
    info = self.api.info
    indent = self.api.indent
    showQuantifiers = self.showQuantifiers
    level = self.level
    universe = yarn
    cleanAtom = _cleanParent(atom, parentName)

    if showQuantifiers:
      indent(level=level + 1, reset=True)
      info(f'"Quantifier on "{cleanAtom}"')

    if quKind == QWITHOUT:
      queryN = '\n'.join((cleanAtom, quTemplates[0]))
      exe = SearchExe(
          self.api,
          queryN,
          level=level + 1,
          sets=self.sets,
          shallow=True,
          showQuantifiers=showQuantifiers
      )
      if showQuantifiers:
        indent(level=level + 2, reset=True)
        info(f'{quKind}\n{queryN}\n{QEND}', tm=False)
      noResults = exe.search()
      resultYarn = universe - noResults
      if showQuantifiers:
        indent(level=level + 2)
        info(f'{len(noResults)} nodes to exclude')
    elif quKind == QWHERE:
      # compute the atom+antecedent:
      #   as result tuples
      queryA = '\n'.join((cleanAtom, quTemplates[0]))
      exe = SearchExe(
          self.api,
          queryA,
          level=level + 1,
          sets=self.sets,
          shallow=False,
          showQuantifiers=showQuantifiers
      )
      if showQuantifiers:
        indent(level=level + 2, reset=True)
        info(f'{quKind}\n{queryA}', tm=False)
      aResultTuples = exe.search(limit=-1)
      if showQuantifiers:
        indent(level=level + 2)
        info(f'{len(aResultTuples)} matching nodes')
      if not aResultTuples:
        resultYarn = yarn
      else:
        sizeA = len(aResultTuples[0])

        # compute the atom+antecedent+consequent:
        #   as shallow result tuples (same length as atom+antecedent)
        queryAH = '\n'.join((cleanAtom, *quTemplates))
        exe = SearchExe(
            self.api,
            queryAH,
            level=level + 1,
            sets=self.sets,
            shallow=sizeA,
            showQuantifiers=showQuantifiers
        )
        if showQuantifiers:
          indent(level=level + 2, reset=True)
          info(f'{QHAVE}\n{queryAH}\n{QEND}', tm=False)
        ahResults = exe.search()
        if showQuantifiers:
          indent(level=level + 2)
          info(f'{len(ahResults)} matching nodes')

        # determine the shallow tuples that correspond to
        #   atom+antecedent but not consequent
        #   and then take the projection to their first components
        resultsAnotH = project(set(aResultTuples) - ahResults, 1)
        if showQuantifiers:
          indent(level=level + 2)
          info(f'{len(resultsAnotH)} match antecedent but not consequent')

        # now have the atoms that do NOT qualify:
        #   we subtract them from the universe
        resultYarn = universe - resultsAnotH
    elif quKind == QWITH:
      # compute the atom+alternative for all alternatives and union them
      resultYarn = set()
      nAlts = len(quTemplates)
      for (i, alt) in enumerate(quTemplates):
        queryAlt = '\n'.join((cleanAtom, alt))
        exe = SearchExe(
            self.api,
            queryAlt,
            level=level + 1,
            sets=self.sets,
            shallow=True,
            showQuantifiers=showQuantifiers
        )
        if showQuantifiers:
          indent(level=level + 2, reset=True)
          info((f'{quKind if i == 0 else QOR}\n{queryAlt}'), tm=False)
        altResults = exe.search() & universe
        nAlt = len(altResults)
        nYarn = len(resultYarn)
        resultYarn |= altResults
        nNew = len(resultYarn)
        if showQuantifiers:
          indent(level=level + 2)
          info(f'adding {nAlt} to {nYarn} yields {nNew} nodes')
          if i == nAlts - 1:
            info(QEND, tm=False)
    if showQuantifiers:
      indent(level=level + 1)
      info(f'reduction from {len(yarn)} to {len(resultYarn)} nodes')
      indent(level=0)
    return resultYarn

  def _spinAtoms(self):
    qnodes = self.qnodes
    for q in range(len(qnodes)):
      self._spinAtom(q)

  def _estimateSpreads(self, both=False):
    TRY_LIMIT_F = 10
    TRY_LIMIT_T = 10
    qnodes = self.qnodes
    relations = self.relations
    converse = self.converse
    qedges = self.qedges
    yarns = self.yarns

    self.spreadsC = {}
    self.spreads = {}

    for (e, (f, rela, t)) in enumerate(qedges):
      tasks = [(f, rela, t, 1)]
      if both:
        tasks.append((t, converse[rela], f, -1))
      for (tf, trela, tt, dir) in tasks:
        s = relations[trela]['spin']
        yarnF = yarns[tf]
        yarnT = yarns[tt]
        dest = self.spreads if dir == 1 else self.spreadsC
        if type(s) is float:
          # fixed estimates
          dest[e] = len(yarnT) * s
          continue
        yarnF = list(yarnF)
        yarnT = yarns[tt]
        totalSpread = 0
        yarnFl = len(yarnF)
        if yarnFl < TRY_LIMIT_F:
          triesn = yarnF
        else:
          triesn = set(yarnF[randrange(yarnFl)] for n in range(TRY_LIMIT_F))
        if len(triesn) == 0:
          dest[e] = 0
        else:
          r = relations[trela]['func'](qnodes[tf][0], qnodes[tt][0])
          nparams = len(signature(r).parameters)
          if nparams == 1:
            for n in triesn:
              mFromN = set(r(n)) & yarnT
              totalSpread += len(mFromN)
          else:
            for n in triesn:
              thisSpread = 0
              yarnTl = len(yarnT)
              if yarnTl < TRY_LIMIT_T:
                triesm = yarnT
              else:
                triesm = set(list(yarnT)[randrange(yarnTl)] for m in range(TRY_LIMIT_T))
              if len(triesm) == 0:
                thisSpread = 0
              else:
                for m in triesm:
                  if r(n, m):
                    thisSpread += 1
              totalSpread += yarnTl * thisSpread / len(triesm)
          dest[e] = totalSpread / len(triesn)

  def _chooseEdge(self):
    F = self.api.F
    yarnFractionNode = {}
    qnodes = self.qnodes
    qedges = self.qedges
    spreads = self.spreads
    sets = self.sets
    for (q, qdata) in enumerate(qnodes):
      otype = qdata[0]
      if sets is not None and otype in sets:
        nodeSet = sets[otype]
        nOtype = len(nodeSet)
      else:
        (begin, end) = F.otype.sInterval(otype)
        nOtype = 1 + end - begin
      nYarn = len(self.yarns[q])
      yf = nYarn / nOtype
      yarnFractionNode[q] = yf * yf
    yarnFractionEdge = {}
    for (e, (f, rela, t)) in enumerate(qedges):
      if self.uptodate[e]:
        continue
      yarnFractionEdge[e] = yarnFractionNode[f] + yarnFractionNode[t] + spreads[e]
    firstEdge = sorted(yarnFractionEdge.items(), key=lambda x: x[1])[0][0]
    return firstEdge

  def _spinEdge(self, e):
    SPIN_LIMIT = 1000
    qnodes = self.qnodes
    relations = self.relations
    yarns = self.yarns
    spreads = self.spreads
    qedges = self.qedges
    uptodate = self.uptodate

    (f, rela, t) = qedges[e]
    yarnF = yarns[f]
    yarnT = yarns[t]
    uptodate[e] = True

    # if the yarns around an edge are big,
    # and the spread of the relation is
    # also big, spinning costs an enormous amount of time,
    # and will not help in reducing the search space.
    # condition for skipping: spread times length from-yarn >= SPIN_LIMIT
    if spreads[e] * len(yarnF) >= SPIN_LIMIT:
      return

    # for some basic relations we know that spinning is useless
    s = relations[rela]['spin']
    if type(s) is float:
      return

    # for other basic realtions we have an optimized spin function
    # if type(s) is types.FunctionType:
    if isinstance(s, types.FunctionType):
      (newYarnF, newYarnT) = s(qnodes[f][0], qnodes[t][0])(yarnF, yarnT)
    else:
      r = relations[rela]['func'](qnodes[f][0], qnodes[t][0])
      nparams = len(signature(r).parameters)
      newYarnF = set()
      newYarnT = set()

      if nparams == 1:
        for n in yarnF:
          mFromN = set(r(n)) & yarnT
          if len(mFromN):
            newYarnT |= mFromN
            newYarnF.add(n)
      else:
        for n in yarnF:
          mFromN = set(m for m in yarnT if r(n, m))
          if len(mFromN):
            newYarnT |= mFromN
            newYarnF.add(n)

    affectedF = len(newYarnF) != len(yarns[f])
    affectedT = len(newYarnT) != len(yarns[t])

    uptodate[e] = True
    for (oe, (of, orela, ot)) in enumerate(qedges):
      if oe == e:
        continue
      if (affectedF and f in {of, ot}) or (affectedT and t in {of, ot}):
        self.uptodate[oe] = False
    self.yarns[f] = newYarnF
    self.yarns[t] = newYarnT

  def _spinEdges(self):
    qnodes = self.qnodes
    qedges = self.qedges
    yarns = self.yarns
    uptodate = self.uptodate

    self._estimateSpreads()

    for e in range(len(qedges)):
      uptodate[e] = False
    it = 0
    while 1:
      if min(len(yarns[q]) for q in range(len(qnodes))) == 0:
        break
      # if reduce(
      #    lambda y,z: y and z,
      #    (uptodate[e] for e in range(len(qedges))),
      #    True,
      # ): break
      if all(uptodate[e] for e in range(len(qedges))):
        break
      e = self._chooseEdge()
      (f, rela, t) = qedges[e]
      self._spinEdge(e)
      it += 1

# STITCHING: STRATEGIES ###

  def _spread_1_first(self):
    qedges = self.qedges
    qnodes = self.qnodes

    s1Edges = []
    for (e, (f, rela, t)) in enumerate(qedges):
      if self.spreads[e] <= 1:
        s1Edges.append((e, 1))
      if self.spreadsC[e] <= 1:
        s1Edges.append((e, -1))
# s1Edges contain all edges with spread <= 1, or whose converse has spread <= 1
# now we want to build the largest graph
# with the original nodes and these edges,
# such that you can walk from a starting point
# over directed s1 edges to every other point
# we initialize candidate graphs: for each node: singletons graph, no edges.
    candidates = []
    # add s1 edges and nodes to all candidates
    for q in range(len(qnodes)):
      cnodes = {q}
      cedges = set()
      cedgesOrder = []
      while 1:
        added = False
        for (e, dir) in s1Edges:
          (f, rela, t) = qedges[e]
          if dir == -1:
            (t, f) = (f, t)
          if f in cnodes:
            if t not in cnodes:
              cnodes.add(t)
              added = True
            if (e, dir) not in cedges:
              cedges.add((e, dir))
              cedgesOrder.append((e, dir))
              added = True
        if not added:
          break
      candidates.append((cnodes, cedgesOrder))

# pick the biggest graph (nodes and edges count for 1)
    startS1 = sorted(candidates, key=lambda x: len(x[0]) + len(x[1]))[-1]

    newNodes = startS1[0]
    newEdges = startS1[1]
    doneEdges = set(e[0] for e in newEdges)

    # we add all edges that are not yet in our startS1.
    # we add them two-fold: also with converse,
    # and we sort the result by spread
    # then we start a big loop:
    # in every iteration, we take the edge with smallest spread
    # that can be connected
    # to the graph under construction
    # then we start a new iteration, because the graph has grown,
    # and and new edges might
    # have become connectable by that

    # in order to fail early, we can also add edges
    # if their from-nodes and to-nodes both have been
    # targeted.
    # That means: an earlier edge went to f,
    # an other earlier edge went to t, and if we
    # have an edge from f to t, we'd better add it now,
    # since it is an extra constraint
    # and by testing it here we can avoid a lot of work.

    remainingEdges = set()
    for e in range(len(qedges)):
      if e not in doneEdges:
        remainingEdges.add((e, 1))
        remainingEdges.add((e, -1))
    remainingEdgesO = sorted(
        remainingEdges,
        key=lambda e: (self.spreads[e[0]] if e[1] == 1 else self.spreadsC[e[0]]),
    )

    while 1:
      added = False
      for (e, dir) in remainingEdgesO:
        if e in doneEdges:
          continue
        (f, rela, t) = qedges[e]
        if dir == -1:
          (f, t) = (t, f)
        if f in newNodes and t in newNodes:
          newEdges.append((e, dir))
          doneEdges.add(e)
          added = True
      for (e, dir) in remainingEdgesO:
        if e in doneEdges:
          continue
        (f, rela, t) = qedges[e]
        if dir == -1:
          (f, t) = (t, f)
        if f in newNodes:
          newNodes.add(t)
          newEdges.append((e, dir))
          doneEdges.add(e)
          added = True
          break
      if not added:
        break

    self.newNodes = newNodes
    self.newEdges = newEdges

  def _small_choice_first(self):

    # This strategy does not try to make a big subgraph of
    # edges with spread 1.
    # The problem is that before the edges work,
    # the initial yarn may have an enormous spread.
    # Here we try out the strategy of postponing
    # broad choices as long as possible.
    # The inituition is that while we are making smaller choices,
    # constraints are encountered,
    # severely limiting the broader choices later on.

    # So, we pick the yarn with the least amount of nodes
    # as our starting point.
    # The corresponding node is our singleton start set.
    # In every iteration we do the following:
    # - we pick all edges of which from- and to-nodes
    #   are already in the node set
    # - we pick the edge with least spread
    #   that has a starting point in the set
    # Until nothing changes anymore

    qedges = self.qedges
    qnodes = self.qnodes

    newNodes = {sorted(range(len(qnodes)), key=lambda x: len(self.yarns[x]))[0]}
    newEdges = []
    doneEdges = set()

    remainingEdges = set()
    for e in range(len(qedges)):
      remainingEdges.add((e, 1))
      remainingEdges.add((e, -1))
    remainingEdgesO = sorted(
        remainingEdges,
        key=lambda e: (self.spreads[e[0]] if e[1] == 1 else self.spreadsC[e[0]]),
    )

    while 1:
      added = False
      for (e, dir) in remainingEdgesO:
        if e in doneEdges:
          continue
        (f, rela, t) = qedges[e]
        if dir == -1:
          (f, t) = (t, f)
        if f in newNodes and t in newNodes:
          newEdges.append((e, dir))
          doneEdges.add(e)
          added = True
      for (e, dir) in remainingEdgesO:
        if e in doneEdges:
          continue
        (f, rela, t) = qedges[e]
        if dir == -1:
          (f, t) = (t, f)
        if f in newNodes:
          newNodes.add(t)
          newEdges.append((e, dir))
          doneEdges.add(e)
          added = True
          break
      if not added:
        break

    self.newNodes = newNodes
    self.newEdges = newEdges

  def _big_choice_first(self):

    # For comparison: the opposite of _small_choice_first.
    # Just to see what the performance difference is.

    qedges = self.qedges
    qnodes = self.qnodes

    newNodes = {sorted(range(len(qnodes)), key=lambda x: -len(self.yarns[x]))[0]}
    newEdges = []
    doneEdges = set()

    remainingEdges = set()
    for e in range(len(qedges)):
      remainingEdges.add((e, 1))
      remainingEdges.add((e, -1))
    remainingEdgesO = sorted(
        remainingEdges,
        key=lambda e: (-self.spreads[e[0]] if e[1] == 1 else -self.spreadsC[e[0]]),
    )

    while 1:
      added = False
      for (e, dir) in remainingEdgesO:
        if e in doneEdges:
          continue
        (f, rela, t) = qedges[e]
        if dir == -1:
          (f, t) = (t, f)
        if f in newNodes and t in newNodes:
          newEdges.append((e, dir))
          doneEdges.add(e)
          added = True
      for (e, dir) in remainingEdgesO:
        if e in doneEdges:
          continue
        (f, rela, t) = qedges[e]
        if dir == -1:
          (f, t) = (t, f)
        if f in newNodes:
          newNodes.add(t)
          newEdges.append((e, dir))
          doneEdges.add(e)
          added = True
          break
      if not added:
        break

    self.newNodes = newNodes
    self.newEdges = newEdges

# STITCHING ###

  def _stitch(self):
    self._estimateSpreads(both=True)
    self._stitchPlan()
    if not self.good:
      return
    self._stitchResults()

# STITCHING: PLANNING ###

  def _stitchPlan(self, strategy=None):
    qnodes = self.qnodes
    qedges = self.qedges
    error = self.api.error

    self._setStrategy(strategy, keep=True)
    if not self.good:
      return

    # Apply the chosen strategy
    self.strategy()

    # remove spurious edges:
    # if we have both the 1 and -1 version of an edge,
    # we can leave out the one that we encounter in the second place

    newNodes = self.newNodes
    newEdges = self.newEdges

    newCedges = set()
    newCedgesOrder = []
    for (e, dir) in newEdges:
      if e not in newCedges:
        newCedgesOrder.append((e, dir))
        newCedges.add(e)

# conjecture: we have all edges and all nodes now
# reason: we work in a connected component, so all nodes are reachable
# by edges or inverses
# we check nevertheless

    qnodesO = tuple(range(len(qnodes)))
    newNodesO = tuple(sorted(newNodes))
    if newNodesO != qnodesO:
      error(
          f'''Object mismatch in plan:
In template: {qnodesO}
In plan    : {newNodesO}''', tm=False
      )
      self.good = False

    qedgesO = tuple(range(len(qedges)))
    newCedgesO = tuple(sorted(newCedges))
    if newCedgesO != qedgesO:
      error(
          f'''Relation mismatch in plan:
In template: {qedgesO}
In plan    : {newCedgesO}''',
          tm=False
      )
      self.good = False

    self.stitchPlan = (newNodes, newCedgesOrder)

# STITCHING: DELIVERING ###

  def _stitchResults(self):
    qnodes = self.qnodes
    qedges = self.qedges
    plan = self.stitchPlan
    relations = self.relations
    converse = self.converse
    yarns = self.yarns

    planEdges = plan[1]
    if len(planEdges) == 0:
      # no edges, hence a single node (because of connectedness,
      # hence we must deliver everything of its yarn
      yarn = yarns[0]

      def deliver(remap=True):
        for n in yarn:
          yield (n, )

      if self.shallow:
        self.results = yarn
      else:
        self.results = deliver
      return

# The next function must be optimized, and the lookup of functions and data
# should be as direct as possible.
# Because deliver() below fetches the results,
# of wich there are unpredictably many.

# We are going to build-up and deliver stitches,
# which are instantiations of all the query nodes
# by text nodes in a specific sequence
# which is the same for all stitches.
# We can compile stitching in such a way, that the stitcher thinks it is
# instantiating q node 0, then 1, and so on.
# I.e. we are going to permute every thing that the stitching process sees,
# so that it happens in this order.

# We build up the stitch in a recursive process.
# When there is choice between a and b, we essentially say
#
# def build(stitch)
#     if there is choice
#        build(stitch+a)
#        build(stitch+b)
#
# But we do not have to pass on the stitch as an immutable data structure.
# We can just keep it as one single mutable datastructure, provided we
# do something between the two recursive calls above.
# Suppose stitch is an array, and in the outer build n elements are filled
# (the rest contains -1)
#
# Then we say
#     if there is choice
#        build(stitch+a)
#        for k in range(n, len(stitch)): stitch[k] = -1
#        build(stitch+b)
#
# It turns out that the data in stitch that is shared between calls
# is not modified by them.
# The only thing that happens, is that -1 values get new values.
# So coming out calls only requires us to restore -1's.
# And if the stitch is ordered in the right way,
# the -1's are always at the end.

# We start compiling and permuting

    edgesCompiled = []
    qPermuted = []  # row of nodes in the order as will be created during stitching
    qPermutedInv = {}  # mapping from original q node number to index in the permuted order
    for (i, (e, dir)) in enumerate(planEdges):
      (f, rela, t) = qedges[e]
      if dir == -1:
        (f, rela, t) = (t, converse[rela], f)
      r = relations[rela]['func'](qnodes[f][0], qnodes[t][0])
      nparams = len(signature(r).parameters)
      if i == 0:
        qPermuted.append(f)
        qPermutedInv[f] = len(qPermuted) - 1
      if t not in qPermuted:
        qPermuted.append(t)
        qPermutedInv[t] = len(qPermuted) - 1

      edgesCompiled.append((qPermutedInv[f], qPermutedInv[t], r, nparams))

# now permute the yarns

    yarnsPermuted = [yarns[q] for q in qPermuted]

    shallow = self.shallow

    def deliver(remap=True):
      stitch = [None for q in range(len(qPermuted))]
      lStitch = len(stitch)
      qs = tuple(range(lStitch))
      edgesC = edgesCompiled
      yarnsP = yarnsPermuted

      def stitchOn(e):
        if e >= len(edgesC):
          if remap:
            yield tuple(stitch[qPermutedInv[q]] for q in qs)
          else:
            yield tuple(stitch)
          return
        (f, t, r, nparams) = edgesC[e]
        yarnT = yarnsP[t]
        if e == 0 and stitch[f] is None:
          yarnF = yarnsP[f]
          for sN in yarnF:
            stitch[f] = sN
            for s in stitchOn(e):
              yield s
          return
        sN = stitch[f]
        sM = stitch[t]
        if sM is not None:
          if nparams == 1:
            if sM in set(r(sN)):  # & yarnT:
              for s in stitchOn(e + 1):
                yield s
          else:
            if r(sN, sM):
              for s in stitchOn(e + 1):
                yield s
          return
        mFromN = tuple(set(r(sN)) & yarnT) if nparams == 1 else tuple(m for m in yarnT if r(sN, m))
        for m in mFromN:
          stitch[t] = m
          for s in stitchOn(e + 1):
            yield s
        stitch[t] = None

      for s in stitchOn(0):
        yield s

    def delivered():
      tupleSize = len(qPermuted)
      shallowTupleSize = max(tupleSize, shallow)
      stitch = [None for q in range(tupleSize)]
      edgesC = edgesCompiled
      yarnsP = yarnsPermuted
      resultQ = qPermutedInv[0]
      resultQmax = max(qPermutedInv[q] for q in range(shallowTupleSize))
      resultSet = set()

      def stitchOn(e):
        if e >= len(edgesC):
          yield tuple(stitch)
          return
        (f, t, r, nparams) = edgesC[e]
        yarnT = yarnsP[t]
        if e == 0 and stitch[f] is None:
          yarnF = yarnsP[f]
          if f == resultQmax:
            for sN in yarnF:
              if sN in resultSet:
                continue
              stitch[f] = sN
              for s in stitchOn(e):
                yield s
          else:
            for sN in yarnF:
              stitch[f] = sN
              for s in stitchOn(e):
                yield s
          return
        sN = stitch[f]
        if f == resultQmax:
          if sN in resultSet:
            return
        sM = stitch[t]
        if sM is not None:
          if t == resultQmax:
            if sM in resultSet:
              return
          if nparams == 1:
            if sM in set(r(sN)):  # & yarnT:
              for s in stitchOn(e + 1):
                yield s
          else:
            if r(sN, sM):
              for s in stitchOn(e + 1):
                yield s
          return
        mFromN = tuple(set(r(sN)) & yarnT) if nparams == 1 else tuple(m for m in yarnT if r(sN, m))
        for m in mFromN:
          stitch[t] = m
          for s in stitchOn(e + 1):
            yield s
        stitch[t] = None

      if shallow == 1:
        for s in stitchOn(0):
          result = s[resultQ]
          resultSet.add(result)
      else:  # shallow > 1
        qs = tuple(range(shallow))
        for s in stitchOn(0):
          result = tuple(s[qPermutedInv[q]] for q in qs)
          resultSet.add(result)

      return resultSet

    if shallow:
      self.results = delivered()
    else:
      self.results = deliver


# TOP-LEVEL IMPLEMENTATION METHODS

  def _parse(self):
    self._syntax()
    self._semantics()

  def _prepare(self):
    if not self.good:
      return
    self.yarns = {}
    self.spreads = {}
    self.spreadsC = {}
    self.uptodate = {}
    self.results = None
    self._connectedness()

  def _setStrategy(self, strategy, keep=False):
    error = self.api.error
    if strategy is None:
      if keep:
        return
      strategy = STRATEGY[0]
    if strategy not in STRATEGY:
      error(f'Strategy not defined: "{strategy}"')
      error('Allowed strategies:\n{}'.format('\n'.join(f'    {s}' for s in STRATEGY)), tm=False)
      self.good = False
      return

    method = f'_{strategy}'
    if not hasattr(self, method):
      error('Strategy is defined, but not implemented: "{}"'.format(strategy))
      self.good = False
      return
    self.strategy = getattr(self, method)
