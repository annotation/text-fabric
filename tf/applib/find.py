import sys
import os
from collections import namedtuple

from importlib import util
import yaml

from ..parameters import (
    ORG,
    APP_CODE,
    APP_CONFIG,
    APP_DISPLAY,
    API_VERSION as apiVersionProvided,
)
from ..core.helpers import console
from .repo import checkoutRepo
from .helpers import getLocalDir


Browser = namedtuple(
    "Browser",
    """
    protocol
    host
    port
""".strip().split(),
)


def findApp(appName, checkoutApp, silent=False):
    if not appName or "/" in appName:
        appPath = os.path.expanduser(appName) if appName else ""
        absPath = os.path.abspath(appPath)
        if os.path.isdir(absPath):
            (appDir, appName) = os.path.split(absPath)
            return (None, None, None, "", appDir, appName)
        else:
            console(f"{absPath} is not an existing directory", error=True)
            return (None, None, None, False, None, None)
    else:
        return (
            *checkoutRepo(
                org=ORG,
                repo=f"app-{appName}",
                folder=APP_CODE,
                checkout=checkoutApp,
                withPaths=True,
                keep=False,
                silent=silent,
                label="TF-app",
            ),
            appName,
        )


def findAppConfig(appName, appPath, commit, release, local, version=None):
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

    cfg.setdefault("provenanceSpec", {})["version"] = version

    if os.path.exists(cssPath):
        with open(cssPath, encoding="utf8") as fh:
            cfg["css"] = fh.read()
    else:
        cfg["css"] = ""

    cfg["local"] = local
    cfg["localDir"] = getLocalDir(cfg, local, version)

    apiVersionRequired = cfg.get("apiVersion", None)
    isCompatible = not checkApiVersion or (
        apiVersionRequired is not None and apiVersionRequired == apiVersionProvided
    )
    if not isCompatible:
        if apiVersionRequired is None or apiVersionRequired < apiVersionProvided:
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

    cfg["isCompatible"] = isCompatible
    return cfg


def findAppClass(appName, appPath):
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
        console(f'findAppClass: Api for "{appName}" not found')
        appClass = None
    return appClass


def loadModule(dataSource, appPath, moduleName):
    try:
        spec = util.spec_from_file_location(
            f"tf.apps.{dataSource}.{moduleName}", f"{appPath}/{moduleName}.py",
        )
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        console(f"loadModule: {str(e)}", error=True)
        console(f'loadModule: {moduleName} in "{dataSource}" not found')
    return module
