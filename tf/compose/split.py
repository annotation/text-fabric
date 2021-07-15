"""
# Split

## Usage

```python
from tf.compose import split
split(
  sourceLocation,
  splitPositions,
  targetLocation,
)
```

"""

import os
import collections

from ..fabric import Fabric
from ..core.data import WARP
from ..core.timestamp import Timestamp
from ..core.helpers import dirEmpty

OTYPE = WARP[0]
OSLOTS = WARP[1]
OTEXT = WARP[2]

GENERATED = set(
    """
    writtenBy
    dateWritten
    version
""".strip().split()
)

TM = Timestamp()
indent = TM.indent
info = TM.info
warning = TM.warning
error = TM.error
setSilent = TM.setSilent
isSilent = TM.isSilent


def split(
    sourceLocation,
    targetLocation,
    splitPositions=None,
    silent=False,
):
    """Splits a TF data source into volumes.

    The splits will occur at the boundaries of sections of level 1.
    By default, each level 1 section becomes a separate volume.
    Alternatively, you can combine multiple level 1 sections into single volumes
    by using the parameter `splitPositions`.

    Each volume is an ordinary dataset that can be loaded by TF on its own.
    But if volume support in TF is enabled, you can load selections of volumes or
    all volumes together in one session.

    The result of the split is a new dataset at the targetLocation.

    Parameters
    ----------

    sourceLocation: string
        The directory where the dataset resides.

    targetLocation: string
        The directory into which the feature files of the split dataset
        will be written.

    splitPositions: iterable of int, optional `None`
        The sections that start a new volume.
        These sections are given by their sequence number in the enumeration
        of sections of level 1, starting at 1.
        You may or may not include the `1` in the sequence, it will have no effect,
        since the first volume will start at the first section anyway.

    silent: boolean, optional `False`
        Suppress or enable informational messages.

    Example
    -------
        split(
            'clariah-gm/tf/0.8.1',
            'clariah-gm/asvolumes/tf/0.8.1'),
        )

    This will split the corpus into its 13 volumes.

    Example
    -------
        split(
            'clariah-gm/tf/0.8.1',
            'clariah-gm/asvolumes/tf/0.8.1'),
            splitPositions=(1,2,3,4,5,6,7,8)
        )

    This will split the corpus into volumes 1,2,3,4,5,6,7 that contain each exactly
    one subsequent level 1 section. Then comes volume 8 containing all remaining
    sections.

    """

    if not dirEmpty(targetLocation):
        error(
            "Output directory is not empty."
            " Clean it or remove it or choose another location",
            tm=False,
        )
        return False

    def getVolumeSplits():
        pass

    def remapFeatures():
        indent(level=1, reset=True)
        for (i, loc) in locItems:
            info(f"\r{i:>3} {os.path.basename(loc)})", nl=False)
            TF = Fabric(locations=loc, silent=silent)
            api = TF.loadAll(silent=silent)
            if not api:
                return False

            F = api.F
            Fs = api.Fs
            Es = api.Es
            fOtype = F.otype.v

            # node features

            for feat in api.Fall():
                fObj = Fs(feat)
                data = {}
                for (nType, boundaries) in nodeTypesComp.items():
                    if i not in boundaries:
                        continue
                    (nF, nT) = boundaries[i]
                    cType = None
                    thisOffset = offsets[nType][i]
                    for n in range(nF, nT + 1):
                        val = fObj.v(n) if cType is None else cType
                        if val is not None:
                            data[thisOffset + n] = val
                nodeFeatures.setdefault(feat, {}).update(data)

            # edge features

            for feat in api.Eall():
                eObj = Es(feat)
                isOslots = feat == OSLOTS
                edgeValues = False if isOslots else eObj.edgeValues
                data = {}
                for (nType, boundaries) in nodeTypesComp.items():
                    if i not in boundaries:
                        continue
                    cSlots = None
                    if nType == slotType and isOslots:
                        continue
                    (nF, nT) = boundaries[i]
                    thisOffset = offsets[nType][i]
                    for n in range(nF, nT + 1):
                        values = (
                            (eObj.s(n) if cSlots is None else cSlots)
                            if isOslots
                            else eObj.f(n)
                        )
                        nOff = thisOffset + n
                        if edgeValues:
                            newVal = {}
                            for (m, v) in values:
                                mType = fOtype(m)
                                thatOffset = offsets[mType][i]
                                newVal[thatOffset + m] = v
                        else:
                            newVal = set()
                            for m in values:
                                mType = fOtype(m)
                                thatOffset = offsets[mType][i]
                                newVal.add(thatOffset + m)
                        data[nOff] = newVal

                edgeFeatures.setdefault(feat, {}).update(data)

        return True

    def writeTf():
        TF = Fabric(locations=targetLocation, silent=True)
        TF.save(
            metaData=metaData,
            nodeFeatures=nodeFeatures,
            edgeFeatures=edgeFeatures,
            silent=silent or True,
        )
        return True

    def process():
        indent(level=0, reset=True)
        info("compute volume splits ...")
        if not getVolumeSplits():
            return False
        info("remap features ...")
        if not remapFeatures():
            return False
        info("write TF data ...")
        if not writeTf():
            return False
        info("done")
        return True

    wasSilent = isSilent()
    setSilent(silent)
    result = process()
    setSilent(wasSilent)
    return result
