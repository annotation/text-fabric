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

