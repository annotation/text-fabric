import os
from glob import glob
from .data import Data, SKELETON
from .helpers import *
from .timestamp import Timestamp
from .prepare import *
from .api import *

LOCATIONS = [
    '~/Downloads',
    '~/text-fabric-data',
    '~/github/text-fabric-data',
    '~/github/text-fabric-data/hebrew/etcbc4c',
    '.',
]

PRECOMPUTE = (
    (True , '__levels__' , levels ,  SKELETON[0:2]                             ),
    (True , '__order__'  , order  ,  SKELETON[0:2]+ ('__levels__',            )),
    (True , '__rank__'   , rank   , (SKELETON[0]  ,  '__order__'              )),
    (True , '__levUp__'  , levUp  ,  SKELETON[0:2]+ ('__rank__'  ,            )),
    (True , '__levDown__', levDown, (SKELETON[0]  ,  '__levUp__' , '__rank__' )),
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
        self.tm.indent(level=0, reset=True)
        self.tm.info('loading features ...')
        if self.good:
            self._precompute()
        if self.good:
            self.featuresRequested = (features.strip().split() if type(features) is str else sorted(features))
            good = True
            for fName in list(SKELETON) + self.featuresRequested:
                if not self._loadFeature(fName):
                    good = False
            self.tm.indent(level=0)
            if good:
                self.tm.info('All features loaded/computed')
            else:
                self.tm.error('Not all features could be loaded/computed')
                self.good = False
        return self._makeApi()

    def loadExtra(self, features):
        self.tm.indent(level=0, reset=True)
        self.tm.info('loading extra features ...')
        if self.good:
            featuresRequested = (features.strip().split() if type(features) is str else sorted(features))
            good = True
            for fName in featuresRequested:
                if not self._loadFeature(fName):
                    good = False
            self.tm.indent(level=0)
            if good:
                self.tm.info('All extra features loaded/computed')
            else:
                self.tm.error('Not all extra features could be loaded/computed')
                self.good = False

    def save(self, nodeFeatures={}, edgeFeatures={}, metaData={}):
        self.tm.indent(level=0, reset=True)
        self.targetDir = self.locations[-1]
        configFeatures = dict(f for f in metaData.items() if f[0] != '' and f[0] not in nodeFeatures and f[0] not in edgeFeatures)
        self.tm.info('Exporting {} node and {} edge and {} config features to {}:'.format(
            len(nodeFeatures), len(edgeFeatures), len(configFeatures), self.targetDir,
        ))
        todo = []
        for (fName, data) in sorted(nodeFeatures.items()):
            todo.append((fName, data, False, False))
        for (fName, data) in sorted(edgeFeatures.items()):
            todo.append((fName, data, True, False))
        for (fName, data) in sorted(configFeatures.items()):
            todo.append((fName, data, None, True))
        reduced = 0
        total = 0
        for (fName, data, isEdge, isConfig) in todo:
            fMeta = metaData.get(fName, metaData.get('', {})) 
            fObj = Data('{}/{}.tf'.format(self.targetDir, fName), self.tm,
                data=data, metaData=fMeta,
                isEdge=isEdge, isConfig=isConfig,
            )
            fObj.save(nodeRanges=fName==SKELETON[0], overwrite=True)
        self.tm.indent(level=0)
        self.tm.info('Exported {} node features and {} edge features to {}:'.format(
            len(nodeFeatures), len(edgeFeatures), self.targetDir,
        ))

    def _loadFeature(self, fName):
        if not self.good: return False
        if fName not in self.features:
            self.tm.error('Feature "{}" not available in\n{}'.format(fName, self.locationRep))
            return False
        return self.features[fName].load()

    def _makeIndex(self):
        self.features = {}
        self.featuresIgnored = {}
        tfFiles = {}
        for loc in self.locations:
            files = glob('{}/*.tf'.format(loc))
            for f in files:
                if not os.path.isfile(f):
                    continue
                (dirF, fileF) = os.path.split(f)
                (fName, ext) = os.path.splitext(fileF)
                tfFiles.setdefault(fName, []).append(f)
        for (fName, featurePaths) in sorted(tfFiles.items()):
            chosenFPath = featurePaths[-1]
            for featurePath in sorted(set(featurePaths[0:-1])):
                if featurePath != chosenFPath:
                    self.featuresIgnored.setdefault(fName, []).append(featurePath)
            self.features[fName] = Data(chosenFPath, self.tm)  
        self.tm.info('{} features found and {} ignored'.format(
            len(tfFiles),
            sum(len(x) for x in self.featuresIgnored.values()),
        ), tm=False)

        good = True
        for fName in SKELETON:
            if fName not in self.features:
                self.tm.error('Skeleton feature "{}" not found in\n{}'.format(fName, self.locationRep))
                good = False
        if not good: return False
        self.skeletonDir = self.features[SKELETON[0]].dirName
        self.precomputeList = []
        for (retain, fName, method, dependencies) in PRECOMPUTE:
            thisGood = True
            for dep in dependencies:
                if dep not in self.features:
                    self.tm.error('Missing dependency for computed data feature "{}": "{}"'.format(fName, dep))
                    thisGood = False
            if not thisGood: good = False
            self.features[fName] = Data(
                '{}/{}.x'.format(self.skeletonDir, fName), 
                self.tm,
                method=method,
                dependencies=[self.features.get(dep, None) for dep in dependencies],
            )
            if retain:
                self.precomputeList.append(fName)
        self.good = good

    def _precompute(self):
        good = True
        for fName in self.precomputeList:
            if not self.features[fName].load():
                good = False
                break
        self.good = good

    def _makeApi(self):
        if not self.good: return None
        api = Api(self)
         
        setattr(api.F, SKELETON[0], OtypeFeature(api, self.features[SKELETON[0]].data))
        setattr(api.E, SKELETON[1], OslotsFeature(api, self.features[SKELETON[1]].data))

        for fName in self.features:
            fObj = self.features[fName]
            if fObj.dataLoaded and not fObj.isConfig:
                if fObj.method:
                    feat = fName.strip('_')
                    ap = api.C
                    if fName in self.precomputeList:
                        setattr(ap, feat, Computed(api, fObj.data))
                    else:
                        fObj.unload()
                        if hasattr(ap, feat): delattr(api.C, feat)
                else:
                    if fName in self.featuresRequested:
                        if fName in SKELETON: continue
                        elif fObj.isEdge:
                            setattr(api.E, fName, EdgeFeature(api, fObj.data, fObj.edgeValues))
                        else:
                            setattr(api.F, fName, NodeFeature(api, fObj.data))
                    else:
                        if fName in SKELETON: continue
                        elif fObj.isEdge:
                            if hasattr(api.E, fName): delattr(api.E, fName)
                        else:
                            if hasattr(api.F, fName): delattr(api.F, fName)
                        fObj.unload()
        addOtype(api)
        addLayer(api)
        addText(api, self)
        return api

