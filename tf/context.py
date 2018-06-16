from functools import reduce


def gatherContext(api, context, nodeTypes, results):
  F = api.F
  Fs = api.Fs
  Es = api.Es
  L = api.L
  T = api.T
  TF = api.TF
  sortNodes = api.sortNodes

  # quit quickly if no context is required
  if not context or not results:
    return {}

  # parse the context requirements
  if context is True:
    langs = True
    featureSpec = True
    doLocality = True
    textFormats = True
  else:
    langs = context.get('languages', set())
    featureSpec = context.get('features', set())
    doLocality = context.get('locality', False)
    textFormats = context.get('formats', set())

  if type(langs) is str:
    langs = set(langs.strip().split())
  elif langs is True:
    langs = set(T.languages)

  if type(featureSpec) is str:
    featureSpec = set(featureSpec.strip().split())
  elif featureSpec is True:
    featureSpec = {f[0] for f in TF.features.items() if not (f[1].isConfig or f[1].method)}
  else:
    featureSpec = {fName for fName in featureSpec}

  testLangs = langs | {None}
  featureSpec = {fName for fName in featureSpec if _depLang(fName) in testLangs}

  if type(textFormats) is str:
    textFormats = set(textFormats.strip().split())
  elif textFormats is True:
    textFormats = T.formats

  # get all nodes

  allNodes = reduce(
      set.union,
      (set(r) for r in results),
      set(),
  )

  if nodeTypes:
    nodeTypes = set(nodeTypes)
    newNodes = set()
    for n in allNodes:
      newNodes |= {m for m in L.d(n) if F.otype.v(m) in nodeTypes}
      newNodes |= {m for m in L.u(n) if F.otype.v(m) in nodeTypes}
  allNodes |= newNodes

  # generate context: features

  loadedFeatures = api.ensureLoaded(featureSpec)
  features = {}
  featureType = {}
  for f in sorted(loadedFeatures):
    fObj = TF.features[f]
    isEdge = fObj.isEdge
    isNode = not (isEdge or fObj.isConfig or fObj.method)
    if isNode:
      featureType[f] = 0
      data = {}
      for n in allNodes:
        val = Fs(f).v(n)
        if val is not None:
          data[n] = val
      features[f] = data
    elif isEdge:
      if f == 'oslots':
        featureType[f] = -1
        data = {}
        for n in allNodes:
          vals = tuple(m for m in Es(f).s(n) if m in allNodes)
          if vals:
            data[n] = vals
        features[f] = data
      else:
        hasValues = TF.features[f].edgeValues
        featureType[f] = 1 if hasValues else -1
        dataF = {}
        dataT = {}
        if hasValues:
          for n in allNodes:
            valsF = tuple(x for x in Es(f).f(n) if x[0] in allNodes)
            valsT = tuple(x for x in Es(f).t(n) if x[0] in allNodes)
            if valsF:
              dataF[n] = valsF
            if valsT:
              dataT[n] = valsT
        else:
          for n in allNodes:
            valsF = tuple(m for m in Es(f).f(n) if m in allNodes)
            valsT = tuple(m for m in Es(f).t(n) if m in allNodes)
            if valsF:
              dataF[n] = valsF
            if valsT:
              dataT[n] = valsT
        features[f] = (dataF, dataT)

  # generate context: locality

  locality = {}
  if doLocality:
    lu = {}
    ld = {}
    ln = {}
    lp = {}
    for n in allNodes:
      lu[n] = tuple(m for m in L.u(n) if m in allNodes)
      ld[n] = tuple(m for m in L.d(n) if m in allNodes)
      ln[n] = tuple(m for m in L.n(n) if m in allNodes)
      lp[n] = tuple(m for m in L.p(n) if m in allNodes)
    locality['u'] = lu
    locality['d'] = ld
    locality['n'] = ln
    locality['p'] = lp

  # generate context: formats

  slotType = F.otype.slotType
  text = {}
  slots = sorted(n for n in allNodes if F.otype.v(n) == slotType)
  for fmt in textFormats:
    data = {}
    for n in slots:
      data[n] = T.text([n], fmt=fmt)
    text[fmt] = data

  return dict(
      nodes=','.join(str(n) for n in sortNodes(allNodes)),
      features=features,
      featureType=featureType,
      locality=locality,
      text=text,
      langs=langs,
  )


def _depLang(feature):
  if '@' not in feature:
    return None
  else:
    return feature.rsplit('@', 1)[1]
