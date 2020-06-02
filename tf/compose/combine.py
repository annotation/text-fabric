"""
.. include:: ../../docs/compose/combine.md
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


def combine(
    locations,
    targetLocation,
    componentType=None,
    componentFeature=None,
    mergeTypes=None,
    featureMeta=None,
    silent=False,
):
    """Creates a new TF data source out of a number of other ones.

    You may pass as many component data sources as you want.

    The combination will be the union of all nodes of the components,
    rearranged according to their types, where node types with the
    same names will be merged.

    The slots of the result are the concatenation of the slots of the
    components, which must all have the same slot type.

    The node and edge features will be remapped, so that they have
    the same values in the combined data as they had in the individual
    components.

    Optionally, nodes corresponding to the components themselves will be
    added to the combined result.

    Care will be taken of the metadata of the features and the contents
    of the `otext.tf` feature, which consists of metadata only.

    All details of the combination can be steered by means of parameters.

    Parameters
    ----------

    locations: tuple of (string or tuple)
        You can either pass just the locations of the components,
        or you can give them a name and pass `(name, location)` instead.
        If you do not give a name to a component, its location will be used as name.

    targetLocation: string
        The directory into which the feature files of the combined dataset
        will be written.

    componentType, componentFeature: string, optional `None`
        If a string value for one of these is passed, a new node type will be added,
        with nodes for each component.
        There will also be a new feature, that assigns the name of a component
        to the node of that component.

        The name of the new node type is the value of `componentType`
        if it is a non-empty string, else it is the value of `componentFeature`.

        The name of the new feature is `componentFeature`
        if it is a non-empty string, else it is the value of `componentType`.

        !!! caution "componentType must be fresh"
            It is an error if the `componentType` is a node type that already
            occurs in one of the components.

        !!! note "componentFeature may exist"
            The `componentFeature` may already exist in one or more components.
            In that case the new feature values for nodes of `componentType` will
            just be added to it.

        Example
        -------
            combine(
                ('banks', 'banks/tf/0.2'),
                ('river', 'banks/tf/0.4'),
                'riverbanks/tf/1.0',
                componentType='volume',
                componentFeature='vol',
            )

        This results of a dataset with nodes and features from the components
        found at the indicated places on your file system.
        After combination, the components are visible in the data set as nodes
        of type `volume`, and the feature `vol` provides the names `banks` and `river`
        for those nodes.

    featureMeta: dict, optional `None`
        The meta data of the components involved will be merged.
        If feature metadata of the same feature is encountered in different components,
        and if components specify different values for the same keys,
        the different values will be stored under a key with the name of
        the component appended to the key, separated by a `!`.

        The special metadata field `valueType` will just be reduced to one single value `str`
        if some components have it as `str` and others as `int`.
        If the components assign the same value type to a feature, that value type
        will be assigned to the combined feature.

        If you want to assign other meta data to specific features,
        or pass meta data for new features that orginate from the merging process,
        you can pass them in the parameter `featureMeta` as in the following example,
        where we pass meta data for a feature called `level` with integer values.

        The contents of the `otext.tf` features are also metadata,
        and their contents will be merged in exactly the same way.

        So if the section/structure specifications and the formats are not
        the same for all components, you will see them spread out
        in fields qualified by the component name with a `!` sign between
        the key and the component.

        But you can add new specifications explicitly,
        as meta data of the `otext` feature.
        by passing them as keyword arguments.
        They will be passed directly to the combined `otext.tf` feature
        and will override anything with the same key
        that is already in one of the components.

    silent: boolean, optional `False`
        Suppress or enable informational messages.

    Example
    -------
        combine(
            ('banks', 'banks/tf/0.2'),
            ('river', 'banks/tf/0.4'),
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
        combine(
            ('banks', 'banks/tf/0.2'),
            ('river', 'banks/tf/0.4'),
            'riverbanks/tf/1.0',
            featureMeta=dict(
                otext=dict(
                    componentType='volume',
                    componentFeature='vol',
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

    if not dirEmpty(targetLocation):
        error(
            f"Output directory is not empty. Clean it or remove it or choose another location",
            tm=False,
        )
        return False

    locations = sorted(locations)
    nodeTypesComp = collections.defaultdict(dict)
    slotTypes = collections.defaultdict(dict)
    slotType = None
    offsets = collections.defaultdict(dict)
    nodeTypes = {}
    nodeFeatures = {}
    edgeFeatures = {}
    componentOslots = {}
    componentOtype = {}
    componentValue = collections.defaultdict(dict)
    metaData = collections.defaultdict(dict)
    if componentType:
        if not componentFeature:
            componentFeature = componentType
    else:
        if componentFeature:
            componentType = componentFeature

    srcs = {0: componentType}
    locs = {0: targetLocation}
    for (i, loc) in enumerate(locations):
        if type(loc) is str:
            locs[i + 1] = loc
            srcs[i + 1] = loc
        else:
            (name, loc) = loc
            locs[i + 1] = loc
            srcs[i + 1] = name
    locItems = sorted(x for x in locs.items() if x[0])

    def getMetas():
        meta = collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(set))
        )

        for (feat, keys) in featureMeta.items():
            for (key, value) in keys.items():
                if value is not None:
                    meta[feat][key][value] = {0}

        if componentFeature:
            meta[componentFeature]["valueType"]["str"] = {0}
            meta[componentFeature]["description"][f"label of {componentType}"] = {0}

        for (i, loc) in locItems:
            TF = Fabric(locations=loc, silent=silent)
            for (feat, fObj) in TF.features.items():
                if fObj.method:
                    continue
                fObj.load(metaOnly=True, silent=silent or True)
                thisMeta = fObj.metaData
                for (k, v) in thisMeta.items():
                    meta[feat][k][v].add(i)

        for (feat, ks) in meta.items():
            for (k, vs) in ks.items():
                isGenerated = k in GENERATED
                if k == "valueType":
                    if len(vs) > 1:
                        warning(
                            f"WARNING: {feat}: valueType varies in components; will be str",
                            tm=False,
                        )
                    else:
                        metaData[feat][k] = sorted(vs)[0]
                elif len(vs) == 1 and not isGenerated:
                    metaData[feat][k] = sorted(vs)[0]
                else:
                    hasCombinedValue = False
                    for (v, iis) in vs.items():
                        for i in iis:
                            if i == 0 and not isGenerated:
                                hasCombinedValue = True
                                key = k
                            else:
                                key = f"{k}!{srcs[i]}"
                            metaData[feat][key] = v
                    if not hasCombinedValue and not isGenerated:
                        warning(
                            f"WARNING: {feat}.{k} metadata varies across sources",
                            tm=False,
                        )

        return True

    def getNtypes():
        nonlocal slotType
        nonlocal slotTypes

        clashes = set()

        good = True
        indent(level=1, reset=True)
        maxSlot = 0
        maxNode = 0

        for (i, loc) in locItems:
            info(f"\r{i:>3} {os.path.basename(loc)})", nl=False)
            TF = Fabric(locations=loc, silent=silent)
            api = TF.load("", silent=silent)
            if not api:
                good = False
                continue
            C = api.C
            nTypeInfo = C.levels.data
            for (t, (nType, av, nF, nT)) in enumerate(nTypeInfo):
                if nType == componentType:
                    clashes.add(i)
                if t == len(nTypeInfo) - 1:
                    slotTypes[nType][i] = (1, nT)
                    maxSlot = nT
                    maxNode = nT
                else:
                    nodeTypesComp[nType][i] = (nF, nT)
                    if nT > maxNode:
                        maxNode = nT
            if componentType:
                nodeTypesComp[componentType][i] = (maxNode + 1, maxNode + 1)
                componentOslots[i] = maxSlot
                componentOtype[i] = maxNode + 1
                componentValue[i][maxNode + 1] = srcs[i]
        if len(slotTypes) > 1:
            slotRep = ", ".join(sorted(slotTypes))
            error(f"Multiple slot types: {slotRep}", tm=False)
            good = False
        commonTypes = set(slotTypes) & set(nodeTypesComp)
        if len(commonTypes):
            error(
                f"Some node types are slots in one source and non slots in another",
                tm=False,
            )
            error(", ".sorted(commonTypes), tm=False)
            good = False
        if clashes:
            clashRep = ", ".join(f"{srcs[i]}" for i in clashes)
            error(
                f"Component type {componentType} occurs inside components {clashRep}",
                tm=False,
            )
            good = False
        if good:
            slotType = list(slotTypes)[0]
            nodeTypesComp[slotType] = slotTypes[slotType]
            slotTypes = set(slotTypes[slotType])
        info("\r", tm=False, nl=False)
        info("done")
        return good

    def getOffsets():
        curOffset = 0
        for i in sorted(slotTypes):
            offsets[slotType][i] = curOffset
            curOffset += nodeTypesComp[slotType][i][1]
        nodeTypes[slotType] = (1, curOffset)

        for (nType, boundaries) in sorted(nodeTypesComp.items()):
            if nType == slotType:
                continue
            for (i, (nF, nT)) in boundaries.items():
                offsets[nType][i] = curOffset - nF + 1
                curOffset += nT - nF + 1

        for (nType, offs) in offsets.items():
            boundaries = nodeTypesComp[nType]
            nF = min(offs[i] + boundaries[i][0] for i in boundaries)
            nT = max(offs[i] + boundaries[i][1] for i in boundaries)
            nodeTypes[nType] = (nF, nT)
        return True

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
                isOtype = feat == OTYPE
                data = {}
                for (nType, boundaries) in nodeTypesComp.items():
                    if i not in boundaries:
                        continue
                    (nF, nT) = boundaries[i]
                    cType = None
                    if nType == componentType and isOtype:
                        cType = componentType
                    thisOffset = offsets[nType][i]
                    for n in range(nF, nT + 1):
                        val = fObj.v(n) if cType is None else cType
                        if val is not None:
                            data[thisOffset + n] = val
                nodeFeatures.setdefault(feat, {}).update(data)

            if componentFeature:
                data = {}
                boundaries = nodeTypesComp[componentType]
                if i in boundaries:
                    (nF, nT) = boundaries[i]
                    thisOffset = offsets[componentType][i]
                    for n in range(nF, nT + 1):
                        val = componentValue[i][n]
                        if val is not None:
                            data[thisOffset + n] = val
                    nodeFeatures.setdefault(componentFeature, {}).update(data)

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
                    if nType == componentType and isOslots:
                        cSlots = set(range(1, componentOslots[i] + 1))
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
        info("inspect metadata ...")
        if not getMetas():
            return False
        info("determine nodetypes ...")
        if not getNtypes():
            return False
        info("compute offsets ...")
        if not getOffsets():
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
