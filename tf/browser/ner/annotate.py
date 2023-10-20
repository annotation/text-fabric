"""API for rule-based annotation

This module contains the top-level methods for applying annotation rules to a corpus.

As a preparation, read `tf.about.annotate` first, since it explains the concepts, and
guides you to set up the configuration for your corpus.
"""

import collections


from ...core.helpers import console as cs

from .settings import TOOLKEY

from .helpers import findCompile, makeCss
from .sets import Sets
from .show import Show
from .match import entityMatch, occMatch


class Annotate(Sets, Show):
    def __init__(self, app, data=None, debug=False, browse=False):
        self.app = app
        super().__init__()

        self.F = app.api.F
        self.debug = debug
        self.browse = browse

        settings = self.settings
        features = settings.features
        keywordFeatures = settings.keywordFeatures

        app.loadToolCss(TOOLKEY, makeCss(features, keywordFeatures))

        if not browse:
            self.loadData()

    def console(self, msg, **kwargs):
        if self.debug or not self.browse:
            cs(msg, **kwargs)

    def findOccs(self, qTokenSet=None):
        app = self.app
        setData = self.getSetData()
        api = app.api
        L = api.L
        F = api.F

        buckets = setData.buckets or ()

        results = {}

        for b in buckets:
            occMatch(L, F, b, qTokenSet, results)

        return results

    def filterContent(
        self,
        node=None,
        bFind=None,
        bFindC=None,
        bFindRe=None,
        anyEnt=None,
        eVals=None,
        qTokens=None,
        valSelect=None,
        freeState=None,
        noFind=False,
        showStats=None,
    ):
        """Filter the buckets.

        Will filter the buckets by tokens if the `tokenStart` and `tokenEnd` parameters
        are both filled in.
        In that case, we look up the text between those tokens and including.
        All buckets that contain that text of those slots will show up,
        all other buckets will be left out.
        However, if `valSelect` is non-empty, then there is a further filter:
        only if the
        text corresponds to an entity with those feature values, the bucket is
        passed through.
        The matching slots will be highlighted.

        Parameters
        ----------
        bFindPattern: string
            A search string that filters the buckets, before applying the search
            for a token sequence.

        valSelect: set
            The feature values to filter on.

        Returns
        -------
        list of tuples
            For each bucket that passes the filter, a tuple with the following
            members is added to the list:

            *   tokens: the tokens of the bucket
            *   matches: the match positions of the found text
            *   positions: the token positions where a targeted token sequence starts
        """
        settings = self.settings
        bucketType = settings.bucketType
        features = settings.features

        browse = self.browse
        app = self.app
        setData = self.getSetData()
        entityIndex = setData.entityIndex
        entityVal = setData.entityVal
        entitySlotVal = setData.entitySlotVal
        entitySlotAll = setData.entitySlotAll
        entitySlotIndex = setData.entitySlotIndex

        api = app.api
        L = api.L
        F = api.F
        T = api.T

        buckets = (
            setData.buckets or ()
            if node is None
            else L.d(T.sectionTuple(node)[1], otype=bucketType)
        )

        nFind = 0
        nEnt = {feat: collections.Counter() for feat in ("",) + features}
        nVisible = {feat: collections.Counter() for feat in ("",) + features}

        if bFindRe is None:
            if bFind is not None:
                (bFind, bFindRe, errorMsg) = findCompile(bFind, bFindC)
                if errorMsg:
                    app.error(errorMsg)

        hasEnt = eVals is not None
        hasQTokens = qTokens is not None and len(qTokens)
        hasOcc = not hasEnt and hasQTokens

        if eVals is not None:
            eSlots = entityVal[eVals]
            eStarts = {s[0]: s[-1] for s in eSlots}
        else:
            eStarts = None

        useQTokens = qTokens if hasOcc else None

        requireFree = (
            True if freeState == "free" else False if freeState == "bound" else None
        )

        results = []

        self.console(f"{eVals=} {anyEnt=} {valSelect=}")

        for b in buckets:
            fValStats = {feat: collections.Counter() for feat in features}
            (fits, result) = entityMatch(
                entityIndex,
                eStarts,
                entitySlotVal,
                entitySlotAll,
                entitySlotIndex,
                L,
                F,
                T,
                b,
                bFindRe,
                anyEnt,
                eVals,
                useQTokens,
                valSelect,
                requireFree,
                fValStats,
            )

            blocked = fits is not None and not fits

            if not blocked:
                nFind += 1

            for feat in features:
                theseStats = fValStats[feat]
                if len(theseStats):
                    theseNEnt = nEnt[feat]
                    theseNVisible = nVisible[feat]

                    for ek, n in theseStats.items():
                        theseNEnt[ek] += n
                        if not blocked:
                            theseNVisible[ek] += n

            nMatches = len(result[1])

            if nMatches:
                nEnt[""][None] += nMatches
                if not blocked:
                    nVisible[""][None] += nMatches

            if fits is not None and not fits:
                continue

            if ((hasEnt or hasQTokens) and nMatches == 0):
                continue

            results.append((b, *result))

        if browse:
            return (results, nFind, nVisible, nEnt)

        nResults = len(results)

        if showStats:
            pluralF = "" if nFind == 1 else "s"
            self.console(f"{nFind} {bucketType}{pluralF} satisfy the filter")
            for feat in ("",) + (() if anyEnt else features):
                if feat == "":
                    self.console("Combined features match:")
                    for ek, n in sorted(nEnt[feat].items()):
                        v = nVisible[feat][ek]
                        self.console(f"\t{v:>5} of {n:>5} x")
                else:
                    self.console(f"Feature {feat}: found the following values:")
                    for ek, n in sorted(nEnt[feat].items()):
                        v = nVisible[feat][ek]
                        self.console(f"\t{v:>5} of {n:>5} x {ek}")
        if showStats or showStats is None:
            pluralR = "" if nResults == 1 else "s"
            self.console(f"{nResults} {bucketType}{pluralR}")
        return results

    def getStrings(self, tokenStart, tokenEnd):
        app = self.app
        api = app.api
        F = api.F

        return tuple(
            token
            for t in range(tokenStart, tokenEnd + 1)
            if (token := (F.str.v(t) or "").strip())
        )
