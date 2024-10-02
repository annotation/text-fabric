"""
# App settings

Developers can create corpus apps by specifying a `config.yaml` with settings.
These settings will be read, checked, and transformed into configuration data
that is read by the app, see `tf.advanced.settings.showContext`

See for examples:

*   [ETCBC/bhsa](https://github.com/etcbc/bhsa/blob/master/app/config.yaml).
*   [Nino-cunei/uruk](https://github.com/Nino-cunei/uruk/blob/master/app/config.yaml).

# Config specs

Here is a specification of all settings you can configure for an app.

Each section below corresponds to a main key in the `config.yaml` of an app.

Everything is optional, an empty `config.yaml` is valid.
TF tries hard to supply reasonable defaults on the basis of the corpus
data it has loaded.

## `apiVersion`

To let TF check whether its version matches the version of the corpus app

Default:
:   integer `1`

---

## `dataDisplay`

Generic display parameters.

Default:
:   dict `{}`

---

### `browseContentPretty`

Whether the content is shown as a list of subsectional items
contained in the selected item or as a pretty display of the item itself

Default:
:   boolean `false`

---

### `browseNavLevel`

The section level up to which the TF browser shows a hierarchical tree.

Values
: `1` or `2`

Default:
:   *one less than the number of section types*

---

### `exampleSection`

Placeholder text for passage entry fields in the TF browser.

Default:
:   string `book 1`

---

### `exampleSectionHtml`

Formatted placeholder text for passage entry fields in the TF browser.

Default:
:   string `<code>piece 1</code>`

---

### `excludedFeatures`

Features that are present in the data source but will not be loaded for the TF browser.

Default:
:   list `[]`

---

### `noneValues`

Feature values that are deemed uninformative, e.g. `None`, `'NA'`

Default:
:   list `[]`

---

### `sectionSep1`

Separator between main and secondary sections in a passage reference;
e.g. the space in `Genesis 1:1`

Default:
:   string: ` ` (*space*)

---

### `sectionSep2`

Separator between secondary and tertiary sections in a passage reference;
e.g. the `:` in `Genesis 1:1`

Default:
:   string `:`

---

### `showVerseInTuple`

Show the full text of verse-like nodes in tables and tuples
(in `tf.advanced.display.plainTuple` and `tf.advanced.display.table`)

Default:
:   boolean `false`

---

### `textFormat`

The default text format.

Default:
:   string `None`

A `None` value will be interpreted later as the default text format `text-orig-full`.

---

### `textFormats`

``` yaml
textFormats:
    layout-orig-full: layoutRich
```

Additional text formats that can use HTML styling.

Keys
:   names of existing and new text formats.

Values
:   (method, style)

where

method
:   name of a method that implements that format.
    If the name is `xxx`, or `typexxx`
    then `app.py` should implement a method `fmt_xxx(node, **kwargs)`
    to produce HTML for node `node`.
    This function will passed the `outer=True` if called by a plain or pretty at
    the outer level, level=recursion depth, and `first=True, last=True`
    if the node is on a leftmost resp.
    rightmost branch in the tree of children below the outer node.
style
:   a keyword indicating in what style the format should be set:
    `normal`, `source`, `trans`, `phono`, `orig`.

Default:
:   dict `{}`

---

## `docs`

In the settings below you may refer to provenance settings, like `{org}` and `{repo}`
You may refer to NBViewer with `{urlNb}` and to GitHub with `{urlGh}`

Default:
:   dict `{}`

---

### `charText`

Hint text when a user hovers over the `charUlr` link to a page that describes how
TF features represent text

Default:
:   string `''`

---

### `charUrl`

Start page for character coding documentation.
TF supports several writing systems with character- and transcription tables.
Replace `Transcription` by the writing system relevant for your data.
`{tfDoc}` will be replaced by the root location of the online TF documentation.

If it is left out, it will point to the transcription table in the TF docs
that corresponds with the writing setting.

If the writing setting is also left out, it will point to the page
from where you can find info about all supported writing systems.

Default:
:   string `{tfDoc}/writing/transcription/`

---

### `docBase`

Base URL page for the corpus documentation

Default:
:   string `{docRoot}/{org}/{repo}/blob/{branch}/docs`

---

### `docExt:`

The extension of documentation pages

Default:
:   string `.md`

---

### `docPage`

Landing page for the corpus documentation

Default:
:   string `home`

---

### `docRoot`

Where the docs are: on GitHub or GitLab (default),
or on NBViewer (`{urlNb}`) or somewhere else.

Default:
:   string `{urlGh}` or `https://backend` where `backend` is a valid back-end

---

### `featureBase`

URL template for feature by feature documentation
`{tfDoc}` will be replaced by the root location of the documentation as set above.
The variable part `<feature>` will be replaced by the names of the features.

Default:
:   string `{docBase}/features/<feature>{docExt}`

---

### `featurePage`

Start page for feature documentation,
will be filled in into `featureBase` for the variable `<feature>`.

Default:
:   string `home`

---

## `interfaceDefaults`

The following options can be passed to the display functions
`tf.advanced.display.plain` and `tf.advanced.display.pretty`.
They can also be set in the TF Browser.
The values set here are the defaults as given by this app.
Not all options are relevant for all corpora.
Only relevant options should be included.
By setting the default to `None`, the option will not be shown
on the TF browser interface.

These options are described in `tf.advanced.options`: all options
marked as **interface option**.


Default:
:   dict `{}`

---

## `provenanceSpec`

Provenance parameters are used to fetch data and to report provenance in data exports.

Default:
:   dict `{}`

---

### `corpus`

A user-friendly name for your corpus.

Default:
:   string `null`

---

### `doi`

If your data is archived: the DOI
[Digital Object Identifier](https://www.doi.org)
of the archived version, like
`xx.yyyy/archive.zzzzzzz` without the `https://doi.org/` in front.

Default:
:   string `null`

---

### `extraData`

If not `null`, it is the path inside the repo to the directory
that holds extra data to be distributed alongside the corpus

Default:
:   string `null`

---

### `graphicsRelative`

If not `null`, it is the path inside the repo to the directory
that holds the graphics files

Default:
:   string `null`

---

### `moduleSpecs`

You can specify modules that should always be loaded with the core data,
as many as you want:

``` yaml
moduleSpecs:
-   backend: gitlab
    org: researcher1
    repo: work1
    relative: tf
    corpus: speicalism1
    docUrl: '{urlNb}/researcher1/work1/blob/master/programs/specialism1.ipynb'
    doi: xx.yyyy/archive.zzzzzzz

-   backend: gitlab.huc.knaw.nl
    org: researcher2
    repo: work2
    relative: tf
    corpus: speicalism2
    docUrl: '{urlNb}/researcher2/work2/blob/master/programs/specialism2.ipynb'
    doi: uu.vvvv/archive.wwwwwww
```

If modules have the same org or repo as the main data, these do not have to
be specified.
If a module has a relative attribute equal to `tf`, it can be left out.

Default:
:   list `[]`

---

### `org`

The GitHub organization or the GitLab group under which your TF data resides.

Default:
:   string `annotation`

---

### `relative`

The path inside the repo to the directory
that holds the version directories of the TF data.

Default:
:   string `tf`

---

### `repo`

The GitHub repo or the GitLab project under which your TF data resides

!!! hint
    *org/repo* = `annotation/default` acts as placeholder for app-less datasets.

Default:
:   string `default`

---

### `version`

The version directory with the actual `tf` files that will be used.

Default:
:   string `null`

---

### `branch`

The branch on the back-end where the corpus data is stored.

Nowadays, repositories typically work with `main` where they used to work
with `master`.

Default:
:   string `master`

---

### `pages`

The URL pattern of the Pages publication service of the back-end, in case it is
unpredictable from the back-end itself.

If this value is `None`, the following defaults are used, depending on the choice of
back-end:

*   for `github.com` the default is `github.io`,
    so pages are addressed by *org*`.github.io/`*repo*;
*   for `gitlab.com` the default is `gitlab.io`,
    so pages are addressed by *org*`.gitlab.io/`*repo*;
*   for on-premise GitLab, e.g. `git.diginfra.net` the default is
    `pages.diginfra.net`,
    so pages are addressed by *org*`.pages.diginfra.net/`*repo*;

If these defaults do not work for a particular situation, you can change the
pattern here. For example, in the last case above, if the on-premise GitLab has a
repository `mondriaan/letters` whose pages are served on
`mondriaan.diginfra.vu/letters`, you have to specify `pages="diginfra.vu"` .


Default:
:   void `None`

---

### `webBase`

If present, the base URL for an online edition of the corpus.

Default:
:   string `null`

---

### `webFeature`

If passed, contains the name of the feature that stores the part of the web link for
that node that comes after `webBase`.
This overrides `webUrl` in that when `webFeature` is present, and a node has a value
for it, than that value will be used in composing the web link, rather than filling
the template `webLink` with values from the headings.

Default:
:   string `null`

---

### `webHint`

If passed, will be used as hint text when the user hovers over a web link

Default:
:   string `null`

---

### `webLang`

If passed, the language in which section headings must be generated in web links

Default:
:   string `null`

---

### `webLexId`

If present, it is either:

*   the name of a feature that contains the lexeme id for lexeme nodes.

or

*   `true` and then the app should implement `app.getLexId(n)`
    that computes lexeme ids for lexeme nodes.

The lexeme id is the one used in the online edition of the corpus to point to lexemes.

Default:
:   string | boolean `null`

---

### `webOffset`

If present, it is a dictionary that specifies offsets between page numbers as derived
from section headings and page numbers as needed in the query string for the URL
of the online resource (see `webUrl`).

Suppose we need to offset sections of level 2 depending on the section of level 1
they are in.
For example, in the
[Missieven corpus](https://github.com/clariah/wp6-missieven/blob/master/app/config.yaml)
we have section levels 1=volume, 2=page, 3=line.
In each volume, the logical page 1 must be translated into a higher
number, depending on the number of preface pages in that volume.

The value of this parameter is a dict of dictionaries.

The first level of keys specifies the section level of the sections that needs offsets.
In our example case we specify offsets for pages (level 1), so the key is `2`.

The second level of keys are the values of section headings of the containing sections,
the volumes.
In our example these are integers 1 - 13.

Finally, the value is the offset that will be applied for pages in that volume.
Values are positive or negative integers or 0.
Missing values translate to 0 or the empty string.

!!! note "integer or string"
    Headings may be integers or strings.
    If a heading is an integer, the offset will be added to it, if it is a string,
    the offset will be concatenated to it.

### `webUrl`

If present, `webLink(node)` will use this as a template to generate a URL
to an online edition of the node.

This may happen in two ways:

*   From a feature whose name is given in `webFeature` we take the value for node `n`.
    If that value exists, it will be appended to the value of `webBase` and that
    will be the link.
*   If `webFeature` is not given, or if it is given,
    but the feature has no value for `n`, the web link will be computed from the
    section headings.
    The following place holders will be honoured:

    *   `{webBase}`: the `webBase` above
    *   `<1>` : value for section heading 1
    *   `<2>` : value for section heading 2
    *   `<3>` : value for section heading 3
    *   `{version}`: version of the TF resource

Default:
:   string `null`

---

### `webUrlZeros`

If present, it specifies for each section level whether its heading
should be padded with zeros.
This padding will be applied to the real values substituted for `<1>`, `<2>` and `<3>`
in the `webUrl` setting.
If there is no value or the value is 0 for a section level, there will be
no padding.
Otherwise is specifies the length to which values should be padded.

E.g. if a value is `123` and the amount of padding specified is 5, two `0`
will be prepended.
This holds also for values that are not integers:
if the value is `a35` and the padding is 5, again two `0` will be prepended.

Default:
:   dict `null`

---

### `webUrlLex`

If present, `webLink(node)` will use this as a template to generate a URL
to an online edition of the lexeme node.

The following place holders will be honoured:
*   `{webBase}`: the `webBase` value above
*   `<lid>` : value for the id of the lexeme
*   `{version}` version of the TF resource

Default:
:   string `null`

---

### `zip`

Only used by `tf-zip` when collecting data into zip files
as attachments to a GitHub / GitLab release.

If left to `null`, will be configured to use the main repo and the modules.

You can also use this scheme to include other data from the repository.
Note that graphics data will be packaged automatically.

You can specify the main repo, modules, and related data:

*   `zip=["repo"]`: Only the main module.

*   `zip=["repo", "mod1", "mod2"]` : if org and relative for the modules
    are the same as for are the main repo)

Default:
:   list `["repo"] + [("org1", "mod1", "relative1"), ("org2", "mod2", "relative2")]`

    where all modules mentioned in the `moduleSpecs` will be filled in.

---

## `typeDisplay`

Here are the type-specific display parameters.
If some types do not need configuration, you may leave them out.

The keys are node types as they exist in the corpus for which this is an app.
The value for each key is a dictionary with the following possible contents
(you may leave out keys if you are content with its default value).

Default:
:   dict `{}`

---

### `base`

If present and `true`: this type acts as the base type.

Default:
:   boolean `true` for the slot type, `false` for other types.

---

### `boundary`

If true, will only mark the start and end boundaries of the node,
without wrapping its descendants in a new box.

!!! caution "gaps"
    If the node has gaps, they will not be marked.

Default:
:   boolean `false`

---

---

### `children`

Which type of child nodes to be included in the display.
The value should be a node type or a set of node types:

``` yaml
children: aya

children:
  - sura
  - aya
```

!!! hint "Reductive"
    Use this if you want to reduce the number of section levels in a display.
    For example, in the Quran there are various types of sections, not very well
    related, and we do not want to get trees of all those sections. Rather, each section
    should unravel straight into the lowest one: the `aya`.

Default:
:   set, `set()`

---

### `condense`

If `true`: this type is the default condense type.

When displaying tuples of nodes,
they will be divided over displays of nodes of this type.

The default is:

`true` for the lowest section type, if there are section types defined in `otext.tf`.

If there are no sections, we pick a medium-sized node type.
If there are no such node types, we pick the slot type, but this is pathological.

Default:
:   boolean `false`

---

### `exclude`

Conditions that will exclude nodes of this type from the display.

All nodes that satisfy at least one of these conditions will be left out.

!!! hint
    Use this if you want to exclude particular nodes of some type, e.g. in
    [ETCBC/dss](https://github.com/etcbc/dss/blob/master/app/config.yaml).
    where we want to prevent line terminator signs.

The value is a dictionary of feature name - value pairs.

``` yaml
exclude:
    type: term
```

Default:
:   dict, `{}`

### `features`

Pretty displays: which node features to display as `name=value`.

You can also specify lookup feature values for upper nodes, e.g. `lex:gloss`
which will look for a `lex` node above the current node and retrieve its `gloss` value.

Default:
:   list of string `''`

---

### `featuresBare: feat1 feat2`

Pretty displays: which features to display by value only
(the feature name is not mentioned).

Things like `lex:gloss` are allowed.

Default:
:   list of string `''`

---

### `flow`

Pretty: whether the container should arrange its subdisplays as a column or as a row.

Values: `hor`, `ver`

Default:
:   string

    *   `ver` if level is 3 (typically section types), except for the verse-like types
    *   `ver` if level is 0 (typically slot types and lexeme types)
    *   `hor` if level is 1 or 2 (typically linguistic types at sentence level) and
        for the verse-like types

---

### `graphics`

If `true`, then there is additional graphics available for nodes of this
type.

The app needs to define a function

``` python
getGraphics(isPretty, node, nodeType, isOuter)
```

results in HTML code for sourcing the graphics.

See [Nino-cunei/uruk](https://github.com/Nino-cunei/uruk/blob/master/app/app.py).

Default
:   boolean `null`

---

### `hidden`

Plain and pretty: whether nodes of this type must be hidden by default.
See for example the `bhsa`, where the `atom` types are hidden by default.

The user of the app can selectively mark any node type (except the slot type)
as hidden, by means of `hiddenTypes` in `tf.advanced.options`.

The user can also switch between showing and hiding hidden node types by passing
the display option `hideTypes=False` or `hideTypes=True`.

Default
:   boolean `false`

---

### `isBig`

If `true`, then this type counts as a big type in plain displays.

Default
:   boolean `false`

---

### `label, template`

Node contribution for plain and pretty displays (template is for plain displays,
label is for pretty displays).

You can have features filled in by mentioning them by name in the template, e.g.
`{name1} - {name2}`.

If you specify `true` as the template or label, the node information will be
the result of:

*   section and structure types nodes: a heading
*   other nodes: plain text of the node

Default:
:   string

    *   `true` for the slot type
    *   `true` for the section and structure types
    *   `""` for all other types

---

### `level`

Pretty: the visual style of the container box of this node, values 0, 1, 2, 3.
The bigger the number, the heavier the borders of the boxes.

The default is:

*   3 for types known as section or structure types, including the verse-like types
*   0 for the slot type and types known as lexeme types
*   1 or 2 for the remaining types: the bigger types are 2, the smaller types are 1

Default
:   integer `1`

---

### `lexOcc`

If present, indicates that this is a lexeme type,
and it points to the type of things that are occurrences of lexemes.
Lexemes are displayed with an indication of their first and last occurrence.

Default
:   string `slotType` (not literal, the value for the slot type)

---

### `lineNumber`

If present, it should be the name of a feature that holds source line numbers.

Default
:   string `null`

---

### `stretch`

Pretty: whether the children should be stretched in the direction perpendicular
to their stacking.

The default is:

*   `true` if the children form a row (then each child is stretched vertically)
*   `false` if the children form a column
    (then each child is NOT stretched horizontally).

Default
:   boolean `true`

!!! hint
    For some types in
    [Nino-cunei/uruk](https://github.com/Nino-cunei/uruk/blob/master/app/config.yaml)
    it is needed to deviate from the default.

---

### `style`

Formatting key for plain and pretty displays.

The label or template may need a special style to format it with.
You can specify:

`normal`
:   normal non-corpus text

`source`
:   source text of the corpus (before conversion)

`trans`
:   transcription of corpus text

`phono`
:   phonological / phonetic transcription of corpus text

`orig`
:   corpus text in UNICODE

*anything else*
:   will be inserted as an extra CSS class.

Default
:   string `null`

---

### `transform`

Sometimes you do not want to display straight feature values, but transformed ones.
For each feature you can specify a transform function `f`:
E.g.

``` yaml
transform:
    type: ctype
```

The feature `type`, when computed for a node of the type we are configuring here,
will yield a value which is transformed by function `ctype` to a new value.
In your app code you have to implement:

``` python
def transform_f(app, origValue):
    ...
    newValue = ...
    return newValue
```

Default
:   dict `{}`

---

### `verselike`

Whether this type should be formatted as a verse

The default is:
`true` for the lowest section type, if there are section types in `otext.tf`.

But more types can be declared as verse-like, e.g. `halfverse` in the
[ETCBC/bhsa](https://github.com/etcbc/bhsa/blob/master/app/config.yaml).

---

### `wrap`

Pretty: whether the child displays may be wrapped.

Default:
:   boolean

    *   `true` if the children form a row, such rows may be wrapped
    *   `false` if the children form a column;
        such columns may not be wrapped (into several columns)

!!! hint
    For some types in
    [Nino-cunei/uruk](https://github.com/Nino-cunei/uruk/blob/master/app/config.yaml)
    it is needed to deviate from the default.

---

## `writing`

Code for triggering special fonts, see `tf.writing`.

Default:
:   string `''`

---
"""


import re
import types

from ..parameters import BRANCH_DEFAULT, OMAP
from ..core.helpers import console, mergeDictOfSets
from ..core.files import backendRep, URL_TFDOC, prefixSlash
from .options import INTERFACE_OPTIONS
from .helpers import (
    parseFeatures,
    transitiveClosure,
    showDict,
    ORIG,
    NORMAL,
    dh,
)


VAR_PATTERN = re.compile(r"\{([^}]+)\}")

WRITING_DEFAULTS = dict(
    akk=dict(
        language="akkadian",
        direction="ltr",
    ),
    hbo=dict(
        language="hebrew",
        direction="rtl",
    ),
    syc=dict(
        language="syriac",
        direction="rtl",
    ),
    uga=dict(
        language="ugaritic",
        direction="ltr",
    ),
    ara=dict(
        language="arabic",
        direction="rtl",
    ),
    grc=dict(
        language="greek",
        direction="ltr",
    ),
    cld=dict(
        language="aramaic",
        direction="ltr",
    ),
)
WRITING_DEFAULTS[""] = dict(
    language="",
    direction="ltr",
)

FONT_BASE = (
    "https://github.com/annotation/text-fabric/blob/master/tf/browser/static/fonts"
)

METHOD = "method"
STYLE = "style"
DESCEND = "descend"

FMT_KEYS = {METHOD, STYLE}

DEFAULT_CLS = "txtn"
DEFAULT_CLS_SRC = "txto"
DEFAULT_CLS_ORIG = "txtu"
DEFAULT_CLS_TRANS = "txtt"
DEFAULT_CLS_PHONO = "txtp"

FORMAT_CLS = (
    (NORMAL, DEFAULT_CLS),
    (ORIG, DEFAULT_CLS_ORIG),
    ("trans", DEFAULT_CLS_TRANS),
    ("source", DEFAULT_CLS_SRC),
    ("phono", DEFAULT_CLS_PHONO),
)

LEVEL_DEFAULTS = dict(
    level={
        4: dict(flow="hor"),
        3: dict(flow="hor"),
        2: dict(flow="hor"),
        1: dict(flow="hor"),
        0: dict(flow="ver"),
    },
    flow=dict(ver=dict(wrap=False, stretch=False), hor=dict(wrap=True, stretch=True)),
    wrap=None,
    stretch=None,
)

RELATIVE_DEFAULT = "tf"

MSPEC_KEYS = set(
    """
    backend
    org
    repo
    relative
    corpus
    docUrl
    doi
""".strip().split()
)

PROVENANCE_DEFAULTS = (
    ("org", None),
    ("repo", None),
    ("relative", prefixSlash(RELATIVE_DEFAULT)),
    ("extraData", None),
    ("graphicsRelative", None),
    ("version", None),
    ("branch", BRANCH_DEFAULT),
    ("pages", None),
    ("moduleSpecs", ()),
    ("zip", None),
    ("corpus", "TF dataset (unspecified)"),
    ("doi", None),
    ("webBase", None),
    ("webHint", None),
    ("webLang", None),
    ("webLexId", None),
    ("webOffset", None),
    ("webFeature", None),
    ("webUrl", None),
    ("webUrlZeros", None),
    ("webUrlLex", None),
    ("webLexId", None),
    ("webHint", None),
)


def DOC_DEFAULTS(backend):
    return (
        ("docRoot", f"{backendRep(backend, 'url')}"),
        ("docExt", ".md"),
        ("docBase", "{docRoot}/{org}/{repo}/blob/{branch}/docs"),
        ("docPage", "home"),
        ("docUrl", "{docBase}/{docPage}{docExt}"),
        ("featureBase", "{docBase}/features/<feature>{docExt}"),
        ("featurePage", "home"),
        ("charUrl", "{tfDoc}/writing/{charLoc}"),
        ("charText", "How TF features represent text"),
    )


DATA_DISPLAY_DEFAULTS = (
    ("excludedFeatures", set(), False),
    ("noneValues", {None}, False),
    ("sectionSep1", " ", False),
    ("sectionSep2", ":", False),
    ("textFormats", {}, True),
    ("textFormat", None, True),
    ("browseNavLevel", None, True),
    ("browseContentPretty", False, False),
    ("showVerseInTuple", False, False),
    ("exampleSection", None, True),
    ("exampleSectionHtml", None, True),
)

TYPE_KEYS = set(
    """
    base
    children
    condense
    features
    featuresBare
    flow
    graphics
    hidden
    isBig
    label
    level
    lexOcc
    lineNumber
    stretch
    template
    transform
    verselike
    wrap
""".strip().split()
)

HOOKS = """
    transform
    afterChild
    plainCustom
    prettyCustom
""".strip().split()


class AppCurrent:
    def __init__(self, specs):
        self.allKeys = set()
        self.update(specs)

    def update(self, specs):
        allKeys = self.allKeys
        for k, v in specs.items():
            allKeys.add(k)
            setattr(self, k, v)

    def get(self, k, v):
        return getattr(self, k, v)

    def set(self, k, v):
        self.allKeys.add(k)
        setattr(self, k, v)


class Check:
    def __init__(self, app, withApi):
        self.app = app
        self.withApi = withApi
        self.errors = []

    def checkSetting(self, k, v, extra=None):
        app = self.app
        withApi = self.withApi
        errors = self.errors
        dKey = self.dKey
        specs = app.specs
        interfaceDefaults = {inf[0]: inf[1] for inf in INTERFACE_OPTIONS}

        if withApi:
            customMethods = app.customMethods
            api = app.api
            F = api.F
            T = api.T
            Fall = api.Fall
            allNodeFeatures = set(Fall())
            nTypes = F.otype.all
            sectionTypes = T.sectionTypes

            if k in {"template", "label"}:
                (template, feats) = extra
                if template is not True and type(template) is not str:
                    errors.append(f"{k} must be `true` or a string")
                for feat in feats:
                    if feat not in allNodeFeatures:
                        if feat not in customMethods.transform.get(dKey, {}):
                            errors.append(f"{k}: feature {feat} not loaded")
            elif k in {"featuresBare", "features"}:
                feats = extra[0]
                tps = extra[1].values()
                for feat in feats:
                    if feat not in allNodeFeatures:
                        errors.append(f"{k}: feature {feat} not loaded")
                for tp in tps:
                    if tp not in nTypes:
                        errors.append(f"{k}: node type {tp} not present")
            elif k == "exclude":
                if type(v) is not dict():
                    errors.append(f"{k}: must be a dict of features and values")
                    for feat in v:
                        if feat not in allNodeFeatures:
                            errors.append(f"{k}: feature {feat} not loaded")
            elif k == "base":
                pass
            elif k == "lineNumber":
                if v not in allNodeFeatures:
                    errors.append(f"{k}: feature {v} not loaded")
            elif k == "browseNavLevel":
                legalValues = set(range(len(sectionTypes)))
                if v not in legalValues:
                    allowed = ",".join(sorted(legalValues))
                    errors.append(f"{k} must be an integer in {allowed}")
            elif k == "children":
                if type(v) is not str and type(v) is not list:
                    errors.append(f"{k} must be a (list of) node types")
                else:
                    v = {v} if type(v) is str else set(v)
                    for tp in v:
                        if tp not in nTypes:
                            errors.append(f"{k}: node type {tp} not present")
            elif k in {"lexOcc"}:
                if type(v) is not str or v not in nTypes:
                    errors.append(f"{k}: node type {v} not present")
            elif k == "transform":
                for feat, method in extra.items():
                    if type(method) is str:
                        errors.append(f"{k}:{feat}: {method}() not implemented in app")
            elif k == "style":
                if type(v) is not str or v.lower() != v:
                    errors.append(f"{k} must be an all lowercase string")
            elif k in interfaceDefaults:
                allowed = self.extra[k]
                if not allowed and v is not None:
                    errors.append(
                        f"{k}={v} is not useful (dataset lacks relevant features)"
                    )
            elif k == "textFormats":
                formatStyle = specs["formatStyle"]
                if type(v) is dict:
                    for fmt, fmtInfo in v.items():
                        for fk, fv in fmtInfo.items():
                            if fk not in FMT_KEYS:
                                errors.append(f"{k}: {fmt}: illegal key {fk}")
                                continue
                            if fk == METHOD:
                                (descendType, func) = T.splitFormat(fv)
                                func = f"fmt_{func}"
                                if not hasattr(app, func):
                                    errors.append(
                                        f"{k}: {fmt} needs unimplemented method {func}"
                                    )
                            elif fk == STYLE:
                                if fv not in formatStyle:
                                    if fv.lower() != fv:
                                        errors.append(
                                            f"{k}: {fmt}: style {fv}"
                                            f" must be all lowercase"
                                        )
                else:
                    errors.append(f"{k} must be a dictionary")
        else:
            if k in {"excludedFeatures", "noneValues"}:
                if type(v) is not list:
                    errors.append(f"{k} must be a list")
            elif k in {
                "sectionSep1",
                "sectionSep2",
                "exampleSection",
                "exampleSectionHtml",
            }:
                if type(v) is not str:
                    errors.append(f"{k} must be a string")
            elif k == "writing":
                legalValues = set(WRITING_DEFAULTS)
                if v not in legalValues:
                    allowed = ",".join(legalValues - {""})
                    errors.append(f"{k} must be the empty string or one of {allowed}")
            elif k in {"direction", "language"}:
                legalValues = {w[k] for w in WRITING_DEFAULTS}
                if v not in legalValues:
                    allowed = ",".join(legalValues)
                    errors.append(f"{k} must be one of {allowed}")
            elif k in {
                "browseContentPretty",
                "base",
                "condense",
                "graphics",
                "hidden",
                "isBig",
                "showVerseInTuple",
                "stretch",
                "verselike",
                "wrap",
            }:
                legalValues = {True, False}
                if v not in legalValues:
                    allowed = "true,false"
                    errors.append(f"{k} must be a boolean in {allowed}")
            elif k == "flow":
                legalValues = {"hor", "ver"}
                if v not in legalValues:
                    allowed = ",".join(legalValues)
                    errors.append(f"{k} must be a value in {allowed}")
            elif k == "level":
                legalValues = set(range(len(4)))
                if v not in legalValues:
                    allowed = ",".join(sorted(legalValues))
                    errors.append(f"{k} must be an integer in {allowed}")

    def checkGroup(self, cfg, defaults, dKey, postpone=set(), extra=None):
        self.cfg = cfg
        self.defaults = defaults
        self.dKey = dKey
        self.extra = extra
        errors = []

        errors.clear()
        dSource = cfg.get(dKey, {})

        for k, v in dSource.items():
            if k in defaults:
                if k not in postpone:
                    self.checkSetting(k, v)
            else:
                errors.append(f"Illegal parameter `{k}` with value {v}")

    def checkItem(self, cfg, dKey):
        self.cfg = cfg
        self.dKey = dKey
        errors = self.errors

        errors.clear()
        if dKey in cfg:
            self.checkSetting(dKey, cfg[dKey])

    def report(self):
        errors = self.errors
        dKey = self.dKey

        if errors:
            console(f"App config error(s) in {dKey}:", error=True)
            for msg in errors:
                console(f"\t{msg}", error=True)

        self.errors = []


def _fillInDefined(template, data):
    val = template.format(**data)
    return None if "None" in val else val


def setAppSpecs(app, cfg, reset=False):
    backend = app.backend
    if not reset:
        app.customMethods = AppCurrent({hook: {} for hook in HOOKS})
    specs = dict(
        urlGh=backendRep(backend, "rep"),
        urlNb=backendRep(backend, "urlnb"),
        tfDoc=URL_TFDOC,
    )
    app.specs = specs
    specs.update(cfg)
    if "apiVersion" not in specs:
        specs["apiVersion"] = None
    checker = Check(app, False)

    dKey = "writing"
    checker.checkItem(cfg, dKey)
    checker.report()
    value = cfg.get(dKey, "")
    specs[dKey] = value
    for k, v in WRITING_DEFAULTS[value].items():
        specs[k] = v
        if k == "language":
            specs["charLoc"] = f"{v}.html" if v else ""
    extension = f" {value}" if value else ""
    defaultClsOrig = f"{DEFAULT_CLS_ORIG}{extension}"
    specs.update(extension=extension, defaultClsOrig=defaultClsOrig)

    for dKey, defaults in (
        ("provenanceSpec", PROVENANCE_DEFAULTS),
        ("docs", DOC_DEFAULTS(backend)),
    ):
        checker.checkGroup(cfg, {d[0] for d in defaults}, dKey)
        checker.report()
        dSource = cfg.get(dKey, {})
        for k, v in defaults:
            val = dSource.get(k, v)
            val = (
                None
                if val is None
                else _fillInDefined(val, specs)
                # else val.format(**specs)
                if type(val) is str
                else val
            )
            specs[k] = val

        if dKey == "provenanceSpec":
            moduleSpecs = specs["moduleSpecs"] or []
            for moduleSpec in moduleSpecs:
                for k in MSPEC_KEYS:
                    if k in moduleSpec:
                        v = moduleSpec[k]
                        if k == "docUrl" and v is not None:
                            # v = v.format(**specs)
                            v = _fillInDefined(v, specs)
                            moduleSpec[k] = v
                    else:
                        moduleSpec[k] = (
                            specs.get(k, None)
                            if k in {"backend", "org", "repo"}
                            else prefixSlash(RELATIVE_DEFAULT)
                            if k == "relative"
                            else None
                        )

        specs[dKey] = {k[0]: specs[k[0]] for k in defaults}

    if specs["zip"] is None:
        org = specs["org"]
        repo = specs["repo"]
        extraData = specs["extraData"]
        extraModule = [(org, repo, extraData)] if extraData else []
        graphicsRelative = specs["graphicsRelative"]
        graphicsModule = [(org, repo, graphicsRelative)] if graphicsRelative else []
        specs["zip"] = (
            [repo]
            + [
                (m["backend"], m["org"], m["repo"], prefixSlash(m["relative"]))
                for m in moduleSpecs
            ]
            + graphicsModule
            + extraModule
        )

    for dKey, method in (
        ("dataDisplay", getDataDefaults),
        ("typeDisplay", getTypeDefaults),
    ):
        method(app, cfg, dKey, False)

    app.context = AppCurrent(specs)


def setAppSpecsApi(app, cfg):
    api = app.api
    T = api.T

    specs = app.specs

    for dKey, method in (
        ("dataDisplay", getDataDefaults),
        ("typeDisplay", getTypeDefaults),
    ):
        method(app, cfg, dKey, True)

    if specs.get("textFormat", None) is None:
        specs["textFormat"] = T.defaultFormat

    dKey = "interfaceDefaults"
    interfaceDefaults = {inf[0]: inf[1] for inf in INTERFACE_OPTIONS}
    dSource = cfg.get(dKey, {})
    specific = {"lineNumbers", "showGraphics"}

    allowed = {}
    for k, v in interfaceDefaults.items():
        allow = (
            (
                k == "lineNumbers"
                and specs["lineNumberFeature"]
                or k == "showGraphics"
                and specs["hasGraphics"]
            )
            if k in specific
            else True
        )
        if k in dSource:
            val = dSource[k]
            default = val if allow else None
        else:
            default = v if allow else None
        interfaceDefaults[k] = default
        allowed[k] = allow
    checker = Check(app, True)
    checker.checkGroup(cfg, interfaceDefaults, dKey, extra=allowed)
    checker.report()
    specs[dKey] = interfaceDefaults
    specs["fmt"] = specs["textFormat"]

    app.context.update(specs)
    app.showContext = types.MethodType(showContext, app)


def getDataDefaults(app, cfg, dKey, withApi):
    checker = Check(app, withApi)

    if withApi:
        api = app.api
        F = api.F
        T = api.T
        sectionTypes = T.sectionTypes

    specs = app.specs

    givenInfo = cfg.get(dKey, {})

    if withApi:
        formatStyle = {f[0]: f[1] for f in FORMAT_CLS}
        formatStyle[ORIG] = specs["defaultClsOrig"]
        specs["formatStyle"] = formatStyle

    legalKeys = {d[0] for d in DATA_DISPLAY_DEFAULTS}
    checker.checkGroup(cfg, legalKeys, dKey)
    checker.report()

    for attr, default, needsApi in DATA_DISPLAY_DEFAULTS:
        if needsApi and not withApi or not needsApi and withApi:
            continue

        if attr == "browseNavLevel":
            default = len(sectionTypes) - 1 if sectionTypes else 1

        value = givenInfo.get(attr, specs.get(attr, default))
        if attr in specs and attr not in givenInfo:
            continue
        elif attr == "exampleSection":
            if not value:
                if sectionTypes:
                    verseType = sectionTypes[-1]
                    firstVerse = F.otype.s(verseType)[0]
                    value = app.sectionStrFromNode(firstVerse)
                else:
                    value = "passage"
            specs["exampleSection"] = value
            specs["exampleSectionHtml"] = f"<code>{value}</code>"
        if attr == "textFormats":
            methods = {fmt: v[METHOD] for (fmt, v) in value.items() if METHOD in v}
            styles = {fmt: v.get(STYLE, None) for (fmt, v) in value.items()}
            specs["formatMethod"] = methods
            specs["formatHtml"] = {T.splitFormat(fmt)[1] for fmt in methods}
            compileFormatCls(app, specs, styles)

        else:
            specs[attr] = value


def getTypeDefaults(app, cfg, dKey, withApi):
    if not withApi:
        return

    checker = Check(app, withApi)
    givenInfo = cfg.get(dKey, {})

    customMethods = app.customMethods

    api = app.api
    F = api.F
    T = api.T
    N = api.N
    Eall = api.Eall
    otypeRank = N.otypeRank
    slotType = F.otype.slotType
    nTypes = F.otype.all
    structureTypes = T.structureTypes
    structureTypeSet = T.structureTypeSet
    sectionTypes = T.sectionTypes
    sectionTypeSet = T.sectionTypeSet

    sectionalTypeSet = sectionTypeSet | structureTypeSet

    specs = app.specs

    featuresBare = {}
    features = {}
    lineNumberFeature = {}
    hasGraphics = set()
    verseTypes = {sectionTypes[-1]} if sectionTypes else set()
    bigTypes = set()
    verseRank = otypeRank[sectionTypes[-1]] if sectionTypes else None
    lexMap = {}
    baseTypes = set()
    edgeFeatures = set()
    hiddenTypes = set()
    condenseType = None
    templates = {}
    labels = {}
    styles = {}
    givenLevels = {}
    levels = {}
    children = {}
    childType = {}
    exclusions = {}
    transform = {}

    customMethods.set("transform", transform)
    formatStyle = specs["formatStyle"]

    for nType in nTypes:
        template = (
            True if nType == slotType or nType in sectionalTypeSet - verseTypes else ""
        )
        for dest in (templates, labels):
            dest[nType] = (template, ())

    unknownTypes = {nType for nType in givenInfo if nType not in nTypes}
    if unknownTypes:
        unknownTypesRep = ",".join(sorted(unknownTypes))
        console(f"App config error(s) in typeDisplay: {unknownTypesRep}", error=True)

    for nType, info in givenInfo.items():
        checker.checkGroup(
            givenInfo,
            TYPE_KEYS,
            nType,
            postpone={
                "base",
                "label",
                "template",
                "features",
                "featuresBare",
                "transform",
            },
        )
        checker.report()

        if info.get("verselike", False):
            verseTypes.add(nType)

        lOcc = info.get("lexOcc", None)
        if lOcc is not None:
            lexMap[lOcc] = nType

        if "base" in info:
            base = info["base"]
            checker.checkSetting("base", base)
            baseTypes.add(nType)

        if "condense" in info:
            condense = info["condense"]
            checker.checkSetting("condense", condense)
            if condense:
                condenseType = nType

        trans = info.get("transform", None)
        if trans is not None:
            resolvedTrans = {}
            for feat, func in trans.items():
                methodName = f"transform_{func}"
                resolvedTrans[feat] = getattr(app, methodName, methodName)
            v = resolvedTrans
            checker.checkSetting("transform", trans, extra=v)
            transform[nType] = v

        for k, dest in (("template", templates), ("label", labels)):
            if k in info:
                template = info[k]
                templateFeatures = (
                    VAR_PATTERN.findall(template) if type(template) is str else ()
                )
                dest[nType] = (template, templateFeatures)
                checker.checkSetting(
                    k,
                    template,
                    extra=(template, templateFeatures),
                )

        if "style" in info:
            style = info["style"]
            styles[nType] = formatStyle.get(style, style)

        for k in ("featuresBare", "features"):
            v = info.get(k, "")
            parsedV = parseFeatures(v)
            checker.checkSetting(k, v, extra=parsedV)
            if k == "features":
                features[nType] = parsedV
            else:
                featuresBare[nType] = parsedV

        lineNumber = info.get("lineNumber", None)
        if lineNumber is not None:
            lineNumberFeature[nType] = lineNumber

        graphics = info.get("graphics", False)
        if graphics:
            hasGraphics.add(nType)

        hidden = info.get("hidden", None)
        if hidden:
            hiddenTypes.add(nType)

        verselike = info.get("verselike", False)
        if verselike:
            verseTypes.add(nType)

        if "children" in info:
            childs = info["children"] or ()
            if type(childs) is str:
                childs = {childs}
            else:
                childs = set(childs)
            children[nType] = set(childs or ())

        isBig = info.get("isBig", False)
        if isBig:
            bigTypes.add(nType)

        if "level" in info or "flow" in info or "wrap" in info or "stretch" in info:
            givenLevels[nType] = {
                k: v for (k, v) in info.items() if k in LEVEL_DEFAULTS
            }

        if "exclude" in info:
            exclusions[nType] = info["exclude"] or {}

        checker.report()

    lexTypes = set(lexMap.values())
    nTypesNoLex = [n for n in nTypes if n not in lexTypes]

    specs["allowedValues"] = dict(
        baseTypes=tuple(e for e in nTypesNoLex if e not in sectionTypeSet),
        condenseType=tuple(nTypesNoLex[0:-1]),
        hiddenTypes=tuple(e for e in nTypesNoLex[0:-1] if e not in sectionTypeSet),
        edgeFeatures=tuple(e for e in Eall(warp=False) if not e.startswith(OMAP)),
    )

    levelTypes = [set(), set(), set(), set(), set()]
    levelTypes[4] = sectionalTypeSet - verseTypes
    levelTypes[3] = verseTypes
    levelTypes[0] = {slotType} | lexTypes

    remainingTypeSet = set(nTypes) - levelTypes[4] - levelTypes[3] - levelTypes[0]
    remainingTypes = tuple(x for x in nTypes if x in remainingTypeSet)
    nRemaining = len(remainingTypes)

    if nRemaining == 0:
        midType = slotType
    elif nRemaining == 1:
        midType = remainingTypes[0]
        levelTypes[1] = {midType}
    else:
        mid = len(remainingTypes) // 2
        midType = remainingTypes[mid]
        levelTypes[2] = set(remainingTypes[0:mid])
        levelTypes[1] = set(remainingTypes[mid:])

    childType = {
        nType: {nTypesNoLex[i + 1]}
        for (i, nType) in enumerate(nTypesNoLex)
        if i < len(nTypesNoLex) - 1
        # if nType in levelTypes[2] | levelTypes[1]
    }
    mergeDictOfSets(
        childType,
        {
            nType: {structureTypes[i + 1]}
            for (i, nType) in enumerate(structureTypes)
            if i < len(structureTypes) - 1
        },
    )
    mergeDictOfSets(
        childType,
        {
            nType: {sectionTypes[i + 1]}
            for (i, nType) in enumerate(sectionTypes)
            if i < len(sectionTypes) - 1
        },
    )

    # here we override from the chlidren information in the app-config

    for nType, childInfo in children.items():
        childType[nType] = childInfo

    lowestSectionalTypes = set() | verseTypes
    if sectionTypes:
        lowestSectionalTypes.add(sectionTypes[-1])
    if structureTypes:
        lowestSectionalTypes.add(structureTypes[-1])

    biggestOtherType = slotType
    for rt in remainingTypes:
        if verseRank is None or otypeRank[rt] < verseRank:
            biggestOtherType = rt
            break
    smallestOtherType = remainingTypes[-1] if remainingTypes else None

    for lexType in lexTypes:
        if lexType in childType:
            del childType[lexType]

    for lowestSectionalType in lowestSectionalTypes:
        if lowestSectionalType not in childType:
            childType[lowestSectionalType] = {biggestOtherType}
        else:
            childType[lowestSectionalType].add(biggestOtherType)

    if smallestOtherType is not None and smallestOtherType != slotType:
        if smallestOtherType not in childType:
            childType[smallestOtherType] = {slotType}
        else:
            childType[smallestOtherType].add(slotType)

    if condenseType is None:
        condenseType = sectionTypes[-1] if sectionTypes else midType

    for i, nTypes in enumerate(levelTypes):
        for nType in nTypes:
            levels[nType] = getLevel(i, givenLevels.get(nType, {}), nType in verseTypes)

    levelCls = {}

    for nType, nTypeInfo in levels.items():
        level = nTypeInfo["level"]
        flow = nTypeInfo["flow"]
        wrap = nTypeInfo["wrap"]

        containerCls = f"contnr c{level}"
        labelCls = f"lbl c{level}"
        childrenCls = (
            f"children {flow} {'wrap' if wrap else ''}"
            if childType.get(nType, None)
            else ""
        )

        levelCls[nType] = dict(
            container=containerCls,
            label=labelCls,
            children=childrenCls,
        )

    descendantType = transitiveClosure(childType, {slotType})

    specs.update(
        baseTypes=baseTypes if baseTypes else {slotType},
        bigTypes=bigTypes,
        childType=childType,
        condenseType=condenseType,
        descendantType=descendantType,
        exclusions=exclusions,
        features=features,
        featuresBare=featuresBare,
        hasGraphics=hasGraphics,
        edgeFeatures=edgeFeatures,
        hiddenTypes=hiddenTypes,
        labels=labels,
        levels=levels,
        levelCls=levelCls,
        lexMap=lexMap,
        lexTypes=lexTypes,
        lineNumberFeature=lineNumberFeature,
        noDescendTypes=lexTypes,
        styles=styles,
        templates=templates,
        verseTypes=verseTypes,
    )


def showContext(app, *keys, withComputed=True, asHtml=False):
    """Shows the *context* of the app `tf.advanced.app.App.context` in a pretty way.

    The context is the result of computing sensible defaults for the corpus
    combined with configuration settings in the app's `config.yaml`.

    Parameters
    ----------
    keys: iterable of string
        For each key passed to this function, the information for that key
        will be displayed. If no keys are passed, all keys will be displayed.
    withComputed: boolean, optional False
        If True, presents also the computed list of application settings.
    asHtml: boolean, optional False
        If True, return the resulting HTML rather than displaying it.

    Returns
    -------
    displayed HTML
        An expandable list of the key-value pair for the requested keys.

    See Also
    --------
    tf.advanced.app.App.reuse
    tf.advanced.settings: options allowed in `config.yaml`
    """

    inNb = app.inNb

    result = []

    for kind, data in (
        ("specified", app.cfgSpecs),
        ("computed", app.specs),
    ):
        if kind == "computed" and not withComputed:
            continue
        result.append(showDict(f"<b>{kind}</b>", data, True, False))

    result = "\n".join(result)

    if asHtml:
        return result

    if inNb is not None:
        dh(result, inNb=inNb)
    else:
        console(result)


def getLevel(defaultLevel, givenInfo, isVerse):
    level = givenInfo.get("level", defaultLevel)
    defaultsFromLevel = LEVEL_DEFAULTS["level"][level]
    flow = givenInfo.get("flow", "hor" if isVerse else defaultsFromLevel["flow"])
    defaultsFromFlow = LEVEL_DEFAULTS["flow"][flow]
    wrap = givenInfo.get("wrap", defaultsFromFlow["wrap"])
    stretch = givenInfo.get("stretch", defaultsFromFlow["stretch"])
    return dict(level=level, flow=flow, wrap=wrap, stretch=stretch)


def compileFormatCls(app, specs, givenStyles):
    api = app.api
    T = api.T

    result = {}
    extraFormats = set()

    formatStyle = specs["formatStyle"]
    defaultClsOrig = specs["defaultClsOrig"]

    for fmt in givenStyles:
        fmt = T.splitFormat(fmt)[1]
        extraFormats.add(fmt)

    for fmt in set(T.formats) | set(extraFormats):
        style = givenStyles.get(fmt, None)
        if style is None:
            textCls = None
            for key, cls in FORMAT_CLS:
                if (
                    f"-{key}-" in fmt
                    or fmt.startswith(f"{key}-")
                    or fmt.endswith(f"-{key}")
                ):
                    textCls = defaultClsOrig if key == ORIG else cls
            if textCls is None:
                textCls = DEFAULT_CLS
        else:
            textCls = defaultClsOrig if style == ORIG else formatStyle.get(style, style)
        result[fmt] = textCls

    specs["formatCls"] = result
