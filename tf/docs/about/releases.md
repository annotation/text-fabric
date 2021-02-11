# Release notes

!!! hint "Consult the tutorials after changes"
    When we change the API, we make sure that the tutorials show off
    all possibilities.

See the app-specific tutorials in
[annotation](https://nbviewer.jupyter.org/github/annotation/tutorials/tree/master).

When TF apps have been updated, they will be autoloaded to the newest version
provided you call the app as follows:

(in a program)

```python
use('appName:latest', ... )
```

(on the command line)

```sh
text-fabric appName:latest
```

This will get you the newest stable version.
To get the newest unstable version:

(in a program)

```python
use('appName:hot', ...)
```

(on the command line)

```sh
text-fabric appName:hot
```

!!! hint "What's going on"
    See the [issue list on GitHub](https://github.com/annotation/text-fabric/issues).

---

## 8

### 8.4

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
That code is now in `tf.compose.nodemaps`.
It is used in the 
[missieven](https://nbviewer.jupyter.org/github/Dans-labs/clariah-gm/blob/master/programs/map.ipynb)
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
[missieven corpus](https://github.com/annotation/app-missieven/blob/master/code/config.yaml).

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


## Older releases

See `tf.about.releasesold`
