![tf](../images/tf-small.png)

# Changes in this major version

???+ hint "Consult the tutorials after changes"
    When we change the API, we make sure that the tutorials shows off
    all possibilities.

    See the app-specific tutorials in [annotation]({{an}}).

## Queued for next release

See the [issue list on GitHub]({{ghissues}})

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
[exportExcel]({{an}}/app-bhsa/blob/master/tutorial/exportExcel.ipynb)

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
      **[display tutorial]({{an}}/app-bhsa/blob/master/tutorial/display.ipynb)**
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

Quick start: the new [share]({{an}}/app-bhsa/blob/master/tutorial/share.ipynb)

See the [v7 guide](../Use/Use7.md) for concrete and detailed hints how to make most of this version.

