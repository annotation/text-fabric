import types
from textwrap import dedent
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


def specialCharacters(app, fmt=None, _browse=False):
    """Generate a widget for hard to type characters.

    For each text format it is known which characters may occur in the text.
    Some of those characters may be hard to type because they do not belong
    to the ASCII range of characters.
    All those characters will be listed in a widget, so that when you
    click such a character it is copied to your clipboard.
    The character will then turn yellow.

    Parameters
    ----------
    fmt: string, optional `None`
        The text format for which you want to display the character widget.
        If not passed, the default format will be chosen.

    Returns
    -------
    html
        A piece of HTML.
    """
    if fmt is None or fmt == "":
        fmt = DEFAULT_FORMAT

    formats = app.plainFormats

    if fmt.startswith("layout-"):
        fmt = "text" + fmt.removeprefix("layout")

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
    extraCls = '" class="ccline"' if _browse else ""
    html.append(dedent(
        f"""\
        <p><b>Special characters in <code>{fmt}</code></b></p>
        <p{extraCls}>
        """))
    for c in specials:
        cc = ord(c)
        html.append(
            f"""<code class="ccoff {extraCls}" """
            f"""onclick="copyChar(this, {cc})">{htmlEsc(c)}</code>"""
        )
    html.append("""</p>""")
    html = "\n".join(html)

    if _browse:
        return html
    return dh(html)
