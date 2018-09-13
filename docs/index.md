![logo](/images/tficon-small.png)
![logo](/images/tf.png)

# Text-Fabric

## About

Before diving head-on into Text-Fabric, you might want to read a bit more about
what it is and where it came from. And after it, if you want to cite it, use this
[DOI: 10.5281/zenodo.592193](https://doi.org/10.5281/zenodo.592193).

??? abstract "Intro"
    Text-Fabric is several things:

    * a *browser* for ancient text corpora
    * a Python3 package for processing ancient corpora

    A corpus of ancient texts and linguistic annotations represents a large body of knowledge.
    Text-Fabric makes that knowledge accessible to non-programmers by means of 
    built-in a search interface that runs in your browser.

    From there the step to program your own analytics is not so big anymore.
    Because you can call the Text-Fabric API from your Python programs, and
    it works really well in Jupyter notebooks.
 
??? abstract "Factory"
    Text-Fabric can be and has been used to construct websites,
    for example [SHEBANQ](https://shebanq.ancient-data.org).
    In the case of SHEBANQ, data has been converted to mysql databases.
    However, with the built-in [TF kernel](/Server/Kernel), it is also possible to
    have one process serve multiple connections and requests.

??? note "Code statistics"
    For a feel of the size of this project, in terms of lines of code,
    see [Code lines](/Code/Stats)

??? abstract "Design principles"
    There are a number of things that set Text-Fabric apart from most other ways to encode 
    corpora.

    ??? abstract "Minimalistic model"
        Text-Fabric is based on a minimalistic data model for text plus annotations.

        A defining characteristic is that Text-Fabric does not make use of XML or JSON,
        but stores text as a bunch of features in plain text files.

        These features are interpreted against a *graph* of nodes and edges, which make up the
        abstract fabric of the text.

    ??? abstract "Performance matters"
        Based on this model, Text-Fabric offers a [processing API](/Api/General/)
        to search, navigate and process text and its annotations.
        A lot of care has been taken to make this API work as fast as possible.
        Efficiency in data processing has been a design criterion from the start.

        See e.g. the comparisons between the Text-Fabric way of serializing (pickle + gzip)
        and
        [avro](https://nbviewer.jupyter.org/github/dans-labs/text-fabric/blob/master/test/avro/avro.ipynb),
        [joblib](https://nbviewer.jupyter.org/github/dans-labs/text-fabric/blob/master/test/joblib/joblib.ipynb), and
        [marshal](https://nbviewer.jupyter.org/github/dans-labs/text-fabric/blob/master/test/marshal/marshal.ipynb).

    ??? abstract "Search for patterns"
        The [search API](/Api/General/#searching)
        works with search templates that define relational patterns
        which will be instantiated by nodes and edges of the fabric.

    ??? abstract "Pick and choose data"
        Students can selectively
        [load](/Api/General/#loading)
        the feature data they need.
        When the time comes to share the fruits of their thought,
        they can do so in various ways:

        * when using the TF browser, results can be exported as PDF and stored
          in a repository;
        * when programming in a notebook, these notebooks can easily be shared online
          by using GitHub of NBViewer.

    ??? abstract "Contributing data"
        Researchers can easily
        [produce new data modules](/Api/General/#saving-features)
        of text-fabric data out of their findings.

??? abstract "Author and co-creation"
    Text-Fabric is not so much an original idea as well putting a few good ideas by others
    into practice.
    The idea for the Text-Fabric data model ultimately derives from ideas floating
    in the ETCBC-avant-la-lettre 30 years ago, culminating in 
    [Crist-Jan Doedens's Ph.D. thesis](https://books.google.nl/books/about/Text_Databases.html?id=9ggOBRz1dO4C&redir_esc=y).
    The fact that Ulrik Sandborg Petersen has made these ideas practical in his
    [Emdros database system](https://emdros.org) 15 years ago was the next crucial step.

    But time moves on, and nowhere is that felt as keenly as in computing science.
    Programming has become easier, humanists become better programmers, and personal computers have become powerful
    enough to do a sizable amount of data science on them.

    That leads to exciting *tipping points*:

    > In sociology, a tipping point is a point in time when a group - or
      a large number of group members — rapidly and dramatically changes
      its behavior by widely adopting a previously rare practice.

    > [WikiPedia](https://en.wikipedia.org/wiki/Tipping_point_(sociology))

    **Text-Fabric is an attempt to tip the scales** by providing digital humanists with the
    functions they need *now*, based on technology that appeals *now*.

    Hence, my implementation of Text-Fabric search has been done from the ground up,
    and uses a strategy that is very different from Ulrik's MQL search engine.

    [Dirk Roorda](https://dans.knaw.nl/en/about/organisation-and-policy/staff/roorda?set_language=en)


??? abstract "Acknowledgements"
    While I wrote most of the code, a product like Text-Fabric is unthinkable without
    the contributions of avid users that take the trouble to give feedback and file issues,
    and have the zeal and stamina to hold on when things are frustrating and bugs overwhelming.

    In particular I thank

    * Martijn Naaijer
    * Cody Kingham
    * Christiaan Erwich
    * Cale Johnson
    * Christian Høygaard-Jensen
    * Camil Staps
    * Stephen Ku
    * James Cuénod
    * Johan de Joode
    * Gyusang Jin
    * Kyoungsik Kim
    * Ernst Boogert

??? explanation "History"
    The foundational ideas derive from work done in and around the
    [ETCBC](http://etcbc.nl)
    by Eep Talstra, Crist-Jan Doedens, Henk Harmsen, Ulrik Sandborg-Petersen
    and many others.

    The author entered in that world in 2007 as a 
    [DANS](https://www.dans.knaw.nl) employee, doing a joint small data project,
    and a bigger project SHEBANQ in 2013/2014.
    In 2013 I developed
    [LAF-Fabric](https://github.com/Dans-labs/laf-fabric)
    in order to be able to construct the website
    [SHEBANQ](https://shebanq.ancient-data.org).

    I have taken out everything that makes LAF-Fabric complicated and
    all things that are not essential for the sake of raw data processing.

## Getting started

[Installation](/Install)

[Use](/Use)

## Documentation

There is extensive documentation here.

If you start using the Text-Fabric API in your programs, you'll definitely need it.

If you are just starting with the Text-Fabric browser, it might help to
look at the online tutorials for the BHSA and the Cunei corpus to see what
Text-Fabric can reveal about the data.

??? abstract "Tutorials"
    There are tutorials and exercises to guide you into increasingly involved tasks
    on specific corpora (outside this repo):

    * [Biblia Hebraica Stuttgartensia Amstelodamensis](https://nbviewer.jupyter.org/github/etcbc/bhsa/blob/master/tutorial/start.ipynb)
    * [Proto-Cuneiform tablets from Uruk IV/III](https://nbviewer.jupyter.org/github/nino-cunei/tutorials/blob/master/start.ipynb)

    These links point to the *static* online versions.
    If you want to get these Jupyter notebooks on your system in order to execute them yourself, 
    you can download them from a release:

    * [BHSA tutorial download](https://github.com/ETCBC/bhsa/releases/download/1.3/tutorial.zip)
    * [Cunei tutorial download](https://github.com/Nino-cunei/tutorials/releases/download/v1.0.0/tutorial.zip)

    These are zip files, you can unpack them where you want.
    You have to have Jupyter installed.

??? note "Concepts"
    The conceptual model of Text-Fabric and how it is realized in a data model and an optimized file format.

    * [data model](/Model/Data-Model/)
    * [file format](/Model/File-formats/)
    * [optimizations](/Model/Optimizations/)
    * [search design](/Model/Search/)

??? note "API Reference"
    Text-Fabric offers lots of functionality that works for all corpora.
    Corpus designers can add *apps* to Text-Fabric that enhance its behaviours,
    especially in displaying the corpus in ways that make sense to people that study the corpus.

    * [TF api](/Api/General/)
    * [TF apps](/Api/Apps/)
    * [Bhsa app for the Hebrew Bible](/Api/Bhsa/)
    * [Cunei app for the Proto-cuneiform tablets from Uruk](/Api/Cunei/)
   
??? note "Papers"
    Papers (preprints on [arxiv](https://arxiv.org)), most of them published:

    * [Coding the Hebrew Bible](https://doi.org/10.1163/24523666-01000011)
    * [Parallel Texts in the Hebrew Bible, New Methods and Visualizations ](https://arxiv.org/abs/1603.01541)
    * [The Hebrew Bible as Data: Laboratory - Sharing - Experiences](https://www.ubiquitypress.com/site/chapters/10.5334/bbi.18/)
       (preprint: [arxiv](https://arxiv.org/abs/1501.01866))
    * [LAF-Fabric: a data analysis tool for Linguistic Annotation Framework with an application to the Hebrew Bible](https://arxiv.org/abs/1410.0286)
    * [Annotation as a New Paradigm in Research Archiving](https://arxiv.org/abs/1412.6069)

??? note "Presentation"
    Here is a motivational
    [presentation](http://www.slideshare.net/dirkroorda/text-fabric),
    given just before
    [SBL 2016](https://global-learning.org/mod/forum/discuss.php?d=22)
    in the Lutheran Church of San Antonio.
