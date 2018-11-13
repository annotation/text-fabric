# Corpora

Corpora are usually stored in an online repository, such as GitHub or a research data archive
such as [DANS](https://dans.knaw.nl/en/front-page?set_language=en).

## Get corpora

??? abstract "Automatically"
    There are a few corpora in Text-Fabric that are being supported
    with extra modules.
    Text-Fabric will fetch them for you if you use the Text-Fabric browser.
    And if you work with them from within a Python program (e.g. in a Jupyter Notebook),
    you get the data when you just say `A = use(*appname*)`.

??? abstract "Manually"
    You can also download the data you need up-front.
    There are basically two ways:

    ??? abstract "from a release binary"
        Go to the relevant GitHub repository, click on releases, and choose the relevant binary
        that has been attached to the release.
        Download it to your system.
        This is the most economical way to get data.

    ??? abstract "clone the complete repository"
        Clone the relevant GitHub repository to your system.
        This will get you lots of additional data that you might not directly need.

        ??? caution "On Windows?"
            You have to install `git` in
            [some way](https://git-scm.com/downloads)
            for this step.


## ETCBC

??? hint "ETCBC data"
    Inspect the repositories of the [etcbc organization on GitHub](https://github.com/etcbc)
    to see what is available. Per repository, click the *Releases* button so see
    the release version that holds the relevant binaries with TF-data.
    For example, try [crossrefs](https://github.com/etcbc/parallels/releases).

### Hebrew Bible

??? abstract "From within a program"
    If you are in a Jupyter notebook or Python script,
    this will fetch the data (25MB)

    ```python
    from tf.app import use
    A = use('bhsa')
    ```

    ??? hint "ETCBC versions"
        The data of the BHSA comes in major versions, ranging from `3` (2011) via
        `4`, `4b`, `2016`, `2017` to `c` (2018).
        The latter is a *continuous* version, which will change over time.

??? abstract "From GitHub"
    If you want to be in complete control, you can get the complete data repository
    from GitHub (5GB):

    ```sh
    cd ~/github/etcbc
    git clone https://github.com/etcbc/bhsa
    ```

    and likewise you can get other ETCBC data modules such as `phono`.

### Peshitta

??? abstract "From within a program"
    If you are in a Jupyter notebook or Python script,
    this will fetch the data (2MB)

    ```python
    from tf.app import use
    A = use('peshitta')
    ```

??? abstract "From GitHub"
    If you want to be in complete control, you can get the complete data repository
    from GitHub:

    ```sh
    cd ~/github/etcbc
    git clone https://github.com/etcbc/peshitta
    ```

### Syriac New Testament

??? abstract "From within a program"
    If you are in a Jupyter notebook or Python script,
    this will fetch the data (2MB)

    ```python
    from tf.app import use
    A = use('syrnt')
    ```

??? abstract "From GitHub"
    If you want to be in complete control, you can get the complete data repository
    from GitHub:

    ```sh
    cd ~/github/etcbc
    git clone https://github.com/etcbc/syrnt
    ```

## Cuneiform tablets from Uruk

??? abstract "From within a program"
    If you are in a Jupyter notebook or Python script,
    Uruk API will fetch the data for you automatically.

    * The TF-part is 1.6 MB
    * the photos and lineart are 550MB!

    ```python
    from tf.app import use
    A = use('uruk')
    ```
    
    ???+ caution
        So do this only when you have a good internet connection.

??? abstract "From GitHub"
    If you want to be in complete control, you can get the complete data repository
    from GitHub (1.5GB):

    ```sh
    cd ~/github/Nino-cunei
    git clone https://github.com/Nino-cunei/uruk
    ```

## More corpora

The
[Greek](https://github.com/Dans-labs/text-fabric-data/tree/master/greek/sblgnt)
New Testament has been converted to TF.

We have example corpora in Sanskrit, and Babylonian.

??? abstract "From GitHub"

    ```sh
    cd ~/github
    git clone https://github.com/etcbc/linksyr
    ```

    ```sh
    cd ~/github
    git clone https://github.com/Dans-labs/text-fabric-data
    ```

All these are not supported by extra interfaces.

