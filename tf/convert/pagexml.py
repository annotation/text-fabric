import sys
from subprocess import run

from ..capable import CheckImport
from ..core.command import readArgs
from ..core.files import (
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
    )
    return (helpText, taskSpec, taskExcluded, paramSpec, flagSpec)


(HELP, TASKS, TASKS_EXCLUDED, PARAMS, FLAGS) = setUp()


class PageXML(CheckImport):
    def __init__(
        self,
        repoDir,
        source=PARAMS["source"][1],
        tf=PARAMS["tf"][1],
        verbose=FLAGS["verbose"][1],
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

        ## Input directories

        ### `source`

        *Location of the PageXML sources.*

        **If it does not exist, the program aborts with an error.**

        Several levels of subdirectories are assumed:

        1.  the version of the source (this could be a date string).
        1.  below the version are directories:
            * `image`: contain the scan images
            * `meta`: contain metadata files
            * `page`: contain the PageXML files

            The files in `image` and `scan` have names that consist of a 4-digit
            number with leading zeros, and any two files with the same name in
            `page` and `image` represent the same document.

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
            global parsePage
            pagexml = self.importGet()
            parsePage = pagexml.parse_pagexml_file
        else:
            return

        self.good = True
        self.verbose = verbose

        (backend, org, repo, relative) = getLocation(targetDir=ex(repoDir))

        if any(s is None for s in (backend, org, repo, relative)):
            console(
                "Not working in a repo: "
                f"backend={backend} org={org} repo={repo} relative={relative}"
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

        settings = readYaml(asFile=convertSpec, plain=True)

        self.settings = settings

        appDir = f"{refDir}/app"
        sourceDir = f"{refDir}/source"
        tfDir = f"{refDir}/tf"

        sourceVersions = sorted(dirContents(sourceDir)[1], key=versionSort)
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
                        f"in {ux(sourceDir)}"
                    )
                    if len(sourceVersions)
                    else f"no source versions in {ux(sourceDir)}",
                    error=True,
                )
                self.good = False
                return
        else:
            sourceVersion = source

        sourcePath = f"{sourceDir}/{sourceVersion}"

        if not dirExists(sourcePath):
            console(
                f"source version {sourceVersion} does not exists in {ux(sourceDir)}",
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
            console(f"TEI data version is {sourceVersion} ({sourceStatusRep})")

        tfVersions = sorted(dirContents(tfDir)[1], key=versionSort)

        latestTfVersion = tfVersions[-1] if len(tfVersions) else "0.0.0"
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
        else:
            tfVersion = tf
            status = "existing" if dirExists(f"{tfDir}/{tfVersion}") else "new"
            vRep = f"explicit {status}"

        tfPath = f"{tfDir}/{tfVersion}"

        if verbose >= 0:
            console(f"TF data version is {tfVersion} ({vRep})")

        self.refDir = refDir
        self.sourceVersion = sourceVersion
        self.sourcePath = sourcePath
        self.tfVersion = tfVersion
        self.tfPath = tfPath
        self.tfDir = tfDir
        self.appDir = appDir
        self.backend = backend
        self.org = org
        self.repo = repo
        self.relative = relative

        myDir = dirNm(abspath(__file__))
        self.myDir = myDir

        metaFile = f"{sourcePath}/meta/metadata.yaml"
        self.slotType = TOKEN

        self.generic = readYaml(asFile=metaFile, plain=True)

        levelNames = ("doc", "page", "line")
        sectionFeatures = ",".join(levelNames)
        sectionTypes = ",".join(levelNames)

        textFeatures = "{str}{after}"
        otext = {
            "fmt:text-orig-full": textFeatures,
            "sectionFeatures": sectionFeatures,
            "sectionTypes": sectionTypes,
        }
        self.otext = otext

        featureMeta = dict(
            id=dict(
                description="the id of the corresponding pagexml object",
            ),
            x=dict(
                description="the leftmost x coordinate of the pagexml object",
            ),
            y=dict(
                description="the lowest y coordinate of the pagexml object",
            ),
            w=dict(
                description="the width of the pagexml object",
            ),
            h=dict(
                description="the height of the pagexml object",
            ),
            str=dict(
                description="the text of a word or token",
            ),
            after=dict(
                description="the text after a word till the next word",
            ),
            doc=dict(
                description="the name of the document",
            ),
            page=dict(
                description="the number of the page within the document",
            ),
            line=dict(
                description="the number of the line within the page",
            ),
        )
        intFeatures = {"page", "line", "x", "y", "w", "h"}

        self.featureMeta = featureMeta
        self.intFeatures = intFeatures

    def getConverter(self):
        """Initializes a converter.

        Returns
        -------
        object
            The `tf.convert.walker.CV` converter object, initialized.
        """
        verbose = self.verbose
        tfPath = self.tfPath

        silent = AUTO if verbose == 1 else TERSE if verbose == 0 else DEEP
        TF = Fabric(locations=tfPath, silent=silent)
        return CV(TF, silent=silent)

    def getDirector(self):
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
        repo = self.repo
        sourcePath = self.sourcePath
        pageSource = f"{sourcePath}/page"
        pageFiles = sorted(dirContents(pageSource)[0])

        if not self.importOK():
            return

        if not self.good:
            return

        # WALKERS

        def emptySlot(cv):
            s = cv.slot()
            cv.feature(s, str="", after="")

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
            nTp = PAGE if isScan else REGION if tp == "text_region" else tp
            nd = cv.node(nTp)
            cur[NODE][nTp] = nd
            cv.feature(nd, id=xId, x=box.x, y=box.y, w=box.w, h=box.h)

            if isScan:
                cv.feature(nd, page=cur["page"])

            if tp == LINE:
                tokens = tokenize(xObj.text or "")
                for tx, sp in tokens:
                    s = cv.slot()
                    cv.feature(s, str=tx, after=sp)
                if len(tokens) == 0:
                    emptySlot(cv)

                cur["line"] += 1
                cv.feature(nd, line=cur["line"])

            elif tp in {"scan", "text_region"}:
                for yObj in xObj.get_text_regions_in_reading_order():
                    walkObject(cv, cur, yObj)
                for yObj in xObj.lines:
                    walkObject(cv, cur, yObj)
            else:
                console(f"UNKNOWN TYPE {tp}", error=True)
                self.good = False

            if not cv.linked(nd):
                emptySlot(cv)
            cv.terminate(nd)

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
            cur = {}
            cur[NODE] = {}
            nd = cv.node(DOC)
            cur[NODE][DOC] = nd
            cv.feature(nd, doc=repo)

            for pageFile in pageFiles:
                pagePath = f"{pageSource}/{pageFile}"
                pageDoc = parsePage(pagePath)
                cur["page"] = int(pageFile.split(".", 1)[0])
                cur["line"] = 0
                walkObject(cv, cur, pageDoc)

            cv.terminate(nd)

        return director

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
        slotType = self.slotType
        generic = self.generic
        otext = self.otext
        featureMeta = self.featureMeta
        intFeatures = self.intFeatures

        tfPath = self.tfPath
        sourcePath = self.sourcePath

        if verbose == 1:
            console(f"PageXML to TF converting: {ux(sourcePath)} => {ux(tfPath)}")

        initTree(tfPath, fresh=True, gentle=True)

        cv = self.getConverter()

        self.good = cv.walk(
            self.getDirector(),
            slotType,
            otext=otext,
            generic=generic,
            intFeatures=intFeatures,
            featureMeta=featureMeta,
            generateTf=True,
        )

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

        tfPath = self.tfPath
        verbose = self.verbose
        silent = AUTO if verbose == 1 else TERSE if verbose == 0 else DEEP

        if not dirExists(tfPath):
            console(f"Directory {ux(tfPath)} does not exist.")
            console("No TF found, nothing to load")
            self.good = False
            return

        TF = Fabric(locations=[tfPath], silent=silent)
        allFeatures = TF.explore(silent=True, show=True)
        loadableFeatures = allFeatures["nodes"] + allFeatures["edges"]
        api = TF.load(loadableFeatures, silent=silent)
        if api:
            if verbose >= 0:
                console(f"max node = {api.F.otype.maxNode}")
            self.good = True
            return

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
                    with open(itemSource, encoding="utf8") as fh:
                        sourceText = fh.read()
                else:
                    sourceText = ""

                if fileExists(itemCustom):
                    with open(itemCustom, encoding="utf8") as fh:
                        customText = fh.read()
                else:
                    customText = ""

                targetText = (
                    createConfig
                    if name == "config"
                    else fileCopy  # this cannot occur because justCopy is False
                )(sourceText, customText)

                with open(itemTarget, "w", encoding="utf8") as fh:
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

        backendOpt = "" if backend == "github" else f"--backend={backend}"
        versionOpt = f"--version={tfVersion}"
        versionOpt = ""
        try:
            run(
                (
                    f"tf {org}/{repo}{relative}:clone --checkout=clone "
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
