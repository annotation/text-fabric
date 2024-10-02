import sys
import os
import time
import glob
import collections
from contextlib import contextmanager
import unittest

from laf.fabric import LafFabric
from laf.names import FabricError
from etcbc.preprocess import prepare

SOURCE = 'etcbc4'
ANNOX = 'px'
DATADIR = './example-data'
DATADIRA = '{}/example-data'.format(os.getcwd())
LAFDIR = DATADIR
LAFDIRA = DATADIRA
OUTPUTDIR = './example-output'
OUTPUTDIRA = '{}/example-output'.format(os.getcwd())
SPECIFIC_MSG = "running an individual test"
SPECIFIC = False

if __name__ == '__main__':
    spec = sys.argv[-1]
    if spec in ('0', '1'):
        SPECIFIC = spec == '1'
        del sys.argv[-1]

class TestLafFabric(unittest.TestCase):
    fabric = None

    def setUp(self):
        if self.fabric == None:
            self.fabric = LafFabric(
                data_dir=DATADIR,
                laf_dir=LAFDIR,
                output_dir=OUTPUTDIR,
                save=False,
                verbose='SILENT',
            )
        pass

    @unittest.skipIf(SPECIFIC, SPECIFIC_MSG)
    def test_a100_startup(self):
        lafapi = self.fabric.lafapi
        self.assertEqual(lafapi.names._myconfig['data_dir'], DATADIRA)
        self.assertEqual(lafapi.names._myconfig['m_source_dir'], LAFDIRA)
        pass

    @unittest.skipIf(SPECIFIC, SPECIFIC_MSG)
    def test_b100_compile_main(self):
        now = time.time()
        time.sleep(1)
        API = self.fabric.load(SOURCE, '--', 'compile', {}, compile_main=True)
        close = API['close']
        found = 0
        the_log = None
        the_log_mtime = None
        newer = True
        for f in glob.glob("{}/{}/bin/*".format(DATADIRA, SOURCE)):
            fn = os.path.basename(f)
            if fn in 'AZ': continue
            elif fn == '__log__compile__.txt':
                the_log = f
                the_log_mtime = os.path.getmtime(f)
            else:
                found += 1
            if os.path.getmtime(f) < now: newer = False
        self.assertTrue(newer)
        self.assertTrue(the_log)
        self.assertEqual(found, 44)
        close()
        API = self.fabric.load_again({}, compile_main=False)
        close = API['close']
        close()
        self.assertEqual(the_log_mtime, os.path.getmtime(the_log)), 

    @unittest.skipIf(SPECIFIC, SPECIFIC_MSG)
    def test_b200_compile_annox(self):
        now = time.time()
        time.sleep(1)
        API = self.fabric.load(SOURCE, ANNOX, 'compile', {}, compile_annox=True)
        close = API['close']
        found = 0
        the_log = None
        the_log_mtime = None
        newer = True
        for f in glob.glob("{}/{}/bin/A/{}/*".format(DATADIRA, SOURCE, ANNOX)):
            fn = os.path.basename(f)
            if fn == '__log__compile__.txt':
                the_log = f
                the_log_mtime = os.path.getmtime(f)
            else:
                found += 1
            if os.path.getmtime(f) < now: newer = False
        self.assertTrue(newer)
        self.assertTrue(the_log)
        self.assertEqual(found, 10)
        close()
        API = self.fabric.load_again({}, compile_annox=False)
        close = API['close']
        close()
        self.assertEqual(the_log_mtime, os.path.getmtime(the_log)), 

    @unittest.skipIf(SPECIFIC, SPECIFIC_MSG)
    def test_d100_load(self):
        self.fabric.lafapi.unload_all()
        API = self.fabric.load(SOURCE, ANNOX, 'load', {
                "xmlids": {
                    "node": True,
                    "edge": True,
                },
                "features": {
                    "etcbc4": {
                        "node": [
                            "db.otype",
                            "ft.g_word_utf8,trailer_utf8",
                            "sft.book",
                        ],
                        "edge": [
                            "ft.mother",
                            "ft.functional_parent",
                        ],
                    },
                },
                "primary": True,
            },
            compile_main=False, compile_annox=False,
        )
        close = API['close']
        close()
        loadspec = self.fabric.lafapi.loadspec
        self.assertEqual(len(loadspec['keep']), 0)
        self.assertEqual(len(loadspec['clear']), 0)
        self.assertEqual(len(loadspec['load']), 37)

        API = self.fabric.load(SOURCE, ANNOX, 'load', {
                "xmlids": {
                    "node": True,
                    "edge": False,
                },
                "features": {
                    "etcbc4": {
                        "node": [
                            "db.oid",
                            "ft.g_word_utf8,trailer_utf8",
                            "sft.book",
                        ],
                        "edge": [
                            "ft.functional_parent",
                        ],
                    },
                },
                "primary": False,
            },
            compile_main=False, compile_annox=False,
        )
        close = API['close']
        close()
        loadspec = self.fabric.lafapi.loadspec
        self.assertEqual(len(loadspec['keep']), 20)
        self.assertEqual(len(loadspec['clear']), 17)
        self.assertEqual(len(loadspec['load']), 2)

    @unittest.skipIf(SPECIFIC, SPECIFIC_MSG)
    def test_d200_load(self):
        self.fabric.lafapi.unload_all()
        API = self.fabric.load(SOURCE, ANNOX, 'load2', {
                "xmlids": {
                    "node": False,
                    "edge": False,
                },
                "features": {
                    "etcbc4": {
                        "node": [
                            "db.otype",
                            "ft.g_word_utf8,trailer_utf8",
                            "sft.book",
                        ],
                        "edge": [
                            "ft.mother",
                            "ft.functional_parent",
                        ],
                    },
                    "dirk": {
                        "node": [
                            "db.otype",
                            "dbs.otype",
                        ],
                    }
                },
                "primary": True,
                "prepare": prepare,
            },
            compile_main=False, compile_annox=False,
        )
        close = API['close']
        close()
        feature_abbs = self.fabric.lafapi.feature_abbs
        feature_abb = self.fabric.lafapi.feature_abb
        self.assertEqual(feature_abb['otype'], 'etcbc4_db_otype')
        self.assertEqual(len(feature_abbs['otype']), 3)
        for nm in ('etcbc4_db_otype', 'dirk_dbs_otype', 'dirk_db_otype'): self.assertTrue(nm in feature_abbs['otype'])
        self.assertEqual(len(feature_abbs['db_otype']), 2)
        for nm in ('etcbc4_db_otype', 'dirk_db_otype'): nm in feature_abbs['db_otype']

    @unittest.skipIf(SPECIFIC, SPECIFIC_MSG)
    def test_d300_resolve(self):
        API = self.fabric.load(SOURCE, '--', 'resolve', {"features": ("","")})
        feature = self.fabric.resolve_feature('node', 'otype')
        self.assertEqual(feature, ('etcbc4', 'db', 'otype'))
        feature = self.fabric.resolve_feature('node', 'db.otype')
        self.assertEqual(feature, ('etcbc4', 'db', 'otype'))
        feature = self.fabric.resolve_feature('node', 'etcbc4:db.otype')
        self.assertEqual(feature, ('etcbc4', 'db', 'otype'))

    @unittest.skipIf(SPECIFIC, SPECIFIC_MSG)
    def test_e100_monad_numbers(self):
        API = self.fabric.load(SOURCE, '--', 'monads', {"features": ("otype monads","")})
        NN = API['NN']
        F = API['F']
        close = API['close']
        monads = []
        for n in NN(test=F.otype.v, value='word'):
            monads.append(int(F.monads.v(n)))
        close()
        expected = [1,2,3,4,5,6,7,8,9,10,11,227281,227282,227284,227283,227285,227286,227287,227288,227289,227290,227291,227292,227293,227295,227294,227296,227297,227298,227299,227300]
        self.assertEqual(monads, expected)

        API = self.fabric.load_again({"features": ("otype monads",""), 'prepare': prepare})
        NN = API['NN']
        F = API['F']
        close = API['close']
        monads = []
        for n in NN(test=F.otype.v, value='word'):
            monads.append(int(F.monads.v(n)))
        close()
        expected = [1,2,3,4,5,6,7,8,9,10,11,227281,227282,227283,227284,227285,227286,227287,227288,227289,227290,227291,227292,227293,227294,227295,227296,227297,227298,227299,227300]
        self.assertEqual(monads, expected)

    @unittest.skipIf(SPECIFIC, SPECIFIC_MSG)
    def test_e200_primary_data(self):
        API = self.fabric.load(SOURCE, '--', 'plain', {"features": ("otype",""), "primary": True})
        NN = API['NN']
        F = API['F']
        P = API['P']
        close = API['close']
        text = ''
        for n in NN(test=F.otype.v, value='word'):
            text += '['+']['.join([p[1] for p in P.data(n)])+']'
        close()
        expected = '''[בְּ][רֵאשִׁ֖ית][בָּרָ֣א][אֱלֹהִ֑ים][אֵ֥ת][הַ][שָּׁמַ֖יִם][וְ][אֵ֥ת][הָ][אָֽרֶץ][אֶתֵּ֤ן][בַּ][מִּדְבָּר֙][][אֶ֣רֶז][שִׁטָּ֔ה][וַ][הֲדַ֖ס][וְ][עֵ֣ץ][שָׁ֑מֶן][אָשִׂ֣ים][בָּ][עֲרָבָ֗ה][][בְּרֹ֛ושׁ][תִּדְהָ֥ר][וּ][תְאַשּׁ֖וּר][יַחְדָּֽו]'''
        self.assertEqual(text, expected)

        API = self.fabric.load_again({"features": ("otype",""), "primary": True, "prepare": prepare})
        NN = API['NN']
        F = API['F']
        P = API['P']
        close = API['close']
        text = ''
        for n in NN(test=F.otype.v, value='word'):
            text += '['+']['.join([p[1] for p in P.data(n)])+']'
        close()
        expected = '''[בְּ][רֵאשִׁ֖ית][בָּרָ֣א][אֱלֹהִ֑ים][אֵ֥ת][הַ][שָּׁמַ֖יִם][וְ][אֵ֥ת][הָ][אָֽרֶץ][אֶתֵּ֤ן][בַּ][][מִּדְבָּר֙][אֶ֣רֶז][שִׁטָּ֔ה][וַ][הֲדַ֖ס][וְ][עֵ֣ץ][שָׁ֑מֶן][אָשִׂ֣ים][בָּ][][עֲרָבָ֗ה][בְּרֹ֛ושׁ][תִּדְהָ֥ר][וּ][תְאַשּׁ֖וּר][יַחְדָּֽו]'''
        self.assertEqual(text, expected)

    @unittest.skipIf(SPECIFIC, SPECIFIC_MSG)
    def test_e300_lingo(self):
        API = self.fabric.load(SOURCE, '--', 'lingo', {"features": ("otype",""), "primary": True})
        F = API['F']
        NE = API['NE']
        close = API['close']
        text = ''
        for (anchor, events) in NE():
            for (node, kind) in events:
                kindr = '(' if kind == 0 else '«' if kind == 1 else '»' if kind == 2 else ')'
                otype = F.otype.v(node)
                text += "{} {:>7}: {:<15} {:>7}\n".format(kindr, anchor, otype, node)
        close()
        expected = '''(       0: book                 79
(       0: chapter              80
(       0: verse                81
(       0: sentence             31
(       0: sentence_atom        32
(       0: clause               33
(       0: clause_atom          34
(       0: half_verse           82
(       0: phrase               35
(       0: phrase_atom          39
(       0: word                  0
)       3: word                  0
(       3: word                  1
)      12: word                  1
)      12: phrase_atom          39
)      12: phrase               35
»      12: clause_atom          34
»      12: clause               33
»      12: sentence_atom        32
»      12: sentence             31
«      13: sentence             31
«      13: sentence_atom        32
«      13: clause               33
«      13: clause_atom          34
(      13: word                  2
(      13: phrase               36
(      13: phrase_atom          40
)      20: phrase_atom          40
)      20: phrase               36
)      20: word                  2
»      20: clause_atom          34
»      20: clause               33
»      20: sentence_atom        32
»      20: sentence             31
«      21: sentence             31
«      21: sentence_atom        32
«      21: clause               33
«      21: clause_atom          34
(      21: word                  3
(      21: phrase               37
(      21: phrase_atom          41
)      30: phrase_atom          41
)      30: phrase               37
)      30: word                  3
»      30: clause_atom          34
»      30: clause               33
»      30: sentence_atom        32
»      30: sentence             31
)      31: half_verse           82
«      31: sentence             31
«      31: sentence_atom        32
«      31: clause               33
«      31: clause_atom          34
(      31: half_verse           83
(      31: phrase               38
(      31: phrase_atom          42
(      31: subphrase            43
(      31: word                  4
)      35: word                  4
»      35: subphrase            43
»      35: phrase_atom          42
»      35: phrase               38
»      35: clause_atom          34
»      35: clause               33
»      35: sentence_atom        32
»      35: sentence             31
«      36: sentence             31
«      36: sentence_atom        32
«      36: clause               33
«      36: clause_atom          34
«      36: phrase               38
«      36: phrase_atom          42
«      36: subphrase            43
(      36: word                  5
)      38: word                  5
(      38: word                  6
)      48: word                  6
)      48: subphrase            43
»      48: phrase_atom          42
»      48: phrase               38
»      48: clause_atom          34
»      48: clause               33
»      48: sentence_atom        32
»      48: sentence             31
«      49: sentence             31
«      49: sentence_atom        32
«      49: clause               33
«      49: clause_atom          34
«      49: phrase               38
«      49: phrase_atom          42
(      49: word                  7
)      51: word                  7
(      51: subphrase            44
(      51: word                  8
)      55: word                  8
»      55: subphrase            44
»      55: phrase_atom          42
»      55: phrase               38
»      55: clause_atom          34
»      55: clause               33
»      55: sentence_atom        32
»      55: sentence             31
«      56: sentence             31
«      56: sentence_atom        32
«      56: clause               33
«      56: clause_atom          34
«      56: phrase               38
«      56: phrase_atom          42
«      56: subphrase            44
(      56: word                  9
)      58: word                  9
(      58: word                 10
)      64: word                 10
)      64: subphrase            44
)      64: phrase_atom          42
)      64: phrase               38
)      64: clause_atom          34
)      64: clause               33
)      64: sentence_atom        32
)      64: sentence             31
)      65: half_verse           83
)      65: verse                81
(      66: sentence             45
(      66: sentence_atom        47
(      66: clause               49
(      66: clause_atom          51
(      66: word                 11
(      66: phrase               53
(      66: phrase_atom          60
)      73: phrase_atom          60
)      73: phrase               53
)      73: word                 11
»      73: clause_atom          51
»      73: clause               49
»      73: sentence_atom        47
»      73: sentence             45
«      74: sentence             45
«      74: sentence_atom        47
«      74: clause               49
«      74: clause_atom          51
(      74: phrase               54
(      74: phrase_atom          61
(      74: word                 12
)      77: word                 12
(      77: word                 13
)      77: word                 13
(      77: word                 14
)      87: word                 14
)      87: phrase_atom          61
)      87: phrase               54
»      87: clause_atom          51
»      87: clause               49
»      87: sentence_atom        47
»      87: sentence             45
«      88: sentence             45
«      88: sentence_atom        47
«      88: clause               49
«      88: clause_atom          51
(      88: phrase               55
(      88: phrase_atom          62
(      88: subphrase            67
(      88: subphrase            68
(      88: word                 15
(      88: subphrase            69
)      94: subphrase            69
)      94: word                 15
»      94: subphrase            68
»      94: subphrase            67
»      94: phrase_atom          62
»      94: phrase               55
»      94: clause_atom          51
»      94: clause               49
»      94: sentence_atom        47
»      94: sentence             45
«      95: sentence             45
«      95: sentence_atom        47
«      95: clause               49
«      95: clause_atom          51
«      95: phrase               55
«      95: phrase_atom          62
«      95: subphrase            67
«      95: subphrase            68
(      95: word                 16
(      95: subphrase            70
)     103: subphrase            70
)     103: word                 16
)     103: subphrase            68
»     103: subphrase            67
»     103: phrase_atom          62
»     103: phrase               55
»     103: clause_atom          51
»     103: clause               49
»     103: sentence_atom        47
»     103: sentence             45
«     104: sentence             45
«     104: sentence_atom        47
«     104: clause               49
«     104: clause_atom          51
«     104: phrase               55
«     104: phrase_atom          62
«     104: subphrase            67
(     104: word                 17
)     106: word                 17
(     106: word                 18
(     106: subphrase            71
)     112: subphrase            71
)     112: word                 18
)     112: subphrase            67
»     112: phrase_atom          62
»     112: phrase               55
»     112: clause_atom          51
»     112: clause               49
»     112: sentence_atom        47
»     112: sentence             45
«     113: sentence             45
«     113: sentence_atom        47
«     113: clause               49
«     113: clause_atom          51
«     113: phrase               55
«     113: phrase_atom          62
(     113: word                 19
)     115: word                 19
(     115: subphrase            72
(     115: word                 20
(     115: subphrase            73
)     119: subphrase            73
)     119: word                 20
»     119: subphrase            72
»     119: phrase_atom          62
»     119: phrase               55
»     119: clause_atom          51
»     119: clause               49
»     119: sentence_atom        47
»     119: sentence             45
«     120: sentence             45
«     120: sentence_atom        47
«     120: clause               49
«     120: clause_atom          51
«     120: phrase               55
«     120: phrase_atom          62
«     120: subphrase            72
(     120: word                 21
(     120: subphrase            74
)     127: subphrase            74
)     127: word                 21
)     127: subphrase            72
)     127: phrase_atom          62
)     127: phrase               55
)     127: clause_atom          51
)     127: clause               49
)     127: sentence_atom        47
)     127: sentence             45
(     128: sentence             46
(     128: sentence_atom        48
(     128: clause               50
(     128: clause_atom          52
(     128: word                 22
(     128: phrase               56
(     128: phrase_atom          63
)     136: phrase_atom          63
)     136: phrase               56
)     136: word                 22
»     136: clause_atom          52
»     136: clause               50
»     136: sentence_atom        48
»     136: sentence             46
«     137: sentence             46
«     137: sentence_atom        48
«     137: clause               50
«     137: clause_atom          52
(     137: phrase               57
(     137: phrase_atom          64
(     137: word                 23
)     140: word                 23
(     140: word                 24
)     140: word                 24
(     140: word                 25
)     148: word                 25
)     148: phrase_atom          64
)     148: phrase               57
»     148: clause_atom          52
»     148: clause               50
»     148: sentence_atom        48
»     148: sentence             46
«     149: sentence             46
«     149: sentence_atom        48
«     149: clause               50
«     149: clause_atom          52
(     149: phrase               58
(     149: phrase_atom          65
(     149: subphrase            75
(     149: word                 26
(     149: subphrase            76
)     158: subphrase            76
)     158: word                 26
»     158: subphrase            75
»     158: phrase_atom          65
»     158: phrase               58
»     158: clause_atom          52
»     158: clause               50
»     158: sentence_atom        48
»     158: sentence             46
«     159: sentence             46
«     159: sentence_atom        48
«     159: clause               50
«     159: clause_atom          52
«     159: phrase               58
«     159: phrase_atom          65
«     159: subphrase            75
(     159: word                 27
(     159: subphrase            77
)     168: subphrase            77
)     168: word                 27
)     168: subphrase            75
»     168: phrase_atom          65
»     168: phrase               58
»     168: clause_atom          52
»     168: clause               50
»     168: sentence_atom        48
»     168: sentence             46
«     169: sentence             46
«     169: sentence_atom        48
«     169: clause               50
«     169: clause_atom          52
«     169: phrase               58
«     169: phrase_atom          65
(     169: word                 28
)     171: word                 28
(     171: word                 29
(     171: subphrase            78
)     182: subphrase            78
)     182: word                 29
)     182: phrase_atom          65
)     182: phrase               58
»     182: clause_atom          52
»     182: clause               50
»     182: sentence_atom        48
»     182: sentence             46
«     183: sentence             46
«     183: sentence_atom        48
«     183: clause               50
«     183: clause_atom          52
(     183: word                 30
(     183: phrase               59
(     183: phrase_atom          66
)     192: phrase_atom          66
)     192: phrase               59
)     192: word                 30
)     192: clause_atom          52
)     192: clause               50
)     192: sentence_atom        48
)     192: sentence             46
)    3901: chapter              80
)  185245: book                 79
( 1365328: book                 84
( 1459635: chapter              85
( 1461757: verse                86
( 1461757: half_verse           87
) 1461819: half_verse           87
( 1461819: half_verse           88
) 1461884: half_verse           88
) 1461884: verse                86
) 1463012: chapter              85
) 1522388: book                 84
'''
        self.assertEqual(text, expected)

    @unittest.skipIf(SPECIFIC, SPECIFIC_MSG)
    def test_m100_connectivity(self):
        API = self.fabric.load(SOURCE, ANNOX, 'connectivity', {"features": {"etcbc4": {"node": ["db.otype"], "edge": ["ft.functional_parent"]}}})
        NN = API['NN']
        F = API['F']
        C = API['C']
        close = API['close']

        top_node_types = collections.defaultdict(lambda: 0)
        top_nodes = set(C.functional_parent.endnodes(NN(test=F.otype.v, value='word')))
        self.assertEqual(len(top_nodes), 3)
        for node in NN(nodes=top_nodes):
            tag = F.otype.v(node)
            top_node_types[tag] += 1
        for tag in top_node_types:
            n = top_node_types[tag]
            self.assertEqual(tag, 'sentence')
            self.assertEqual(n, 3)
        nt = 0
        for node in NN():
            if C.functional_parent.e(node) and F.otype.v(node) == 'sentence':
                nt += 1
        self.assertEqual(nt, 0)
        close()

    @unittest.skipIf(SPECIFIC, SPECIFIC_MSG)
    def test_u100_plain(self):
        API = self.fabric.load(SOURCE, '--', 'plain', {"features": {"etcbc4": {"node": ["db.otype", "ft.g_word_utf8,trailer_utf8", "sft.book"]}}})
        F = API['F']
        close = API['close']
        textitems = []
        for i in F.otype.s('word'):
            text = F.g_word_utf8.v(i) 
            trailer = F.trailer_utf8.v(i) 
            textitems.append('{}{}{}'.format(text, trailer, "\n" if '׃' in trailer else ""))
        text = ''.join(textitems)
        expected = '''בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃
אֶתֵּ֤ן בַּמִּדְבָּר֙ אֶ֣רֶז שִׁטָּ֔ה וַהֲדַ֖ס וְעֵ֣ץ שָׁ֑מֶן אָשִׂ֣ים בָּעֲרָבָ֗ה בְּרֹ֛ושׁ תִּדְהָ֥ר וּתְאַשּׁ֖וּר יַחְדָּֽו׃
'''
        self.assertEqual(text, expected)
        close()
        API = self.fabric.load_again({"features": {"etcbc4": {"node": ["db.otype", "ft.g_word_utf8,trailer_utf8", "sft.book"]}}, "prepare": prepare})
        F = API['F']
        close = API['close']
        textitems = []
        for i in F.otype.s('word'):
            text = F.g_word_utf8.v(i) 
            trailer = F.trailer_utf8.v(i) 
            textitems.append('{}{}{}'.format(text, trailer, "\n" if '׃' in trailer else ""))
        text = ''.join(textitems)
        expected = '''בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃
אֶתֵּ֤ן בַּמִּדְבָּר֙ אֶ֣רֶז שִׁטָּ֔ה וַהֲדַ֖ס וְעֵ֣ץ שָׁ֑מֶן אָשִׂ֣ים בָּעֲרָבָ֗ה בְּרֹ֛ושׁ תִּדְהָ֥ר וּתְאַשּׁ֖וּר יַחְדָּֽו׃
'''
        self.assertEqual(text, expected)
        close()

    @unittest.skipIf(SPECIFIC, SPECIFIC_MSG)
    def test_u210_node_order(self):
        API = self.fabric.load(SOURCE, '--', 'n_prep', {"features": ("otype","")})
        NN = API['NN']
        close = API['close']
        expected_nodes = (79, 80, 81, 31, 32, 33, 34, 82, 35, 39, 0, 1, 2, 36, 40, 3, 37, 41, 83, 38, 42, 43, 4, 5, 6, 7, 44, 8, 9, 10, 45, 47, 49, 51, 11, 53, 60, 54, 61, 12, 14, 13, 55, 62, 67, 68, 15, 69, 16, 70, 17, 18, 71, 19, 72, 20, 73, 21, 74, 46, 48, 50, 52, 22, 56, 63, 57, 64, 23, 25, 24, 58, 65, 75, 26, 76, 27, 77, 28, 29, 78, 30, 59, 66, 84, 85, 86, 87, 88)
        close()
        for (i, n) in enumerate(NN()): self.assertEqual(n, expected_nodes[i])

        API = self.fabric.load_again({"features": ("otype",""), "prepare": prepare})
        NN = API['NN']
        close = API['close']
        expected_nodes = (79, 80, 81, 31, 32, 33, 34, 82, 35, 39, 0, 1, 36, 40, 2, 37, 41, 3, 83, 38, 42, 43, 4, 5, 6, 7, 44, 8, 9, 10, 84, 85, 86, 87, 45, 47, 49, 51, 53, 60, 11, 54, 61, 12, 13, 14, 55, 62, 67, 68, 69, 15, 70, 16, 17, 71, 18, 19, 72, 73, 20, 74, 21, 88, 46, 48, 50, 52, 56, 63, 22, 57, 64, 23, 24, 25, 58, 65, 75, 76, 26, 77, 27, 28, 78, 29, 59, 66, 30)
        close()
        for (i, n) in enumerate(NN()): self.assertEqual(n, expected_nodes[i])

    @unittest.skipIf(SPECIFIC, SPECIFIC_MSG)
    def test_u310_edge_features(self):
        API = self.fabric.load(SOURCE, ANNOX, 'edges', {"features": ("", "dirk:part.sectioning"), "prepare": prepare})
        FE = API['FE']
        C = API['C']
        Ci = API['Ci']
        close = API['close']
        i = 0
        expected_annots = (2,"from verse to its first half verse"),(3,"from verse to its second half verse")
        for (n, v) in sorted(FE.sectioning.alookup.items()):
            self.assertEqual((n, v), expected_annots[i])
            i += 1
        close()

    @unittest.skipIf(SPECIFIC, SPECIFIC_MSG)
    def test_u320_unmarked_edges(self):
        API = self.fabric.load(SOURCE, ANNOX, 'u_edges', {"features": ("", "dirk:part.sectioning laf:.x laf:.y"), "prepare": prepare})
        NN = API['NN']
        C = API['C']
        Ci = API['Ci']
        close = API['close']
        expected_x = [[80], [81], [82, 83], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [85], [86], [87, 88], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
        expected_xi = [[], [79], [80], [], [], [], [], [81], [], [], [], [], [], [], [], [], [], [], [81], [], [], [], [], [], [], [], [], [], [], [], [], [84], [85], [86], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [86], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
        expected_y = [[], [], [82, 83], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
        expected_yi = [[], [], [], [], [], [], [], [81], [], [], [], [], [], [], [], [], [], [], [81], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []] 
        i = 0
        for n in NN():
            j = 0
            for (m, v) in C.laf__x.vv(n, sort=True):
                self.assertEqual(v, '')
                self.assertEqual(m, expected_x[i][j])
                j += 1
            i += 1
        i = 0
        for n in NN():
            j = 0
            for (m, v) in C.laf__y.vv(n, sort=True):
                self.assertEqual(v, '')
                self.assertEqual(m, expected_y[i][j])
                j += 1
            i += 1
        i = 0
        for n in NN():
            j = 0
            for (m, v) in Ci.laf__x.vv(n, sort=True):
                self.assertEqual(v, '')
                self.assertEqual(m, expected_xi[i][j])
                j += 1
            i += 1
        i = 0
        for n in NN():
            j = 0
            for (m, v) in Ci.laf__y.vv(n, sort=True):
                self.assertEqual(v, '')
                self.assertEqual(m, expected_yi[i][j])
                j += 1
            i += 1
        close()

    @unittest.skipIf(SPECIFIC, SPECIFIC_MSG)
    def test_u330_endnodes(self):
        API = self.fabric.load(SOURCE, '--', 'plain', {
                "xmlids": {"node": True, "edge": True},
                "features": ("otype", "functional_parent .x"),
                "prepare": prepare,
            },
            compile_main=False, compile_annox=False,
        )
        NN = API['NN']
        F = API['F']
        C = API['C']
        Ci = API['Ci']
        close = API['close']
        for query in (
                ('functional_parent', 'forward', C.functional_parent, ['word', 'phrase', 'clause', 'sentence'], 48, 3, 1, {'sentence'}),
                ('functional_parent', 'backward', Ci.functional_parent, ['word', 'phrase', 'clause', 'sentence'], 48, 31, 1, {'word'}),
                ('unannotated', 'forward', C.laf__x, ['half_verse', 'verse', 'chapter', 'book'], 10, 4, 1, {'half_verse'}),
                ('unannotated', 'backward', Ci.laf__x, ['half_verse', 'verse', 'chapter', 'book'], 10, 2, 1, {'book'}),
            ):
                (the_edgetype, direction, the_edge, the_types, exp_o, exp_n, exp_t, exp_s) = query
                the_set = list(NN(test=F.otype.v, values=the_types))
                the_endset = set(the_edge.endnodes(the_set))
                the_endtypes = set([F.otype.v(n) for n in the_endset])
                self.assertEqual(len(the_set), exp_o)
                self.assertEqual(len(the_endset), exp_n)
                self.assertEqual(len(the_endtypes), exp_t)
                self.assertEqual(the_endtypes, exp_s)
        close()

    @unittest.skipIf(SPECIFIC, SPECIFIC_MSG)
    def test_u400_xml_ids(self):
        API = self.fabric.load(SOURCE, ANNOX, 'plain', {
                "xmlids": {"node": True,"edge": True,},
                "features": ("", "mother functional_parent"),
                "prepare": prepare,
            },
        )
        FE = API['FE']
        NN = API['NN']
        X = API['X']
        XE = API['XE']
        close = API['close']

        expected = {0: 'n2', 1: 'n3', 2: 'n4', 3: 'n5', 4: 'n6', 5: 'n7', 6: 'n8', 7: 'n9', 8: 'n10', 9: 'n11', 10: 'n12', 11: 'n705160', 12: 'n705161', 13: 'n705162', 14: 'n705163', 15: 'n705164', 16: 'n705165', 17: 'n705166', 18: 'n705167', 19: 'n705168', 20: 'n705169', 21: 'n705170', 22: 'n705171', 23: 'n705172', 24: 'n705173', 25: 'n705174', 26: 'n705175', 27: 'n705176', 28: 'n705177', 29: 'n705178', 30: 'n705179', 31: 'n84383', 32: 'n88917', 33: 'n28737', 34: 'n34680', 35: 'n59556', 36: 'n59557', 37: 'n59558', 38: 'n59559', 39: 'n40767', 40: 'n40768', 41: 'n40769', 42: 'n40770', 43: 'n77637', 44: 'n77638', 45: 'n763819', 46: 'n763820', 47: 'n768033', 48: 'n768034', 49: 'n717061', 50: 'n717062', 51: 'n722765', 52: 'n722766', 53: 'n749941', 54: 'n749942', 55: 'n749943', 56: 'n749944', 57: 'n749945', 58: 'n749946', 59: 'n749947', 60: 'n734528', 61: 'n734529', 62: 'n734530', 63: 'n734531', 64: 'n734532', 65: 'n734533', 66: 'n734534', 67: 'n759929', 68: 'n759927', 69: 'n759925', 70: 'n759926', 71: 'n759928', 72: 'n759932', 73: 'n759930', 74: 'n759931', 75: 'n759935', 76: 'n759933', 77: 'n759934', 78: 'n759936', 79: 'n1', 80: 'n93473', 81: 'n93523', 82: 'n95056', 83: 'n95057', 84: 'n690878', 85: 'n769812', 86: 'n770653', 87: 'n772740', 88: 'n772741'}
        self.assertEqual(len(set(NN())), len(expected))
        for (n,x) in expected.items():
            self.assertEqual(X.i(x), n)
            self.assertEqual(X.r(n), x)

        expected_e = {8: 'el1', 9: 'el101734', 10: 'el53244', 11: 'el53245', 12: 'el190840', 13: 'el190841', 14: 'el190842', 15: 'el253771', 16: 'el253772', 17: 'el253773', 18: 'el253774', 19: 'el385981', 20: 'el385982', 21: 'el385983', 22: 'el385984', 23: 'el385985', 24: 'el385986', 25: 'el385987', 26: 'el511117', 27: 'el511118', 28: 'el511119', 29: 'el511120', 30: 'el657926', 31: 'el657927', 32: 'el657928', 33: 'el657929', 34: 'el657930', 35: 'el657931', 36: 'el657932', 37: 'el793283', 38: 'el825158', 39: 'el825159', 40: 'el865010', 41: 'el865011', 42: 'el865012', 43: 'el953312', 44: 'el953313', 45: 'el953314', 46: 'el953315', 47: 'el953316', 48: 'el953317', 49: 'el953318', 50: 'el953319', 51: 'el953320', 52: 'el953321', 53: 'el953322', 54: 'el953323', 55: 'el953324', 56: 'el953325', 57: 'el953326', 58: 'el953327', 59: 'el953328', 60: 'el953329', 61: 'el1029314', 62: 'el1029315', 63: 'el1029316', 64: 'el1029317', 65: 'el1029318', 66: 'el1029319', 67: 'el1029320', 68: 'el1029321', 69: 'el1029322', 70: 'el1029323', 71: 'el1029324', 72: 'el1255606', 73: 'el1255607', 74: 'el1255608', 75: 'el1255609', 76: 'el1255610', 77: 'el1255611', 78: 'el1255612', 79: 'el1255613', 80: 'el1255614', 81: 'el1255615', 82: 'el1255616', 83: 'el1255617', 84: 'el1255618', 85: 'el1255619', 86: 'el1255620', 87: 'el1255621', 88: 'el1255622', 89: 'el1255623', 90: 'el1255624', 91: 'el1255625'}
        self.assertEqual(len(set(FE.functional_parent.lookup)|set(FE.mother.lookup)), len(expected_e))
        for (e,x) in expected_e.items():
            self.assertEqual(XE.i(x), e)
            self.assertEqual(XE.r(e), x)

        close()

    @unittest.skipIf(SPECIFIC, SPECIFIC_MSG)
    def test_u500_load_dict(self):
        self.assertRaises(FabricError, self.fabric.load, SOURCE, '--', 'load', {
                "xmlids": {
                    "node": True,
                    "edge": True,
                    "region": True,
                },
            }
        )
        self.assertRaises(FabricError, self.fabric.load, SOURCE, '--', 'load', {
                "xmlids": {
                    "node": True,
                    "edge": None,
                },
            },
        )
        self.assertRaises(FabricError, self.fabric.load, SOURCE, '--', 'load', {
                "features": {
                    "etcbc4": {
                        "node": [ ],
                        "edge": [ ],
                        "region": [ ],
                    },
                },
            },
        )
        self.assertRaises(FabricError, self.fabric.load, SOURCE, '--', 'load', {
                "features": {
                    "etcbc4": {
                        "node": { },
                        "edge": [ ],
                    },
                },
            },
        )
        self.assertRaises(FabricError, self.fabric.load, SOURCE, '--', 'load', {
                "features": {
                    "etcbc4": {
                        "node": [ ],
                        "edge": { },
                    },
                },
            },
        )
        self.assertRaises(FabricError, self.fabric.load, SOURCE, '--', 'load', {
                "features": ('etcbc4:db.oid etcbc4:db.otype', '', ''),
            },
        )
        self.assertRaises(FabricError, self.fabric.load, SOURCE, '--', 'load', {
                "features": ('etcbc4:db.oid etcbc4:db.otype', 'laf:.z'),
            },
        )
        self.assertRaises(FabricError, self.fabric.load, SOURCE, '--', 'load', {
                "prepare": set(),
            },
        )

    @unittest.skipIf(SPECIFIC, SPECIFIC_MSG)
    def test_u600_node_order(self):
        API = self.fabric.load(SOURCE, '--', 'before', {"features": ("otype monads", "")}) 
        NN = API['NN']
        F = API['F']
        BF = API['BF']
        close = API['close']

        def normalize(pairset):return {(y,x) if y < x else (x,y) for (x,y) in pairset}
        
        expected = {(24, 30), (13, 55), (24, 79), (13, 70), (13, 17), (24, 66), (24, 55), (13, 83), (13, 30), (24, 42), (13, 32), (24, 50), (3, 24), (8, 24), (13, 45), (22, 24), (24, 27), (30, 66), (13, 58), (24, 67), (24, 76), (13, 73), (13, 20), (24, 52), (13, 86), (37, 41), (24, 39), (13, 35), (10, 13), (14, 24), (5, 24), (13, 37), (19, 24), (10, 24), (13, 61), (54, 61), (45, 51), (24, 29), (33, 34), (24, 62), (13, 76), (13, 23), (24, 49), (24, 74), (24, 36), (13, 38), (6, 13), (13, 51), (59, 66), (48, 50), (21, 24), (24, 83), (49, 51), (13, 66), (24, 70), (24, 59), (13, 79), (13, 26), (27, 77), (24, 46), (24, 80), (24, 33), (13, 41), (24, 31), (47, 49), (13, 54), (12, 13), (0, 24), (7, 24), (13, 69), (13, 16), (12, 24), (18, 71), (17, 24), (24, 56), (13, 82), (13, 29), (18, 24), (24, 43), (13, 44), (24, 28), (13, 57), (45, 47), (24, 77), (31, 34), (13, 19), (2, 24), (15, 69), (23, 24), (13, 85), (46, 48), (9, 13), (24, 40), (13, 34), (13, 47), (24, 25), (13, 60), (20, 73), (24, 87), (50, 52), (24, 63), (31, 33), (13, 22), (8, 13), (13, 72), (13, 88), (46, 50), (24, 37), (5, 13), (24, 38), (57, 64), (13, 50), (35, 39), (30, 59), (13, 63), (24, 84), (32, 33), (13, 65), (55, 62), (24, 64), (24, 71), (24, 60), (13, 78), (13, 25), (24, 47), (4, 13), (2, 13), (24, 53), (24, 34), (13, 40), (4, 24), (29, 78), (9, 24), (22, 63), (13, 53), (3, 37), (16, 70), (24, 81), (13, 68), (13, 15), (24, 68), (24, 57), (13, 81), (13, 28), (21, 74), (24, 44), (56, 63), (13, 43), (15, 24), (22, 56), (13, 56), (20, 24), (2, 40), (7, 13), (24, 78), (13, 71), (13, 18), (24, 65), (24, 54), (13, 84), (13, 31), (26, 76), (24, 41), (13, 33), (38, 42), (13, 46), (24, 69), (53, 60), (24, 26), (13, 59), (45, 49), (24, 88), (6, 24), (46, 52), (11, 24), (24, 73), (16, 24), (31, 32), (13, 21), (11, 13), (24, 51), (13, 87), (58, 65), (3, 13), (13, 74), (13, 36), (11, 60), (13, 49), (3, 41), (48, 52), (13, 62), (24, 85), (32, 34), (13, 64), (1, 24), (24, 72), (24, 61), (13, 77), (13, 24), (36, 40), (1, 13), (24, 48), (24, 35), (13, 39), (13, 48), (24, 86), (47, 51), (13, 52), (2, 36), (24, 75), (24, 32), (24, 82), (13, 67), (13, 14), (0, 13), (24, 58), (13, 80), (13, 27), (24, 45), (11, 53), (13, 75), (13, 42)}
        self.assertEqual(expected, normalize(expected))

        nones = {(n,m) for n in NN() for m in NN() if n < m and BF(n,m) == None}
        self.assertEqual(expected, nones)
        for (n,m) in nones: self.assertEqual(BF(m,n), None)
        close()

        plain_expected = {(24, 30), (82, 13), (13, 55), (41, 13), (82, 24), (45, 51), (13, 70), (13, 17), (24, 66), (24, 86), (13, 30), (3, 24), (8, 24), (40, 13), (46, 48), (54, 13), (24, 27), (30, 66), (13, 58), (37, 13), (61, 13), (36, 40), (24, 76), (13, 73), (13, 20), (38, 24), (13, 86), (37, 41), (58, 65), (10, 13), (14, 24), (5, 24), (19, 24), (10, 24), (34, 13), (72, 24), (31, 24), (54, 61), (36, 24), (60, 13), (15, 24), (41, 24), (62, 24), (43, 13), (33, 34), (13, 76), (13, 23), (6, 13), (59, 66), (48, 50), (21, 24), (49, 51), (13, 66), (52, 24), (24, 59), (39, 13), (13, 26), (69, 24), (27, 77), (83, 24), (74, 24), (83, 13), (81, 13), (47, 49), (24, 78), (12, 13), (67, 24), (0, 24), (7, 24), (13, 69), (13, 16), (12, 24), (18, 71), (17, 24), (13, 71), (21, 74), (13, 29), (1, 13), (43, 24), (13, 18), (48, 24), (80, 13), (53, 13), (79, 13), (24, 28), (13, 57), (45, 47), (68, 24), (24, 77), (31, 34), (13, 19), (2, 24), (15, 69), (23, 24), (13, 85), (9, 13), (33, 24), (54, 24), (33, 13), (35, 13), (50, 24), (46, 50), (71, 24), (81, 24), (20, 73), (24, 87), (42, 13), (50, 52), (31, 33), (13, 22), (8, 13), (13, 72), (13, 88), (73, 24), (32, 13), (5, 13), (57, 64), (31, 13), (13, 50), (61, 24), (35, 39), (47, 24), (13, 63), (24, 84), (32, 33), (13, 65), (55, 62), (13, 78), (13, 25), (2, 36), (4, 13), (2, 13), (4, 24), (29, 78), (9, 24), (22, 63), (57, 24), (3, 37), (35, 24), (16, 70), (40, 24), (13, 68), (13, 15), (13, 28), (13, 77), (13, 48), (56, 63), (24, 29), (22, 56), (13, 56), (20, 24), (2, 40), (25, 24), (7, 13), (46, 24), (37, 24), (51, 24), (42, 24), (56, 24), (63, 24), (51, 13), (24, 65), (49, 13), (13, 84), (11, 13), (26, 76), (64, 24), (13, 46), (53, 60), (24, 26), (14, 13), (13, 59), (45, 49), (24, 88), (6, 24), (38, 13), (46, 52), (11, 24), (24, 75), (16, 24), (31, 32), (13, 21), (53, 24), (47, 13), (79, 24), (45, 13), (13, 74), (11, 60), (45, 24), (3, 41), (48, 52), (13, 62), (24, 85), (32, 34), (13, 64), (1, 24), (22, 24), (13, 24), (3, 13), (44, 13), (18, 24), (32, 24), (39, 24), (44, 24), (49, 24), (13, 87), (70, 24), (47, 51), (13, 52), (80, 24), (38, 42), (36, 13), (13, 67), (0, 13), (24, 58), (30, 59), (13, 27), (11, 53), (34, 24), (13, 75), (55, 24), (60, 24)}
        self.assertEqual(expected, normalize(plain_expected))

        plain_found = {tuple(NN(test=lambda x: x in {p[0],p[1]})) for p in nones}
        self.assertEqual(plain_expected, plain_found)

        API = self.fabric.load_again({"features": ("otype monads", ""), "prepare": prepare}) 
        NN = API['NN']
        F = API['F']
        BF = API['BF']
        close = API['close']
        
        prep_expected = {(84, 13), (24, 30), (82, 13), (13, 55), (86, 24), (60, 11), (41, 13), (82, 24), (45, 51), (13, 70), (13, 17), (69, 15), (24, 66), (13, 30), (3, 24), (8, 24), (40, 13), (46, 48), (54, 13), (76, 26), (24, 27), (13, 58), (37, 13), (77, 27), (61, 13), (36, 40), (24, 76), (13, 73), (13, 20), (87, 13), (38, 24), (37, 41), (58, 65), (10, 13), (14, 24), (5, 24), (19, 24), (10, 24), (34, 13), (72, 24), (31, 24), (54, 61), (36, 24), (60, 13), (15, 24), (41, 24), (62, 24), (43, 13), (33, 34), (13, 76), (13, 23), (70, 16), (6, 13), (36, 2), (59, 66), (48, 50), (21, 24), (37, 3), (49, 51), (13, 66), (52, 24), (24, 59), (39, 13), (13, 26), (69, 24), (83, 24), (74, 24), (88, 24), (59, 30), (83, 13), (81, 13), (47, 49), (24, 78), (12, 13), (67, 24), (0, 24), (7, 24), (13, 69), (13, 16), (12, 24), (17, 24), (13, 71), (13, 29), (1, 13), (43, 24), (13, 18), (7, 13), (48, 24), (80, 13), (53, 13), (85, 24), (79, 13), (24, 28), (13, 57), (45, 47), (68, 24), (24, 77), (31, 34), (13, 19), (2, 24), (23, 24), (9, 13), (33, 24), (54, 24), (33, 13), (35, 13), (50, 24), (46, 50), (71, 24), (74, 21), (24, 25), (38, 42), (81, 24), (50, 52), (31, 33), (13, 22), (8, 13), (13, 72), (73, 20), (41, 3), (32, 13), (5, 13), (71, 18), (57, 64), (31, 13), (13, 50), (61, 24), (35, 39), (47, 24), (13, 63), (87, 24), (32, 33), (13, 65), (55, 62), (13, 78), (13, 25), (4, 13), (2, 13), (13, 77), (4, 24), (9, 24), (57, 24), (11, 13), (35, 24), (40, 24), (86, 13), (13, 68), (13, 15), (63, 22), (56, 22), (13, 48), (56, 63), (24, 29), (40, 2), (13, 56), (20, 24), (42, 13), (66, 30), (46, 24), (37, 24), (51, 24), (42, 24), (56, 24), (63, 24), (51, 13), (24, 65), (49, 13), (73, 24), (64, 24), (13, 46), (53, 60), (24, 26), (13, 59), (45, 49), (6, 24), (38, 13), (13, 88), (11, 24), (24, 75), (16, 24), (31, 32), (13, 21), (53, 24), (47, 13), (79, 24), (45, 13), (84, 24), (13, 74), (45, 24), (78, 29), (48, 52), (46, 52), (32, 34), (13, 64), (1, 24), (13, 62), (22, 24), (13, 24), (3, 13), (44, 13), (18, 24), (32, 24), (39, 24), (44, 24), (49, 24), (70, 24), (47, 51), (13, 52), (80, 24), (85, 13), (36, 13), (13, 67), (13, 14), (24, 58), (0, 13), (13, 28), (13, 27), (53, 11), (34, 24), (13, 75), (55, 24), (60, 24)}
        self.assertEqual(expected, normalize(prep_expected))

        prep_found = {tuple(NN(test=lambda x: x in {p[0],p[1]})) for p in nones}
        self.assertEqual(prep_expected, prep_found)
        close()

    @unittest.skipIf(SPECIFIC, SPECIFIC_MSG)
    def test_u600_node_order(self):
        API = self.fabric.load(SOURCE, '--', 'before', {"features": ("", "")}) 
        MK = API['MK']
        close = API['close']

        anchors = [set(), {1}, {2}, {3}, {4}, {1,2}, {1,3}, {1,4}, {2,3}, {2,4}, {3,4}, {1,2,3}, {1,2,4}, {1,3,4}, {2,3,4}, {1,2,3,4}]
        ordered_anchors = sorted(anchors, key=MK)
        expected_anchors = [{1, 2, 3, 4}, {1, 2, 3}, {1, 2, 4}, {1, 2}, {1, 3, 4}, {1, 3}, {1, 4}, {1}, {2, 3, 4}, {2, 3}, {2, 4}, {2}, {3, 4}, {3}, {4}, set()]
        self.assertEqual(ordered_anchors, expected_anchors)
        close()
        

if __name__ == '__main__':
    unittest.main()
