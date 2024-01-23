import sys
from importlib import util

from ..parameters import (
    API_VERSION as avTf,
)
from ..core.helpers import console
from ..core.files import (
    APP_CONFIG,
    APP_CONFIG_OLD,
    APP_DISPLAY,
    fileOpen,
    prefixSlash,
    fileExists,
    normpath,
    readYaml,
)
from .helpers import getLocalDir


def findAppConfig(
    appName,
    appPath,
    commit,
    release,
    local,
    backend,
    org=None,
    repo=None,
    version=None,
    relative=None,
    straight=False,
):
    """Find the configuration information of an app.

    If there is a `config.yaml` file, read it and check the compatibility
    of the configuration settings with the current version of TF.

    If there is no such file but a `config.py` is present,
    conclude that this is an older app, not compatible with TF v8.0.0 or higher.

    If there are no such configuration files, fill in a few basic settings.

    See Also
    --------
    tf.advanced.settings: options allowed in `config.yaml`
    """

    appPath = normpath(appPath)
    configPath = f"{appPath}/{APP_CONFIG}"
    configPathOld = f"{appPath}/{APP_CONFIG_OLD}"
    cssPath = f"{appPath}/{APP_DISPLAY}"

    checkApiVersion = True

    isCompatible = None

    cfg = readYaml(asFile=configPath, plain=True)

    if cfg is None or cfg == {}:
        cfg = {}
        checkApiVersion = False
        if fileExists(configPathOld):
            isCompatible = False
    if straight:
        return cfg

    cfg.update(
        appName=appName, appPath=appPath, commit=commit, release=release, local=local
    )

    if version is None:
        version = cfg.setdefault("provenanceSpec", {}).get("version", None)
    else:
        cfg.setdefault("provenanceSpec", {})["version"] = version

    if org is None:
        org = cfg.get("provenanceSpec", {}).get("org", None)
    else:
        cfg["provenanceSpec"]["org"] = org

    if repo is None:
        repo = cfg.get("provenanceSpec", {}).get("repo", None)
    else:
        cfg["provenanceSpec"]["repo"] = repo

    if relative is None:
        relative = prefixSlash(cfg.get("provenanceSpec", {}).get("relative", None))
    else:
        cfg["provenanceSpec"]["relative"] = prefixSlash(relative)

    cfg["local"] = local
    cfg["localDir"] = getLocalDir(backend, cfg, local, version)

    avA = cfg.get("apiVersion", None)
    if isCompatible is None and checkApiVersion:
        isCompatible = avA is not None and avA == avTf
    if not isCompatible:
        if isCompatible is None:
            pass
        elif avA is None or avA < avTf:
            console(
                f"""
App `{appName}` requires API version {avA or 0} but TF provides {avTf}.
Your copy of the TF app `{appName}` is outdated for this version of TF.
Recommendation: obtain a newer version of `{appName}`.
Hint: load the app in one of the following ways:

    {org}/{repo}
    {org}/{repo}:latest
    {org}/{repo}:hot

    For example:

    The TF browser:

        tf {org}/{repo}:latest

    In a program / notebook:

        A = use('{org}/{repo}:latest', hoist=globals())

""",
                error=True,
            )
        else:
            console(
                f"""
App `{appName}` or rather `{org}/{repo}` requires API version {avA or 0}
but TF provides {avTf}.
Your TF is outdated and cannot use this version of the TF app `{org}/{repo}`.
Recommendation: upgrade TF.
Hint:

    pip install --upgrade text-fabric

""",
                error=True,
            )

    cfg["isCompatible"] = isCompatible

    if fileExists(cssPath):
        with fileOpen(cssPath) as fh:
            cfg["css"] = fh.read()
    else:
        cfg["css"] = ""

    return cfg


def findAppClass(appName, appPath):
    """Find the class definition of an app.

    The file `app.py` in the app directory will be looked up,
    if it exists, it will be loaded as a Python module, and from
    this module we try to get the class `TfApp`.

    Returns
    -------
    class | None
        If `TfApp` can be found and imported, it is the result.
        Otherwise we return `None`.
    """

    appPath = normpath(appPath)
    appClass = None
    moduleName = f"tf.apps.{appName}.app"
    filePath = f"{appPath}/app.py"
    if not fileExists(filePath):
        return None

    try:
        spec = util.spec_from_file_location(moduleName, f"{appPath}/app.py")
        code = util.module_from_spec(spec)
        sys.path.insert(0, appPath)
        spec.loader.exec_module(code)
        sys.path.pop(0)
        appClass = code.TfApp
    except Exception as e:
        console(f"findAppClass: {str(e)}", error=True)
        console(f'findAppClass: Api for "{appName}" not loaded')
        appClass = None
    return appClass


def loadModule(moduleName, *args):
    """Load a module dynamically, by name.

    Parameters
    ----------
    moduleName: string
        Name of a module under a TF app that needs to be imported.
    args: mixed
        The same list of arguments that is passed to `tf.advanced.app.App`
        of which only the `appName` and the `appPath` are used.
    """

    (appName, appPath) = args[1:3]
    appPath = normpath(appPath)
    try:
        spec = util.spec_from_file_location(
            f"tf.apps.{appName}.{moduleName}",
            f"{appPath}/{moduleName}.py",
        )
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        console(f"loadModule: {str(e)}", error=True)
        console(f'loadModule: {moduleName} in "{appName}" not found')
    return module
