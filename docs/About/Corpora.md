# Corpora

Corpora are usually stored in an online repository, such as GitHub or a research data archive
such as [DANS]({{dans}}/front-page?set_language=en).

## Current apps

Some corpora are supported by Text-Fabric *apps*.

These apps provide a browser interface for the corpus, and they enhance the API for working
with them programmatically.

Here is the list of current apps:

* [bhsa](../Apps/Bhsa.md) - Hebrew Bible
* [peshitta](../Apps/Peshitta.md) - Syriac Old Testament
* [syrnt](../Apps/Syrnt.md) - Syriac New Testament
* [uruk](../Apps/Uruk.md) - proto cuneiform tablets from Uruk

## Get data

??? abstract "Automatically"
    Text-Fabric apps download the corpus data for you
    automatically. When you use the browser, it happens when you start it up.
    And from within a Python program,
    you get the data when you do the
    [incantation](../Api/App.md#incantation).

    The TF data is fairly compact
    (25 MB for the Hebrew Bible,
    2,1 MB for the Peshitta,
    2,1 MB for the Syriac New Testament,
    1.6 MB for the Uruk corpus).

    ??? caution "Size of data"
        There might be sizable additional data (550 MB images for the Uruk corpus).
        In that case, take care to have a good internet connection when you use the
        Text-Fabric browser for the first time.

??? abstract "Extra data"
    Researchers are continually adding new insights in the form of new feature
    data. TF apps make it easy to use that data alongside the main data source.
    Read more about the data life cycle in [Data](../Api/Data.md)

## More corpora

??? abstract "Greek New Testament"
    The
    [Greek]({{tfdght}}/greek/sblgnt)
    New Testament has been converted to TF.

    We have example corpora in Sanskrit, and Babylonian.

??? abstract "From GitHub"

    ```sh
    cd ~/github
    git clone {{etcbcgh}}/linksyr
    ```

    ```sh
    cd ~/github
    git clone {{tfdgh}}
    ```

All these are not supported by extra interfaces.

