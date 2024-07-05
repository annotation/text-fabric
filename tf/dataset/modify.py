"""
# Modify

## Usage

``` python
from tf.dataset import modify
modify(
    location,
    targetLocation,
    mergeFeatures=None,
    deleteFeatures=None,
    addFeatures=None,
    mergeTypes=None,
    deleteTypes=None,
    addTypes=None,
    replaceSlotType=None,
    featureMeta=None,
    silent="deep",
)
```


"""

import collections
import functools

from ..fabric import Fabric
from ..parameters import WARP, OTYPE, OSLOTS, OTEXT
from ..core.timestamp import Timestamp, SILENT_D, DEEP
from ..core.helpers import itemize, fitemize, isInt, collectFormats
from ..core.files import dirEmpty, expanduser as ex

VALTP = "valueType"

GENERATED = set(
    """
    writtenBy
    dateWritten
    version
""".strip().split()
)

NODE = "node"
NODES = "nodes"
EDGE = "edge"
EDGES = "edges"

NFS = "nodeFeatures"
EFS = "edgeFeatures"

ADD_F_KEYS = {NFS, EFS}

NF = "nodeFrom"
NT = "nodeTo"
NS = "nodeSlots"

ADD_T_KEYS = {NF, NT, NS, NFS, EFS}

SE_TP = "sectionTypes"
SE_FT = "sectionFeatures"
ST_TP = "structureTypes"
ST_FT = "structureFeatures"


def _rep(iterable):
    return ", ".join(sorted(iterable))


def modify(
    location,
    targetLocation,
    targetVersion=None,
    mergeFeatures=None,
    deleteFeatures=None,
    addFeatures=None,
    mergeTypes=None,
    deleteTypes=None,
    addTypes=None,
    replaceSlotType=None,
    featureMeta=None,
    silent=SILENT_D,
):
    """Modifies the supply of node types and features in a single data set.

    Dependent on the presence of the parameters, the following steps will be
    executed before the result is written out as a new TF dataset:

    *   merge existing features into an other feature, removing the features
        that went in;
    *   delete any number of existing features;
    *   add any number of features and their data;
    *   merge existing node types into a new one, removing the
        types that went in, without loss of nodes;

    So far, no new nodes have been added or removed. But then:

    *   delete any number of node types with their nodes;
    *   add any number of new node types, with nodes and features.

    The last two actions lead to a shifting of nodes, and all features that map
    them, will be shifted accordingly.

    After all that, there is one remaining action that could be performed

    You can also pass meta data to be merged in.

    Finally, the resulting features will be written to disk.

    !!! hint "Only added / merged features"
        It is possible to output only the added and merged features instead
        of a complete dataset. Just pass the boolean value `True` to `deleteFeatures`
        below.

    Parameters
    ----------

    location: string
        You can pass just the location of the original dataset in the file system,
        i.e. the directory that contains the `.tf` files.

    targetLocation: string
        The directory into which the result dataset will be written.

    targetVersion: string, optional None
        If given, the new version that will be written to the metadata of each
        feature in the modified dataset.
        If None, no version modification takes place.

    mergeFeatures: dict, optional None
        You can merge several features into one. This is especially useful if there
        are many features each operating on different node types, and you want to
        unify them into one feature.
        The situation may occur that several of the features to be merged supply
        conflicting values for a node. Then the last feature in the merge list wins.

        The result feature may exist already. Also then there is a risk of conflict.
        Again, the merge result wins.

        Example
        -------
            mergeFeatures=dict(
                resultFeature1=[feat1, feat2],
                resultFeature2="feat3, feat4",
            ),

        If the resulting feature is new, or needs a new description, you can
        provide metadata in the `featureMeta` argument.
        For new features you may want to set the `valueType`, although we try
        hard to deduce it from the data available.

    deleteFeatures: boolean | string | iterable, optional None
        This should be either a boolean value `True` or an iterable or space/comma
        separated string of features that you want to delete from the result.

        `True` means: all features will be deleted that are not the result of merging
        or adding features (see `mergeFeatures` above and `addFeatures` below.

    addFeatures: dict, optional None
        You can add as many features as you want, assigning values to all types,
        including new nodes of new types that have been generated in the steps before.

        You can also use this parameter to override existing features:
        if a feature that you are adding already exists, the new data will be merged
        in, overriding assignments of the existing feature if there is a conflict.
        The meta data of the old and new feature will also be merged.

        This parameter must have this shape:

        Example
        -------
            addFeatures=dict(
                nodeFeatures=dict(
                  feat1=data1,
                  feat2=data2,
                ),
                edgeFeatures=dict(
                  feat3=data3,
                  feat4=data4,
                ),

        If the resulting features are new, or need a new description, you can
        provide metadata in the `featureMeta` argument.
        For new features you may want to set the `valueType`, although we try
        hard to deduce it from the data available.

    mergeTypes: dict, optional None
        You can merge several node types into one.
        The merged node type will have the union of nodes of the types that are merged.
        All relevant features will stay the same, except the `otype` feature of course.

        You can pass additional information to be added as features to nodes
        of the new node type.
        These features can be used to discriminate between the merged types.

        This parameter must have this shape:

        Example
        -------
            mergeTypes=dict(
                outTypeA=(
                    'inType1',
                    'inType2',
                ),
                outTypeB="inType3, inType4",
            )

        Example
        -------
            mergeTypes=dict(
                outTypeA=dict(
                    inType1=dict(
                        featureI=valueI,
                        featureK=valueK,
                    ),
                    inType2=dict(
                        featureL=valueL,
                        featureM=valueM,
                    ),
                ),
                outTypeB=dict(
                    inType3=dict(
                        featureN=valueN,
                        featureO=valueO,
                    ),
                    inType4=dict(
                        featureP=valueP,
                        featureQ=valueQ,
                    ),
                ),
            )

        It does not matter if these types and features already occur.
        The `outTypes` may be existing types of really new types.
        The new features may be existing or new features.

        Do not forget to provide meta data for new features in the `featureMeta` argument.

        This will migrate nodes of type `inType1` or `inType2` to nodes of `outTypeA`.

        In the extended form, when there are feature specifications associated
        with the old types, after merging the following assignments will be made:

        `featureI = valueI` to nodes coming from `inType1`

        and

        `featureK = valueK` to nodes coming from `inType2`.

        No nodes will be removed!

        !!! caution "slot types"
            Merging is all about non-slot types.
            It is an error if a new type or an old type is a slot type.

    deleteTypes: string | iterable, optional None
        You can delete node types from the result altogether.
        You can specify a list of node types as an iterable or as a space
        separated string.

        If a node type has to be deleted, all nodes in that type
        will be removed, and features that assign values to these nodes will have
        those assignments removed.

        Example
        -------
            deleteTypes=('line', 'sentence')

        Example
        -------
            deleteTypes="line sentence"

        !!! caution "slot types"
            Deleting is all about non-slot types.
            It is an error to attempt to delete slot type.

    addTypes: dict, optional None
        You may add as many node types as you want.

        Per node type that you add, you need to specify the current boundaries of
        that type and how all those nodes map to slots.
        You can also add features that assign values to those nodes:

        Example
        -------
            dict(
                nodeType1=dict(
                    nodeFrom=from1,
                    nodeTo=to1,
                    nodeSlots=slots1,
                    nodeFeatures=nFeatures1,
                    edgeFeatures=eFeatures1,
                ),
                nodeType2=dict(
                    nodeFrom=from2,
                    nodeTo=to2,
                    nodeSlots=slots2,
                    nodeFeatures=nFeatures2,
                    edgeFeatures=eFeatures2,
                ),
            ),

        The boundaries may be completely arbitrary, so if you get your nodes from another
        TF data source, you do not need to align their values.

        If you also add features about those nodes, the only thing that matters is
        that the features assign the right values to the nodes within the boundaries.
        Assignments to nodes outside the boundaries will be ignored.

        The slots that you link the new nodes to, must exist in the original.
        You cannot use this function to add slots to your data set.

        !!! caution "existing node types"
            It is an error if a new node type already exists in the original,
            unless that type is meant to be deleted.

        !!! info "`nodeFeatures`, `edgeFeatures`"
            You can add any number of features.
            Per feature you have to provide the mapping that defines the feature.

            These features may be new,
            or they may already be present in the original data.

            If these features have values for nodes that are not within the boundaries
            of the new node type,
            those values will not be assigned but silently discarded.

            Example
            -------
                dict(
                    feat1=dict(
                        n1=val1,
                        n2=val2,
                    ),
                    feat2=dict(
                        n1=val1,
                        n2=val2,
                    ),
                ),

            Edge features without values are specified like this:

            Example
            -------
                dict(
                    feat1=dict(
                        n1={m1, m2},
                        n2={m3, m4},
                    ),
                    feat2=dict(
                        n1={m5, m6},
                        n2={m7, m8},
                    ),
                ),

            Edge features with values are specified like this:

            Example
            -------
                dict(
                    feat1=dict(
                        n1={m1: v1, m2: v2},
                        n2={m3: v3, m4: v4},
                    ),
                    feat2=dict(
                        n1={m5: v5, m6: v6},
                        n2={m7: v7, m8: v8},
                    ),
                ),

        !!! info "`edgeFeatures` to nodes of other types"
            However, you may want to define edge features that relate the new nodes
            to nodes of other types. There is a limited way to do that.

            *   the other type must be the last type that was added before the current
                type;
            *   the nodes in the specification of the previously added type must be
                disjoint from the nodes of the currently added type.

    replaceSlotType: string, optional None
        If passed, it should be a tuple whose first member is a valid, non-slot
        node type.
        The slot type will be replaced by this node type and the original slots will
        be deleted.
        The remaining members are features that should be discarded in the process,
        they are typically features defined for old slot nodes that have little or no
        meaning for new slot nodes.
        Other features that are defined for old slots carry over to the corresponding
        new slots, but only if the new slot does not have already that feature
        assigned. Only the value of the first old slot that corresponds with a new slot
        carries over to that new slot.

        When the original slot type gets replaced, the slot mapping of other nodes
        needs to be adjusted. The new slots are a coarser division of the
        corpus than the old slots. It might even be the case that the new slots
        do not cover the corpus completely.

        If other nodes are linked to slots that are not covered by the new slots,
        these links are lost.
        This may lead to nodes that do not have links to slots anymore.
        These nodes will be lost, together with the feature values for these nodes
        and the edges that involve these nodes.

        Once the slot type is replaced, you may want to adapt the text formats in
        the OTEXT feature. You can do so by passing appropriate values
        in the `featureMeta` argument.

    featureMeta: dict, optional None
        If the features you have specified in one of the parameters above are new,
        do not forget to pass metadata for them in this  parameter
        It is especially important to state the value type:

        Example
        -------
            featureMeta=dict(
                featureI=dict(
                  valueType='int',
                  description='level of node'
                ),
                featureK=dict(
                  valueType='str',
                  description='subtype of node'
                ),
            ),

        You can also tweak the section / structure configuration and the
        text-formats that are specified in the `otext` feature.
        Just specify them as keys and values to the `otext` feature.

        The logic of tweaking meta data is this: what you provide in this
        parameter will be merged into existing meta data.

        If you want to remove a key from a feature, give it the value None.

    silent: string, optional tf.core.timestamp.SILENT_D
        See `tf.core.timestamp.Timestamp`
    """

    TM = Timestamp()
    indent = TM.indent
    info = TM.info
    error = TM.error
    warning = TM.warning
    setSilent = TM.setSilent

    setSilent(silent)

    addFeatures = addFeatures or {}
    onlyDeliverUpdatedFeatures = False
    if type(deleteFeatures) is bool and deleteFeatures:
        deleteFeatures = set()
        onlyDeliverUpdatedFeatures = True
    deleteFeatures = set(fitemize(deleteFeatures))
    mergeFeatures = mergeFeatures or {}

    addTypes = addTypes or {}
    deleteTypes = set(fitemize(deleteTypes))
    mergeTypes = mergeTypes or {}

    featureMeta = featureMeta or {}

    origMaxNode = None
    origNodeTypes = None
    origNodeFeatures = None
    origEdgeFeatures = None
    origFeatures = None

    shift = {}
    shiftNeeded = False

    slotType = None
    maxNode = None
    nodeFeatures = {}
    edgeFeatures = {}
    deletedTypes = set()
    deletedFeatures = set()
    nodeTypes = {}

    nodeFeaturesOut = {}
    edgeFeaturesOut = {}
    metaDataOut = {}

    api = None

    good = True
    ePrefix = ""
    eItem = ""

    targetLocation = ex(targetLocation)

    def err(msg):
        nonlocal good
        error(f"{ePrefix}{eItem}{msg}", tm=False)
        good = False

    def warn(msg):
        warning(f"WARNING: {ePrefix}{eItem}{msg}", tm=False)

    def inf(msg):
        info(f"{ePrefix}{eItem}{msg}", tm=False)

    def meta(feat):
        return api.TF.features[feat].metaData

    def valTp(feat):
        return meta(feat).get(VALTP, None)

    def otextInfo():
        orig = meta(OTEXT)
        custom = featureMeta.get(OTEXT, {})
        combi = {}
        for key in set(custom) | set(orig):
            origVal = orig.get(key, "")
            customVal = custom.get(key, "")
            combi[key] = customVal or origVal

        ensureTypes = set()
        ensureFeatures = set()
        for kind in (SE_TP, ST_TP):
            ensureTypes |= set(itemize(combi.get(kind, ""), sep=","))
        for kind in (SE_FT, ST_FT):
            ensureFeatures |= set(itemize(combi.get(kind, ""), sep=","))
        ensureFeatures |= set(collectFormats(combi)[-1])
        return (ensureTypes, ensureFeatures)

    def allInt(values):
        return all(isInt(v) for v in values) and any(True for v in values)

    def prepare():
        nonlocal api
        nonlocal origNodeTypes
        nonlocal origFeatures
        nonlocal origNodeFeatures
        nonlocal origEdgeFeatures
        nonlocal origMaxNode
        nonlocal slotType
        nonlocal maxNode
        nonlocal shift
        nonlocal ePrefix
        nonlocal eItem

        indent(level=0, reset=True)
        info("preparing and checking ...")
        indent(level=1, reset=True)

        TF = Fabric(locations=location, silent=silent)
        origAllFeatures = TF.explore(silent=DEEP, show=True)
        origNodeFeatures = set(origAllFeatures[NODES])
        origEdgeFeatures = set(origAllFeatures[EDGES])
        origFeatures = origNodeFeatures | origEdgeFeatures

        api = TF.load("", silent=silent)
        if not api:
            return False

        F = api.F
        C = api.C
        slotType = F.otype.slotType
        origNodeTypes = {x[0]: (x[2], x[3]) for x in C.levels.data}
        origMaxSlot = F.otype.maxSlot
        origMaxNode = F.otype.maxNode
        maxNode = origMaxNode

        addedTp = set()
        addedFt = set()
        deletedTp = set()
        deletedFt = set()

        # check mergeFeatures

        ePrefix = "Merge features: "

        for outFeat, inFeats in mergeFeatures.items():
            eItem = f"{outFeat}: "

            inFeats = fitemize(inFeats)
            if outFeat in WARP:
                err("Can not merge into standard features")
                continue

            if not inFeats:
                err("Nothing to merge from")
                continue

            addedFt.add(outFeat)

            for inFeat in inFeats:
                if inFeat in WARP:
                    err(f"Can not merge from standard features: {inFeat}")
                    continue
                deletedFt.add(inFeat)

            missingIn = {f for f in inFeats if f not in origFeatures}

            if missingIn:
                err(f"Missing features {_rep(missingIn)}")

            allInIsNode = all(f in origNodeFeatures for f in inFeats)
            allInIsEdge = all(f in origEdgeFeatures for f in inFeats)
            outExists = outFeat in origFeatures
            outIsNode = outExists and outFeat in origNodeFeatures
            outIsEdge = outExists and outFeat in origEdgeFeatures

            if outIsNode and not allInIsNode:
                err("Node Feature can not be merged from an edge feature")

            if outIsEdge and not allInIsEdge:
                err("Edge Feature can not be merged from a node feature")

            if not allInIsNode and not allInIsEdge:
                err("Feature can not be merged from both node and edge features")

            allInIsInt = all(valTp(f) == "int" for f in inFeats)
            correctTp = "int" if allInIsInt else "str"
            checkValType(outFeat, correctTp=correctTp)

        # check deleteFeatures

        ePrefix = "Delete features: "

        for feat in deleteFeatures:
            eItem = f"{feat}: "

            if feat in WARP:
                err("Can not delete standard features")
                continue
            if feat not in origFeatures:
                err("Not in data set")

            deletedFt.add(feat)

        # check addFeatures

        ePrefix = "Add features: "
        eItem = ""

        illegalKeys = set(addFeatures) - ADD_F_KEYS
        if illegalKeys:
            err(f"{_rep(illegalKeys)} unrecognized, expected {_rep(ADD_F_KEYS)}")

        bothFeatures = set(addFeatures.get(NFS, {})) & set(addFeatures.get(EFS, {}))
        if bothFeatures:
            err(f"{_rep(bothFeatures)}: Both node and edge features")

        for kind, otherKind, origSet, origSetOther in (
            (NODE, EDGE, origNodeFeatures, origEdgeFeatures),
            (EDGE, NODE, origEdgeFeatures, origNodeFeatures),
        ):
            for feat, data in addFeatures.get(f"{kind}Features", {}).items():
                eItem = f"{feat}: "

                if feat in WARP:
                    err("Cannot add standard features")
                    continue
                if feat in origSetOther:
                    err(f"{kind} feature already exists as {otherKind} feature")

                checkValType(feat, vals=data.values())

                addedFt.add(feat)

        # check mergeTypes

        ePrefix = "Merge types: "

        mData = {}

        for outType, inTypes in mergeTypes.items():
            eItem = f"{outType}: "

            if outType == slotType:
                err("Result cannot be the slot type")

            withFeatures = type(inTypes) is dict

            addedTp.add(outType)

            for inType in inTypes:
                if inType == slotType:
                    err(f"Slot type {inType} is not mergeable")
                    continue

                if inType not in origNodeTypes:
                    err(f"Cannot merge non-existing node type {inType}")
                    continue

                deletedTp.add(inType)

                mFeatures = inTypes[inType] if withFeatures else {}
                for feat, val in mFeatures.items():
                    mData.setdefault(feat, set()).add(val)
                    addedFt.add(feat)

        for feat, vals in mData.items():
            eItem = f"{feat}: "
            checkValType(feat, vals=vals)

        # check deleteTypes

        ePrefix = "Delete types: "

        for nodeType in deleteTypes:
            eItem = f"{nodeType}: "

            if nodeType not in origNodeTypes:
                err("Not in data set")
                continue

            deletedTp.add(nodeType)

        # check addTypes

        ePrefix = "Add types: "

        for nodeType, typeInfo in sorted(addTypes.items()):
            eItem = f"{nodeType}: "

            illegalKeys = set(typeInfo) - ADD_T_KEYS
            if illegalKeys:
                err(f"{_rep(illegalKeys)} unrecognized, expected {_rep(ADD_T_KEYS)}")
                continue

            if nodeType in set(origNodeTypes) - deleteTypes:
                err("Already occurs")
                continue

            addedTp.add(nodeType)

            nodeSlots = typeInfo.get(NS, {})
            if not nodeSlots:
                err("No slot information given")
            nF = typeInfo.get(NF, None)
            if not nF:
                err("No lower bound given")
            nT = typeInfo.get(NT, None)
            if not nT:
                err("No upper bound given")
            if nF is not None and nT is not None:
                unlinked = 0
                badlinked = 0
                for n in range(nF, nT + 1):
                    slots = nodeSlots.get(n, ())
                    if not slots:
                        unlinked += 1
                    else:
                        slotGood = True
                        for slot in slots:
                            if slot < 1 or slot > origMaxSlot:
                                slotGood = False
                        if not slotGood:
                            badlinked += 1
                if unlinked:
                    err(f"{unlinked} nodes not linked to slots")
                if badlinked:
                    err(f"{badlinked} nodes linked to non-slot nodes")

            for kind in (NODE, EDGE):
                for feat, data in typeInfo.get(f"{kind}Features", {}).items():
                    eItem = f"{feat}: "
                    checkValType(feat, vals=data.values())

                    addedFt.add(feat)

        (otextTypes, otextFeatures) = otextInfo()

        if False:
            # it is no problem to first delete a type and then add a type with
            # the same name (I think)
            problemTypes = addedTp & deletedTp

            if problemTypes:
                ePrefix = "Add and then delete: "
                eItem = "types: "
                err(f"{_rep(problemTypes)}")

        problemTypes = otextTypes - ((set(origNodeTypes) | addedTp) - deletedTp)
        if problemTypes:
            ePrefix = "Missing for text API: "
            eItem = "types: "
            warn(f"{_rep(problemTypes)}")

        problemFeats = addedFt & deletedFt

        if problemFeats:
            ePrefix = "Add and then delete: "
            eItem = "features: "
            err(f"{_rep(problemFeats)}")

        problemFeats = otextFeatures - ((origFeatures | addedFt) - deletedFt)
        if problemFeats:
            ePrefix = "Missing for text API: "
            eItem = "features: "
            warn(f"{_rep(problemFeats)}")

        if not dirEmpty(targetLocation):
            ePrefix = "Output directory: "
            eItem = "not empty: "
            err("Clean it or remove it or choose another location")

        if not good:
            return False

        api = TF.loadAll(silent=silent)

        info("done")
        return True

    def checkValType(feat, vals=None, correctTp=None):
        origTp = valTp(feat) if feat in origFeatures else None
        customTp = featureMeta.get(feat, {}).get(VALTP, None)
        assignedTp = origTp or customTp

        if correctTp is None:
            correctTp = "int" if allInt(vals) else "str"
        newTp = customTp or correctTp

        if newTp != assignedTp:
            featureMeta.setdefault(feat, {})[VALTP] = newTp

        if customTp and customTp != correctTp and customTp == "int":
            err("feature values are declared to be int but some values are not int")

        if assignedTp != newTp:
            rep1 = f"feature of type {newTp}"
            rep2 = f" (was {assignedTp})" if assignedTp else ""
            inf(f"{rep1}{rep2}")

    def shiftx(vs, offset=None, nF=None, nT=None, nodeMap={}):
        if offset is None:
            return (
                {shift[m]: v for (m, v) in vs.items()}
                if type(vs) is dict
                else {shift[m] for m in vs}
            )
        else:
            if type(vs) is dict:
                result = {}
                for (m, v) in vs.items():
                    if nF <= m <= nT:
                        result[m + offset] = v
                    elif m in nodeMap:
                        result[nodeMap[m]] = v
            else:
                result = set()
                for m in vs:
                    if nF <= m <= nT:
                        result.add(m + offset)
                    elif m in nodeMap:
                        result.add(nodeMap[m])
            return result

    def shiftFeature(kind, feat, data):
        return (
            {shift[n]: v for (n, v) in data.items() if n in shift}
            if kind == NODE
            else {shift[n]: shiftx(v) for (n, v) in data.items() if n in shift}
        )

    def mergeF():
        nonlocal deletedFeatures
        Fs = api.Fs
        Es = api.Es

        indent(level=0)
        if mergeFeatures:
            info("merge features ...")
        indent(level=1, reset=True)

        inF = set()

        for outFeat, inFeats in mergeFeatures.items():
            data = {}
            inFeats = fitemize(inFeats)
            if all(f in origNodeFeatures for f in inFeats):
                featSrc = Fs
                featDst = nodeFeatures
            else:
                featSrc = Es
                featDst = edgeFeatures

            for inFeat in inFeats:
                for n, val in featSrc(inFeat).data.items():
                    data[n] = val
            featDst.setdefault(outFeat, {}).update(data)

            for inFeat in inFeats:
                inF.add(inFeat)
                if inFeat in featDst:
                    del featDst[inFeat]
        deletedFeatures |= inF

        if mergeFeatures:
            info(f"done (deleted {len(inF)} and added {len(mergeFeatures)} features)")
            indent(level=2)
            info(f"deleted {_rep(inF)}", tm=False)
            info(f"added   {_rep(mergeFeatures)}", tm=False)
        return True

    def deleteF():
        indent(level=0)
        if deleteFeatures:
            info("delete features ...")
        indent(level=1, reset=True)
        for feat in deleteFeatures:
            dest = (
                nodeFeatures
                if feat in origNodeFeatures
                else edgeFeatures
                if feat in origEdgeFeatures
                else None
            )
            if dest and feat in dest:
                del dest[feat]
            deletedFeatures.add(feat)

        if deleteFeatures:
            info(f"done ({len(deleteFeatures)} features)")
            indent(level=2)
            info(_rep(deleteFeatures), tm=False)
        return True

    def addF():
        indent(level=0)
        if addFeatures:
            info("add features ...")
        indent(level=1, reset=True)
        added = collections.defaultdict(set)
        for kind, dest in (
            (NODE, nodeFeatures),
            (EDGE, edgeFeatures),
        ):
            for feat, data in addFeatures.get(f"{kind}Features", {}).items():
                dest.setdefault(feat, {}).update(data)
                added[kind].add(feat)
        if addFeatures:
            info(
                f'done (added {len(added["node"])} node + {len(added["edge"])} edge features)'
            )
            indent(level=2)
            for kind, feats in sorted(added.items()):
                info(f"{kind} features: {_rep(feats)}")

        return True

    def mergeT():
        nonlocal deletedTypes

        indent(level=0)
        if mergeTypes:
            info("merge types ...")
        indent(level=1, reset=True)

        inT = set()

        for outType, inTypes in mergeTypes.items():
            info(f"Merging {outType}")
            withFeatures = type(inTypes) is dict

            for inType in inTypes:
                addFeatures = inTypes[inType] if withFeatures else {}
                addFeatures[OTYPE] = outType
                (nF, nT) = origNodeTypes[inType]
                for feat, val in addFeatures.items():
                    for n in range(nF, nT + 1):
                        nodeFeatures.setdefault(feat, {})[n] = val
                inT.add(inType)

        deletedTypes |= inT

        if mergeTypes:
            info(f"done (merged {len(mergeTypes)} node types)")
            indent(level=2)
            info(f"deleted {_rep(inT)}", tm=False)
            info(f"added   {_rep(mergeTypes)}", tm=False)
        return True

    def deleteT():
        nonlocal maxNode
        nonlocal shiftNeeded
        nonlocal ePrefix
        nonlocal eItem

        ePrefix = "Delete types: "
        indent(level=0)
        if deleteTypes:
            info("delete types ...")
        indent(level=1, reset=True)

        curShift = 0

        for nType, (nF, nT) in sorted(origNodeTypes.items(), key=lambda x: x[1][0]):
            eItem = f"{nType:<20}: "
            if nType in deleteTypes:
                curShift -= nT - nF + 1
                deletedTypes.add(nType)
                inf(f"remove: delete nodes {nF:>7}-{nT:>7}")
            else:
                nodeTypes[nType] = (nF + curShift, nT + curShift)
                for n in range(nF, nT + 1):
                    shift[n] = n + curShift
                inf(
                    f"keep:   shift  nodes {nF:>7}-{nT:>7} to   "
                    f"{nF + curShift:>7}-{nT + curShift:>7}"
                )

        for kind, upd in (
            (NODE, nodeFeatures),
            (EDGE, edgeFeatures),
        ):
            for feat, uData in upd.items():
                upd[feat] = shiftFeature(kind, feat, uData)

        maxNode = origMaxNode + curShift
        eItem = "max node: "
        inf(f"shifted from {origMaxNode} to {maxNode}")
        shiftNeeded = curShift != 0

        if deleteTypes:
            info(f"done ({len(deleteTypes)} types)")
            indent(level=2)
            info(_rep(deleteTypes), tm=False)
        return True

    def addT():
        nonlocal maxNode

        indent(level=0)
        if addTypes:
            info("add types ...")
        indent(level=1, reset=True)

        nodeMap = {}

        for nodeType, typeInfo in sorted(addTypes.items()):
            nF = typeInfo[NF]
            nT = typeInfo[NT]
            offset = maxNode - nF + 1
            nodeSlots = typeInfo[NS]

            data = {}
            newNodeMap = {}

            for n in range(nF, nT + 1):
                data[offset + n] = nodeType
                newNodeMap[n] = offset + n

            nodeFeatures.setdefault(OTYPE, {}).update(data)

            data = {}

            for n in range(nF, nT + 1):
                data[offset + n] = set(nodeSlots[n])

            edgeFeatures.setdefault(OSLOTS, {}).update(data)

            for feat, addData in typeInfo.get(NFS, {}).items():
                data = {}

                for n in range(nF, nT + 1):
                    value = addData.get(n, None)
                    if value is not None:
                        data[offset + n] = value

                nodeFeatures.setdefault(feat, {}).update(data)

            for feat, addData in typeInfo.get(EFS, {}).items():
                data = {}

                for n in range(nF, nT + 1):
                    value = addData.get(n, None)
                    if value:
                        newValue = shiftx(
                            value, offset=offset, nF=nF, nT=nT, nodeMap=nodeMap
                        )
                        if newValue:
                            data[offset + n] = newValue

                edgeFeatures.setdefault(feat, {}).update(data)

            maxNode += nT - nF + 1
            nodeMap = newNodeMap

        if addTypes:
            info(f"done ({len(addTypes)} types)")
            indent(level=2)
            info(_rep(addTypes), tm=False)
        return True

    def applyUpdates():
        nonlocal good
        nonlocal ePrefix
        nonlocal eItem
        nonlocal replaceSlotType
        Fs = api.Fs
        Es = api.Es

        indent(level=0)
        info("applying updates ...")
        indent(level=1, reset=True)

        mFeat = 0

        for kind, featSet, featSrc, featUpd, featOut in (
            (NODE, origNodeFeatures, Fs, nodeFeatures, nodeFeaturesOut),
            (EDGE, origEdgeFeatures, Es, edgeFeatures, edgeFeaturesOut),
        ):
            ePrefix = f"Shift {kind} feature: "

            allFeatSet = set() if onlyDeliverUpdatedFeatures else set(featSet)
            for feat in sorted((allFeatSet | set(featUpd)) - deletedFeatures):
                eItem = f"{feat:<20}: "
                outData = {}
                outMeta = {}
                if feat in featSet:
                    # inf("original feature")
                    featObj = featSrc(feat)
                    if feat != OSLOTS and kind == EDGE and featObj.doValues:
                        outMeta["edgeValues"] = True
                    outMeta.update(featObj.meta)
                    if shiftNeeded:
                        outData.update(shiftFeature(kind, feat, featObj))
                        mFeat += 1
                    else:
                        outData.update(featObj.items())
                if feat in featUpd:
                    # inf("new / updated feature")
                    outData.update(featUpd[feat])
                    if kind == EDGE:
                        aVal = next(iter(featUpd[feat].values()))
                        hasValues = type(aVal) is dict
                        if outMeta.get("edgeValues", False) != hasValues:
                            outMeta["edgeValues"] = hasValues
                if feat in featureMeta:
                    for k, v in featureMeta[feat].items():
                        if v is None:
                            if k in outMeta:
                                del outMeta[k]
                        else:
                            outMeta[k] = v

                featOut[feat] = outData
                metaDataOut[feat] = outMeta

        if replaceSlotType:
            if type(replaceSlotType) is str:
                ignoreSlotFeatures = ()
            else:
                (replaceSlotType, *ignoreSlotFeatures) = replaceSlotType
            ignoreSlotFeatures = set(ignoreSlotFeatures)

            ignoreRep = (
                f" while ignoring {ignoreSlotFeatures}" if ignoreSlotFeatures else ""
            )
            info(f"Replacing slot type {slotType} by {replaceSlotType}{ignoreRep}")

            # check replaceSlotType

            ePrefix = "Replace slot type: "
            eItem = f"{replaceSlotType}: "

            allTypes = (set(nodeTypes) - deletedTypes) | set(addTypes)

            if replaceSlotType not in allTypes:
                err("Node type does not exist")
            if replaceSlotType == slotType:
                err("Node type is already the slot type")
            if not good:
                return

            # map old slots to nodes of the new slot type

            currentOtype = nodeFeaturesOut[OTYPE]
            currentOslots = edgeFeaturesOut[OSLOTS]

            # We have to sort the nodes of the new slot type in the canonical order

            nextSlots = sorted(
                (
                    node
                    for (node, nType) in currentOtype.items()
                    if nType == replaceSlotType
                ),
                key=_canonical(currentOslots),
            )

            # Now we walk through the nodes of the new slot type and see
            # to what slots they are linked.
            # There might be old slots that are not linked to any of these nodes.
            # These old slots must be removed.

            currentSlotMap = {}
            removeNodes = set()

            for newSlot in nextSlots:
                for oldSlot in currentOslots[newSlot]:
                    currentSlotMap[oldSlot] = newSlot

            for oldSlot, nType in currentOtype.items():
                if nType == slotType:
                    if oldSlot not in currentSlotMap:
                        removeNodes.add(oldSlot)

            info(f"{len(removeNodes)} old {slotType}s do not map to {replaceSlotType}s")

            # All features (except those in ignoreSlotFeatures) on old slots
            # have to be extended to the new slots
            # If a new slot has conflicting feature values for the old slots
            # it is linked to, the first defined feature value will be taken.
            # Likewise, all edge features that involve old slots
            # have to be extended to the new slots.

            for feat, featData in nodeFeaturesOut.items():
                if feat == OTYPE:
                    continue
                if feat in ignoreSlotFeatures:
                    continue
                updates = {}
                for oldSlot, value in featData.items():
                    if oldSlot in removeNodes:
                        continue
                    nType = currentOtype[oldSlot]
                    if nType != slotType:
                        continue
                    newSlot = currentSlotMap[oldSlot]
                    currentVal = featData.get(newSlot, None)
                    if currentVal is None:
                        alreadyUpdated = updates.get(newSlot, None)
                        if alreadyUpdated is None:
                            updates[newSlot] = value
                if updates:
                    for node, val in updates.items():
                        featData[node] = val

            for feat, featData in edgeFeaturesOut.items():
                if feat == OSLOTS:
                    continue
                updates = {}
                for fromNode, toNodes in featData.items():
                    if fromNode in removeNodes:
                        continue
                    nTypeFrom = currentOtype[fromNode]
                    if nTypeFrom == slotType:
                        newFromNode = currentSlotMap[fromNode]
                    else:
                        newFromNode = fromNode
                    if type(toNodes) is dict:
                        for toNode, value in toNodes.items():
                            if toNode in removeNodes:
                                continue
                            nTypeTo = currentOtype[toNode]
                            if nTypeTo == slotType:
                                newToNode = currentSlotMap[toNode]
                            else:
                                newToNode = toNode
                            if nTypeFrom != slotType and nTypeTo != slotType:
                                continue
                            currentVals = featData.get(newFromNode, {})
                            if newToNode not in currentVals:
                                alreadyUpdateds = updates.get(newFromNode, {})

                                if newToNode not in alreadyUpdateds:
                                    doUpdate = True
                                else:
                                    alreadyVal = alreadyUpdateds[newToNode]
                                    if alreadyVal is None:
                                        doUpdate = value is not None
                                    else:
                                        doUpdate = False

                                if doUpdate:
                                    updates.setdefault(newFromNode, {})[
                                        newToNode
                                    ] = value
                    else:
                        for toNode in toNodes:
                            if toNode in removeNodes:
                                continue
                            nTypeTo = currentOtype[toNode]
                            if nTypeTo == slotType:
                                newToNode = currentSlotMap[toNode]
                            else:
                                newToNode = toNode
                            if nTypeFrom != slotType and nTypeTo != slotType:
                                continue
                            currentVals = featData.get(newFromNode, set())
                            if newToNode not in currentVals:
                                alreadyUpdateds = updates.get(newFromNode, set())

                                if newToNode not in alreadyUpdateds:
                                    updates.setdefault(newFromNode, set()).add(
                                        newToNode
                                    )
                if updates:
                    for fromNode, toNodes in updates.items():
                        if type(toNodes) is dict:
                            for toNode, val in toNodes.items():
                                featData.setdefault(fromNode, {})[toNode] = val
                        else:
                            for toNode in toNodes:
                                featData.setdefault(fromNode, set()).add(toNode)

            # link all nodes, except slot nodes and nodes of the new slot type to
            # new slots.
            # N.B. the new slots are still ordinary nodes, so this is just
            # the next version of oslots, not the final version
            # Gather the nodes that end up unlinked to new slots.

            nextOslots = {}

            for node, slots in currentOslots.items():
                newSlots = {currentSlotMap[s] for s in slots if s in currentSlotMap}
                if len(newSlots):
                    nextOslots[node] = newSlots
                else:
                    removeNodes.add(node)

            # build the final otype and oslots features
            # we will shuffle nodes and delete nodes, so we maintain a map

            newOtype = {}
            newOslots = {}
            newFromCurrent = {}
            newNode = 0

            # first the new slots

            for node in nextSlots:
                newNode += 1
                newFromCurrent[node] = newNode
                newOtype[newNode] = replaceSlotType

            # now the rest

            for node, nType in currentOtype.items():
                if nType == slotType or nType == replaceSlotType or node in removeNodes:
                    continue
                newNode += 1
                newFromCurrent[node] = newNode
                newOtype[newNode] = nType
                newOslots[newNode] = {newFromCurrent[s] for s in nextOslots[node]}

            # now apply the node mapping to the remaining node and edge features
            # we may have to delete features

            removeNodeFeatures = set()
            removeEdgeFeatures = set()

            for feat, featData in nodeFeaturesOut.items():
                if feat == OTYPE:
                    nodeFeaturesOut[OTYPE] = newOtype
                    continue

                newFeatData = {}
                for node, value in featData.items():
                    if node in removeNodes:
                        continue
                    if node not in newFromCurrent:
                        continue
                    newFeatData[newFromCurrent[node]] = value
                if len(newFeatData):
                    nodeFeaturesOut[feat] = newFeatData
                else:
                    removeNodeFeatures.add(feat)

            for feat, featData in edgeFeaturesOut.items():
                if feat == OSLOTS:
                    edgeFeaturesOut[OSLOTS] = newOslots
                    continue

                newFeatData = {}
                for fromNode, toNodes in featData.items():
                    if fromNode in removeNodes:
                        continue
                    newFromNode = newFromCurrent[fromNode]
                    if type(toNodes) is dict:
                        newToNodes = {}
                        for toNode, value in toNodes.items():
                            if toNode in removeNodes:
                                continue
                            newTNode = newFromCurrent[toNode]
                            newToNodes[newTNode] = value
                    else:
                        newToNodes = set()
                        for toNode in toNodes:
                            if toNode in removeNodes:
                                continue
                            newTNode = newFromCurrent[toNode]
                            newToNodes.add(newTNode)
                    if not len(newToNodes):
                        continue
                    newFeatData[newFromNode] = newToNodes

                if len(newFeatData):
                    edgeFeaturesOut[feat] = newFeatData
                else:
                    removeEdgeFeatures.add(feat)

            # remove empty features

            for feat in removeNodeFeatures:
                del nodeFeaturesOut[feat]
                if feat in metaDataOut:
                    del metaDataOut[feat]
            for feat in removeEdgeFeatures:
                del edgeFeaturesOut[feat]
                if feat in metaDataOut:
                    del metaDataOut[feat]

        otextMeta = {}
        otextMeta.update(meta(OTEXT))
        mK = 0
        if OTEXT in featureMeta:
            for k, v in featureMeta[OTEXT].items():
                if v is None:
                    if k in otextMeta:
                        del otextMeta[k]
                        mK += 1
                else:
                    if k not in otextMeta or otextMeta[k] != v:
                        otextMeta[k] = v
                        mK += 1
        metaDataOut[OTEXT] = otextMeta

        if mFeat or mK:
            fRep = f" (shifted {mFeat} features)" if mFeat else ""
            kRep = f" (adapted {mK} keys in otext)" if mK else ""
            info(f"done{fRep}{kRep}")

        return True

    def _canonical(oslots):
        def before(nodeA, nodeB):
            slotsA = oslots[nodeA]
            slotsB = oslots[nodeB]
            if slotsA == slotsB:
                return 0

            aWithoutB = slotsA - slotsB
            if not aWithoutB:
                return 1

            bWithoutA = slotsB - slotsA
            if not bWithoutA:
                return -1

            aMin = min(aWithoutB)
            bMin = min(bWithoutA)
            return -1 if aMin < bMin else 1

        return functools.cmp_to_key(before)

    def writeTf():
        indent(level=0)
        if targetVersion is None:
            versionMsg = "with the original version number"
        else:
            versionMsg = f"as version {targetVersion}"
            for feat in set(nodeFeaturesOut) | set(edgeFeaturesOut):
                metaDataOut.setdefault(feat, {})["version"] = targetVersion

        info(f"write TF data {versionMsg} ... ")
        indent(level=1, reset=True)
        TF = Fabric(locations=targetLocation, silent=silent)
        TF.save(
            metaData=metaDataOut,
            nodeFeatures=nodeFeaturesOut,
            edgeFeatures=edgeFeaturesOut,
            silent=silent,
        )
        return True

    def finalize():
        indent(level=0)
        info("all done")
        return True

    def process():
        for step in (
            prepare,
            mergeF,
            deleteF,
            addF,
            mergeT,
            deleteT,
            addT,
            applyUpdates,
            writeTf,
            finalize,
        ):
            if not step():
                return False
        return True

    result = process()
    return result
