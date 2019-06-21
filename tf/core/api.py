import collections
from .helpers import makeInverse, makeInverseVal, flattenToSet, console
from .locality import Locality
from .text import Text
from ..search.search import Search

API_REFS = dict(
    AllComputeds=('Computed', 'computedall', 'computed-data'),
    AllEdges=('Features', 'edgeall', 'edge-features'),
    AllFeatures=('Features', 'nodeall', 'node-features'),
    C=('Computed', 'computed', 'computed-data'),
    Call=('Computed', 'computedall', 'computed-data'),
    Computed=('Computed', 'computed', 'computed-data'),
    ComputedString=('Computed', 'computedstr', 'computed-data'),
    Cs=('Computed', 'computedstr', 'computed-data'),
    E=('Features', 'edge', 'edge-features'),
    Eall=('Features', 'edgeall', 'edge-features'),
    Edge=('Features', 'edge', 'edge-features'),
    EdgeString=('Features', 'edgestr', 'edge-features'),
    Es=('Features', 'edgestr', 'edge-features'),
    F=('Features', 'node', 'node-features'),
    Fall=('Features', 'nodeall', 'node-features'),
    Feature=('Features', 'node', 'node-features'),
    FeatureString=('Features', 'nodestr', 'node-features'),
    Fs=('Features', 'nodestr', 'node-features'),
    L=('Locality', 'locality', 'locality'),
    Locality=('Locality', 'locality', 'locality'),
    N=('Nodes', 'generator', 'navigating-nodes'),
    Nodes=('Nodes', 'generator', 'navigating-nodes'),
    S=('Search', 'search', 'search'),
    Search=('Search', 'search', 'search'),
    T=('Text', 'text', 'text'),
    TF=('Fabric', 'fabric', 'loading'),
    Text=('Text', 'text', 'text'),
    cache=('Misc', 'cache', 'messaging'),
    ensureLoaded=('Fabric', 'ensure', 'loading'),
    error=('Misc', 'error', 'messaging'),
    ignored=('Fabric', 'ignored', 'loading'),
    indent=('Misc', 'indent', 'messaging'),
    info=('Misc', 'info', 'messaging'),
    warning=('Misc', 'warning', 'messaging'),
    isSilent=('Misc', 'isSilent', 'messaging'),
    setSilent=('Misc', 'setSilent', 'messaging'),
    silentOn=('Misc', 'silentOn', 'messaging'),
    silentOff=('Misc', 'silentOff', 'messaging'),
    loadLog=('Fabric', 'loadlog', 'loading'),
    otypeRank=('Nodes', 'rank', 'navigating-nodes'),
    reset=('Misc', 'reset', 'messaging'),
    sortKey=('Nodes', 'key', 'navigating-nodes'),
    sortKeyTuple=('Nodes', 'keyTuple', 'navigating-nodes'),
    sortNodes=('Nodes', 'sort', 'navigating-nodes'),
)


class OtypeFeature(object):

  def __init__(self, api, metaData, data):
    self.api = api
    self.meta = metaData
    self.data = data[0]
    self.maxSlot = data[1]
    self.maxNode = data[2]
    self.slotType = data[3]

  def items(self):
    slotType = self.slotType
    maxSlot = self.maxSlot
    data = self.data

    for n in range(1, maxSlot + 1):
      yield (n, slotType)

    maxNode = self.maxNode

    shift = maxSlot + 1

    for n in range(maxSlot + 1, maxNode + 1):
      yield (n, data[n - shift])

  def v(self, n):
    if n == 0:
      return None
    if n < self.maxSlot + 1:
      return self.slotType
    m = n - self.maxSlot
    if m <= len(self.data):
      return self.data[m - 1]
    return None

  def s(self, val):
    # NB: the support attribute has been added by precomputing __levels__
    if val in self.support:
      (b, e) = self.support[val]
      return range(b, e + 1)
    else:
      return ()

  def sInterval(self, val):
    # NB: the support attribute has been added by precomputing __levels__
    if val in self.support:
      return self.support[val]
    else:
      return ()


class OslotsFeature(object):

  def __init__(self, api, metaData, data):
    self.api = api
    self.meta = metaData
    self.data = data[0]
    self.maxSlot = data[1]
    self.maxNode = data[2]

  def items(self):
    maxSlot = self.maxSlot
    data = self.data
    maxNode = self.maxNode

    shift = maxSlot + 1

    for n in range(maxSlot + 1, maxNode + 1):
      yield (n, data[n - shift])

  def s(self, n):
    if n == 0:
      return ()
    if n < self.maxSlot + 1:
      return (n, )
    m = n - self.maxSlot
    if m <= len(self.data):
      return self.data[m - 1]
    return ()


class NodeFeature(object):

  def __init__(self, api, metaData, data):
    self.api = api
    self.meta = metaData
    self.data = data

  def items(self):
    return self.data.items()

  def v(self, n):
    if n in self.data:
      return self.data[n]
    return None

  def s(self, val):
    Crank = self.api.C.rank.data
    return tuple(
        sorted(
            [n for n in self.data if self.data[n] == val],
            key=lambda n: Crank[n - 1],
        )
    )

  def freqList(self, nodeTypes=None):
    fql = collections.Counter()
    if nodeTypes is None:
      for n in self.data:
        fql[self.data[n]] += 1
    else:
      fOtype = self.api.F.otype.v
      for n in self.data:
        if fOtype(n) in nodeTypes:
          fql[self.data[n]] += 1
    return tuple(sorted(fql.items(), key=lambda x: (-x[1], x[0])))


class EdgeFeature(object):

  def __init__(self, api, metaData, data, doValues):
    self.api = api
    self.meta = metaData
    self.doValues = doValues
    if type(data) is tuple:
      self.data = data[0]
      self.dataInv = data[1]
    else:
      self.data = data
      self.dataInv = makeInverseVal(self.data) if doValues else makeInverse(self.data)

  def items(self):
    return self.data.items()

  def f(self, n):
    if n not in self.data:
      return ()
    Crank = self.api.C.rank.data
    if self.doValues:
      return tuple(sorted(
          self.data[n].items(),
          key=lambda mv: Crank[mv[0] - 1],
      ))
    else:
      return tuple(sorted(
          self.data[n],
          key=lambda m: Crank[m - 1],
      ))

  def t(self, n):
    if n not in self.dataInv:
      return ()
    Crank = self.api.C.rank.data
    if self.doValues:
      return tuple(sorted(
          self.dataInv[n].items(),
          key=lambda mv: Crank[mv[0] - 1],
      ))
    else:
      return tuple(sorted(
          self.dataInv[n],
          key=lambda m: Crank[m - 1],
      ))

  def b(self, n):
    if n not in self.data and n not in self.dataInv:
      return ()
    Crank = self.api.C.rank.data
    if self.doValues:
      result = {}
      if n in self.dataInv:
        result.update(self.dataInv[n].items())
      if n in self.data:
        result.update(self.data[n].items())
      return tuple(sorted(
          result.items(),
          key=lambda mv: Crank[mv[0] - 1],
      ))
    else:
      result = set()
      if n in self.dataInv:
        result |= self.dataInv[n]
      if n in self.data:
        result |= self.data[n]
      return tuple(sorted(
          result,
          key=lambda m: Crank[m - 1],
      ))

  def freqList(self, nodeTypesFrom=None, nodeTypesTo=None):
    if nodeTypesFrom is None and nodeTypesTo is None:
      if self.doValues:
        fql = collections.Counter()
        for (n, vals) in self.data.items():
          for val in vals.values():
            fql[val] += 1
        return tuple(sorted(fql.items(), key=lambda x: (-x[1], x[0])))
      else:
        fql = 0
        for (n, ms) in self.data.items():
          fql += len(ms)
        return fql
    else:
      fOtype = self.api.F.otype.v
      if self.doValues:
        fql = collections.Counter()
        for (n, vals) in self.data.items():
          if nodeTypesFrom is None or fOtype(n) in nodeTypesFrom:
            for (m, val) in vals.items():
              if nodeTypesTo is None or fOtype(m) in nodeTypesTo:
                fql[val] += 1
        return tuple(sorted(fql.items(), key=lambda x: (-x[1], x[0])))
      else:
        fql = 0
        for (n, ms) in self.data.items():
          if nodeTypesFrom is None or fOtype(n) in nodeTypesFrom:
            for m in ms:
              if nodeTypesTo is None or fOtype(m) in nodeTypesTo:
                fql += len(ms)
        return fql


class Computed(object):

  def __init__(self, api, data):
    self.api = api
    self.data = data


class NodeFeatures(object):
  pass


class EdgeFeatures(object):
  pass


class Computeds(object):
  pass


class Api(object):

  def __init__(self, TF):
    self.TF = TF
    self.ignored = tuple(sorted(TF.featuresIgnored))
    self.F = NodeFeatures()
    self.Feature = self.F
    self.E = EdgeFeatures()
    self.Edge = self.E
    self.C = Computeds()
    self.Computed = self.C
    tm = TF.tm
    self.silentOn = tm.silentOn
    self.silentOff = tm.silentOff
    self.isSilent = tm.isSilent
    self.setSilent = tm.setSilent
    self.info = tm.info
    self.warning = tm.warning
    self.error = tm.error
    self.cache = tm.cache
    self.reset = tm.reset
    self.indent = tm.indent
    self.loadLog = tm.cache
    setattr(self, 'FeatureString', self.Fs)
    setattr(self, 'EdgeString', self.Es)
    setattr(self, 'ComputedString', self.Cs)
    setattr(self, 'Nodes', self.N)
    setattr(self, 'AllFeatures', self.Fall)
    setattr(self, 'AllEdges', self.Eall)
    setattr(self, 'AllComputeds', self.Call)

  def Fs(self, fName):
    if not hasattr(self.F, fName):
      self.error(f'Node feature "{fName}" not loaded')
      return None
    return getattr(self.F, fName)

  def Es(self, fName):
    if not hasattr(self.E, fName):
      self.error(f'Edge feature "{fName}" not loaded')
      return None
    return getattr(self.E, fName)

  def Cs(self, fName):
    if not hasattr(self.C, fName):
      self.error(f'Computed feature "{fName}" not loaded')
      return None
    return getattr(self.C, fName)

  def N(self):
    for n in self.C.order.data:
      yield n

  def sortNodes(self, nodeSet):
    Crank = self.C.rank.data
    return sorted(nodeSet, key=lambda n: Crank[n - 1])

  def Fall(self):
    return sorted(x[0] for x in self.F.__dict__.items())

  def Eall(self):
    return sorted(x[0] for x in self.E.__dict__.items())

  def Call(self):
    return sorted(x[0] for x in self.C.__dict__.items())

  # API_REFS:
  # F=>(Features, node, node-features),

  def makeAvailableIn(self, scope):
    for member in dir(self):
      if '_' not in member and member != 'makeAvailableIn':
        scope[member] = getattr(self, member)
        if member not in API_REFS:
          console(f'WARNING: API member "{member}" not documented')

    grouped = {}
    for (member, (head, sub, ref)) in API_REFS.items():
      grouped.setdefault(ref, {}).setdefault((head, sub), []).append(member)

  # grouped
  # node-features=>(Features, node)=>[F, ...]

    docs = []
    for (ref, groups) in sorted(grouped.items()):
      chunks = []
      for ((head, sub), members) in sorted(groups.items()):
        chunks.append(' '.join(sorted(members, key=lambda x: (len(x), x))))
      docs.append((head, ref, tuple(chunks)))
    return docs

  # docs
  # (Features, node-features, ('F ...', ...))

  def ensureLoaded(self, features):
    F = self.F
    E = self.E
    TF = self.TF
    warning = self.warning

    needToLoad = set()
    loadedFeatures = set()

    for fName in sorted(flattenToSet(features)):
      fObj = TF.features.get(fName, None)
      if not fObj:
        warning(f'Cannot load feature "{fName}": not in dataset')
        continue
      if fObj.dataLoaded and (hasattr(F, fName) or hasattr(E, fName)):
        loadedFeatures.add(fName)
      else:
        needToLoad.add(fName)
    if len(needToLoad):
      TF.load(
          needToLoad,
          add=True,
          silent='deep',
      )
      loadedFeatures |= needToLoad
    return loadedFeatures


def addSortKey(api):
  Crank = api.C.rank.data
  api.sortKey = lambda n: Crank[n - 1]
  api.sortKeyTuple = lambda tup: tuple(Crank[n - 1] for n in tup)


def addOtype(api):
  setattr(api.F.otype, 'all', tuple(o[0] for o in api.C.levels.data))
  setattr(api.F.otype, 'support', dict(((o[0], (o[2], o[3])) for o in api.C.levels.data)))


def addLocality(api):
  api.L = Locality(api)
  api.Locality = api.L


def addRank(api):
  C = api.C
  api.otypeRank = {d[0]: i for (i, d) in enumerate(reversed(C.levels.data))}


def addText(api):
  api.T = Text(api)
  api.Text = api.T


def addSearch(api, silent):
  api.S = Search(api, silent)
  api.Search = api.S
