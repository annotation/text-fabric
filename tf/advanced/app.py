import os
import types
import traceback

from ..parameters import ORG, APP_CODE
from ..fabric import Fabric
from ..parameters import APIREF, TEMP_DIR
from ..lib import readSets
from ..core.helpers import console, setDir, mergeDict
from .find import findAppConfig, findAppClass
from .helpers import getText, dm, dh
from .settings import setAppSpecs, setAppSpecsApi
from .links import linksApi, outLink
from .text import textApi
from .sections import sectionsApi
from .display import displayApi
from .search import searchApi
from .data import getModulesData
from .repo import checkoutRepo


# SET UP A TF API FOR AN APP


FROM_TF_METHODS = """
    banner
    silentOn
    silentOff
    isSilent
    setSilent
    info
    warning
    error
    indent
""".strip().split()


class App:
    def __init__(
        self,
        cfg,
        appName,
        appPath,
        commit,
        release,
        local,
        _browse,
        hoist=False,
        version=None,
        checkout="",
        mod=None,
        locations=None,
        modules=None,
        api=None,
        setFile="",
        silent=False,
        **configOverrides,
    ):
        """Set up the advanced TF API.

        Parameters
        ----------
        appName: string
            The appname  can be as simple as the name of an existing TF-app.
            The app should exist as a repository `app-`*appName* under
            [github.com/annotation](https://github.com/annotation).

            If there is a `/` in the *appName argument*,
            it is interpreted as a location on your  system.

            If it points to a directory with a *config.yaml* in it,
            this config file will be read and interpreted as settings
            for the advanced API.
            If there is also a *app.py*, it will be imported as custom application code.
            And if there is a *static/display.css* there, it will be used
            for styling the display of corpus material.

            If there is no `config.yaml` there, it will be assumed that there are
            `.tf` data files in that location, and they will be loaded.
            The advanced API will work with default settings,
            based on the `.tf` data found.

            !!! hint "appName:specifier, checkout=specifier"
                You may want to load downloadable features from the internet,
                or you want to experiment with features you are developing.
                The specifiers let you use a specific point in the
                history of the app and data.

                *appName:specifier* is used for retrieving a TF-app (*code*).

                *checkout=specifier* is for retrieving the corpus itself  (*data*).

                *   `''` (empty string or absent) (**default**):
                    use local data if it is present under `~/text-fabric-data`,
                    otherwise use the latest release if there are releases online,
                    otherwise, use the latest commit.
                *   `latest`: use the latest release.
                    If there are commits after the commit that has been tagged
                    with the latest release, these will **not** be used.
                *   `hot`: use the latest commit, even if it comes after the
                    latest commit of the latest release.
                *   *release tag*, e.g. `v1.3`: use exactly this release.
                    More precisely, this is the commit that has been tagged
                    with that release tag.
                *   *commit hash*, e.g. `2d0ca1f593805af0c13c4a62ed7405b94d870045`:
                    use exactly this commit.
                *   `local`: use local data from your `~/text-fabric-data` directory
                    if it is present, otherwise fail.
                *   `clone`: use local data from your `~/github` directory
                    if it is present, otherwise fail.

                For a demo, see
                [banks/repo](https://nbviewer.jupyter.org/github/annotation/tutorials/blob/master/banks/repo.ipynb)

        hoist: dict, optional `False`
            If you pass `globals()`, the core API elements are made directly available
            as global names in your script or notebook:

            * `tf.core.nodefeature.NodeFeature` as `F` instead of `A.api.F`
            * `tf.core.locality.Locality` as `L` instead of `A.api.L`
            * `tf.core.text.Text` as `T` instead of `A.api.T`
            * and a few others (listed after executing the incantation)

        version: string, optional `None`
            If you do not want to work with the default version of your main corpus,
            you can specify a different version here.

            !!! caution "Modules"
                If you also ask for extra data modules by means of the `mod` argument,
                then the corresponding version of those modules will be chosen.
                Every properly designed data module must refer to a specific
                version of the main source!

        mod: string, optional `None`
            A comma-separated list of modules in one of the forms

               {org}/{repo}/{path}`

            or

               {org}/{repo}/{path}:specifier`

            All features of all those modules will be loaded.
            If they are not yet present, they will be downloaded from GitHub first.

            For example, there is an easter egg module on GitHub,
            and you can obtain it by

               mod='etcbc/lingo/easter/tf'`

            Here the `{org}` is `etcbc`, the `{repo}` is `lingo`,
            and the `{path}` is `easter/tf` under which
            version `c` of the feature `egg`
            is available in TF format.

            You can point to any such directory om the entire GitHub
            if you know that it contains relevant features.

            The specifier is as in `appName:specifier` and `checkData=specifier`.
            It is used to get data from a different point in the history.

            Your TF app might be configured to download specific modules.
            See `moduleSpecs` in the app's `config.yaml` file.

            !!! caution "Let TF manage your text-fabric-data directory"
                It is better not to fiddle with your `~/text-fabric-data` directory
                manually. Let it be filled with auto-downloaded data.
                You can then delete data sources and modules when needed,
                and have them redownloaded at your wish,
                without any hassle or data loss.

        locations, modules: string, optional `None`
            If you want to add other search locations for TF features manually,
            you can pass optional `locations` and `modules` parameters,
            which will be passed to the `tf.fabric.Fabric` call to the core of TF.

            !!! note "More, not less"
                Using these arguments will load features on top of the
                default selection of features.
                You cannot use these arguments to prevent features from being loaded.

            !!! note "appName with `/`"
                If you use the *appName* argument with a `/` in it,
                and it does not point to a TF app you have locally,
                it will be interpreted as a *locations* search path to find `.tf` files.
                It acts as the main `locations` argument,
                and will be combined with the `modules` argument.

        api: object, optional, `None`
            So far, the TF app will construct an advanced API
            with a more or less standard set of features
            loaded, and make that API avaible to you, under `A.api`.

            But you can also setup a core API yourself by using
            `tf.fabric.Fabric` with your choice of locations and modules:

               from tf.fabric import Fabric`
               TF = Fabric(locations=..., modules=...)`
               api = TF.load(features)`

            Here you have full control over what you load and what not.

            If you want the extra power of the TF app, you can wrap this `api`:

               A = use('xxxx', api=api)`

            !!! hint "Unloaded features"
                Some apps do not load all available features of the corpus by default.

                This happens when a corpus contains quite a number of features
                that most people never need.
                Loading them cost time and takes a lot of RAM.

                In the case where you need an available feature
                that has not been loaded, you can load it by demanding

                   TF.load('feature1 feature2', add=True)`

                provided you have used the `hoist=globals()` parameter earlier.
                If not, you have to say

                   A.api.TF.load('feature1 feature2', add=True)`

        setFile: string, optional, `None`
            The name of a file that contains condensed set information,
            produces with `tf.lib.writeSets`.
            These sets will be read and will become usable in TF queries.

        silent: boolean, optional `False`
            If `True`, nearly all output of this call will be suppressed,
            including the links to the loaded
            data, features, and the API methods.
            Error messages will still come through.

        configOverrides: key value pairs
            All values here will be used to override configuration settings
            that are specified in the app's `config.yaml` file.
            The list of those settings is spelled out in
            `tf.advanced.settings`.

        See Also
        --------
        tf.about.corpora: list of corpora with an official TF app
        tf.advanced.settings: description of what can go in a `config.yaml`
        """

        self.context = None
        """Result of interpreting all configuration options in `config.yaml`.

        See Also
        --------
        tf.advanced.settings.showContext
        """

        mergeDict(cfg, configOverrides)

        for (key, value) in dict(
            isCompatible=cfg.get("isCompatible", None),
            appName=appName,
            api=api,
            version=version,
            silent=silent,
            _browse=_browse,
        ).items():
            setattr(self, key, value)

        setattr(self, "dm", dm)
        setattr(self, "dh", dh)

        setAppSpecs(self, cfg)
        aContext = self.context
        version = aContext.version

        setDir(self)

        if not self.api:
            self.sets = None
            if setFile:
                sets = readSets(setFile)
                if sets:
                    self.sets = sets
                    console(f'Sets from {setFile}: {", ".join(sets)}')
            specs = getModulesData(
                self, mod, locations, modules, version, checkout, silent
            )
            if specs:
                (locations, modules) = specs
                self.tempDir = f"{self.repoLocation}/{TEMP_DIR}"
                TF = Fabric(locations=locations, modules=modules, silent=silent or True)
                self.TF = TF
                api = TF.load("", silent=silent or True)
                if api:
                    self.api = api
                    excludedFeatures = aContext.excludedFeatures
                    allFeatures = TF.explore(silent=silent or True, show=True)
                    loadableFeatures = allFeatures["nodes"] + allFeatures["edges"]
                    useFeatures = [
                        f for f in loadableFeatures if f not in excludedFeatures
                    ]
                    result = TF.load(useFeatures, add=True, silent=silent or True)
                    if result is False:
                        self.api = None
            else:
                self.api = None

        if self.api:
            for m in FROM_TF_METHODS:
                setattr(self, m, getattr(self.TF, m))
            self.getText = types.MethodType(getText, self)
            linksApi(self, silent)
            searchApi(self)
            sectionsApi(self)
            setAppSpecsApi(self, cfg)
            displayApi(self, silent)
            textApi(self)
            if hoist:
                # docs = self.api.makeAvailableIn(hoist)
                self.api.makeAvailableIn(hoist)
                if not silent:
                    dh(
                        "<div><b>Text-Fabric API:</b> names "
                        + outLink("N F E L T S C TF", APIREF, title="doc",)
                        + " directly usable</div><hr>"
                    )

            silentOff = self.silentOff
            silentOff()
        else:
            if not _browse:
                console(
                    f"""
There were problems with loading data.
The Text-Fabric API has not been loaded!
The app "{appName}" will not work!
""",
                    error=True,
                )

    def reinit(self):
        """TF-Apps may override this method.
        It is called by `reuse`. Hence it needs to be present.
        """

        pass

    def reuse(self, hoist=False):
        """Re-initialize the app.

        The app's settings are read again, the app's code is re-imported,
        the app's stylesheets are applied again.
        But the data is left untouched, and no time-consuming reloading of data
        takes place.

        Handy when you are developing a new app and want to experiment with it
        without the costly re-loading of the data in every cycle.

        Parameters
        ----------
        hoist: boolean, optional `False`
            Same as in `App`.

        !!! hint "the effect of the config settings"
            If you are developing a TF app and need to see the effects of
            the configuration settings in detail, you can conveniently
            call `reuse` and `tf.advanced.settings.showContext` in tandem.
        """

        aContext = self.context
        appPath = aContext.appPath
        appName = aContext.appName
        local = aContext.local
        commit = aContext.commit
        release = aContext.release
        version = aContext.version
        api = self.api

        cfg = findAppConfig(appName, appPath, commit, release, local, version=version)
        findAppClass(appName, appPath)

        setAppSpecs(self, cfg, reset=True)

        if api:
            TF = self.TF
            TF._makeApi()
            api = TF.api
            self.api = api
            self.reinit()  # may be used by custom TF apps
            linksApi(self, True)
            searchApi(self)
            sectionsApi(self)
            setAppSpecsApi(self, cfg)
            displayApi(self, True)
            textApi(self)
            if hoist:
                api.makeAvailableIn(hoist)


def findApp(appName, checkoutApp, _browse, *args, silent=False, version=None, **kwargs):
    """Find a TF app by name and initialize an object of its main class.

    Parameters
    ----------
    appName: string
        Either:

        * the plain name of an official TF app (e.g. `bhsa`, `oldbabylonian`)
        * or a local directory, containing at least one `/`:
          * if it points to a directory under which an unofficial app sits:
            that app will be loaded
          * else it is assumed that the local directory is a TF data directory:
            a vanilla app without extra configuration is initialized
            and this local directory is supplied for its `locations`
            parameter. This has the effect that the TF features here will
            be loaded.

    checkoutApp: string
        The checkout specifier for the app code. See `tf.advanced.app.App`.

    args: mixed
        Arguments that will be passed to the initializer of the `tf.advanced.app.App`
        class.

    kwargs: mixed
        Keyword arguments that will be passed to the initializer of the
        `tf.advanced.app.App` class.

    """

    if not appName or "/" in appName:
        appPath = os.path.expanduser(appName) if appName else ""
        absPath = os.path.abspath(appPath)
        (commit, release, local) = (None, None, None)

        if os.path.isdir(absPath):
            (appDir, appName) = os.path.split(absPath)
            codePath = f"{absPath}/{APP_CODE}"
            if os.path.isdir(codePath):
                appDir = codePath
            appBase = ""
        else:
            console(f"{absPath} is not an existing directory", error=True)
            appBase = False
        appPath = appDir
    else:
        (commit, release, local, appBase, appDir) = checkoutRepo(
            _browse=_browse,
            org=ORG,
            repo=f"app-{appName}",
            folder=APP_CODE,
            checkout=checkoutApp,
            withPaths=True,
            keep=False,
            silent=silent,
            label="TF-app",
        )
        appBaseRep = f"{appBase}/" if appBase else ""
        appPath = f"{appBaseRep}{appDir}"
    cfg = findAppConfig(appName, appPath, commit, release, local, version=version)
    version = cfg["provenanceSpec"].get("version", None)
    if not appBase and appBase != "":
        return None

    isCompatible = cfg["isCompatible"]
    if isCompatible is None:
        appClass = App
    elif not isCompatible:
        return None
    else:
        appBaseRep = f"{appBase}/" if appBase else ""
        appPath = f"{appBaseRep}{appDir}"

        appClass = findAppClass(appName, appPath) or App
    try:
        app = appClass(
            cfg,
            appName,
            appPath,
            commit,
            release,
            local,
            _browse,
            *args,
            version=version,
            silent=silent,
            **kwargs,
        )
    except Exception as e:
        if appClass is not App:
            console(
                f"There was an error loading TF-app {appName} from {appPath}", error=True
            )
            console(repr(e), error=True)
        traceback.print_exc()
        console("Text-Fabric is not loaded", error=True)
        return None
    return app
