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

from ..parameters import OTYPE, OSLOTS, OWORK, OINTERF, OINTERT
from ..core.fabric import FabricCore
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

    Volumes will get a node feature `owork` which maps nodes in the volume to
    nodes in the work.

    !!! note "use of feature owork
        If volumes are combined to a work, nodes in distinct volumes may
        correspond to a single node in the work. In that case, they have the
        same value in the `owork` feature.
        When combining, such nodes are merged into one node in the work,
        with slots the union of the slots of those nodes in the volumes.

        See also `tf.volumes.collect`.

    !!! caution "inter-volume edges"
        Some edge features may link nodes across volumes.
        When creating a volume, we leave out those edges.
        Doing so, we loose information, which prevents us to reinstate
        inter volume edges when we collect volumes.
        That's why we'll save those inter-volume edges in two special features.

    Volumes will also get two node features `ointerfrom` and `ointerto`.

    For each node *f* in the volume, `ointerfrom` has a value composed of
    all work nodes *t* outside the volume that are reached by an edge
    named *e* from *f* with value *val*.

    For each node *t* in the volume, `ointerto` has a value composed of
    all work nodes *f* outside the volume that reach *t* by an edge
    named *e* with value *val*.

    More precisely, the keys of `ointerf` and `ointert` are nodes *nW* of the
    *original work* that correspond with nodes in the volume that have outgoing resp.
    incoming edges to resp. from other volumes.

    Each value of `oninterf` and `ointert` is a semicolon separated list of

    *mW*, *e*, *doValues*, *valueType* , *value*

    where

    *mW* is the node in the *original work* reached by *nW* or that reaches *nW*

    *e* is the name of the edge feature in question

    *doValues* is `v` if the edge feature has values and `x` otherwise

    *valueType* is "i" (int) or "s" (str)

    *value* is the value assigned by the edge feature to the edge from *nW* to *mW*
    or from *mW* to *nW*. If the edge does not have values it is a dummy value `x`.

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

    volumes: dict or tuple
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
        TF = FabricCore(locations=workLocation, silent=silent)
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
    edgeFeatureData = {
        feat: (
            Es(feat).doValues,
            "i" if Es(feat).metadata["valueType"] == "int" else "s",
            Es(feat).data,
            Es(feat).dataInv,
        )
        for feat in Eall()
        if feat != OSLOTS
    }

    nTypeInfo = {}
    for (nType, av, nF, nT) in C.levels.data[0:-1]:
        nTypeInfo[nType] = (nF, nT)

    toplevels = {}

    def getTopLevels():
        nodes = F.otype.s(toplevelType)

        for (i, nW) in enumerate(nodes):
            head = T.sectionFromNode(nW)[0] if byTitle else i + 1
            toplevels[head] = dict(
                firstSlot=L.d(nW, otype=slotType)[0],
                lastSlot=L.d(nW, otype=slotType)[-1],
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
            sV = 0

            heads = v["heads"]

            for head in heads:
                lv = toplevels[head]
                firstSlot = lv["firstSlot"]
                lastSlot = lv["lastSlot"]
                nSlots = lastSlot - firstSlot + 1
                info(f"{toplevelType} {head:<20} with {nSlots} slots")

                for sW in range(firstSlot, lastSlot + 1):
                    sV += 1
                    allSlots.add(sW)
                    owork[sV] = sW
                    allNodes |= set(up[sW - 1])

            indent(level=1)

            allNodes = sorted(allNodes)

            nodesByType = collections.defaultdict(list)
            for nW in allNodes:
                nType = fOtypeData[nW - maxSlot - 1]
                nodesByType[nType].append(nW)

            nV = sV + 1

            indent(level=2)
            for (nType, nodesW) in nodesByType.items():
                startV = nV
                for nW in nodesW:
                    owork[nV] = nW
                    nV += 1
                if DEBUG:
                    info(
                        f"node type {nType:<20}: {startV:>8} - {nV - 1:>8}",
                        tm=False,
                    )
            indent(level=1)

            v[ALLSLOTS] = allSlots
            v[OWORK] = owork
            v[OWORKI] = {m: k for (k, m) in owork.items()}
            info(f"volume {name:<20} with {sV} slots" f" and {len(owork):>8} nodes ...")

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

            for (tp, feat, desc) in (
                ("int", OWORK, "mapping from nodes in the volume to nodes in the work"),
                ("str", OINTERF, "all outgoing inter-volume edges"),
                ("str", OINTERT, "all incoming inter-volume edges"),
            ):
                metaData[feat] = {k: m for (k, m) in metaData[OTYPE].items()}
                metaData[feat]["description"] = desc
                metaData[feat]["valueType"] = tp

            # node features

            nodeFeatures = {}
            v["nodeFeatures"] = nodeFeatures

            nodeFeatures[OWORK] = owork

            otype = {}
            ointerf = {}
            ointert = {}
            nodeFeatures[OTYPE] = otype
            nodeFeatures[OINTERF] = ointerf
            nodeFeatures[OINTERT] = ointert

            # edge features

            edgeFeatures = {}
            v["edgeFeatures"] = edgeFeatures

            oslots = {}
            edgeFeatures[OSLOTS] = oslots

            for (nV, nW) in owork.items():
                otype[nV] = slotType if nW <= maxSlot else fOtypeData[nW - maxSlot - 1]

                if nW > maxSlot:
                    oslots[nV] = set(
                        oworki[s]
                        for s in eOslotsData[nW - maxSlot - 1]
                        if s in allSlots
                    )
                    if not oslots[nV]:
                        error(f"{otype[nV]} node {nV=} {nW=} has no slots", tm=False)

                for (feat, featD) in nodeFeatureData.items():
                    val = featD.get(nW, None)
                    if val is not None:
                        nodeFeatures.setdefault(feat, {})[nV] = val

                for (feat, (doValues, valTp, featF, featT)) in edgeFeatureData.items():
                    # outgoing edges are used to construct the in-volume edge
                    # and the inter-volume outgoing edges
                    valData = featF.get(nW, None)
                    doValuesRep = "v" if doValues else "x"
                    if valData is not None:
                        value = {} if doValues else set()
                        interItems = []

                        for tW in valData:
                            tV = oworki.get(tW, None)
                            if doValues:
                                val = valData[tW]
                            if tV is None:
                                valRep = str(val) if doValues else "x"
                                interItems.append = (
                                    nW,
                                    tW,
                                    feat,
                                    doValuesRep,
                                    valTp,
                                    valRep,
                                )
                            else:
                                if doValues:
                                    value[tV] = val
                                else:
                                    value.add(tV)
                        if value:
                            edgeFeatures.setdefault(feat, {})[nV] = value
                        if interItems:
                            ointerf[nW] = ";".join(
                                ",".join(str(i) for i in item) for item in interItems
                            )
                    # incoming edges are only used to construct
                    # the inter-volume incoming edges

                    valData = featT.get(nW, None)
                    if valData is not None:
                        value = set()
                        interItems = []

                        for fW in valData:
                            fV = oworki.get(fW, None)
                            if fV is None:
                                interItems.append(
                                    (nW, fW, feat, valData[fW])
                                    if doValues
                                    else (nV, fW, feat)
                                )
                        if interItems:
                            ointert[nW] = ";".join(
                                ",".join(item) for item in interItems
                            )

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
            TF = FabricCore(locations=loc, silent=True)
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
