import types
from random import randrange
from inspect import signature

from .syntax import (
    reTp,
    cleanParent,
    QWHERE,
    QWITHOUT,
    QWITH,
    QHAVE,
    QOR,
    QEND,
)
from ..core.helpers import project

# SPINNING ###


def _spinAtom(searchExe, q):
  F = searchExe.api.F
  Fs = searchExe.api.Fs
  qnodes = searchExe.qnodes
  sets = searchExe.sets

  (otype, features, src, quantifiers) = qnodes[q]
  featureList = sorted(features.items())
  yarn = set()
  nodeSet = sets[otype] if sets is not None and otype in sets else F.otype.s(otype)
  for n in nodeSet:
    good = True
    for (ft, val) in featureList:
      fval = Fs(ft).v(n)
      if val is None:
        if fval is not None:
          good = False
          break
      elif val is True:
        if fval is None:
          good = False
          break
      elif isinstance(val, types.FunctionType):
        if not val(fval):
          good = False
          break
      elif isinstance(val, reTp):
        if fval is None or not val.search(fval):
          good = False
          break
      else:
        (ident, val) = val
        if ident is None and val is True:
          pass
        elif ident:
          if fval not in val:
            good = False
            break
        else:
          if fval in val:
            good = False
            break
    if good:
      yarn.add(n)
  if quantifiers:
    for quantifier in quantifiers:
      yarn = _doQuantifier(searchExe, yarn, src, quantifier)
  searchExe.yarns[q] = yarn


def _doQuantifier(searchExe, yarn, atom, quantifier):
  from .searchexe import SearchExe
  (quKind, quTemplates, parentName, ln) = quantifier
  info = searchExe.api.info
  msgCache = searchExe.msgCache
  indent = searchExe.api.indent
  showQuantifiers = searchExe.showQuantifiers
  level = searchExe.level
  universe = yarn
  cleanAtom = cleanParent(atom, parentName)
  offset = searchExe.offset + ln

  if showQuantifiers:
    indent(level=level + 1, reset=True)
    info(f'"Quantifier on "{cleanAtom}"', cache=msgCache)

  if quKind == QWITHOUT:
    queryN = '\n'.join((cleanAtom, quTemplates[0]))
    exe = SearchExe(
        searchExe.api,
        queryN,
        outerTemplate=searchExe.outerTemplate,
        quKind=quKind,
        level=level + 1,
        offset=offset,
        sets=searchExe.sets,
        shallow=True,
        showQuantifiers=showQuantifiers,
        msgCache=msgCache,
        setInfo=searchExe.setInfo,
    )
    if showQuantifiers:
      indent(level=level + 2, reset=True)
      info(f'{quKind}\n{queryN}\n{QEND}', tm=False, cache=msgCache)
    noResults = exe.search()
    resultYarn = universe - noResults
    if showQuantifiers:
      indent(level=level + 2)
      info(f'{len(noResults)} nodes to exclude', cache=msgCache)
  elif quKind == QWHERE:
    # compute the atom+antecedent:
    #   as result tuples
    queryA = '\n'.join((cleanAtom, quTemplates[0]))
    exe = SearchExe(
        searchExe.api,
        queryA,
        outerTemplate=searchExe.outerTemplate,
        quKind=quKind,
        offset=offset,
        level=level + 1,
        sets=searchExe.sets,
        shallow=False,
        showQuantifiers=showQuantifiers,
        msgCache=msgCache,
        setInfo=searchExe.setInfo,
    )
    if showQuantifiers:
      indent(level=level + 2, reset=True)
      info(f'{quKind}\n{queryA}', tm=False, cache=msgCache)
    aResultTuples = exe.search(limit=-1)
    if showQuantifiers:
      indent(level=level + 2)
      info(f'{len(aResultTuples)} matching nodes', cache=msgCache)
    if not aResultTuples:
      resultYarn = yarn
    else:
      sizeA = len(aResultTuples[0])

      # compute the atom+antecedent+consequent:
      #   as shallow result tuples (same length as atom+antecedent)
      queryAH = '\n'.join((cleanAtom, *quTemplates))
      offset += len(quTemplates[0].split('\n'))
      exe = SearchExe(
          searchExe.api,
          queryAH,
          outerTemplate=searchExe.outerTemplate,
          quKind=QHAVE,
          offset=offset,
          level=level + 1,
          sets=searchExe.sets,
          shallow=sizeA,
          showQuantifiers=showQuantifiers,
          msgCache=msgCache,
          setInfo=searchExe.setInfo,
      )
      if showQuantifiers:
        indent(level=level + 2, reset=True)
        info(f'{QHAVE}\n{queryAH}\n{QEND}', tm=False, cache=msgCache)
      ahResults = exe.search()
      if showQuantifiers:
        indent(level=level + 2)
        info(f'{len(ahResults)} matching nodes', cache=msgCache)

      # determine the shallow tuples that correspond to
      #   atom+antecedent but not consequent
      #   and then take the projection to their first components
      resultsAnotH = project(set(aResultTuples) - ahResults, 1)
      if showQuantifiers:
        indent(level=level + 2)
        info(f'{len(resultsAnotH)} match antecedent but not consequent', cache=msgCache)

      # now have the atoms that do NOT qualify:
      #   we subtract them from the universe
      resultYarn = universe - resultsAnotH
  elif quKind == QWITH:
    # compute the atom+alternative for all alternatives and union them
    resultYarn = set()
    nAlts = len(quTemplates)
    for (i, alt) in enumerate(quTemplates):
      queryAlt = '\n'.join((cleanAtom, alt))
      exe = SearchExe(
          searchExe.api,
          queryAlt,
          outerTemplate=searchExe.outerTemplate,
          quKind=quKind if i == 0 else QOR,
          offset=offset,
          level=level + 1,
          sets=searchExe.sets,
          shallow=True,
          showQuantifiers=showQuantifiers,
          msgCache=msgCache,
          setInfo=searchExe.setInfo,
      )
      offset += len(alt.split('\n')) + 1
      if showQuantifiers:
        indent(level=level + 2, reset=True)
        info((f'{quKind if i == 0 else QOR}\n{queryAlt}'), tm=False, cache=msgCache)
      altResults = exe.search()
      altResults &= universe
      nAlt = len(altResults)
      nYarn = len(resultYarn)
      resultYarn |= altResults
      nNew = len(resultYarn)
      if showQuantifiers:
        indent(level=level + 2)
        info(f'adding {nAlt} to {nYarn} yields {nNew} nodes', cache=msgCache)
        if i == nAlts - 1:
          info(QEND, tm=False, cache=msgCache)
  if showQuantifiers:
    indent(level=level + 1)
    info(f'reduction from {len(yarn)} to {len(resultYarn)} nodes', cache=msgCache)
    indent(level=0)
  return resultYarn


def spinAtoms(searchExe):
  qnodes = searchExe.qnodes
  for q in range(len(qnodes)):
    _spinAtom(searchExe, q)


def estimateSpreads(searchExe, both=False):
  TRY_LIMIT_F = 10
  TRY_LIMIT_T = 10
  qnodes = searchExe.qnodes
  relations = searchExe.relations
  converse = searchExe.converse
  qedges = searchExe.qedges
  yarns = searchExe.yarns

  spreadsC = {}
  spreads = {}

  for (e, (f, rela, t)) in enumerate(qedges):
    tasks = [(f, rela, t, 1)]
    if both:
      tasks.append((t, converse[rela], f, -1))
    for (tf, trela, tt, dir) in tasks:
      s = relations[trela]['spin']
      yarnF = yarns[tf]
      yarnT = yarns[tt]
      dest = spreads if dir == 1 else spreadsC
      if type(s) is float:
        # fixed estimates
        dest[e] = len(yarnT) * s
        continue
      yarnF = list(yarnF)
      yarnT = yarns[tt]
      totalSpread = 0
      yarnFl = len(yarnF)
      if yarnFl < TRY_LIMIT_F:
        triesn = yarnF
      else:
        triesn = set(yarnF[randrange(yarnFl)] for n in range(TRY_LIMIT_F))
      if len(triesn) == 0:
        dest[e] = 0
      else:
        r = relations[trela]['func'](qnodes[tf][0], qnodes[tt][0])
        nparams = len(signature(r).parameters)
        if nparams == 1:
          for n in triesn:
            mFromN = set(r(n)) & yarnT
            totalSpread += len(mFromN)
        else:
          for n in triesn:
            thisSpread = 0
            yarnTl = len(yarnT)
            if yarnTl < TRY_LIMIT_T:
              triesm = yarnT
            else:
              triesm = set(list(yarnT)[randrange(yarnTl)] for m in range(TRY_LIMIT_T))
            if len(triesm) == 0:
              thisSpread = 0
            else:
              for m in triesm:
                if r(n, m):
                  thisSpread += 1
            totalSpread += yarnTl * thisSpread / len(triesm)
        dest[e] = totalSpread / len(triesn)
  searchExe.spreads = spreads
  searchExe.spreadsC = spreadsC


def _chooseEdge(searchExe):
  F = searchExe.api.F
  yarnFractionNode = {}
  qnodes = searchExe.qnodes
  qedges = searchExe.qedges
  spreads = searchExe.spreads
  sets = searchExe.sets
  for (q, qdata) in enumerate(qnodes):
    otype = qdata[0]
    if sets is not None and otype in sets:
      nodeSet = sets[otype]
      nOtype = len(nodeSet)
    else:
      (begin, end) = F.otype.sInterval(otype)
      nOtype = 1 + end - begin
    nYarn = len(searchExe.yarns[q])
    yf = nYarn / nOtype
    yarnFractionNode[q] = yf * yf
  yarnFractionEdge = {}
  for (e, (f, rela, t)) in enumerate(qedges):
    if searchExe.uptodate[e]:
      continue
    yarnFractionEdge[e] = yarnFractionNode[f] + yarnFractionNode[t] + spreads[e]
  firstEdge = sorted(yarnFractionEdge.items(), key=lambda x: x[1])[0][0]
  return firstEdge


def _spinEdge(searchExe, e):
  SPIN_LIMIT = 1000
  qnodes = searchExe.qnodes
  relations = searchExe.relations
  yarns = searchExe.yarns
  spreads = searchExe.spreads
  qedges = searchExe.qedges
  uptodate = searchExe.uptodate

  (f, rela, t) = qedges[e]
  yarnF = yarns[f]
  yarnT = yarns[t]
  uptodate[e] = True

  # if the yarns around an edge are big,
  # and the spread of the relation is
  # also big, spinning costs an enormous amount of time,
  # and will not help in reducing the search space.
  # condition for skipping: spread times length from-yarn >= SPIN_LIMIT
  if spreads[e] * len(yarnF) >= SPIN_LIMIT:
    return

  # for some basic relations we know that spinning is useless
  s = relations[rela]['spin']
  if type(s) is float:
    return

  # for other basic realtions we have an optimized spin function
  # if type(s) is types.FunctionType:
  if isinstance(s, types.FunctionType):
    (newYarnF, newYarnT) = s(qnodes[f][0], qnodes[t][0])(yarnF, yarnT)
  else:
    r = relations[rela]['func'](qnodes[f][0], qnodes[t][0])
    nparams = len(signature(r).parameters)
    newYarnF = set()
    newYarnT = set()

    if nparams == 1:
      for n in yarnF:
        mFromN = set(r(n)) & yarnT
        if len(mFromN):
          newYarnT |= mFromN
          newYarnF.add(n)
    else:
      for n in yarnF:
        mFromN = set(m for m in yarnT if r(n, m))
        if len(mFromN):
          newYarnT |= mFromN
          newYarnF.add(n)

  affectedF = len(newYarnF) != len(yarns[f])
  affectedT = len(newYarnT) != len(yarns[t])

  uptodate[e] = True
  for (oe, (of, orela, ot)) in enumerate(qedges):
    if oe == e:
      continue
    if (affectedF and f in {of, ot}) or (affectedT and t in {of, ot}):
      uptodate[oe] = False
  searchExe.yarns[f] = newYarnF
  searchExe.yarns[t] = newYarnT


def spinEdges(searchExe):
  qnodes = searchExe.qnodes
  qedges = searchExe.qedges
  yarns = searchExe.yarns
  uptodate = searchExe.uptodate

  estimateSpreads(searchExe)

  for e in range(len(qedges)):
    uptodate[e] = False
  it = 0
  while 1:
    if min(len(yarns[q]) for q in range(len(qnodes))) == 0:
      break
    # if reduce(
    #    lambda y,z: y and z,
    #    (uptodate[e] for e in range(len(qedges))),
    #    True,
    # ): break
    if all(uptodate[e] for e in range(len(qedges))):
      break
    e = _chooseEdge(searchExe)
    (f, rela, t) = qedges[e]
    _spinEdge(searchExe, e)
    it += 1
