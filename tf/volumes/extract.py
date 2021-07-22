"""
# Extract

## Usage

```python
from tf.volumes import extract
extract(
  workLocation,
  volumesLocation,
  volumes=None or dict of top-level section titles/numbers
)
```

"""

import collections
from shutil import rmtree

from ..fabric import Fabric
from ..parameters import OTYPE, OSLOTS, OWORK
from ..core.timestamp import Timestamp
from ..core.helpers import dirEmpty, unexpanduser

DEBUG = False
OWORKI = "oworki"
ALLSLOTS = "allSlots"

TM = Timestamp()
indent = TM.indent
info = TM.info
warning = TM.warning
error = TM.error
setSilent = TM.setSilent
isSilent = TM.isSilent


def extract(
    workLocation,
    volumesLocation,
    byTitle=True,
    volumes=None,
    silent=False,
    api=None,
    overwrite=False,
):
    """Extracts volumes of a work.

    The volumes are new TF data sets, the work is an existing TF data set.
    Volumes of a work consist of collections of its top-level sections.

    You can define volumes by passing a volume specification.
    If no specification is given, a volume will be created for every single
    top-level section.

    Volumes will get a feature `owork` which maps nodes in the volume to
    nodes in the work.

    !!! note "use of feature owork
        If volumes are combined to a work, nodes in distinct volumes may
        correspond to a single node in the work. In that case, they have the
        same value in the `owork` feature.
        When combining, such nodes are merged into one node in the work,
        with slots the union of the slots of those nodes in the volumes.

        See also `tf.volumes.collect`.

    Parameters
    ----------

    workLocation: string
        The directory where the dataset resides.

    volumesLocation: string
        The directory under which the feature files of the volumes
        will be written.

    byTitle: boolean, optional `True`
        Whether the top-level sections are named by their sequence numbers
        (starting at 1).
        or by their titles.
        Default: by their titles.
        Note, that depending on the work, section titles may be strings or integers.

    volumes: dict or tuple of (string or tuple)
        If not given or None, extracts all top-level sections into separate volumes.
        If given, it must be dict or tuple.

        If it is a dict, the keys are names for the volumes, and the values
        are iterables of top-level sections that make up the volumes.

        If it is a tuple, each member is an iterable of top-level sections that
        belong to that volume.
        In this case, each volume gets a generated name.

        The top-level sections must be specified by their title if
        `byTitle` is True, else by their sequence number.

        If names for volumes have to be generated,
        they will consist of the top-level section specifications, separated by a "-".

    silent: boolean, optional `False`
        Suppress or enable informational messages.

    api: object, optional `None`
        If given, assume it is the TF api of a loaded work
        from which the volumes are to be extracted.
        In this case, the `workLocation` parameter is not used.
        If absent or `None`, the dataset at `workLocation`
        will be loaded by Text-Fabric, and its api will be used subsequently.

    overwrite: boolean, optional `False`
        If True, overwrites volume directories by cleaning them first.
        If False, refuses to proceed if a volume directory already exists.

    Returns
    -------
    dict
        For each new volume an item,
        whose key is the name of the volume and whose value is its location
        on disk.

    Example
    -------
        volumeList = extract(
            'clariah-gm/tf/0.9.1',
            'clariah-gm/asvolumes/tf/0.9.1',
        )

    This will extract the top-level sections of the missives corpus
    into that many volumes.

    Example
    -------
        volumeList = extract(
            'clariah-gm/tf/0.9.1',
            'clariah-gm/asvolumes/tf/0.9.1',
            volumes=dict(
                early=(1,2,3,4,5,6,7,8),
                late=(9, 10, 11, 12),
            )
        )

    This will create 2 volumes, named `early` and `late`,
    where `early` consists of top-level sections 1-8,
    and `late` consists of top-level sections 9-12.
    Top-level section 13 will not be extracted into a volume.

    Example
    -------
        volumeList = extract(
            'bhsa/tf/2021',
            'bhsa/asvolumes/tf/2021',
        )

    This will extract the books of the bible as separate volumes.

    Example
    -------
        volumeList = extract(
            'bhsa/tf/2021',
            'bhsa/asvolumes/tf/2021',
            volumes=dict(
                thora=("Genesis", "Exodus", "Leviticus", "Numeri", "Deuteronomy"),
                poetry=("Psalms", "Proverbs"),
            ),
        )

    This will extract two volumes of the bible:
    `thora` with the first 5 books and `poetry` with two poetic books.
    """

    if api:
        TF = api.TF
    else:
        TF = Fabric(locations=workLocation, silent=silent)
        api = TF.loadAll(silent=silent)

    if not api:
        return False

    T = getattr(api, "T", None)
    if T is None:
        error("This work has no Text-API", tm=False)
        return False

    sectionTypes = T.sectionTypes
    if not sectionTypes:
        error("This work has no section levels", tm=False)
        return False

    toplevelType = sectionTypes[0]

    E = api.E
    Eall = api.Eall
    Es = api.Es
    F = api.F
    Fall = api.Fall
    Fs = api.Fs
    L = api.L
    C = api.C

    slotType = F.otype.slotType
    maxSlot = E.oslots.maxSlot
    fOtypeData = F.otype.data
    eOslotsData = E.oslots.data

    allFeatures = tuple(feat for feat in TF.features if not TF.features[feat].method)

    metaDataTotal = {feat: TF.features[feat].metaData for feat in allFeatures}
    nodeFeatureData = {feat: Fs(feat).data for feat in Fall() if feat != OTYPE}
    edgeFeatureDataV = {
        feat: Es(feat).data for feat in Eall() if feat != OSLOTS and Es(feat).doValues
    }
    edgeFeatureData = {
        feat: Es(feat).data
        for feat in Eall()
        if feat != OSLOTS and not Es(feat).doValues
    }

    nTypeInfo = {}
    for (nType, av, nF, nT) in C.levels.data[0:-1]:
        nTypeInfo[nType] = (nF, nT)

    toplevels = {}

    def getTopLevels():
        nodes = F.otype.s(toplevelType)

        for (i, n) in enumerate(nodes):
            head = T.sectionFromNode(n)[0] if byTitle else i + 1
            toplevels[head] = dict(
                firstSlot=L.d(n, otype=slotType)[0],
                lastSlot=L.d(n, otype=slotType)[-1],
            )

        info(f"Work consists of {len(toplevels)} {toplevelType}s:", tm=False)
        indent(level=1, reset=True)

        for (head, lv) in toplevels.items():
            firstSlot = lv["firstSlot"]
            lastSlot = lv["lastSlot"]
            nSlots = lastSlot - firstSlot + 1
            info(
                f"{toplevelType} {head:<20}: with {nSlots:>8} slots",
                tm=False,
            )
        indent(level=0)
        return True

    def checkVolumes():
        nonlocal volumes

        info("Check volumes ...")

        if volumes is None:
            volumes = {head: dict(heads=(head,)) for head in toplevels}
        else:
            if type(volumes) is tuple:
                volumes = {
                    "-".join(str(head) for head in heads): dict(heads=heads)
                    for heads in volumes
                }

            good = True
            errors = set()

            for (name, v) in volumes.items():
                thisGood = True
                heads = v["heads"]
                if not heads:
                    error("Empty volumes not allowed")
                    thisGood = False
                    continue
                for head in heads:
                    if head not in toplevels:
                        errors.add(head)
                        thisGood = False
                if not thisGood:
                    good = False

            if errors:
                extra = "title" if byTitle else "number"
                for head in sorted(errors):
                    error(f"No such {toplevelType} {extra}: {head}")

            if not good:
                return None

        for name in volumes:
            loc = f"{volumesLocation}/{name}"
            if not dirEmpty(loc):
                if overwrite:
                    rmtree(loc)
                else:
                    error(
                        f"Volume directory is not empty: {unexpanduser(loc)}"
                        " Clean it or remove it or choose another location",
                        tm=False,
                    )
                    good = False

        if not good:
            return None

        indent(level=0)
        info("volumes ok")

    def distributeNodes():
        info("Distribute nodes over volumes ...")
        indent(level=1, reset=True)
        up = C.levUp.data

        for (name, v) in volumes.items():
            info(f"volume {name} ...")
            indent(level=2, reset=True)

            owork = {}
            allNodes = set()
            allSlots = set()
            curSlot = 0

            heads = v["heads"]

            for head in heads:
                lv = toplevels[head]
                firstSlot = lv["firstSlot"]
                lastSlot = lv["lastSlot"]
                nSlots = lastSlot - firstSlot + 1
                info(f"{toplevelType} {head:<20} with {nSlots} slots")

                for s in range(firstSlot, lastSlot + 1):
                    curSlot += 1
                    allSlots.add(s)
                    owork[curSlot] = s
                    allNodes |= set(up[s - 1])

            indent(level=1)

            allNodes = sorted(allNodes)

            nodesByType = collections.defaultdict(list)
            for n in allNodes:
                nType = fOtypeData[n - maxSlot - 1]
                nodesByType[nType].append(n)

            curNode = curSlot + 1

            indent(level=2)
            for (nType, nodes) in nodesByType.items():
                startNode = curNode
                for n in nodes:
                    owork[curNode] = n
                    curNode += 1
                if DEBUG:
                    info(
                        f"node type {nType:<20}: {startNode:>8} - {curNode - 1:>8}",
                        tm=False,
                    )
            indent(level=1)

            v[ALLSLOTS] = allSlots
            v[OWORK] = owork
            v[OWORKI] = {m: k for (k, m) in owork.items()}
            info(
                f"volume {name:<20} with {curSlot} slots"
                f" and {len(owork):>8} nodes ..."
            )

        indent(level=0)
        info("distribution done")
        return True

    def remapFeatures():
        info("Remap features ...")
        indent(level=1, reset=True)

        for (name, v) in volumes.items():
            owork = v[OWORK]
            oworki = v[OWORKI]
            allSlots = v[ALLSLOTS]

            info(f"volume {name} with {len(owork):>8} nodes ...")

            # metadata

            metaData = {}
            v["metaData"] = metaData

            for (feat, meta) in metaDataTotal.items():
                metaData[feat] = {k: m for (k, m) in meta.items()}
                metaData[feat]["volume"] = name

            metaData[OWORK] = {k: m for (k, m) in metaData[OTYPE].items()}
            metaData[OWORK][
                "description"
            ] = "mapping from nodes in the volume to nodes in the work"
            metaData[OWORK]["valueType"] = "int"

            # node features

            nodeFeatures = {}
            v["nodeFeatures"] = nodeFeatures

            otype = {}
            nodeFeatures[OTYPE] = otype
            nodeFeatures[OWORK] = owork

            # edge features

            edgeFeatures = {}
            v["edgeFeatures"] = edgeFeatures

            oslots = {}
            edgeFeatures[OSLOTS] = oslots

            for (nP, n) in owork.items():
                otype[nP] = slotType if n <= maxSlot else fOtypeData[n - maxSlot - 1]

                if n > maxSlot:
                    oslots[nP] = set(
                        oworki[s] for s in eOslotsData[n - maxSlot - 1] if s in allSlots
                    )
                    if not oslots[nP]:
                        error(f"{otype[nP]} node {nP=} {n=} has no slots", tm=False)

                for (feat, featD) in nodeFeatureData.items():
                    val = featD.get(n, None)
                    if val is not None:
                        nodeFeatures.setdefault(feat, {})[nP] = val

                for (feat, featD) in edgeFeatureData.items():
                    valData = featD.get(n, None)
                    if valData is not None:
                        value = frozenset(oworki[t] for t in valData if t in oworki)
                        if value:
                            edgeFeatures.setdefault(feat, {})[nP] = value
                for (feat, featD) in edgeFeatureDataV.items():
                    valData = featD.get(n, None)
                    if valData is not None:
                        for (t, val) in valData.items():
                            tP = oworki.get(t, None)
                            if tP is not None:
                                edgeFeatures.setdefault(feat, {}).setdefault(nP, {})[
                                    tP
                                ] = val

        indent(level=0)
        info("remapping done")
        return True

    def writeTf():
        info("Write volumes as TF datasets")
        indent(level=1, reset=True)

        for (name, v) in volumes.items():
            info(f"Writing volume {name}")
            metaData = v["metaData"]
            nodeFeatures = v["nodeFeatures"]
            edgeFeatures = v["edgeFeatures"]
            loc = f"{volumesLocation}/{name}"
            v["loc"] = loc
            TF = Fabric(locations=loc, silent=True)
            TF.save(
                metaData=metaData,
                nodeFeatures=nodeFeatures,
                edgeFeatures=edgeFeatures,
                silent=False if DEBUG else silent or True,
            )
        indent(level=0)
        info("writing done")
        return True

    def process():
        nonlocal volumes

        indent(level=0, reset=True)
        if not getTopLevels():
            return False
        volumes = checkVolumes()
        if volumes is None:
            return False
        if not distributeNodes():
            return False
        if not remapFeatures():
            return False
        if not writeTf():
            return False
        info("All done")
        return {name: v["loc"] for (name, v) in volumes.items()}

    wasSilent = isSilent()
    setSilent(silent)
    result = process()
    setSilent(wasSilent)
    return result
