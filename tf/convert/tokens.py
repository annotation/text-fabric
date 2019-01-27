import collections
import functools
import re

from ..core.data import WARP


class Token(object):
  N = 'N'
  T = 'T'
  R = 'R'
  F = 'F'
  E = 'E'

  @classmethod
  def slot(cls):
    return (cls.N, None)

  @classmethod
  def node(cls, nType):
    return (cls.N, nType)

  @classmethod
  def terminate(cls, node=None):
    return (cls.T, node)

  @classmethod
  def resume(cls, node):
    return (cls.R, node)

  @classmethod
  def feature(cls, *nodes, **features):
    if len(nodes) == 0:
      return (cls.F, None, dict(features))
    return (cls.F, nodes[0], dict(features))

  @classmethod
  def edge(cls, nodeFrom, nodeTo, **features):
    return (cls.E, nodeFrom, nodeTo, dict(features))

  def __init__(self, TF):
    self.TF = TF

  def _showErrors(self):
    error = self.TF.tm.error
    info = self.TF.tm.info
    indent = self.TF.tm.indent

    good = self.good
    errors = self.errors

    if errors:
      for (kind, msgs) in sorted(errors.items()):
        error(f'ERROR {kind} ({len(msgs)} x):')
        indent(level=2)
        for msg in msgs[0:20]:
          error(f'{msg}', tm=False)
      self.errors = {}
      self.good = False
    else:
      info('OK' if good else 'ERROR(S)')

  def convert(
      self,
      tokens,
      slotType,
      otext={},
      generic={},
      intFeatures=set(),
      featureMeta={},
  ):
    info = self.TF.tm.info
    indent = self.TF.tm.indent

    indent(level=0, reset=True)
    info('Importing data from tokens ...')

    self.good = True
    self.errors = collections.defaultdict(list)
    self.slotType = slotType

    self.intFeatures = intFeatures
    self.featureMeta = featureMeta
    self.metaData = {}
    self.nodeFeatures = {}
    self.edgeFeatures = {}

    indent(level=1, reset=True)
    self._prepareMeta(otext, generic)

    indent(level=1, reset=True)
    self._slurp(tokens)

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

    indent(level=0)

    if self.good:
      self.good = self.TF.save(
          metaData=self.metaData,
          nodeFeatures=self.nodeFeatures,
          edgeFeatures=self.edgeFeatures,
      )
    return self.good

  def _prepareMeta(self, otext, generic):
    varRe = re.compile(r'\{([^}]+)\}')

    info = self.TF.tm.info
    indent = self.TF.tm.indent

    if not self.good:
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
      sectionLevels = {}
      for f in ('sectionTypes', 'sectionFeatures'):
        if f not in otext:
          errors['Incomplete section specs in "otext"'].append(f'no key "{f}"')
          sectionLevels[f] = []
        else:
          sectionLevels[f] = otext[f].split(',')
      sLevels = {f: len(sectionLevels[f]) for f in sectionLevels}
      if min(sLevels.values()) != max(sLevels.values()):
        errors['Inconsistent section info'].append(
            ' but '.join(f'"{f}" has {sLevels[f]} levels' for f in sLevels)
        )
      self.sectionFeatures = sectionLevels['sectionFeatures']
      self.sectionTypes = sectionLevels['sectionTypes']

      textFormats = {}
      textFeatures = set()
      for (k, v) in sorted(otext.items()):
        if k.startswith('fmt:'):
          featureSet = set()
          features = varRe.findall(v)
          for ff in features:
            for f in ff.split('/'):
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

    info(f'SECTION TYPES:    {", ".join(self.sectionTypes)}', tm=False)
    info(f'SECTION FEATURES: {", ".join(self.sectionFeatures)}', tm=False)
    info(f'TEXT    FEATURES"', tm=False)
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
      if feat in WARP[0:3] + ('',):
        if feat == '':
          errors['featureMeta'].append(
              f'Specify the generic feature meta data in "generic"'
          )
        elif feat == WARP[2]:
          errors['featureMeta'].append(
              f'Specify the "{WARP[2]}" feature in "otext"'
          )
        else:
          errors['featureMeta'].append(
              f'Do not pass metaData for the "{feat}" feature in "featureMeta"'
          )
          continue
      if 'valueType' in featMeta:
        errors['featureMeta'].append(
            f'Do not specify "valueType" for the "{feat}" feature in "featureMeta"'
        )
        continue
      metaData.setdefault(feat, {}).update(featMeta)
      metaData[feat]['valueType'] = 'int' if feat in intFeatures else 'str'

    self._showErrors()

  def _checkType(self, k, v, i, tokenType):
    if k in self.intFeatures:
      try:
        v = int(v)
      except Exception:
        self.errors[f'Not a number'].append(
            f'token {i}: "{tokenType}" node feature "{k}": "{v}"'
        )

  def _slurp(self, tokens):

    # node = yield (N, nodeType) : make a new node of type nodeType or slotNode
    # (T, node)                  : terminate specified or current node
    # (R, slot)                  : link current context nodes to the specified slot node
    # (R, node)                  : resume the specified non slot node
    # (F, node, featureDict)     : add features to specified or current node
    # (E, nodeFrom, edgeFrom, featureDict)
    #                            : add features to specified edge fron nodeFrom to nodeTo
    #
    # after node = yield ('N', nodeType) all slot nodes that are yielded
    # will be linked to node, until a ('T', node) is yielded.
    # If needed, you can resume this node again, after which new slot nodes
    # continue to be linked to this node.
    # If you resume a slot node, it all non slot nodes in the current context
    # will be linked to it.

    error = self.TF.tm.error
    info = self.TF.tm.info

    if not self.good:
      return

    info(f'Slurping tokens... ')

    slotType = self.slotType
    errors = self.errors

    curSeq = collections.Counter()
    curEmbedders = set()
    curNode = None
    oslots = collections.defaultdict(set)
    nodeFeatures = collections.defaultdict(dict)
    edgeFeatures = collections.defaultdict(lambda: collections.defaultdict(dict))
    nodes = collections.defaultdict(set)

    self.oslots = oslots
    self.nodeFeatures = nodeFeatures
    self.edgeFeatures = edgeFeatures
    self.nodeTypes = curSeq
    self.nodes = nodes

    stats = collections.Counter()
    info('Collecting tokens ...')
    i = 0
    token = next(tokens)

    try:
      while True:
        i += 1

        if not token:
          error(f'Terminated at token {i} = {token}')
          self.good = False
          tokens.close()
          continue

        tokenType = token[0]
        stats[tokenType] += 1

        if tokenType == self.N:
          nType = token[1]
          if nType is None:
            isSlot = True
            nType = slotType
          else:
            isSlot = False

          curSeq[nType] += 1
          seq = curSeq[nType]
          curNode = (nType, seq)

          if isSlot:
            for eNode in curEmbedders:
              oslots[eNode].add(seq)
          else:
            curEmbedders.add(curNode)

        elif tokenType == self.T:
          node = token[1]
          if node is None:
            node = curNode
          if node is not None:
            curEmbedders.discard(node)

        elif tokenType == self.R:
          node = token[1]
          (nType, seq) = node
          if nType == slotType:
            for eNode in curEmbedders:
              oslots[eNode].add(seq)
          else:
            curEmbedders.add(node)

        elif tokenType == self.F:
          (node, features) = token[1:]
          if node is None:
            node = curNode
          for (k, v) in features.items():
            self._checkType(k, v, i, tokenType)
            nodeFeatures[k][node] = v

        elif tokenType == self.E:
          (nodeFrom, nodeTo, features) = token[1:]
          for (k, v) in features.items():
            self._checkType(k, v, i, tokenType)
            edgeFeatures[k][nodeFrom][nodeTo] = v

        else:
          errors[f'Unrecognized token type'].append(
              f'token {i}: "{tokenType}"'
          )

        if tokenType == self.N:
          token = tokens.send((nType, seq))
        else:
          token = next(tokens)

    except StopIteration:
      pass

    info(f'collected {i} tokens')

    for tokenType in sorted(stats):
      info(f'"{tokenType}" tokens: {stats[tokenType]}')

    totalNodes = 0

    for (nType, lastSeq) in sorted(curSeq.items()):
      for seq in range(1, lastSeq + 1):
        nodes[nType].add(seq)
      slotRep = ' = slot type' if nType == slotType else ''
      info(f'{lastSeq:>8} x "{nType}" node {slotRep}', tm=False)
      totalNodes += lastSeq
    info(f'{totalNodes:>8} nodes of all types', tm=False)

    self.totalNodes = totalNodes

    self._showErrors()

  def _removeUnlinked(self):
    info = self.TF.tm.info
    indent = self.TF.tm.indent

    if not self.good:
      return

    nodeTypes = self.nodeTypes
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

    if not self.good:
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

    if not self.good:
      return

    info(f'checking features ... ')

    intFeatures = self.intFeatures
    featureMeta = self.featureMeta
    metaData = self.metaData

    nodes = self.nodes
    nodeFeatures = self.nodeFeatures
    edgeFeatures = self.edgeFeatures

    errors = self.errors

    for feat in intFeatures:
      if feat not in nodeFeatures and feat not in edgeFeatures:
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
    for feat in self.textFeatures:
      if feat not in nodeFeatures:
        errors['text formats'].append(
            f'"{feat}" is used in a text format, but this node feature does not occur'
        )

    for feat in WARP:
      if feat in nodeFeatures or feat in edgeFeatures:
        errors[feat].append(f'Do not construct the "{feat}" feature yourself')

    for feat in sorted(nodeFeatures) + sorted(edgeFeatures):
      if feat not in WARP and feat not in self.featureMeta:
        errors['feature metadata'].append(
            f'node feature "{feat}" has no metadata in featureMeta'
        )

    for feat in sorted(featureMeta):
      if feat not in WARP and feat not in nodeFeatures and feat not in edgeFeatures:
        errors['feature metadata'].append(
            f'node feature "{feat}" has metadata in featureMeta but does not occur'
        )

    for (feat, featData) in sorted(edgeFeatures.items()):
      hasValues = False
      for (nodeTo, toValues) in featData.items():
        if any(v is not None for v in toValues.values()):
          hasValues = True
          break

      if not hasValues:
        edgeFeatures[feat] = {nodeTo: set(toValues) for (nodeTo, toValues) in featData.items()}

      metaData.setdefault(feat, {})['edgeValues'] = hasValues

    self._showErrors()

  def _reorderNodes(self):
    info = self.TF.tm.info

    if not self.good:
      return

    info('reordering nodes ...')

    nodeTypes = self.nodeTypes
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

      aMin = min(slotsA - slotsB)
      bMin = min(slotsB - slotsA)
      return -1 if aMin < bMin else 1

    return functools.cmp_to_key(before)

  def _reassignFeatures(self):
    info = self.TF.tm.info
    indent = self.TF.tm.indent

    if not self.good:
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
