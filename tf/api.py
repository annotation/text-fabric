import collections

class Feature(object):
    def __init__(self, data=None):
        self.data = data

    def v(self, n): 
        if n in self.data:
            return data[n]
        return None

class Pre(object):
    def __init__(self, data=None):
        self.data = data
