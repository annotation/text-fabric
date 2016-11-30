from .data import SKELETON

class Text(object):
    def __init__(self, api, tf):
        self.api = api
        self.languages = {}
        self.nameFromNode = {}
        self.nodeFromName = {}
        config = tf.features[SKELETON[2]].metaData
        sections = config.get('sections', '').strip().split(',')
        sectionFeatureNames = [config.get('{}Feature'.format(s), '') for s in sections]
        sectionTypes = [config.get('{}Otype'.format(s), '') for s in sections]
        good = True
        for i in range(len(sections)):
            if sectionFeatureNames[i] == '':
                tf.tm.error('No feature name associated with section level {} = {}'.format(i+1, sections[i]))
                good = False
            if sectionTypes[i] == '':
                tf.tm.error('No node type associated with section level {} = {}'.format(i+1, sections[i]))
                good = False

        tf.loadExtra(sectionFeatureNames)
        if not good or not tf.good:
            tf.tm.error('Failed to load the Text API')
            return

        sectionFeatures = tuple(tf.features[sectionFeatureNames[i]] for i in range(len(sections)))

        for (fName, fObj) in [('', sectionFeatures[0])] + sorted(f for f in tf.features.items() if f[0].startswith(
            '{}@'.format(sectionFeatureNames[0])
        )):
            if fName != '': fObj.load(silent=True)
            meta = fObj.metaData
            code = meta.get('languageCode', '')
            self.languages[code] = dict(((k, meta.get(k, 'default')) for k in ('language', 'languageEnglish')))
            self.nameFromNode[code] = fObj.data
            self.nodeFromName[code] = dict(((name, node) for (node, name) in fObj.data.items()))

        self.sectionTypes = sectionTypes
        self.sectionFeatureNames = sectionFeatureNames
        self.sectionFeatures = sectionFeatures
        setattr(self, '{}Name'.format(sections[0]), self._sec0Name)
        setattr(self, '{}Node'.format(sections[0]), self._sec0Node)

    def _sec0Name(self, n, lang='en'):
        stp = self.sectionTypes[0]
        return self.nameFromNode['' if lang not in self.languages else lang].get(
            n if self.api.F.otype.v(n) == stp else self.api.L.u(n, stp)[0], 'not a {} node'.format(stp),
        )

    def _sec0Node(self, name, lang='en'):
        return self.nodeFromName['' if lang not in self.languages else lang].get(name, None)

    def sectionFromNode(self, n, lastSlot=True, lang='en'):
        F = self.api.F
        Fs = self.api.Fs
        L = self.api.L
        slotType = F.otype.slotType
        nType = F.otype.v(n)
        r = L.d(n, slotType)[-1] if lastSlot and nType != slotType else L.d(n, slotType)[0] if nType != slotType else n
        n0 = L.u(r, self.sectionTypes[0])[0]
        n1 = L.u(r, self.sectionTypes[1])[0]
        n2 = L.u(r, self.sectionTypes[2])[0]
        return (
            self._sec0Name(n0, lang=lang),
            self.sectionFeatures[1].data.get(n1, None),
            self.sectionFeatures[2].data.get(n2, None),
        )

