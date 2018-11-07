![tf](images/tficon-small.png)

# Changes

???+ hint "Consult the tutorials after changes"
    When we change the API, we make sure that the tutorials shows off
    all possibilities:
    [bhsa](http://nbviewer.jupyter.org/github/etcbc/bhsa/blob/master/tutorial/start.ipynb)
    [peshitta](http://nbviewer.jupyter.org/github/etcbc/peshitta/blob/master/tutorial/start.ipynb)
    [syrnt](http://nbviewer.jupyter.org/github/etcbc/syrnt/blob/master/tutorial/start.ipynb)
    [cunei](http://nbviewer.jupyter.org/github/nino-cunei/tutorials/blob/master/start.ipynb)

## Queued for next release

## 6.4.5

2018-11-07

* Bug fix: Now TF can truly work if you do not have a feature `text.tf` in your dataset.
* Tests added for basic relations in search: all relations are rigorously tested, a few small bugs fixed.
* The comment sign in queries is now `%`, only at the start of a line.

## 6.4.3-4

2018-11-06

Big bug fix in queries: basic relationships in combination with custom sets.
The implementation of the basic relationships did not reckon with custom sets that contains both slot nodes
and non-slot nodes. And it did not trigger the right code when a custom set has only slot nodes.
That has been remedied. Some of the search tutorials have been expanded to include a number of these critical
cases. A more complete test suite outside the tutorials is still on my to do list.
Thanks to Cody Kingham for spotting and reporting this bug.

## 6.4, 6.4.1-2

2018-11-02

* A passage browsing interface that interacts with the search results. 
* The interface scrolls to the highlighted row.

Minor things:

* More refined warnings when you run out of memory
* TF checks whether you are running 64 bit Python. If not, a warning is issued.

## 6.3.2

2018-10-27

* Better documentation for installation of Text-Fabric on Ubuntu.
* Added new module requirements: ipykernel and notebook.

## 6.3.1

2018-10-24

An optional parameter `silent=False` has been added to the initialisation calls of the specific app APIs:
you can say now

```python
A = Bhsa(silent=True)
A = Cunei(silent=True)
A = Peshitta(silent=True)
A = Syrnt(silent=True)
```

and then all non-error messages will be suppressed.
If the underlying TF API needs to precompute data, it will still be shown, because this may cause an otherwise
unexpected delay.
Since this is a releatively rare case, and since this can be remedied by running the call again,
I leave this behaviour as it is.

## 6.3

2018-10-19

* Character tables for Hebrew abd Syriac, with links to them from the TF browser
* Better font handling
* In the `pretty` and `plain` functions you can pass a `fmt` parameter, to control the text representation
  (original script, transcription, phonetics)
* You can also control the text representation in the Text-Fabric browser.

## 6.2.2

2018-10-18

* Added ETCBC/WIT transcriptions to the SyrNT data source. Now both Peshitta
  and Syriac New Testament have ETCBC transcriptions.
* The older, rectangular logo makes place for the more crisp, circular one 

## 6.2.1

2018-10-17

* New app: Syrnt (Syriac New Testament. It works much like the Peshitta, but the SyrNT data
  has linguistic annotations at the word and lexeme levels.
  After this upgrade you can browse the SyrNT by saying `text-fabric syrnt` on the command line.

## 6.2

2018-10-16

* New app: Peshitta. It works much like the BHSA, but there is one big difference: the current Peshitta data
  does not have linguistic annotations. There are just books, chapters, verses and words.
  We expect to add lemmatizations of words shortly.
  After this upgrade you can browse the peshitta by saying `text-fabric peshitta` on the command line.
* Fixed a bug in exportMQL:
  when there are no enumerated values, do not write out an empty
  `CREATE ENUMERATION` statement to the MQL file. 

## 6.1

2018-10-12

* More precise provenance data when you export results from the Text-Fabric data;
* Under the hood reorganization of configuration data of apps like Bhsa and Cunei;
* App-specific parts of the code have moved to more generic parts: a big cleanup has performed;
* This will make it easier to add new apps.

## 6.0.7-8-9

2018-10-11

* Avoid computing the notebook name when the user passes a name for the notebook to `Cunei()` or `Bhsa()`.
  And when the computing needs to be done, all exceptions will be caught, because the code for determining
  the notebook name is brittle, and may crash if the Jupyter version does not match.
* Fixed the bug that the Bhsa and Cunei did not run properly outside a notebook or outside a github repo.
* In Bhsa and Cunei, the generated info after the incantation can be collapsed (features, API members).

## 6.0.6

2018-10-10

In the BHSA, the edge features are now shown too after the incantation.

If you hoist the API members into your namespace, you will get a list of hoisted names,
linked to the API documentation.

## 6.0.5

2018-10-09

When using BHSA and Cunei in a notebook, there is an even simpler incantation which auto downloads features.

In the BHSA it is shown which features are loaded, with direct links to the feature docs.

## 6.0.4

2018-10-09

When using BHSA and Cunei in a notebook, there is a simpler incantation which auto downloads features.

Some issues concerning paths in zipfiles of downloaded data have been solved.

## 6.0.3

Easier incantations for `Bhsa()` and `Cunei()`.

* It is no longer needed to pass the name of the notebook, but you can still do so: `name='mynotebook'`
* You can leave out the `api` argument in `Bhsa()`. Then you do not have to load features by means of `TF.load()`,
  `Bhsa()` will load a standard set of features, and if the BHSA data is missing, it will download them first.

The former ways of calling `Bhsa()` and `Cunei()` are still valid. Note that all arguments have become optional.

2018-10-08

The Text-Fabric browser will always print a banner with its name and version.
If you pass it the argument --help or -h or --version or -v it will show the relevant information
and stop executing.

## 6.0.2

2018-10-07

The Text-Fabric browser takes it data by default from `~/text-fabric-data`.
It will not check local github clones for data.

But if you pass the option `-lgc`, it will first check your local github clones.

So it you do nothing special, the TF browser always works with the auto-downloaded data.

## 6.0.1

2018-10-06

Not only the core BHSA data will auto load, also the related PHONO and PARALLELS data.
A new release has been made of the related data, and they are now in sync with the release of the core data.

If you use auto load already, you do not have to do anything.

But if you have the etcbc/phono and etcbc/parallels repos in your `~/github` folder, you should do 
a `git pull origin master` on those repos.

**N.B.**: I am contemplating to have the Text-Fabric browser always use data from `~/text-fabric-data` and no longer
from `~/github/etcbc`. Then the TF browser always controls its own data, and it will not occur that
the version of the TF browser is not compatible with the version of the TF data in your github repos, or that
the main data and the related data are out of synch.

The disadvantage is that if you have the github repos on your system, you get redundant data in `~/text-fabric-data`.
However, there is only one version kept in `~/text-fabric-data`, so this is not much.

## 6.0

2018-10-05

A big update with several changes:

###  API change:
`T.text()` has got more behaviours.

This change was needed for the Text-Fabric browser, in order to represent *lexemes* in exported files.

!!! hint "Showcase: BHSA dictionary"
    Here is how you can collect the BHSA lexemes in an Excel sheet.

    * [about.md](https://github.com/Dans-labs/text-fabric/blob/master/test/bhsa/bhsa-Dictionary/about.md)
    * [RESULTSX.tsv](https://github.com/Dans-labs/text-fabric/blob/master/test/bhsa/bhsa-Dictionary/RESULTSX.tsv)

It might also be handy for the programmers amongst you.
See the updated [API doc on T](/Api/General/#text-representation), expand the T.text() item.

### Auto update
The Text-Fabric browser checks if you are using the most recent release of the data.

### Font rendering
A font rendering issue in Safari 12 in macos Mojave prevented the use of Ezra SIL for Hebrew in notebooks.
We now work around this by relying on the distribution of Ezra SIL as webfont
in the [font library](https://fontlibrary.org).

### Additional small fixes.
Not worth telling.

!!! hint "update Text-Fabric"
    To update Text-Fabric itself to version 6.0, consult [Upgrade](/Install/#text-fabric).
    Perform this step first, because the new TF may download the new data for you.

!!! caution "Data update needed"
    In order to work successfully with the new `T.text()` function, you need a newer release (1.4) of the BHSA *data*.
    (In fact, only one line in one feature has changed (`otext.tf`).

Here is how you get the new data release:

#### Automatically
If previously your Text-Fabric browser has automatically downloaded the data for you, it will detect the new release
and download it automatically. You do not have to do anything, except increase your patience.
The download (24 MB) takes some time and after that Text-Fabric will precompute related data, which may take
a few minutes. This is a one-time-step after a data update.

#### Manually
If you have a clone of the BHSA repository, then go to that directory and say `git pull origin master`.
If you get error messages, then you have local changes in your local BHSA repository that conflict with
the github version. Probably you have run the tutorials in place. Best thing to do is:

* copy your BHSA tutorial directory to somehwere else;
* remove your local BHSA repository entirely;
* decide whether you really want the whole repo back (nearly 4 GB).

If not: you're done, and TF will download automatically the data it needs.

If you still need it: move one directory up (into the `etcbc` directory) and do `git clone https://github.com/ETCBC/bhsa`.

If you want to consult the tutorials, either:

* view them on [nbviewer](https://nbviewer.jupyter.org/github/etcbc/bhsa/tree/master/tutorial/); or
* run them in a directory outside the BHSA repo (where you have copied it a minute ago).

## 5.6.4

2018-10-04

Solved a font-rendering issue on Safari 12 (Macos Mojave): locally installed fonts, such as Ezra SIL are not being
honored. So I linked to a stylesheet of the [fontlibrary](https://fontlibrary.org) which has a webfont version of
Ezra SIL. That worked.

## 5.6.3

2018-10-04

Exported tab-separated files get extension `.tsv` instead of `.csv`, because then they render better in GitHub. 

## 5.6.2

2018-10-04

Small optimization.
More docs about reading and writing Excel compatible CSV files with Hebrew characters in it.

## 5.6.1

2018-10-04

Better exporting from TF browser: a good RESULTSX.tsv with results, sensibly augmented with information, directly openable
in Excel, even when non-latin unicode code characters are present .
All features that occur in the searchTemplate are drawn in into the RESULTSX.tsv, onto the nodes they filter.

An additonal feature filtering is now possible in searchTemplates: `feature*`. 
This acts as "no additional constraint", so it does not influence the result set.
But it will be picked up and used to add information into the RESULTSX.tsv.

## 5.5.25

2018-10-03

The Text-Fabric browser exports results as node lists and produces also a CONTEXT.tsv with all feature
values for all nodes in the results.
However, it does not contain full text representations of the nodes and it is also not possible to see in what verses
the nodes occur.

That has changed. The last column of CONTEXT.tsv contains the full text of a node.
And there are three columns at the beginning that contain the references to the sections the node is in.
For the BHSA that is the book, chapter and verse.

## 5.5.24

2018-09-25

BHSA app in Text-Fabric Browser: the book names on the verse pad should be the English book names.
That is now in the help texts, including a link to the list of English book names.

## 5.5.23

2018-09-21

Problem in use of `msgCache` in the search engine, which caused `fetch()` to fail in some cases. Fixed.

## 5.5.22

2018-09-13

Fix in left-to-right displays of extra features in `pretty()` displays in the BHSA.

## 5.5.21

2018-08-30

Bug fix in transcription.py w.r.t. to Syriac transcriptions.

## 5.5.20

2018-08-16

BHSA app: adjusted the color of the gloss attribute: darker.

## 5.5.19

2018-07-19

Fixed: when opening files for reading and writing for an export of a TF browser session: specify that
the encoding is `utf8`. 
This is needed on those windowses where the default encoding is something else, usually `cp1252`.

## 5.5.18

2018-07-19

No change, only in the build script.
This is a test whether after uploading to PyPi, users
can upgrade without using the `--no-cache-dir` in their
pip commands.

## 5.5.17

2018-07-19

The main functions in kernel and web can be passed arguments, instead that they always
read from sys.argv.

So that it can be used packaged apps.

## 5.5.16

2018-07-17

Extra option when starting up the text-fabric web interface: `-docker` to let the webserver
listen at `0.0.0.0` instead of `localhost`.

So that it can be used in a Docker container.

## 5.5.15

2018-07-16

Extra option when starting up the text-fabric web interface: `-noweb` to not start the web browser.

So that it can be used in a Docker container.

## 5.5.13-14

2018-07-12

Better error reporting of quantified queries.

## 5.5.12

2018-07-11

* Faster export of big csv lists.
* Tweaks in the web interface.
* Cleaner termination of processes.
* The concept *TF data server* is now called *TF kernel*

## 5.5.8-11

2018-07-10

* Better in catching out-of-memory errors.
* Prevents creation of corrupt compiled binary TF data.
* Prevents starting the webserver if the TF kernel fails to load.

## 5.5.7

2018-07-09

Optimization is export from TF browser.

## 5.5.6

2018-07-09

Better help display.

* The opened-state of help sections is remembered.
* You can open help next to an other open section in the sidebar.

## 5.5.5

2018-07-08

Crisper icon.

## 5.5.4

2018-07-6

Docs updated. Little bit of refactoring.

## 5.5.1-3

2018-07-4

In the TF browser, use a selection of all the features when working with the BHSA.
Otherwise in Windows you might run out of memory, even if you have 8GB RAM.

## 5.5

2018-07-4

Text-Fabric can download data for BHSA and Cunei. You do not have to clone github repositories for that.
The data downloaded by Text-Fabric ends up in `text-fabric-data` under your home directory.

## 5.4.5-7

2018-07-03

Experimenting with setuptools to get the text-fabric script working
on Windows.

## 5.4.4

2018-07-02

Added renaming/duplicating of jobs and change of directory.

## 5.4.3

2018-06-29

Small fixes in error reporting in search.

## 5.4.1-2

2018-06-28

Text-Fabric browser: at export a csv file with all results is created, and also a markdown file with metadata.

Small fixes.

## 5.4

2018-06-26

Improved interface and functionality of the text-fabric browser:

* you can save your work
* you can enter verse references and tablet P numbers
* there is help
* there is a side bar

???+ cautions "Docs not up to date"
    The API docs are not up-to-date: there are new functions in the Bhsa and Cunei APIs.
    The server/kernel/client apis are not completely spelled out.
    However, the help for the text-fabric browser is included in the interface itself.

## 5.3.3

2018-06-23

Small fix: command line args for text-fabric.

## 5.3.0-2

2018-06-22

??? abstract "Better process management"
    When the TF web interface is started, it cleans up remnant process that might get in the way otherwise.
    You can also say

    ```
    text-fabric -k
    ```

    to kill all remnant processes,
    or

    ```
    text-fabric -k datasource
    ```

    to kill the processes for a specific datasource only.

??? abstract "Manual node entry"
    You can enter nodes manually in the TF browser.
    Handy for quick inspection.
    You can click on the sequence number to
    append the node tuple of that row to the tuple input field.
    That way you can collect interesting results.

??? abstract "Name and Description"
    You can enter a name which will be used as title and file name during export.

    You can enter a description in Markdown.
    When you export your query, the description appears
    formatted on top.

??? abstract "Provenance"
    If you export a query, provenance is added, using DOIs.

??? abstract "Small fixes"
    No more blank pages due to double page breaks.

## 5.2.1

2018-06-21

* Added an `expand all` checkbox in the text-fabric browser,
  to expand all shown rows or to collapse them.
* Export function for search results in the text-fabric browser.
  What you see is what you get, 1 pretty display per page if you have
  the browser save it to pdf.
* Small tweaks

## 5.1

2018-06-21

When displaying results in condensed mode, you
can now choose the level of the container in which results are highlighted.
So far it was fixed to `verse` for the bhsa and `tablet` for cunei.

The docs are lagging behind!
But it is shown in the tutorials and you can observer it in the text-fabric browser.

## 5.0.1,2,3,4

2018-06-19

Addressed start-up problems.

## 5.0

2018-06-18

Built in webserver and client for local query running.
It is implemented for Bhsa and Cunei.

## 4.4.2,3

2018-06-13

New distribution method with setuptools.
Text-Fabric has now dependencies on modules rpyc and bottle,
because it contains a built-in TF kernel and webserver.

This website is still barely functional, though.

## 4.4.1

2018-06-10

Search API:

Escapes in regular expression search was buggy and convoluted.
If a feature value contains a `|` then in an RE you have to enter `\|` to match it.
But to have that work in a TF search, you needed to say `\\\|`. 

On the other hand, in the same case for `.` instead of `|`, you could just sat `\.`

In the new situation you do not have to double escape in REs anymore.
You can just say `\|` and `\.`.

## 4.4

2018-06-06

Search API:

S.search() accepts a new optional parameter: `withContext`.
It triggers the output of context information for nodes in the result tuples.

## 4.3.4, 4.3.5

2018-06-05

Search API:

The `/with/ /or/ /or/ /-/' quantifier is also allowed with zero `/or/` s.

Small fix in the `/with/` quantifier if there are quantifiers between this one and its parent atom.

## 4.3.3

2018-06-01

Search API:

Improved quantifiers in search: 

*   `/where/` `/have/` `/without/` `/with/` `/or/` `/-/`;
*   much clearer indentation rules (no caret anymore);
*   better reporting by `S.study()`.

## 4.3.2

2018-05-31

Search API: 

*   quantifiers may use the name `..` to refer to their parents
*   you may use names in the place of atoms, which lessens the need for constructs with `p = q`
*   stricter checks on the syntax and position of quantifiers

## 4.3.1

2018-05-30

Docs and metadata update

## 4.3.0

2018-05-30

*   API Change in Search.

    In search templates I recently added things like

    ```
      word vt!
    ```

    which checks for words that do not have a value for feature `vt`.

    The syntax for this has now changed to

    ```
      word vt#
    ```

*   Unequal (#) in feature value conditions.

    Now you can say things like

    ```
      word vt#infa|infc
    ```

    meaning that the value of feature is not one of `infa`, `infc`.

    So, in addition to `=` we have `#` for "not equal".
*   Quantifiers.

    You can now use quantifiers in search. One of them is like `NOTEXIST` in MQL.
    See the [docs](/Api#quantifiers)

*   A number of minor fixes.

## 4.2.1

2018-05-25

*   Several improvements in the pretty display in Bhsa and Cunei APIs
*   Under the hood changes in `S.search()` to prepare for *quantifiers* in search templates.

    *   Tokenisation of quantifiers already works
    *   Searches can now spawn auxiliary searches without polluting intermediate data
    *   This has been done by promoting the `S` API to a factory of search engines.
        By deafault, `S` creates and maintains a single factory, so to the user
        it is the same `S`. But when it needs to run a query in the middle of processing another query
        it can just spawn another search engine to do that, without interfering with the
        original search.

*   NB: the search tutorial for the Bhsa got too big. It has thoroughly been rewritten.

## 4.2

2018-05-23

The Search API has been extended:

*   you can use custom sets in your query templates
*   you can search in shallow mode: instead of full result tuples, you just get a set
    of the top-level thing you mention in your template.
    
This functionality is a precursor for
[quantifiers in search templates](https://github.com/Dans-labs/text-fabric/issues/4)
but is also a powerful addition to search in its own right.

## 4.1.2

2018-05-17

Bhsa and Cunei APIs:

*   custom highlight colours also work for condensed results.
*   you can pass the `highlights` parameter also to `show` and `prettyTuple`


## 4.1.1

2018-05-16

Bhsa API: you can customize the features that are shown in pretty displays.

## 4.1

2018-05-16

Bhsa and Cunei APIs: you can customize the highlighting of search results:

*   different colours for different parts of the results
*   you can choose your colours freely from all that CSS has to offer.

See the updated search tutorials.

## 4.0.3

2018-05-11

No changes, just quirks in the update process to get a new version of TF out.

## 4.0.1

2018-05-11

Documentation updates.

## 4.0.0

2018-05-11

*   Additions to Search.
    You can now include the values of edges in your search templates.
*   `F.`*feature*`.freqList()` accepts a new parameter: `nodeTypes`. It will restrict its results to nodes in
    one of the types in `nodeTypes`. 
*   You can now also do `E.`*feature*`.freqList()`.
    It will count the number of edges if the edge is declared to be without values, 
    or it will give a frequency list of the edges by value if the edge has values.
    Like `F.freqList`, you can pass parameters to constrain the frequency list to certain node types.
    You can constrain the node types from which the edges start (`nodeTypesFrom`) and where they arrive
    (`nodeTypesTo`).
*   New documentation system based on [MkDocs](https://mkdocs.readthedocs.io/en/stable/).

## 3.4.12

2018-05-02

The Cunei and Bhsa APIs show the version of Text-Fabric that is being called.

## 3.4.11

2018-05-01

Cunei

*   cases are divided horizontally and vertically, alternating with their
    nesting level;
*   cases have a feature **depth** now, indicating at which level of nesting they
    are.

## 3.4.8-9-10

2018-04-30

Various small fixes, such as:

*   Bhsa: Lexeme links in pretty displays.

*   Cunei: Prevented spurious `</div>` in NbViewer.

## 3.4.7

Cunei: Modified local image names

## 3.4.6

Small tweaks in search.

## 3.4.5

2018-04-28

Bhsa API:

*   new functions `plain()` and `table()` for plainly representing nodes, tuples
    and result lists, as opposed to the abundant representations by `pretty()` and
    `show()`.

## 3.4.4

2018-04-27

Cunei API:

*   new functions `plain()` and `table()` for plainly representing nodes, tuples
    and result lists, as opposed to the abundant representations by `pretty()` and
    `show()`.

## 3.4.2

2018-04-26

Better search documentation.

Cunei API: small fixes.

## 3.4.1

2018-04-25

Bhsa API:

*   Search/show: you can now show results condensed: i.e. a list of passages with
    highlighted results is returned. This is how SHEBANQ represents the results of
    a query. If you have two results in the same verse, with `condensed=True` you
    get one verse display with two highlights, with `condensed=False` you get two
    verse displays with one highlight each.

Cunei API:

*   Search/show: the `pretty`, `prettyTuple`, `show` functions of the Bhsa API
    have bee translated to the Cunei API. You can now get **very** pretty displays
    of search results.

## 3.4

2018-04-23

[Search](/Api#search):

*   You can use regular expressions to specify feature values in queries.
*   You could already search for nodes which have a non-None value for a certain
    feature. Now you can also search for the complement: nodes that do not have a
    certain feature.

Bhsa API:

The display of query results also works with lexeme nodes.

## 3.3.4

2018-04-20

Cunei API: Better height and width control for images. Leaner captions.

## 3.3.3

2018-04-19

Cunei API: `casesByLevel()` returns case nodes in corpus order.

## 3.3.2

2018-04-18

Change in the Cunei api reflecting that undivided lines have no cases now (was:
they had a single case with the same material as the line). Also: the feature
`fullNumber` on cases is now called `number`, and contains the full hierarchical
part leading to a case. There is an extra feature `terminal` on lines and cases
if they are not subdivided.

Changes in Cunei and Bhsa api:

*   fixed a bug that occurred when working outside a GitHub repository.

## 3.3.1

2018-04-18

Change in the Cunei api. `casesByLevel()` now takes an optional argument
`terminal` instead of `withChildren`, with opposite values.

`withChildren=False` is ambiguous: will it deliver only cases that have no
children (intended), or will it deliver cases and their children (understood,
but not intended).

`terminal=True`: delivers only cases that are terminal.

`terminal=False`: delivers all cases at that level.

## 3.3

2018-04-14

Small fix in the bhsa api.

Bumped the version number because of the inclusion of corpus specific APIs.

## 3.2.6

2018-04-14

*   Text-Fabric now contains corpus specific extras:
    *   `bhsa.py` for the Hebrew Bible (BHSA)
    *   `cunei.py` for the Proto-Cuneiform corpus Uruk
*   The `Fabric(locations=locations, modules=modules)` constructor now uses `['']`
    as default value for modules. Now you can use the `locations` parameter on its
    own to specify the search paths for TF features, leaving the `modules`
    parameter undefined, if you wish.

## 3.2.5

2018-03-23

Enhancement in search templates: you can now test for the presence of features.
Till now, you could only test for one or more concrete values of features. So,
in addition to things like

    word number=plural tense=yiqtol

you can also say things like

    word number=plural tense

and it will give you words in the plural that have a tense.

## 3.2.4

2018-03-20

The short API names `F`, `T`, `L` etc. have been aliased to longer names:
`Feature`, `Text`, `Locality`, etc.

## 3.2.2

2018-02-27

Removed the sub module `cunei.py`. It is better to keep corpus dependent modules
in outside the TF package.

## 3.2.1

2018-02-26

Added a sub module `cunei.py`, which contains methods to produce ATF
transcriptions for nodes of certain types.

## 3.2

2018-02-19

**API change** Previously, the functions `L.d()` and `L.u()` took rank into
account. In the Hebrew Bible, that means that `L.d(sentence)` will not return a
verse, even if the verse is contained in the sentence.

This might be handy for sentences and verses, but in general this behaviour
causes problems. It also disturbs the expectation that with these functions you
get *all* embedders and embeddees.

So we have lifted this restriction. Still, the results of the `L` functions have
an ordering that takes into account the levels of the returned nodes.

**Enhancement** Previously, Text-Fabric determined the levels of node types
automatically, based on the average slot-size of nodes within the node types. So
books get a lower level than chapters than verses than phrases, etc.

However, working with cuneiform tablets revealed that containing node types may
have a smaller average size than contained node types. This happens when a
container type only contains small instances of the contained type and not the
bigger ones.

Now you can override the computation by text-fabric by means of a key-value in
the *otext* feature. See the [api](/Api#levels-of-node-types).

## 3.1.5

2018-02-15

Fixed a small problem in `sectionFromNode(n)` when `n` is a node within a
primary section but outside secondary/tertiary sections.

## 3.1.4

2018-02-15

Small fix in the Text API. If your data set does not have language dependent
features, for section level 1 headings, such as `book@en`, `book@sw`, the Text
API will not break, and the plain `book` feature will be taken always.

We also reformatted all code with a PEP8 code formatter.

## 3.1.3

2018-01-29

Small adaptions in conversion from MQL to TF, it can now also convert the MQL
coming from CALAP dataset (Syriac).

## 3.1.2

2018-01-27

Nothing changed, only the names of some variables and the text of some messages.
The terminology has been made more consistent with the fabric metaphor, in
particular, *grid* has been replaced by *warp*.

## 3.1.1

2017-10-21

The `exportMQL()` function now generates one single enumeration type that serves
for all enumeration features. That makes it possible to compare values of different
enumeration features with each other, such as `ps` and `prs_ps`.

## 3.1

2017-10-20

The `exportMQL()` function now generates enumeration types for features, if
certain conditions are fulfilled. That makes it possible to query those features
with the `IN` relationship of MQL, like `[chapter book IN (Genesis, Exodus)]`.

## 3.0.8

2017-10-07

When reading edges with values, also the edges without a value are taken in.

## 3.0.7

2017-10-07

Edges with edge values did not allow for the absence of values. Now they do.

## 3.0.6

2017-10-05

A major tweak in the [importMQL()](/Api#mql-import) function so that it can
handle gaps in the monad sequence. The issue arose when converting MQL for
version 3 of the [BHSA](https://github.com/ETCBC/bhsa). In that version there
are somewhat arbitrary gaps in the monad sequence between the books of the
Hebrew Bible. I transform a gapped sequence of monads into a continuous sequence
of slots.

## 3.0.5

2017-10-05

Another little tweak in the [importMQL()](/Api#mql-import) function so that it
can handle more patterns in the MQL dump file. The issue arose when converting
MQL for version 3 of the [BHSA](https://github.com/ETCBC/bhsa).

## 3.0.4

2017-10-04

Little tweak in the [importMQL()](/Api#mql-import) function so that it can handle
more patterns in the MQL dump file. The issue arose when converting MQL for
[extrabiblical](https://github.com/ETCBC/extrabiblical) material.

## 3.0.2, 3.0.3

2017-10-03

No changes, only an update of the package metadata, to reflect that Text-Fabric
has moved from [ETCBC](https://github.com/ETCBC) to
[Dans-labs](https://github.com/Dans-labs).

## 3.0.1

2017-10-02

Bug fix in reading edge features with values.

## 3.0.0

2017-10-02

MQL! You can now convert MQL data into a TF dataset:
[importMQL()](/Api#mql-import). We had already [exportMQL()](/Api#mql-export).

The consequence is that we can operate with much agility between the worlds of
MQL and TF.

We can start with source data in MQL, convert it to TF, combine it with other TF
data sources, compute additional stuff and add it, and then finally export it as
enriched MQL, so that the enriched data can be queried by MQL.

## 2.3.15

2017-09-29

Completion: TF defines the concept of
[edges](/Api/General/#edge-features) that
carry a value. But so far we have not used them. It turned out that it was
impossible to let TF know that an edge carries values, when
[saving](/Api/General/#saving-features) data
as a new feature. Now it is possible.

## 2.3.14

2017-09-29

Bug fix: it was not possible to get
`T.nodeFromSection(('2_Chronicles', 36, 23))`, the last verse in the Bible.

This is the consequence of a bug in precomputing the sections
[sections](/Api/General/#computed-data). The
preparation step used

```python
range(firstVerse, lastVerse)
```

somewhere, which should of course have been

```python
range(firstVerse, lastVerse + 1)
```

## 2.3.13

2017-09-28

Loading TF was not completely silent if `silent=True` was passed. Better now.

## 2.3.12

2017-09-18

*   Small fix in
    [TF.save()](/Api/General/#saving-features).
    The spec says that the metadata under the empty key will be inserted into all
    features, but in fact this did not happen. Instead it was used as a default
    when some feature did not have metadata specified.

    From now on, that metadata will spread through all features.

*   New API function [explore](/Api/General#loading), to get a list of all known
    features in a dataset.

## 2.3.11

2017-09-18

*   Small fix in Search: the implementation of the relation operator `||`
    (disjoint slot sets) was faulty. Repaired.
*   The
    [search tutorial](/Dans-labs/text-fabric/blob/master/docs/searchTutorial.ipynb)
    got an extra example: how to look for gaps. Gaps are not a primitive in the TF
    search language. Yet the language turns out to be powerful enough to look for
    gaps. This answers a question by Cody Kingham.

## 2.3.10

2017-08-24

When defining text formats in the `otext.tf` feature, you can now include
newlines and tabs in the formats. Enter them as `\n` and `\t`.

## 2.3.9

2017-07-24

TF has a list of default locations to look for data sources: `~/Downloads`,
`~/github`, etc. Now `~/Dropbox` has been added to that list.

## 2.3.8

2017-07-24

The section levels (book, chapter, verse) were supposed to be customizable
through the [otext](Data-Model#otext-config-feature-optional) feature. But in
fact, up till version 2.3.7 this did not work. From now on the names of the
section types and the features that name/number them, are given in the `otext`
feature. It is still the case that exactly three levels must be specified,
otherwise it does not work.

## 2.3.7

2017-05-12

Fixes. Added an extra default location for looking for text-fabric-data sources,
for the benefit of running text-fabric within a shared notebook service.

## 2.3.5, 2.3.6

2017-03-01

Bug fix in Search. Spotted by Cody Kingham. Relational operators between atoms
in the template got discarded after an outdent.

## 2.3.4

2017-02-12

Also the `Fabric()` call can be made silent now.

## 2.3.3

2017-02-11

Improvements:

*   you can load features more silently. See [`TF.load()`](/Api#loading-features);
*   you can search more silently. See [`S.study()`](/Api#prepare-for-search);
*   you can search more concisely. See the new [`S.search()`](/Api#search-command);
*   when fetching results, the `amount` parameter of
    [`S.fetch()`](/Api#getting-results) has been renamed to `limit`;
*   the tutorial notebooks (see links on top) have been updated.

## 2.3.2

2017-02-03

Bug fix: the results of `F.feature.s()`, `E.feature.f()`, and `E.features.t()`
are now all tuples. They were a mixture of tuples and lists.

## 2.3.1

2017-01-23

Bug fix: when searching simple queries with only one query node, the result
nodes were delivered as integers, instead of 1-tuples of integers.

## 2.3

2017-01-13

We start archiving releases of Text-Fabric at [Zenodo](https://zenodo.org).

## 2.2.1

2017-01-09

Small fixes.

## 2.2.0

2017-01-06

### New: sortKey

The API has a new member: [`sortKey`](/Api#sorting-nodes)

New relationships in templates: [`nearness`](/Api#nearness-comparison). See for
examples the end of the
[searchTutorial](/Dans-labs/text-fabric/blob/master/docs/searchTutorial.ipynb).
Thanks to James Cuénod for requesting nearness operators.

### Fixes

*   in `S.glean()` word nodes were not printed;
*   the check whether the search graph consists of a single connected component
    did not handle the case of one node without edges well;

## 2.1.3

2017-01-04

Various fixes.

## 2.1.0

2017-01-04

### New: relations

Some relations have been added to search templates:

*   `=:` and `:=` and `::`: *start at same slot*, *end at same slot*, *start at
    same slot and end at same slot*
*   `<:` and `:>`: *adjacent before* and *adjacent next*.

The latter two can also be used through the `L`-api: `L.p()` and `L.n()`.

The data that feeds them is precomputed and available as `C.boundary`.

### New: enhanced search templates

You can now easily make extra constraints in search templates without naming
atoms.

See the
[searchTutorial](/Dans-labs/text-fabric/blob/master/docs/searchTutorial.ipynb)
for an updated exposition on searching.

## 2.0.0

2016-12-23

### New: Search

![warmXmas](/images/warmXmas.jpg)

*Want to feel cosy with Christmas? Put your laptop on your lap, update
Text-Fabric, and start playing with search. Your laptop will spin itself warm
with your queries!*

Text-Fabric just got a powerful search facility, based on (graph)-templates.

It is still very fresh, and more experimentation will be needed. Feedback is
welcome.

Start with the
[tutorial](/Dans-labs/text-fabric/blob/master/docs/searchTutorial.ipynb).

The implementation of this search engine can be nicely explained with a textile
metaphor: spinning wool into yarn and then stitching the yarns together.

That will be explained further in a document that I'll love to write during
Xmas.

## 1.2.7

2016-12-14

### New

[`F.otype.sInterval()`](/Api#warp-feature-otype)

## 1.2.6

2016-12-14

### bug fix

There was an error in computing the order of nodes. One of the consequences was
that objects that occupy the same slots were not ordered properly. And that had
as consequence that you could not go up from words in one-word phrases to their
containing phrase.

It has been remedied.

??? note
    Your computed data needs to be refreshed. This can be done by calling a new
    function [`TF.clearCache()`](/Api#clearing-the-cache). When you use TF after
    this, you will see it working quite hard to recompute a bunch of data.

## 1.2.5

2016-12-13

Documentation update

## 1.2.0

2016-12-08

??? note
    Data update needed

### New

### Frequency lists ###

[`F.feature.freqList()`](/Api#node-features): get a sorted frequency list for any
feature. Handy as a first step in exploring a feature.

### Export to MQL ###

[`TF.exportMQL()`](/Api#export-to-mql): export a whole dataset as a MQL database.
Including all modules that you have loaded with it.

### Changed

The slot numbers start at 0, no longer at 1. Personally I prefer the zero
starting point, but Emdros insists on positive monads and objects ids. Most
important is that users do not have to add/subtract one from the numbers they
see in TF if they want to use it in MQL and vice versa.

Because of this you need to update your data too:

```sh
    cd ~/github/text-fabric-data
    git pull origin master
```
