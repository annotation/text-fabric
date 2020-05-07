def textApi(app):
    api = app.api
    T = api.T
    F = api.F
    fOtype = F.otype.v

    def rescue(n, **kwargs):
        return f"{fOtype(n)}{n}"

    formats = T.formats
    xFormats = T._xformats
    xdTypes = T._xdTypes

    aContext = app.context
    formatMethod = aContext.formatMethod

    for (fmt, method) in formatMethod.items():
        (descendType, fmt) = T.splitFormat(fmt)
        formats[fmt] = descendType
        xdTypes[fmt] = descendType
        func = getattr(app, f"fmt_{method}", rescue)
        xFormats[fmt] = func

    aContext.allFormats = T.formats
