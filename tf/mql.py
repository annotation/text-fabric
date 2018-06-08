import os
import re
from functools import reduce
from .data import WARP
from .helpers import (
    cleanName,
    isClean,
    specFromRanges,
    rangesFromList,
    setFromSpec,
    nbytes,
)

# If a feature, with type string, has less than ENUM_LIMIT values,
# an enumeration type for it will be created
# provided all values of that feature are a valid name for MQL.

ENUM_LIMIT = 1000

ONE_ENUM_TYPE = True


class MQL(object):
  def __init__(self, mqlDir, mqlName, tfFeatures, tm):
    self.mqlDir = mqlDir
    cleanDb = cleanName(mqlName)
    if cleanDb != mqlName:
      self.tm.error('db name "{}" => "{}"'.format(mqlName, cleanDb))
    self.mqlName = cleanDb
    self.tfFeatures = tfFeatures
    self.tm = tm
    self.enums = {}
    self._check()

  def write(self):
    if not self.good:
      return
    if not os.path.exists(self.mqlDir):
      try:
        os.makedirs(self.mqlDir, exist_ok=True)
      except Exception:
        self.tm.error('Cannot create directory "{}"'.format(self.mqlDir))
        self.good = False
        return
    mqlPath = '{}/{}.mql'.format(self.mqlDir, self.mqlName)
    try:
      fm = open(mqlPath, 'w', encoding='utf8')
    except Exception:
      self.tm.error('Could not write to {}'.format(mqlPath))
      self.good = False
      return

    self.tm.info('Loading {} features'.format(len(self.featureList)))
    for ft in self.featureList:
      fObj = self.features[ft]
      fObj.load()

    self.fm = fm
    self._writeStartDb()
    self._writeEnums()
    self._writeTypes()
    self._writeDataAll()
    self._writeEndDb()
    self.tm.indent(level=0)
    self.tm.info('Done')

  def _check(self):
    self.tm.info('Checking features of dataset {}'.format(self.mqlName))
    self.features = {}
    self.featureList = []
    self.tm.indent(level=1)
    for (f, fo) in sorted(self.tfFeatures.items()):
      if fo.method is not None or f in WARP:
        continue
      fo.load(metaOnly=True)
      if fo.isConfig:
        continue
      cleanF = cleanName(f)
      if cleanF != f:
        self.tm.error('feature "{}" => "{}"'.format(f, cleanF))
      self.featureList.append(cleanF)
      self.features[cleanF] = fo
    good = True
    for feat in (WARP[0], WARP[1], '__levels__'):
      if feat not in self.tfFeatures:
        self.tm.error(
            '{} feature {} is missing from data set'.format(
                'Warp' if feat in WARP else 'Computed' if feat.startswith('__') else 'Data',
                feat,
            )
        )
        good = False
      else:
        fObj = self.tfFeatures[feat]
        if not fObj.load():
          good = False
    self.tm.indent(level=0)
    if (not good):
      self.tm.error('Export to MQL aborted')
    else:
      self.tm.info('{} features to export to MQL ...'.format(len(self.featureList)))
    self.good = good

  def _writeStartDb(self):
    self.fm.write(
        '''
CREATE DATABASE '{name}'
GO
USE DATABASE '{name}'
GO
'''.format(name=self.mqlName)
    )

  def _writeEndDb(self):
    self.fm.write('''
VACUUM DATABASE ANALYZE
GO
''')
    self.fm.close()

  def _writeEnums(self):
    self.tm.indent(level=0)
    self.tm.info('Writing enumerations')
    self.tm.indent(level=1)
    for ft in self.featureList:
      fObj = self.features[ft]
      if fObj.isEdge or fObj.dataType == 'int':
        continue
      fMap = fObj.data
      fValues = sorted(set(fMap.values()))
      if len(fValues) > ENUM_LIMIT:
        continue
      eligible = all(isClean(fVal) for fVal in fValues)
      if not eligible:
        unclean = [fVal for fVal in fValues if not isClean(fVal)]
        print(
            '\t{:<15}: {:>4} values, {} not a name, e.g. «{}»'.format(
                ft,
                len(fValues),
                len(unclean),
                unclean[0],
            )
        )
        continue
      self.enums[ft] = fValues

    if ONE_ENUM_TYPE:
      self._writeEnumsAsOne()
    else:
      for ft in sorted(self.enums):
        self._writeEnum(ft)
      self.tm.indent(level=0)
      self.tm.info('Written {} enumerations'.format(len(self.enums)))

  def _writeEnumsAsOne(self):
    fValues = reduce(
        set.union,
        (set(fV) for fV in self.enums.values()),
        set(),
    )
    self.tm.info('Writing an all-in-one enum with {:>4} values'.format(len(fValues)))
    fValuesEnumerated = ',\n\t'.join('{} = {}'.format(fVal, i) for (i, fVal) in enumerate(fValues))
    self.fm.write('''
CREATE ENUMERATION all_enum = {{
    {}
}}
GO
'''.format(fValuesEnumerated))

  def _writeEnum(self, ft):
    fValues = self.enums[ft]
    self.tm.info('enum {:<15} with {:>4} values'.format(ft, len(fValues)))
    fValuesEnumerated = ',\n\t'.join('{} = {}'.format(fVal, i) for (i, fVal) in enumerate(fValues))
    self.fm.write(
        '''
CREATE ENUMERATION {}_enum = {{
    {}
}}
GO
'''.format(ft, fValuesEnumerated)
    )

  def _writeTypes(self):
    def valInt(n):
      return str(n)

    def valStr(s):
      if "'" in s:
        return '"{}"'.format(s.replace('"', '\\"'))
      else:
        return "'{}'".format(s)

    def valIds(ids):
      return '({})'.format(','.join(str(i) for i in ids))

    self.levels = self.tfFeatures['__levels__'].data[::-1]
    self.tm.indent(level=0)
    self.tm.info(
        'Mapping {} features onto {} object types'.format(
            len(self.featureList),
            len(self.levels),
        )
    )
    otypeSupport = {}
    for (otype, av, start, end) in self.levels:
      cleanOtype = cleanName(otype)
      if cleanOtype != otype:
        self.tm.error('otype "{}" => "{}"'.format(otype, cleanOtype))
      otypeSupport[cleanOtype] = set(range(start, end + 1))

    self.otypes = {}
    self.featureTypes = {}
    self.featureMethods = {}
    for ft in self.featureList:
      fObj = self.features[ft]
      if fObj.isEdge:
        dataType = 'LIST OF id_d'
        method = valIds
      else:
        if fObj.dataType == 'str':
          dataType = 'string DEFAULT ""'
          method = valInt if ft in self.enums else valStr
        elif fObj.dataType == 'int':
          dataType = 'integer DEFAULT 0'
          method = valInt
        else:
          dataType = 'string DEFAULT ""'
          method = valStr
      self.featureTypes[ft] = dataType
      self.featureMethods[ft] = method

      support = set(fObj.data.keys())
      for otype in otypeSupport:
        if len(support & otypeSupport[otype]):
          self.otypes.setdefault(otype, []).append(ft)

    for otype in (cleanName(x[0]) for x in self.levels):
      self._writeType(otype)

  def _writeType(self, otype):
    self.fm.write('''
CREATE OBJECT TYPE
[{}
'''.format(otype))
    for ft in self.otypes[otype]:
      fType = '{}_enum'.format('all' if ONE_ENUM_TYPE else ft
                               ) if ft in self.enums else self.featureTypes[ft]
      self.fm.write('  {}:{};\n'.format(ft, fType))
    self.fm.write('''
]
GO
''')

  def _writeDataAll(self):
    self.tm.info(
        'Writing {} features as data in {} object types'.format(
            len(self.featureList),
            len(self.levels),
        )
    )
    self.oslots = self.tfFeatures[WARP[1]].data
    for (otype, av, start, end) in self.levels:
      self._writeData(otype, start, end)

  def _writeData(self, otype, start, end):
    tm = self.tm
    fm = self.fm
    tm.indent(level=1, reset=True)
    tm.info('{} data ...'.format(otype))
    oslots = self.oslots
    maxSlot = oslots[-1]
    oFeats = self.otypes[otype]
    features = self.features
    featureMethods = self.featureMethods
    fm.write(
        '''
DROP INDEXES ON OBJECT TYPE[{o}]
GO
CREATE OBJECTS
WITH OBJECT TYPE[{o}]
'''.format(o=otype)
    )
    curSize = 0
    LIMIT = 50000
    t = 0
    j = 0
    tm.indent(level=2, reset=True)
    for n in range(start, end + 1):
      oMql = '''
CREATE OBJECT
FROM MONADS= {{ {m} }}
WITH ID_D={i} [
'''.format(
          m=n if n <= maxSlot else specFromRanges(rangesFromList(oslots[n - maxSlot - 1])),
          i=n,
      )
      for ft in oFeats:
        method = featureMethods[ft]
        fMap = features[ft].data
        if n in fMap:
          oMql += '{}:={};\n'.format(ft, method(fMap[n]))
      oMql += '''
]
'''
      fm.write(oMql)
      curSize += len(bytes(oMql, encoding='utf8'))
      t += 1
      j += 1
      if j == LIMIT:
        fm.write('''
GO
CREATE OBJECTS
WITH OBJECT TYPE[{o}]
'''.format(o=otype))
        tm.info('batch of size {:>20} with {:>7} of {:>7} {}s'.format(nbytes(curSize), j, t, otype))
        j = 0
        curSize = 0

    tm.info('batch of size {:>20} with {:>7} of {:>7} {}s'.format(nbytes(curSize), j, t, otype))
    fm.write('''
GO
CREATE INDEXES ON OBJECT TYPE[{o}]
GO
'''.format(o=otype))

    tm.indent(level=1)
    tm.info('{} data: {} objects'.format(otype, t))


# MQL IMPORT

uniscan = re.compile(r'(?:\\x..)+')


def makeuni(match):
  ''' Make proper unicode of a text that contains byte escape codes
        such as backslash xb6
    '''
  byts = eval('"' + match.group(0) + '"')
  return byts.encode('latin1').decode('utf-8')


def uni(line):
  return uniscan.sub(makeuni, line)


def tfFromMql(mqlFile, tm, slotType=None, otext=None, meta=None):
  if slotType is None:
    tm.error('ERROR: no slotType specified')
    return (False, {}, {}, {})
  (good, objectTypes, tables, edgeF, nodeF) = parseMql(mqlFile, tm)
  if not good:
    return (False, {}, {}, {})
  return tfFromData(tm, objectTypes, tables, edgeF, nodeF, slotType, otext, meta)


def parseMql(mqlFile, tm):
  tm.info('Parsing mql source ...')
  fh = open(mqlFile)

  objectTypes = dict()
  tables = dict()

  edgeF = dict()
  nodeF = dict()

  curId = None
  curEnum = None
  curObjectType = None
  curTable = None
  curObject = None
  curValue = None
  curFeature = None
  seeObjects = False

  inObjectTypeFeatures = False

  STRING_TYPES = {'ascii', 'string'}

  enums = dict()

  chunkSize = 1000000
  inThisChunk = 0

  good = True

  for (ln, line) in enumerate(fh):
    inThisChunk += 1
    if inThisChunk == chunkSize:
      tm.info('\tline {:>9}'.format(ln + 1))
      inThisChunk = 0
    if line.startswith('CREATE OBJECTS WITH OBJECT TYPE') or line.startswith('WITH OBJECT TYPE'):
      comps = line.rstrip().rstrip(']').split('[', 1)
      curTable = comps[1]
      tm.info('\t\tobjects in {}'.format(curTable))
      curObject = None
      if curTable not in tables:
        tables[curTable] = dict()
      seeObjects = True
    elif line == 'CREATE OBJECT\n':
      curObject = None
      curObject = dict(feats=dict(), monads=None)
      curId = None
      seeObjects = True
    elif curEnum is not None:
      if line.startswith('}'):
        curEnum = None
        continue
      comps = line.strip().rstrip(',').split('=', 1)
      comp = comps[0].strip()
      words = comp.split()
      if words[0] == 'DEFAULT':
        enums[curEnum]['default'] = uni(words[1])
        value = words[1]
      else:
        value = words[0]
      enums[curEnum]['values'].append(value)
    elif curObjectType is not None:
      if line.startswith(']'):
        curObjectType = None
        inObjectTypeFeatures = False
        continue
      if curObjectType is True:
        if line.startswith('['):
          curObjectType = line.rstrip()[1:]
          objectTypes[curObjectType] = dict()
          tm.info('\t\totype {}'.format(curObjectType))
          inObjectTypeFeatures = True
          continue
      if inObjectTypeFeatures:
        comps = line.strip().rstrip(';').split(':', 1)
        feature = comps[0].strip()
        fInfo = comps[1].strip()
        fCleanInfo = fInfo.replace('FROM SET', '')
        fInfoComps = fCleanInfo.split(' ', 1)
        fMQLType = fInfoComps[0]
        if len(fInfoComps) == 2:
          fDefaultComps = fInfoComps[1].strip().split(' ', 1)
          fDefault = fDefaultComps[1] if len(fDefaultComps) > 1 else None
        else:
          fDefault = None
        if fDefault is not None and fMQLType in STRING_TYPES:
          fDefault = uni(fDefault[1:-1])
        default = enums.get(fMQLType, {}).get('default', fDefault)
        ftype = 'str' if fMQLType in enums else\
                'int' if fMQLType == 'integer' else\
                'str' if fMQLType in STRING_TYPES else\
                'int' if fInfo == 'id_d' else\
                'str'
        isEdge = fMQLType == 'id_d'
        if isEdge:
          edgeF.setdefault(curObjectType, set()).add(feature)
        else:
          nodeF.setdefault(curObjectType, set()).add(feature)

        objectTypes[curObjectType][feature] = (ftype, default)
        tm.info(
            '\t\t\tfeature {} ({}) =def= {} : {}'.format(
                feature, ftype, default, 'edge' if isEdge else 'node'
            )
        )
    elif seeObjects:
      if curObject is not None:
        if line.startswith(']'):
          objectType = objectTypes[curTable]
          for (feature, (ftype, default)) in objectType.items():
            if feature not in curObject['feats'] and default is not None:
              curObject['feats'][feature] = default
          tables[curTable][curId] = curObject
          curObject = None
          continue
        elif line.startswith('['):
          name = line.rstrip()[1:]
          if len(name):
            curTable = name
            if curTable not in tables:
              tables[curTable] = dict()
        elif line.startswith('FROM MONADS'):
          monads = line.split('=', 1)[1].replace('{', '').replace('}', '').replace(' ', '').strip()
          curObject['monads'] = setFromSpec(monads)
        elif line.startswith('WITH ID_D'):
          comps = line.replace('[', '').rstrip().split('=', 1)
          curId = int(comps[1])
        elif line.startswith('GO'):
          pass
        elif line.strip() == '':
          pass
        else:
          if curValue is not None:
            toBeContinued = not line.rstrip().endswith('";')
            if toBeContinued:
              curValue += line
            else:
              curValue += line.rstrip().rstrip(';').rstrip('"')
              curObject['feats'][curFeature] = uni(curValue)
              curValue = None
              curFeature = None
            continue
          if ':=' in line:
            (featurePart, valuePart) = line.split('=', 1)
            feature = featurePart[0:-1].strip()
            valuePart = valuePart.lstrip()
            isText = ':="' in line
            toBeContinued = isText and not line.rstrip().endswith('";')
            if toBeContinued:
              # this happens if a feature value
              # contains a new line
              # we must continue scanning lines
              # until we meet the end of the value
              curFeature = feature
              curValue = valuePart.lstrip('"')
            else:
              value = valuePart.rstrip().rstrip(';').strip('"')
              curObject['feats'][feature] = uni(value) if isText else value
          else:
            tm.error('ERROR: line {}: unrecognized line -->{}<--'.format(ln, line))
            good = False
            break
      else:
        if line.startswith('CREATE OBJECT'):
          curObject = dict(feats=dict(), monads=None)
          curId = None
    else:
      if line.startswith('CREATE ENUMERATION'):
        words = line.split()
        curEnum = words[2]
        enums[curEnum] = dict(default=None, values=[])
        tm.info('\t\tenum {}'.format(curEnum))
      elif line.startswith('CREATE OBJECT TYPE'):
        curObjectType = True
        inObjectTypeFeatures = False
  tm.info('{} lines parsed'.format(ln + 1))
  fh.close()
  for table in tables:
    tm.info('{} objects of type {}'.format(len(tables[table]), table))

  if len(tables) == 0:
    tm.info('No objects found')
  return (good, objectTypes, tables, nodeF, edgeF)


def tfFromData(tm, objectTypes, tables, nodeF, edgeF, slotType, otext, meta):
  tm.info('Making TF data ...')

  NIL = {'nil', 'NIL', 'Nil'}

  tableOrder = [slotType] + [t for t in sorted(tables) if t != slotType]

  iddFromMonad = dict()
  slotFromMonad = dict()

  nodeFromIdd = dict()
  iddFromNode = dict()

  nodeFeatures = dict()
  edgeFeatures = dict()
  metaData = dict()

  # metadata that ends up in every feature
  metaData[''] = {} if meta is None else meta

  # the config feature otext
  metaData['otext'] = otext

  good = True

  tm.info('Monad - idd mapping ...')
  for idd in tables.get(slotType, {}):
    monad = list(tables[slotType][idd]['monads'])[0]
    iddFromMonad[monad] = idd

  tm.info('Removing holes in the monad sequence')
  # we set up a monad - slot mapping
  curSlot = 0
  otype = dict()
  for monad in sorted(iddFromMonad):
    curSlot += 1
    slotFromMonad[monad] = curSlot
    idd = iddFromMonad[monad]
    nodeFromIdd[idd] = curSlot
    iddFromNode[curSlot] = idd
    otype[curSlot] = slotType

  maxSlot = curSlot
  tm.info('maxSlot={}'.format(maxSlot))

  tm.info('Node mapping and otype ...')
  node = maxSlot
  for t in tableOrder[1:]:
    for idd in sorted(tables[t]):
      node += 1
      nodeFromIdd[idd] = node
      iddFromNode[node] = idd
      otype[node] = t

  nodeFeatures['otype'] = otype
  metaData['otype'] = dict(valueType='str', )

  tm.info('oslots ...')
  oslots = dict()
  for t in tableOrder[1:]:
    for idd in tables.get(t, {}):
      node = nodeFromIdd[idd]
      monads = tables[t][idd]['monads']
      oslots[node] = {slotFromMonad[m] for m in monads}
  edgeFeatures['oslots'] = oslots
  metaData['oslots'] = dict(valueType='str', )

  tm.info('metadata ...')
  for t in nodeF:
    for f in nodeF[t]:
      ftype = objectTypes[t][f][0]
      metaData.setdefault(f, {})['valueType'] = ftype
  for t in edgeF:
    for f in edgeF[t]:
      metaData.setdefault(f, {})['valueType'] = 'str'

  tm.info('features ...')
  chunkSize = 100000
  for t in tableOrder:
    tm.info('\tfeatures from {}s'.format(t))
    inThisChunk = 0
    thisTable = tables.get(t, {})
    for (i, idd) in enumerate(thisTable):
      inThisChunk += 1
      if inThisChunk == chunkSize:
        tm.info('\t{:>9} {}s'.format(i + 1, t))
        inThisChunk = 0
      node = nodeFromIdd[idd]
      features = tables[t][idd]['feats']
      for (f, v) in features.items():
        isEdge = f in edgeF.get(t, set())
        if isEdge:
          if v not in NIL:
            edgeFeatures.setdefault(f, {}).setdefault(node, set()).add(nodeFromIdd[int(v)])
        else:
          nodeFeatures.setdefault(f, {})[node] = v
    tm.info('\t{:>9} {}s'.format(len(thisTable), t))

  return (good, nodeFeatures, edgeFeatures, metaData)
