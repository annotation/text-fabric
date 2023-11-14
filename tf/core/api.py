"""
# The core API of TF.

It provides methods to navigate nodes and edges and lookup features.
"""

import collections
from textwrap import wrap, dedent

from .helpers import flattenToSet, console, fitemize, deepSize
from ..advanced.helpers import dm
from .files import unexpanduser as ux
from .nodes import Nodes
from .locality import Locality
from .nodefeature import NodeFeatures
from .edgefeature import EdgeFeatures
from .computed import Computeds
from .text import Text
from ..parameters import OTYPE, OSLOTS
from ..search.search import Search
from ..core.timestamp import SILENT_D, DEEP, silentConvert


API_REFS = dict(
    AllComputeds=("Computed", "computedall", "computed-data"),
    AllEdges=("Features", "edgeall", "edge-features"),
    AllFeatures=("Features", "nodeall", "node-features"),
    C=("Computed", "computed", "computed-data"),
    Call=("Computed", "computedall", "computed-data"),
    Computed=("Computed", "computed", "computed-data"),
    ComputedString=("Computed", "computedstr", "computed-data"),
    Cs=("Computed", "computedstr", "computed-data"),
    E=("Features", "edge", "edge-features"),
    Eall=("Features", "edgeall", "edge-features"),
    Edge=("Features", "edge", "edge-features"),
    EdgeString=("Features", "edgestr", "edge-features"),
    Es=("Features", "edgestr", "edge-features"),
    F=("Features", "node", "node-features"),
    Fall=("Features", "nodeall", "node-features"),
    Feature=("Features", "node", "node-features"),
    FeatureString=("Features", "nodestr", "node-features"),
    Fs=("Features", "nodestr", "node-features"),
    L=("Locality", "locality", "locality"),
    Locality=("Locality", "locality", "locality"),
    N=("Nodes", "nodes", "navigating-nodes"),
    Nodes=("Nodes", "nodes", "navigating-nodes"),
    S=("Search", "search", "search"),
    Search=("Search", "search", "search"),
    T=("Text", "text", "text"),
    TF=("Fabric", "fabric", "loading"),
    Text=("Text", "text", "text"),
)


class Api:
    def __init__(self, TF):
        self.TF = TF
        self.ignored = tuple(sorted(TF.featuresIgnored))
        """Which features were found but ignored.

        Features are ignored if the feature is also present in another location
        that is loaded later.
        """
        TF.ignored = self.ignored

        self.F = NodeFeatures()
        self.Feature = self.F
        self.E = EdgeFeatures()
        self.Edge = self.E
        self.C = Computeds()
        self.Computed = self.C
        tmObj = TF.tmObj
        TF.silentOn = tmObj.silentOn
        TF.silentOff = tmObj.silentOff
        TF.isSilent = tmObj.isSilent
        TF.setSilent = tmObj.setSilent
        TF.info = tmObj.info
        TF.warning = tmObj.warning
        TF.error = tmObj.error
        TF.cache = tmObj.cache
        TF.reset = tmObj.reset
        TF.indent = tmObj.indent

        """All messages produced during the feature loading process.

        It also shows the messages that have been suppressed due to the `silent`
        parameter.
        """

        TF.ensureLoaded = self.ensureLoaded
        TF.makeAvailableIn = self.makeAvailableIn
        TF.footprint = self.footprint

        setattr(self, "FeatureString", self.Fs)
        setattr(self, "EdgeString", self.Es)
        setattr(self, "ComputedString", self.Cs)
        setattr(self, "AllFeatures", self.Fall)
        setattr(self, "AllEdges", self.Eall)
        setattr(self, "AllComputeds", self.Call)
        setattr(self, "loadLog", self.isLoaded)

    def Fs(self, fName, warn=True):
        """Get the node feature sub API.

        If feature name is not a valid python identifier,
        or if you do not know its name in advance,
        you can not use `F.feature`, but you should use
        `Fs(feature)`.

        Parameters
        ----------
        fName: string
            The name of the feature.
        warn: boolean, optional `True`
            Whether to warn if the feature is not loaded.

        Returns
        -------
        The feature API, or `None` if the feature is not loaded.
        """

        if not hasattr(self.F, fName):
            if warn:
                self.TF.error(f'Node feature "{fName}" not loaded')
            return None
        return getattr(self.F, fName)

    def Es(self, fName, warn=True):
        """Get the edge feature sub API.

        If feature name is not a valid python identifier,
        or if you do not know its name in advance,
        you can not use `E.feature`, but you should use
        `Es(feature)`.

        Parameters
        ----------
        fName: string
            The name of the feature.
        warn: boolean, optional `True`
            Whether to warn if the feature is not loaded.

        Returns
        -------
        The feature API, or `None` if the feature is not loaded.
        """

        if not hasattr(self.E, fName):
            if warn:
                self.TF.error(f'Edge feature "{fName}" not loaded')
            return None
        return getattr(self.E, fName)

    def Cs(self, fName, warn=True):
        """Get the computed data sub API.

        If component name is not a valid python identifier,
        or if you do not know its name in advance,
        you can not use `C.component`, but you should use
        `Cs(component)`.

        Parameters
        ----------
        fName: string
            The name of the feature.
        warn: boolean, optional `True`
            Whether to warn if the feature is not loaded.

        Returns
        -------
        The feature API, or `None` if the feature is not loaded.
        """

        if not hasattr(self.C, fName):
            if warn:
                self.TF.error(f'Computed feature "{fName}" not loaded')
            return None
        return getattr(self.C, fName)

    def Fall(self, warp=True):
        """Returns a sorted list of all usable, loaded node feature names.

        Parameters
        ----------
        warp: boolean, optional True
            Whether to include the warp features, i.e. `otype`.
        """

        return sorted(x[0] for x in self.F.__dict__.items() if warp or x[0] != OTYPE)

    def Eall(self, warp=True):
        """Returns a sorted list of all usable, loaded edge feature names.

        Parameters
        ----------
        warp: boolean, optional True
            Whether to include the warp features, i.e. `oslots`.
        """

        return sorted(x[0] for x in self.E.__dict__.items() if warp or x[0] != OSLOTS)

    def Call(self):
        """Returns a sorted list of all usable, loaded computed data names."""

        return sorted(x[0] for x in self.C.__dict__.items())

    def isLoaded(
        self, features=None, pretty=True, valueType=True, path=False, meta="description"
    ):
        """Show information about loaded features.

        Parameters
        ----------
        features: iterable | string, optional None
            The features to get info for.
            If absent or None: all features seen by TF.
            If a string, it is a comma and / or space separated list of feature names.
            Otherwise the items of the iterable are feature names.

        pretty: boolean, optional True
            If True, it prints an overview of all features seen by TF with
            information about kind, type, source location and loaded status.
            The amount of information printed can be tweaked by other parameters.
            Otherwise, it returns this information as a dict.

        valueType: boolean, optional True
            Only relevant if `pretty=True`: whether to print the value type of
            the values in the feature file.

        path: boolean, optional True
            Only relevant if `pretty=True`: whether to print the path name of
            the feature file.

        meta: string|list|boolean, optional "description"
            Only relevant if `pretty=True`: controls what metadata of the feature
            should be printed.

            If it is None, False, or the empty string or empty list:
            no metadata will be printed.

            It it is the boolean value True: all metadata will be printed.

            If it is a list of key names or a string with key names
            separated by white-space and / or commas, only these metadata keys
            will be printed.

        Returns
        -------
        dict of dict
            The features are keys, the value per feature is None or a dict with the
            following information:

            `None` if  the feature is not loaded.

            If the feature is loaded:

            *   `kind`: `node`, `edge`, `config`, `computed`;
            *   `type` is the type of values: `int`, or `str` or `""`;
            *   `edgeValues`: if an edge feature it indicates whether
                the edges have values. Otherwise `None`.
            *   `meta`: dictionary containing the metadata of the feature

            If `pretty`, nothing is returned, but the dict is pretty printed.
        """

        fNames = list(self.TF.features) if features is None else fitemize(features)
        info = {}

        for fName in fNames:
            fMeta = {}
            fType = None
            edgeValues = None
            fSource = None
            hasInfo = True
            if fName in self.TF.features:
                fObj = self.TF.features[fName]
                fSource = ux(fObj.dirName)
                fMeta = fObj.metaData
                fType = fMeta.get("valueType", "")
                fMeta = {k: v for (k, v) in fMeta.items() if k != "valueType"}

            isLoadedF = hasattr(self.F, fName)
            isLoadedE = hasattr(self.E, fName)
            if isLoadedF or isLoadedE:
                if isLoadedF:
                    fKind = "node"
                elif isLoadedE:
                    fKind = "edge"
                    flObj = getattr(self.E, fName)
                    edgeValues = False if fName == "oslots" else flObj.doValues
            elif (
                fName.startswith("__")
                and fName.endswith("__")
                and hasattr(self.C, fName.strip("_"))
            ):
                fKind = "computed"
            elif fName in self.TF.features:
                if fObj.isConfig:
                    fKind = "config"
                else:
                    hasInfo = False
            else:
                hasInfo = False

            info[fName] = (
                dict(
                    kind=fKind,
                    type=fType,
                    meta=fMeta,
                    source=fSource,
                    edgeValues=edgeValues,
                )
                if hasInfo
                else None
            )
        if pretty:
            for (fName, fInfo) in sorted(info.items()):
                if fInfo is None:
                    kind = "NOT LOADED"
                    kind = f" {kind:<10}"
                    fSource = ""
                    metaRep = ""
                    heading = f"{fName:<20}{kind}{fSource}"
                else:
                    fKind = fInfo["kind"]
                    fMeta = fInfo.get("meta", {})
                    fType = fInfo.get("type", "")
                    fSource = fInfo.get("source", "") if path else ""
                    fSource = f" {fSource}" if fSource else ""
                    fEV = fInfo.get("edgeValues", "")
                    if valueType:
                        kind = (
                            f"node ({fType})"
                            if fKind == "node"
                            else f"edge ({fType})"
                            if fKind == "edge" and fEV
                            else "edge"
                            if fKind == "edge"
                            else f"{fKind}"
                        )
                        kind = f" {kind:<10}" if kind else ""
                    else:
                        kind = ""
                    if meta is True:
                        metaKeys = sorted(fMeta.keys())
                        metaInfo = fMeta
                    elif not meta:
                        metaInfo = {}
                    else:
                        metaKeys = fitemize(meta)
                        metaInfo = {k: fMeta[k] for k in metaKeys if k in fMeta}

                    heading = f"{fName:<20}{kind}{fSource}"
                    metaRep = ""
                    indent = " " * (len(heading) + 1)
                    if metaInfo:
                        if len(metaKeys) == 1:
                            value = metaInfo.get(metaKeys[0], "")
                            value = "\n".join(
                                wrap(value, width=80, subsequent_indent=indent)
                            )
                            metaRep = f" {value}" if value else ""
                        else:
                            indent = " " * 21
                            for k in metaKeys:
                                value = metaInfo.get(k, "")
                                value = "\n".join(
                                    wrap(
                                        value,
                                        width=80,
                                        subsequent_indent=f"\t{indent}  ",
                                    )
                                )
                                metaRep += f"\n\t{k:<20} = {value}"

                msg = f"{heading}{metaRep}"
                console(msg)
            return None
        return info

    def makeAvailableIn(self, scope):
        """Exports members of the API to the global namespace.

        Only the members whose names start with a capital are exported.

        If you are working with a single data source in your program, it is a bit
        tedious to write the initial `TF.api.` or `A.api` all the time.
        By this method you can avoid that.

        !!! explanation "Longer names"
            There are also longer names which can be used as aliases
            to the single capital letters.
            This might or might not improve the readability of your program.

            short name | long name
            --- | ---
            `N` | `Nodes`
            `F` | `Feature`
            `Fs` | `FeatureString`
            `Fall` | `AllFeatures`
            `E` | `Edge`
            `Es` | `EdgeString`
            `Eall`  `AllEdges`
            `C` | `Computed`
            `Cs`  `ComputedString`
            `Call` | `AllComputeds`
            `L` | `Locality`
            `T` | `Text`
            `S` | `Search`

        Parameters
        ----------
        scope: dict
            A dictionary into which the members of the core API will be inserted.
            The only sensible choice is: `globals()`.

        Returns
        -------
        tuple
            A grouped list of API members that has been hoisted to the global
            scope.

        Notes
        -----
        !!! explanation "Why pass `globals()`?"
            Although we know it should always be `globals()`, we cannot
            define a function that looks into the `globals()` of its caller.
            So we have to pass it on.
        """

        for member in dir(self):
            if "_" not in member and member[0].isupper():
                scope[member] = getattr(self, member)
                if member not in API_REFS:
                    console(f'WARNING: API member "{member}" not documented')

        grouped = {}
        for (member, (head, sub, ref)) in API_REFS.items():
            grouped.setdefault(ref, {}).setdefault((head, sub), []).append(member)

        # grouped
        # node-features=>(Features, node)=>[F, ...]

        docs = []
        for (ref, groups) in sorted(grouped.items()):
            chunks = []
            for ((head, sub), members) in sorted(groups.items()):
                chunks.append(" ".join(sorted(members, key=lambda x: (len(x), x))))
            docs.append((head, ref, tuple(chunks)))
        return docs

    # docs
    # (Features, node-features, ('F ...', ...))

    def ensureLoaded(self, features):
        """Checks if features are loaded and if not loads them.

        All features in question will be made available to the core API.

        Parameters
        ----------
        features: string | iterable of strings
            It is a string containing space separated feature names,
            or an iterable of feature names.
            The feature names are just the names of `.tf` files
            without directory information and without extension.

        Returns
        -------
        set
            The names of the features in question as a set of strings.
        """

        F = self.F
        E = self.E
        TF = self.TF
        warning = TF.warning

        needToLoad = set()
        loadedFeatures = set()

        for fName in sorted(flattenToSet(features)):
            fObj = TF.features.get(fName, None)
            if not fObj:
                warning(f'Cannot load feature "{fName}": not in dataset')
                continue
            if fObj.dataLoaded and (hasattr(F, fName) or hasattr(E, fName)):
                loadedFeatures.add(fName)
            else:
                needToLoad.add(fName)
        if len(needToLoad):
            TF.load(
                needToLoad,
                add=True,
                silent=DEEP,
            )
            loadedFeatures |= needToLoad
        return loadedFeatures

    def footprint(self, recompute=False, bySize=True):
        """Computes the memory footprint in RAM of the loaded TF data.

        This includes the pre-computed data.

        Parameters
        ----------
        recompute: boolean, optional False
            The function looks first for earlier computed size data.
            If that is found, it will be used, and no size computation will take place.
            Unless this parameter is True.
            If no earlier computed size data is found, sizes will be computed anyway.
        bySize: boolean, optional True
            Whether to sort the features by the size they occupy in RAM.
            If False, the features will be sorted alphabetically.
        """
        if hasattr(self, "sizes") and not recompute:
            sizes = self.sizes
        else:
            TF = self.TF
            features = TF.features
            nFeatures = len(features)
            sizes = {}

            for ft in sorted(features):
                console(f"\rcomputing size of {ft:<30}", newline=False)
                data = features[ft].data
                if data is None:
                    continue
                nData = len(data)
                sData = deepSize(data)
                sizes[ft] = (nData, sData)

            console(f'\r{"":>40}', newline=False)
            self.sizes = sizes

        material = ""

        nFeatures = len(sizes)
        totals = collections.Counter()

        for (ft, (nData, sData)) in sorted(
            sizes.items(),
            key=(lambda x: (-x[1][1], x[0])) if bySize else lambda x: x[0],
        ):
            material += f"{ft} | {nData:,} | {sData:,}\n"
            totals["nData"] += nData
            totals["sData"] += sData

        material += f'TOTAL | {totals["nData"]:,} | {totals["sData"]:,}'
        header = dedent(
            f"""
            # {nFeatures} features

            feature | members | size in bytes
            --- | --- | ---
            """
        )

        dm(header + material)


def addOtype(api):
    setattr(api.F.otype, "all", tuple(o[0] for o in api.C.levels.data))
    setattr(
        api.F.otype, "support", dict(((o[0], (o[2], o[3])) for o in api.C.levels.data))
    )


def addLocality(api):
    api.L = Locality(api)
    api.Locality = api.L


def addNodes(api):
    api.N = Nodes(api)
    api.Nodes = api.N


def addText(api):
    api.T = Text(api)
    api.Text = api.T


def addSearch(api, silent=SILENT_D):
    silent = silentConvert(silent)
    api.S = Search(api, silent)
    api.Search = api.S
