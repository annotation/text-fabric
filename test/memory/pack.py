from sys import getsizeof, stderr
from itertools import chain
from collections import deque
from reprlib import repr
from array import array


def deepSize(o, handlers={}, verbose=False, seen=None):
    """Returns the approximate memory footprint an object and all of its contents.

    Automatically finds the contents of the following builtin containers and
    their subclasses:  tuple, list, deque, dict, set and `frozenset`.
    To search other containers, add handlers to iterate over their contents:

        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}

    """

    def dict_handler(d):
        return chain.from_iterable(d.items())

    all_handlers = {
        tuple: iter,
        list: iter,
        deque: iter,
        dict: dict_handler,
        set: iter,
        frozenset: iter,
    }
    all_handlers.update(handlers)  # user handlers take precedence
    if seen is None:
        seen = set()  # track which object id's have already been seen
    default_size = getsizeof(0)  # estimate sizeof object without __sizeof__

    def sizeof(o):
        if id(o) in seen:  # do not double count the same object
            return 0
        seen.add(id(o))
        s = getsizeof(o, default_size)

        if verbose:
            print(s, type(o), repr(o), file=stderr)

        for typ, handler in all_handlers.items():
            if isinstance(o, typ):
                s += sum(map(sizeof, handler(o)))
                break
        return s

    return sizeof(o)


def findStretches(sequence, threshold=1, amount=None):
    default = (((sequence[0], sequence[-1]),), 0)
    if amount == 1:
        return default
    prevN = 1
    gaps = []
    for n in sequence:
        gap = n - prevN
        if gap > 1:
            gaps.append((prevN, n))
        prevN = n
    nInGap = sum(e - b - 1 for (b, e) in gaps if b >= sequence[0] and e <= sequence[-1])
    nTotal = sequence[-1] - sequence[0] + 1
    gapRatio = nInGap / nTotal if nTotal else 0
    gaps = tuple((b, e) for (b, e) in gaps if e - b > threshold)
    if len(gaps) == 0:
        return default
    if amount is not None and len(gaps) > amount:
        gaps = sorted(
            sorted(gaps, key=lambda x: (x[0] - x[1], x[0]))[0:amount],
            key=lambda x: x[0],
        )
    stretches = []
    if sequence[0] <= gaps[0][0]:
        stretches.append((sequence[0], gaps[0][0]))
    for (i, gap) in enumerate(gaps[0:-1]):
        stretches.append((gap[1], gaps[i + 1][0]))
    if sequence[-1] >= gaps[-1][1]:
        stretches.append((gaps[-1][1], sequence[-1]))
    return (stretches, gapRatio)


CONTAINER_TYPE = {
    "dict": dict,
    "tup": tuple,
}
ELEMENT_TYPE = {
    "int": int,
    "str": str,
    "tup": tuple,
}


def pack(origData, containerSpec, elementSpec, threshold=1000, amount=5):
    UTF8 = "utf8"

    containerType = CONTAINER_TYPE[containerSpec]
    elementType = ELEMENT_TYPE[elementSpec]

    isDict = containerType is dict
    isInt = elementType is int
    isStr = elementType is str
    isTup = elementType is tuple

    arraySpecifier = "i"

    if isStr:
        arraySpecifier = "B"

    valueNumber = array("I")
    valueStart = array("I")
    values = array(arraySpecifier)

    vNumber = 0
    vStart = 0
    offsets = []
    origValueIndex = {}

    if isDict:
        valueNumber.append(0)
        valueStart.append(0)
        values.append(0)
        vNumber = 1
        vStart = 1
        origKeys = sorted(origData)
        (stretches, gapRatio) = findStretches(
            origKeys, threshold=threshold, amount=amount
        )

    def addValInt(origVal):
        values.append(origVal)

    def addValStr(origVal):
        nonlocal vStart
        bval = bytes(origVal, encoding=UTF8)
        lval = len(bval)
        values.extend(bval)
        valueStart.append(vStart)
        vStart += lval

    def addValTup(origVal):
        nonlocal vStart
        lval = len(origVal)
        values.extend(origVal)
        valueStart.append(vStart)
        vStart += lval

    addVal = (
        addValStr
        if isStr
        else addValInt
        if isInt
        else addValTup
        if isTup
        else addValInt
    )
    if isDict:
        nKeys = 0
        for (b, e) in stretches:
            offset = b - len(valueNumber)
            offsets.append((b, e, offset))
            for n in range(b, e + 1):
                origVal = origData.get(n, None)
                if origVal is None:
                    valueNumber.append(0)
                else:
                    nKeys += 1
                    thisVNumber = origValueIndex.get(origVal, None)
                    if thisVNumber is None:
                        thisVNumber = vNumber
                        origValueIndex[origVal] = vNumber
                        addVal(origVal)
                        vNumber += 1
                    valueNumber.append(thisVNumber)
    else:
        for origVal in origData:
            thisVNumber = origValueIndex.get(origVal, None)
            if thisVNumber is None:
                thisVNumber = vNumber
                origValueIndex[origVal] = vNumber
                addVal(origVal)
                vNumber += 1
            valueNumber.append(thisVNumber)

    alength = len(valueNumber)
    length = alength
    if isDict:
        offsets = tuple(offsets)
        length = nKeys

    if isStr or isTup:
        valueStart.append(vStart)

    return dict(
        container=containerSpec,
        element=elementSpec,
        valueNumber=valueNumber,
        valueStart=valueStart,
        values=values,
        alength=alength,
        length=length,
        offsets=offsets,
    )


class Pack(object):
    def __init__(self, packedData):
        for (k, v) in packedData.items():
            setattr(self, k, v)
        ctp = self.container
        etp = self.element
        setattr(self, "get", getattr(self, f"get{ctp}{etp}", None))

    def gettupint(self, n):
        valueNumber = self.valueNumber
        values = self.values
        if n >= len(valueNumber):
            return None
        vNumber = valueNumber[n]
        return values[vNumber]

    def gettuptup(self, n):
        valueNumber = self.valueNumber
        valueStart = self.valueStart
        values = self.values
        if n >= len(valueNumber):
            return None
        vNumber = valueNumber[n]
        vStart = valueStart[vNumber]
        vStartNext = valueStart[vNumber + 1]
        return tuple(values[vStart:vStartNext])

    def gettupstr(self, n):
        UTF8 = "utf8"
        valueNumber = self.valueNumber
        valueStart = self.valueStart
        values = self.values
        if n >= len(valueNumber):
            return None
        vNumber = valueNumber[n]
        vStart = valueStart[vNumber]
        vStartNext = valueStart[vNumber + 1]
        return str(values[vStart:vStartNext], encoding=UTF8)

    def getdictint(self, n):
        valueNumber = self.valueNumber
        values = self.values
        offsets = self.offsets
        for (b, e, offset) in offsets:
            if b <= n <= e:
                m = n - offset
                vNumber = valueNumber[m]
                if vNumber == 0:
                    return None
                return values[vNumber]
        return None

    def getdicttup(self, n):
        valueNumber = self.valueNumber
        valueStart = self.valueStart
        values = self.values
        offsets = self.offsets
        for (b, e, offset) in offsets:
            if b <= n <= e:
                m = n - offset
                vNumber = valueNumber[m]
                if vNumber == 0:
                    return None
                vStart = valueStart[vNumber]
                vStartNext = valueStart[vNumber + 1]
                return tuple(values[vStart:vStartNext])
        return None

    def getdictstr(self, n):
        UTF8 = "utf8"
        valueNumber = self.valueNumber
        valueStart = self.valueStart
        values = self.values
        offsets = self.offsets
        for (b, e, offset) in offsets:
            if b <= n <= e:
                m = n - offset
                vNumber = valueNumber[m]
                if vNumber == 0:
                    return None
                vStart = valueStart[vNumber]
                vStartNext = valueStart[vNumber + 1]
                return str(values[vStart:vStartNext], encoding=UTF8)
        return None
