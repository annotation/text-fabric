# Usage

## Use Text-Fabric browser

Explore your corpus without programming.
Here is how to start up text-fabric.

??? hint "On Windows?"
    You can click the Start Menu, and type `text-fabric bhsa` or `text-fabric cunei`
    in the search box, and then Enter.

??? hint "On Linux or Macos?"
    You can open a terminal (command prompt), and just say

    ```sh
    text-fabric bhsa
    ```

    or 

    ```sh
    text-fabric cunei
    ```

??? abstract "All platforms"
    The corpus data will be downloaded automatically,
    and be loaded into text-fabric.
    Then your browser will open and load the search interface.
    There you'll find links to further help.


![bhsa](/images/bhsa-app.png)

*Above: Querying the BHSA data*

*Below: Querying the Cunei data*

![cunei](/images/cunei-app.png)


??? hint "Fetching corpora"
    The Text-Fabric browser fetches the corpora it needs from GitHub automatically.
    The TF data is fairly compact (25 MB for the Hebrew Bible, 1.6 MB for the Cunei corpus).

    ??? caution "Size of data"
        There might be sizable additional data (550 MB images for the Cunei corpus).
        In that case, take care to have a good internet connection when you use the
        Text-Fabric browser for the first time.

    [More about corpora](/Corpora)

??? hint "Saving your session"
    Your session will be saved in a file with extension `.tfjob` in the directory
    from where you have issued the `text-fabric` command.
    From within the browser you can rename and duplicate sessions and move to
    other directories. You can also load other sessions in other tabs.

??? hint "Multiple windows"
    After you have issued the `text-fabric` command, a *TF kernel* is started for you.
    This is a process that holds all the data and can deliver it to other processes,
    such as your web browser.

    As long as you leave the TF kernel on, you have instant access to your corpus.

    You can open other browsers and windows and tabs with the same url,
    and they will load quickly, without the long wait you experienced when the TF kernel was loading.

??? hint "Close"
    You can close the TF kernel by pressing Ctrl-C in the terminal or command prompt where you have
    started `text-fabric` up.

## Work with exported results

You can export your results to CSV files which you can process with various tools,
including your own.

??? hint "Exporting your results"
    You can use the "Export" tab to tell the story behind your query and then export all your
    results. A new page will open, which you can save as a PDF.
    
    There is also a markdown file `about.md` with
    your description and some provenance metadata.

    Moreover, a file `RESULTSX.csv` is written into a local directory corresponding to the
    job you are in, which contains your precise search results, decorated with the features
    you have used in your searchTemplate.

    In addition, some extra data files will be written along side.
    Your results as tuples of nodes, your condensed results (if you have opted for them),
    and a CONTEXT.csv that contains all feature values for every node in the results.

    Now, if you want to share your results for checking and replication, put all this in a GitHub repository:

    ???+ note "Examples"
        **Cunei**:
        [about.md](https://github.com/Dans-labs/text-fabric/blob/master/test/cunei/cunei-DefaulT/about.md)
        [RESULTSX.csv](https://github.com/Dans-labs/text-fabric/blob/master/test/cunei/cunei-DefaulT/RESULTSX.csv)

        **BHSA**:
        [about.md](https://github.com/Dans-labs/text-fabric/blob/master/test/bhsa/bhsa-DefaulT/about.md)
        [RESULTSX.csv](https://github.com/Dans-labs/text-fabric/blob/master/test/bhsa/bhsa-DefaulT/RESULTSX.csv)

    If you want to be able to cite those results in a journal article, archive the GitHub repo
    in question to [ZENODO](https://zenodo.org) and obtain a DOI.

## Use the Text-Fabric API

Explore your corpus by means of programming.

??? abstract "Into the notebook"
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

    Adapt `my/dataset` to where your particalur dataset is"

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

