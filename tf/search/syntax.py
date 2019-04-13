import re

# SYNTACTIC ANALYSIS OF SEARCH TEMPLATE ###

QWHERE = '/where/'
QHAVE = '/have/'
QWITHOUT = '/without/'
QWITH = '/with/'
QOR = '/or/'
QEND = '/-/'

QINIT = {QWHERE, QWITHOUT, QWITH}
QCONT = {QHAVE, QOR}
QTERM = {QEND}

PARENT_REF = '..'

ESCAPES = (
    '\\\\',
    '\\ ',
    '\\t',
    '\\n',
    '\\|',
    '\\=',
)
VAL_ESCAPES = {
    '\\|',
    '\\=',
}

opPat = r'(?:[#&|\[\]<>:=-]+\S*)'

atomOpPat = r'(\s*)({op})\s+([^ \t=#<>~*]+)(?:(?:\s*\Z)|(?:\s+(.*)))$'.format(op=opPat)
atomPat = r'(\s*)([^ \t=#<>~*]+)(?:(?:\s*\Z)|(?:\s+(.*)))$'
compPat = r'^([a-zA-Z0-9-@_]+)([<>])(.*)$'
identPat = r'^([a-zA-Z0-9-@_]+)([=#])(.+)$'
indentLinePat = r'^(\s*)(.*)'
kPat = r'^([^0-9]*)([0-9]+)([^0-9]*)$'
namePat = r'[A-Za-z0-9_.-]+'
namesPat = r'^\s*(?:{op}\s+)?([^ \t:=#<>~*]+):'
nonePat = r'^([a-zA-Z0-9-@_]+)(#?)\s*$'
truePat = r'^([a-zA-Z0-9-@_]+)[*]\s*$'
numPat = r'^-?[0-9]+$'
opLinePat = r'^(\s*)({op})\s*$'.format(op=opPat)
opStripPat = r'^\s*{op}\s+(.*)$'.format(op=opPat)
quPat = f'(?:{QWHERE}|{QHAVE}|{QWITHOUT}|{QWITH}|{QOR}|{QEND})'
quLinePat = r'^(\s*)({qu})\s*$'.format(qu=quPat)
relPat = r'^(\s*)({nm})\s+({op})\s+({nm})\s*$'.format(nm=namePat, op=opPat)
rePat = r'^([a-zA-Z0-9-@_]+)~(.*)$'

atomOpRe = re.compile(atomOpPat)
atomRe = re.compile(atomPat)
compRe = re.compile(compPat)
identRe = re.compile(identPat)
indentLineRe = re.compile(indentLinePat)
kRe = re.compile(kPat)
nameRe = re.compile(f'^{namePat}$')
namesRe = re.compile(namesPat)
numRe = re.compile(numPat)
noneRe = re.compile(nonePat)
trueRe = re.compile(truePat)
opLineRe = re.compile(opLinePat)
opStripRe = re.compile(opStripPat)
quLineRe = re.compile(quLinePat)
relRe = re.compile(relPat)
reRe = re.compile(rePat)
whiteRe = re.compile(r'^\s*$')

reTp = type(reRe)


def syntax(searchExe):
  error = searchExe.api.error
  msgCache = searchExe.msgCache
  searchExe.good = True
  searchExe.badSyntax = []
  searchExe.searchLines = searchExe.searchTemplate.split('\n')
  offset = searchExe.offset

  _tokenize(searchExe)

  if not searchExe.good:
    searchExe.showOuterTemplate(msgCache)
    for (i, line) in enumerate(searchExe.searchLines):
      error(f'{i + offset:>2} {line}', tm=False, cache=msgCache)
    for (ln, eline) in searchExe.badSyntax:
      txt = eline if ln is None else f'line {ln + offset}: {eline}'
      error(txt, tm=False, cache=msgCache)


def _tokenize(searchExe):

  def readFeatures(x, i):
    features = {}
    featureString = x.replace('\\ ', chr(1)) if x is not None else ''
    featureList = featureString.split()
    good = True
    for featStr in featureList:
      if not parseFeatureVals(searchExe, featStr, features, i):
        good = False
    return features if good else None

  searchLines = searchExe.searchLines
  tokens = []
  allGood = True

  # the template may contain nested quantifiers
  # However, we detect only the outer level of quantifiers.
  # Everything contained in a quantifiers is collected in
  # a new search template, verbatim, without interpretion,
  # because it will be fed to search() on another instance.
  # We only strip the quantified lines of the outermost quantifiers.

  # We can maintain the current quantifier, None if there is none.
  # We also remember the current indentation of the current quantifier
  # We collect the templates within the quantifier in a list of strings.
  # We add all the material into a quantifier token of the shape
  #
  # Because indentation is not indicative of quantifier nesting
  # we need to maintain a stack of inner quantifiers,
  # just to be able to determine wich quantifier words
  # belong to the outerlevel quantifiers.

  curQu = []
  curQuTemplates = None

  for (i, line) in enumerate(searchLines):
    if line.startswith('%') or whiteRe.match(line):
      continue
    opFeatures = {}

    # first check whether we have a line with a quantifier
    # and what the indent on the line is

    match = quLineRe.match(line)
    if match:
      (indent, lineQuKind) = match.groups()
    else:
      lineQuKind = None
      match = indentLineRe.match(line)
      indent = match.group(1)

    lineIndent = len(indent)

    # QUANTIFIER FILTERING
    #
    # now check whether we are in a quantifier or not
    # and determine whether a quantifier starts or ends here

    # we have the following possible situations:
    #
    # UUO no outer              - no q-keyword
    #
    # UBO no outer              - q-keyword
    #     * ES no start keyword
    #     * ET no preceding token
    #     * EA no preceding atom
    #     * EI preceding atom not the same indentation
    #
    # PBI outer                 - q-keyword init
    #
    # PPO outer                 - no q-keyword
    #
    # PPI inner                 - no q-keyword
    #
    # PCO outer                 - q-keyword continue
    #     * EP wrong precursor
    #     * EK preceding keyword not the same indentation
    #
    # PCI inner                 - q-keyword continue
    #     * EP wrong precursor
    #     * EK preceding keyword not the same indentation
    #
    # PEO outer                 - q-keyword end
    #     * EP wrong precursor
    #     * EK preceding keyword not the same indentation
    #
    # PEI inner                 - q-keyword end
    #     * EP wrong precursor
    #     * EK preceding keyword not the same indentation
    #
    # at the end we may have a non-empty quantifier stack:
    #     * generate an unterminated quantifier error for each member
    #       of the stack

    # first we determine what is the case and we store it in booleans

    curQuLine = None
    curQuKind = None
    curQuIndent = None
    curQuDepth = len(curQu)
    if curQuDepth:
      (curQuLine, curQuKind, curQuIndent) = curQu[-1]

    UUO = not curQuDepth and not lineQuKind
    UBO = not curQuDepth and lineQuKind
    PBI = curQuDepth and lineQuKind in QINIT
    PPO = curQuDepth == 1 and not lineQuKind
    PPI = curQuDepth > 1 and not lineQuKind
    PCO = curQuDepth == 1 and lineQuKind in QCONT
    PCI = curQuDepth > 1 and lineQuKind in QCONT
    PEO = curQuDepth == 1 and lineQuKind in QTERM
    PEI = curQuDepth > 1 and lineQuKind in QTERM

    (ES, ET, EA, EI, EP, EK) = (False, ) * 6

    if UBO:
      ES = lineQuKind not in QINIT
      ET = len(tokens) == 0
      EA = (len(tokens) and tokens[-1]['kind'] != 'atom' and 'otype' not in tokens[-1])
      EI = (len(tokens) and tokens[-1]['indent'] != lineIndent)

    if PCO or PCI:
      EP = ((lineQuKind == QHAVE and curQuKind != QWHERE)
            or (lineQuKind == QOR and curQuKind not in {QWITH, QOR}))
      EK = curQu[-1][2] != lineIndent

    if PEO or PEI:
      EP = curQuKind in {QWHERE}
      EK = curQu[-1][2] != lineIndent

    # QUANTIFIER HANDLING
    #
    # Based on what is the case, we take actions.
    # * we swallow quantified templates
    # * we handle quantifier lines
    # * we let all other lines pass through

    good = True

    for x in [True]:
      if UUO:
        # no quantifier business
        continue
      if UBO:
        # start new quantifier from nothing
        if ES:
          searchExe.badSyntax.append((i, f'Quantifier: Can not start with "{lineQuKind}:"'))
          good = False
        if ET:
          searchExe.badSyntax.append((i, f'Quantifier: No preceding tokens'))
          good = False
        if EA or EI:
          searchExe.badSyntax.append(
              (i, f'Quantifier: Does not immediately follow an atom at the same level')
          )
          good = False
        prevAtom = tokens[-1]
        curQu.append((i, lineQuKind, lineIndent))
        curQuTemplates = [[]]
        quantifiers = prevAtom.setdefault('quantifiers', [])
        quantifiers.append((lineQuKind, curQuTemplates, i))
        continue
      if PBI:
        # start inner quantifier
        # lines are passed with stripped indentation
        # based on the outermost quantifier level
        outerIndent = curQu[0][2]
        strippedLine = line[outerIndent:]
        curQuTemplates[-1].append(strippedLine)
        curQu.append((i, lineQuKind, lineIndent))
      if PPO:
        # inside an outer quantifier
        # lines are passed with stripped indentation
        strippedLine = line[curQuIndent:]
        curQuTemplates[-1].append(strippedLine)
        continue
      if PPI:
        # inside an inner quantifier
        # lines are passed with stripped indentation
        # based on the outermost quantifier level
        outerIndent = curQu[0][2]
        strippedLine = line[outerIndent:]
        curQuTemplates[-1].append(strippedLine)
      if PCO or PCI:
        if EP:
          searchExe.badSyntax.append(
              (i, f'Quantifier: "{lineQuKind}" can not follow "{curQuKind}" on line {curQuLine}')
          )
          good = False
        if EK:
          searchExe.badSyntax.append((
              i, (
                  f'Quantifier "{lineQuKind}"'
                  f' has not same indentation as "{curQuKind}" on line {curQuLine}'
              )
          ))
          good = False
        if PCO:
          curQuTemplates.append([])
        else:
          outerIndent = curQu[0][2]
          strippedLine = line[outerIndent:]
          curQuTemplates[-1].append(strippedLine)
        curQu[-1] = (i, lineQuKind, lineIndent)
        continue
      if PEO or PEI:
        if EP:
          searchExe.badSyntax.append((
              i, (
                  f'Quantifier: "{lineQuKind}"'
                  f' : premature end of "{curQuKind}" on line {curQuLine}'
              )
          ))
          good = False
        if EK:
          searchExe.badSyntax.append((
              i, (
                  f'Quantifier "{lineQuKind}"'
                  f' has not same indentation as "{curQuKind}" on line {curQuLine}'
              )
          ))
          good = False
        if PEO:
          curQuTemplates = None
        else:
          outerIndent = curQu[0][2]
          strippedLine = line[outerIndent:]
          curQuTemplates[-1].append(strippedLine)
        curQu.pop()
        continue

    if not good:
      allGood = False

    if UUO:
      # go on with normal template tokenization
      pass
    else:
      # quantifiers stuff has been dealt with
      continue

    # QUANTIFIER FREE HANDLING

    good = False

    for x in [True]:
      (kind, data) = parseLine(line)

      if kind == 'op':
        (indent, op) = data
        if not parseFeatureVals(searchExe, op, opFeatures, i, asEdge=True):
          good = False
        else:
          if opFeatures:
            op = (op, opFeatures)
          tokens.append(dict(
              ln=i,
              kind='atom',
              indent=len(indent),
              op=op,
          ))
          good = True
        break

      if kind == 'rel':
        (indent, f, op, t) = data
        if not parseFeatureVals(searchExe, op, opFeatures, i, asEdge=True):
          good = False
        else:
          if opFeatures:
            op = (op, opFeatures)
          tokens.append(dict(
              ln=i,
              kind='rel',
              f=f,
              op=op,
              t=t,
          ))
          good = True
        break

      if kind == 'atom':
        (indent, op, name, otype, features) = data
        good = True
        if name != '':
          mt = nameRe.match(name)
          if not mt:
            searchExe.badSyntax.append((i, f'Illegal name: "{name}"'))
            good = False
        features = readFeatures(features, i)
        if features is None:
          good = False
        else:
          if op is not None:
            if not parseFeatureVals(searchExe, op, opFeatures, i, asEdge=True):
              good = False
          if good:
            if opFeatures:
              op = (op, opFeatures)
            tokens.append(
                dict(
                    ln=i,
                    kind='atom',
                    indent=len(indent),
                    op=op,
                    name=name,
                    otype=otype,
                    src=line.lstrip(),
                    features=features,
                )
            )
        break

      if kind == 'feat':
        features = data[0]
        features = readFeatures(features, i)
        if features is None:
          good = False
        else:
          tokens.append(dict(
              ln=i,
              kind='feat',
              features=features,
          ))
          good = True
        break

      good = False
      searchExe.badSyntax.append((i, f'Unrecognized line: {line}'))

    if not good:
      allGood = False

  if curQu:
    for (curQuLine, curQuKind, curQuIndent) in curQu:
      searchExe.badSyntax.append((curQuLine, f'Quantifier: Unterminated "{curQuKind}"'))
    good = False
    allGood = False
  if allGood:
    searchExe.tokens = tokens
  else:
    searchExe.good = False


def parseLine(line):
  for x in [True]:
    escLine = _esc(line)

    match = opLineRe.match(escLine)
    if match:
      (indent, op) = match.groups()
      kind = 'op'
      data = (indent, op)
      break

    match = relRe.match(escLine)
    if match:
      (indent, f, op, t) = match.groups()
      kind = 'rel'
      data = (indent, f, op, t)
      break

    matchOp = atomOpRe.match(escLine)
    if matchOp:
      (indent, op, atom, features) = matchOp.groups()
    else:
      match = atomRe.match(escLine)
      if match:
        op = None
        (indent, atom, features) = match.groups()
    if matchOp or match:
      atomComps = atom.split(':', 1)
      if len(atomComps) == 1:
        name = ''
        otype = atomComps[0]
      else:
        name = atomComps[0]
        otype = atomComps[1]
      kind = 'atom'
      if features is None:
        features = ''
      data = (indent, op, name, otype, features)
      break

    kind = 'feat'
    data = (escLine, )

  return (kind, data)


def parseFeatureVals(searchExe, featStr, features, i, asEdge=False):
  if asEdge:
    if not (
        (featStr[0] == '-' and featStr[-1] == '>') or
        (featStr[0] == '<' and featStr[-1] == '-') or
        (featStr[0] == '<' and featStr[-1] == '>')
    ):
      return True
    feat = featStr[1:-1]
  else:
    feat = featStr.replace(chr(1), ' ')
  good = True
  for x in [True]:
    match = trueRe.match(feat)
    if match:
      (featN, ) = match.groups()
      featName = _unesc(featN)
      featVals = (None, True)
      break
    match = noneRe.match(feat)
    if match:
      (featN, unequal) = match.groups()
      featName = _unesc(featN)
      featVals = None if unequal else True
      break
    match = identRe.match(feat)
    if match:
      (featN, comp, featValStr) = match.groups()
      featName = _unesc(featN)
      featValSet = frozenset(_unesc(featVal) for featVal in featValStr.split('|'))
      featVals = (comp == '=', featValSet)
      break
    match = compRe.match(feat)
    if match:
      (featN, comp, limit) = match.groups()
      featName = _unesc(featN)
      if not numRe.match(limit):
        searchExe.badSyntax.append((i, f'Limit is non numeric "{limit}"'))
        good = False
        featVals = None
      else:
        featVals = _makeLimit(int(limit), comp == '>')
      break
    match = reRe.match(feat)
    if match:
      (featN, valRe) = match.groups()
      featName = _unesc(featN)
      valRe = _unesc(valRe, inRe=True)
      try:
        featVals = re.compile(valRe)
      except Exception() as err:
        searchExe.badSyntax.append((i, f'Wrong regular expression "{valRe}": "{err}"'))
        good = False
        featVals = None
      break
    searchExe.badSyntax.append((i, f'Unrecognized feature condition "{feat}"'))
    good = False
    featVals = None
  if good:
    features[featName] = featVals
  return good


def _genLine(kind, data):
  result = None

  for x in [True]:
    if kind == 'op':
      (indent, op) = data
      result = f'{indent}{_unesc(op)}'
      break

    if kind == 'rel':
      (indent, f, op, t) = data
      result = f'{indent}{f} {_unesc(op)} {t}'
      break

    if kind == 'atom':
      (indent, op, name, otype, features) = data
      opRep = '' if op is None else f'{_unesc(op)} '
      nameRep = '' if name == '' else f'{name}:'
      featRep = _unesc(features)
      if featRep:
        featRep = f' {featRep}'
      result = f'{indent}{opRep}{nameRep}{otype}{featRep}'
      break

    features = data[0]
    result = _unesc(features)

  return result


def cleanParent(atom, parentName):
  (kind, data) = parseLine(atom)
  (indent, op, name, otype, features) = data
  if name == '':
    name = parentName
  return _genLine(kind, (indent, None, name, otype, features))


def deContext(quantifier, parentName):
  (quKind, quTemplates, ln) = quantifier

  # choose a name for the parent
  # either the given name
  if not parentName:
    # or make a new name
    # collect all used names
    # to avoid choosing a name that is already used
    usedNames = set()
    for template in quTemplates:
      for line in template:
        for name in namesRe.findall(line):
          usedNames.add(name)
    parentName = 'parent'
    while parentName in usedNames:
      parentName += 'x'

  newQuTemplates = []
  newQuantifier = (quKind, newQuTemplates, parentName, ln)

  # replace .. (PARENT_REF) by parentName
  # wherever it is applicable
  for template in quTemplates:
    newLines = []
    for line in template:
      (kind, data) = parseLine(line)
      newLine = line
      if kind == 'rel':
        (indent, f, op, t) = data
        if f == PARENT_REF or t == PARENT_REF:
          newF = parentName if f == PARENT_REF else f
          newT = parentName if t == PARENT_REF else t
          newData = (indent, newF, op, newT)
          newLine = _genLine(kind, newData)
      elif kind == 'atom':
        (indent, op, name, otype, features) = data
        if name == '' and otype == PARENT_REF:
          newData = (indent, op, name, parentName, features)
          newLine = _genLine(kind, newData)
      newLines.append(newLine)
    templateStr = '\n'.join(newLines)
    newQuTemplates.append(templateStr)
  return newQuantifier


def _makeLimit(n, isLower):
  if isLower:
    return lambda x: x is not None and x > n
  return lambda x: x is not None and x < n


def _esc(x):
  for (i, c) in enumerate(ESCAPES):
    x = x.replace(c, chr(i))
  return x


def _unesc(x, inRe=False):
  for (i, c) in enumerate(ESCAPES):
    if inRe and c in VAL_ESCAPES:
      x = x.replace(chr(i), f'\\{c[1]}')
    else:
      x = x.replace(chr(i), c[1])
  return x
