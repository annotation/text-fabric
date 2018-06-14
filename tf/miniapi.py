from .api import NodeFeature, EdgeFeature

DEFAULT_FORMAT = 'text-orig-full'


class MiniApi(object):
  def __init__(
      self,
      nodes=None,
      features={},
      featureType={},
      locality={},
      text={},
      langs=set(),
  ):
    self.isMini = True
    self.nodes = () if nodes is None else tuple(int(n) for n in nodes.split(','))
    self.F = NodeFeatures()
    self.E = EdgeFeatures()

    rank = {n: i for (i, n) in enumerate(self.nodes)}
    self.rank = rank
    self.sortKey = lambda n: rank[n]

    for f in features:
      fType = featureType[f]
      if fType:
        fObj = EdgeFeature(self, features[f], fType == 1)
        setattr(self.E, f, fObj)
      else:
        fObj = NodeFeature(self, features[f])
        setattr(self.F, f, fObj)

    self.L = Locality(self, locality)
    self.T = Text(self, text, langs)

  def Fs(self, fName):
    return getattr(self.F, fName, None)

  def Es(self, fName):
    return getattr(self.E, fName, None)

  def Fall(self):
    return sorted(x[0] for x in self.F.__dict__.items())

  def Eall(self):
    return sorted(x[0] for x in self.E.__dict__.items())

  def N(self):
    for n in self.nodes:
      yield n

  def sortNodes(self, nodeSet):
    return sorted(nodeSet, key=self.sortKey)


class NodeFeatures(object):
  pass


class EdgeFeatures(object):
  pass


class Locality(object):
  def __init__(self, api, data):
    self.api = api
    self.data = data
    for member in ('u', 'd', 'n', 'p'):
      _makeLmember(self, member)


class Text(object):
  def __init__(self, api, langs, text):
    self.api = api
    self.langs = langs
    self.formats = set(text)
    self.data = text

  def text(self, slots, fmt=None):
    if fmt is None:
      fmt = DEFAULT_FORMAT
    thisText = self.data.get(fmt, None)
    if thisText is None:
      return ' '.join(str(s) for s in slots)
    return ''.join(thisText.get(s, '?') for s in slots)


def _makeLmember(dest, member):
  def memberFunction(n, otype=None):
    data = dest.data
    if n not in data.get(member, {}):
      return ()
    ms = data[member][n]
    if otype is None:
      return ms
    api = dest.api
    F = api.F
    return tuple(m for m in ms if F.otype.v(m) == otype)
  setattr(dest, member, memberFunction)
