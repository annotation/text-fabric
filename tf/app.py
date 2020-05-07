from .applib.app import findApp

# START AN APP


def use(appName, *args, **kwargs):
    parts = appName.split(":", maxsplit=1)
    if len(parts) == 1:
        parts.append("")
    (appName, checkoutApp) = parts

    return findApp(appName, checkoutApp, *args, **kwargs)
