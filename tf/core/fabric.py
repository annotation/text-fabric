"""
# `FabricCore`

The main class that works the core API is `tf.fabric.Fabric`.
In this module we define `FabricCore`, which contains most of the
functionality of `Fabric`.

It does not contain the volume support.
Volume support requires `tf.volumes.extract` and `tf.volumes.collect` which
need to load and save TF datasets, and loading and saving are Fabric
functionalities.

Hence a Fabric with volume support would lead to circular imports.
By leaving out volume support, volume support can use `FabricCore` instead of Fabric.
"""

import collections
from itertools import chain
from typing import Dict, Union, Set

from ..parameters import BANNER, VERSION, OTYPE, OSLOTS, OTEXT
from .data import Data, MEM_MSG
from .helpers import (
    itemize,
    fitemize,
    collectFormats,
    check32,
    console,
    makeExamples,
)
from .files import (
    expanduser as ex,
    LOCATIONS,
    setDir,
    expandDir,
    dirExists,
    normpath,
    splitExt,
    scanDir,
)
from .timestamp import Timestamp, SILENT_D, silentConvert
from .prepare import (
    levels,
    order,
    rank,
    levUp,
    levDown,
    boundary,
    characters,
    sections,
    structure,
)
from .computed import Computed
from .nodefeature import NodeFeature
from .edgefeature import EdgeFeature
from .otypefeature import OtypeFeature
from .oslotsfeature import OslotsFeature
from .api import (
    Api,
    addNodes,
    addOtype,
    addLocality,
    addText,
    addSearch,
)

# declare some types for type annotation
featureType = Union[str, int]
nodeFeatureDict = Dict[str, Dict[int, featureType]]
edgeFeatureDict = Dict[str, Dict[int, Union[Set[int], Dict[int, featureType]]]]
metaDataDict = Dict[str, Dict[str, str]]


OTEXT_DEFAULT = dict(sectionFeatures="", sectionTypes="")


PRECOMPUTE = (
    (0, "__levels__", levels, (OTYPE, OSLOTS, OTEXT)),
    (0, "__order__", order, (OTYPE, OSLOTS) + ("__levels__",)),
    (0, "__rank__", rank, (OTYPE, "__order__")),
    (0, "__levUp__", levUp, (OTYPE, OSLOTS) + ("__rank__",)),
    (0, "__levDown__", levDown, (OTYPE, "__levUp__", "__rank__")),
    (1, "__characters__", characters, (OTEXT,)),
    (0, "__boundary__", boundary, (OTYPE, OSLOTS) + ("__rank__",)),
    (
        2,
        "__sections__",
        sections,
        (OTYPE, OSLOTS, OTEXT) + ("__levUp__", "__levDown__", "__levels__"),
    ),
    (
        2,
        "__structure__",
        structure,
        (OTYPE, OSLOTS, OTEXT)
        + (
            "__rank__",
            "__levUp__",
        ),
    ),
)
"""Pre-computation steps.

Each step corresponds to a pre-computation task.

A task is specified by a tuple containing:

Parameters
----------
dep: boolean
    Whether the step is dependent on the presence of additional features.
    Only relevant for the pre-computation of section structure:
    that should only happen if there are section features.
name: string
    The name of the result of a pre-computed task.
    The result is a blob of data that can be loaded and compressed just as ordinary features.
function: function
    The function that performs the pre-computation task.
    These functions are defined in `tf.core.prepare`.
dependencies: strings
    The remaining parts of the tuple are the names of pre-computed features
    that must be coomputed before and whose results are passed as argument
    to the function that executes the pre-computation.

For a description of what the steps are for, see the functions
in `tf.core.prepare`.
"""
KIND = dict(__sections__="section", __structure__="structure")


class FabricCore:
    """Initialize the core API for a corpus.

    Top level management of

    *   locating TF feature files
    *   loading and saving feature data
    *   pre-computing auxiliary data
    *   caching pre-computed and compressed data

    TF is initialized for a corpus.
    It will search a set of directories and catalogue all `.tf` files it finds there.
    These are the features you can subsequently load.

    Here `directories` and `subdirectories` are strings with directory names
    separated by newlines, or iterables of directories.

    Parameters
    ----------
    locations: string | iterable of strings, optional
        The directories specified here are used as base locations
        in searching for TF feature files.
        In general, they will not searched directly, but certain subdirectories
        of them will be searched, specified by the `modules` parameter.

        Defaults:

            ~/Downloads/text-fabric-data
            ~/text-fabric-data
            ~/github/text-fabric-data

        So if you have stored your main TF dataset in
        `text-fabric-data` in one of these directories
        you do not have to pass a location to Fabric.

    modules: string | iterable of strings
        The directories specified in here are used as sub directories
        appended to the directories given by the `locations` parameter.

        All `.tf` files (non-recursively) in any `location/module`
        will be added to the feature set to be loaded in this session.
        The order in `modules` is important, because if a feature occurs in
        multiple modules, the last one will be chosen.
        In this way you can easily override certain features in one module
        by features in an other module of your choice.

        Default: `['']`

        So if you leave it out, TF will just search the paths specified
        in `locations`.

    silent: string, optional tf.core.timestamp.SILENT_D
        See `tf.core.timestamp.Timestamp`

    _withGc: boolean, optional True
        If False, it disables the Python garbage collector before
        loading features. Used to experiment with performance.


    !!! note "`otext@` in modules"
        If modules contain features with a name starting with `otext@`, then the format
        definitions in these features will be added to the format definitions in the
        regular `otext` feature (which is a `tf.parameters.WARP` feature).
        In this way, modules that define new features for text representation,
        also can add new formats to the Text-API.

    Returns
    -------
    object
        An object from which you can call up all the of methods of the core API.
    """

    def __init__(self, locations=None, modules=None, silent=SILENT_D, _withGc=True):
        silent = silentConvert(silent)
        self._withGc = _withGc
        self.silent = silent
        tmObj = Timestamp(silent=silent)
        self.tmObj = tmObj
        setSilent = tmObj.setSilent
        setSilent(silent)
        self.banner = BANNER
        """The banner Text-Fabric.

        Will be shown just after start up, if the silence is not `deep`.
        """

        self.version = VERSION
        """The version number of the TF library.
        """

        (on32, warn, msg) = check32()
        warning = tmObj.warning
        info = tmObj.info
        debug = tmObj.debug

        if on32:
            warning(warn, tm=False)
        if msg:
            info(msg, tm=False)
        debug(self.banner, tm=False)
        self.good = True

        if modules is None:
            modules = [""]
        elif type(modules) is str:
            modules = [normpath(x.strip()) for x in itemize(modules, "\n")]
        else:
            modules = [normpath(str(x)) for x in modules]
        self.modules = modules

        if locations is None:
            locations = LOCATIONS
        elif type(locations) is str:
            locations = [normpath(x.strip()) for x in itemize(locations, "\n")]
        else:
            locations = [normpath(str(x)) for x in locations]
        setDir(self)
        self.locations = []
        for loc in locations:
            self.locations.append(expandDir(self, loc))

        self.locationRep = "\n\t".join(
            "\n\t".join(f"{lc}/{f}" for f in self.modules) for lc in self.locations
        )
        self.featuresRequested = []
        self.features = {}
        """Dictionary of all features that TF has found, whether loaded or not.

        Under each feature name is all info about that feature.

        The best use of this is to get the metadata of features:

            TF.features['fff'].metaData

        This works for all features `fff` that have been found,
        whether the feature is loaded or not.

        If a feature is loaded, you can also use

        `F.fff.meta` of `E.fff.meta` depending on whether `fff` is a node feature
        or an edge feature.

        !!! caution "Do not print!"
            If a feature is loaded, its data is also in the feature info.
            This can be an enormous amount of information, and you can easily
            overwhelm your notebook if you print it.
        """

        self._makeIndex()

    def load(self, features, add=False, silent=SILENT_D):
        """Loads features from disk into RAM memory.

        Parameters
        ----------

        features: string | iterable
            Either a string containing space separated feature names, or an
            iterable of feature names.
            The feature names are just the names of `.tf` files
            without directory information and without extension.
        add: boolean, optional False
            The features will be added to the same currently loaded features, managed
            by the current API.
            Meant to be able to dynamically load features without reloading lots
            of features for nothing.
        silent: string, optional tf.core.timestamp.SILENT_D
            See `tf.core.timestamp.Timestamp`

        Returns
        -------
        boolean | object
            If `add` is `True` a boolean indicating success is returned.
            Otherwise, the result is a new `tf.core.api.Api`
            if the feature could be loaded, else `False`.
        """

        silent = silentConvert(silent)
        tmObj = self.tmObj
        isSilent = tmObj.isSilent
        setSilent = tmObj.setSilent
        indent = tmObj.indent
        debug = tmObj.debug
        warning = tmObj.warning
        error = tmObj.error
        cache = tmObj.cache
        reset = tmObj.reset
        featuresOnly = self.featuresOnly

        wasSilent = isSilent()
        setSilent(silent)
        indent(level=0, reset=True)
        self.sectionsOK = True
        self.structureOK = True
        self.good = True

        if self.good:
            featuresRequested = sorted(fitemize(features))
            if add:
                self.featuresRequested += featuresRequested
            else:
                self.featuresRequested = featuresRequested
            for fName in (OTYPE, OSLOTS, OTEXT):
                self._loadFeature(fName, optional=fName == OTEXT or featuresOnly)

        self.textFeatures = set()

        if self.good and not featuresOnly:
            if OTEXT in self.features:
                otextMeta = self.features[OTEXT].metaData
                for otextMod in self.features:
                    if otextMod.startswith(OTEXT + "@"):
                        self._loadFeature(otextMod)
                        otextMeta.update(self.features[otextMod].metaData)
                self.sectionFeats = itemize(otextMeta.get("sectionFeatures", ""), ",")
                self.sectionTypes = itemize(otextMeta.get("sectionTypes", ""), ",")
                self.structureFeats = itemize(
                    otextMeta.get("structureFeatures", ""), ","
                )
                self.structureTypes = itemize(otextMeta.get("structureTypes", ""), ",")
                (self.cformats, self.formatFeats) = collectFormats(otextMeta)

                if not (0 < len(self.sectionTypes) <= 3) or not (
                    0 < len(self.sectionFeats) <= 3
                ):
                    if not add:
                        warning(
                            f"Dataset without sections in {OTEXT}:"
                            f"no section functions in the T-API"
                        )
                    self.sectionsOK = False
                else:
                    self.textFeatures |= set(self.sectionFeats)
                    self.sectionFeatsWithLanguage = tuple(
                        f
                        for f in self.features
                        if f == self.sectionFeats[0]
                        or f.startswith(f"{self.sectionFeats[0]}@")
                    )
                    self.textFeatures |= set(self.sectionFeatsWithLanguage)
                if not self.structureTypes or not self.structureFeats:
                    if not add:
                        debug(
                            f"Dataset without structure sections in {OTEXT}:"
                            f"no structure functions in the T-API"
                        )
                    self.structureOK = False
                else:
                    self.textFeatures |= set(self.structureFeats)

                formatFeats = set(self.formatFeats)
                self.textFeatures |= formatFeats

                for fName in self.textFeatures:
                    self._loadFeature(fName, optional=fName in formatFeats)

                dep1Feats = self.dep1Feats
                if dep1Feats:
                    cformats = self.cformats
                    tFormats = {}
                    tFeats = set()
                    for (fmt, (otpl, tpl, featData)) in cformats.items():
                        feats = set(chain.from_iterable(x[0] for x in featData))
                        tFormats[fmt] = tuple(sorted(feats))
                        tFeats |= feats
                    tFeats = tuple(sorted(tFeats))
                    extraDependencies = [tFormats]
                    for tFeat in tFeats:
                        featData = self.features[tFeat].data
                        extraDependencies.append((tFeat, featData))
                    for cFeat in dep1Feats:
                        self.features[cFeat].dependencies += extraDependencies

            else:
                self.sectionsOK = False
                self.structureOK = False

        if self.good and not featuresOnly:
            self._precompute()

        if self.good:
            reset()
            for fName in self.featuresRequested:
                self._loadFeature(fName)
                if not self.good:
                    indent(level=0)
                    cache()
                    error("Not all features could be loaded / computed")
                    result = False
                    break
                reset()

        if self.good:
            if add:
                try:
                    self._updateApi()
                    result = True
                except MemoryError:
                    console(MEM_MSG)
                    result = False
            else:
                try:
                    result = self._makeApi()
                except MemoryError:
                    console(MEM_MSG)
                    result = False
        else:
            result = False

        setSilent(wasSilent)
        return result

    def explore(self, silent=SILENT_D, show=True):
        """Makes categorization of all features in the dataset.

        Parameters
        ----------
        silent: string, optional tf.core.timestamp.SILENT_D
            See `tf.core.timestamp.Timestamp`
        show: boolean, optional True
            If `False`, the resulting dictionary is delivered in `TF.featureSets`;
            if `True`, the dictionary is returned as function result.

        Returns
        -------
        dict | None
            A dictionary  with keys `nodes`, `edges`, `configs`, `computeds`.
            Under each key there is the set of feature names in that category.
            How this dictionary is delivered, depends on the parameter *show*.

        Notes
        -----
        !!! explanation "`configs`"
            These are configuration features, with metadata only, no data. E.g. `otext`.

        !!! explanation "`computeds`"
            These are blocks of pre-computed data, available under the `C` API,
            see `tf.core.computed.Computeds`.

        The sets do not indicate whether a feature is loaded or not.
        There are other functions that give you the loaded features:
        `tf.core.api.Api.Fall` for nodes and `tf.core.api.Api.Eall` for edges.
        """

        silent = silentConvert(silent)
        tmObj = self.tmObj
        isSilent = tmObj.isSilent
        setSilent = tmObj.setSilent
        info = tmObj.info

        wasSilent = isSilent()
        setSilent(silent)
        nodes = set()
        edges = set()
        configs = set()
        computeds = set()

        for (fName, fObj) in self.features.items():
            fObj.load(silent=silent, metaOnly=True)
            dest = None
            if fObj.method:
                dest = computeds
            elif fObj.isConfig:
                dest = configs
            elif fObj.isEdge:
                dest = edges
            else:
                dest = nodes
            dest.add(fName)
        info(
            "Feature overview: {} for nodes; {} for edges; {} configs; {} computed".format(
                len(nodes),
                len(edges),
                len(configs),
                len(computeds),
            )
        )
        self.featureSets = dict(
            nodes=nodes, edges=edges, configs=configs, computeds=computeds
        )
        setSilent(wasSilent)
        if show:
            return dict(
                (kind, tuple(sorted(kindSet)))
                for (kind, kindSet) in sorted(
                    self.featureSets.items(), key=lambda x: x[0]
                )
            )

    def loadAll(self, silent=SILENT_D):
        """Load all loadable features.

        Parameters
        ----------
        silent: string, optional tf.core.timestamp.SILENT_D
            See `tf.core.timestamp.Timestamp`
        """

        silent = silentConvert(silent)
        api = self.load("", silent=silent)
        allFeatures = self.explore(silent=silent, show=True)
        loadableFeatures = allFeatures["nodes"] + allFeatures["edges"]
        self.load(loadableFeatures, add=True, silent=silent)
        return api

    def clearCache(self):
        """Clears the cache of compiled TF data.

        TF pre-computes data for you, so that it can be loaded faster.
        If the original data is updated, TF detects it,
        and will recompute that data.

        But there are cases, when the algorithms of TF have changed,
        without any changes in the data, where you might want to clear the cache
        of pre-computed results.

        Calling this function just does it, and it is equivalent with manually removing
        all `.tfx` files inside the hidden `.tf` directory inside your dataset.

        !!! hint "No need to load"
            It is not needed to execute a `TF.load()` first.

        See Also
        --------
        tf.clean
        """

        for (fName, fObj) in self.features.items():
            fObj.cleanDataBin()

    def save(
        self,
        nodeFeatures: nodeFeatureDict = {},
        edgeFeatures: edgeFeatureDict = {},
        metaData: metaDataDict = {},
        location=None,
        module=None,
        silent=SILENT_D,
    ):
        """Saves newly generated data to disk as TF features, nodes and / or edges.

        If you have collected feature data in dictionaries, keyed by the
        names of the features, and valued by their feature data,
        then you can save that data to `.tf` feature files on disk.

        It is this easy to export new data as features:
        collect the data and metadata of the features and feed it in an orderly way
        to `TF.save()` and there you go.

        Parameters
        ----------
        nodeFeatures: dict of dict
            The data of a node feature is a dictionary with nodes as keys (integers!)
            and strings or numbers as (feature) values.
            This parameter holds all those dictionaries, keyed by feature name.

        edgeFeatures: dict of dict
            The data of an edge feature is a dictionary with nodes as keys, and sets or
            dictionaries as values. These sets should be sets of nodes (integers!),
            and these dictionaries should have nodes as keys and strings or numbers
            as values.
            This parameter holds all those dictionaries, keyed by feature name.

        metaData: dict of  dict
            The meta data for every feature to be saved is a key-value dictionary.
            This parameter holds all those dictionaries, keyed by feature name.

            !!! explanation "value types"
                The type of the feature values (`int` or `str`) should be specified
                under key `valueType`.

            !!! explanation "edge values"
                If you save an edge feature, and there are values in that edge feature,
                you have to say so, by specifying `edgeValues=True`
                in the metadata for that feature.

            !!! explanation "generic metadata"
                This parameter may also contain fields under the empty name.
                These fields will be added to all features in `nodeFeatures` and
                `edgeFeatures`.

            !!! explanation "configuration features"
                If you need to write the *configuration* feature `otext`,
                which is a metadata-only feature, just
                add the metadata under key `otext` in this parameter and make sure
                that `otext` is not a key in `nodeFeatures` nor in
                `edgeFeatures`.
                These fields will be written into the separate configuration
                feature `otext`, with no data associated.

        location: dict
            The (meta)data will be written to the very last directory that TF searched
            when looking for features (this is determined by the
            `locations` and `modules` parameters in `tf.fabric.Fabric`.

            If both `locations` and `modules` are empty, writing will take place
            in the current directory.

            But you can override it:

            If you pass `location=something`, TF will save in `something/mod`,
            where `mod` is the last member of the `modules` parameter of TF.

        module: dict
            This is an additional way of overriding the default location
            where TF saves new features. See the *location* parameter.

            If you pass `module=something`, TF will save in `loc/something`,
            where `loc` is the last member of the `locations` parameter of TF.

            If you pass `location=path1` and `module=path2`,
            TF will save in `path1/path2`.

        silent: string, optional tf.core.timestamp.SILENT_D
            See `tf.core.timestamp.Timestamp`
        """

        silent = silentConvert(silent)
        tmObj = self.tmObj
        isSilent = tmObj.isSilent
        setSilent = tmObj.setSilent
        indent = tmObj.indent
        info = tmObj.info
        error = tmObj.error

        good = True
        wasSilent = isSilent()
        setSilent(silent)
        indent(level=0, reset=True)
        self._getWriteLoc(location=location, module=module)
        configFeatures = dict(
            f
            for f in metaData.items()
            if f[0] != "" and f[0] not in nodeFeatures and f[0] not in edgeFeatures
        )
        info(
            "Exporting {} node and {} edge and {} configuration features to {}:".format(
                len(nodeFeatures),
                len(edgeFeatures),
                len(configFeatures),
                self.writeDir,
            )
        )
        todo = []
        for fName in sorted(nodeFeatures):
            todo.append((fName, nodeFeatures[fName], False, False))
        for fName in sorted(edgeFeatures):
            todo.append((fName, edgeFeatures[fName], True, False))
        for fName in sorted(configFeatures):
            todo.append((fName, configFeatures[fName], None, True))
        total = collections.Counter()
        failed = collections.Counter()
        maxSlot = None
        maxNode = None
        slotType = None
        if OTYPE in nodeFeatures:
            info(f"VALIDATING {OSLOTS} feature")
            otypeData = nodeFeatures[OTYPE]
            if type(otypeData) is tuple:
                (otypeData, slotType, maxSlot, maxNode) = otypeData
            elif 1 in otypeData:
                slotType = otypeData[1]
                maxSlot = max(n for n in otypeData if otypeData[n] == slotType)
                maxNode = max(otypeData)
        if OSLOTS in edgeFeatures:
            info(f"VALIDATING {OSLOTS} feature")
            oslotsData = edgeFeatures[OSLOTS]
            if type(oslotsData) is tuple:
                (oslotsData, maxSlot, maxNode) = oslotsData
            if maxSlot is None or maxNode is None:
                error(f"ERROR: cannot check validity of {OSLOTS} feature")
                good = False
            else:
                info(f"maxSlot={maxSlot:>11}")
                info(f"maxNode={maxNode:>11}")
                maxNodeInData = max(oslotsData)
                minNodeInData = min(oslotsData)

                mappedSlotNodes = []
                unmappedNodes = []
                fakeNodes = []

                start = min((maxSlot + 1, minNodeInData))
                end = max((maxNode, maxNodeInData))
                for n in range(start, end + 1):
                    if n in oslotsData:
                        if n <= maxSlot:
                            mappedSlotNodes.append(n)
                        elif n > maxNode:
                            fakeNodes.append(n)
                    else:
                        if maxSlot < n <= maxNode:
                            unmappedNodes.append(n)

                if mappedSlotNodes:
                    error(f"ERROR: {OSLOTS} maps slot nodes")
                    error(makeExamples(mappedSlotNodes), tm=False)
                    good = False
                if fakeNodes:
                    error(f"ERROR: {OSLOTS} maps nodes that are not in {OTYPE}")
                    error(makeExamples(fakeNodes), tm=False)
                    good = False
                if unmappedNodes:
                    error(f"ERROR: {OSLOTS} fails to map nodes:")
                    unmappedByType = {}
                    for n in unmappedNodes:
                        unmappedByType.setdefault(
                            otypeData.get(n, "_UNKNOWN_"), []
                        ).append(n)
                    for (nType, nodes) in sorted(
                        unmappedByType.items(),
                        key=lambda x: (-len(x[1]), x[0]),
                    ):
                        error(f"--- unmapped {nType:<10} : {makeExamples(nodes)}")
                    good = False

            if good:
                info(f"OK: {OSLOTS} is valid")

        for (fName, data, isEdge, isConfig) in todo:
            edgeValues = False
            fMeta = {}
            fMeta.update(metaData.get("", {}))
            fMeta.update(metaData.get(fName, {}))
            if fMeta.get("edgeValues", False):
                edgeValues = True
            if "edgeValues" in fMeta:
                del fMeta["edgeValues"]
            fObj = Data(
                f"{self.writeDir}/{fName}.tf",
                self.tmObj,
                data=data,
                metaData=fMeta,
                isEdge=isEdge,
                isConfig=isConfig,
                edgeValues=edgeValues,
            )
            tag = "config" if isConfig else "edge" if isEdge else "node"
            if fObj.save(nodeRanges=fName == OTYPE, overwrite=True, silent=silent):
                total[tag] += 1
            else:
                failed[tag] += 1
        indent(level=0)
        info(
            f"""Exported {total["node"]} node features"""
            f""" and {total["edge"]} edge features"""
            f""" and {total["config"]} config features"""
            f""" to {self.writeDir}"""
        )
        if len(failed):
            for (tag, nf) in sorted(failed.items()):
                error(f"Failed to export {nf} {tag} features")
            good = False

        setSilent(wasSilent)
        return good

    def _loadFeature(self, fName, optional=False):
        if not self.good:
            return False

        tmObj = self.tmObj
        isSilent = tmObj.isSilent
        error = tmObj.error

        silent = isSilent()
        if fName not in self.features:
            if not optional:
                error(f'Feature "{fName}" not available in\n{self.locationRep}')
                self.good = False
        else:
            if not self.features[fName].load(silent=silent, _withGc=self._withGc):
                self.good = False

    def _makeIndex(self):
        tmObj = self.tmObj
        info = tmObj.info
        debug = tmObj.debug
        warning = tmObj.warning

        self.features = {}
        self.featuresIgnored = {}
        tfFiles = {}
        for loc in self.locations:
            for mod in self.modules:
                dirF = normpath(f"{loc}/{mod}")
                if not dirExists(dirF):
                    continue
                with scanDir(dirF) as sd:
                    files = tuple(
                        e.name for e in sd if e.is_file() and e.name.endswith(".tf")
                    )
                for fileF in files:
                    (fName, ext) = splitExt(fileF)
                    tfFiles.setdefault(fName, []).append(f"{dirF}/{fileF}")
        for (fName, featurePaths) in sorted(tfFiles.items()):
            chosenFPath = featurePaths[-1]
            for featurePath in sorted(set(featurePaths[0:-1])):
                if featurePath != chosenFPath:
                    self.featuresIgnored.setdefault(fName, []).append(featurePath)
            self.features[fName] = Data(chosenFPath, self.tmObj)
        self._getWriteLoc()
        debug(
            "{} features found and {} ignored".format(
                len(tfFiles),
                sum(len(x) for x in self.featuresIgnored.values()),
            ),
            tm=False,
        )

        self.featuresOnly = False

        if OTYPE not in self.features or OSLOTS not in self.features:
            info(
                f"Not all of the warp features {OTYPE} and {OSLOTS} "
                f"are present in\n{self.locationRep}"
            )
            info("Only the Feature and Edge APIs will be enabled")
            self.featuresOnly = True
        if OTEXT in self.features:
            self._loadFeature(OTEXT, optional=True)
        else:
            info((f'Warp feature "{OTEXT}" not found. Working without Text-API\n'))
            self.features[OTEXT] = Data(
                f"{OTEXT}.tf",
                self.tmObj,
                isConfig=True,
                metaData=OTEXT_DEFAULT,
            )
            self.features[OTEXT].dataLoaded = True

        good = True
        if not self.featuresOnly:
            self.warpDir = self.features[OTYPE].dirName
            self.precomputeList = []
            self.dep1Feats = []
            for (dep2, fName, method, dependencies) in PRECOMPUTE:
                thisGood = True
                if dep2 and OTEXT not in self.features:
                    continue
                if dep2 == 1:
                    self.dep1Feats.append(fName)
                elif dep2 == 2:
                    otextMeta = self.features[OTEXT].metaData
                    sFeatures = f"{KIND[fName]}Features"
                    sFeats = tuple(itemize(otextMeta.get(sFeatures, ""), ","))
                    dependencies = dependencies + sFeats
                for dep in dependencies:
                    if dep not in self.features:
                        warning(
                            "Missing dependency for computed data feature "
                            f'"{fName}": "{dep}"'
                        )
                        thisGood = False
                if not thisGood:
                    good = False
                self.features[fName] = Data(
                    f"{self.warpDir}/{fName}.x",
                    self.tmObj,
                    method=method,
                    dependencies=[self.features.get(dep, None) for dep in dependencies],
                )
                self.precomputeList.append((fName, dep2))
        self.good = good

    def _getWriteLoc(self, location=None, module=None):
        writeLoc = (
            ex(location)
            if location is not None
            else ""
            if len(self.locations) == 0
            else self.locations[-1]
        )
        writeMod = (
            module
            if module is not None
            else ""
            if len(self.modules) == 0
            else self.modules[-1]
        )
        self.writeDir = (
            f"{writeLoc}{writeMod}"
            if writeLoc == "" or writeMod == ""
            else f"{writeLoc}/{writeMod}"
        )

    def _precompute(self):
        tmObj = self.tmObj
        isSilent = tmObj.isSilent
        good = True

        for (fName, dep2) in self.precomputeList:
            ok = getattr(self, f'{fName.strip("_")}OK', False)
            if dep2 == 2 and not ok:
                continue
            if not self.features[fName].load(silent=isSilent()):
                good = False
                break
        self.good = good

    def _makeApi(self):
        if not self.good:
            return None

        tmObj = self.tmObj
        isSilent = tmObj.isSilent
        indent = tmObj.indent
        debug = tmObj.debug
        featuresOnly = self.featuresOnly

        silent = isSilent()
        api = Api(self)
        api.featuresOnly = featuresOnly

        if not featuresOnly:
            w0info = self.features[OTYPE]
            w1info = self.features[OSLOTS]

        if not featuresOnly:
            setattr(api.F, OTYPE, OtypeFeature(api, w0info.metaData, w0info.data))
            setattr(api.E, OSLOTS, OslotsFeature(api, w1info.metaData, w1info.data))

        requestedSet = set(self.featuresRequested)

        for fName in self.features:
            fObj = self.features[fName]
            if fObj.dataLoaded and not fObj.isConfig:
                if fObj.method:
                    if not featuresOnly:
                        feat = fName.strip("_")
                        ok = getattr(self, f"{feat}OK", False)
                        ap = api.C
                        if fName in [
                            fn
                            for (fn, dep2) in self.precomputeList
                            if not dep2 == 2 or ok
                        ]:
                            setattr(ap, feat, Computed(api, fObj.data))
                        else:
                            fObj.unload()
                            if hasattr(ap, feat):
                                delattr(api.C, feat)
                else:
                    if fName in requestedSet | self.textFeatures:
                        if fName in (OTYPE, OSLOTS, OTEXT):
                            continue
                        elif fObj.isEdge:
                            setattr(
                                api.E,
                                fName,
                                EdgeFeature(
                                    api, fObj.metaData, fObj.data, fObj.edgeValues
                                ),
                            )
                        else:
                            setattr(
                                api.F, fName, NodeFeature(api, fObj.metaData, fObj.data)
                            )
                    else:
                        if (
                            fName in (OTYPE, OSLOTS, OTEXT)
                            or fName in self.textFeatures
                        ):
                            continue
                        elif fObj.isEdge:
                            if hasattr(api.E, fName):
                                delattr(api.E, fName)
                        else:
                            if hasattr(api.F, fName):
                                delattr(api.F, fName)
                        fObj.unload()
        if not featuresOnly:
            addOtype(api)
            addNodes(api)
            addLocality(api)
            addText(api)
            addSearch(api, silent)
        indent(level=0)
        debug("All features loaded / computed - for details use TF.isLoaded()")
        self.api = api
        setattr(self, "isLoaded", self.api.isLoaded)
        return api

    def _updateApi(self):
        if not self.good:
            return None
        api = self.api
        tmObj = self.tmObj
        indent = tmObj.indent
        debug = tmObj.debug

        requestedSet = set(self.featuresRequested)

        for fName in self.features:
            fObj = self.features[fName]
            if fObj.dataLoaded and not fObj.isConfig:
                if not fObj.method:
                    if fName in requestedSet | self.textFeatures:
                        if fName in (OTYPE, OSLOTS, OTEXT):
                            continue
                        elif fObj.isEdge:
                            apiFobj = EdgeFeature(
                                api, fObj.metaData, fObj.data, fObj.edgeValues
                            )
                            setattr(api.E, fName, apiFobj)
                        else:
                            apiFobj = NodeFeature(api, fObj.metaData, fObj.data)
                            setattr(api.F, fName, apiFobj)
                    else:
                        if (
                            fName in (OTYPE, OSLOTS, OTEXT)
                            or fName in self.textFeatures
                        ):
                            continue
                        elif fObj.isEdge:
                            if hasattr(api.E, fName):
                                delattr(api.E, fName)
                        else:
                            if hasattr(api.F, fName):
                                delattr(api.F, fName)
                        fObj.unload()
        indent(level=0)
        debug("All additional features loaded - for details use TF.isLoaded()")
