from .applib.find import findApp, findAppClass
from .applib.app import App

# START AN APP


def use(appName, *args, **kwargs):
    parts = appName.split(":", maxsplit=1)
    if len(parts) == 1:
        parts.append("")
    (appName, checkoutApp) = parts

    (commit, release, local, appBase, appDir, appName) = findApp(
        appName, checkoutApp, silent=kwargs.get("silent", False)
    )
    if not appBase and appBase != "":
        return None

    appBaseRep = f"{appBase}/" if appBase else ""
    appPath = f"{appBaseRep}{appDir}"

    appClass = findAppClass(appName, appPath) or App

    return appClass(appName, appPath, commit, release, local, *args, **kwargs)
