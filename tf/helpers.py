import sys

OTYPE = 'otype'
MONADS = 'monads'

def error(msg, line=None):
    sys.stderr.write('{}{}\n'.format('ERROR at line {}: '.format(line) if line != None else '', msg))
    sys.stderr.flush()

def setFromSpec(spec):
    covered = set()
    for r_str in spec.split(','):
        bounds = r_str.split('-')
        if len(bounds) == 1:
            covered.add(int(r_str))
        else:
            b = int(bounds[0])
            e = int(bounds[1])
            if (e < b): (b, e) = (e, b)
            for n in range(b, e+1): covered.add(n)
    return covered

def rangesFromSet(nodeSet):
    ranges = []
    curstart = None
    curend = None
    for n in sorted((nodeSet)):
        if curstart == None:
            curstart = n
            curend = n
        elif n == curend + 1:
            curend = n
        else:
            ranges.append((curstart, curend))
            curstart = n
            curend = n
    if curstart != None:
        ranges.append((curstart, curend))
    return ranges

def specFromRanges(ranges): # ranges must be normalized
    return ','.join('{}'.format(r[0]) if r[0] == r[1] else '{}-{}'.format(*r) for r in ranges)

valueFromTf = lambda tf: '\\'.join(x.replace('\\t','\t').replace('\\n','\n') for x in tf.split('\\\\'))
tfFromValue = lambda val: val.replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n')

def averageMonadLength(otype, monads, monadType):
    otypeCount = collections.Counter()
    monadSetLengths = collections.Counter()
    for n in otype:
        ntp = otype[n]
        otypeCount[ntp] += 1
        monadSetLengths[ntp] += len(monads[n]) if ntp != monadType else 1 
    return sorted(
        ((otype, monadSetLengths[otype]/otypeCount[otype]) for otype in otypeCount),
        key=lambda x: -x[1],
    )

# if reading edges, you can opt to ignore the values, and construct sets instead of dictionaries
# handy for the monads edge feature, which is big, and is not supposed to have values

