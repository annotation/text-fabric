import json
import re

from tf.core.helpers import console
from tf.core.files import initTree, dirContents, expanduser as ex
from tf.core.timestamp import DEEP
from tf.parameters import OTYPE, OSLOTS
from tf.app import use


TT_NAME = "watm"

NS_TF = "tf"
NS_PAGEXML = "pagexml"
NS_TEI = "tei"
NS_NLP = "nlp"
NS_TT = "tt"
NS_NONE = "tf"

NS_FROM_OTYPE = dict(
    doc=NS_TF,
    page=NS_TF,
    file=NS_TF,
    folder=NS_TF,
    letter=NS_TF,
    chapter=NS_TF,
    chunk=NS_TF,
    word=NS_TF,
    char=NS_TF,
    token=NS_NLP,
    sentence=NS_NLP,
)
NS_FROM_FEAT = dict(
    otype=NS_TF,
    doc=NS_TF,
    page=NS_TF,
    line=NS_TF,
    after=NS_TF,
    rafter=NS_TF,
    str=NS_TF,
    rstr=NS_TF,
)

KIND_NODE = "node"
KIND_EDGE = "edge"
KIND_ELEM = "element"
KIND_PI = "pi"
KIND_ATTR = "attribute"
KIND_FMT = "format"
KIND_ANNO = "anno"

REL_RE = re.compile(r"""/tf\b""")


class WATM:
    def __init__(self, app, nsOrig, skipMeta=False, extra={}):
        self.app = app
        self.nsOrig = nsOrig
        self.extra = extra
        api = app.api
        F = api.F
        warning = app.warning

        self.L = api.L
        self.E = api.E
        self.Es = api.Es
        self.F = F
        self.Fs = api.Fs
        self.slotType = self.F.otype.slotType
        self.otypes = self.F.otype.all
        self.info = app.info
        self.warning = warning
        self.repoLocation = app.repoLocation

        Fall = api.Fall
        Eall = api.Eall
        excludedFeatures = {OTYPE, OSLOTS, "after", "str"}
        self.nodeFeatures = [f for f in Fall() if f not in excludedFeatures]
        self.edgeFeatures = [f for f in Eall() if f not in excludedFeatures]

        FAllSet = set(Fall())
        F = api.F

        self.emptyv = F.empty.v if "empty" in FAllSet else None
        self.strv = F.str.v if "str" in FAllSet else None
        self.rstrv = F.rstr.v if "rstr" in FAllSet else None
        self.afterv = F.after.v if "after" in FAllSet else None
        self.rafterv = F.rafter.v if "rafter" in FAllSet else None
        is_metav = F.is_meta.v if "is_meta" in FAllSet else None
        self.is_metav = is_metav

        if skipMeta and not is_metav:
            warning(
                "skipMeta=True has no effect because feature is_meta is not defined."
            )
            skipMeta = False

        self.skipMeta = skipMeta

    def makeText(self):
        F = self.F
        slotType = self.slotType
        skipMeta = self.skipMeta

        text = []
        tlFromTf = {}

        self.text = text
        self.tlFromTf = tlFromTf

        for s in F.otype.s(slotType):
            if skipMeta and F.is_meta.v(s):
                continue

            value = F.rstr.v(s)
            if value is None:
                value = F.str.v(s) or ""

            after = F.rafter.v(s)
            if after is None:
                after = F.after.v(s) or ""

            value = f"{value}{after}"

            text.append(value)
            t = len(text) - 1
            tlFromTf[s] = t

    def mkAnno(self, kind, ns, body, target):
        """Make an annotation and return its id.

        Parameters
        ----------
        kind: string
            The kind of annotation.
        ns: string
            The namespace of the annotation.
        body: string
            The body of the annotation.
        target: string  or tuple of strings
            The target of the annotation.
        """
        annos = self.annos
        aId = f"a{len(annos):>08}"
        annos.append((kind, aId, ns, body, target))
        return aId

    def makeAnno(self):
        E = self.E
        Es = self.Es
        F = self.F
        Fs = self.Fs
        nodeFeatures = self.nodeFeatures
        edgeFeatures = self.edgeFeatures
        slotType = self.slotType
        otypes = self.otypes
        nsOrig = self.nsOrig
        skipMeta = self.skipMeta
        warning = self.warning

        tlFromTf = self.tlFromTf

        annos = []
        text = self.text
        self.annos = annos

        wrongTargets = []

        for otype in otypes:
            isSlot = otype == slotType

            for n in F.otype.s(otype):
                if isSlot:
                    if skipMeta and F.is_meta.v(n):
                        continue
                    t = tlFromTf[n]
                    target = f"{t}-{t + 1}"
                    self.mkAnno(KIND_NODE, NS_TF, n, target)
                else:
                    ws = E.oslots.s(n)
                    if skipMeta and (F.is_meta.v(ws[0]) or F.is_meta.v(ws[-1])):
                        continue
                    start = tlFromTf[ws[0]]
                    end = tlFromTf[ws[-1]]
                    if end < start:
                        wrongTargets.append((otype, start, end))

                    target = f"{start}-{end + 1}"
                    aId = (
                        self.mkAnno(KIND_PI, nsOrig, otype[1:], target)
                        if otype.startswith("?")
                        else self.mkAnno(
                            KIND_ELEM, NS_FROM_OTYPE.get(otype, nsOrig), otype, target
                        )
                    )
                    tlFromTf[n] = aId
                    self.mkAnno(KIND_NODE, NS_TF, n, aId)

        for feat in nodeFeatures:
            ns = Fs(feat).meta.get("conversionCode", NS_FROM_FEAT.get(feat, nsOrig))

            if ns is None:
                warning(
                    f"Node feature {feat} has no namespace, "
                    f"defaulting to {NS_NONE}"
                )
                ns = NS_NONE

            for n, val in Fs(feat).items():
                t = tlFromTf.get(n, None)
                if t is None:
                    continue
                target = f"{t}-{t + 1}" if F.otype.v(n) == slotType else t
                aId = self.mkAnno(KIND_ATTR, ns, f"{feat}={val}", target)

        for feat in edgeFeatures:
            ns = Es(feat).meta.get("conversionCode", NS_FROM_FEAT.get(feat, nsOrig))

            if ns is None:
                warning(
                    f"Edge feature {feat} has no conversion code, "
                    f"defaulting to {NS_NONE}"
                )
                ns = NS_NONE

            for fromNode, toNodes in Es(feat).items():
                if skipMeta and F.is_meta.v(fromNode):
                    continue
                fromT = tlFromTf.get(fromNode, None)
                if fromT is None:
                    continue
                targetFrom = (
                    f"{fromT}-{fromT + 1}" if F.otype.v(fromNode) == slotType else fromT
                )

                if type(toNodes) is dict:
                    for toNode, val in toNodes.items():
                        if skipMeta and F.is_meta.v(toNode):
                            continue
                        toT = tlFromTf.get(toNode, None)
                        if toT is None:
                            continue

                        targetTo = (
                            f"{toT}-{toT + 1}" if F.otype.v(toNode) == slotType else toT
                        )
                        target = f"{targetFrom}->{targetTo}"
                        aId = self.mkAnno(KIND_EDGE, ns, f"{feat}={val}", target)
                else:
                    for toNode in toNodes:
                        if skipMeta and F.is_meta.v(toNode):
                            continue
                        toT = tlFromTf.get(toNode, None)
                        if toT is None:
                            continue
                        target = f"{fromT}->{toT}"
                        aId = self.mkAnno(KIND_EDGE, ns, feat, target)

        extra = {}
        extra.update(self.extra)

        for n, value in extra.items():
            t = tlFromTf[n]
            target = f"{t}-{t + 1}" if F.otype.v(n) == slotType else t
            aId = self.mkAnno(KIND_ANNO, NS_TT, str(value), target)

        if len(wrongTargets):
            print(f"WARNING: wrong targets, {len(wrongTargets)}x")
            for otype, start, end in wrongTargets:
                sega = text[start]
                segb = text[end - 1]
                print(f"{otype:>20} {start:>6} `{sega}` > {end - 1} `{segb}`")

    def writeAll(self):
        app = self.app
        info = self.info
        warning = self.warning
        text = self.text
        annos = self.annos

        baseDir = self.repoLocation
        relative = app.context.relative
        version = app.version
        wRelative = REL_RE.sub(f"/{TT_NAME}/{version}/", relative, count=1)
        resultDir = f"{baseDir}{wRelative}"
        textFile = f"{resultDir}/text.json"

        self.textFile = textFile

        initTree(resultDir, fresh=True)

        with open(textFile, "w") as fh:
            json.dump(dict(_ordered_segments=text), fh, ensure_ascii=False, indent=1)

        info(f"Text file: {len(text):>7} segments to {textFile}", tm=False)

        annoStore = {}

        for kind, aId, ns, body, target in annos:
            annoStore[aId] = (kind, ns, body, target)

        aIdSorted = sorted(annoStore.keys())

        annoFile = f"{resultDir}/anno.tsv"

        if False:
            with open(annoFile, "w") as fh:
                for aId in aIdSorted:
                    (kind, ns, body, target) = annoStore[aId]
                    fh.write(f"{aId}\t{kind}\t{ns}\t{body}\t{target}\n")

        thisAnnoStore = {}
        thisA = 1
        annoFiles = []
        self.annoFiles = annoFiles

        LIMIT = 400000
        j = 0
        total = 0

        def writeThis():
            annoFile = f"{resultDir}/anno-{thisA:>01}.json"
            annoFiles.append(annoFile)

            with open(annoFile, "w") as fh:
                json.dump(thisAnnoStore, fh, ensure_ascii=False, indent=1)

            info(f"{j:>6} annotations written to {annoFile}")

        for aId in aIdSorted:
            if j >= LIMIT:
                writeThis()
                thisA += 1
                thisAnnoStore = {}
                total += j
                j = 0

            thisAnnoStore[aId] = annoStore[aId]
            j += 1

        if len(thisAnnoStore):
            writeThis()
            total += j

        if len(annos) != total:
            info(f"Sum of batches : {total:>8}", tm=False)
            info(f"All annotations: {len(annoStore):>8}", tm=False)
            warning("Mismatch in number of annotations", tm=False)
        info(
            f"Anno files: {len(annos):>7} annotations to {len(annoFiles)} files",
            tm=False,
        )


class WATMS:
    def __init__(self, org, repo, backend):
        self.org = org
        self.repo = repo
        self.backend = backend

        repoDir = ex(f"~/{backend}/{org}/{repo}")
        tfDir = f"{repoDir}/tf"
        docs = dirContents(tfDir)[1]
        console(f"Found {len(docs)} docs in {tfDir}")
        self.docs = docs

    def produce(self, doc=None):
        org = self.org
        repo = self.repo
        backend = self.backend
        docs = self.docs

        chosenDoc = doc

        for doc in sorted(docs, key=lambda x: (x[0], int(x[1:]))):
            if chosenDoc is not None and chosenDoc != doc:
                continue

            console(f"{doc:>5} ... ", newline=False)
            A = use(
                f"{org}/{repo}:clone",
                relative=f"tf/{doc}",
                checkout="clone",
                backend=backend,
                silent=DEEP,
            )
            WA = WATM(A)
            WA.makeText()
            WA.makeAnno()
            WA.writeAll()
