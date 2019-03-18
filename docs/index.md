![logo](images/tf-small.png)

# Text-Fabric

## About

Before diving head-on into Text-Fabric, you might want to read a bit more about
what it is and where it came from. And after it, if you want to cite it, use this
[DOI: 10.5281/zenodo.592193]({{tfdoi}}).

??? abstract "Intro"
    Text-Fabric is several things:

    * a *browser* for ancient text corpora
    * a Python3 package for processing ancient corpora
    * a tool to contribute additional research data to corpora

    A corpus of ancient texts and linguistic annotations represents a large body of knowledge.
    Text-Fabric makes that knowledge accessible to non-programmers by means of a
    built-in a search interface that runs in your browser.

    From there the step to program your own analytics is not so big anymore.

    You can
    [export](Use/Browser.md#work-with-exported-results)
    your results to Excel and work with them from there.

    And if that is not enough,
    you can call the Text-Fabric API from your Python programs.
    This works really well in Jupyter notebooks.

??? abstract "Apps"
    When the generic functions of TF are not enough, *apps* come into play.
    TF offers an API for apps that contain custom code for the display
    of specific corpora.
    Apps can also make use of functions to retrieve online data that has been
    added later as the results of research.

    * [current TF apps](About/Corpora.md)
    * [app-api](Api/App.md)
    * [implementation](Implementation/Apps.md)

??? abstract "Capabilities"
    ???+ abstract "Search for patterns"
        The [search API](Api/Search.md#search)
        works with search templates that define relational patterns
        which will be instantiated by nodes and edges of the big fabric of the corpus.

    ???+ abstract "Pick and choose data"
        Students can selectively
        [load](Api/Fabric.md#loading)
        the feature data they need.
        When the time comes to share the fruits of their thought,
        they can do so in various ways:

        * when using the TF browser, results can be
          [exported](Use/Browser.md#work-with-exported-results) as a PDF
          plus a zip archive of tab separated files and stored in a repository;
        * when programming in a notebook, these notebooks can easily be shared online
          by using GitHub or NBViewer.

    ???+ abstract "Contributing data"
        Researchers can easily
        produce new data [features](Api/Fabric.md#saving-features)
        of text-fabric data out of their findings.

        They can package their new data into modules and
        [distribute](Api/Data.md) it to GitHub.
        Other people can use that data just by mentioning the GitHub location.
        Text-Fabric will auto-load it for them.

    ???+ abstract "Factory"
        Text-Fabric can be and has been used to construct websites,
        for example [SHEBANQ]({{shebanq}}).
        In the case of SHEBANQ, data has been converted to mysql databases.
        However, with the built-in [TF kernel](Server/Kernel.md),
        it is also possible to TF itself as a database to
        serve multiple connections and requests.

??? abstract "Design principles"
    There are a number of things that set Text-Fabric apart from most other ways to encode 
    corpora.

    ???+ abstract "Minimalistic model"
        Text-Fabric is based on a minimalistic data model for text plus annotations.

        A defining characteristic is that Text-Fabric 
        stores text as a bunch of features in plain text files.

        These features are interpreted against a *graph* of nodes and edges,
        which make up the abstract fabric of the text.

        A graph is a more general concept than a tree.
        Whilst trees are ubiquitous in linguistic analysis,
        there is much structure in a corpus that is not strictly tree-like.

        Therefore, we do not adopt technologies
        that have the tree as their first class data model.
        Hence, almost by definition, Text-Fabric does not make use of XML technology.

    ???+ abstract "Performance matters"
        Based on this model, Text-Fabric offers a [processing API](Api/Fabric.md)
        to search, navigate and process text and its annotations.
        A lot of care has been taken to make this API work as fast as possible.
        Efficiency in data processing has been a design criterion from the start.

        ??? example "Comparisons"
            See e.g. the comparisons between the Text-Fabric way of serializing
            (pickle + gzip) and
            [avro]({{tfnb}}/test/avro/avro.ipynb),
            [joblib]({{tfnb}}/test/joblib/joblib.ipynb), and
            [marshal]({{tfnb}}/test/marshal/marshal.ipynb).

    ???+ note "Code organization and statistics"
        To get an impression of the software that is Text-Fabric,
        in terms of organization and size, see
        [Code](Code/Overview.md) and [lines](Code/Stats.md).

??? abstract "History"
    The foundational ideas derive from work done in and around the
    [ETCBC]({{etcbc}}) avant-la-lettre from 1970 onwards
    by Eep Talstra,
    Crist-Jan Doedens, ([Ph.D. thesis]({{doedens}})),
    Henk Harmsen, Ulrik Sandborg-Petersen ([Emdros]({{emdros}})),
    and many others.

    I entered in that world in 2007 as a 
    [DANS]({{dans}}) employee, doing a joint small data project,
    and a bigger project SHEBANQ in 2013/2014.
    In 2013 I developed
    [LAF-Fabric]({{lfgh}})
    as a tool for constructing the website
    [SHEBANQ]({{shebanq}}).

    ???+ explanation "House cleaning"
        LAF-Fabric is based on the ISO standard
        [Linguistic Annotation Framework (LAF)](https://www.iso.org/standard/37326.html).
        LAF is an attempt to marry graph models to the 
        [Text Encoding Initiative (TEI)](http://www.tei-c.org) which lives in XML.
        It is a good try, but it turns out that using XML technology for
        graphs is a pain. All the usual advantages of using the XML toolchain evaporate.

        So I decided to leave XML and its associated syntactical complexity.
        While I was at it, I took out everything that makes LAF-Fabric complicated and
        all things that are not essential for the sake of raw data processing.
        That became Text-Fabric version 1 at the end of 2016.

        It turned out that this move has freed the way to work towards higher-level goals:

        * a new search engine (inspired by [MQL]({{emdros}}) and
        * support for research data workflows.

        [Version 7](Use/Use7.md) capitalizes on the latter.

    ???+ explanation "State of the art"
        Time moves on, and nowhere is that felt as keenly as in computing science.
        Programming has become easier, humanists become better programmers,
        and personal computers have become powerful
        enough to do a sizable amount of data science on them.

        That leads to exciting *tipping points*:

        > In sociology, a tipping point is a point in time when a group - or
          a large number of group members — rapidly and dramatically changes
          its behavior by widely adopting a previously rare practice.

        > [WikiPedia]({{wikip}}/Tipping_point_(sociology))

        **Text-Fabric is an attempt to tip the scales** by providing digital humanists with the
        functions they need *now*, based on technology that appeals *now*.

        Hence, my implementation of Text-Fabric search has been done from the ground up,
        and uses a strategy that is very different from Ulrik's MQL search engine.

??? abstract "Author and acknowledgements"
    **Author**:
    [Dirk Roorda]({{dans}}/about/organisation-and-policy/staff/roorda?set_language=en)

    Text-Fabric is a matter of putting a few good ideas by others into practice.

    ???+ explanation "Co-creation"
        In version 7, the idea of co-creation becomes fully tangible:
        Text-Fabric does not only work with a few curated corpora,
        but it allows you to add your own data in a seamless way.
        So you when you do research,
        you have the fruits of many people's work at your finger tips.

    ???+ explanation "Acknowledgements"
        While I wrote most of the code,
        a product like Text-Fabric is unthinkable without the contributions
        of avid users that take the trouble to give feedback and file issues,
        and have the zeal and stamina to hold on
        when things are frustrating and bugs overwhelming,
        and give encouragement when they are happy.

        In particular I thank

        * Andrea Scharnhorst
        * Cale Johnson
        * Camil Staps
        * Christian Høygaard-Jensen
        * Christiaan Erwich
        * Cody Kingham
        * Ernst Boogert
        * Eliran Wong
        * Gyusang Jin
        * Henk Harmsen
        * James Cuénod
        * Johan de Joode
        * Kyoungsik Kim
        * Martijn Naaijer
        * Stephen Ku
        * Wido van Peursen

## Getting started

[Installation](About/Install.md)

[Use](Use/Use.md)

## Existing users

Read the [version 7 guide](Use/Use7.md)

## Documentation

There is extensive documentation here.

If you start using the Text-Fabric API in your programs, you'll definitely need it.

If you are just starting with the Text-Fabric browser,
consult the [Search guide](Use/Search.md) first.
It might also help to look at the online tutorials for
the app-supported [annotated corpora]({{an}})
to see what Text-Fabric can reveal about the data.

??? note "Concepts"
    The conceptual model of Text-Fabric and how it is realized in a data model and an optimized file format.

    * [data model](Model/Data-Model.md)
    * [file format](Model/File-formats.md)
    * [optimizations](Model/Optimizations.md)
    * [search design](Model/Search.md)

??? note "API Reference"
    Text-Fabric offers lots of functionality that works for all corpora.
    Corpus designers can add *apps* to Text-Fabric that enhance its behaviours,
    especially in displaying the corpus in ways that make sense to people that study the corpus.

    * [TF apps](Api/App.md)
    * [TF api](Api/Fabric.md)

    See also [Corpora](About/Corpora.md)
   
??? note "Papers"
    Papers (preprints on [arxiv]({{arxiv}})), most of them published:

    * [Coding the Hebrew Bible]({{codingdoi}})
    * [Parallel Texts in the Hebrew Bible, New Methods and Visualizations ]({{arxiv4}})
    * [The Hebrew Bible as Data: Laboratory - Sharing - Experiences]({{ubiq1}})
       (preprint: [arxiv]({{arxiv1}}))
    * [LAF-Fabric: a data analysis tool for Linguistic Annotation Framework with an application to the Hebrew Bible]({{arxiv2}})
    * [Annotation as a New Paradigm in Research Archiving]({{arxiv3}})

??? note "Presentation"
    Here is a motivational
    [presentation]({{pres1}}),
    given just before
    [SBL 2016]({{sbl1}})
    in the Lutheran Church of San Antonio.

