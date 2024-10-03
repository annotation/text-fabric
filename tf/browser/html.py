"""HTML generation done in the Pythonic way.
"""
from ..core.generic import isIterable
from ..core.helpers import console, NBSP


H_ELEMENT_DEFS = """
    a
    b
    br>
    button
    code
    details
    div
    i
    input>
    li
    ol
    option
    p
    select
    span
    style
    summary
    table
    td
    tr
    ul
""".strip().split()

H_ELEMENTS = tuple(
    (x[0:-1], False) if x.endswith(">") else (x, True) for x in H_ELEMENT_DEFS
)
"""The HTML elements used in this tool."""


def dig(*content, sep=""):
    """A method to join nested iterables of strings into a string.

    Parameters
    ----------
    content: iterable or string
        Arbitrarily nested iterable of strings.
    sep: string, optional ""
        The string by which the individual strings from the iterables are to be joined.

    Returns
    -------
    string
        The fully joined string corresponding to the original iterables.
    """
    if len(content) == 0:
        return ""
    if len(content) == 1:
        content = content[0]
        return (
            sep.join(dig(c) for c in content)
            if isIterable(content)
            else
            str(content)
        )
    return sep.join(dig(c) for c in content)


def generate(close, tag, *content, **atts):
    """Transform the logical information for an HTML element into an HTML string.

    Parameters
    ----------
    close: boolean
        Whether the element must be closed with an end tag.
    tag: string
        The name of the tag.
    content: iterable
        The content of the element. This may be an arbitrarily nested iterable of
        strings.
    atts: dict
        The attributes of the element.

    Returns
    -------
    string
        The HTML string representation of an element.
    """
    endRep = f"""</{tag}>""" if close else ""

    attsRep = " ".join(
        (k if vl else "")
        if type(vl) is bool
        else f'''{"class" if k == "cls" else k}="{vl}"'''
        for (k, vl) in atts.items()
    )
    if attsRep:
        attsRep = f" {attsRep}"

    contentRep = dig(content)

    return f"""<{tag}{attsRep}>{contentRep}{endRep}"""


def elemFunc(close, elem):
    """Generates a function to serialize a specific HTML element.

    Parameters
    ----------
    close: boolean
        Whether the element needs an end tag.
    elem: string
        The name of the element.

    Returns
    -------
    function
        The function has the same signature as `generate()` except it does not
        take the parameters `close` and `tag`.
    """
    if close:

        def result(*content, **atts):
            return generate(close, elem, *content, **atts)

    else:

        def result(**atts):
            return generate(close, elem, **atts)

    return result


class H:
    """Provider of HTML serializing functions per element type.

    Also has a class attribute `nb`: the non-breaking space.

    For each HTML element in the specs (`H_ELEMENTS`) a corresponding
    generating function is added as method.
    """
    nb = NBSP


setattr(H, "join", dig)

for (elem, close) in H_ELEMENTS:
    setattr(H, elem, elemFunc(close, elem))


if __name__ == "__main__":
    console(H.input(type="hidden"))
    console(H.button("aap", "noot", "mies", type="hidden"))
    console(H.button(["aap", "noot", "mies"], type="hidden"))
    console(H.button(["aap", "noot", "mies", range(10)], type="hidden"))
    messages = [("error", "wrong!"), ("info", "succeeded!")]
    console(H.p((H.span(text, cls=lev) + H.br() for (lev, text) in messages)))
    console(H.join(range(10)))
    console(H.join([]))
