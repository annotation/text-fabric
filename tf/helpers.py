import re

LETTER = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
VALID = set('_0123456789') | LETTER


def cleanName(name):
  clean = ''.join(c if c in VALID else '_' for c in name)
  if clean == '' or not clean[0] in LETTER:
    clean = 'x' + clean
  return clean


def isClean(name):
  if name is None or len(name) == 0 or name[0] not in LETTER:
    return False
  return all(c in VALID for c in name[1:])


def expandDir(dirName, paths):
  if dirName.startswith('~'):
    dirName = dirName.replace('~', paths['home'], 1)
  elif dirName.startswith('..'):
    dirName = dirName.replace('..', paths['up'], 1)
  elif dirName.startswith('.'):
    dirName = dirName.replace('.', paths['cur'], 1)
  return dirName


def setFromSpec(spec):
  covered = set()
  for r_str in spec.split(','):
    bounds = r_str.split('-')
    if len(bounds) == 1:
      covered.add(int(r_str))
    else:
      b = int(bounds[0])
      e = int(bounds[1])
      if e < b:
        (b, e) = (e, b)
      for n in range(b, e + 1):
        covered.add(n)
  return covered


def rangesFromSet(nodeSet):
  ranges = []
  curstart = None
  curend = None
  for n in sorted(nodeSet):
    if curstart is None:
      curstart = n
      curend = n
    elif n == curend + 1:
      curend = n
    else:
      ranges.append((curstart, curend))
      curstart = n
      curend = n
  if curstart is not None:
    ranges.append((curstart, curend))
  return ranges


def rangesFromList(nodeList):  # the list must be sorted
  ranges = []
  curstart = None
  curend = None
  for n in nodeList:
    if curstart is None:
      curstart = n
      curend = n
    elif n == curend + 1:
      curend = n
    else:
      ranges.append((curstart, curend))
      curstart = n
      curend = n
  if curstart is not None:
    ranges.append((curstart, curend))
  return ranges


def specFromRanges(ranges):  # ranges must be normalized
  return ','.join('{}'.format(r[0]) if r[0] == r[1] else '{}-{}'.format(*r) for r in ranges)


def valueFromTf(tf):
  return '\\'.join(x.replace('\\t', '\t').replace('\\n', '\n') for x in tf.split('\\\\'))


def tfFromValue(val):
  return str(val) if type(val) is int else val.replace('\\',
                                                       '\\\\').replace('\t',
                                                                       '\\t').replace('\n', '\\n')


def makeInverse(data):
  inverse = {}
  for n in data:
    for m in data[n]:
      inverse.setdefault(m, set()).add(n)
  return inverse


def makeInverseVal(data):
  inverse = {}
  for n in data:
    for (m, val) in data[n].items():
      inverse.setdefault(m, {})[n] = val
  return inverse


def nbytes(by):
  units = ['B', 'KB', 'MB', 'GB', 'TB']
  for i in range(len(units)):
    if by < 1024 or i == len(units) - 1:
      fmt = '{:>5}{}' if i == 0 else '{:>5.1f}{}'
      return fmt.format(by, units[i])
    by /= 1024


def collectFormats(config):
  varPattern = re.compile(r'\{([^}]+)\}')
  featureSet = set()

  def collectFormat(tpl):
    features = []

    def varReplace(match):
      varText = match.group(1)
      fts = tuple(varText.split('/'))
      features.append(fts)
      for ft in fts:
        featureSet.add(ft)
      return '{}'

    rtpl = varPattern.sub(varReplace, tpl)
    return (rtpl, tuple(features))

  formats = {}
  for (fmt, tpl) in sorted(config.items()):
    if fmt.startswith('fmt:'):
      formats[fmt[4:]] = collectFormat(tpl)
  return (formats, sorted(featureSet))


def compileFormats(cformats, features):
  xformats = {}
  for (fmt, (rtpl, feats)) in sorted(cformats.items()):
    tpl = rtpl.replace('\\n', '\n').replace('\\t', '\t')
    xformats[fmt] = compileFormat(tpl, feats, features)
  return xformats


def compileFormat(rtpl, feats, features):
  replaceFuncs = []
  for feat in feats:
    replaceFuncs.append(makeFunc(feat, features))

  def g(n):
    values = tuple(replaceFunc(n) for replaceFunc in replaceFuncs)
    return rtpl.format(*values)

  return g


def makeFunc(feat, features):
  if len(feat) == 1:
    ft = feat[0]
    f = features[ft].data
    return (lambda n: f.get(n, ''))
  elif len(feat) == 2:
    (ft1, ft2) = feat
    f1 = features[ft1].data
    f2 = features[ft2].data
    return (lambda n: (f1.get(n, f2.get(n, ''))))


def itemize(string, sep=None):
  if not string:
    return []
  if not sep:
    return string.strip().split()
  return string.strip().split(sep)


def project(iterableOfTuples, maxDimension):
  if maxDimension == 1:
    return {r[0] for r in iterableOfTuples}
  return {r[0:maxDimension] for r in iterableOfTuples}
