import collections
import functools
import array
from .lib import monad_set, object_rank
from .layer import Layer
from .text import Text

ETCBCREF = 'http://laf-fabric.readthedocs.org/en/latest/texts/ETCBC-reference.html'

otypes = (
    'book',
    'chapter',
    'verse',
    'half_verse',
    'sentence',
    'sentence_atom',
    'clause',
    'clause_atom',
    'phrase',
    'phrase_atom',
    'subphrase',
    'word',
)

def node_order(API):
    API['fabric'].load_again({"features": ('db.otype db.monads db.minmonad db.maxmonad', '')}, add=True)
    msg = API['msg']
    F = API['F']
    NN = API['NN']

    def before(a,b):
        sa = monad_set(F.db_monads.v(a))
        sb = monad_set(F.db_monads.v(b))
        oa = object_rank[F.db_otype.v(a)]
        ob = object_rank[F.db_otype.v(b)]
        if sa == sb: return 0 if oa == ob else -1 if oa < ob else 1
        if sa < sb: return 1
        if sa > sb: return -1
        am = min(sa - sb)
        bm = min(sb - sa)
        return -1 if am < bm else 1 if bm < am else None

    etcbckey = functools.cmp_to_key(before)
    msg('SORTING nodes ...')
    nodes = sorted(NN(), key=etcbckey)
    return array.array('I', nodes)

def node_order_inv(API):
    msg = API['msg']
    msg('SORTING nodes (inv) ...', verbose='NORMAL')
    make_array_inverse = API['make_array_inverse']
    data_items = API['data_items']
    return make_array_inverse(data_items['zG00(node_sort)'])


Lu = {}
Ld = {}

def getmonads(attr):
    ranges = attr.split(',')
    covered = set()
    for r in ranges:
        if '-' in r:
            (start, end) = r.split('-', 1)
            for i in range(int(start), int(end)+1): covered.add(i)
        else:
            covered.add(int(r))
    return covered

def fill(NN, F, er, ed):
    cur_min = None
    cur_max = None
    cur_ers = collections.deque()
    skip_ed = None
    for n in NN():
        otype = F.db_otype.v(n)
        if otype == er:
            this_er = n
            this_min = int(F.db_minmonad.v(n))
            this_max = int(F.db_maxmonad.v(n))
            this_monads = getmonads(F.db_monads.v(n))
            while len(cur_ers):
                if cur_ers[0][2] < this_min:
                    cur_ers.popleft()
                else:
                    break
            cur_ers.append((this_er, this_min, this_max, this_monads))
            cur_max = max(x[2] for x in cur_ers)
            cur_min = min(x[1] for x in cur_ers)
            skip_ed = False
        elif otype in ed:
            if len(cur_ers) > 0:
                if not skip_ed:
                    this_min = int(F.db_minmonad.v(n))
                    this_max = int(F.db_maxmonad.v(n))
                if this_min > cur_max:
                    skip_ed = True
                if this_max <= cur_max:
                    this_monads = getmonads(F.db_monads.v(n))
                    for (that_er, that_min, that_max, that_monads) in cur_ers:
                        if  this_monads <= that_monads:
                            Lu.setdefault(er, {})[n] = that_er
                            Ld.setdefault(otype, {}).setdefault(that_er, []).append(n)

def node_ud(API):
    API['fabric'].load_again({"features": ('db.otype db.monads db.minmonad db.maxmonad', '')}, add=True)
    msg = API['msg']
    F = API['F']
    NN = API['NN']
    lower_types = set(otypes)
    for t in otypes:
        msg("Objects contained in {}s".format(t), verbose='NORMAL')
        lower_types.remove(t)
        fill(NN, F, t, lower_types)

def node_up(API):
    if len(Lu) == 0: node_ud(API)
    return Lu

def node_down(API):
    if len(Ld) == 0: node_ud(API)
    return Ld

def verses(API):
    API['fabric'].load_again({"features": ('db.otype sft.book sft.chapter sft.verse', '')}, add=True)
    msg = API['msg']
    F = API['F']
    NN = API['NN']
    verses = {}
    n = 0
    msg('Making verse index', verbose='NORMAL')
    for vn in F.db_otype.s('verse'):
        n += 1
        bk = Lu['book'][vn]
        ch = int(F.sft_chapter.v(vn))
        vs = int(F.sft_verse.v(vn))
        verses.setdefault(bk, {}).setdefault(ch, {})[vs] = vn
    msg('Done. {} verses'.format(n), verbose='NORMAL')
    return verses

def books_la(API):
    msg = API['msg']
    F = API['F']
    msg('Listing books', verbose='NORMAL')
    books = tuple((b, F.sft_book.v(b)) for b in F.db_otype.s('book'))
    msg('Done. {} books'.format(len(books), verbose='NORMAL'))
    return books

def prep_post(biblang='Hebrew', select=None):
    def p(lafapi):
        lafapi.stamp.Nmsg('ETCBC reference: {}'.format(ETCBCREF))
        if select == None or 'L' in select: lafapi.api['L'] = Layer(lafapi)
        if select == None or 'T' in select: lafapi.api['T'] = Text(lafapi, biblang=biblang)
    return p
    
prepare_dict = collections.OrderedDict((
    ('zG00(node_sort)', (node_order, __file__, True, 'etcbc')),
    ('zG00(node_sort_inv)', (node_order_inv, __file__, True, 'etcbc')),
    ('zL00(node_up)', (node_up, __file__, False, 'etcbc')),
    ('zL00(node_down)', (node_down, __file__, False, 'etcbc')),
    ('zV00(verses)', (verses, __file__, False, 'etcbc')),
    ('zV00(books_la)', (books_la, __file__, False, 'etcbc')),
))

def prep(biblang='Hebrew', select=None):
    return (prepare_dict, prep_post(biblang=biblang, select=select))

prepare = (prepare_dict, prep_post(biblang='Hebrew'))
