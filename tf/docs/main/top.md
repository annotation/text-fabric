![logo](images/tf.png)

# Text-Fabric

A corpus of ancient texts and (linguistic) annotations represents a large body of knowledge.
Text-Fabric makes that knowledge accessible to programmers and non-programmers.

Text-Fabric is machinery for processing such corpora as annotated graphs.
It treats corpora and annotations as data, much like big tables, but without
loosing the rich structure of text, such as embedding and multiple representations.
It deals with text in a state where all markup is gone, but where the complete logical
structure still sits in the data.

Whether a corpus comes from plain texts, OCR output, databases, XML, TEI: Text-Fabric has support
to convert it to single column files, where each file corresponds with a *feature* of the text.

The Python library `tf` can be used to collect a bunch of features and display it as an annotated text.
What ties the features together are natural numbers, that serve to anchor the elementary positions
in the text as well as the relevant structures within the text.

When Text-Fabric loads a dataset of features, you can instruct it to get the features from anywhere.
That means it supports workflows where annotations are produced by third parties
and can be used against the original corpus, *without additional work*.
It also facilitates mappings between ongoing versions of the corpus,
so that annotations made on older versions can be ported to newer versions without
redoing the annotation creation.

## Straight to ...

* Release notes (`tf.about.releases`)
* Install (`tf.about.install`)
* FAQ (`tf.about.faq`)
* Browser (`tf.about.browser`)
* Search Client (`tf.about.clientmanual`) simplified (`tf.about.manual`)
* Use (`tf.about.use`)
* Volumes and collections (`tf.about.volumes`)
* Search (`tf.about.searchusage`)
* API (`tf.cheatsheet`)
* Corpora (`tf.about.corpora`)
* Data sharing (`tf.about.datasharing`)
* Data Structures and Algorithms
  (`tf.about.datamodel`, `tf.about.searchdesign`, `tf.about.displaydesign`)
* File Format (`tf.about.fileformats`, `tf.about.optimizations`)
* Converting to TF (`tf.convert.walker`, `tf.convert.mql`)
* Exporting data and reimporting it with enrichments (`tf.convert.recorder`)
* Dataset manipulation (`tf.dataset.modify` and `tf.dataset.nodemaps.Versions`)
* Crossing versions of datasets (`tf.dataset.nodemaps`)
* Code Organisation (`tf.about.code`)

## Author

**Author**:
[Dirk Roorda](https://pure.knaw.nl/portal/en/persons/dirk-roorda)

Cite Text-Fabric as
[DOI: 10.5281/zenodo.592193](https://doi.org/10.5281/zenodo.592193).

## Acknowledgements

Text-Fabric is a matter of putting a few good ideas by others into practice.

While I wrote most of the code,
a product like Text-Fabric is unthinkable without the contributions
of avid users that take the trouble to give feedback and file issues,
and have the zeal and stamina to hold on
when things are frustrating and bugs overwhelming,
and give encouragement when they are happy.

In particular thanks to

* Cale Johnson
* Camil Staps
* Christian Høygaard-Jensen
* Christiaan Erwich
* Cody Kingham
* Ernst Boogert
* Eliran Wong
* Gyusang Jin
* James Cuénod
* Johan de Joode
* Kyoungsik Kim
* Martijn Naaijer
* Oliver Glanz
* Stephen Ku
* Willem van Peursen

<img src="images/huc.png" width="200"> 2022-now

<img src="images/DANS-logo.png" width="200"> 2014-2022

Special thanks to Henk Harmsen for nudging me into a corner
where I was exposed to the Hebrew Text Database, and for letting me play
there for almost longer than could be defended.

And to Andrea Scharnhorst for understanding and encouragement on this path.

## More resources

Tutorials:

* [BHSA](https://nbviewer.jupyter.org/github/etcbc/bhsa/blob/master/tutorial/start.ipynb)
* [DSS](https://nbviewer.jupyter.org/github/etcbc/dss/blob/master/tutorial/start.ipynb)
* [OldBabylonian](https://nbviewer.jupyter.org/github/Nino-cunei/oldbabylonian/blob/master/tutorial/start.ipynb)
* [OldAssyrian](https://nbviewer.jupyter.org/github/Nino-cunei/oldassyrian/blob/master/tutorial/start.ipynb)
* [Uruk](https://nbviewer.jupyter.org/github/Nino-cunei/uruk/blob/master/tutorial/start.ipynb)
* [Q'uran](https://nbviewer.jupyter.org/github/q-ran/quran/blob/master/tutorial/start.ipynb)
* and more via `tf.about.corpora`.

---

Papers:

* [Coding the Hebrew Bible](https://doi.org/10.1163/24523666-01000011)
* [Parallel Texts in the Hebrew Bible, New Methods and Visualizations ](https://arxiv.org/abs/1603.01541)
* [The Hebrew Bible as Data: Laboratory - Sharing - Experiences](https://www.ubiquitypress.com/site/chapters/10.5334/bbi.18/)
   (preprint: [arxiv](https://arxiv.org/abs/1501.01866))
* [LAF-Fabric: a data analysis tool for Linguistic Annotation Framework with an application to the Hebrew Bible](https://arxiv.org/abs/1410.0286)
* [Annotation as a New Paradigm in Research Archiving](https://arxiv.org/abs/1412.6069)

---

Presentations:

[Hands on with Dead Sea Scrolls, Old Babylonian Tablets, and the Q'uran](https://nbviewer.jupyter.org/github/annotation/tutorials/blob/master/lorentz2020/start.ipynb)
(Lorentz Leiden 2020)

[Text-Fabric in Context](https://www.slideshare.net/dirkroorda/tf-incontext) (Lorentz Leiden 2020)

[Data Analysis in Ancient Corpora](https://www.slideshare.net/dirkroorda/ancient-corpora-analysis) (Cambridge 2019, with Cody Kingham)

[Text-Fabric as IKEA logistics](https://nbviewer.jupyter.org/github/etcbc/lingo/blob/master/presentations/Copenhagen2018.ipynb) (Copenhagen 2017)

Here is a motivational [presentation](http://www.slideshare.net/dirkroorda/text-fabric), given just before [SBL 2016](https://global-learning.org/mod/forum/discuss.php?d=22)
in the Lutheran Church of San Antonio.
