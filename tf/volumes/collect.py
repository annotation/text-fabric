"""
# Collect

## Usage

```python
from tf.volumes import collect
collect(
  (
      location1,
      location2,
  ),
  workLocation,
)
```

```
collect(
  (
      (name1, location1),
      (name2, location2),
  ),
  workLocation,
  volumeType=None,
  volumeFeature=None,
  featureMeta=None,
  **otext,
)
```
"""

import os
import collections
from shutil import rmtree

from ..parameters import OTYPE, OSLOTS, OVOLUME, OWORK, OINTERF, OINTERT, OMAP
from ..core.fabric import FabricCore
from ..core.timestamp import Timestamp
from ..core.helpers import dirEmpty, unexpanduser as ux, getAllFeatures

DEBUG = False

GENERATED = set(
    """
    writtenBy
    dateWritten
    version
    volume
""".strip().split()
)

TM = Timestamp()
indent = TM.indent
info = TM.info
warning = TM.warning
error = TM.error
setSilent = TM.setSilent
isSilent = TM.isSilent


def collect(
    volumes,
    workLocation,
    volumeType=None,
    volumeFeature=None,
    mergeTypes=None,
    featureMeta=None,
    silent=False,
    overwrite=False,
):
    """Creates a work out of a number of volumes.

    The volumes are individual TF data sets, the work is a new TF data set.

    You may pass as many volume data sources as you want.

    The work will be the union of all nodes of the volumes,
    rearranged according to their types, where node types with the
    same names will be merged.

    The slots of the work are the concatenation of the slots of the
    volumes, which must all have the same slot type.

    The node and edge features will be remapped, so that they have
    the same values in the work as they had in the individual
    volumes.

    !!! caution "inter-volume edges"
        The edge features of each volume only contain edges between nodes
        in that volume. But the work as a whole may have had edges
        between nodes of different volumes.
        These can be restored from two extra features that may exist in the
        volumes: `ointerfrom` and `ointerto`.

        See also `tf.volumes.extract`.

    The volumes may contain a feature `owork` which maps each node in a volume
    to the corresponding node in the work.
    Some non-slot nodes in the work may have slots in multiple volumes.

    !!! hint "Lexeme nodes"
        Think of lexeme nodes that have slots for all occurrences of that lexeme.
        When a work is split into volumes, the lexeme nodes map to
        separate lexeme nodes in each volume where these lexemes occur.
        When we collect volumes into works, we want to merge these lexeme
        nodes again.

    When non-slot nodes across volumes have the same value for their `owork` feature,
    they will be merged into the work. That means: only one node will be created
    in the work, and the slots of that node will be the union of the
    slots these nodes have in the individual volumes.

    !!! caution "Overlapping slots"
        It is an error if volumes have overlapping slots.
        Overlapping slots are those whose values of `owork` are identical.

    A feature `ovolume` will be created which maps each node of the work
    to the corresponding node(s) in the individual volume(s).

    Optionally, nodes corresponding to the volumes themselves will be
    added to the work.

    Care will be taken of the metadata of the features and the contents
    of the `otext.tf` feature, which consists of metadata only.

    All details of the work can be steered by means of parameters.

    You can use this function to recombine volumes that have been obtained
    by extracting them from a work by means of `tf.volumes.extract`.
    In this case, there is no need to pass `volumeType` and `volumeFeature`.

    Parameters
    ----------

    volumes: dict or tuple of (string or tuple)
        You can either pass just the locations of the volumes,
        or you can give them a name and pass `(name, location)` instead,
        or pass them as a dictionary with names as keys and locations as values.
        If you do not give names to volumes, their locations will be used as name.
        However, names are only used if you pass `volumeType` and /or `volumeFeature`.

        !!! caution "Disjointness"
            A collection can not contain the same volume more than once.

    workLocation: string
        The directory into which the feature files of the work will be written.

    overwrite: boolean, optional `None`
        If True, the target collection will be
        be created and will replace any existing collection/volume of the same name.
        If None, the collection will only be created if it does not exist.
        No check will be performed as to whether an existing collection
        is equal to what would have been created by this call.
        If False, refuses to proceed if the collection directory already exists.


    volumeType, volumeFeature: string, optional `None`
        If a string value for one of these is passed,
        a new node type will be added to the work,
        with one new node for each volume: the volume node.
        There will also be a new feature, that assigns the name of a volume
        to the node of that volume.

        The name of the new node type is the value of `volumeType`
        if it is a non-empty string, else it is the value of `volumeFeature`.

        The name of the new feature is `volumeFeature`
        if it is a non-empty string, else it is the value of `volumeType`.

        !!! caution "volumeType must be fresh"
            It is an error if the `volumeType` is a node type that already
            occurs in one of the volumes.

        !!! note "volumeFeature may exist"
            The `volumeFeature` may already exist in one or more volumes.
            In that case the new feature values for nodes of `volumeType` will
            just be added to it.

        Example
        -------
            collect(
                dict(
                    banks='banks/tf/0.2',
                    river='banks/tf/0.4',
                ),
                'riverbanks/tf/1.0',
                volumeType='volume',
                volumeFeature='vol',
            )

        This results in a work with nodes and features from the volumes
        found at the indicated places on your file system.
        After combination, the volumes are visible in the work as nodes
        of type `volume`, and the feature `vol` provides the names `banks` and `river`
        for those nodes.

    featureMeta: dict, optional `None`
        The meta data of the volumes involved will be merged.
        If feature metadata of the same feature is encountered in different volumes,
        and if volumes specify different values for the same keys,
        the different values will be stored under a key with the name of
        the volume appended to the key, separated by a `!`.

        The special metadata field `valueType` will just be reduced
        to one single value `str` if some volumes have it as `str` and others as `int`.
        If the volumes assign the same value type to a feature, that value type
        will be assigned to the combined feature.

        If you want to assign other meta data to specific features,
        or pass meta data for new features that orginate from the merging process,
        you can pass them in the parameter `featureMeta` as in the following example,
        where we pass meta data for a feature called `level` with integer values.

        The contents of the `otext.tf` features are also metadata,
        and their contents will be merged in exactly the same way.

        So if the section/structure specifications and the formats are not
        the same for all volumes, you will see them spread out
        in fields qualified by the volume name with a `!` sign between
        the key and the volume.

        But you can add new specifications explicitly,
        as meta data of the `otext` feature.
        by passing them as keyword arguments.
        They will be passed directly to the combined `otext.tf` feature
        and will override anything with the same key
        that is already in one of the volumes.

    silent: boolean, optional `False`
        Suppress or enable informational messages.

    Returns
    -------
    boolean
        Whether the creation was successful.

        All features in the resulting collection will get a metadata key
        `volume` with as value the name of the collection and its component volumes.

    Example
    -------
        collect(
            dict(
                banks='banks/tf/0.2',
                river='banks/tf/0.4',
            ),
            'riverbanks/tf/1.0',
            featureMeta=dict(
              level=dict(
                valueType='int',
                description='level of a section node',
              ),
            ),
        )

    Example
    -------
        collect(
            dict(
                banks='banks/tf/0.2',
                river='banks/tf/0.4',
            ),
            'riverbanks/tf/1.0',
            featureMeta=dict(
                otext=dict(
                    volumeType='volume',
                    volumeFeature='vol',
                    sectionTypes='volume,chapter,line',
                    sectionFeatures='title,number,number',
                ),
            ),
            silent=False,
        )

    This will give rise to something like this (assuming that `banks` and
    `rivers` have some deviating material in their `otext.tf`:

        @config
        @compiler=Dirk Roorda
        @dateWritten=2019-05-20T19:12:23Z
        @fmt:line-default={letters:XXX}{terminator}
        @fmt:line-term=line#{terminator}
        @fmt:text-orig-extra={letters}{punc}{gap}
        @fmt:text-orig-full={letters}
        @fmt:text-orig-full!banks={letters}{punc}
        @fmt:text-orig-full!rivers={letters}{gap}
        @name=Culture quotes from Iain Banks
        @purpose=exposition
        @sectionFeatures=title,number,number
        @sectionFeatures!banks=title,number,number
        @sectionFeatures!rivers=number,number,number
        @sectionTypes=volume,chapter,line
        @sectionTypes!banks=book,chapter,sentence
        @sectionTypes!rivers=chapter,sentence,line
        @source=Good Reads
        @status=with for similarities in a separate module
        @structureFeatures!banks=title,number,number,number
        @structureFeatures!rivers=title,number,number
        @structureTypes!banks=book,chapter,sentence,line
        @structureTypes!rivers=book,chapter,sentence
        @url=https://www.goodreads.com/work/quotes/14366-consider-phlebas
        @version=0.2
        @writtenBy=Text-Fabric
        @writtenBy=Text-Fabric
        @dateWritten=2019-05-28T10:55:06Z

    !!! caution "inter-version edges"
        Features with names starting in `omap@` contain node maps from
        older to newer versions.
        These will be excluded from collection.

    """

    collection = os.path.basename(workLocation)
    loc = ux(os.path.dirname(workLocation))

    if not dirEmpty(workLocation):
        proceed = True
        good = True

        if overwrite is None:
            info(
                f"Collection {collection} already exists and will not be recreated",
                tm=False,
            )
            proceed = False
        else:
            if overwrite:
                rmtree(workLocation)
                info(
                    f"Collection {collection} exists and will be recreated", tm=False
                )
            else:
                good = False
                proceed = False
                error(
                    f"Collection {collection} already exists at {loc}",
                    tm=False,
                )

        if not good or not proceed:
            return good

    if volumeType:
        if not volumeFeature:
            volumeFeature = volumeType
    else:
        if volumeFeature:
            volumeType = volumeFeature

    TFs = {}
    apis = {}
    getOworks = {}

    slotType = None
    allSlots = set()
    volumeMap = {}
    volumeMapI = {}
    maxSlotW = None
    maxNodeW = None
    metaData = collections.defaultdict(dict)
    nodeFeatures = {}
    edgeFeatures = {}
    allNodeFeatures = set()
    allEdgeFeatures = set()
    volumeOslots = {}
    fromWork = {}

    good = True

    if type(volumes) is not dict:
        volProto = {}
        volNames = set()
        for loc in volumes:
            if type(loc) is str:
                name = os.path.basename(loc)
            else:
                (name, loc) = loc
            if name in volNames:
                error(f"Volume {name} is already part of the collection")
                good = False
            else:
                volNames.add(name)
            volProto[name] = loc
        volumes = volProto

    if not good:
        return False

    volumeIndex = {}
    for (name, loc) in volumes.items():
        seenName = volumeIndex.get(loc, None)
        if seenName:
            error(
                f"Volume {seenName} at location {loc} reoccurs as volume {name}")
            good = False
        volumeIndex[loc] = name

    if not good:
        return False

    def loadVolumes():
        for (name, loc) in volumes.items():
            info(f"Loading volume {name:<60} from {ux(loc)} ...")
            TFs[name] = FabricCore(locations=loc, silent=silent)
            apis[name] = TFs[name].loadAll(silent=silent)
        return True

    def getMetas():
        info("inspect metadata ...")
        meta = collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(set))
        )

        volumeStr = ",".join(volumes)
        collectionMeta = f"{collection}:{volumeStr}"

        for (feat, keys) in (featureMeta or {}).items():
            if feat.startswith(OMAP):
                continue
            meta[feat]["collection"][collectionMeta] = {"+"}
            for (key, value) in keys.items():
                if value is not None:
                    meta[feat][key][value] = {""}

        if volumeFeature:
            meta[volumeFeature]["valueType"]["str"] = {""}
            meta[volumeFeature]["description"][f"label of {volumeType}"] = {""}

        for name in volumes:
            allFeatures = getAllFeatures(apis[name])
            for (feat, fObj) in TFs[name].features.items():
                if feat not in allFeatures:
                    continue
                meta[feat]["collection"][collectionMeta].add(name)
                thisMeta = fObj.metaData
                for (k, v) in thisMeta.items():
                    meta[feat][k][v].add(name)
                if fObj.isConfig:
                    continue
                if fObj.isEdge:
                    allEdgeFeatures.add(feat)
                    meta[feat]["edgeValues"][fObj.edgeValues].add(name)
                else:
                    allNodeFeatures.add(feat)

        for (feat, ks) in meta.items():
            for (k, vs) in ks.items():
                isGenerated = k in GENERATED
                if k == "valueType":
                    if len(vs) > 1:
                        warning(
                            (
                                f"WARNING: {feat}: "
                                "valueType varies in volumes; will be str"
                            ),
                            tm=False,
                        )
                    else:
                        metaData[feat][k] = sorted(vs)[0]
                elif len(vs) == 1:
                    metaData[feat][k] = list(vs)[0]
                else:
                    hasCombinedValue = False
                    for (v, names) in vs.items():
                        for name in names:
                            if name == "+" or name == "" and not isGenerated:
                                hasCombinedValue = True
                                key = k
                            elif name == "":
                                key = k
                            else:
                                key = f"{k}!{name}"
                            metaData[feat][key] = v
                    if not hasCombinedValue and not isGenerated:
                        warning(
                            f"WARNING: {feat}.{k} metadata varies across volumes",
                            tm=False,
                        )
        metaData[OVOLUME] = {k: m for (k, m) in metaData[OTYPE].items()}
        metaData[OVOLUME]["description"] = (
            "mapping from a node in the work to the volume it comes from"
            " and its corresponding node there"
        )
        metaData[OVOLUME]["valueType"] = "str"

        indent(level=0)
        info("metadata sorted out")
        return True

    def checkTypes():
        nonlocal slotType

        slotTypes = set()
        otherTypes = set()

        clashes = set()

        good = True
        info("check nodetypes ...")
        indent(level=1, reset=True)

        for name in volumes:
            info(f"volume {name}", tm=False)
            api = apis[name]
            if not api:
                good = False
                continue
            C = api.C
            nTypeInfo = C.levels.data
            for (t, (nType, av, nF, nT)) in enumerate(nTypeInfo):
                if nType == volumeType:
                    clashes.add(name)
                if t == len(nTypeInfo) - 1:
                    slotTypes.add(nType)
                else:
                    otherTypes.add(nType)
        if len(slotTypes) > 1:
            slotRep = ", ".join(sorted(slotTypes))
            error(f"Multiple slot types: {slotRep}", tm=False)
            good = False

        commonTypes = slotTypes & otherTypes
        if len(commonTypes):
            error(
                "Some node types are slots in one volume and non-slots in another",
                tm=False,
            )
            error(", ".sorted(commonTypes), tm=False)
            good = False

        if clashes:
            clashRep = ", ".join(f"{name}" for name in clashes)
            error(
                f"Volume type {volumeType} occurs inside volumes {clashRep}",
                tm=False,
            )
            good = False

        if good:
            slotType = list(slotTypes)[0]
        else:
            return False

        indent(level=0)
        info("node types ok")
        return True

    def collectNodes():
        info("Collect nodes from volumes ...")
        indent(level=1, reset=True)
        nodesByType = collections.defaultdict(list)

        sW = 0

        good = True

        # check whether volumes have overlapping slots
        # we use the original work slots, provided by the owork feature
        # if it exists; otherwise we cannot know whether slots are overlapping
        info("Check against overlapping slots ...")
        indent(level=2, reset=True)
        for name in volumes:
            api = apis[name]
            E = api.E
            getOwork = api.Fs(OWORK)
            if getOwork:
                getOwork = getOwork.v
            getOworks[name] = getOwork

            maxSlotI = E.oslots.maxSlot
            info(f"{name:<60}: {maxSlotI:>8} slots", tm=False)
            volumeOslots[name] = set(range(sW + 1, sW + 1 + maxSlotI))

            overlap = 0

            for sV in range(1, maxSlotI + 1):
                sW += 1
                nameSv = (name, sV)
                if getOwork:
                    sOW = getOwork(sV)
                    if sOW:
                        if sOW in fromWork:
                            overlap += 1
                        fromWork[sOW] = None

                allSlots.add(sW)
                volumeMap[sW] = nameSv
                volumeMapI[nameSv] = sW

                if overlap:
                    error(f"Overlapping slots: {overlap}")
                    good = False
        indent(level=1)
        if overlap == 0:
            info("no overlap")

        if not good:
            return False

        info("Group non-slot nodes by type")
        indent(level=2, reset=True)
        for name in volumes:
            api = apis[name]

            E = api.E
            F = api.F
            fOtypeData = F.otype.data
            maxSlotI = E.oslots.maxSlot
            maxNodeI = E.oslots.maxNode
            info(f"{name:<60}: {maxSlotI + 1:>8}-{maxNodeI:>8}", tm=False)

            for nV in range(maxSlotI + 1, maxNodeI + 1):
                nType = fOtypeData[nV - maxSlotI - 1]
                nodesByType[nType].append((name, nV))

        nW = sW

        indent(level=1)
        info("Mapping nodes from volume to/from work ...")
        indent(level=2)
        for (nType, nodes) in nodesByType.items():
            startW = nW
            for nameNv in nodes:
                (name, nV) = nameNv
                getOwork = getOworks[name]
                if getOwork:
                    nOW = getOwork(nV)
                    if nOW in fromWork:
                        fromWork[nOW].append(nameNv)
                        continue
                    else:
                        fromWork[nOW] = []
                nW += 1
                volumeMap[nW] = nameNv
                volumeMapI[nameNv] = nW

            info(
                f"{nType:<20}: {startW + 1:>8} - {nW:>8}",
                tm=False,
            )

        nVolumeNodes = len(volumes) if volumeFeature else 0
        nNodesW = len(volumeMap) + nVolumeNodes

        indent(level=1)
        info(f"The new work has {nNodesW} nodes of which {len(allSlots)} slots")

        nonlocal maxSlotW
        nonlocal maxNodeW

        maxSlotW = sW
        maxNodeW = nW

        indent(level=0)
        info("collection done")
        return True

    def remapFeatures():
        info("remap features ...")
        indent(level=1, reset=True)

        # node features

        otype = {}
        nodeFeatures[OTYPE] = otype
        ovolume = {}
        nodeFeatures[OVOLUME] = ovolume

        # edge features

        oslots = {}
        edgeFeatures[OSLOTS] = oslots

        ointerf = {}
        ointert = {}
        fOtypeDatas = {}
        eOslotsDatas = {}
        maxSlots = {}
        maxNodes = {}
        nodeFeatureDatas = {}
        edgeFeatureDatas = {}

        for name in volumes:
            api = apis[name]
            allFeatures = getAllFeatures(api)
            for (ointer, OINTER) in ((ointerf, OINTERF), (ointert, OINTERT)):
                if api.isLoaded(features=OINTER)[OINTER] is None:
                    continue
                interSource = api.Fs(OINTER).data

                interData = {}
                ointer[name] = interData

                for (nW, interEdgesStr) in interSource.items():
                    interEdges = interEdgesStr.split(";")
                    for interEdge in interEdges:
                        (mW, feat, doValues, isInt, val) = interEdge.split(",")
                        doValues = doValues == "v"
                        isInt = isInt == "i"
                        dest = interData.setdefault(feat, {}).setdefault(
                            nW, {} if doValues else set()
                        )
                        if doValues:
                            dest[mW] = int(val) if isInt else val
                        else:
                            dest.add(mW)

            fOtypeDatas[name] = api.F.otype.data
            eOslotsDatas[name] = api.E.oslots.data
            maxSlots[name] = api.E.oslots.maxSlot
            maxNodes[name] = api.E.oslots.maxNode
            nodeFeatureDatas[name] = {
                feat: api.Fs(feat).data
                for feat in api.Fall()
                if feat != OTYPE and feat in allFeatures
            }
            edgeFeatureDatas[name] = {
                feat: (
                    api.Es(feat).doValues,
                    api.Es(feat).data,
                    api.Es(feat).dataInv,
                )
                for feat in api.Eall()
                if not feat.startswith(OMAP) and feat != OSLOTS and feat in allFeatures
            }

        for (nW, (name, nV)) in volumeMap.items():
            ovolume[nW] = f"{name},{nV}"
            maxSlotI = maxSlots[name]

            otype[nW] = (
                slotType if nW <= maxSlotW else fOtypeDatas[name][nV - maxSlotI - 1]
            )

            if nW > maxSlotW:
                oslots[nW] = set(
                    volumeMapI[(name, sV)]
                    for sV in eOslotsDatas[name][nV - maxSlotI - 1]
                )
                if nW in fromWork:
                    for (name2, nV2) in fromWork[nW]:
                        oslots[nW] |= set(
                            volumeMapI[(name2, sV)]
                            for sV in eOslotsDatas[name2][nV2 - maxSlots[name2] - 1]
                        )

            for (feat, featD) in nodeFeatureDatas[name].items():
                val = featD.get(nV, None)
                if val is not None:
                    nodeFeatures.setdefault(feat, {})[nW] = val

            for (feat, (doValues, featF, featT)) in edgeFeatureDatas[name].items():
                valData = featF.get(nV, None)
                if valData is not None:
                    value = {} if doValues else set()
                    for tV in valData:
                        tW = volumeMapI[(name, tV)]
                        if doValues:
                            val = valData.get(tV, None)
                            value[tW] = val
                        else:
                            value.add(tW)
                    if value:
                        edgeFeatures.setdefault(feat, {})[nW] = value

        # add inter-volume edges
        # the ointerf and ointert features have in their values a node
        # from the original work.
        # We have to infer the volume and the corresponding node in that volume.
        # And then we can get the corresponding node in the collected work.

        # If this sounds like a detour that can be cut short:
        # the new collection we are making does not have to be identical
        # to the original work.
        # It could very well be that we have extracted all volumes from a work
        # and are now collecting only certain volumes for the new work.

        # Indeed, when splitting the original work into volumes,
        # it might have been the case that certain top-level sections
        # of the orginal work do not end up in one of the volumes.

        getOworkWI = {}

        # get the mapping from nodes in the original work
        # to nodes in all volumes

        for name in volumes:
            getOwork = getOworks[name]
            if getOwork:
                maxNode = maxNodes[name]
                for nV in range(1, maxNode):
                    nW = getOwork(nV)
                    getOworkWI[nW] = (name, nV)

        # OUTGOING edges

        for (name, interData) in ointerf.items():
            for (feat, interFeatData) in interData.items():
                doValues = edgeFeatureDatas[name][feat][0]
                thisEdgeFeature = edgeFeatures.setdefault(feat, {})
                for (fW, interValueData) in interFeatData.items():
                    for tOW in interValueData:
                        if tOW not in getOworkWI:
                            # edge goes outside the new work
                            continue
                        else:
                            (nameT, tV) = getOworkWI[tOW]
                            tW = volumeMapI[(nameT, tV)]

                            dest = thisEdgeFeature[feat].setdefault(
                                fW, {} if doValues else set()
                            )
                            if doValues:
                                dest[tW] = interValueData[tOW]
                            else:
                                dest.add(tW)

        # INCOMING edges

        for (name, interData) in ointert.items():
            for (feat, interFeatData) in interData.items():
                doValues = edgeFeatureDatas[name][feat][0]
                thisEdgeFeature = edgeFeatures.setdefault(feat, {})
                for (tW, interValueData) in interFeatData.items():
                    for fOW in interValueData:
                        if fOW not in getOworkWI:
                            # edge comes from outside the new work
                            continue
                        else:
                            (nameF, fV) = getOworkWI[fOW]
                            fW = volumeMapI[(nameF, fV)]

                            dest = thisEdgeFeature[feat].setdefault(
                                fW, {} if doValues else set()
                            )
                            if doValues:
                                dest[tW] = interValueData[tOW]
                            else:
                                dest.add(tW)

        if volumeFeature:
            nW = maxNodeW

            for name in volumes:
                nW += 1
                nodeFeatures.setdefault(volumeFeature, {})[nW] = name
                edgeFeatures[OSLOTS][nW] = volumeOslots[name]

        indent(level=0)
        info("remapping done")
        return True

    def writeTf():
        info("write work as TF data set")
        TF = FabricCore(locations=workLocation, silent=True)
        good = TF.save(
            metaData=metaData,
            nodeFeatures=nodeFeatures,
            edgeFeatures=edgeFeatures,
            silent=False if DEBUG else silent or True,
        )
        indent(level=0)
        if not good:
            return False
        info("writing done")
        return good

    def process():
        indent(level=0, reset=True)
        if not loadVolumes():
            return False
        if not getMetas():
            return False
        if not checkTypes():
            return False
        if not collectNodes():
            return False
        if not remapFeatures():
            return False
        if not writeTf():
            return False
        info("done")
        return True

    wasSilent = isSilent()
    setSilent(silent)
    result = process()
    setSilent(wasSilent)
    return result
