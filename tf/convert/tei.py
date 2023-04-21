"""
# TEI import

You can convert any TEI source into TF by specifying a few details about the source.

Text-Fabric then invokes the `tf.convert.walker` machinery to produce a Text-Fabric
dataset out of the source.

Text-Fabric knows the TEI elements, because it will read and parse the complete
TEI schema. From this the set of complex, mixed elements is distilled.

If the TEI source conforms to a customised TEI schema, you can pass it to the TEI
importer, and it will read it and override the generic information of the TEI elements.

The converter goes the extra mile: it generates a TF-app and documentation
(an *about.md* file and a *transcription.md* file), in such a way that the Text-Fabric
browser is instantly usable.

The TEI conversion is rather straightforward because of some conventions
that cannot be changed.

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
`TEI.task()` method.

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

The resulting script will look like
[tfFromTeiExample.py](https://github.com/annotation/text-fabric/blob/master/tf/convert/tfFromTeiExample.py)
which you can use as a starting point.
"""

import sys
import collections
import re
from textwrap import dedent
from io import BytesIO
from subprocess import run

import yaml
from lxml import etree
from ..parameters import BRANCH_DEFAULT_NEW
from ..fabric import Fabric
from ..core.helpers import console
from ..convert.walker import CV
from ..core.timestamp import AUTO, DEEP, TERSE
from ..core.helpers import mergeDict
from ..core.files import (
    abspath,
    expanduser as ex,
    unexpanduser as ux,
    getLocation,
    initTree,
    dirNm,
    dirExists,
    fileExists,
    fileCopy,
    fileRemove,
    scanDir,
)

from ..tools.xmlschema import Analysis


ZWSP = "\u200b"  # zero-width space

CSS_REND = dict(
    h1=(
        "heading of level 1",
        dedent(
            """
        font-size: xx-large;
        font-weight: bold;
        margin-top: 3rem;
        margin-bottom: 1rem;
        """
        ),
    ),
    h2=(
        "heading of level 2",
        dedent(
            """
        font-size: x-large;
        font-weight: bold;
        margin-top: 2rem;
        margin-bottom: 1rem;
        """
        ),
    ),
    h3=(
        "heading of level 3",
        dedent(
            """
        font-size: large;
        font-weight: bold;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        """
        ),
    ),
    h4=(
        "heading of level 4",
        dedent(
            """
        font-size: large;
        font-style: italic;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        """
        ),
    ),
    h5=(
        "heading of level 5",
        dedent(
            """
        font-size: medium;
        font-weight: bold;
        font-variant: small-caps;
        margin-top: 0.5rem;
        margin-bottom: 0.25rem;
        """
        ),
    ),
    h6=(
        "heading of level 6",
        dedent(
            """
        font-size: medium;
        font-weight: normal;
        font-variant: small-caps;
        margin-top: 0.25rem;
        margin-bottom: 0.125rem;
        """
        ),
    ),
    italic=(
        "cursive font style",
        dedent(
            """
        font-style: italic;
        """
        ),
    ),
    bold=(
        "bold font weight",
        dedent(
            """
        font-weight: bold;
        """
        ),
    ),
    underline=(
        "underlined text",
        dedent(
            """
        text-decoration: underline;
        """
        ),
    ),
    center=(
        "horizontally centered text",
        dedent(
            """
        text-align: center;
        """
        ),
    ),
    large=(
        "large font size",
        dedent(
            """
        font-size: large;
        """
        ),
    ),
    spaced=(
        "widely spaced between characters",
        dedent(
            """
        letter-spacing: .2rem;
        """
        ),
    ),
    margin=(
        "in the margin",
        dedent(
            """
        position: relative;
        top: -0.3em;
        font-weight: bold;
        color: #0000ee;
        """
        ),
    ),
    above=(
        "above the line",
        dedent(
            """
        position: relative;
        top: -0.3em;
        """
        ),
    ),
    below=(
        "below the line",
        dedent(
            """
        position: relative;
        top: 0.3em;
        """
        ),
    ),
    small_caps=(
        "small-caps font variation",
        dedent(
            """
        font-variant: small-caps;
        """
        ),
    ),
    sub=(
        "as subscript",
        dedent(
            """
        vertical-align: sub;
        font-size: small;
        """
        ),
    ),
    super=(
        "as superscript",
        dedent(
            """
        vertical-align: super;
        font-size: small;
        """
        ),
    ),
)
CSS_REND_ALIAS = dict(
    italic="italics i",
    bold="b",
    underline="ul",
    spaced="spat",
    small_caps="smallcaps sc",
    super="sup",
)


KNOWN_RENDS = set()
REND_DESC = {}

NEST = "nest"
SLOT = "slot"
WORD = "word"
CHAR = "char"
TOKEN = "token"

FOLDER = "folder"
FILE = "file"
CHAPTER = "chapter"
CHUNK = "chunk"


def makeCssInfo():
    rends = ""

    for (rend, (description, css)) in sorted(CSS_REND.items()):
        aliases = CSS_REND_ALIAS.get(rend, "")
        aliases = sorted(set(aliases.split()) | {rend})
        for alias in aliases:
            KNOWN_RENDS.add(alias)
            REND_DESC[alias] = description
        selector = ",".join(f".r_{alias}" for alias in aliases)
        contribution = f"\n{selector} {{{css}}}\n"
        rends += contribution

    return rends


SECTION_MODELS = dict(
    I=dict(levels=(list, [FOLDER, FILE, CHUNK])),
    II=dict(
        levels=(list, [CHAPTER, CHUNK]),
        element=(str, "head"),
        attributes=(dict, {}),
    ),
)
SECTION_MODEL_DEFAULT = "I"


def checkSectionModel(sectionModel):
    if sectionModel is None:
        model = SECTION_MODEL_DEFAULT
        console(f"WARNING: No section model specified. Assuming model {model}.")
        properties = {k: v[1] for (k, v) in SECTION_MODELS[model].items()}
        return dict(model=model, properties=properties)

    if type(sectionModel) is str:
        if sectionModel in SECTION_MODELS:
            sectionModel = dict(model=sectionModel)
        else:
            console(f"WARNING: unknown section model: {sectionModel}")
            return False

    elif type(sectionModel) is not dict:
        console(
            f"ERROR: Section model must be a dict. You passed a {type(sectionModel)}"
        )
        return False

    model = sectionModel.get("model", None)
    if model is None:
        model = SECTION_MODEL_DEFAULT
        console(f"WARNING: No section model specified. Assuming model {model}.")
        sectionModel["model"] = model
    if model not in SECTION_MODELS:
        console(f"WARNING: unknown section model: {sectionModel}")
        return False

    properties = {k: v for (k, v) in sectionModel.items() if k != "model"}
    modelProperties = SECTION_MODELS[model]

    good = True
    delKeys = []

    for (k, v) in properties.items():
        if k not in modelProperties:
            console(f"WARNING: ignoring unknown model property {k}={v}")
            delKeys.append(k)
        elif type(v) is not modelProperties[k][0]:
            console(
                f"ERROR: property {k} should have type {modelProperties[k][0]}"
                f" but {v} has type {type(v)}"
            )
            good = False
    if good:
        for k in delKeys:
            del properties[k]

    for (k, v) in modelProperties.items():
        if k not in properties:
            console(f"WARNING: model property {k} not specified, taking default {v[1]}")
            properties[k] = v[1]

    if not good:
        return False

    return dict(model=model, properties=properties)


def tweakTrans(template, wordAsSlot, tokenBased, sectionModel, sectionProperties):
    if wordAsSlot:
        slot = WORD
        slotc = "Word"
        slotf = "words"
        xslot = "`word`"
    else:
        slotc = "Char"
        slot = CHAR
        slotf = "characters"
        xslot = "`char` and `word`"
    if tokenBased:
        slot = TOKEN
        slotc = "Token"
        slotf = "tokens"
        xslot = "`token`"
        tokenGen = dedent(
            """
            Tokens and sentence boundaries have been generated by a Natural Language
            Pipeline, such as Spacy.
            """
        )
        tokenWord = "token"
        hasToken = "Yes"
    else:
        tokenGen = ""
        tokenWord = "word"
        hasToken = "No"

    levelNames = sectionProperties["levels"]

    if sectionModel == "II":
        nLevels = "2"
        chapterSection = levelNames[0]
        chunkSection = levelNames[1]
        head = sectionProperties["element"]
        attributes = sectionProperties["attributes"]
        propertiesRaw = repr(sectionProperties)
        properties = (
            "".join(
                f"\t*\t`{att}` = `{val}`\n" for (att, val) in sorted(attributes.items())
            )
            if attributes
            else "\t*\t*no attribute properties*\n"
        )
    else:
        nLevels = "3"
        folderSection = levelNames[0]
        fileSection = levelNames[1]
        chunkSection = levelNames[2]

    rendDesc = "\n".join(
        f"`{val}` | {desc}" for (val, desc) in sorted(REND_DESC.items())
    )
    modelKeepRe = re.compile(rf"«(?:begin|end)Model{sectionModel}»")
    modelRemoveRe = re.compile(r"«beginModel([^»]+)».*?«endModel\1»", re.S)
    slotKeepRe = re.compile(rf"«(?:begin|end)Slot{slot}»")
    slotRemoveRe = re.compile(r"«beginSlot([^»]+)».*?«endSlot\1»", re.S)
    tokenKeepRe = re.compile(rf"«(?:begin|end)Token{hasToken}»")
    tokenRemoveRe = re.compile(r"«beginToken([^»]+)».*?«endToken\1»", re.S)

    skipVars = re.compile(r"«[^»]+»")

    text = (
        template.replace("«slot»", slot)
        .replace("«Slot»", slotc)
        .replace("«slotf»", slotf)
        .replace("«char and word»", xslot)
        .replace("«tokenWord»", tokenWord)
        .replace("«token generation»", tokenGen)
        .replace("«nLevels»", nLevels)
        .replace("«sectionModel»", sectionModel)
        .replace("«rendDesc»", rendDesc)
    )
    if sectionModel == "II":
        text = (
            text.replace("«head»", head)
            .replace("«properties»", properties)
            .replace("«propertiesRaw»", propertiesRaw)
            .replace("«chapter»", chapterSection)
            .replace("«chunk»", chunkSection)
        )
    else:
        text = (
            text.replace("«folder»", folderSection)
            .replace("«file»", fileSection)
            .replace("«chunk»", chunkSection)
        )

    text = tokenKeepRe.sub("", text)
    text = tokenRemoveRe.sub("", text)
    text = modelKeepRe.sub("", text)
    text = modelRemoveRe.sub("", text)
    text = slotKeepRe.sub("", text)
    text = slotRemoveRe.sub("", text)

    text = skipVars.sub("", text)
    return text


class TEI:
    def __init__(
        self,
        sourceVersion="0.1",
        schema=None,
        testSet=set(),
        wordAsSlot=True,
        sectionModel=None,
        generic={},
        transform=None,
        tfVersion="0.1",
        appConfig={},
        docMaterial={},
        force=False,
        verbose=-1,
    ):
        """Converts TEI to TF.

        For documentation of the resulting encoding, read the
        [transcription template](https://github.com/annotation/text-fabric/blob/master/tf/convert/app/transcription.md).

        Below we describe how to control the conversion machinery.

        We adopt a fair bit of "convention over configuration" here, in order to lessen
        the burden for the user of specifying so many details.

        Based on current directory from where the script is called,
        it defines all the ingredients to carry out
        a `tf.convert.walker` conversion of the TEI input.

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

        ### `tei`

        *Location of the TEI-XML sources.*

        **If it does not exist, the program aborts with an error.**

        Several levels of subfolders are assumed:

        1.  the version of the source (this could be a date string).
        2.  volumes/collections of documents. The subfolder `__ignore__` is ignored.
        3.  the TEI documents themselves, conforming to the TEI schema or some
            customisation of it.

        ### `schema`

        *Location of the TEI-XML schemas against which the sources can be validated.*

        It should be an `.xsd` file, and the parameter `schema` may specify
        its name (without extension).

        !!! note "Multiple `.xsd` files"
            When you started with a `.rng` file and used `tf.tools.xmlschema` to
            convert it to `xsd`, you may have got multiple `.xsd` files.
            One of them has the same base name as the original `.rng` file,
            and you should pass that name. It will import the remaining `.xsd` files,
            so do not throw them away.

        We use this file as custom TEI schema,
        but to be sure, we still analyse the full TEI schema and
        use the schema passed here as a set of overriding element definitions.

        If no schema is specified, we use the *full* TEI schema.

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
        These settings can be overriden by the parameter `appConfig`.
        Also a default `display.css` file and a logo are added.

        If such a file already exists, it will be left untouched and a generated file
        is put next to the item, with `_generated` in the file name.

        This behaviour can be modified by passing `force=True` to the initialization
        of the TEI object.

        ### `docs`

        Location of additional documentation.
        This can be generated or had-written material, or a mixture of the two.

        !!! caution "Dataloss by overwriting app and docs files.
            When `force` is `False`, the app docs files will not be overwritten by
            generated files. Instead, the generated files are produced
            alongside them, with `_generated` in their names.
            These `_generated` files will be overwritten by successive runs
            of the `app` task.

            When you have generated your files, and they cannot be improved anymore,
            be sure to set `force` to `False`.

            Then you can edit the apps and docs files by hand, and they will not be
            overwritten inadvertently.

        Parameters
        ----------

        sourceVersion: string, optional "0.1"
            Version of the source files. This is the name of a top-level
            subfolder of the `tei` input folder.

        schema: string, optional None
            Which XML schema to be used, if not specified we fall back on full TEI.
            If specified, leave out the `.xsd` extension. The file is relative to the
            `schema` directory.

        testSet: set, optional empty
            A set of file names. If you run the conversion in test mode
            (pass `test` as argument to the `TEI.task()` method),
            only the files in the test set are converted.

        wordAsSlot: boolean, optional False
            Whether to take words as the basic entities (slots).
            If not, the characters are taken as basic entities.
        sectionModel: dict, optional {}
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

        generic: dict, optional {}
            Metadata for all generated TF feature.

        transform: function, optional None
            If not None, a function that transforms text to text, used
            as a preprocessing step for each input xml file.

        tfVersion: string, optional "0.1"
            Version of the generated tf files. This is the name of a top-level
            subfolder of the `tf` output folder.

        appConfig: dict, optional {}
            Additional configuration settings, which will override the initial
            settings.

        docMaterial: dict, optional {}
            Additional documentation:

            *   under key `about`: colofon-like information;
            *   under key `trans`: additional information about the
                transcription and encoding details.

        force: boolean, optional False
            If True, the `app` task will overwrite existing files with generated
            files, and remove any files with `_generated` in the name.
            Except for the logo, which will not be overwritten.

        verbose: integer, optional -1
            Produce no (-1), some (0) or many (1) orprogress and reporting messages
        """
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
        sourceDir = f"{refDir}/tei/{sourceVersion}"
        reportDir = f"{refDir}/report"
        tfDir = f"{refDir}/tf"
        appDir = f"{refDir}/app"
        docsDir = f"{refDir}/docs"

        self.refDir = refDir
        self.sourceDir = sourceDir
        self.reportDir = reportDir
        self.tfDir = tfDir
        self.appDir = appDir
        self.docsDir = docsDir
        self.backend = backend
        self.org = org
        self.repo = repo
        self.relative = relative

        self.good = True

        if sourceDir is None or not dirExists(sourceDir):
            console(f"Source location does not exist: {sourceDir}")
            self.good = False
            return

        self.schema = schema
        self.schemaFile = None if schema is None else f"{refDir}/schema/{schema}.xsd"
        self.sourceVersion = sourceVersion
        self.testMode = False
        self.testSet = testSet
        self.wordAsSlot = wordAsSlot
        sectionModel = checkSectionModel(sectionModel)
        if not sectionModel:
            self.good = False
            return

        self.sectionModel = sectionModel["model"]
        sectionProperties = sectionModel.get("properties", None)
        self.sectionProperties = sectionProperties
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

        self.generic = generic
        self.transform = transform
        self.tfVersion = tfVersion
        self.tfPath = f"{tfDir}/{tfVersion}"
        if (
            "provenanceSpec" not in appConfig
            or "branch" not in appConfig["provenanceSpec"]
        ):
            appConfig.setdefault("provenanceSpec", {})["branch"] = BRANCH_DEFAULT_NEW
        self.appConfig = appConfig
        self.docMaterial = docMaterial
        self.force = force
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
            app:
                just configures the TF-app for the result;
            apptoken:
                just modifies the TF-app to make it token- instead of character-based;
            browse:
                just starts the text-fabric browser on the result;

        flags:
            -test, +test:
                whether to run in test mode
            -force, +force:
                whether to overwrite previously existing app files when
                generating app files
            +verbose, ++verbose:
                Produce more progress and reporting messages
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
        )

    def getValidator(self):
        """Parse the schema.

        A parsed schema can be used for XML-validation.
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

    def getElementInfo(self, verbose=None):
        """Analyse the schema.

        The XML schema has useful information about the XML elements that
        occur in the source. Here we extract that information and make it
        fast-accessible.

        Parameters
        ----------
        verbose: boolean, optional None
            Produce more progress and reporting messages
            If not passed, take the verbose member of this object.

        Returns
        -------
        dict
            Keyed by element name (without namespaces), where the value
            for each name is a tuple of booleans: whether the element is simple
            or complex; whether the element allows mixed content or only pure content.
        """
        if verbose is not None:
            self.verbose = verbose
        verbose = self.verbose
        schemaFile = self.schemaFile

        self.elementDefs = {}

        A = Analysis(verbose=verbose)
        A.configure(override=schemaFile)
        A.interpret()
        if not A.good:
            return

        self.elementDefs = {name: (typ, mixed) for (name, typ, mixed) in A.getDefs()}

    def getXML(self):
        """Make an inventory of the TEI source files.

        Returns
        -------
        tuple of tuple | string
            If section model I is in force:

            The outer tuple has sorted entries corresponding to folders under the
            TEI input directory.
            Each such entry consists of the folder name and an inner tuple
            that contains the file names in that folder, sorted.

            If section model II is in force:

            It is the name of the single XML file.
        """
        verbose = self.verbose
        sourceDir = self.sourceDir
        sectionModel = self.sectionModel
        if verbose == 1:
            console(f"Section model {sectionModel}")

        if sectionModel == "I":
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
                            if not (
                                fileName.lower().endswith(".xml") and file.is_file()
                            ):
                                continue
                            if testMode and fileName not in testSet:
                                continue
                            xmlFilesRaw[folderName].append(fileName)

            xmlFiles = tuple(
                (folderName, tuple(sorted(fileNames)))
                for (folderName, fileNames) in sorted(xmlFilesRaw.items())
            )
            return xmlFiles

        if sectionModel == "II":
            xmlFile = None
            with scanDir(sourceDir) as fh:
                for file in fh:
                    fileName = file.name
                    if not (fileName.lower().endswith(".xml") and file.is_file()):
                        continue
                    xmlFile = fileName
                    break
            return xmlFile

    def checkTask(self):
        """Implementation of the "check" task.

        It validates the TEI, but only if a schema file has been passed explicitly
        when constructing the `TEI()` object.

        Then it makes an inventory of all elements and attributes in the TEI files.

        If tags are used in multiple namespaces, it will be reported.

        !!! caution "Conflation of namespaces"
            The TEI to TF conversion does constructs node types and attributes
            without taking namespaces into account.
            However, the parsing process is namespace aware.

        The inventory lists all elements and attributes, and many attribute values.
        But is represents any digit with `n`, and some attributes that contain
        ids or keywords, are reduced to the value `x`.

        This information reduction helps to get a clear overview.

        It writes reports to the `reportDir`:

        *   `errors.txt`: validation errors
        *   `elements.txt`: element/attribute inventory.
        """
        if not self.good:
            return

        verbose = self.verbose

        sourceDir = self.sourceDir
        reportDir = self.reportDir
        docsDir = self.docsDir
        sectionModel = self.sectionModel

        if verbose == 1:
            console(f"TEI to TF checking: {ux(sourceDir)} => {ux(reportDir)}")

        kindLabels = dict(
            format="Formatting Attributes",
            keyword="Keyword Attributes",
            rest="Remaining Attributes and Elements",
        )
        getStore = lambda: collections.defaultdict(  # noqa: E731
            lambda: collections.defaultdict(collections.Counter)
        )
        analysis = {x: getStore() for x in kindLabels}
        errors = []
        tagByNs = collections.defaultdict(collections.Counter)

        parser = self.getParser()
        validator = self.getValidator()
        self.getElementInfo()
        elementDefs = self.elementDefs

        initTree(reportDir)
        initTree(docsDir)

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
                    nodeInfo(child)

            nodeInfo(root)

        def writeErrors():
            errorFile = f"{reportDir}/errors.txt"

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
            errorFile = f"{reportDir}/namespaces.txt"

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
            reportFile = f"{reportDir}/elements.txt"
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
                    if tag:
                        (typ, mixed) = elementDefs[tag]
                        extraInfo = f"{'mixed' if mixed else 'pure '}: "
                    else:
                        extraInfo = ""
                    fh.write(
                        f"{nl}\t{extraInfo}{tagRep:<18} "
                        f"{attRep:<18} {amount:>5}x {val}\n"
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

        def writeDoc():
            teiUrl = "https://tei-c.org/release/doc/tei-p5-doc/en/html"
            elUrlPrefix = f"{teiUrl}/ref-"
            attUrlPrefix = f"{teiUrl}/REF-ATTS.html#"
            docFile = f"{docsDir}/elements.md"
            with open(docFile, "w", encoding="utf8") as fh:
                fh.write(
                    dedent(
                        """
                        # Element and attribute inventory

                        Table of contents

                        """
                    )
                )
                for label in kindLabels.values():
                    labelAnchor = label.replace(" ", "-")
                    fh.write(f"*\t[{label}](#{labelAnchor})\n")

                fh.write("\n")

                tableHeader = dedent(
                    """
                    element | attribute | value | amount
                    --- | --- | --- | ---
                    """
                )

                def writeAttInfo(tag, att, attInfo):
                    tagRep = " " if tag == "" else f"[{tag}]({elUrlPrefix}{tag}.html)"
                    attRep = " " if att == "" else f"[{att}]({attUrlPrefix}{att})"
                    atts = sorted(attInfo.items())
                    (val, amount) = atts[0]
                    valRep = f"`{val}`" if val else ""
                    fh.write(f"{tagRep} | {attRep} | {valRep} | {amount}\n")
                    for (val, amount) in atts[1:]:
                        valRep = f"`{val}`" if val else ""
                        fh.write(f"""\u00a0| | {valRep} | {amount}\n""")

                def writeTagInfo(tag, tagInfo):
                    tags = sorted(tagInfo.items())
                    (att, attInfo) = tags[0]
                    writeAttInfo(tag, att, attInfo)
                    for (att, attInfo) in tags[1:]:
                        writeAttInfo("", att, attInfo)

                for (kind, label) in kindLabels.items():
                    fh.write(f"## {label}\n{tableHeader}")
                    for (tag, tagInfo) in sorted(analysis[kind].items()):
                        writeTagInfo(tag, tagInfo)
                    fh.write("\n")

        def filterError(msg):
            return msg == (
                "Element 'graphic', attribute 'url': [facet 'pattern'] "
                "The value '' is not accepted by the pattern '\\S+'."
            )

        NS_RE = re.compile(r"""\{[^}]+}""")

        def doXMLFile(xmlPath):
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
                    console("ERROR\n")
                    errors.append((xmlFile, theseErrors))
                return

            root = tree.getroot()
            analyse(root, analysis)

        if sectionModel == "I":
            i = 0
            for (xmlFolder, xmlFiles) in self.getXML():
                console(f"Start folder {xmlFolder}:")
                for xmlFile in xmlFiles:
                    i += 1
                    console(f"\r{i:>4} {xmlFile:<50}", newline=False)
                    xmlPath = f"{sourceDir}/{xmlFolder}/{xmlFile}"
                    doXMLFile(xmlPath)
                console("")
                console(f"End   folder {xmlFolder}")

        elif sectionModel == "II":
            xmlFile = self.getXML()
            if xmlFile is None:
                console("No XML files found!")
                return False

            xmlPath = f"{sourceDir}/{xmlFile}"
            doXMLFile(xmlPath)

        console("")
        writeReport()
        writeDoc()
        writeErrors()
        writeNamespaces()

    # SET UP CONVERSION

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
        TEI_HEADER = "teiHeader"

        TEXT_ANCESTOR = "text"
        TEXT_ANCESTORS = set(
            """
            front
            body
            back
            group
            """.strip().split()
        )
        CHUNK_PARENTS = TEXT_ANCESTORS | {TEI_HEADER}

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
            """.strip().split()
        )

        # CHECKING

        HY = "\u2010"  # hyphen

        IN_WORD_HYPHENS = {HY, "-"}

        verbose = self.verbose
        sourceDir = self.sourceDir
        wordAsSlot = self.wordAsSlot
        featureMeta = self.featureMeta
        intFeatures = self.intFeatures
        transform = self.transform
        chunkLevel = self.chunkLevel

        transformFunc = (
            (lambda x: x)
            if transform is None
            else (lambda x: BytesIO(transform(x).encode("utf-8")))
        )

        parser = self.getParser()
        self.getElementInfo(verbose=-1)

        # WALKERS

        WHITE_TRIM_RE = re.compile(r"\s+", re.S)
        NON_NAME_RE = re.compile(r"[^a-zA-Z0-9_]+", re.S)

        NOTE_LIKE = set(
            """
            note
            """.strip().split()
        )
        EMPTY_ELEMENTS = set(
            """
            addSpan
            alt
            anchor
            anyElement
            attRef
            binary
            caesura
            catRef
            cb
            citeData
            classRef
            conversion
            damageSpan
            dataFacet
            default
            delSpan
            elementRef
            empty
            equiv
            fsdLink
            gb
            handShift
            iff
            lacunaEnd
            lacunaStart
            lb
            link
            localProp
            macroRef
            milestone
            move
            numeric
            param
            path
            pause
            pb
            ptr
            redo
            refState
            specDesc
            specGrpRef
            symbol
            textNode
            then
            undo
            unicodeProp
            unihanProp
            variantEncoding
            when
            witEnd
            witStart
            """.strip().split()
        )
        # N.B. We will alway generate newlines at the closing tags of
        # elements that occur in pure elements
        NEWLINE_ELEMENTS = set(
            """
            ab
            cb
            l
            lb
            lg
            list
            p
            pb
            seg
            table
            u
            """.strip().split()
        )

        def makeNameLike(x):
            return NON_NAME_RE.sub("_", x).strip("_")

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
            cur[NEST].append(tag)

            beforeChildren(cv, cur, node, tag)

            for child in node.iterchildren(tag=etree.Element):
                walkNode(cv, cur, child)

            afterChildren(cv, cur, node, tag)
            cur[NEST].pop()
            afterTag(cv, cur, node, tag)

        def isChapter(cur):
            """Whether the current element counts as a chapter node.

            ## Model I

            Not relevant: there are no chapter nodes inside an XML file.

            ## Model II

            Chapters are the highest section level (the only lower level is chunks).

            Chapters come in two kinds:

            *   the TEI header;
            *   the immediate children of `<text>`
                except `<front>`, `<body>`, `<back>`, `<group>`;
            *   the immediate children of
                `<front>`, `<body>`, `<back>`, `<group>`.

            Parameters
            ----------
            cur: dict
                Various pieces of data collected during walking
                and relevant for some next steps in the walk.

            Returns
            -------
            boolean
            """
            sectionModel = self.sectionModel

            if sectionModel == "II":
                nest = cur[NEST]
                nNest = len(nest)

                if nNest > 0 and nest[-1] in EMPTY_ELEMENTS:
                    return False

                outcome = nNest > 0 and (
                    nest[-1] == TEI_HEADER
                    or (
                        nNest > 1
                        and (
                            nest[-2] in TEXT_ANCESTORS
                            or nest[-2] == TEXT_ANCESTOR
                            and nest[-1] not in TEXT_ANCESTORS
                        )
                    )
                )
                if outcome:
                    cur["chapterElems"].add(nest[-1])

                return outcome

            return False

        def isChunk(cur):
            """Whether the current element counts as a chunk node.

            ## Model I

            Chunks are the lowest section level (the higher levels are folders
            and then files)

            Chunks are the immediate children of the `<teiHeader>` and the `<body>`
            elements, and a few other elements also count as chunks.

            ## Model II

            Chunks are the lowest section level (the only higher level is chapters).

            Chunks are the immediate children of the chapters, and they come in two
            kinds: the ones that are `<p>` elements, and the rest.

            Deviation from this rule:

            *   If a chapter is a mixed content node, then it is also a chunk.
                and its subelements are not chunks

            Parameters
            ----------
            cur: dict
                Various pieces of data collected during walking
                and relevant for some next steps in the walk.

            Returns
            -------
            boolean
            """
            sectionModel = self.sectionModel

            nest = cur[NEST]
            nNest = len(nest)

            if sectionModel == "II":
                meChptChnk = isChapter(cur) and cur[NEST][-1] not in cur["pureElems"]
                outcome = nNest > 1 and (
                    meChptChnk
                    or (
                        nest[-2] == TEI_HEADER
                        or (
                            nNest > 2
                            and (
                                nest[-3] in TEXT_ANCESTORS
                                and nest[-1] not in EMPTY_ELEMENTS
                                or nest[-3] == TEXT_ANCESTOR
                                and nest[-2] not in TEXT_ANCESTORS
                            )
                            and cur[NEST][-2] in cur["pureElems"]
                        )
                    )
                )
                if outcome:
                    cur["chunkElems"].add(nest[-1])
                return outcome

            outcome = nNest > 0 and (
                nest[-1] in CHUNK_ELEMS
                or (
                    nNest > 1
                    and (
                        nest[-2] in CHUNK_PARENTS
                        and nest[-1] not in EMPTY_ELEMENTS
                        or nest[-2] == TEXT_ANCESTOR
                        and nest[-1] not in TEXT_ANCESTORS
                    )
                )
            )
            if outcome:
                cur["chunkElems"].add(nest[-1])
            return outcome

        def isPure(cur):
            """Whether the current tag has pure content.

            Parameters
            ----------
            cur: dict
                Various pieces of data collected during walking
                and relevant for some next steps in the walk.

            Returns
            -------
            boolean
            """
            nest = cur[NEST]
            return len(nest) == 0 or len(nest) > 0 and nest[-1] in cur["pureElems"]

        def isEndInPure(cur):
            """Whether the current end tag occurs in an element with pure content.

            If that is the case, then it is very likely that the end tag also
            marks the end of the current word.

            And we should not strip spaces after it.

            Parameters
            ----------
            cur: dict
                Various pieces of data collected during walking
                and relevant for some next steps in the walk.

            Returns
            -------
            boolean
            """
            nest = cur[NEST]
            return len(nest) > 1 and nest[-2] in cur["pureElems"]

        def hasMixedAncestor(cur):
            """Whether the current tag has an ancestor with mixed content.

            We use this in case a tag ends in an element with pure content.
            We should then add whitespace to separate it from the next
            element of its parent.

            If the whole stack of element has pure content, we add
            a newline, because then we are probably in the TEI header,
            and things are most clear if they are on separate lines.

            But if one of the ancestors has mixed content, we are typically
            in some structured piece of information within running text,
            such as change markup. In this case we want to add merely a space.

            And we should not strip spaces after it.

            Parameters
            ----------
            cur: dict
                Various pieces of data collected during walking
                and relevant for some next steps in the walk.

            Returns
            -------
            boolean
            """
            nest = cur[NEST]
            return any(n in cur["mixedElems"] for n in nest[0:-1])

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
            curWord = cur[WORD]
            if not curWord:
                prevWord = cur["prevWord"]
                if prevWord is not None:
                    cv.feature(prevWord, after=cur["afterStr"])
                if ch is not None:
                    if wordAsSlot:
                        curWord = cv.slot()
                    else:
                        curWord = cv.node(WORD)
                    cur[WORD] = curWord
                    addSlotFeatures(cv, cur, curWord)

            if ch is not None:
                cur["wordStr"] += ch

        def finishWord(cv, cur, ch, withNewline):
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
            withNewline:
                Whether to add a newline or space after the word.
                That depends on whether there is a mixed ancestor.
            """
            curWord = cur[WORD]
            if curWord:
                cv.feature(curWord, str=cur["wordStr"])
                if not wordAsSlot:
                    cv.terminate(curWord)
                cur[WORD] = None
                cur["wordStr"] = ""
                cur["prevWord"] = curWord
                cur["afterStr"] = ""

            if ch is not None:
                cur["afterStr"] += ch
            if withNewline:
                spaceChar = " " if hasMixedAncestor(cur) else "\n"
                cur["afterStr"] = cur["afterStr"].rstrip() + spaceChar
                if not wordAsSlot:
                    addSpace(cv, cur, spaceChar)
                cur["afterSpace"] = True
            else:
                cur["afterSpace"] = False

        def addEmpty(cv, cur):
            """Add an empty slot.

            We also terminate the current word.
            If words are slots, the empty slot is a word on its own.

            Returns
            -------
            node
                The empty slot
            """
            finishWord(cv, cur, None, False)
            startWord(cv, cur, ZWSP)
            emptyNode = cur[WORD]
            cv.feature(emptyNode, empty=1)

            if not wordAsSlot:
                emptyNode = cv.slot()
                cv.feature(emptyNode, ch=ZWSP, empty=1)

            finishWord(cv, cur, None, False)

            return emptyNode

        def addSlotFeatures(cv, cur, s):
            """Add generic features to a slot.

            Whenever we encounter a character, we add it as a new slot, unless
            `wordAsSlot` is in force. In that case we suppress the triggering of a
            slot node.
            If needed, we start/terminate word nodes as well.

            Parameters
            ----------
            cv: object
                The convertor object, needed to issue actions.
            cur: dict
                Various pieces of data collected during walking
                and relevant for some next steps in the walk.
            s: slot
                A previously added (slot) node
            """
            if cur["inHeader"]:
                cv.feature(s, is_meta=1)
            if cur["inNote"]:
                cv.feature(s, is_note=1)
            for (r, stack) in cur.get("rend", {}).items():
                if len(stack) > 0:
                    cv.feature(s, **{f"rend_{r}": 1})

        def addSlot(cv, cur, ch):
            """Add a slot.

            Whenever we encounter a character, we add it as a new slot, unless
            `wordAsSlot` is in force. In that case we suppress the triggering of a
            slot node.
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
            if ch in {"_", None} or ch.isalnum() or ch in IN_WORD_HYPHENS:
                startWord(cv, cur, ch)
            else:
                finishWord(cv, cur, ch, False)

            if wordAsSlot:
                s = cur[WORD]
            elif ch is None:
                s = None
            else:
                s = cv.slot()
                cv.feature(s, ch=ch)
            if s is not None:
                addSlotFeatures(cv, cur, s)

        def addSpace(cv, cur, spaceChar):
            """Adds a space or a new line.

            Parameters
            ----------
            cv: object
                The convertor object, needed to issue actions.
            cur: dict
                Various pieces of data collected during walking
                and relevant for some next steps in the walk.
            spaceChar: string
                The character to add (supposed to be either a space or a newline).

            Only meant for the case where slots are characters.

            Suppressed when not in a lowest-level section.
            """
            if chunkLevel in cv.activeTypes():
                s = cv.slot()
                cv.feature(s, ch=spaceChar, extraspace=1)
                addSlotFeatures(cv, cur, s)

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
            sectionModel = self.sectionModel
            sectionProperties = self.sectionProperties

            atts = {etree.QName(k).localname: v for (k, v) in node.attrib.items()}

            if sectionModel == "II":
                chapterSection = self.chapterSection
                chunkSection = self.chunkSection

                if isChapter(cur):
                    cur["chapterNum"] += 1
                    cur["prevChapter"] = cur.get(CHAPTER, None)
                    cur[CHAPTER] = cv.node(chapterSection)
                    for danglingSlot in cur["danglingSlots"]:
                        cv.link(cur[CHAPTER], danglingSlot)

                    value = {chapterSection: f"{cur['chapterNum']} {tag}"}
                    cv.feature(cur[CHAPTER], **value)
                    cur["chunkPNum"] = 0
                    cur["chunkONum"] = 0
                    cur["prevChunk"] = cur.get(CHUNK, None)
                    cur[CHUNK] = cv.node(chunkSection)
                    for danglingSlot in cur["danglingSlots"]:
                        cv.link(cur[CHUNK], danglingSlot)
                    cur["danglingSlots"] = set()
                    cur["infirstChunk"] = True

                # N.B. A node can count both as chapter and as chunk,
                # e.g. a <trailer> sibling of the chapter <div>s
                # A trailer has mixed content, so its subelements aren't typical chunks.
                if isChunk(cur):
                    if cur["infirstChunk"]:
                        cur["infirstChunk"] = False
                    else:
                        cur[CHUNK] = cv.node(chunkSection)
                        for danglingSlot in cur["danglingSlots"]:
                            cv.link(cur[CHUNK], danglingSlot)
                        cur["danglingSlots"] = set()
                    if tag == "p":
                        cur["chunkPNum"] += 1
                        cn = cur["chunkPNum"]
                    else:
                        cur["chunkONum"] -= 1
                        cn = cur["chunkONum"]
                    value = {chunkSection: cn}
                    cv.feature(cur[CHUNK], **value)

                if tag == sectionProperties["element"]:
                    criticalAtts = sectionProperties["attributes"]
                    match = True
                    for (k, v) in criticalAtts.items():
                        if atts.get(k, None) != v:
                            match = False
                            break
                    if match:
                        heading = etree.tostring(
                            node, encoding="unicode", method="text", with_tail=False
                        ).replace("\n", " ")
                        value = {chapterSection: heading}
                        cv.feature(cur[CHAPTER], **value)
                        chapterNum = cur["chapterNum"]
                        console(
                            f"\rchapter {chapterNum:>4} {heading:<50}", newline=False
                        )
            else:
                chunkSection = self.chunkSection

                if isChunk(cur):
                    cur["chunkNum"] += 1
                    cur["prevChunk"] = cur.get(CHUNK, None)
                    cur[CHUNK] = cv.node(chunkSection)
                    for danglingSlot in cur["danglingSlots"]:
                        cv.link(cur[CHUNK], danglingSlot)
                    cur["danglingSlots"] = set()
                    value = {chunkSection: cur["chunkNum"]}
                    cv.feature(cur[CHUNK], **value)

            if tag == TEI_HEADER:
                cur["inHeader"] = True
                if sectionModel == "II":
                    value = {chapterSection: "TEI header"}
                    cv.feature(cur[CHAPTER], **value)
            if tag in NOTE_LIKE:
                cur["inNote"] = True
                finishWord(cv, cur, None, False)

            if tag not in PASS_THROUGH:
                cur["afterSpace"] = False
                curNode = cv.node(tag)
                if wordAsSlot:
                    if cur[WORD]:
                        cv.link(curNode, [cur[WORD][1]])
                cur["elems"].append(curNode)
                if len(atts):
                    cv.feature(curNode, **atts)
                    if "rend" in atts:
                        rValue = atts["rend"]
                        r = makeNameLike(rValue)
                        if r:
                            cur.setdefault("rend", {}).setdefault(r, []).append(True)
            if node.text:
                textMaterial = WHITE_TRIM_RE.sub(" ", node.text)
                if isPure(cur):
                    if textMaterial and textMaterial != " ":
                        console(
                            "WARNING: Text material at the start of "
                            f"pure-content element <{tag}>"
                        )
                        stack = "-".join(cur[NEST])
                        console(f"\tElement stack: {stack}")
                        console(f"\tMaterial: `{textMaterial}`")
                else:
                    for ch in textMaterial:
                        addSlot(cv, cur, ch)

        def afterChildren(cv, cur, node, tag):
            """Node actions after dealing with the children, but before the end tag.

            Here we make sure that the newline elements will get their last slot
            having a newline at the end of their `after` feature.

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
            sectionModel = self.sectionModel
            isChap = isChapter(cur)
            isChnk = isChunk(cur)

            hasFinishedWord = False

            if tag not in PASS_THROUGH:
                curNode = cur["elems"][-1]
                slots = cv.linked(curNode)
                empty = len(slots) == 0

                if (
                    tag in NEWLINE_ELEMENTS
                    or isEndInPure(cur)
                    and not empty
                    and not cur["afterSpace"]
                ):
                    finishWord(cv, cur, None, True)
                    hasFinishedWord = True

                slots = cv.linked(curNode)
                empty = len(slots) == 0

                if empty:
                    lastSlot = addEmpty(cv, cur)
                    if cur["inHeader"]:
                        cv.feature(lastSlot, is_meta=1)
                    if cur["inNote"]:
                        cv.feature(lastSlot, is_note=1)
                    # take care that this empty slot falls under all sections
                    # for folders and files this is already guaranteed
                    # We need only to watch out for chapters and chunks
                    if cur.get(CHUNK, None) is None:
                        prevChunk = cur.get("prevChunk", None)
                        if prevChunk is None:
                            cur["danglingSlots"].add(lastSlot)
                        else:
                            cv.link(prevChunk, lastSlot)
                    if sectionModel == "II":
                        if cur.get(CHAPTER, None) is None:
                            prevChapter = cur.get("prevChapter", None)
                            if prevChapter is None:
                                cur["danglingSlots"].add(lastSlot)
                            else:
                                cv.link(prevChapter, lastSlot)

                cur["elems"].pop()
                cv.terminate(curNode)

            if isChnk:
                if not hasFinishedWord:
                    finishWord(cv, cur, None, True)
                cv.terminate(cur[CHUNK])
            if sectionModel == "II":
                if isChap:
                    if not hasFinishedWord:
                        finishWord(cv, cur, None, True)
                    cv.terminate(cur[CHAPTER])

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
            if tag == TEI_HEADER:
                cur["inHeader"] = False
            elif tag in NOTE_LIKE:
                cur["inNote"] = False

            if tag not in PASS_THROUGH:
                atts = {etree.QName(k).localname: v for (k, v) in node.attrib.items()}
                if "rend" in atts:
                    rValue = atts["rend"]
                    r = makeNameLike(rValue)
                    if r:
                        cur["rend"][r].pop()

            if node.tail:
                tailMaterial = WHITE_TRIM_RE.sub(" ", node.tail)
                if isPure(cur):
                    if tailMaterial and tailMaterial != " ":
                        elem = cur[NEST][-1]
                        console(
                            "WARNING: Text material after "
                            f"<{tag}> in pure-content element <{elem}>"
                        )
                        stack = "-".join(cur[NEST])
                        console(f"\tElement stack: {stack}-{tag}")
                        console(f"\tMaterial: `{tailMaterial}`")
                else:
                    for ch in tailMaterial:
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
            sectionModel = self.sectionModel
            elementDefs = self.elementDefs

            cur = {}
            cur["pureElems"] = {
                x for (x, (typ, mixed)) in elementDefs.items() if not mixed
            }
            cur["mixedElems"] = {
                x for (x, (typ, mixed)) in elementDefs.items() if mixed
            }

            if sectionModel == "I":
                folderSection = self.folderSection
                fileSection = self.fileSection

                i = 0
                for (xmlFolder, xmlFiles) in self.getXML():
                    console(f"Start folder {xmlFolder}:")

                    cur[FOLDER] = cv.node(folderSection)
                    value = {folderSection: xmlFolder}
                    cv.feature(cur[FOLDER], **value)

                    for xmlFile in xmlFiles:
                        i += 1
                        console(f"\r{i:>4} {xmlFile:<50}", newline=False)

                        cur[FILE] = cv.node(fileSection)
                        value = {fileSection: xmlFile.removesuffix(".xml")}
                        cv.feature(cur[FILE], **value)

                        with open(
                            f"{sourceDir}/{xmlFolder}/{xmlFile}", encoding="utf8"
                        ) as fh:
                            text = fh.read()
                            text = transformFunc(text)
                            tree = etree.parse(text, parser)
                            root = tree.getroot()
                            cur["inHeader"] = False
                            cur["inNote"] = False
                            cur[NEST] = []
                            cur["elems"] = []
                            cur["chunkNum"] = 0
                            cur["prevChunk"] = None
                            cur["danglingSlots"] = set()
                            cur[WORD] = None
                            cur["prevWord"] = None
                            cur["wordStr"] = ""
                            cur["afterStr"] = ""
                            cur["afterSpace"] = True
                            cur["chunkElems"] = set()
                            walkNode(cv, cur, root)

                        addSlot(cv, cur, None)
                        cv.terminate(cur[FILE])

                    console("")
                    console(f"End   folder {xmlFolder}")
                    cv.terminate(cur[FOLDER])

            elif sectionModel == "II":
                xmlFile = self.getXML()
                if xmlFile is None:
                    console("No XML files found!")
                    return False

                with open(f"{sourceDir}/{xmlFile}", encoding="utf8") as fh:
                    text = fh.read()
                    text = transformFunc(text)
                    tree = etree.parse(text, parser)
                    root = tree.getroot()
                    cur["inHeader"] = False
                    cur["inNote"] = False
                    cur[NEST] = []
                    cur["elems"] = []
                    cur["chapterNum"] = 0
                    cur["chunkPNum"] = 0
                    cur["chunkONum"] = 0
                    cur["prevChunk"] = None
                    cur["prevChapter"] = None
                    cur["danglingSlots"] = set()
                    cur[WORD] = None
                    cur["prevWord"] = None
                    cur["wordStr"] = ""
                    cur["afterStr"] = ""
                    cur["afterSpace"] = True
                    cur["chunkElems"] = set()
                    cur["chapterElems"] = set()
                    for child in root.iterchildren(tag=etree.Element):
                        walkNode(cv, cur, child)

                addSlot(cv, cur, None)

            console("")

            for fName in featureMeta:
                if not cv.occurs(fName):
                    cv.meta(fName)
            for fName in cv.features():
                if fName not in featureMeta:
                    if fName.startswith("rend_"):
                        r = fName[5:]
                        cv.meta(
                            fName,
                            description=f"whether text is to be rendered as {r}",
                            valueType="int",
                        )
                        intFeatures.add(fName)
                    else:
                        cv.meta(
                            fName,
                            description=f"this is TEI attribute {fName}",
                            valueType="str",
                        )

            levelConstraints = ["note < chunk, p"]
            if "chapterElems" in cur:
                for elem in cur["chapterElems"]:
                    levelConstraints.append(f"{elem} < chapter")
            if "chunkElems" in cur:
                for elem in cur["chunkElems"]:
                    levelConstraints.append(f"{elem} < chunk")

            levelConstraints = "; ".join(levelConstraints)

            cv.meta("otext", levelConstraints=levelConstraints)

            if verbose == 1:
                console("source reading done")
            return True

        return director

    def convertTask(self):
        """Implementation of the "convert" task.

        It sets up the `tf.convert.walker` machinery and runs it.

        Returns
        -------
        boolean
            Whether the conversion was successful.
        """
        if not self.good:
            return

        verbose = self.verbose
        wordAsSlot = self.wordAsSlot
        sectionModel = self.sectionModel
        tfPath = self.tfPath
        sourceDir = self.sourceDir
        chunkSection = self.chunkSection
        levelNames = self.levelNames

        if verbose == 1:
            console(f"TEI to TF converting: {ux(sourceDir)} => {ux(tfPath)}")

        slotType = WORD if wordAsSlot else CHAR

        sectionFeatures = ",".join(levelNames)
        sectionTypes = ",".join(levelNames)

        textFeatures = "{str}{after}" if wordAsSlot else "{ch}"
        otext = {
            "fmt:text-orig-full": textFeatures,
            "sectionFeatures": sectionFeatures,
            "sectionTypes": sectionTypes,
        }
        intFeatures = {"empty", chunkSection}
        featureMeta = dict(
            str=dict(description="the text of a word"),
            after=dict(description="the text after a word till the next word"),
            empty=dict(
                description="whether a slot has been inserted in an empty element"
            ),
            is_meta=dict(
                description="whether a slot or word is in the teiHeader element"
            ),
            is_note=dict(description="whether a slot or word is in the note element"),
        )
        featureMeta[chunkSection] = dict(
            description=f"number of a {chunkSection} within a document"
        )

        if not wordAsSlot:
            featureMeta["ch"] = dict(description="the unicode character of a slot")
        if sectionModel == "II":
            chapterSection = self.chapterSection
            featureMeta[chapterSection] = dict(description=f"name of {chapterSection}")
        else:
            folderSection = self.folderSection
            fileSection = self.fileSection
            featureMeta[folderSection] = dict(
                description=f"name of source {folderSection}"
            )
            featureMeta[fileSection] = dict(description=f"name of source {fileSection}")

        self.intFeatures = intFeatures
        self.featureMeta = featureMeta

        schema = self.schema
        tfVersion = self.tfVersion
        generic = self.generic
        generic["sourceFormat"] = "TEI"
        generic["version"] = tfVersion
        if schema:
            generic["schema"] = schema

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
            A file with named snippets of code to be inserted
            at corresponding places in the generated `app.py`
        *   `display_custom.css`:
            Additonal css definitions that will be appended to the generated
            `display.css`.

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
        appConfig = self.appConfig
        force = self.force
        wordAsSlot = self.wordAsSlot
        sectionModel = self.sectionModel
        sectionProperties = self.sectionProperties
        docsDir = self.docsDir

        initTree(docsDir)

        # key | parent dir | file | template based

        # if parent dir is a tuple, the first part is the parent of the source
        # end the second part is the parent of the destination

        itemSpecs = (
            ("about", "docs", "about.md", False),
            ("trans", ("app", "docs"), "transcription.md", True),
            ("logo", "app/static", "logo.png", True),
            ("display", "app/static", "display.css", True),
            ("config", "app", "config.yaml", True),
            ("app", "app", "app.py", True),
        )
        genTasks = {
            s[0]: dict(parent=s[1], file=s[2], hasTemplate=s[3]) for s in itemSpecs
        }
        cssInfo = makeCssInfo()

        def readCustom(itemTarget):
            (base, ext) = itemTarget.rsplit(".", 1)
            itemCustom = f"{base}_custom.{ext}"

            custom = ""

            if fileExists(itemCustom):
                with open(itemCustom, encoding="utf8") as fh:
                    custom = fh.read()

            return custom

        def createConfig(itemSource, itemTarget):
            tfVersion = self.tfVersion

            with open(itemSource, encoding="utf8") as fh:
                text = fh.read()

            version = tfVersion.removesuffix("pre") if tokenBased else tfVersion
            text = text.replace("«version»", f'"{version}"')

            settings = yaml.load(text, Loader=yaml.FullLoader)
            mergeDict(settings, appConfig)

            if tokenBased:
                if "typeDisplay" in settings and "word" in settings["typeDisplay"]:
                    del settings["typeDisplay"]["word"]

            customText = readCustom(itemTarget)
            customSettings = yaml.load(customText, Loader=yaml.FullLoader)

            mergeDict(settings, customSettings)

            text = yaml.dump(settings, allow_unicode=True)

            with open(itemTarget, "w", encoding="utf8") as fh:
                fh.write(text)

        def createDisplay(itemSource, itemTarget):
            """Copies and tweaks the display.css file of an TF app.

            We generate css code for a certain text formatting styles,
            triggered by `rend` attributes in the source.
            """

            with open(itemSource, encoding="utf8") as fh:
                css = fh.read()

            css = css.replace("«rends»", cssInfo)

            customText = readCustom(itemTarget)

            with open(itemTarget, "w", encoding="utf8") as fh:
                fh.write(css)
                fh.write(f"\n{customText}\n")

        def createApp(itemSource, itemTarget):
            """Copies and tweaks the app.py file of an TF app.

            The template app.py provides text formatting functions.
            It retrieves text from features, but that is dependent on
            the settings of the conversion, in particular whether we have words as
            slots or characters.

            Depending on that we insert some code in the template.

            The template contains the string `F.matérial`, and it will be replaced
            by something like

            ```
            F.ch.v(n)
            ```

            or

            ```
            f"{F.str.v(n)}{F.after.v(n)}"
            ```

            That's why the variable `materialCode` in the body gets a rather
            unusual value: it is interpreted later on as code.
            """

            materialCode = (
                """f'{F.str.v(n) or ""}{F.after.v(n) or ""}'"""
                if wordAsSlot or tokenBased
                else '''F.ch.v(n) or ""'''
            )
            rendValues = repr(KNOWN_RENDS)

            with open(itemSource, encoding="utf8") as fh:
                code = fh.read()

            code = code.replace("F.matérial", materialCode)
            code = code.replace('"rèndValues"', rendValues)

            hookStartRe = re.compile(r"^# DEF (import|init|extra)\s*$", re.S)
            hookEndRe = re.compile(r"^# END DEF\s*$", re.S)
            hookInsertRe = re.compile(r"^# INSERT (import|init|extra)\s*$", re.S)

            customCode = readCustom(itemTarget)

            custom = {}
            section = None

            for line in customCode.split("\n"):
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

            with open(itemTarget, "w", encoding="utf8") as fh:
                fh.write("\n".join(codeLines))

        def createTranscription(itemSource, itemTarget):
            """Copies and tweaks the transcription.md file for a TF corpus."""
            org = self.org
            repo = self.repo
            relative = self.relative
            generic = self.generic

            generic = "\n\n".join(
                f"## {key}\n\n{value}\n" for (key, value) in generic.items()
            )

            with open(itemSource, encoding="utf8") as fh:
                template = fh.read()

            result = (
                dedent(
                    f"""
                # Corpus {org} - {repo}{relative}

                """
                )
                + tweakTrans(
                    template, wordAsSlot, tokenBased, sectionModel, sectionProperties
                )
                + dedent(
                    """

                    ## See also

                    *   [about](about.md)
                    """
                )
            )
            with open(itemTarget, "w", encoding="utf8") as fh:
                fh.write(result)

        def createAbout():
            org = self.org
            repo = self.repo
            relative = self.relative
            generic = self.generic

            generic = "\n\n".join(
                f"## {key}\n\n{value}\n" for (key, value) in generic.items()
            )

            return (
                dedent(
                    f"""
                # Corpus {org} - {repo}{relative}

                """
                )
                + generic
                + dedent(
                    """

                    ## Conversion

                    Converted from TEI to Text-Fabric

                    ## See also

                    *   [transcription](transcription.md)
                    """
                )
            )

        extraRep = " adapted to tokens and sentences" if tokenBased else ""

        if verbose >= 0:
            console(f"App updating {extraRep} ...")

        for (name, info) in genTasks.items():
            parent = info["parent"]
            (sourceBit, targetBit) = (
                parent if type(parent) is tuple else (parent, parent)
            )
            file = info[FILE]
            hasTemplate = info["hasTemplate"]

            targetDir = f"{refDir}/{targetBit}"
            itemTarget = f"{targetDir}/{file}"
            fileParts = file.rsplit(".", 1)
            if len(fileParts) == 1:
                fileParts = [file, ""]
            (fileBase, fileExt) = fileParts
            itemTargetGen = f"{targetDir}/{fileBase}_generated.{fileExt}"
            itemExists = fileExists(itemTarget)
            itemGenExists = fileExists(itemTargetGen)

            existRep = "exists " if itemExists else "missing"
            changeRep = "generated" if itemExists else "added   "

            initTree(targetDir, fresh=False)

            target = itemTarget

            if force:
                if itemGenExists:
                    fileRemove(itemTargetGen)
            else:
                if itemExists:
                    target = itemTargetGen

            if force and itemExists and name == "logo":
                continue

            if hasTemplate:
                sourceDir = f"{myDir}/{sourceBit}"
                itemSource = f"{sourceDir}/{file}"
                (
                    createConfig
                    if name == "config"
                    else createApp
                    if name == "app"
                    else createDisplay
                    if name == "display"
                    else createTranscription
                    if name == "trans"
                    else fileCopy
                )(itemSource, target)

            else:
                with open(target, "w", encoding="utf8") as fh:
                    fh.write(createAbout())
            if verbose == 1:
                console(f"\t{name:<7}: {existRep}, {changeRep} {ux(target)}")

        if verbose >= 0:
            console("Done")
        else:
            console(f"App updated{extraRep}")

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
        apptoken=False,
        browse=False,
        test=None,
        force=False,
        verbose=-1,
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
        apptoken: boolean, optional False
            Whether to carry out the "apptoken" task.
        browse: boolean, optional False
            Whether to carry out the "browse" task"
        test: boolean, optional None
            Whether to run in test mode.
            In test mode only the files in the test set are converted.
        verbose: integer, optional -1
            Produce no (-1), some (0) or many (1) orprogress and reporting messages
        force: boolean, optional False
            Whether the app task should overwrite previously generated files

            If None, it will read its value from the attribute `testMode` of the
            `TEI` object.

        Returns
        -------
        boolean
            Whether all tasks have executed successfully.
        """
        if test is not None:
            self.testMode = test

        self.force = force
        self.verbose = verbose

        if not self.good:
            return False

        for (condition, method, kwargs) in (
            (check, self.checkTask, {}),
            (convert, self.convertTask, {}),
            (load, self.loadTask, {}),
            (app, self.appTask, {}),
            (apptoken, self.appTask, dict(tokenBased=True)),
            (browse, self.browseTask, {}),
        ):
            if condition:
                method(**kwargs)
                if not self.good:
                    break

        return self.good

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
        possibleTasks = {"check", "convert", "load", "app", "apptoken", "browse"}
        possibleFlags = {
            "-test": False,
            "+test": True,
            "-force": False,
            "+force": True,
            "-verbose": -1,
            "+verbose": 0,
            "++verbose": 1,
        }
        possibleArgs = possibleTasks | set(possibleFlags)

        args = set(sys.argv[1:])

        if not len(args) or "--help" in args or "-h" in args:
            self.help(programRep)
            console("No task specified")
            sys.exit(-1)

        illegalArgs = {arg for arg in args if arg not in possibleArgs}

        if len(illegalArgs):
            self.help(programRep)
            for arg in illegalArgs:
                console(f"Illegal argument `{arg}`")
            sys.exit(-1)

        tasks = {arg: True for arg in possibleTasks if arg in args}
        flags = {
            arg.lstrip("+-"): val for (arg, val) in possibleFlags.items() if arg in args
        }

        self.task(**tasks, **flags)
        if self.good:
            sys.exit(0)
        else:
            sys.exit(1)
