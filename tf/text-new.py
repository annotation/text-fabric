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

    def sectionFromNode(self, n, lastSlot=True, lang='en'):
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

    def passage(self, section=None, otype=None, fmt=None, html=False, sectionLabel=True, lang='en', style=None):
        sTypes = self.sectionTypes
        if len(sTypes) == 0: return None
        L = self.api.L
        F = self.api.F
        info = self.api.info
        error = self.api.error
        if fmt != None and otype != None:
            otype = None
            error('fmt and otype parameters exclude each other. Ignoring otype="{}"'.format(otype)) 
        if otype == None and fmt == None: fmt = DEFAULT_FORMAT
        tables = []
        txt = []
        sec0 = None if section == None or len(section) < 1 else section[0]
        sec1 = None if section == None or len(section) < 2 else section[1]
        sec2 = None if section == None or len(section) < 3 else section[2]
        sec0s = [] if sec0 == None else [sec0] if type(sec0) is str else list(sec0)
        sec1s = [] if sec1 == None else [sec1] if type(sec1) is int else [int(sec1)] if type(sec1) is str else list(sec1)
        sec2s = [] if sec2 == None else [sec2] if type(sec2) is int else [int(sec2)] if type(sec2) is str else list(sec2)
        result_sec2_nodes = []

        def dump_table():
            if not otype:
                if html:
                    tables.append('<table class="t">\n{}</table>\n\n'.format(''.join(txt)))
                else:
                    tables.append(''.join(txt))
                txt.clear()
            
        if sec0 == None: sec0_nodes = tuple(x[0] for x in self._sec0s)
        else:
            sec0_nodes = []
            for sec0 in sec0s:
                bn = self._sec0_node.get(lang, {}).get(sec0, None)
                if bn == None:
                    error('No {} named "{}" in language "{}"'.format(SECTIONS[0], sec0, lang))
                    continue
                sec0_nodes.append(bn)
        for bn in sec0_nodes:
            sec0name = self.sec0_name(bn, lang) 
            cnodes = L.d(bn, sTypes[1])
            if len(sec1s) == 0: sec1_nodes = cnodes
            else:
                sec1_nodes = []
                for sec1 in sec1s:
                    if sec1 not in self._sec2s[bn]:
                        error('No {} {} in {} "{}" ({})'.format(SECTIONS[1], sec1, SECTIONS[0], sec0name, lang))
                    else:
                        sec1_nodes.extend([c for c in cnodes if int(F.sft_sec1.v(c)) == sec1])
            for cn in sec1_nodes:
                chname = F.sft_sec1.v(cn)
                vnodes = L.d(cn, sTypes[2])
                if len(sec2s) == 0: sec2_nodes = vnodes
                else: 
                    sec2_nodes = []
                    for sec2 in sec2s:
                        if sec2 not in self._sec2s[bn][int(sec1name)]:
                            error('No {} {} in {} "{}" ({}) {} {}'.format(SECTIONS[2], sec2, SECTIONS[0], sec0name, lang, SECTIONS[1], sec1name))
                        else:
                            sec2_nodes.extend([v for v in vnodes if int(F.sft_sec2.v(v)) == sec2])
                if otype:
                    result_sec2_nodes.extend(sec2_nodes)
                if fmt:
                    for vn in sec2_nodes:
                        sec2name = F.sft_sec2.v(vn)
                        sec2label = '{} {}:{}'.format(sec0name,sec1name,sec2name)
                        sec2head = '' if not sectionLabel else '<td class="vl">{}</td>'.format(sec2label) if html else '{}\t'.format(sec2label)
                        tx = self.words(L.d('word', vn), fmt=fmt)
                        if html: tx = '<td class="{}">{}</td>'.format(fmt[0], h_esc(tx))
                        line = '<tr>{}{}</tr>\n'.format(sec2head, tx) if html else sec2head + tx.rstrip('\n')+'\n'
                        txt.append(line)

                if len(sec2s) != 1: dump_table()
            if len(sec2s) == 1 and len(sec1s) != 1: dump_table()
        if len(sec2s) == 1 and len(sec1s) == 1: dump_table()
        if otype:
            result_words = []
            for vn in result_sec2_nodes: result_words.extend(L.d('word', vn))
            if otype == 'word': return result_words
            else:
                result_objects = []
                objects_seen = set()
                for wn in result_words:
                    obj = L.u(otype, wn)
                    if obj not in objects_seen:
                        result_objects.append(obj)
                        objects_seen.add(obj)
                return result_objects
        if fmt:
            body = ''.join(tables)
            if not style or not html:
                return body
            else:
                title = '{} {}:{} [{}]'.format(
                    ', '.join(str(sec0) for sec0 in sec0s) if sec0 != None else 'all {}s'.format(SECTIONS[0]),
                    ', '.join(str(sec1) for sec1 in sec1s) if sec1 != None else 'all {}s'.format(SECTIONS[1]),
                    ', '.join(str(sec2) for sec2 in sec2s) if sec2 != None else 'all {}s'.format(SECTIONS[2]),
                    fmt,
                )
                return '''<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<title>{}</title>
{}
</head>
<body>
{}
</body>
</html>
'''.format(title, style, body)

    def style(self, params=None, show_params=False):
        error = self.api.error
        info = self.api.info
        if self.biblang == 'Hebrew':
            style_defaults = dict(
                hebrew_color='000000',
                hebrew_size='large',
                hebrew_line_height='1.8',
                etcbc_color='aa0066',
                etcbc_size='small',
                etcbc_line_height='1.5',
                phono_color='00b040',
                phono_size='medium',
                phono_line_height='1.5',
                sec2_color='0000ff',
                sec2_size='small',
                sec2_width='5em',
            )
        elif self.biblang == 'Greek':
            style_defaults = dict(
                greek_color='000000',
                greek_size='large',
                greek_line_height='1.8',
                sec2_color='0000ff',
                sec2_size='small',
                sec2_width='5em',
            )
        errors = []
        good = True
        for x in [1]:
            good = False
            if params == None:
                params = dict()
            if type(params) is not dict:
                errors.append('ERROR: the style parameters should be a dictionary')
                break
            thisgood = True
            for x in params:
                if x not in style_defaults:
                    errors.append('ERROR: unknown style parameter: {}'.format(x))
                    thisgood = False
            if not thisgood: break
            good = True
        if not good:
            errors.append('ERROR: wrong style specfication. Switching to default values')
            for e in errors: error(e)
            params = dict()
        style_defaults.update(params)
        if not good or show_params:
            for x in sorted(style_defaults): info('{} = {}'.format(x, style_defaults[x]))

        if self.biblang == 'Hebrew':
            thestyle = '''
<style type="text/css">
table.t {{
    width: 100%;
}}
td.h {{
    font-family: Ezra SIL, SBL Hebrew, Verdana, sans-serif;
    font-size: {hebrew_size};
    line-height: {hebrew_line_height};
    color: #{hebrew_color};
    text-align: right;
    direction: rtl;
}}
td.e {{
    font-family: Menlo, Courier New, Courier, monospace;
    font-size: {etcbc_size};
    line-height: {etcbc_line_height};
    color: #{etcbc_color};
    text-align: left;
    direction: ltr;
}}
td.p {{
    font-family: Verdana, Arial, sans-serif;
    font-size: {phono_size};
    line-height: {phono_line_height};
    color: #{phono_color};
    text-align: left;
    direction: ltr;
}}

td.vl {{
    font-family: Verdana, Arial, sans-serif;
    font-size: {sec2_size};
    text-align: right;
    vertical-align: top;
    color: #{sec2_color};
    width: {sec2_width};
    direction: ltr;
}}
</style>
'''.format(**style_defaults)
        elif self.biblang == 'Greek':
            thestyle = '''
<style type="text/css">
table.t {{
    width: 100%;
}}
td.g {{
    font-family: Galatia SIL, SBL Greek, Verdana, sans-serif;
    font-size: {greek_size};
    line-height: {greek_line_height};
    color: #{greek_color};
    text-align: left;
    direction: ltr;
}}

td.vl {{
    font-family: Verdana, Arial, sans-serif;
    font-size: {sec2_size};
    text-align: right;
    vertical-align: top;
    color: #{sec2_color};
    width: {sec2_width};
    direction: ltr;
}}
</style>
'''.format(**style_defaults)
        return thestyle

