---
title: 'Text-Fabric: Text representation for text with stand-off annotations and linguistic features'
tags:
  - hebrew
  - greek
  - linguistics
  - annotation
  - bible
  - text database
  - data science
authors:
  - name: Dirk Roorda
    email: dirk.roorda@dans.knaw.nl
    affiliation: 1
affiliations:
  - name: Data Archiving and Networked Services
    url: https://dans.knaw.nl/en
    index: 1
date: 07 March 2017
codeRepository: 'https://github.com/ETCBC/text-fabric'
identifier: 'http://doi.org/10.5281/zenodo.242384'
bibliography: README.md 
---

# Summary

Text-Fabric is a Python3 package for Text plus Annotations.

It provides a data model, a text file format, and a binary format for (ancient) text plus (linguistic) annotations.

The emphasis of text-fabric is on:

* data processing
* sharing data
* contributing modules

A defining characteristic is that Text-Fabric does not make use of XML or JSON,
but stores text as a bunch of features.
These features are interpreted against a graph of nodes and edges, which make up the abstract fabric of the text.

