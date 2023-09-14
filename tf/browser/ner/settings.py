import re


GENERIC = "any"

FEATURES = ("eid", "kind")
NF = len(FEATURES)
KEYWORD_FEATURES = set(FEATURES[-1])

WHITE_RE = re.compile(r"""\s{2,}""", re.S)


def ucFirst(x):
    return x[0].upper() + x[1:].lower()


def getText(F, slots):
    return WHITE_RE.sub(
        " ",
        "".join(f"""{F.str.v(s)}{F.after.v(s) or ""}""" for s in slots).strip(),
    )


def get0(F, slots):
    return WHITE_RE.sub(
        "", "".join(ucFirst(x) for s in slots if (x := F.str.v(s).strip())).strip()
    )


def get1(F, slots):
    return GENERIC


featureDefault = {
    FEATURES[0]: get0,
    FEATURES[1]: get1,
}
