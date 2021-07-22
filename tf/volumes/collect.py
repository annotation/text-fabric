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

from ..fabric import Fabric
from ..parameters import OTYPE, OSLOTS, OVOLUME, OWORK
from ..core.timestamp import Timestamp
from ..core.helpers import dirEmpty, unexpanduser

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

    workLocation: string
        The directory into which the feature files of the work will be written.

    overwrite: boolean, optional `False`
        If True, overwrites work directory by cleaning it first.
        If False, refuses to proceed if work directory exists.

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

    """

    if not dirEmpty(workLocation):
        if overwrite:
            rmtree(workLocation)
        else:
            error(
                "Work directory is not empty."
                " Clean it or remove it or choose another location",
                tm=False,
            )
            return False

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
    maxSlotTotal = None
    maxNodeTotal = None
    metaData = collections.defaultdict(dict)
    nodeFeatures = {}
    edgeFeatures = {}
    allNodeFeatures = set()
    allEdgeFeatures = set()
    volumeOslots = {}
    fromWork = {}

    if type(volumes) is not dict:
        volProto = {}
        volNames = set()
        for loc in volumes:
            if type(loc) is str:
                name = os.path.basename(loc)
            else:
                (name, loc) = loc
            i = 0
            while name in volNames:
                i += 1
                name = f"{name}_{i}"
            volNames.add(name)
            volProto[name] = loc
        volumes = volProto

    def loadVolumes():
        for (name, loc) in volumes.items():
            info(f"Loading volume {name} from {unexpanduser(loc)} ...")
            TFs[name] = Fabric(locations=loc, silent=silent)
            apis[name] = TFs[name].loadAll(silent=silent)
        return True

    def getMetas():
        info("inspect metadata ...")
        meta = collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(set))
        )

        for (feat, keys) in (featureMeta or {}).items():
            for (key, value) in keys.items():
                if value is not None:
                    meta[feat][key][value] = {""}

        if volumeFeature:
            meta[volumeFeature]["valueType"]["str"] = {""}
            meta[volumeFeature]["description"][f"label of {volumeType}"] = {""}

        for name in volumes:
            for (feat, fObj) in TFs[name].features.items():
                if fObj.method:
                    continue
                thisMeta = fObj.metaData
                for (k, v) in thisMeta.items():
                    meta[feat][k][v].add(name)
                if fObj.isConfig:
                    continue
                if fObj.isEdge:
                    allEdgeFeatures.add(feat)
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
                            if name == "" and not isGenerated:
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
            info(f"volume {name}")
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

        curSlot = 0

        indent(level=2, reset=True)

        good = True

        for name in volumes:
            info(f"{name}: slots")
            api = apis[name]
            E = api.E
            getOwork = api.Fs(OWORK)
            if getOwork:
                getOwork = getOwork.v
            getOworks[name] = getOwork

            maxSlotI = E.oslots.maxSlot
            volumeOslots[name] = set(range(curSlot + 1, curSlot + 1 + maxSlotI))

            overlap = 0

            for s in range(1, maxSlotI + 1):
                curSlot += 1
                vs = (name, s)
                if getOwork:
                    sWork = getOwork(s)
                    if sWork:
                        if sWork in fromWork:
                            overlap += 1
                        fromWork[sWork] = None

                allSlots.add(curSlot)
                volumeMap[curSlot] = vs
                volumeMapI[vs] = curSlot

                if overlap:
                    error(f"Overlapping slots: {overlap}")
                    good = False

        if not good:
            return False

        for name in volumes:
            info(f"{name}: grouping other nodes by type")
            api = apis[name]

            E = api.E
            F = api.F
            fOtypeData = F.otype.data
            maxSlotI = E.oslots.maxSlot
            maxNodeI = E.oslots.maxNode

            for n in range(maxSlotI + 1, maxNodeI + 1):
                nType = fOtypeData[n - maxSlotI - 1]
                nodesByType[nType].append((name, n))

        curNode = curSlot

        indent(level=1)
        info("mapping nodes ...")
        indent(level=2)
        for (nType, nodes) in nodesByType.items():
            startNode = curNode
            for vn in nodes:
                (name, n) = vn
                getOwork = getOworks[name]
                if getOwork:
                    nWork = getOwork[n]
                    if nWork in fromWork:
                        fromWork[nWork].append(vn)
                        continue
                    else:
                        fromWork[nWork] = []
                curNode += 1
                volumeMap[curNode] = vn
                volumeMapI[vn] = curNode
            if DEBUG:
                info(
                    f"node type {nType:<20}: {startNode + 1:>8} - {curNode:>8}",
                    tm=False,
                )

        nVolumeNodes = len(volumes) if volumeFeature else 0
        nNodes = len(volumeMap) + nVolumeNodes

        indent(level=1)
        info(f"The new work has {nNodes} nodes of which {len(allSlots)} slots")

        nonlocal maxSlotTotal
        nonlocal maxNodeTotal

        maxSlotTotal = curSlot
        maxNodeTotal = curNode

        indent(level=0)
        info("collection done")
        return True

    def remapFeatures():
        info("remap features ...")
        indent(level=1, reset=True)

        # node features

        otype = {}
        nodeFeatures[OTYPE] = otype
        nodeFeatures[OVOLUME] = {}

        # edge features

        oslots = {}
        edgeFeatures[OSLOTS] = oslots

        fOtypeDatas = {}
        eOslotsDatas = {}
        maxSlots = {}
        maxNodes = {}
        nodeFeatureDatas = {}
        edgeFeatureDataVs = {}
        edgeFeatureDatas = {}

        for name in volumes:
            fOtypeDatas[name] = apis[name].F.otype.data
            eOslotsDatas[name] = apis[name].E.oslots.data
            maxSlots[name] = apis[name].E.oslots.maxSlot
            maxNodes[name] = apis[name].E.oslots.maxNode
            nodeFeatureDatas[name] = {
                feat: apis[name].Fs(feat).data
                for feat in apis[name].Fall()
                if feat != OTYPE
            }
            edgeFeatureDataVs[name] = {
                feat: apis[name].Es(feat).data
                for feat in apis[name].Eall()
                if feat != OSLOTS and apis[name].Es(feat).doValues
            }
            edgeFeatureDatas[name] = {
                feat: apis[name].Es(feat).data
                for feat in apis[name].Eall()
                if feat != OSLOTS and not apis[name].Es(feat).doValues
            }

        ovolume = nodeFeatures[OVOLUME]

        for (n, (name, nV)) in volumeMap.items():
            ovolume[n] = f"{name},{nV}"
            maxSlotI = maxSlots[name]

            otype[n] = (
                slotType if n <= maxSlotTotal else fOtypeDatas[name][nV - maxSlotI - 1]
            )

            if n > maxSlotTotal:
                oslots[n] = set(
                    volumeMapI[(name, s)] for s in eOslotsDatas[name][nV - maxSlotI - 1]
                )
                if n in fromWork:
                    for (name2, nV2) in fromWork[n]:
                        oslots[n] |= set(
                            volumeMapI[(name2, s)]
                            for s in eOslotsDatas[name2][nV2 - maxSlots[name2] - 1]
                        )

            for (feat, featD) in nodeFeatureDatas[name].items():
                val = featD.get(nV, None)
                if val is not None:
                    nodeFeatures.setdefault(feat, {})[n] = val

            for (feat, featD) in edgeFeatureDatas[name].items():
                valData = featD.get(nV, None)
                if valData is not None:
                    value = frozenset(
                        volumeMapI[(name, t)]
                        for t in valData
                        if (name, t) in volumeMapI
                    )
                    if value:
                        edgeFeatures.setdefault(feat, {})[n] = value

            for (feat, featD) in edgeFeatureDataVs[name].items():
                valData = featD.get(nV, None)
                if valData is not None:
                    for (t, val) in valData.items():
                        tT = volumeMapI[(name, t)]
                        edgeFeatures.setdefault(feat, {}).setdefault(n, {})[tT] = val

        if volumeFeature:
            curNode = maxNodeTotal

            for name in volumes:
                curNode += 1
                nodeFeatures.setdefault(volumeFeature, {})[curNode] = name
                edgeFeatures[OSLOTS][curNode] = volumeOslots[name]

        indent(level=0)
        info("remapping done")
        return True

    def writeTf():
        info("write work as TF data set")
        TF = Fabric(locations=workLocation, silent=True)
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
