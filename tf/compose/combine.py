import os
import collections

from ..fabric import Fabric
from ..core.data import WARP
from ..core.timestamp import Timestamp
from ..core.helpers import itemize

OTYPE = WARP[0]
OSLOTS = WARP[1]
OTEXT = WARP[2]

GENERATED = set('''
    writtenBy
    dateWritten
    version
'''.strip().split())

TM = Timestamp()
indent = TM.indent
info = TM.info
error = TM.error


def combine(
    locations,
    targetLocation,
    componentType=None,
    componentFeature=None,
    deleteTypes=None,
    mergeTypes=None,
    featureMeta=None,
    **otext,
):
  locations = sorted(locations)
  deleteTypes = set(
      []
      if not deleteTypes else
      itemize(deleteTypes) if type(deleteTypes) is str else list(deleteTypes)
  )
  nodeTypesComp = collections.defaultdict(dict)
  slotTypes = collections.defaultdict(dict)
  slotType = None
  offsets = collections.defaultdict(dict)
  nodeTypes = {}
  nodeFeatures = {}
  edgeFeatures = {}
  componentOslots = {}
  componentOtype = {}
  componentValue = collections.defaultdict(dict)
  metaData = collections.defaultdict(dict)
  if componentType:
    if not componentFeature:
      componentFeature = componentType
  else:
    if componentFeature:
      componentType = componentFeature

  srcs = {0: componentType}
  locs = {0: targetLocation}
  for (i, loc) in enumerate(locations):
    if type(loc) is str:
      locs[i + 1] = loc
      srcs[i + 1] = loc
    else:
      (name, loc) = loc
      locs[i + 1] = loc
      srcs[i + 1] = name
  locItems = sorted(x for x in locs.items() if x[0])

  def getApi(location, full=False):
    TF = Fabric(locations=location, silent=True)
    if full:
      api = TF.loadAll(silent=True)
    else:
      api = TF.load('', silent=True)
    if not api:
      error(f'Cannot load features of TF set in {location}', tm=False)
      return False
    return api

  def getMetas():
    meta = collections.defaultdict(
        lambda: collections.defaultdict(
            lambda: collections.defaultdict(set)
        )
    )

    for (feat, keys) in featureMeta.items():
      for (key, value) in keys.items():
        if value is not None:
          meta[feat][key][value] = {0}

    for (key, value) in otext.items():
      if value is not None:
        meta[OTEXT][key][value] = {0}

    if componentFeature:
      meta[componentFeature]['valueType']['str'] = {0}
      meta[componentFeature]['description'][f'label of {componentType}'] = {0}

    for (i, loc) in locItems:
      TF = Fabric(locations=loc, silent=True)
      for (feat, fObj) in TF.features.items():
        if fObj.method:
          continue
        fObj.load(metaOnly=True, silent=True)
        thisMeta = fObj.metaData
        for (k, v) in thisMeta.items():
          meta[feat][k][v].add(i)

    for (feat, ks) in meta.items():
      for (k, vs) in ks.items():
        isGenerated = k in GENERATED
        if k == 'valueType':
          if len(vs) > 1:
            info(f'WARNING: {feat}: valueType varies in components; will be str', tm=False)
          else:
            metaData[feat][k] = sorted(vs)[0]
        elif len(vs) == 1 and not isGenerated:
          metaData[feat][k] = sorted(vs)[0]
        else:
          hasCombinedValue = False
          for (v, iis) in vs.items():
            for i in iis:
              if i == 0 and not isGenerated:
                hasCombinedValue = True
                key = k
              else:
                key = f'{k}!{srcs[i]}'
              metaData[feat][key] = v
          if not hasCombinedValue and not isGenerated:
            info(f'WARNING: {feat}.{k} metadata varies across sources', tm=False)

    return True

  def getNtypes():
    nonlocal slotType
    nonlocal slotTypes

    clashes = set()

    good = True
    indent(level=1, reset=True)
    maxSlot = 0
    maxNode = 0

    for (i, loc) in locItems:
      info(f'\r{i:>3} {os.path.basename(loc)})', nl=False)
      api = getApi(loc)
      C = api.C
      nTypeInfo = C.levels.data
      for (t, (nType, av, nF, nT)) in enumerate(nTypeInfo):
        if nType == componentType:
          clashes.add(i)
        if t == len(nTypeInfo) - 1:
          slotTypes[nType][i] = (1, nT)
          if nType in deleteTypes:
            error(f'Slot type cannot be deleted: {nType}', tm=False)
            good = False
          maxSlot = nT
          maxNode = nT
        else:
          if nType not in deleteTypes:
            nodeTypesComp[nType][i] = (nF, nT)
            if nT > maxNode:
              maxNode = nT
      if componentType:
        nodeTypesComp[componentType][i] = (maxNode + 1, maxNode + 1)
        componentOslots[i] = maxSlot
        componentOtype[i] = maxNode + 1
        componentValue[i][maxNode + 1] = srcs[i]
    if len(slotTypes) > 1:
      error('Multiple slot types: {slotTypeRep}', tm=False)
      good = False
    commonTypes = set(slotTypes) & set(nodeTypesComp)
    if len(commonTypes):
      error('Some node types are slots in one source and non slots in another', tm=False)
      error(', '.sorted(commonTypes), tm=False)
      good = False
    if clashes:
      clashRep = ', '.join(f'{srcs[i]}' for i in clashes)
      error(f'Component type {componentType} occurs inside components {clashRep}', tm=False)
      good = False
    if good:
      slotType = list(slotTypes)[0]
      nodeTypesComp[slotType] = slotTypes[slotType]
      slotTypes = set(slotTypes[slotType])
    info('\r', tm=False, nl=False)
    info('done')
    return good

  def getOffsets():
    curOffset = 0
    for i in sorted(slotTypes):
      offsets[slotType][i] = curOffset
      curOffset += nodeTypesComp[slotType][i][1]
    nodeTypes[slotType] = (1, curOffset)

    for (nType, boundaries) in sorted(nodeTypesComp.items()):
      if nType == slotType:
        continue
      for (i, (nF, nT)) in boundaries.items():
        offsets[nType][i] = curOffset - nF + 1
        curOffset += nT - nF + 1

    for (nType, offs) in offsets.items():
      boundaries = nodeTypesComp[nType]
      nF = min(offs[i] + boundaries[i][0] for i in boundaries)
      nT = max(offs[i] + boundaries[i][1] for i in boundaries)
      nodeTypes[nType] = (nF, nT)
    return True

  def remapFeatures():
    indent(level=1, reset=True)
    for (i, loc) in locItems:
      info(f'\r{i:>3} {os.path.basename(loc)})', nl=False)
      api = getApi(loc, full=True)
      if api:
        return False

      F = api.F
      Fs = api.Fs
      Es = api.Es

      # node features

      for feat in api.Fall():
        fObj = Fs(feat)
        isOtype = feat == OTYPE
        data = {}
        for (nType, boundaries) in nodeTypesComp.items():
          if i not in boundaries:
            continue
          (nF, nT) = boundaries[i]
          cType = None
          if nType == componentType and isOtype:
              cType = componentType
          thisOffset = offsets[nType][i]
          for n in range(nF, nT + 1):
            val = fObj.v(n) if cType is None else cType
            if val is not None:
              data[thisOffset + n] = val
        nodeFeatures.setdefault(feat, {}).update(data)

      if componentFeature:
        data = {}
        boundaries = nodeTypesComp[componentType]
        if i in boundaries:
          (nF, nT) = boundaries[i]
          thisOffset = offsets[componentType][i]
          for n in range(nF, nT + 1):
            val = componentValue[i][n]
            if val is not None:
              data[thisOffset + n] = val
          nodeFeatures.setdefault(componentFeature, {}).update(data)

      # edge features

      for feat in api.Eall():
        eObj = Es(feat)
        isOslots = feat == OSLOTS
        edgeValues = (
            False
            if isOslots else
            eObj.edgeValues
        )
        data = {}
        for (nType, boundaries) in nodeTypesComp.items():
          if i not in boundaries:
            continue
          cSlots = None
          if nType == slotType and isOslots:
            continue
          if nType == componentType and isOslots:
            cSlots = set(range(1, componentOslots[i] + 1))
          (nF, nT) = boundaries[i]
          thisOffset = offsets[nType][i]
          for n in range(nF, nT + 1):
            values = (
                (
                    eObj.s(n)
                    if cSlots is None else
                    cSlots
                )
                if isOslots else
                eObj.f(n)
            )
            nOff = thisOffset + n
            if edgeValues:
              newVal = {}
              for (m, v) in values:
                mType = F.otype.v(m)
                thatOffset = offsets[mType][i]
                newVal[thatOffset + m] = v
            else:
              newVal = set()
              for m in values:
                mType = F.otype.v(m)
                thatOffset = offsets[mType][i]
                newVal.add(thatOffset + m)
            data[nOff] = newVal

        edgeFeatures.setdefault(feat, {}).update(data)

    return True

  def thinTypes():
    if mergeTypes is None:
      return True

    good = True

    indent(level=1, reset=True)

    for (newType, oldTypes) in mergeTypes.items():
      info(newType)
      if newType == slotType:
        error('Merge result cannot be the slot type', tm=False)
        good = False
        continue

      withFeatures = type(oldTypes) is dict

      for oldType in oldTypes:
        if oldType == slotType:
          error('Slot type is not mergeable', tm=False)
          good = False
          continue

        if oldType not in nodeTypes:
          error(f'Cannot merge non-existing node types: {oldType}', tm=False)
          good = False
          continue

        addFeatures = oldTypes[oldType] if withFeatures else {}
        addFeatures[OTYPE] = newType
        (nF, nT) = nodeTypes[oldType]
        for (feat, val) in addFeatures.items():
          for n in range(nF, nT + 1):
            nodeFeatures.setdefault(feat, {})[n] = val

    info('done')

    return good

  def writeTf():
    TF = Fabric(locations=targetLocation)
    TF.save(metaData=metaData, nodeFeatures=nodeFeatures, edgeFeatures=edgeFeatures)
    return True

  def process():
    indent(level=0, reset=True)
    info('inspect metadata ...')
    if not getMetas():
      return False
    info('determine nodetypes ...')
    if not getNtypes():
      return False
    info('compute offsets ...')
    if not getOffsets():
      return False
    info('remap features ...')
    if not remapFeatures():
      return False
    info('merge types ...')
    if not thinTypes():
      return False
    info('write TF data ...')
    if not writeTf():
      return False
    info('done')
    return True

  return process()
