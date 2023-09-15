from ...core.generic import isIterable


H_ELEMENT_DEFS = """
    b
    br>
    button
    code
    div
    i
    input>
    option
    p
    select
    span
    style
""".strip().split()

H_ELEMENTS = tuple(
    (x[0:-1], False) if x.endswith(">") else (x, True) for x in H_ELEMENT_DEFS
)


def dig(*content, sep=""):
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
    endRep = f"""</{tag}>""" if close else ""

    attsRep = " ".join(
        (k if v else "")
        if type(v) is bool
        else f'''{"class" if k == "cls" else k}="{v}"'''
        for (k, v) in atts.items()
    )
    if attsRep:
        attsRep = f" {attsRep}"

    contentRep = dig(content)

    return f"""<{tag}{attsRep}>{contentRep}{endRep}"""


def elemFunc(close, elem):
    if close:

        def result(*content, **atts):
            return generate(close, elem, *content, **atts)

    else:

        def result(**atts):
            return generate(close, elem, **atts)

    return result


class H:
    pass


setattr(H, "join", dig)

for (elem, close) in H_ELEMENTS:
    setattr(H, elem, elemFunc(close, elem))


if __name__ == "__main__":
    print(H.input(type="hidden"))
    print(H.button("aap", "noot", "mies", type="hidden"))
    print(H.button(["aap", "noot", "mies"], type="hidden"))
    print(H.button(["aap", "noot", "mies", range(10)], type="hidden"))
    messages = [("error", "wrong!"), ("info", "succeeded!")]
    print(H.p((H.span(text, cls=lev) + H.br() for (lev, text) in messages)))
    print(H.join(range(10)))
    print(H.join([]))
