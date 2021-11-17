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
