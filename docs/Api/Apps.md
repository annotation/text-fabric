# Apps

??? abstract "About"
    Text-Fabric is a generic engine to process text and annotations.

    When working with specific corpora, we want to have more power at our fingertips.

    We need extra power on top of the TF engine.

    The way we have chosen to do it is via *apps*.
    An app is a bunch of extra functions that *know* the structure of a specific corpus.

## Current apps

??? abstract "Current apps"
    At the moment we have these apps

    * bhsa
    * cunei

## The structure of apps

??? abstract "App components"
    The apps themselves are modules inside 
    [tf.extra](https://github.com/Dans-labs/text-fabric/tree/master/tf/extra)

    For each *app*, you find there:

    ??? abstract "module"
        *app*`.py`
        contains all the functionality specific to the corpus in question, organized as an extended
        TF api. In the code this is referred to as the `extraApi`.

    ??? abstract "webapp"
        the package *app*`-app`
        is used by the text-fabric browser, and contain settings and assets
        to set up a browsing experience.

        * `config.py`: settings
        * a `static` folder with fonts and logos.


        ??? abstract "config.py"
            Contains values for parameters and an API calling function.

            ??? abstract "extraApi(locations, modules)"
                Responsible for calling the extra Api for the corpus
                with the desired locations and modules.

                This extraApi will be active as a TF kernel,
                interacting with a local webserver that serves local
                web page in the browser.

            ??? abstract "web browsing settings"
                The TF kernel, webserver and browser need settings:

                setting | example | description
                --- | --- | ---
                protocol | `http://` | protocol of local website
                host | `localhost` | server address of local website
                webport | `8001` | port for the local website
                port | `18981` | port through wich the TF kernel and the webserver communicate

            ??? abstract "data settings"
                The TF kernel needs context information:

                setting | type | description
                --- | --- | ---
                locations | list | where to look for tf features
                modules | list | combines with locations to search paths for tf features
                localDir | directory name | temporary directory for writing and reading
                options | tuple | names of extra options for seaerching and displaying query results
                condenseType | string | the default container type to which query results may be condensed
                PROVENANCE | dict | corpus specific provenance metadata: name and DOI

## The generic part of apps

??? abstract "App helpers"
    Apps turn out to have several things in common that we want to deal with generically.
    These functions are collected in the
    [apphelpers](https://github.com/Dans-labs/text-fabric/blob/master/tf/apphelpers.py)
    module of TF.

??? abstract "Generic/specific"
    Sometimes there is an intricate mix of functionality that is shared by all apps and that
    is specific to some app.
    Here is our logistics of functionality.

    There are a number of methods that are offered as a generic function and
    just added as a method to the *extraApi* of the app, e.g. `pretty()`
    For example, the Bhsa app imports `pretty` first:

    ```python
    from tf.apphelpers import pretty
    ```

    and in the Bhsa `__init__()` function it says:

    ```python
    self.pretty = types.MethodType(pretty, self)
    ```

    which adds the function `pretty` as an instance method to the class Bhsa.
    The first argument `extraApi` of the function `pretty` acts as the `self` when 
    `pretty()` is used as a method of Bhsa.

    So although we define `pretty(extraApi, ...)` as a generic function,
    through its argument `extraApi` we can call app specific functionality.

    We follow this pattern for quite a bit of functions.
    They all have `extraApi` as first argument.

??? abstract "Two contexts"
    Most functions with the `extraApi` argument are meant to perform their duty in two contexts:

    * when called in a Jupyter notebook they deliver output meant for a notebook output cell,
      using methods provided by the `ipython` package.
    * when called by the web app they deliver output meant for the TF browser website,
      generating raw HTML.

    The `extraApi` is the rich app specific API, and when we construct this API, we pass the information
    whether it is constructed for the purposes of the Jupyter notebook, or for the purposes of the web app.

    We pass this information by setting the attribute `asApi` on the `extraApi`. 
    If it is set, we use the `extraApi` in the web app context.

    Most of the code in such functions is independent of `asApi`.
    The main difference is how to output the result: by a call to an IPython display method, or by
    returning raw HTML.


## TF Data getters

??? abstract "Auto loading of TF data"
    The specific apps have functions to load and download data from github.
    They check first whether there is local data in a github repository,
    and if not, they check a local text-fabric-data directory,
    and if not, they download data from a know online GitHub repo into the local
    text-fabric-data directory.

    The data functions provided take parameters with these meanings:

    ??? note "dataUrl"
        The complete url from which to download data.

    ??? note "ghBase"
        The location of the local github directory, usually `~/github`.
        This directory is expected to be subdivided by org and then by repo, just as the online
        GitHub.

    ??? note dataRel
        The relative path within the local github/text-fabric-data directory to the directory
        that holds versions of TF data.

    ??? note version
        The version of the TF data of interest.

??? abstract "hasData(dataRel, ghBase, version)"
    Checks whether there is TF data in standard locations.
    Returns the full path of the local github directory if the data is found in the expected place below it.
    Returns the full path of the local text-fabric-data directory if the data is found in the expected place below it.
    Returns `False` if there no offline copy of the data has been found in these locations.

??? abstract "getData(dataUrl, dataRel, ghBase, version)"
    Checks whether there is TF data in standard locations.
    If not, downloads data from `dataUrl` and places it in `~/text-fabric-data/dataRel/version`

??? abstract "getDataCustom(dataUrl, dest)"
    Retrieves a zip file from `dataUrl`, and unpacks it at directory `dest` locally.

## TF search performers

??? abstract "search(extraApi, query, silent=False, sets=None, shallow=False)"
    This is a thin wrapper around the generic search interface of TF:
    [S.search](/Api/General/#searching)

    The extra thing it does it collecting the results.
    `S.search()` may yield a generator, and this `search()` makes sure to iterate
    over that generator, collect the results, and return them as a sorted list.

    ??? note "Context Jupyter"
        The intended context of this function is: an ordinary Python program (including
        the Jupyter notebook).
        Web apps can better use `runSearch` below.

??? abstract "runSearch(api, query, cache)"
    A wrapper around the generic search interface of TF.
    Before running the TF search, the *query* will be looked up in the *cache*.
    If present, its cached results/error messages will be returned.
    If not, the query will be run, results/error messages collected, put in the *cache*, and returned.

    ??? note "Context web app"
        The intended context of this function is: web app.

??? abstract "runSearchCondensed(api, query, cache, condenseType)"
    When query results need to be condensed into a container, this function takes care of that.
    It first tries the *cache* for condensed query results.
    If that fails,
    it collects the bare query results from the cache or by running the query.
    Then it condenses the results, puts them in the *cache*, and returns them.

    ??? note "Context web app"
        The intended context of this function is: web app.

## Tabular display

??? abstract "table(extraApi, tuples, ...)"
    Takes a list of *tuples* and
    composes it into a Markdown table.

    ??? note "Context Jupyter"
        The intended context of this function is:
        the Jupyter notebook.

??? abstract "compose(extraApi, tuples, start. position, opened, ...)"
    Takes a list of *tuples* and
    composes it into an HTML table.
    Some of the rows will be expandable, namely the rows specified by `opened`,
    for which extra data has been fetched.
    
    ??? note "Context web app"
        The intended context of this function is: web app.

??? abstract "plainTuple(extraApi, tuple)"
    Displays a *tuple* of nodes as a table row:

    * a markdown row in the context Jupyter;
    * an HTML row in the context web app.

## Pretty display

??? abstract "What is pretty?"
    Nodes are just numbers, but they stand for all the information that the corpus
    has about a certain item.
    `pretty(node)` makes a lot of that information visible in an app dependent way.

    For the Bhsa it means showing nested and intruding sentences, clauses and phrases.

    For the Cunei tablets it means showing alternating vertical and horizontal
    subdivisions of faces into columns, lines and cases.

    When you show a pretty representation of a node,
    usually pretty representations of "contained" nodes will also be drawn.

    You can selectively highlight those nodes with custom colors.

    When pretty-displaying a tuple of nodes, container nodes that contain those nodes
    will be looked up and displayed, and the actual tuple nodes will be highlighted.

    You can customize the highlight colors by selecting colors on the basis of the
    postions of nodes in their tuples, or you can explicitly pass a micro-managed
    colormap of nodes to colors.

    In pretty displays you can opt for showing/hiding the node numbers,
    for suppressing certain standard features, and there are app dependent options.

    In the case of Cunei tablets, you can opt to show the lineart of signs and quads,
    and to show the line numbers of the source transcriptions.

??? abstract "show(extraApi, tuples, ...)"
    Takes a list of *tuples* and
    composes it into a sequence of pretty displays per tuple.

    ??? note "Context Jupyter"
        The intended context of this function is:
        the Jupyter notebook.

??? abstract "prettyTuple(extraApi, tuple)"
    Displays a *tuple* of nodes as an expanded display, both

    * in the context Jupyter and
    * in the context web app.

??? abstract "pretty(extrApi, node, ...)"
    Displays a single *node* as an expanded display, both

    * in the context Jupyter and
    * in the context web app.

??? abstract "prettyPre(extraApi, node, ...)"
    Helper for `pretty`.
    Pretty display is pretty complicated.
    There are large portions of functionality that are generic,
    and large portions that are app specific.

    This function computes a lot of generic things, based on which
    a pretty display can be constructed.

??? abstract "prettySetup(extraApi, features=None, noneValues=None)"
    Pretty displays show a chosen set of standard features for nodes.
    By means of the parameter `suppress` you can leave out certain features.
    But what if you want to add features to the display?

    That is what `prettySetup()` does.
    It adds a list of *features* to the display, provided they are loadable.
    If they are not yet loaded, they will be loaded.
    
    Features with values that represent no information, will be suppressed.
    But you can customise what counts as no information, by passing a set
    of such values as `noneValues`. 

## HTML and Markdown

??? abstract "getBoundary(api, node)"
    Utility function to ask from the TF API the first slot and the last slot contained in a node.

??? abstract "getFeatures(extraApi, node, ...)"
    Helper for `pretty()`: wrap the requested features and their values for *node* in HTML for pretty display.

??? abstract "getContext(api, nodes)"
    Get the features and values for a set of *nodes*. 
    All loaded features will be retrieved.

??? abstract "header(extraApi)"
    Get the app-specific links to data and documentation and wrap it into HTML for display in the TF browser.

??? abstract "outLink(text, href, title=None, ...)"
    Produce a formatted HTML link.

??? abstract "htmlEsc(val)"
    Produce a representation of *val* that is safe for usage in a HTML context.

??? abstract "mdEsc(val)"
    Produce a representation of *val* that is safe for usage in a Markdown context.

??? abstract "dm(markdown)"
    Display a *markdown* string in a Jupyter notebook.

## Constants

??? abstract "Fixed values"
    The following values are used by other parts of the program:

    name | description
    --- | ---
    `RESULT` | the label of a query result: `result`
    `GH_BASE` | the location of the local github directory
    `URL_GH` | the url to the GitHub site
    `URL_NB` | the url to the NBViewer site
