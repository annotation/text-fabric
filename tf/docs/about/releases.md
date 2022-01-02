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

## 9

### 9.0

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
*   A new function `tf.advanced.app.text.specialCharacters` which provides
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

## Older releases

See `tf.about.releasesold`.
