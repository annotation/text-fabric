![logo](/images/tf.png)

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
the command line.

???+ abstract "Python"
    Install or upgrade [Python3](https://www.python.org/downloads/) on your system to at least version 3.6.

??? hint "Jupyter"
    Optionally install [Jupyter](http://jupyter.org) as well:

    ```sh
    pip3 install jupyter
    ```

    ???+ hint "Jupyter Lab"
        *Jupyter lab* is a nice context to work with Jupyter notebooks.
        Recommended for working with the
        the tutorials of Text-Fabric.
        Also when you want to copy and paste cells from one notebook
        to another.

        ```sh
        pip3 install jupyterlab
        jupyter labextension install jupyterlab-toc
        ```

        The toc-extension is handy to get an overview
        when working with the lengthy tutorial. It will create an extra
        tab in the Jupyter Lab interface with a table of contents of the
        current notebook.

???+ abstract "Text-Fabric"
    Install Text-Fabric:

    ```sh
    pip3 install text-fabric
    ```

# Get corpora

There are a few corpora in Text-Fabric that are being supported
with extra modules.

??? abstract "Hebrew Bible"
    Get the corpus:

    ```sh
    cd ~/github/etcbc
    git clone https://github.com/etcbc/bhsa
    ```

??? abstract "Cuneiform tablets from Uruk"
    Get the corpus:

    ```sh
    cd ~/github/Nino-cunei
    git clone https://github.com/Nino-cunei/uruk
    ```

??? hint "More"
    The
    [Greek](https://github.com/Dans-labs/text-fabric-data/tree/master/greek/sblgnt) and
    [Syriac](https://github.com/ETCBC/linksyr/tree/master/data/tf/syrnt)
    New Testament have been converted to TF.

    We have example corpora in Sanskrit, and Babylonian.

    ```sh
    cd ~/github
    git clone https://github.com/etcbc/linksyr
    ```

    ```sh
    cd ~/github
    git clone https://github.com/Dans-labs/text-fabric-data
    ```

    All these are not supported by extra innterfaces.

# Use the built-in search interface

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
<img src="images/bhsa-app.png" width="45%"/>
&nbsp;
&nbsp;
<img src="images/cunei-app.png" width="45%"/>
</p>

???+ hint "Multiple windows"
    After you have issued the `text-fabric` command, you can open many connections
    in different browsers and windows and tabs.
    They all use the same data, which only gets loaded when the command `text-fabric` is run.
    If you leave it on all day, you have instant access to the data.

??? hint "Close"
    You can close the data server by pressing Ctrl-C in the terminal where you have
    started `text-fabric` up.

# Documentation

There is extensive documentation.
If you start using the Text-Fabric API in your programs, you'll need it.

??? note "Reference"
    The pages you are reading now are the reference docs.
    * It explains the [data model](https://dans-labs.github.io/text-fabric/Model/Data-Model/)
    * It specifies the [file format](https://dans-labs.github.io/text-fabric/Model/File-formats/)
    * It holds the [api docs](https://dans-labs.github.io/text-fabric/Api/General/)
   
???+ note "Tutorials"
    There are tutorials and exercises to guide you into increasingly involved tasks
    on specific corpora (outside this repo):
    * [Biblia Hebraica Stuttgartensia Amstelodamensis](https://nbviewer.jupyter.org/github/etcbc/bhsa/blob/master/tutorial/start.ipynb)
    * [Proto-Cuneiform tablets from Uruk IV/III](https://nbviewer.jupyter.org/github/nino-cunei/tutorials/blob/master/start.ipynb)

??? note "Background"
    For more background information (earlier work, institutes, people, datasets), consult the
    [wiki](https://github.com/ETCBC/shebanq/wiki) pages of SHEBANQ.

??? note "Papers"
    Papers (preprints on [arxiv](https://arxiv.org)), most of them published:
    * [Parallel Texts in the Hebrew Bible, New Methods and Visualizations ](https://arxiv.org/abs/1603.01541)
    * [The Hebrew Bible as Data: Laboratory - Sharing - Experiences](https://www.ubiquitypress.com/site/chapters/10.5334/bbi.18/)
       (preprint: [arxiv](https://arxiv.org/abs/1501.01866))
    * [LAF-Fabric: a data analysis tool for Linguistic Annotation Framework with an application to the Hebrew Bible](https://arxiv.org/abs/1410.0286)
    * [Annotation as a New Paradigm in Research Archiving](https://arxiv.org/abs/1412.6069)


# Getting started with the API

Start programming: write a python script or code in the Jupyter notebook

```sh
cd somewhere-else
jupyter notebook
```

Enter the following text in a code cell

```python
from tf.fabric import Fabric
TF = Fabric(modules=['my/dataset'])
api = TF.load('sp lex')
api.makeAvailableIn(globals())
```

??? note "locations"
    Maybe you have to tell Text-Fabric exactly where your data is.
    If you have the data in a directory `text-fabric-data`
    under your home directory  or under `~/github`, Text-Fabric can find it.
    In your `modules` argument you then specify one or more subdirectories of
    `text-fabric-data`.

??? abstract "Using Hebrew data"
    To get started with the Hebrew corpus, use its tutorial in the BHSA repo:
    [start](http://nbviewer.jupyter.org/github/etcbc/bhsa/blob/master/tutorial/start.ipynb).

    Or go straight to the
    [bhsa-api-docs](/Api/Bhsa).

??? abstract "Using Cuneiform data"
    To get started with the Uruk corpus, use its tutorial in the Nino-cunei repo:
    [start](http://nbviewer.jupyter.org/github/nino-cunei/tutorials/blob/master/start.ipynb).

    Or go straight to the
    [cunei-api-docs](/Api/Cunei).

# Design principles

??? abstract "Minimalistic model"
    Text-Fabric is based on a minimalistic data model for text plus annotations.

    A defining characteristic is that Text-Fabric does not make use of XML or JSON,
    but stores text as a bunch of features in plain text files.

    These features are interpreted against a *graph* of nodes and edges, which make up the
    abstract fabric of the text.

??? abstract "Processing API"
    [efficient data processing](/Api/General/)
    Based on this model, Text-Fabric offers an API to search, navigate and process text
    and its annotations.

??? abstract "Graph search"
    [search for patterns](/Api/General/#searching)
    The search API works with search templates that define relational patterns
    which will be instantiated by nodes and edges of the fabric.

??? abstract "Sharing data"
    [easy sharing of sharing data](/Api/General/#loading)
    Students can pick and choose the feature data they need.

??? abstract "Contributing data"
    [facilitating the contribution of new data modules](/Api/General/#saving-features)
    Researchers can easily produce new modules of text-fabric data out of their
    findings.

??? abstract "Factory"
    Text-Fabric can be and has been used to construct websites,
    for example [SHEBANQ](https://shebanq.ancient-data.org).
    In the case of SHEBANQ, data has been converted to mysql databases.
    However, with the built-in data server, it is also possible to
    have one Text-Fabric process serve multiple connections and requests.

??? explanation "History"
    Most ideas derive from an earlier project, 
    [LAF-Fabric](https://github.com/Dans-labs/laf-fabric).
    We have taken out everything that makes LAF-Fabric complicated and
    all things that are not essential for the sake of raw data processing.
