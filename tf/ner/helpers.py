"""Auxiliary functions.
"""

import re
import unicodedata


WHITE_STRIP_RE = re.compile(r"""(?:\s|[​‌‍])+""")


def xstrip(x):
    return WHITE_STRIP_RE.sub("", x)


WHITE_RE = re.compile(r"""\s+""", re.S)
NON_WORD = re.compile(r"""\W+""", re.S)

LOC_RE = re.compile(r"[.:@]")

PART_CUT_OFF = 8
"""Maximum length of parts of entity identifiers."""

PREFIX_PART = 5
SUFFIX_PART = PART_CUT_OFF - PREFIX_PART - 1

CUT_OFF = 40
"""Maximum length of entity identifiers."""

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


def toTokens(text, spaceEscaped=False, caseSensitive=False):
    """Split a text into tokens.

    The text is split on white-space.
    Tokens are further split into maximal segments of word characters
    and individual non-word characters.

    Parameters
    ----------
    spaceEscaped: boolean, optional False
        If True, it is assumed that if a `_` occurs in a token string, a space is meant.
    caseSensitive: boolean, optional False
        If True, return all tokens in lower case.

    Returns
    -------
    tuple of string
        The sequence of tokens to which the text has decomposed
    """
    result = TOKEN_RE.findall(normalize(text))
    result = tuple((t.replace("_", " ") for t in result) if spaceEscaped else result)

    if not caseSensitive:
        result = tuple(t.lower() for t in result)

    return tuple(t for t in result if t != " ")


def fromTokens(tokens, spaceEscaped=False):
    """The inverse of `toTokens()`.

    Doing first toTokens and then fromTokens is idempotent (provided you do it in
    a case-sensitive way).
    So if you have to revert back from tokens to text,
    make sure that you have done a combo of toTokens and
    fromTokens first.
    You can use `tnorm()` for that.

    Parameters
    ----------
    spaceEscaped: boolean, optional False
        If True, it all ` ` in token strings will be escaped as `-`
    caseSensitive: boolean, optional False
        If True, return all tokens in lower case.

    Returns
    -------
    tuple of string
        The sequence of tokens to which the text has decomposed
    """
    return " ".join(
        tuple(t.replace(" ", "_") for t in tokens) if spaceEscaped else tokens
    )


def tnorm(text, spaceEscaped=False, caseSensitive=False):
    """Normalize text.

    Split a text into tokens and then recombine to text again.
    This will result in a normalized version of the text with respect to whitespace.

    Parameters
    ----------
    spaceEscaped: boolean, optional False
        If your corpus has tokens with spaces in it, pass True, otherwise False.
    caseSensitive: boolean, optional False
        If True, case sensitivity is preserved, otherwise all uppercase will be
        converted to lowercase.

    Returns
    -------
    string
    """
    return fromTokens(
        toTokens(text, spaceEscaped=spaceEscaped, caseSensitive=caseSensitive),
        spaceEscaped=spaceEscaped,
    )


def toAscii(text):
    """Transforms a text with diacritical marks into a plain ASCII text.

    Characters with diacritics are replaced by their base character.
    Some characters with diacritics are considered by UNICODE to be undecomposable
    characters, such as `ø` and `ñ`.
    We use a table (`TO_ASCII_DEF`) to map these on their related ASCII characters.

    Parameters
    ----------
    text: string
        The text to be translated

    Returns
    -------
    string
        The translated text.
    """
    return "".join(
        TO_ASCII.get(c, c)
        for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def toId(text):
    """Transforms text to an identifier string.

    Tokens are lower-cased, separated by `.`, reduced to ASCII.

    Parameters
    ----------
    text: string
        The text to be transformed

    Returns
    -------
        The identifier string based on `text`
    """
    return NON_WORD.sub(".", toAscii(text.lower())).strip(".")


def toSmallId(text, transform={}):
    """Transforms text to a smaller identifier string.

    As `toId()`, but now certain parts of the resulting identifier are
    either left out or replaced by shorter strings.

    This transformation is defined by the `transform` dictionary,
    which ultimately is provided in the corpus-dependent
    `ner/config.yaml` .

    Parameters
    ----------
    text: string
        The text to be transformed
    transform: dict, optional {}
        Custom transformations to be applied; usually this is the omission of frequent
        non-content words in the language.

    Returns
    -------
        The identifier string based on `text`
    """
    eid = toId(text)

    if len(eid) <= CUT_OFF:
        return eid

    parts = [y for x in eid.split(".") if (y := transform.get(x, x))]
    result = []
    n = 0

    for part in parts:
        if len(part) > PART_CUT_OFF:
            part = part[0:PREFIX_PART] + "~" + part[-SUFFIX_PART:]

        nPart = len(part)

        result.append(part)
        n += nPart

        if n > CUT_OFF:
            break

    return ".".join(result)


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
