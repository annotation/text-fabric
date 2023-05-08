"""
# XML import

You can convert any XML source into TF by specifying a few details about the source.

Text-Fabric then invokes the `tf.convert.walker` machinery to produce a Text-Fabric
dataset out of the source.

## Whitespace

Becasue of the lack of schema information we do not know exactly which white-space
is significant. The only thing we do to whitespace is to condense each stretch
of whitespace to a single space.

Whether some of these spaces around tags must be ignored is a matter of further
customization.

This converter limits itself to generating the TF, it does not generated docs and
also the creation of a TF app is out of scope.

## Tasks

We have the following conversion tasks:

1.  `check`: makes and inventory of all XML elements and attributes used.
2.  `convert`: produces actual TF files by converting XML files.
3.  `load`: loads the generated TF for the first time, by which the precomputation
    step is triggered. During precomputation some checks are performed. Once this
    has succeeded, we have a workable Text-Fabric dataset.

Tasks can be run by passing any choice of task keywords to the
`XML.task()` method.

## Flags

We have one flag:

1. `test`: only converts those files in the input that are named in a test set.

The test set is passed as argument to the `XML` constructur.

The `test` flag is passed to the `XML.task()` method.

## Usage

It is intended that you call this converter in a script.

In that script you can define auxiliary Python functions and pass them
to the converter. The `XML` class has some hooks where such functions
can be plugged in.

Here you can also define a test set, in case you want to experiment with the
conversion.

Last, but not least, you can assemble all the input parameters needed to
get the conversion off the ground.

The resulting script will look like this:

``` python

from tf.convert.xml import XML
from tf.core.files import baseNm


TEST_SET = set(
    '''
    aa00.xml
    bb11.xml
    '''.strip().split()
)

AUTHOR = "Corpus Author"
TITLE = "Corpus"
INSTITUTE = "Corpus Maintainer"

GENERIC = dict(
    author=AUTHOR,
    title=TITLE,
    institute=INSTITUTE,
    language="en",
    converters="Corpus Convertor (Text-Fabric)",
    sourceFormat="XML",
    descriptionTf="Edition",
)

ABOUT_TEXT = '''
# CONTRIBUTORS

Researcher: S. Scholar.

Editors: E. Editor et al.
'''

TRANSCRIPTION_TEXT = '''

The XML has not been validated or polished
before generating the TF data.
'''

def transform(text):
    return text.replace(",,", ",")


X = XML(
    sourceVersion="2023-01-31",
    testSet=TEST_SET,
    generic=GENERIC,
    transform=transform,
    tfVersion="0.1",
)

X.run(baseNm(__file__))
```
"""

import sys
import collections
import re
from io import BytesIO

from lxml import etree
from ..fabric import Fabric
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
    scanDir,
)


__pdoc__ = {}

DOC_TRANS = """
## Essentials

*   Text-Fabric non-slot nodes correspond to XML elements in the source.
*   Text-Fabric node-features correspond to XML attributes.
*   Text-Fabric slot nodes correspond to characters in XML element content.

## Sectioning

The material is divided into two levels of sections, mainly for the purposes
of text display.

It is assumed that the source is a directory consisting of subdirectories
consisting of xml files, the XML files.

1.  Subdirectories and files are sorted in the lexicographic ordering
1.  The subdirectory `__ignore__` is ignored.
1.  For each subdirectory, a section level 1 node will be created, with
    feature `name` containing its name.
1.  For each file in a subdirecotry, a section level 2 node will be created, with
    feature `name` containing its name.


## Elements and attributes

1.  All elements result in nodes whose type is
    exactly equal to the tag name.
1.  These nodes are linked to the slots that are produced when converting the
    content of the corresponding source elements.
1.  Attributes translate into features of the same name; the feature assigns
    the attribute value (as string) to the node that corresponds to the element
    of the attribute.

## Slots

The basic unit is the unicode character.
For each character in the input we make a slot, but the correspondence is not
quite 1-1.

1.  Whitespace is reduced to a single space.
1.  Empty elements will receive one extra slot; this will anchor the element to
    a textual position; the empty slot gets the ZERO-WIDTH-SPACE (Unicode 200B)
    as character value.
1.  Slots get the following features:
    *   `ch`: the character of the slot
    *   `empty`: 1 if the slot has been inserted as an empty slot, no value otherwise.


## Text-formats

Text-formats regulate how text is displayed, and they can also determine
what text is displayed.

We have the following formats:

*   `text-orig-full`: all text

## Simplifications

XML is complicated.

On the other hand, the resulting TF should consist of clearly demarcated node types
and a simple list of features. In order to make that happen, we simplify matters
a bit.

1.  Processing instructions (`<!proc a="b">`) are ignored.
1.  Comments (`<!-- this is a comment -->`) are ignored.
1.  Declarations (`<?xml ...>` `<?xml-model ...>` `<?xml-stylesheet ...>`) are
    read by the parser, but do not leave traces in the TF output.
1.  The atrributes of the root-element are ignored.
1.  Namespaces are read by the parser,
    but only the unqualified names are distinguishable in the output as feature names.
    So if the input has elements `ns1:abb` and `ns2:abb`, we'll see just the node
    type `abb` in the output.

## TF noded and features

(only in as far they are not in 1-1 correspondence with XML elements and attributes)

### node type `folder`

*The type of subfolders of XML documents.*

**Section level 1.**

**Features**

feature | description
--- | ---
`folder` | name of the subfolder

### node type `file`

*The type of individual XML documents.*

**Section level 2.**

**Features**

feature | description
--- | ---
`file` | name of the file, without the `.xml` extension. Other extensions are included.

### node type `char`

*Unicode characters.*

**Slot type.**

The characters of the text of the elements.
Ignorable whitespace has been discarded, and is not present in the TF dataset.
Meaningful whitespace has been condensed to single spaces.

Some empty slots have been inserted to mark the place of empty elements.

**Features**

feature | description
--- | ---
`ch` | the unicode character in that slot. There are also slots
`empty` | whether a slot has been inserted in an empty element
"""


class XML:
    def __init__(
        self,
        sourceVersion="0.1",
        testSet=set(),
        generic={},
        transform=None,
        tfVersion="0.1",
    ):
        """Converts XML to TF.

        We adopt a fair bit of "convention over configuration" here, in order to lessen
        the burden for the user of specifying so many details.

        Based on current directory from where the script is called,
        it defines all the ingredients to carry out
        a `tf.convert.walker` conversion of the XML input.

        This function is assumed to work in the context of a repository,
        i.e. a directory on your computer relative to which the input directory
        `xml` and the output directory `tf` exist.

        Your current directory must be somewhere inside

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

        ## Input directory

        ### `xml`

        *Location of the XML sources.*

        **If it does not exist, the program aborts with an error.**

        Several levels of subfolders are assumed:

        1.  the version of the source (this could be a date string).
        2.  volumes/collections of documents. The subfolder `__ignore__` is ignored.
        3.  the XML documents themselves

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
        The tf files will be generated in a subdirectory named by a version number,
        passed as `tfVersion`.

        Parameters
        ----------

        sourceVersion: string, optional "0.1"
            Version of the source files. This is the name of a top-level
            subfolder of the `xml` input folder.

        testSet: set, optional empty
            A set of file names. If you run the conversion in test mode
            (pass `test` as argument to the `XML.task()` method),
            only the files in the test set are converted.

        generic: dict, optional {}
            Metadata for all generated TF feature.

        transform: function, optional None
            If not None, a function that transforms text to text, used
            as a preprocessing step for each input xml file.

        tfVersion: string, optional "0.1"
            Version of the generated tf files. This is the name of a top-level
            subfolder of the `tf` output folder.
        """
        (backend, org, repo, relative) = getLocation()
        if any(s is None for s in (backend, org, repo, relative)):
            console(
                "Not working in a repo: "
                f"backend={backend} org={org} repo={repo} relative={relative}"
            )
            quit()

        console(f"Working in repository {org}/{repo}{relative} in backend {backend}")

        base = ex(f"~/{backend}")
        repoDir = f"{base}/{org}/{repo}"
        refDir = f"{repoDir}{relative}"
        sourceDir = f"{refDir}/xml/{sourceVersion}"
        reportDir = f"{refDir}/report"
        tfDir = f"{refDir}/tf"

        self.refDir = refDir
        self.sourceDir = sourceDir
        self.reportDir = reportDir
        self.tfDir = tfDir
        self.org = org
        self.repo = repo

        if sourceDir is None or not dirExists(sourceDir):
            console(f"Source location does not exist: {sourceDir}")
            quit()

        self.sourceVersion = sourceVersion
        self.testMode = False
        self.testSet = testSet
        self.generic = generic
        self.transform = transform
        self.tfVersion = tfVersion
        self.tfPath = f"{tfDir}/{tfVersion}"
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


__pdoc__["XML"] = DOC_TRANS
