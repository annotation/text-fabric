import collections
import sys
from laf.fabric import LafFabric

processor = LafFabric(verbose='DETAIL')

API = processor.load('bhs3.txt.hdr', '--', 'events',
    {
        "xmlids": {"node": False, "edge": False},
        "features": ("otype", ""),
        'primary': True,
    }
)

NE = API['NE']
F = API['F']
msg = API['msg']
outfile = API['outfile']
close = API['close']

mode = sys.argv[1] if len(sys.argv) > 1 else '1'
if mode not in ['1', '2']:
    mode = '1'

msg("Doing mode {}".format(mode))

'''Crude visualization of the embedding structure of nodes based on node events.  '''

out = outfile("output-{}.txt".format(mode))

if mode == '1':

    level = 0
    for (anchor, events) in NE():
        for (node, kind) in events:
            otype = F.otype.v(node)
            event_rep = ''
            if kind == 0:
                event_rep = "{}({}[{}]\n".format("\t"*level, otype, node)
                level += 1
            elif kind == 3:
                level -= 1
                event_rep = "{}{}[{}])\n".format("\t"*level, otype, node)
            elif kind == 1: 
                event_rep = "{}«{}[{}]\n".format("\t"*level, otype, node)
                level += 1
            elif kind == 2:
                level -= 1
                event_rep = "{}{}[{}]»\n".format("\t"*level, otype, node)
            out.write(event_rep)

elif mode == '2':

    for (anchor, events) in NE():
        for (node, kind) in events:
            kindr = '(' if kind == 0 else '«' if kind == 1 else '»' if kind == 2 else ')'
            otype = F.otype.v(node)
            out.write("{} {:>7}: {:<10} {:<7}\n".format(kindr, anchor, otype, node))
close()
