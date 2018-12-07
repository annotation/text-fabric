from tf.applib.helpers import dm

FLAGS = (
    ('damage', '#'),
    ('remarkable', '!'),
    ('written', ('!(', ')')),
    ('uncertain', '?'),
)

OUTER_QUAD_TYPES = {'sign', 'quad'}

CLUSTER_BEGIN = {'[': ']', '<': '>', '(': ')'}
CLUSTER_END = {y: x for (x, y) in CLUSTER_BEGIN.items()}
CLUSTER_KIND = {'[': 'uncertain', '(': 'properName', '<': 'supplied'}
CLUSTER_BRACKETS = dict(
    (name, (bOpen, CLUSTER_BEGIN[bOpen]))
    for (bOpen, name) in CLUSTER_KIND.items()
)


class Atf(object):

  def __init__(self, api=None):
    if api:
      self.api = api

  def getSource(self, node, nodeType=None, lineNumbers=False):
    api = self.api
    F = api.F
    L = api.L
    sourceLines = []
    lineNumber = ''
    if lineNumbers:
      lineNo = F.srcLnNum.v(node)
      lineNumber = f'{lineNo:>5} ' if lineNo else ''
    sourceLine = F.srcLn.v(node)
    if sourceLine:
      sourceLines.append(f'{lineNumber}{sourceLine}')
    for child in L.d(node, nodeType):
      sourceLine = F.srcLn.v(child)
      lineNumber = ''
      if sourceLine:
        if lineNumbers:
          lineNumber = f'{F.srcLnNum.v(child):>5}: '
        sourceLines.append(f'{lineNumber}{sourceLine}')
    return sourceLines

  def atfFromSign(self, n, flags=False):
    F = self.api.F
    Fs = self.api.Fs
    if F.otype.v(n) != 'sign':
      return '«no sign»'

    grapheme = F.grapheme.v(n)
    if grapheme == '…':
      grapheme = '...'
    primeN = F.prime.v(n)
    prime = ("'" * primeN) if primeN else ''

    variantValue = F.variant.v(n)
    variant = f'~{variantValue}' if variantValue else ''

    modifierValue = F.modifier.v(n)
    modifier = f'@{modifierValue}' if modifierValue else ''
    modifierInnerValue = F.modifierInner.v(n)
    modifierInner = f'@{modifierInnerValue}' if modifierInnerValue else ''

    modifierFirst = F.modifierFirst.v(n)

    repeat = F.repeat.v(n)
    if repeat is None:
      varmod = (f'{modifier}{variant}' if modifierFirst else f'{variant}{modifier}')
      result = f'{grapheme}{prime}{varmod}'
    else:
      if repeat == -1:
        repeat = 'N'
      varmod = (f'{modifierInner}{variant}' if modifierFirst else f'{variant}{modifierInner}')
      result = f'{repeat}({grapheme}{prime}{varmod}){modifier}'

    if flags:
      for (flag, char) in FLAGS:
        value = Fs(flag).v(n)
        if value:
          if type(char) is tuple:
            result += f'{char[0]}{value}{char[1]}'
          else:
            result += char

    return result

  def atfFromQuad(self, n, flags=False, outer=True):
    api = self.api
    E = api.E
    F = api.F
    Fs = api.Fs
    if F.otype.v(n) != 'quad':
      return '«no quad»'

    children = E.sub.f(n)
    if not children or len(children) < 2:
      return f'«quad with less than two sub-quads»'
    result = ''
    for child in children:
      nextChildren = E.op.f(child)
      if nextChildren:
        op = nextChildren[0][1]
      else:
        op = ''
      childType = F.otype.v(child)

      thisResult = (
          self.atfFromQuad(child, flags=flags, outer=False)
          if childType == 'quad' else self.atfFromSign(child, flags=flags)
      )
      result += f'{thisResult}{op}'

    variant = F.variantOuter.v(n)
    variantStr = f'~{variant}' if variant else ''

    flagStr = ''
    if flags:
      for (flag, char) in FLAGS:
        value = Fs(flag).v(n)
        if value:
          if type(char) is tuple:
            flagStr += f'{char[0]}{value}{char[1]}'
          else:
            flagStr += char

    if variant:
      if flagStr:
        if outer:
          result = f'|({result}){variantStr}|{flagStr}'
        else:
          result = f'(({result}){variantStr}){flagStr}'
      else:
        if outer:
          result = f'|({result}){variantStr}|'
        else:
          result = f'({result}){variantStr}'
    else:
      if flagStr:
        if outer:
          result = f'|{result}|{flagStr}'
        else:
          result = f'({result}){flagStr}'
      else:
        if outer:
          result = f'|{result}|'
        else:
          result = f'({result})'

    return result

  def atfFromOuterQuad(self, n, flags=False):
    api = self.api
    F = api.F
    nodeType = F.otype.v(n)
    if nodeType == 'sign':
      return self.atfFromSign(n, flags=flags)
    elif nodeType == 'quad':
      return self.atfFromQuad(n, flags=flags, outer=True)
    else:
      return '«no outer quad»'

  def atfFromCluster(self, n, seen=None):
    api = self.api
    F = api.F
    E = api.E
    if F.otype.v(n) != 'cluster':
      return '«no cluster»'

    typ = F.type.v(n)
    (bOpen, bClose) = CLUSTER_BRACKETS[typ]
    if bClose == ')':
      bClose = ')a'
    children = api.sortNodes(E.sub.f(n))

    if seen is None:
      seen = set()
    result = []
    for child in children:
      if child in seen:
        continue
      childType = F.otype.v(child)

      thisResult = (
          self.atfFromCluster(child, seen=seen)
          if childType == 'cluster' else self.atfFromQuad(child, flags=True) if childType == 'quad'
          else self.atfFromSign(child, flags=True) if childType == 'sign' else None
      )
      seen.add(child)
      if thisResult is None:
        dm(f'TF: child of cluster has type {childType}:' ' should not happen')
      result.append(thisResult)
    return f'{bOpen}{" ".join(result)}{bClose}'

  def getOuterQuads(self, n):
    api = self.api
    F = api.F
    E = api.E
    L = api.L
    return [
        quad for quad in L.d(n) if (
            F.otype.v(quad) in OUTER_QUAD_TYPES
            and all(F.otype.v(parent) != 'quad' for parent in E.sub.t(quad))
        )
    ]

  def lineFromNode(app, n):
    api = app.api
    F = api.F
    L = api.L
    caseOrLineUp = [m for m in L.u(n) if F.terminal.v(m)]
    return caseOrLineUp[0] if caseOrLineUp else None

  def nodeFromCase(app, passage):
    api = app.api
    F = api.F
    L = api.L
    T = api.T
    section = passage[0:2]
    caseNum = passage[2].replace('.', '')
    column = T.nodeFromSection(section)
    if column is None:
      return None
    casesOrLines = [c for c in L.d(column) if F.terminal.v(c) and F.number.v(c) == caseNum]
    if not casesOrLines:
      return None
    return casesOrLines[0]

  def caseFromNode(app, n):
    api = app.api
    F = api.F
    T = api.T
    L = api.L
    section = T.sectionFromNode(n)
    if section is None:
      return None
    nodeType = F.otype.v(n)
    if nodeType in {'sign', 'quad', 'cluster', 'case'}:
      if nodeType == 'case':
        caseNumber = F.number.v(n)
      else:
        caseOrLine = [m for m in L.u(n) if F.terminal.v(m)][0]
        caseNumber = F.number.v(caseOrLine)
      return (section[0], section[1], caseNumber)
    else:
      return section

  def casesByLevel(app, lev, terminal=True):
    api = app.api
    F = api.F
    lkey = 'line' if lev == 0 else 'case'
    if lev == 0:
      return (tuple(c for c in F.otype.s(lkey) if F.terminal.v(c)) if terminal else F.otype.s(lkey))
    return (
        tuple(c for c in F.otype.s(lkey) if F.depth.v(c) == lev and F.terminal.v(c))
        if terminal else tuple(c for c in F.otype.s(lkey) if F.depth.v(c) == lev)
    )
