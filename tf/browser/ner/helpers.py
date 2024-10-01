"""Auxiliary functions.

To see how this fits among all the modules of this package, see
`tf.browser.ner.ner` .
‹›
"""

import re
import unicodedata
import functools

from ...core.helpers import console
from ..html import H
from .settings import STYLES


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


def getIntvIndex(buckets, instructions, getHeadings):
    intervals = sortScopes(x for x in instructions if x != ())

    nIntervals = len(intervals)

    if nIntervals == 0:
        return {bucket: () for bucket in buckets}

    intvIndex = {}
    i = 0
    intv = intervals[i]
    (b, e) = intv

    for bucket in buckets:
        hd = getHeadings(bucket)

        assigned = False

        if _locCmp(b, hd) == 1:
            intvIndex[bucket] = ()
            continue

        while i < nIntervals:
            if _locCmp(e, hd) == -1:
                i += 1

                if i < nIntervals:
                    intv = intervals[i]
                    (b, e) = intv
                else:
                    intvIndex[bucket] = ()
                    assigned = True
                    break
            else:
                intvIndex[bucket] = () if _locCmp(b, hd) == 1 else intv
                assigned = True
                break

        if not assigned:
            intvIndex[bucket] = ()

    return intvIndex


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
    from tf.browser.ner.helpers import hasCommon

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


def interference(
    rowMap, triggerScopes, myToTokens, alsoInternal=False, alsoExpected=False
):
    triggers = list(rowMap)

    triggerTokens, parts = makePartitions(triggers, myToTokens)

    nParts = len(parts)

    interferences = []

    intersections = {}

    for i, part in enumerate(parts):
        if i == nParts - 1:
            break

        for otherPart in parts[i + 1 : nParts]:
            for triggerA in part:
                for triggerB in otherPart:
                    tokensA = triggerTokens[triggerA]
                    tokensB = triggerTokens[triggerB]

                    if not alsoInternal:
                        rowsA = set(rowMap[triggerA])
                        rowsB = set(rowMap[triggerB])
                        if rowsA == rowsB:
                            continue

                    scopesA = ",".join(sorted(triggerScopes[triggerA]))
                    scopesB = ",".join(sorted(triggerScopes[triggerB]))
                    commonScopes = intersections.get((triggerA, triggerB), None)

                    if commonScopes is None:
                        commonScopes = intersectScopes(scopesA, scopesB)
                        intersections[(triggerA, triggerB)] = commonScopes

                    if len(commonScopes) == 0:
                        continue

                    common = hasCommon(tokensA, tokensB)

                    if common is None:
                        continue

                    ref, pos, length = common
                    nTokensA = len(tokensA)
                    nTokensB = len(tokensB)

                    nTokensLatter = nTokensB if ref == 1 else nTokensA

                    expected = length == nTokensLatter

                    if expected and not alsoExpected:
                        continue

                    if ref == 1:
                        nB = len(tokensB)
                        union = tokensA

                        if length < nB:
                            union += tokensB[length:]
                    else:
                        nA = len(tokensA)
                        union = tokensB

                        if length < nA:
                            union += tokensA[length:]

                    interferences.append(
                        (
                            triggerA,
                            triggerB,
                            " ".join(union),
                            scopesA,
                            scopesB,
                            commonScopes,
                        )
                    )

    parts = makePartitions([x[2] for x in interferences], myToTokens)[1]

    return interferences, parts


# SCOPES


def _prevLoc(x):
    # only for locs that can start a scope

    if x[2] != 0:
        return (x[0], x[1], x[2] - 1)

    if x[1] != 0:
        return (x[0], x[1] - 1, -1)

    if x[0] != 0:
        return (x[0] - 1, -1, -1)

    return (0, 0, 0)


def _nextLoc(x):
    # only for locs that can end a scope

    if x[2] != -1:
        return (x[0], x[1], x[2] + 1)

    if x[1] != -1:
        return (x[0], x[1] + 1, 0)

    if x[0] != -1:
        return (x[0] + 1, 0, 0)

    return (-1, -1, -1)


def _pointCmp(x, y):
    return 0 if x == y else -1 if y == -1 or (x != -1 and x < y) else 1


def _locCmp(xLoc, yLoc):
    for x, y in zip(xLoc, yLoc):
        if x != y:
            eq = _pointCmp(x, y)

            if eq != 0:
                return eq

    return 0


def _locMax(xLoc, yLoc):
    return xLoc if _locCmp(xLoc, yLoc) == 1 else yLoc


def _locMin(xLoc, yLoc):
    return xLoc if _locCmp(xLoc, yLoc) == -1 else yLoc


def _sameLoc(xLoc, yLoc):
    return all(
        xc == yc or ((xc == -1 or xc == 0) and (yc == -1 or yc == 0))
        for (xc, yc) in zip(xLoc, yLoc)
    )


def _scopeBefore(xScope, yScope):
    (xB, xE) = xScope
    (yB, yE) = yScope

    eqx = _locCmp(xB, yB)

    return _locCmp(yE, xE) if eqx == 0 else eqx


_locSort = functools.cmp_to_key(_locCmp)
_scopeSort = functools.cmp_to_key(_scopeBefore)


def sortLocs(locs):
    return tuple(sorted(locs, key=_locSort))


def sortScopes(scopes):
    return tuple(sorted(scopes, key=_scopeSort))


def locInScope(loc, scope):
    (b, e) = scope
    return _locCmp(b, loc) <= 0 and _locCmp(loc, e) <= 0


def locInScopes(loc, scopes):
    if not len(scopes):
        return False

    return any(locInScope(loc, scope) for scope in scopes)


def repLoc(loc):
    return ".".join(
        f"{x:02}" if i == 0 else f"{x:03}" if i == 1 else f"{x}"
        for (i, x) in enumerate(loc)
        if x != 0 and x != -1
    )


def parseLoc(locStr, plain=True):
    locStr = locStr.strip()

    if not locStr:
        result = ()
        return () if plain else dict(result=(), warning=None, normal=repLoc(result))

    parts = LOC_RE.split(locStr, maxsplit=2)

    if any(x != "-1" and not (x.lstrip("0") or "0").isdecimal() for x in parts):
        result = None
        normal = None
        warning = f"not a valid location: {locStr}"
    else:
        result = tuple(int(x.lstrip("0") or "0") for x in parts)
        normal = repLoc(result)
        warning = None

    return result if plain else dict(result=result, warning=warning, normal=normal)


def repScope(scope):
    if scope is None or len(scope) == 0:
        return "()"

    (b, e) = scope
    return repLoc(b) if _sameLoc(b, e) else f"{repLoc(b)}-{repLoc(e)}"


def repScopes(scopes):
    return ", ".join(repScope(scope) for scope in scopes)


def parseScope(scopeStr, plain=True):
    result = None
    warnings = []

    scopeStr = scopeStr.strip()

    if not scopeStr:
        result = ((0, 0, 0), (-1, -1, -1))
        return (
            result
            if plain
            else dict(result=result, warning=warnings, normal=repScope(result))
        )

    parts = scopeStr.split("-", 1)

    if len(parts) == 1:
        info = parseLoc(scopeStr, plain=False)
        w = info["warning"]

        if w:
            warnings.append(w)
        else:
            s = info["result"]
            result = (
                (s + (0, 0, 0))[0:3],
                (s + (-1, -1, -1))[0:3],
            )
    else:
        part = parts[0].strip()
        info1 = parseLoc(part, plain=False)
        w1 = info1["warning"]

        part = parts[1].strip()
        info2 = parseLoc(part, plain=False)
        w2 = info2["warning"]

        if w1 or w2:
            if w1:
                warnings.append(w1)
            if w2:
                warnings.append(w2)
        else:
            s1 = info1["result"]
            s2 = info2["result"]
            result = (
                (s1 + (0, 0, 0))[0:3],
                (s2 + (-1, -1, -1))[0:3],
            )

    normal = None if result is None else repScope(result)

    return result if plain else dict(result=result, warning=warnings, normal=normal)


def parseScopes(scopeStr, plain=True):
    results = []
    warnings = []

    if not scopeStr:
        return () if plain else dict(result=(), warning=warnings, normal="")

    for scopeStrPart in scopeStr.split(","):

        if not scopeStrPart:
            continue

        info = parseScope(scopeStrPart, plain=plain)
        result = info if plain else info["result"]

        if result is None:
            if not plain:
                warnings.extend(info["warning"])
            continue

        results.append(result)

    results = tuple(sortScopes(results))

    return (
        results
        if plain
        else dict(result=results, warning=warnings, normal=repScopes(results))
    )


def intersectScopes(*scopeStrs):
    curIntersection = [parseScope("")]

    for scopeStr in scopeStrs:
        newIntersection = []
        for bLoc, eLoc in parseScopes(scopeStr):

            for ibLoc, ieLoc in curIntersection:
                if _locCmp(ieLoc, bLoc) == -1:
                    # ieLoc < bLoc
                    continue
                if _locCmp(ibLoc, eLoc) == 1:
                    # ibLoc > eLoc
                    break

                # now
                # bLoc <= ieLoc
                # ibLoc <= eLoc
                newIbLoc = _locMax(ibLoc, bLoc)
                newIeLoc = _locMin(ieLoc, eLoc)
                newIntersection.append((newIbLoc, newIeLoc))

        curIntersection = newIntersection

    return tuple(curIntersection)


def partitionScopes(scopesDict):
    scopeFromStr = {}
    strFromScope = {}
    boundaries = {}
    intervals = []

    for scopeStr, scopes in scopesDict.items():
        for scope in scopes:
            (b, e) = scope
            boundaries.setdefault(b, {}).setdefault("b", set()).add(scope)
            boundaries.setdefault(e, {}).setdefault("e", set()).add(scope)

            scopeFromStr.setdefault(scopeStr, set()).add(scope)
            strFromScope.setdefault(scope, set()).add(scopeStr)

    curScopes = set()
    inScope = False

    for x in sortLocs(boundaries):
        beginScopes = boundaries[x].get("b", set())
        endScopes = boundaries[x].get("e", set())

        inScope = len(curScopes) > 0

        hasB = len(beginScopes) > 0
        hasE = len(endScopes) > 0

        if hasB and hasE:
            intervals[-1][1] = _prevLoc(x)
            if intervals[-1][1] < intervals[-1][0]:
                intervals.pop()
            curScopes |= beginScopes
            intervals.append([x, x, sortScopes(curScopes)])
            curScopes -= endScopes
            inScope = len(curScopes) > 0
            if inScope:
                intervals.append([_nextLoc(x), None, sortScopes(curScopes)])
        elif hasB:
            if inScope:
                intervals[-1][1] = _prevLoc(x)
                if intervals[-1][1] < intervals[-1][0]:
                    intervals.pop()
            curScopes |= beginScopes
            intervals.append([x, None, sortScopes(curScopes)])
        elif hasE:
            intervals[-1][1] = x
            curScopes -= endScopes
            inScope = len(curScopes) > 0
            if inScope:
                intervals.append([_nextLoc(x), None, sortScopes(curScopes)])

    if inScope:
        intervals[-1][1] = x

    for x in intervals:
        newX = []
        seen = set()

        for scope in x[2]:
            for scopeStr in strFromScope[scope]:
                if scopeStr in seen:
                    continue

                seen.add(scopeStr)
                newX.append(scopeStr)

        x[2] = tuple(newX)

    return intervals


def testScopes(scopeStrs):
    scopeIndex = {}

    for scopeStr in scopeStrs:
        info = parseScopes(scopeStr, plain=False)
        warning = info["warning"]

        if len(warning):
            console(f"Errors in {scopeStr}: {'; '.join(warning)}")
        else:
            scopes = info["result"]
            normScopeStr = info["normal"]
            console(f"{scopeStr} => {normScopeStr}\n\t{repScopes(sortScopes(scopes))}")
            scopeIndex[normScopeStr] = scopes

    partitionScopes(scopeIndex)
