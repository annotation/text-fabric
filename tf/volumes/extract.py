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
from ..core.helpers import dirEmpty, unexpanduser as ux, getAllFeatures

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
    volumes,
    byTitle=True,
    silent=False,
    api=None,
    overwrite=None,
    checkOnly=False,
):
    """Extracts volumes of a work.

    The volumes are new TF data sets, the work is an existing TF data set.
    Volumes of a work consist of collections of its top-level sections.

    You can define volumes by passing a volume specification.
    If the specification `True` is given, a volume will be created for every single
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

    !!! caution "inter-version edges"
        Features with names starting in `omap@` contain node maps from
        older to newer versions.
        These will be excluded from volumes.

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

    volumes: boolean or dict or set
        If True, extracts all top-level sections into separate volumes.

        If it is a dict, the keys are names for the volumes, and the values
        are tuples or lists of top-level sections that make up the volumes.

        If it is a set, each member is an tuple of top-level sections that
        belong to that volume.
        In this case, each volume gets a generated name.

        The top-level sections must be specified by their title if
        `byTitle` is True, else by their sequence number.

        If names for volumes have to be generated,
        they will consist of the top-level section specifications, separated by a "-".

        !!! caution "Disjointness"
            All volumes must be disjoint, they cannot have top-level sections
            in common.

    byTitle: boolean, optional `True`
        Whether the top-level sections are named by their sequence numbers
        (starting at 1).
        or by their titles.
        Default: by their titles.
        Note, that depending on the work, section titles may be strings or integers.

    silent: boolean, optional `False`
        Suppress or enable informational messages.

    api: object, optional `None`
        If given, assume it is the TF api of a loaded work
        from which the volumes are to be extracted.
        In this case, the `workLocation` parameter is not used.
        If absent or `None`, the dataset at `workLocation`
        will be loaded by Text-Fabric, and its api will be used subsequently.

    overwrite: boolean, optional `None`
        If True, the volumes defined by `volumes` will be
        all be created and will replace any existing volumes of the same names.
        If None, only missing volumes will be created. No check will be performed
        as to whether existing volumes conform to the volume specifications.
        If False, refuses to proceed if any of the volume directories already exist.

    checkOnly: boolean, optional `False`
        If True, only checks whether there is work to do based on the values
        of the `volumes` and `overwrite` parameters.
        If there is an error, returns False, otherwise returns the volumes in as
        far as they have to be extracted.


    Returns
    -------
    dict
        For each volume an item,
        whose key is the name of the volume and whose value is a dict with
        items `location` (on disk) and `new` (whether the volume has been created
        by this call).

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

    volumeData = {}

    def checkVolumeLocs():
        good = True

        removable = set()
        for name in volumeData:
            loc = f"{volumesLocation}/{name}"
            if not dirEmpty(loc):
                if overwrite is None:
                    info(
                        f"Volume {name} already exists and will not be recreated",
                        tm=False,
                    )
                    removable.add(name)
                else:
                    if overwrite:
                        rmtree(loc)
                        info(f"Volume {name} exists and will be recreated", tm=False)
                    else:
                        good = False
                        error(
                            f"Volume {name} already exists in {ux(loc)}",
                            tm=False,
                        )
        for name in removable:
            del volumeData[name]
        return good

    def checkVolumes():
        info("Check volumes ...")
        indent(level=1)

        good = True
        if volumes is not True:
            if type(volumes) is dict:
                for (name, heads) in volumes.items():
                    volumeData[name] = dict(heads=heads)
            else:
                for heads in volumes:
                    volumeData["-".join(str(head) for head in heads)] = dict(
                        heads=heads
                    )

            headIndex = {}

            for (name, v) in volumeData.items():
                heads = v["heads"]
                if not heads:
                    error("Empty volumes not allowed")
                    good = False
                    continue
                for head in heads:
                    seenName = headIndex.get(head, None)
                    if seenName:
                        error(
                            f"Section {head} of volume {seenName}"
                            f" reoccurs in volume {name}")
                        good = False
                    headIndex[head] = name

            if good:
                good = checkVolumeLocs()
        return good

    def checkVolumes2():
        if volumes is True:
            for head in toplevels:
                volumeData[head] = dict(heads=(head,))
            if not checkVolumeLocs():
                return False

        good = True
        errors = set()

        for (name, v) in volumeData.items():
            thisGood = True
            for head in v["heads"]:
                if head not in toplevels:
                    errors.add(head)
                    thisGood = False
            if not thisGood:
                good = False

        if errors:
            extra = "title" if byTitle else "number"
            for head in sorted(errors):
                error(f"No such {toplevelType} {extra}: {head}")

        indent(level=0)
        if good:
            info("volumes ok")
        return good

    if api:
        TF = api.TF
    else:
        TF = FabricCore(locations=workLocation, silent=silent)
        api = TF.load("", silent=silent) if checkOnly else TF.loadAll(silent=silent)

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

    allFeatures = getAllFeatures(api)

    metaDataTotal = {feat: TF.features[feat].metaData for feat in allFeatures}
    nodeFeatureData = {
        feat: Fs(feat).data for feat in Fall() if feat != OTYPE and feat in allFeatures
    }
    edgeFeatureData = {
        feat: (
            Es(feat).doValues,
            "i" if Es(feat).meta["valueType"] == "int" else "s",
            Es(feat).data,
            Es(feat).dataInv,
        )
        for feat in Eall()
        if feat != OSLOTS and feat in allFeatures
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

    def distributeNodes():
        info("Distribute nodes over volumes ...")
        indent(level=1, reset=True)
        up = C.levUp.data

        for (name, v) in volumeData.items():
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

        for (name, v) in volumeData.items():
            owork = v[OWORK]
            oworki = v[OWORKI]
            allSlots = v[ALLSLOTS]

            info(f"volume {name} with {len(owork):>8} nodes ...")

            # metadata

            metaData = {}
            v["metaData"] = metaData
            headStr = "-".join(str(head) for head in v["heads"])
            volumeMeta = name if headStr == name else f"{name}:{headStr}"

            for (feat, meta) in metaDataTotal.items():
                metaData[feat] = {k: m for (k, m) in meta.items()}
                metaData[feat]["volume"] = volumeMeta

            for (tp, feat, desc) in (
                ("int", OWORK, "mapping from nodes in the volume to nodes in the work"),
                ("str", OINTERF, "all outgoing inter-volume edges"),
                ("str", OINTERT, "all incoming inter-volume edges"),
            ):
                metaData[feat] = {k: m for (k, m) in metaData[OTYPE].items()}
                metaData[feat]["description"] = desc
                metaData[feat]["valueType"] = tp

            # node features

            nodeFeatures = {feat: {} for feat in nodeFeatureData}
            v["nodeFeatures"] = nodeFeatures

            nodeFeatures[OWORK] = owork

            otype = {}
            ointerf = {}
            ointert = {}
            nodeFeatures[OTYPE] = otype
            nodeFeatures[OINTERF] = ointerf
            nodeFeatures[OINTERT] = ointert

            # edge features

            edgeFeatures = {feat: {} for feat in edgeFeatureData}
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
                        error(f"{otype[nV]} node v={nV} w={nW} has no slots", tm=False)

                for (feat, featD) in nodeFeatureData.items():
                    val = featD.get(nW, None)
                    if val is not None:
                        nodeFeatures.setdefault(feat, {})[nV] = val

                for (feat, (doValues, valTp, featF, featT)) in edgeFeatureData.items():
                    # outgoing edges are used to construct the in-volume edge
                    # and the inter-volume outgoing edges
                    if doValues:
                        metaData[feat]["edgeValues"] = True
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
                                interItems.append(
                                    (tW, feat, doValuesRep, valTp, valRep)
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
                            if doValues:
                                val = valData[fW]
                            if fV is None:
                                valRep = str(val) if doValues else "x"
                                interItems.append(
                                    (fW, feat, doValuesRep, valTp, valRep)
                                )
                        if interItems:
                            ointert[nW] = ";".join(
                                ",".join(str(i) for i in item) for item in interItems
                            )

        indent(level=0)
        info("remapping done")
        return True

    def writeTf():
        info("Write volumes as TF datasets")
        indent(level=1, reset=True)

        good = True

        for (name, v) in volumeData.items():
            info(f"Writing volume {name}")
            metaData = v["metaData"]
            nodeFeatures = v["nodeFeatures"]
            edgeFeatures = v["edgeFeatures"]
            loc = f"{volumesLocation}/{name}"
            v["loc"] = loc
            TF = FabricCore(locations=loc, silent=True)
            if not TF.save(
                metaData=metaData,
                nodeFeatures=nodeFeatures,
                edgeFeatures=edgeFeatures,
                silent=False if DEBUG else silent or True,
            ):
                good = False
        indent(level=0)
        if not good:
            return False
        info("writing done")
        return good

    def process():
        indent(level=0, reset=True)
        if not checkVolumes():
            return False
        if checkOnly:
            if not volumeData:
                return {name: v["heads"] for (name, v) in volumeData.items()}
        if not getTopLevels():
            return False
        if not checkVolumes2():
            return False
        if checkOnly:
            return {name: v["heads"] for (name, v) in volumeData.items()}
        if not distributeNodes():
            return False
        if not remapFeatures():
            return False
        if not writeTf():
            return False
        info("All done")
        return {
            name: dict(location=f"{volumesLocation}/{name}", new=name in volumeData)
            for name in volumes
        }

    wasSilent = isSilent()
    setSilent(silent)
    result = process()
    setSilent(wasSilent)
    return result
