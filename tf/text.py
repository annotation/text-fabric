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

    def passage(self, n, firstSlot=False, lang='en'):
        F = self.api.F
        L = self.api.L
        slotType = F.otype.slotType
        nType = F.otype.v(n)
        r = L.d(n, slotType)[0] if firstSlot and nType != slotType else n
        rType = F.otype.v(r)
        if rType in {'book', 'chapter', 'verse'}: return r
        isSlot = rType == slotType
        isBook = rType == 'book'
        isChapter = rType == 'chapter'
        isVerse = rType == 'verse'
        slots = [r] if isSlot else L.d(r, slotType)
        fS = r if isSlot else slots[0]
        lS = r if isSlot else slots[-1]
        bn = r if isBook else  L.u(r, 'book')
        cn = r if isChapter else None if isBook else L.u(r, 'chapter')
        vn = r if isVerse else None if isBook or isChapter else L.u(fS, 'verse')
        vnl = r if isVerse else None if isBook or isChapter else L.u(lS, 'verse')
        return (
            self.bookName(bn, lang=lang),
            F.chapter.v(cn),
            F.verse.v(vn),
        )+((F.verse.v(vnl),) if vn != vnl else ())

