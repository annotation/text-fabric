# Code organisation


??? abstract "About"
    The code base of Text-Fabric is evolving to a considerable
    [size](/Code/Stats).

    However, the code can be divided into a few major parts,
    each with their own, identifiable task.

???+ abstract "The base"
    The
    [base](/Code/StatsBase)
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

???+ abstract "TF search"
    TF contains a
    [search engine](/Code/StatsSearch)
    based on templates, with are little graphs
    of nodes and edges that must be instantiated against the corpus.
    The template language is inspired by MQL, but has a different syntax.
    It is both weaker and stronger than MQL.

    Search templates are the most accessible way to get at the data,
    easier than hand-coding your own little programs.

    The underlying engine is quite complicated.
    Sometimes it is faster than hand coding,
    sometimes (much) slower.

???+ abstract "TF apps"
    TF contains corpus-dependent
    [apps](/Code/StatsApps)
    mainly for pretty displaying the contents of your corpus and automatic data loading from the internet.

???+ abstract "TF web interface"
    TF contains a 
    [local web interface](/Code/StatsServer)
    for interacting with your corpus without programming.

    The local web interface lets you fire queries (search templates) to TF and interact
    with the results:
    
    * expanding rows to pretty displays;
    * condensing results to verious container types;
    * exporting results as PDF and CSV.
