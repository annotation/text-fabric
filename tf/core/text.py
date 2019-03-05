from .data import WARP
from .helpers import itemize, compileFormats

DEFAULT_FORMAT = 'text-orig-full'
DEFAULT_FORMAT_TYPE = '{}-default'


class Text(object):

  def __init__(self, api):
    self.api = api
    self.languages = {}
    self.nameFromNode = {}
    self.nodeFromName = {}
    config = api.TF.features[WARP[2]].metaData if WARP[2] in api.TF.features else {}
    self.sectionTypes = itemize(config.get('sectionTypes', ''), ',')
    sectionFeats = itemize(config.get('sectionFeatures', ''), ',')
    self.sectionFeatures = []
    self.sectionFeatureTypes = []
    self.config = config
    self.defaultFormat = DEFAULT_FORMAT
    otype = api.F.otype.v

    good = True
    if len(sectionFeats) != 0 and len(self.sectionTypes) != 0:
      for (fName,
           fObj) in sorted(f for f in api.TF.features.items()
                           if f[0] == sectionFeats[0] or f[0].startswith(f'{sectionFeats[0]}@')):
        if not fObj.load(silent=True):
          good = False
          continue
        meta = fObj.metaData
        code = meta.get('languageCode', '')
        self.languages[code] = dict(((k, meta.get(k, 'default'))
                                     for k in ('language', 'languageEnglish')))
        self.nameFromNode[code] = fObj.data
        self.nodeFromName[code] = dict(
            ((otype(node), name), node)
            for (node, name) in fObj.data.items()
        )
      for fName in (sectionFeats):
        if not api.TF.features[fName].load(silent=True):
          good = False
          continue
        sectionFeature = api.TF.features[fName]
        self.sectionFeatures.append(sectionFeature.data)
        self.sectionFeatureTypes.append(sectionFeature.dataType)

      sec0 = self.sectionTypes[0]
      setattr(self, f'{sec0}Name', self._sec0Name)
      setattr(self, f'{sec0}Node', self._sec0Node)

    self._xformats = compileFormats(api.TF._cformats, api.TF.features)
    self.formats = set(self._xformats.keys())
    self.good = good

  def _sec0Name(self, n, lang='en'):
    sec0T = self.sectionTypes[0]
    otype = self.api.F.otype.v
    refNode = n if otype(n) == sec0T else self.api.L.u(n, sec0T)[0]
    lookup = (
        self.nameFromNode['' if lang not in self.languages else lang]
    )
    return lookup.get(refNode, f'not a {sec0T} node')

  def _sec0Node(self, name, lang='en'):
    sec0T = self.sectionTypes[0]
    return self.nodeFromName['' if lang not in self.languages else lang].get((sec0T, name), None)

  def sectionTuple(self, n, lastSlot=False, fillup=False):
    sTypes = self.sectionTypes
    lsTypes = len(sTypes)
    if lsTypes == 0:
      return ()
    F = self.api.F
    E = self.api.E
    L = self.api.L
    slotType = F.otype.slotType
    maxSlot = F.otype.maxSlot
    eoslots = E.oslots.data
    nType = F.otype.v(n)

    if nType == slotType:
      r = n
    else:
      slots = eoslots[n - maxSlot - 1]
      r = slots[-1 if lastSlot else 0]

    if nType == sTypes[0]:
      if fillup:
        r1 = L.u(r, otype=sTypes[1])
        r1 = r1[0] if r1 else ''
        if lsTypes > 2:
          r2 = L.u(r, otype=sTypes[2])
          r2 = r2[0] if r2 else ''
          return (n, r1, r2)
        return (n, r1)
      return (n,)

    r0s = L.u(r, sTypes[0])
    r0 = r0s[0] if r0s else None

    if nType == sTypes[1]:
      if fillup:
        if lsTypes > 2:
          r2 = L.u(r, otype=sTypes[2])
          r2 = r2[0] if r2 else ''
          return (r0, n, r2)
      return (r0, n)

    r1s = L.u(r, sTypes[1])
    r1 = r1s[0] if r1s else ''

    if lsTypes < 3:
      return (r0, r1)

    if nType == sTypes[2]:
      return (r0, r1, n)

    r2s = L.u(r, sTypes[2])
    r2 = r2s[0] if r2s else ''

    return (r0, r1, r2)

  def sectionFromNode(self, n, lastSlot=False, lang='en', fillup=False):
    sTuple = self.sectionTuple(n, lastSlot=lastSlot, fillup=fillup)
    if len(sTuple) == 0:
      return ()

    sFs = self.sectionFeatures

    return tuple(
        '' if n is None else
        self._sec0Name(n, lang=lang)
        if i == 0 else
        sFs[i].get(n, None)
        for (i, n) in enumerate(sTuple)
    )

  def nodeFromSection(self, section, lang='en'):
    sTypes = self.sectionTypes
    if len(sTypes) == 0:
      return None
    (sec1, sec2) = self.api.C.sections.data
    sec0node = self._sec0Node(section[0], lang=lang)
    if len(section) == 1:
      return sec0node
    elif len(section) == 2:
      return sec1.get(sec0node, {}).get(section[1], None)
    else:
      return sec2.get(sec0node, {}).get(section[1], {}).get(section[2], None)

  def text(self, nodes, fmt=None, descend=False, func=None):
    E = self.api.E
    F = self.api.F
    slotType = F.otype.slotType
    maxSlot = F.otype.maxSlot
    eoslots = E.oslots.data

    if type(nodes) is int:
      nType = F.otype.v(nodes)
      if fmt is None:
        fmt = DEFAULT_FORMAT_TYPE.format(nType)
      repf = func or self._xformats.get(fmt, None)
      if repf is None or descend:
        if repf is None:
          fmt = DEFAULT_FORMAT
        nodes = [nodes] if nType == slotType else eoslots[nodes - maxSlot - 1]
      else:
        return repf(nodes)
    else:
      if fmt is None:
        fmt = DEFAULT_FORMAT
    repf = func or self._xformats.get(fmt, None)
    if repf is None:
      return ' '.join(f'{F.otype.v(n)}_{n}' for n in nodes)
    return ''.join(repf(n) for n in nodes)
