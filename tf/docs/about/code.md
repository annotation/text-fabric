# Code organization

The code base of TF can be divided into a few major parts,
each with their own, identifiable task.

Some parts of the code are covered by unit tests (`tf.about.tests`).

## Base

(`tf.core`) The core API is responsible for:

Data management
:   TF data consists of *feature files*.
    TF must be able to load them, save them, import / export from MQL.

Provide an API
:   TF must offer an API for handling its data in applications.
    That means: feature lookup, containment lookup, text serialization.

Pre-computation
:   In order to make its API work efficiently, TF has to pre-compute certain
    compiled forms of the data.

## Search

(`tf.search.search`) TF contains a search engine based on templates,
which are little graphs of nodes and edges
that must be instantiated against the corpus.

Search vs MQL
:   The template language is inspired by
    [MQL](https://emdros.org), but has a different syntax.
    It is both weaker and stronger than MQL.

Search vs hand coding
:   Search templates are the most accessible way to get at the data,
    easier than hand-coding your own little programs.

    The underlying engine is quite complicated.
    Sometimes it is faster than hand coding,
    sometimes (much) slower.

## Advanced

(`tf.advanced`) TF contains an advanced API geared to auto-downloading
corpus data and displaying corpus materials in useful ways.

## Web interface

(`tf.browser`) TF contains a browser interface for interacting
with your corpus without programming.

The web interface lets you fire queries (search templates) to TF and interact
with the results:

*   expanding rows to pretty displays;
*   condensing results to various container types;
*   exporting results as PDF and CSV.

This interface be served by a local web server provided with data from a TF app.
(`tf.browser.start`, `tf.browser.kernel` and `tf.browser.web`).

## Volumes and collections

(`tf.volumes`) Machinery to support the idea that a TF dataset
is a work that consists of volumes. Volumes and collections of volumes
can be loaded without loading the whole work while still maintaining
a profound connection with the whole work through additional features such as `owork`.
See also `tf.about.volumes`.

## Dataset

(`tf.dataset`) Machinery to manipulate datasets as a whole.

## Convert

(`tf.convert`) There is support for conversion to and from MQL and for converting
arbitrary structured data (such as database dumps or TEI files) to TF
(`tf.convert.mql`, `tf.convert.walker`).

There is also some support for round-trips of TF data into other annotation tools and back
(`tf.convert.recorder`).

## Writing

(`tf.writing`) TF supports several writing systems by means of transliterations
and conversions between them and UNICODE.
