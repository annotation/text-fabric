import re
import unicodedata

from .html import H

from .settings import STYLES


WHITE_RE = re.compile(r"""\s+""", re.S)
NON_WORD = re.compile(r"""\W+""", re.S)

CUT_OFF = 20

TOKEN_RE = re.compile(r"""\w+|\W""")


TO_ASCII_DEF = dict(
    ñ="n",
    ø="o",
    ç="c",
)


TO_ASCII = {}

for u, a in TO_ASCII_DEF.items():
    TO_ASCII[u] = a
    TO_ASCII[u.upper()] = a.upper()


def normalize(text):
    return WHITE_RE.sub(" ", text).strip()


def toTokens(text):
    return tuple(TOKEN_RE.findall(normalize(text)))


def toAscii(text):
    return "".join(
        TO_ASCII.get(c, c)
        for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def toId(text):
    return NON_WORD.sub(".", toAscii(text.lower())).strip(".")


def toSmallId(text, transform={}):
    parts = [y for x in toId(text).split(".") if (y := transform.get(x, x))]
    result = []
    n = 0

    for part in parts:
        if len(part) > CUT_OFF:
            part = part[0:CUT_OFF]

        nPart = len(part)

        if n + nPart > CUT_OFF:
            break

        result.append(part)
        n += nPart

    return ".".join(result)


def repIdent(features, vals, active=""):
    return H.join(
        (H.span(val, cls=f"{feat} {active}") for (feat, val) in zip(features, vals)),
        sep=" ",
    )


def repSummary(keywordFeatures, vals, active=""):
    return H.join(
        (
            H.span(val, cls=f"{feat} {active}")
            for (feat, val) in zip(keywordFeatures, vals)
        ),
        sep=" ",
    )


def valRep(features, fVals):
    return ", ".join(f"<i>{feat}</i>={val}" for (feat, val) in zip(features, fVals))


def findCompile(bFind, bFindC):
    bFind = (bFind or "").strip()
    bFindFlag = [] if bFindC else [re.I]
    bFindRe = None
    errorMsg = ""

    if bFind:
        try:
            bFindRe = re.compile(bFind, *bFindFlag)
        except Exception as e:
            errorMsg = str(e)

    return (bFind, bFindRe, errorMsg)


def makeCss(features, keywordFeatures, generic=""):
    propMap = dict(
        ff="font-family",
        fz="font-size",
        fw="font-weight",
        fg="color",
        bg="background-color",
        bw="border-width",
        bs="border-style",
        bc="border-color",
        br="border-radius",
        p="padding",
        m="margin",
    )

    def makeBlock(manner):
        props = STYLES[manner]
        defs = [f"\t{propMap[abb]}: {val};\n" for (abb, val) in props.items()]
        return H.join(defs)

    def makeCssDef(selector, *blocks):
        return selector + " {\n" + H.join(blocks) + "}\n"

    css = []

    for feat in features:
        manner = "keyword" if feat in keywordFeatures else "free"

        plain = makeBlock(manner)
        bordered = makeBlock(f"{manner}_bordered")
        active = makeBlock(f"{manner}_active")
        borderedActive = makeBlock(f"{manner}_bordered_active")

        css.extend(
            [
                makeCssDef(f".{feat}", plain),
                makeCssDef(f".{feat}.active", active),
                makeCssDef(f"span.{feat}_sel,button.{feat}_sel", plain, bordered),
                makeCssDef(f"button.{feat}_sel[st=v]", borderedActive, active),
            ]
        )

    featureCss = H.join(css, sep="\n")
    allCss = generic + H.style(featureCss, type="text/css")
    return allCss
