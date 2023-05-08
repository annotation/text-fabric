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

# Configuration

We assume that you have a `programs` directory at the top-level of your repo.
In this directory we'll look for two optional files:

*   a file `tei.yaml` in which you specify a bunch of values
    Last, but not least, you can assemble all the input parameters needed to
    get the conversion off the ground.

*   a file `tei.py` in which you define a function `transform(text)` which
    takes a text string ar argument and delivers a text string as result.
    The converter will call this on every TEI input file it reads *before*
    feeding it to the XML parser.


## Keys and values of the `tei.yaml` file

### generic

dict, optional `{}`

Metadata for all generated TF features.
The actual source version of the TEI files does not have to be stated here,
it will be inserted based on the version that the converter will actually use.
That version depends on the `tei` argument passed to the program.
The key under which the source version will be inserted is `teiVersion`.

### schema

string, optional `None`

Which XML schema to be used, if not specified we fall back on full TEI.
If specified, leave out the `.xsd` extension. The file is relative to the
`schema` directory.

### prelim

boolean, optional `True`

Whether to work with the `pre` tf versions.
Use this if you convert TEI to a preliminary TF dataset, which will
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
tf-fromtei tasks flags
```

## From Python

```python
from tf.convert.tei import TEI

T = TEI()
T.task(**tasks, **flags)
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
`TEI.task()` method.

## Note on versions

The TEI source files come in versions, indicated with a data.
The converter picks the most recent one, unless you specify an other one:

```python
tf-from-tei tei=-2  # previous version
tf-from-tei tei=0  # first version
tf-from-tei tei=3  # third version
tf-from-tei tei=2019-12-23  # explicit version
```

The resulting TF data is independently versioned, like `1.2.3` or `1.2.3pre`.
When the converter runs, by default it overwrites the most recent version,
unless you specify another one.

It looks at the latest version and then bumps a part of the version number.

```python
tf-fromtei tf=3  # minor version, 1.2.3 becomes 1.2.4; 1.2.3pre becomes 1.2.4pre
tf-fromtei tf=2  # intermediate version, 1.2.3 becomes 1.3.0
tf-fromtei tf=1  # major version, 1.2.3 becomes 2.0.0
tf-fromtei tf=1.8.3  # explicit version
```

## Examples

Exactly how you can call the methods of this module is demonstrated in the small
corpus of 14 letter by the Dutch artist Piet Mondriaan.

*   [Mondriaan](https://nbviewer.org/github/annotation/mondriaan/blob/master/programs/convertExpress.ipynb).
"""

import sys
import collections
import re
from textwrap import dedent
from io import BytesIO
from subprocess import run
from importlib import util

import yaml
from lxml import etree
from .helpers import (
    setUp,
    tweakTrans,
    checkSectionModel,
    FOLDER,
    FILE,
    CHAPTER,
    CHUNK,
    PRE,
    ZWSP,
    NEST,
    WORD,
    CHAR,
)
from ..parameters import BRANCH_DEFAULT_NEW
from ..fabric import Fabric
from ..core.helpers import console, versionSort
from ..convert.walker import CV
from ..core.timestamp import AUTO, DEEP, TERSE
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
    scanDir,
)

from ..tools.xmlschema import Analysis


(HELP, TASKS, TASKS_EXCLUDED, PARAMS, FLAGS) = setUp("TEI")

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


class TEI:
    def __init__(
        self, tei=PARAMS["tei"][1], tf=PARAMS["tf"][1], verbose=FLAGS["verbose"][1]
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
        These settings can be overriden in the `app/config_custom.yaml` file.
        Also a default `display.css` file and a logo are added.

        Custom content for these files can be provided in files
        with `_custom` appended to their base name.

        ### `docs`

        Location of additional documentation.
        This can be generated or had-written material, or a mixture of the two.

        Parameters
        ----------
        tei: string, optional ""
            If empty, use the latest version under the `tei` directory with sources.
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
            the TEI object, only versions ending in `pre` will be taken into account.

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
        convertSpec = f"{programDir}/tei.yaml"
        convertCustom = f"{programDir}/tei.py"

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
        teiPath = self.teiPath
        sectionModel = self.sectionModel
        if verbose == 1:
            console(f"Section model {sectionModel}")

        if sectionModel == "I":
            IGNORE = "__ignore__"

            xmlFilesRaw = collections.defaultdict(list)

            with scanDir(teiPath) as dh:
                for folder in dh:
                    folderName = folder.name
                    if folderName == IGNORE:
                        continue
                    if not folder.is_dir():
                        continue
                    with scanDir(f"{teiPath}/{folderName}") as fh:
                        for file in fh:
                            fileName = file.name
                            if not (
                                fileName.lower().endswith(".xml") and file.is_file()
                            ):
                                continue
                            xmlFilesRaw[folderName].append(fileName)

            xmlFiles = tuple(
                (folderName, tuple(sorted(fileNames)))
                for (folderName, fileNames) in sorted(xmlFilesRaw.items())
            )
            return xmlFiles

        if sectionModel == "II":
            xmlFile = None
            with scanDir(teiPath) as fh:
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
            The TEI to TF conversion does construct node types and attributes
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

        teiPath = self.teiPath
        reportPath = self.reportPath
        docsDir = self.docsDir
        sectionModel = self.sectionModel

        if verbose == 1:
            console(f"TEI to TF checking: {ux(teiPath)} => {ux(reportPath)}")

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

        initTree(reportPath)
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
                    self.good = False
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
                    xmlPath = f"{teiPath}/{xmlFolder}/{xmlFile}"
                    doXMLFile(xmlPath)
                console("")
                console(f"End   folder {xmlFolder}")

        elif sectionModel == "II":
            xmlFile = self.getXML()
            if xmlFile is None:
                console("No XML files found!")
                return False

            xmlPath = f"{teiPath}/{xmlFile}"
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
        teiPath = self.teiPath
        wordAsSlot = self.wordAsSlot
        featureMeta = self.featureMeta
        intFeatures = self.intFeatures
        transform = self.transform
        chunkLevel = self.chunkLevel

        transformFunc = (
            (lambda x: BytesIO(x.encode("utf-8")))
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
                            f"{teiPath}/{xmlFolder}/{xmlFile}", encoding="utf8"
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

                with open(f"{teiPath}/{xmlFile}", encoding="utf8") as fh:
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

            levelConstraints = ["note < chunk, p", "salute < opener, closer"]
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
        teiPath = self.teiPath
        chunkSection = self.chunkSection
        levelNames = self.levelNames

        if verbose == 1:
            console(f"TEI to TF converting: {ux(teiPath)} => {ux(tfPath)}")

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
        teiVersion = self.teiVersion
        generic = self.generic
        generic["sourceFormat"] = "TEI"
        generic["version"] = tfVersion
        generic["teiVersion"] = teiVersion
        generic["schema"] = "TEI" + (f" + {schema}" if schema else "")

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

        It creates/updates a corpus-specific app plus specific documentation files.
        There should be a valid TF dataset in place, because some
        settings in the app derive from it.

        It will also read custom additions that are present in the target app directory.
        These files are:

        *   `about_custom.md`:
            A markdown file with specific colofon information about the dataset.
            In the generated file, this information will be put at the start.
        *   `transcription_custom.md`:
            A markdown file with specific encoding information about the dataset.
            In the generated file, this information will be put at the start.
        *   `config_custom.yaml`:
            A yaml file with config data that will be *merged* into the generated
            config.yaml.
        *   `app_custom.py`:
            A python file with named snippets of code to be inserted
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
        wordAsSlot = self.wordAsSlot
        sectionModel = self.sectionModel
        sectionProperties = self.sectionProperties

        # key | parent dir | file | template based

        # if parent dir is a tuple, the first part is the parent of the source
        # end the second part is the parent of the destination

        itemSpecs = (
            ("about", "docs", "about.md", False),
            ("trans", ("app", "docs"), "transcription.md", False),
            ("logo", "app/static", "logo.png", True),
            ("display", "app/static", "display.css", False),
            ("config", "app", "config.yaml", False),
            ("app", "app", "app.py", False),
        )
        genTasks = {
            s[0]: dict(parent=s[1], file=s[2], justCopy=s[3]) for s in itemSpecs
        }
        cssInfo = makeCssInfo()

        tfVersion = self.tfVersion
        version = tfVersion.removesuffix(PRE) if tokenBased else tfVersion

        def createConfig(sourceText, customText):
            text = sourceText.replace("«version»", f'"{version}"')

            settings = yaml.load(text, Loader=yaml.FullLoader)
            settings.setdefault("provenanceSpec", {})["branch"] = BRANCH_DEFAULT_NEW

            if tokenBased:
                if "typeDisplay" in settings and "word" in settings["typeDisplay"]:
                    del settings["typeDisplay"]["word"]

            customSettings = (
                {}
                if customText is None
                else yaml.load(customText, Loader=yaml.FullLoader)
            )

            mergeDict(settings, customSettings)

            text = yaml.dump(settings, allow_unicode=True)

            return text

        def createDisplay(sourceText, customText):
            """Copies and tweaks the display.css file of an TF app.

            We generate css code for a certain text formatting styles,
            triggered by `rend` attributes in the source.
            """

            css = sourceText.replace("«rends»", cssInfo)
            return f"{css}\n\n{customText}\n"

        def createApp(sourceText, customText):
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

            code = sourceText.replace("F.matérial", materialCode)
            code = code.replace('"rèndValues"', rendValues)

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

        def createTranscription(sourceText, customText):
            """Copies and tweaks the transcription.md file for a TF corpus."""
            org = self.org
            repo = self.repo
            relative = self.relative
            generic = self.generic

            generic = "\n\n".join(
                f"## {key}\n\n{value}\n" for (key, value) in generic.items()
            )

            text = (
                dedent(
                    f"""
                # Corpus {org} - {repo}{relative}

                """
                )
                + tweakTrans(
                    sourceText,
                    wordAsSlot,
                    tokenBased,
                    sectionModel,
                    sectionProperties,
                    REND_DESC,
                )
                + dedent(
                    """

                    ## See also

                    *   [about](about.md)
                    """
                )
            )
            return f"{text}\n\n{customText}\n"

        def createAbout(sourceText, customText):
            org = self.org
            repo = self.repo
            relative = self.relative
            generic = self.generic
            if tokenBased:
                generic["version"] = version

            generic = "\n\n".join(
                f"## {key}\n\n{value}\n" for (key, value) in generic.items()
            )

            return f"{customText}\n\n{sourceText}\n\n" + (
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

        extraRep = " with tokens and sentences " if tokenBased else ""

        if verbose >= 0:
            console(f"App updating {extraRep} ...")

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
            teiDir = f"{myDir}/{sourceBit}"
            itemSource = f"{teiDir}/{file}"

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
                    customText = ""

                targetText = (
                    createConfig
                    if name == "config"
                    else createApp
                    if name == "app"
                    else createDisplay
                    if name == "display"
                    else createTranscription
                    if name == "trans"
                    else createAbout
                    if name == "about"
                    else fileCopy  # this cannot occur because justCopy is False
                )(sourceText, customText)

                with open(itemTarget, "w", encoding="utf8") as fh:
                    fh.write(targetText)

            if verbose >= 0:
                console(f"\t{ux(itemTarget):30} {msg}")

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
        apptoken: boolean, optional False
            Whether to carry out the "apptoken" task.
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
            (apptoken, self.appTask, dict(tokenBased=True)),
            (browse, self.browseTask, {}),
        ):
            if condition:
                method(**kwargs)
                if not self.good:
                    break

        return self.good


def main():
    (good, tasks, params, flags) = readArgs(
        "tf-fromtei", HELP, TASKS, PARAMS, FLAGS, notInAll=TASKS_EXCLUDED
    )
    if not good:
        return False

    T = TEI(**params, **flags)
    T.task(**tasks, **flags)

    return T.good


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
