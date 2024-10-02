import sys
import collections

import laf
from laf.fabric import LafFabric
from etcbc.preprocess import prepare
fabric = LafFabric()

version = '4b'
API = fabric.load('etcbc{}'.format(version), ['lexicon','complements','para'], 'test', {
    "xmlids": {"node": False, "edge": False},
    "features": ('''
        otype gn
        phono
        semantic
        pargr
    ''',
    '''
    '''),
    "prepare": prepare,
    "primary": False,
}, verbose='DETAIL')
exec(fabric.localnames.format(var='fabric'))

print(L.p('word', book=None, chapter=1, verse=1, sentence=1, clause=1, phrase=1))
