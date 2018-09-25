import os
import collections
from glob import glob
from .data import Data, WARP, MEM_MSG
from .helpers import itemize, expandDir, collectFormats, cleanName
from .timestamp import Timestamp
from .prepare import (levels, order, rank, levUp, levDown, boundary, sections)
from .api import (
    Api,
    NodeFeature,
    EdgeFeature,
    OtypeFeature,
    OslotsFeature,
    Computed,
    addSortKey,
    addOtype,
    addLocality,
    addRank,
    addText,
    addSearch,
)
from .mql import MQL, tfFromMql

NAME = 'Text-Fabric'
VERSION = '5.5.24'
DOI = '10.5281/zenodo.592193'
DOI_URL = 'https://doi.org/10.5281/zenodo.592193'
APIREF = 'https://dans-labs.github.io/text-fabric/Api/General/'
TUTORIAL = 'https://github.com/Dans-labs/text-fabric/blob/master/docs/tutorial.ipynb'
COMPOSE_URL = (
    'https://nbviewer.jupyter.org/github/dans-labs/'
    'text-fabric/blob/master/examples/compose.ipynb'
)
DATA = 'https://github.com/Dans-labs/text-fabric-data'

LOCATIONS = [
    '~/Downloads/text-fabric-data',
    '~/text-fabric-data',
    '~/github/text-fabric-data',
    '~/Dropbox/text-fabric-data',
    '/mnt/shared/text-fabric-data',
]

MODULES = [
    'core',
    'phono',
]

PRECOMPUTE = (
    (False, '__levels__', levels, WARP),
    (False, '__order__', order, WARP[0:2] + ('__levels__', )),
    (False, '__rank__', rank, (WARP[0], '__order__')),
    (False, '__levUp__', levUp, WARP[0:2] + ('__rank__', )),
    (False, '__levDown__', levDown, (WARP[0], '__levUp__', '__rank__')),
    (False, '__boundary__', boundary, WARP[0:2] + ('__rank__', )),
    (True, '__sections__', sections, WARP + ('__levUp__', '__levels__')),
)


class Fabric(object):
  def __init__(self, locations=None, modules=None, silent=False):
    self.silent = silent
    self.tm = Timestamp()
    self.banner = f'This is {NAME} {VERSION}'
    self.version = VERSION
    if not silent:
      self.tm.info(
          '''{}
Api reference : {}
Tutorial      : {}
Example data  : {}
'''.format(
              self.banner,
              APIREF,
              TUTORIAL,
              DATA,
          ),
          tm=False
      )
    self.good = True

    if modules is None:
      modules = ['']
    if type(modules) is str:
      modules = [x.strip() for x in itemize(modules, '\n')]
    self.modules = modules

    if locations is None:
      locations = LOCATIONS
    if type(locations) is str:
      locations = [x.strip() for x in itemize(locations, '\n')]
    self.homeDir = os.path.expanduser('~').replace('\\', '/')
    self.curDir = os.getcwd().replace('\\', '/')
    (self.parentDir, x) = os.path.split(self.curDir)
    self.locations = []
    for loc in locations:
      self.locations.append(
          expandDir(loc, dict(
              cur=self.curDir,
              up=self.parentDir,
              home=self.homeDir,
          ))
      )

    self.locationRep = '\n\t'.join(
        '\n\t'.join('{}/{}'.format(l, f) for f in self.modules) for l in self.locations
    )
    self.featuresRequested = []
    self._makeIndex()

  def load(self, features, add=False, silent=False):
    self.tm.indent(level=0, reset=True)
    if not silent:
      self.tm.info('loading features ...')
    self.sectionsOK = True
    self.good = True
    if self.good:
      featuresRequested = itemize(features) if type(features) is str else sorted(features)
      if add:
        self.featuresRequested += featuresRequested
      else:
        self.featuresRequested = featuresRequested
      for fName in list(WARP):
        self._loadFeature(fName, optional=fName == WARP[2], silent=silent)
    if self.good:
      self._cformats = {}
      self._formatFeats = []
      if WARP[2] in self.features:
        otextMeta = self.features[WARP[2]].metaData
        for otextMod in self.features:
          if otextMod.startswith(WARP[2] + '@'):
            self._loadFeature(otextMod, silent=silent)
            otextMeta.update(self.features[otextMod].metaData)
        sectionFeats = itemize(otextMeta.get('sectionFeatures', ''), ',')
        sectionTypes = itemize(otextMeta.get('sectionTypes', ''), ',')
        if len(sectionTypes) != 3 or len(sectionFeats) != 3:
          if not silent:
            self.tm.info(
                f'Not enough info for sections in {WARP[2]}, section functionality will not work'
            )
          self.sectionsOK = False
        else:
          for (i, fName) in enumerate(sectionFeats):
            self._loadFeature(fName, silent=silent)
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
      return False
    if add:
      try:
        self._updateApi(silent)
      except MemoryError:
        print(MEM_MSG)
        return False
    else:
      try:
        result = self._makeApi(silent)
      except MemoryError:
        print(MEM_MSG)
        return False
      return result

  def explore(self, silent=True, show=True):
    nodes = set()
    edges = set()
    configs = set()
    computeds = set()
    for (fName, fObj) in self.features.items():
      fObj.load(metaOnly=True, silent=True)
      dest = None
      if fObj.method:
        dest = computeds
      elif fObj.isConfig:
        dest = configs
      elif fObj.isEdge:
        dest = edges
      else:
        dest = nodes
      dest.add(fName)
    if not silent:
      self.tm.info(
          'Feature overview: {} for nodes; {} for edges; {} configs; {} computed'.format(
              len(nodes),
              len(edges),
              len(configs),
              len(computeds),
          )
      )
    self.featureSets = dict(nodes=nodes, edges=edges, configs=configs, computeds=computeds)
    if show:
      return dict((kind, tuple(sorted(kindSet)))
                  for (kind, kindSet) in sorted(self.featureSets.items(), key=lambda x: x[0]))

  def clearCache(self):
    for (fName, fObj) in self.features.items():
      fObj.cleanDataBin()

  def save(self, nodeFeatures={}, edgeFeatures={}, metaData={}, module=None):
    self.tm.indent(level=0, reset=True)
    self._getWriteLoc(module=module)
    configFeatures = dict(
        f for f in metaData.items()
        if f[0] != '' and f[0] not in nodeFeatures and f[0] not in edgeFeatures
    )
    if not self.silent:
      self.tm.info(
          'Exporting {} node and {} edge and {} config features to {}:'.format(
              len(nodeFeatures),
              len(edgeFeatures),
              len(configFeatures),
              self.writeDir,
          )
      )
    todo = []
    for (fName, data) in sorted(nodeFeatures.items()):
      todo.append((fName, data, False, False))
    for (fName, data) in sorted(edgeFeatures.items()):
      todo.append((fName, data, True, False))
    for (fName, data) in sorted(configFeatures.items()):
      todo.append((fName, data, None, True))
    total = collections.Counter()
    failed = collections.Counter()
    for (fName, data, isEdge, isConfig) in todo:
      edgeValues = False
      fMeta = {}
      fMeta.update(metaData.get('', {}))
      fMeta.update(metaData.get(fName, {}))
      if fMeta.get('edgeValues', False):
        edgeValues = True
      if 'edgeValues' in fMeta:
        del fMeta['edgeValues']
      fObj = Data(
          '{}/{}.tf'.format(self.writeDir, fName),
          self.tm,
          data=data,
          metaData=fMeta,
          isEdge=isEdge,
          isConfig=isConfig,
          edgeValues=edgeValues,
      )
      tag = 'config' if isConfig else 'edge' if isEdge else 'node'
      if fObj.save(nodeRanges=fName == WARP[0], overwrite=True):
        total[tag] += 1
      else:
        failed[tag] += 1
    self.tm.indent(level=0)
    if not self.silent:
      self.tm.info(
          'Exported {} node features and {} edge features and {} config features to {}'.format(
              total['node'],
              total['edge'],
              total['config'],
              self.writeDir,
          )
      )
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
    mql = MQL(mqlDir, mqlNameClean, self.features, self.tm)
    mql.write()

  def importMQL(self, mqlFile, slotType=None, otext=None, meta=None):
    self.tm.indent(level=0, reset=True)
    (good, nodeFeatures, edgeFeatures, metaData) = tfFromMql(
        mqlFile, self.tm, slotType=slotType, otext=otext, meta=meta
    )
    if good:
      self.save(nodeFeatures=nodeFeatures, edgeFeatures=edgeFeatures, metaData=metaData)

  def _loadFeature(self, fName, optional=False, silent=False):
    if not self.good:
      return False
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
    if not self.silent:
      self.tm.info(
          '{} features found and {} ignored'.format(
              len(tfFiles),
              sum(len(x) for x in self.featuresIgnored.values()),
          ),
          tm=False
      )

    good = True
    for fName in WARP:
      if fName not in self.features:
        if fName == WARP[2]:
          if not self.silent:
            self.tm.info((f'Warp feature "{WARP[2]}" not found. Working without Text-API\n'))
        else:
          if not self.silent:
            self.tm.error('Warp feature "{}" not found in\n{}'.format(fName, self.locationRep))
          good = False
      elif fName == WARP[2]:
        self._loadFeature(fName, optional=True, silent=True)
    if not good:
      return False
    self.warpDir = self.features[WARP[0]].dirName
    self.precomputeList = []
    for (dep2, fName, method, dependencies) in PRECOMPUTE:
      thisGood = True
      if dep2 and WARP[2] not in self.features:
        continue
      if dep2:
        otextMeta = self.features[WARP[2]].metaData
        sectionFeats = tuple(itemize(otextMeta.get('sectionFeatures', ''), ','))
        dependencies = dependencies + sectionFeats
      for dep in dependencies:
        if dep not in self.features:
          self.tm.error(f'Missing dependency for computed data feature "{fName}": "{dep}"')
          thisGood = False
      if not thisGood:
        good = False
      self.features[fName] = Data(
          '{}/{}.x'.format(self.warpDir, fName),
          self.tm,
          method=method,
          dependencies=[self.features.get(dep, None) for dep in dependencies],
      )
      self.precomputeList.append((fName, dep2))
    self.good = good

  def _getWriteLoc(self, dirName=None, module=None):
    writeLoc = dirName if dirName is not None else '' if len(self.locations
                                                             ) == 0 else self.locations[-1]
    writeMod = module if module is not None else '' if len(self.modules) == 0 else self.modules[-1]
    self.writeDir = (
        f'{writeLoc}{writeMod}' if writeLoc == '' or writeMod == '' else f'{writeLoc}/{writeMod}'
    )

  def _precompute(self):
    good = True
    for (fName, dep2) in self.precomputeList:
      if dep2 and not self.sectionsOK:
        continue
      if not self.features[fName].load(silent=True):
        good = False
        break
    self.good = good

  def _makeApi(self, silent):
    if not self.good:
      return None
    api = Api(self)

    setattr(api.F, WARP[0], OtypeFeature(api, self.features[WARP[0]].data))
    setattr(api.E, WARP[1], OslotsFeature(api, self.features[WARP[1]].data))

    sectionFeats = []
    if WARP[2] in self.features:
      otextMeta = self.features[WARP[2]].metaData
      sectionFeats = itemize(otextMeta.get('sectionFeatures', ''), ',')

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
            if hasattr(ap, feat):
              delattr(api.C, feat)
        else:
          if fName in self.featuresRequested:
            if fName in WARP:
              continue
            elif fObj.isEdge:
              setattr(api.E, fName, EdgeFeature(api, fObj.data, fObj.edgeValues))
            else:
              setattr(api.F, fName, NodeFeature(api, fObj.data))
          else:
            if (fName in WARP or fName in sectionFeats or fName in self._formatFeats):
              continue
            elif fObj.isEdge:
              if hasattr(api.E, fName):
                delattr(api.E, fName)
            else:
              if hasattr(api.F, fName):
                delattr(api.F, fName)
            fObj.unload()
    addSortKey(api)
    addOtype(api)
    addLocality(api)
    addRank(api)
    addText(api)
    addSearch(api, silent)
    self.tm.indent(level=0)
    if not silent:
      self.tm.info('All features loaded/computed - for details use loadLog()')
    self.api = api
    return api

  def _updateApi(self, silent):
    if not self.good:
      return None
    api = self.api

    sectionFeats = []
    if WARP[2] in self.features:
      otextMeta = self.features[WARP[2]].metaData
      sectionFeats = itemize(otextMeta.get('sectionFeatures', ''), ',')

    for fName in self.features:
      fObj = self.features[fName]
      if fObj.dataLoaded and not fObj.isConfig:
        if not fObj.method:
          if fName in self.featuresRequested:
            if fName in WARP:
              continue
            elif fObj.isEdge:
              if not hasattr(api.E, fName):
                setattr(api.E, fName, EdgeFeature(api, fObj.data, fObj.edgeValues))
            else:
              if not hasattr(api.F, fName):
                setattr(api.F, fName, NodeFeature(api, fObj.data))
          else:
            if (fName in WARP or fName in sectionFeats or fName in self._formatFeats):
              continue
            elif fObj.isEdge:
              if hasattr(api.E, fName):
                delattr(api.E, fName)
            else:
              if hasattr(api.F, fName):
                delattr(api.F, fName)
            fObj.unload()
    self.tm.indent(level=0)
    if not silent:
      self.tm.info('All additional features loaded - for details use loadLog()')
