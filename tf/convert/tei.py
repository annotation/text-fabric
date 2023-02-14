"""
# TEI import

You can convert any TEI source into TF by specifying a few details about the source.

Text-Fabric then invokes the `tf.convert.walker` machinery to produce a Text-Fabric
dataset out of the source.

Text-Fabric knows the TEI elements, because it will read and parse the complete
TEI schema. From this the set of complex, mixed elements is distilled.

If the TEI source conforms to a cutomised TEI schema, you can pass it to the TEI
importer, and it will read it and override the generic information of the TEI elements.

The TEI conversion is rather straightforward because of some conventions
that cannot be changed:

## Sectioning

The material is divided into three levels of sections, mainly for the purposes
of text display.

It is assumed that the source is a directory consisting of subdirectories
consisting of xml files, the TEI files.

1.  Subdirectories and files are sorted in the lexicographic ordering
1.  The subdirectory `__ignore__` is ignored.
1.  For each subdirectory, a section level 1 node will be created, with
    feature `name` containing its name.
1.  For each file in a subdirecotry, a section level 2 node will be created, with
    feature `name` containing its name.
1.  A third section level, named `chunk` will be made.
    For each immediate child element of `<teiHeader>` and for each immediate child
    element of `<body>`, a chunk node will be created, wit a feature `cn`
    containing the number of the chunk within the file, starting with 1.
    Also the following elements will trigger a chunk node:
    `<facsimile>`, `<fsdDecl>`, `<sourceDoc>`, and `<standOff>`.


## Elements and attributes

1.  All elements, except `<TEI>` and `<teiHeader>` result in nodes whose type is
    exactly equal to the tag name.
1.  These nodes are linked to the slots that are produced when converting the
    content of the corresponding source elements.
1.  Attributes translate into features of the same name; the feature assigns
    the attribute value (as string) to the node that corresponds to the element
    of the attribute.

## Word detection

Words will be detected. They are maximally long sequences of alphanumeric characters
and hyphens.

1.  What is alphanumeric is determined by the unicode class of the character,
    see the Python documentation of the function
    [`isalnum()`](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)
1.  Hyphens are Unicode characters 002D (ascii hyphen) and 2010 (unicode hyphen).
1.  Words get two features:
    *   `str`: the alphanumeric string that is the word;
    *   `after`: the non-alphanumeric string after the word unti the following word.
    *   `ismeta`: 1 if the word occurs in inside the `<teiHeader>`, no value otherwise.

## Slots

The basic unit is the unicode character.
For each character in the input we make a slot, but the correspondence is not
quite 1-1.

1. Spaces are stripped when they are between elements whose parent does not allow
   mixed content; other whitespace is reduced to a single space.
1. All slots inside the teiHeader will get the feature `ismeta` set to 1;
   for slots inside the body, `ismeta` has no value.
1. Empty elements will receive one extra slot; this will anchor the element to
   a textual position; the empty slot gets the ZERO-WIDTH-SPACE (Unicode 200B)
   as character value.
1. Slots get the following features:
   *    `ch`: the character of the slot
   *    `empty`: 1 if the slot has been inserted as an empty slot, no value otherwise.
    *   `ismeta`: 1 if the slot occurs in inside the `<teiHeader>`, no value otherwise.

## Simplifications

XML is complicated, the TEI guidelines use that complexity to the full.
In particular, it is difficult to determine what the set of TEI elements is
and what their properties are, just by looking at the schemas, because they are full
of macros, indirections, and abstractions, which can be overridden in any particular
TEI application.

On the other hand, the resulting TF should consist of clearly demarcated node types
and a simple list of features. In order to make that happen, we simplify matters
a bit.

1.  Processing instructions (`<!proc a="b">`) are ignored.
1.  Comments (`<!-- this is a comment -->`) are ignored.
1.  Declarations (`<?xml ...>` `<?xml-model ...>` `<?xml-stylesheet ...>`) are
    read by the parser, but do not leave traces in the TF output.
1.  The atrributes of the root-element (`<TEI>`) are ignored.
1.  Namespaces (`xmlns="http://www.tei-c.org/ns/1.0"`) are read by the parser,
    but only the unqualified names are distinguishable in the output as feature names.
    So if the input has elements `tei:abb` and `ns:abb`, we'll see just the node
    type `abb` in the output.

## Tasks, parsing, and validation

We have three conversion tasks:

1.  `check`: makes and inventory of all XML elements and attributes used.
2.  `convert`: produces actual TF files by converting XML files.
3.  `load`: loads the generated TF for the first time, by which the precomputation
    step is triggered. During precomputation some checks are performed. Once this
    has succeeded, we have a workable Text-Fabric dataset.

Tasks can be run by passing any choice of task keywords to the
`TEI.task()` method.

We use [lxml](https://lxml.de) for XML parsing. During `convert` it is not used
in validating mode, but we can trigger a validation step during `check`.

However, some information about the elements, in particular whether they allow
mixed content or not, will be read off the schemas, and will be used
during conversion.

## Flags

We have one flag:

1. `test`: only converts those files in the input that are named in a test set.

The test set is passed as argument to the `TEI` constructur.

The `test` flag is passed to the `TEI.task()` method.

## Usage

It is intended that you call this converter in a script.

In that script you can define auxiliary Python functions and pass them
to the converter. The `TEI` class has some hooks where such functions
can be plugged in.

Here you can also define a test set, in case you want to experiment with the
conversion.

Last, but not least, you can assemble all the input parameters needed to
get the conversion off the ground.

The resulting script will look like this:

``` python
from tf.convert.tei import TEI
from tf.core.helpers import getLocation

(BACKEND, ORG, REPO) = getLocation()
BASE = os.path.expanduser(f"~/{BACKEND}")
REPO_DIR = f"{BASE}/{ORG}/{REPO}"
SOURCE_DIR = f"{REPO_DIR}/xml"
VERSION_SOURCE = "2023-01-31"
SCHEMA_FILE = f"{REPO_DIR}/resources/MD.xsd"
REPORT_DIR = f"{REPO_DIR}/report"
TF_DIR = f"{REPO_DIR}/tf"
VERSION_TF = "0.1"

GENERIC = dict(
    author="Piet Mondriaan",
    institute="KNAW/Huygens Amsterdam",
    language="nl",
    converters="Dirk Roorda (Text-Fabric)",
    sourceFormat="TEI",
    descriptionTf="Critical edition",
)
TEST_SET = set(
    '''
    18920227.xml
    18920302.xml
    18930711.xml
    18980415.xml
    '''.strip().split()
)


def transform(text):
    return text.replace(",,", "-")


T = TEI(
    sourceDir=f"{SOURCE_DIR}/{VERSION_SOURCE}",
    schemaFile=SCHEMA_FILE,
    generic=GENERIC,
    reportDir=REPORT_DIR,
    transform=transform,
    tfDir=f"{TF_DIR}/{VERSION_TF}",
    testSet=TEST_SET,
)

T.run(os.path.basename(__file__))

```
"""

import sys
import os
import collections
import re
from io import BytesIO
from lxml import etree
from tf.fabric import Fabric
from tf.core.helpers import console
from tf.convert.walker import CV
from tf.core.helpers import initTree, dirExists, unexpanduser as ux
from tf.tools.xmlschema import Analysis


class TEI:
    def __init__(
        self,
        sourceDir=None,
        schemaFile=None,
        generic={},
        reportDir=".",
        transform=None,
        tfDir="tf",
        testSet=set(),
    ):
        """Converts TEI to TF.

        Based on the arguments, it defines all the ingredients to carry out
        a `tf.convert.walker` conversion of the TEI input,
        where nodes are created when start tags are encountered in the TEI,
        and those same nodes are terminated upon encountering the corresponding
        end tags.
        Attributes of elements give rise to features on the corresponding nodes.

        Parameters
        ----------
        sourceDir: string, optional None
            Path on the file system where the TEI source resides.
            It is assumed that there is one level of subfolders
            underneath, under which there are `.xml` files
            conforming to the TEI schema or some customisation of it.

            The subfolder `__ignore__` is ignored.

            If sourceDir is None or does not exist, the program aborts with an error.

        schemaFile: string, optional None
            If None, we use the full TEI schema.
            Otherwise, we use this file as custom TEI schema,
            but to be sure, we still analyse the full TEI schema and
            use the schemaFile passed here as overrides.

        generic: dict, optional {}
            Metadata for all generated TF feature.

        reportDir: string, optional "."
            Directory to write the results of the `check` task to: an inventory
            of elements/attributes encountered, and possible validation errors.
            If the directory does not exist, it will be created.
            The default value is `.` (i.e. the current directory in which
            the script is invoked).

        transform: function, optional None
            If not None, a function that transforms text to text, used
            as a preprocessing step for each input xml file.

        tfDir: string, optional None
            The directory under which the text-fabric output file (with extension `.tf`)
            are placed. If it does not exist, it will be created.
            If you want your tf files in subdirectories named by a version number,
            you have to include that version number in the value for `tfDir`.

        testSet: set, optional empty
            A set of file names. If you run the conversion in test mode
            (pass `test` as argument to the `TEI.task()` method),
            only the files in the test set are converted.
        """
        if sourceDir is None or not dirExists(sourceDir):
            console(f"Source location does not exist: {sourceDir}")
            quit()

        self.sourceDir = sourceDir
        self.schemaFile = schemaFile
        self.generic = generic
        self.reportDir = reportDir
        self.transform = transform
        self.tfDir = tfDir
        self.testMode = False
        self.testSet = testSet

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

        Convert TEI to TF.
        There are also commands to check the TEI and to load the TF.

        python3 {program} [tasks/flags] [--help]

        --help: show this text and exit

        tasks:
            a sequence of tasks:
            check:
                just reports on the elements in the source.
            convert:
                just converts TEI to TF
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
            remove_blank_text=True,
            collect_ids=False,
            remove_comments=True,
            remove_pis=True,
        )

    def getValidator(self):
        """Parse the schema.

        A parsed schemacan be used for XML-validation.
        This will only happen during the `check` task.

        Returns
        -------
        object
            A configured lxml schema validator.
        """
        schemaFile = self.schemaFile

        if schemaFile is None:
            return None

        schemaDoc = etree.parse(schemaFile)
        return etree.XMLSchema(schemaDoc)

    def getElementInfo(self):
        """Analyse the schema.

        The XML schema has useful information about the XML elements that
        occur in the source. Here we extract that information and make it
        fast-accessible.

        Returns
        -------
        dict
            Keyed by element name (without namespaces), where the value
            for each name is a tuple of booleans: whether the element is simple
            or complex; whether the element allows mixed content or only pure content.
        """
        schemaFile = self.schemaFile

        A = Analysis()
        A.configure(override=schemaFile)
        A.interpret()
        if not A.good:
            quit()
        return {name: (typ, mixed) for (name, typ, mixed) in A.getDefs()}

    def getXML(self):
        """Make an inventory of the TEI source files.

        Returns
        -------
        tuple of tuple
            The outer tuple has sorted entries corresponding to folders under the
            TEI input directory.
            Each such entry consists of the folder name and an inner tuple
            that contains the file names in that folder, sorted.
        """
        sourceDir = self.sourceDir
        testMode = self.testMode
        testSet = self.testSet

        IGNORE = "__ignore__"

        xmlFilesRaw = collections.defaultdict(list)

        with os.scandir(sourceDir) as dh:
            for folder in dh:
                folderName = folder.name
                if folderName == IGNORE:
                    continue
                if not folder.is_dir():
                    continue
                with os.scandir(f"{sourceDir}/{folderName}") as fh:
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

    def check(self):
        """Implementation of the "check" task.

        It validates the TEI, but only if a schema file has been passed explicitly
        when constructing the `TEI()` object.

        Then it makes an inventory of all elements and attributes in the TEI files.

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

        kindLabels = dict(
            format="FORMATTING ATTRIBUTES",
            keyword="KEYWORD ATTRIBUTES",
            rest="REMAINING ATTRIBUTES and ELEMENTS",
        )
        getStore = lambda: collections.defaultdict(  # noqa: E731
            lambda: collections.defaultdict(collections.Counter)
        )
        analysis = {x: getStore() for x in kindLabels}
        errors = []

        parser = self.getParser()
        validator = self.getValidator()

        initTree(reportDir)

        def analyse(root, analysis):
            FORMAT_ATTS = set(
                """
                dim
                level
                place
                rend
            """.strip().split()
            )

            KEYWORD_ATTS = set(
                """
                facs
                form
                function
                lang
                reason
                type
                unit
                who
            """.strip().split()
            )

            TRIM_ATTS = set(
                """
                id
                key
                target
                value
            """.strip().split()
            )

            NUM_RE = re.compile(r"""[0-9]""", re.S)

            def nodeInfo(node, analysis):
                tag = etree.QName(node.tag).localname
                atts = node.attrib

                if len(atts) == 0:
                    kind = "rest"
                    analysis[kind][tag][""][""] += 1
                else:
                    for (kOrig, v) in atts.items():
                        k = etree.QName(kOrig).localname
                        kind = (
                            "format"
                            if k in FORMAT_ATTS
                            else "keyword"
                            if k in KEYWORD_ATTS
                            else "rest"
                        )
                        dest = analysis[kind]

                        if kind == "rest":
                            vTrim = "X" if k in TRIM_ATTS else NUM_RE.sub("N", v)
                            dest[tag][k][vTrim] += 1
                        else:
                            words = v.strip().split()
                            for w in words:
                                dest[tag][k][w.strip()] += 1

                for child in node.iterchildren(tag=etree.Element):
                    nodeInfo(child, analysis)

            nodeInfo(root, analysis)

        def writeErrors():
            errorFile = f"{reportDir}/errors.txt"

            nErrors = 0

            with open(errorFile, "w") as fh:
                for (xmlFile, lines) in errors:
                    fh.write(f"{xmlFile}\n")
                    for line in lines:
                        fh.write(line)
                        nErrors += 1
                    fh.write("\n")

            console(
                f"{nErrors} error(s) in {len(errors)} file(s) written to {errorFile}"
            )

        def writeReport():
            reportFile = f"{reportDir}/elements.txt"
            with open(reportFile, "w") as fh:
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

                for (kind, label) in kindLabels.items():
                    fh.write(f"\n{label}\n")
                    for (tag, tagInfo) in sorted(analysis[kind].items()):
                        writeTagInfo(tag, tagInfo)

            console(f"{infoLines} info line(s) written to {reportFile}")

        def filterError(msg):
            return msg == (
                "Element 'graphic', attribute 'url': [facet 'pattern'] "
                "The value '' is not accepted by the pattern '\\S+'."
            )

        NS_RE = re.compile(r"""\{[^}]+}""")
        i = 0
        for (xmlFolder, xmlFiles) in self.getXML():
            console(xmlFolder)
            for xmlFile in xmlFiles:
                i += 1
                console(f"\r{i:>4} {xmlFile:<50}", newline=False)
                xmlPath = f"{sourceDir}/{xmlFolder}/{xmlFile}"
                tree = etree.parse(xmlPath, parser)
                if validator is not None and not validator.validate(tree):
                    theseErrors = []
                    for entry in validator.error_log:
                        msg = entry.message
                        msg = NS_RE.sub("", msg)
                        if filterError(msg):
                            continue
                        # domain = entry.domain_name
                        # typ = entry.type_name
                        level = entry.level_name
                        line = entry.line
                        col = entry.column
                        address = f"{line}:{col}"
                        theseErrors.append(f"{address:<6} {level:} {msg}\n")
                    if len(theseErrors):
                        console("ERROR")
                        errors.append((xmlFile, theseErrors))
                    continue

                root = tree.getroot()
                analyse(root, analysis)

        console("")
        writeReport()
        writeErrors()

        return True

    # SET UP CONVERSION

    def getConverter(self):
        """Initializes a converter.

        Returns
        -------
        object
            The `tf.convert.walker.CV` converter object, initialized.
        """
        tfDir = self.tfDir

        TF = Fabric(locations=tfDir)
        return CV(TF)

    def convert(self):
        """Implementation of the "convert" task.

        It sets up the `tf.convert.walker` machinery and runs it.

        Returns
        -------
        boolean
            Whether the conversion was successful.
        """
        slotType = "u"
        otext = {
            "fmt:text-orig-full": "{ch}",
            "sectionFeatures": "name,name,cn",
            "sectionTypes": "folder,file,chunk",
        }
        intFeatures = {"empty", "cn"}
        featureMeta = dict(
            name=dict(description="name of source folder or file"),
            cn=dict(description="number of a chunk within a file"),
            ch=dict(description="the unicode character of a slot"),
            str=dict(description="the text of a word"),
            after=dict(description="the text after a word till the next word"),
            empty=dict(
                description="whether a slot has been inserted in an empty element"
            ),
            ismeta=dict(
                description="whether a slot or word is in the teiHeader element"
            ),
        )
        self.featureMeta = featureMeta

        tfDir = self.tfDir
        generic = self.generic

        initTree(tfDir, fresh=True, gentle=True)

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

        The director function that walks through the TEI input must be conditioned
        by the properties defined in the TEI schema and the customised schema, if any,
        that describes the source.

        Also some special additions need to be programmed, such as an extra section
        level, word boundaries, etc.

        We collect all needed data, store it, and define a local director function
        that has access to this data.

        Returns
        -------
        function
            The local director function that has been constructed.
        """
        CHUNK_PARENTS = set(
            """
            teiHeader
            body
            """.strip().split()
        )

        CHUNK_ELEMS = set(
            """
            facsimile
            fsdDecl
            sourceDoc
            standOff
            """.strip().split()
        )

        PASS_THROUGH = set(
            """
            TEI
            teiHeader
            """.strip().split()
        )

        # CHECKING

        HY = "\u2010"  # hyphen

        IN_WORD_HYPHENS = {HY, "-"}

        TEI_LINK_ATTS = (
            "https://www.tei-c.org/release/doc/tei-p5-doc/en/html/REF-ATTS.html"
        )

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
        elemDefs = self.getElementInfo()

        # WALKERS

        WHITE_RE = re.compile(r"\s\s+", re.S)

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

        def isChunk(cur):
            """Whether the current element counts as a chunk node.

            Chunks are the third section level (folders are the first level,
            files the second level).
            Chunks are the immediate children of the `<teiHeader>` and the `<body>`
            elements, and a few other elements also count as chunks.

            Parameters
            ----------
            cur: dict
                Various pieces of data collected during walking
                and relevant for some next steps in the walk.

            Returns
            -------
            boolean
            """
            nest = cur["nest"]
            return len(nest) > 1 and (
                nest[-1] in CHUNK_ELEMS or nest[-2] in CHUNK_PARENTS
            )

        def isEndInPure(cur):
            """Whether the current end tag occurs in an element with pure content.

            If that is the case, then it is very likely that the end tag also
            marks the end of the current word.

            Parameters
            ----------
            cur: dict
                Various pieces of data collected during walking
                and relevant for some next steps in the walk.

            Returns
            -------
            boolean
            """
            nest = cur["nest"]
            return len(nest) > 1 and nest[-2] in cur["pureElems"]

        def startWord(cv, cur, ch):
            """Start a word node if necessary.

            Whenever we encounter a character, we determine
            whether it starts or ends a word, and if it starts
            one, this function takes care of the necessary actions.

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
            curWord = cur["word"]
            if not curWord:
                prevWord = cur["prevWord"]
                if prevWord is not None:
                    cv.feature(prevWord, after=cur["afterStr"])
                if ch is not None:
                    cur["word"] = cv.node("word")
                    if cur["inHeader"]:
                        cv.feature(cur["word"], ismeta=1)

            if ch is not None:
                cur["wordStr"] += ch

        def finishWord(cv, cur, ch):
            """Terminate a word node if necessary.

            Whenever we encounter a character, we determine
            whether it starts or ends a word, and if it ends
            one, this function takes care of the necessary actions.

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
            curWord = cur["word"]
            if curWord:
                cv.feature(curWord, str=cur["wordStr"])
                cv.terminate(curWord)
                cur["word"] = None
                cur["wordStr"] = ""
                cur["prevWord"] = curWord
                cur["afterStr"] = ""

            if ch is not None:
                cur["afterStr"] += ch

        def addSlot(cv, cur, ch):
            """Add a slot.

            Whenever we encounter a character, we add it as a new slot.
            If needed, we start/terminate word nodes as well.

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
            if ch is None or ch.isalnum() or ch in IN_WORD_HYPHENS:
                startWord(cv, cur, ch)
            else:
                finishWord(cv, cur, ch)

            s = cv.slot()
            cv.feature(s, ch=ch)
            if cur["inHeader"]:
                cv.feature(s, ismeta=1)

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
            if isChunk(cur):
                cur["chunkNum"] += 1
                cur["chunk"] = cv.node("chunk")
                cv.feature(cur["chunk"], cn=cur["chunkNum"])

            if tag == "teiHeader":
                cur["inHeader"] = True

            if tag not in PASS_THROUGH:
                curNode = cv.node(tag)
                cur["elems"].append(curNode)
                atts = {etree.QName(k).localname: v for (k, v) in node.attrib.items()}
                if len(atts):
                    cv.feature(curNode, **atts)

            if node.text:
                for ch in WHITE_RE.sub(" ", node.text):
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
            if isChunk(cur):
                cv.terminate(cur["chunk"])

            if tag == "teiHeader":
                cur["inHeader"] = False

            if tag not in PASS_THROUGH:
                if isEndInPure(cur):
                    finishWord(cv, cur, None)

                curNode = cur["elems"].pop()

                if not cv.linked(curNode):
                    s = cv.slot()
                    cv.feature(s, ch=ZWSP, empty=1)
                    if cur["inHeader"]:
                        cv.feature(s, ismeta=1)

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
                for ch in WHITE_RE.sub(" ", node.tail):
                    addSlot(cv, cur, ch)

        def director(cv):
            """Director function.

            Here we program a walk through the TEI sources.
            At every step of the walk we fire some actions that build TF nodes
            and assign features for them.

            Because everything is rather dynamic, we generate fairly standard
            metadata for the features, namely a link to the tei website.

            Parameters
            ----------
            cv: object
                The convertor object, needed to issue actions.
            """
            cur = {}
            cur["pureElems"] = {
                x for (x, (typ, mixed)) in elemDefs.items() if not mixed
            }

            i = 0
            for (xmlFolder, xmlFiles) in self.getXML():
                console(xmlFolder)

                cur["folder"] = cv.node("folder")
                cv.feature(cur["folder"], name=xmlFolder)

                for xmlFile in xmlFiles:
                    i += 1
                    console(f"\r{i:>4} {xmlFile:<50}", newline=False)

                    cur["file"] = cv.node("file")
                    cv.feature(cur["file"], name=xmlFile.removesuffix(".xml"))

                    with open(f"{sourceDir}/{xmlFolder}/{xmlFile}") as fh:
                        text = fh.read()
                        text = transformFunc(text)
                        tree = etree.parse(text, parser)
                        root = tree.getroot()
                        cur["inHeader"] = False
                        cur["nest"] = []
                        cur["elems"] = []
                        cur["chunkNum"] = 0
                        cur["word"] = None
                        cur["prevWord"] = None
                        cur["wordStr"] = ""
                        cur["afterStr"] = ""
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
                        description=f"this is TEI attribute {fName}, see {TEI_LINK_ATTS}",
                        valueType="str",
                    )
            console("source reading done")
            return True

        return director

    def load(self):
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
        tfDir = self.tfDir

        if not os.path.exists(tfDir):
            console(f"Directory {ux(tfDir)} does not exist.")
            console("No tf found, nothing to load")
            return False

        TF = Fabric(locations=[tfDir])
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
            `TEI` object.

        Returns
        -------
        boolean
            Whether all tasks have executed successfully.
        """
        sourceDir = self.sourceDir
        reportDir = self.reportDir
        tfDir = self.tfDir

        if test is not None:
            self.testMode = test

        good = True

        if check:
            console(f"TEI to TF checking: {ux(sourceDir)} => {ux(reportDir)}")
            good = self.check()

        if good and convert:
            console(f"TEI to TF converting: {ux(sourceDir)} => {ux(tfDir)}")
            good = self.convert()

        if good and load:
            good = self.load()

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
        programRep = "TEI-converter" if program is None else program
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
