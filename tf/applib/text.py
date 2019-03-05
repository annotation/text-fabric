def textApi(app):
  api = app.api
  error = api.error
  T = api.T

  if hasattr(app, 'textFormats'):
    formats = T.formats
    xFormats = T._xformats
    defaultFormat = T.defaultFormat
    for (fmt, method) in app.textFormats.items():
      formats.add(fmt)
      func = f'fmt_{method}'
      if not hasattr(app, func):
        error(f'WARNING: custom text format "{fmt}" is not implemented by method "{func}"')
        func = xFormats[fmt] = xFormats[defaultFormat]
      else:
        func = getattr(app, func)
      xFormats[fmt] = func
