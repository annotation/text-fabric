import collections
from .helpers import *
from .locality import Locality
from .text import Text
from .search import Search

class OtypeFeature(object):
    def __init__(self, api, data=None):
        self.api = api
        self.data = data
        self.slotType = self.data[-2]
        self.maxSlot = self.data[-1]
        self.maxNode = len(self.data) - 2 + self.maxSlot

    def v(self, n): 
        if n == 0: return None
        if n < self.maxSlot + 1:
            return self.data[-2]
        m = n - self.maxSlot
        if m <= len(self.data) - 2:
            return self.data[m-1]
        return None

    def s(self, val):
        # NB: the support attribute has been added by precomputing __levels__
        if val in self.support:        
            (b, e) = self.support[val]
            return range(b, e+1)
        else:
            return ()

    def sInterval(self, val):
        # NB: the support attribute has been added by precomputing __levels__
        if val in self.support:        
            return self.support[val]
        else:
            return ()

class OslotsFeature(object):
    def __init__(self, api, data=None):
        self.api = api
        self.data = data
        self.maxSlot = self.data[-1]

    def s(self, n): 
        if n == 0: return ()
        if n < self.maxSlot + 1:
            return (n,)
        m = n - self.maxSlot
        if m <= len(self.data) - 1:
            return self.data[m-1]
        return ()

class NodeFeature(object):
    def __init__(self, api, data):
        self.api = api
        self.data = data

    def v(self, n): 
        if n in self.data:
            return self.data[n]
        return None

    def s(self, val):
        Crank = self.api.C.rank.data
        return tuple(sorted(
            [n for n in self.data if self.data[n] == val],
            key=lambda n: Crank[n-1],
        ))
    def freqList(self):
        fql = collections.Counter()
        for n in self.data: fql[self.data[n]] += 1
        return tuple(sorted(fql.items(), key=lambda x: (-x[1], x[0])))

class EdgeFeature(object):
    def __init__(self, api, data, doValues):
        self.api = api
        self.data = data
        self.doValues = doValues
        self.dataInv = makeInverseVal(self.data) if doValues else makeInverse(self.data)

    def f(self, n): 
        Crank = self.api.C.rank.data
        if n in self.data:
            if self.doValues:
                return tuple(sorted(
                    self.data[n].items(),
                    key=lambda mv: Crank[mv[0]-1],
                ))
            else:
                return tuple(sorted(
                    self.data[n],
                    key=lambda m: Crank[m-1],
                ))
        return ()

    def t(self, n): 
        Crank = self.api.C.rank.data
        if n in self.dataInv:
            if self.doValues:
                return tuple(sorted(
                    self.dataInv[n].items(),
                    key=lambda mv: Crank[mv[0]-1],
                ))
            else:
                return tuple(sorted(
                    self.dataInv[n],
                    key=lambda m: Crank[m-1],
                ))
        return ()

class Computed(object):
    def __init__(self, api, data):
        self.api = api
        self.data = data

class NodeFeatures(object): pass
class EdgeFeatures(object): pass
class Computeds(object): pass

class Api(object):
    def __init__(self, tf):
        self.ignored = tuple(sorted(tf.featuresIgnored))
        self.F = NodeFeatures()
        self.E = EdgeFeatures()
        self.C = Computeds()
        self.info = tf.tm.info
        self.error = tf.tm.error
        self.indent = tf.tm.indent
        self.loadLog = tf.tm.cache

    def Fs(self, fName):
        if not hasattr(self.F, fName):
            self.error('Node feature "{}" not loaded'.format(fName))
            return None
        return getattr(self.F, fName)

    def Es(self, fName):
        if not hasattr(self.E, fName):
            self.error('Edge feature "{}" not loaded'.format(fName))
            return None
        return getattr(self.E, fName)

    def Cs(self, fName):
        if not hasattr(self.C, fName):
            self.error('Computed feature "{}" not loaded'.format(fName))
            return None
        return getattr(self.C, fName)
    
    def N(self):
        for n in self.C.order.data: yield n

    def sortNodes(self, nodeSet):
        Crank = self.C.rank.data
        return sorted(nodeSet, key=lambda n: Crank[n-1])

    def Fall(self): return sorted(x[0] for x in self.F.__dict__.items())
    def Eall(self): return sorted(x[0] for x in self.E.__dict__.items())
    def Call(self): return sorted(x[0] for x in self.C.__dict__.items())

    def makeAvailableIn(self, scope):
        for member in dir(self):
            if '_' not in member and member != 'makeAvailableIn': scope[member] = getattr(self, member) 

def addSortKey(api):
    Crank = api.C.rank.data
    api.sortKey = lambda n: Crank[n-1]

def addOtype(api):
    setattr(api.F.otype, 'all', tuple(o[0] for o in api.C.levels.data))
    setattr(api.F.otype, 'support', dict(((o[0], (o[2], o[3])) for o in api.C.levels.data)))

def addLocality(api):
    api.L = Locality(api)

def addText(api, tf):
    api.T = Text(api, tf)

def addSearch(api, tf, silent):
    api.S = Search(api, tf, silent)

