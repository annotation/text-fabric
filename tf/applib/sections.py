import types


def sectionsApi(app):
  app.nodeFromSectionStr = types.MethodType(nodeFromSectionStr, app)
  app.sectionStrFromNode = types.MethodType(sectionStrFromNode, app)
  app._sectionLink = types.MethodType(_sectionLink, app)


def nodeFromSectionStr(app, sectionStr, lang='en'):
  api = app.api
  T = api.T
  sep1 = app.sectionSep1
  sep2 = app.sectionSep2
  msg = f'Not a valid passage: "{sectionStr}"'
  msgi = '{} "{}" is not a number'
  section = sectionStr.split(sep1)
  if len(section) > 2:
    return msg
  elif len(section) == 2:
    section2 = section[1].split(sep2)
    if len(section2) > 2:
      return msg
    section = [section[0]] + section2
  dataTypes = T.sectionFeatureTypes
  sectionTypes = T.sectionTypes
  sectionTyped = []
  msgs = []
  for (i, sectionPart) in enumerate(section):
    if dataTypes[i] == 'int':
      try:
        part = int(sectionPart)
      except ValueError:
        msgs.append(msgi.format(sectionTypes[i], sectionPart))
        part = None
    else:
      part = sectionPart
    sectionTyped.append(part)
  if msgs:
    return '\n'.join(msgs)

  sectionNode = T.nodeFromSection(sectionTyped, lang=lang)
  if sectionNode is None:
    return msg
  return sectionNode


def sectionStrFromNode(app, n, lang='en', lastSlot=False, fillup=False):
  api = app.api
  T = api.T
  seps = ('', app.sectionSep1, app.sectionSep2)

  section = T.sectionFromNode(n, lang=lang, lastSlot=lastSlot, fillup=fillup)
  return ''.join(
      '' if part is None else f'{seps[i]}{part}'
      for (i, part) in enumerate(section)
  )


def _sectionLink(app, n, text=None, className=None):
  newClassName = f'rwh {className or ""}'
  return app.webLink(n, className=newClassName, text=text, _asString=True, _noUrl=True)
