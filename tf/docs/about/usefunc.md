## Summary

The function `tf.app.use` lets you make use of a corpus
in the same way as the `use` statements in MySQL and MongoDb let you
make use of a database.
It loads the features of a corpus plus extra modules, it loads the
Text-Fabric app or a customization of it, and makes it all available in an
API.
If any of the above mentioned ingredients is not locally available on your
computer, it will auto-download it, subject to checkout specifiers that you
provide.

### Basic usage:

```
A = use("org/repo")
```

or

```
A = use("org/repo:specapp", checkout="specdata")
```

See `tf.about.corpora` for a list of known corpora that can be loaded this way.

### Full usage

```
A = use(
    "org/repo:specapp",
    checkout=None, # e.g. "latest"
    version=None,  # e.g. "1.2.3"
    mod=None,      # e.g. "org1/repo1/path1:specmod1,org2/repo2/path2:specmod2"
    setFile=None,  # e.g. "path/to/file"
    legacy=False,
    hoist=globals(),
    locations=None,
    modules=None,
    volume=None,
    collection=None,
    silent=False,
    **configOverrides,
)
```

### Legacy usage:

```
A = use("corpus")
```

or

```
A = use("corpus", legacy=True)
```

## Security

!!! caution "Security warning"
    Text-Fabric apps may be downloaded from GitHub and then
    imported as a module and then *executed*.

    Do you trust the downloaded code?
    Make sure you know the repository where the code comes from, and the people
    who own the repository.

!!! note "Security note"
    Text-Fabric data maybe downloaded from arbitrary repositories on GitHub,
    but the downloaded material will be read as *data* and not executed as code.

## Details

When loading a corpus via this method, most of the features in view will
be loaded and made available.
However, some Text-Fabric apps may exclude some features from being
automatically loaded.
And in general, features whose names start with `omap@` will not be
automatically loaded.
Any of these features can be loaded on demand later by means of
`tf.advanced.app.App.load()`.

During start-up the following happens:

1.  the corpus data may be downloaded to your
    `~/text-fabric-data` directory,
    if not already present there;
2.  if your data has been freshly downloaded,
    a series of optimizations is executed;
3.  most features of the corpus are loaded into memory.
4.  the data is inspected to derive configuration information for the
    advanced API; if present, additional settings, code and styling is loaded.

## Loading

Loading a corpus consists of 2 separate steps:

1. load the *app* of the corpus (config setting, static material, python code)
2. load the *data* of the corpus.

Both items can be specified independently, in terms of where they reside
locally or online.
Such a specification consists of a *path* and a *checkout specifier*.
The *path* part looks like a directory, and specifies a location inside
a repository, e.g. `etcbc/bhsa`.
The *checkout specifier* part is a keyword:

*   `local` under your local directory `~/text-fabric-data`
*   `clone` under your local directory `~/github`
*   `latest` under the latest release, to be checked with online GitHub
*   `hot` under the latest commit, to be checked with online GitHub
*   `v1.2.3` under release `v1.2.3`, to be fetched from online GitHub
*   `123aef` under commit `123aef`, to be fetched from online GitHub
*   *absent* under your local directory `~/text-fabric-data` if present,
    otherwise the latest release on GitHub, if present, otherwise the latest commit on GitHub

For a demo, see
[banks/repo](https://nbviewer.jupyter.org/github/annotation/banks/blob/master/tutorial/repo.ipynb).

## Specifying app and/or data

The specification of the app is in the first argument:
*app-path*`:`*app-checkout-specifier*
The normal case is where *app-path* has the form `org/repo` pointing to
a repository that holds the corpus, both app and data.
If we find an app under *app-path*, it will have information about where the data is, so the
*data-path* is known. The *data-checkout-specifier* is passed as an optiona argument:
`checkout=`*data-checkout-specifier*.

So far we have described how to use a TF corpus which has an `app` inside in the
standard location, i.e. as org/repo/`app` .
But app and data may also reside in arbitrary places, and for that there
is additional syntax in the first argument:

*   `app:full/path/to/tf/app`
    **Specify the location of the app**.
    You may not append a *checkout specifier* to this.

*   `data:full/path/to/tf/data/version`
    **Do not try to find an app, but point to the data instead**
    (a generic TF app with default settings will be used).
    You may pass a *checkout specifier* by appending `:`*xxx*.

*   *corpus*
    **legacy way of calling an app by its name only**.
    Find a TF app in repo `annotation/app-`*corpus*.

    Without `legacy=True`,
    you get a warning, and TF assumes the TF app has been migrated
    from annotation/app-corpus to org/repo/app, and it loads the app from there.

    If you pass `legacy=True` you do not get that warning, and TF loads
    the app from annotation/app-corpus.

    You have to use this if you go back in the history to times where
    the legacy method was the only method of loading a corpus.
    The older history of the app is preserved in annotation/app-corpus,
    but not in the migrated org/repo/app.

## Versions

Text-Fabric expects that the data resides in version directories.
The configuration of a TF-app specifies which version will be used.
You can override that by passing
the optional argument `version="x.y.z"`.
Where we do not have a TF-app that specifies the version,
i.e. if you pass a `data:path/to/tf/data` string
you must either:

*   specify the paths so that they include the version directory
*   specify the path to the parent of the version directories
    and pass `version="x.y.z"`

!!! caution "Modules"
    If you also ask for extra data modules by means of the `mod` argument,
    then the corresponding version of those modules will be chosen.
    Every properly designed data module must refer to a specific
    version of the main source!

## Modules and sets

Besides the main corpus data, you can also draw in other data.

### Modules

They are typically sets of features provides by others to enrich or comment
the main corpus.
A module is specified in much the same way as the main corpus data.
The optional **mod** argument is a comma-separated list
or an iterable of modules in one of the forms

```
{org}/{repo}/{path}
```

or

```
{org}/{repo}/{path}:data-checkout-specifier
```

All features of all those modules will be loaded.
If they are not yet present, they will be downloaded from GitHub first.
For example, there is an easter egg module on GitHub,
and you can obtain it by

```
mod='etcbc/lingo/easter/tf'
```

Here the `{org}` is `etcbc`, the `{repo}` is `lingo`,
and the `{path}` is `easter/tf` under which
version `c` of the feature `egg`
is available in TF format.
You can point to any such directory om the entire GitHub
if you know that it contains relevant features.

Your TF app might be configured to download specific modules.
See `moduleSpecs` in the app's `config.yaml` file.
If you need these specific module with a different checkout specifier,
you can override those by passing those modules in this parameter
explicitly.

!!! hint
    This is needed for example if you specify a specific release
    for the core data module. The associated standard modules probably
    do not have that exact same release, so you have to look up their
    releases in Github, and attach the release numbers found
    to the module specifiers.

!!! caution "Let TF manage your text-fabric-data directory"
    It is better not to fiddle with your `~/text-fabric-data` directory
    manually. Let it be filled with auto-downloaded data.
    You can then delete data sources and modules when needed,
    and have them redownloaded at your wish,
    without any hassle or data loss.

### Sets

They are named nodesets, that, when imported, can be used in
[search templates](https://annotation.github.io/text-fabric/tf/about/searchusage.html#simple-indent-nameotype-or-set-features)
as if they were node types.
You can construct them in a Python program and then write them to disk
with `tf.lib.writeSets`. 
When you pass that file path with `setFile=path/to/file`,
the named sets will be loaded by Text-Fabric.

See also `tf.search.search.Search.search` and `tf.lib.readSets`.

## Overrides

Sometimes you need to deviate from settings that have been specified in the TF app
that you invoke. Or you want to set things explicitly when you do not invoke
a TF app.
You can prepare a dictionary of such settings, say `configOverrides`,
and pass the contents as keyword arguments: `**configOverrides`.
The list of possible settings is spelled out in
`tf.advanced.settings`.

!!! hint "Corpus has moved"
    Suppose you want to work with an older version of the corpus.
    A complication occurs if the repo has been renamed and/or moved
    to an other organization.
    When you go back in the history and download an older version of the app,
    its configuration settings specify a different org, repo and relative path
    than what is currently the case. Here the possibility to override settings
    come to the rescue.

    A good example is in
    [clariah/wp6-missieven](https://nbviewer.org/github/clariah/wp6-missieven/blob/master/tutorial/annotate.ipynb)
    which resided in annotation/clariah-gm before, and in Dans-labs/clariah-gm even earlier.

    When we want to migrate manual annotations made against the 0.4 version to the 0.7
    version, we run into this issue.
    But we can still load the 0.4 version by means of

    ```
    A = use(
        "missieven:v0.4",
        checkout="clone",
        version="0.4",
        hoist=globals(),
        legacy=True,
        provenanceSpec=dict(org="clariah", repo="wp6-missieven"),
    )
    ```

## Hoisting

The result of `A = use()` is that the variable `A` holds an object,
the TF-app, loaded in memory, offering an API to the corpus data.
You get that API by `api = A.api`, and then you have access to the particular members
such as

* `F = api.F` (see `tf.core.nodefeature.NodeFeature`)
* `L = api.L` (see `tf.core.locality.Locality`)
* `T = api.T` (see `tf.core.text.Text`)
* `TF = api.TF` (see `tf.core.fabric.FabricCore`)

If you work with one corpus in a notebook, this gets cumbersome.
You can inject the global variables `F`, `L`, `T`, `TF` and a few others
directly into your program by passing `hoist=globals()`.
See the output for a list wof the new globals that you have got this way.
Do not do this if you work with several corpora or several versions of a corpus
in the same program!

## Volumes and collections

Instead of loading a whole corpus, you can also load individual volumes
or collections of individual volumes of it.
If your work is confined to a volume or collection, it might pay off
to load only the relevant pieces of the corpus.
Text-Fabric will maintain the details of the relationship between the parts
and the whole.

!!! caution "Volumes and collections"
    It is an error to load a volume as a collection and vice-versa

    You get a warning if you pass both a volume and a collection.
    The collection takes precedence, and the volume is ignored in that case.

### Volumes

If you pass `volume=volume-heading`
TF will load a single volume of
the work, specified by its heading.
The volume is stored in a directory with `.tf` files,
located under the directory `_local` which is in the
same directory as the `.tf` files of the work.
See `tf.about.volumes`.

### Collections

If you pass `collection="collection-name"`
TF will load a single named collection of volumes of the work.
The collection is stored in a directory with `.tf` files,
located under the directory `_local` which is in the
same directory as the `.tf` files of the work.
See `tf.about.volumes`.

## Lower level

### locations, modules

You can add other directories that TF will search for feature files.
They can be passed with the `locations` and `modules` optional parameters.
For the precise meaning of these parameters see `tf.core.fabric.FabricCore`.

!!! note "More, not less"
    Using these arguments will load features on top of the
    default selection of features.
    You cannot use these arguments to prevent features from being loaded.
    Read on to see how you can achieve the loading of fewer features.


### api

So far, `A = use()` will construct an advanced API with a more or less standard set of features
loaded, and make that API avaible to you, under `A.api`.
But you can also setup a core API yourself by usin the lower level method
`tf.core.fabric.FabricCore` with your choice of locations and modules:

```
from tf.fabric import Fabric
TF = Fabric(locations=..., modules=...)
api = TF.load(features)
```

Here you have full control over what you load and what not.
If you want the extra power of the TF app, you can wrap this `api`:

```
A = use("org/repo", api=api)`
```

or

```
A = use("app:path/to/app", api=api)`
```

etc.

!!! hint "Unloaded features"
    Some apps do not load all available features of the corpus by default.

    This happens when a corpus contains quite a number of features
    that most people never need.
    Loading them cost time and takes a lot of RAM.

    In the case where you need an available feature
    that has not been loaded, you can load it by demanding

       TF.load('feature1 feature2', add=True)`

    provided you have used the `hoist=globals()` parameter earlier.
    If not, you have to say

       A.api.TF.load('feature1 feature2', add=True)`

## Silence

Loading a corpus can be quite noisy in the output.
You can reduce that by means of the `slient` paramenter.
If `True`, nearly all output of this call will be suppressed,
including the links to the loaded data, features, and the API methods.
Error messages will still come through.
If `deep`, all output will be suppressed, except errors.
