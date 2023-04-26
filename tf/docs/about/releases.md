# Release notes

!!! hint "Consult the tutorials after changes"
    When we change the API, we make sure that the tutorials show off
    all possibilities.

See the app-specific tutorials via `tf.about.corpora`.

---

## 11

### 11.4.2 (upcoming)

2023-04-26

##### Commandline tasks

I'am going to change the commands that Text-Fabric provides on the commandline after installing.

They will all start with `tf-`.
Then there is less risk of interference with other commands that users already have on the commandline.

Here is a table with the old names and the new names.
The old names remain available until the next intermediate version 11.5 or major version 12.

Here is a table of the commands in question

current | new | description
--- | --- | ---
not yet available | `tf-fromtei` | converts a TEI source in the repo of the current directory to TF
not yet available | `tf-zipall` | makes a complete zip of the dataset in the repo of the current directory
`text-fabric` | `tf` | starts the text-fabric browser
`text-fabric-zip` | `tf-zip` | zips tf files into versioned zip files
`text-fabric-make` | `tf-make` | builds a client-side search interface for a dataset
`nbconvert` | `tf-nbconvert` | converts a directory with Jupyter notebooks to html
`xmlschema` | `tf-xmlschema` | extracts useful information from xml schemas
`addnlp` | `tf-addnlp` | feeds a dataset to Spacy and adds results to it

The usage of `tf-fromtei` and `tf-addnlp` is now highly streamlined: you 
can pass them arguments which are

*   plain word strings are *tasks*
*   name`=`value strings are parameters
*   `-`word, `+`word, `++`word are flags

##### Conversion and NLP workflows

*   The way the `tf-fromtei` and `tf-addnlp` workflows can be controlled has
    been streamlined; they have the same conventions for passing tasks, parameters, and
    flags. 
*   You do not have to write an almost trivial program to wrap the tei conversion,
    typically `tfFromTei.py`. Instead, put some config info in a `tei.yaml` file and
    a transformation function in a `tei.py` file, both optional.
*   You can pass less info to `tf-fromtei`: the converter autodetects available versions
    of the TEI source, and selects the latest by default.
    It also autodetects the generated TF dataset versions, and by default overwrites
    the latest one. But you can easily direct the converter to other versions, both
    of the TEI and the TF.

### 11.4.1

2023-04-24

Small fixes in the TEI conversion and the NLP pipeline integration.
The parameters/flags for the convert steps and pipeline operations have been
made more powerful and superfluous options have been removed.

### 11.4.0

2023-04-21

This new version is all about using the results of NLP pipelines in the creation
of a TF dataset.
We build on the TEI to TF conversion in `tf.convert.tei` and surround it with
other data creation steps.
The following workflow is now supported by means of simple commands.

*   The TEI to TF conversion can now be extended with NLP generated tokens and
    sentences, there is single command to do this but the individual steps can
    also be run in a notebook, see `tf.convert.addnlp`. Work in progress.
*   TF can now invoke a Spcay-based workflow to detect tokens and sentences.
    See `tf.tools.myspacy`.
*   TEI to TF conversion: usability improvements and fixes.
*   `tf.dataset.modify` can now also replace the slot type in a dataset by an other
    node type. For example, you can use this function to add tokens to a dataset
    that is character-based and make the tokens the new slot type and cause all
    character nodes to be discarded. This can be done in one go.
*   Examples are in the Mondriaan test garden:
    [annotation/mondriaan](https://nbviewer.org/github/annotation/mondriaan/blob/master/programs/convertExpress.ipynb)
    in three levels of detail.

### 11.3

### 11.3.1

2023-04-11

*   GitHub API Rate Limit avoidance
    *   TF first tries to download requested data without using the GitHub API.
        This happens when you request the latest release of a corpus.
        All data specified in the corpus app (the app itself, the main data,
        the standard module data for that corpus, the graphics files if the corpus
        needs them) are expected in the file `complete.zip` which should be
        attached to the latest release on Github.
        TF can find that file and download it without any API access.
    *   There is a new function `A.zipAll()` that zips all corpus data into
        a file `complete.zip`, which you can attach to a release.
    *   This file can also be unzipped in your text-fabric-data directory.
        
*   TEI to TF converter:
    *   Fix: better console output when running the the check task.
    *   Improvement: detect when tags are being used in multiple namespaces.
    *   Improvement: you can configure the names of the section levels and features.
    *   Change: more straightforward dealing with empty elements: all empty elements
        get an empty slot, and care is being taken that these slots end up within
        the section structure and not strangely outside it.

*   Walker converter
    *   Fix in cv.linked(): the slots are returned sorted. If during the walk you linked
        slots to nodes by cv.link(), the order of linking the slots might not be the
        order of the slots in the text. So, cv.linked() has to sort the slots before
        returning.

*   Display in TF browser and in Notebooks:
    *   Fix: a deliberate newline in feature values is translated to a `<br>` element,
        so that you see a line-break.
    *   Fix: in the TF-browser, if not default text format is configured, the default
        `text-orig-full` will be taken.

*   Fix: `open()` statements should specify the `encoding="utf8"`, otherwise
    a non utf8 encoding may be used on Windows.
    I
    [knew}(https://annotation.github.io/text-fabric/tf/about/releasesold.html#7102)
    this, but in later code I have forgotten this.
    Thanks to Saulo de Oliveira Cantanhêde for reporting this.

*   Fix: bumped the version requirement for Python to 3.9.
*   Fix: Text-Fabric should not print the full-path to your home directory,
    but replace it with a `~`. There were some cases where this escaping was
    not successfully applied, e.g. in `tf.advanced.repo`.

### 11.3.0

2023-03-23

*   New interface option in pretty displays: show all features, except `otype`.
    See `tf.advanced.options` under `multiFeatures`.
    It works in the Text-Fabric browser and in Jupyter notebooks.

    Handy for exploring new and unknown TF datasets, for example those which are
    converted literally from an intricate TEI nest of files.

*   Improvements in the transcription document generated by the `tf.convert.tei`.

*   New conversion from TF to Pandas `tf.convert.pandas`, callable as
    `A.exportPandas()`. For examples see:
    [BHSA](https://nbviewer.org/github/ETCBC/bhsa/blob/master/tutorial/export.ipynb)
    [Moby Dick](https://nbviewer.org/github/CLARIAH/wp6-mobydick/blob/main/tutorial/export.ipynb)
    [Ferdinand Huyck](https://nbviewer.org/github/CLARIAH/wp6-ferdinandhuyck/blob/main/tutorial/export.ipynb)

*   The function `importMQL()` must be called in a different way. The function
    `exportMQL()` can be called from a `TF` or `A` object.

*   Removed a clumsy fix that produces a spurious space in unwanted places.
    The fix was introduced earlier to provide extra spaces in the Hermans corpus,
    and it worked quite nicely there. But now is Martijn complaining because he sees
    too many spaces in the Samaritan Pentateuch. This has been fixed.

### 11.2

### 11.2.3

2023-03-08

Improvements in the TEI to TF conversion:

*   you can opt for the word as slot type instead of the character;
    this gives a bit of a lower resolution, but data processing is much quicker;
*   you can choose between two sectioning models
    1.  folders, files, top-level elements as chunks
    1.  top-level elements as chapters, elements below it as chunks.

Fix in `tf.advanced.display.export`: if a value starts with a quote, it will be preceded by a backslash,
otherwise it disturbs Excel and Numbers when they read it in a tab-separated file.

Other small fixes.

### 11.2.2

2023-02-22

Added `tf.convert.xml`, a straightforward, generic XML to TF converter, obtained from
`tf.convert.tei` by stripping almost all intelligence from it.
It serves as a stub to start off with your own XML to TF conversion program.

For an example how to use it, see its application to the 
[Greek New Testament, lowfat trees](https://github.com/ETCBC/nestle1904).

### 11.2.1

2023-02-21

Addition to the nbconvert tool: `tf.tools.nbconvert`:
If you pass only an input dir, it creates an html index for that directory.
You can put that in the top of your `public` folder in GitLab,
so that readers of the Pages documentation can navigate to all generated docs.

A fix in `tf.tools.xmlschema`: while analysing definitions in an `xsd` file,
the imports of other `xsd` files were not heeded. Now they are.
But not recursively, because in the examples I saw, files imported
each other mutually or with cycles.

Various enhancements to the `tf.convert.tei` conversion:

*   a fix in whitespace handling (the whitespace removal was a bit too aggressive),
    the root cause of this was the afore-mentioned bug in `tf.tools.xmlschema`;
*   a text format with layout is defined and set as the default;
*   text within the tei header and notes is displayed in a different color.

A fix of an error, spotted by Christian C. Høygaard, while loading a TF resource in
a slightly unusual way. 

### 11.2.0

2023-02-16

#### New converter: TEI to TF

This is a generic, but also somewhat dumb, converter that
takes all information in a nest of TEI files and transforms
it into a valid and ready-to-use TF dataset.

But it is also a somewhat smart, because it generates a TF app
and documentation for the new dataset.

See `tf.convert.tei`

#### New command line tool: nbconvert

``` sh
nbconvert inDirectory outDirectory
```

Converts a directory of interlinked notebooks to HTML and keeps the
interlinking intact.  Handy if you want to show your notebooks in the Pages
service of GitHub or GitLab, bypassing NBViewer.

See `tf.tools.nbconvert`

#### New command line tool: xmlschema

``` sh
xmlschema analyse schema.xsd
```

Derives meaningful information from an XML schema.

See `tf.tools.xmlschema`

#### New API function: flexLink

`A.flexLink()` generates an app-dependent link
to a tutorial or document served via the Pages of GitHub or GitLab.

See `tf.advanced.links.flexLink`

#### Other improvements

Various app-configuration improvements under the hood, solving all kinds of edge
cases, mostly having to do with on-premiss GitLab backends.

### 11.1

### 11.1.4

2023-02-12

Small improvement in rendering features with nodes: if a feature value ends
with a space,
it was invisible in a pretty display. now we replace the last space by a
non-breaking space.

Small fix for when Text-Fabric is installed without extras, just
`pip install text-fabric` and not `pip install 'text-fabric[all]'`

In that case text-fabric referred to an error class that
was not imported. Spotted by Martijn Naaijer. Fixed.

### 11.1.3

2023-02-03

In the Text-Fabric browser you can now resize the column in which you write
your query.

### 11.1.2

2023-01-15

Small fix in math display.

### 11.1.1

2023-01-13

Small fixes

### 11.1.0

2023-01-12

Mathematical formulas in TeX notation are supported.
You can configure any app by putting `showMath: true` in its
`config.yaml`, under interface defaults.

Several small tweaks and fixes and the higher level functions: how text-fabric displays
nodes in Jupyter Notebooks and in the Text-Fabric browser.

It is used in the
[letters of Descartes](https://github.com/CLARIAH/descartes-tf).

### 11.0

### 11.0.7

2022-12-30

This fixes issue
[#78](https://github.com/annotation/text-fabric/issues/78),
where Text-Fabric crashes if the binary data for a feature is corrupted.
This may happen if Text-Fabric is interrupted in the precomputation stage.
Thanks to [Seth Howell](https://github.com/sethbam9) for reporting this.

### 11.0.6

2022-12-27

* Small fix in the TF browser (`prettyTuple()` is called with `sec=` instead of `seq=`).
* Fix in advanced.search.py, introduced by revisiting some code that deals with sets.
  Reported by Oliver Glanz.


### 11.0.4-5

2022-12-18

* Improved display of special characters in text-fabric browser.
* When custom sets are loaded together with a data source, they are automatically
  passed to the `sets` parameter in `A.search()`, so that you do not have to
  pass them explicitly.
* The header information after loading a dataset is improved: it contains a list of the 
  custom sets that have been loaded and a list of the node types in the dataset,
  with some statistics.
* In the Text-Fabric browser this header information is shown when you expand a new
  tab in the side bar: **Corpus**.

### 11.0.3

2022-12-17

**Backends**

Small fixes for problems encountered when using gitlab backends.

**Search**

Fixed a problem spotted by Camil Staps: in the Text-Fabric browser valid queries
with a quantifier gave error-like messages and no results.

* The cause was two-fold: the processing of quantifiers led to extra
informational messages. (This is a regression)
* The Text-Fabric browser interpreted these messages as error messages.

Both problems have been fixed.

* The extra informational messages are suppressed (as it was earlier the case).
* The result that the kernel passes to the webserver now includes a status parameter,
separate from the messages, which conveys whether the query was successfull.
Queries with informational messages and a positive status will have their results
shown as well as their messages. 

### 11.0.2

2022-12-04

Text-Fabric will detect if it runs on an iPad.
On an iPad the home directory `~` is not writable.
In that case, Text-Fabric will use `~/Documents` instead of `~`
consistently.

When Text-Fabric reports filenames on the interface, it always *unexpanduser*s
it, so that it does not reveal the location of your home directory.

Normally, it replaces your home directory by `~`, but on iPad it replaces
*your home directory*`/Documents` by `~`.

So if you publish notebooks made on an iPad or made on a computer,
there is no difference in the reported file names.

### 11.0.1

2022-11-18

Small fixes: the newest version of the
[pygithub](https://pygithub.readthedocs.io/en/latest/introduction.html)
module issues slightly different errors.
Text-Fabric did not catch some of them, and went on after failures,
which led to unspeakable and incomprehensible further errors.
That has been fixed. 

As a consequence, we require the now newest release of that module,
which in turns requires a Python version of at least 3.7.0.

So we have bumped the Python requirement for Text-Fabric from 3.6.3 to 3.7.0.

### 11.0.0

2022-11-11

Text-Fabric can be installed with different capabilities.

On some platforms not all requirements for Text-Fabric can be met, e.g.
the Github or GitLab backends, or the Text-Fabric browser.

You can now install a bare Text-Fabric, without those capabilities,
or a more capable Text-Fabric with additional capabilities.

Text-Fabric will detect what its capabilities are, and issue warnings
if it asked to do tasks for which it lacks the capabilities.

See more in `tf.about.install`.


---

## Older releases

See `tf.about.releasesold`.

