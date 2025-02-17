from ..core.helpers import itemize
from ..core.files import backendRep, expandDir, prefixSlash, normpath
from .helpers import splitModRef
from .repo import checkoutRepo
from .links import provenanceLink


# GET DATA FOR MAIN SOURCE AND ALL MODULES


class AppData:
    def __init__(
        self,
        app,
        backend,
        moduleRefs,
        locations,
        modules,
        version,
        checkout,
        silent,
        dest=None,
    ):
        """Collects TF data according to specifications.

        The specifications are passed as arguments when the object is initialized.

        Parameters
        ----------
        backend: string
            `github` or `gitlab` or a GitLab instance such as `gitlab.huc.knaw.nl`.
        app: obj
            The high-level API object
        moduleRefs: tuple
            Each member consists of a module ref, which is a tuple of information
            that defines a module.
        locations: string|tuple
            One or more directory paths. They will be combined with the `modules`
            argument and used as locations to search for TF data files.
        modules: string|tuple
            One or more directory path segments. They will be appended to the
            paths given by the `locations` argument to form search locations
            for TF data files.
        version: string
            The version of TF data that should be retrieved. Version is a directory
            level just below the search locations.
        checkout: string
            A specifier to use a specific release or commit of a data repository.
        silent: string, optional tf.core.timestamp.SILENT_D
            See `tf.core.timestamp.Timestamp`
        dest: string, optional None
            The location where the text-fabric-data cache is.

        """
        self.backend = backend
        self.app = app
        self.moduleRefs = (
            []
            if moduleRefs is None
            else moduleRefs.split(",")
            if type(moduleRefs) is str
            else list(moduleRefs)
        )
        self.locationsArg = locations
        self.modulesArg = modules
        self.version = version
        self.checkout = checkout
        self.dest = dest
        self.silent = silent

    def getMain(self):
        """Get the main data of the corpus.

        This is specified by the `org`, `repo` and `relative` settings under
        `provenanceSpec` in `config.yaml`.

        See Also
        --------
        tf.advanced.settings: options allowed in `config.yaml`
        """

        app = self.app
        checkout = self.checkout
        aContext = app.context
        org = aContext.org
        repo = aContext.repo
        relative = prefixSlash(aContext.relative)
        appPath = aContext.appPath
        appName = aContext.appName

        if appName.startswith("app:"):
            appParent = appPath.rsplit("/", 1)[0]
            relative = f"{appParent}{relative}"
        elif org is None or repo is None:
            appPathRep = f"{appPath}/" if appPath else ""
            relative = f"{appPathRep}{appName}"
            self.checkout = "local"

        if not self.getModule(
            org,
            repo,
            prefixSlash(relative),
            checkout,
            isBase=True,
            versionOverride=app.versionOverride,
            allowExpress=True,
        ):
            self.good = False

    def getStandard(self):
        """Get the data of the standard modules specified by the settings of the corpus.

        These are specified in the `moduleSpecs` setting under
        `provenanceSpecs` in `config.yaml`.

        They will be loaded *after* the extra modules specified in the `mod`
        parameter, and only in as far they have not been specified in the
        `mod` parameter. In this way you can pass overriding
        checkout specifiers to the standard modules.

        See Also
        --------
        tf.advanced.settings: options allowed in `config.yaml`
        """

        app = self.app
        loadData = app.loadData

        if not loadData or loadData == "core":
            return

        aContext = app.context
        moduleSpecs = aContext.moduleSpecs
        seen = self.seen
        checkout = self.checkout
        backend = self.backend

        for m in moduleSpecs or []:
            org = m["org"]
            repo = m["repo"]
            relative = m["relative"]
            theCheckout = m.get("checkout", checkout)
            theBackend = m.get("backend", backend)
            bRep = backendRep(theBackend, "spec", default=backend)

            ref = f"{bRep}{org}/{repo}{relative}"
            if ref in seen:
                continue

            if not self.getModule(
                org,
                repo,
                relative,
                theCheckout,
                backend=theBackend,
                specs=m,
                versionOverride=app.versionOverride,
                allowExpress=True,
            ):
                self.good = False

    def getExtra(self):
        """Get the extra data specified by the settings of the corpus.

        These are specified in the `extraData` setting under
        `provenanceSpecs` in `config.yaml`.

        This data will be downloaded if needed, but it will not be loaded.
        It probably is not even TF data.

        See Also
        --------
        tf.advanced.settings: options allowed in `config.yaml`
        """

        app = self.app
        loadData = app.loadData

        if not loadData or loadData == "core":
            return

        aContext = app.context
        extraData = aContext.extraData

        if not extraData:
            return

        checkout = self.checkout
        backend = self.backend

        org = aContext.org
        repo = aContext.repo
        relative = extraData

        if not self.getModule(
            org,
            repo,
            relative,
            checkout,
            backend=backend,
            isExtra=True,
            versionOverride=app.versionOverride,
            allowExpress=True,
        ):
            self.good = False

    def getRefs(self):
        """Get data from additional modules.

        These are specified in the `moduleRefs` parameter of `AppData`.
        We store the set of special modules in order to skip them
        later when we are loading the standard modules.
        """

        app = self.app
        backend = self.backend
        refs = self.moduleRefs
        for ref in refs:
            refPure = ref.rsplit(":", 1)[0]
            if refPure in self.seen:
                continue

            parts = splitModRef(ref)
            if not parts:
                self.good = False
                continue

            parts[2] = prefixSlash(normpath(parts[2]))  # the relative bit
            theBackend = (
                None if parts[-1] is None or parts[-1] == backend else parts[-1]
            )

            if not self.getModule(
                *parts[0:-1],
                backend=theBackend,
                versionOverride=app.versionOverride,
                allowExpress=False,
            ):
                self.good = False

    def getModules(self):
        """Get data from additional local directories.

        These are specified in the `locations` and `modules` parameters of `AppData`.
        """

        self.provenance = []
        provenance = self.provenance
        self.mLocations = []
        mLocations = self.mLocations

        self.locations = None
        self.modules = None

        self.good = True
        self.seen = set()

        self.getMain()
        self.getRefs()
        self.getStandard()
        self.getExtra()

        version = self.version
        good = self.good
        app = self.app

        if good:
            app.mLocations = mLocations
            app.provenance = provenance
        else:
            return

        mModules = []
        if mLocations:
            mModules.append(version or "")

        locations = self.locationsArg
        modules = self.modulesArg

        givenLocations = (
            []
            if locations is None
            else [expandDir(app, x.strip()) for x in itemize(locations, "\n")]
            if type(locations) is str
            else [str(x) for x in locations]
        )
        givenModules = (
            []
            if modules is None
            else [normpath(x.strip()) for x in itemize(modules, "\n")]
            if type(modules) is str
            else [normpath(str(x)) for x in modules]
        )

        self.locations = mLocations + givenLocations
        self.modules = mModules + givenModules

    def getModule(
        self,
        org,
        repo,
        relative,
        checkout,
        backend=None,
        isBase=False,
        isExtra=False,
        specs=None,
        versionOverride=False,
        allowExpress=True,
    ):
        """Prepare to load a single module.

        Eventually, all TF data will be downloaded from local directories, bases
        on a list of location paths and module paths.

        This function computes the contribution of a single module to both the
        location paths and the module paths.

        Parameters
        ----------
        org: string
            GitHub organization or GitLab group of the module
        repo: string:
            GitHub repository or GitLab project of the module
        relative: string
            Path within the repository of the module
        checkout: string
            A specifier to use a specific release or commit of a data repository.
        backend: string
            The back-end if different from the back-end of the main module
        isExtra: boolean, optional False
            If this is True, we are dealing with extra (non-TF) data.
            The data must be obtained, but not loaded.
        isBase: boolean, optional False
            Whether this module is the main data of the corpus.
        specs: dict, optional False
            Additional informational attributes of the module, e.g. a DOI
        versionOverride: boolean, optional False
            Whether we ask for the data of a non-standard version
        allowExpress: boolean, optional True
            Whether express downloading of the whole corpus may be triggered
        """

        backend = self.backend if backend is None else backendRep(backend, "norm")
        bRep = backendRep(backend, "spec", default=self.backend)
        dest = self.dest
        version = self.version
        silent = self.silent
        mLocations = self.mLocations
        provenance = self.provenance
        seen = self.seen
        app = self.app
        _browse = app._browse
        aContext = app.context
        branch = aContext.provenanceSpec["branch"]

        relative = prefixSlash(normpath(relative))

        moduleRef = f"{bRep}{org}/{repo}{relative}"
        if moduleRef in self.seen:
            return True

        if org is None or repo is None:
            relativeBare = relative.removeprefix("/")
            repoLocation = relativeBare
            if not isExtra:
                mLocations.append(relativeBare)
            (commit, local, release) = (None, None, None)
        else:
            (commit, release, local, localBase, localDir) = checkoutRepo(
                backend,
                _browse=_browse,
                org=org,
                repo=repo,
                folder=relative,
                version=None if isExtra else version,
                versionOverride=versionOverride,
                checkout=checkout,
                dest=dest,
                withPaths=True if isExtra else False,
                keep=True if isExtra else False,
                silent=silent,
                allowExpress=allowExpress,
            )
            if not localBase:
                return False

            repoLocation = f"{localBase}/{org}/{repo}"
            if not isExtra:
                mLocations.append(f"{localBase}/{localDir}")

        seen.add(moduleRef)
        if isBase:
            app.repoLocation = repoLocation

        if isExtra:
            return True

        info = {}
        for item in (
            ("doi", None),
            ("corpus", f"{org}/{repo}{relative}"),
        ):
            (key, default) = item
            info[key] = (
                getattr(aContext, key)
                if isBase
                else specs[key]
                if specs and key in specs
                else default
            )
        provenance.append(
            (
                ("corpus", info["corpus"]),
                ("version", version),
                ("commit", commit or "??"),
                ("release", release or "none"),
                (
                    "live",
                    provenanceLink(
                        backend,
                        org,
                        repo,
                        version,
                        branch,
                        commit,
                        local,
                        release,
                        relative,
                    ),
                ),
                ("doi", info["doi"]),
            )
        )
        return True


def getModulesData(*args, dest=None):
    """Retrieve all data for a corpus.

    Parameters
    ----------
    args: list
        All parameters needed to retrieve all associated data.
        They are the same as are needed to construct an `AppData` object.
    """

    mData = AppData(*args, dest=dest)
    mData.getModules()

    if not mData.good or mData.locations is None:
        return None

    return (mData.locations, mData.modules)
