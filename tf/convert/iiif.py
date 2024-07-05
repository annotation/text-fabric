from ..core.files import (
    readYaml,
    readJson,
    writeJson,
    fileOpen,
    initTree,
    dirExists,
    dirCopy,
)
from ..core.helpers import console
from .helpers import parseIIIF, fillinIIIF


class IIIF:
    def __init__(self, teiVersion, app, prod=False, silent=False):
        self.teiVersion = teiVersion
        self.app = app
        self.prod = prod
        self.silent = silent

        F = app.api.F

        repoLocation = app.repoLocation
        iiifDir = f"{repoLocation}/iiif"
        self.logoDir = f"{iiifDir}/logo"
        self.manifestDir = (
            f"{iiifDir}/manifests/{teiVersion}/{'prod' if prod else 'dev'}"
        )
        self.thumbDir = (
            f"{repoLocation}/{app.context.provenanceSpec['graphicsRelative']}"
        )
        self.origDir = f"{repoLocation}/scans"
        self.reportDir = f"{repoLocation}/report/{teiVersion}"

        settings = readYaml(asFile=f"{repoLocation}/programs/iiif.yaml", plain=True)
        self.templates = parseIIIF(settings, prod, "templates")

        self.getSizes()
        self.getPageSeq()
        pages = self.pages
        folders = [F.folder.v(f) for f in F.otype.s("folder")]
        self.folders = folders

        self.console("Collections:")

        for folder in folders:
            n = len(pages[folder])
            self.console(f"{folder:>5} with {n:>4} pages")

    def console(self, msg, **kwargs):
        """Print something to the output.

        This works exactly as `tf.core.helpers.console`

        When the silent member of the object is True, the message will be suppressed.
        """
        silent = self.silent

        if not silent:
            console(msg, **kwargs)

    def getSizes(self):
        prod = self.prod
        thumbDir = self.thumbDir
        origDir = self.origDir
        sizeFile = f"{origDir if prod else thumbDir}/sizes.tsv"

        sizeInfo = {}
        self.sizeInfo = sizeInfo

        maxW, maxH = 0, 0

        n = 0

        totW, totH = 0, 0

        ws, hs = [], []

        with fileOpen(sizeFile) as rh:
            next(rh)
            for line in rh:
                fields = line.rstrip("\n").split("\t")
                p = fields[0]
                (w, h) = (int(x) for x in fields[1:3])
                sizeInfo[p] = (w, h)
                ws.append(w)
                hs.append(h)
                n += 1
                totW += w
                totH += h

                if w > maxW:
                    maxW = w
                if h > maxH:
                    maxH = h

        avW = int(round(totW / n))
        avH = int(round(totH / n))

        devW = int(round(sum(abs(w - avW) for w in ws) / n))
        devH = int(round(sum(abs(h - avH) for h in hs) / n))

        self.console(f"Maximum dimensions: W = {maxW:>4} H = {maxH:>4}")
        self.console(f"Average dimensions: W = {avW:>4} H = {avH:>4}")
        self.console(f"Average deviation:  W = {devW:>4} H = {devH:>4}")

    def getPageSeq(self):
        reportDir = self.reportDir
        pageSeqFile = f"{reportDir}/pageseq.json"
        self.pages = readJson(asFile=pageSeqFile, plain=True)

    def genFolder(self, folder):
        templates = self.templates
        sizeInfo = self.sizeInfo
        pages = self.pages
        thesePages = pages[folder]

        canvasLevel = templates.canvasLevel

        items = []

        for p in thesePages:
            item = {}
            w, h = sizeInfo.get(p, (0, 0))

            for k, v in canvasLevel.items():
                v = fillinIIIF(v, folder=folder, page=p, width=w, height=h)
                item[k] = v

            items.append(item)

        manifestLevel = templates.manifestLevel
        manifestDir = self.manifestDir

        data = {}

        for k, v in manifestLevel.items():
            v = fillinIIIF(v, folder=folder)
            data[k] = v

        data["items"] = items

        writeJson(data, asFile=f"{manifestDir}/{folder}.json")

    def manifests(self):
        folders = self.folders
        manifestDir = self.manifestDir
        logoDir = self.logoDir

        initTree(manifestDir, fresh=True)

        for folder in folders:
            self.genFolder(folder)

        if dirExists(logoDir):
            dirCopy(logoDir, f"{manifestDir}/logo")
        else:
            console(f"Directory with logos not found: {logoDir}", error=True)

        self.console(f"IIIF manifests generated in {manifestDir}")
