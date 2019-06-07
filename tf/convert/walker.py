import collections
import functools
import re

from ..core.data import WARP
from ..core.helpers import itemize, isInt


class CV(object):
  S = 'slot'
  N = 'node'
  T = 'terminate'
  R = 'resume'
  F = 'feature'
  E = 'edge'

  def __init__(self, TF, silent=False):
    self.TF = TF
    self.wasSilent = self.TF.tm.isSilent()
    self.TF.tm.setSilent(silent)

  def _showWarnings(self):
    error = self.TF.tm.error
    info = self.TF.tm.info
    indent = self.TF.tm.indent

    warnings = self.warnings
    warn = self.warn

    if warn is None:
      if warnings:
        info('use `cv.walk(..., warn=False)` to make warnings visible')
        info('use `cv.walk(..., warn=True)` to stop on warnings')
    else:
      method = error if warn else info

      if warnings:
        for (kind, msgs) in sorted(warnings.items()):
          method(f'WARNING {kind} ({len(msgs)} x):')
          indent(level=2)
          for msg in sorted(set(msgs))[0:20]:
            if msg:
              method(f'{msg}', tm=False)
        self.warnings = {}
        if warn:
          info('use `cv.walk(..., warn=False)` to continue after warnings')
          info('use `cv.walk(..., warn=None)` to suppress warnings')
          self.good = False
        else:
          info('use `cv.walk(..., warn=True)` to stop after warnings')
          info('use `cv.walk(..., warn=None)` to suppress warnings')

  def _showErrors(self):
    error = self.TF.tm.error
    info = self.TF.tm.info
    indent = self.TF.tm.indent

    errors = self.errors

    if errors:
      for (kind, msgs) in sorted(errors.items()):
        error(f'ERROR {kind} ({len(msgs)} x):')
        indent(level=2)
        for msg in sorted(set(msgs))[0:20]:
          if msg:
            error(f'{msg}', tm=False)
      self.errors = {}
      self.good = False

    if not errors:
      if self.good:
        info('OK')
      else:
        error('STOPPED because of warnings')

  def walk(
      self,
      director,
      slotType,
      otext={},
      generic={},
      intFeatures=set(),
      featureMeta={},
      warn=True,
      generateTf=True,
      force=False,
  ):
    info = self.TF.tm.info
    indent = self.TF.tm.indent

    indent(level=0, reset=True)
    info('Importing data from walking through the source ...')

    self.force = force
    self.good = True
    self.errors = collections.defaultdict(list)
    self.warnings = collections.defaultdict(list)
    self.warn = warn
    self.slotType = slotType

    self.intFeatures = set(intFeatures)
    self.featureMeta = featureMeta
    self.metaData = {}
    self.nodeFeatures = {}
    self.edgeFeatures = {}

    indent(level=1, reset=True)
    self._prepareMeta(otext, generic)

    indent(level=1, reset=True)
    self._follow(director)

    indent(level=1, reset=True)
    self._removeUnlinked()

    indent(level=1, reset=True)
    self._checkGraph()

    indent(level=1, reset=True)
    self._checkFeatures()

    indent(level=1, reset=True)
    self._reorderNodes()

    indent(level=1, reset=True)
    self._reassignFeatures()

    if generateTf:

      indent(level=0)

      if self.good or self.force:
        self.good = self.TF.save(
            metaData=self.metaData,
            nodeFeatures=self.nodeFeatures,
            edgeFeatures=self.edgeFeatures,
        )

    self._showWarnings()
    self.TF.tm.setSilent(self.wasSilent)

    return self.good

  def _prepareMeta(self, otext, generic):
    varRe = re.compile(r'\{([^}]+)\}')

    info = self.TF.tm.info
    indent = self.TF.tm.indent

    if not self.good and not self.force:
      return

    info(f'Preparing metadata... ')

    intFeatures = self.intFeatures
    featureMeta = self.featureMeta

    errors = self.errors

    self.metaData = {
        '': generic,
        WARP[0]: {
            'valueType': 'str',
        },
        WARP[1]: {
            'valueType': 'str',
        },
        WARP[2]: otext,
    }
    metaData = self.metaData

    self.intFeatures = intFeatures
    self.sectionTypes = []
    self.sectionFeatures = []
    self.sectionFromLevel = {}
    self.levelFromSection = {}
    self.structureTypes = []
    self.structureFeatures = []
    self.structureLevel = {}
    self.textFormats = {}
    self.textFeatures = set()

    if not generic:
      errors['Missing feature meta data in "generic"'].append(
          'Consider adding provenance metadata to all features'
      )
    if not otext:
      errors['Missing "otext" configuration'].append(
          'Consider adding configuration for text representation and section levels'
      )
    else:
      sectionInfo = {}
      for f in ('sectionTypes', 'sectionFeatures'):
        if f not in otext:
          errors['Incomplete section specs in "otext"'].append(f'no key "{f}"')
          sectionInfo[f] = []
        else:
          sFields = itemize(otext[f], sep=',')
          sectionInfo[f] = sFields
          if f == 'sectionTypes':
            for (i, s) in enumerate(sFields):
              self.levelFromSection[s] = i + 1
              self.sectionFromLevel[i + 1] = s
      sLevels = {f: len(sectionInfo[f]) for f in sectionInfo}
      if min(sLevels.values()) != max(sLevels.values()):
        errors['Inconsistent section info'].append(
            ' but '.join(f'"{f}" has {sLevels[f]} levels' for f in sLevels)
        )
      self.sectionFeatures = sectionInfo['sectionFeatures']
      self.sectionTypes = sectionInfo['sectionTypes']

      structureInfo = {}
      for f in ('structureTypes', 'structureFeatures'):
        if f not in otext:
          structureInfo[f] = []
          continue
        sFields = itemize(otext[f], sep=',')
        structureInfo[f] = sFields
      if not structureInfo:
        info('No structure definition found in otext')
      sLevels = {f: len(structureInfo[f]) for f in structureInfo}
      if min(sLevels.values()) != max(sLevels.values()):
        errors['Inconsistent structure info'].append(
            ' but '.join(f'"{f}" has {sLevels[f]} levels' for f in sLevels)
        )
        structureInfo = {}
      if not structureInfo or all(len(info) == 0 for (s, info) in structureInfo.items()):
        info('No structure nodes will be set up')
        self.structureFeatures = []
        self.structureTypes = []
      self.structureFeatures = structureInfo['structureFeatures']
      self.structureTypes = structureInfo['structureTypes']
      self.featFromType = {
          typ: feat
          for (typ, feat) in zip(self.structureTypes, self.structureFeatures)
      }
      self.structureSet = set(self.structureTypes)

      textFormats = {}
      textFeatures = set()
      for (k, v) in sorted(otext.items()):
        if k.startswith('fmt:'):
          featureSet = set()
          features = varRe.findall(v)
          for ff in features:
            fr = ff.rsplit(':', maxsplit=1)[0]
            for f in fr.split('/'):
              featureSet.add(f)
          textFormats[k[4:]] = featureSet
          textFeatures |= featureSet
      if not textFormats:
        errors['No text formats in "otext"'].append(
            f'add "fmt:text-orig-full"'
        )
      elif 'text-orig-full' not in textFormats:
        errors['No default text format in otext'].append(
            f'add "fmt:text-orig-full"'
        )
      self.textFormats = textFormats
      self.textFeatures = textFeatures

    info(f'SECTION   TYPES:    {", ".join(self.sectionTypes)}', tm=False)
    info(f'SECTION   FEATURES: {", ".join(self.sectionFeatures)}', tm=False)
    info(f'STRUCTURE TYPES:    {", ".join(self.structureTypes)}', tm=False)
    info(f'STRUCTURE FEATURES: {", ".join(self.structureFeatures)}', tm=False)
    info(f'TEXT      FEATURES:', tm=False)
    indent(level=2)
    for (fmt, feats) in sorted(textFormats.items()):
      info(f'{fmt:<20} {", ".join(sorted(feats))}', tm=False)
    indent(level=1)

    for feat in WARP[0:3] + ('',):
      if feat in intFeatures:
        if feat == '':
          errors['intFeatures'].append(
              'Do not declare the "valueType" for all features'
          )
        else:
          errors['intFeatures'].append(
              f'Do not mark the "{feat}" feature as integer valued'
          )
        self.good = False

    for (feat, featMeta) in sorted(featureMeta.items()):
      good = self._checkFeatMeta(
          feat,
          featMeta,
          checkRegular=True,
          valueTypeAllowed=False,
          showErrors=False,
      )
      if not good:
        self.good = False
      metaData.setdefault(feat, {}).update(featMeta)
      metaData[feat]['valueType'] = 'int' if feat in intFeatures else 'str'

    self._showErrors()

  def _checkFeatMeta(
      self,
      feat,
      featMeta,
      checkRegular=False,
      valueTypeAllowed=True,
      showErrors=True,
  ):
    errors = collections.defaultdict(list)
    good = True

    if checkRegular:
      if feat in WARP[0:3] + ('',):
        if feat == '':
          errors['featureMeta'].append(
              f'Specify the generic feature meta data in "generic"'
          )
          good = False
        elif feat == WARP[2]:
          errors['featureMeta'].append(
              f'Specify the "{WARP[2]}" feature in "otext"'
          )
          good = False
        else:
          errors['featureMeta'].append(
              f'Do not pass metaData for the "{feat}" feature in "featureMeta"'
          )
          good = False
    if 'valueType' in featMeta:
      if not valueTypeAllowed:
        errors['featureMeta'].append(
            f'Do not specify "valueType" for the "{feat}" feature in "featureMeta"'
        )
        good = False
      elif featMeta['valueType'] not in {'int', 'str'}:
        errors['featureMeta'].append(
            f'valueType must be "int" or "str"'
        )
        good = False

    for (e, eData) in errors.items():
      self.errors[e].extend(eData)
    if showErrors:
      self._showErrors
    return good

  def stop(self, msg):
    self.TM.error(f'Forced stop: msg')
    self.good = False
    self.force = False

  def slot(self):
    curSeq = self.curSeq
    curEmbedders = self.curEmbedders
    oslots = self.oslots
    levelFromSection = self.levelFromSection
    warnings = self.warnings

    self.stats[self.S] += 1
    nType = self.slotType

    curSeq[nType] += 1
    seq = curSeq[nType]

    inSection = False
    for eNode in curEmbedders:
      if eNode[0] in levelFromSection:
        inSection = True
      oslots[eNode].add(seq)

    if levelFromSection and not inSection:
      warnings['slot outside sections'].append(f'{seq}')

    return (nType, seq)

  def node(self, nType):
    slotType = self.slotType
    errors = self.errors

    if nType == slotType:
      errors[f'use `cv.slot()` instead of `cv.node("{nType}")`'].append(None)
      return

    curSeq = self.curSeq
    curEmbedders = self.curEmbedders

    self.stats[self.N] += 1

    curSeq[nType] += 1
    seq = curSeq[nType]
    node = (nType, seq)

    self._checkSecLevel(node, before=True)
    curEmbedders.add(node)

    return node

  def terminate(self, node):
    self.stats[self.T] += 1
    if node is not None:
      self.curEmbedders.discard(node)
      self._checkSecLevel(node, before=False)

  def resume(self, node):
    curEmbedders = self.curEmbedders
    oslots = self.oslots

    self.stats[self.R] += 1

    (nType, seq) = node
    if nType == self.slotType:
      for eNode in curEmbedders:
        oslots[eNode].add(seq)
    else:
      self._checkSecLevel(node, before=None)
      curEmbedders.add(node)

  def feature(self, node, **features):
    nodeFeatures = self.nodeFeatures

    self.stats[self.F] += 1

    for (k, v) in features.items():
      if v is None:
        continue
      # self._checkType(k, v, self.N)
      nodeFeatures[k][node] = v

  def edge(self, nodeFrom, nodeTo, **features):
    edgeFeatures = self.edgeFeatures

    self.stats[self.E] += 1

    for (k, v) in features.items():
      # self._checkType(k, v, self.E)
      edgeFeatures[k][nodeFrom][nodeTo] = v

  def occurs(self, feat):
    nodeFeatures = self.nodeFeatures
    edgeFeatures = self.edgeFeatures
    if feat in nodeFeatures or feat in edgeFeatures:
      return True
    return False

  def meta(self, feat, **metadata):
    errors = self.errors
    intFeatures = self.intFeatures
    metaData = self.metaData
    featMeta = metaData.get(feat, {})

    good = True

    if not metadata:
      if feat in metaData:
        del metaData[feat]
        intFeatures.discard(feat)

    for (field, text) in metadata.items():
      if text is None:
        if field == 'valueType':
          errors[f'did not delete metadata field "valueType"'].append(feat)
          good = False
        else:
          if feat in metaData and field in metaData[feat]:
            del metaData[feat][field]
      else:
        metaData.setdefault(feat, {})[field] = text
        if field == 'valueType':
          if text == 'int':
            intFeatures.add(feat)
          else:
            intFeatures.discard(feat)

    self.good = self._checkFeatMeta(feat, featMeta) and good

  def linked(self, node):
    oslots = self.oslots
    return tuple(oslots.get(node, []))

  def active(self, node):
    return node in self.curEmbedders

  def activeTypes(self):
    return {node[0] for node in self.curEmbedders}

  def get(self, feature, *args):
    errors = self.errors
    nodeFeatures = self.nodeFeatures
    edgeFeatures = self.edgeFeatures
    nArgs = len(args)
    if nArgs == 0 or nArgs > 2:
      errors[f'use `cv.get(ft, n)` or `cv.get(ft, nf, nt)`'].append(None)
      return None

    return (
        nodeFeatures.get(feature, {}).get(args[0], None)
        if len(args) == 1 else
        edgeFeatures.get(feature, {}).get(args[0], {}).get(args[1], None)
    )

  def _checkSecLevel(self, node, before=True):
    levelFromSection = self.levelFromSection
    sectionFeatures = self.sectionFeatures
    nodeFeatures = self.nodeFeatures
    warnings = self.warnings
    curEmbedders = self.curEmbedders

    (nType, seq) = node

    msg = 'starts' if before is True else 'ends' if before is False else 'resumes'

    if levelFromSection:
      level = levelFromSection.get(nType, None)
      if level is None:
        return

      headingFeature = sectionFeatures[level - 1]
      nHeading = nodeFeatures.get(headingFeature, {}).get(node, '??')

      for em in curEmbedders:
        eType = em[0]
        if eType in levelFromSection:
          eLevel = levelFromSection.get(eType, None)
          eHeadingFeature = sectionFeatures[eLevel - 1]
          eHeading = nodeFeatures.get(eHeadingFeature, {}).get(em, '??')

        if eType == nType:
          warnings[
              f'section {nType} "{nHeading}" of level {level}'
              f' enclosed in another {nType}: {eHeading}'
          ].append(None)
        elif eType in levelFromSection:
          eLevel = levelFromSection[eType]
          if eLevel > level:
            warnings[
                f'section {nType} "{nHeading}" of level {level} {msg}'
                f' inside a {eType} "{eHeading}" of level {eLevel}'
            ].append(None)

  def _follow(self, director):

    # after node = yield ('N', nodeType) all slot nodes that are yielded
    # will be linked to node, until a ('T', node) is yielded.
    # If needed, you can resume this node again, after which new slot nodes
    # continue to be linked to this node.
    # If you resume a slot node, it all non slot nodes in the current context
    # will be linked to it.

    info = self.TF.tm.info

    if not self.good:
      return

    info(f'Following director... ')

    slotType = self.slotType
    errors = self.errors

    self.oslots = collections.defaultdict(set)
    self.nodeFeatures = collections.defaultdict(dict)
    self.edgeFeatures = collections.defaultdict(lambda: collections.defaultdict(dict))
    self.nodes = collections.defaultdict(set)
    nodes = self.nodes

    self.curSeq = collections.Counter()
    self.curEmbedders = set()
    curEmbedders = self.curEmbedders

    self.stats = {actionType: 0 for actionType in (
        self.S,
        self.N,
        self.T,
        self.R,
        self.F,
        self.E,
    )}

    director(self)

    if not self.stats:
      self.good = False
      return

    for (actionType, amount) in sorted(self.stats.items()):
      info(f'"{actionType}" actions: {amount}')

    totalNodes = 0

    for (nType, lastSeq) in sorted(self.curSeq.items()):
      for seq in range(1, lastSeq + 1):
        nodes[nType].add(seq)
      slotRep = ' = slot type' if nType == slotType else ''
      info(f'{lastSeq:>8} x "{nType}" node {slotRep}', tm=False)
      totalNodes += lastSeq
    info(f'{totalNodes:>8} nodes of all types', tm=False)

    self.totalNodes = totalNodes

    if curEmbedders:
      embedCount = collections.Counter()
      for (nType, seq) in curEmbedders:
        embedCount[nType] += 1
      for (nType, amount) in sorted(
          embedCount.items(),
          key=lambda x: (-x[1], x[0]),
      ):
        errors['Unterminated nodes'].append(
            f'{nType}: {amount} x'
        )

    self._showErrors()

  def _removeUnlinked(self):
    info = self.TF.tm.info
    indent = self.TF.tm.indent

    if not self.good and not self.force:
      return

    nodeTypes = self.curSeq
    nodes = self.nodes
    slotType = self.slotType
    oslots = self.oslots
    nodeFeatures = self.nodeFeatures
    edgeFeatures = self.edgeFeatures

    unlinked = {}

    for nType in nodeTypes:
      if nType == slotType:
        continue
      for seq in range(1, nodeTypes[nType] + 1):
        if (nType, seq) not in oslots:
          unlinked.setdefault(nType, []).append(seq)

    if unlinked:
      info(f'Removing unlinked nodes ... ')
      indent(level=2)
      totalRemoved = 0
      for (nType, seqs) in unlinked.items():
        theseNodes = nodes[nType]
        lSeqs = len(seqs)
        totalRemoved += lSeqs
        rep = ' ...' if lSeqs > 5 else ''
        pl = '' if lSeqs == 1 else 's'
        info(f'{lSeqs:>6} unlinked "{nType}" node{pl}: {seqs[0:5]}{rep}')
        for seq in seqs:
          node = (nType, seq)
          theseNodes.discard(seq)
          for (f, fData) in nodeFeatures.items():
            if node in fData:
              del fData[node]
          for (f, fData) in edgeFeatures.items():
            if node in fData:
              del fData[node]
              for (fNode, toValues) in fData:
                if node in toValues:
                  del toValues[node]
      pl = '' if totalRemoved == 1 else 's'
      info(f'{totalRemoved:>6} unlinked node{pl}')
      self.totalNodes -= totalRemoved
      info(f'Leaving {self.totalNodes:>6} nodes')
      indent(level=1)

  def _checkGraph(self):
    info = self.TF.tm.info

    if not self.good and not self.force:
      return

    info(f'checking for nodes and edges ... ')

    nodes = self.nodes
    errors = self.errors
    edgeFeatures = self.edgeFeatures

    # edges refer to nodes

    for (k, featureData) in edgeFeatures.items():
      for nFrom in featureData:
        (nType, seq) = nFrom
        if nType not in nodes or seq not in nodes[nType]:
          errors['Edge feature: illegal node'].append(
              f'"{k}": from-node  {nFrom} not in node set'
          )
          continue
        for nTo in featureData[nFrom]:
          (nType, seq) = nTo
          if nType not in nodes or seq not in nodes[nType]:
            errors['Edge feature: illegal node'].append(
                f'"{k}": to-node  {nTo} not in node set'
            )

    self._showErrors()

  def _checkFeatures(self):
    info = self.TF.tm.info

    if not self.good and not self.force:
      return

    info(f'checking features ... ')

    intFeatures = self.intFeatures
    metaData = self.metaData

    nodes = self.nodes
    nodeFeatures = self.nodeFeatures
    edgeFeatures = self.edgeFeatures

    errors = self.errors

    for feat in intFeatures:
      if feat not in WARP and feat not in nodeFeatures and feat not in edgeFeatures:
        errors['intFeatures'].append(
            f'"{feat}" is declared as integer valued, but this feature does not occur'
        )
    for nType in self.sectionTypes:
      if nType not in nodes:
        errors['sections'].append(
            f'node type "{nType}" is declared as a section type, but this node type does not occur'
        )
    for feat in self.sectionFeatures:
      if feat not in nodeFeatures:
        errors['sections'].append(
            f'"{feat}" is declared as a section feature, but this node feature does not occur'
        )
    for nType in self.structureTypes:
      if nType not in nodes:
        errors['structure'].append(
            f'node type "{nType}" is declared as a structure type,'
            f' but this node type does not occur'
        )
    for feat in self.structureFeatures:
      if feat not in nodeFeatures:
        errors['structure'].append(
            f'"{feat}" is declared as a structure feature, but this node feature does not occur'
        )
        nodeFeatures[feat] = {}

    structureSet = self.structureSet
    featFromType = self.featFromType
    for nType in nodes:
      if nType not in structureSet:
        continue
      feat = featFromType[nType]
      for seq in nodes[nType]:
        if (nType, seq) not in nodeFeatures[feat]:
          errors['structure features'].append(
              f'"structure element "{nType}" {seq} has no value for "{feat}"'
          )

    for feat in self.textFeatures:
      if feat not in nodeFeatures:
        errors['text formats'].append(
            f'"{feat}" is used in a text format, but this node feature does not occur'
        )

    for feat in WARP:
      if feat in nodeFeatures or feat in edgeFeatures:
        errors[feat].append(f'Do not construct the "{feat}" feature yourself')

    for feat in sorted(nodeFeatures) + sorted(edgeFeatures):
      if feat not in self.metaData:
        errors['feature metadata'].append(
            f'node feature "{feat}" has no metadata'
        )

    for feat in sorted(metaData):
      if feat and feat not in WARP and feat not in nodeFeatures and feat not in edgeFeatures:
        errors['feature metadata'].append(
            f'node feature "{feat}" has metadata but does not occur'
        )

    for (feat, featData) in sorted(nodeFeatures.items()):
      if None in featData:
        errors['feature values assigned to None'].append(
            f'node feature "{feat}" has a node None'
        )
    for (feat, featData) in sorted(edgeFeatures.items()):
      if None in featData:
        errors['feature values assigned to None'].append(
            f'edge feature "{feat}" has a from-node None'
        )
      for toValues in featData.values():
        if None in toValues:
          errors['feature values assigned to None'].append(
              f'edge feature "{feat}" has a to-node None'
          )

    for (feat, featData) in sorted(edgeFeatures.items()):
      if feat in WARP:
        continue
      hasValues = False
      for (nodeTo, toValues) in featData.items():
        if any(v is not None for v in toValues.values()):
          hasValues = True
          break

      if not hasValues:
        edgeFeatures[feat] = {nodeTo: set(toValues) for (nodeTo, toValues) in featData.items()}
      metaData.setdefault(feat, {})['edgeValues'] = hasValues

    for feat in intFeatures:
      if feat in WARP:
        continue
      if feat in nodeFeatures:
        featData = nodeFeatures[feat]
        for (k, v) in featData.items():
          if not isInt(v):
            errors[f'Not a number'].append(
                f'"node feature "{k}": "{v}"'
            )
      if feat in edgeFeatures and metaData[feat]['edgeValues']:
        featData = edgeFeatures[feat]
        for (fromNode, toValues) in featData.items():
          for v in toValues.values():
            if not isInt(v):
              errors[f'Not a number'].append(
                  f'"edge feature "{k}": "{v}"'
              )

    self._showErrors()

  def _reorderNodes(self):
    info = self.TF.tm.info

    if not self.good and not self.force:
      return

    info('reordering nodes ...')

    nodeTypes = self.curSeq
    nodes = self.nodes
    slotType = self.slotType

    nTypes = (slotType,) + tuple(sorted(nType for nType in nodes if nType != slotType))

    self.nodeMap = {}
    self.maxSlot = nodeTypes[slotType]

    nodeMap = self.nodeMap
    maxSlot = self.maxSlot

    n = 0

    for nType in nTypes:
      canonical = self._canonical(nType)
      if nType == slotType:
        sortedSeqs = range(1, maxSlot + 1)
      else:
        seqs = nodes[nType]
        info(f'Sorting {len(seqs)} nodes of type "{nType}"')
        sortedSeqs = sorted(seqs, key=canonical)
      for seq in sortedSeqs:
        n += 1
        nodeMap[(nType, seq)] = n

    self.maxNode = n
    info(f'Max node = {n}')

    self._showErrors()

  def _canonical(self, nType):
    oslots = self.oslots

    def before(nodeA, nodeB):
      slotsA = oslots[(nType, nodeA)]
      slotsB = oslots[(nType, nodeB)]
      if slotsA == slotsB:
        return 0

      aWithoutB = slotsA - slotsB
      if not aWithoutB:
        return 1

      bWithoutA = slotsB - slotsA
      if not bWithoutA:
        return -1

      aMin = min(aWithoutB)
      bMin = min(bWithoutA)
      return -1 if aMin < bMin else 1

    return functools.cmp_to_key(before)

  def _reassignFeatures(self):
    info = self.TF.tm.info
    indent = self.TF.tm.indent

    if not self.good and not self.force:
      return

    info('reassigning feature values ...')

    nodeMap = self.nodeMap
    oslots = self.oslots
    nodeFeatures = self.nodeFeatures
    edgeFeatures = self.edgeFeatures

    otype = {n: nType for ((nType, seq), n) in nodeMap.items()}
    oslots = {nodeMap[node]: slots for (node, slots) in oslots.items()}

    nodeFeaturesProto = self.nodeFeatures
    edgeFeaturesProto = self.edgeFeatures

    nodeFeatures = collections.defaultdict(dict)
    edgeFeatures = collections.defaultdict(lambda: collections.defaultdict(dict))

    indent(level=2)

    for k in sorted(nodeFeaturesProto):
      featureDataProto = nodeFeaturesProto[k]
      ln = len(featureDataProto)
      pl = '' if ln == 1 else 's'
      info(f'node feature "{k}" with {ln} node{pl}')
      featureData = {}
      for (node, value) in featureDataProto.items():
        featureData[nodeMap[node]] = value
      nodeFeatures[k] = featureData

    for k in sorted(edgeFeaturesProto):
      featureDataProto = edgeFeaturesProto[k]
      ln = len(featureDataProto)
      pl = '' if ln == 1 else 's'
      info(f'edge feature "{k}" with {ln} start node{pl}')
      featureData = {}
      for (nodeFrom, toValues) in featureDataProto.items():
        if type(toValues) is set:
          toData = {nodeMap[nodeTo] for nodeTo in toValues}
        else:
          toData = {}
          for (nodeTo, value) in toValues.items():
            toData[nodeMap[nodeTo]] = value
        featureData[nodeMap[nodeFrom]] = toData
      edgeFeatures[k] = featureData

    nodeFeatures['otype'] = otype
    edgeFeatures['oslots'] = oslots

    indent(level=1)

    self.oslots = None
    self.otype = None
    self.nodeFeatures = nodeFeatures
    self.edgeFeatures = edgeFeatures

    self._showErrors()
