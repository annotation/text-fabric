import sys
import os
from importlib import util
import yaml

from ..parameters import (
    APP_CONFIG,
    APP_DISPLAY,
    API_VERSION as apiVersionProvided,
)
from ..core.helpers import console
from .helpers import getLocalDir


def findAppConfig(appName, appPath, commit, release, local, version=None):
    """Find the config information of an app.

    If there is a `config.yaml` file, read it and check the compatibility
    of the config settings with the current version of Text-Fabric.

    If there is no such file, fill in a few basic settings.

    See Also
    --------
    tf.applib.settings: options allowed in `config.yaml`
    """

    configPath = f"{appPath}/{APP_CONFIG}"
    cssPath = f"{appPath}/{APP_DISPLAY}"

    checkApiVersion = True

    if os.path.exists(configPath):
        with open(configPath) as fh:
            cfg = yaml.load(fh, Loader=yaml.FullLoader)
    else:
        cfg = {}
        checkApiVersion = False
    cfg.update(
        appName=appName, appPath=appPath, commit=commit, release=release, local=local
    )

    if version is None:
        version = cfg.setdefault("provenanceSpec", {}).get("version", None)
    else:
        cfg.setdefault("provenanceSpec", {})["version"] = version

    if os.path.exists(cssPath):
        with open(cssPath, encoding="utf8") as fh:
            cfg["css"] = fh.read()
    else:
        cfg["css"] = ""

    cfg["local"] = local
    cfg["localDir"] = getLocalDir(cfg, local, version)

    apiVersionRequired = cfg.get("apiVersion", None)
    isCompatible = (
        None
        if not checkApiVersion
        else (
            apiVersionRequired is not None and apiVersionRequired == apiVersionProvided
        )
    )
    if not isCompatible:
        if isCompatible is None:
            console("No app configuration found.")
        elif apiVersionRequired is None or apiVersionRequired < apiVersionProvided:
            console(
                f"""
Your copy of the TF app `{appName}` is outdated for this version of TF.
Recommendation: obtain a newer version of `{appName}`.
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
Text-Fabric will be loaded, but no app specific code will be loaded
and app config may not be optimal.
The corpus data may not be found.
"""
        )

    cfg["isCompatible"] = isCompatible
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
        Otherwise we return `none`.
    """

    appClass = None
    moduleName = f"tf.apps.{appName}.app"
    filePath = f"{appPath}/app.py"
    if not os.path.exists(filePath):
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
        Name of a module under a TF-app that needs to be imported.
    args: mixed
        The same list of arguments that is passed to `tf.applib.app.App`
        of which only the `appName` and the `appPath` are used.
    """

    (appName, appPath) = args[1:3]
    try:
        spec = util.spec_from_file_location(
            f"tf.apps.{appName}.{moduleName}", f"{appPath}/{moduleName}.py",
        )
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        console(f"loadModule: {str(e)}", error=True)
        console(f'loadModule: {moduleName} in "{appName}" not found')
    return module
