![logo](images/tf.png)

# Text-Fabric

A corpus of ancient texts and (linguistic) annotations represents a large body
of knowledge.
Text-Fabric (TF) makes that knowledge accessible to programmers and non-programmers.

TF is machinery for processing such corpora as annotated graphs.
It treats corpora and annotations as data, much like big tables, but without
losing the rich structure of text, such as embedding and multiple representations.
It deals with text in a state where all markup is gone, but where the complete logical
structure still sits in the data.

Whether a corpus comes from plain texts, OCR output, databases, XML, TEI: TF has support
to convert it to single column files, where each file corresponds with a
*feature* of the text.

The Python library `tf` can be used to collect a bunch of features and display
it as an annotated text.
What ties the features together are natural numbers, that serve to anchor the
elementary positions in the text as well as the relevant structures within the
text.

When TF loads a dataset of features, you can instruct it to get the features
from anywhere.
That means it supports workflows where annotations are produced by third parties
and can be used against the original corpus, *without additional work*.
It also facilitates mappings between ongoing versions of the corpus,
so that annotations made on older versions can be ported to newer versions without
redoing the annotation creation.

## Straight to ...

*   Release notes (`tf.about.releases`)
*   Install (`tf.about.install`)
*   FAQ (`tf.about.faq`)
*   Corpora (`tf.about.corpora`)
*   Browser (`tf.about.browser`)
*   Search Client (`tf.about.clientmanual`) simplified (`tf.about.manual`)
*   Use (`tf.about.use`)
*   Search (`tf.about.searchusage`)
*   Volumes and collections (`tf.about.volumes`)
*   API (`tf.cheatsheet`)
*   Annotation, manual (`tf.about.annotate`)
*   Data sharing (`tf.about.datasharing`)
*   Data Structures and Algorithms
    (`tf.about.datamodel`, `tf.about.searchdesign`, `tf.about.displaydesign`)
*   File Format (`tf.about.fileformats`, `tf.about.optimizations`)
*   Converting to TF (`tf.convert.walker`, `tf.convert.mql`).
    For converting from XML, TEI, PageXML etc. see
    [text-fabric-factory](https://github.com/annotation/text-fabric-factory)
*   Exporting data and re-importing it with enrichments (`tf.convert.recorder`)
*   Dataset manipulation (`tf.dataset.modify` and `tf.dataset.nodemaps.Versions`)
*   Crossing versions of datasets (`tf.dataset.nodemaps`)
*   Code Organization (`tf.about.code`)

## Author

**Author**:
[Dirk Roorda](https://pure.knaw.nl/portal/en/persons/dirk-roorda)

Cite TF as
[DOI: 10.5281/zenodo.592193](https://doi.org/10.5281/zenodo.592193).

## Acknowledgments

TF is a matter of putting a few good ideas by others into practice.

While I wrote most of the code,
a product like TF is unthinkable without the contributions
of avid users that take the trouble to give feedback and file issues,
and have the zeal and stamina to hold on
when things are frustrating and bugs overwhelming,
and give encouragement when they are happy.

In particular thanks to

*   Cale Johnson
*   Camil Staps
*   Christian Højgaard-Jensen
*   Christiaan Erwich
*   Cody Kingham
*   Ernst Boogert
*   Eliran Wong
*   Gyusang Jin
*   James Cuénod
*   Johan de Joode
*   Kyoungsik Kim
*   Martijn Naaijer
*   Oliver Glanz
*   Stephen Ku
*   Willem van Peursen

<img src="images/huc.png" width="200"> 2022-now

<img src="images/DANS-logo.png" width="200"> 2014-2022

Special thanks to Henk Harmsen for nudging me into a corner
where I was exposed to the Hebrew Text Database, and for letting me play
there for almost longer than could be defended.

And to Andrea Scharnhorst for understanding and encouragement on this path.

## More resources

Tutorials:

*   [BHSA](https://nbviewer.jupyter.org/github/ETCBC/bhsa/blob/master/tutorial/start.ipynb)
*   [DSS](https://nbviewer.jupyter.org/github/ETCBC/dss/blob/master/tutorial/start.ipynb)
*   [OldBabylonian](https://nbviewer.jupyter.org/github/Nino-cunei/oldbabylonian/blob/master/tutorial/start.ipynb)
*   [OldAssyrian](https://nbviewer.jupyter.org/github/Nino-cunei/oldassyrian/blob/master/tutorial/start.ipynb)
*   [Uruk](https://nbviewer.jupyter.org/github/Nino-cunei/uruk/blob/master/tutorial/start.ipynb)
*   [Quran](https://nbviewer.jupyter.org/github/q-ran/quran/blob/master/tutorial/start.ipynb)
*   and more via `tf.about.corpora`.

---

Papers:

*   (2018) [Text-Fabric: handling Biblical data withIKEA logistics](https://tidsskrift.dk/hiphilnovum/article/view/142740/186442)
*   (2018) [Coding the Hebrew Bible](https://doi.org/10.1163/24523666-01000011)
*   (2017) [The Hebrew Bible as Data: Laboratory - Sharing - Experiences](https://www.ubiquitypress.com/site/chapters/10.5334/bbi.18/)
     (preprint: [arxiv](https://arxiv.org/abs/1501.01866))
*   (2016) [Parallel Texts in the Hebrew Bible, New Methods and Visualizations ](https://arxiv.org/abs/1603.01541)
*   (2014) [LAF-Fabric: a data analysis tool for Linguistic Annotation Framework with an application to the Hebrew Bible](https://arxiv.org/abs/1410.0286)
*   (2012) [Annotation as a New Paradigm in Research Archiving](https://arxiv.org/abs/1412.6069)

---

Presentations:

*   (Lorentz Leiden 2020)
    [Hands on with Dead Sea Scrolls, Old Babylonian Tablets, and the Quran](https://nbviewer.jupyter.org/github/annotation/text-fabric/blob/master/conferences/Lorentz2020/start.ipynb)
    and
    [Text-Fabric in Context](https://github.com./annotation/text-fabric/blob/master/conferences/Lorentz2020/TF-in-context.pdf)

*   (Cambridge 2019, with Cody Kingham)
    [Data Analysis in Ancient Corpora](https://github.com./annotation/text-fabric/blob/master/conferences/Cambridge2019/ancient-corpora-analysis.pdf)

*   (San Antonio 2016)
    [Text-Fabric](https://github.com./annotation/text-fabric/blob/master/conferences/SBL2016/Text-Fabric.pdf),
    A motivational presentation given just before
    [SBL 2016](https://www.sbl-site.org/meetings/Congresses_Abstracts.aspx?MeetingId=29)
    in the Lutheran Church of San Antonio.
    The day after this presentation, during the SBL conference, sitting in one
    of the broad corridors of the building, I started with the first code of
    Text-Fabric: reading and writing TF-feature files, somewhat like
    [here](https://github.com/annotation/text-fabric/blob/94ddafd955a5042f565229151dc88db9333cfabd/tf/data.py).
