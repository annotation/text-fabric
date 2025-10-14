# Release notes

!!! hint "Consult the tutorials after changes"
    When we change the API, we make sure that the tutorials show off
    all possibilities.

See the app-specific tutorials via `tf.about.corpora`.

---

## 13

This major update has a few small fixes and adds nothing, but it deletes a lot.
All functions having to do with XML conversion have been moved out of Text-Fabric,
into a new package,
[Text-Fabric-Factory](https://github.com/annotation/text-fabric),
which kan be pip installed separately.

### 13.0

#### 13.0.14

2025-10-14

Fixed an exception when starting TF if the library marimo has been uninstalled.
(It seems that the removal of marimo by pip is not complete).

#### 13.0.13

2025-09-04

Moved text-fabric back to github.com/annotation

#### 13.0.12

2025-09-01

Moved the text-fabric repo to gitlab.huc.knaw.nl, but that was unwise.
This release has been yanked, you should not install this one.

#### 13.0.11

2025-08-05

Fixed a bug introduced by the previous release.

#### 13.0.8-10

2025-07-16

When using `tf.app.use()` and specifying the corpus with `app:` + path to the
`app` directory of the corpus, loading failed because a leading `/` got removed
somewhere. This removal is functional when loading most modules, but not when
loading the main module. A condition to that effect was added.

#### 13.0.7

2025-07-06

A fix in pretty displays: if you passed the parameter `extraFeatures`, those
extra features did not show up in all cases, and one of the ways to let them show
up was to set `standardFeatures=True`. But that should not be necessary, and in fact
this was a bug. It has been fixed.

Thanks to Tony Jurg for
[reporting](https://github.com/tonyjurg/test/blob/main/test.ipynb)
this.

#### 13.0.1-6

2025-03-18

GitLab backends: downloading deeper-than-toplevel subfolders from a repo led to
a wrong directory structure of the downloaded files. This has been fixed.

#### 13.0.0

2025-03-18

The place where the downloader thinks the `text-fabric-data` directory is,
is in fact a parameter, but only the module `tf.advanced.repo` used it.
Now you can also pass it to the `use()` command in `tf.app`

This is needed when you drive TF programmatically in contexts where your
home directory is not the best place for it.
For example in conversion pipelines with multiple projects.

