from array import array
from bisect import bisect_right as br

from ints import getIntSpec

NONE_INT = -1
NONE_STR = "\x00"
NULL = b"\x00"
UTF8 = "utf8"


class PlainString:
    def __init__(self, items):
        """Create data container for (index, string) pairs.

        The pairs must be sorted by index, and no duplicate indices may occur.
        The set of indices must be a set of numbers, not necessarily consecutive.
        The values must be all strings (Unicode UTF8).
        """

        if not items:
            self.offsets = []
            return

        offsets = [0]
        values = [NULL]
        curPos = 1
        prevI = 0

        def addValue(v):
            nonlocal curPos

            offsets.append(curPos)
            vb = v.encode(UTF8)
            values.append(vb)
            curPos += len(vb)

        for (i, v) in items:
            if i != prevI + 1:
                for j in range(prevI + 1, i):
                    addValue(NONE_STR)
            addValue(NONE_STR if v is None else v)
            prevI = i
        offsets.append(curPos)

        self.values = b"".join(values)
        oTp = getIntSpec(min(offsets), max(offsets))
        self.offsets = array(oTp, offsets)
        self.lastValue = len(values) - 1

    def size(self):
        offsets = self.offsets
        values = self.values

        oSize = offsets.itemsize * len(offsets)
        vSize = len(values)
        return f"""{oSize + + vSize:>8}
\t{'offsets':<8}: {offsets.typecode}: {oSize:>8}
\t{'values':<8}: x: {vSize:>8}
"""

    def get(self, index):
        if index < 0:
            return None
        lastValue = self.lastValue
        if index > lastValue:
            return None

        offset = self.offsets[index]
        result = self.values[offset:self.offsets[index + 1]]
        return None if result == NULL else result.decode(UTF8)


class SparseString:
    def __init__(self, items):
        """Create sparse data container for (index, string) pairs.

        The pairs must be sorted by index, and no duplicate indices may occur.
        The set of indices must be a set of numbers, not necessarily consecutive.
        The values must be all strings (Unicode UTF8).

        Only indices where values change are stored.
        """

        if not items:
            self.indices = []
            return

        indices = []
        offsets = []
        bounds = []
        values = [NULL]
        valueMap = {NONE_STR: (0, 1)}
        curPos = 1
        prevV = None
        prevI = None

        def addValue(v):
            nonlocal curPos

            if v in valueMap:
                (offset, bound) = valueMap[v]
                offsets.append(offset)
                bounds.append(bound)
            else:
                offsets.append(curPos)
                vb = v.encode(UTF8)
                bound = curPos + len(vb)
                bounds.append(bound)
                values.append(vb)
                valueMap[v] = (curPos, bound)
                curPos += len(vb)

        for (i, v) in items:
            if prevI is None:
                indices.append(i)
                addValue(v)
            elif i != prevI + 1:
                indices.append(prevI + 1)
                addValue(NONE_STR)
                if v is not None:
                    indices.append(i)
                    addValue(v)
            elif prevV != v:
                indices.append(i)
                addValue(v)
            prevV = v
            prevI = i
        if prevV is not None:
            indices.append(prevI + 1)
            addValue(NONE_STR)

        offsets.append(curPos)
        self.values = b"".join(values)

        iTp = getIntSpec(min(indices), max(indices))
        self.indices = array(iTp, indices)
        self.nIndices = len(indices)
        oTp = getIntSpec(min(offsets), max(offsets))
        self.offsets = array(oTp, offsets)
        bTp = getIntSpec(min(bounds), max(bounds))
        self.bounds = array(bTp, bounds)

    def size(self):
        indices = self.indices
        offsets = self.offsets
        bounds = self.bounds
        values = self.values

        iSize = indices.itemsize * len(indices)
        oSize = offsets.itemsize * len(offsets)
        bSize = bounds.itemsize * len(bounds)
        vSize = len(values)
        return f"""{iSize + oSize + + bSize + vSize:>8}
\t{'indices':<8}: {indices.typecode}: {iSize:>8}
\t{'offsets':<8}: {offsets.typecode}: {oSize:>8}
\t{'bounds':<8}: {bounds.typecode}: {bSize:>8}
\t{'values':<8}: x: {vSize:>8}
"""

    def get(self, index):
        nIndices = self.nIndices

        pos = br(self.indices, index)
        if pos == 0:
            return None
        pos = nIndices - 1 if pos > nIndices else pos - 1

        offset = self.offsets[pos]
        if offset == 0:
            return None
        return self.values[offset:self.bounds[pos]].decode(UTF8)


class PlainInt:
    def __init__(self, items):
        """Create data container for (index, value) pairs.

        The pairs must be sorted by index, and no duplicate indices may occur.
        The set of indices must be a set of numbers, not necessarily consecutive.
        The values must be all integers (negatives allowed).
        """

        if not items:
            self.values = []
            return

        values = [NONE_INT]
        prevI = 0

        def addValue(v):
            values.append(v)

        for (i, v) in items:
            if i != prevI + 1:
                for j in range(prevI + 1, i):
                    addValue(NONE_INT)
            values.append(NONE_INT if v is None else v - 1 if v < 0 else v)
            prevI = i

        vTp = getIntSpec(min(values), max(values))
        self.values = array(vTp, values)
        self.lastValue = len(values) - 1

    def size(self):
        values = self.values

        vSize = values.itemsize * len(values)
        return f"""{vSize:>8}
\t{'values':<8}: {values.typecode}: {vSize:>8}
"""

    def get(self, index):
        if index < 0:
            return None
        lastValue = self.lastValue
        if index > lastValue:
            return None
        v = self.values[index]
        return None if v is NONE_INT else v + 1 if v < 0 else v


class SparseInt:
    def __init__(self, items):
        """Create sparse data container for (index, value) pairs.

        The pairs must be sorted by index, and no duplicate indices may occur.
        The set of indices must be a set of numbers, not necessarily consecutive.
        The values must be all integers (negatives allowed).

        Only indices where values change are stored.
        """

        if not items:
            self.indices = []
            return

        indices = []
        values = []
        prevV = None
        prevI = None

        for (i, v) in items:
            if prevI is None:
                indices.append(i)
                values.append(v - 1 if v < 0 else v)
            elif i != prevI + 1:
                indices.append(prevI + 1)
                values.append(NONE_INT)
                if v is not None:
                    indices.append(i)
                    values.append(v - 1 if v < 0 else v)
            elif prevV != v:
                indices.append(i)
                values.append(v - 1 if v < 0 else v)
            prevV = v
            prevI = i
        if prevV is not NONE_INT:
            indices.append(prevI + 1)
            values.append(NONE_INT)

        iTp = getIntSpec(min(indices), max(indices))
        self.indices = array(iTp, indices)
        self.nIndices = len(indices)
        vTp = getIntSpec(
            min(values),
            max(values),
        )
        self.values = array(vTp, values)

    def size(self):
        indices = self.indices
        values = self.values

        iSize = indices.itemsize * len(indices)
        vSize = values.itemsize * len(values)
        return f"""{iSize + vSize:>8}
\t{'indices':<8}: {indices.typecode}: {iSize:>8}
\t{'values':<8}: {values.typecode}: {vSize:>8}
"""

    def get(self, index):
        nIndices = self.nIndices

        pos = br(self.indices, index)
        if pos == 0:
            return None
        pos = nIndices - 1 if pos > nIndices else pos - 1

        v = self.values[pos]
        return None if v is NONE_INT else v + 1 if v < 0 else v
