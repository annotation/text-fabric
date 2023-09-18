import re


GENERIC = "PER"

FEATURES = ("eid", "kind")
NF = len(FEATURES)
KEYWORD_FEATURES = {FEATURES[-1]}
SUMMARY_INDICES = tuple(i for i in range(NF) if FEATURES[i] in KEYWORD_FEATURES)
SUMMARY_FEATURES = tuple(FEATURES[i] for i in SUMMARY_INDICES)

STYLES = dict(
    minus=dict(
        bg="#ffaaaa;"
    ),
    plus=dict(
        bg="#aaffaa;"
    ),
    replace=dict(
        bg="#ffff88;"
    ),
    free=dict(
        ff="monospace",
        fz="small",
        fw="normal",
        fg="black",
        bg="white",
    ),
    free_active=dict(
        fg="black",
        bg="yellow",
    ),
    free_bordered=dict(
        bg="#eeeeee",
        br="0",
        bw="1pt",
        bs="solid",
        bc="#aaaaaa",
        p="0.4rem",
        m="0.1rem 0.2rem",
    ),
    free_bordered_active=dict(
        bw="3pt",
        bs="solid",
        bc="black",
    ),
    keyword=dict(
        ff="monospace",
        fz="medium",
        fw="bold",
        fg="black",
        bg="#eeeeee",
    ),
    keyword_active=dict(
        fg="black",
        bg="yellow",
    ),
    keyword_bordered=dict(
        br="0.5rem",
        bw="2pt",
        bs="solid",
        bc="#aaaaaa",
        p="0.3rem",
        m="0.1rem 0.5rem",
    ),
    keyword_bordered_active=dict(
        bw="3pt",
        bs="solid",
        bc="black",
    ),
)

WHITE_RE = re.compile(r"""\s{2,}""", re.S)
NON_ALPHA_RE = re.compile(r"""[^\w ]""", re.S)


def ucFirst(x):
    return x[0].upper() + x[1:].lower()


def getText(F, slots):
    text = "".join(f"""{F.str.v(s)}{F.after.v(s) or ""}""" for s in slots).strip()
    text = WHITE_RE.sub(" ", text)
    return text


def get0(F, slots):
    text = getText(F, slots)
    text = NON_ALPHA_RE.sub("", text)
    text = text.replace(" ", ".").strip(".").lower()
    return text


def get1(F, slots):
    return GENERIC


featureDefault = {
    FEATURES[0]: get0,
    FEATURES[1]: get1,
}
