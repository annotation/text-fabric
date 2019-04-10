<img src="/docs/images/tf-small.png" align="left"/>

# Text-Fabric

[![sha](sha.png) Software Heritage Archive](https://archive.softwareheritage.org/browse/origin/https://github.com/annotation/text-fabric/)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1008899.svg)](https://doi.org/10.5281/zenodo.592193)

[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/2592/badge)](https://bestpractices.coreinfrastructure.org/projects/2592)

Text-Fabric is several things:

* a *browser* for ancient text corpora
* a Python3 package for processing ancient corpora

A corpus of ancient texts and linguistic annotations represents a large body of knowledge.
Text-Fabric makes that knowledge accessible to non-programmers by means of 
built-in a search interface that runs in your browser.

From there the step to program your own analytics is not so big anymore.

You can export your results to Excel and work with them from there.

And if that is not enough,
you can call the Text-Fabric API from your Python programs.
This works really well in Jupyter notebooks.
 
# Apps

It is possible to prepare a dataset in TF format and extend Text-Fabric with an *app*
that has further knowledge of that specific dataset.

A TF-app takes care of automatic downloading of the dataset and it supports the Text-Fabric browser.

[Current TF apps](https://annotation.github.io/text-fabric/About/Corpora/)

# Install

Text Fabric is a Python(3) package on the Python Package Index, so you can install it easily with `pip` from
the command line. Here are the precise
[installation instructions](https://annotation.github.io/text-fabric/).

# Use

## On Windows?

You can click the Start Menu, and type `text-fabric bhsa` or `text-fabric uruk`
in the search box, and then Enter.

## On Linux or Macos?
You can open a terminal (command prompt), and just say

```sh
text-fabric bhsa
```

or 

```sh
text-fabric uruk
```

The corpus data will be downloaded automatically,
and be loaded into text-fabric.
Then your browser will open and load the search interface.
There you'll find links to further help.

# Documentation

There is extensive documentation.
If you start using the Text-Fabric API in your programs, you'll need it.

Jump off to the [docs](https://annotation.github.io/text-fabric/)

# Data

In order to work with Text-Fabric, you need a dataset to operate on.
Such a data set must be in TF format.

If you have digital text that you control, in whatever format, and want to
convert it to *tf*,
Text-Fabric meets you half-way.

If you walk through the source, and tell TF what you see, it will pick that
up and compile a valid TF dataset out of it.

See the [conversion tutorial](https://nbviewer.jupyter.org/github/annotation/tutorials/blob/master/text-fabric/convert.ipynb).

# Contributing

Want to contribute?

Start with the [contribution notes](codestyle/contributing.md).

---

<a target="_blank" href="https://archive.softwareheritage.org/browse/origin/https://github.com/annotation/text-fabric/directory/"><img src="/docs/images/sha-logo.png" width="100" align="left"/></a>

**This repository is being archived continuously by the 
[Software Heritage Archive](https://archive.softwareheritage.org).
If you want to cite snippets of the code of this repository, the Software Archive
offers an easy and elegant way to do so.
As an example, here I quote the 
[*stitching* algorithm](https://archive.softwareheritage.org/swh:1:cnt:6169c074089ddc8a0e048cb67e1fec57857ef54d;lines=3224-3270/),
by means of which Text-Fabric Search collects the solutions of a
[search template](https://annotation.github.io/text-fabric/Use/Search/).
The quote refers directly to specific lines of code, deeply buried in
a Python file within a particular version of Text-Fabric.**
