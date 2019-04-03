from .applib.app import findApp, findAppClass

# START AN APP


def use(appName, *args, **kwargs):
  parts = appName.split(':', maxsplit=1)
  if len(parts) == 1:
    parts.append('')
  (appName, checkoutApp) = parts
  (commit, appDir) = findApp(
      appName,
      checkoutApp,
      kwargs.get('lgc', False),
      kwargs.get('check', True),
  )
  if not appDir:
    return None

  appClass = findAppClass(appName, appDir)
  if not appClass:
    return None

  return appClass(appName, appDir, commit, *args, **kwargs)
