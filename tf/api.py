import collections

class OtypeFeature(object):
    def __init__(self, data=None):
        self.data = data
        self.maxMonad = self.data[-1]

    def v(self, n): 
        if n < self.maxMonad + 1:
            return self.data[0]
        m = n - self.maxMonad - 1
        if m < len(self.data) - 2:
            return self.data[m]
        return None

class MonadsFeature(object):
    def __init__(self, data=None):
        self.data = data
        self.maxMonad = self.data[-1]

    def v(self, n): 
        if n < self.maxMonad + 1:
            return [n]
        m = n - self.maxMonad - 1
        if m < len(self.data) - 1:
            return self.data[m]
        return []

class Feature(object):
    def __init__(self, data=None):
        self.data = data

    def v(self, n): 
        if n in self.data:
            return self.data[n]
        return None

class Layer(object):
    def __init__(self, otypeFeature, levUp, levDown):
        self.otype = otypeFeature
        self.levUp = levUp
        self.levDown = levDown

    def u(self, otp, n): return tuple(m for m in self.levUp[n] if self.otype.v(m) == otp) 
    def d(self, otp, n):
        maxMonad = self.otype.data[-1]
        return tuple() if n < maxMonad+1 else tuple(m for m in self.levDown[n-maxMonad-1] if self.otype.v(m) == otp)

class Pre(object):
    def __init__(self, data=None):
        self.data = data
