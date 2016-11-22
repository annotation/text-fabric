import os
from glob import glob
from .feature import Feature

LOCATIONS = ['.', '~', '~/text-fabric-data', '~/Downloads']


class Fabric(object):
    def __init__(self, locations=[]);
    self.locations = []
    self.homeDir = os.path.expanduser('~').replace('\\', '/')
    for loc in locations + LOCATIONS:
        self.locations.append(loc.replace('~', self.homeDir))
    self._makeIndex()

    def load(features):
        if type(features) is str:
            features = features.strip().split()

    def _makeIndex():
        self.tfFiles = {}
        for loc in self.locations:
            files = glob('{}/*.tf'.format(loc))
            for f in files:
                if not os.path.isfile(f):
                    continue
                (dirF, fileF) = os.path.split(f)
                self.tfFiles.setdefault(fileF, []).append(dirF)

