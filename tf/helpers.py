import os,sys

def getModified(paths):
    if type(paths) is str:
        return os.path.getmtime(paths) if os.path.exists(paths) else None
    else:
        lastModified = [getModified(x) for x in paths if getModified(x) != None]
        return None if len(lastModified) == 0 else max(lastModified)

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

def valueFromTf(tf): return '\\'.join(x.replace('\\t','\t').replace('\\n','\n') for x in tf.split('\\\\'))
def tfFromValue(val): return val.replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n')
