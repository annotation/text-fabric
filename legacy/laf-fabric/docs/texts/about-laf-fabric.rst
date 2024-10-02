About
#####

.. caution::
    LAF-Fabric has a successor: 
    `Text-Fabric <https://github.com/ETCBC/text-fabric/wiki>`_.
    LAF-Fabric stays around in order to run legacy notebooks.
    It is recommended to use **Text-Fabric** for new work.

Description
===========
LAF-fabric is a Python tool for running Python notebooks with access to the information in a LAF resource.
It has these major components:

* the *laf* package
    * a LAF compiler for transforming a LAF resource into binary data
      that can be loaded nearly instantly into Python data structures;
    * an execution environment that gives Python notebooks access to LAF data
      and is optimized for feature lookup.
* the *etcbc* package
    * an extension toolkit geared to a specific LAF resource:
      the `ETCBC Hebrew Text Database <http://www.persistent-identifier.nl/?identifier=urn%3Anbn%3Anl%3Aui%3A13-048i-71>`_.
* the *emdros2laf* package
    * conversion from EMDROS to LAF. The ETCBC Hebrew is originally available as an EMDROS database.
      This package performs the conversion to LAF.

The selling point of LAF-fabric is performance, both in terms of speed and memory usage.
The second goal is to make it really easy for you to write analytic notebooks
straightforwardly in terms of LAF concepts without bothering about performance.

Both points go hand in hand, because if LAF-fabric needs too much time to execute your notebooks,
it becomes very tedious to experiment with them.
I wrote LAF-fabric to make the cycle of trial and error with your notebooks as smooth as possible.

Workflow
========
The typical workflow is:

#. download a LAF resource [#laf]_ to your computer
   (or work with a compiled version [#nolaf]_).
#. install LAF-fabric on your computer.
#. adapt a config file to change the location of the work directory.
#. write your own `iPython notebook <http://ipython.org>`_ or script
#. run the code cells in an `iPython notebook <http://ipython.org>`_ or your script

You can run your cells, modify them, run them again, ad libitum.
While the notebook is alive, loading and unloading of data will be done only when it is really needed.

So if you have to debug a notebook, you can do so without repeatedly waiting for the loading of the data.

The first time a source or annox [#annox]_ is used, the LAF resource will be compiled.
Compiling of the full Hebrew Bible source may take considerable time,
say 10 minutes for a 2 GB XML annotations on a Macbook Air (2012).
The compiled source will be saved to disk across runs of LAF-fabric.
Loading the compiled data takes, in the same setting with the Hebrew Bible, less than a second,
but then the feature data is not yet loaded, only the regions, nodes and edges.
If you need the original XML identifiers for your notebook, there will be 2 to 5 seconds of extra load time.

You must declare the LAF-features that you use in your notebook, and LAF-fabric will load data for them.
Loading a feature typically adds 0.1 to 1 second to the load time.
Edge features may take some seconds, because of the connectivity data that will be built on the basis of edge information.

LAF-Fabric will also unload the left-over data from previous runs for features
that the current run has not declared.
In this way we can give each run the maximal amount of RAM.

License
=======

This work is freely available, without any restrictions.
It is free for commerical use and non-commercial use.
The only limitation is that parties that include this work may not in anyway restrict the freedom
of others to use it.

Designed for Performance
========================
Since there is a generic LAF tool for smaller resources,
(`POIO, Graf-python <http://media.cidles.eu/poio/graf-python/>`_)
this tool has been designed with performance in mind. 
In fact, performance has been the most important design criterion of all.
There isa price for that: we use a simplified feature concept.
See the section of LAF :ref:`feature coverage` below.

.. _feature coverage:

LAF feature coverage
====================
This tool cannot deal with LAF resources in their full generality.

In LAF, annotations have labels, and annotations are organized in annotation spaces.
In a previous version, LAF-fabric ignored annotation spaces altogether.
Now annotation spaces are fully functional.

*primary data*
    LAF-fabric deals with primary data in the form of text.
    It is not designed for other media such as audio and video.
    Further, it is assumed that the text is represented in UNICODE, in an
    encoding supported by python, such as utf-8.
    LAF-fabric assumes that the basic unit is the UNICODE character.
    It does not deal with alternative units such as bytes or words. 

*feature structures*
    The content of an annotation can be a feature structure.
    A feature structure is a set of features and sub features, ordered again as a graph.
    LAF-fabric can deal with feature structures that are merely sets of key-value pairs.
    The graph-like model of features and subfeatures is not supported.

*annotations*
    Even annotations get lost. LAF-fabric is primarily interested in features and values.
    It forgets the annotations in which they have been packaged except for: 

    * the annotation space,
    * the annotation label,
    * the target kind of the annotation (node or edge)

*dependencies*
    In LAF one can specify the dependencies of the files containing regions, nodes, edges and/or annotations.
    LAF-fabric assumes that all dependent files are present in the resource.
    Hence LAF-fabric reads all files mentioned in the GrAF header, in the order stated in the GrAF header file.
    This should be an order in which regions appear before the nodes that link to them,
    nodes before the edges that connect them, and nodes and edges before the annotations that target them.

Future directions
=================
LAF-Fabric has proven to function well for in increasing number of tasks.
This proves that the methodology works and we are trying more challenging things.
The direction of the future work should be determined by your research needs.

Adding new annotations
----------------------
LAF-Fabric supports adding an extra annotation package to the existing LAF resource,
and contains an example workflow to create such packages.
We have used it to add an extra annotation package to the
`ETCBC Hebrew Text Database <http://www.persistent-identifier.nl/?identifier=urn%3Anbn%3Anl%3Aui%3A13-048i-71>`_
containing data that has not made it yet to the published set of features, but it relevant to researchers.
See the notebook `extra px data <http://nbviewer.ipython.org/github/ETCBC/laf-fabric-nbs/blob/master/extradata/para%20from%20px.ipynb>`_

Visualization
-------------
You can invoke additional packages for
data analysis and visualization right after your task has been completed in the notebook.

The division of labour is that LAF-Fabric helps you to extract the relevant data from the resource,
and outside LAF-Fabric, but still inside your notebook, you continue to play with that data.

When we get more experience with visualization, we might need new ways of data extraction, which
would drive a new wave of changes in LAF-Fabric.

Graph methodology and full feature structures
---------------------------------------------
LAF-Fabric has not been implemented as a graph database.
We might adopt more techniques from graph databases to make it more compatible with
current graph technology.
We could use the python `networkx <http://networkx.github.io/#>`_ module for that.
That would also help to implement feature structures in full generality.

API completion
--------------
The API offers functionality that covers the following aspects of a LAF resource:

*node iterator*
    iterator that produces nodes in the order by which they are anchored to the primary data (which are linearly ordered).
*feature lookup*
    a class that gives easy access to feature data and has methods for feature value lookup and mapping of
    feature values.
*connectivity*
    adjacency information for nodes, by which you can travel via (annotated) edges to neighbouring nodes;
    there are also methods to generate sets of end-points when traveling from a nodeset along featured edges until there are no
    outgoing edges. You can also travel in the opposite direction.
*xml identifier mapping*
    a two-way mapping from orginal identifiers in the LAF XML resource to integers that denote the corresponding nodes in LAF-Fabric.
*primary data access*
    The primary data can be accessed through nodes that are linked to regions of primary data.
*hooks for custom pre-computed data*
    Third party modules geared to a particular LAF resource may perform additional computations and store the result
    alongside the complied data.

.. rubric:: Footnotes

.. [#laf] A LAF resource is a directory with a primary data file, annotation files and header files.
   This program has been tested with :ref:`LAF version of the Hebrew Bible <data>`.

.. [#nolaf] It is perfectly possible to run the workflow without the original LAF resource.
   If somebody has compiled a LAF resource for you, you only need to obtain you the compiled data,
   and let the LAF source in the configuration point to something non-existent.
   In that case LAF-fabric will not complain, and never attempt to recompile the original resource.
   You can still add extra annotation packages, which can be compiled against the original LAF source,
   since the original LAF XML identifiers are part of the compiled data.
   In case of the Hebrew Bible LAF resource: the original resource is 1.64 GB on disk,
   while the compiled binary data is 268 MB.

.. [#annox] Shorthand for *extra annotation package*. You can add an extra package of annotations in LAF format
   to your data. When needed, this annox will be compiled into binary data and combined with the compiled data
   of the main LAF resource. So you can integrate your own annotation work with the annotations that have been done before.
   **You cannot add new regions, nodes, edges in this way**.

.. [#api] Python does not have strict encapsulation of data structures,
   so by just inspecting the classes and objects you can reach out
   for all aspects of the LAF data that went into the compiled data.

