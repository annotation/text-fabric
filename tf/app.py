from .applib.find import findApp, findAppClass
from .applib.app import App

# START AN APP


def use(appName, *args, **kwargs):
    if '/' in appName:
        return App(appName, None, None, None, None, *args, **kwargs)

    parts = appName.split(":", maxsplit=1)
    if len(parts) == 1:
        parts.append("")
    (appName, checkoutApp) = parts
    (commit, release, local, appBase, appDir) = findApp(
        appName, checkoutApp, silent=kwargs.get("silent", False)
    )
    if not appBase:
        return None

    appPath = f"{appBase}/{appDir}"
    appClass = findAppClass(appName, appPath) or App

    return appClass(appName, appPath, commit, release, local, *args, **kwargs)
