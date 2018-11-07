# Code organisation


The code base of Text-Fabric is evolving to a considerable
[size](/Code/Stats).

However, he code can be divided into a few major parts,
each with their own, identifiable task.

Some parts of the code are covered by unit [tests](/Code/Tests).

## Base

The
[generic API](/Api/General) ([stats](/Code/StatsBase))
of Text-Fabric is responsible for:

??? abstract "Data management"
    Text-Fabric data consists of *feature files*.
    TF must be able to load them, save them, import/export from MQL.

??? abstract "Provide an API"
    TF must offer an API for handling its data in applications.
    That means: feature lookup, containment lookup, text serialization.

??? abstract "Precomputation"
    In order to make its API work efficiently, TF has to precompute certain
    compiled forms of the data.

## Search

TF contains a
[search engine](/Api/General/#searching) ([stats](/Code/StatsSearch))
based on templates, which are little graphs
of nodes and edges that must be instantiated against the corpus.

??? abstract "Search vs MQL"
    The template language is inspired by MQL, but has a different syntax.
    It is both weaker and stronger than MQL.

??? abstract "Search vs hand coding"
    Search templates are the most accessible way to get at the data,
    easier than hand-coding your own little programs.

    The underlying engine is quite complicated.
    Sometimes it is faster than hand coding,
    sometimes (much) slower.

## Apps

TF contains corpus-dependent [apps](/Api/Apps) ([stats](/Code/StatsApps)).

??? abstract "Display"
    An app knows how to display a particular corpus.

??? abstract "Download"
    An app knows how to download a particular corpus from its online repository.

??? abstract "Web interface"
    An app can set up a local web interface for a particular corpus.

## Web interface

TF contains a 
[local web interface](/Server/Web) ([stats](/Code/StatsServer))
for interacting with your corpus without programming.

??? abstract "Working with your corpus"
    The local web interface lets you fire queries (search templates) to TF and interact
    with the results:

    * expanding rows to pretty displays;
    * condensing results to verious container types;
    * exporting results as PDF and CSV.
