# Release notes

!!! hint "Consult the tutorials after changes"
    When we change the API, we make sure that the tutorials show off
    all possibilities.

See the app-specific tutorials via `tf.about.corpora`.

---

## 10

## 10.0

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

---

## Older releases

See `tf.about.releasesold`.

