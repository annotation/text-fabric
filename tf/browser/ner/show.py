"""Rendering of corpus extracts with annotations.

To see how this fits among all the modules of this package, see
`tf.browser.ner.annotate` .
"""

from itertools import chain

from ...advanced.helpers import dh

from .helpers import repIdent, repSummary
from ..html import H

from .settings import (
    SORT_DEFAULT,
    SORTKEY_DEFAULT,
    SORTDIR_DEFAULT,
    SORTDIR_DESC,
    LIMIT_BROWSER,
    LIMIT_NB,
)


class Show:
    def showEntityOverview(self):
        """Generates HTML for an overview of the entities.

        The entity overview consists of a listing of the possible
        entity kinds with for each kind how many entities there are of that kind.

        Returns
        -------
        string or void
            If called by the browser, it returns the HTML string.
            Otherwise, it displays the HTML string in the output, assuming
            it is a cell in a Jupyter Notebook.
        """
        settings = self.settings
        keywordFeatures = settings.keywordFeatures

        browse = self.browse
        setData = self.getSetData()

        content = H.p(
            H.span(
                H.code(f"{len(es):>5}"),
                " x ",
                H.span(repSummary(keywordFeatures, fVals)),
            )
            + H.br()
            for (fVals, es) in sorted(
                setData.entitySummary.items(), key=lambda x: (-len(x[1]), x[0])
            )
        )

        if browse:
            return content

        dh(content)

    def showEntities(
        self, activeEntity=None, sortKey=None, sortDir=None, cutOffFreq=None
    ):
        """Generates HTML for a sorted list of the entities.

        The entity list consists of a table of entity identifiers, with the columns for
        the kind and frequency of the entities.

        There may be one active entity, and that one will be highlighted.

        Parameters
        ----------
        activeEntity: tuple, optional None
            The entity that must be highlighted.

        sortKey: string, optional None
            The key by which the entity list is sorted.

            Possible values:

            *   `freqsort`: by frequency
            *   `sort_0` or `sort_eid`: by entity identifier
            *   `sort_1` or `sort_kind`: by entity kind

            If `None` is passed, `freqsort` is filled in.

        sortDir: string, optional None
            The direction of the sort.

            Possible values:

            *   `a`: ascending
            *   `d`: descending

            If `None` is passed, `a` is filled in.
            However, if `None` is passed for both `sortKey` and `sortDir`,
            a `d` is filled in.

            As a consequence, the default sort order is by frequency, most
            frequent on top.

        cutOffFreq: integer, optional None
            If passed, it is a lower limit on the frequency of the entities that
            will be shown. Every entity with a lower frequency will be skipped.

        Returns
        -------
        string or void
            If called by the browser, it returns the HTML string.
            Otherwise, it displays the HTML string in the output, assuming
            it is a cell in a Jupyter Notebook.
        """
        settings = self.settings
        features = settings.features

        browse = self.browse
        setData = self.getSetData()

        hasEnt = activeEntity is not None

        entries = setData.entityIdent.items()
        sortKeyMap = {feat: i for (i, feat) in enumerate(features)}

        if sortKey is None and sortDir is None:
            (sortKey, sortDir) = SORT_DEFAULT
        else:
            if sortKey is None:
                sortKey = SORTKEY_DEFAULT
            if sortDir is None:
                sortDir = SORTDIR_DEFAULT

        if sortKey == SORTKEY_DEFAULT:
            entries = sorted(entries, key=lambda x: (len(x[1]), x[0]))
        else:
            if sortKey.startswith("sort_"):
                index = sortKey[5:]
                if index.isdecimal():
                    index = int(index)
                    if index >= len(features):
                        index = 0
                else:
                    index = sortKeyMap.get(index, 0)
            else:
                index = 0

            entries = sorted(entries, key=lambda x: (x[0][index], -len(x[1])))

        if sortDir == SORTDIR_DESC:
            entries = reversed(entries)

        content = []

        for vals, es in entries:
            x = len(es)

            if cutOffFreq is not None and x < cutOffFreq:
                continue
            identRep = "⊙".join(vals)

            active = " queried " if hasEnt and vals == activeEntity else ""

            content.append(
                H.p(
                    H.code(f"{x:>5}", cls="w"),
                    " x ",
                    repIdent(features, vals, active=active),
                    cls=f"e {active}",
                    enm=identRep,
                )
            )

        content = H.join(content)

        if browse:
            return content

        dh(content)

    def showContent(
        self,
        buckets,
        activeEntity=None,
        excludedTokens=set(),
        mayLimit=True,
        start=None,
        end=None,
        withNodes=False,
    ):
        """Generates HTML for a given portion of the corpus.

        The corpus text will be marked up with entities, the positions of
        these entities are present in the input parameter `buckets`.

        It is recommended to apply this function to the outcome of
        `tf.browser.ner.annotate.Annotate.filterContent`

        !!! caution "Truncated"
            Unless the user has selected an entity or forced a start and end
            boundary to the list of buckets, the display may be truncated.
            See the parameter `mayLimit` below.

        Parameters
        ----------
        buckets: iterable of tuple
            A selection of buckets (chunks / paragraphs) of the corpus.
            Each bucket is given as a tuple.
            The exact form is this data structure is equal to what the
            function `tf.browser.ner.annotate.Annotate.filterContent`
            returns.

        activeEntity: tuple, optional None
            The entity that must be highlighted.

        excludedTokens: set, optional None
            If passed, it is a set of tokens where a ❌ has been placed by the
            user. They correspond to occurrences that have been deselected from
            being subject to add / delete operations.

        mayLimit: boolean, optional False
            It is possible that the buckets make up the whole corpus.
            Although we have optimised things in such a way that the browser can handle
            a webpage with thousands of pages of material in it, such large pages
            may compromise the performance.
            If the bucket set is potentially very large, and the `start` and `end`
            parameters are not both specified, we will truncate the list of buckets
            to a smallish value (see `settings.LIMIT_BROWSER` and `settings.LIMIT_NB`).

            However, when there is an `activeEntity`, we assume the buckets are those
            containing that entity, and that it is a limited set anyway, and in that
            case we do not truncate.

        start: integer, optional None
            If passed, start rendering the buckets at this position.

        end: integer, optional None
            If passed, stop rendering the buckets at this position.

        withNodes: boolean, optional None
            Shows the node in each token.

        Returns
        -------
        string or void
            If called by the browser, it returns the HTML string.
            Otherwise, it displays the HTML string in the output, assuming
            it is a cell in a Jupyter Notebook.
        """

        settings = self.settings
        bucketType = settings.bucketType
        features = settings.features
        style = self.style
        ltr = self.ltr

        browse = self.browse
        setData = self.getSetData()
        annoSet = self.annoSet
        afterv = self.getAfter()
        sectionHead = self.sectionHead

        entityIdent = setData.entityIdent
        entitySlotIndex = setData.entitySlotIndex

        hasEnt = activeEntity is not None

        limited = mayLimit and not hasEnt and (start is None or end is None)
        limit = LIMIT_BROWSER if browse else LIMIT_NB

        content = []

        nB = 0
        nBshown = 0

        for b, bTokens, matches, positions in buckets:
            nB += 1

            if start is not None and nB < start:
                continue
            if end is not None and nB > end:
                break

            if limited and nBshown > limit:
                content.append(
                    H.div(
                        f"Showing only the first {limit} {bucketType}s of all "
                        f"{len(buckets)} ones.",
                        cls="report",
                    )
                )
                break

            nBshown += 1
            charPos = 0

            if annoSet:
                allMatches = set()
                endMatches = set()
                for match in matches:
                    allMatches |= set(match)
                    endMatches.add(match[-1])

            else:
                allMatches = set(chain.from_iterable(matches))

            headContent = H.span(
                H.span(sectionHead(b), cls="bhl ltr", title="show context"),
                cls=f"bh {ltr}",
                node=b,
            )
            subContent = []

            for t, w in bTokens:
                info = entitySlotIndex.get(t, None)
                inEntity = False

                if info is not None:
                    inEntity = True
                    for item in sorted(
                        (x for x in info if x is not None), key=lambda z: z[1]
                    ):
                        (status, lg, ident) = item
                        # e = eFirst[ident]
                        identRep = "⊙".join(ident)

                        if status:
                            active = (
                                " queried " if hasEnt and ident == activeEntity else ""
                            )
                            subContent.append(
                                H.span(
                                    H.span(abs(lg), cls="lgb"),
                                    repIdent(features, ident, active=active),
                                    " ",
                                    H.span(len(entityIdent[ident]), cls="n"),
                                    cls="es",
                                    enm=identRep,
                                )
                            )

                after = afterv(t) or ""
                lenW = len(w)
                lenWa = len(w) + len(after)
                # found = any(charPos + i in positions for i in range(lenW))
                foundSet = set(range(charPos, charPos + lenW)) & positions
                found = len(foundSet) != 0

                if found:
                    firstFound = min(foundSet) - charPos
                    lastFound = max(foundSet) - charPos
                    leading = "" if firstFound == charPos else w[0:firstFound]
                    trailing = "" if lastFound == lenW - 1 else w[lastFound + 1:]
                    hit = w[firstFound : lastFound + 1]
                    wRep = H.join(leading, H.span(hit, cls="found"), trailing)
                else:
                    wRep = w
                queried = t in allMatches

                hlClasses = " queried " if queried else ""
                hlClasses += " ei " if inEntity else ""
                hlClasses += f" {style} " if style else ""
                hlClass = dict(cls=hlClasses) if hlClasses else {}

                endQueried = annoSet and t in endMatches
                excl = "x" if t in excludedTokens else "v"
                nodeRep = H.span(str(t), cls="nd") if withNodes else ""

                subContent.append(
                    H.join(
                        H.span(wRep + nodeRep, **hlClass, t=t),
                        H.span(te=t, st=excl) if endQueried else "",
                        after,
                    )
                )

                if info is not None:
                    for item in sorted(
                        (x for x in info if x is not None), key=lambda z: z[1]
                    ):
                        (status, lg, ident) = item
                        if not status:
                            subContent.append(
                                H.span(H.span(abs(lg), cls="lge"), cls="ee")
                            )

                charPos += lenWa

            content.append(
                H.div(headContent, H.nb, H.span(subContent, cls=ltr), cls=f"b {ltr}")
            )

        if browse:
            return H.div(content, id="buckets", cls=f"buckets {ltr}")

        dh(H.div(content, cls=f"buckets {ltr}"))
