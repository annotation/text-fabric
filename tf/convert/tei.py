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

We use [lxml](https://lxml.de) for XML parsing. During `convert` it is not used
in validating mode, but we can trigger a validation step during `check`.

However, some information about the elements, in particular whether they allow
mixed content or not, will be read off the schemas, and will be used
during conversion.
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
from tf.core.helpers import initTree, unexpanduser as ux
from tt.xmlschema import Analysis as AnalysisCls


class TEI:
    def __init__(
        self,
        sourceDir=None,
        schemaFile=None,
        generic={},
        reportDir=None,
        transform=None,
        tfDir=None,
        testSet=set(),
    ):
        self.sourceDir = sourceDir
        self.schemaFile = schemaFile
        self.generic = generic
        self.reportDir = reportDir
        self.transform = transform
        self.tfDir = tfDir
        self.testMode = False
        self.testSet = testSet

    # SOURCE READING

    # NS1 = "{http://www.tei-c.org/ns/1.0}"
    # NS2 = "{http://www.w3.org/XML/1998/namespace}"
    # NS3 = "{http://mondrian.huygens.knaw.nl/}"

    @staticmethod
    def help(program):
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
        return etree.XMLParser(
            remove_blank_text=True,
            collect_ids=False,
            remove_comments=True,
            remove_pis=True,
        )

    def getValidator(self):
        schemaFile = self.schemaFile

        if schemaFile is None:
            return None

        schemaDoc = etree.parse(schemaFile)
        return etree.XMLSchema(schemaDoc)

    def getElementInfo(self):
        schemaFile = self.schemaFile

        Analysis = AnalysisCls(schemaFile)
        if not Analysis.good:
            quit()
        defs = Analysis.interpret()
        return {name: (typ, mixed) for (name, typ, mixed) in defs}

    def getXML(self):
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
        tfDir = self.tfDir

        TF = Fabric(locations=tfDir)
        return CV(TF)

    def convert(self):
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
            )
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
            """Handle all elements in the XML file."""
            tag = etree.QName(node.tag).localname
            cur["nest"].append(tag)

            beforeChildren(cv, cur, node, tag)

            for child in node.iterchildren(tag=etree.Element):
                walkNode(cv, cur, child)

            afterChildren(cv, cur, node, tag)
            cur["nest"].pop()
            afterTag(cv, cur, node, tag)

        def isChunk(cur):
            nest = cur["nest"]
            return len(nest) > 1 and (
                nest[-1] in CHUNK_ELEMS or nest[-2] in CHUNK_PARENTS
            )

        def isEndInPure(cur):
            nest = cur["nest"]
            return len(nest) > 1 and nest[-2] in cur["pureElems"]

        def startWord(cv, cur, ch):
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
            if ch is None or ch.isalnum() or ch in IN_WORD_HYPHENS:
                startWord(cv, cur, ch)
            else:
                finishWord(cv, cur, ch)

            s = cv.slot()
            cv.feature(s, ch=ch)
            if cur["inHeader"]:
                cv.feature(s, ismeta=1)

        def beforeChildren(cv, cur, node, tag):
            """Node actions before dealing with the children."""
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
            """Node actions after dealing with the children, but before the end tag."""
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
            """Node actions after dealing with the children and after the end tag."""
            if node.tail:
                for ch in WHITE_RE.sub(" ", node.tail):
                    addSlot(cv, cur, ch)

        def director(cv):
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
                    cv.feature(cur["file"], name=xmlFile)

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

    def loadTf(self):
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

    def task(self, check=False, convert=False, load=False, test=None):
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
            good = self.loadTf()

        return good

    def run(self, program=None):
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
