import re

from ...core.helpers import console as cs
from ...core.files import annotateDir, readYaml

TOOLKEY = "ner"

NONE = "⌀"
EMPTY = "␀"

LIMIT_BROWSER = 100
LIMIT_NB = 20

ERROR = "error"

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

WHITE_RE = re.compile(r"""\s{2,}""", re.S)
NON_ALPHA_RE = re.compile(r"""[^\w ]""", re.S)

SORTDIR_DESC = "d"
SORTDIR_ASC = "a"
SORTDIR_DEFAULT = SORTDIR_ASC
SORTKEY_DEFAULT = "freqsort"
SORT_DEFAULT = (SORTKEY_DEFAULT, SORTDIR_DESC)

SC_ALL = "a"
SC_FILT = "f"


class Settings:
    def __init__(self):
        """Provides configuration details.

        There is fixed configuration, that is not intended to be modifiable by users.
        These configuration values are put in variables in this module, which
        other modules can import.

        There is also customizable configuration, meant to adapt the tool to the
        specifics of a corpus.
        Those configuration values are read from a yaml file, located in a directory
        `ner` next to the `tf` data of the corpus.
        """
        app = self.app
        version = app.context.version
        (specDir, annoDir) = annotateDir(app, TOOLKEY)
        self.specDir = specDir
        self.annoDir = f"{annoDir}/{version}"
        self.sheetDir = f"{specDir}/sheets"
        nerSpec = f"{specDir}/config.yaml"
        settings = readYaml(asFile=nerSpec, preferTuples=True)
        settings.entitySet = settings.entitySet.format(entityType=settings.entityType)
        self.settings = settings

        features = self.settings.features
        keywordFeatures = self.settings.keywordFeatures
        self.settings.summaryIndices = tuple(
            i for i in range(len(features)) if features[i] in keywordFeatures
        )

        def getText(F, slots):
            """Get the text for a number of slots.

            Leading and trailing whitespace is stripped, and inner whitespace is
            normalized to a single space.
            """
            text = "".join(
                f"""{F.str.v(s)}{F.after.v(s) or ""}""" for s in slots
            ).strip()
            text = WHITE_RE.sub(" ", text)
            return text

        def get0(F, slots):
            """Makes an identifier value out of a number of slots.

            This acts as the default value for the `eid` feature of new
            entities.

            Starting with the whitespace-normalized text of a number of slots,
            the string is lowercased, non-alphanumeric characters are stripped,
            and spaces are replaced by dots.
            """
            text = getText(F, slots)
            text = NON_ALPHA_RE.sub("", text)
            text = text.replace(" ", ".").strip(".").lower()
            return text

        def get1(F, slots):
            """Return a fixed value specified in the corpus-dependent settings.

            This acts as the default value ofr the `kind` feature of new
            entities.
            """
            return self.settings.defaultValues[features[1]]

        self.featureDefault = {
            "": getText,
            features[0]: get0,
            features[1]: get1,
        }

    def console(self, msg, **kwargs):
        """Print something to the output.

        This works exactly as `tf.core.helpers.console`

        It is handy to have this as a method on the Annotate object,
        so that we can issue temporary console statements during development
        without the need to add an `import` statement to the code.
        """
        cs(msg, **kwargs)
