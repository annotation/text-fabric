# text-fabric

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1008899.svg)](https://doi.org/10.5281/zenodo.592193)
![text-fabric](/docs/images/tf.png)


Text-Fabric is several things:

* a *browser* for ancient text corpora
* a Python3 package for processing ancient corpora

A corpus of ancient texts and linguistic annotations represents a large body of knowledge.
Text-Fabric makes that knowledge accessible to non-programmers by means of 
built-in a search interface that runs in your browser.

From there the step to program your own analytics is not so big anymore.
Because you can call the Text-Fabric API from your Python programs, and
it works really well in Jupyter notebooks.
 
# Install

Text Fabric is a Python(3) package on the Python Package Index, so you can install it easily with `pip` from
the command line. Here are the precise
[installation instructions](https://dans-labs.github.io/text-fabric/).

# Use

Provided you have the data repositories for the Hebrew Bible (bhsa) or the Proto-Cuneiform Uruk corpus (cunei)
in place (see below),
you can open a terminal (command prompt), and just say

```sh
text-fabric bhsa
```

or 

```sh
text-fabric cunei
```

After loading the data your browser will open and load the search interface.
There you'll find links to further help.

<p>
<img src="/docs/images/bhsa-app.png"/>
</p>

<p>
<img src="/docs/images/cunei-app.png"/>
</p>

# Documentation

There is extensive documentation.
If you start using the Text-Fabric API in your programs, you'll need it.

Jump off to the [docs](https://dans-labs.github.io/text-fabric/)

1. The [github pages associated with this repo](https://dans-labs.github.io/text-fabric/) are meant as a reference.
   1. It explains the [data model](https://dans-labs.github.io/text-fabric/Model/Data-Model/)
   2. It specifies the [file format](https://dans-labs.github.io/text-fabric/Model/File-formats/)
   3. It holds the [api docs](https://dans-labs.github.io/text-fabric/Api/General/)
2. There are tutorials and exercises to guide you into increasingly involved tasks
   on specific corpora (outside this repo):
   1. [Biblia Hebraica Stuttgartensia Amstelodamensis](https://nbviewer.jupyter.org/github/etcbc/bhsa/blob/master/tutorial/start.ipynb)
   1. [Proto-Cuneiform tablets from Uruk IV/III](https://nbviewer.jupyter.org/github/nino-cunei/tutorials/blob/master/start.ipynb)
3. For more background information (earlier work, institutes, people, datasets), consult the
   [wiki](https://github.com/ETCBC/shebanq/wiki)
   pages of SHEBANQ.
4. Papers (preprints on [arxiv](https://arxiv.org)), most of them published:
   1. [Parallel Texts in the Hebrew Bible, New Methods and Visualizations ](https://arxiv.org/abs/1603.01541)
   1. [The Hebrew Bible as Data: Laboratory - Sharing - Experiences](https://www.ubiquitypress.com/site/chapters/10.5334/bbi.18/)
      (preprint: [arxiv](https://arxiv.org/abs/1501.01866))
   1. [LAF-Fabric: a data analysis tool for Linguistic Annotation Framework with an application to the Hebrew Bible](https://arxiv.org/abs/1410.0286)
   1. [Annotation as a New Paradigm in Research Archiving](https://arxiv.org/abs/1412.6069)

   N.B. [LAF-Fabric](https://github.com/Dans-labs/laf-fabric) is a precursor of Text-Fabric.
   Text-Fabric is simpler to use, and has something that LAF-Fabric does not have:
   a powerful structured search engine.

# Data

In order to work with Text-Fabric, you need a dataset to operate on.
The most developed corpora in TF are

1. [Biblia Hebraica Stuttgartensia Amstelodamensis](https://github/etcbc/bhsa)
1. [Proto-Cuneiform tablets from Uruk IV/III](https://github/nino-cunei/uruk)

There is a also
[collection of datasets and additional modules](https://Dans-labs.github.io/text-fabric-data/)
ready to be used in text-fabric. The link points to the data documentation, and from there you find the GitHub
repo where the data resides.

It is based on

* a minimalistic data model for text plus annotations
* a text file format for such corpora
* and a binary format optimized for processing.

A defining characteristic is that Text-Fabric does not make use of XML or JSON,
but stores text as a bunch of features.
These features are interpreted against a *graph* of nodes and edges, which make up the
abstract fabric of the text.

Based on this model, Text-Fabric offers an API to search, navigate and process text
and its annotations.
The search API works with search templates that define relational patterns
which will be instantiated by nodes and edges of the fabric.

The emphasis of this all is on:

* data processing
* sharing data
* contributing modules
* search for patterns

The intended use case is ancient writings, such as the Hebrew Bible or (Proto)-Cuneifrom tablets.
Also the Greek and Syriac New Testament have been converted to TF.

Text-Fabric not only deals with the text, but also with rich sets of linguistic annotations added to them.
It has been used to construct the website
[SHEBANQ](https://shebanq.ancient-data.org) and it is being
used by researchers to analyse such texts. 

<a target="_blank" href="https://archive.softwareheritage.org/browse/origin/https://github.com/Dans-labs/text-fabric/directory/"><img src="/docs/images/swh-logo-archive.png" width="100" align="left"/></a>

**This repository is being archived continuously by the 
[Software Heritage Archive](https://archive.softwareheritage.org).
If you want to cite snippets of the code of this repository, the Software Archive
offers an easy and elegant way to do so.
As an example, here I quote the 
[*stitching* algorithm](https://archive.softwareheritage.org/swh:1:cnt:6169c074089ddc8a0e048cb67e1fec57857ef54d;lines=3224-3270/),
by means of which Text-Fabric Search collects the solutions of a
[search template](https://dans-labs.github.io/text-fabric/Api/General/#searching).
The quote refers directly to specific lines of code, deeply buried in
a Python file within a particular version of Text-Fabric.**

---

[Motivation](http://www.slideshare.net/dirkroorda/text-fabric) 

