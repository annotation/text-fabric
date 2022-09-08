# Release notes

!!! hint "Consult the tutorials after changes"
    When we change the API, we make sure that the tutorials show off
    all possibilities.

See the app-specific tutorials via `tf.about.corpora`.

---

## 10

## 10.2.2

2022-09-08

Changes in the output of Text-Fabric to the console.
It is detected whether it runs in interactive mode (e.g. Jupyter notebook) or not.
If not, the display methods of the Jupyter notebook are suppressed, 
and many outputs are done in plain text instead of HTML.

## 10.2.1

2022-08-23

Changes in the messages that TF emits.
Several functions have an optional `silent` parameter
by which you could control the verbosity of TF.

That parameter now accepts different values, although the old
values still work with nearly the same effect.

The default value for silent results in slightly terser
behaviour than the previous default setting.

See `tf.core.timestamp.Timestamp`.

## 10.2.0

2022-08-18

The `tf.app.use` function has an extra optional parameter `loadData=True`
by which you can prevent data loading.
That is useful if you want to inspect properties of a dataset without
the costly loading of much data.

There is a new function to get existing volumes in a dataset:
`tf.volumes.extract.getVolumes()`.
It is also available as methods on the `tf.advanced.app.App` and `tf.fabric.Fabric` objects
so you can also say `TF.getVolumes()` and `A.getVolumes()`.

Improvements in the function `tf.volumes.extract.extract()`:

*   its third argument (`volumes`) is replaced from a positional
    argument into a keyword argument with default value `True`.
*   Fixed a bug in reporting results 

Improvement in the function `tf.volumes.collect.collect()`:

*   Fixed a crash that occurred while executing this function under certain conditions

## 10.2

## 10.1.0

2022-07-13

Addition of a module `tf.convert.variants` that can be used in a `tf.convert.walker` conversion.
It can be used to process TEI app-lem-rdg elements (critical apparatus).
What it does for you is to create sentence-like nodes from sentence-boundary information.
It deals with the cases where variants have different sentence boundaries.

Some minor fixes in defaults and documentation.

## 10.1

## 10.0.4

2022-07-04

Addition to the `tf.convert.walker` api: `cv.link()` to manually link a node 
to existing slots instead of relying on the automatic linking.

## 10.0.3

2022-06-22

Bug fix in the Text-Fabric browser.
Spotted by Jorik Groen.

The Text-Fabric browser was not able to download data correctly, because
it communicated the name of the backend incorrectly to the TF-kernel.

## 10.0.2

2022-06-20

It is now also possible to have datasets and modules of datasets coming 
from different backends.

Refactoring:

*   ditched the word `host`. Used `backend` instead.
*   the `~/text-fabric-data` cache dir now first has a layer of subdirectories
    according to the backend that the data comes from: `github`, `gitlab` and
    whatever server is serving a GitLab instance.
*   subfolder download for GitLab is supported if the gitlab backend supports it.
    If not, we fall back on downloading the whole repo and then discarding what we
    do not need. Gitlabs with versions at least 14.4.0 support downloading of subfolders.

## 10.0.1

2022-06-17

Small fix. GitLab.com supports downloading of subfolders,
and I am prepared to make use of that
but the current python-gitlab module does not support that part of the API.
So I work around it.

## 10.0.0

2022-06-17

**Additions**

*Backend support*: see `tf.advanced.repo.checkoutRepo()` and `tf.advanced.app.App`.

A backend is an online repository where TF apps/data can be stored.

Up till now, Text-Fabric worked with a single backend: **GitHub**.
It uses the API of GitHub to find releases and commits and to download
required data on demand.

With this version, Text-Fabric can also talk to GitLab instances.

The most prominent calls on the backend are the `use()` function
and the start of the Text-Fabric browser.

They will work with a GitLab backend if you pass the instance address
with the optional parameter `backend`:

``` python
A = use("annotation/banks", backend="gitlab.huc.knaw.nl")
```

or

``` python
A = use("annotation/banks", backend="gitlab.com")
```

In the Text-Fabric browser that looks as follows:

``` sh
text-fabric annotation/banks --backend=gitlab.huc.knaw.nl
```

or
``` sh
text-fabric annotation/banks --backend=gitlab.com
```

When `backend` is omitted or is `None`, the backend defaults to `github`.

**Limitations**

GitLab does not support Jupyter Notebooks.
And even if you converted them to HTML, GitLab does not offer a rendered view on HTML pages,
unless you use GitLab Pages.

But that is not always enabled.

Currently, Text-Fabric does not support publishing to GitLab pages,
although everything up to building a Pages site is supported.

When on a closed on-premise installation of GitLab, there is no way to
see rendered notebooks on NBViewer, simply because NBViewer has no access
to the shielded notebooks.

## 10.0

---

## Older releases

See `tf.about.releasesold`.

