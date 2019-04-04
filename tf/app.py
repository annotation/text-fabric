from .applib.app import findApp, findAppClass

# START AN APP


def use(appName, *args, **kwargs):
  parts = appName.split(':', maxsplit=1)
  if len(parts) == 1:
    parts.append('')
  (appName, checkoutApp) = parts
  (commit, release, local, appDir) = findApp(appName, checkoutApp)
  if not appDir:
    return None

  appClass = findAppClass(appName, appDir)
  if not appClass:
    return None

  return appClass(appName, appDir, commit, release, local, *args, **kwargs)
