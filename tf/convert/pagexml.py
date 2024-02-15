import sys
from subprocess import run

from ..capable import CheckImport
from ..core.command import readArgs
from ..core.files import (
    fileOpen,
    abspath,
    dirNm,
    dirContents,
    dirExists,
    fileExists,
    fileCopy,
    initTree,
    getLocation,
    readYaml,
    writeYaml,
    expanduser as ex,
    unexpanduser as ux,
)
from ..core.generic import AttrDict
from ..core.helpers import console, versionSort, mergeDict
from ..core.timestamp import AUTO, DEEP, TERSE
from ..parameters import BRANCH_DEFAULT_NEW
from ..fabric import Fabric
from ..convert.walker import CV

from .helpers import FILE, PAGE, DOC, REGION, LINE, NODE, tokenize


TOKEN = "token"
SOFT_HYPHEN_CHARS = {"¬", "\u00ad"}


def setUp():
    helpText = """
    Convert PageXML to TF.

    There are also commands to check the to load and browse the resulting TF."""

    taskSpec = dict(
        convert="converts PageXML to TF",
        load="loads the generated TF",
        app="configures the TF app for the result",
        browse="starts the TF browser on the result",
    )
    taskExcluded = {"browse"}

    paramSpec = {
        "tf": (
            (
                "0 or latest: update latest version;\n\t\t"
                "1 2 3: increase major, intermediate, minor TF version;\n\t\t"
                "rest: explicit version."
            ),
            "latest",
        ),
        "source": (
            (
                "0 or latest: latest version;\n\t\t"
                "-1 -2 etc: previous version, before previous, ...;\n\t\t"
                "1 2 etc: first version, second version, ...;\n\t\t"
                "rest: explicit version."
            ),
            "latest",
        ),
    }

    flagSpec = dict(
        verbose=("Produce less or more progress and reporting messages", -1, 3),
        doc=("Do only this document", None, 0),
    )
    return (helpText, taskSpec, taskExcluded, paramSpec, flagSpec)


(HELP, TASKS, TASKS_EXCLUDED, PARAMS, FLAGS) = setUp()


def diverge(cv, s, rtx, rsp, ltx, lsp):
    if ltx != rtx:
        cv.feature(s, str=ltx, rstr=rtx)
    if lsp != rsp:
        cv.feature(s, after=lsp, rafter=rsp)


def tokenLogic(cv, s, token, hangover, isFirst, isSecondLast, isLast):
    (rtx, rsp) = token

    same = not isLast and not isSecondLast and (not isFirst or hangover is None)

    if same:
        cv.feature(s, str=rtx, after=rsp)
        # cv.feature(s, str=rtx)
        # if rsp == "\n":
        #     cv.feature(s, after=" ", rafter=rsp)
        # else:
        #     cv.feature(s, after=rsp)
    else:
        cv.feature(s, str="", after="", rstr=rtx, rafter=rsp)

    if isFirst and hangover:
        hangover[3] += rtx
        # hangover[4] = " " if rsp == "\n" else rsp
        hangover[4] = rsp

    if isSecondLast:
        if hangover is None:
            hangover = [s, rtx, rsp, rtx, rsp]
        else:
            hangover[3] += rtx
            # hangover[4] = " " if rsp == "\n" else rsp
            hangover[4] = rsp

    else:
        if isLast:
            cv.feature(s, str="", after="", rstr=rtx, rafter=rsp)
        elif hangover is not None:
            diverge(cv, *hangover)
            hangover = None

    return hangover


# WALKERS


def emptySlot(cv):
    s = cv.slot()
    cv.feature(s, rstr="", rafter="", str="", after="")


def linebreakSlot(cv):
    s = cv.slot()
    cv.feature(s, rstr="", rafter="\n", str="", after="")


def walkObject(cv, cur, xObj):
    """Internal function to deal with a single element.

    Will be called recursively.

    Parameters
    ----------
    cv: object
        The converter object, needed to issue actions.
    cur: dict
        Various pieces of data collected during walking
        and relevant for some next steps in the walk.

        The subdictionary `cur["node"]` is used to store the currently generated
        nodes by node type.
    bj
    xode: object
        An PageXML object.
    """
    tp = xObj.main_type
    xId = xObj.id
    box = AttrDict(xObj.coords.box)

    isScan = tp == "scan"
    isRegion = tp == "text_region"
    isLine = tp == LINE

    nTp = PAGE if isScan else REGION if isRegion else LINE if isLine else tp
    nd = cv.node(nTp)
    cur[NODE][nTp] = nd
    cv.feature(nd, id=xId, x=box.x, y=box.y, w=box.w, h=box.h)

    if isLine:
        cur["line"] += 1
        cv.feature(nd, line=cur["line"])

        tokens = tokenize(xObj.text or "")
        nTokens = len(tokens)
        slots = []

        hangover = cur["hangover"]

        hasHyphen = len(tokens) > 0 and tokens[-1][0] in SOFT_HYPHEN_CHARS

        for token in tokens:
            s = cv.slot()
            slots.append(s)
            isFirst = len(slots) == 1
            isLast = hasHyphen and len(slots) == nTokens
            isSecondLast = hasHyphen and len(slots) == nTokens - 1
            hangover = tokenLogic(cv, s, token, hangover, isFirst, isSecondLast, isLast)

        cur["hangover"] = hangover

        hangover = None

        linebreakSlot(cv)

    elif isScan or isRegion:
        if isScan:
            cv.feature(nd, page=cur["page"])

        hangover = cur["hangover"]

        for yObj in xObj.get_text_regions_in_reading_order():
            walkObject(cv, cur, yObj)
        for yObj in xObj.lines:
            walkObject(cv, cur, yObj)
    else:
        cv.stop(f"UNKNOWN TYPE {tp}")

    if not cv.linked(nd):
        emptySlot(cv)
    cv.terminate(nd)


class PageXML(CheckImport):
    def __init__(
        self,
        sourceDir,
        repoDir,
        source=PARAMS["source"][1],
        tf=PARAMS["tf"][1],
        verbose=FLAGS["verbose"][1],
        doc=FLAGS["doc"][1],
    ):
        """Converts PageXML to TF.

        Below we describe how to control the conversion machinery.

        Based on current directory from where the script is called,
        it defines all the ingredients to carry out
        a `tf.convert.walker` conversion of the PageXML input.

        This function is assumed to work in the context of a repository,
        i.e. a directory on your computer relative to which the input directory exists,
        and various output directories: `tf`, `app`, `docs`.

        The `repoDir` must be at

        ```
        ~/backend/org/repo/relative
        ```

        where

        *   `~` is your home directory;
        *   `backend` is an online back-end name,
            like `github`, `gitlab`, `git.huc.knaw.nl`;
        *   `org` is an organization, person, or group in the back-end;
        *   `repo` is a repository in the `org`.
        *   `relative` is a directory path within the repo (0 or more components)

        This is only about the directory structure on your local computer;
        it is not required that you have online incarnations of your repository
        in that back-end.
        Even your local repository does not have to be a git repository.

        The only thing that matters is that the full path to your repo can be parsed
        as a sequence of `home/backend/org/repo/relative`.

        Relative to this directory the program expects and creates
        input / output directories.

        ## source/version directory

        The source directory is specified by `sourceDir`, and within it are version
        directories.

        ## Document directories

        These are the top-level directories within the version directories.

        They correspond to individual documents. Documents typically contain
        a set of pages.

        ## Input directories per document

        *   `image`: contain the scan images
        *   `meta`: contain metadata files
        *   `page`: contain the PageXML files

        The files in `image` and `page` have names that consist of a 4-digit
        number with leading zeros, and any two files with the same name in
        `image` and `page` represent the same document.

        ## Output directories

        ### `tf`

        The directory under which the TF output file (with extension `.tf`)
        are placed.
        If it does not exist, it will be created.
        The TF files will be generated in a folder named by a version number,
        passed as `tfVersion`.

        ### `app` and `docs`

        Location of additional TF app configuration and documentation files.
        If they do not exist, they will be created with some sensible default
        settings and generated documentation.
        These settings can be overridden in the `app/config_custom.yaml` file.
        Also a default `display.css` file and a logo are added.

        ### `docs`

        Location of additional documentation.
        This can be generated or hand-written material, or a mixture of the two.

        Parameters
        ----------
        sourceDir: string
            The location of the source directory
        repoDir: string
            The location of the target repo where the TF data is generated.
        source: string, optional ""
            If empty, use the latest version under the `source` directory with sources.
            Otherwise it should be a valid integer, and it is the index in the
            sorted list of versions there.

            *   `0` or `latest`: latest version;
            *   `-1`, `-2`, ... : previous version, version before previous, ...;
            *   `1`, `2`, ...: first version, second version, ....
            *   everything else that is not a number is an explicit version

            If the value cannot be parsed as an integer, it is used as the exact
            version name.

        tf: string, optional ""
            If empty, the TF version used will be the latest one under the `tf`
            directory.

            If it can be parsed as the integers 1, 2, or 3 it will bump the latest
            relevant TF version:

            *   `0` or `latest`: overwrite the latest version
            *   `1` will bump the major version
            *   `2` will bump the intermediate version
            *   `3` will bump the minor version
            *   everything else is an explicit version

            Otherwise, the value is taken as the exact version name.

        verbose: integer, optional -1
            Produce no (-1), some (0) or many (1) progress and reporting messages

        """
        super().__init__("pagexml")
        if self.importOK(hint=True):
            pagexml = self.importGet()
            self.parsePage = pagexml.parse_pagexml_file
        else:
            return

        self.good = True
        self.verbose = verbose
        self.chosenDoc = doc

        (backend, org, repo, relative) = getLocation(targetDir=ex(repoDir))

        if any(s is None for s in (backend, org, repo, relative)):
            console(
                (
                    "Not working in a repo: "
                    f"backend={backend} org={org} repo={repo} relative={relative}"
                ),
                error=True
            )
            self.good = False
            return

        if verbose == 1:
            console(
                f"Working in repository {org}/{repo}{relative} in back-end {backend}"
            )

        base = ex(f"~/{backend}")
        repoDir = f"{base}/{org}/{repo}"
        refDir = f"{repoDir}{relative}"
        convertSpec = f"{refDir}/pagexml.yaml"

        settings = readYaml(asFile=convertSpec, plain=False)

        self.settings = settings

        appDir = f"{refDir}/app"
        metaDir = f"{refDir}/meta"
        tfDir = f"{refDir}/tf"
        tfVersionFile = f"{refDir}/tfVersions.txt"

        sourceVersions = sorted(dirContents(metaDir)[1], key=versionSort)
        nSourceVersions = len(sourceVersions)

        if source in {"latest", "", "0", 0} or str(source).lstrip("-").isdecimal():
            sourceIndex = (0 if source == "latest" else int(source)) - 1

            try:
                sourceVersion = sourceVersions[sourceIndex]
            except Exception:
                absIndex = sourceIndex + (nSourceVersions if sourceIndex < 0 else 0) + 1
                console(
                    (
                        f"no item in {absIndex} in {nSourceVersions} source versions "
                        f"in {ux(metaDir)}"
                    )
                    if len(sourceVersions)
                    else f"no source versions in {ux(metaDir)}",
                    error=True,
                )
                self.good = False
                return
        else:
            sourceVersion = source

        metaPath = f"{metaDir}/{sourceVersion}"

        if not dirExists(metaPath):
            console(
                f"source version {sourceVersion} does not exists in {ux(metaDir)}",
                error=True,
            )
            self.good = False
            return

        sourceStatuses = {tv: i for (i, tv) in enumerate(reversed(sourceVersions))}
        sourceStatus = sourceStatuses[sourceVersion]
        sourceStatusRep = (
            "most recent"
            if sourceStatus == 0
            else "previous"
            if sourceStatus == 1
            else f"{sourceStatus - 1} before previous"
        )
        if sourceStatus == len(sourceVersions) - 1 and len(sourceVersions) > 1:
            sourceStatusRep = "oldest"

        if verbose >= 0:
            console(f"PageXML data version is {sourceVersion} ({sourceStatusRep})")

        if fileExists(tfVersionFile):
            with fileOpen(tfVersionFile) as fh:
                latestTfVersion = fh.read().strip() or "0.0.0"
        else:
            latestTfVersion = "0.0.0"
            with fileOpen(tfVersionFile, mode="w") as fh:
                fh.write(latestTfVersion)

        writeVersion = False

        if tf in {"latest", "", "0", 0}:
            tfVersion = latestTfVersion
            vRep = "latest"
        elif tf in {"1", "2", "3", 1, 2, 3}:
            bump = int(tf)
            parts = latestTfVersion.split(".")

            def getVer(b):
                return int(parts[b])

            def setVer(b, val):
                parts[b] = val

            if bump > len(parts):
                console(
                    f"Cannot bump part {bump} of latest TF version {latestTfVersion}",
                    error=True,
                )
                self.good = False
                return
            else:
                b1 = bump - 1
                old = getVer(b1)
                setVer(b1, old + 1)
                for b in range(b1 + 1, len(parts)):
                    setVer(b, 0)
                tfVersion = ".".join(str(p) for p in parts)
                vRep = (
                    "major" if bump == 1 else "intermediate" if bump == 2 else "minor"
                )
                vRep = f"next {vRep}"
                writeVersion = True
        else:
            tfVersion = tf
            status = "existing" if dirExists(f"{tfDir}/{tfVersion}") else "new"
            vRep = f"explicit {status}"
            writeVersion = True

        if writeVersion:
            with fileOpen(tfVersionFile, mode="w") as fh:
                fh.write(tfVersion)

        if verbose >= 0:
            console(f"TF data version is {tfVersion} ({vRep})")

        self.refDir = refDir
        self.sourceVersion = sourceVersion
        self.sourceDir = ex(sourceDir)
        self.tfVersion = tfVersion
        self.tfDir = tfDir
        self.appDir = appDir
        self.backend = backend
        self.org = org
        self.repo = repo
        self.relative = relative

        myDir = dirNm(abspath(__file__))
        self.myDir = myDir
        self.slotType = TOKEN

        levelNames = ("doc", "page", "line")
        sectionFeatures = ",".join(levelNames)
        sectionTypes = ",".join(levelNames)

        textFeatures = "{str}{after}"
        rawTextFeatures = "{rstr/str}{rafter/after}"
        otext = {
            "fmt:text-orig-full": rawTextFeatures,
            "fmt:text-logic-full": textFeatures,
            "sectionFeatures": sectionFeatures,
            "sectionTypes": sectionTypes,
        }
        self.otext = otext

        self.generic = dict(
            project="TransLatin",
            conversion="KNAW/HuC TeamText",
            conversionTF="Dirk Roorda",
        )

        featureMeta = dict(
            id=dict(description="the id of the corresponding pagexml object"),
            x=dict(description="the leftmost x coordinate of the pagexml object"),
            y=dict(description="the lowest y coordinate of the pagexml object"),
            w=dict(description="the width of the pagexml object"),
            h=dict(description="the height of the pagexml object"),
            rstr=dict(
                description=(
                    "the physical text of a token, "
                    "if it is different from the logical text"
                ),
            ),
            str=dict(description="the logical text of a token"),
            rafter=dict(
                description=(
                    "the physical text after a token till the next token, "
                    "if it is different from the logical after-text"
                ),
            ),
            after=dict(
                description=(
                    "the logical text after a token till the next logical token,"
                ),
            ),
            page=dict(description="the number of the page within the document"),
            line=dict(description="the number of the line within the page"),
        )
        self.intFeatures = {"page", "line", "x", "y", "w", "h"}

        customFeatureMeta = settings.featureMeta or {}

        for k, v in customFeatureMeta.items():
            featureMeta[k] = v

        self.featureMeta = featureMeta

    def getDirector(self, doc, docMeta, pageSource, pageFiles):
        """Factory for the director function.

        The `tf.convert.walker` relies on a corpus dependent `director` function
        that walks through the source data and spits out actions that
        produces the TF dataset.

        Also some special additions need to be programmed, such as an extra section
        level, word boundaries, etc.

        We collect all needed data, store it, and define a local director function
        that has access to this data.

        Returns
        -------
        function
            The local director function that has been constructed.
        """
        parsePage = self.parsePage

        def director(cv):
            """Director function.

            Here we program a walk through the PageXML sources.
            At every step of the walk we fire some actions that build TF nodes
            and assign features for them.

            Parameters
            ----------
            cv: object
                The converter object, needed to issue actions.
            """
            featureMeta = self.featureMeta

            cur = {}
            cur[NODE] = {}
            nd = cv.node(DOC)
            cur[NODE][DOC] = nd

            cv.feature(nd, doc=doc, **docMeta)

            cur["hangover"] = None

            for pageFile in pageFiles:
                pagePath = f"{pageSource}/{pageFile}"
                pageNr = int(pageFile.split(".", 1)[0])
                pageDoc = parsePage(pagePath)
                cur["page"] = pageNr
                cur["line"] = 0
                walkObject(cv, cur, pageDoc)

                hangover = cur["hangover"]
                if hangover is not None:
                    diverge(cv, *hangover)

            cv.terminate(nd)

            for fName in featureMeta:
                if not cv.occurs(fName):
                    cv.meta(fName)

        return director

    def getConverter(self, doc):
        """Initializes a converter.

        Returns
        -------
        object
            The `tf.convert.walker.CV` converter object, initialized.
        """
        verbose = self.verbose
        tfDir = self.tfDir
        tfVersion = self.tfVersion

        silent = AUTO if verbose == 1 else TERSE if verbose == 0 else DEEP
        TF = Fabric(locations=f"{tfDir}/{doc}/{tfVersion}", silent=silent)
        return CV(TF, silent=silent)

    def convertTask(self):
        """Implementation of the "convert" task.

        It sets up the `tf.convert.walker` machinery and runs it.

        Returns
        -------
        boolean
            Whether the conversion was successful.
        """
        if not self.importOK():
            return

        if not self.good:
            return

        verbose = self.verbose
        chosenDoc = self.chosenDoc
        slotType = self.slotType
        generic = self.generic
        otext = self.otext
        featureMeta = self.featureMeta
        intFeatures = self.intFeatures
        sourceDir = self.sourceDir
        sourceVersion = self.sourceVersion
        tfDir = self.tfDir
        tfVersion = self.tfVersion

        if verbose == 1:
            console(
                f"PageXML to TF converting: {ux(sourceDir)}/Mxx/{sourceVersion}"
                f" ==> {ux(tfDir)}/Mxx/{tfVersion}"
            )

        initTree(tfDir, fresh=True, gentle=True)

        docDirs = sorted(dirContents(sourceDir)[1], key=lambda x: (x[0], int(x[1:])))

        for doc in docDirs:
            if chosenDoc is not None and chosenDoc != doc:
                continue
            pageSource = f"{sourceDir}/{doc}/{sourceVersion}/page"
            pageFiles = sorted(dirContents(pageSource)[0])

            if len(pageFiles) == 0:
                continue

            console(f"\t\t{doc:>5} ... {len(pageFiles):>8} pages")

            metaFile = f"{sourceDir}/{doc}/{sourceVersion}/meta/metadata.yaml"
            docMeta = readYaml(asFile=metaFile)
            docMeta.title = (docMeta.title or "").replace("_", " ")
            docMeta.url = (docMeta.url or "").replace("&amp;", "&")

            cv = self.getConverter(doc)

            if not cv.walk(
                self.getDirector(doc, docMeta, pageSource, pageFiles),
                slotType,
                otext=otext,
                generic=generic,
                intFeatures=intFeatures,
                featureMeta=featureMeta,
                generateTf=True,
            ):
                self.good = False

    def loadTask(self):
        """Implementation of the "load" task.

        It loads the TF data that resides in the directory where the "convert" task
        deliver its results.

        During loading there are additional checks. If they succeed, we have evidence
        that we have a valid TF dataset.

        Also, during the first load intensive pre-computation of TF data takes place,
        the results of which will be cached in the invisible `.tf` directory there.

        That makes the TF data ready to be loaded fast, next time it is needed.

        Returns
        -------
        boolean
            Whether the loading was successful.
        """
        if not self.importOK():
            return

        if not self.good:
            return

        tfDir = self.tfDir
        tfVersion = self.tfVersion
        chosenDoc = self.chosenDoc
        verbose = self.verbose
        silent = AUTO if verbose == 1 else TERSE if verbose == 0 else DEEP

        if not dirExists(tfDir):
            console(f"Directory {ux(tfDir)} does not exist.")
            console("No TF found, nothing to load")
            self.good = False
            return

        docDirs = sorted(dirContents(tfDir)[1], key=lambda x: (x[0], int(x[1:])))

        for doc in docDirs:
            if chosenDoc is not None and chosenDoc != doc:
                continue
            tfPath = f"{tfDir}/{doc}/{tfVersion}"
            msg = f"\t\t{doc:>5} ... "
            TF = Fabric(locations=[tfPath], silent=silent)
            allFeatures = TF.explore(silent=True, show=True)
            loadableFeatures = allFeatures["nodes"] + allFeatures["edges"]
            api = TF.load(loadableFeatures, silent=silent)
            if api:
                if not silent:
                    console(f"{msg}{api.F.otype.maxSlot:>8} slots")
                self.good = True
            else:
                console(f"{msg}XX", error=True)
                self.good = False

    def appTask(self):
        """Implementation of the "app" task.

        It creates / updates a corpus-specific app plus specific documentation files.
        There should be a valid TF dataset in place, because some
        settings in the app derive from it.

        It will also read custom additions that are present in the target app directory.
        These files are:

        *   `about_custom.md`:
            A markdown file with specific colophon information about the dataset.
            In the generated file, this information will be put at the start.
        *   `transcription_custom.md`:
            A markdown file with specific encoding information about the dataset.
            In the generated file, this information will be put at the start.
        *   `config_custom.yaml`:
            A YAML file with configuration data that will be *merged* into the generated
            config.yaml.
        *   `app_custom.py`:
            A python file with named snippets of code to be inserted
            at corresponding places in the generated `app.py`
        *   `display_custom.css`:
            Additional CSS definitions that will be appended to the generated
            `display.css`.

        If the TF app for this resource needs custom code, this is the way to retain
        that code between automatic generation of files.

        Returns
        -------
        boolean
            Whether the operation was successful.
        """
        if not self.importOK():
            return

        if not self.good:
            return

        verbose = self.verbose

        refDir = self.refDir
        myDir = self.myDir
        tfVersion = self.tfVersion

        # key | parentDir | file | file-default | template based

        # if parentDir is a tuple, the first part is the parentDir of the source
        # end the second part is the parentDir of the destination

        itemSpecs = (("config", "app", "config.yaml", "config2.yaml", False),)
        genTasks = {
            s[0]: dict(parentDir=s[1], file=s[2], fileOrig=s[3], justCopy=s[4])
            for s in itemSpecs
        }

        version = tfVersion

        def createConfig(sourceText, customText):
            text = sourceText.replace("«version»", f'"{version}"')

            settings = readYaml(text=text, plain=True)
            settings.setdefault("provenanceSpec", {})["branch"] = BRANCH_DEFAULT_NEW

            customSettings = (
                {} if not customText else readYaml(text=customText, plain=True)
            )

            mergeDict(settings, customSettings)

            text = writeYaml(settings)

            return text

        if verbose >= 0:
            console("App updating ...")

        for name, info in genTasks.items():
            parentDir = info["parentDir"]
            (sourceBit, targetBit) = (
                parentDir if type(parentDir) is tuple else (parentDir, parentDir)
            )
            file = info[FILE]
            fileOrig = info["fileOrig"]
            fileParts = file.rsplit(".", 1)
            if len(fileParts) == 1:
                fileParts = [file, ""]
            (fileBase, fileExt) = fileParts
            if fileExt:
                fileExt = f".{fileExt}"
            targetDir = f"{refDir}/{targetBit}"
            itemTarget = f"{targetDir}/{file}"
            itemCustom = f"{targetDir}/{fileBase}_custom{fileExt}"
            itemPre = f"{targetDir}/{fileBase}_orig{fileExt}"

            justCopy = info["justCopy"]
            sourceDir = f"{myDir}/{sourceBit}"
            itemSource = f"{sourceDir}/{fileOrig}"

            # If there is custom info, we do not have to preserve the previous version.
            # Otherwise we save the target before overwriting it; # unless it
            # has been saved before

            preExists = fileExists(itemPre)
            targetExists = fileExists(itemTarget)
            customExists = fileExists(itemCustom)

            msg = ""

            if justCopy:
                if targetExists:
                    msg = "(already exists, not overwritten)"
                    safe = False
                else:
                    msg = "(copied)"
                    safe = True
            else:
                if targetExists:
                    if customExists:
                        msg = "(generated with custom info)"
                    else:
                        if preExists:
                            msg = "(no custom info, older original exists)"
                        else:
                            msg = "(no custom info, original preserved)"
                            fileCopy(itemTarget, itemPre)
                else:
                    msg = "(created)"

            initTree(targetDir, fresh=False)

            if justCopy:
                if safe:
                    fileCopy(itemSource, itemTarget)
            else:
                if fileExists(itemSource):
                    with fileOpen(itemSource) as fh:
                        sourceText = fh.read()
                else:
                    sourceText = ""

                if fileExists(itemCustom):
                    with fileOpen(itemCustom) as fh:
                        customText = fh.read()
                else:
                    customText = ""

                targetText = (
                    createConfig
                    if name == "config"
                    else fileCopy  # this cannot occur because justCopy is False
                )(sourceText, customText)

                with fileOpen(itemTarget, mode="w") as fh:
                    fh.write(targetText)

            if verbose >= 0:
                console(f"\t{ux(itemTarget):30} {msg}")

        if verbose >= 0:
            console("Done")
        else:
            console("App updated")

    # START the TEXT-FABRIC BROWSER on this CORPUS

    def browseTask(self):
        """Implementation of the "browse" task.

        It gives a shell command to start the TF browser on
        the newly created corpus.
        There should be a valid TF dataset and app configuration in place

        Returns
        -------
        boolean
            Whether the operation was successful.
        """
        if not self.importOK():
            return

        if not self.good:
            return

        org = self.org
        repo = self.repo
        relative = self.relative
        backend = self.backend
        tfVersion = self.tfVersion
        chosenDoc = self.chosenDoc

        if chosenDoc is None:
            console(
                "You have to choose a particular document by passing the doc parameter"
            )
            return

        backendOpt = "" if backend == "github" else f"--backend={backend}"
        versionOpt = f"--version={tfVersion}"
        versionOpt = ""
        docOpt = f"--relative=tf/{chosenDoc}"

        try:
            run(
                (
                    f"tf {org}/{repo}{relative}:clone {docOpt} --checkout=clone "
                    f"{versionOpt} {backendOpt}"
                ),
                shell=True,
            )
        except KeyboardInterrupt:
            pass

    def task(
        self,
        convert=False,
        load=False,
        app=False,
        browse=False,
        verbose=None,
        doc=None,
    ):
        """Carry out any task, possibly modified by any flag.

        This is a higher level function that can execute a selection of tasks.

        The tasks will be executed in a fixed order:
        `convert`, `load`, `app`, `browse`.
        But you can select which one(s) must be executed.

        If multiple tasks must be executed and one fails, the subsequent tasks
        will not be executed.

        Parameters
        ----------
        convert: boolean, optional False
            Whether to carry out the `convert` task.
        load: boolean, optional False
            Whether to carry out the `load` task.
        app: boolean, optional False
            Whether to carry out the `app` task.
        browse: boolean, optional False
            Whether to carry out the `browse` task"
        verbose: integer, optional -1
            Produce no (-1), some (0) or many (1) progress and reporting messages

        Returns
        -------
        boolean
            Whether all tasks have executed successfully.
        """
        if not self.importOK():
            return

        if verbose is not None:
            verboseSav = self.verbose
            self.verbose = verbose

        if doc is not None:
            docSav = self.chosenDoc
            self.chosenDoc = doc

        if not self.good:
            return False

        for condition, method, kwargs in (
            (convert, self.convertTask, {}),
            (load, self.loadTask, {}),
            (app, self.appTask, {}),
            (browse, self.browseTask, {}),
        ):
            if condition:
                method(**kwargs)
                if not self.good:
                    break

        if verbose is not None:
            self.verbose = verboseSav
        if doc is not None:
            self.chosenDoc = docSav
        return self.good


def main():
    (good, tasks, params, flags) = readArgs(
        "pagexml", HELP, TASKS, PARAMS, FLAGS, notInAll=TASKS_EXCLUDED
    )
    if not good:
        return False

    Obj = PageXML(**params, **flags)
    Obj.task(**tasks, **flags)

    return Obj.good


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
