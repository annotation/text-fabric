import sys
from etcbc.emdros import patch

modes = {
    'test': (2, 'bhs4_test', 'etcbc4s_test'),
    'fullb': ('4b', 1000000, 'bhs4', 'bhs4b', 'etcbc4b'),
    'fullc': ('4c', 1000000, 'bhs4', 'bhs4c', 'etcbc4c'),
}

if len(sys.argv) != 3:
    print("Usage\nlf-patch mode workdir \nwhere mode in {}".format(sorted(modes.keys())))
    sys.exit(1)
mode = sys.argv[1]
workdir = sys.argv[2]
if mode not in modes:
    print("Wrong mode [{}]".format(mode))
    print("Usage\nlf-patch mode\nwhere mode in {}".format(sorted(modes.keys())))
    sys.exit(1)

(version, chunk, dbnamei, fnamei, fnameo) = modes[mode]
patch(version, chunk, '{}/{}.mql'.format(workdir, fnamei), '{}/{}.mql'.format(workdir, fnameo), dbnamei, fnameo)
