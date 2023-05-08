"""
# XML import

You can convert any XML source into TF by specifying a few details about the source.

Text-Fabric then invokes the `tf.convert.walker` machinery to produce a Text-Fabric
dataset out of the source.

The converter goes one extra mile: it generates a TF-app, in such a way that
the Text-Fabric browser is instantly usable.

!!! caution "As an example"
    This is more intended as an example of how to tackle the conversion
    of XML to TF than as a production engine.
    Most XML corpora use elements for special things, and a good conversion
    to TF should deal with the intention behind the elements.

    See `tf.convert.tei` for a production converter of TEI XML to TF.

## Whitespace

This converter does not read schemas and has no extra knowledge about the elements.

Becasue of the lack of schema information we do not know exactly which white-space
is significant. The only thing we do to whitespace is to condense each stretch
of whitespace to a single space.

Whether some of these spaces around tags must be ignored is a matter of further
customization.

# Configuration

We assume that you have a `programs` directory at the top-level of your repo.
In this directory we'll look for two optional files:

*   a file `xml.yaml` in which you specify a bunch of values
    Last, but not least, you can assemble all the input parameters needed to
    get the conversion off the ground.

*   a file `xml.py` in which you define a function `transform(text)` which
    takes a text string ar argument and delivers a text string as result.
    The converter will call this on every XML input file it reads *before*
    feeding it to the XML parser.


## Keys and values of the `xml.yaml` file

### generic

dict, optional `{}`

Metadata for all generated TF features.
The actual source version of the XML files does not have to be stated here,
it will be inserted based on the version that the converter will actually use.
That version depends on the `xml` argument passed to the program.
The key under which the source version will be inserted is `xmlVersion`.

# Usage

## Commandline

```sh
tf-fromxml tasks flags
```

## From Python

```python
from tf.convert.xml import XML

X = XML()
X.task(**tasks, **flags)
```

For a short overview the tasks and flags, see `HELP`.

## Tasks

We have the following conversion tasks:

1.  `check`: makes and inventory of all XML elements and attributes used.
1.  `convert`: produces actual TF files by converting XML files.
1.  `load`: loads the generated TF for the first time, by which the precomputation
    step is triggered. During precomputation some checks are performed. Once this
    has succeeded, we have a workable Text-Fabric dataset.
1.  `app`: creates or updates a corpus specific TF-app with minimal sensible settings.
1.  `browse`: starts the text-fabric browser on the newly created dataset.

Tasks can be run by passing any choice of task keywords to the
`XML.task()` method.

## Note on versions

The XML source files come in versions, indicated with a data.
The converter picks the most recent one, unless you specify an other one:

```python
tf-fromxml xml=-2  # previous version
tf-fromxml xml=0  # first version
tf-fromxml xml=3  # third version
tf-fromxml xml=2019-12-23  # explicit version
```

The resulting TF data is independently versioned, like `1.2.3`.
When the converter runs, by default it overwrites the most recent version,
unless you specify another one.

It looks at the latest version and then bumps a part of the version number.

```python
tf-fromxml tf=3  # minor version, 1.2.3 becomes 1.2.4
tf-fromxml tf=2  # intermediate version, 1.2.3 becomes 1.3.0
tf-fromxml tf=1  # major version, 1.2.3 becomes 2.0.0
tf-fromxml tf=1.8.3  # explicit version
```

## Examples

Exactly how you can call the methods of this module and add your own customised
conversion code is demonstrated in the Greek New Testament:

*   [Nestle1904](https://nbviewer.org/github/ETCBC/nestle1904/blob/master/programs/tfFromLowfat.ipynb).
"""

import sys
import collections
import re
from subprocess import run
from importlib import util

import yaml
from lxml import etree
from .helpers import setUp, FILE
from .xmlCustom import convertTaskDefault
from ..parameters import BRANCH_DEFAULT_NEW
from ..fabric import Fabric
from ..core.helpers import console, versionSort
from ..convert.walker import CV
from ..core.timestamp import AUTO, DEEP, TERSE
from ..core.text import DEFAULT_FORMAT
from ..core.command import readArgs
from ..core.helpers import mergeDict
from ..core.files import (
    abspath,
    expanduser as ex,
    unexpanduser as ux,
    getLocation,
    initTree,
    dirNm,
    dirExists,
    dirContents,
    fileExists,
    fileCopy,
    fileRemove,
    scanDir,
)

(HELP, TASKS, TASKS_EXCLUDED, PARAMS, FLAGS) = setUp("XML")


class XML:
    def __init__(
        self,
        convertTaskCustom=None,
        xml=PARAMS["xml"][1],
        tf=PARAMS["tf"][1],
        verbose=FLAGS["verbose"][1],
    ):
        """Converts XML to TF.

        For documentation of the resulting encoding, read the
        [transcription template](https://github.com/annotation/text-fabric/blob/master/tf/convert/app/transcription.md).

        Below we describe how to control the conversion machinery.

        We adopt a fair bit of "convention over configuration" here, in order to lessen
        the burden for the user of specifying so many details.

        Based on current directory from where the script is called,
        it defines all the ingredients to carry out
        a `tf.convert.walker` conversion of the XML input.

        This function is assumed to work in the context of a repository,
        i.e. a directory on your computer relative to which the input directory exists,
        and various output directories: `tf`, `app`.

        Your current directory must be at

        ```
        ~/backend/org/repo/relative
        ```

        where

        *   `~` is your home directory;
        *   `backend` is an online *backend* name,
            like `github`, `gitlab`, `git.huc.knaw.nl`;
        *   `org` is an organisation, person, or group in the backend;
        *   `repo` is a repository in the `org`.
        *   `relative` is a directory path within the repo (0 or more components)

        This is only about the directory structure on your local computer;
        it is not required that you have online incarnations of your repository
        in that backend.
        Even your local repository does not have to be a git repository.

        The only thing that matters is that the full path to your repo can be parsed
        as a sequence of *home*/*backend*/*org*/*repo*/*relative*.

        Relative to this directory the program expects and creates
        input/output directories.

        ## Input directories

        ### `xml`

        *Location of the XML sources.*

        **If it does not exist, the program aborts with an error.**

        Several levels of subfolders are assumed:

        1.  the version of the source (this could be a date string).
        2.  volumes/collections of documents. The subfolder `__ignore__` is ignored.
        3.  the XML documents themselves.

        ## Output directories

        ### `report`

        Directory to write the results of the `check` task to: an inventory
        of elements/attributes encountered.
        If the directory does not exist, it will be created.
        The default value is `.` (i.e. the current directory in which
        the script is invoked).

        ### `tf`

        The directory under which the text-fabric output file (with extension `.tf`)
        are placed.
        If it does not exist, it will be created.
        The tf files will be generated in a folder named by a version number,
        passed as `tfVersion`.

        ### `app`

        Location of additional TF-app configuration files.
        If they do not exist, they will be created with some sensible default
        settings and generated documentation.
        These settings can be overriden in the `app/config_custom.yaml` file.
        Also a default `display.css` file and a logo are added.

        Custom content for these files can be provided in files
        with `_custom` appended to their base name.

        Parameters
        ----------
        convertTaskCustom: function, optional None
            You can pass a replacement for the `convertTask` method.
            If you do that, it will be used instead.
            By means of this approach you can use the generic machinery of the
            xml convertor as much as possible, and you only have to adpat the bits
            that process the XML sources.
        xml: string, optional ""
            If empty, use the latest version under the `xml` directory with sources.
            Otherwise it should be a valid integer, and it is the index in the
            sorted list of versions there.

            *   `0` or `latest`: latest version;
            *   `-1`, `-2`, ... : previous version, version before previous, ...;
            *   `1`, `2`, ...: first version, second version, ....
            *   everything else that is not a number is an explicit version

            If the value cannot be parsed as an integer, it is used as the exact
            version name.

        tf: string, optional ""
            If empty, the tf version used will be the latest one under the `tf`
            directory.

            If it can be parsed as the integers 1, 2, or 3 it will bump the latest
            relevant tf version:

            *   `0` or `latest`: overwrite the latest version
            *   `1` will bump the major version
            *   `2` will bump the intermediate version
            *   `3` will bump the minor version
            *   everything else is an explicit version

            Otherwise, the value is taken as the exact version name.

        verbose: integer, optional -1
            Produce no (-1), some (0) or many (1) orprogress and reporting messages
        """
        self.good = True
        self.convertTaskCustom = convertTaskCustom

        (backend, org, repo, relative) = getLocation()
        if any(s is None for s in (backend, org, repo, relative)):
            console(
                "Not working in a repo: "
                f"backend={backend} org={org} repo={repo} relative={relative}"
            )
            self.good = False
            return

        if verbose == 1:
            console(
                f"Working in repository {org}/{repo}{relative} in backend {backend}"
            )

        base = ex(f"~/{backend}")
        repoDir = f"{base}/{org}/{repo}"
        refDir = f"{repoDir}{relative}"
        programDir = f"{refDir}/programs"
        convertSpec = f"{programDir}/xml.yaml"
        convertCustom = f"{programDir}/xml.py"

        settings = {}
        if fileExists(convertSpec):
            with open(convertSpec, encoding="utf8") as fh:
                text = fh.read()
            settings = yaml.load(text, Loader=yaml.FullLoader)

        self.transform = None
        if fileExists(convertCustom):
            try:
                spec = util.spec_from_file_location("xmlcustom", convertCustom)
                code = util.module_from_spec(spec)
                sys.path.insert(0, dirNm(convertCustom))
                spec.loader.exec_module(code)
                sys.path.pop(0)
                self.transform = code.transform
            except Exception as e:
                print(str(e))
                self.transform = None

        generic = settings.get("generic", {})
        self.generic = generic

        reportDir = f"{refDir}/report"
        appDir = f"{refDir}/app"
        xmlDir = f"{refDir}/xml"
        tfDir = f"{refDir}/tf"

        xmlVersions = sorted(dirContents(xmlDir)[1], key=versionSort)
        nXmlVersions = len(xmlVersions)

        if xml in {"latest", "", "0", 0} or str(xml).lstrip("-").isdecimal():
            xmlIndex = (0 if xml == "latest" else int(xml)) - 1

            try:
                xmlVersion = xmlVersions[xmlIndex]
            except Exception:
                absIndex = xmlIndex + (nXmlVersions if xmlIndex < 0 else 0) + 1
                console(
                    (
                        f"no item in {absIndex} in {nXmlVersions} source versions "
                        f"in {ux(xmlDir)}"
                    )
                    if len(xmlVersions)
                    else f"no source versions in {ux(xmlDir)}",
                    error=True,
                )
                self.good = False
                return
        else:
            xmlVersion = xml

        xmlPath = f"{xmlDir}/{xmlVersion}"
        reportPath = f"{reportDir}/{xmlVersion}"

        if not dirExists(xmlPath):
            console(
                f"source version {xmlVersion} does not exists in {ux(xmlDir)}",
                error=True,
            )
            self.good = False
            return

        xmlStatuses = {tv: i for (i, tv) in enumerate(reversed(xmlVersions))}
        xmlStatus = xmlStatuses[xmlVersion]
        xmlStatusRep = (
            "most recent"
            if xmlStatus == 0
            else "previous"
            if xmlStatus == 1
            else f"{xmlStatus - 1} before previous"
        )
        if xmlStatus == len(xmlVersions) - 1 and len(xmlVersions) > 1:
            xmlStatusRep = "oldest"

        if verbose >= 0:
            console(f"XML data version is {xmlVersion} ({xmlStatusRep})")

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
            status = "exising" if dirExists(f"{tfDir}/{tfVersion}") else "new"
            vRep = f"explicit {status}"

        tfPath = f"{tfDir}/{tfVersion}"

        if verbose >= 0:
            console(f"TF data version is {tfVersion} ({vRep})")

        self.refDir = refDir
        self.xmlVersion = xmlVersion
        self.xmlPath = xmlPath
        self.tfVersion = tfVersion
        self.tfPath = tfPath
        self.reportPath = reportPath
        self.tfDir = tfDir
        self.appDir = appDir
        self.backend = backend
        self.org = org
        self.repo = repo
        self.relative = relative

        self.verbose = verbose
        myDir = dirNm(abspath(__file__))
        self.myDir = myDir

    @staticmethod
    def getParser():
        """Configure the lxml parser.

        See [parser options](https://lxml.de/parsing.html#parser-options).

        Returns
        -------
        object
            A configured lxml parse object.
        """
        return etree.XMLParser(
            remove_blank_text=False,
            collect_ids=False,
            remove_comments=True,
            remove_pis=True,
            huge_tree=True,
        )

    def getXML(self):
        """Make an inventory of the XML source files.

        Returns
        -------
        tuple of tuple | string
            The outer tuple has sorted entries corresponding to folders under the
            XML input directory.
            Each such entry consists of the folder name and an inner tuple
            that contains the file names in that folder, sorted.
        """
        xmlPath = self.xmlPath

        IGNORE = "__ignore__"

        xmlFilesRaw = collections.defaultdict(list)

        with scanDir(xmlPath) as dh:
            for folder in dh:
                folderName = folder.name
                if folderName == IGNORE:
                    continue
                if not folder.is_dir():
                    continue
                with scanDir(f"{xmlPath}/{folderName}") as fh:
                    for file in fh:
                        fileName = file.name
                        if not (fileName.lower().endswith(".xml") and file.is_file()):
                            continue
                        xmlFilesRaw[folderName].append(fileName)

        xmlFiles = tuple(
            (folderName, tuple(sorted(fileNames)))
            for (folderName, fileNames) in sorted(xmlFilesRaw.items())
        )
        return xmlFiles

    def checkTask(self):
        """Implementation of the "check" task.

        Then it makes an inventory of all elements and attributes in the XML files.

        If tags are used in multiple namespaces, it will be reported.

        !!! caution "Conflation of namespaces"
            The XML to TF conversion does construct node types and attributes
            without taking namespaces into account.
            However, the parsing process is namespace aware.

        The inventory lists all elements and attributes, and many attribute values.
        But is represents any digit with `n`, and some attributes that contain
        ids or keywords, are reduced to the value `x`.

        This information reduction helps to get a clear overview.

        It writes reports to the `reportPath`:

        *   `errors.txt`: validation errors
        *   `elements.txt`: element/attribute inventory.
        """
        if not self.good:
            return

        verbose = self.verbose

        xmlPath = self.xmlPath
        reportPath = self.reportPath

        if verbose == 1:
            console(f"XML to TF checking: {ux(xmlPath)} => {ux(reportPath)}")

        kindLabels = dict(
            rest="Remaining Attributes and Elements",
        )
        getStore = lambda: collections.defaultdict(  # noqa: E731
            lambda: collections.defaultdict(collections.Counter)
        )
        analysis = {x: getStore() for x in kindLabels}
        errors = []
        tagByNs = collections.defaultdict(collections.Counter)

        parser = self.getParser()

        initTree(reportPath)

        def analyse(root, analysis):
            TRIM_ATTS = set(
                """
                id
                key
                target
                value
            """.strip().split()
            )

            NUM_RE = re.compile(r"""[0-9]""", re.S)

            def nodeInfo(node):
                qName = etree.QName(node.tag)
                tag = qName.localname
                ns = qName.namespace
                atts = node.attrib

                tagByNs[tag][ns] += 1

                if len(atts) == 0:
                    kind = "rest"
                    analysis[kind][tag][""][""] += 1
                else:
                    for (kOrig, v) in atts.items():
                        k = etree.QName(kOrig).localname
                        kind = "rest"
                        dest = analysis[kind]

                        if kind == "rest":
                            vTrim = "X" if k in TRIM_ATTS else NUM_RE.sub("N", v)
                            dest[tag][k][vTrim] += 1
                        else:
                            words = v.strip().split()
                            for w in words:
                                dest[tag][k][w.strip()] += 1

                for child in node.iterchildren(tag=etree.Element):
                    nodeInfo(child)

            nodeInfo(root)

        def writeErrors():
            errorFile = f"{reportPath}/errors.txt"

            nErrors = 0

            with open(errorFile, "w", encoding="utf8") as fh:
                for (xmlFile, lines) in errors:
                    fh.write(f"{xmlFile}\n")
                    for line in lines:
                        fh.write(line)
                        nErrors += 1
                    fh.write("\n")

            console(
                f"{nErrors} error(s) in {len(errors)} file(s) written to {errorFile}"
                if verbose >= 0 or nErrors
                else "Validation OK"
            )

        def writeNamespaces():
            errorFile = f"{reportPath}/namespaces.txt"

            nErrors = 0

            nTags = len(tagByNs)

            with open(errorFile, "w", encoding="utf8") as fh:
                for (tag, nsInfo) in sorted(
                    tagByNs.items(), key=lambda x: (-len(x[1]), x[0])
                ):
                    label = "OK"
                    nNs = len(nsInfo)
                    if nNs > 1:
                        nErrors += 1
                        label = "XX"

                    for (ns, amount) in sorted(
                        nsInfo.items(), key=lambda x: (-x[1], x[0])
                    ):
                        fh.write(
                            f"{label} {nNs:>2} namespace for "
                            f"{tag:<16} : {amount:>5}x {ns}\n"
                        )

            console(
                f"{nTags} tags of which {nErrors} with multiple namespaces "
                f"written to {errorFile}"
                if verbose >= 0 or nErrors
                else "Namespaces OK"
            )

        def writeReport():
            reportFile = f"{reportPath}/elements.txt"
            with open(reportFile, "w", encoding="utf8") as fh:
                fh.write(
                    "Inventory of tags and attributes in the source XML file(s).\n"
                    "Contains the following sections:\n"
                )
                for label in kindLabels.values():
                    fh.write(f"\t{label}\n")
                fh.write("\n\n")

                infoLines = 0

                def writeAttInfo(tag, att, attInfo):
                    nonlocal infoLines
                    nl = "" if tag == "" else "\n"
                    tagRep = "" if tag == "" else f"<{tag}>"
                    attRep = "" if att == "" else f"{att}="
                    atts = sorted(attInfo.items())
                    (val, amount) = atts[0]
                    fh.write(
                        f"{nl}\t{tagRep:<18} " f"{attRep:<18} {amount:>5}x {val}\n"
                    )
                    infoLines += 1
                    for (val, amount) in atts[1:]:
                        fh.write(
                            f"""\t{'':<7}{'':<18} {'"':<18} {amount:>5}x {val}\n"""
                        )
                        infoLines += 1

                def writeTagInfo(tag, tagInfo):
                    nonlocal infoLines
                    tags = sorted(tagInfo.items())
                    (att, attInfo) = tags[0]
                    writeAttInfo(tag, att, attInfo)
                    infoLines += 1
                    for (att, attInfo) in tags[1:]:
                        writeAttInfo("", att, attInfo)

                for (kind, label) in kindLabels.items():
                    fh.write(f"\n{label}\n")
                    for (tag, tagInfo) in sorted(analysis[kind].items()):
                        writeTagInfo(tag, tagInfo)

            if verbose >= 0:
                console(f"{infoLines} info line(s) written to {reportFile}")

        def filterError(msg):
            return msg == (
                "Element 'graphic', attribute 'url': [facet 'pattern'] "
                "The value '' is not accepted by the pattern '\\S+'."
            )

        def doXMLFile(xmlPath):
            tree = etree.parse(xmlPath, parser)
            root = tree.getroot()
            analyse(root, analysis)

        i = 0
        for (xmlFolder, xmlFiles) in self.getXML():
            console(f"Start folder {xmlFolder}:")
            for xmlFile in xmlFiles:
                i += 1
                console(f"\r{i:>4} {xmlFile:<50}", newline=False)
                thisXmlPath = f"{xmlPath}/{xmlFolder}/{xmlFile}"
                doXMLFile(thisXmlPath)
            console("")
            console(f"End   folder {xmlFolder}")

        console("")
        writeReport()
        writeErrors()
        writeNamespaces()

    # SET UP CONVERSION

    def convertTask(self):
        """Implementation of the "convert" task.

        It sets up the `tf.convert.walker` machinery and runs it.

        Returns
        -------
        boolean
            Whether the conversion was successful.
        """
        convertTaskCustom = self.convertTaskCustom
        return (convertTaskDefault if convertTaskCustom is None else convertTaskCustom)(
            self
        )

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

    def loadTask(self):
        """Implementation of the "load" task.

        It loads the tf data that resides in the directory where the "convert" task
        deliver its results.

        During loading there are additional checks. If they succeed, we have evidence
        that we have a valid TF dataset.

        Also, during the first load intensive precomputation of TF data takes place,
        the results of which will be cached in the invisible `.tf` directory there.

        That makes the TF data ready to be loaded fast, next time it is needed.

        Returns
        -------
        boolean
            Whether the loading was successful.
        """
        if not self.good:
            return

        tfPath = self.tfPath
        verbose = self.verbose
        silent = AUTO if verbose == 1 else TERSE if verbose == 0 else DEEP

        if not dirExists(tfPath):
            console(f"Directory {ux(tfPath)} does not exist.")
            console("No tf found, nothing to load")
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

    # APP CREATION/UPDATING

    def appTask(self, tokenBased=False):
        """Implementation of the "app" task.

        It creates/updates a corpus-specific app.
        There should be a valid TF dataset in place, because some
        settings in the app derive from it.

        It will also read custom additions that are present in the target app directory.
        These files are:

        *   `config_custom.yaml`:
            A yaml file with config data that will be *merged* into the generated
            config.yaml.
        *   `app_custom.py`:
            A python file with named snippets of code to be inserted
            at corresponding places in the generated `app.py`
        *   `display_custom.css`:
            Additonal css definitions that will be put in place.

        If the TF app for this resource needs custom code, this is the way to retain
        that code between automatic generation of files.

        Returns
        -------
        boolean
            Whether the operation was successful.
        """
        if not self.good:
            return

        verbose = self.verbose

        refDir = self.refDir
        myDir = self.myDir

        # key | parent dir | file | template based

        # if parent dir is a tuple, the first part is the parent of the source
        # end the second part is the parent of the destination

        itemSpecs = (
            ("logo", "app/static", "logo.png", True),
            ("display", "app/static", "display.css", False),
            ("config", "app", "config.yaml", False),
            ("app", "app", "app.py", False),
        )
        genTasks = {
            s[0]: dict(parent=s[1], file=s[2], justCopy=s[3]) for s in itemSpecs
        }

        tfVersion = self.tfVersion
        version = tfVersion

        def createConfig(sourceText, customText):
            text = sourceText.replace("«version»", f'"{version}"')

            settings = yaml.load(text, Loader=yaml.FullLoader)
            settings.setdefault("provenanceSpec", {})["branch"] = BRANCH_DEFAULT_NEW
            dataDisplay = settings.setdefault("dataDisplay", {})
            interfaceDefaults = settings.setdefault("interfaceDefaults", {})
            if "textFormats" in dataDisplay:
                del dataDisplay["textFormats"]
            dataDisplay["textFormat"] = DEFAULT_FORMAT
            interfaceDefaults["fmt"] = DEFAULT_FORMAT

            customSettings = (
                {}
                if customText is None
                else yaml.load(customText, Loader=yaml.FullLoader)
            )

            mergeDict(settings, customSettings)

            text = yaml.dump(settings, allow_unicode=True)

            return text

        def createDisplay(sourceText, customText):
            """Copies the custom display.css file of an TF app."""
            return customText or ""

        def createApp(sourceText, customText):
            """Copies and tweaks the app.py file of an TF app.

            The template app.py provides text formatting functions.
            It retrieves text from features, but that is dependent on
            the settings of the conversion.
            """
            if customText is None:
                return None

            materialCode = '''F.ch.v(n) or ""'''

            code = sourceText.replace("F.matérial", materialCode)
            code = code.replace('"rèndValues"', "{}")

            hookStartRe = re.compile(r"^# DEF (import|init|extra)\s*$", re.S)
            hookEndRe = re.compile(r"^# END DEF\s*$", re.S)
            hookInsertRe = re.compile(r"^# INSERT (import|init|extra)\s*$", re.S)

            custom = {}
            section = None

            for line in (customText or "").split("\n"):
                line = line.rstrip()

                if section is None:
                    match = hookStartRe.match(line)
                    if match:
                        section = match.group(1)
                        custom[section] = []
                else:
                    match = hookEndRe.match(line)
                    if match:
                        section = None
                    else:
                        custom[section].append(line)

            codeLines = []

            for line in code.split("\n"):
                line = line.rstrip()

                match = hookInsertRe.match(line)
                if match:
                    section = match.group(1)
                    codeLines.extend(custom.get(section, []))
                else:
                    codeLines.append(line)

            return "\n".join(codeLines) + "\n"

        if verbose >= 0:
            console("App updating ...")

        for (name, info) in genTasks.items():
            parent = info["parent"]
            (sourceBit, targetBit) = (
                parent if type(parent) is tuple else (parent, parent)
            )
            file = info[FILE]
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
            xmlDir = f"{myDir}/{sourceBit}"
            itemSource = f"{xmlDir}/{file}"

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
                            msg = "(no custom info, older orginal exists)"
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
                    customText = None

                targetText = (
                    createConfig
                    if name == "config"
                    else createApp
                    if name == "app"
                    else createDisplay
                    if name == "display"
                    else fileCopy  # this cannot occur because justCopy is False
                )(sourceText, customText)

                if targetText is None:
                    fileRemove(itemTarget)
                    msg = "(deleted)"
                else:
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

        It gives a shell command to start the text-fabric browser on
        the newly created corpus.
        There should be a valid TF dataset and app configuraiton in place

        Returns
        -------
        boolean
            Whether the operation was successful.
        """
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
                    f"text-fabric {org}/{repo}{relative}:clone --checkout=clone "
                    f"{versionOpt} {backendOpt}"
                ),
                shell=True,
            )
        except KeyboardInterrupt:
            pass

    def task(
        self,
        check=False,
        convert=False,
        load=False,
        app=False,
        browse=False,
        verbose=None,
    ):
        """Carry out any task, possibly modified by any flag.

        This is a higher level function that can execute a selection of tasks.

        The tasks will be executed in a fixed order: check, convert, load, app,
        apptoken, browse.
        But you can select which one(s) must be executed.

        If multiple tasks must be executed and one fails, the subsequent tasks
        will not be executed.

        Parameters
        ----------
        check: boolean, optional False
            Whether to carry out the "check" task.
        convert: boolean, optional False
            Whether to carry out the "convert" task.
        load: boolean, optional False
            Whether to carry out the "load" task.
        app: boolean, optional False
            Whether to carry out the "app" task.
        browse: boolean, optional False
            Whether to carry out the "browse" task"
        verbose: integer, optional -1
            Produce no (-1), some (0) or many (1) orprogress and reporting messages

        Returns
        -------
        boolean
            Whether all tasks have executed successfully.
        """
        if verbose is not None:
            self.verbose = verbose

        if not self.good:
            return False

        for (condition, method, kwargs) in (
            (check, self.checkTask, {}),
            (convert, self.convertTask, {}),
            (load, self.loadTask, {}),
            (app, self.appTask, {}),
            (browse, self.browseTask, {}),
        ):
            if condition:
                method(**kwargs)
                if not self.good:
                    break

        return self.good


def main():
    (good, tasks, params, flags) = readArgs(
        "tf-fromxml", HELP, TASKS, PARAMS, FLAGS, notInAll=TASKS_EXCLUDED
    )
    if not good:
        return False

    X = XML(**params, **flags)
    X.task(**tasks, **flags)

    return X.good


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
