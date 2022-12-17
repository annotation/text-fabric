"""
# Search execution management
"""

from .relations import basicRelations
from .syntax import syntax
from .semantics import semantics
from .graph import connectedness, displayPlan
from .spin import spinAtoms, spinEdges
from .stitch import setStrategy, stitch
from ..parameters import SEARCH_FAIL_FACTOR, YARN_RATIO, TRY_LIMIT_FROM, TRY_LIMIT_TO
from ..core.timestamp import DEEP


PROGRESS = 100


class SearchExe:
    perfDefaults = dict(
        yarnRatio=YARN_RATIO,
        tryLimitFrom=TRY_LIMIT_FROM,
        tryLimitTo=TRY_LIMIT_TO,
    )
    perfParams = dict(**perfDefaults)

    @classmethod
    def setPerfParams(cls, params):
        cls.perfParams = params

    def __init__(
        self,
        api,
        searchTemplate,
        outerTemplate=None,
        quKind=None,
        offset=0,
        level=0,
        sets=None,
        shallow=False,
        silent=DEEP,
        showQuantifiers=False,
        _msgCache=False,
        setInfo={},
    ):
        self.api = api
        TF = api.TF
        setSilent = TF.setSilent

        self.searchTemplate = searchTemplate
        self.outerTemplate = outerTemplate
        self.quKind = quKind
        self.level = level
        self.offset = offset
        self.sets = sets
        self.shallow = 0 if not shallow else 1 if shallow is True else shallow
        self.silent = silent
        setSilent(silent)
        self.showQuantifiers = showQuantifiers
        self._msgCache = (
            _msgCache if type(_msgCache) is list else -1 if _msgCache else 0
        )
        self.good = True
        self.setInfo = setInfo
        basicRelations(self, api)

    # API METHODS ###

    def search(self, limit=None):
        api = self.api
        TF = api.TF
        setSilent = TF.setSilent
        setSilent(True)
        self.study()
        setSilent(self.silent)
        return self.fetch(limit=limit)

    def study(self, strategy=None):
        api = self.api
        TF = api.TF
        info = TF.info
        indent = TF.indent
        isSilent = TF.isSilent
        setSilent = TF.setSilent
        _msgCache = self._msgCache

        indent(level=0, reset=True)
        self.good = True

        wasSilent = isSilent()

        setStrategy(self, strategy)
        if not self.good:
            return

        info("Checking search template ...", cache=_msgCache)

        self._parse()
        self._prepare()
        if not self.good:
            return
        info(
            f"Setting up search space for {len(self.qnodes)} objects ...",
            cache=_msgCache,
        )
        spinAtoms(self)
        # in spinAtoms an inner call to study may have happened due to quantifiers
        # That will restore the silent level to what we had outside
        # study(). So we have to make it deep again.
        setSilent(wasSilent)
        info(
            f"Constraining search space with {len(self.qedges)} relations ...",
            cache=_msgCache,
        )
        spinEdges(self)
        info(f"\t{len(self.thinned)} edges thinned", cache=_msgCache)
        info(
            f"Setting up retrieval plan with strategy {self.strategyName} ...",
            cache=_msgCache,
        )
        stitch(self)
        if self.good:
            yarnContent = sum(len(y) for y in self.yarns.values())
            info(f"Ready to deliver results from {yarnContent} nodes", cache=_msgCache)
            info("Iterate over S.fetch() to get the results", tm=False, cache=_msgCache)
            info("See S.showPlan() to interpret the results", tm=False, cache=_msgCache)

    def fetch(self, limit=None):
        api = self.api
        TF = api.TF
        F = api.F
        error = TF.error
        _msgCache = self._msgCache

        if limit and limit < 0:
            limit = 0

        if not self.good:
            queryResults = set() if self.shallow else []
        elif self.shallow:
            queryResults = self.results
        else:
            failLimit = limit if limit else SEARCH_FAIL_FACTOR * F.otype.maxNode

            def limitedResults():
                for (i, result) in enumerate(self.results()):
                    if i < failLimit:
                        yield result
                    else:
                        if not limit:
                            error(
                                f"cut off at {failLimit} results. There are more ...",
                                cache=_msgCache,
                            )
                        return

            queryResults = (
                limitedResults() if limit is None else tuple(limitedResults())
            )

        return queryResults

    def count(self, progress=None, limit=None):
        TF = self.api.TF
        info = TF.info
        error = TF.error
        _msgCache = self._msgCache
        indent = TF.indent
        indent(level=0, reset=True)

        if limit and limit < 0:
            limit = 0

        if not self.good:
            error(
                "This search has problems. No results to count.",
                tm=False,
                cache=_msgCache,
            )
            return

        if progress is None:
            progress = PROGRESS

        if limit:
            failLimit = limit
            msg = f" up to {failLimit}"
        else:
            failLimit = SEARCH_FAIL_FACTOR * self.api.F.otype.maxNode
            msg = ""

        info(
            f"Counting results per {progress}{msg} ...",
            cache=_msgCache,
        )
        indent(level=1, reset=True)

        j = 0
        good = True
        for (i, r) in enumerate(self.results(remap=False)):
            if i >= failLimit:
                if not limit:
                    good = False
                break
            j += 1
            if j == progress:
                j = 0
                info(i + 1, cache=_msgCache)

        indent(level=0)
        if good:
            info(f"Done: {i + 1} results", cache=_msgCache)
        else:
            error(
                f"cut off at {failLimit} results. There are more ...", cache=_msgCache
            )

    # SHOWING WITH THE SEARCH GRAPH ###

    def showPlan(self, details=False):
        displayPlan(self, details=details)

    def showOuterTemplate(self, _msgCache):
        error = self.api.TF.error
        offset = self.offset
        outerTemplate = self.outerTemplate
        quKind = self.quKind
        if offset and outerTemplate is not None:
            for (i, line) in enumerate(outerTemplate.split("\n")):
                error(f"{i:>2} {line}", tm=False, cache=_msgCache)
            error(f"line {offset:>2}: Error under {quKind}:", tm=False, cache=_msgCache)

    # TOP-LEVEL IMPLEMENTATION METHODS

    def _parse(self):
        syntax(self)
        semantics(self)

    def _prepare(self):
        if not self.good:
            return
        self.yarns = {}
        self.spreads = {}
        self.spreadsC = {}
        self.uptodate = {}
        self.results = None
        connectedness(self)
