"""Corpus dependent setup of the annotation tool.
"""

import sys
from importlib import util

from ..browser.html import H
from ..core.helpers import console
from ..core.files import readYaml, fileExists, APP_CONFIG


ERROR = "error"

TOOLKEY = "ner"
"""The name of this annotation tool.

This name is used

*   in directory paths on the file system to find the data that is managed by this tool;
*   as a key to address the in-memory data that belongs to this tool;
*   as a prefix to modularize the Flask app for this tool within the encompassing
    TF browser Flask app and also it CSS files.
"""

SET_ENT = "🟰"
SET_SHEET = "🧾"
SET_MAIN = "🖍️"

DEFAULT_SETTINGS = """
entityType: ent
entitySet: "{entityType}-nodes"

strFeature: str
afterFeature: after

features:
  - eid
  - kind

keywordFeatures:
  - kind

defaultValues:
  kind: PER

spaceEscaped: false
"""

NONE = "⌀"
"""GUI representiation of an empty value.

Used to mark the fact that an occurrence does not have a value for an entity feature.
That happens when an occurrence is not part of an entity.
"""

EMPTY = "␀"
"""GUI representation of the empty string.

If an entity feature has the empty string as value, and we want to create a button for
it, this is the label we draw on that button.
"""

STYLES = dict(
    minus=dict(bg="#ffaaaa;"),
    plus=dict(bg="#aaffaa;"),
    replace=dict(bg="#ffff88;"),
    free=dict(
        ff="monospace",
        fz="small",
        fw="normal",
        fg="black",
        bg="white",
    ),
    free_active=dict(
        fg="black",
        bg="yellow",
    ),
    free_bordered=dict(
        bg="white",
        br="0.5rem",
        bw="1pt",
        bs="solid",
        bc="white",
        p="0.4rem",
        m="0.1rem 0.2rem",
    ),
    free_bordered_active=dict(
        bw="1pt",
        bs="solid",
        bc="yellow",
    ),
    keyword=dict(
        ff="monospace",
        fz="medium",
        fw="bold",
        fg="black",
        bg="white",
    ),
    keyword_active=dict(
        fg="black",
        bg="yellow",
    ),
    keyword_bordered=dict(
        bg="white",
        br="0.5rem",
        bw="1pt",
        bs="solid",
        bc="white",
        p="0.3rem",
        m="0.1rem 0.2rem",
    ),
    keyword_bordered_active=dict(
        bw="1pt",
        bs="solid",
        bc="yellow",
    ),
)
"""CSS style configuration for entity features.

Here we define properties of the styling of the entity features and their
values.
Since these features are defined in configuration, we cannot work with a fixed
style sheet.

We divide entity features in *keyword* features and *free* features.
The typical keyword feature is `kind`, it has a limited set of values.
The typical free feature is `eid`, it has an unbounded number of values.

As it is now, we could have expressed this in a fixed style sheet.
But if we open up to allowing for more entity features, we can use this setup
to easily configure the formatting of them.

However, we should move these definitions to the `ner.yaml` file then, so that the
only place of configuration is that YAML file, and not this file.
"""


def makeCss(features, keywordFeatures):
    """Generates CSS for the tool.

    The CSS for this tool has a part that depends on the choice of entity features.
    For now, the dependency is mild: keyword features such as `kind` are formatted
    differently than features with an unbounded set of values, such as `eid`.

    Parameters
    ----------
    features, keywordFeatures: iterable
        What the features are and what the keyword features are.
        These derive ultimately from the corpus-dependent `ner/config.yaml`.
    """
    propMap = dict(
        ff="font-family",
        fz="font-size",
        fw="font-weight",
        fg="color",
        bg="background-color",
        bw="border-width",
        bs="border-style",
        bc="border-color",
        br="border-radius",
        p="padding",
        m="margin",
    )

    def makeBlock(manner):
        props = STYLES[manner]
        defs = [f"\t{propMap[abb]}: {val};\n" for (abb, val) in props.items()]
        return H.join(defs)

    def makeCssDef(selector, *blocks):
        return selector + " {\n" + H.join(blocks) + "}\n"

    css = []

    for feat in features:
        manner = "keyword" if feat in keywordFeatures else "free"

        plain = makeBlock(manner)
        bordered = makeBlock(f"{manner}_bordered")
        active = makeBlock(f"{manner}_active")
        borderedActive = makeBlock(f"{manner}_bordered_active")

        css.extend(
            [
                makeCssDef(f".{feat}", plain),
                makeCssDef(f".{feat}.active", active),
                makeCssDef(f"span.{feat}_sel,button.{feat}_sel", plain, bordered),
                makeCssDef(f"button.{feat}_sel[st=v]", borderedActive, active),
            ]
        )

    featureCss = H.join(css, sep="\n")
    allCss = H.style(featureCss, type="text/css")
    return allCss


class Settings:
    def __init__(self):
        """Provides configuration details.

        There is fixed configuration, that is not intended to be modifiable by users.
        These configuration values are put in variables in this module, which
        other modules can import.

        There is also customisable configuration, meant to adapt the tool to the
        specifics of a corpus.
        Those configuration values are read from a YAML file *config.yaml*,
        located in a directory `ner` next to the `tf` data of the corpus.

        This file has the following information:

        *   `entityType`: the node type of entities that are already in the corpus,
            possibly generated by a tool like Spacy;

        *   `entitySet`: a name for the pre-existing set of entities;

        *   `lineType`: the name of the node type for individual lines; this is needed
            to deal with words that are split across a line boundary;

        *   `strFeature`: the name of the feature that has the string values of tokens;

        *   `afterFeature`: the name of the feature that has the string values of the
            text between tokens, usually a space, it is on the preceding token;

        *   `features`: the features that contain essential information about
            the entities. Currently, we specify only 2 features. You may rename these
            features, but we advise not modify the number of features.
            Probably, in later releases, you'll have more choice here.

        *   `keywordFeatures`: some features have a limited set of values, e.g.
            the kind of entity. Those features are mentioned under this key.

        *   `defaultValues`: provide default values for the keyword features.
            The tool also provides a default for the first feature, the entity
            identifier, basically a lower case version of the full name where
            the parts of the name are separated by dots.

        *   `featureMeta`: metadata of the features specified in `features`;

        *   `eNameFeature`: the name and metadata of the feature that has the
            full name of an entity; this is only available for annotation sets
            that correspond to a NER sheet;

        *   `spaceEscaped`: set this to True if your corpus has tokens with
            spaces in it.
            You can then escape spaces with `_`, for example in spreadsheets where you
            specify annotation instructions.

        *   `transform`: the tool can read a spreadsheet with full names and per name
            a list of occurrences that should be marked as entities for that name.
            When the full name is turned into an identifier, the identifier might
            become longer than is convenient. Here you can specify a replacement
            table for name parts. You can use it to shorten or repress certain
            name parts that are very generic, such as `de`, `van`, `von`.

        *   `variants`: for sheet-based sets, the tool can compute spelling variants
            of the triggers. This is done by *analiticcl*. Here the parameters for
            running that program are specified. See `tf.ner.variants`
        """
        specDir = self.specDir

        nerSpec = f"{specDir}/{APP_CONFIG}"
        nerCode = f"{specDir}/code.py"

        normalizeChars = None

        if fileExists(nerCode):
            try:
                spec = util.spec_from_file_location("nerutils", nerCode)
                code = util.module_from_spec(spec)
                sys.path.insert(0, specDir)
                spec.loader.exec_module(code)
                sys.path.pop(0)
                normalizeChars = code.normalizeChars
                self.console(f"normalizeChars() loaded from {nerCode}")
            except Exception as e:
                normalizeChars = None
                console(
                    f"normalizeChars() could not be loaded from existing {nerCode}",
                    error=True,
                )
                console(str(e), error=True)

        if normalizeChars is None:
            self.console(
                "normalizeChars() not found. No normalization will take place."
            )

        self.normalizeChars = normalizeChars

        kwargs = (
            dict(asFile=nerSpec) if fileExists(nerSpec) else dict(text=DEFAULT_SETTINGS)
        )
        settings = readYaml(preferTuples=True, **kwargs)
        settings.entitySet = (settings.entitySet or "entity-nodes").format(
            entityType=settings.entityType
        )
        self.settings = settings

        features = self.settings.features
        keywordFeatures = self.settings.keywordFeatures
        self.settings.summaryIndices = tuple(
            i for i in range(len(features)) if features[i] in keywordFeatures
        )

    def console(self, msg, **kwargs):
        """Print something to the output.

        This works exactly as `tf.core.helpers.console`

        When the silent member of the object is True, the message will be suppressed.
        """
        silent = self.silent

        if not silent:
            console(msg, **kwargs)

    def consoleLine(self, isError, indent, msg):
        """Print a formatted line to the output.

        When the silent member of the object is True, the message will be suppressed,
        if it is not an error message.

        Parameters
        ----------
        isError: boolean or void
            If True, it the message is an error message, and it will be shown.
            If False, the message, if it is shown, will be shown as a normal message.
            If None, the message, if it is shown, will be preceded and followed by
            some decoration to make it more conspicuous.
        indent: integer
            The number of quads to indent the message with. A quad is two spaces.
        msg: string
            The text of the message.
        """
        silent = self.silent

        if silent and not isError:
            return

        tabs = "  " * indent
        head = "-" * len(msg)

        if isError is None:
            console("")
            console(f"{tabs}{head}")

        console(f"{tabs}{msg}\n", error=isError)

        if isError is None:
            console(f"{tabs}{head}")
