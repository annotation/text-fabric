import os,collections
from glob import glob
from .data import Data, GRID, SECTIONS
from .helpers import *
from .timestamp import Timestamp
from .prepare import *
from .api import *
from .mql import MQL

NAME = 'Text-Fabric'
VERSION = '2.3.6'
APIREF = 'https://github.com/ETCBC/text-fabric/wiki/Api'
TUTORIAL = 'https://github.com/ETCBC/text-fabric/blob/master/docs/tutorial.ipynb'
DATA = 'https://github.com/ETCBC/text-fabric-data'
DATADOC = 'https://etcbc.github.io/text-fabric-data'
SHEBANQ = 'https://shebanq.ancient-data.org/text'
EMAIL = 'shebanq@ancient-data.org'
SLACK = 'https://shebanq.slack.com/signup'

LOCATIONS = [
    '~/Downloads/text-fabric-data',
    '~/text-fabric-data',
    '~/github/text-fabric-data',
]

DATASETS = [
    'hebrew/etcbc4c',
]

MODULES = [
    'core',
    'phono',
]

PRECOMPUTE = (
    (False, '__levels__'   , levels   ,  GRID[0:2]                                            ),
    (False, '__order__'    , order    ,  GRID[0:2]+  ('__levels__' ,                         )),
    (False, '__rank__'     , rank     , (GRID[0]  ,   '__order__'                            )),
    (False, '__levUp__'    , levUp    ,  GRID[0:2]+  (               '__rank__'  ,           )),
    (False, '__levDown__'  , levDown  , (GRID[0]  ,   '__levUp__'   ,'__rank__'              )),
    (False, '__boundary__' , boundary ,  GRID[0:2]+  (               '__rank__'  ,           )),
    (True,  '__sections__' , sections ,  GRID     +  ('__levUp__'   , '__levels__') + SECTIONS),
)

class Fabric(object):
    def __init__(self, locations=None, modules=None, silent=False):
        self.silent = silent
        self.tm = Timestamp()
        if not silent: self.tm.info('''This is {} {}
Api reference : {}
Tutorial      : {}
Data sources  : {}
Data docs     : {}
Shebanq docs  : {}
Slack team    : {}
Questions? Ask {} for an invite to Slack'''.format(
            NAME, VERSION, APIREF, TUTORIAL, DATA, DATADOC, SHEBANQ, SLACK, EMAIL,
        ), tm=False)
        self.good = True

        if modules == None: modules = []
        if type(modules) is str: modules = [x.strip() for x in itemize(modules, '\n')]
        self.modules = modules

        if locations == None: locations = LOCATIONS
        if type(locations) is str: locations = [x.strip() for x in itemize(locations, '\n')]
        self.homeDir = os.path.expanduser('~').replace('\\', '/')
        self.curDir = os.getcwd().replace('\\', '/')
        (self.parentDir, x) = os.path.split(self.curDir)
        self.locations = []
        for loc in locations:
            self.locations.append(expandDir(loc, dict(
                cur=self.curDir,
                up=self.parentDir,
                home=self.homeDir,
            )))

        self.locationRep = '\n\t'.join('\n\t'.join('{}/{}'.format(l,f) for f in self.modules) for l in self.locations)
        self.featuresRequested = []
        self._makeIndex()

    def load(self, features, add=False, silent=False):
        self.tm.indent(level=0, reset=True)
        if not silent: self.tm.info('loading features ...')
        self.sectionsOK = True
        self.good = True
        if self.good:
            featuresRequested = itemize(features) if type(features) is str else sorted(features)
            if add:
                self.featuresRequested += featuresRequested
            else:
                self.featuresRequested = featuresRequested
            for fName in list(GRID):
                self._loadFeature(fName, optional=fName==GRID[2], silent=silent)
        if self.good:
            self._cformats = {}
            self._formatFeats = []
            if GRID[2] in self.features:
                otextMeta = self.features[GRID[2]].metaData
                for otextMod in self.features:
                    if otextMod.startswith(GRID[2]+'@'):
                        self._loadFeature(otextMod, silent=silent)
                        otextMeta.update(self.features[otextMod].metaData)
                sectionFeats = itemize(otextMeta.get('sectionFeatures', ''), ',')
                sectionTypes = itemize(otextMeta.get('sectionTypes', ''), ',')
                if len(sectionTypes) != 3 or len(sectionFeats) != 3:
                    if not silent: self.tm.info('Not enough info for sections in {}, section functionality will not work'.format(GRID[2]))
                    self.sectionsOK = False
                else:
                    for (i, fName) in enumerate(sectionFeats):
                        self._loadFeature(fName, silent=silent)
                        if self.good:
                            self.features[SECTIONS[i]] = self.features[fName]
                if self.good:
                    (cformats, formatFeats) = collectFormats(otextMeta)
                    for fName in formatFeats:
                        self._loadFeature(fName, silent=silent)
                    self._cformats = cformats
                    self._formatFeats = formatFeats
            else:
                self.sectionsOK = False

        if self.good:
            self._precompute()
        if self.good:
            for fName in self.featuresRequested:
                self._loadFeature(fName, silent=silent)
        if not self.good:
            self.tm.indent(level=0)
            self.tm.error('Not all features could be loaded/computed')
            self.tm.cache()
            return None
        if add: self._updateApi(silent)
        else:
            return self._makeApi(silent)

    
    def explore(self, silent=True):
        nodes = set()
        edges = set()
        configs = set()
        computeds = set()
        for (fName, fObj) in self.features.items():
            fObj.load(metaOnly=True, silent=True)
            dest = None
            if fObj.method: dest = computeds
            elif fObj.isConfig: dest = configs
            elif fObj.isEdge: dest = edges
            else: dest = nodes
            dest.add(fName)
        if not silent: self.tm.info('Feature overview: {} for nodes; {} for edges; {} configs; {} computed'.format(
                len(nodes), len(edges), len(configs), len(computeds),
            ))
        self.featureSets = dict(nodes=nodes, edges=edges, configs=configs, computeds=computeds)

    def clearCache(self):
        for (fName, fObj) in self.features.items():
            fObj.cleanDataBin()

    def save(self, nodeFeatures={}, edgeFeatures={}, metaData={}, module=None):
        self.tm.indent(level=0, reset=True)
        self._getWriteLoc(module=module)
        configFeatures = dict(f for f in metaData.items() if f[0] != '' and f[0] not in nodeFeatures and f[0] not in edgeFeatures)
        if not self.silent: self.tm.info('Exporting {} node and {} edge and {} config features to {}:'.format(
            len(nodeFeatures), len(edgeFeatures), len(configFeatures), self.writeDir,
        ))
        todo = []
        for (fName, data) in sorted(nodeFeatures.items()):
            todo.append((fName, data, False, False))
        for (fName, data) in sorted(edgeFeatures.items()):
            todo.append((fName, data, True, False))
        for (fName, data) in sorted(configFeatures.items()):
            todo.append((fName, data, None, True))
        reduced = 0
        total = collections.Counter()
        failed = collections.Counter()
        for (fName, data, isEdge, isConfig) in todo:
            fMeta = metaData.get(fName, metaData.get('', {})) 
            fObj = Data('{}/{}.tf'.format(self.writeDir, fName), self.tm,
                data=data, metaData=fMeta,
                isEdge=isEdge, isConfig=isConfig,
            )
            tag = 'config' if isConfig else 'edge' if isEdge else 'node'
            if fObj.save(nodeRanges=fName==GRID[0], overwrite=True):
                total[tag] += 1
            else:
                failed[tag] += 1
        self.tm.indent(level=0)
        if not self.silent: self.tm.info('Exported {} node features and {} edge features and {} config features to {}'.format(
            total['node'], total['edge'], total['config'], self.writeDir,
        ))
        if len(failed):
            for (tag, nf) in sorted(failed.items()):
                self.tm.error('Failed to export {} {} features'.format(nf, tag))

    def exportMQL(self, mqlName, mqlDir):
        self.tm.indent(level=0, reset=True)
        mqlDir = expandDir(mqlDir, dict(
            cur=self.curDir,
            up=self.parentDir,
            home=self.homeDir,
        ))

        mqlNameClean = cleanName(mqlName)
        mql = MQL(mqlDir, mqlName, self.features, self.tm)
        mql.write()

    def _loadFeature(self, fName, optional=False, silent=False):
        if not self.good: return False
        if fName not in self.features:
            if not optional:
                self.tm.error('Feature "{}" not available in\n{}'.format(fName, self.locationRep))
                self.good = False
        else:
            if not self.features[fName].load(silent=silent or (fName not in self.featuresRequested)):
                self.good = False

    def _makeIndex(self):
        self.features = {}
        self.featuresIgnored = {}
        tfFiles = {}
        for loc in self.locations:
            for mod in self.modules:
                files = glob('{}/{}/*.tf'.format(loc, mod))
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
        self._getWriteLoc()
        if not self.silent: self.tm.info('{} features found and {} ignored'.format(
            len(tfFiles),
            sum(len(x) for x in self.featuresIgnored.values()),
        ), tm=False)

        good = True
        for fName in GRID:
            if fName not in self.features:
                if fName == GRID[2]:
                    if not self.silent: self.tm.info('Grid feature "{}" not found. Working without Text-API\n'.format(GRID[2]))
                else:
                    self.tm.error('Grid feature "{}" not found in\n{}'.format(fName, self.locationRep))
                    good = False
        if not good: return False
        self.gridDir = self.features[GRID[0]].dirName
        self.precomputeList = []
        for (dep2, fName, method, dependencies) in PRECOMPUTE:
            thisGood = True
            if dep2 and GRID[2] not in self.features: continue
            for dep in dependencies:
                if dep not in self.features:
                    self.tm.error('Missing dependency for computed data feature "{}": "{}"'.format(fName, dep))
                    thisGood = False
            if not thisGood: good = False
            self.features[fName] = Data(
                '{}/{}.x'.format(self.gridDir, fName), 
                self.tm,
                method=method,
                dependencies=[self.features.get(dep, None) for dep in dependencies],
            )
            self.precomputeList.append((fName, dep2))
        self.good = good

    def _getWriteLoc(self, dirName=None, module=None):
        writeLoc = dirName if dirName != None else '' if len(self.locations) == 0 else self.locations[-1]
        writeMod = module if module != None else '' if len(self.modules) == 0 else self.modules[-1]
        self.writeDir = '{}{}'.format(writeLoc, writeMod) if writeLoc == '' or writeMod == '' else '{}/{}'.format(writeLoc, writeMod)

    def _precompute(self):
        good = True
        for (fName, dep2) in self.precomputeList:
            if dep2 and not self.sectionsOK: continue
            if not self.features[fName].load(silent=True):
                good = False
                break
        self.good = good

    def _makeApi(self, silent):
        if not self.good: return None
        api = Api(self)
         
        setattr(api.F, GRID[0], OtypeFeature(api,  self.features[GRID[0]].data))
        setattr(api.E, GRID[1], OslotsFeature(api, self.features[GRID[1]].data))

        for fName in self.features:
            fObj = self.features[fName]
            if fObj.dataLoaded and not fObj.isConfig:
                if fObj.method:
                    feat = fName.strip('_')
                    ap = api.C
                    if fName in [x[0] for x in self.precomputeList if not x[1] or self.sectionsOK]:
                        setattr(ap, feat, Computed(api, fObj.data))
                    else:
                        fObj.unload()
                        if hasattr(ap, feat): delattr(api.C, feat)
                else:
                    if fName in self.featuresRequested:
                        if fName in GRID: continue
                        elif fObj.isEdge:
                            setattr(api.E, fName, EdgeFeature(api, fObj.data, fObj.edgeValues))
                        else:
                            setattr(api.F, fName, NodeFeature(api, fObj.data))
                    else:
                        if fName in GRID or fName in SECTIONS or fName in self._formatFeats: continue
                        elif fObj.isEdge:
                            if hasattr(api.E, fName): delattr(api.E, fName)
                        else:
                            if hasattr(api.F, fName): delattr(api.F, fName)
                        fObj.unload()
        addSortKey(api)
        addOtype(api)
        addLocality(api)
        addText(api, self)
        addSearch(api, self, silent)
        self.tm.indent(level=0)
        if not silent: self.tm.info('All features loaded/computed - for details use loadLog()')
        self.api = api
        return api

    def _updateApi(self, silent):
        if not self.good: return None
        api = self.api
         
        for fName in self.features:
            fObj = self.features[fName]
            if fObj.dataLoaded and not fObj.isConfig:
                if not fObj.method:
                    if fName in self.featuresRequested:
                        if fName in GRID: continue
                        elif fObj.isEdge:
                            if not hasattr(api.E, fName):
                                setattr(api.E, fName, EdgeFeature(api, fObj.data, fObj.edgeValues))
                        else:
                            if not hasattr(api.F, fName):
                                setattr(api.F, fName, NodeFeature(api, fObj.data))
                    else:
                        if fName in GRID or fName in SECTIONS or fName in self._formatFeats: continue
                        elif fObj.isEdge:
                            if hasattr(api.E, fName): delattr(api.E, fName)
                        else:
                            if hasattr(api.F, fName): delattr(api.F, fName)
                        fObj.unload()
        self.tm.indent(level=0)
        if not silent: self.tm.info('All additional features loaded - for details use loadLog()')

