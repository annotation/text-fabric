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
