import collections
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


def rep(status):
    return "OK" if status else "XX"


class WATM:
    def __init__(self, app, nsOrig, skipMeta=False, extra={}):
        self.app = app
        self.nsOrig = nsOrig
        self.extra = extra
        api = app.api
        F = api.F
        E = api.E

        self.L = api.L
        self.Es = api.Es
        self.F = F
        self.E = E
        self.Fs = api.Fs
        self.slotType = self.F.otype.slotType
        self.otypes = self.F.otype.all
        self.info = app.info
        self.repoLocation = app.repoLocation

        Fall = api.Fall
        Eall = api.Eall
        self.Fall = Fall
        self.Eall = Eall

        excludedFeatures = {OTYPE, OSLOTS, "after", "str"}
        self.nodeFeatures = [f for f in Fall() if f not in excludedFeatures]
        self.edgeFeatures = [f for f in Eall() if f not in excludedFeatures]

        FAllSet = set(Fall())

        self.fotypev = F.otype.v
        self.eoslots = E.oslots.s
        self.emptyv = F.empty.v if "empty" in FAllSet else None
        self.strv = F.str.v if "str" in FAllSet else None
        self.rstrv = F.rstr.v if "rstr" in FAllSet else None
        self.afterv = F.after.v if "after" in FAllSet else None
        self.rafterv = F.rafter.v if "rafter" in FAllSet else None
        is_metav = F.is_meta.v if "is_meta" in FAllSet else None
        self.is_metav = is_metav

        if skipMeta and not is_metav:
            console(
                "skipMeta=True has no effect because feature is_meta is not defined.",
                error=True,
            )
            skipMeta = False

        self.skipMeta = skipMeta

    def makeText(self):
        F = self.F
        slotType = self.slotType
        skipMeta = self.skipMeta

        emptyv = self.emptyv
        strv = self.strv
        rstrv = self.rstrv
        afterv = self.afterv
        rafterv = self.rafterv
        is_metav = self.is_metav

        text = []
        tlFromTf = {}

        self.text = text
        self.tlFromTf = tlFromTf

        for s in F.otype.s(slotType):
            if skipMeta and is_metav(s):
                continue

            after = rafterv(s) if rafterv else None

            if after is None:
                after = afterv(s) if afterv else None

            if after is None:
                after = ""

            if emptyv and emptyv(s):
                value = after
            else:
                string = rstrv(s) if rstrv else None

                if string is None:
                    string = strv(s) if strv else None

                if string is None:
                    string = ""

                value = f"{string}{after}"

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
        Es = self.Es
        F = self.F
        Fs = self.Fs
        fotypev = self.fotypev
        eoslots = self.eoslots
        nodeFeatures = self.nodeFeatures
        edgeFeatures = self.edgeFeatures
        slotType = self.slotType
        otypes = self.otypes
        nsOrig = self.nsOrig
        skipMeta = self.skipMeta

        tlFromTf = self.tlFromTf

        is_metav = self.is_metav

        isTei = nsOrig == NS_TEI

        annos = []
        text = self.text
        self.annos = annos

        wrongTargets = []

        for otype in otypes:
            isSlot = otype == slotType

            for n in F.otype.s(otype):
                if isSlot:
                    if skipMeta and is_metav(n):
                        continue

                    t = tlFromTf[n]
                    target = f"{t}-{t + 1}"
                    self.mkAnno(KIND_NODE, NS_TF, n, target)
                else:
                    ws = eoslots(n)
                    if skipMeta and (is_metav(ws[0]) or is_metav(ws[-1])):
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
                console(
                    f"Node feature {feat} has no namespace, "
                    f"defaulting to {NS_NONE}",
                    error=True,
                )
                ns = NS_NONE

            isRend = False
            isNote = False

            if isTei:
                parts = feat.split("_", 2)
                isRend = len(parts) >= 2 and parts[0] == "rend"
                isNote = len(parts) == 2 and parts[0] == "is" and parts[1] == "note"

            if isRend:
                for n, val in Fs(feat).items():
                    if not val or (skipMeta and is_metav(n)):
                        continue

                    prop = parts[1]
                    t = tlFromTf[n]
                    target = f"{t}-{t + 1}" if fotypev(n) == slotType else t
                    self.mkAnno(KIND_FMT, ns, prop, target)
            elif isNote:
                for n, val in Fs(feat).items():
                    if not val or (skipMeta and is_metav(n)):
                        continue

                    t = tlFromTf[n]
                    target = f"{t}-{t + 1}" if fotypev(n) == slotType else t
                    self.mkAnno(KIND_FMT, ns, "note", target)
            else:
                for n, val in Fs(feat).items():
                    if skipMeta and is_metav(n):
                        continue

                    t = tlFromTf.get(n, None)

                    if t is None:
                        continue

                    target = f"{t}-{t + 1}" if fotypev(n) == slotType else t
                    aId = self.mkAnno(KIND_ATTR, ns, f"{feat}={val}", target)

        for feat in edgeFeatures:
            ns = Es(feat).meta.get("conversionCode", NS_FROM_FEAT.get(feat, nsOrig))

            if ns is None:
                console(
                    f"Edge feature {feat} has no conversion code, "
                    f"defaulting to {NS_NONE}",
                    error=True,
                )
                ns = NS_NONE

            for fromNode, toNodes in Es(feat).items():
                if skipMeta and is_metav(fromNode):
                    continue

                fromT = tlFromTf.get(fromNode, None)

                if fromT is None:
                    continue

                targetFrom = (
                    f"{fromT}-{fromT + 1}" if fotypev(fromNode) == slotType else fromT
                )

                if type(toNodes) is dict:
                    for toNode, val in toNodes.items():
                        if skipMeta and is_metav(toNode):
                            continue

                        toT = tlFromTf.get(toNode, None)

                        if toT is None:
                            continue

                        targetTo = (
                            f"{toT}-{toT + 1}" if fotypev(toNode) == slotType else toT
                        )
                        target = f"{targetFrom}->{targetTo}"
                        aId = self.mkAnno(KIND_EDGE, ns, f"{feat}={val}", target)
                else:
                    for toNode in toNodes:
                        if skipMeta and is_metav(toNode):
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
            target = f"{t}-{t + 1}" if fotypev(n) == slotType else t
            aId = self.mkAnno(KIND_ANNO, NS_TT, str(value), target)

        if len(wrongTargets):
            print(f"WARNING: wrong targets, {len(wrongTargets)}x")
            for otype, start, end in wrongTargets:
                sega = text[start]
                segb = text[end - 1]
                print(f"{otype:>20} {start:>6} `{sega}` > {end - 1} `{segb}`")

    def writeAll(self):
        app = self.app
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

        console(f"Text file: {len(text):>7} segments to {textFile}")

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

            console(f"{j:>6} annotations written to {annoFile}")

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
            console(f"Sum of batches : {total:>8}")
            console(f"All annotations: {len(annoStore):>8}")
            console("Mismatch in number of annotations", error=True)
        console(f"Anno files: {len(annos):>7} annotations to {len(annoFiles)} files")

    @staticmethod
    def compare(nTF, nWA):
        console(f"\tTF: {nTF:>6}\n\tWA: {nWA:>6}", error=nTF != nWA)
        return nTF == nWA

    @staticmethod
    def strEqual(wa=None, tf=None):
        different = False
        for i, cTF in enumerate(tf):
            if i >= len(wa):
                contextI = max((0, i - 10))
                console(f"\tWA {i}: {wa[contextI:i]} <END>", error=True)
                console(f"\tTF {i}: {tf[contextI:i]} <> {tf[i:i + 10]}", error=True)
                different = True
                break
            elif tf[i] != wa[i]:
                contextI = max((0, i - 10))
                console(
                    f"\tWA {i}: {wa[contextI:i]} <{wa[i]}> {wa[i + 1:i + 11]}",
                    error=True,
                )
                console(
                    f"\tTF {i}: {tf[contextI:i]} <{tf[i]}> {tf[i + 1:i + 11]}",
                    error=True,
                )
                different = True
                break

        if not different and len(wa) > len(tf):
            i = len(tf)
            contextI = max((0, i - 10))
            console(f"\tWA {i}: {wa[contextI:i]} <> {wa[i:i + 10]}", error=True)
            console(f"\tTF {i}: {tf[contextI:i]} <END>", error=True)
            different = True

        sampleWA = f"{wa[0:20]} ... {wa[-20:]}".replace("\n", " ")
        sampleTF = f"{tf[0:20]} ... {tf[-20:]}".replace("\n", " ")
        console(f"\tTF: {sampleTF:>6}\n\tWA: {sampleWA:>6}")
        return not different

    def testSetup(self):
        textFile = self.textFile
        annoFiles = self.annoFiles

        with open(textFile) as fh:
            text = json.load(fh)
            tokens = text["_ordered_segments"]

        self.testTokens = tokens

        annotationById = {}
        annotations = []

        for annoFile in annoFiles:
            with open(annoFile) as fh:
                annos = json.load(fh)

                for aId, (kind, ns, body, target) in annos.items():
                    if "->" in target:
                        parts = target.split("->", 1)
                    else:
                        parts = [target]
                    newParts = []
                    for part in parts:
                        if "-" in part:
                            (start, end) = part.split("-", 1)
                            part = (int(start), int(end))
                        newParts.append(part)

                    target = newParts[0] if len(newParts) == 1 else tuple(newParts)

                    annotationById[aId] = (kind, body, target)
                    annotations.append((aId, kind, body, target))

        annotations = sorted(annotations)
        self.testAnnotations = annotations

    def testText(self):
        F = self.F
        skipMeta = self.skipMeta
        is_metav = self.is_metav
        tokens = self.testTokens
        text = self.text

        console("Testing the text ...")

        nTokensTF = sum(
            0 if skipMeta and is_metav(s) else 1 for s in range(1, F.otype.maxSlot + 1)
        )
        nTokensWA = len(tokens)
        nGood = self.compare(nTokensTF, nTokensWA)
        console(f"{rep(nGood)} - Same number of tokens", error=not nGood)

        textWA = "".join(tokens)
        textTF = "".join(text)

        tGood = self.strEqual(wa=textWA, tf=textTF)
        console(f"{rep(tGood)} - Same text", error=not tGood)

        return nGood and tGood

    def testElements(self):
        F = self.F
        fotypev = self.fotypev
        eoslots = self.eoslots
        skipMeta = self.skipMeta
        is_metav = self.is_metav
        annotations = self.testAnnotations

        console("Testing the elements ...")

        nElementsTF = 0
        nPisTF = 0

        for n in range(F.otype.maxSlot + 1, F.otype.maxNode + 1):
            nType = fotypev(n)
            isPi = nType.startswith("?")

            if isPi:
                nPisTF += 1

            slots = eoslots(n)
            b = slots[0]
            e = slots[-1]

            if skipMeta and (is_metav(b) or is_metav(e)):
                continue
            else:
                if not isPi:
                    nElementsTF += 1

        nElementsWA = sum(
            1 if kind == "element" else 0 for (aId, kind, body, target) in annotations
        )
        nPisWA = sum(
            1 if kind == "pi" else 0 for (aId, kind, body, target) in annotations
        )

        eGood = self.compare(nElementsTF, nElementsWA)
        console(f"{rep(eGood)} - Same number of elements as nodes", error=not eGood)

        pGood = self.compare(nPisTF, nPisWA)
        console(
            f"{rep(pGood)} - Same number of processing instructions", error=not pGood
        )

        # element annotations

        tfFromAid = {}

        element = 0
        pi = 0
        other = 0
        good = 0
        wrong = 0
        unmapped = 0

        for aId, kind, body, target in annotations:
            if kind == "node":
                tfFromAid[target] = body

        self.tfFromAid = tfFromAid

        console(f"\t{len(tfFromAid)} element annotations")

        for aId, kind, body, target in annotations:
            isElem = kind == "element"
            isPi = kind == "pi"

            if not isElem and not isPi:
                other += 1
                continue

            if isElem:
                element += 1
            else:
                pi += 1

            tag = body
            node = tfFromAid.get(aId, None)
            if node is None:
                unmapped += 1
                continue

            otype = fotypev(node)

            if isPi and tag == otype[1:] or not isPi and tag == otype:
                good += 1
            else:
                wrong += 1

        console(f"\tElement : {element:>5} x")
        console(f"\tPi      : {pi:>5} x")
        console(f"\tOther   : {other:>5} x")
        console(f"\tGood    : {good:>5} x")
        console(f"\tWrong   : {wrong:>5} x")
        console(f"\tUnmapped: {unmapped:>5} x")

        aGood = wrong == 0 and unmapped == 0
        console(f"{rep(aGood)} - All element annotations OK", error=not aGood)

        return aGood and eGood and pGood

    def testAttributes(self):
        Fs = self.Fs
        Fall = self.Fall
        eoslots = self.eoslots
        skipMeta = self.skipMeta
        is_metav = self.is_metav
        annotations = self.testAnnotations
        tfFromAid = self.tfFromAid
        nsOrig = self.nsOrig

        isTei = nsOrig == NS_TEI

        console("Testing the attributes ...")

        attWA = []

        for aId, kind, body, target in annotations:
            if kind != "attribute":
                continue
            node = tfFromAid[target]
            (att, value) = body.split("=", 1)
            attWA.append((node, att, value))

        attWA = sorted(attWA)

        console(f"\t{len(attWA)} attribute values")

        good = 0
        wrong = []

        for node, att, valWA in attWA:
            valTF = str(Fs(att).v(node))
            if valWA == valTF:
                good += 1
            else:
                wrong.append((node, att, valWA, valTF))

        console(f"\tGood:     {good:>5} x")
        console(f"\tWrong:    {len(wrong):>5} x")
        consistent = len(wrong) == 0
        console(
            f"{rep(consistent)} - annotations consistent with features",
            error=not consistent,
        )

        attTF = []

        for feat in Fall():
            if feat in {"otype", "str", "after"}:
                continue

            if skipMeta and feat == "is_meta":
                continue

            if isTei and (
                (feat != "is_meta" and feat.startswith("is_"))
                or feat.startswith("rend_")
            ):
                continue

            for node, valTF in Fs(feat).items():
                slots = eoslots(node)
                b = slots[0]
                e = slots[-1]

                if skipMeta and (is_metav(b) or is_metav(e)):
                    continue

                attTF.append((node, feat, str(valTF)))

        attTF = sorted(attTF)

        console(f"\tWA attributes: {len(attWA)}")
        console(f"\tTF attributes: {len(attTF)}")
        complete = attTF == attWA
        console(
            f"{rep(complete)} - annotations complete w.r.t. features",
            error=not complete,
        )

        console("Testing the format attributes ...")

        fmtWA = []

        for aId, kind, body, target in annotations:
            if kind != "format":
                continue
            if body == "note":
                continue
            node = tfFromAid[target]
            fmtWA.append((node, body))

        fmtWA = sorted(fmtWA)
        fmtWaFreq = collections.Counter()

        for node, body in fmtWA:
            fmtWaFreq[body] += 1

        console(f"\t{len(fmtWA)} format values")
        console("\tformatting attributes: ")
        for fa, n in sorted(fmtWaFreq.items(), key=lambda x: (-x[1], x[0])):
            console(f"\t\t{n:>6} x {fa}")

        good = 0
        wrong = []

        for node, valWA in fmtWA:
            feat = f"rend_{valWA}"
            valTF = valWA if str(Fs(feat).v(node)) else None
            if valWA == valTF:
                good += 1
            else:
                wrong.append((node, feat, valWA, valTF))

        console(f"\tGood:     {good:>5} x")
        console(f"\tWrong:    {len(wrong):>5} x")
        fconsistent = len(wrong) == 0
        console(
            f"{rep(fconsistent)} - format annotations consistent with features",
            error=not fconsistent,
        )

        fmtTF = []

        for feat in Fall():
            if not feat.startswith("rend_"):
                continue

            value = feat.split("_", 2)[1]
            if value == "note":
                continue

            for node, valTF in Fs(feat).items():
                slots = eoslots(node)
                b = slots[0]
                e = slots[-1]

                if skipMeta and (is_metav(b) or is_metav(e)):
                    continue

                fmtTF.append((node, value))

        fmtTF = sorted(fmtTF)

        console(f"\tWA format attributes: {len(fmtWA)}")
        console(f"\tTF format attributes: {len(fmtTF)}")
        fcomplete = fmtTF == fmtWA
        console(
            f"{rep(complete)} - format annotations complete w.r.t. features",
            error=not fcomplete,
        )

        return consistent and complete and fconsistent and fcomplete

    def testEdges(self):
        Es = self.Es
        Eall = self.Eall
        annotations = self.testAnnotations

        console("Testing the edges ...")

        tfFromAidNodes = {}
        tfFromAidEdges = {}

        for aId, kind, body, target in annotations:
            if kind != "node":
                continue
            if type(target) is tuple:
                (start, end) = target
                if start + 1 != end:
                    print(target)
                    break
                target = end
            tfFromAidNodes[target] = body

        for aId, kind, body, target in annotations:
            if kind != "edge":
                continue

            (fro, to) = target
            fromNode = tfFromAidNodes[fro]
            toNode = tfFromAidNodes[to]
            parts = body.split("=", 1)
            (name, val) = (body, None) if len(parts) == 1 else parts
            tfFromAidEdges.setdefault(name, {}).setdefault(fromNode, {})[toNode] = val

        console(f"\tFound: {len(tfFromAidNodes)} nodes")

        for edge, edgeData in sorted(tfFromAidEdges.items()):
            print(f"\tFound edge {edge} with {len(edgeData)} starting nodes")

        allGood = True

        for edge in set(Eall()) | set(tfFromAidEdges):
            if edge == "oslots":
                continue

            print(f"Checking edge {edge}")

            good = True

            if edge not in set(Eall()):
                print("\tmissing in TF data")
                good = False

            if edge not in tfFromAidEdges:
                print("\tmissing in annotation data")
                good = False

            if not good:
                continue

            dataTF = dict(Es(edge).items())
            dataAid = tfFromAidEdges[edge]

            fromNodesTF = set(dataTF)
            fromNodesAid = set(dataAid)

            nFromTF = len(fromNodesTF)
            nFromAid = len(fromNodesAid)

            if fromNodesTF == fromNodesAid:
                console(f"\tsame {nFromTF} fromNodes")
            else:
                console(f"\tfrom nodes differ: {nFromTF} in TF, {nFromAid} in Aid")
                good = False

            diffs = []

            nToChecked = 0

            for f, toNodeInfoTF in dataTF.items():
                toNodeInfoAid = dataAid[f]
                if type(toNodeInfoTF) is dict:
                    toNodeInfoTF = {k: str(v) for (k, v) in toNodeInfoTF.items()}
                else:
                    toNodeInfoTF = {x: None for x in toNodeInfoTF}

                if toNodeInfoTF != toNodeInfoAid:
                    diffs.append((f, toNodeInfoTF, toNodeInfoAid))

                nToChecked += len(toNodeInfoTF)

            if len(diffs):
                good = False
                console(
                    f"\tdifferences in toNodes for {len(diffs)} fromNodes", error=True
                )

                for f, toNodeInfoTF, toNodeInfoAid in sorted(diffs)[0:10]:
                    console(f"\t\tfromNode {f}", error=True)

                    toNodesTF = set(toNodeInfoTF)
                    toNodesAid = set(toNodeInfoAid)

                    nToTF = len(toNodesTF)
                    nToAid = len(toNodesAid)

                    if toNodesTF == toNodesAid:
                        console(f"\t\t\tsame {nToTF} toNodes")
                    else:
                        console(
                            f"\t\t\ttoNodes differ: {nToTF} in TF, {nToAid} in Aid",
                            error=True,
                        )
                    for t in toNodesTF | toNodesAid:
                        doCompare = True
                        if t not in toNodesTF:
                            console(f"\t\t\t\ttoNode {t} not in TF", error=True)
                            doCompare = False
                        else:
                            valTF = toNodeInfoTF[t]

                        if t not in toNodesAid:
                            console(f"\t\t\t\ttoNode {t} not in Aid", error=True)
                            doCompare = False
                        else:
                            valAid = toNodeInfoAid[t]

                        if doCompare:
                            if valTF == valAid:
                                console(
                                    f"\t\t\t\ttoNode{t} values agree: {repr(valTF)}"
                                )
                            else:
                                console(
                                    f"\t\t\t\ttoNode{t} values differ: "
                                    f"TF: {repr(valTF)} Aid: {repr(valAid)}",
                                    error=True,
                                )

            console(f"\t{nToChecked} toNodes checked")
            console("\tOK" if good else "\tWRONG", error=not good)

            if not good:
                allGood = False

        console(f"{rep(allGood)} - {'All' if allGood else 'Not all'} edges agree")

        return allGood

    def testAll(self):
        self.testSetup()

        good = True

        if not self.testText():
            good = False

        if not self.testElements():
            good = False

        if not self.testAttributes():
            good = False

        if not self.testEdges():
            good = False

        console("Overall outcome ...")
        allRep = "All" if good else "Not all"
        console(f"{rep(good)} - {allRep} tests passed", error=not good)

        return good


class WATMS:
    def __init__(self, org, repo, backend, nsOrig, skipMeta=False, extra={}):
        self.org = org
        self.repo = repo
        self.backend = backend
        self.nsOrig = nsOrig
        self.skipMeta = skipMeta
        self.extra = extra

        repoDir = ex(f"~/{backend}/{org}/{repo}")
        tfDir = f"{repoDir}/tf"
        docs = dirContents(tfDir)[1]
        console(f"Found {len(docs)} docs in {tfDir}")
        self.docs = docs

    def produce(self, doc=None):
        org = self.org
        repo = self.repo
        backend = self.backend
        nsOrig = self.nsOrig
        skipMeta = self.skipMeta
        extra = self.extra
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
            WA = WATM(A, nsOrig, skipMeta=skipMeta, extra=extra)
            WA.makeText()
            WA.makeAnno()
            WA.writeAll()
