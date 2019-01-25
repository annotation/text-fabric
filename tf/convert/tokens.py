import collections
import functools
import re

from ..core.data import WARP


class Tokens(object):

  def __init__(self, tm):
    self.tm = tm

  def _showErrors(self):
    error = self.tm.error
    info = self.tm.info
    indent = self.tm.indent

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

  def convert(self, tokens, slotType, otext, generic, intFeatures, featureMeta):
    info = self.tm.info
    indent = self.tm.indent

    indent(level=0, reset=True)
    info('Importing data from tokens ...')

    self.good = True
    self.errors = {}
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

    return (
        self.good,
        dict(
            metaData=self.metaData,
            nodeFeatures=self.nodeFeatures,
            edgeFeatures=self.edgeFeatures,
        ),
    )

  def _prepareMeta(self, otext, generic):
    varRe = re.compile(r'\{([^}]+)\}')

    info = self.tm.info
    indent = self.tm.indent

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
      errors.setdefault('Missing feature meta data in "generic"', []).append(
          'Consider adding provenance metadata to all features'
      )
    if not otext:
      errors.setdefault('Missing "otext" configuration', []).append(
          'Consider adding configuration for text representation and section levels'
      )
    else:
      sectionLevels = {}
      for f in ('sectionTypes', 'sectionFeatures'):
        if f not in otext:
          errors.setdefault('Incomplete section specs in "otext"', []).append(f'no key "{f}"')
          sectionLevels[f] = []
        else:
          sectionLevels[f] = otext[f].split(',')
      sLevels = {f: len(sectionLevels[f]) for f in sectionLevels}
      if min(sLevels.values()) != max(sLevels.values()):
        errors.setdefault('Inconsistent section info', []).append(
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
        errors.setdefault('No text formats in "otext"', []).append(
            f'add "fmt:text-orig-full"'
        )
      elif 'text-orig-full' not in textFormats:
        errors.setdefault('No default text format in otext', []).append(
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
          errors.setdefault('intFeatures', []).append(
              'Do not declare the "valueType" for all features'
          )
        else:
          errors.setdefault('intFeatures', []).append(
              f'Do not mark the "{feat}" feature as integer valued'
          )
        self.good = False
    for (feat, featMeta) in sorted(featureMeta.items()):
      if feat in WARP[0:3] + ('',):
        if feat == '':
          errors.setdefault('featureMeta', []).append(
              f'Specify the generic feature meta data in "generic"'
          )
        elif feat == WARP[2]:
          errors.setdefault('featureMeta', []).append(
              f'Specify the "{WARP[2]}" feature in "otext"'
          )
        else:
          errors.setdefault('featureMeta', []).append(
              f'Do not pass metaData for the "{feat}" feature in "featureMeta"'
          )
          continue
      if 'valueType' in featMeta:
        errors.setdefault('featureMeta', []).append(
            f'Do not specify "valueType" for the "{feat}" feature in "featureMeta"'
        )
        continue
      metaData.setdefault(feat, {}).update(featMeta)
      metaData[feat]['valueType'] = 'int' if feat in intFeatures else 'str'

    self._showErrors()

  def _slurp(self, tokens):

    # slot token         (S, seq, ((type, seq),...)), features)
    # node feature token (N, (type, seq), features)
    # edge feature token (E, (typeFrom, seqFrom), (typeTo, seqTo), features)

    S = 'S'
    N = 'N'
    E = 'E'
    NN = {S, N}

    error = self.tm.error
    info = self.tm.info

    if not self.good:
      return

    info(f'Slurping tokens... ')

    self.otypeProto = {}
    self.oslotsProto = {}
    self.nodeFeaturesProto = {}
    self.edgeFeaturesProto = {}
    self.slots = set()
    self.nodesProto = {}

    slotType = self.slotType
    otypeProto = self.otypeProto
    oslotsProto = self.oslotsProto
    nodeFeaturesProto = self.nodeFeaturesProto
    edgeFeaturesProto = self.edgeFeaturesProto
    nodesProto = self.nodesProto
    slots = self.slots
    errors = self.errors

    stats = collections.Counter()
    info('Collecting tokens ...')
    i = 0

    for token in tokens:
      i += 1
      if not token:
        error(f'Terminated at token {i} = {token}')
        self.good = False
        break

      tokenType = token[0]
      stats[tokenType] += 1

      if tokenType == S:
        nType = slotType
        seq = token[1]
        embedders = token[2]
        features = token[3]
      elif tokenType == N:
        nType = token[1][0]
        seq = token[1][1]
        features = token[2]
      elif tokenType == E:
        nTypeF = token[1][0]
        seqF = token[1][1]
        nTypeT = token[2][0]
        seqT = token[2][1]
        features = token[3]
      else:
        errors.setdefault(f'Unrecognized token type', []).append(
            f'token {i}: "{tokenType}"'
        )
        continue
      if tokenType in NN:
        try:
          seq = int(seq)
        except Exception:
          errors.setdefault(f'Not a number', []).append(
              f'token {i}: "{tokenType}" {nType} "{seq}"'
          )
          break
      elif tokenType == E:
        try:
          seqF = int(seqF)
        except Exception:
          errors.setdefault(f'Not a number', []).append(
              f'token {i}: "{tokenType}" *from* {nTypeF} "{seqF}"'
          )
          break
        try:
          seqT = int(seqT)
        except Exception:
          errors.setdefault(f'Not a number', []).append(
              f'token {i}: "{tokenType}" *to* {nTypeT} "{seqT}"'
          )
          break

      if tokenType in NN:
        node = (nType, seq)
        nodesProto.setdefault(nType, set()).add(seq)
        otypeProto[node] = nType
        for (k, v) in features.items():
          if k in self.intFeatures:
            try:
              v = int(v)
            except Exception:
              errors.setdefault(f'Not a number', []).append(
                  f'token {i}: "{tokenType}" node feature "{k}": "{v}"'
              )
          nodeFeaturesProto.setdefault(k, {})[node] = v
        if tokenType == S:
          slots.add(seq)
          for (nTypeE, seqE) in embedders:
            try:
              seqE = int(seqE)
            except Exception:
              errors.setdefault(f'Not a number', []).append(
                  f'token {i}: "{tokenType}" *embedder* {nTypeE} "{seqE}"'
              )
              break
            nodeE = (nTypeE, seqE)
            oslotsProto.setdefault(nodeE, set()).add(node)
      elif tokenType == E:
        nodeF = (nTypeF, seqF)
        nodeT = (nTypeT, seqT)
        for (k, v) in features.items():
          if k in self.intFeatures:
            try:
              v = int(v)
            except Exception:
              errors.setdefault(f'Not a number', []).append(
                  f'token {i}: edge feature "{k}": "{v}"'
              )
          edgeFeaturesProto.setdefault(k, {}).setdefault(nodeF, {})[nodeT] = v

    info(f'collected {i} tokens')

    for tokenType in sorted(stats):
      info(f'"{tokenType}" tokens: {stats[tokenType]}')

    totalNodes = 0

    for (nType, ns) in sorted(nodesProto.items()):
      slotRep = ' = slot type' if nType == slotType else ''
      lns = len(ns)
      info(f'{lns:>8} x "{nType}" node {slotRep}', tm=False)
      totalNodes += lns
    info(f'{totalNodes:>8} nodes of all types', tm=False)

    self.totalNodes = totalNodes

    self._showErrors()

  def _removeUnlinked(self):
    info = self.tm.info
    indent = self.tm.indent

    if not self.good:
      return

    nodesProto = self.nodesProto
    slotType = self.slotType
    otypeProto = self.otypeProto
    oslotsProto = self.oslotsProto
    nodeFeaturesProto = self.nodeFeaturesProto
    edgeFeaturesProto = self.edgeFeaturesProto

    unlinked = {}

    for nType in nodesProto:
      if nType == slotType:
        continue
      for seq in nodesProto[nType]:
        if (nType, seq) not in oslotsProto:
          unlinked.setdefault(nType, []).append(seq)

    if unlinked:
      info(f'Removing unlinked nodes ... ')
      indent(level=2)
      totalRemoved = 0
      for (nType, seqs) in unlinked.items():
        theseNodesProto = nodesProto[nType]
        lSeqs = len(seqs)
        totalRemoved += lSeqs
        rep = ' ...' if lSeqs > 5 else ''
        pl = '' if lSeqs == 1 else 's'
        info(f'{lSeqs:>6} unlinked "{nType}" node{pl}: {seqs[0:5]}{rep}')
        for seq in seqs:
          node = (nType, seq)
          theseNodesProto.discard(seq)
          if node in otypeProto:
            del otypeProto[node]
          for (f, fData) in nodeFeaturesProto.items():
            if node in fData:
              del fData[node]
          for (f, fData) in edgeFeaturesProto.items():
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
    info = self.tm.info

    if not self.good:
      return

    info(f'checking for nodes and edges ... ')

    slots = self.slots
    nodesProto = self.nodesProto
    errors = self.errors
    edgeFeaturesProto = self.edgeFeaturesProto

    # slot sequence

    lSlots = len(slots)
    mxSlots = max(slots)
    mnSlots = min(slots)
    if len(slots) != max(slots):
      errors.setdefault('Slot sequence', []).append(
          f'{lSlots} found between {mnSlots} and {mxSlots}:'
          f' not an unbroken sequence from 1 to {lSlots}'
      )

    # edges refer to nodes

    for (k, featureData) in edgeFeaturesProto.items():
      for nFrom in featureData:
        (nType, seq) = nFrom
        if nType not in nodesProto or seq not in nodesProto[nType]:
          errors.setdefault('Edge feature: illegal node', []).append(
              f'"{k}": from-node  {nFrom} not in node set'
          )
          continue
        for nTo in featureData[nFrom]:
          (nType, seq) = nTo
          if nType not in nodesProto or seq not in nodesProto[nType]:
            errors.setdefault('Edge feature: illegal node', []).append(
                f'"{k}": to-node  {nTo} not in node set'
            )

    self._showErrors()

  def _checkFeatures(self):
    info = self.tm.info

    if not self.good:
      return

    info(f'checking features ... ')

    intFeatures = self.intFeatures
    featureMeta = self.featureMeta
    metaData = self.metaData

    nodesProto = self.nodesProto
    nodeFeaturesProto = self.nodeFeaturesProto
    edgeFeaturesProto = self.edgeFeaturesProto

    errors = self.errors

    for feat in intFeatures:
      if feat not in nodeFeaturesProto and feat not in edgeFeaturesProto:
        errors.setdefault('intFeatures', []).append(
            f'"{feat}" is declared as integer valued, but this feature does not occur'
        )
    for nType in self.sectionTypes:
      if nType not in nodesProto:
        errors.setdefault('sections', []).append(
            f'node type "{nType}" is declared as a section type, but this node type does not occur'
        )
    for feat in self.sectionFeatures:
      if feat not in nodeFeaturesProto:
        errors.setdefault('sections', []).append(
            f'"{feat}" is declared as a section feature, but this node feature does not occur'
        )
    for feat in self.textFeatures:
      if feat not in nodeFeaturesProto:
        errors.setdefault('text formats', []).append(
            f'"{feat}" is used in a text format, but this node feature does not occur'
        )

    for feat in WARP:
      if feat in nodeFeaturesProto or feat in edgeFeaturesProto:
        errors.setdefault(feat, []).append(f'Do not construct the "{feat}" feature yourself')

    for feat in sorted(nodeFeaturesProto) + sorted(edgeFeaturesProto):
      if feat not in WARP and feat not in self.featureMeta:
        errors.setdefault('feature metadata', []).append(
            f'node feature "{feat}" has no metadata in featureMeta'
        )

    for feat in sorted(featureMeta):
      if feat not in WARP and feat not in nodeFeaturesProto and feat not in edgeFeaturesProto:
        errors.setdefault('feature metadata', []).append(
            f'node feature "{feat}" has metadata in featureMeta but does not occur'
        )

    for feat in sorted(edgeFeaturesProto):
      metaData.setdefault(feat, {})['edgeValues'] = True

    self._showErrors()

  def _reorderNodes(self):
    info = self.tm.info

    if not self.good:
      return

    info('reordering nodes ...')

    nodesProto = self.nodesProto
    slots = self.slots
    slotType = self.slotType

    nTypes = (slotType,) + tuple(sorted(nType for nType in nodesProto if nType != slotType))

    self.nodeMap = {}
    self.maxSlot = len(slots)

    nodeMap = self.nodeMap
    maxSlot = self.maxSlot

    n = 0

    for nType in nTypes:
      nodes = nodesProto[nType]
      canonical = self._canonical(nType)
      if nType == slotType:
        sortedNodes = range(1, maxSlot + 1)
      else:
        info(f'Sorting {len(nodes)} nodes of type "{nType}"')
        sortedNodes = sorted(nodes, key=canonical)
      for node in sortedNodes:
        n += 1
        nodeMap[(nType, node)] = n

    self.maxNode = n
    info(f'Max node = {n}')

    self._showErrors()

  def _canonical(self, nType):
    oslotsProto = self.oslotsProto

    def before(nodeA, nodeB):
      slotsA = {x[1] for x in oslotsProto[(nType, nodeA)]}
      slotsB = {x[1] for x in oslotsProto[(nType, nodeB)]}
      if slotsA == slotsB:
        return 0

      aMin = min(slotsA - slotsB)
      bMin = min(slotsB - slotsA)
      return -1 if aMin < bMin else 1

    return functools.cmp_to_key(before)

  def _reassignFeatures(self):
    info = self.tm.info
    indent = self.tm.indent

    if not self.good:
      return

    info('reassigning feature values ...')

    nodeMap = self.nodeMap
    otypeProto = self.otypeProto
    oslotsProto = self.oslotsProto
    nodeFeaturesProto = self.nodeFeaturesProto
    edgeFeaturesProto = self.edgeFeaturesProto

    nodeFeaturesProto['otype'] = otypeProto
    edgeFeaturesProto['oslots'] = oslotsProto

    nodeFeatures = self.nodeFeatures
    edgeFeatures = self.edgeFeatures

    indent(level=2)

    for k in sorted(nodeFeaturesProto):
      featureDataProto = nodeFeaturesProto[k]
      info(f'node feature "{k}" with {len(featureDataProto)} nodes')
      featureData = {}
      for (node, value) in featureDataProto.items():
        featureData[nodeMap[node]] = value
      nodeFeatures[k] = featureData

    for k in sorted(edgeFeaturesProto):
      featureDataProto = edgeFeaturesProto[k]
      info(f'edge feature "{k}" with {len(featureDataProto)} start nodes')
      featureData = {}
      for (nodeFrom, toValues) in featureDataProto.items():
        if type(toValues) is set:
          toData = set()
          for nodeTo in toValues:
            toData.add(nodeMap[nodeTo])
        else:
          toData = {}
          for (nodeTo, value) in toValues.items():
            toData[nodeMap[nodeTo]] = value
        featureData[nodeMap[nodeFrom]] = toData
      edgeFeatures[k] = featureData

    indent(level=1)

    self.oslotsProto = None
    self.otypeProto = None
    self.nodeFeaturesProto = None
    self.edgeFeaturesProto = None

    self._showErrors()
