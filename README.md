# text-fabric
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1008899.svg)](https://doi.org/10.5281/zenodo.1008899)
![text-fabric](https://raw.github.com/Dans-labs/text-fabric/master/docs/tf.png)


Text-Fabric is a Python3 package for Text plus Annotations.

It provides a data model, a text file format, and a binary format for (ancient) text plus
(linguistic) annotations.

The emphasis of this all is on:

* data processing
* sharing data
* contributing modules

A defining characteristic is that Text-Fabric does not make use of XML or JSON,
but stores text as a bunch of features.
These features are interpreted against a *graph* of nodes and edges, which make up the
abstract fabric of the text.

The intended use case is ancient writings, such as the Hebrew Bible or the Greek New Testament.
Text-Fabric not only deals with the text, but also with rich sets of linguistic annotations added to them.
It has been used to construct the website
[SHEBANQ](https://shebanq.ancient-data.org) and it is being
used by researchers to analyse such texts. 

# Install

Text Fabric is a Python(3) package on the Python Package Index, so you can install it easily with `pip` from
the command line. Here are the precise
[installation instructions](https://github.com/Dans-labs/text-fabric/wiki/Home).

# Documentation

There is extensive documentation.

1. The [wiki associated with this repo](https://github.com/Dans-labs/text-fabric/wiki) is meant as a reference.
   1. It explains the [data model](https://github.com/Dans-labs/text-fabric/wiki/Data-model)
   2. It specifies the [file format](https://github.com/Dans-labs/text-fabric/wiki/File-formats)
   3. It holds the [api docs](https://github.com/Dans-labs/text-fabric/wiki/Api)
2. Included in this repo are also tutorials and exercises to guide you into increasingly involved tasks
   1. [general tutorial](https://github.com/Dans-labs/text-fabric/blob/master/docs/tutorial.ipynb)
   1. [search tutorial](https://github.com/Dans-labs/text-fabric/blob/master/docs/searchTutorial.ipynb)
   1. [from MQL to search](https://github.com/Dans-labs/text-fabric/blob/master/docs/searchFromMQL.ipynb) if you know already
      [MQL](http://emdros.org)
   1. [exercises](https://github.com/Dans-labs/text-fabric/tree/master/exercises) various Jupyter notebooks, with tasks in the
      Hebrew Bible and the Greek New Testament.
3. For more background information (earlier work, institutes, people, datasets), consult the
   [sources](https://shebanq.ancient-data.org/sources)
   page of SHEBANQ.
4. Papers (preprints on [arxiv](https://arxiv.org)), most of them published:
   1. [Parallel Texts in the Hebrew Bible, New Methods and Visualizations ](https://arxiv.org/abs/1603.01541)
   1. [The Hebrew Bible as Data: Laboratory - Sharing - Experiences](https://arxiv.org/abs/1501.01866)
   1. [LAF-Fabric: a data analysis tool for Linguistic Annotation Framework with an application to the Hebrew Bible](https://arxiv.org/abs/1410.0286)
   1. [Annotation as a New Paradigm in Research Archiving](https://arxiv.org/abs/1412.6069)

   N.B. [LAF-Fabric](https://github.com/Dans-labs/laf-fabric) is a precursor of Text-Fabric.
   Text-Fabric is simpler to use, and has something that LAF-Fabric does not have:
   a powerful structured search engine.

# Data

In order to work with Text-Fabric, you need a dataset to operate on.
Here is a
[collection of datasets and additional modules](https://Dans-labs.github.io/text-fabric-data/)
ready to be used in text-fabric. The link points to the data documentation, and from there you find the GitHub
repo where the data resides.

---

[Motivation](http://www.slideshare.net/dirkroorda/text-fabric) - 
[Data](https://github.com/Dans-labs/text-fabric-data)

