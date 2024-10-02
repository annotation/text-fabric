import sys, collections

import laf
from laf.fabric import LafFabric
from etcbc.preprocess import prepare
fabric = LafFabric()

version = '4b'
API = fabric.load('etcbc{}'.format(version), '--', 'text', {
    "xmlids": {"node": False, "edge": False},
    "features": ('''
    ''',
    '''
    '''),
    "prepare": prepare,
    "primary": False,
}, verbose='NORMAL')
exec(fabric.localnames.format(var='fabric'))

default_style = T.style()
tweak_style = T.style(dict(
    verse_color='00ffff',
    phono_color='ffff00',
    hebrew_color='ff0000',
))

tasks = [
    dict(book=['Exodus','Genesis'], chapter=[7,4,2], verse=[6,3,1]),
    dict(),
    dict(chapter=1),
    dict(verse=1),
    dict(chapter=1, verse=1),
    dict(book='Genesis'),
    dict(book='Genesis', chapter=1),
    dict(book='Genesis', verse=1, chapter=1),
]
def do_tasks():
    i = 0
    for p in tasks:
        bks = [] if 'book' not in p else [p['book']] if type(p['book']) is str else list(p['book'])
        chs = [] if 'chapter' not in p else [p['chapter']] if type(p['chapter']) is int else list(p['chapter'])
        vss = [] if 'verse' not in p else [p['verse']] if type(p['verse']) is int else list(p['verse'])
        for fmt in ['pf', 'ha']:
            for html in [True, False]:
                for lb in [True, False]:
                    for styled in [True, False]:
                        if not styled and not html: continue
                        fname = '{}_{}_{}_{}{}.{}.{}'.format(
                            ''.join(str(bk) for bk in bks) if bks else 'all books',
                            ','.join(str(ch) for ch in chs) if chs else 'all chapters',
                            ','.join(str(vs) for vs in vss) if vss else 'all verses',
                            fmt,
                            '+labels' if lb else '',
                            'default' if styled else 'tweaked',
                            'html' if html else 'txt',
                        )
                        fh = outfile(fname)
                        i += 1
                        print('{:>2} - task {}'.format(i, fname))
                        fh.write(T.text(**p, fmt=fmt, html=html, verse_label=lb, style=default_style if styled else tweak_style))
                        fh.close()

do_tasks()
