from .applib.appmake import findAppClass

# START AN APP


def use(appName, *args, **kwargs):
  appClass = findAppClass(appName)
  if not appClass:
    return None
  return appClass(appName, *args, **kwargs)
