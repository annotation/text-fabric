from .applib.app import findApp, findAppClass

# START AN APP


def use(appName, *args, **kwargs):
  parts = appName.split(':', maxsplit=1)
  if len(parts) == 1:
    parts.append('')
  (appName, checkoutApp) = parts
  (commit, release, local, appBase, appDir) = findApp(appName, checkoutApp)
  if not appBase:
    return None

  appPath = f'{appBase}/{appDir}'
  appClass = findAppClass(appName, appPath)
  if not appClass:
    return None

  return appClass(appName, appPath, commit, release, local, *args, **kwargs)
