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

#### 13.0.18

2025-12-04

Small fix.

#### 13.0.17

2025-11-10

Small fixes

#### 13.0.15-16

2025-10-16

Performance of writing precomputed TF data to disk in suddenly decreased with a
factor 3.
The culprit turned out to be the pickletools.optimize function in the standard library.
It turns out that this optimization does not help much, so I left it out.
Also in 3.13 this optimize function had a significant performance penalty.
Without it, expect much shorter load times for data that is loaded into TF
for the first time.

Update: although the performance drop manifested itself in the optimize function
of pickletools, the real culprit is the garbage collector. If we switch it off
during feature computation and loading, there is no performance drop at all, and
it appears that Python 3.14 is just a bit faster than Python 3.13.

So we keep the garbage collector swithced off during loading and dumping features,
but we still do not use the optimize function.

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

