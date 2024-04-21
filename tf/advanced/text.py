import types
from textwrap import dedent
from unicodedata import normalize

from ..core.text import DEFAULT_FORMAT
from ..core.helpers import htmlEsc
from .helpers import dh, dm, console


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
    app.showFormats = types.MethodType(showFormats, app)


def showFormats(app):
    inNb = app.inNb
    api = app.api
    T = api.T
    tFormats = T._tformats
    xFormats = T._xformats

    md = dedent(
        """\
    format | level | template
    --- | --- | ---
    """
    )

    for (fmt, level) in T.formats.items():
        tpl = (
            f"`{tFormats[fmt]}`"
            if fmt in tFormats
            else f"*function* `{xFormats[fmt].__name__}`"
            if fmt in xFormats
            else "*unknown*"
        )
        md += f"""`{fmt}` | **{level}** | {tpl}\n"""

    dm(md, inNb=inNb)


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
    fmt: string, optional None
        The text format for which you want to display the character widget.
        If not passed, the default format will be chosen.

    Returns
    -------
    string
        A piece of HTML.
    """

    inNb = app.inNb
    aContext = app.context
    formatCls = aContext.formatCls

    if fmt is None or fmt == "":
        fmt = DEFAULT_FORMAT

    textCls = formatCls.get(fmt, formatCls[DEFAULT_FORMAT]).lower()
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

    output = []
    extraCls = "ccline"
    output.append(
        dedent(
            f"""\
        <p><b>Special characters in <code>{fmt}</code></b></p>
        <p class="scharacters {extraCls} {textCls}">
        """
        )
    )
    charReps = []
    for c in specials:
        cc = ord(c)
        charReps.append(
            (
                f"""<span class="ccoff {extraCls}" title="{cc:>05x}" """
                f"""onclick="copyChar(this, {cc})">{htmlEsc(c)}</span>"""
            )
        )
    output.append(("\n").join(charReps))
    output.append("""</p>""")

    output = "\n".join(output)

    if _browse:
        return output
    if inNb is not None:
        dh(output, inNb=inNb)
    else:
        console(output)
