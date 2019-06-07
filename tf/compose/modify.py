import collections

from ..fabric import Fabric
from ..core.data import WARP
from ..core.timestamp import Timestamp
from ..core.helpers import itemize, isInt, collectFormats, dirEmpty

OTYPE = WARP[0]
OSLOTS = WARP[1]
OTEXT = WARP[2]

VALTP = 'valueType'

GENERATED = set('''
    writtenBy
    dateWritten
    version
'''.strip().split())

NODE = 'node'
NODES = 'nodes'
EDGE = 'edge'
EDGES = 'edges'

NFS = 'nodeFeatures'
EFS = 'edgeFeatures'

ADD_F_KEYS = {NFS, EFS}

NF = 'nodeFrom'
NT = 'nodeTo'
NS = 'nodeSlots'

ADD_T_KEYS = {NF, NT, NS, NFS, EFS}

SE_TP = 'sectionTypes'
SE_FT = 'sectionFeatures'
ST_TP = 'structureTypes'
ST_FT = 'structureFeatures'

TM = Timestamp()
indent = TM.indent
info = TM.info
error = TM.error
isSilent = TM.isSilent
setSilent = TM.setSilent


def _itemize(arg):
  return (
      []
      if not arg else
      itemize(arg) if type(arg) is str else list(arg)
  )


def _rep(iterable):
  return ', '.join(sorted(iterable))


def modify(
    location,
    targetLocation,
    mergeFeatures=None,
    deleteFeatures=None,
    addFeatures=None,
    mergeTypes=None,
    deleteTypes=None,
    addTypes=None,
    featureMeta=None,
    silent=False,
):
  addFeatures = addFeatures or {}
  deleteFeatures = set(_itemize(deleteFeatures))
  mergeFeatures = mergeFeatures or {}

  addTypes = addTypes or {}
  deleteTypes = set(_itemize(deleteTypes))
  mergeTypes = mergeTypes or {}

  featureMeta = featureMeta or {}

  origMaxNode = None
  origNodeTypes = None
  origNodeFeatures = None
  origEdgeFeatures = None
  origFeatures = None

  shift = {}
  shiftNeeded = False

  slotType = None
  maxNode = None
  nodeFeatures = {}
  edgeFeatures = {}
  deletedTypes = set()
  deletedFeatures = set()
  nodeTypes = {}

  nodeFeaturesOut = {}
  edgeFeaturesOut = {}
  metaDataOut = {}

  api = None

  good = True
  ePrefix = ''
  eItem = ''

  def err(msg):
    nonlocal good
    error(f'{ePrefix}{eItem}{msg}', tm=False)
    good = False

  def inf(msg):
    info(f'{ePrefix}{eItem}{msg}', tm=False)

  def meta(feat):
    return api.TF.features[feat].metaData

  def valTp(feat):
    return meta(feat).get(VALTP, None)

  def otextInfo():
    orig = meta(OTEXT)
    custom = featureMeta.get(OTEXT, {})
    combi = {}
    for key in set(custom) | set(orig):
      origVal = orig.get(key, '')
      customVal = custom.get(key, '')
      combi[key] = customVal or origVal

    ensureTypes = set()
    ensureFeatures = set()
    for kind in (SE_TP, ST_TP):
      ensureTypes |= set(itemize(combi.get(kind, ''), sep=','))
    for kind in (SE_FT, ST_FT):
      ensureFeatures |= set(itemize(combi.get(kind, ''), sep=','))
    ensureFeatures |= set(collectFormats(combi)[1])
    return (ensureTypes, ensureFeatures)

  def allInt(values):
    return all(isInt(v) for v in values)

  def prepare():
    nonlocal api
    nonlocal origNodeTypes
    nonlocal origFeatures
    nonlocal origNodeFeatures
    nonlocal origEdgeFeatures
    nonlocal origMaxNode
    nonlocal maxNode
    nonlocal shift
    nonlocal ePrefix
    nonlocal eItem

    indent(level=0, reset=True)
    info('preparing and checking ...')
    indent(level=1, reset=True)

    TF = Fabric(locations=location, silent=silent)
    origAllFeatures = TF.explore(silent=silent or True, show=True)
    origNodeFeatures = set(origAllFeatures[NODES])
    origEdgeFeatures = set(origAllFeatures[EDGES])
    origFeatures = origNodeFeatures | origEdgeFeatures

    api = TF.load('', silent=silent)
    if not api:
      return False

    F = api.F
    C = api.C
    origNodeTypes = {x[0]: (x[2], x[3]) for x in C.levels.data}
    origMaxSlot = F.otype.maxSlot
    origMaxNode = F.otype.maxNode
    maxNode = origMaxNode

    addedTp = set()
    addedFt = set()
    deletedTp = set()
    deletedFt = set()

    # check mergeFeatures

    ePrefix = 'Merge features: '

    for (outFeat, inFeats) in mergeFeatures.items():
      eItem = f'{outFeat}: '

      inFeats = _itemize(inFeats)
      if outFeat in WARP:
        err(f'Can not merge into standard features')
        continue

      if not inFeats:
        err('Nothing to merge from')
        continue

      addedFt.add(outFeat)

      for inFeat in inFeats:
        if inFeat in WARP:
          err(f'Can not merge from standard features: {inFeat}')
          continue
        deletedFt.add(inFeat)

      missingIn = set(f for f in inFeats if f not in origFeatures)

      if missingIn:
        err(f'Missing features {_rep(missingIn)}')

      allInIsNode = all(f in origNodeFeatures for f in inFeats)
      allInIsEdge = all(f in origEdgeFeatures for f in inFeats)
      outExists = outFeat in origFeatures
      outIsNode = outExists and outFeat in origNodeFeatures
      outIsEdge = outExists and outFeat in origEdgeFeatures

      if outIsNode and not allInIsNode:
        err(f'Node Feature can not be merged from an edge feature')

      if outIsEdge and not allInIsEdge:
        err(f'Edge Feature can not be merged from a node feature')

      if not allInIsNode and not allInIsEdge:
        err(f'Feature can not be merged from both node and edge features')

      allInIsInt = all(valTp(f) == 'int' for f in inFeats)
      correctTp = 'int' if allInIsInt else 'str'
      checkValType(outFeat, correctTp=correctTp)

    # check deleteFeatures

    ePrefix = 'Delete features: '

    for feat in deleteFeatures:
      eItem = f'{feat}: '

      if feat in WARP:
        err(f'Can not delete standard features')
        continue
      if feat not in origFeatures:
        err(f'Not in data set')

      deletedFt.add(feat)

    # check addFeatures

    ePrefix = 'Add features: '
    eItem = ''

    illegalKeys = set(addFeatures) - ADD_F_KEYS
    if illegalKeys:
      err(f'{_rep(illegalKeys)} unrecognized, expected {_rep(ADD_F_KEYS)}')

    bothFeatures = (
        set(addFeatures.get(NFS, {}))
        &
        set(addFeatures.get(EFS, {}))
    )
    if bothFeatures:
      err(f'{_rep(bothFeatures)}: Both node and edge features')

    for (kind, otherKind, origSet, origSetOther) in (
        (NODE, EDGE, origNodeFeatures, origEdgeFeatures),
        (EDGE, NODE, origEdgeFeatures, origNodeFeatures),
    ):
      for (feat, data) in addFeatures.get(f'{kind}Features', {}).items():
        eItem = f'{feat}: '

        if feat in WARP:
          err(f'Cannot add standard features')
          continue
        if feat in origSetOther:
          err(f'{kind} feature already exists as {otherKind} feature')

        checkValType(feat, vals=data.values())

        addedFt.add(feat)

    # check mergeTypes

    ePrefix = 'Merge types: '

    mData = {}

    for (outType, inTypes) in mergeTypes.items():
      eItem = f'{outType}: '

      if outType == slotType:
        err(f'Result cannot be the slot type')

      withFeatures = type(inTypes) is dict

      addedTp.add(outType)

      for inType in inTypes:
        if inType == slotType:
          err(f'Slot type {inType} is not mergeable')
          continue

        if inType not in origNodeTypes:
          err(f'Cannot merge non-existing node type {inType}')
          continue

        deletedTp.add(inType)

        mFeatures = inTypes[inType] if withFeatures else {}
        for (feat, val) in mFeatures.items():
          mData.setdefault(feat, set()).add(val)
          addedFt.add(feat)

    for (feat, vals) in mData.items():
      eItem = f'{feat}: '
      checkValType(feat, vals=vals)

    # check deleteTypes

    ePrefix = 'Delete types: '

    for nodeType in deleteTypes:
      eItem = f'{nodeType}: '

      if nodeType not in origNodeTypes:
        err(f'Not in data set')
        continue

      deletedTp.add(nodeType)

    # check addTypes

    ePrefix = 'Add types: '

    for (nodeType, typeInfo) in sorted(addTypes.items()):
      eItem = f'{nodeType}: '

      illegalKeys = set(typeInfo) - ADD_T_KEYS
      if illegalKeys:
        err(f'{_rep(illegalKeys)} unrecognized, expected {_rep(ADD_T_KEYS)}')
        continue

      if nodeType in origNodeTypes:
        err(f'Already occurs')
        continue

      addedTp.add(nodeType)

      nodeSlots = typeInfo.get(NS, {})
      if not nodeSlots:
        err(f'No slot information given')
      nF = typeInfo.get(NF, None)
      if not nF:
        err(f'No lower bound given')
      nT = typeInfo.get(NT, None)
      if not nT:
        err(f'No upper bound given')
      if nF is not None and nT is not None:
        unlinked = 0
        badlinked = 0
        for n in range(nF, nT + 1):
          slots = nodeSlots.get(n, ())
          if not slots:
            unlinked += 1
          else:
            slotGood = True
            for slot in slots:
              if slot < 1 or slot > origMaxSlot:
                slotGood = False
            if not slotGood:
              badlinked += 1
        if unlinked:
          err(f'{unlinked} nodes not linked to slots')
        if badlinked:
          err(f'{badlinked} nodes linked to non-slot nodes')

      for kind in (NODE, EDGE):
        for (feat, data) in typeInfo.get(f'{kind}Features', {}).items():
          eItem = f'{feat}: '
          checkValType(feat, vals=data.values())

          addedFt.add(feat)

    (otextTypes, otextFeatures) = otextInfo()

    problemTypes = addedTp & deletedTp

    if problemTypes:
      ePrefix = 'Add and then delete: '
      eItem = 'types: '
      err(f'{_rep(problemTypes)}')

    problemTypes = otextTypes - ((set(origNodeTypes) | addedTp) - deletedTp)
    if problemTypes:
      ePrefix = 'Missing for text API: '
      eItem = 'types: '
      err(f'{_rep(problemTypes)}')

    problemFeats = addedFt & deletedFt

    if problemFeats:
      ePrefix = 'Add and then delete: '
      eItem = 'features: '
      err(f'{_rep(problemFeats)}')

    problemFeats = otextFeatures - ((origFeatures | addedFt) - deletedFt)
    if problemFeats:
      ePrefix = 'Missing for text API: '
      eItem = 'features: '
      err(f'{_rep(problemFeats)}')

    if not dirEmpty(targetLocation):
      ePrefix = 'Output directory: '
      eItem = 'not empty: '
      err(f'Clean it or remove it or choose another location')

    if not good:
      return False

    api = TF.loadAll()

    info('done')
    return True

  def checkValType(feat, vals=None, correctTp=None):
    origTp = (
        valTp(feat)
        if feat in origFeatures else
        None
    )
    customTp = featureMeta.get(feat, {}).get(VALTP, None)
    assignedTp = origTp or customTp

    if correctTp is None:
      correctTp = 'int' if allInt(vals) else 'str'
    newTp = customTp or correctTp

    if newTp != assignedTp:
      featureMeta.setdefault(feat, {})[VALTP] = newTp

    if customTp and customTp != correctTp and customTp == 'int':
      err(f'feature values are declared to be int but some values are not int')

    if assignedTp != newTp:
      rep1 = f'feature of type {newTp}'
      rep2 = f' (was {assignedTp})' if assignedTp else ''
      inf(f'{rep1}{rep2}')

  def shiftx(vs, offset=None, nF=None, nT=None):
    if offset is None:
      return (
          {shift[m]: v for (m, v) in vs.items()}
          if type(vs) is dict else
          {shift[m] for m in vs}
      )
    else:
      return (
          {m + offset: v for (m, v) in vs.items() if nF <= m <= nT}
          if type(vs) is dict else
          {m + offset for m in vs if nF <= m <= nT}
      )

  def shiftFeature(kind, feat, data):
    return (
        {shift[n]: v for (n, v) in data.items() if n in shift}
        if kind == NODE else
        {shift[n]: shiftx(v) for (n, v) in data.items() if n in shift}
    )

  def mergeF():
    nonlocal deletedFeatures
    Fs = api.Fs
    Es = api.Es

    indent(level=0)
    if mergeFeatures:
      info('merge features ...')
    indent(level=1, reset=True)

    inF = set()

    for (outFeat, inFeats) in mergeFeatures.items():
      data = {}
      inFeats = _itemize(inFeats)
      if all(f in origNodeFeatures for f in inFeats):
        featSrc = Fs
        featDst = nodeFeatures
      else:
        featSrc = Es
        featDst = edgeFeatures

      for inFeat in inFeats:
        for (n, val) in featSrc(inFeat).data.items():
          data[n] = val
      featDst.setdefault(outFeat, {}).update(data)

      for inFeat in inFeats:
        inF.add(inFeat)
        if inFeat in featDst:
          del featDst[inFeat]
    deletedFeatures |= inF

    if mergeFeatures:
      info(f'done (deleted {len(inF)} and added {len(mergeFeatures)} features)')
      indent(level=2)
      info(f'deleted {_rep(inF)}', tm=False)
      info(f'added   {_rep(mergeFeatures)}', tm=False)
    return True

  def deleteF():
    indent(level=0)
    if deleteFeatures:
      info('delete features ...')
    indent(level=1, reset=True)
    for feat in deleteFeatures:
      dest = (
          nodeFeatures if feat in origNodeFeatures else
          edgeFeatures if feat in origEdgeFeatures else
          None
      )
      if dest and feat in dest:
        del dest[feat]
      deletedFeatures.add(feat)

    if deleteFeatures:
      info(f'done ({len(deleteFeatures)} features)')
      indent(level=2)
      info(_rep(deleteFeatures), tm=False)
    return True

  def addF():
    indent(level=0)
    if addFeatures:
      info('add features ...')
    indent(level=1, reset=True)
    added = collections.defaultdict(set)
    for (kind, dest) in (
        (NODE, nodeFeatures),
        (EDGE, edgeFeatures),
    ):
      for (feat, data) in addFeatures.get(f'{kind}Features', {}).items():
        dest.setdefault(feat, {}).update(data)
        added[kind].add(feat)
    if addFeatures:
      info(f'done (added {len(added["node"])} node + {len(added["edge"])} edge features)')
      indent(level=2)
      for (kind, feats) in sorted(added.items()):
        info(f'{kind} features: {_rep(feats)}')

    return True

  def mergeT():
    nonlocal deletedTypes

    indent(level=0)
    if mergeTypes:
      info('merge types ...')
    indent(level=1, reset=True)

    inT = set()

    for (outType, inTypes) in mergeTypes.items():
      info(f'Merging {outType}')
      withFeatures = type(inTypes) is dict

      for inType in inTypes:
        addFeatures = inTypes[inType] if withFeatures else {}
        addFeatures[OTYPE] = outType
        (nF, nT) = origNodeTypes[inType]
        for (feat, val) in addFeatures.items():
          for n in range(nF, nT + 1):
            nodeFeatures.setdefault(feat, {})[n] = val
        inT.add(inType)

    deletedTypes |= inT

    if mergeTypes:
      info(f'done (merged {len(mergeTypes)} node types)')
      indent(level=2)
      info(f'deleted {_rep(inT)}', tm=False)
      info(f'added   {_rep(mergeTypes)}', tm=False)
    return True

  def deleteT():
    nonlocal maxNode
    nonlocal shiftNeeded

    indent(level=0)
    if deleteTypes:
      info('delete types ...')
    indent(level=1, reset=True)

    curShift = 0
    for (nType, (nF, nT)) in sorted(
        origNodeTypes.items(),
        key=lambda x: x[1][0],
    ):
      if nType in deleteTypes:
        curShift -= nT - nF + 1
        deletedTypes.add(nType)
      else:
        nodeTypes[nType] = (nF + curShift, nT + curShift)
        for n in range(nF, nT + 1):
          shift[n] = n - curShift

    for (kind, upd) in (
        (NODE, nodeFeatures,),
        (EDGE, edgeFeatures,),
    ):
      for (feat, uData) in upd.items():
        upd[feat] = shiftFeature(kind, feat, uData)

    maxNode = origMaxNode - curShift
    shiftNeeded = curShift != 0

    if deleteTypes:
      info(f'done ({len(deleteTypes)} types)')
      indent(level=2)
      info(_rep(deleteTypes), tm=False)
    return True

  def addT():
    nonlocal maxNode

    indent(level=0)
    if addTypes:
      info('add types ...')
    indent(level=1, reset=True)

    for (nodeType, typeInfo) in sorted(addTypes.items()):
      nF = typeInfo[NF]
      nT = typeInfo[NT]
      offset = maxNode - nF + 1
      nodeSlots = typeInfo[NS]

      data = {}
      for n in range(nF, nT + 1):
        data[offset + n] = nodeType
      nodeFeatures.setdefault(OTYPE, {}).update(data)

      data = {}
      for n in range(nF, nT + 1):
        data[offset + n] = set(nodeSlots[n])
      edgeFeatures.setdefault(OSLOTS, {}).update(data)

      for (feat, addData) in typeInfo.get(NFS, {}).items():
        data = {}
        for n in range(nF, nT + 1):
          value = addData.get(n, None)
          if value is not None:
            data[offset + n] = value
        nodeFeatures.setdefault(feat, {}).update(data)

      for (feat, addData) in typeInfo.get(EFS, {}).items():
        data = {}
        for n in range(nF, nT + 1):
          value = addData.get(n, None)
          if value:
            newValue = shiftx(value, offset=offset, nF=nF, nT=nT)
            if newValue:
              data[offset + n] = newValue
        edgeFeatures.setdefault(feat, {}).update(data)
      maxNode += nT - nF + 1

    if addTypes:
      info(f'done ({len(addTypes)} types)')
      indent(level=2)
      info(_rep(addTypes), tm=False)
    return True

  def applyUpdates():
    Fs = api.Fs
    Es = api.Es

    indent(level=0)
    info('applying updates ...')
    indent(level=1, reset=True)

    mFeat = 0

    for (kind, featSet, featSrc, featUpd, featOut) in (
        (NODE, origNodeFeatures, Fs, nodeFeatures, nodeFeaturesOut),
        (EDGE, origEdgeFeatures, Es, edgeFeatures, edgeFeaturesOut),
    ):
      for feat in (set(featSet) | set(featUpd)) - deletedFeatures:
        outData = {}
        outMeta = {}
        if feat in featSet:
          featObj = featSrc(feat)
          outMeta.update(featObj.meta)
          if shiftNeeded:
            outData.update(shiftFeature(kind, feat, featObj))
            mFeat += 1
          else:
            outData.update(featObj.items())
        if feat in featUpd:
          outData.update(featUpd[feat])
          if kind == EDGE:
            aVal = next(iter(featUpd[feat].values()))
            hasValues = type(aVal) is dict
            if outMeta.get('edgeValues', False) != hasValues:
              outMeta['edgeValues'] = hasValues
        if feat in featureMeta:
          for (k, v) in featureMeta[feat].items():
            if v is None:
              if k in outMeta:
                del outMeta[k]
            else:
              outMeta[k] = v

        featOut[feat] = outData
        metaDataOut[feat] = outMeta

    otextMeta = {}
    otextMeta.update(meta(OTEXT))
    mK = 0
    if OTEXT in featureMeta:
      for (k, v) in featureMeta[OTEXT].items():
        if v is None:
          if k in otextMeta:
            del otextMeta[k]
            mK += 1
        else:
          if k not in otextMeta or otextMeta[k] != v:
            otextMeta[k] = v
            mK += 1
    metaDataOut[OTEXT] = otextMeta

    if mFeat or mK:
      fRep = f' (shifted {mFeat} features)' if mFeat else ''
      kRep = f' (adapted {mK} keys in otext)' if mK else ''
      info(f'done{fRep}{kRep}')

    return True

  def writeTf():
    indent(level=0)
    info('write TF data ...')
    indent(level=1, reset=True)
    TF = Fabric(locations=targetLocation, silent=silent or True)
    TF.save(
        metaData=metaDataOut,
        nodeFeatures=nodeFeaturesOut,
        edgeFeatures=edgeFeaturesOut,
    )
    return True

  def finalize():
    indent(level=0)
    info('all done')
    return True

  def process():
    for step in (
        prepare,
        mergeF,
        deleteF,
        addF,
        mergeT,
        deleteT,
        addT,
        applyUpdates,
        writeTf,
        finalize,
    ):
      if not step():
        return False
    return True

  wasSilent = isSilent()
  setSilent(silent)
  result = process()
  setSilent(wasSilent)
  return result
