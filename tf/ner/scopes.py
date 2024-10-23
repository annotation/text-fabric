"""Scope handling

Scopes are a column in entity spreadsheets that limit the effects of entity
triggers. This module defines data structures for scopes and some fundamental
operations on them, such as representing them as string, parsing them from strings,
comparing and sorting them.

A scope specification is a comma-separated list of interval strings.

An interval string is either a section or an interval between two sections.

A section is written as a section heading, an interval as two section headings
with a `-` in between.

An interval is taken from the start of the first section to the end of the
second section.

A section on its own is taken from its start to its end.

Examples:

*   `3` is the whole of section `3`
*   `3-3.4` is from the start of section `3` to the end of section `3.4`
*   `3.4-3` is from the start of section `3.4` to the end of section `3`
*   `3.4-5` is from the start of section `3.4`, through the rest of section `3`,
    through the whole of section `4`, till the end of section `5`

A section heading is written as it appears when TF represents sections.
If you browse the corpus in the TF browser you'll see how those
sections are represented. Even if section headings are not numeric, TF knows
which sections you mean:

*   `Genesis 1:5-Deuteronomy 26:6` if from the start of book Genesis
    chapter 1 verse 5, through the rest of Genesis, through the books of
    Exodus and Leviticus, till the end of Deuteronomy chapter 26 verse 6.

Even if the headings given at the boundaries of an interval are numeric, TF
knows the exact ordering of all sections, and will fill them in.

Suppose in a corpus you have main sections `1`, `4`, `3`, `3b`, `5` in that
order, then:

*   `1-5` is from the start of `1`, through `4`, `3`, `3b`, to the end of `5`
*   `1-4` is sections `1` and `4` *only*
*   `1-3` is sections `1`, `4`, `3` *only*
*   `3-5` is sections `3`, `3b` and `5` *only*

Implementation detail: Text-Fabric pre-computes the sequence of all sections
in your corpus, and maps them onto a legal numbering system, where each
section corresponds to a tuple of sequence numbers. For example, in the
[Hebrew Bible](https://github.com/ETCBC/bhsa),
`Exodus 3:4` is mapped to `(2, 3, 4)` since `Exodus` is the
second top level section in that corpus.

In the [Suriano letters](https://gitlab.huc.knaw.nl/suriano/letters),
`04@027:5` is mapped to `(3, 27, 5)`, since the main sections start at
`02`, there is no `01`.

The inverse mapping is also present in the pre-computed data of the corpus.
These mappings are from section nodes to legal number tuples and back.
The mapping from section node to heading string and back is is done by
TF functions `tf.advanced.sections.sectionStrFromNode()` and
`tf.advanced.sections.nodeFromSectionStr()`.
"""

import functools

from ..core.helpers import console


def _prevLoc(x):
    """Find the previous location.

    Only for locs that can start a scope.

    Parameters
    ----------
    tuple
        The tuple is a "legal" section number, possibly with `0` in them, but not `-1`.

    Returns
    -------
    tuple
        Nearly the same tuple, but with the last element decreased by one, if possible,
        otherwise the last element is set to `-1` and the next last element is
        decreased by one, if possible, and so on.
    """

    if x[2] != 0:
        return (x[0], x[1], x[2] - 1)

    if x[1] != 0:
        return (x[0], x[1] - 1, -1)

    if x[0] != 0:
        return (x[0] - 1, -1, -1)

    return (0, 0, 0)


def _nextLoc(x):
    """Find the next location.

    Only for locs that can end a scope.

    Parameters
    ----------
    tuple
        The tuple is a "legal" section number, possibly with `-1` in them, but not `0`.

    Returns
    -------
    tuple
        Nearly the same tuple, but with the last element increased by one, if it is not
        `-1`, otherwise the last element is set to `0` and the next last element is
        increased by one, if it is not `-1`, and so on.
    """

    if x[2] != -1:
        return (x[0], x[1], x[2] + 1)

    if x[1] != -1:
        return (x[0], x[1] + 1, 0)

    if x[0] != -1:
        return (x[0] + 1, 0, 0)

    return (-1, -1, -1)


def _pointCmp(x, y):
    """Compares two section sequence numbers, only one component of them.

    We reckon with the value `-1` under the interpretation that it is the last one.

    Parameters
    ----------
    x: integer
        The first point
    y: integer
        The second point

    Returns
    -------
    integer
        0 if they are equal, -1 if the first comes before the second, -1 otherwise.
    """
    return 0 if x == y else -1 if y == -1 or (x != -1 and x < y) else 1


def _locCmp(xLoc, yLoc):
    """Compares two full section sequence numbers.

    Parameters
    ----------
    xLoc: tuple
        The first section
    yLoc: tuple
        The second section

    Returns
    -------
    integer
        0 if they are equal, -1 if the first comes before the second, -1 otherwise.
    """
    for x, y in zip(xLoc, yLoc):
        if x != y:
            eq = _pointCmp(x, y)

            if eq != 0:
                return eq

    return 0


def _locMax(xLoc, yLoc):
    """Which of two sections comes last?

    Parameters
    ----------
    xLoc: tuple
        The first section
    yLoc: tuple
        The second section

    Returns
    -------
    tuple
        either `xLoc` or `yLoc`, whichever comes last.
    """
    return xLoc if _locCmp(xLoc, yLoc) == 1 else yLoc


def _locMin(xLoc, yLoc):
    """Which of two sections comes first?

    Parameters
    ----------
    xLoc: tuple
        The first section
    yLoc: tuple
        The second section

    Returns
    -------
    tuple
        either `xLoc` or `yLoc`, whichever comes first.
    """
    return xLoc if _locCmp(xLoc, yLoc) == -1 else yLoc


def _sameLoc(xLoc, yLoc):
    """Whether two section tuples correspond to the same section.

    Example: `(2, 0 , 0)` is the same section as `(2,)`, likewise
    `(2, -1, -1)` is the same section as `(2,)`, although they point
    to different places within that section.

    This function abstracts from that difference in representation.

    Parameters
    ----------
    xLoc: tuple
        The first section
    yLoc: tuple
        The second section

    Returns
    -------
    boolean
        whether both tuples refer to the same section.
    """
    return all(
        xc == yc or ((xc == -1 or xc == 0) and (yc == -1 or yc == 0))
        for (xc, yc) in zip(xLoc, yLoc)
    )


def _intervalCmp(xIntv, yIntv):
    """Compares two intervals of section sequence numbers.

    We extend the notion of before and after from sections to intervals.
    The canonical rule is this:

    The interval that starts earlier comes first, no matter what.
    If both intervals have the same start point, the one that ends *later* comes
    first.
    So containing intervals preceded contained intervals, and this makes this
    relationship a generalization of the pre-order in trees.
    If you have a nest of intervals and all pairs of intervals either are disjunct,
    or the one lies embedded in the other, then this nest is a tree. The children of
    an interval are the intervals properly embedded in it. The pre-order on this tree
    is exactly defined as the canonical rule above.

    But if there are intervals that properly overlap each other, the canonical rule
    still makes sense, hence we have a generalization of the tree order.

    Parameters
    ----------
    xIntv: tuple
        The first interval
    yIntv: tuple
        The second interval

    Returns
    -------
    integer
        0 if they are equal, -1 if the first comes before the second, -1 otherwise.
    """

    (xB, xE) = xIntv
    (yB, yE) = yIntv

    eqx = _locCmp(xB, yB)

    return _locCmp(yE, xE) if eqx == 0 else eqx


_locSort = functools.cmp_to_key(_locCmp)
"""Sort key for locations (individual sections).
"""

_intervalSort = functools.cmp_to_key(_intervalCmp)
"""Sort key for intervals of sections.
"""


def _sortLocs(locs):
    """Sort function for locations (individual sections).

    Parameters
    ----------
    locs: iterable of tuple of integer
        The sequence of locations

    Returns
    -------
    tuple
        The sorted locations.
    """
    return tuple(sorted(locs, key=_locSort))


def _sortIntervals(scopes):
    """Sort function for intervals of sections.

    Parameters
    ----------
    intvs: iterable of tuple of tuple of integer
        The sequence of intervals

    Returns
    -------
    tuple
        The sorted intervals.
    """
    return tuple(sorted(scopes, key=_intervalSort))


def _locInInterval(loc, intv):
    """Whether a location (section) is contained in an interval.

    Parameters
    ----------
    loc: tuple of integer
        The location, which is a section given by its sequence numbers
    intv: tuple of tuple of integer
        The interval, given by its start and and location

    Returns
    -------
    boolean
        Whether the location is contained in the interval
    """
    (b, e) = intv
    return _locCmp(b, loc) <= 0 and _locCmp(loc, e) <= 0


def locInScope(loc, scope):
    """Whether a location (section) is contained in a scope (sequence of intervals).

    Parameters
    ----------
    loc: tuple of integer
        The location, which is a section given by its sequence numbers
    scope: tuple of tuple of tuple of integer
        The scope, given as a tuple of intervals

    Returns
    -------
    boolean
        Whether the location is contained in the scope
    """
    if not len(scope):
        return False

    return any(_locInInterval(loc, intv) for intv in scope)


def partitionScopes(scopeDict):
    """Partition a set of scopes into intervals.

    The idea is to create a set of intervals such that:

    *   there is no scope boundary within any interval;
    *   every interval has at least one scope boundary at its start and one at its end.

    Parameters
    ----------
    scopeDict: dict
        The scopes are given as a mapping from string representations of scopes to
        logical scopes, i.e. the data structures you get when you parse scopes.

    Returns
    -------
    list
        The sorted sequence of resulting intervals
    """
    scopeFromStr = {}
    strFromScope = {}
    boundaries = {}
    intervals = []

    for scopeStr, scope in scopeDict.items():
        for intv in scope:
            (b, e) = intv
            boundaries.setdefault(b, {}).setdefault("b", set()).add(intv)
            boundaries.setdefault(e, {}).setdefault("e", set()).add(intv)

            scopeFromStr.setdefault(scopeStr, set()).add(intv)
            strFromScope.setdefault(intv, set()).add(scopeStr)

    curScopes = set()
    inScope = False

    for x in _sortLocs(boundaries):
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
            intervals.append([x, x, _sortIntervals(curScopes)])
            curScopes -= endScopes
            inScope = len(curScopes) > 0
            if inScope:
                intervals.append([_nextLoc(x), None, _sortIntervals(curScopes)])
        elif hasB:
            if inScope:
                intervals[-1][1] = _prevLoc(x)
                if intervals[-1][1] < intervals[-1][0]:
                    intervals.pop()
            curScopes |= beginScopes
            intervals.append([x, None, _sortIntervals(curScopes)])
        elif hasE:
            intervals[-1][1] = x
            curScopes -= endScopes
            inScope = len(curScopes) > 0
            if inScope:
                intervals.append([_nextLoc(x), None, _sortIntervals(curScopes)])

    if inScope:
        intervals[-1][1] = x

    for x in intervals:
        newX = []
        seen = set()

        for intv in x[2]:
            for scopeStr in strFromScope[intv]:
                if scopeStr in seen:
                    continue

                seen.add(scopeStr)
                newX.append(scopeStr)

        x[2] = tuple(newX)

    return intervals


def getIntvIndex(buckets, instructions, getSeqFromNode):
    """Map buckets in the corpus on intervals in a given set of intervals.

    When we are going to look up triggers in the corpus, we do so bucket by bucket.
    The validity of triggers is constrained to their scope. Whenever we leave an
    interval and go to the next, the those scopes change.
    We need a quick way to determine for each bucket in the corpus to which
    interval it belongs.

    Parameters
    ----------
    buckets: iterable of integer
        The nodes corresponding to the lowest level sections in the corpus
    instructions: iterable of tuple of tuple of integer
        This is a sequence of intervals. You may pass the `instructions` member
        of sheet data, since that is a mapping from intervals to search
        instructions for those intervals.
        When treated as an iterbale, such a dict is a sequence of intervals.

        We will sort the intervals before computing the index.
    getSeqFromNode:
        Corpus dependent function that gives the "legal" sequence number for
        sections, passed as nodes. See `tf.ner.corpus.Corpus.getSeqFromNode()`

    Returns
    -------
    dict
        Maps bucket nodes to the interval in the sequence of intervals to which they
        belong.
    """
    intervals = _sortIntervals(x for x in instructions if x != ())

    nIntervals = len(intervals)

    if nIntervals == 0:
        return {bucket: () for bucket in buckets}

    intvIndex = {}
    i = 0
    intv = intervals[i]
    (b, e) = intv

    for bucket in buckets:
        hd = getSeqFromNode(bucket)

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


class Scopes:
    """Functions that do scope handling.

    These functions will be added as methods to the class that inherits this class.
    """

    def repLoc(self, loc):
        """Represent a location as a string.

        A location identifies a section by means of legal number.
        We now want the heading of that section, as given by the features and
        settings of the corpus. We use the corpus dependent function
        `tf.ner.corpus.Corpus.getStrFromSeq()` for that.

        Parameters
        ----------
        loc: tuple of integer
            The "legal" number of a section.

        Returns
        -------
        string
            The section heading of the corresponding section.
        """
        getStrFromSeq = self.getStrFromSeq

        return getStrFromSeq(tuple(x for x in loc if x != 0 and x != -1))

    def parseLoc(self, locStr, plain=True):
        """Parses a location string.

        A location string is a section heading in the corpus.
        Now we want the "legal" number of that section.
        We use the corpus dependent function
        `tf.ner.corpus.Corpus.getSeqFromStr()` for that.

        Parameters
        ----------
        locStr: string
            The section heading as it appears in the corpus
        plain: boolean, optional True
            Whether to return just the result or additional information as well.

        Returns
        -------
        tuple of integer or dict
            The plain result is a tuple of the numbers that make up the "legal"
            number of the section. This is returned when `plain=False` is passed.
            If there are errors, None is returned.

            But if `plain=True` is passed, a dict is returned, with keys **result**
            for the plain result; **warning** for warnings if the parsing failed; and
            **normal** for a normalized representaiton of the section.
        """
        getSeqFromStr = self.getSeqFromStr

        locStr = locStr.strip()

        if not locStr:
            result = ()
            return (
                ()
                if plain
                else dict(result=(), warning=None, normal=self.repLoc(result))
            )

        (error, result) = getSeqFromStr(locStr)

        if error:
            result = None
            normal = None
            warning = error
        else:
            normal = self.repLoc(result)
            warning = None

        return result if plain else dict(result=result, warning=warning, normal=normal)

    def repInterval(self, intv):
        """Represent an interval of sections as string.

        Parameters
        ----------
        intv: tuple of tuple of integer
            The interval given as start and end section tuples

        Returns
        -------
        string
            Either a single section heading, if the start and end section are the same,
            or `-` surrounded by the start and end section headings.
        """
        if intv is None or len(intv) == 0:
            return "()"

        (b, e) = intv

        return (
            self.repLoc(b) if _sameLoc(b, e) else f"{self.repLoc(b)}-{self.repLoc(e)}"
        )

    def repScope(self, scope):
        """Represent a scope as string.

        Parameters
        ----------
        scope: tuple of tuple of tuple of integer
            The scope given as sequence of intervals

        Returns
        -------
        string
            Either a single section heading, if the start and end section are the same,
            or `-` surrounded by the start and end section headings.
        """
        return ", ".join(self.repInterval(intv) for intv in scope)

    def parseInterval(self, intvStr, plain=True):
        """Parses an interval given as string.

        A interval string is two section headings separated by a `-`.
        We parse it into a 2-tuple of the section headings, both also parsed into
        tuples of integers.

        If the resulting section tuples have less than the maximum number of components,
        we fill them up: the start section will be filled up with `0`-s, and the
        end section will be filled up with `-1`-s. This corresponds to the
        interpretation that the start section represent its start point, and
        the end section represent its end point.

        Parameters
        ----------
        intvStr: string
            The interval string
        plain: boolean, optional True
            Whether to return just the result or additional information as well.

        Returns
        -------
        tuple of integer or dict
            The plain result is a 2-tuple of tuples of integer.
            This is returned when `plain=False` is passed.
            If there are errors, None is returned.

            But if `plain=True` is passed, a dict is returned, with keys **result**
            for the plain result; **warning** for warnings if the parsing failed; and
            **normal** for a normalized representaiton of the section.
        """
        result = None
        warnings = []

        intvStr = intvStr.strip()

        if not intvStr:
            result = ((0, 0, 0), (-1, -1, -1))

            return (
                result
                if plain
                else dict(
                    result=result, warning=warnings, normal=self.repInterval(result)
                )
            )

        parts = intvStr.split("-", 1)

        if len(parts) == 1:
            info = self.parseLoc(intvStr, plain=False)
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
            info1 = self.parseLoc(part, plain=False)
            w1 = info1["warning"]

            part = parts[1].strip()
            info2 = self.parseLoc(part, plain=False)
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

        normal = None if result is None else self.repInterval(result)

        return result if plain else dict(result=result, warning=warnings, normal=normal)

    def parseScope(self, scopeStr, plain=True):
        """Parse a scope specification into logical specifiers of regions in the corpus.

        A scope specification is a comma-separated list of interval strings.

        An interval string is either a section or an interval between two sections.

        A section is written as a section heading, an interval as two section headings
        with a `-` in between.

        An interval is taken from the start of the first section to the end of the
        second section.

        A section on its own is taken from its start to its end.

        Parameters
        ----------
        scopeStr: string
            The scope string
        plain: boolean, optional True
            Whether to return just the result or additional information as well.

        Returns
        -------
        tuple of tuple of integer or dict
            The plain result is a tuple of 2-tuple of tuples of integer.
            This is returned when `plain=False` is passed.
            If there are errors, None is returned.

            But if `plain=True` is passed, a dict is returned, with keys **result**
            for the plain result; **warning** for warnings if the parsing failed; and
            **normal** for a normalized representaiton of the section.
        """

        results = []
        warnings = []

        if not scopeStr:
            return () if plain else dict(result=(), warning=warnings, normal="")

        for intvStr in scopeStr.split(","):

            if not intvStr:
                continue

            info = self.parseInterval(intvStr, plain=plain)
            result = info if plain else info["result"]

            if result is None:
                if not plain:
                    warnings.extend(info["warning"])
                continue

            results.append(result)

        results = tuple(_sortIntervals(results))

        return (
            results
            if plain
            else dict(result=results, warning=warnings, normal=self.repScope(results))
        )

    def intersectScopes(self, *scopeStrs):
        """Produce the intersection of severel scopes.

        We use this function to test whether two triggers have a region where they
        are both in scope.

        Parameters
        ----------
        scopeStrs: iterable
            Sequence of scope specifiers

        Returns
        -------
        tuple of tuple of tuple of integer
            This is a tuple of intervals, forming the intersection of all given scopes
        """
        curIntersection = [self.parseInterval("")]

        for scopeStr in scopeStrs:
            newIntersection = []
            for bLoc, eLoc in self.parseScope(scopeStr):

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

    def testPartitioning(self, scopeStrs):
        """Test the partitioning of scopes.

        Only for debugging purposes.

        Parameters
        ----------
        scopeStrs: iterable of string
            The scope specifiers

        Returns
        -------
        list
            A list of intervals that make up the resulting partition.
        """
        scopeIndex = {}

        for scopeStr in scopeStrs:
            info = self.parseScope(scopeStr, plain=False)
            warning = info["warning"]

            if len(warning):
                console(f"Errors in {scopeStr}: {'; '.join(warning)}")
            else:
                scopes = info["result"]
                normScopeStr = info["normal"]
                console(
                    f"{scopeStr} => {normScopeStr}\n"
                    f"\t{self.repScope(_sortIntervals(scopes))}"
                )
                scopeIndex[normScopeStr] = scopes

        partitionScopes(scopeIndex)
