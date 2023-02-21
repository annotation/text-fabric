# Release notes

!!! hint "Consult the tutorials after changes"
    When we change the API, we make sure that the tutorials show off
    all possibilities.

See the app-specific tutorials via `tf.about.corpora`.

---

## 11

### 11.2

### 11.2.1 (Upcoming)

2023-02-??

Addition to the nbconvert tool: `tf.tools.nbconvert`:
If you pass only an input dir, it creates an html index for that directory.
You can put that in the top of your `public` folder in GitLab,
so that readers of the Pages documentation can navigate to all generated docs.

A fix in `tf.tools.xmlschema`: while analysing definitions in an `xsd` file,
the imports of other `xsd` files were not heeded. Now they are.
But not recursively, because in the examples I saw, files imported
each other mutually or with cycles.

Various enhancements to the `tf.convert.TEI` conversion:

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

