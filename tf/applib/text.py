def textApi(app):
    api = app.api
    T = api.T

    if app.isCompatible:
        formats = T.formats
        xFormats = T._xformats
        xdTypes = T._xdTypes

        aContext = app.context
        formatMethod = aContext.formatMethod

        for (fmt, method) in formatMethod.items():
            (descendType, fmt) = T.splitFormat(fmt)
            formats[fmt] = descendType
            xdTypes[fmt] = descendType
            func = getattr(app, f"fmt_{method}")
            xFormats[fmt] = func

        aContext.allFormats = T.formats
