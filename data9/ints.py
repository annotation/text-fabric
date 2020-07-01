from bisect import bisect_left as bl


INTS = dict(
    B=("char", 1, False),
    b=("signed char", 1, True),
    H=("unsigned short", 2, False),
    h=("short", 2, True),
    I=("unsigned int", 4, False),
    i=("int", 4, True),
    Q=("unsigned int", 8, False),
    q=("int", 8, True),
)


def makeBoundaries():
    minpoints = []
    maxpoints = []
    signedmaxpoints = []
    typeindex = {}
    for (tp, (name, nbytes, signed)) in INTS.items():
        topvalue = 256 ** nbytes
        if signed:
            minvalue = topvalue // 2
            maxvalue = topvalue // 2 - 1
        else:
            minvalue = 0
            maxvalue = topvalue - 1
        if signed:
            typeindex[minvalue] = tp
            minpoints.append(minvalue)
            signedmaxpoints.append(maxvalue)
        else:
            maxpoints.append(maxvalue)
        typeindex[maxvalue] = tp
    minpoints = sorted(minpoints)
    maxpoints = sorted(maxpoints)
    signedmaxpoints = sorted(signedmaxpoints)
    typerank = {
        tp: i
        for (i, tp) in enumerate(
            sorted((t for t in INTS if INTS[t][2]), key=lambda t: INTS[t][1])
        )
    }

    def getType(minv, maxv):
        if minv >= 0:
            pos = bl(maxpoints, maxv)
            return None if pos >= len(maxpoints) else typeindex[maxpoints[pos]]
        posmin = bl(minpoints, -minv)
        if posmin >= len(minpoints):
            return None
        if maxv <= 0:
            return typeindex[minpoints[posmin]]
        posmax = bl(signedmaxpoints, maxv)
        if posmax >= len(signedmaxpoints):
            return None
        typemin = typeindex[minpoints[posmin]]
        typemax = typeindex[signedmaxpoints[posmax]]
        return typemin if typerank[typemin] > typerank[typemax] else typemax

    return getType


getIntSpec = makeBoundaries()
