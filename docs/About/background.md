# Background

## Research data management

Text-Fabric supports the research data cycle of retrieving/analysing/generating/archiving
research results.

### Share data

When using the TF browser, results can be
exported, see `tf.applib.display.export`.

When programming in a notebook, TF generates many useful links after having been
invoked. In this way the provenance of your data will be shared wherever you
share the notebook (GitHub, NBviewer, Software Heritage Archive).

### Contribute data

Researchers can produce new data (`tf.fabric.Fabric.save`)
out of their findings and package their new data into modules and
distribute it to GitHub, see `tf.about.datasharing`.
Other people can use that data just by mentioning the GitHub location.
Text-Fabric will auto-load it for them.

## Factory

Text-Fabric can be used to construct websites,
for example [SHEBANQ](https://shebanq.ancient-data.org).
In the case of SHEBANQ, data has been converted to mysql databases.
However, with the built-in TF kernel] (`tf.server.kernel`),
it is also possible to use TF itself as a database to
serve multiple connections and requests.

## API organization

All corpora are different, and it shows when we have to display the materials.
Text-Fabric offers a plain display of corpus text and a pretty display of feature-enriched
structures.  
These functions are supported by advanced configuration settings, derived from
the corpus itself. Where these default settings are not enough, the corpus designer
can add and tweak corpus settings. 
Moreover, custom code can be written and hooked into the display functions.
The combination of a custom configuration file (*config.yaml*) and a bit of
application code (*app.py*), together with additional styling (*display.css*) is an
**app**.
A well-configured app can auto-download the corpus data, holds provenance information
of all data sources that are being used for a corpus, and takes care of an optimal display
of the patterns in the corpus.

* Corpora: `tf.about.corpora`
* advanced: API: `tf.applib`
* core API: `tf.core`

## Design principles

There are a number of things that set Text-Fabric apart from most other ways to encode 
corpora.

### Minimalistic model

Text-Fabric is based on a minimalistic data model for text plus annotations.

A defining characteristic is that Text-Fabric 
stores text as a bunch of features in plain text files.

These features are interpreted against a *graph* of nodes and edges,
which make up the abstract fabric of the text.

A graph is a more general concept than a tree.
Whilst trees are ubiquitous in linguistic analysis,
there is much structure in a corpus that is not strictly tree-like.

Therefore, we do not adopt technologies
that have the tree as their first class data model.
Hence, almost by definition, Text-Fabric does not make use of XML technology.

### Performance matters

Based on this model, Text-Fabric offers a core API (`tf.fabric`)
to search, navigate and process text and its annotations.
A lot of care has been taken to make this API work as fast as possible.
Efficiency in data processing has been a design criterion from the start.

!!! example "Comparisons"
    See e.g. the comparisons between the Text-Fabric way of serializing
    (pickle + gzip) and
    [avro](https://nbviewer.jupyter.org/github/annotation/text-fabric/blob/master/test/avro/avro.ipynb),
    [joblib](https://nbviewer.jupyter.org/github/annotation/text-fabric/blob/master/test/joblib/joblib.ipynb), and
    [marshal](https://nbviewer.jupyter.org/github/annotation/text-fabric/blob/master/test/marshal/marshal.ipynb).

## Code organization and statistics

To get an impression of the software that is Text-Fabric,
in terms of organization and size, see `tf.about.code`.

## History

The foundational ideas derive from work done in and around the
[ETCBC](http://etcbc.nl) avant-la-lettre from 1970 onwards
by Eep Talstra,
Crist-Jan Doedens, ([Ph.D. thesis](https://books.google.nl/books?id=9ggOBRz1dO4C)),
Henk Harmsen, Ulrik Sandborg-Petersen ([Emdros](https://emdros.org)),
and many others.

I entered in that world in 2007 as a 
[DANS](https://dans.knaw.nl/en) employee, doing a joint small data project,
and a bigger project SHEBANQ in 2013/2014.
In 2013 I developed
[LAF-Fabric](https://github.com/annotation/laf-fabric)
as a tool for constructing the website
[SHEBANQ](https://shebanq.ancient-data.org).

!!! explanation "House cleaning"
    LAF-Fabric is based on the ISO standard
    [Linguistic Annotation Framework (LAF)](https://www.iso.org/standard/37326.html).
    LAF is an attempt to marry graph models to the 
    [Text Encoding Initiative (TEI)](http://www.tei-c.org) which lives in XML.
    It is a good try, but it turns out that using XML technology for
    graphs is a pain. All the usual advantages of using the XML toolchain evaporate.

    So I decided to leave XML and its associated syntactical complexity.
    While I was at it, I took out everything that makes LAF-Fabric complicated and
    all things that are not essential for the sake of raw data processing.
    That became Text-Fabric version 1 at the end of 2016.

    It turned out that this move has freed the way to work towards higher-level goals:

    * a new search engine (inspired by [MQL](https://emdros.org) and
    * support for research data workflows.

Time moves on, and nowhere is that felt as keenly as in computing science.
Programming has become easier, humanists become better programmers,
and personal computers have become powerful
enough to do a sizable amount of data science on them.

That leads to exciting *tipping points*:

> In sociology, a tipping point is a point in time when a group - or
  a large number of group members — rapidly and dramatically changes
  its behavior by widely adopting a previously rare practice.

> [WikiPedia](https://en.wikipedia.org/wiki/Tipping_point_(sociology))

**Text-Fabric is an attempt to tip the scales** by providing digital humanists with the
functions they need *now*, based on technology that appeals *now*.

Hence, my implementation of Text-Fabric search has been done from the ground up,
and uses a strategy that is very different from Ulrik's MQL search engine.
