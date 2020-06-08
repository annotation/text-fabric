"""
.. include:: ../docs/main/fabric.md
"""

import os

import collections
from .parameters import VERSION, NAME, APIREF, LOCATIONS
from .core.data import Data, WARP, WARP2_DEFAULT, MEM_MSG
from .core.helpers import (
    itemize,
    setDir,
    expandDir,
    collectFormats,
    cleanName,
    check32,
    console,
    makeExamples,
)
from .core.timestamp import Timestamp
from .core.prepare import (
    levels,
    order,
    rank,
    levUp,
    levDown,
    boundary,
    sections,
    structure,
)
from .core.computed import Computed
from .core.nodefeature import NodeFeature
from .core.edgefeature import EdgeFeature
from .core.otypefeature import OtypeFeature
from .core.oslotsfeature import OslotsFeature
from .core.api import (
    Api,
    addNodes,
    addOtype,
    addLocality,
    addText,
    addSearch,
)
from .convert.mql import MQL, tfFromMql


PRECOMPUTE = (
    (False, "__levels__", levels, WARP),
    (False, "__order__", order, WARP[0:2] + ("__levels__",)),
    (False, "__rank__", rank, (WARP[0], "__order__")),
    (False, "__levUp__", levUp, WARP[0:2] + ("__rank__",)),
    (False, "__levDown__", levDown, (WARP[0], "__levUp__", "__rank__")),
    (False, "__boundary__", boundary, WARP[0:2] + ("__rank__",)),
    (True, "__sections__", sections, WARP + ("__levUp__", "__levels__")),
    (True, "__structure__", structure, WARP + ("__rank__", "__levUp__",)),
)
"""Precomputation steps.

Each step corresponds to a precomputation task.

A task is specified by a tuple containing:

Parameters
----------
dep: boolean
    Whether the step is dependent on the presence of additional features.
    Only relevant for the precomputation of section structure:
    that should only happen if there are section features.
name: string
    The name of the result of a precomputed task.
    The result is a blob of data that can be loaded and compressed just as ordinary features.
function: function
    The function that performs the precomputation task.
    These functions are defined in `tf.core.prepare`.
dependencies: strings
    The remaining parts of the tuple are the names of precomputed features
    that must be coomputed before and whose results are passed as argument
    to the function that executes the precomputation.

For a description of what the steps are for, see the functions
in `tf.core.prepare`.
"""
KIND = dict(__sections__="section", __structure__="structure")


class Fabric(object):
    """Initialize the core API for a corpus.

    Top level management of

    *   locating tf feature files
    *   loading and saving feature data
    *   precomputing auxiliary data
    *   caching precomputed and compressed data

    Text-Fabric is initialized for a corpus.
    It will search a set of directories and catalog all `.tf` files it finds there.
    These are the features you can subsequently load.

    Here `directories` and `subdirectories` are strings with directory names
    separated by newlines, or iterables of directories.

    Parameters
    ----------
    locations: string | iterable of strings, optional
        The directories specified here are used as base locations
        in searching for tf feature files.
        In general, they will not searched directly, but certain subdirectories
        of them will be searched, specified by the `modules` parameter.

        Defaults:

            ~/Downloads/text-fabric-data
            ~/text-fabric-data
            ~/github/text-fabric-data

        So if you have stored your main Text-Fabric dataset in
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

        So if you leave it out, Text-Fabric will just search the paths specified
        in `locations`.

    silent:
        If `True` is passed, banners and normal progress messages are suppressed.
        If `'deep'` is passed, all informational and warning messages are suppressed.
        Errors still pass through.

    !!! note "otext@ in modules"
        If modules contain features with a name starting with `otext@`, then the format
        definitions in these features will be added to the format definitions in the
        regular `otext` feature (which is a `tf.core.data.WARP` feature).
        In this way, modules that define new features for text representation,
        also can add new formats to the Text-API.

    Returns
    -------
    object
        An object from which you can call up all the of methods of the core API.
    """

    def __init__(self, locations=None, modules=None, silent=False):

        self.silent = silent
        tmObj = Timestamp()
        self.tmObj = tmObj
        setSilent = tmObj.setSilent
        setSilent(silent)
        self.banner = f"This is {NAME} {VERSION}"
        """The banner the Text-Fabric.

        Will be shown just after start up, if the silence is not `deep`.
        """

        self.version = VERSION
        """The version number of the Text-Fabric library.
        """

        (on32, warn, msg) = check32()
        warning = tmObj.warning
        info = tmObj.info

        if on32:
            warning(warn, tm=False)
        if msg:
            info(msg, tm=False)
        info(
            f"""{self.banner}
Api reference : {APIREF}
""",
            tm=False,
        )
        self.good = True

        if modules is None:
            modules = [""]
        if type(modules) is str:
            modules = [x.strip() for x in itemize(modules, "\n")]
        self.modules = modules

        if locations is None:
            locations = LOCATIONS
        if type(locations) is str:
            locations = [x.strip() for x in itemize(locations, "\n")]
        setDir(self)
        self.locations = []
        for loc in locations:
            self.locations.append(expandDir(self, loc))

        self.locationRep = "\n\t".join(
            "\n\t".join(f"{l}/{f}" for f in self.modules) for l in self.locations
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

    def load(self, features, add=False, silent=None):
        """Loads features from disk into RAM memory.

        Parameters
        ----------

        features: string | iterable
            Either a string containing space separated feature names, or an
            iterable of feature names.
            The feature names are just the names of `.tf` files
            without directory information and without extension.
        add: boolean, optional `False`
            The features will be added to the same currently loaded features, managed
            by the current API.
            Meant to be able to dynamically load features without reloading lots
            of features for nothing.
        silent: boolean, optional `None`
            If `False`, the features will be loaded rather silently,
            most messages will be suppressed.
            Time consuming operations will always be announced,
            so that you know what Text-Fabric is doing.
            If `True` is passed, all informational messages will be suppressed.
            This is handy I you want to load data as part of other methods, on-the-fly.

        Returns
        -------
        boolean | object
            If `add` is `True` nothing is returned. Otherwise,
            the result is a new `tf.core.api.Api` if the feature could be loaded,
            else `False`.
        """

        tmObj = self.tmObj
        isSilent = tmObj.isSilent
        setSilent = tmObj.setSilent
        indent = tmObj.indent
        info = tmObj.info
        warning = tmObj.warning
        error = tmObj.error
        cache = tmObj.cache

        if silent is not None:
            wasSilent = isSilent()
            setSilent(silent)
        indent(level=0, reset=True)
        info("loading features ...")
        self.sectionsOK = True
        self.structureOK = True
        self.good = True
        if self.good:
            featuresRequested = (
                itemize(features) if type(features) is str else sorted(features)
            )
            if add:
                self.featuresRequested += featuresRequested
            else:
                self.featuresRequested = featuresRequested
            for fName in list(WARP):
                self._loadFeature(fName, optional=fName == WARP[2])
        if self.good:
            self.textFeatures = set()
            if WARP[2] in self.features:
                otextMeta = self.features[WARP[2]].metaData
                for otextMod in self.features:
                    if otextMod.startswith(WARP[2] + "@"):
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
                            f"Dataset without sections in {WARP[2]}:"
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
                        info(
                            f"Dataset without structure sections in {WARP[2]}:"
                            f"no structure functions in the T-API"
                        )
                    self.structureOK = False
                else:
                    self.textFeatures |= set(self.structureFeats)

                self.textFeatures |= set(self.formatFeats)

                for fName in self.textFeatures:
                    self._loadFeature(fName)

            else:
                self.sectionsOK = False
                self.structureOK = False

        if self.good:
            self._precompute()
        if self.good:
            for fName in self.featuresRequested:
                self._loadFeature(fName)
        if not self.good:
            indent(level=0)
            error("Not all features could be loaded/computed")
            cache()
            result = False
        elif add:
            try:
                self._updateApi()
            except MemoryError:
                console(MEM_MSG)
                result = False
        else:
            try:
                result = self._makeApi()
            except MemoryError:
                console(MEM_MSG)
                result = False
        if silent is not None:
            setSilent(wasSilent)
        if not add:
            return result

    def explore(self, silent=None, show=True):
        """Makes categorization of all features in the dataset.

        Parameters
        ----------
        silent: boolean, optional `None`
            If `False` a message containing the total numbers of features
            is issued.
        show: boolean, optional `True`
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
        !!! explanation "configs"
            These are config features, with metadata only, no data. E.g. `otext`.

        !!! explanation "computeds"
            These are blocks of precomputed data, available under the `C` API,
            see `tf.core.computed.Computeds`.

        The sets do not indicate whether a feature is loaded or not.
        There are other functions that give you the loaded features:
        `tf.core.api.Api.Fall` for nodes and `tf.core.api.Api.Eall` for edges.
        """

        tmObj = self.tmObj
        isSilent = tmObj.isSilent
        setSilent = tmObj.setSilent
        info = tmObj.info

        if silent is not None:
            wasSilent = isSilent()
            setSilent(silent)
        nodes = set()
        edges = set()
        configs = set()
        computeds = set()
        for (fName, fObj) in self.features.items():
            fObj.load(metaOnly=True)
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
                len(nodes), len(edges), len(configs), len(computeds),
            )
        )
        self.featureSets = dict(
            nodes=nodes, edges=edges, configs=configs, computeds=computeds
        )
        if silent is not None:
            setSilent(wasSilent)
        if show:
            return dict(
                (kind, tuple(sorted(kindSet)))
                for (kind, kindSet) in sorted(
                    self.featureSets.items(), key=lambda x: x[0]
                )
            )

    def loadAll(self, silent=None):
        """Load all loadable features.

        Parameters
        ----------
        silent: boolean, optional `None`
            TF is silent if you specified `silent=True` in a preceding
            `TF=Fabric()` call.
            But if you did not, you can also pass `silent=True` to this call.
        """

        api = self.load("", silent=silent)
        allFeatures = self.explore(silent=silent or True, show=True)
        loadableFeatures = allFeatures["nodes"] + allFeatures["edges"]
        self.load(loadableFeatures, add=True, silent=silent)
        return api

    def clearCache(self):
        """Clears the cache of compiled TF data.

        Text-Fabric precomputes data for you, so that it can be loaded faster.
        If the original data is updated, Text-Fabric detects it,
        and will recompute that data.

        But there are cases, when the algorithms of Text-Fabric have changed,
        without any changes in the data, where you might want to clear the cache
        of precomputed results.

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
        nodeFeatures={},
        edgeFeatures={},
        metaData={},
        location=None,
        module=None,
        silent=None,
    ):
        """Saves newly generated data to disk as TF features, nodes and/or edges.

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

        metadata: dict of  dict
            The meta data for every feature to be saved is a key-value dictionary.
            This parameter holds all those dictionaries, keyed by feature name.

            !!! explanation "value types"
                The type of the feature values ('int' or 'str') should be specified
                under key `valueType`.

            !!! explanation "edge values"
                If you save an edge feature, and there are values in that edge feature,
                you have to say so, by specifying `edgeValues=True`
                in the metadata for that feature.

            !!! explanation "generic metadata"
                This parameter may also contain fields under the empty name.
                These fields will be added to all features in `nodeFeatures` and
                `edgeFeatures`.

            !!! explanation "config features"
                If you need to write the *config* feature `otext`,
                which is a metadata-only feature, just
                add the metadata under key `otext` in this parameter and make sure
                that `otext` is not a key in `nodeFeatures` nor in
                `edgeFeatures`.
                These fields will be written into the separate config feature `otext`,
                with no data associated.

        location: dict
            The (meta)data will be written to the very last directory that TF searched
            when looking for features (this is determined by the
            `locations` and `modules` parameters in `tf.fabric.Fabric`.

            If both `locations` and `modules` are empty, writing will take place
            in the current directory.

            But you can override it:

            If you pass `location=something`, TF will save in `something/mod`,
            where `mod` is the last meber of the `modules` parameter of TF.

        module: dict
            This is an additional way of overriding the default location
            where TF saves new features. See the *location* parameter.

            If you pass `module=something`, TF will save in `loc/something`,
            where `loc` is the last member of the `locations` parameter of TF.

            If you pass `location=path1` and `module=path2`,
            TF will save in `path1/path2`.

        silent: boolean, optional `None`
            TF is silent if you specified `silent=True` in a preceding
            `TF=Fabric()` call.
            But if you did not, you can also pass `silent=True` to this call.
        """

        tmObj = self.tmObj
        isSilent = tmObj.isSilent
        setSilent = tmObj.setSilent
        indent = tmObj.indent
        info = tmObj.info
        error = tmObj.error

        good = True
        if silent is not None:
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
            "Exporting {} node and {} edge and {} config features to {}:".format(
                len(nodeFeatures),
                len(edgeFeatures),
                len(configFeatures),
                self.writeDir,
            )
        )
        todo = []
        for (fName, data) in sorted(nodeFeatures.items()):
            todo.append((fName, data, False, False))
        for (fName, data) in sorted(edgeFeatures.items()):
            todo.append((fName, data, True, False))
        for (fName, data) in sorted(configFeatures.items()):
            todo.append((fName, data, None, True))
        total = collections.Counter()
        failed = collections.Counter()
        maxSlot = None
        maxNode = None
        slotType = None
        if WARP[0] in nodeFeatures:
            info(f"VALIDATING {WARP[1]} feature")
            otypeData = nodeFeatures[WARP[0]]
            if type(otypeData) is tuple:
                (otypeData, slotType, maxSlot, maxNode) = otypeData
            elif 1 in otypeData:
                slotType = otypeData[1]
                maxSlot = max(n for n in otypeData if otypeData[n] == slotType)
                maxNode = max(otypeData)
        if WARP[1] in edgeFeatures:
            info(f"VALIDATING {WARP[1]} feature")
            oslotsData = edgeFeatures[WARP[1]]
            if type(oslotsData) is tuple:
                (oslotsData, maxSlot, maxNode) = oslotsData
            if maxSlot is None or maxNode is None:
                error(f"ERROR: cannot check validity of {WARP[1]} feature")
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
                    error(f"ERROR: {WARP[1]} maps slot nodes")
                    error(makeExamples(mappedSlotNodes), tm=False)
                    good = False
                if fakeNodes:
                    error(f"ERROR: {WARP[1]} maps nodes that are not in {WARP[0]}")
                    error(makeExamples(fakeNodes), tm=False)
                    good = False
                if unmappedNodes:
                    error(f"ERROR: {WARP[1]} fails to map nodes:")
                    unmappedByType = {}
                    for n in unmappedNodes:
                        unmappedByType.setdefault(
                            otypeData.get(n, "_UNKNOWN_"), []
                        ).append(n)
                    for (nType, nodes) in sorted(
                        unmappedByType.items(), key=lambda x: (-len(x[1]), x[0]),
                    ):
                        error(f"--- unmapped {nType:<10} : {makeExamples(nodes)}")
                    good = False

            if good:
                info(f"OK: {WARP[1]} is valid")

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
            if fObj.save(nodeRanges=fName == WARP[0], overwrite=True):
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

        if silent is not None:
            setSilent(wasSilent)
        return good

    def exportMQL(self, mqlName, mqlDir):
        """Exports the complete TF dataset into single MQL database.

        Parameters
        ----------
        dirName: string
        dbName: string

        Returns
        -------
        None
            The exported data will be written to file *dirName*`/`*dbName.mql*.
            If `dirName` starts with `~`, the `~` will be expanded to your
            home directory.
            Likewise, `..` will be expanded to the parent of the current directory,
            and `.` to the current directory, both only at the start of `dirName`.

        See Also
        --------
        tf.convert.mql
        """

        tmObj = self.tmObj
        indent = tmObj.indent

        indent(level=0, reset=True)
        mqlDir = expandDir(self, mqlDir)

        mqlNameClean = cleanName(mqlName)
        mql = MQL(mqlDir, mqlNameClean, self.features, self.tmObj)
        mql.write()

    def importMQL(self, mqlFile, slotType=None, otext=None, meta=None):
        """Converts an MQL database dump to a Text-Fabric dataset.

        !!! hint "Destination directory"
            It is recommended to call this `importMQL` on a TF instance called with

                TF = Fabric(locations=targetDir)

            Then the resulting features will be written in the targetDir.
            In fact, the rules are exactly the same as for `save()`.

        Parameters
        ----------
        slotType: string
            You have to tell which object type in the MQL file acts as the slot type,
            because TF cannot see that on its own.

        otext: dict
            You can pass the information about sections and text formats as
            the parameter `otext`. This info will end up in the `otext.tf` feature.
            Pass it as a dictionary of keys and values, like so:

                otext = {
                    'fmt:text-trans-plain': '{glyphs}{trailer}',
                    'sectionFeatures': 'book,chapter,verse',
                }

        meta: dict
            Likewise, you can add a dictionary of keys and values that will added to
            the metadata of all features. Handy to add provenance data here:

                meta = dict(
                    dataset='DLC',
                    datasetName='Digital Language Corpus',
                    author="That 's me",
                )
        """

        tmObj = self.tmObj
        indent = tmObj.indent

        indent(level=0, reset=True)
        (good, nodeFeatures, edgeFeatures, metaData) = tfFromMql(
            mqlFile, self.tmObj, slotType=slotType, otext=otext, meta=meta
        )
        if good:
            self.save(
                nodeFeatures=nodeFeatures, edgeFeatures=edgeFeatures, metaData=metaData
            )

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
            # if not self.features[fName].load(silent=silent or (fName not in self.featuresRequested)):
            if not self.features[fName].load(silent=silent):
                self.good = False

    def _makeIndex(self):
        tmObj = self.tmObj
        info = tmObj.info
        warning = tmObj.warning

        self.features = {}
        self.featuresIgnored = {}
        tfFiles = {}
        for loc in self.locations:
            for mod in self.modules:
                dirF = f"{loc}/{mod}"
                if not os.path.exists(dirF):
                    continue
                with os.scandir(dirF) as sd:
                    files = tuple(
                        e.name for e in sd if e.is_file() and e.name.endswith(".tf")
                    )
                for fileF in files:
                    (fName, ext) = os.path.splitext(fileF)
                    tfFiles.setdefault(fName, []).append(f"{dirF}/{fileF}")
        for (fName, featurePaths) in sorted(tfFiles.items()):
            chosenFPath = featurePaths[-1]
            for featurePath in sorted(set(featurePaths[0:-1])):
                if featurePath != chosenFPath:
                    self.featuresIgnored.setdefault(fName, []).append(featurePath)
            self.features[fName] = Data(chosenFPath, self.tmObj)
        self._getWriteLoc()
        info(
            "{} features found and {} ignored".format(
                len(tfFiles), sum(len(x) for x in self.featuresIgnored.values()),
            ),
            tm=False,
        )

        good = True
        for fName in WARP:
            if fName not in self.features:
                if fName == WARP[2]:
                    info(
                        (
                            f'Warp feature "{WARP[2]}" not found. Working without Text-API\n'
                        )
                    )
                    self.features[WARP[2]] = Data(
                        f"{WARP[2]}.tf",
                        self.tmObj,
                        isConfig=True,
                        metaData=WARP2_DEFAULT,
                    )
                    self.features[WARP[2]].dataLoaded = True
                else:
                    info(f'Warp feature "{fName}" not found in\n{self.locationRep}')
                    good = False
            elif fName == WARP[2]:
                self._loadFeature(fName, optional=True)
        if not good:
            return False
        self.warpDir = self.features[WARP[0]].dirName
        self.precomputeList = []
        for (dep2, fName, method, dependencies) in PRECOMPUTE:
            thisGood = True
            if dep2 and WARP[2] not in self.features:
                continue
            if dep2:
                otextMeta = self.features[WARP[2]].metaData
                sFeatures = f"{KIND[fName]}Features"
                sFeats = tuple(itemize(otextMeta.get(sFeatures, ""), ","))
                dependencies = dependencies + sFeats
            for dep in dependencies:
                if dep not in self.features:
                    warning(
                        f'Missing dependency for computed data feature "{fName}": "{dep}"'
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
            os.path.expanduser(location)
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
        good = True
        for (fName, dep2) in self.precomputeList:
            ok = getattr(self, f'{fName.strip("_")}OK', False)
            if dep2 and not ok:
                continue
            if not self.features[fName].load():
                good = False
                break
        self.good = good

    def _makeApi(self):
        if not self.good:
            return None

        tmObj = self.tmObj
        isSilent = tmObj.isSilent
        indent = tmObj.indent
        info = tmObj.info

        silent = isSilent()
        api = Api(self)

        w0info = self.features[WARP[0]]
        w1info = self.features[WARP[1]]

        setattr(api.F, WARP[0], OtypeFeature(api, w0info.metaData, w0info.data))
        setattr(api.E, WARP[1], OslotsFeature(api, w1info.metaData, w1info.data))

        requestedSet = set(self.featuresRequested)

        for fName in self.features:
            fObj = self.features[fName]
            if fObj.dataLoaded and not fObj.isConfig:
                if fObj.method:
                    feat = fName.strip("_")
                    ok = getattr(self, f"{feat}OK", False)
                    ap = api.C
                    if fName in [x[0] for x in self.precomputeList if not x[1] or ok]:
                        setattr(ap, feat, Computed(api, fObj.data))
                    else:
                        fObj.unload()
                        if hasattr(ap, feat):
                            delattr(api.C, feat)
                else:
                    if fName in requestedSet | self.textFeatures:
                        if fName in WARP:
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
                        if fName in WARP or fName in self.textFeatures:
                            continue
                        elif fObj.isEdge:
                            if hasattr(api.E, fName):
                                delattr(api.E, fName)
                        else:
                            if hasattr(api.F, fName):
                                delattr(api.F, fName)
                        fObj.unload()
        addOtype(api)
        addNodes(api)
        addLocality(api)
        addText(api)
        addSearch(api, silent)
        indent(level=0)
        info("All features loaded/computed - for details use loadLog()")
        self.api = api
        return api

    def _updateApi(self):
        if not self.good:
            return None
        api = self.api
        tmObj = self.tmObj
        indent = tmObj.indent
        info = tmObj.info

        requestedSet = set(self.featuresRequested)

        for fName in self.features:
            fObj = self.features[fName]
            if fObj.dataLoaded and not fObj.isConfig:
                if not fObj.method:
                    if fName in requestedSet | self.textFeatures:
                        if fName in WARP:
                            continue
                        elif fObj.isEdge:
                            if not hasattr(api.E, fName):
                                setattr(
                                    api.E,
                                    fName,
                                    EdgeFeature(
                                        api, fObj.metaData, fObj.data, fObj.edgeValues
                                    ),
                                )
                        else:
                            if not hasattr(api.F, fName):
                                setattr(
                                    api.F,
                                    fName,
                                    NodeFeature(api, fObj.metaData, fObj.data),
                                )
                    else:
                        if fName in WARP or fName in self.textFeatures:
                            continue
                        elif fObj.isEdge:
                            if hasattr(api.E, fName):
                                delattr(api.E, fName)
                        else:
                            if hasattr(api.F, fName):
                                delattr(api.F, fName)
                        fObj.unload()
        indent(level=0)
        info("All additional features loaded - for details use loadLog()")
