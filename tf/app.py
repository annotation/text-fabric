from .applib.app import findApp, findAppClass

# START AN APP


def use(appName, *args, **kwargs):
  (commit, appDir) = findApp(
      appName,
      kwargs.get('lgc', False),
      kwargs.get('check', False),
  )
  if not appDir:
    return None

  appClass = findAppClass(appName, appDir)
  if not appClass:
    return None

  return appClass(appName, appDir, commit, *args, **kwargs)
