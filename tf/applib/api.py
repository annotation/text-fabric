import types
from ..fabric import Fabric
from ..parameters import URL_TFDOC, TEMP_DIR, API_VERSION as apiVersionProvided
from ..lib import readSets
from ..core.helpers import console, setDir
from .app import findAppConfig
from .helpers import getLocalDir, configure, dh
from .links import linksApi, outLink
from .text import textApi
from .sections import sectionsApi
from .display import displayApi
from .search import searchApi
from .data import getModulesData


# SET UP A TF API FOR AN APP


CONFIG_DEFAULTS = (
    ("standardFeatures", None),
    ("excludedFeatures", set()),
)


def setupApi(
    app,
    appName,
    appPath,
    commit,
    release,
    local,
    hoist=False,
    version=None,
    checkout="",
    mod=None,
    locations=None,
    modules=None,
    api=None,
    setFile="",
    silent=False,
    _browse=False,
):
    for (key, value) in dict(
        appName=appName, _browse=_browse, api=api, version=version, silent=silent,
    ).items():
        setattr(app, key, value)

    app.appPath = appPath
    app.commit = commit

    config = findAppConfig(appName, appPath)
    cfg = configure(config, version)

    apiVersionRequired = cfg.get("apiVersion", None)
    app.isCompatible = (
        apiVersionRequired is not None and apiVersionRequired == apiVersionProvided
    )
    if not app.isCompatible:
        if apiVersionRequired is None or apiVersionRequired < apiVersionProvided:
            console(
                f"""
Your copy of the TF app `{appName}` is outdated for this version of TF.
Recommendation: obtain a newer version of `appName`.
Hint: load the app in one of the following ways:

    {appName}
    {appName}:latest
    {appName}:hot

    For example:

    The Text-Fabric browser:

        text-fabric {appName}:latest

    In a program/notebook:

        A = use('{appName}:latest', hoist=globals())

""",
                error=True,
            )
        else:
            console(
                f"""
Your Text-Fabric is outdated and cannot use this version of the TF app `{appName}`.
Recommendation: upgrade Text-Fabric.
Hint:

    pip3 install --upgrade text-fabric

""",
                error=True,
            )
        console(
            f"""
Text-Fabric will be loaded, but all app specific functionality will not be available.
That means that the following will not work:

    A.search(query)
    A.plain(node)
    A.pretty(node)

but the core API will still work:
    F.feature.v(node)
    T.text(node)
    S.search(query)

""",
            error=True,
        )

    version = cfg["version"]
    cfg["localDir"] = getLocalDir(cfg, local, version)
    for (key, value) in cfg.items():
        setattr(app, key, value)

    for (attr, default) in CONFIG_DEFAULTS:
        setattr(app, attr, getattr(app, attr, default))

    setDir(app)

    if app.api:
        if app.standardFeatures is None:
            allFeatures = app.api.TF.explore(silent=silent or True, show=True)
            loadableFeatures = allFeatures["nodes"] + allFeatures["edges"]
            app.standardFeatures = loadableFeatures
    else:
        app.sets = None
        if setFile:
            sets = readSets(setFile)
            if sets:
                app.sets = sets
                console(f'Sets from {setFile}: {", ".join(sets)}')
        specs = getModulesData(app, mod, locations, modules, version, checkout, silent)
        if specs:
            (locations, modules) = specs
            app.tempDir = f"{app.repoLocation}/{TEMP_DIR}"
            TF = Fabric(locations=locations, modules=modules, silent=silent or True)
            api = TF.load("", silent=silent or True)
            if api:
                app.api = api
                allFeatures = TF.explore(silent=silent or True, show=True)
                loadableFeatures = allFeatures["nodes"] + allFeatures["edges"]
                if app.standardFeatures is None:
                    app.standardFeatures = loadableFeatures
                useFeatures = [
                    f for f in loadableFeatures if f not in app.excludedFeatures
                ]
                result = TF.load(useFeatures, add=True, silent=silent or True)
                if result is False:
                    app.api = None
        else:
            app.api = None

    if app.api:
        app.reuse = types.MethodType(reuse, app)
        linksApi(app, appName, silent)
        searchApi(app)
        sectionsApi(app)
        displayApi(app, silent)
        textApi(app)
        if hoist:
            docs = app.api.makeAvailableIn(hoist)
            if not silent:
                dh(
                    "<details open><summary><b>API members</b>:</summary>\n"
                    + "<br/>\n".join(
                        ", ".join(
                            outLink(
                                entry, f"{URL_TFDOC}/Api/{head}/#{ref}", title="doc",
                            )
                            for entry in entries
                        )
                        for (head, ref, entries) in docs
                    )
                    + "</details>"
                )
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


def reuse(app, hoist=False):
    appPath = app.appPath
    appName = app.appName
    version = app.version
    api = app.api

    config = findAppConfig(appName, appPath)
    cfg = configure(config, version)

    for (key, value) in cfg.items():
        setattr(app, key, value)

    if api:
        linksApi(app, appName, True)
        textApi(app)
        searchApi(app)
        sectionsApi(app)
        displayApi(app, True)
        if hoist:
            api.makeAvailableIn(hoist)
