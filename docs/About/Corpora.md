# Corpora

Corpora are usually stored in an online repository, such as GitHub or a research data archive
such as [DANS]({{dans}}/front-page?set_language=en).

## Current apps

Some corpora are supported by Text-Fabric *apps*.

These apps provide a browser interface for the corpus, and they enhance the API for working
with them programmatically.

A list of current apps can be found in 
[annotation]({{an}}) on GitHub.


## Get apps

??? abstract "Automatically"
    Text-Fabric downloads apps from this [annotation]({{an}}) automatically
    when you use them.

    So when you say in a notebook

    ```python
    use('xxxx')
    ```

    Text-Fabric will fetch the `xxxx` app for you, if it exists.

    And if you use the Text-Fabric browser, and say

    ```sh
    text-fabric xxxx
    ```

    the same thing happens.

## Get data

??? abstract "Automatically"
    Text-Fabric apps download the corpus data for you
    automatically. When you use the browser, it happens when you start it up.
    And from within a Python program,
    you get the data when you do the
    [incantation](../Api/App.md#incantation).

    The TF data is fairly compact,

    ??? caution "Size of data"
        There might be sizable additional data for some corpora,
        images for example.
        In that case, take care to have a good internet connection when you use the
        Text-Fabric browser for the first time.

??? abstract "Extra data"
    Researchers are continually adding new insights in the form of new feature
    data. TF apps make it easy to use that data alongside the main data source.
    Read more about the data life cycle in [Data](../Api/Data.md)

## More corpora

??? abstract "text-fabric-data"
    The
    [text-fabric-data]({{tfdgh}})
    repo has some corpora that have been converted to TF,
    but for which no supporting  TF-apps have been written.
