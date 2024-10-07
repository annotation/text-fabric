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
    """
    result = TOKEN_RE.findall(normalize(text))
    result = tuple((t.replace("_", " ") for t in result) if spaceEscaped else result)

    if not caseSensitive:
        result = tuple(t.lower() for t in result)

    return tuple(t for t in result if t != " ")


def fromTokens(tokens, spaceEscaped=False):
    """The inverse of `toTokens()`.

    Doing first toTokens and then fromTokens is idempotent.
    So if you have to revert back from tokens to text,
    make sure that you have done a combo of toTokens and
    fromTokens first.
    You can use `tnorm()` for that.
    """
    return " ".join(
        tuple(t.replace(" ", "_") for t in tokens) if spaceEscaped else tokens
    )


def tnorm(text, spaceEscaped=False, caseSensitive=False):
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


def repSet(s):
    return "{" + ", ".join(str(x) for x in sorted(s)) + "}"


# COMMON TOKENS


def hasCommon(tokensA, tokensB):
    """Whether one sequence of tokens interferes with another.

    The idea is: we want to determine whether matches for tokensA may interfere
    with matches for tokensB.

    This happens if tokensB is a sublist of tokensA, or if an initial segment of
    tokensB forms a tail inside tokensA.

    Or the same with tokensA and tokensB reversed.

    Proposition: tokensA en tokensB have something in common (in the above sense)
    if and only if you can make a text where tokensA and tokensB have overlapping
    matches. Proof follows.

    We return a result consisting of 3 integers: `ref`, `pos`, `length`

    *   `ref` is either 0, 1 or -1.

        It is 0 if tokensA and tokensB are identical.
        It is 1 if tokensA properly contains B or if tokensB starts somewhere
        in tokensA.
        It is -1 otherwise.

    Proof:

    (direction =>)

    Suppose tokensA and tokensB have something in common.

    Let i, j be the start-end position of the (part of) tokensB that occur in tokensA.
    Construct a match for the combination of tokensA and tokensB as follows:

    tokensA[0:i] + tokensA[i:j] + xxx

    Two cases:

    1.  tokensB is fully contained in tokensA.
        Then take for xxx: tokensA[j:].
        The result is a match for tokensA and hence for tokensB.
    2.  tokensB is only contained in A up to index k. By definition of common, this
        means that tokensB[0:k] is equal to tokensA[-k:] and hence
        that j == len(tokensA).
        Then take for xxx: tokensB[k:].
        We then have:

        tokensA + tokensB[k:] =

        tokensA[0:i] + tokensA[i:] + tokensB[k:]

        tkoensA[0:i] + tokensA[i:j] + tokensB[k:] = (because j == len(tokensA))

        tokensA[0:i] + tokensA[i:j] + tokensB[k:] =

        tokensA[0:i] + tokensB[0:k] + tokensB[k:] =

        tokensA[0:i] + tokensB

        So, this text is a match for tokensA and for tokensB

        (direction <=)

        Suppose we have a text T with an overlapping match for tokensA and tokensB.

        Suppose T[i:j] is a match for tokensA and T[n:m] is a match for tokensB, and
        T[i:j] and T[m:n] overlap.

        Two cases:

        1.  one match is contained in the other. We consider T[m:n] is
            contained in T[i:j]. For the reverse case, the argument is the same
            with tokensA and tokensB interchanged.

            T[m:n] is part of a match of tokensA, so T[m:n] occurs in tokensA.
            T[m:n] is also a match for tokensB, so tokensB == T[m:n], so tokensB
            is a part of tokensA, hence, by definition: tokensA and tokensB
            have something in common.
        2.  the two matches have a region in common, but none is contained in the
            other.
            We consider the case where m is between i and j. The case where i is
            between m and n is analogous, with tokensA and tokensB interchanged.

            Now T[m:j] is part of a match for tokensA and for tokensB.
            Then T[m:j] is at the end of T[i:j], so part of tokensB is at the
            end of tokensA.

    Test:

    ```
    from tf.ner.helpers import hasCommon

    tokensA = list("abcd")
    tokensB = list("cdef")
    tokensC = list("defg")
    tokensD = list("bc")
    tokensE = list("ab")
    tokensF = list("cd")
    tokensG = list("a")
    assert hasCommon(tokensA, tokensA) == (0, 0, 4), hasCommon(tokensA, tokensA)
    assert hasCommon(tokensA, tokensB) == (1, 2, 2), hasCommon(tokensA, tokensB)
    assert hasCommon(tokensB, tokensA) == (-1, 2, 2), hasCommon(tokensB, tokensA)
    assert hasCommon(tokensA, tokensC) == (1, 3, 1), hasCommon(tokensA, tokensC)
    assert hasCommon(tokensC, tokensA) == (-1, 3, 1), hasCommon(tokensC, tokensA)
    assert hasCommon(tokensA, tokensD) == (1, 1, 2), hasCommon(tokensA, tokensD)
    assert hasCommon(tokensD, tokensA) == (-1, 1, 2), hasCommon(tokensD, tokensA)
    assert hasCommon(tokensA, tokensE) == (1, 0, 2), hasCommon(tokensA, tokensE)
    assert hasCommon(tokensE, tokensA) == (-1, 0, 2), hasCommon(tokensE, tokensA)
    assert hasCommon(tokensA, tokensF) == (1, 2, 2), hasCommon(tokensA, tokensF)
    assert hasCommon(tokensF, tokensA) == (-1, 2, 2), hasCommon(tokensF, tokensA)
    assert hasCommon(tokensE, tokensG) == (1, 0, 1), hasCommon(tokensE, tokensG)
    assert hasCommon(tokensG, tokensE) == (-1, 0, 1), hasCommon(tokensG, tokensE)

    tokensA = list("abcd")
    tokensB = list("cef")
    tokensC = list("efg")
    tokensD = list("bd")
    tokensE = list("ac")
    tokensF = list("ad")

    assert hasCommon(tokensA, tokensB) == None, hasCommon(tokensA, tokensB)
    assert hasCommon(tokensB, tokensA) == None, hasCommon(tokensB, tokensA)
    assert hasCommon(tokensA, tokensC) == None, hasCommon(tokensA, tokensC)
    assert hasCommon(tokensC, tokensA) == None, hasCommon(tokensC, tokensA)
    assert hasCommon(tokensA, tokensD) == None, hasCommon(tokensA, tokensD)
    assert hasCommon(tokensD, tokensA) == None, hasCommon(tokensD, tokensA)
    assert hasCommon(tokensA, tokensE) == None, hasCommon(tokensA, tokensE)
    assert hasCommon(tokensE, tokensA) == None, hasCommon(tokensE, tokensA)
    assert hasCommon(tokensA, tokensF) == None, hasCommon(tokensA, tokensF)
    assert hasCommon(tokensF, tokensA) == None, hasCommon(tokensF, tokensA)
    ```
    """
    nA = len(tokensA)
    nB = len(tokensB)

    if tokensA == tokensB:
        return (0, 0, nA)

    for i in range(nA - 1, -1, -1):
        end = min((nB, nA - i))

        if tokensA[i : i + end] == tokensB[0:end]:
            ref = 1 if i > 0 else 1 if nA >= nB else -1
            return (ref, i, end)

    for i in range(nB - 1, -1, -1):
        end = min((nA, nB - i))

        if tokensB[i : i + end] == tokensA[0:end]:
            ref = -1 if i > 0 else -1 if nB >= nA else 1
            return (ref, i, end)

    return None


def makePartitions(triggers, myToTokens):
    """Partition a set of triggers into groups where triggers are pairwise disjoint.

    The intention is to explore all triggers that apparently do not have hits.
    We need to look them up in isolation, because then they might have hits.

    But searching per trigger is expensive. We want to group triggers together
    that can not interact with each other: triggers whose tokens are pairwise
    disjoint. A hit of one trigger can then never be part of a hit of any other
    trigger in the group.
    """

    triggerTokens = {}
    nTriggerTokens = {}

    for trigger in triggers:
        tokens = myToTokens(trigger)
        triggerTokens[trigger] = tokens
        nTriggerTokens.setdefault(len(tokens), {})[trigger] = tokens

    singleTokenTriggers = list(nTriggerTokens[1]) if 1 in nTriggerTokens else []

    partition = [singleTokenTriggers]

    for n in sorted(nTriggerTokens):
        if n == 1:
            continue
        for triggerA, tokensA in nTriggerTokens[n].items():
            added = False

            for part in partition:
                common = False

                for triggerB in part:
                    tokensB = triggerTokens[triggerB]

                    if hasCommon(tokensA, tokensB):
                        common = True
                        break

                if common:
                    continue

                part.append(triggerA)
                added = True
                break

            if not added:
                partition.append([triggerA])

    return (triggerTokens, partition)


# SCOPES
