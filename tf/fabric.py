import os
from glob import glob
from .data import Data
from .helpers import *
from .timestamp import Timestamp
from .prepare import *
from .api import Pre, Feature

LOCATIONS = ['~/Downloads', '~', '~/text-fabric-data', '.']

SKELETON = (
    '__otype__',
    '__monads__',
)

PRECOMPUTE = (
    ('__levels__', levels,  SKELETON                  ),
    ('__order__',  order,   SKELETON   +('__levels__',)),
    ('__rank__',   rank,   (SKELETON[0], '__order__'  )),
)

class Fabric(object):
    def __init__(self, locations=[]):
        self.tm = Timestamp()
        if type(locations) is str: locations = locations.strip().split()
        self.locations = []
        self.homeDir = os.path.expanduser('~').replace('\\', '/')
        self.curDir = os.getcwd().replace('\\', '/')
        (self.parentDir, x) = os.path.split(self.curDir)
        for loc in LOCATIONS + locations:
            if loc.startswith('~'):
                loc = loc.replace('~', self.homeDir, 1)
            elif loc.startswith('..'):
                loc = loc.replace('..', self.parentDir, 1)
            elif loc.startswith('.'):
                loc = loc.replace('.', self.curDir, 1)
            self.locations.append(loc)
        self.locationRep = '\n\t'.join(self.locations)
        self._makeIndex()

    def load(self, features):
        if not self.good: return
        self._precompute()
        if not self.good: return

        if type(features) is str: features = features.strip().split()
        good = True
        for featureName in features:
            if not self._loadFeature(featureName):
                good = False
        if good:
            self.tm.info('All features loaded/computed\n')
        else:
            self.tm.error('Not all features could be loaded/computed\n')
            self.good = False
        return self._makeApi()

    def _loadFeature(self, featureName):
        if not self.good: return False
        if featureName not in self.features:
            self.tm.error('Feature "{}" not available in\n\t{}\n'.format(featureName, self.locationRep))
            return False
        return self.features[featureName].load()

    def _makeIndex(self):
        self.tm.info('Looking for available data features:\n')
        self.features = {}
        tfFiles = {}
        for loc in self.locations:
            files = glob('{}/*.tf'.format(loc))
            for f in files:
                if not os.path.isfile(f):
                    continue
                (dirF, fileF) = os.path.split(f)
                (featureName, ext) = os.path.splitext(fileF)
                tfFiles.setdefault(featureName, []).append(f)
        for (featureName, featurePaths) in sorted(tfFiles.items()):
            for (i, featurePath) in enumerate(featurePaths):
                self.tm.info('{:<1} {:<20} from {}\n'.format('X' if i < len(featurePaths)-1 else '', featureName, featurePath))
            self.features[featureName] = Data(featurePaths[-1])  
        self.tm.info('{} features found\n'.format(len(tfFiles)))

        good = True
        for featureName in SKELETON:
            if featureName not in self.features:
                self.tm.error('Skeleton feature "{}" not found in\n\t{}\n'.format(featureName, self.locationRep))
                good = False
        if not good: return False
        self.skeletonDir = self.features[SKELETON[0]].dirName
        self.precomputeList = []
        for (featureName, method, dependencies) in PRECOMPUTE:
            thisGood = True
            for dep in dependencies:
                if dep not in self.features:
                    self.tm.error('Missing dependency for computed data feature "{}": "{}"\n'.format(featureName, dep))
                    thisGood = False
            if not thisGood: good = False
            self.features[featureName] = Data(
                '{}/{}.x'.format(self.skeletonDir, featureName), 
                method=method,
                dependencies=[self.features.get(dep, None) for dep in dependencies],
            )
            self.precomputeList.append(featureName)
        self.good = good

    def _precompute(self):
        good = True
        for featureName in self.precomputeList:
            if not self.features[featureName].load():
                good = False
                break
        self.good = good

    def _makeApi(self):
        api = dict(
            F=dict(),
            P=dict(),
        )
        if not self.good: return api
        for featureName in self.features:
            featureObject = self.features[featureName]
            if featureObject.method:
                api['P'][featureName] = Pre(featureObject.data)
            else:
                api['F'][featureName] = Feature(featureObject.data)
        return api

