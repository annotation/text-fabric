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
2.  `convert`: produces actual TF files by converting XML files.
3.  `load`: loads the generated TF for the first time, by which the precomputation
    step is triggered. During precomputation some checks are performed. Once this
    has succeeded, we have a workable Text-Fabric dataset.
4.  `app`: creates or updates a corpus specific TF-app with minimal sensible settings,
    plus basic documentation.
4.  `browse`: starts the text-fabric browser on the newly created dataset.

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

The resulting script will look like this:

``` python

import os
from tf.convert.tei import TEI


TEST_SET = set(
    '''
    18920227_HMKR_0001.xml
    18920302_HMKR_0002.xml
    18930711_PM_RANI_5003.xml
    18980415y_PRIX_0007.xml
    '''.strip().split()
)

AUTHOR = "Piet Mondriaan"
TITLE = "Letters"
INSTITUTE = "KNAW/Huygens Amsterdam"

GENERIC = dict(
    author=AUTHOR,
    title=TITLE,
    institute=INSTITUTE,
    language="nl",
    converters="Dirk Roorda (Text-Fabric)",
    sourceFormat="TEI",
    descriptionTf="Critical edition",
)

ABOUT_TEXT = '''
# CONTRIBUTORS

Researcher: Mariken Teeuwen

Editors: Peter Boot et al.
'''

TRANSCRIPTION_TEXT = '''

The TEI has been validated and polished
before generating the TF data.
'''

DOC_MATERIAL = dict(
    about=ABOUT_TEXT,
    trans=TRANSCRIPTION_TEXT,
)

APP_CONFIG = dict(
    provenanceSpec=dict(
        corpus=f"{GENERIC['author']} - {GENERIC['title']}",
        doi="10.5281/zenodo.nnnnnn",
    )
)


HY = "\u2010"  # hyphen


def transform(text):
    return text.replace(",,", HY)


T = TEI(
    schema="MD",
    sourceVersion="2023-01-31",
    testSet=TEST_SET,
    slotLevel="word",
    sectionModel=dict(model="I"),
    generic=GENERIC,
    transform=transform,
    tfVersion="0.1",
    appConfig=APP_CONFIG,
    docMaterial=DOC_MATERIAL,
    force=True,
)

T.run(os.path.basename(__file__))
```
"""

import sys
import os
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
from ..core.helpers import (
    initTree,
    dirExists,
    fileExists,
    fileCopy,
    fileRemove,
    mergeDict,
    getLocation,
    unexpanduser as ux,
)
from ..tools.xmlschema import Analysis


__pdoc__ = {}

DOC_TRANS = """
## Essentials

*   Text-Fabric non-slot nodes correspond to TEI elements in the source.
*   Text-Fabric node-features correspond to TEI attributes.
*   Text-Fabric slot nodes correspond to characters in TEI element content.

In order to understand the encoding, you need to know

*   the [TEI elements](https://tei-c.org/release/doc/tei-p5-doc/en/html/REF-ELEMENTS.html).
*   the [TEI attributes](https://tei-c.org/release/doc/tei-p5-doc/en/html/REF-ATTS.html).
*   the [Text-Fabric datamodel](https://annotation.github.io/text-fabric/tf/about/datamodel.html)

The TEI to TF conversion is an almost literal and very faithful transformation from
the TEI source files to a Text-Fabric data set.

But there are some peculiarities.

## Sectioning

The material is divided into three levels of sections, mainly for the purposes
of text display.

But how these levels relate to the source material is a different matter.

The conversion supports a few sectioning models that specify this.
This aspect is *work-in-progress*, because TEI sources differ wildly in how they
are sectioned.
The sectioning models that are currently supported correspond to cases we have
encountered, we have not done exhaustive research into TEI sectioning in practice.

### Model I: folders and files

This model assumes that the source is a directory consisting of folders
consisting of xml files, the TEI files.

There are three section levels: folder - file - subdivision in file.

1.  Subdirectories and files are sorted in the lexicographic ordering
1.  The folder `__ignore__` is ignored.
1.  For each folder, a section level 1 node will be created, with
    feature `name` containing its name.
1.  For each file in a folder, a section level 2 node will be created, with
    feature `name` containing its name.
1.  A third section level, named `chunk` will be made.
    For each immediate child element of `<teiHeader>` and for each immediate child
    element of `<body>`, a chunk node will be created, wit a feature `chunk`
    containing the number of the chunk within the file, starting with 1.
    Also the following elements will trigger a chunk node:
    `<facsimile>`, `<fsdDecl>`, `<sourceDoc>`, and `<standOff>`.

### Model II: single file and divs.

This model assumes that the source is a single TEI file.

There are two section levels: "chapter"like - "p"like.

1.  The name of the source file is not recorded.
1.  The first section level, named `chapter` will be made as follows:
    For the `<teiHeader>` and for each immediate child
    element of `<body>`, a chapter node will be created, wit a feature `chapter`
    containing the content of the first element with certain properties that
    follows the section-1-level element.
1.  The properties of the heading bearing element is given by its element
    name and a dictionary of attribute values.
    For example:

    ```
    element = "head"
    attributes = dict(rend="h3")
    ```

    Heading bearing elements also occur in the text, and are treated in the same
    way as all other element. The only special thing is that their plain text
    content is used as the value of a feature.
1.  The second section level, named `chunk` consists of the top-level elements within
    the chapters, except certain empty elements, such as breaks.
1.  Section-2-level nodes get a feature `chunk` with a chunk number.
1.  `cn` is positive for `<p>` elements, and it is the sequence number
    of the `p` within the chapter.
1.  `cn` is negative for all other elements of section-level-2. For those elements
    it is the sequence number of the non-p immediate children of the chapter.

### Specifying a sectioning model

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
1.  Words get the following features:
    *   `str`: the alphanumeric string that is the word;
    *   `after`: the non-alphanumeric string after the word unti the following word.

## Slots

The basic unit is the unicode character.
For each character in the input we make a slot, but the correspondence is not
quite 1-1.

1.  Spaces are stripped when they are between elements whose parent does not allow
    mixed content; other whitespace is reduced to a single space.
1.  All slots inside the teiHeader will get the feature `is_meta` set to 1;
    for slots inside the body, `is_meta` has no value.
1.  Empty elements will receive one extra slot; this will anchor the element to
    a textual position; the empty slot gets the ZERO-WIDTH-SPACE (Unicode 200B)
    as character value.
1.  Slots get the following features:
    *   `ch`: the character of the slot
    *   `empty`: 1 if the slot has been inserted as an empty slot, no value otherwise.

## Words as slots

It is also possible to take the word as basic unit instead of the character.
The decision to do so can be passed as a parameter (`wordAsSlot`).
Here is what that entails:

1. Instead of inserting empty characters for empty elements, we insert empty words,
   with ZERO-WIDTH-SPACE (Unicode 200B) as value for feature `str` and `empty=1`.
2. Nodes that contain only part of the characters of a word, will contain the whole
   word.
3. Features that have different values for different characters in the word,
   will have the most salient value for the whole word.
   The concept of *salient* is rather coarse:

   *    `None` values are the least salient
   *    for integer values: bigger values are more salient than smaller values
   *    for string values: linger strings are more salient than smaller strings,
        for strings of equal length the lexicographic ordering holds.

## Text kinds and text formatting

We record in additional features whether text occurs in metadata elements and
in note elements and what formatting specifiers influence the text.
These features are provided for characters and words, and have only one value: 1.
The absence of values means that the corresponding property does not hold.

The following features are added:

*   `is_meta`: 1 if the word occurs in inside the `<teiHeader>`, no value otherwise.
*   `is_note`: 1 if the word occurs in inside the `<note>`, no value otherwise.
*   `rend_`*r*: for any *r* that is the value of a `rend` attribute.

All these features are defined for `char` and `word` nodes.
For word nodes, the value of these features is set equal to what these features
are for their first character.

Special formatting for the `rend_`*r* features is supported for some values of *r*.
The conversion supports these out-of-the-box:

`italic`
`bold`
`underline`
`center`
`large`
`spaced`
`margin`
`above`
`below`
`sub`
`sup`
`super`

It is possible for the corpus designer to add more formatting on a per-corpus
basis by adding it to the `display.css` in the app directory of the corpus.
Unsupported values get a generic kind of special format: an orange-like color.

Special formatting becomes visible when material is rendered in a `layout` text
format.

## Text-formats

Text-formats regulate how text is displayed, and they can also determine
what text is displayed.

There are two kind of text-formats: those that start with the word `layout` and
those that start with `text`.

The `text` formats do not apply any kind of special formating, the `layout` formats
do.

We have the following formats:

*   `text-orig-full`: all text
*   `layout-orig-full`: all text, formatted in HTML

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

## Validation

We have used [lxml](https://lxml.de) for XML parsing. During `convert` it is not used
in validating mode, but we can trigger a validation step during `check`.

However, some information about the elements, in particular whether they allow
mixed content or not, has been gleaned from the schemas, and has been used
during conversion.

Care has been taken that the names of these extra nodes and features do not collide
with element/attribute names of the TEI.

## TF noded and features

(only in as far they are not in 1-1 correspondence with TEI elements and attributes)

### node type `folder`

*The type of subfolders of TEI documents.*

**Section level 1.**

**Features**

feature | description
--- | ---
`folder` | name of the subfolder

### node type `file`

*The type of individual TEI documents.*

**Section level 2.**

**Features**

feature | description
--- | ---
`file` | name of the file, without the `.xml` extension. Other extensions are included.

### node type `chunk`

*Top-level division of material inside a document.*

**Section level 3.**

**Features**

feature | description
--- | ---
`chunk` | sequence number of the chunk within the document, starting with 1.

### node type `word`

*Individual words, without punctuation.*

**Features**

feature | description
--- | ---
`str` | the characters of the word, without soft hyphens.
`after` | the non-word characters after the word, up till the next word.
`is_meta` | whether a word is in the teiHeader element
`is_note` | whether a word is in a note element
`rend_`*r* | whether a word is under the influence of a `rend="`*r*`"` attribute.

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
`is_meta` | whether a character is in the teiHeader element
`is_note` | whether a character is in a note element
`rend_`*r* | whether a character is under the influence of a `rend="`*r*`"` attribute.
"""


SECTION_MODELS = dict(I={}, II=dict(element=(str, "head"), attributes=(dict, {})))
SECTION_MODEL_DEFAULT = "I"


def checkSectionModel(sectionModel):
    if sectionModel is None:
        model = SECTION_MODEL_DEFAULT
        console(f"WARNING: No section model specified. Assuming model {model}.")
        criteria = {k: v[1] for (k, v) in SECTION_MODELS[model].items()}
        return dict(model=model, criteria=criteria)

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

    criteria = {k: v for (k, v) in sectionModel.items() if k != "model"}
    modelCriteria = SECTION_MODELS[model]

    good = True
    delKeys = []

    for (k, v) in criteria.items():
        if k not in modelCriteria:
            console(f"WARNING: ignoring unknown model criterium {k}={v}")
            delKeys.append(k)
        elif type(v) is not modelCriteria[k][0]:
            console(
                f"ERROR: criterium {k} should have type {modelCriteria[k][0]}"
                f" but {v} has type {type(v)}"
            )
            good = False
    if good:
        for k in delKeys:
            del criteria[k]

    for (k, v) in modelCriteria.items():
        if k not in criteria:
            console(
                f"WARNING: model criterium {k} not specified, taking default {v[1]}"
            )
            criteria[k] = v[1]

    if not good:
        return False

    return dict(model=model, criteria=criteria)


class TEI:
    def __init__(
        self,
        repoDir=".",
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
    ):
        """Converts TEI to TF.

        We adopt a fair bit of "convention over configuration" here, in order to lessen
        the burden for the user of specifying so many details.

        Based on current direcotry from where the script is called,
        it defines all the ingredients to carry out
        a `tf.convert.walker` conversion of the TEI input.

        This function is assumed to work in the context of a repository,
        i.e. a directory on your computer relative to which the input directory exists,
        and various output directories: `tf`, `app`, `docs`.

        Your current directory must be somewhere inside

        ```
        ~/backend/org/repo
        ```

        where

        *   `~` is your home directory;
        *   `backend` is an online *backend* name,
            like `github`, `gitlab`, `git.huc.knaw.nl`;
        *   `org` is an organisation, person, or group in the backend;
        *   `repo` is a repository in the `org`.

        This is only about the directory structure on your local computer;
        it is not required that you have online incarnations of your repository
        in that backend.
        Even your local repository does not have to be a git repository.

        The only thing that matters is that the full path to your repo can be parsed
        as a sequence of *home*/*backend*/*org*/*repo*.

        Relative to the repo directory the program expects and creates
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
            dict(model="II", element="head", attributes=dict(rend="h3"))
            ```

            or

            ```
            dict(model="I")
            ```

            because model I does not require parameters.

            For model II, the default parameters are:

            ```
            element="head"
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
        """
        (backend, org, repo) = getLocation(repoDir)
        if any(s is None for s in (backend, org, repo)):
            console("Not working in a repo: backend={backend} org={org} repo={repo}")
            quit()

        console(f"Working in repository {org}/{repo} in backend {backend}")

        base = os.path.expanduser(f"~/{backend}")
        repoDir = f"{base}/{org}/{repo}"
        sourceDir = f"{repoDir}/tei/{sourceVersion}"
        reportDir = f"{repoDir}/report"
        tfDir = f"{repoDir}/tf"
        appDir = f"{repoDir}/app"
        docsDir = f"{repoDir}/docs"

        self.repoDir = repoDir
        self.sourceDir = sourceDir
        self.reportDir = reportDir
        self.tfDir = tfDir
        self.appDir = appDir
        self.docsDir = docsDir
        self.backend = backend
        self.org = org
        self.repo = repo

        if sourceDir is None or not dirExists(sourceDir):
            console(f"Source location does not exist: {sourceDir}")
            quit()

        self.schema = schema
        self.schemaFile = None if schema is None else f"{repoDir}/schema/{schema}.xsd"
        self.sourceVersion = sourceVersion
        self.testMode = False
        self.testSet = testSet
        self.wordAsSlot = wordAsSlot
        sectionModel = checkSectionModel(sectionModel)
        if not sectionModel:
            quit()
        self.sectionModel = sectionModel["model"]
        self.sectionCriteria = sectionModel.get("criteria", None)
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
        myDir = os.path.dirname(os.path.abspath(__file__))
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
            browse:
                just starts the text-fabric browser on the result;

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
        tuple of tuple | string
            If section model I is in force:

            The outer tuple has sorted entries corresponding to folders under the
            TEI input directory.
            Each such entry consists of the folder name and an inner tuple
            that contains the file names in that folder, sorted.

            If section model II is in force:

            It is the name of the single XML file.
        """
        sourceDir = self.sourceDir
        sectionModel = self.sectionModel
        console(f"Section model {sectionModel}")

        if sectionModel == "I":
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
            with os.scandir(sourceDir) as fh:
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
        sectionModel = self.sectionModel

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

            def nodeInfo(node):
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
                    nodeInfo(child)

            nodeInfo(root)

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
                    console("ERROR")
                    errors.append((xmlFile, theseErrors))
                return

            root = tree.getroot()
            analyse(root, analysis)

        if sectionModel == "I":
            i = 0
            for (xmlFolder, xmlFiles) in self.getXML():
                console(xmlFolder)
                for xmlFile in xmlFiles:
                    i += 1
                    console(f"\r{i:>4} {xmlFile:<50}", newline=False)
                    xmlPath = f"{sourceDir}/{xmlFolder}/{xmlFile}"
                    doXMLFile(xmlPath)

        elif sectionModel == "II":
            xmlFile = self.getXML()
            if xmlFile is None:
                console("No XML files found!")
                return False

            xmlPath = f"{sourceDir}/{xmlFile}"
            doXMLFile(xmlPath)

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
        wordAsSlot = self.wordAsSlot
        sectionModel = self.sectionModel

        slotType = "word" if wordAsSlot else "char"

        sectionFeatures = "folder,file,chunk"
        sectionTypes = "folder,file,chunk"
        if sectionModel == "II":
            sectionFeatures = "chapter,chunk"
            sectionTypes = "chapter,chunk"

        textFeatures = "{str}{after}" if wordAsSlot else "{ch}"
        otext = {
            "fmt:text-orig-full": textFeatures,
            "sectionFeatures": sectionFeatures,
            "sectionTypes": sectionTypes,
        }
        intFeatures = {"empty", "chunk"}
        featureMeta = dict(
            chunk=dict(description="number of a chunk within a file"),
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
        if not wordAsSlot:
            featureMeta["ch"] = dict(description="the unicode character of a slot")
        if sectionModel == "II":
            featureMeta["chapter"] = dict(description="name of chapter")
        else:
            featureMeta["folder"] = dict(description="name of source folder")
            featureMeta["file"] = dict(description="name of source file")

        self.intFeatures = intFeatures
        self.featureMeta = featureMeta

        schema = self.schema
        tfVersion = self.tfVersion
        tfPath = self.tfPath
        generic = self.generic
        generic["sourceFormat"] = "TEI"
        generic["version"] = tfVersion
        if schema:
            generic["schema"] = schema

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
        BODY = "body"

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

        ZWSP = "\u200b"  # zero-width space

        sourceDir = self.sourceDir
        wordAsSlot = self.wordAsSlot
        featureMeta = self.featureMeta
        intFeatures = self.intFeatures
        transform = self.transform

        transformFunc = (
            (lambda x: x)
            if transform is None
            else (lambda x: BytesIO(transform(x).encode("utf-8")))
        )

        parser = self.getParser()
        elemDefs = self.getElementInfo()

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
            cur["nest"].append(tag)

            beforeChildren(cv, cur, node, tag)

            for child in node.iterchildren(tag=etree.Element):
                walkNode(cv, cur, child)

            afterChildren(cv, cur, node, tag)
            cur["nest"].pop()
            afterTag(cv, cur, node, tag)

        def isChapter(cur):
            """Whether the current element counts as a chapter node.

            ## Model I

            Not relevant: there are no chapter nodes.

            ## Model II

            Chapters are the highest section level (the only lower level is chunks).

            Chapters come in two kinds:

            *   the TEI header
            *   the immediate children of the `<body>` elements.

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
                nest = cur["nest"]
                nNest = len(nest)

                if nNest > 0 and nest[-1] in EMPTY_ELEMENTS:
                    return False

                return nNest > 0 and (
                    nest[-1] == TEI_HEADER or (nNest > 1 and nest[-2] == BODY)
                )

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

            nest = cur["nest"]
            nNest = len(nest)

            if nNest > 0 and nest[-1] in EMPTY_ELEMENTS:
                return False

            if sectionModel == "II":
                return nNest > 1 and (
                    nest[-2] == TEI_HEADER or (nNest > 2 and nest[-3] == BODY)
                )

            return nNest > 0 and (
                nest[-1] in CHUNK_ELEMS or (nNest > 1 and nest[-2] in CHUNK_PARENTS)
            )

        def isPure(cur):
            """Whether the current tag has pure content.

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
            nest = cur["nest"]
            return len(nest) > 0 and nest[-1] in cur["pureElems"]

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
                    curWord = cv.slot() if wordAsSlot else cv.node("word")
                    cur["word"] = curWord
                    if cur["inHeader"]:
                        cv.feature(curWord, is_meta=1)
                    if cur["inNote"]:
                        cv.feature(curWord, is_note=1)
                    for (r, stack) in cur.get("rend", {}).items():
                        if len(stack) > 0:
                            cv.feature(curWord, **{f"rend_{r}": 1})

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
                if not wordAsSlot:
                    cv.terminate(curWord)
                cur["word"] = None
                cur["wordStr"] = ""
                cur["prevWord"] = curWord
                cur["afterStr"] = ""

            if ch is not None:
                cur["afterStr"] += ch

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
            if ch is None or ch.isalnum() or ch in IN_WORD_HYPHENS:
                startWord(cv, cur, ch)
            else:
                finishWord(cv, cur, ch)

            if wordAsSlot:
                s = cur["word"]
            else:
                s = cv.slot()
                cv.feature(s, ch=ch)
            if s is not None:
                if cur["inHeader"]:
                    cv.feature(s, is_meta=1)
                if cur["inNote"]:
                    cv.feature(s, is_note=1)
                for (r, stack) in cur.get("rend", {}).items():
                    if len(stack) > 0:
                        cv.feature(s, **{f"rend_{r}": 1})

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
            sectionCriteria = self.sectionCriteria
            atts = None

            if sectionModel == "II":
                if isChapter(cur):
                    cur["chapter"] = cv.node("chapter")
                    cur["chunkPNum"] = 0
                    cur["chunkONum"] = 0
                elif isChunk(cur):
                    cur["chunk"] = cv.node("chunk")
                    if tag == "p":
                        cur["chunkPNum"] += 1
                        cn = cur["chunkPNum"]
                    else:
                        cur["chunkONum"] -= 1
                        cn = cur["chunkONum"]
                    cv.feature(cur["chunk"], chunk=cn)

                if tag == sectionCriteria["element"]:
                    atts = {
                        etree.QName(k).localname: v for (k, v) in node.attrib.items()
                    }
                    criticalAtts = sectionCriteria["attributes"]
                    match = True
                    for (k, v) in criticalAtts.items():
                        if atts.get(k, None) != v:
                            match = False
                            break
                    if match:
                        heading = etree.tostring(
                            node, encoding="unicode", method="text", with_tail=False
                        ).replace("\n", " ")
                        cv.feature(cur["chapter"], chapter=heading)
            else:
                if isChunk(cur):
                    cur["chunkNum"] += 1
                    cur["chunk"] = cv.node("chunk")
                    cv.feature(cur["chunk"], chunk=cur["chunkNum"])

            if tag == TEI_HEADER:
                cur["inHeader"] = True
                cv.feature(cur["chapter"], chapter="TEI header")
            if tag in NOTE_LIKE:
                cur["inNote"] = True
                finishWord(cv, cur, None)

            if tag not in PASS_THROUGH:
                curNode = cv.node(tag)
                cur["elems"].append(curNode)
                if atts is None:
                    atts = {
                        etree.QName(k).localname: v for (k, v) in node.attrib.items()
                    }
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
                        stack = "-".join(cur["nest"])
                        console(f"\tElement stack: {stack}")
                        console(f"\tMaterial: `{textMaterial}`")
                else:
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
            sectionModel = self.sectionModel
            if sectionModel == "II":
                if isChapter(cur):
                    cv.terminate(cur["chapter"])
                elif isChunk(cur):
                    cv.terminate(cur["chunk"])
            else:
                if isChunk(cur):
                    cv.terminate(cur["chunk"])

            if tag not in PASS_THROUGH:
                if isEndInPure(cur):
                    finishWord(cv, cur, None)

                curNode = cur["elems"].pop()

                if not cv.linked(curNode):
                    s = cv.slot()
                    if wordAsSlot:
                        cv.feature(s, str=ZWSP, empty=1)
                    else:
                        cv.feature(s, ch=ZWSP, empty=1)
                    if cur["inHeader"]:
                        cv.feature(s, is_meta=1)
                    if cur["inNote"]:
                        cv.feature(s, is_note=1)

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
                        elem = cur["nest"][-1]
                        console(
                            "WARNING: Text material after "
                            f"<{tag}> in pure-content element <{elem}>"
                        )
                        stack = "-".join(cur["nest"])
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

            cur = {}
            cur["pureElems"] = {
                x for (x, (typ, mixed)) in elemDefs.items() if not mixed
            }

            if sectionModel == "I":
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

                        with open(f"{sourceDir}/{xmlFolder}/{xmlFile}") as fh:
                            text = fh.read()
                            text = transformFunc(text)
                            tree = etree.parse(text, parser)
                            root = tree.getroot()
                            cur["inHeader"] = False
                            cur["inNote"] = False
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

            elif sectionModel == "II":
                xmlFile = self.getXML()
                if xmlFile is None:
                    console("No XML files found!")
                    return False

                with open(f"{sourceDir}/{xmlFile}") as fh:
                    text = fh.read()
                    text = transformFunc(text)
                    tree = etree.parse(text, parser)
                    root = tree.getroot()
                    cur["inHeader"] = False
                    cur["inNote"] = False
                    cur["nest"] = []
                    cur["elems"] = []
                    cur["chunkPNum"] = 0
                    cur["chunkONum"] = 0
                    cur["word"] = None
                    cur["prevWord"] = None
                    cur["wordStr"] = ""
                    cur["afterStr"] = ""
                    for child in root.iterchildren(tag=etree.Element):
                        walkNode(cv, cur, child)

                addSlot(cv, cur, None)

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

        if not os.path.exists(tfPath):
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

    # APP CREATION/UPDATING

    def appTask(self):
        """Implementation of the "app" task.

        It creates/updates a corpus-specific app.
        There should be a valid TF dataset in place, because some
        settings in the app derive from it.

        Returns
        -------
        boolean
            Whether the operation was successful.
        """
        repoDir = self.repoDir
        myDir = self.myDir
        appConfig = self.appConfig
        force = self.force

        itemSpecs = (
            ("about", "docs", "about.md", False),
            ("trans", "docs", "transcription.md", False),
            ("logo", "app/static", "logo.png", True),
            ("display", "app/static", "display.css", True),
            ("config", "app", "config.yaml", True),
            ("app", "app", "app.py", True),
        )
        items = {
            s[0]: dict(parent=s[1], file=s[2], hasTemplate=s[3]) for s in itemSpecs
        }

        def createConfig(itemSource, itemTarget):
            tfVersion = self.tfVersion

            with open(itemSource) as fh:
                settings = yaml.load(fh, Loader=yaml.FullLoader)

            mergeDict(settings, appConfig)

            text = yaml.dump(settings, allow_unicode=True)

            text = text.replace("«version»", f'"{tfVersion}"')

            with open(itemTarget, "w") as fh:
                fh.write(text)

        def createAbout():
            org = self.org
            repo = self.repo
            generic = self.generic

            generic = "\n\n".join(
                f"## {key}\n\n{value}\n" for (key, value) in generic.items()
            )

            return (
                dedent(
                    f"""
                # Corpus {org} - {repo}

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

        def createTranscription():
            org = self.org
            repo = self.repo
            generic = self.generic

            generic = "\n\n".join(
                f"## {key}\n\n{value}\n" for (key, value) in generic.items()
            )

            return (
                dedent(
                    f"""
                # Corpus {org} - {repo}

                """
                )
                + DOC_TRANS
                + dedent(
                    """

                    ## See also

                    *   [about](about.md)
                    """
                )
            )

        console("App updating ...")

        for (name, info) in items.items():
            parent = info["parent"]
            file = info["file"]
            hasTemplate = info["hasTemplate"]

            targetDir = f"{repoDir}/{parent}"
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
                sourceDir = f"{myDir}/{parent}"
                itemSource = f"{sourceDir}/{file}"
                (createConfig if name == "config" else fileCopy)(itemSource, target)

            else:
                with open(target, "w") as fh:
                    fh.write(
                        (createAbout if name == "about" else createTranscription)()
                    )
            console(f"\t{name:<7}: {existRep}, {changeRep} {ux(target)}")

        return True

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
        org = self.org
        repo = self.repo
        backend = self.backend

        backendOpt = "" if backend == "github" else f"--backend={backend}"
        run(f"text-fabric {org}/{repo}:clone --checkout=clone {backendOpt}", shell=True)
        return True

    def task(
        self, check=False, convert=False, load=False, app=False, browse=False, test=None
    ):
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
        app: boolean, optional False
            Whether to carry out the "app" task.
        browse: boolean, optional False
            Whether to carry out the "browse" task"
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
        tfPath = self.tfPath

        if test is not None:
            self.testMode = test

        good = True

        if check:
            console(f"TEI to TF checking: {ux(sourceDir)} => {ux(reportDir)}")
            good = self.checkTask()

        if good and convert:
            console(f"TEI to TF converting: {ux(sourceDir)} => {ux(tfPath)}")
            good = self.convertTask()

        if good and load:
            good = self.loadTask()

        if good and app:
            good = self.appTask()

        if good and browse:
            good = self.browseTask()

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
        possibleTasks = {"check", "convert", "load", "app", "browse"}
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


__pdoc__["TEI"] = DOC_TRANS
