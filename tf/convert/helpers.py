import re
from textwrap import dedent

from ..core.helpers import console


PRE = "pre"
ZWSP = "\u200b"  # zero-width space

NODE = "node"
FOLDER = "folder"
FILE = "file"
PAGE = "page"
LINE = "line"
LN = "ln"
REGION = "region"
DOC = "doc"
CHAPTER = "chapter"
CHUNK = "chunk"

XNEST = "xnest"
TNEST = "tnest"
TSIB = "tsiblings"
SLOT = "slot"
WORD = "word"
CHAR = "char"
TOKEN = "token"
T = "t"


LINE_MODELS = dict(
    I=dict(),
    II=dict(
        element=(str, "p"),
        nodeType=(str, LN),
    ),
)


LINE_MODEL_DEFAULT = "I"

PAGE_MODELS = dict(
    I=dict(),
    II=dict(
        element=(str, "div"),
        attributes=(dict, {}),
        pbAtTop=(bool, True),
        nodeType=(str, PAGE),
    ),
)


PAGE_MODEL_DEFAULT = "I"

SECTION_MODELS = dict(
    I=dict(
        levels=(list, [FOLDER, FILE, CHUNK]),
        drillDownDivs=(bool, True),
        backMatter=(str, "backmatter"),
    ),
    II=dict(
        levels=(list, [CHAPTER, CHUNK]),
        element=(str, "head"),
        attributes=(dict, {}),
    ),
)
"""Models for sections.

A section is a part of the corpus that is defined by a set of files,
or by elements within a single TEI source file.

A model
"""


SECTION_MODEL_DEFAULT = "I"
"""Default model for sections.
"""

CM_LIT = "literal"
"""The value is taken literally from a TEI attribute.

Code `tei`, since there is a 1-1 correspondence with the TEI source.
"""

CM_LITP = "literal-processed"
"""The value results from straightforward processing of material in the TEI.

Code `tei`, since there is a direct correspondence with the TEI source.

*Straightforward* means: by taking into account the semantics of XML.

Examples:

*   Generated white-space based on whether elements are pure or mixed;
*   Edges between parent and child elements, or sibling elements.
"""

CM_LITC = "literal-composed"
"""The value is results from more intricate processing of material in the TEI.

*More intricate means*: we derive data that goes beyond pure XML syntax.

Examples:

*   The values of the `rend` attributes are translated into `rend_`*value* features;
*   Adding features `is_meta` (being inside the TEI-header) and `is_note`
    (being inside a note);
*   The feature that gives the content of a (character) slot;
*   Decomposing strings into words material and after-word material.

Code `tf`, since this is for the benefit of the resulting TF dataset.
"""

CM_PROV = "provided"
"""The value is added by the conversion to TF w.r.t. the material in the TEI.

Examples:

*   Slots in empty elements, in order to anchor the element to the text sequence;
*   Section levels, based on the folder and file that the TEI source is in;
*   A section level within the TEI, defined from several elements and the way they
    are nested;

Code `tf`, since this is for the benefit of the resulting TF dataset.
"""

CM_NLP = "nlp-generated"
"""The value is added by an NLP pipeline w.r.t. the material in the TEI.

Code `nlp`, since this comes from third party software.

Examples:

*   The feature `nsent` which gives the sentence number in the corpus.
    Sentences are not encoded in the TEI, but detected by an NLP program such as Spacy.
"""

CONVERSION_METHODS = {
    CM_LIT: "tei",
    CM_LITP: "tei",
    CM_LITC: "tf",
    CM_PROV: "tf",
    CM_NLP: "nlp",
}
"""Information about the conversion.

When we produce TF features, we specify a bit of information in the feature
metadata as how we arrived at the specific value.

That information ends up in two keys:

*   `conversionMethod`: with values any of:
    *   `CM_LIT`
    *   `CM_LITP`
    *   `CM_LITC`
    *   `CM_PROV`
    *   `CM_NLP`
*   `conversionCode`: the value is derived from `conversionMethod` by looking it
    up in this table. These values can be used to qualify the name of the attribute
    for further processing.

    For example, if you have a feature `n` that originates literally from the TEI,
    you could pass it on as `tei:n`.

    But if you have a feature `chapter` that is provided by the conversion,
    you could pass it on as `tf:chapter`.

    This passing on is a matter of other software, that takes the generated TF as
    input and processes it further, e.g. as annotations.

!!! note "More methods and codes"

The TEI conversion is customizable by providing your own methods to several hooks
in the program. These hooks may generate extra features, which you can give metadata
in the `tei.yaml` file next to the `tei.py` file where you define the custom functions.

It is advised to state appropriate values for the `conversionMethod` and
`conversionCode` fields of these features.

Examples:

*   A feature `country` is derived from specific elements in the TEI Header, and
    defined for nodes of type `letter`.
    This happens in order to support the software of Team Text that shows the
    text on a webpage.

    In such a case you could define

    *   `conversionMethod="derived"
    *   `conversionCode="tt"
"""


TOKEN_RE = re.compile(r"""\w+|\W""")
NUMBER_RE = re.compile(
    r"""
    ^
    [0-9]+
    (?:
        [.,]
        [0-9]+
    )*
    $
""",
    re.X,
)

W_BEFORE = re.compile(r"""^\s+""")
W_AFTER = re.compile(r"""\s+$""")


def getWhites(text):
    match = W_BEFORE.match(text)
    if match:
        before = match.group(0)
        rest = text[len(before) :]
    else:
        before = ""
        rest = text
    match = W_AFTER.search(rest)
    if match:
        after = match.group(0)
        material = rest[0 : -len(after)]
    else:
        after = ""
        material = rest
    return (" " if before else "", material, " " if after else "")


def tokenize(line):
    tokens = []

    for word in line.split():
        ts = (
            [[word, ""]]
            if NUMBER_RE.match(word)
            else [[t, ""] for t in TOKEN_RE.findall(word)]
        )
        if len(ts):
            ts[-1][-1] = " "
        tokens.extend(ts)

    if len(tokens):
        tokens[-1][-1] = ""
    return tuple(tokens)


def repTokens(tokens):
    text = []
    for t, space in tokens:
        text.append(f"‹{t}›{space}")
    return "".join(text)


def checkModel(kind, thisModel, verbose):
    modelDefault = (
        LINE_MODEL_DEFAULT
        if kind == LINE
        else PAGE_MODEL_DEFAULT
        if kind == PAGE
        else SECTION_MODEL_DEFAULT
    )
    modelSpecs = (
        LINE_MODELS if kind == LINE else PAGE_MODELS if kind == PAGE else SECTION_MODELS
    )

    if thisModel is None:
        model = modelDefault
        if verbose == 1:
            console(f"WARNING: No {kind} model specified. Assuming model {model}.")
        properties = {k: v[1] for (k, v) in modelSpecs[model].items()}
        return dict(model=model, properties=properties)

    if type(thisModel) is str:
        if thisModel in modelSpecs:
            thisModel = dict(model=thisModel)
        else:
            console(f"ERROR: unknown {kind} model: {thisModel}")
            return False

    elif type(thisModel) is not dict:
        console(f"ERROR: {kind} model must be a dict. You passed a {type(thisModel)}")
        return False

    model = thisModel.get("model", None)

    if model is None:
        model = modelDefault
        if verbose == 1:
            console(f"WARNING: No {kind} model specified. Assuming model {model}.")
        thisModel["model"] = model

    if model not in modelSpecs:
        console(f"WARNING: unknown {kind} model: {thisModel}")
        return False

    if verbose >= 0:
        console(f"{kind} model is {model}")

    properties = {k: v for (k, v) in thisModel.items() if k != "model"}
    modelProperties = modelSpecs[model]

    good = True
    delKeys = []

    for k, v in properties.items():
        if k not in modelProperties:
            console(f"WARNING: ignoring unknown {kind} model property {k}={v}")
            delKeys.append(k)
        elif type(v) is not modelProperties[k][0]:
            console(
                f"ERROR: {kind} property {k} should have type {modelProperties[k][0]}"
                f" but {v} has type {type(v)}"
            )
            good = False
    if good:
        for k in delKeys:
            del properties[k]

    for k, v in modelProperties.items():
        if k not in properties:
            if verbose == 1:
                console(
                    f"WARNING: {kind} model property {k} not specified, "
                    f"taking default {v[1]}"
                )
            properties[k] = v[1]

    if not good:
        return False

    return dict(model=model, properties=properties)


def matchModel(properties, tag, atts):
    if tag == properties["element"]:
        criticalAtts = properties["attributes"]
        match = True
        for k, cVal in criticalAtts.items():
            aVal = atts.get(k, None)

            thisNoMatch = (
                all(aVal != cV for cV in cVal)
                if type(cVal) in {list, tuple, set}
                else aVal != cVal
            )
            if thisNoMatch:
                match = False
                break
        return match


def setUp(kind):
    helpText = f"""
    Convert {kind} to TF.

    There are also commands to check the {kind} and to load the TF."""

    taskSpec = dict(
        check="reports on the elements in the source",
        convert=f"converts {kind} to TF",
        load="loads the generated TF",
        app="configures the TF app for the result",
        apptoken="modifies the TF app to make it token- instead of character-based",
        browse="starts the TF browser on the result",
    )
    taskExcluded = {"apptoken", "browse"}

    paramSpec = {
        "tf": (
            (
                "0 or latest: update latest version;\n\t\t"
                "1 2 3: increase major, intermediate, minor TF version;\n\t\t"
                "rest: explicit version."
            ),
            "latest",
        ),
        kind.lower(): (
            (
                "0 or latest: latest version;\n\t\t"
                "-1 -2 etc: previous version, before previous, ...;\n\t\t"
                "1 2 etc: first version, second version, ...;\n\t\t"
                "rest: explicit version."
            ),
            "latest",
        ),
        "validate": ("Whether to validate the XML input", True),
    }

    flagSpec = dict(
        verbose=("Produce less or more progress and reporting messages", -1, 3),
    )
    return (helpText, taskSpec, taskExcluded, paramSpec, flagSpec)


def tweakTrans(
    template,
    procins,
    wordAsSlot,
    tokenAsSlot,
    charAsSlot,
    parentEdges,
    siblingEdges,
    tokenBased,
    sectionModel,
    sectionProperties,
    rendDesc,
    extra,
):
    if wordAsSlot:
        slot = WORD
        slotc = "Word"
        slotf = "words"
        xslot = "`word`"
    elif charAsSlot:
        slotc = "Char"
        slot = CHAR
        slotf = "characters"
        xslot = "`char` and `word`"
    elif tokenAsSlot or True:
        slotc = "Token"
        slot = T
        slotf = "tokens"
        xslot = "`t` and `word`"

    if parentEdges:
        hasParent = "Yes"
    else:
        hasParent = "No"

    if siblingEdges:
        hasSibling = "Yes"
    else:
        hasSibling = "No"

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

    if extra:
        hasExtra = "Yes"
    else:
        hasExtra = "No"

    if procins:
        doProcins = "Yes"
    else:
        doProcins = "No"

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

    rendDescStr = "\n".join(
        f"`{val}` | {desc}" for (val, desc) in sorted(rendDesc.items())
    )
    modelKeepRe = re.compile(rf"«(?:begin|end)Model{sectionModel}»")
    modelRemoveRe = re.compile(r"«beginModel([^»]+)».*?«endModel\1»", re.S)
    slotKeepRe = re.compile(rf"«(?:begin|end)Slot{slot}»")
    slotRemoveRe = re.compile(r"«beginSlot([^»]+)».*?«endSlot\1»", re.S)
    tokenKeepRe = re.compile(rf"«(?:begin|end)Token{hasToken}»")
    tokenRemoveRe = re.compile(r"«beginToken([^»]+)».*?«endToken\1»", re.S)
    parentKeepRe = re.compile(rf"«(?:begin|end)Parent{hasParent}»")
    parentRemoveRe = re.compile(r"«beginParent([^»]+)».*?«endParent\1»", re.S)
    siblingKeepRe = re.compile(rf"«(?:begin|end)Sibling{hasSibling}»")
    siblingRemoveRe = re.compile(r"«beginSibling([^»]+)».*?«endSibling\1»", re.S)
    extraKeepRe = re.compile(rf"«(?:begin|end)Extra{hasExtra}»")
    extraRemoveRe = re.compile(r"«beginExtra([^»]+)».*?«endToken\1»", re.S)
    procinsKeepRe = re.compile(rf"«(?:begin|end)Procins{doProcins}»")
    procinsRemoveRe = re.compile(r"«beginProcins([^»]+)».*?«endToken\1»", re.S)

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
        .replace("«rendDesc»", rendDescStr)
        .replace("«extraFeatures»", extra)
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

    text = parentKeepRe.sub("", text)
    text = parentRemoveRe.sub("", text)
    text = siblingKeepRe.sub("", text)
    text = siblingRemoveRe.sub("", text)
    text = tokenKeepRe.sub("", text)
    text = tokenRemoveRe.sub("", text)
    text = modelKeepRe.sub("", text)
    text = modelRemoveRe.sub("", text)
    text = slotKeepRe.sub("", text)
    text = slotRemoveRe.sub("", text)
    text = extraKeepRe.sub("", text)
    text = extraRemoveRe.sub("", text)
    text = procinsKeepRe.sub("", text)
    text = procinsRemoveRe.sub("", text)

    text = skipVars.sub("", text)

    if extra:
        text += dedent(
            f"""
            # Additional features

            {extra}
            """
        )

    return text


def lookupSource(cv, cur, tokenAsSlot, specs):
    """Looks up information from the current XML stack.

    The current XML stack contains the ancestry of the current node, including
    the current node itself.

    It is a list of components, corresponding to the path from the root node to the
    current node.
    Each component is a tuple, consisting of the tag name and the attributes of
    an XML node.

    Against this stack a sequence of instructions, given in `specs`, is executed.
    These instructions collect information from the stack, under certain conditions,
    and put that information into a feature, as value for a certain node.

    Here is an example of a single instruction:

    Parameters
    ----------
    cv: object
        The converter object, needed to issue actions.
    cur: dict
        Various pieces of data collected during walking
        and relevant for some next steps in the walk.
    specs: tuple
        A sequence of instructions what to look for.
        Each instruction has the following parts:

        *   `pathSpec`
        *   `nodeType`
        *   `featureName`

        The effect is:

        The `pathSpec` is compared to the current XML stack.
        If it matches the current node, the text content of the current node or one of
        its attributes will be collected and put in a feature with name
        `featureName`, for the current TF node of type `nodeType`.

        The `pathSpec` is a list of components.
        The first component should match the top of the XML stack, the second
        component the element that is below the top, etc.
        Each component is a tuple of

        *   a tag name;
        *   a dictionary of attribute values;

        The first component may have a tag name that has `@` plus an attribute name
        appended to it. That means that the information will be extracted from
        that attribute, not from the content of the element.
    """
    nest = cur[XNEST]
    nNest = len(nest)

    for path, nodeType, feature in specs:
        nPath = len(path)

        if nPath > nNest:
            continue

        ok = True
        extractAttr = None

        for p, (lookForTag, lookForAtts) in enumerate(path):
            (compareToTag, compareToAtts) = nest[-(p + 1)]

            if p == 0:
                pieces = lookForTag.split("@", 1)
                if len(pieces) == 2:
                    (lookForTag, extractAttr) = pieces
                else:
                    extractAttr = None
            ok = compareToTag == lookForTag

            if not ok:
                break

            if lookForAtts is not None:
                for att, val in lookForAtts.items():
                    if att not in compareToAtts or compareToAtts[att] != val:
                        ok = False
                        break

            if not ok:
                break

        if not ok:
            continue

        targetNode = cur[NODE][nodeType]
        sourceNode = cur[TNEST][-1]
        slots = cv.linked(sourceNode)
        sourceText = (
            (
                "".join(
                    cv.get("str", (T, slot)) + cv.get("after", (T, slot))
                    for slot in slots
                )
                if tokenAsSlot
                else "".join(cv.get("ch", (CHAR, slot)) for slot in slots)
            )
            if extractAttr is None
            else cv.get(extractAttr, sourceNode)
        )
        sourceText = (sourceText or "").strip()
        source = {feature: sourceText}
        cv.feature(targetNode, **source)
