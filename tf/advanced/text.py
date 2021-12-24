import types
from unicodedata import normalize

from ..core.text import DEFAULT_FORMAT
from ..core.helpers import htmlEsc
from .helpers import dh


def textApi(app):
    api = app.api
    T = api.T
    F = api.F
    fOtype = F.otype.v

    def rescue(n, **kwargs):
        return f"{fOtype(n)}{n}"

    formats = T.formats
    app.plainFormats = set(formats)
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

    aContext.allowedValues["textFormat"] = T.formats
    app.specialCharacters = types.MethodType(specialCharacters, app)


def specialCharacters(app, fmt=None):
    if fmt is None:
        fmt = DEFAULT_FORMAT

    formats = app.plainFormats

    if fmt not in formats:
        choices = "\n\t".join(formats)
        default = f"or omit the fmt parameter to use {DEFAULT_FORMAT} by default"
        app.error(
            f"No such format: {fmt}. Choose one from\n\t{choices}\n{default}", tm=False
        )
        return None

    api = app.api
    C = api.C

    characters = C.characters.data
    freqList = characters[fmt]

    specials = sorted(
        (c for (c, f) in freqList if not c.isascii()),
        key=lambda c: normalize("NFD", c.upper()),
    )

    html = []
    html.append(f"""<p><b>Special characters in <code>{fmt}</code></b>""")
    for c in specials:
        cc = ord(c)
        html.append(
            """<code class="ccoff" """
            f"""onclick="copyChar(this, {cc})">{htmlEsc(c)}</code>"""
        )
    html.append("""</p>""")
    return dh("\n".join(html))
