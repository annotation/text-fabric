from itertools import chain

from ...advanced.helpers import dh

from .helpers import repIdent, repSummary
from .html import H

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
        """HTML for the feature values of entities.

        Parameters
        ----------
        setData: dict
            The entity data for the chosen set.

        Returns
        -------
        HTML string
        """
        settings = self.settings
        summaryFeatures = settings.summaryFeatures

        browse = self.browse
        setData = self.getSetData()

        content = H.p(
            H.span(
                H.code(f"{len(es):>5}"),
                " x ",
                H.span(repSummary(summaryFeatures, fVals)),
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
        settings = self.settings
        features = settings.features

        browse = self.browse
        setData = self.getSetData()

        hasEnt = activeEntity is not None

        entries = setData.entityIdent.items()
        # eFirst = setData.entityIdentFirst
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
            # e1 = eFirst[vals]
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
    ):
        settings = self.settings
        bucketType = settings.bucketType
        features = settings.features

        browse = self.browse
        app = self.app
        setData = self.getSetData()
        annoSet = self.annoSet
        api = app.api
        F = api.F

        entityIdent = setData.entityIdent
        # eFirst = setData.entityIdentFirst
        entitySlotIndex = setData.entitySlotIndex

        hasEnt = activeEntity is not None

        limited = mayLimit and not hasEnt and (start is None or end is None)
        limit = LIMIT_BROWSER if browse else LIMIT_NB

        content = []

        nB = 0

        for b, bTokens, matches, positions in buckets:
            nB += 1

            if start is not None and nB < start:
                continue
            if end is not None and nB > end:
                break
            if limited and nB > limit:
                content.append(
                    H.div(
                        f"Showing only the first {limit} {bucketType}s of all "
                        f"{len(buckets)} ones.",
                        cls="report",
                    )
                )
                break

            charPos = 0

            if annoSet:
                allMatches = set()
                endMatches = set()
                for match in matches:
                    allMatches |= set(match)
                    endMatches.add(match[-1])

            else:
                allMatches = set(chain.from_iterable(matches))

            subContent = [
                H.span(
                    app.sectionStrFromNode(b), node=b, cls="bh", title="show context"
                )
            ]

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
                            active = " queried " if hasEnt and ident == activeEntity else ""
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

                after = F.after.v(t) or ""
                lenW = len(w)
                lenWa = len(w) + len(after)
                found = any(charPos + i in positions for i in range(lenW))
                queried = t in allMatches

                hlClasses = (" found " if found else "") + (
                    " queried " if queried else ""
                )
                hlClasses += " ei " if inEntity else ""
                hlClass = dict(cls=hlClasses) if hlClasses else {}

                endQueried = annoSet and t in endMatches
                excl = "x" if t in excludedTokens else "v"

                subContent.append(
                    H.join(
                        H.span(w, **hlClass, t=t),
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

            content.append(H.div(subContent, cls="b"))

        if browse:
            return H.join(content)

        dh(H.div(content, cls="buckets"))
