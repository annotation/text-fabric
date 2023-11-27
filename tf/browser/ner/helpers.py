"""Auxiliary functions.

To see how this fits among all the modules of this package, see
`tf.browser.ner.annotate` .
‹›
"""

import re
import unicodedata

from ..html import H

from .settings import STYLES


WHITE_RE = re.compile(r"""\s+""", re.S)
NON_WORD = re.compile(r"""\W+""", re.S)

CUT_OFF = 20
"""Maximum length of parts of entity identifiers."""

TOKEN_RE = re.compile(r"""\w+|\W""")


TO_ASCII_DEF = dict(
    ñ="n",
    ø="o",
    ç="c",
)
"""Undecomposable UNICODE characters mapped to their related ASCII characters."""


TO_ASCII = {}

for u, a in TO_ASCII_DEF.items():
    TO_ASCII[u] = a
    TO_ASCII[u.upper()] = a.upper()


def normalize(text):
    """Normalize white-space in a text."""
    return WHITE_RE.sub(" ", text).strip()


def toTokens(text, spaceEscaped=False):
    """Split a text into tokens.

    The text is split on white-space.
    Tokens are further split into maximal segments of word characters
    and individual non-word characters.

    Parameters
    ----------
    spaceEscaped: boolean, optional False
        If True, it is assumed that if a `_` occurs in a token string, a space is meant.
    """
    result = TOKEN_RE.findall(normalize(text))
    return tuple((t.replace("_", " ") for t in result) if spaceEscaped else result)


def toAscii(text):
    """Transforms a text with diacritical marks into a plain ASCII text.

    Characters with diacritics are replaced by their base character.
    Some characters with diacritics are considered by UNICODE to be undecomposable
    characters, such as `ø` and `ñ`.
    We use a table (`TO_ASCII_DEF`) to map these on their related ASCII characters.
    """
    return "".join(
        TO_ASCII.get(c, c)
        for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def toId(text):
    """Transforms text to an identifier string.

    Tokens are lower-cased, separated by `.`, reduced to ASCII.
    """
    return NON_WORD.sub(".", toAscii(text.lower())).strip(".")


def toSmallId(text, transform={}):
    """Transforms text to a smaller identifier string.

    As `toId()`, but now certain parts of the resulting identifier are
    either left out or replaced by shorter strings.

    This transformation is defined by the `transform` dictionary,
    which ultimately is provided in the corpus-dependent
    `ner/config.yaml` .
    """
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
    """Represents an identifier in HTML.

    Parameters
    ----------
    vals: iterable
        The material is given as a list of feature values.
    active: string, optional ""
        A CSS class name to add to the HTML representation.
        Can be used to mark the entity as active.
    """
    return H.join(
        (H.span(val, cls=f"{feat} {active}") for (feat, val) in zip(features, vals)),
        sep=" ",
    )


def repSummary(keywordFeatures, vals, active=""):
    """Represents an keyword value in HTML.

    Parameters
    ----------
    vals: iterable
        The material is given as a list of values of keyword features.
    active: string, optional ""
        A CSS class name to add to the HTML representation.
        Can be used to mark the entity as active.
    """
    return H.join(
        (
            H.span(val, cls=f"{feat} {active}")
            for (feat, val) in zip(keywordFeatures, vals)
        ),
        sep=" ",
    )


def valRep(features, fVals):
    """HTML representation of an entity as a sequence of `feat=val` strings."""
    return ", ".join(f"<i>{feat}</i>={val}" for (feat, val) in zip(features, fVals))


def findCompile(bFind, bFindC):
    """Compiles a regular expression out of a search pattern.

    Parameters
    ----------
    bFind: string
        The search pattern as a plain string.
    bFindC: boolean
        Whether the search is case-sensitive.

    Returns
    -------
    tuple
        the white-space-stripped search pattern;
        the regular expression object, if successful, otherwise None;
        the error message if the re-compilation was not successful.
    """
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


def makeCss(features, keywordFeatures):
    """Generates CSS for the tool.

    The CSS for this tool has a part that depends on the choice of entity features.
    For now, the dependency is mild: keyword features such as `kind` are formatted
    differently than features with an unbounded set of values, such as `eid`.

    Parameters
    ----------
    features, keywordFeatures: iterable
        What the features are and what the keyword features are.
        These derive ultimately from the corpus-dependent `ner/config.yaml`.
    """
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
    allCss = H.style(featureCss, type="text/css")
    return allCss
