# App settings

Developers can create TF-apps by specifying a `config.yaml` with settings.
These settings will be read, checked, and transformed into configuration data
that is read by the app, see `tf.applib.settings.showContext`

See for examples:
* [bhsa](https://github.com/annotation/app-bhsa/blob/master/code/config.yaml).
* [uruk](https://github.com/annotation/app-uruk/blob/master/code/config.yaml).

# Config specs

Here is a specification of all settings you can configure for an app.

Each section below corresponds to a main key in the `config.yaml` of an app.

Everything is optional, an empty `config.yaml` is valid.
Text-Fabric tries hard to supply reasonable defaults on the basis of the corpus
data it has loaded.

## `apiVersion`

To let Text-Fabric check whether its version matches the version of the TF-app

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

The section level up to which the TF-browser shows a hierarchical tree.

Values
: `1` or `2`

Default:
:   *one less than the number of section types*

---

### `exampleSection`

Placeholder text for passage entry fields in the TF browser.
"book" is the node type of top level sections.

Default:
:   string `book 1`

---

### `exampleSectionHtml`

Formatted placeholder text for passage entry fields in the TF browser.
"book" is the node type of top level sections.

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

Show the full text of verselike nodes in tables and tuples
(in `tf.applib.display.plainTuple` and `tf.applib.display.table`)

Default:
:   boolean `false`

---

### `textFormats`

```
textFormats:
    layout-orig-full: layoutRich
```

Additional text formats that can use HTML styling.

Keys
:   names of existing and new text formats.

Values
:   (methd, style)

where

method
:   name of a method that implements that format.
    If the name is `xxx`, or n`typexxx`
    then `app.py` should implement a method `fmt_xxx(node, **kwargs)`
    to produce html for node `node`. 
    This function will passed the `outer=True` if called by a plain or pretty at
    the outer level, level=recursion depth, and `first=True, last=True`
    if the node is on a leftmost resp.
    rightmost branch in the tree of children below the outer node.
style
:   a keyword indicating in what style the format should be set:
    normal, source, trans, phono, orig.

Default:
:   dict `{}`

---

## `docs`

In the settings below you may refer to provenance settings, like `{org}` and `{repo}`
You may refer to nbviewer with `{urlNb}` and to github with `{urlGh}`

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

Default:
:   string `{tfDoc}/writing/transcription/`

---

### `docBase`

Base url page for the corpus documentation

Default:
:   string `{docRoot}/{org}/{repo}/blob/master/docs`

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

Where the docs are: on Github (default), or on nbviewer (`{urlNb}`) or somewhere else.

Default:
:   string `{urlGh}`

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
`tf.applib.display.plain` and `tf.applib.display.pretty`.
They can also be set in the Text-Fabric Browser.
The values set here are the defaults as given by this app.
Not all options are relevant for all corpora.
Only relevant options should be included.
By setting the default to `None`, the option will not be shown
on the TF-browser interface.

These options are described in `tf.applib.displaysettings`: all options
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

If your data is archived: the doi of the archived version, like
`xx.yyyy/archive.zzzzzzz` without the `https://doi.org/` in front.

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

```
moduleSpecs = (
  dict(
      org="researcher1",
      repo="work1",
      relative="tf",
      corpus="speicalism1",
      docUrl=(
          "{urlNb}/researcher1/work1/blob/master/programs/specialism1.ipynb"
      ),
      doi="xx.yyyy/archive.zzzzzzz",
  ),
  dict(
      org="researcher2",
      repo="work2",
      relative="tf",
      corpus="speicalism2",
      docUrl=(
          "{urlNb}/researcher2/work2/blob/master/programs/specialism2.ipynb"
      ),
      doi="uu.vvvv/archive.wwwwwww",
  ),
)
```

If modules have the same org or repo as the main data, these do not have to
be specified.
If a module has a relative attribute equal to `tf`, it can be left out.

Default:
:   list `[]`

---

### `org`

The GitHub organisation name under which your TF data resides.

Default:
:   string `annotation`

---

### `relative`

The path inside the repo to the directory
that holds the version directories of the tf data.

Default:
:   string `tf`

---

### `repo`

The GitHub repo name under which your TF data resides

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

### `webBase`

If present, the base url for an online edition of the corpus.

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

### `webUrl`

If present, `webLink(node)` will use this as a template to generate a url
to an online edition of the node.

The following place holders will be honoured:

*   `{webBase}`: the webBase above
*   `<1>` : value for section heading 1
*   `<2>` : value for section heading 2
*   `<3>` : value for section heading 3
*   `{version}`: version of the TF resource

Default:
:   string `null`

---

### `webUrlLex`

If present, `webLink(node)` will use this as a template to generate a url
to an online edition of the lexeme node.

The following place holders will be honoured:
*   `{webBase}`: the `webBase` value above
*   `<lid>` : value for the id of the lexeme
*   `{version}` version of the TF resource

Default:
:   string `null`

---

### `zip`

Only used by `text-fabric-zip` when collecting data into zip files
as attachments to a GitHub release.

If left to `null`, will be configured to use the main repo and the modules.

You can also use this scheme to include other data from the repository.
Note that graphics data will be packaged automatically.

You can specify the main repo, modules, and related data:

*   `zip=["repo"]`: Only the main module.

*   `zip=["repo", "mod1", "mod2"]` : if org and relative for the modules
    are the same as for are the main repo)

Default:
:   list `["repo"] + [("org1", "mod1", "relative1"), ("org2", "mod2", "relative2")]`

    where all modules mentioned in the moduleSpecs will be filled in.

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

plain display
:   if the node needs to be highlighted, it gets a coloured background.
    Nodes of other types receive their highlights as coloured borders
    around their boxes.
pretty
:   children of these nodes are not expanded further, but displayed in
    plain mode (with highlighting).

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

### `children`

Which type of child nodes to be included in the display.
The value should be a node type or a set of node types:

```
children: subphrase
```

```
children:
  - subphrase
  - word
```

### `exclude`

Conditions that will exclude nodes of this type from the display.

All nodes that satisfy at least one of these conditions will be left out.

!!! hint
    Use this if you want to exclude particular nodes of some type, e.g. in
    [dss](https://github.com/annotation/app-dss/blob/master/code/config.yaml).
    where we want to prevent line terminator signs.

The value is a dictionary of feature name - value pairs.

```
exclude:
    type: term
```

Default:
:   dict, `{}`

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
:   boolean `true`

---

### `features`

Pretty displays: which node features to display as `name=value`.

You can also specify lookup feature values for upper nodes, e.g. `{lex:gloss}`
which will look for a `lex` node above the current node and retrieve its `gloss` value.

Default:
:   list of string `''`

---

### `featuresBare: feat1 feat2`

Pretty displays: which features to display by value only
(the feature name is not mentioned).

Things like `{lex:gloss}` are allowed.

Default:
:   list of string `''`

---

### `flow:`

Pretty: whether the container should arrange its subdisplays as a column or as a row.

Values: `hor`, `ver`

Default:
:   string

    *   `ver` if level is 3 (typically section types), except for the verselike types
    *   `ver` if level is 0 (typically slot types and lexeme types)
    *   `hor` if level is 1 or 2 (typically linguistic types at sentence level) and
        for the verselike types

---

### `graphics`

If `true`, then there is additional graphics available for nodes of this
type.

The app needs to define a function

```
getGraphics(isPretty, node, nodeType, isOuter) => HTML code for sourcing the graphics
```

See [uruk](https://github.com/annotation/app-uruk/blob/master/code/app.py).

Default
:   boolean `null`

---

### `level`

Pretty: the visual style of the container box of this node, values 0, 1, 2, 3.
The bigger the number, the heavier the borders of the boxes.

The default is:

*   3 for types known as section or structure types, including the verselike types
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
:   string *slotType*

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
    [uruk](https://github.com/annotation/app-uruk/blob/master/code/config.yaml)
    it is needed to deviate from the default.

---

### `hidden`

Plain and pretty: whether nodes of this type must be hidden by default.
See for example the bhsa, where the `atom` types are hidden.

Nodes that unravel to other nodes will exclude nodes of hidden types from
the unraveling, unless you pass the display option `showHidden=True`.

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

### `style`

Formatting key for plain and pretty displays.

The label or template may need a special style to format it with.
You pass specify:

`normal`
:   normal non-corpus text

`source`
:   source text of the corpus (before conversion)

`trans`
:   transcription of corpus text

`phono`
:   phonological/phonetic transcription of corpus text

`orig`
:   unicode corpus text

*anything else*
:   will be inserted as an extra css class.

Default
:   string `null`

---

### `transform`

Sometimes you do not want to display straight feature values, but transformed ones.
For each feature you can specfiy a transform function `f`:
E.g.

```
transform:
    type: ctype
```

The feature `type`, when computed for a node of the type we are configuring here,
will yield a value which is transformed by function `ctype` to a new value. 
In your app code you have to implement:

```
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

But more types can be declared as verselike, e.g. `halfverse` in the
[bhsa](https://github.com/annotation/app-bhsa/blob/master/code/config.yaml).

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
    [uruk](https://github.com/annotation/app-uruk/blob/master/code/config.yaml)
    it is needed to deviate from the default.

---

## `writing`

Code for triggering special fonts, e.g.

iso | language
--- | ---
`akk` | akkadian
`hbo` | hebrew
`syc` | syriac
`ara` | arabic
`grc` | greek
`cld` | neo aramaic

Default:
:   string `''`

---
