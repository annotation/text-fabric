from .data import GRID, SECTIONS
from .helpers import *

DEFAULT_FORMAT = 'text-orig-full'

class Text(object):
    def __init__(self, api, tf):
        self.api = api
        self.languages = {}
        self.nameFromNode = {}
        self.nodeFromName = {}
        config = tf.features[GRID[2]].metaData if GRID[2] in tf.features else {}
        self.sectionTypes = itemize(config.get('sectionTypes', ''), ',')
        sectionFeats = itemize(config.get('sectionFeatures', ''), ',')
        self.sectionFeatures = []
        self.config = config

        good = True
        if len(sectionFeats) != 0 and len(self.sectionTypes) != 0:
            for (fName, fObj) in sorted(
                    f for f in tf.features.items() if f[0].startswith(
                        '{}@'.format(sectionFeats[0])
            )):
                if not fObj.load(silent=True):
                    good=False
                    continue
                meta = fObj.metaData
                code = meta.get('languageCode', '')
                self.languages[code] = dict(((k, meta.get(k, 'default')) for k in ('language', 'languageEnglish')))
                self.nameFromNode[code] = fObj.data
                self.nodeFromName[code] = dict(((name, node) for (node, name) in fObj.data.items()))
            for fName in (SECTIONS):
                if not tf.features[fName].load(silent=True):
                    good=False
                    continue
                self.sectionFeatures.append(tf.features[fName].data)


            sec0 = SECTIONS[0]
            setattr(self, '{}Name'.format(sec0), self._sec0Name)
            setattr(self, '{}Node'.format(sec0), self._sec0Node)

        self._xformats = compileFormats(tf._cformats, tf.features)
        self.formats = set(self._xformats.keys())
        self.good = good

    def _sec0Name(self, n, lang='en'):
        sec0T = self.sectionTypes[0]
        return self.nameFromNode['' if lang not in self.languages else lang].get(
            n if self.api.F.otype.v(n) == sec0T else self.api.L.u(n, sec0T)[0], 'not a {} node'.format(sec0T),
        )

    def _sec0Node(self, name, lang='en'):
        return self.nodeFromName['' if lang not in self.languages else lang].get(name, None)

    def sectionFromNode(self, n, lastSlot=False, lang='en'):
        sTypes = self.sectionTypes
        if len(sTypes) == 0: return ()
        sFs = self.sectionFeatures 
        F = self.api.F
        L = self.api.L
        slotType = F.otype.slotType
        nType = F.otype.v(n)
        r = L.d(n, slotType)[-1] if lastSlot and nType != slotType else L.d(n, slotType)[0] if nType != slotType else n
        n0 = L.u(r, sTypes[0])[0]
        n1 = L.u(r, sTypes[1])[0]
        n2 = L.u(r, sTypes[2])[0]
        return (
            self._sec0Name(n0, lang=lang),
            sFs[1].get(n1, None),
            sFs[2].get(n2, None),
        )

    def nodeFromSection(self, section, lang='en'):
        sTypes = self.sectionTypes
        if len(sTypes) == 0: return None
        (sec1, sec2) = self.api.C.sections.data
        sec0node = self._sec0Node(section[0], lang=lang)
        if len(section) == 1:
            return sec0node 
        elif len(section) == 2:
            return sec1.get(sec0node, {}).get(section[1], None)
        else:
            return sec2.get(sec0node, {}).get(section[1], {}).get(section[2], None)

    def text(self, slots, fmt=None):
        if fmt == None: fmt = DEFAULT_FORMAT
        repf = self._xformats.get(fmt, None)
        if repf == None:
            return ' '.join(str(s) for s in slots)
        return ''.join(repf(s) for s in slots)

