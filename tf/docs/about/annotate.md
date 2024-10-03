# Named Entity Recognition

## What kind of NER detection does TF support?

Named Entity Recognition is a task for which automated tools exist.
But in a smallish, well-known corpus, such tools tend to create more noise than signal.
If you know which names to expect and in what forms they occur in the corpus,
it might be easier to mark them by means of a set of triggers, or even by hand.

TF contains a tool to help you with that. The basic thing it does is
to find all occurrences of a set of patterns you specify, and then assign identifiers
and other attributes to all occurrences of those patterns.

For example, it finds all `Gio. Ernesto di Nassau` occurrences and it assigns
identity `gio.ernesto.di.nassau` and kind `PER` to them.

There are two interfaces:

*   a spreadsheet for bulk assignment, operated from a Jupyter Notebook or
    Python program;
*   the TF browser for inspection and manual assignment of entities.

## How do you tackle NER with TF?

The recommended scenario is this:

* prepare a spreadsheet where named entities are linked to *triggers*;
* TF can load such a spreadsheet and find those entities in the corpus;
* TF will check the spreadsheet for various mistakes, and reports on the outcomes;
* Depending on the reports, adapt the spreadsheet and load it again;
* Optionally run analiticcl to find spelling variants;
* Check the variants and put the wrong ones in an exception list;
* Use TF to merge the variants with the original triggers into a new spreadsheet;
* Load the merged spreadsheet;
* Check the reports and adapt the original or the merged spreadsheet;
* Iterate until the outcome is optimal, use the TF browser to inspect special cases;
* Optionally use the TF browser to add/delete individual entity occurrences;
* Use TF to bake the entities with the corpus into a new TF dataset.

See

*   `tf.ner.ner` for how to work with spreadsheets;
*   `tf.browser.ner.web` for how to work with the browser interface.

## How well does it work?

We applied this method on the
[corpus of letters of Suriano](https://gitlab.huc.knaw.nl/suriano/letters),
using a spreadsheet with over 700 named entities and over 2000 triggers leading to
12,500 marked entities.

TF is performant, it looks up all those triggers in one pass over the corpus.
Later, when it diagnoses the outcome, it needs to search for those triggers in isolation
because triggers may interfere with each other in unexpected ways. TF will then search
for them in as few passes over the corpus as possible.

## Is it subtle enough?

It is quite common that a trigger stands for various entities depending on the context.
For example, `il papa` (the pope) may refer to one person when it occurs in a letter of
1617, and another person when it occurs in a letter of 1620.

TF allows *scoped* triggers: for each set of triggers you can supply a scope, in the
form of ranges of sections for which the trigger should be looked up.

There is also an implicit rule that no piece of text falls under two entities.
When two triggers fight for a match, the trigger that has the match that starts earlier
wins. If they start at the same spot, the longer trigger wins. Because a longer trigger
is more specific than a shorter trigger.

Yet it is quite an art to fill such a spreadsheet with triggers, and some trial and
error is needed. TF helps with that in two ways:

*   it provides a lot of feedback on problem cases;
*   the process of loading a spreadsheet, searching for the triggers, and producing
    reports takes only a few seconds.

## Is it generic?

Yes. It only makes use of those characteristics of a corpus that it can glean from
the TF dataset. If your corpus is in TF, these methods will work.

However, as the software is not yet completely mature, it might be the case that you
bump into some details that will conflict with the characteristics of your corpus.

Currently I am aware of only this:

*   We assume that the section headings are integers at all levels, so that we can
    meaningfully refer to ranges of sections, e.g. `1.2-3.4.5`.
    If your corpus has strings as section headings, the current version of `tf.ner`
    will not work.

Later I intend to work around it by using the index of sections (that already is
part of the TF dataset), so that ranges like `Genesis 1-Exodus 2:3` become
meaningful.

See `tf.core.prepare.sections`

## How exactly are the entities delivered?

The first product is a `.tsv` file



Here is what the browser interface looks like:

![browser](../images/Ner/browser.png)

# Work-in-progress

This is a tool where you can add entity annotations to a corpus.
These annotations consist of a new nodes of a new type (`ent`, or `entity`) and
features that give information about those nodes.

## Supported corpora

This tool is being developed against the
[Suriano/letters](https://gitlab.huc.knaw.nl/suriano/letters) corpus.
Yet it is meant to be usable for all TF corpora. No corpus knowledge is baked in.
If corpus specifics are needed, it will be fetched from the already present TF
configuration of that corpus.
And where that is not sufficient, details are put in `ner/config.yaml`, which 
can be put next to the corpus.

I have tested it for the
[ETCBC/bhsa (Hebrew Bible) corpus](https://github.com/ETCBC/bhsa), and the
machinery works.
But it remains to be seen whether the tools is sufficiently *ergonomic* for that
corpus.

See also the following Jupyter Notebooks that show the work-in-progress:

*   Suriano
    *   [basic annotation API](https://nbviewer.org/urls/gitlab.huc.knaw.nl/suriano/letters/-/raw/main/programs/ner.ipynb/%3Fref_type%3Dheads%26inline%3Dfalse)
    *   [using a spreadsheet with instructions](https://nbviewer.org/urls/gitlab.huc.knaw.nl/suriano/letters/-/raw/main/programs/convertPlain.ipynb/%3Fref_type%3Dheads%26inline%3Dfalse)

*   BHSA
    *   [basic annotation API](https://nbviewer.org/github/ETCBC/bhsa/blob/master/programs/nerTest.ipynb)
    *   [using a spreadsheet with instructions](https://nbviewer.org/github/ETCBC/bhsa/blob/master/programs/ner.ipynb)
    *   [cookbook recipe](https://nbviewer.org/github/ETCBC/bhsa/blob/master/tutorial/cookbook/nerByTheBook.ipynb)

## Ergonomics of annotation

We try to reduce the work of manual annotations as much as possible.
It is a balancing act between automating as much as possible, but not so much that
you miss the fine points in your corpus.

We need to gather experience in order to arrive at a truly usable tool.

We are going to mark up the 
[Suriano/letters](https://gitlab.huc.knaw.nl/suriano/letters) corpus in this
way and hope to acquire a lot of experience in the process.

## Delivery of annotation data

But how exactly are those new nodes and features delivered?

This is work in progress!

Currently, TF supports data modules on top of a corpus, provided the modules
consist of features that annotate the existing nodes in the corpus.

Here we have a new situation: we not only have new features, but also a new node type.

TF has not (yet) a module system by which you can invoke such data modules on top of
an existing TF dataset.

What do we have, though?

TF has already functions to *add* new types with their features to a dataset:
`tf.dataset.modify`. This will create a completely new and separate data set out of
the existing dataset and the new nodes and features.

We deliver the annotation data as TSV files, where each line specifies
a new (entity) node, and the columns specify the values of the entity features for
that node, plus the slots that are linked to that node.

With this information in hand, it is possible

*   to call the `tf.dataset.modify` function **or**
*   work in a Jupyter notebook and use the entity data in whatever way you like.

In the future I intend to broaden the concept of data module to modules that introduce
new node types. In order to do that I have to write code for TF to include
the module data in the existing `otype` and `oslots` features and, most of all,
to generate adapted computed features such as `__levup__` and `__levdown__`.
See `tf.core.prepare` .

# Concepts

## Entities

An *entity* is a thing in the real world that is referenced by specific pieces of
text in the corpus. Think of persons, places, organizations. 

We mark up those text occurrences by creating nodes for those locations in the corpus
and assigning feature values to the features `eid` (entity identifier) and `kind`
(entity kind such as `PER`, `LOC`, `ORG`).

## How entities exist in a corpus

Your corpus may already have entities, marked up by an automatic tool such as
Spacy (see `tf.tools.myspacy`). In that case there is already a node type
`ent` and features `eid` and `kind`.

When you make manual annotations, the annotations are saved as TSV files.
In order to create nodes for them in your corpus, you can use those TSV files,
read off the feature information, and invoke `tf.dataset.modify` function to
generate new nodes and add them to your corpus.

In a next iteration, we'll include a function that will do this for you.

## Occurrences and identifiers

Entity nodes mark the text occurrences that refer to outside entities in the world.
Different occurrences have different entity nodes, but they may refer to the same
entity in the world. It is the entity identifier that unifies the various occurrences
that refer to the same entity in the world.
We do not have nodes in the corpus that correspond 1-1 to the real world entities.
The entity nodes correspond to the occurrences.

The same occurrence may have multiple entity nodes.
For example, if an occurrence `Amsterdam` refers to a location, a city council,
and a ship at the same time, you might mark it up as

*   `('amsterdam', 'LOC')`
*   `('amsterdam', 'ORG')`
*   `('amsterdam', 'SHIP')`

In fact, an entity in the real word is not solely identified by the `eid` feature,
but by the *combination* of the `eid` and `kind` features.

Of course, you are free to make the identifiers distinct if the same name refers
to entities of different kinds.

## Entity sets

When you are in the process of marking entities, you create an entity *set*.
You can give this a name, and the data you create will be stored under that name.

## For annotators

Go to the manual for annotating in the TF browser:
`tf.about.annotateBrowser`

## For programming annotators

Go to the manual for annotating in in a Jupyter Notebook, using the API:
`tf.ner.ner`
Or see this
[example notebook](https://nbviewer.jupyter.org/github/HuygensING/suriano/blob/main/programs/ner.ipynb).

## For corpus maintainers

This tool needs additional input data and produces additional output data.

The *input* data can be found in the directory `ner` next to the actual `tf` directory
from where the program has loaded the corpus data.

Depending on how you invoke TF, this can be in a clone of the
repository of the corpus, or an auto-downloaded copy of the data.

If you work with the corpus in a local clone, you'll find it under
`~/github/HuygensING/suriano` (in this example).

If you work in an auto-downloaded copy of the corpus, it is under
`~/text-fabric-data/github/HuygensING/suriano` (in this example).

Note that

*   the part `github` may be another back-end in your situation, e.g. `gitlab` or 
    `gitlab.huc.di.nl`;
*   the part `HuygensING` may be another organization, e.g. `annotation`, or wherever
    your corpus is located;
*   `suriano` might also be another repo such as `descartes`, or where ever
    your corpus is located.

The *output* data can be found a directory `_temp/ner` where the `_temp`
directory is located next to the `ner` directory that holds the input data.


### Input data

There are several bits of information needed to set up the annotation tool.
They are corpus specific, so they must be specified in a YAML file in the corpus
repository.

As an example, we refer to the
[Suriano/letters](https://gitlab.huc.knaw.nl/suriano/letters) corpus:

*   `config.yaml` in directory `ner`;
*   optional Excel sheets in directory `ner/sheets` with instructions to
    bulk-annotate entities.

Concerning `ner/config.yaml`: it has the following information:

*   `entityType`: the node type of entities that are already in the corpus,
    possibly generated by a tool like Spacy;

*   `entitySet`: a name for the pre-existing set of entities;

*   `bucketType`: the annotation works with paragraph-like chunks of text
    of your corpus. These units are called *buckets*.
    Here you can specify which node type must be taken as the buckets.

*   `features`: the features that contain essential information about
    the entities. Currently, we specify only 2 features. You may rename these
    features, but we advise not modify the number of features.
    Probably, in later releases, you'll have more choice here.

*   `keywordFeatures`: some features have a limited set of values, e.g.
    the kind of entity. Those features are mentioned under this key.

*   `defaultValues`: provide default values for the keyword features.
    The tool also provides a default for the first feature, the entity
    identifier, basically a lower case version of the full name where
    the parts of the name are separated by dots.

*   `spaceEscaped`: set this to True if your corpus as tokens with spaces in it.
    You can then escape spaces with `_`, for example in spreadsheets where you
    specify annotation instructions.

*   `transform`: the tool can read a spreadsheet with full names and per name
    a list of occurrences that should be marked as entities for that name.
    When the full name is turned into an identifier, the identifier might
    become longer than is convenient. Here you can specify a replacement
    table for name parts. You can use it to shorten or repress certain
    name parts that are very generic, such as `de`, `van`, `von`. 

Concerning the Excel sheets in `ner/sheets`:

*   they can be read by `tf.ner.ner.NER.setSheet`;

*   you might need to `pip install openpyxl` first;

*   only the first two columns of the sheet are read, the first column is
    expected to have the full names, the second column is a list of 
    surface forms that trigger the marking of an entity with this name, separated
    by semicolons.

### Good practice

All NER input data (configuration file and Excel sheets) should reside in the
repository.
The corresponding TF app should specify in its `app/config.yaml`,
under `provenanceSpecs`:

*   `extraData: ner`

When you make a new release on GitHub of the repo, do not forget to run

``` python
A = use("HuygensING/suriano:clone", checkout="clone")
A.zipAll()
```

Then pick up the new `~/Downloads/github/HuygensING/suriano/complete.zip`
and attach it to your new release on GitHub.

Then other users can invoke the corpus by

``` python
A = use("HuygensING/suriano")
```

This way there is no need to clone the repository first.
TF will auto-download the corpus, including the `ner` input data.

Then multiple people can work on annotation tasks on their local computers.

### Output data

The results of all your annotation actions will end up in the
`_temp/ner/`*version* folder in your corpus, where *version* is the
TF version of your corpus.
The output data is tightly coupled to a specific version of the corpus.

!!! caution "Versioning"
    If a new versions of the corpus is published, the generated annotations
    do not automatically migrate to the new version.
    TF has tools to perform those migrations, but they are not fully automatic.
    Whenever a new version of the corpus is produced, the producer should also
    generate a mapping file from the nodes of the new corpus to the old corpus.
    That will enable the migration of the annotations.
    See `tf.dataset.nodemaps` .

### Recommended practice

When the annotators are done, you need to ask them to dig out their data files and send
them to you.

Then you can turn that data into new entity nodes and features and merge
them into the corpus.
This is not trivial, it involves using `tf.dataset.modify`.
I intend to write functions to make this task easier.
