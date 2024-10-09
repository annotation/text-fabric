import functools

from ..core.helpers import console


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


def _sortLocs(locs):
    return tuple(sorted(locs, key=_locSort))


def _sortScopes(scopes):
    return tuple(sorted(scopes, key=_scopeSort))


def _locInScope(loc, scope):
    (b, e) = scope
    return _locCmp(b, loc) <= 0 and _locCmp(loc, e) <= 0


def locInScopes(loc, scopes):
    if not len(scopes):
        return False

    return any(_locInScope(loc, scope) for scope in scopes)


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
            intervals.append([x, x, _sortScopes(curScopes)])
            curScopes -= endScopes
            inScope = len(curScopes) > 0
            if inScope:
                intervals.append([_nextLoc(x), None, _sortScopes(curScopes)])
        elif hasB:
            if inScope:
                intervals[-1][1] = _prevLoc(x)
                if intervals[-1][1] < intervals[-1][0]:
                    intervals.pop()
            curScopes |= beginScopes
            intervals.append([x, None, _sortScopes(curScopes)])
        elif hasE:
            intervals[-1][1] = x
            curScopes -= endScopes
            inScope = len(curScopes) > 0
            if inScope:
                intervals.append([_nextLoc(x), None, _sortScopes(curScopes)])

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


def getIntvIndex(buckets, instructions, seqFromNode):
    intervals = _sortScopes(x for x in instructions if x != ())

    nIntervals = len(intervals)

    if nIntervals == 0:
        return {bucket: () for bucket in buckets}

    intvIndex = {}
    i = 0
    intv = intervals[i]
    (b, e) = intv

    for bucket in buckets:
        hd = seqFromNode(bucket)

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
    def repLoc(self, loc):
        strFromSeq = self.strFromSeq

        return strFromSeq(tuple(x for x in loc if x != 0 and x != -1))

    def parseLoc(self, locStr, plain=True):
        seqFromStr = self.seqFromStr

        locStr = locStr.strip()

        if not locStr:
            result = ()
            return (
                ()
                if plain
                else dict(result=(), warning=None, normal=self.repLoc(result))
            )

        (error, result) = seqFromStr(locStr)

        if error:
            result = None
            normal = None
            warning = error
        else:
            normal = self.repLoc(result)
            warning = None

        return result if plain else dict(result=result, warning=warning, normal=normal)

    def repScope(self, scope):
        if scope is None or len(scope) == 0:
            return "()"

        (b, e) = scope
        return (
            self.repLoc(b) if _sameLoc(b, e) else f"{self.repLoc(b)}-{self.repLoc(e)}"
        )

    def repScopes(self, scopes):
        return ", ".join(self.repScope(scope) for scope in scopes)

    def parseScope(self, scopeStr, plain=True):
        result = None
        warnings = []

        scopeStr = scopeStr.strip()

        if not scopeStr:
            result = ((0, 0, 0), (-1, -1, -1))
            return (
                result
                if plain
                else dict(result=result, warning=warnings, normal=self.repScope(result))
            )

        parts = scopeStr.split("-", 1)

        if len(parts) == 1:
            info = self.parseLoc(scopeStr, plain=False)
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

        normal = None if result is None else self.repScope(result)

        return result if plain else dict(result=result, warning=warnings, normal=normal)

    def parseScopes(self, scopeStr, plain=True):
        """Parse a scope specification into logical specifiers of regions in the corpus.

        A scope specification is a comma-separated list of scope strings.

        A scope string is either a section or an interval between two sections.

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

        results = []
        warnings = []

        if not scopeStr:
            return () if plain else dict(result=(), warning=warnings, normal="")

        for scopeStrPart in scopeStr.split(","):

            if not scopeStrPart:
                continue

            info = self.parseScope(scopeStrPart, plain=plain)
            result = info if plain else info["result"]

            if result is None:
                if not plain:
                    warnings.extend(info["warning"])
                continue

            results.append(result)

        results = tuple(_sortScopes(results))

        return (
            results
            if plain
            else dict(result=results, warning=warnings, normal=self.repScopes(results))
        )

    def intersectScopes(self, *scopeStrs):
        curIntersection = [self.parseScope("")]

        for scopeStr in scopeStrs:
            newIntersection = []
            for bLoc, eLoc in self.parseScopes(scopeStr):

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

    def testScopes(self, scopeStrs, seqFromStr):
        scopeIndex = {}

        for scopeStr in scopeStrs:
            info = self.parseScopes(scopeStr, plain=False)
            warning = info["warning"]

            if len(warning):
                console(f"Errors in {scopeStr}: {'; '.join(warning)}")
            else:
                scopes = info["result"]
                normScopeStr = info["normal"]
                console(
                    f"{scopeStr} => {normScopeStr}\n"
                    f"\t{self.repScopes(_sortScopes(scopes))}"
                )
                scopeIndex[normScopeStr] = scopes

        partitionScopes(scopeIndex)
