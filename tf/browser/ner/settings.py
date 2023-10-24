"""Corpus dependent setup of the annotation tool.

To see how this fits among all the modules of this package, see
`tf.browser.ner.annotate` .
"""

import re

from ...core.helpers import console as cs
from ...core.files import annotateDir, readYaml

TOOLKEY = "ner"
"""The name of this annotation tool.

This name is used

*   in directory paths on the file system to find the data that is managed by this tool;
*   as a key to address the in-memory data that belongs to this tool;
*   as a prefix to modularize the Flask app for this tool within the encompassing
    TF browser Flask app and also it CSS files.
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

LIMIT_BROWSER = 100
"""Limit of amount of buckets to load on one page when in the TF browser.

This is not a hard limit. We only use it if the page contains the whole corpus or
a filtered subset of it.

But as soon we have selected a token string or an entity, we show all buckets
that contain it, no matter how many there are.

!!! note "Performance"
    We use the
    [CSS device *content-visibility*](https://developer.mozilla.org/en-US/docs/Web/CSS/content-visibility)
    to restrict rendering to the material that is visible in the viewport. However,
    this is not supported in Safari, so the performance may suffer in Safari if we load
    the whole corpus on a single page.

    In practice, even in browsers that support this device are not happy with a big
    chunk of HTML on the page, since they do have to build a large DOM, including
    event listeners.

    That's why we restrict the page to a limited amount of buckets.

    But when a selection has been made, it is more important to show the whole,
    untruncated result set, than to incur a performance penalty.
    Moreover, it is hardly the case that a selected entity of occurrence occurs in a
    very large number of buckets.
"""

LIMIT_NB = 20
"""Limit of amount of buckets to load on one page when in a Jupyter notebook.

See also `LIMIT_BROWSER` .
"""

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
"""CSS style configuration for entity features.

Here we define properties of the styling of the entity features and their
values.
Since these features are defined in configuration, we cannot work with a fixed
style sheet.

We divide entity features in *keyword* features and *free* features.
The typical keyword feature is `kind`, it has a limited set of values.
The typical free feature is `eid`, it has an unbounded number of values.

As it is now, we could have expressed this in a fixed stylesheet.
But if we open up to allowing for more entity features, we can use this setup
to easily configure the formatting of them.

However, we should move these definitions to the `ner.yaml` file then, so that the
only place of configuration is that yaml file, and not this file.
"""

WHITE_RE = re.compile(r"""\s{2,}""", re.S)
NON_ALPHA_RE = re.compile(r"""[^\w ]""", re.S)

SORTDIR_DESC = "d"
"""Value that indicates the descending sort direction."""

SORTDIR_ASC = "a"
"""Value that indicates the ascending sort direction."""

SORTDIR_DEFAULT = SORTDIR_ASC
"""Default sort direction."""

SORTKEY_DEFAULT = "freqsort"
"""Default sort key."""

SORT_DEFAULT = (SORTKEY_DEFAULT, SORTDIR_DESC)
"""Default sort key plus sort direction combination."""

SC_ALL = "a"
"""Value that indicates *all* buckets."""

SC_FILT = "f"
"""Value that indicates *filtered* buckets."""


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
        api = app.api
        F = api.F

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

        def getText(slots):
            """Get the text for a number of slots.

            Leading and trailing whitespace is stripped, and inner whitespace is
            normalized to a single space.
            """
            text = "".join(
                f"""{F.str.v(s)}{F.after.v(s) or ""}""" for s in slots
            ).strip()
            text = WHITE_RE.sub(" ", text)
            return text

        def get0(slots):
            """Makes an identifier value out of a number of slots.

            This acts as the default value for the `eid` feature of new
            entities.

            Starting with the whitespace-normalized text of a number of slots,
            the string is lowercased, non-alphanumeric characters are stripped,
            and spaces are replaced by dots.
            """
            text = getText(slots)
            text = NON_ALPHA_RE.sub("", text)
            text = text.replace(" ", ".").strip(".").lower()
            return text

        def get1(slots):
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

    def getStrings(self, tokenStart, tokenEnd):
        """Gets the text of the tokens occupying a sequence of slots.

        Parameters
        ----------
        tokenStart: integer
            The position of the starting token.
        tokenEnd: integer
            The position of the ending token.

        Returns
        -------
        tuple
            The members consist of the string values of the tokens in question,
            as far as these values are not purely whitespace.
            Also, the string values are stripped from leading and trailing whitespace.
        """
        app = self.app
        api = app.api
        F = api.F

        return tuple(
            token
            for t in range(tokenStart, tokenEnd + 1)
            if (token := (F.str.v(t) or "").strip())
        )

    def console(self, msg, **kwargs):
        """Print something to the output.

        This works exactly as `tf.core.helpers.console`

        It is handy to have this as a method on the Annotate object,
        so that we can issue temporary console statements during development
        without the need to add an `import` statement to the code.
        """
        cs(msg, **kwargs)
