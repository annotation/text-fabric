# Release notes

!!! hint "Consult the tutorials after changes"
    When we change the API, we make sure that the tutorials show off
    all possibilities.

See the app-specific tutorials via `tf.about.corpora`.

---

**The TEI converter is still in active development.
If you need the latest version, clone the TF repo
and in its top-level directory run the command:**

``` sh
pip install -e .
```

## 12

### 12.5

#### 12.5.5

2024-10-??

New functions in NER to help analyze triggers that do not find named entities.
Also to add spelling variants of triggers automatically to the spreadsheets
of names and triggers.

* Fix: in the `use()` command, the loading of an additional data module triggered the
express download of `complete.zip` and eventually did not try to download the
additional module. This has been fixed.

#### 12.5.4

2024-09-16

Many changes in NER, TEI conversion, WATM generation, IIIF manifest generation.
Documentation on these points may lag behind.

Also: when the TF browser starts, it selects a port to listen to.
For each datasource, a different port number is chosen.
However, different versions of the same datasource were assigned the same version.
Now the version number is taken into account when selecting a port number, so
that you can have a TF brtowser running on different versions of the same datasource
at the same time.

#### 12.5.3

2024-07-05

**NER** 

The machinery of Named-Entity-Recognition by triggers defined in spreadsheets is now
available in the Text-Fabric browser.

You get the diagnostic messages after reading the spreadsheets, and a column with all
defined names and triggers. You can click on names to view their occurrences, and you
can click on triggers to view their occurrences in a slightly other highlight color.

When you update a spreadsheet, and reload the browser, the changes are applied
automatically.

**NB:** The docs are lagging behind on this point.

**WATM**

Further development in converting TF data to WATM (see `tf.convert.watm`), including
generating IIIF manifests for page scans.
This is work in progress.
The work is targeted at the
[Suriano Letters](https://annotation.github.io/text-fabric/tf/about/corpora.html#knawhuygensing-and-gitlabhucknawnl).

**NB:** The docs are lagging behind on this point.

**Lesser points**

*   Minor improvements in the TEI converter.
*   New functions `tf.core.files.readJson` and `tf.core.files.writeJson`
*   Replaced raw `open()` calls by `tf.core.files.fileOpen()` calls to make sure that
    `encoding="utf8"` is always passed to them.
*   MQL export now checks whether int-valued features have values within reasonable
    bounds, otherwise MQL will choke on them when importing the resulting MQL file.
    Thanks to Saulo Oliviera de Cantanhêde for spotting this.


#### 12.5.2

2024-06-13

*   New function to show the types for which each feature has defined values.
    Thanks to Marek Polášek for asking for it, writing an algorithm to produce this
    information, and then speeding it up 10-fold! For details see this
    [cookbook](https://nbviewer.org/github/ETCBC/bhsa/blob/master/tutorial/cookbook/lexemes.ipynb)

*   Working on integrating NER by spreadsheet in the TF browser. This is currently in
    an unfinished state.

#### 12.5.1

2024-06-06

*   WATM production tweaks:

    By default, WATM files are written to versioned directories inside the `_temp`
    directory. Existing data may be overwritten.
    However, if you pass a flag indicating that it is for production, the result is
    written to a new versioned directory inside `watm`. The new versioned directories
    created in this way have a suffix `-001`, `-002`, etc.
    This helps to keep published WATM fixed.

*   NER more refined entity lookup

    When looking up entities on the basis of spreadsheet instructions, you can now give
    spreadsheets for the whole corpus, and for sections and subsections and ranges
    of them. The more specificly targeted spreadsheets override the more
    generally targeted ones.

    The lookup is also more efficient, and it prefers longer matches over shorter ones.

    After the lookup, a detailed tsv file is generated with details information about
    the hits: to which triggers in which spreadsheet they correspond, and how many
    are found in which paragraphs.

#### 12.5.0

2024-05-28

Fixes in NER Browser:

*   If you click a chunk heading
    you get a box with the whole section, scrollable, just above
    the section. Previously, you got this at the end of the  chunk,
    which could be confusing if the chunk is long and the context box
    disappears below the bottom of the page.

*   When looking for complex names and translating such
    names into tokens, leave out tokens that are just spaces.

*   The NER browser will repeatedly read the list of annotation sets. This is needed
    when sets have been added or deleted from outside the NER browser.
    You do not have to restart the NER browser in that case.

*   Hyphenated occurrences were not found. That has been fixed, without decreasing the
    speed of the algorithm too much.

*   Once a set of entities has been marked, it can now also be baked into the TF
    dataset.

Fix in display algorithm

*   In plain display, when a line break occurs, we needed a trick to make it happen,
    because such a display is a flex box. A simple `<br>` has no effect.
    We found the trick and it worked. However, if the break occurs in something that
    is also highlighted, the trick did not work anymore, because the highlight
    introduces an extra `<span>` level. We fixed it by disrupting the extra span level
    for the tricked br and resuming it after the br.

### 12.4

#### 12.4.5,6

2024-05-13

*   Fix in the autodownload by TF.
    When TF downloads the `complete.zip` of a corpus and extracts it, it does
    not remove previously exisiting files in the directories in which the data
    files land.  That pre-existing material can interfere in surprising ways
    with the resulting dataset, as Christian Højgaard experienced (thanks
    Christian for reporting it and taking the time to help me pinpoint the culprit).

    The fix is that TF first inspects the `complete.zip` and determines what the
    folders are in which the file `__checkout__.txt` exists. These are the folders
    that do not tolerate pre-existing material. The will be deleted before
    extracting the zip file.

*   Fix in displaying nodes by means of `pretty()`. Sometimes an error is raised
    when composing the features and values that should be displayed for a node
    (spotted by Cody Kingham, thanks). It happens in cases where you want to
    show a feature of a related node on a node, but the related node does not exist.
    In that case TF tries to access an undefined variable. That has been fixed.
    Now these cases will not raise errors, but you might still be surprised by the
    fact that in some cases the related node does not exist.

#### 12.4.3,4

2024-05-08

*   Fix in TF browser, spotted by Jorik Groen.
    When exporting query results, the values features used in the query were not written
    to the table at all.
    The expected behaviour was that features used in the query lead to extra columns
    in the exported table.
    It has been fixed. The cause was an earlier fix in the display of features in query
    results.
    This new fix only affects the export function from the browser, not the
    `tf.advanced.display.export` function, which did not have this bug.

*   The pipeline from TEI or PageXML via TF to WATM is a complex thing to steer.
    There is now a new class `tf.convert.makewatm` that takes care of this: it provides
    a command line interface to perform the necessary convert steps.

    Moreover, you can use it as a base class and extend it with additional 
    convert steps and options, with minimal code.


#### 12.4.2

2024-04-24

Tiny fixes in the TEI and WATM conversions.

#### 12.4.1

2024-04-24

Improvements in the TEI and WATM conversions.

#### 12.4.0

2024-04-21

Support for [Marimo notebooks](https://docs.marimo.io/index.html).

TF detects when its run in a notebook, and also in what kind of notebook:
`ipython` (~ Jupyter) or `marimo`. When it needs to display material in the output
of a cell, it will choose the methods that are suitable for the kind of notebook it
is working in.

### 12.3

#### 12.3.7

2024-04-19

Improvements in `tf.convert.watm`: the resulting data is much more compact, because:

*   you can choose to export it as TSV instead of JSON;
*   no annotations of type `node` are produced anymore, they only served to map
    annotations and text segments to TF nodes; now that mapping is exported as a simple
    TSV file;
*   you can opt to exclude an arbitrary set of tags from being exported as WATM
    annotations.

#### 12.3.6

2024-04-16

* Minimal fixes in `tf.convert.tei`: it can handle a biography.
* Fixed `prettyTuple()` when passed `_asString=True`: it did not pass this on
  to `pretty()` which caused a Python error.

#### 12.3.5

2024-03-26

*   extra functionality:
    When adding types with `tf.dataset.modify` you can link nodes of a newly added type
    to nodes that were added as the preiviously added type.
    This is a bit of a limited and ad hoc extension of the functionality of this function.
    I needed a quick fix to add nodes for entities and entity occurrences at the same time
    and link them with edges. This is for the corpus
    [CLARIAH/wp6-missieven](https://github.com/CLARIAH/wp6-missieven).

*   fix: the express download of a dataset (complete.zip) was nit triggered in all
    cases where it should.

#### 12.3.4

2024-02-26

The output of `tf.convert.watm` has been changed.
It now generates token files per section, where you can configure the TF
section level for that.

The syntax for targets has been changed: more things are possible.

Tests have been adapted and strengthened.

#### 12.3.3

2024-02-20

Fix in `tf.advanced.repo.publishRelease`: it did not work if you are on a branch
named `main` because `master` was hard-coded in the source code.
Now it takes the branch name from the app context.
Do not forget to specify `branch: main` under the `provenanceSpecs` in your
`/app/config.yaml`.

Many thanks to Tony Jorg for reporting this error.

#### 12.3.1,2

2024-02-15

Minor improvements to the WATM converter, and an update of its docs.

#### 12.3.0

2024-02-08

*   A new data export conversion, from TF to WATM. See `tf.convert.watm`.
    WATM is a not yet hardened data format that powers the publishing line
    for text and annotations built by Team Text at 
    [KNAW/HuC Digital Infrastructure](https://di.huc.knaw.nl/text-analysis-en.html).
    Currently this export is used for the corpora

    *   [Mondriaan Proeftuin](https://github.com/annotation/mondriaan)
    *   [Suriano Letters](https://gitlab.huc.knaw.nl/suriano/letters)
    *   [TransLatin Corpus](https://gitlab.huc.knaw.nl/translatin/corpus)

*   Small fixes in `tf.convert.addnlp`: when the NLP data is integrated in the
    TF dataset, the NLP-generated features will get some metadata

### 12.2

#### 12.2.8,9,10

2024-01-24/25

TF can auto-download extra data with a TF dataset, e.g. a directory with named entities
(`ner`) as in the [suriano corpus](https://gitlab.huc.knaw.nl/suriano/letters).

However, this only worked when the repo was in the `github` backend and the extra
data had been packed for express-download and attached to a release.

Now it also works with the normal download methods using the GitHub and GitLab APIs.

So, after the move of Suriano from GitHub to GitLab, this functionality is still
available.

There was a glitch in the layout of the NER tool which caused section labels to be
chopped off at the margin, only in notebooks. Thats has been fixed by moving some
CSS code from one file to an other.

#### 12.2.7

2024-01-23

There were issues with starting up the Text-Fabric browser:

*   If the system could not start the browser, the TF stopped the webserver. That is
    not helpful, because one can always open a browser and enter the url in the
    address bar. Now TF shows the url rather prominently when it does not open
    a browser.
*   If debug mode is on, Flask reloads the whole process, and that might include 
    opening the browser as well. Now Flask only opens the browser after the startup of
    the webserver, and not anymore after successive reloads.


#### 12.2.6

2024-01-15

Somehow the express way of downloading data (via complete.zip attached to the latest
release) did not get triggered in all cases where it should.
It is now triggered in more cases than before.

#### 12.2.5

2023-12-18

Small fix in NER browser: prevent submitting the form if the focus is in a textarea 
field or in an input field that does not have type=submit.

#### 12.2.3,4

2023-12-09

Writing support for Ugaritic, thanks to Martijn Naaijer and Christian Højgaard for
converting a Ugaritic corpus to TF.

Fix in display functions (continued):

*   The logic of feature display, fixed in the previous version, was not effective 
    when things are displayed in the TF browser. Because in the TF browser the
    features of the last query were passed as `extraFeatures` instead of
    `tupleFeatures`. This has been fixed by using `tupleFeatures` in the TF browser
    as well.


#### 12.2.2

2023-12-02

Fix in display functions, thanks to Tony Jurg:

*   if you do `A.pretty(x, queryFeatures=False, extraFeatures="yy zz")`
    the extra features were not shown. So there was no obvious way to control
    exactly the features that you want to show in a display. That has been fixed.
    Further clarification: the node features that are used by a query are stored in
    the display option `tupleFeatures`. That is what causes them to be displayed in 
    subsequent display statements. You can also explicitly set/pass the `tupleFeatures`
    parameter.
    However, the fact that `queryFeatures=False` prohibited the display of features
    mentioned in `extraFeatures` was against the intuitions.

Improvements in the PageXML conversion.

*   There are token features `str`, `after` that reflect the logical tokens
*   There are token features `rstr`, `rafter` that reflect the physical tokens
*   The distincition between logical and physical is that physical token triplets
    with the soft hyphen as the middle one, are joined to one logical token;
    this happens across line boundaries, but also region and page boundaries.

#### 12.2.0,1

2023-11-28

New conversion tool: from PageXML. Still in its infancy.
It uses the
[PageXML tools](https://github.com/knaw-huc/pagexml)
by Marijn Koolen.

For an example see
[translatin/logic](https://gitlab.huc.knaw.nl/translatin/logic/-/blob/main/tools/convertPlain.ipynb?ref_type=heads).

Fix:

*   TF did not fetch an earlier version of a corpus if the newest release
    contains a `complete.zip` (which only has the latest version).
*   For some technical reason that still escapes me, the TF browser was slow to start.
    Fixed it by saying `threaded=True` to Flask, as suggested on
    [stackoverflow](https://stackoverflow.com/a/11150849/15236220)

From now on: TF does not try to download `complete.zip` if you pass a `version` argument
to the `use()` command.

### 12.1

#### 12.1.6,7

2023-11-15

Various fixes:

*   Some package data was not included for the NER annotation tool.
*   In the NER tool, the highlighting of hits of the search pattern is now exact, it was
    sometimes off.

Deleted tf.tools.docsright again, but developed it further in 
[docsright](https://github.com/annotation/docsright).

#### 12.1.5

2023-11-02

*   Improvement in dependencies. Text-Fabric is no longer mandatory dependent on
    `openpyxl`, `pandas`, `pyarrow`, `lxml`.
    The optional dependencies on `pygithub` and `python-gitlab` remain, but most users
    will never need them, because TF can also fetch the `complete.zip` that is
    available as release asset for most corpora.

    Whenever TF invokes a module that is not in the mandatory dependencies,
    it will act gracefully, providing hints to install the modules in question.

#### 12.1.3,4

2023-11-01

*   API change in the Annotator:
    Calling the annotator is now easier: 

        A.makeNer()

    (No need to make an additional `import` statement.)

    This will give you access to all annotation methods, including using a spreadsheet
    to read annotation instructions from.
*   Removal of deprecated commands (on the command line) in version 11:

    * `text-fabric` (has become `tf`)
    * `text-fabric-zip` (has become `tf-zip`)
    * `text-fabric-make` (has become `tf-make`)
    
*   Bug fixes:
    [#81](https://github.com/annotation/text-fabric/issues/81)
    and
    [#82](https://github.com/annotation/text-fabric/issues/82)

*   Spell-checked all bits of the TF docs here (33,000 lines).
    Wrote a script tf.tools.docsright to separate the code content from
    the markdown content, and to strip bits from the markdown content that lead
    to false positives for the spell checker.
    Then had the Vim spell checker run over those lines and corrected all mistakes
    by hand.
    Still, there might be grammar errors and content inaccuracies.
*   12.1.4 follows 12.1.3. quickly, because in corpora without a NER configuration file,
    TF did not start up properly.

#### 12.1.1,2

2023-10-29

*   Bug fix: the mechanism to make individual exceptions when adding named entities
    in the tf.browser.ner.annotate tool was broken. Thanks to Daniel Swanson for
    spotting it.
*   Additional fixes and enhancements.

### 12.1.0

2023-10-28

##### New stuff

*   In the TF browser there will be a new tab in the vertical sidebar: 
    **Annotate**, which will give access to manual annotation tools. I am developing
    the first one, a tool to annotate named entities efficiently, both in the
    TF browser and in a Jupyter Notebook.
    Reed more in `tf.about.annotate`.

    These tools will let you save your work as files on your own computer.

*   In `tf.convert.addnlp` we can now extract more NLP information besides tokens
    and sentences: part-of-speech, morphological tagging, lemmatisation, named
    entity recognition

##### Fixes

*   in the TEI converter.

### 12.0

#### 12.0.6,7

2023-09-13

Trivial fix in code that exports the data from a job in the TF browser.
In the meanwhile there is unfinished business in the `Annotate` tab in the TF browser,
that will come into production in the upcoming 12.1 release.

The Chrome browser has an attractive feature that other browsers such as Safari lack:
It supports the CSS property
[content-visibility](https://developer.mozilla.org/en-US/docs/Web/CSS/content-visibility).
With this property you can prevent
the browser to do the expensive rendering of content that is not visible on the screen.
That makes it possible to load a lot of content in a single page without tripping up
the browser. You also need the
[IntersectionObserver API](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API),
but that is generally supported by browsers. With the help of that API you can
restrict the binding of event listeners to elements that are visible on the screen.

So, you can open the TF browser in Chrome by passing the option `--chrome`.
But if Chrome is not installed, it will open in the default browser anyway.
Also, when the opening of the browser fails somehow, the web server is stopped.

#### 12.0.5

2023-07-10

Fixed references to static files that still went to `/server` instead of `/browser`.
This has to do with the new approach to the TF browser.

#### 12.0.0-4

2023-07-05

##### Simplification

*   The TF browser no longer works with a separate process that holds the
    TF corpus data. Instead, the web server (flask) loads the corpus itself.
    This will restrict the usage of the TF browser to local-single-user scenarios.

*   TF no longer exposes the installation options `[browser, pandas]`

        pip install 'text-fabric[browser]'
        pip install 'text-fabric[pandas]'

    If you work with Pandas (like exporting to Pandas) you have to install it yourself:

        pip install pandas pyarrow

    The TF browser is always supported.

    The reason to have these distinct capabilities was that there are python libraries 
    involved that do not install on the iPad.
    The simplification of the TF browser makes it possible to be no longer dependent
    on these modules.

    Hence, TF can be installed on the iPad, although the
    TF browser works is not working there yet.
    But the auto-downloading of data from GitHub / GitLab works.


##### Minor things

*   Header. After loading a dataset, a header is shown with shows all kinds of
    information about the corpus. But so far, it did not show the TF app settings.
    Now they are included in the header. There are two kinds: the explicitly given
    settings and the derived and computed settings.
    The latter ones will be suppressed when loading a dataset in a Jupyter notebook,
    because these settings can become quite big. You can still get them with
    `A.showContext()`. In the TF browser they will be always included, you find it in
    the *Corpus* tab.

---

## Older releases

See `tf.about.releasesold`.

