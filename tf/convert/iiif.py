from ..core.files import (
    readYaml,
    readJson,
    writeJson,
    fileOpen,
    initTree,
    dirExists,
    dirCopy,
    dirContents,
    stripExt,
)
from ..core.helpers import console
from .helpers import parseIIIF, fillinIIIF

DS_STORE = ".DS_Store"


class IIIF:
    def __init__(self, teiVersion, app, pageInfoFile, prod=False, silent=False):
        self.teiVersion = teiVersion
        self.app = app
        self.pageInfoFile = pageInfoFile
        self.prod = prod
        self.silent = silent

        teiVersionRep = f"/{teiVersion}" if teiVersion else teiVersion

        F = app.api.F

        repoLocation = app.repoLocation
        staticDir = f"{repoLocation}/static{teiVersionRep}/{'prod' if prod else 'dev'}"
        self.staticDir = staticDir
        self.manifestDir = f"{staticDir}/manifests"
        self.thumbDir = (
            f"{repoLocation}/{app.context.provenanceSpec['graphicsRelative']}"
        )
        scanDir = f"{repoLocation}/scans"
        self.scanDir = scanDir
        coversDir = f"{scanDir}/covers"
        self.coversDir = coversDir
        self.pagesDir = f"{scanDir}/pages"
        self.logoInDir = f"{scanDir}/logo"
        self.logoDir = f"{staticDir}/logo"

        self.coversHtmlIn = f"{repoLocation}/programs/covers.html"
        self.coversHtmlOut = f"{staticDir}/covers.html"
        settings = readYaml(asFile=f"{repoLocation}/programs/iiif.yaml", plain=True)
        self.settings = settings
        self.templates = parseIIIF(settings, prod, "templates")

        self.getSizes()
        self.getRotations()
        self.getPageSeq()
        pages = self.pages
        folders = [F.folder.v(f) for f in F.otype.s("folder")]
        self.folders = folders

        self.console("Collections:")

        for folder in folders:
            n = len(pages["pages"][folder])
            self.console(f"{folder:>5} with {n:>4} pages")

    def console(self, msg, **kwargs):
        """Print something to the output.

        This works exactly as `tf.core.helpers.console`

        When the silent member of the object is True, the message will be suppressed.
        """
        silent = self.silent

        if not silent:
            console(msg, **kwargs)

    def getRotations(self):
        prod = self.prod
        thumbDir = self.thumbDir
        scanDir = self.scanDir

        rotateFile = f"{scanDir if prod else thumbDir}/rotation_pages.tsv"

        rotateInfo = {}
        self.rotateInfo = rotateInfo

        with fileOpen(rotateFile) as rh:
            next(rh)
            for line in rh:
                fields = line.rstrip("\n").split("\t")
                p = fields[0]
                rot = int(fields[1])
                rotateInfo[p] = rot

    def getSizes(self):
        prod = self.prod
        thumbDir = self.thumbDir
        scanDir = self.scanDir

        self.sizeInfo = {}

        for kind in ("covers", "pages"):
            sizeFile = f"{scanDir if prod else thumbDir}/sizes_{kind}.tsv"

            sizeInfo = {}
            self.sizeInfo[kind] = sizeInfo

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
        coversDir = self.coversDir
        pageInfoFile = self.pageInfoFile

        covers = sorted(
            stripExt(f) for f in dirContents(coversDir)[0] if f is not DS_STORE
        )
        self.covers = covers
        self.pages = dict(
            pages=readJson(asFile=pageInfoFile, plain=True), covers=dict(covers=covers)
        )

    def genPages(self, kind, folder=None):
        if kind == "covers":
            folder = kind
        templates = self.templates
        sizeInfo = self.sizeInfo[kind]
        rotateInfo = None if kind == "covers" else self.rotateInfo
        pages = self.pages[kind]
        thesePages = pages[folder]

        pageItem = templates.coverItem if kind == "covers" else templates.pageItem

        items = []

        for p in thesePages:
            item = {}
            w, h = sizeInfo.get(p, (0, 0))
            rot = 0 if rotateInfo is None else rotateInfo.get(p, 0)

            for k, v in pageItem.items():
                v = fillinIIIF(v, folder=folder, page=p, width=w, height=h, rot=rot)
                item[k] = v

            items.append(item)

        pageSequence = (
            templates.coverSequence if kind == "covers" else templates.pageSequence
        )
        manifestDir = self.manifestDir

        data = {}

        for k, v in pageSequence.items():
            v = fillinIIIF(v, folder=folder)
            data[k] = v

        data["items"] = items

        writeJson(data, asFile=f"{manifestDir}/{folder}.json")

    def manifests(self):
        folders = self.folders
        manifestDir = self.manifestDir
        logoInDir = self.logoInDir
        logoDir = self.logoDir
        coversHtmlIn = self.coversHtmlIn
        coversHtmlOut = self.coversHtmlOut
        prod = self.prod
        settings = self.settings

        with fileOpen(coversHtmlIn) as fh:
            coversHtml = fh.read()

        server = settings["switches"]["prod" if prod else "dev"]["server"]
        coversHtml = coversHtml.replace("«server»", server)

        with fileOpen(coversHtmlOut, "w") as fh:
            fh.write(coversHtml)

        initTree(manifestDir, fresh=True)

        self.genPages("covers")

        for folder in folders:
            self.genPages("pages", folder=folder)

        if dirExists(logoInDir):
            dirCopy(logoInDir, logoDir)
        else:
            console(f"Directory with logos not found: {logoInDir}", error=True)

        self.console(f"IIIF manifests generated in {manifestDir}")
