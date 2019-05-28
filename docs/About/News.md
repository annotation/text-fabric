![tf](../images/tf-small.png)

# Changes in this major version

???+ hint "Consult the tutorials after changes"
    When we change the API, we make sure that the tutorials shows off
    all possibilities.

    See the app-specific tutorials in [annotation]({{tutnbt}}).

???+ hint "Auto-update"
    When TF apps have been updated, they will be autoloaded to the newest version
    provided you call the app as follows:

    In a program:
    
    ```python
    use('appName', ... )
    ```

    Calling the browser

    ```
    text-fabric appName
    ```

    This will get you the newest stable version.
    To get the newest unstable version:

    ```python
    use('appName:hot', ...)
    ```

    ```
    text-fabric appName:hot
    ```

See the [issue list on GitHub]({{ghissues}})

### Queued for next release

*   New tf.compose package with operators to manipulate TF data sets: combine,
    add/remove node types, etc.
*   New TF.loadAll() function to load all features in one go.

---

# 7.7.11

2019-05-27

Small fixes:

*   tweaks in edge spinning (part of the search engine), but no real performance improvements
*   nothing in TF relies on Python's `glob` module anymore, which turned out to miss
    file names with characters such as `[ ]` in it.

# 7.7.10

2019-05-23

Fixed a bug in fabric.py spotted by Ernst Boogert, where there was
a confusion between `sections` and `structure`

If a TF-app needs to import its own modules, there is the risk of conflicts
when several TF-apps get loaded in the same program and they import modules
with the same name.
TF offers a function
[`loadModule()`](../Implementation/Apps.md#components)
by which an app can dynamically load
a module, and this function makes sure that the imported module gets
an app-dependent internal name.

## 7.7.9

2019-05-21

Some queries perform much better now.
Especially the ones with `==` (same slots), `&&` (overlapping slots), and
`::` (same boundaries).

The performance of the machinery has been tuned with new parameters, and all BHSA
queries in the tutorials have been tested.

There was a pair of queries in
[searchGaps]({{tutnb}}/bhsa/searchGaps.ipynb)
that
either took 9 seconds or 40, randomly. Now it is consistently 9 seconds.

See
[searchRough]({{tutnb}}/bhsa/searchRough.ipynb)
at the end where the performance parameters are tweaked.

## 7.7.6-8

2019-05-20

New functions
`cv.active()`
and
`cv.activeTypes()`
in the walker conversion (requested by Ernst Boogert). 

## 7.7.5

2019-05-18

Another 20% of the original memory footprint has been shaved off.
Method: using arrays instead of tuples for sequences of integers.

## 7.7.4

2019-05-16

Optimization: the memory footprint of the features has been reduced by ca 30%.
Method: reusing readonly objects with the same value.

The BHSA now needs 2.2 GB of RAM, instead of the 3.4 before.

Bug fixes:
*   silent means silent again in `A.use()`
*   the walk converter will not stop if there is no structure configured

## 7.7.3

2019-05-13

Added more checks for the new structure API when using the walk converter.
Made the pre-computing for structure more robust.

## 7.7.2

2019-05-12

The `T` API has been extended with *structure types*.
Structure types is a flexible sectioning system with unlimited levels.
It can be configured next to the more rigid sections that `T` already supported.

The rigid system is meant to be used by the TF browser for chunking up the material
in decent portions.

The new, flexible system is meant to reflect the structure of the corpus, and will
give you means to navigate the copus accordingly.

Quick examples: [banks]({{tfbanks}}/programs/structure.ipynb).
Documentation: [structure](../Api/Text.md#structure). 

## 7.7.1

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

## 7.7.0

2019-05-08

Big improvement on `T.text()`.
It now accepts one or more nodes of arbitrary types and produces text
for them all.

Largely backward compatible, in that:

*   it takes the same arguments
*   when it produced sensisble results, it will produce the same results
*   when it produced nothing, it will now produce sensible things, in many cases.

You have to use the `descend` parameter a lot less.

See the [docs](../Api/Text.md#text-representation)

## 7.6.8

2019-05-02

There is an extra `cv.occurs()` function to check whether a feature actually
occurs in the result data.

`cv.meta(feature)` without more arguments deletes the feature from the metadata,

## 7.6.7

2019-04-27

Added the option `force=True` to the `cv.walk()` function,
to continue conversion after errors.

## 7.6.5-6

2019-04-26

Added punctation geresh and gershayim to the Hebrew mapping from unicode to ETCBC transcription.
The ETCBC transcription only mapped the *accents* but not the *punctuation* characters of these.

Fixed a bug in `cv.meta()` in the conversion walker.

## 7.6.4

2019-04-25

The walker conversion module has an extra check: if you assign features to None,
it will be reported.

There is an extra `cv.meta()` function to accomodate a use case brought in by
Ernst Boogert.

## 7.6.3

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

See the [docs](../Use/Search.md#relational-operators)

This corresponds to
[`E.`*edgeFeature*`.b()`](../Api/Features.md#edge-features).

See also the
[Banks example]({{tutnb}}/banks/app.ipynb).

## 7.6.2

2019-04-12

Small but important fix in the display logic of the `pretty()` function.
The bug is not in the particular TF-apps that partly implementt `pretty()`,
but in the generic `tf.applib.display` library that implements the other part.

Thanks to Gyusang Jin, Christiaan Erwich and Cody Kingham for spottting it.

I wrote an account of the bug and its fixing in this 
[notebook]({{tfnb}}/test/fixing/Ps18-49.ipynb).

## 7.6.1

2019-04-10

Small fix in reporting of the location of data being used.

## 7.6

2019-04-09

Simplified sharing: pushing to GitHub is enough.
It is still recommended to make a release on GitHub now and them,
but it is not necessary.

The `use()` function and the calling of the TF browser undergo an API change.

### API addition:

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

Or consult the [repo]({{tutnb}}/banks/repo.ipynb) notebook.

### API deletion (backwards incompatible):

The parameters `check=...` and `lgc=...` of `use()` and `-lgc` and `-c` when
calling the TF browser have been removed.

These parameters were all-or-nothing, they were applied TF app code, main data,
and included data modules.

### Advice

In most cases, just do not use the checkout parameters at all.
Then the TF-app will be kept updated, and you keep using the newest data.

If you want to producing fixed output, not influenced by future changes,
run TF once with a particular version or commit,
and after that supply the value `local` as long as you wish.

If you are developing data yourself, place the data in your repository
under `~/github`, and use the value `clone` for checkout.

### Sharing

If you create your own features and want to share them, it is no longer needed
to zip the data and attach it to a newly created release on GitHub.
Just pushing your repo to GitHub is sufficient.

Still it is a good practice to make a release every now and then.

Even then, you do not need to attach your data as a binary.
But, if you have much data or many files, doing so makes the downloading
more efficient for the users.

### `checkoutRepo()`

There is a new utility function `checkoutRepo()`, by which you can
maintain a local copy of any subdirectory of any repo on Github.

See [Repo](../Api/Repo.md)

This is yet another step in making your scholarly work reproducible.

### Fix in query parsing

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

## 7.5.4

2019-03-28

The TF browser now displays the total number of results clearly.

## 7.5.3

2019-03-27

Small fix in Excel export when called by the TF kernel.

## 7.5.2

2019-03-26

Small fix: a TF app that did not define its own text-formats caused an error.
Now the generic TF applib is robust against this.

## 7.5.1

2019-03-14

Modified `E.feature.b()` so that it gives precedence to outgoing edges.

Further tweaks in layout of `plain()`.

## 7.5

2019-03-13

API addition for `E` (edges):
[`E.feature.b()`](https://annotation.github.io/text-fabric/Api/Features/#edge-features)
gives the symmetrical closure
of the edges under `feature`. That means it combines the results of
`E.feature.f()` and `E.feature.t()`.
In plain speech: `E.feature.b(m)` collects the nodes
that have an incoming edge from `m` and the nodes that have an outgoing edge to `m`.

## 7.4.11

2019-03-11

* `TF.save()`an now write to any absolute location by means of the
  optional parameter `location`.

## 7.4.10

2019-03-10

* The markdown display in online notebooks showed many spurious `</span>`.
  This is a bug in the Markdown renderer used by Github and NBViewer.
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

## 7.4.9

2019-03-08

* Changes in font handling
* New flag in `pretty()`: `full=False`.
  See the [docs](../Api/App.md#display)

## 7.4.8

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

## 7.4.7

2019-02-28

When converting a new corpus, Old Babylonian Letters (cuneiform),
I tuned the conversion module a bit.
Several improvements in the conversion program.
Better warnings for potential problems.
Several other small changes have been applied here and there.

## 7.4.6

2019-02-07

When querying integer valued features with inequality conditions, such as 

```
word level>0
```

an unpleasant error was raised if not all words have a level, or if some words have level `None`.

That has been fixed now.

Missing values and `None` values always cause the `>` and `<` comparisons to be `False`. 

## 7.4.5

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

## 7.4.4

2019-01-30

Added checks to the converter for section structure.

## 7.4.3

2019-01-30

A much simpler implementation of conversions from source data to Text-Fabric.
Especially the code that the conversion writer has to produce is simplified.

## 7.4.1-2

2019-01-29

Small fixes in the token converter.

## 7.4

2019-01-25

Easier conversion of data sources to TF: via an intermediate token stream.
For more info: see [#38]({{ghissues}}/45) 


## 7.3.14-15

2019-01-16

Make sure it works.

## 7.3.13

2019-01-16

Feature display within pretty displays: a newline in a feature value will cause a line break
in the display, by means of a `<br/>` element.

## 7.3.12

2019-01-16

Small fix in oslots validation.
You can save a data set without the oslots feature (a module).
The previous release wrongly flagged a oslots validation error because of a missing
oslots feature. 

That has been remedied.

## 7.3.11

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

## 7.3.10

2019-01-10

Moved the app tutorials from the annotation/app-appName repos into a new
annotation/tutorials repo.

The reason: the app-appName are used for downloading the app code.
It should not be burdened with extra material, which is also often updated,
giving rise to many spurious redownloads of the app code.

Additionally, for education purposes it is handy to have the tutorials for all apps inside
one repo. 
For example, to use in a Microsoft Azure environment.

## 7.3.9

2019-01-09

Better browsing for corpora with very many top level sections, such as Uruk.

For more info: see [#38]({{ghissues}}/36) 

## 7.3.8

2019-01-07

Small fix.

## 7.3.7

2019-01-07

Small fixes in the core: the Text API can now work with corpora with only two levels
of sections, such as the Quran.

## 7.3.6

2019-01-04

Arabic transcription functions

## 7.3.5

2018-12-19

TF-browser: Fixed a performance bottleneck in showing passages.
The computation of the highlights took too much time
if the query in question has many results.

## 7.3.4

2018-12-18

In the `plain()` representation NBconvert has a glitch.
We can prevent that by directly outputting the plain representation as HTML,
instead of going through Markdown.
Fixed that.

## 7.3.3

2018-12-17

The TF browser could not fiund its templates, because I had forgotten
to include the template files in the Python package.
(More precisely, I had renamed the templates folder from `views`, which was included,
to `templates`, and I had forgotten to adapt the `MANIFEST.in` file).

## 7.3.1

2018-12-14

Glitch in the Uruk app: it imports other modules, but because of the 
dynamic way it is imported itself, a trick is needed to
let it import its submodules correctly.


2018-12-13

## 7.3

2018-12-13

* Text-Fabric has moved house from `Dans-labs` to `annotation` on GitHub.
* The TF-apps have been moved to separate repos with name `app-`*xxxx*
  within [annotation]({{an}})
* The tutorials have been moved from the repos that store the corpus data
  to the `app`-*xxxx* repositories.

## 7.2.3

2018-12-13

The TF-browser exports an Excel export of results.
Now you can also export to Excel from a notebook,
using `A.export(results)`.

Jump to the tutorial:
[exportExcel]({{tutnb}}/bhsa/exportExcel.ipynb)

For more info: see [#38]({{ghissues}}/38) 

## 7.2.2

2018-12-12

??? abstract "Web framework: Bottle => Flask"
    The dependency on
    [Bottle]({{bottle}})
    as webserver has been replaced by
    [Flask]({{flask}})
    because Bottle is lagging behind in support for Python 3.7.

??? abstract "Plain display in Uruk"
    The plain display of lines and cases now outputs their ATF source,
    instead of merely `line 1` or `case a`.

??? abstract "Further code reorganization
    Most Python files are now less than 200 lines, although there is still
    a code file of more than 1000 lines.

## 7.2.1

2018-12-10

* Fix broken links to the documentation of the TF API members, after the incantation.
* Fix in the Uruk lineart option: it could not be un-checked.

## 7.2

2018-12-08

??? abstract "TF Browser"
    * The TF kernel/server/website is also fit to be served over the internet
    * There is query result highlighting in passage view (like in SHEBANQ)
    * Various tweaks

??? abstract "TF app API"
    * `prettySetup()` has been replaced with `displaySetup()` and `displayReset()`,
      by which
      you can configure a whole bunch of display parameters selectively.
      **[Display](../Api/App.md#display)**
    * All display functions (`pretty plain prettyTuple plainTuple show table`)
      accept a new optional parameter `withPassage`
      which will add a section label to the display.
      This parameter can be regulated in `displaySetup`. 
      **[Display](../Api/App.md#display)**
    * `A.search()` accepts a new optional parameter: `sort=...`
      by which you can ask for
      canonically sorted results (`True`),
      custom sorted results (pass your onw key function),
      or unsorted results (`False`).
      **[A.search](../Api/App.md#search)**
    * New functions `A.nodeFromSectionStr()` and `A.sectionStrFromNode()`
      which give the passage string of any kind of node, if possible.
      **[Section support for apps](../Api/App.md#sections)**
    * The function `A.plain()` now responds to the `highlights` parameter:
      you can highlight material inside plain displays.
      **[A.plain](../Api/App.md#display)**
      and
      **[display tutorial]({{tutnb}}/bhsa/display.ipynb)**
    * New function `T.sectionTuple(n)` which gives the tuple of section nodes in which `n`
      is embedded
      **[T.sectionTuple](../Api/Text.md#sections)**
    * **Modified function `T.sectionFromNode(n, fillup=False)`**
      It used to give a tuple (section1, section2, section3), also for nodes of type
      section1 and section2 (like book and chapter). The new behaviour is the same if
      `fillup=True`. But if `fillup=False` (default), it returns a 1-tuple for
      section1 nodes and a 2-tuple for section2 nodes.
      **[T.sectionFromNode](../Api/Text.md#sections)**
    * New API member `sortKeyTuple` to sort tuples of nodes in the
      canonical ordering.
      **[sortKeyTuple](../Api/Nodes.md#navigating-nodes)**
    * The code to detect the file name and path of the script/notebook you are running in,
      is inherently brittle. It is unwise to base decisions on that.
      This code has been removed from TF.
      So TF no longer knows whether you are in a notebook or not.
      And it will no longer produce links to the online
      notebook on GitHub or NBViewer.
    * Various other fixes

??? abstract "Documentation"
    The entry points and paths from superficial to in-depth information have been
    adapted. Writing docs is an uphill battle.

??? abstract "Under the hood"
    As TF keeps growing, the need arises over and over again to reorganize the
    code, weed out duplicate pieces of near identical functionality, and abstract from
    concrete details to generic patterns.
    This release has seen a lot of that.

## 7.1.1

2018-11-21

* Queries in the TF browser are limited to three minutes, after that
  a graceful error message is shown.
* Other small fixes.

## 7.1

2018-11-19

* You can use custom sets in queries in the TF browser
* Reorganized the docs of the individual apps, took the common parts together
* New functions `writeSets` and `readSets` in `tf.lib`

## 7.0.3

2018-11-17

* In the BHSA, feature values on the atom-types and subphrases are now shown too, and that includes extra features
  from foreign data sets
* The feature listing after the incantation in a notebook now lists the loaded modules in a meaningful order.

## 7.0.2

2018-11-16

* Small fixes in `text-fabric-zip`
* Internal reorgnization of the code
* Documentation updates (but internal docs are still lagging behind)

## 7.0.1

2018-11-15

* Fixed messages and logic in finding data and checking for updates (thanks to feedback of Christian Høygaard-Jensen)
* Fixed issue #30
* Improved the doc links under features after the incantation.
* Typos in the documentation

## 7.0.0

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

Quick start: the new [share]({{tutnb}}/bhsa/share.ipynb)

See the [advanced guide](../Use/UseX.md)
for concrete and detailed hints how to make most of this version.

