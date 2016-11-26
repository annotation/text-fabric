import collections

class OtypeFeature(object):
    def __init__(self, api, data=None):
        self.api = api
        self.data = data
        self.monadType = self.data[-2]
        self.maxMonad = self.data[-1]
        self.maxNode = len(self.data) + self.data[-1] - 1

    def v(self, n): 
        if n < self.maxMonad + 1:
            return self.data[-2]
        m = n - self.maxMonad - 1
        if m < len(self.data) - 2:
            return self.data[m]
        return None

    def s(self, val):
        Crank = self.api.C.rank.data
        maxMonad = self.maxMonad
        if val == self.data[-2]:
            return range(maxMonad+1)
        return sorted(
            [n+maxMonad+1 for n in range(len(self.data)-2) if self.data[n] == val],
            key=lambda n: Crank[n],
        )

class MonadsFeature(object):
    def __init__(self, api, data=None):
        self.api = api
        self.data = data
        self.maxMonad = self.data[-1]

    def m(self, n): 
        if n < self.maxMonad + 1:
            return [n]
        m = n - self.maxMonad - 1
        if m < len(self.data) - 1:
            return self.data[m]
        return []

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
        return sorted(
            [n for n in self.data if self.data[n] == val],
            key=lambda n: Crank[n],
        )

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
                return sorted(
                    self.data[n].items(),
                    key=lambda n: Crank[n[0]],
                )
            else:
                return sorted(
                    self.data[n],
                    key=lambda n: Crank[n],
                )
        return None

    def t(self, n): 
        Crank = self.api.C.rank.data
        if n in self.dataInv:
            if self.doValues:
                return sorted(
                    self.dataInv[n].items(),
                    key=lambda n: Crank[n[0]],
                )
            else:
                return sorted(
                    self.dataInv[n],
                    key=lambda n: Crank[n],
                )
        return None

class Computed(object):
    def __init__(self, api, data):
        self.api = api
        self.data = data

class NodeFeatures(object): pass
class EdgeFeatures(object): pass
class Computeds(object): pass

class Layer(object):
    def __init__(self, api):
        self.api = api

    def u(self, n, otype=None):
        Fotype = self.api.F.otype
        levUp = self.api.C.levUp.data
        if otype == None:
            return levUp[n]
        else:
            return tuple(m for m in levUp[n] if Fotype.v(m) == otype) 

    def d(self, n, otype=None):
        Fotype = self.api.F.otype
        Emonads = self.api.E.monads
        Crank = self.api.C.rank.data
        levDown = self.api.C.levDown.data
        monadType = Fotype.monadType
        maxMonad = Fotype.maxMonad
        if n < maxMonad+1: return tuple()
        if otype == None:
            return sorted(
                levDown[n-maxMonad-1]+Emonads.m(n),
                key=lambda n: Crank[n],
            )
        elif otype == monadType:
            return sorted(
                Emonads.m(n),
                key=lambda n: Crank[n],
            )
        else:
            return tuple(m for m in levDown[n-maxMonad-1] if Fotype.v(m) == otype)

class Api(object):
    def __init__(self, tm):
        self.F = NodeFeatures()
        self.E = EdgeFeatures()
        self.C = Computeds()
        self.info = tm.info
        self.error = tm.error
        self.zero = tm.reset

    def Fs(self, fName):
        if not hasattr(self.F, fName):
            self.tm.error('Node feature "{}" not loaded'.format(fName))
            return None
        return getattr(self.F, fName)

    def Es(self, fName):
        if not hasattr(self.E, fName):
            self.tm.error('Edge feature "{}" not loaded'.format(fName))
            return None
        return getattr(self.E, fName)

    def Cs(self, fName):
        if not hasattr(self.C, fName):
            self.tm.error('Computed feature "{}" not loaded'.format(fName))
            return None
        return getattr(self.C, fName)
    
    def N(self):
        for n in self.C.order.data: yield n

    def sorted(self, nodeSet):
        Crank = self.C.rank.data
        return sorted(nodeSet, key=lambda n: Crank[n])

    def Fall(self): return sorted(x[0] for x in self.F.__dict__.items())
    def Eall(self): return sorted(x[0] for x in self.E.__dict__.items())
    def Call(self): return sorted(x[0] for x in self.C.__dict__.items())

def addOtype(api):
    setattr(api.F.otype, 'all', tuple(o[0] for o in api.C.levels.data))

def addLayer(api):
    api.L = Layer(api)

def makeInverse(data):
    inverse = {}
    for n in data:
        for m in data[n]:
            inverse.setdefault(m, set()).add(n)
    return inverse

def makeInverseVal(data):
    inverse = {}
    for n in data:
        for (m, val) in data[n].items():
            inverse.setdefault(m, {})[n] = val
    return inverse

