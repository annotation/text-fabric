# tf.convert.xml.XML is to be reimplemented with the same interface and
# capabilities as the current tf.convert.tei.TEI.
# That will happen here, and then this will become the new xml.py on which
# the new tei.py can be based.

"""
# XML import

You can convert any XML source into TF by specifying a few details about the source.

Text-Fabric then invokes the `tf.convert.walker` machinery to produce a Text-Fabric
dataset out of the source.

!!! caution "As an example"
    This is more intended as an example of how to tackle the conversion
    of XML to TF than as a production engine.
    Most XML corpora use elements for special things, and a good conversion
    to TF should deal with the intention behind the elements.

    See `tf.convert.tei` for a production converter of TEI XML to TF.

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

### schema

string, optional `None`

Which XML schema to be used, if not specified we work in a schemaless way.
If specified, leave out the `.xsd` extension. The file is relative to the
`schema` directory.

### prelim

boolean, optional `True`

Whether to work with the `pre` tf versions.
Use this if you convert XML to a preliminary TF dataset, which will
receive NLP additions later on. That version will then lose the `pre`.

### wordAsSlot

boolean, optional `False`

Whether to take words as the basic entities (slots).
If not, the characters are taken as basic entities.

### sectionModel

dict, optional `{}`

If not passed, or an empty dict, section model I is assumed.
A section model must be specified with the parameters relevant for the
model:

```
dict(
    model="II",
    levels=["chapter", "chunk"],
    element="head",
    attributes=dict(rend="h3"),
)
```

or

```
dict(
    model="I",
    levels=["folder", "file", "chunk"],
)
```

because model I does not require the *attribute* parameter.

For model II, the default parameters are:

```
element="head"
levels=["chapter", "chunk"],
attributes={}
```

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
1.  `app`: creates or updates a corpus specific TF-app with minimal sensible settings,
    plus basic documentation.
1.  `apptoken`: updates a corpus specific TF-app from a character-based dataset
    to a token-based dataset.
1.  `browse`: starts the text-fabric browser on the newly created dataset.

Tasks can be run by passing any choice of task keywords to the
`XML.task()` method.

## Note on versions

The XML source files come in versions, indicated with a data.
The converter picks the most recent one, unless you specify an other one:

```python
tf-from-xml xml=-2  # previous version
tf-from-xml xml=0  # first version
tf-from-xml xml=3  # third version
tf-from-xml xml=2019-12-23  # explicit version
```

The resulting TF data is independently versioned, like `1.2.3` or `1.2.3pre`.
When the converter runs, by default it overwrites the most recent version,
unless you specify another one.

It looks at the latest version and then bumps a part of the version number.

```python
tf-fromxml tf=3  # minor version, 1.2.3 becomes 1.2.4; 1.2.3pre becomes 1.2.4pre
tf-fromxml tf=2  # intermediate version, 1.2.3 becomes 1.3.0
tf-fromxml tf=1  # major version, 1.2.3 becomes 2.0.0
tf-fromxml tf=1.8.3  # explicit version
```

## Examples

Exactly how you can call the methods of this module is demonstrated in the small
corpus of 14 letter by the Dutch artist Piet Mondriaan.

*   [Mondriaan](https://nbviewer.org/github/annotation/mondriaan/blob/master/programs/convertExpress.ipynb).
"""

import sys
import collections
import re
from io import BytesIO

from lxml import etree
from .helpers import tweakTrans, checkSectionModel
from ..fabric import Fabric
from ..core.command import readArgs
from ..core.helpers import console
from ..convert.walker import CV
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
    scanDir,
)

from ..tools.xmlschema import Analysis



FOLDER = "folder"
FILE = "file"
CHAPTER = "chapter"
CHUNK = "chunk"


SECTION_MODELS = dict(
    I=dict(levels=(list, [FOLDER, FILE, CHUNK])),
    II=dict(
        levels=(list, [CHAPTER, CHUNK]),
        element=(str, "head"),
        attributes=(dict, {}),
    ),
)
SECTION_MODEL_DEFAULT = "I"


class XML:
    def __init__(
        self, xml=PARAMS["xml"][1], tf=PARAMS["tf"][1], verbose=FLAGS["verbose"][1]
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
        and various output directories: `tf`, `app`, `docs`.

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
        3.  the XML documents themselves, conforming to a schema

        ### `schema`

        *Location of the XML schema against which the sources can be validated.*

        It should be an `.xsd` file, and the parameter `schema` may specify
        its name (without extension).

        !!! note "Multiple `.xsd` files"
            When you started with a `.rng` file and used `tf.tools.xmlschema` to
            convert it to `xsd`, you may have got multiple `.xsd` files.
            One of them has the same base name as the original `.rng` file,
            and you should pass that name. It will import the remaining `.xsd` files,
            so do not throw them away.

        If no schema is specified, we do not do validation and we cannot do
        intelligent white-space stripping.

        ## Output directories

        ### `report`

        Directory to write the results of the `check` task to: an inventory
        of elements/attributes encountered, and possible validation errors.
        If the directory does not exist, it will be created.
        The default value is `.` (i.e. the current directory in which
        the script is invoked).

        ### `tf`

        The directory under which the text-fabric output file (with extension `.tf`)
        are placed.
        If it does not exist, it will be created.
        The tf files will be generated in a folder named by a version number,
        passed as `tfVersion`.

        ### `app` and `docs`

        Location of additional TF-app configuration and documentation files.
        If they do not exist, they will be created with some sensible default
        settings and generated documentation.
        These settings can be overriden in the `app/config_custom.ymal` file.
        Also a default `display.css` file and a logo are added.

        Custom content for these files can be provided in files
        with `_custom` appended to their base name.

        ### `docs`

        Location of additional documentation.
        This can be generated or had-written material, or a mixture of the two.

        Parameters
        ----------
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
            directory. If the parameter `prelim` was used in the initialization of
            the XML object, only versions ending in `pre` will be taken into account.

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
                spec = util.spec_from_file_location("teicustom", convertCustom)
                code = util.module_from_spec(spec)
                sys.path.insert(0, dirNm(convertCustom))
                spec.loader.exec_module(code)
                sys.path.pop(0)
                self.transform = code.transform
            except Exception as e:
                print(str(e))
                self.transform = None

        generic = settings.get("generic", {})
        schema = settings.get("schema", None)
        prelim = settings.get("prelim", True)
        wordAsSlot = settings.get("wordAsSlot", True)
        sectionModel = settings.get("sectionModel", {})

        sectionModel = checkSectionModel(sectionModel)
        if not sectionModel:
            self.good = False
            return

        sectionProperties = sectionModel.get("properties", None)

        self.generic = generic
        self.schema = schema
        self.prelim = prelim
        self.wordAsSlot = wordAsSlot
        self.sectionModel = sectionModel["model"]
        self.sectionProperties = sectionProperties

        reportDir = f"{refDir}/report"
        appDir = f"{refDir}/app"
        docsDir = f"{refDir}/docs"
        teiDir = f"{refDir}/tei"
        tfDir = f"{refDir}/tf"

        teiVersions = sorted(dirContents(teiDir)[1], key=versionSort)
        nTeiVersions = len(teiVersions)

        if tei in {"latest", "", "0", 0} or str(tei).lstrip("-").isdecimal():
            teiIndex = (0 if tei == "latest" else int(tei)) - 1

            try:
                teiVersion = teiVersions[teiIndex]
            except Exception:
                absIndex = teiIndex + (nTeiVersions if teiIndex < 0 else 0) + 1
                console(
                    (
                        f"no item in {absIndex} in {nTeiVersions} source versions "
                        f"in {ux(teiDir)}"
                    )
                    if len(teiVersions)
                    else f"no source versions in {ux(teiDir)}",
                    error=True,
                )
                self.good = False
                return
        else:
            teiVersion = tei

        teiPath = f"{teiDir}/{teiVersion}"
        reportPath = f"{reportDir}/{teiVersion}"

        if not dirExists(teiPath):
            console(
                f"source version {teiVersion} does not exists in {ux(teiDir)}",
                error=True,
            )
            self.good = False
            return

        teiStatuses = {tv: i for (i, tv) in enumerate(reversed(teiVersions))}
        teiStatus = teiStatuses[teiVersion]
        teiStatusRep = (
            "most recent"
            if teiStatus == 0
            else "previous"
            if teiStatus == 1
            else f"{teiStatus - 1} before previous"
        )
        if teiStatus == len(teiVersions) - 1 and len(teiVersions) > 1:
            teiStatusRep = "oldest"

        if verbose >= 0:
            console(f"TEI data version is {teiVersion} ({teiStatusRep})")

        tfVersions = sorted(dirContents(tfDir)[1], key=versionSort)
        if prelim:
            tfVersions = [tv for tv in tfVersions if tv.endswith(PRE)]

        latestTfVersion = (
            tfVersions[-1] if len(tfVersions) else ("0.0.0" + (PRE if prelim else ""))
        )
        if tf in {"latest", "", "0", 0}:
            tfVersion = latestTfVersion
            vRep = "latest"
        elif tf in {"1", "2", "3", 1, 2, 3}:
            bump = int(tf)
            parts = latestTfVersion.split(".")

            def getVer(b):
                return (
                    int(parts[b].removesuffix(PRE))
                    if prelim and b == len(parts) - 1
                    else int(parts[b])
                )

            def setVer(b, val):
                parts[b] = f"{val}{PRE}" if prelim and b == len(parts) - 1 else f"{val}"

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
                tfVersion = ".".join(parts)
                vRep = "major" if bump == 1 else "intermediate" if bump == 2 else "minor"
                vRep = f"next {vRep}"
        else:
            tfVersion = tf
            status = "exising" if dirExists(f"{tfDir}/{tfVersion}") else "new"
            vRep = f"explicit {status}"

        tfPath = f"{tfDir}/{tfVersion}"

        if verbose >= 0:
            console(f"TF data version is {tfVersion} ({vRep})")

        self.refDir = refDir
        self.teiVersion = teiVersion
        self.teiPath = teiPath
        self.tfVersion = tfVersion
        self.tfPath = tfPath
        self.reportPath = reportPath
        self.tfDir = tfDir
        self.appDir = appDir
        self.docsDir = docsDir
        self.backend = backend
        self.org = org
        self.repo = repo
        self.relative = relative

        self.schemaFile = None if schema is None else f"{refDir}/schema/{schema}.xsd"
        levelNames = sectionProperties["levels"]
        self.levelNames = levelNames
        self.chunkLevel = levelNames[-1]

        if self.sectionModel == "II":
            self.chapterSection = levelNames[0]
            self.chunkSection = levelNames[1]
        else:
            self.folderSection = levelNames[0]
            self.fileSection = levelNames[1]
            self.chunkSection = levelNames[2]

        self.verbose = verbose
        myDir = dirNm(abspath(__file__))
        self.myDir = myDir


    @staticmethod
    def help(program):
        """Print a help text to the console.

        The intended use of this module is that it is included by a conversion
        script.
        In order to give help on the command line, here is a pre-baked help text.
        Only the name of the conversion script needs to be merged in.

        Parameters
        ----------
        program: string
            The name of the program that you want to display
            in the help string.
        """

        console(
            f"""

        Convert XML to TF.
        There are also commands to check the XML and to load the TF.

        python3 {program} [tasks/flags] [--help]

        --help: show this text and exit

        tasks:
            a sequence of tasks:
            check:
                just reports on the elements in the source.
            convert:
                just converts XML to TF
            load:
                just loads the generated TF;

        flags:
            test:
                run in test mode
        """
        )

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
        tuple of tuple
            The outer tuple has sorted entries corresponding to folders under the
            XML input directory.
            Each such entry consists of the folder name and an inner tuple
            that contains the file names in that folder, sorted.
        """
        sourceDir = self.sourceDir
        testMode = self.testMode
        testSet = self.testSet

        IGNORE = "__ignore__"

        xmlFilesRaw = collections.defaultdict(list)

        with scanDir(sourceDir) as dh:
            for folder in dh:
                folderName = folder.name
                if folderName == IGNORE:
                    continue
                if not folder.is_dir():
                    continue
                with scanDir(f"{sourceDir}/{folderName}") as fh:
                    for file in fh:
                        fileName = file.name
                        if not (fileName.lower().endswith(".xml") and file.is_file()):
                            continue
                        if testMode and fileName not in testSet:
                            continue
                        xmlFilesRaw[folderName].append(fileName)

        xmlFiles = tuple(
            (folderName, tuple(sorted(fileNames)))
            for (folderName, fileNames) in sorted(xmlFilesRaw.items())
        )
        return xmlFiles

    def checkTask(self):
        """Implementation of the "check" task.

        It validates the XML, but only if a schema file has been passed explicitly
        when constructing the `XML()` object.

        Then it makes an inventory of all elements and attributes in the XML files.

        The inventory lists all elements and attributes, and many attribute values.
        But is represents any digit with `n`, and some attributes that contain
        ids or keywords, are reduced to the value `x`.

        This information reduction helps to get a clear overview.

        It writes reports to the `reportDir`:

        *   `errors.txt`: validation errors
        *   `elements.txt`: element/attribute inventory.
        """
        sourceDir = self.sourceDir
        reportDir = self.reportDir

        getStore = lambda: collections.defaultdict(  # noqa: E731
            lambda: collections.defaultdict(collections.Counter)
        )
        analysis = getStore()

        parser = self.getParser()

        initTree(reportDir)

        def analyse(root, analysis):
            NUM_RE = re.compile(r"""[0-9]""", re.S)

            def nodeInfo(node):
                tag = etree.QName(node.tag).localname
                atts = node.attrib

                if len(atts) == 0:
                    analysis[tag][""][""] += 1
                else:
                    for (kOrig, v) in atts.items():
                        k = etree.QName(kOrig).localname

                        vTrim = NUM_RE.sub("N", v)
                        analysis[tag][k][vTrim] += 1

                for child in node.iterchildren(tag=etree.Element):
                    nodeInfo(child)

            nodeInfo(root)

        def writeReport():
            reportFile = f"{reportDir}/elements.txt"
            with open(reportFile, "w", encoding="utf8") as fh:
                fh.write(
                    "Inventory of tags and attributes in the source XML file(s).\n"
                )
                fh.write("\n\n")

                infoLines = 0

                def writeAttInfo(tag, att, attInfo):
                    nonlocal infoLines
                    nl = "" if tag == "" else "\n"
                    tagRep = "" if tag == "" else f"<{tag}>"
                    attRep = "" if att == "" else f"{att}="
                    atts = sorted(attInfo.items())
                    (val, amount) = atts[0]
                    fh.write(f"{nl}\t{tagRep:<12} {attRep:<12} {amount:>5}x {val}\n")
                    infoLines += 1
                    for (val, amount) in atts[1:]:
                        fh.write(f"""\t{'':<12} {'"':<12} {amount:>5}x {val}\n""")
                        infoLines += 1

                def writeTagInfo(tag, tagInfo):
                    nonlocal infoLines
                    tags = sorted(tagInfo.items())
                    (att, attInfo) = tags[0]
                    writeAttInfo(tag, att, attInfo)
                    infoLines += 1
                    for (att, attInfo) in tags[1:]:
                        writeAttInfo("", att, attInfo)

                for (tag, tagInfo) in sorted(analysis.items()):
                    writeTagInfo(tag, tagInfo)

            console(f"{infoLines} info line(s) written to {reportFile}")

        i = 0
        for (xmlFolder, xmlFiles) in self.getXML():
            console(xmlFolder)
            for xmlFile in xmlFiles:
                i += 1
                console(f"\r{i:>4} {xmlFile:<50}", newline=False)
                xmlPath = f"{sourceDir}/{xmlFolder}/{xmlFile}"
                tree = etree.parse(xmlPath, parser)
                root = tree.getroot()
                analyse(root, analysis)

        console("")
        writeReport()

        return True

    # SET UP CONVERSION

    def getConverter(self):
        """Initializes a converter.

        Returns
        -------
        object
            The `tf.convert.walker.CV` converter object, initialized.
        """
        tfPath = self.tfPath

        TF = Fabric(locations=tfPath)
        return CV(TF)

    def convertTask(self):
        """Implementation of the "convert" task.

        It sets up the `tf.convert.walker` machinery and runs it.

        Returns
        -------
        boolean
            Whether the conversion was successful.
        """
        slotType = "char"
        otext = {
            "fmt:text-orig-full": "{ch}",
            "sectionFeatures": "folder,file",
            "sectionTypes": "folder,file",
        }
        intFeatures = {"empty"}
        featureMeta = dict(
            folder=dict(description="name of source folder"),
            file=dict(description="name of source file"),
            ch=dict(description="the unicode character of a slot"),
            empty=dict(
                description="whether a slot has been inserted in an empty element"
            ),
        )
        self.intFeatures = intFeatures
        self.featureMeta = featureMeta

        tfVersion = self.tfVersion
        tfPath = self.tfPath
        generic = self.generic
        generic["sourceFormat"] = "XML"
        generic["version"] = tfVersion

        initTree(tfPath, fresh=True, gentle=True)

        cv = self.getConverter()

        return cv.walk(
            self.getDirector(),
            slotType,
            otext=otext,
            generic=generic,
            intFeatures=intFeatures,
            featureMeta=featureMeta,
            generateTf=True,
        )

    # DIRECTOR

    def getDirector(self):
        """Factory for the director function.

        The `tf.convert.walker` relies on a corpus dependent `director` function
        that walks through the source data and spits out actions that
        produces the TF dataset.

        We collect all needed data, store it, and define a local director function
        that has access to this data.

        Returns
        -------
        function
            The local director function that has been constructed.
        """
        PASS_THROUGH = set(
            """
            xml
            """.strip().split()
        )

        # CHECKING

        ZWSP = "\u200b"  # zero-width space

        sourceDir = self.sourceDir
        featureMeta = self.featureMeta
        transform = self.transform

        transformFunc = (
            (lambda x: x)
            if transform is None
            else (lambda x: BytesIO(transform(x).encode("utf-8")))
        )

        parser = self.getParser()

        # WALKERS

        WHITE_TRIM_RE = re.compile(r"\s+", re.S)

        def walkNode(cv, cur, node):
            """Internal function to deal with a single element.

            Will be called recursively.

            Parameters
            ----------
            cv: object
                The convertor object, needed to issue actions.
            cur: dict
                Various pieces of data collected during walking
                and relevant for some next steps in the walk.
            node: object
                An lxml element node.
            """
            tag = etree.QName(node.tag).localname
            cur["nest"].append(tag)

            beforeChildren(cv, cur, node, tag)

            for child in node.iterchildren(tag=etree.Element):
                walkNode(cv, cur, child)

            afterChildren(cv, cur, node, tag)
            cur["nest"].pop()
            afterTag(cv, cur, node, tag)

        def addSlot(cv, cur, ch):
            """Add a slot.

            Whenever we encounter a character, we add it as a new slot.

            Parameters
            ----------
            cv: object
                The convertor object, needed to issue actions.
            cur: dict
                Various pieces of data collected during walking
                and relevant for some next steps in the walk.
            ch: string
                A single character, the next slot in the result data.
            """
            s = cv.slot()
            cv.feature(s, ch=ch)

        def beforeChildren(cv, cur, node, tag):
            """Actions before dealing with the element's children.

            Parameters
            ----------
            cv: object
                The convertor object, needed to issue actions.
            cur: dict
                Various pieces of data collected during walking
                and relevant for some next steps in the walk.
            node: object
                An lxml element node.
            tag: string
                The tag of the lxml node.
            """
            if tag not in PASS_THROUGH:
                curNode = cv.node(tag)
                cur["elems"].append(curNode)
                atts = {etree.QName(k).localname: v for (k, v) in node.attrib.items()}
                if len(atts):
                    cv.feature(curNode, **atts)

            if node.text:
                textMaterial = WHITE_TRIM_RE.sub(" ", node.text)
                for ch in textMaterial:
                    addSlot(cv, cur, ch)

        def afterChildren(cv, cur, node, tag):
            """Node actions after dealing with the children, but before the end tag.

            Parameters
            ----------
            cv: object
                The convertor object, needed to issue actions.
            cur: dict
                Various pieces of data collected during walking
                and relevant for some next steps in the walk.
            node: object
                An lxml element node.
            tag: string
                The tag of the lxml node.
            """
            if tag not in PASS_THROUGH:
                curNode = cur["elems"].pop()

                if not cv.linked(curNode):
                    s = cv.slot()
                    cv.feature(s, ch=ZWSP, empty=1)

                cv.terminate(curNode)

        def afterTag(cv, cur, node, tag):
            """Node actions after dealing with the children and after the end tag.

            This is the place where we proces the `tail` of an lxml node: the
            text material after the element and before the next open/close
            tag of any element.

            Parameters
            ----------
            cv: object
                The convertor object, needed to issue actions.
            cur: dict
                Various pieces of data collected during walking
                and relevant for some next steps in the walk.
            node: object
                An lxml element node.
            tag: string
                The tag of the lxml node.
            """
            if node.tail:
                tailMaterial = WHITE_TRIM_RE.sub(" ", node.tail)
                for ch in tailMaterial:
                    addSlot(cv, cur, ch)

        def director(cv):
            """Director function.

            Here we program a walk through the XML sources.
            At every step of the walk we fire some actions that build TF nodes
            and assign features for them.

            Because everything is rather dynamic, we generate fairly standard
            metadata for the features.

            Parameters
            ----------
            cv: object
                The convertor object, needed to issue actions.
            """
            cur = {}

            i = 0
            for (xmlFolder, xmlFiles) in self.getXML():
                console(xmlFolder)

                cur["folder"] = cv.node("folder")
                cv.feature(cur["folder"], folder=xmlFolder)

                for xmlFile in xmlFiles:
                    i += 1
                    console(f"\r{i:>4} {xmlFile:<50}", newline=False)

                    cur["file"] = cv.node("file")
                    cv.feature(cur["file"], file=xmlFile.removesuffix(".xml"))

                    with open(
                        f"{sourceDir}/{xmlFolder}/{xmlFile}", encoding="utf8"
                    ) as fh:
                        text = fh.read()
                        text = transformFunc(text)
                        tree = etree.parse(text, parser)
                        root = tree.getroot()
                        cur["nest"] = []
                        cur["elems"] = []
                        walkNode(cv, cur, root)

                    addSlot(cv, cur, None)
                    cv.terminate(cur["file"])

                cv.terminate(cur["folder"])

            console("")

            for fName in featureMeta:
                if not cv.occurs(fName):
                    cv.meta(fName)
            for fName in cv.features():
                if fName not in featureMeta:
                    cv.meta(
                        fName,
                        description=f"this is XML attribute {fName}",
                        valueType="str",
                    )
            console("source reading done")
            return True

        return director

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
        tfPath = self.tfPath

        if not dirExists(tfPath):
            console(f"Directory {ux(tfPath)} does not exist.")
            console("No tf found, nothing to load")
            return False

        TF = Fabric(locations=[tfPath])
        allFeatures = TF.explore(silent=True, show=True)
        loadableFeatures = allFeatures["nodes"] + allFeatures["edges"]
        api = TF.load(loadableFeatures, silent=False)
        if api:
            console(f"max node = {api.F.otype.maxNode}")
            return True
        return False

    def task(self, check=False, convert=False, load=False, test=None):
        """Carry out any task, possibly modified by any flag.

        This is a higher level function that can execute a selection of tasks.

        The tasks will be executed in a fixed order: check, convert load.
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
        test: boolean, optional None
            Whether to run in test mode.
            In test mode only the files in the test set are converted.

            If None, it will read its value from the attribute `testMode` of the
            `XML` object.

        Returns
        -------
        boolean
            Whether all tasks have executed successfully.
        """
        sourceDir = self.sourceDir
        reportDir = self.reportDir
        tfPath = self.tfPath

        if test is not None:
            self.testMode = test

        good = True

        if check:
            console(f"XML to TF checking: {ux(sourceDir)} => {ux(reportDir)}")
            good = self.checkTask()

        if good and convert:
            console(f"XML to TF converting: {ux(sourceDir)} => {ux(tfPath)}")
            good = self.convertTask()

        if good and load:
            good = self.loadTask()

        return good

    def run(self, program=None):
        """Carry out tasks specified by arguments on the command line.

        The intended use of this module is that it is included by a conversion
        script.
        When that script is invoked, you can pass arguments to specify tasks
        and flags.

        This function inspects those arguments, and runs the specified tasks,
        with the specified flags enabled.

        Parameters
        ----------
        program: string
            The name of the program that you want to display
            in the help string, in case a help text must be displayed.

        Returns
        -------
        integer
            In fact, this function will terminate the conversion program
            an return a status code: 0 for succes, 1 for failure.
        """
        programRep = "XML-converter" if program is None else program
        possibleTasks = {"check", "convert", "load"}
        possibleFlags = {"test"}
        possibleArgs = possibleTasks | possibleFlags

        args = sys.argv[1:]

        if not len(args):
            self.help(programRep)
            console("No task specified")
            sys.exit(-1)

        illegalArgs = {arg for arg in args if arg not in possibleArgs}

        if len(illegalArgs):
            self.help(programRep)
            for arg in illegalArgs:
                console(f"Illegal argument `{arg}`")
            sys.exit(-1)

        tasks = {arg: True for arg in args if arg in possibleTasks}
        flags = {arg: True for arg in args if arg in possibleFlags}

        good = self.task(**tasks, **flags)
        if good:
            sys.exit(0)
        else:
            sys.exit(1)


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
