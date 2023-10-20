import re

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
        self.debug = True  # might be overridden by child class Annotate
        app = self.app
        (specDir, annoDir) = annotateDir(app, TOOLKEY)
        self.specDir = specDir
        self.annoDir = annoDir
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

        def get0(F, slots):
            text = getText(F, slots)
            text = NON_ALPHA_RE.sub("", text)
            text = text.replace(" ", ".").strip(".").lower()
            return text

        def get1(F, slots):
            return self.settings.defaultValues[features[1]]

        self.featureDefault = {
            features[0]: get0,
            features[1]: get1,
        }


def ucFirst(x):
    return x[0].upper() + x[1:].lower()


def getText(F, slots):
    text = "".join(f"""{F.str.v(s)}{F.after.v(s) or ""}""" for s in slots).strip()
    text = WHITE_RE.sub(" ", text)
    return text
