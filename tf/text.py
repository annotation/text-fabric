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
    self.config = config
    self.defaultFormat = DEFAULT_FORMAT

    good = True
    if len(sectionFeats) != 0 and len(self.sectionTypes) != 0:
      for (fName, fObj) in sorted(
          f for f in api.TF.features.items()
          if f[0] == sectionFeats[0] or f[0].startswith('{}@'.format(sectionFeats[0]))
      ):
        if not fObj.load(silent=True):
          good = False
          continue
        meta = fObj.metaData
        code = meta.get('languageCode', '')
        self.languages[code] = dict(((k, meta.get(k, 'default'))
                                     for k in ('language', 'languageEnglish')))
        self.nameFromNode[code] = fObj.data
        self.nodeFromName[code] = dict(((name, node) for (node, name) in fObj.data.items()))
      for fName in (sectionFeats):
        if not api.TF.features[fName].load(silent=True):
          good = False
          continue
        self.sectionFeatures.append(api.TF.features[fName].data)

      sec0 = self.sectionTypes[0]
      setattr(self, '{}Name'.format(sec0), self._sec0Name)
      setattr(self, '{}Node'.format(sec0), self._sec0Node)

    self._xformats = compileFormats(api.TF._cformats, api.TF.features)
    self.formats = set(self._xformats.keys())
    self.good = good

  def _sec0Name(self, n, lang='en'):
    sec0T = self.sectionTypes[0]
    return self.nameFromNode['' if lang not in self.languages else lang].get(
        n if self.api.F.otype.v(n) == sec0T else self.api.L.u(n, sec0T)[0],
        'not a {} node'.format(sec0T),
    )

  def _sec0Node(self, name, lang='en'):
    return self.nodeFromName['' if lang not in self.languages else lang].get(name, None)

  def sectionFromNode(self, n, lastSlot=False, lang='en'):
    sTypes = self.sectionTypes
    if len(sTypes) == 0:
      return ()
    sFs = self.sectionFeatures
    F = self.api.F
    L = self.api.L
    slotType = F.otype.slotType
    nType = F.otype.v(n)
    r = L.d(n, slotType)[-1] if lastSlot and nType != slotType else L.d(
        n, slotType
    )[0] if nType != slotType else n
    n0s = L.u(r, sTypes[0])
    n0 = n0s[0] if n0s else None
    n1s = L.u(r, sTypes[1])
    n1 = n1s[0] if n1s else None
    n2s = L.u(r, sTypes[2])
    n2 = n2s[0] if n2s else None
    return (
        self._sec0Name(n0, lang=lang),
        sFs[1].get(n1, None),
        sFs[2].get(n2, None),
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

  def text(self, nodes, fmt=None, descend=False):
    F = self.api.F
    L = self.api.L
    slotType = F.otype.slotType
    if type(nodes) is int:
      nType = F.otype.v(nodes)
      if fmt is None:
        fmt = DEFAULT_FORMAT_TYPE.format(nType)
      repf = self._xformats.get(fmt, None)
      if repf is None or descend:
        if repf is None:
          fmt = DEFAULT_FORMAT
        nodes = [nodes] if nType == slotType else L.d(nodes, otype=slotType)
      else:
        return repf(nodes)
    else:
      if fmt is None:
        fmt = DEFAULT_FORMAT
    repf = self._xformats.get(fmt, None)
    if repf is None:
      return ' '.join(f'{F.otype.v(n)}_{n}' for n in nodes)
    return ''.join(repf(n) for n in nodes)

  '''
    else:
      if fmt is None:
        fmt = DEFAULT_FORMAT
      repf = self._xformats.get(fmt, None)
      if repf is None:
        return ' '.join(str(s) for s in slots)
      return ''.join(repf(s) for s in slots)
  '''
