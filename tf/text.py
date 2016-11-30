class Text(object):
    def __init__(self, api, tf):
        self.api = api
        self.languages = {}
        self.nameFromNode = {}
        self.nodeFromName = {}

        for (fName, fObj) in sorted(f for f in tf.features.items() if f[0] == 'book' or f[0].startswith('book@')):
            fObj.load(silent=True)
            meta = fObj.metaData
            code = meta.get('languageCode', '')
            self.languages[code] = dict(((k, meta.get(k, 'default')) for k in ('language', 'languageEnglish')))
            self.nameFromNode[code] = fObj.data
            self.nodeFromName[code] = dict(((name, node) for (node, name) in fObj.data.items()))

    def bookName(self, n, lang='en'):
        return self.nameFromNode['' if lang not in self.languages else lang].get(
            n if self.api.F.otype.v(n) == 'book' else self.api.L.u(n, 'book')[0], 'not a book node',
        )

    def bookNode(self, name, lang='en'):
        return self.nodeFromName['' if lang not in self.languages else lang].get(name, None)
