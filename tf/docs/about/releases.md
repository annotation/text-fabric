# Release notes

!!! hint "Consult the tutorials after changes"
    When we change the API, we make sure that the tutorials show off
    all possibilities.

See the app-specific tutorials via `tf.about.corpora`.

---

## 11

### 11.0

### 11.0.4

2023-12-18

* Improved display of special characters in text-fabric browser.
* When custom sets are loaded together with a data source, they are automatically
  passed to the `sets` parameter in `A.search()`, so that you do not have to
  pass them explicitly.
* The header information after loading a dataset is improved: it contains a list of the 
  custom sets that have been loaded and a list of the node types in the dataset

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

