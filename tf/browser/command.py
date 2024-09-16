"""
Command-line argument processing
"""

from zlib import crc32

from ..parameters import PORT_BASE
from ..core.files import getLocation

# COMMAND-LINE ARGS


def getPort(slug):
    portOffset = crc32(slug.encode("utf8")) % 10000
    return PORT_BASE + portOffset


def argApp(cargs, simple):
    (appName, checkoutApp, dataLoc) = argParam(cargs)
    backend = _argCollect("backend", cargs)
    checkout = _argCollect("checkout", cargs)
    version = _argCollect("version", cargs)
    dataRelative = _argCollect("relative", cargs)

    if (
        appName is None
        and checkoutApp is None
        and dataLoc is None
        and backend is None
        and checkout is None
    ):
        (backend, org, repo, relative) = getLocation()
        appName = f"{org}/{repo}{relative}"
        checkoutApp = "clone"
        checkout = "clone"

    if simple:
        return f"{appName}:{version}"

    locations = _argCollect("locations", cargs)
    modules = _argCollect("modules", cargs)
    moduleRefs = _argCollect("mod", cargs)
    version = _argCollect("version", cargs)
    setFile = _argCollect("sets", cargs)

    return (
        None
        if appName is None
        else dict(
            appName=appName,
            backend=backend,
            checkoutApp=checkoutApp,
            dataLoc=dataLoc,
            checkout=checkout,
            relative=dataRelative,
            locations=locations,
            modules=modules,
            moduleRefs=moduleRefs,
            setFile=setFile,
            version=version,
        )
    )


def argNoweb(cargs):
    for arg in cargs:
        if arg == "-noweb":
            return True
    return False


def _argCollect(prefix, cargs):
    for arg in cargs:
        if arg.startswith(f"--{prefix}="):
            return arg[len(prefix) + 3 :]
    return None


def argParam(cargs):
    appName = None
    checkoutApp = None

    for arg in cargs:
        if arg.startswith("-"):
            continue
        appName = arg
        break

    if appName is None:
        return (None, None, None)

    if appName.startswith("data:"):
        dataLoc = appName[5:]
        appName = None
        checkoutApp = None
    elif appName.startswith("app:"):
        dataLoc = None
        checkoutApp = None
    else:
        dataLoc = None
        parts = appName.split(":", maxsplit=1)
        if len(parts) == 1:
            parts.append("")
        (appName, checkoutApp) = parts

    return (appName, checkoutApp, dataLoc)
