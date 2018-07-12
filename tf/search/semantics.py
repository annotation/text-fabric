import types

from .relations import add_K_Relations, add_V_Relations
from .syntax import reTp, kRe, deContext

# SEMANTIC ANALYSIS OF SEARCH TEMPLATE ###


def semantics(searchExe):
  if not searchExe.good:
    return
  error = searchExe.api.error
  msgCache = searchExe.msgCache
  searchExe.badSemantics = []
  offset = searchExe.offset

  _grammar(searchExe)

  if not searchExe.good:
    searchExe.showOuterTemplate(msgCache)
    for (i, line) in enumerate(searchExe.searchLines):
      error(f'{i + offset:>2} {line}', tm=False, cache=msgCache)
    for (ln, eline) in searchExe.badSemantics:
      txt = eline if ln is None else f'line {ln + offset}: {eline}'
      error(txt, tm=False, cache=msgCache)
    return

  if searchExe.good:
    _validation(searchExe)
  if not searchExe.good:
    searchExe.showOuterTemplate(msgCache)
    for (i, line) in enumerate(searchExe.searchLines):
      error(f'{i + offset:>2} {line}', tm=False, cache=msgCache)
    for (ln, eline) in searchExe.badSemantics:
      txt = eline if ln is None else f'line {ln + offset}: {eline}'
      error(txt, tm=False, cache=msgCache)


def _grammar(searchExe):
  prevKind = None
  good = True
  qnames = {}
  qnodes = []
  qedges = []
  edgeLine = {}
  nodeLine = {}
  nTokens = len(searchExe.tokens)

  def tokenSort(t):
    return (nTokens + t['ln']) if t['kind'] == 'rel' else t['ln']

  tokens = sorted(searchExe.tokens, key=tokenSort)

  # atomStack is a stack of qnodes with their indent levels
  # such that every next member is one level deeper
  # and every member is the last qnode encountered at that level
  # The stack is implemented as a dict,
  # keyed by the indent, and valued by the qnode
  atomStack = {}

  for token in tokens:
    i = token['ln']
    kind = token['kind']
    if kind == 'atom':
      if 'quantifiers' in token:
        token['quantifiers'] = [deContext(q, token['name']) for q in token['quantifiers']]
      indent = token['indent']
      op = token['op']
      if 'name' in token:
        name = token['name']
        otype = token['otype']
        features = token['features']
        src = token.get('src', '')
        quantifiers = token.get('quantifiers', [])
        qnodes.append((otype, features, src, quantifiers))
        q = len(qnodes) - 1
        nodeLine[q] = i
        name = f':{i}' if name == '' else name
        qnames[name] = q
      if len(atomStack) == 0:
        if indent > 0:
          searchExe.badSemantics.append(
              (i, f'Unexpected indent: {indent}, expected 0')
          )
          good = False
        if op is not None:
          searchExe.badSemantics.append(
              (i, f'Lonely relation: not allowed at outermost level')
          )
          good = False
        if 'name' in token:
          atomStack[0] = q
      else:
        atomNest = sorted(atomStack.items(), key=lambda x: x[0])
        top = atomNest[-1]
        if indent == top[0]:
          # sibling of previous atom
          if len(atomNest) > 1:
            if 'name' not in token:
              # lonely operator:
              # left is previous atom, right is parent atom
              qedges.append((top[1], op, atomNest[-2][1]))
              edgeLine[len(qedges) - 1] = i
            else:
              # take the qnode of the subtop of the
              # atomStack, if there is one
              qedges.append((q, ']]', atomNest[-2][1]))
              edgeLine[len(qedges) - 1] = i
              if op is not None:
                qedges.append((top[1], op, q))
                edgeLine[len(qedges) - 1] = i
          else:
            if op is not None:
              qedges.append((top[1], op, q))
              edgeLine[len(qedges) - 1] = i
        elif indent > top[0]:
          if 'name' not in token:
            searchExe.badSemantics.append(
                (i, f'Lonely relation: not allowed as first child'))
            good = False
          else:
            # child of previous atom
            qedges.append((q, ']]', top[1]))
            edgeLine[len(qedges) - 1] = i
            if op is not None:
              qedges.append((top[1], op, q))
              edgeLine[len(qedges) - 1] = i
        else:
          # outdent action:
          # look up the proper parent in the stack
          if indent not in atomStack:
            # parent cannot be found: indentation error
            searchExe.badSemantics.append(
                (
                    i,
                    'Unexpected indent: {}, expected one of {}'.format(
                        indent,
                        ', '.join(str(at[0]) for at in atomNest if at[0] < indent),
                    )
                )
            )
            good = False
          else:
            parents = [at[1] for at in atomNest if at[0] < indent]
            if len(parents) != 0:  # if not already at outermost level
              if 'name' not in token:
                # connect previous sibling to parent
                qedges.append((atomStack[indent], op, parents[-1]))
                edgeLine[len(qedges) - 1] = i
              else:
                qedges.append((q, ']]', parents[-1]))
                edgeLine[len(qedges) - 1] = i
                if op is not None:
                  qedges.append((atomStack[indent], op, q))
                  edgeLine[len(qedges) - 1] = i
            removeKeys = [at[0] for at in atomNest if at[0] > indent]
            for rk in removeKeys:
              del atomStack[rk]
        atomStack[indent] = q
    elif kind == 'feat':
      features = token['features']
      if prevKind is not None and prevKind != 'atom':
        searchExe.badSemantics.append((i, f'Features without atom: "{features}"'))
        good = False
      else:
        qnodes[-1][1].update(features)
    elif kind == 'rel':
      fName = token['f']
      tName = token['t']
      op = token['op']
      f = qnames.get(fName, None)
      t = qnames.get(tName, None)
      namesGood = True
      for (q, n) in ((f, fName), (t, tName)):
        if q is None:
          searchExe.badSemantics.append((i, f'Relation with undefined name: "{n}"'))
          namesGood = False
      if not namesGood:
        good = False
      else:
        qedges.append((f, op, t))
        edgeLine[len(qedges) - 1] = i
    prevKind = kind

  # resolve names when used in atoms
  for (q, qdata) in enumerate(qnodes):
    otype = qdata[0]
    referQ = qnames.get(otype, None)
    if referQ is not None:
      referOtype = qnodes[referQ][0]
      qnodes[q] = (referOtype, *qdata[1:])
      qedges.append((q, '=', referQ))

  if good:
      searchExe.qnames = qnames
      searchExe.qnodes = qnodes
      searchExe.qedgesRaw = qedges
      searchExe.nodeLine = nodeLine
      searchExe.edgeLine = edgeLine
  else:
    searchExe.good = False


def _validateFeature(
    searchExe, q, fName, features, missingFeatures, wrongValues, hasValues={}, asEdge=False
):
  values = features[fName]
  fSet = 'edges' if asEdge else 'nodes'
  if fName not in searchExe.api.TF.featureSets[fSet]:
    missingFeatures.setdefault(fName, []).append(q)
  else:
    if asEdge:
      doValues = searchExe.api.TF.features[fName].edgeValues
      if not doValues and values is not True:
        hasValues.setdefault(fName, {}).setdefault(values, []).append(q)
        return
    requiredType = searchExe.api.TF.features[fName].dataType
    if values is True:
      return
    elif values is None:
      return
    elif isinstance(values, types.FunctionType):
      if requiredType == 'str':
        wrongValues.setdefault(fName, {}).setdefault(values, []).append(q)
    elif isinstance(values, reTp):
      if requiredType == 'int':
        wrongValues.setdefault(fName, {}).setdefault(values, []).append(q)
    else:
      valuesCast = set()
      if requiredType == 'int':
        (ident, values) = values
        for val in values:
          try:
            valCast = int(val)
          except Exception:
            valCast = val
            wrongValues.setdefault(fName, {}).setdefault(val, []).append(q)
          valuesCast.add(valCast)
        features[fName] = (ident, frozenset(valuesCast))


def _validation(searchExe):
  levels = searchExe.api.C.levels.data
  otypes = set(x[0] for x in levels)
  qnodes = searchExe.qnodes
  nodeLine = searchExe.nodeLine
  edgeMap = searchExe.edgeMap

  edgeLine = searchExe.edgeLine
  relationFromName = searchExe.relationFromName

  offset = searchExe.offset

  # check the object types of atoms

  good = True
  otypesGood = True
  sets = searchExe.sets
  for (q, qdata) in enumerate(qnodes):
    otype = qdata[0]
    if sets is not None and otype in sets:
      continue
    if otype not in otypes:
      searchExe.badSemantics.append((nodeLine[q], f'Unknown object type: "{otype}"'))
      otypesGood = False
  if not otypesGood:
    searchExe.badSemantics.append(
        (None, 'Valid object types are: {}'.format(', '.join(x[0] for x in levels), ))
    )
    if sets is not None:
      searchExe.badSemantics.append(
          (None, 'Or choose a custom set from: {}'.format(', '.join(x for x in sorted(sets)), ))
      )
    good = False

  # check the feature names of feature specs
  # and check the types of their values

  missingFeatures = {}
  wrongValues = {}
  hasValues = {}
  for (q, qdata) in enumerate(qnodes):
    features = qdata[1]
    for fName in sorted(features):
      _validateFeature(searchExe, q, fName, features, missingFeatures, wrongValues)

  # check the relational operator token in edges
  # and replace them by an index
  # in the relations array of known relations
  qedges = []
  edgesGood = True

  # relations may have a variable number k in them (k-nearness, etc.)
  # make an entry in the relation map for each value of k
  addRels = {}
  for (e, (f, op, t)) in enumerate(searchExe.qedgesRaw):
    if (
        type(op) is tuple or (op[0] == '-' and op[-1] == '>') or (op[0] == '<' and op[-1] == '-')
    ):
      continue
    match = kRe.findall(op)
    if len(match):
      (pre, k, post) = match[0]
      opNameK = f'{pre}k{post}'
      addRels.setdefault(opNameK, set()).add(int(k))
  add_K_Relations(searchExe, addRels)

  # edge relations may have a value spec in them
  # make an entry in the relation map for each value spec
  addRels = {}
  for (e, (f, op, t)) in enumerate(searchExe.qedgesRaw):
    if type(op) is not tuple:
      continue
    (opName, opFeatures) = op
    for eName in sorted(opFeatures):
      _validateFeature(
          searchExe,
          e, eName, opFeatures, missingFeatures, wrongValues, hasValues, asEdge=True
      )
      addRels.setdefault(opName, set()).add((eName, opFeatures[eName]))
  add_V_Relations(searchExe, addRels)

  # now look up each particalur relation in the relation map
  for (e, (f, op, t)) in enumerate(searchExe.qedgesRaw):
    theOp = op[0] if type(op) is tuple else op
    rela = relationFromName.get(theOp, None)
    if rela is None:
      searchExe.badSemantics.append((edgeLine[e], f'Unknown relation: "{theOp}"'))
      edgesGood = False
    qedges.append((f, rela, t))
  if not edgesGood:
    searchExe.badSemantics.append((None, f'Allowed relations:\n{searchExe.relationLegend}'))
    good = False

  # report error found above
  if len(missingFeatures):
    for (fName, qs) in sorted(missingFeatures.items()):
      searchExe.badSemantics.append((
          None,
          'Missing feature "{}" in line(s) {}'.format(
              fName,
              ', '.join(str(nodeLine[q] + offset) for q in qs),
          )
      ))
    good = False

  if len(hasValues):
    for (fName, wrongs) in sorted(hasValues.items()):
      searchExe.badSemantics.append((None, f'Feature "{fName}" has cannot have values:'))
      for (val, qs) in sorted(wrongs.items()):
        searchExe.badSemantics.append((
            None,
            '    "{}" superfluous: line(s) {}'.format(
                val,
                ', '.join(str(nodeLine[q] + offset) for q in qs),
            )
        ))
    good = False

  if len(wrongValues):
    for (fName, wrongs) in sorted(wrongValues.items()):
      searchExe.badSemantics.append((None, f'Feature "{fName}" has wrong values:'))
      for (val, qs) in sorted(wrongs.items()):
        searchExe.badSemantics.append((
            None,
            '    "{}" is not a number: line(s) {}'.format(
                val,
                ', '.join(str(nodeLine[q] + offset) for q in qs),
            )
        ))
    good = False

  searchExe.qedges = qedges

  # determine which node and edge features are not yet loaded,
  # and load them
  eFeatsUsed = set()
  for (f, rela, t) in qedges:
    efName = edgeMap.get(rela, (None, ))[0]
    if efName is not None:
      eFeatsUsed.add(efName)
  nFeatsUsed = set()
  for qdata in qnodes:
    features = qdata[1]
    for nfName in features:
      nFeatsUsed.add(nfName)

  if good:
    searchExe.api.ensureLoaded(eFeatsUsed | nFeatsUsed)
  else:
    searchExe.good = False
