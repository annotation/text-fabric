from ..core.files import (
    readJson,
    readYaml,
    writeJson,
    fileOpen,
    fileExists,
    initTree,
    dirExists,
    dirCopy,
    dirContents,
    stripExt,
)
from ..core.generic import AttrDict
from ..core.helpers import console, readCfg

DS_STORE = ".DS_Store"


def fillinIIIF(data, **kwargs):
    tpd = type(data)

    if tpd is str:
        for k, v in kwargs.items():
            pattern = "{" + k + "}"

            if type(v) is int and data == pattern:
                data = v
                break
            else:
                data = data.replace(pattern, str(v))

        return data

    if tpd is list:
        return [fillinIIIF(item, **kwargs) for item in data]

    if tpd is dict:
        return {k: fillinIIIF(v, **kwargs) for (k, v) in data.items()}

    return data


def parseIIIF(settings, prod, selector):
    """Parse the iiif yml file.

    We fill in the parameters.
    """

    def applySwitches(prod, constants, switches):
        if len(switches):
            for k, v in switches["prod" if prod else "dev"].items():
                constants[k] = v

        return constants

    def substituteConstants(data, macros, constants):
        tpd = type(data)

        if tpd is str:
            for k, v in macros.items():
                pattern = f"<{k}>"
                data = data.replace(pattern, str(v))

            for k, v in constants.items():
                pattern = f"«{k}»"

                if type(v) is int and data == pattern:
                    data = v
                    break
                else:
                    data = data.replace(pattern, str(v))

            return data

        if tpd is list:
            return [substituteConstants(item, macros, constants) for item in data]

        if tpd is dict:
            return {
                k: substituteConstants(v, macros, constants) for (k, v) in data.items()
            }

        return data

    constants = applySwitches(
        prod, settings.get("constants", {}), settings.get("switches", {})
    )
    macros = applySwitches(
        prod, settings.get("macros", {}), settings.get("switches", {})
    )

    return AttrDict(
        {
            x: substituteConstants(xText, macros, constants)
            for (x, xText) in settings[selector].items()
        }
    )


class IIIF:
    def __init__(self, teiVersion, app, pageInfoDir, prod=False, silent=False):
        self.teiVersion = teiVersion
        self.app = app
        self.pageInfoDir = pageInfoDir
        self.prod = prod
        self.silent = silent
        self.error = False

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

        if dirExists(coversDir):
            self.console(f"Found covers in directory: {coversDir}")
            doCovers = True
        else:
            self.console(f"No cover directory: {coversDir}")
            doCovers = False

        self.doCovers = doCovers

        self.pagesDir = f"{scanDir}/pages"
        self.logoInDir = f"{scanDir}/logo"
        self.logoDir = f"{staticDir}/logo"

        if doCovers:
            self.coversHtmlIn = f"{repoLocation}/programs/covers.html"
            self.coversHtmlOut = f"{staticDir}/covers.html"

        (ok, settings) = readCfg(
            repoLocation, "iiif", "IIIF", verbose=-1 if silent else 1, plain=True
        )
        if not ok:
            self.error = True
            return

        self.settings = settings

        (ok, teiSettings) = readCfg(
            repoLocation, "tei", "TEI", verbose=-1 if silent else 1, plain=False
        )
        zoneBased = False

        if ok and teiSettings.zoneBased is not None:
            zoneBased = teiSettings.zoneBased

        self.zoneBased = zoneBased

        self.templates = parseIIIF(settings, prod, "templates")
        folders = [F.folder.v(f) for f in F.otype.s("folder")]

        self.getSizes()
        self.getRotations()
        self.getPageSeq(folders)
        pages = self.pages
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
        if self.error:
            return

        prod = self.prod
        thumbDir = self.thumbDir
        scanDir = self.scanDir

        rotateFile = f"{scanDir if prod else thumbDir}/rotation_pages.tsv"

        rotateInfo = {}
        self.rotateInfo = rotateInfo

        if not fileExists(rotateFile):
            console(f"Rotation file not found: {rotateFile}")
            return

        with fileOpen(rotateFile) as rh:
            next(rh)
            for line in rh:
                fields = line.rstrip("\n").split("\t")
                p = fields[0]
                rot = int(fields[1])
                rotateInfo[p] = rot

    def getSizes(self):
        if self.error:
            return

        prod = self.prod
        thumbDir = self.thumbDir
        scanDir = self.scanDir
        doCovers = self.doCovers

        self.sizeInfo = {}

        for kind in ("covers", "pages") if doCovers else ("pages",):
            sizeFile = f"{scanDir if prod else thumbDir}/sizes_{kind}.tsv"

            sizeInfo = {}
            self.sizeInfo[kind] = sizeInfo

            maxW, maxH = 0, 0

            n = 0

            totW, totH = 0, 0

            ws, hs = [], []

            if not fileExists(sizeFile):
                console(f"Size file not found: {sizeFile}", error=True)
                return

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

    def getPageSeq(self, folders):
        if self.error:
            return

        doCovers = self.doCovers
        zoneBased = self.zoneBased

        if doCovers:
            coversDir = self.coversDir
            covers = sorted(
                stripExt(f) for f in dirContents(coversDir)[0] if f is not DS_STORE
            )
            self.covers = covers

        pageInfoDir = self.pageInfoDir
        pageInfoFile = f"{pageInfoDir}/pageseq.json"
        facsFile = f"{pageInfoDir}/facs.yml"

        pages = None

        if fileExists(pageInfoFile):
            console(f"Using page info file {pageInfoFile}")
            pages = readJson(asFile=pageInfoFile, plain=True)
        elif fileExists(facsFile):
            console(f"Using facs file info file {facsFile}")
            pagesProto = readYaml(asFile=facsFile, plain=True, preferTuples=False)
            pages = {}

            if zoneBased:
                facsMappingFile = f"{pageInfoDir}/facsMapping.yml"

                if fileExists(facsMappingFile):
                    console(f"Using facs mapping file {facsMappingFile}")
                    facsMapping = readYaml(
                        asFile=facsMappingFile, plain=True, preferTuples=False
                    )

                    for path, ps in pagesProto.items():
                        folder = path.split("/")[0]
                        mapping = facsMapping.get(path, {})
                        pages.setdefault(folder, []).extend(
                            [mapping.get(p, p) for p in ps]
                        )
                else:
                    console(f"No facs mapping file {facsMappingFile}", error=True)
            else:
                for path, ps in pagesProto.items():
                    (folder, file) = path.split("/")
                    pages.setdefault(folder, []).extend(ps)
        else:
            console("No page-facsimile relating information found", error=True)

        if pages is None:
            console(
                "Could not assemble page sequence info, "
                "working with dummy page sequence",
                error=True,
            )
            self.pages = dict(
                pages={
                    folder: [f"page_{i:>03}" for i in range(1, 11)]
                    for folder in folders
                }
            )
        else:
            self.pages = dict(pages=pages)

        if doCovers:
            self.pages["covers"] = covers

    def genPages(self, kind, folder=None):
        if self.error:
            return

        zoneBased = self.zoneBased

        templates = self.templates
        sizeInfo = self.sizeInfo[kind]
        rotateInfo = None if kind == "covers" else self.rotateInfo
        pages = self.pages[kind]
        thesePages = pages if folder is None else pages[folder]

        if kind == "covers":
            folder = "covers"

        pageItem = templates.coverItem if kind == "covers" else templates.pageItem

        items = []

        for p in thesePages:
            item = {}
            w, h = sizeInfo.get(p, (0, 0))
            rot = 0 if rotateInfo is None else rotateInfo.get(p, 0)

            if zoneBased:
                (p, region) = p.split("«»")
            else:
                region = "full"

            for k, v in pageItem.items():
                v = fillinIIIF(
                    v, folder=folder, page=p, region=region, width=w, height=h, rot=rot
                )
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
        if self.error:
            return

        folders = self.folders
        manifestDir = self.manifestDir
        logoInDir = self.logoInDir
        logoDir = self.logoDir
        doCovers = self.doCovers

        prod = self.prod
        settings = self.settings
        server = settings["switches"]["prod" if prod else "dev"]["server"]

        initTree(manifestDir, fresh=True)

        if doCovers:
            coversHtmlIn = self.coversHtmlIn
            coversHtmlOut = self.coversHtmlOut

            with fileOpen(coversHtmlIn) as fh:
                coversHtml = fh.read()

            coversHtml = coversHtml.replace("«server»", server)

            with fileOpen(coversHtmlOut, "w") as fh:
                fh.write(coversHtml)

            self.genPages("covers")

        for folder in folders:
            self.genPages("pages", folder=folder)

        if dirExists(logoInDir):
            dirCopy(logoInDir, logoDir)
        else:
            console(f"Directory with logos not found: {logoInDir}", error=True)

        self.console(f"IIIF manifests generated in {manifestDir}")
