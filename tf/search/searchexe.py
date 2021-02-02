"""
# Search execution management
"""

from .relations import basicRelations
from .syntax import syntax
from .semantics import semantics
from .graph import connectedness, displayPlan
from .spin import spinAtoms, spinEdges
from .stitch import setStrategy, stitch


PROGRESS = 100
LIMIT = 1000


class SearchExe(object):
    perfParams = {}

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
        silent=True,
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
        self._msgCache = _msgCache if type(_msgCache) is list else -1 if _msgCache else 0
        self.good = True
        self.setInfo = setInfo
        basicRelations(self, api)

    # API METHODS ###

    def search(self, limit=None):
        api = self.api
        TF = api.TF
        isSilent = TF.isSilent
        setSilent = TF.setSilent
        wasSilent = isSilent()
        setSilent(True)
        self.study()
        setSilent(wasSilent)
        return self.fetch(limit=limit)

    def study(self, strategy=None):
        api = self.api
        TF = api.TF
        info = TF.info
        indent = TF.indent
        _msgCache = self._msgCache

        indent(level=0, reset=True)
        self.good = True

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
        if not self.good:
            queryResults = set() if self.shallow else []
        elif self.shallow:
            queryResults = self.results
        else:
            if limit is None:
                queryResults = self.results()
            else:
                queryResults = []
                for r in self.results():
                    queryResults.append(r)
                    if len(queryResults) == limit:
                        break
                queryResults = tuple(queryResults)
        return queryResults

    def count(self, progress=None, limit=None):
        TF = self.api.TF
        info = TF.info
        error = TF.error
        _msgCache = self._msgCache
        indent = TF.indent
        indent(level=0, reset=True)

        if not self.good:
            error(
                "This search has problems. No results to count.",
                tm=False,
                cache=_msgCache,
            )
            return

        if progress is None:
            progress = PROGRESS
        if limit is None:
            limit = LIMIT

        info(
            "Counting results per {} up to {} ...".format(
                progress, limit if limit > 0 else " the end of the results",
            ),
            cache=_msgCache,
        )
        indent(level=1, reset=True)

        i = 0
        j = 0
        for r in self.results(remap=False):
            i += 1
            j += 1
            if j == progress:
                j = 0
                info(i, cache=_msgCache)
            if limit > 0 and i >= limit:
                break

        indent(level=0)
        info(f"Done: {i} results")

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
