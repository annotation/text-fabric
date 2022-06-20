Newer releases: `tf.about.releases`

# Older releases

## 9

### 9.5

#### 9.5.2

2022-06-14

* Small fix in `tf.core.helpers.initTree`.
* New function `tf.advanced.text.showFormats`; call as `A.showFormats()`
  that gives a nicely formatted list of all text-formats and the templates
  by which they are defined.
* Small fix in text formats: when you specify a text-format with default values,
  the empty string is now also allowed as default value.

#### 9.5.1

2022-05-31

Bug discovered thanks to an observation of Oliver Glanz:

In search templates, a quantifier has to follow an atom line, like so

```
word gn=f
/without/
.. nu=pl
/-/
```

This looks for a word with female gender, without it being a word in the plural.

An alternative syntax with the same semantics is

```
word
  gn=f
/without/
.. nu=pl
/-/
```

However, the parser in Text-Fabric got distracted by the intervening `gn=f` and
did not connect the quantifier with the preceding `word`, which gave erroneous results.

That has been fixed, and now the second form leads to the same results as the first one.

#### 9.5.0

2022-05-18

New behaviour in walking nodes: `tf.core.nodes.Nodes.walk`: with `events=True`
it generates open/close events for nodes, so that you can do something
when the node starts and something else when the node ends.

New utility functions `tf.core.helpers.clearTree` and `tf.core.helpers.initTree`.

Various friction reducing changes:

*   functions with file or directory arguments always perform an expansion
    of a leading `~` to the user's home directory.

#### 9.4.4

2022-05-16

Several minor improvements in various parts of the app.

#### 9.4.2-3

2022-05-04

The `weblink` function can now also be driven by feature values. See `tf.advanced.settings`
and look in section `webFeature`.
Additional small fixes.

#### 9.4.1

2022-05-03

Fixed a bug introduced by the previous change which caused a failure in the export from the TF-browser.

#### 9.4.0

2022-04-29

*   Preprocessing took a bit too much time.
    The culprit was the computation of boundaries of nodes.
    It could be sped up by changing the data representation somewhat (going from `array` to `tuple`)
    in some cases.
    Since the new data representation is incompatible with the previous one, we bumped the internal
    version for that (`tf.parameters.PACK_VERSION`).
    That means that Text-Fabric will recompute your precomputed corpus data if needed.

*   If you inadvertently type a query in the text-fabric browser that takes for ever to 
    execute, it is difficult to get the tf-browser in a usable state again.
    We have chosen a remedy: we limit the search results to 4 * the maximum node in your corpus.
    This holds for all query execution, also when executed outside the text-fabric browser.

    When outside the text-fabric browser, you can pass the `limit` parameter to `A.search` or `S.search`
    to enforce a different and bigger limit.
    Setting it to `None` or 0 restores the default of 4 * maxNode.
    You cannot pass custom limits in the text-fabric browser.

### 9.4

#### 9.3.2

2022-03-21

Bug in Text-Fabric browser: corpora that show a pretty display for section items instead
of a list of subsection items (setting *browseContentPretty* in `tf.advanced.settings`)
did not respond to the display options, because in this particular case the options 
were not passed to the `tf.advanced.display.pretty()` function. That has been
remedied. The only corpus that makes use of this setting (that I know of) is the
[Nino-cunei/uruk](https://github.com/Nino-cunei/uruk) corpus.

#### 9.3.0-1

2022-02-10

The text-Fabric browser now displays hard-to-type characters, depending
on the text format chosen.
It is right below the query window.
From there you can click to copy characters and then paste them in the
query window.

#### 9.3

#### 9.2.5

2022-02-04

When precomputing section data, better error messages are generated
when section nodes do not have values for the features that are supposed
to contain their headings.

Removed a debug statement that I left previously.

#### 9.2.4

2022-02-02

Bug fix. When writing TF data to file, the function `_writeDataTf` in `tf.core.data.Data`
had a bug that caused misalignment if the feature data had explicit `None` values.
That has been fixed. Now it makes no difference anymore whether you save
feature data where node `n` has value `None`, or where node `n` is absent.

Thanks to Martijn Naaijer for spotting it.

#### 9.2.3

2022-01-31

Improvement in app loading: added an argument `legacy=True` to `use()`,
so that older versions of older apps still can be loaded.

#### 9.2.1-2

2022-01-24

The text-fabric browser did not start-up well.
That has been fixed.
Loading an app from an arbitrary location on the local machine has been fixed.

#### 9.2

2022-01-06

A big reorganization, so that all things related to a corpus can be stored in the
same neighbourhood.
Before this release we had the situation that

*   a corpus is resides in org/corpus
*   its tutorials resides in annotation/tutorials/corpus
*   its tf-app resides in annotation/app-corpus
*   its layered search interface is provided by annotation/app-corpus

In the new situation we have

*   a corpus is resides in org/corpus
*   its tutorials resides in org//corpus/tutorial
*   its tf-app resides in org/corpus/app
*   its layered search interface is provided by org/corpus-search

So, in order to make a full fledged TF corpus there is no longer any dependency
on the annotation organization.

Additional fixes: quite a bit, among which

*   When downloading zip files from releases, the Uruk images got
    the wrong paths. That has been fixed in zipData, used by
    the text-fabric-zip command.

#### 9.1.13

2022-01-02

Test release. Since 9.1.7 the text-fabric distribution has become bloated because
setuptools includes a lot more files by default.
I now distribute a wheel only, and took care that it has no more than the usual files
included.

#### 9.1.12

2021-12-24

*   New data is computed and stored for a corpus: for each text format a frequency
    list of the characters in the corpus when rendered in that text format:
    `tf.core.prepare.characters`
*   A new function `tf.advanced.text.specialCharacters` which provides
    a widget from which you can easily copy the special characters in the corpus.
    Call it as `A.specialCharacters(fmt=textformat)`.
*   In the `tf.convert.walker` module there is an extra *cv* method:
    `tf.convert.walker.CV.activeNodes`.
*   Fix a bug that prevented the text-fabric browser to start up in some cases.

#### 9.1.11

2021-12-16

Loading of features somehow became painfully slow.
There binary representations of feature data are pickled Python datastructure.
I now optimize the pickled strings before writing them to disk.
Then they load much faster afterwards.

In order to feel the effects: perform a `tf.core.fabric.FabricCore.clearCache()`,
which will wipe out all previously generated binary feature data, so that the next time
the binary features will be created afresh.

Further improvements:

*   `omap@v-w` features will not be loaded by default by `tf.app.use()` calls.
    If needed, they can be loaded afterwards
    by `A.load("omap@v-w")` call
*   When these mappings are needed by modules of TF, the module will have ensured
    they are loaded.


#### 9.1.10

2021-12-15

Improved `tf.dataset.nodemaps.Versions.migrateFeatures`.
When migrating features from one data version to another along
a node mapping between the two versions, the quality of the links
between old nodes and new nodes is taken into account.
We migrate feature values only through the best links available.

#### 9.1.9

2021-12-13

*   Made sure that path names of files and directories, when retrieved by means of
    os.path.expanduser or os.path.abspath use forward slashes rather than backward slashes.
    These two functions might introduces path with backslashes when on Windows.
    The rest of TF works with forward slashes exclusively.
    We want prevent paths with mixed forward slashes and backslashes.
*   The `mod` parameter in A.use() accepts not only comma separated strings of 
    data modules, but also iterables of such modules.
*   If you want to override the checkout specifiers of standard modules (e.g.
    the `etcbc/parallels/tf` or `etcbc/phono/tf` modules of the `bhsa`,
    you can now override them by passing these modules in the `mod` parameter.


#### 9.1.8

2021-12-10

Fixed missing expander triangles in the feature overview after the incantation.
This happened in the classical notebook, not in jupyter lab.
The classical notebook styles the summary element in such a way as
to rob it from the triangle.
A simple overriding CSS instruction was enough.

Thanks to Oliver Glanz for spotting it.

#### 9.1.7

2021-12-09

More information on the metadata of features on the interface.

*   After `use("xxx")` you get an expandable list of features.
    Formerly, a feature was represented by its name, hyperlinked to the feature documentation.
    Now you see also the data type of the feature, its description, and you can expand
    further to see all metadata of a feature.
*   TF.isLoaded and A.isLoaded (`tf.core.api.Api.isLoaded`) can show/hide more information,
    such as the file path to a feature, its data type, its description, and all of its
    metadata.
*   importMQL (`tf.core.fabric.FabricCore.importMQL`) accepts a parameter `meta` which
    one can use to specify metadata that is common to all features.
    Now you can use it to pass feature-specific metadata as well.
*   Several datasources have been converted by means of importMQL:
    bhsa, extrabiblical and calap.
    Of these, I have updated the BHSA to have richer metadata in their features
    (only version 2021) including the standard modules phono, parallels, trees.
    And while I was at it, also did the non-standard modules valence and bridging.

#### 9.1.6

2021-11-17

Bug in search, spotted by Oliver Glanz, with thanks to him for reporting it.
Queries with `.f<g.` constructs in it (numeric feature comparison)
delivered wrong results.
The root cause waas clear: I declared the converse of `.f<g.` to be `.g>f.`.
But this is not the converse, the two are identical.
The converse is `.f>g.`.
See [code](https://github.com/annotation/text-fabric/blob/947aa5071d545ed5c875fe24eeb7329d4a8e9893/tf/search/relations.py#L1450-L1457)

#### 9.1.5

2021-11-17

Added an extra method `A.load()` by which you can load extra features
after loading the main dataset.

#### 9.1.4

2021-11-14

* Small fix in the `tf.volumes.collect.collect` function.
* Small fix in search when run from the TF browser.
  Features that are mentioned in feature comparison relations
  were not shown in the search results. Now they do.

#### 9.1.2,3

2021-11-03

In TF-apps, in the config.yaml where you specify an online location based on
section headings, you can configure the app to put leading zeroes before 
section headings.
See [webUrlZeros](https://annotation.github.io/text-fabric/tf/advanced/settings.html#weburlzeros).
Small fixes in the handling of these configuration settings.

#### 9.1.1

2021-10-25

**Layered search**

The layered search app hints in which browsers multiple highlighting is supported.
It now works in Safari 15.0 on the Mac.
It also works in browsers on iOs and iPadOs.
The hints have been updated.

#### 9.1

2021-09-10

**Additions to the API**

The display functions are

* `tf.advanced.display.table`
* `tf.advanced.display.plainTuple`
* `tf.advanced.display.plain`
* `tf.advanced.display.show`
* `tf.advanced.display.prettyTuple`
* `tf.advanced.display.pretty`

Some of them are defined with the parameter `asString=False`.
When omitted or False, the result will be displayed in the notebook.
But when used by the TF-browser, the result will not be displayed, but returned
as HTML. Text-Fabric knows when it is used by the TF browser or not.

But there are cases when you want to tell Text-Fabric to not display the result,
but to deliver it as HTML. For that the `_asString` parameter was used.
However, it was not defined for all of these display functions.

The improvement is, that it now works for *all* of the above display functions.

When you pass `asString=True`, the result will not be displayed (in the notebook),
but returned as HTML.

#### 9.0.4

2021-08-26

**Fixes**

* Section headings in the BHSA were not always rendered in ltr mode. Fixed.

#### 9.0.2, 9.0.3

2021-08-24

**Fixes**

* Bug reported by Gyusang Jin: when a string specification of features that must be loaded
  contains newlines, an error will occur.
* TF.loadLog() did not provide useful information anymore. Instead, there is now
  TF.isLoaded and A.isLoaded (`tf.core.api.Api.isLoaded`). For compatibility,
  loadLog still can be called, but is identical to isLoaded.

#### 9.0.1

2021-08-23

**Fixes**

* Bug reported by Jaime Toledo (https://github.com/annotation/text-fabric/issues/73)
* Bug reported by Christian Jensen (https://github.com/annotation/text-fabric/issues/74)

Thanks for reporting!

#### 9.0.0

2021-07-29

**Additions**

*Volume support*: see `tf.about.volumes`.
This allows for partially loading a TF-dataset.
It is the start of making Text-Fabric more agile.
By being able to load portions of a work, and still not loose the connection
with the whole work, it has potential for large corpora that do nit fit into RAM.

However, as it stands now, in order to make portions of a work, the whole work will
be loaded. When the portions are made, they can be loaded without loading the whole
work.

Later in the development of version 9 I hope to be able to synthesize whole works
out of portions without the need of having the whole work in RAM.

*   `tf.advanced.volumes.volumesApi`
*   `tf.volumes.extract`
*   `tf.fabric.Fabric.extract`
*   `tf.advanced.volumes.extract`
*   `tf.volumes.collect`
*   `tf.fabric.Fabric.collect`
*   `tf.advanced.volumes.collect`
*   `tf.fabric.Fabric` now takes optional `volume=` and `collection=` parameters
*   `tf.app.use` now takes optional `volume=` and `collection=` parameters
*   `tf.advanced.app.App` now takes optional `volume=` and `collection=` parameters
*   `tf.core.api.Api.isLoaded`. A convenient way to get information about loaded features.

**Changes**

*   "tf.compose.modify" has moved to `tf.dataset.modify`
*   "tf.compose.combine" has been replaced by `tf.volumes.collect`
*   "tf.compose.nodemaps" has moved to `tf.dataset.nodemaps`
*   "tf.compose.Versions" has moved to `tf.dataset.nodemaps.Versions`

### 9.0

---

## 8

### 8.5

#### 8.5.14

2021-07-06

Small fix in the search client: the totals of nodes where displayed as undefined
for node types for which no layers have been defined.

#### 8.5.13

2021-06-28

No changes except that the version requirement for Python is back to 3.6.3.

#### 8.5.7,8,9,10,11,12

2021-06-14

Small fixes in the distribution of tf.client.make

#### 8.5.6

2021-06-09

*   Updates in `tf.advanced.repo`: a function `releaseData` that releases
    a version of TF data of a corpus to GitHub.
    The release number gets bumped, the data is zipped and attached to the release.
    This helps to write pipeline scripts that transfer corpus updates to the TF
    eco-system.

#### 8.5.5

2021-06-08


*   Updates in the `tf.client`: more ways of building the layeredsearch client.
    Driven by the NENA pipeline.

#### 8.5.4

2021-05-20

*   Updates in the `tf.convert.recorder`: a new method to export positions using
    much less data, provided certain assumptions hold.
*   Updates in the `tf.client`: a more memory-friendly way to store
    the corpus data, especially the positions data.
    The method can be switched on and off, depending whether the corpus
    satisfies the preliminaries for this space optimization.

#### 8.5.3

2021-05-11

Updates in the layered search app and its distribution.
The Recorder API has some additions `tf.convert.recorder`

#### 8.5.2

2021-05-06

Updates in the layered search app and its distribution.

#### 8.5.1

2021-05-04

Small fixes in the the layered search app and its documentation.

#### 8.5.0

2021-05-03

There is a new piece of functionality in Text-Fabric: making search interfaces for existing TF-apps.
These are static HTML+CSS+Javascript pages, that provide *layered search*.
Text-Fabric has a new command `text-fabric-make dataset interfacename` which generates such an app
from a bit of configuration and code, which you have to provide in the `app-`*dataset* repo.

See `tf.client`.

### 8.4

#### 8.4.14

2021-04-20

A minor addition: you can now get the CSS of an app and re-use it in notebooks without
loading the whole API.
See `advanced.display.getCss`.

#### 8.4.13

2021-03-22

A few minor improvements:

* the `tf.convert.recorder` is improved. It can now save postion files per node type.
* the `tf.core.timestamp.Timestamp.indent` method now accepts a boolean for its `level` parameter.
  By this you can increase and decrease the current indentation level of messages.

#### 8.4.12

2021-02-11

Fix in `tf.convert.recorder.Recorder.read`:
this method wrote to the positions file, rather than reading from it.
Thanks to Sophie Arnoult for spotting it.

#### 8.4.11

2021-02-03

Enhancement: the TF-browser can now export the contents of the node pad, decorated
with location information and text content. Previously, you only got a
bare list of nodes in `nodes.tsv`. Now you also get a `nodesx.tsv`, 
analogously to `resultsx.tsv`. See `tf.about.browser`.
However, such a list of node tuples may not be as uniform as a list of query results.
Non-uniform lists lead to a messy output table, but still usable.

Thanks to Jorik Groen for asking for this.

This also affects the `A.export()` function (`tf.advanced.display.export`),
which was only able to export uniform lists.
Now it can also export non-uniform lists.

#### 8.4.10

2021-02-01

Bug fix: when loading an additional feature into an existing TF API,
the feature did not get properly reloaded if it had already been loaded
and the feature data had changed.

#### 8.4.9

2021-02-01

Updated links to the documentation.
The documentation has now a working search interface.

#### 8.4.8

2021-01-30

Added logic to map nodes between versions of TF datasets.
This logic existed in a notebook that explores versions of the Hebrew Bible:
[versionMappings](https://nbviewer.jupyter.org/github/ETCBC/bhsa/blob/master/programs/versionMappings.ipynb).
Whereas the code to map slots between versions is highly dependent on the dataset in question,
the code to extend a slot mapping to a node mapping is generic.
That code is now in "tf.compose.nodemaps" (as of version 9 in `tf.dataset.nodemaps`).
It is used in the 
[missieven](https://nbviewer.jupyter.org/github/clariah/wp6-missieven/blob/master/programs/map.ipynb)
corpus.

#### 8.4.7

2021-01-20

Renamed some CSS classes in the display style sheet of Text-Fabric.
These names interfered with class names used in Jupyter Book.

Added several transcriptions for Arabic characters.
See `tf.writing.arabic`.

#### 8.4.6

2020-12-30

Small fixes in the functions that load a TF app: you could already
directly load the data of an app-less corpus from disk, now you can do the
same if such data resides on GitHub.

Various other things had to be tweaked a little.

#### 8.4.5

2020-10-29

Small fix of a problem introduced by the previous enhancement.

#### 8.4.4

2020-10-15

Enhancement in web links to nodes:
there is a new setting `webOffset` in the configuration of a TF app that let you specify
an offset between a logical page number and a physical page number.
See the webOffset setting of `tf.advanced.settings`.
It is needed by the new
[missieven corpus](https://github.com/clariah/wp6-missieven/blob/master/app/config.yaml).

#### 8.4.3

2020-09-25

Minor fix in the display:

* **Left-to-right transcriptions in right-to-left corpora still had rtl tendencies**
  Fixed by using the CSS mechanism `unicode-bidi: embed` more consistently.

#### 8.4.2

2020-09-20

Minor fixes in the display:

* **The Text-Fabric browser showed the chunks around a gap in the wrong order for right to left scripts.**
  Fixed by using CSS mechanisms such as `display: inline-block` and `unicode-bidi: embed`.
* **Chrome did not display dotted borders good enough: in some circumstances the dots were hardly visible**.
  Sadly one of those circumstances is the default zoom level of the browser: if the user enlarges or decreases the
  zoom level, the dots become better visible.
  It seems that using the `rem` unit for specifying border-sizes contributes to this behaviour.
  So I specified all border widths in `px`, assuming 20px = 1rem.

#### 8.4.1

2020-09-08

Better error message if a standard module of a data set cannot be found.
E.g. the parallels modules for the BHSA, DSS.

Addition in `tf.convert.walker`, in the `cv.node()` function to add nodes:
it accepts an additional optional parameter to link an explicit set of
slots to a node.

#### 8.4.0

2020-07-09

Added the `tf.convert.tf.explode` function, by which you can *explode* feature files
into TF files without optimizations. 

### 8.3

#### 8.3.5

2020-06-29

Fixed an error when opening the Uruk corpus in the Text-Fabric browser.

#### 8.3.4

2020-06-26

Various small fixes:

*   Fix in result display in TF browser: the members of a result
    form a row again instead of a column.
*   Better error message in some cases in `tf.convert.walker`.
*   Moved documentation of the walker functions into the docstrings of those functions.

#### 8.3.3

Small fix by Cody Kingham: when calling `use(api=...)` with an TF api constructed
before, the `TF` attribute of this api is not transported to the app object.

2020-06-13

#### 8.3.1, 8.3.2

2020-06-11

Gentium Plus font installed.
Greek Character table added.
Small fixes, one blocking for the Text-Fabric browser.

#### 8.3.0

2020-06-10

#### Backward incompatibility

!!! caution "corpus apps"
    The API between TF and its apps has changed.
    If you upgrade TF to this version, you also have to upgrade the
    TF apps you work with.
    You can do that by adding the checkout specifier `latest` when
    you call the corpus, e.g. for the BHSA (one time is enough):

```python
A = use("bhsa:latest", hoist=globals()")
```

Text-Fabric is now better in detecting if you load an incompatible app and will give
you a useful hint.

The post-incantation messages of TF are now better formatted and more modest.
Most information is collapsed and expandible by a triangle.

Under the hood improvement of the display algorithm.
Both `plain` and `pretty` rely on the same *unravel* algorithm
that turns a graph fragment into a tree for display.

See `tf.advanced.unravel`.

The unravel function is also exposed as `A.unravel(node)`,
see `tf.advanced.unravel.unravel`.

Now you can define your own rendering function, taking the unraveled tree as input.

#### New display settings

See `tf.advanced.options`.

*   `plainGaps`: normally, gaps are shown in plain displays.
    But the control is yours, with `plainGaps=False` gaps are suppressed.
*   `hiddenTypes`: you can prevent node types from adding to the structure of the
    display, which might become very cluttered. E.g. the atom types of the
    BHSA, and also the subphrases and half verses.
    Before, it was a binary choice: the app determines which node types are hidden
    by default, and the user can switch them all on or all off.

    Now the app still determines the default, but the user can hide/unhide all
    combinations of node types.

#### TF browser

Various fixes:

*   Starting in v8, the ports through which the TF-browser communicates are no longer
    hardwired in the app config, but are determined at run time: the first
    available ports are choses.
    This had the negative consequence that different corpora could use the same port in turn,
    thereby wreaking havoc with the sessions for those corpora.
    Now the ports are determined as a function of the arguments to `text-fabric`.
*   Text alignment and line wrapping has improved, especially in plain displays.


### 8.2

#### 8.2.2

2020-06-02

When you load a corpus by means of `use`, you can now also override the config settings of the
app on the fly. See `tf.advanced.app.App`

#### 8.2.1

2020-05-30

Fixed two silly bugs, one of which a show stopper, preventing precomputation after
download of data to complete.

#### 8.2.0

2020-05-29

Improved display algorithm: corpora need less configuration for TF
to generate good displays.
In particular, the atom types of the BHSA are now handled without
tricky branches in the code.

See `tf.advanced.display`.

Core API: a bit of streamlining:
all exposed methods now fall under one of `A TF N F E L T S`.

!!! hint "new"
    If you want to talk to yourself in markdown or HTML you can use
    `A.dm(markdownString)` and `A.dh(htmlString)`.

    See `tf.advanced.helpers.dm` and `tf.advanced.helpers.dh`.

#### Backward incompatibility

!!! caution "corpus apps"
    The API between TF and its apps has changed.
    If you upgrade TF to this version, you also have to upgrade the
    TF apps you work with.
    You can do that by adding the checkout specifier `latest` when
    you call the corpus, e.g. for the BHSA (one time is enough):

```python
A = use("bhsa:latest", hoist=globals()")
```


!!! caution "logging functions"
    The methods `info` `error` `warning` are no longer hoisted to the
    global name space.

    Use `A.info` or `TF.info` for these methods.

!!! caution "node functions"
    `N()` has become: `N.walk()`

    `sortNodes`, `sortKey`, `sortkeyTuple`, `sortkeyChunk`
    and `otypeRank` are no longer hoisted to the global name space.

    Use `N.sortNodes` etc. instead for all these methods.

!!! hint "fix the compatibility relatively easily"
    If you use the functions in question a lot in a program or notebook,
    define them right after the incantation as follows:

``` python
A = use('xxx', hoist=globals())

info = A.info
error = A.error
silentOn = A.silentOn
...
sortNodes = N.sortNodes
...
```

etc.

### 8.1

#### 8.1.2

2020-05-22

Thoroughly reorganized docs.
All available documentation has now moved into docstrings.
The formatted docstrings form the online documentation as well.
See `tf`.

#### 8.1.0, 8.1.1

2020-05-14

* New method in the
  `L`-API (`tf.core.locality.Locality.i`): `L.i(node, otype=nodeTypes)`.
  It delivers the *intersectors* of a node, i.e. the nodes that share slots
  with the given `node`.
* Fixed a subtle bug in the `A.pretty()` which manifested itself in the Old Babylonian corpus.
  A line with clusters in it displayed the clusters twice if `baseTypes` has a non slot type.
  When doing a `plain` within a `pretty`,
  the displayer "forgot" the nodes encountered in `plain`, so they could not be skipped by the
  rest of `pretty`.
* More improvements in the display logic where things refuse to be hierarchical.
* To the display option `extraFeatures` you may also pass values like `type:feature`,
  see options (`tf.advanced.options`) under list of display parameters.


### 8.0

#### 8.0.3

2020-05-12

* `A.header()` was used by the TF-browser to produce a colofon.
  Now it can be used in a Jupyter Notebook to produce the overview of features used,
  normally displayed after the incantantation.
* There is a new `A.showProvenance()` that can be used to show detailed provenance of
  the corpus data and all its modules. When you exported from the TF-browser, this data was
  included (and still is), but now you can invoke it from a program as well (typically in
  a Jupter notebook)
* **Provenance** When exporting data from the TF-browser, a provenance sheet is generated
  with entries for the data modules. Now you can generate this sheet in a Jupyter notebook
  as well, by means of `A.showProvenance()`.
* Online data fetching/checking does not happen by default anymore if there is already
  local data. This reduces the number of GitHub API requests greatly, and users are less prone
  to hit the limit.

#### 8.0.2

2020-05-11

Small fix in `webLink()`.

#### 8.0.1

2020-05-10

Small fixes in order to accomodate NBviewer.

There were two problems

* the online nbviewer clipped many boxes in the display
  (cause: name conflict between CSS class names in Text-Fabric and in NBviewer)
* the lineheight in the classic Jupyter notebook is fixed on a value that is too low,
  in Jupyter lab it is ok. Fix: we add CSS code that unsets the line height that
  the classic notebook sets.

#### 8.0.0

2020-05-08

**NB: This is a backwards incompatible change. Strongly recommended:**

```sh
pip3 install --upgrade text-fabric
```

**All known TF-apps (the ones in under the `annotation` org on GitHub) have been
adapted to this change.**

**Text-Fabric auto-downloads the newest version of an app by default.
As a consequence, if you have not upgraded Text-Fabric, it will fail.**

*   The functionality offered by TF-apps is now called the *Advanced API*, as opposed to the
    *core API*. Everything under `A` is the advanced API. The things under `F`, `E`, `L`, `T`,
    etc. are the core API.
*   `A` will work also for TF datasets without an app. The advanced API will compute
    reasonable defaults based on what it finds in the TF data. It is still possible to
    write full-fledged TF apps that extend the capabilities of the advanced API.
*   Several special effects of individual TF apps are now supported by the advanced API.
    The most intricate it support for displaying discontinuous types piece by piece, as
    in the BHSA. The other one is support for graphics inclusion as in the Uruk corpus.
*   Improvements in `plain()` and `pretty()`: they deliver better results and
    they make it easier for tf-app developers.
    *   Pretty displays can be tamed by cutting of the unfolding of structure at some level
        and replacing it by plain displays (`baseTypes` display option).
    *   Highlights in plain display will be done, also for nodes deeply buried in the top node.
        This is determined by `baseTypes`: a node of type in `baseTypes` will get full 
        highlighting, all other nodes will get highlighting by boxes around the material.
*   Core API improvement:
    The `Locality` (`L`) functions `d()`, `u()`, `l()`, `r()` take an optional
    parameter `otype` holding the node type of the related nodes that will be delivered.
    This can now also be an iterable of types (preferably a set of frozenset).
*   Text-Fabric will detect when apps have a version mismatch with the general framework.
    If so, it will issue warnings and it will gracefully fall back to the core API.
    Note that if you use Text-Fabric prior version 8, there will be no graceful fallback.


---

## 7

### 7.11

#### 7.11.2

2020-04-07

Improvement in `plain()` display of nodes with highlights:

*   if a parent node *contains* a highlighted child node
    that is not separately displayed,
    the parent node receives a secondary highlight.
*   if a child node *is contained* in a highlighted parent node
    that is not separately displayd,
    the child node receives a secondary highlight.
    (This was already the case)

Secondary highlights are suppressed if either the parent or the child node
is a section node.


#### 7.11.1

2020-04-06

*   Performance imporovement in Text-Fabric browser: displaying passages
    in the presence of a query with very many results took too long.
    That has improved.
*   It is now possible to pass the optional parameter `descend` to the highlight
    function `hlText`.
    That is needed by some TF apps when they want to use text formats for nodes
    with a smaller node type than the node type for which the format has been designed. 

#### 7.11.0

2020-03-22

*   In TF browser: passages are not expanded if the user hits the expand icon,
    for some corpora. It happened when the type of level 3 sections is not the
    same as the type of level 2 sections (`int` vs `str`). TF looked at the
    wrong level when determining the type. Fixed.
*   When fetching data from GitHub, we got a deprecation warning from `pygithub`.
    Replaced the call to a deprecated method by a call to a new method.
*   Mismatch between docs and implementation of `A.plain()`: the `isLinked` parameter
    is `False` according to the docs, but was coded as `True`. The docs have been
    adapted.
*   For tf-app developers: when defining `_pretty()`, it is no longer required
    to compute whether the node type counts as big. It is done for you in the TF-generic
    method `prettyPre()`. But you can still use another definition of `bigTyoe` if
    your corpus requires is. See e.g. the Quran app.
*   For tf-app developers: the `_plain()` function tended to add a link under the material
    also in cases where there was already a hyperlinked passage indicator.
    This is now suppressed.

    **All known TF-apps (the ones in under the `annotation` org on GitHub) have been
    adapted to this change.**

### 7.10

#### 7.10.2

Fix: in some `open()` statements, the encoding parameter `encoding="utf8"` was not passed.
On some system that causes problems. The parameter has been added in all appropriate cases.

#### 7.10.0, 7.10.1

2020-02-13

GitHub is deprecating its token system for authentication when using the GitHub API.
Text-Fabric uses the GitHub API to fetch data from repositories.
In order to increase the rate limit from 50 x per hour to 5000 x per hour, users
were advised to create a pair of client-id and client-token strings.

The advise is now: create a personal access token.

See Rate limiting in (`tf.advanced.repo`).

Also: a bug fix to the walker conversion, again: thanks Ernst for spotting it.

### 7.9

#### 7.9.1-2

2020-02-13

Fixed a few bugs in the `cv.stop()` function in the
walker conversion, see `tf.convert.walker`.

Thanks to Ernst Boogert for spotting them.

#### 7.9.0

2019-12-16

Add behaviour to the "tf.compose.modify()"  function
(as of version 9 `tf.dataset.modify()`)
so that you can output modified features only instead of a whole dataset.
(Following a suggestion by Cody Kingham).


2019-07-24

### 7.8

#### 7.8.12

2019-07-24

Fix a bug spotted by Robert Voogdgeert: in search templates with qunatifiers:
if the line before the quantifier is not an atom line but a feature line,
TF crashes.
Not anymore.
The fix is at the syntactical level of queries.
I have tested most known queries and they gave identical results as before.

#### 7.8.11

2019-07-23

Following a suggestion by Camil Staps:

In search templates, the comment sign `%` does not have to be at the start of a line,
it may also be indented by white space.
Still, you cannot use % to comment out trailing parts of lines after non-blank parts.

#### 7.8.9-10

2019-07-11

When TF wants to fetch data from GitHub, but cannot get connection, it will give
some sort of message as to why.

#### 7.8.8

2019-07-05

Something new: **Recorder**, a device to export plain text from
TF in such a way that the position of nodes in that text is stored.
Then you can annotate the plain text in some tool, e.g. BRAT,
and after that, the Recorder can turn those annotations into TF features.

It is not documented yet, but this 
[notebook](https://nbviewer.jupyter.org/github/annotation/text-fabric/blob/master/test/varia/recorder.ipynb) 
shows you a complete examnple.

#### 7.8.7

2019-07-03

Fixed adding multiple click events in the javascript of the TF browser.

#### 7.8.6

2019-07-02

Unmentionable fixes.

#### 7.8.5

2019-06-21

Added fonts for the upcoming
[NENA](https://github.com/CambridgeSemiticsLab/nena_tf) corpus with TF aapp by Cody Kingham.

Updated docs for app writers.

#### 7.8.4

2019-06-14

All queries go a tad faster.
Additional small fixes.

#### 7.8.3

2019-06-13

Performance tweaks in querying.
Especially long running queries perform better.
The query planning can now handle multiple relationships of the kind
`a < b` and `b < c`.

Formerly, every `b` after `a` was searched, including the ones after `c`, and they then failed.
Now the ones after `c` are not tried anymore.

Yet the gain is not as high as I had hoped, because finding the right `b`-s between `a` and
`b` turns out to be tricky. The machinery for getting that in place and then walking
in the right direction worked, but was so costly itself, that it defeated the purpose
of a performance gain.

Have a look at some
[profiling results](https://nbviewer.jupyter.org/github/annotation/text-fabric/blob/master/test/query/bounded.ipynb).

#### 7.8.2

2019-06-11

The performance of the new feature comparison relations turned out to be bad.
They have been greatly improved. Now they are workable.
But it is possible that new cases will turn up with a bad performance.

#### 7.8.1

2019-06-10

Main thing in this release: new relations in queries, based on feature comparison,
as asked for by Oliver Glanz.
For more info: see [#50](https://github.com/annotation/text-fabric/issues/50) 

Key examples:

```
phrase
  word
  .nu. word
```

which gives the pairs of words in phrases that agree in `nu` (= grammatical number),
provided both words are marked for number.

```
phrase
  word
  .nu#nu. word
```

which gives the pairs of words in phrases that **disagree** in `nu`,
provided both words are marked for number.

```
phrase
  word
  .nu=prs_nu. word
```

which gives the pairs of words in phrases of which the number of the first word agrees
with the number of the pronominal suffix of the second word,
provided feature `nu` is present on the first word and feature `prs_nu` is present on the
second word.

These are only examples, the new relations work for any combination of node features.

You can also test on `>` and `<` if the node features are integer valued.

And for string valued features, you can also reduce the values before comparing by means
of a regular expression, which specifies the parts of the value that will be stripped.

See also `tf.about.searchusage`, jump to **Based on node features**.

The working of `silent=True` has been fine-tuned (i.e. it is
easier to silence TF in more cases.)
There is also a `silent` parameter for the `tf.convert.walker` conversion.

The `info()` function always checks whether it should be silent or not.
There is a new `warning()` function that is silent if `silent='deep'`.
So you can use `warning()` to issue messages that you do not want to be silenced
by `silent=True`.

#### 7.8.0

2019-05-30

##### Compose

The biggest addition is
a new "tf.compose" package with operators to manipulate TF data sets:
`modify()` and `combine()`.

As of version 9: `tf.dataset.modify` and `tf.volumes.collect`.

See
[compose chapter](https://nbviewer.jupyter.org/github/annotation/banks/blob/master/tutorial/compose.ipynb)
in the Banks tutorial, where you can see it in action
on (2 copies of) the nice little 100-word example corpus.

Minor goodies:

*   New `TF.loadAll()` function to load all features in one go.
*   New method `items()` for all features, which yields all pairs in the
    mapping of the feature one by one.
    See [../Api/Features.md#generics-for-features].

### 7.7

#### 7.7.11

2019-05-27

Small fixes:

*   tweaks in edge spinning (part of the search engine), but no real performance improvements
*   nothing in TF relies on Python's `glob` module anymore, which turned out to miss
    file names with characters such as `[ ]` in it.

#### 7.7.10

2019-05-23

Fixed a bug in fabric.py spotted by Ernst Boogert, where there was
a confusion between `sections` and `structure`

If a TF-app needs to import its own modules, there is the risk of conflicts
when several TF-apps get loaded in the same program and they import modules
with the same name.
TF offers a function `tf.advanced.find.loadModule`
by which an app can dynamically load
a module, and this function makes sure that the imported module gets
an app-dependent internal name.

#### 7.7.9

2019-05-21

Some queries perform much better now.
Especially the ones with `==` (same slots), `&&` (overlapping slots), and
`::` (same boundaries).

The performance of the machinery has been tuned with new parameters, and all BHSA
queries in the tutorials have been tested.

There was a pair of queries in
[searchGaps](https://nbviewer.jupyter.org/github/etcbc/bhsa/blob/master/tutorial/searchGaps.ipynb)
that
either took 9 seconds or 40, randomly. Now it is consistently 9 seconds.

See
[searchRough](https://nbviewer.jupyter.org/github/etcbc/bhsa/blob/master/tutorial/searchRough.ipynb)
at the end where the performance parameters are tweaked.

#### 7.7.6-8

2019-05-20

New functions

    cv.active(  

and

    cv.activeTypes()

in the walker conversion (requested by Ernst Boogert). 

#### 7.7.5

2019-05-18

Another 20% of the original memory footprint has been shaved off.
Method: using arrays instead of tuples for sequences of integers.

#### 7.7.4

2019-05-16

Optimization: the memory footprint of the features has been reduced by ca 30%.
Method: reusing readonly objects with the same value.

The BHSA now needs 2.2 GB of RAM, instead of the 3.4 before.

Bug fixes:
*   silent means silent again in `A.use()`
*   the walk converter will not stop if there is no structure configured

#### 7.7.3

2019-05-13

Added more checks for the new structure API when using the walk converter.
Made the pre-computing for structure more robust.

#### 7.7.2

2019-05-12

The `T` API has been extended with *structure types*.
Structure types is a flexible sectioning system with unlimited levels.
It can be configured next to the more rigid sections that `T` already supported.

The rigid system is meant to be used by the TF browser for chunking up the material
in decent portions.

The new, flexible system is meant to reflect the structure of the corpus, and will
give you means to navigate the copus accordingly.

Quick examples: [banks](https://nbviewer.jupyter.org/github/annotation/banks/blob/master/programs/structure.ipynb).
Documentation: structure in `tf.core.text`.

#### 7.7.1

2019-05-10

*   You can ask the meta data of any feature by `TF.features['featureName'].metaData`.
    That is not new.
    You can get it also by `F.featureName.meta`, for node features
    and `E.featureName.meta` for edge features.
    Both only work for loaded features.
    This is a bit more crisp.
    Thanks to Ernst Boogert for bringing this up.
*   In the TF browser, in the control where you select a book/document/scroll:
    the chosen item disappeared from the view if you narrowed down the list by typing
    a capital letter. Fixed.

#### 7.7.0

2019-05-08

Big improvement on `T.text()`.
It now accepts one or more nodes of arbitrary types and produces text
for them all.

Largely backward compatible, in that:

*   it takes the same arguments
*   when it produced sensisble results, it will produce the same results
*   when it produced nothing, it will now produce sensible things, in many cases.

You have to use the `descend` parameter a lot less.

See the `tf.core.text`.

### 7.6

#### 7.6.8

2019-05-02

There is an extra `cv.occurs()` function to check whether a feature actually
occurs in the result data.

`cv.meta(feature)` without more arguments deletes the feature from the metadata,

#### 7.6.7

2019-04-27

Added the option `force=True` to the `cv.walk()` function,
to continue conversion after errors.

#### 7.6.5-6

2019-04-26

Added punctation geresh and gershayim to the Hebrew mapping from unicode to ETCBC transcription.
The ETCBC transcription only mapped the *accents* but not the *punctuation* characters of these.

Fixed a bug in `cv.meta()` in the conversion walker.

#### 7.6.4

2019-04-25

The walker conversion module has an extra check: if you assign features to None,
it will be reported.

There is an extra `cv.meta()` function to accomodate a use case brought in by
Ernst Boogert.

#### 7.6.3

2019-04-14

Small addition to search templates.
You could already use edges in search by means of the relational operator

```
  -edgeFeature>
```

that look for `n` and `m` such that there is an `edgeFeature` edge from `n` to `m`,
and likewise

```
  <edgeFeature-
```

for edges in the opposite direction.

Now you can also use

```
  <edgeFeature>
```

that look for `n` and `m` such that there is an `edgeFeature` edge from `n` to `m`,
or from `m` to `n`, or both.

See the `tf.about.searchusage`.

This corresponds to edge features.

See also the
[Banks example](https://nbviewer.jupyter.org/github/annotation/banks/blob/master/tutorial/app.ipynb).

#### 7.6.2

2019-04-12

Small but important fix in the display logic of the `pretty()` function.
The bug is not in the particular TF-apps that partly implementt `pretty()`,
but in the generic `tf.advanced.display` library that implements the other part.

Thanks to Gyusang Jin, Christiaan Erwich and Cody Kingham for spottting it.

I wrote an account of the bug and its fixing in this 
[notebook](https://nbviewer.jupyter.org/github/annotation/text-fabric/blob/master/test/fixing/Ps18-49.ipynb).

#### 7.6.1

2019-04-10

Small fix in reporting of the location of data being used.

#### 7.6.0

2019-04-09

Simplified sharing: pushing to GitHub is enough.
It is still recommended to make a release on GitHub now and them,
but it is not necessary.

The `use()` function and the calling of the TF browser undergo an API change.

##### API addition:

When calling up data and a TF-app, you can go back in history:
to previous releases and previous commits, using a `checkout` parameter.

You can specify the checkout parameter separately for 

* the TF-app code (so you can go back to previous instantiations of the TF-app)
* the main data of the app plus its standard data modules
* every data-module that you include by means of the `--mod=` parameter.

The values of the checkout parameters tell you to use data that is:

* `clone`: locally present under `~/github` in the appropriate place
* `local`: locally present under `~/text-fabric-data` in the appropriate place
* `latest`: from the latest online release
* `hot`: from the latest online commit
* `''`: (default):
  from the latest online release, or if there are no releases,
  from the latest online commit
* `2387abc78f9de...`: a concrete commit hash found on GitHub (under Commits)
* `v1.3`: a release tag found on GitHub (under Releases)

Or consult the
[repo](https://nbviewer.jupyter.org/github/annotation/banks/blob/master/tutorial/repo.ipynb) notebook.

##### API deletion (backwards incompatible):

The parameters `check=...` and `lgc=...` of `use()` and `-lgc` and `-c` when
calling the TF browser have been removed.

These parameters were all-or-nothing, they were applied TF app code, main data,
and included data modules.

##### Advice

In most cases, just do not use the checkout parameters at all.
Then the TF-app will be kept updated, and you keep using the newest data.

If you want to producing fixed output, not influenced by future changes,
run TF once with a particular version or commit,
and after that supply the value `local` as long as you wish.

If you are developing data yourself, place the data in your repository
under `~/github`, and use the value `clone` for checkout.

##### Sharing

If you create your own features and want to share them, it is no longer needed
to zip the data and attach it to a newly created release on GitHub.
Just pushing your repo to GitHub is sufficient.

Still it is a good practice to make a release every now and then.

Even then, you do not need to attach your data as a binary.
But, if you have much data or many files, doing so makes the downloading
more efficient for the users.

##### `checkoutRepo()`

There is a new utility function `checkoutRepo()`, by which you can
maintain a local copy of any subdirectory of any repo on GitHub.

See `tf.advanced.repo`.

This is yet another step in making your scholarly work reproducible.

##### Fix in query parsing

Queries like 

```
sentence
<: sentence
```

caused TF to complain erroneously about disconnected components.
You had to say

```
s1:sentence
s2:sentence
s1 <: s2
```

instead.
That workaround is not needed anymore.

Thanks to Oliver Glanz for mentioning this behaviour.

### 7.5

#### 7.5.4

2019-03-28

The TF browser now displays the total number of results clearly.

#### 7.5.3

2019-03-27

Small fix in Excel export when called by the TF kernel.

#### 7.5.2

2019-03-26

Small fix: a TF app that did not define its own text-formats caused an error.
Now the generic TF advanced is robust against this.

#### 7.5.1

2019-03-14

Modified `E.feature.b()` so that it gives precedence to outgoing edges.

Further tweaks in layout of `plain()`.

#### 7.5

2019-03-13

API addition for `E` (edges):

    E.feature.b()

gives the symmetrical closure
of the edges under `feature`. That means it combines the results of
`E.feature.f()` and `E.feature.t()`.
In plain speech: `E.feature.b(m)` collects the nodes
that have an incoming edge from `m` and the nodes that have an outgoing edge to `m`.

### 7.4

#### 7.4.11

2019-03-11

* `TF.save()`an now write to any absolute location by means of the
  optional parameter `location`.

#### 7.4.10

2019-03-10

* The markdown display in online notebooks showed many spurious `</span>`.
  This is a bug in the Markdown renderer used by GitHub and NBViewer.
  It happens if table cells have doubly nested `<span>` elements.
  It did not show up in local notebooks.
  In order to avoid it, TF does no longer work with the Markdown renderer.
  Instead, it produces output in HTML and uses the HTML renderer in notebooks.
  That fixes the issue.
* When using `A.export()` to export data to Excel-friendly CSV files,
  some node types will get their text exported, and some just a label.
  It depended on whether the node type was a section or not.
  Now it depends on whether the node type is small or big. We export text for
  small node types. A node type is small if it is not bigger than the condense
  type. This behaviour is now the same as for pretty displays.

#### 7.4.9

2019-03-08

* Changes in font handling
* New flag in `pretty()`: `full=False`.
  See `tf.advanced.display`

#### 7.4.8

2019-03-07

* When looking for data in `lgc=True` mode, TF will report clearly when
  data cannot be found in local github clones.
  In such cases TF will look for an online release of the repo with
  the desired data attached.
  Before it was not clear enough that TF was looking online, despite the
  `lgc` flag, because of missing data.
  So if you misspelled a module path, you got messages that did not point
  you to the root cause.
* Some fixes in the plain display having to do with the passage label.

#### 7.4.7

2019-02-28

When converting a new corpus, Old Babylonian Letters (cuneiform),
I tuned the conversion module a bit.
Several improvements in the conversion program.
Better warnings for potential problems.
Several other small changes have been applied here and there.

#### 7.4.6

2019-02-07

When querying integer valued features with inequality conditions, such as 

```
word level>0
```

an unpleasant error was raised if not all words have a level, or if some words have level `None`.

That has been fixed now.

Missing values and `None` values always cause the `>` and `<` comparisons to be `False`. 

#### 7.4.5

2019-01-31

Bug fix in data pre-computation.
The bug was introduced in version **7.4.2**.

**If you have been running that version or a newer one, you might need to
recompute your features. Here is how.**

Manually: delete the `.tf` directory in `~/github/.../.../tf/version` or in
`~/text-fabric-data/.../.../tf/version/`.

This directory is hidden on the Mac and Linux and you can make it visible by pressing
`Cmd+Shift+.` on the Mac, or you can navigate to this directory in a terminal and do
`ls -al` (Mac and Linux).

The other method can be used in a Jupyter notebook:

```
from tf.app import Fabric
A = use(...)
TF.clearCache
```

After this, restart the notebook, and run it again, except the `TF.clearCache`.

If you are still pre 7.4.2, you're out of trouble. You can upgrade to 7.4.5

#### 7.4.4

2019-01-30

Added checks to the converter for section structure.

#### 7.4.3

2019-01-30

A much simpler implementation of conversions from source data to Text-Fabric.
Especially the code that the conversion writer has to produce is simplified.

#### 7.4.1-2

2019-01-29

Small fixes in the token converter.

#### 7.4.0

2019-01-25

Easier conversion of data sources to TF: via an intermediate token stream.
For more info: see [#45](https://github.com/annotation/text-fabric/issues/45) 


### 7.3

#### 7.3.14-15

2019-01-16

Make sure it works.

#### 7.3.13

2019-01-16

Feature display within pretty displays: a newline in a feature value will cause a line break
in the display, by means of a `<br/>` element.

#### 7.3.12

2019-01-16

Small fix in oslots validation.
You can save a data set without the oslots feature (a module).
The previous release wrongly flagged a oslots validation error because of a missing
oslots feature. 

That has been remedied.

#### 7.3.11

2019-01-16

If the oslots feature is not valid, weird error messages used to occur when TF tried to load
a dataset containing it. 
The oslots feature was loaded, but the computing of derived data threw a deep error.

Not anymore.

When TF saves the oslots feature it checks whether it is valid:
It should map all non-slot nodes and only non-slot nodes to slots.

So, right after you have converted a data source to TF you can check whether the oslots
is valid, during `TF.save()`.

And further down the line, if you somehow have let a faulty oslots pass,
and try to load a dataset containing such a oslots feature,
TF checks whether the range of nodes mapped by oslots does not have holes in it.

If so, it generates a clear error and stops processing.

#### 7.3.10

2019-01-10

Moved the app tutorials from the annotation/app-appName repos into a new
annotation/tutorials repo.

The reason: the app-appName are used for downloading the app code.
It should not be burdened with extra material, which is also often updated,
giving rise to many spurious redownloads of the app code.

Additionally, for education purposes it is handy to have the tutorials for all apps inside
one repo. 
For example, to use in a Microsoft Azure environment.

#### 7.3.9

2019-01-09

Better browsing for corpora with very many top level sections, such as Uruk.

For more info: see [#36](https://github.com/annotation/text-fabric/issues/36) 

#### 7.3.8

2019-01-07

Small fix.

#### 7.3.7

2019-01-07

Small fixes in the core: the Text API can now work with corpora with only two levels
of sections, such as the Quran.

#### 7.3.6

2019-01-04

Arabic transcription functions

#### 7.3.5

2018-12-19

TF-browser: Fixed a performance bottleneck in showing passages.
The computation of the highlights took too much time
if the query in question has many results.

#### 7.3.4

2018-12-18

In the `plain()` representation NBconvert has a glitch.
We can prevent that by directly outputting the plain representation as HTML,
instead of going through Markdown.
Fixed that.

#### 7.3.3

2018-12-17

The TF browser could not fiund its templates, because I had forgotten
to include the template files in the Python package.
(More precisely, I had renamed the templates folder from `views`, which was included,
to `templates`, and I had forgotten to adapt the `MANIFEST.in` file).

#### 7.3.1

2018-12-14

Glitch in the Uruk app: it imports other modules, but because of the 
dynamic way it is imported itself, a trick is needed to
let it import its submodules correctly.


2018-12-13

#### 7.3.0

2018-12-13

* Text-Fabric has moved house from `Dans-labs` to `annotation` on GitHub.
* The TF-apps have been moved to separate repos with name `app-`*xxxx*
  within [annotation](https://github.com/annotation)
* The tutorials have been moved from the repos that store the corpus data
  to the `app`-*xxxx* repositories.

### 7.2

#### 7.2.3

2018-12-13

The TF-browser exports an Excel export of results.
Now you can also export to Excel from a notebook,
using `A.export(results)`.

Jump to the tutorial:
[exportExcel](https://nbviewer.jupyter.org/github/etcbc/bhsa/blob/master/tutorial/exportExcel.ipynb)

For more info: see [#38](https://github.com/annotation/text-fabric/issues/38) 

#### 7.2.2

2018-12-12

!!! abstract "Web framework: Bottle => Flask"
    The dependency on
    [Bottle](https://bottlepy.org)
    as webserver has been replaced by
    [Flask](http://flask.pocoo.org/docs/1.0/)
    because Bottle is lagging behind in support for Python 3.7.

!!! abstract "Plain display in Uruk"
    The plain display of lines and cases now outputs their ATF source,
    instead of merely `line 1` or `case a`.

!!! abstract "Further code reorganization
    Most Python files are now less than 200 lines, although there is still
    a code file of more than 1000 lines.

#### 7.2.1

2018-12-10

* Fix broken links to the documentation of the TF API members, after the incantation.
* Fix in the Uruk lineart option: it could not be un-checked.

#### 7.2.0

2018-12-08

!!! abstract "TF Browser"
    * The TF kernel/server/website is also fit to be served over the internet
    * There is query result highlighting in passage view (like in SHEBANQ)
    * Various tweaks

!!! abstract "TF app API"
    * `prettySetup()` has been replaced with `displaySetup()` and `displayReset()`,
      by which
      you can configure a whole bunch of display parameters selectively.
    * All display functions (`pretty plain prettyTuple plainTuple show table`)
      accept a new optional parameter `withPassage`
      which will add a section label to the display.
      This parameter can be regulated in `displaySetup`. 
    * `A.search()` accepts a new optional parameter: `sort=...`
      by which you can ask for
      canonically sorted results (`True`),
      custom sorted results (pass your onw key function),
      or unsorted results (`False`).
    * New functions `A.nodeFromSectionStr()` and `A.sectionStrFromNode()`
      which give the passage string of any kind of node, if possible.
    * The function `A.plain()` now responds to the `highlights` parameter:
      you can highlight material inside plain displays.
      and
      **[display tutorial](https://nbviewer.jupyter.org/github/etcbc/bhsa/blob/master/tutorial/display.ipynb)**
    * New function `T.sectionTuple(n)` which gives the tuple of section nodes in which `n`
      is embedded
    * **Modified function `T.sectionFromNode(n, fillup=False)`**
      It used to give a tuple (section1, section2, section3), also for nodes of type
      section1 and section2 (like book and chapter). The new behaviour is the same if
      `fillup=True`. But if `fillup=False` (default), it returns a 1-tuple for
      section1 nodes and a 2-tuple for section2 nodes.
    * New API member `sortKeyTuple` to sort tuples of nodes in the
      canonical ordering (`tf.core.nodes`).
    * The code to detect the file name and path of the script/notebook you are running in,
      is inherently brittle. It is unwise to base decisions on that.
      This code has been removed from TF.
      So TF no longer knows whether you are in a notebook or not.
      And it will no longer produce links to the online
      notebook on GitHub or NBViewer.
    * Various other fixes

!!! abstract "Documentation"
    The entry points and paths from superficial to in-depth information have been
    adapted. Writing docs is an uphill battle.

!!! abstract "Under the hood"
    As TF keeps growing, the need arises over and over again to reorganize the
    code, weed out duplicate pieces of near identical functionality, and abstract from
    concrete details to generic patterns.
    This release has seen a lot of that.

### 7.1

#### 7.1.1

2018-11-21

* Queries in the TF browser are limited to three minutes, after that
  a graceful error message is shown.
* Other small fixes.

#### 7.1.0

2018-11-19

* You can use custom sets in queries in the TF browser
* Reorganized the docs of the individual apps, took the common parts together
* New functions `writeSets` and `readSets` in `tf.lib`

### 7.0

#### 7.0.3

2018-11-17

* In the BHSA, feature values on the atom-types and subphrases are now shown too, and that includes extra features
  from foreign data sets
* The feature listing after the incantation in a notebook now lists the loaded modules in a meaningful order.

#### 7.0.2

2018-11-16

* Small fixes in `text-fabric-zip`
* Internal reorgnization of the code
* Documentation updates (but internal docs are still lagging behind)

#### 7.0.1

2018-11-15

* Fixed messages and logic in finding data and checking for updates (thanks to feedback of Christian Høygaard-Jensen)
* Fixed issue #30
* Improved the doc links under features after the incantation.
* Typos in the documentation

#### 7.0.0

2018-11-14

Just before SBL Denver, two years after SBL San Antonio, where I started writing Text-Fabric,
here is major version 7.

Here is what is new:

* you can call in "foreign data": tf feature files made by yourself and other researchers;
* the foreign data shows up in the text-fabric browser;
* all features that are used in a query, show up in the pretty displays in the TF browser,
  also the foreign features;
* there is a command to prepare your own data for distribution via GitHub;
* the incantantion is simpler, but ut has changed in a backwards-incompatible way;
* after the incantation, for each feature it is shown where it comes from.

Under the hood:

* apps (bhsa, peshitta, syrnt, uruk) have been refactored thoroughly;
* a lot of repeated code inside apps has been factored out
* it is easier to turn corpora into new text-fabric apps.

Quick start: the new [share](https://nbviewer.jupyter.org/github/etcbc/bhsa/blob/master/tutorial/share.ipynb)

See the `tf.about.datasharing`
for concrete and detailed hints how to make most of this version.

---

## 6

### 6.4

#### 6.4.5-6

2018-11-08

* Bug fix: Now TF can truly work if you do not have a feature `text.tf` in your dataset.
* Tests added for basic relations in search: all relations are rigorously tested, a few small bugs fixed.
* The comment sign in queries is now `%`, only at the start of a line.

#### 6.4.3-4

2018-11-06

Big bug fix in queries: basic relationships in combination with custom sets.
The implementation of the basic relationships did not reckon with custom sets that contains both slot nodes
and non-slot nodes. And it did not trigger the right code when a custom set has only slot nodes.
That has been remedied. Some of the search tutorials have been expanded to include a number of these critical
cases. A more complete test suite outside the tutorials is still on my to do list.
Thanks to Cody Kingham for spotting and reporting this bug.

#### 6.4, 6.4.1-2

2018-11-02

* A passage browsing interface that interacts with the search results. 
* The interface scrolls to the highlighted row.

Minor things:

* More refined warnings when you run out of memory
* TF checks whether you are running 64 bit Python. If not, a warning is issued.

### 6.3

#### 6.3.2

2018-10-27

* Better documentation for installation of Text-Fabric on Ubuntu.
* Added new module requirements: ipykernel and notebook.

#### 6.3.1

2018-10-24

An optional parameter `silent=False` has been added to the initialisation calls of the specific app APIs:
you can say now

```python
A = Xxxx(silent=True)
```

where `Xxxx` is a know corpus.

and then all non-error messages will be suppressed.
If the underlying TF API needs to precompute data, it will still be shown, because this may cause an otherwise
unexpected delay.
Since this is a releatively rare case, and since this can be remedied by running the call again,
I leave this behaviour as it is.

#### 6.3.0

2018-10-19

* Character tables for Hebrew abd Syriac, with links to them from the TF browser
* Better font handling
* In the `pretty` and `plain` functions you can pass a `fmt` parameter, to control the text representation
  (original script, transcription, phonetics)
* You can also control the text representation in the Text-Fabric browser.

### 6.2

#### 6.2.2

2018-10-18

* Added ETCBC/WIT transcriptions to the SyrNT data source. Now both Peshitta
  and Syriac New Testament have ETCBC transcriptions.
* The older, rectangular logo makes place for the more crisp, circular one 

#### 6.2.1

2018-10-17

* New app: Syrnt (Syriac New Testament. It works much like the Peshitta, but the SyrNT data
  has linguistic annotations at the word and lexeme levels.
  After this upgrade you can browse the SyrNT by saying `text-fabric syrnt` on the command line.

#### 6.2.0

2018-10-16

* New app: Peshitta. It works much like the BHSA, but there is one big difference: the current Peshitta data
  does not have linguistic annotations. There are just books, chapters, verses and words.
  We expect to add lemmatizations of words shortly.
  After this upgrade you can browse the peshitta by saying `text-fabric peshitta` on the command line.
* Fixed a bug in exportMQL:
  when there are no enumerated values, do not write out an empty
  `CREATE ENUMERATION` statement to the MQL file. 

### 6.1

#### 6.1.0

2018-10-12

* More precise provenance data when you export results from the Text-Fabric data;
* Under the hood reorganization of configuration data of apps like Bhsa and Uruk;
* App-specific parts of the code have moved to more generic parts: a big cleanup has performed;
* This will make it easier to add new apps.

### 6.0

#### 6.0.7-8-9

2018-10-11

* Avoid computing the notebook name when the user passes a name for the notebook to `Uruk()` or `Bhsa()`.
  And when the computing needs to be done, all exceptions will be caught, because the code for determining
  the notebook name is brittle, and may crash if the Jupyter version does not match.
* Fixed the bug that the Bhsa and Uruk did not run properly outside a notebook or outside a github repo.
* In Bhsa and Uruk, the generated info after the incantation can be collapsed (features, API members).

#### 6.0.6

2018-10-10

In the BHSA, the edge features are now shown too after the incantation.

If you hoist the API members into your namespace, you will get a list of hoisted names,
linked to the API documentation.

#### 6.0.5

2018-10-09

When using BHSA and Uruk in a notebook, there is an even simpler incantation which auto downloads features.

In the BHSA it is shown which features are loaded, with direct links to the feature docs.

#### 6.0.4

2018-10-09

When using BHSA and Uruk in a notebook, there is a simpler incantation which auto downloads features.

Some issues concerning paths in zipfiles of downloaded data have been solved.

#### 6.0.3

Easier incantations for `Bhsa()` and `Uruk()`.

* It is no longer needed to pass the name of the notebook, but you can still do so: `name='mynotebook'`
* You can leave out the `api` argument in `Bhsa()`. Then you do not have to load features by means of `TF.load()`,
  `Bhsa()` will load a standard set of features, and if the BHSA data is missing, it will download them first.

The former ways of calling `Bhsa()` and `Uruk()` are still valid. Note that all arguments have become optional.

2018-10-08

The Text-Fabric browser will always print a banner with its name and version.
If you pass it the argument --help or -h or --version or -v it will show the relevant information
and stop executing.

#### 6.0.2

2018-10-07

The Text-Fabric browser takes it data by default from `~/text-fabric-data`.
It will not check local github clones for data.

But if you pass the option `-lgc`, it will first check your local github clones.

So it you do nothing special, the TF browser always works with the auto-downloaded data.

#### 6.0.1

2018-10-06

Not only the core BHSA data will auto load, also the related PHONO and PARALLELS data.
A new release has been made of the related data, and they are now in sync with the release of the core data.

If you use auto load already, you do not have to do anything.

But if you have the etcbc/phono and etcbc/parallels repos in your `~/github` folder, you should do 
a `git pull origin master` on those repos.

**N.B.**: I am contemplating to have the Text-Fabric browser always use data from `~/text-fabric-data` and no longer
from `~/github/etcbc`. Then the TF browser always controls its own data, and it will not occur that
the version of the TF browser is not compatible with the version of the TF data in your github repos, or that
the main data and the related data are out of synch.

The disadvantage is that if you have the github repos on your system, you get redundant data in `~/text-fabric-data`.
However, there is only one version kept in `~/text-fabric-data`, so this is not much.

#### 6.0.0

2018-10-05

A big update with several changes:

#####  API change:
`T.text()` has got more behaviours.

This change was needed for the Text-Fabric browser, in order to represent *lexemes* in exported files.

!!! hint "Showcase: BHSA dictionary"
    Here is how you can collect the BHSA lexemes in an Excel sheet.

    * [about.md](https://github.com/annotation/text-fabric/blob/master/test/bhsa/bhsa-Dictionary/about.md)
    * [RESULTSX.tsv](https://github.com/annotation/text-fabric/blob/master/test/bhsa/bhsa-Dictionary/RESULTSX.tsv)

It might also be handy for the programmers amongst you.

##### Auto update
The Text-Fabric browser checks if you are using the most recent release of the data.

##### Font rendering
A font rendering issue in Safari 12 in macos Mojave prevented the use of Ezra SIL for Hebrew in notebooks.
We now work around this by relying on the distribution of Ezra SIL as webfont
in the [font library](https://fontlibrary.org).

##### Additional small fixes.
Not worth telling.

!!! hint "update Text-Fabric"
    To update Text-Fabric itself to version 6.0, consult `tf.about.install`.
    Perform this step first, because the new TF may download the new data for you.

!!! caution "Data update needed"
    In order to work successfully with the new `T.text()` function, you need a newer release (1.4) of the BHSA *data*.
    (In fact, only one line in one feature has changed (`otext.tf`).

Here is how you get the new data release:

###### Automatically
If previously your Text-Fabric browser has automatically downloaded the data for you, it will detect the new release
and download it automatically. You do not have to do anything, except increase your patience.
The download (24 MB) takes some time and after that Text-Fabric will precompute related data, which may take
a few minutes. This is a one-time-step after a data update.

###### Manually
If you have a clone of the BHSA repository, then go to that directory and say `git pull origin master`.
If you get error messages, then you have local changes in your local BHSA repository that conflict with
the github version. Probably you have run the tutorials in place. Best thing to do is:

* copy your BHSA tutorial directory to somehwere else;
* remove your local BHSA repository entirely;
* decide whether you really want the whole repo back (nearly 4 GB).

If not: you're done, and TF will download automatically the data it needs.

If you still need it: move one directory up (into the `etcbc` directory) and do `git clone https://github.com/etcbc/bhsa`.

If you want to consult the tutorials, either:

* view them on [nbviewer](https://nbviewer.jupyter.org/github/etcbc/bhsa/tree/master/tutorial/); or
* run them in a directory outside the BHSA repo (where you have copied it a minute ago).

---

## 5

### 5.6

#### 5.6.4

2018-10-04

Solved a font-rendering issue on Safari 12 (Macos Mojave): locally installed fonts, such as Ezra SIL are not being
honored. So I linked to a stylesheet of the [fontlibrary](https://fontlibrary.org) which has a webfont version of
Ezra SIL. That worked.

#### 5.6.3

2018-10-04

Exported tab-separated files get extension `.tsv` instead of `.csv`, because then they render better in GitHub. 

#### 5.6.2

2018-10-04

Small optimization.
More docs about reading and writing Excel compatible CSV files with Hebrew characters in it.

#### 5.6.1

2018-10-04

Better exporting from TF browser: a good RESULTSX.tsv with results, sensibly augmented with information, directly openable
in Excel, even when non-latin unicode code characters are present .
All features that occur in the searchTemplate are drawn in into the RESULTSX.tsv, onto the nodes they filter.

An additonal feature filtering is now possible in searchTemplates: `feature*`. 
This acts as "no additional constraint", so it does not influence the result set.
But it will be picked up and used to add information into the RESULTSX.tsv.

### 5.5

#### 5.5.25

2018-10-03

The Text-Fabric browser exports results as node lists and produces also a CONTEXT.tsv with all feature
values for all nodes in the results.
However, it does not contain full text representations of the nodes and it is also not possible to see in what verses
the nodes occur.

That has changed. The last column of CONTEXT.tsv contains the full text of a node.
And there are three columns at the beginning that contain the references to the sections the node is in.
For the BHSA that is the book, chapter and verse.

#### 5.5.24

2018-09-25

BHSA app in Text-Fabric Browser: the book names on the verse pad should be the English book names.
That is now in the help texts, including a link to the list of English book names.

#### 5.5.23

2018-09-21

Problem in use of `msgCache` in the search engine, which caused `fetch()` to fail in some cases. Fixed.

#### 5.5.22

2018-09-13

Fix in left-to-right displays of extra features in `pretty()` displays in the BHSA.

#### 5.5.21

2018-08-30

Bug fix in transcription.py w.r.t. to Syriac transcriptions.

#### 5.5.20

2018-08-16

BHSA app: adjusted the color of the gloss attribute: darker.

#### 5.5.19

2018-07-19

Fixed: when opening files for reading and writing for an export of a TF browser session: specify that
the encoding is `utf8`. 
This is needed on those windowses where the default encoding is something else, usually `cp1252`.

#### 5.5.18

2018-07-19

No change, only in the build script.
This is a test whether after uploading to PyPi, users
can upgrade without using the `--no-cache-dir` in their
pip commands.

#### 5.5.17

2018-07-19

The main functions in kernel and web can be passed arguments, instead that they always
read from sys.argv.

So that it can be used packaged apps.

#### 5.5.16

2018-07-17

Extra option when starting up the text-fabric web interface: `-docker` to let the web server
listen at `0.0.0.0` instead of `localhost`.

So that it can be used in a Docker container.

#### 5.5.15

2018-07-16

Extra option when starting up the text-fabric web interface: `-noweb` to not start the web browser.

So that it can be used in a Docker container.

#### 5.5.13-14

2018-07-12

Better error reporting of quantified queries.

#### 5.5.12

2018-07-11

* Faster export of big csv lists.
* Tweaks in the web interface.
* Cleaner termination of processes.
* The concept *TF data server* is now called *TF kernel*

#### 5.5.8-11

2018-07-10

* Better in catching out-of-memory errors.
* Prevents creation of corrupt compiled binary TF data.
* Prevents starting the web server if the TF kernel fails to load.

#### 5.5.7

2018-07-09

Optimization is export from TF browser.

#### 5.5.6

2018-07-09

Better help display.

* The opened-state of help sections is remembered.
* You can open help next to an other open section in the sidebar.

#### 5.5.5

2018-07-08

Crisper icon.

#### 5.5.4

2018-07-6

Docs updated. Little bit of refactoring.

#### 5.5.1-3

2018-07-4

In the TF browser, use a selection of all the features when working with the BHSA.
Otherwise in Windows you might run out of memory, even if you have 8GB RAM.

#### 5.5.0

2018-07-4

Text-Fabric can download data for BHSA and Uruk. You do not have to clone github repositories for that.
The data downloaded by Text-Fabric ends up in `text-fabric-data` under your home directory.

### 5.4

#### 5.4.5-7

2018-07-03

Experimenting with setuptools to get the text-fabric script working
on Windows.

#### 5.4.4

2018-07-02

Added renaming/duplicating of jobs and change of directory.

#### 5.4.3

2018-06-29

Small fixes in error reporting in search.

#### 5.4.1-2

2018-06-28

Text-Fabric browser: at export a csv file with all results is created, and also a markdown file with metadata.

Small fixes.

#### 5.4.0

2018-06-26

Improved interface and functionality of the text-fabric browser:

* you can save your work
* you can enter verse references and tablet P numbers
* there is help
* there is a side bar

!!! cautions "Docs not up to date"
    The API docs are not up-to-date: there are new functions in the Bhsa and Uruk APIs.
    The server/kernel/client apis are not completely spelled out.
    However, the help for the text-fabric browser is included in the interface itself.

### 5.3

#### 5.3.3

2018-06-23

Small fix: command line args for text-fabric.

#### 5.3.0-2

2018-06-22

!!! abstract "Better process management"
    When the TF web interface is started, it cleans up remnant process that might get in the way otherwise.
    You can also say

```
text-fabric -k
```

to kill all remnant processes,
or

```
text-fabric -k corpus
```

to kill the processes for a specific corpus only.

!!! abstract "Manual node entry"
    You can enter nodes manually in the TF browser.
    Handy for quick inspection.
    You can click on the sequence number to
    append the node tuple of that row to the tuple input field.
    That way you can collect interesting results.

!!! abstract "Name and Description"
    You can enter a name which will be used as title and file name during export.

    You can enter a description in Markdown.
    When you export your query, the description appears
    formatted on top.

!!! abstract "Provenance"
    If you export a query, provenance is added, using DOIs.

!!! abstract "Small fixes"
    No more blank pages due to double page breaks.

### 5.2

#### 5.2.1

2018-06-21

* Added an `expand all` checkbox in the text-fabric browser,
  to expand all shown rows or to collapse them.
* Export function for search results in the text-fabric browser.
  What you see is what you get, 1 pretty display per page if you have
  the browser save it to pdf.
* Small tweaks

#### 5.1

2018-06-21

When displaying results in condensed mode, you
can now choose the level of the container in which results are highlighted.
So far it was fixed to `verse` for the bhsa and `tablet` for Uruk.

The docs are lagging behind!
But it is shown in the tutorials and you can observer it in the text-fabric browser.

### 5.0

#### 5.0.1,2,3,4

2018-06-19

Addressed start-up problems.

#### 5.0.0

2018-06-18

Built in web server and client for local query running.
It is implemented for Bhsa and Uruk.

---

## 4

### 4.4

#### 4.4.2,3

2018-06-13

New distribution method with setuptools.
Text-Fabric has now dependencies on modules rpyc and bottle,
because it contains a built-in TF kernel and web server.

This website is still barely functional, though.

#### 4.4.1

2018-06-10

Search API:

Escapes in regular expression search was buggy and convoluted.
If a feature value contains a `|` then in an RE you have to enter `\|` to match it.
But to have that work in a TF search, you needed to say `\\\|`. 

On the other hand, in the same case for `.` instead of `|`, you could just sat `\.`

In the new situation you do not have to double escape in REs anymore.
You can just say `\|` and `\.`.

#### 4.4.0

2018-06-06

Search API:

S.search() accepts a new optional parameter: `withContext`.
It triggers the output of context information for nodes in the result tuples.

### 4.3

#### 4.3.4, 4.3.5

2018-06-05

Search API:

The `/with/ /or/ /or/ /-/` quantifier is also allowed with zero `/or/` s.

Small fix in the `/with/` quantifier if there are quantifiers between this one and its parent atom.

#### 4.3.3

2018-06-01

Search API:

Improved quantifiers in search: 

*   `/where/` `/have/` `/without/` `/with/` `/or/` `/-/`;
*   much clearer indentation rules (no caret anymore);
*   better reporting by `S.study()`.

#### 4.3.2

2018-05-31

Search API: 

*   quantifiers may use the name `..` to refer to their parents
*   you may use names in the place of atoms, which lessens the need for constructs with `p = q`
*   stricter checks on the syntax and position of quantifiers

#### 4.3.1

2018-05-30

Docs and metadata update

#### 4.3.0

2018-05-30

*   API Change in Search.

    In search templates I recently added things like

        word vt!

    which checks for words that do not have a value for feature `vt`.

    The syntax for this has now changed to

        word vt#

*   Unequal (#) in feature value conditions.

    Now you can say things like

        word vt#infa|infc

    meaning that the value of feature is not one of `infa`, `infc`.

    So, in addition to `=` we have `#` for "not equal".
*   Quantifiers.

    You can now use quantifiers in search. One of them is like `NOTEXIST` in MQL.

*   A number of minor fixes.

### 4.2

#### 4.2.1

2018-05-25

*   Several improvements in the pretty display in Bhsa and Uruk APIs
*   Under the hood changes in `S.search()` to prepare for *quantifiers* in search templates.

    *   Tokenisation of quantifiers already works
    *   Searches can now spawn auxiliary searches without polluting intermediate data
    *   This has been done by promoting the `S` API to a factory of search engines.
        By deafault, `S` creates and maintains a single factory, so to the user
        it is the same `S`. But when it needs to run a query in the middle of processing another query
        it can just spawn another search engine to do that, without interfering with the
        original search.

*   NB: the search tutorial for the Bhsa got too big. It has thoroughly been rewritten.

#### 4.2.0

2018-05-23

The Search API has been extended:

*   you can use custom sets in your query templates
*   you can search in shallow mode: instead of full result tuples, you just get a set
    of the top-level thing you mention in your template.
    
This functionality is a precursor for
[quantifiers in search templates](https://github.com/annotation/text-fabric/issues/4)
but is also a powerful addition to search in its own right.

### 4.1

#### 4.1.2

2018-05-17

Bhsa and Uruk APIs:

*   custom highlight colours also work for condensed results.
*   you can pass the `highlights` parameter also to `show` and `prettyTuple`


#### 4.1.1

2018-05-16

Bhsa API: you can customize the features that are shown in pretty displays.

#### 4.1.0

2018-05-16

Bhsa and Uruk APIs: you can customize the highlighting of search results:

*   different colours for different parts of the results
*   you can choose your colours freely from all that CSS has to offer.

See the updated search tutorials.

### 4.0

#### 4.0.3

2018-05-11

No changes, just quirks in the update process to get a new version of TF out.

#### 4.0.1

2018-05-11

Documentation updates.

#### 4.0.0

2018-05-11

*   Additions to Search.
    You can now include the values of edges in your search templates.
*   `F.`*feature*`.freqList()` accepts a new parameter: `nodeTypes`. It will restrict its results to nodes in
    one of the types in `nodeTypes`. 
*   You can now also do `E.`*feature*`.freqList()`.
    It will count the number of edges if the edge is declared to be without values, 
    or it will give a frequency list of the edges by value if the edge has values.
    Like `F.freqList`, you can pass parameters to constrain the frequency list to certain node types.
    You can constrain the node types from which the edges start (`nodeTypesFrom`) and where they arrive
    (`nodeTypesTo`).
*   New documentation system based on [MkDocs](https://mkdocs.readthedocs.io/en/stable/).

---

## 3

### 3.4

#### 3.4.12

2018-05-02

The Uruk and Bhsa APIs show the version of Text-Fabric that is being called.

#### 3.4.11

2018-05-01

Uruk

*   cases are divided horizontally and vertically, alternating with their
    nesting level;
*   cases have a feature **depth** now, indicating at which level of nesting they
    are.

#### 3.4.8-9-10

2018-04-30

Various small fixes, such as:

*   Bhsa: Lexeme links in pretty displays.

*   Uruk: Prevented spurious `</div>` in NbViewer.

#### 3.4.7

Uruk: Modified local image names

#### 3.4.6

Small tweaks in search.

#### 3.4.5

2018-04-28

Bhsa API:

*   new functions `plain()` and `table()` for plainly representing nodes, tuples
    and result lists, as opposed to the abundant representations by `pretty()` and
    `show()`.

#### 3.4.4

2018-04-27

Uruk API:

*   new functions `plain()` and `table()` for plainly representing nodes, tuples
    and result lists, as opposed to the abundant representations by `pretty()` and
    `show()`.

#### 3.4.2

2018-04-26

Better search documentation.

Uruk API: small fixes.

#### 3.4.1

2018-04-25

Bhsa API:

*   Search/show: you can now show results condensed: i.e. a list of passages with
    highlighted results is returned. This is how SHEBANQ represents the results of
    a query. If you have two results in the same verse, with `condensed=True` you
    get one verse display with two highlights, with `condensed=False` you get two
    verse displays with one highlight each.

Uruk API:

*   Search/show: the `pretty`, `prettyTuple`, `show` functions of the Bhsa API
    have bee translated to the Uruk API. You can now get **very** pretty displays
    of search results.

#### 3.4.0

2018-04-23

Search

*   You can use regular expressions to specify feature values in queries.
*   You could already search for nodes which have a non-None value for a certain
    feature. Now you can also search for the complement: nodes that do not have a
    certain feature.

Bhsa API:

The display of query results also works with lexeme nodes.

### 3.3

#### 3.3.4

2018-04-20

Uruk API: Better height and width control for images. Leaner captions.

#### 3.3.3

2018-04-19

Uruk API: `casesByLevel()` returns case nodes in corpus order.

#### 3.3.2

2018-04-18

Change in the Uruk api reflecting that undivided lines have no cases now (was:
they had a single case with the same material as the line). Also: the feature
`fullNumber` on cases is now called `number`, and contains the full hierarchical
part leading to a case. There is an extra feature `terminal` on lines and cases
if they are not subdivided.

Changes in Uruk and Bhsa api:

*   fixed a bug that occurred when working outside a GitHub repository.

#### 3.3.1

2018-04-18

Change in the Uruk api. `casesByLevel()` now takes an optional argument
`terminal` instead of `withChildren`, with opposite values.

`withChildren=False` is ambiguous: will it deliver only cases that have no
children (intended), or will it deliver cases and their children (understood,
but not intended).

`terminal=True`: delivers only cases that are terminal.

`terminal=False`: delivers all cases at that level.

#### 3.3.0

2018-04-14

Small fix in the bhsa api.

Bumped the version number because of the inclusion of corpus specific APIs.

### 3.2

#### 3.2.6

2018-04-14

*   Text-Fabric now contains corpus specific extras:
    *   `bhsa.py` for the Hebrew Bible (BHSA)
    *   `uruk.py` for the Proto-Cuneiform corpus Uruk
*   The `Fabric(locations=locations, modules=modules)` constructor now uses `['']`
    as default value for modules. Now you can use the `locations` parameter on its
    own to specify the search paths for TF features, leaving the `modules`
    parameter undefined, if you wish.

#### 3.2.5

2018-03-23

Enhancement in search templates: you can now test for the presence of features.
Till now, you could only test for one or more concrete values of features. So,
in addition to things like

    word number=plural tense=yiqtol

you can also say things like

    word number=plural tense

and it will give you words in the plural that have a tense.

#### 3.2.4

2018-03-20

The short API names `F`, `T`, `L` etc. have been aliased to longer names:
`Feature`, `Text`, `Locality`, etc.

#### 3.2.2

2018-02-27

Removed the sub module `uruk.py`. It is better to keep corpus dependent modules
in outside the TF package.

#### 3.2.1

2018-02-26

Added a sub module `uruk.py`, which contains methods to produce ATF
transcriptions for nodes of certain types.

#### 3.2.0

2018-02-19

**API change** Previously, the functions `L.d()` and `L.u()` took rank into
account. In the Hebrew Bible, that means that `L.d(sentence)` will not return a
verse, even if the verse is contained in the sentence.

This might be handy for sentences and verses, but in general this behaviour
causes problems. It also disturbs the expectation that with these functions you
get *all* embedders and embeddees.

So we have lifted this restriction. Still, the results of the `L` functions have
an ordering that takes into account the levels of the returned nodes.

**Enhancement** Previously, Text-Fabric determined the levels of node types
automatically, based on the average slot-size of nodes within the node types. So
books get a lower level than chapters than verses than phrases, etc.

However, working with cuneiform tablets revealed that containing node types may
have a smaller average size than contained node types. This happens when a
container type only contains small instances of the contained type and not the
bigger ones.

Now you can override the computation by text-fabric by means of a key-value in
the *otext* feature.

### 3.1

#### 3.1.5

2018-02-15

Fixed a small problem in `sectionFromNode(n)` when `n` is a node within a
primary section but outside secondary/tertiary sections.

#### 3.1.4

2018-02-15

Small fix in the Text API. If your data set does not have language dependent
features, for section level 1 headings, such as `book@en`, `book@sw`, the Text
API will not break, and the plain `book` feature will be taken always.

We also reformatted all code with a PEP8 code formatter.

#### 3.1.3

2018-01-29

Small adaptions in conversion from MQL to TF, it can now also convert the MQL
coming from CALAP dataset (Syriac).

#### 3.1.2

2018-01-27

Nothing changed, only the names of some variables and the text of some messages.
The terminology has been made more consistent with the fabric metaphor, in
particular, *grid* has been replaced by *warp*.

#### 3.1.1

2017-10-21

The `exportMQL()` function now generates one single enumeration type that serves
for all enumeration features. That makes it possible to compare values of different
enumeration features with each other, such as `ps` and `prs_ps`.

#### 3.1.0

2017-10-20

The `exportMQL()` function now generates enumeration types for features, if
certain conditions are fulfilled. That makes it possible to query those features
with the `IN` relationship of MQL, like `[chapter book IN (Genesis, Exodus)]`.

### 3.0

#### 3.0.8

2017-10-07

When reading edges with values, also the edges without a value are taken in.

#### 3.0.7

2017-10-07

Edges with edge values did not allow for the absence of values. Now they do.

#### 3.0.6

2017-10-05

A major tweak in the `tf.fabric.Fabric.importMQL` function so that it can
handle gaps in the monad sequence. The issue arose when converting MQL for
version 3 of the [BHSA](https://github.com/etcbc/bhsa). In that version there
are somewhat arbitrary gaps in the monad sequence between the books of the
Hebrew Bible. I transform a gapped sequence of monads into a continuous sequence
of slots.

#### 3.0.5

2017-10-05

Another little tweak in the `tf.fabric.Fabric.importMQL` function so that it
can handle more patterns in the MQL dump file. The issue arose when converting
MQL for version 3 of the [BHSA](https://github.com/etcbc/bhsa).

#### 3.0.4

2017-10-04

Little tweak in the `tf.fabric.Fabric.importMQL` function so that it can handle
more patterns in the MQL dump file. The issue arose when converting MQL for
[extrabiblical](https://github.com/etcbc/extrabiblical) material.

#### 3.0.2, 3.0.3

2017-10-03

No changes, only an update of the package metadata, to reflect that Text-Fabric
has moved from [ETCBC](https://github.com/etcbc) to
[Dans-labs](https://github.com/Dans-labs).

#### 3.0.1

2017-10-02

Bug fix in reading edge features with values.

#### 3.0.0

2017-10-02

MQL! You can now convert MQL data into a TF dataset:
`tf.fabric.Fabric.importMQL`. We had already `tf.fabric.Fabric.exportMQL`.

The consequence is that we can operate with much agility between the worlds of
MQL and TF.

We can start with source data in MQL, convert it to TF, combine it with other TF
data sources, compute additional stuff and add it, and then finally export it as
enriched MQL, so that the enriched data can be queried by MQL.

--- 

## 2

### 2.3

#### 2.3.15

2017-09-29

Completion: TF defines the concept of
edges that
carry a value. But so far we have not used them. It turned out that it was
impossible to let TF know that an edge carries values, when
saving data as a new feature. Now it is possible.

#### 2.3.14

2017-09-29

Bug fix: it was not possible to get
`T.nodeFromSection(('2_Chronicles', 36, 23))`, the last verse in the Bible.

This is the consequence of a bug in precomputing the sections
sections. The preparation step used

```python
range(firstVerse, lastVerse)
```

somewhere, which should of course have been

```python
range(firstVerse, lastVerse + 1)
```

#### 2.3.13

2017-09-28

Loading TF was not completely silent if `silent=True` was passed. Better now.

#### 2.3.12

2017-09-18

*   Small fix in
    TF.save().
    The spec says that the metadata under the empty key will be inserted into all
    features, but in fact this did not happen. Instead it was used as a default
    when some feature did not have metadata specified.

    From now on, that metadata will spread through all features.

*   New API function explore, to get a list of all known
    features in a dataset.

#### 2.3.11

2017-09-18

*   Small fix in Search: the implementation of the relation operator `||`
    (disjoint slot sets) was faulty. Repaired.
*   The
    [search tutorial](https://github.com/annotation/text-fabric/blob/master/docs/searchTutorial.ipynb)
    got an extra example: how to look for gaps. Gaps are not a primitive in the TF
    search language. Yet the language turns out to be powerful enough to look for
    gaps. This answers a question by Cody Kingham.

#### 2.3.10

2017-08-24

When defining text formats in the `otext.tf` feature, you can now include
newlines and tabs in the formats. Enter them as `\n` and `\t`.

#### 2.3.9

2017-07-24

TF has a list of default locations to look for data sources: `~/Downloads`,
`~/github`, etc. Now `~/Dropbox` has been added to that list.

#### 2.3.8

2017-07-24

The section levels (book, chapter, verse) were supposed to be customizable
through the otext feature. But in
fact, up till version 2.3.7 this did not work. From now on the names of the
section types and the features that name/number them, are given in the `otext`
feature. It is still the case that exactly three levels must be specified,
otherwise it does not work.

#### 2.3.7

2017-05-12

Fixes. Added an extra default location for looking for text-fabric-data sources,
for the benefit of running text-fabric within a shared notebook service.

#### 2.3.5, 2.3.6

2017-03-01

Bug fix in Search. Spotted by Cody Kingham. Relational operators between atoms
in the template got discarded after an outdent.

#### 2.3.4

2017-02-12

Also the `Fabric()` call can be made silent now.

#### 2.3.3

2017-02-11

Improvements:

*   you can load features more silently. See `TF.load()`;
*   you can search more silently. See `S.study()`;
*   you can search more concisely. See the new `S.search()`;
*   when fetching results, the `amount` parameter of
    `S.fetch()` has been renamed to `limit`;
*   the tutorial notebooks (see links on top) have been updated.

#### 2.3.2

2017-02-03

Bug fix: the results of `F.feature.s()`, `E.feature.f()`, and `E.features.t()`
are now all tuples. They were a mixture of tuples and lists.

#### 2.3.1

2017-01-23

Bug fix: when searching simple queries with only one query node, the result
nodes were delivered as integers, instead of 1-tuples of integers.

#### 2.3.0 

2017-01-13

We start archiving releases of Text-Fabric at [Zenodo](https://zenodo.org).

### 2.2

#### 2.2.1

2017-01-09

Small fixes.

#### 2.2.0

2017-01-06

##### New: sortKey

The API has a new member: `sortKey`

New relationships in templates: `nearness`. See for examples the end of the
[searchTutorial](https://github.com/annotation/text-fabric/blob/master/docs/searchTutorial.ipynb).
Thanks to James Cuénod for requesting nearness operators.

##### Fixes

*   in `S.glean()` word nodes were not printed;
*   the check whether the search graph consists of a single connected component
    did not handle the case of one node without edges well;

### 2.1

#### 2.1.3

2017-01-04

Various fixes.

#### 2.1.0

2017-01-04

##### New: relations

Some relations have been added to search templates:

*   `=:` and `:=` and `::`: *start at same slot*, *end at same slot*, *start at
    same slot and end at same slot*
*   `<:` and `:>`: *adjacent before* and *adjacent next*.

The latter two can also be used through the `L`-api: `L.p()` and `L.n()`.

The data that feeds them is precomputed and available as `C.boundary`.

##### New: enhanced search templates

You can now easily make extra constraints in search templates without naming
atoms.

See the
[searchTutorial](https://github.com/annotation/text-fabric/blob/master/docs/searchTutorial.ipynb)
for an updated exposition on searching.

### 2.0

#### 2.0.0

2016-12-23

##### New: Search

![warmXmas](../images/warmXmas.jpg)

*Want to feel cosy with Christmas? Put your laptop on your lap, update
Text-Fabric, and start playing with search. Your laptop will spin itself warm
with your queries!*

Text-Fabric just got a powerful search facility, based on (graph)-templates.

It is still very fresh, and more experimentation will be needed. Feedback is
welcome.

Start with the
[tutorial](https://github.com/annotation/text-fabric/blob/master/docs/searchTutorial.ipynb).

The implementation of this search engine can be nicely explained with a textile
metaphor: spinning wool into yarn and then stitching the yarns together.

That will be explained further in a document that I'll love to write during
Xmas.

---

## 1

### 1.2

#### 1.2.7

2016-12-14

##### New

`F.otype.sInterval()`

#### 1.2.6

2016-12-14

##### bug fix

There was an error in computing the order of nodes. One of the consequences was
that objects that occupy the same slots were not ordered properly. And that had
as consequence that you could not go up from words in one-word phrases to their
containing phrase.

It has been remedied.

!!! note
    Your computed data needs to be refreshed. This can be done by calling a new
    function `TF.clearCache()`. When you use TF after
    this, you will see it working quite hard to recompute a bunch of data.

#### 1.2.5

2016-12-13

Documentation update

#### 1.2.0

2016-12-08

!!! note
    Data update needed

##### New

##### Frequency lists ###

`F.feature.freqList()`: get a sorted frequency list for any
feature. Handy as a first step in exploring a feature.

##### Export to MQL ###

`TF.exportMQL()`: export a whole dataset as a MQL database.
Including all modules that you have loaded with it.

##### Changed

The slot numbers start at 0, no longer at 1. Personally I prefer the zero
starting point, but Emdros insists on positive monads and objects ids. Most
important is that users do not have to add/subtract one from the numbers they
see in TF if they want to use it in MQL and vice versa.

Because of this you need to update your data too:

```sh
    cd ~/github/text-fabric-data
    git pull origin master
```
