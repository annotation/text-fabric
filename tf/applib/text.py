def textApi(app):
    api = app.api
    error = api.error
    T = api.T

    if app.isCompatible:
        formats = T.formats
        xFormats = T._xformats
        xdTypes = T._xdTypes
        defaultFormat = T.defaultFormat

        ac = app.context
        textFormats = ac.textFormats

        for (fmt, method) in textFormats.items():
            (descendType, method) = T.splitFormat(method)
            formats[fmt] = descendType
            xdTypes[fmt] = descendType
            func = f"fmt_{method}"
            if not hasattr(app, func):
                error(
                    f'WARNING: custom text format "{fmt}" is not implemented by method "{func}"'
                )
                func = xFormats[fmt] = xFormats[defaultFormat]
            else:
                func = getattr(app, func)
            xFormats[fmt] = func
