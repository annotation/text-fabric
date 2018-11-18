# Apps

??? abstract "About"
    Text-Fabric is a generic engine to process text and annotations.

    When working with specific corpora, we want to have more power at our fingertips.

    We need extra power on top of the core TF engine.

    The way we have chosen to do it is via *apps*.
    An app is a bunch of extra functions that *know* the structure of a specific corpus.

    In particular, an app knows how to produce plain representations
    and pretty displays of nodes of each type in the corpus.

## Current apps

??? abstract "Current apps"
    At the moment we have these apps

    name | description
    --- | ---
    [bhsa](Bhsa.md) | Biblia Hebraica Stuttgartensia (Amstelodamensis)
    [peshitta](Peshitta.md) | Syriac Old Testament
    [syrnt](Syrnt.md) | Syriac New Testament
    [uruk](Uruk.md) | Proto-cuneiform Uruk Corpus

## The structure of apps

??? abstract "App components"
    The apps themselves are modules inside 
    [apps]({{tfght}}/{{c_apps}})

    For each *app*, you find there a subfolder *app* with:

    ??? abstract "static"
        A folder with fonts and logos, to be used by webservers such as the the
        [text-fabric browser](../Server/Web.md).

    ??? abstract "config.py"
        Settings to set up a browsing experience and to feed the specific API for this app.

        The TF kernel, local webserver and browser need settings:

        setting | example | description
        --- | --- | ---
        protocol | `http://` | protocol of local website
        host | `localhost` | server address of local website
        webport | `8001` | port for the local website
        port | `18981` | port through wich the TF kernel and the webserver communicate
        localDir | directory name | temporary directory for writing and reading
        options | tuple | names of extra options for searching and displaying query results

        The app itself is driven by the following settings

        setting | type | description
        --- | --- | ---
        ORG | string | GitHub organization name of the main data source of the corpus
        REPO | string | GitHub repository name of the main data source of the corpus
        RELATIVE | string | Path to the *tf* directory within the GitHub repository of the main data
        CORPUS | string | Descriptive name of the main corpus
        VERSION | string | Version of the main corpus that is used in the TF browser
        DOI | string | Text of the Digital Object Identifier pointing to the main corpus
        DOI_URL | url | Digital Object Identifier that points to the main corpus
        DOC_URL | url | Base url for the online documentation of the main corpus
        DOC_INTRO | string | Relative url to the introduction page of the documentation of the main corpus 
        CHAR_TEXT | string | Text of the link pointing to the character table of the relevant Unicode blocks
        CHAR_URL | string | Link to the character table of the relevant Unicode blocks
        FEATURE_URL | url | Url to feature documentation. Contains `{feature}` and `{version}` which can be filled in later with the actual feature name and version tag
        MODULE_SPECS | tuple of dicts | Provides information for standard data modules that will be loaded together with the main corpus: *org*, *repo*, *relative*, *corpus*, *docUrl*, *doi* (text and link)
        ZIP | list | data directories to be zipped for a release, given as either `(org, repo, relative)` or `repo` (with org and relative taken from main corpus); only used by `text-fabric-zip` when collecting data into zip files to be attached to a GitHub release
        CONDENSE_TYPE | string | the default node type to condense search results in, e.g. `verse` or `tablet`
        NONE_VALUES | set | feature values that are deemed uninformative, e.g. `None`, `'NA'`
        STANDARD_FEATURES | set | features that are shown by default in all pretty displays
        EXCLUDED_FEATURES | set | features that are present in the data source but will not be loaded for the TF browser
        NO_DESCEND_TYPES | set | when representing nodes as text in exports from the TF browser, node of type in this set will not be expanded to their slot occurrences; e.g. `lex`: we do not want represent lexeme nodes by their list of occurrences
        EXAMPLE_SECTION | html | what a passage reference looks like in this corpus; may have additional information in the form of a link; used in the Help of the TF browser
        EXAMPLE_SECTION_TEXT | string | what a passage reference looks like in this corpus; just the plain text; used in the Help of the TF browser
        SECTION_SEP1 | string | separator between main and secondary sections in a passage reference; e.g. the space in `Genesis 1:1`
        SECTION_SEP2 |string |  separator between secondary and tertiary sections in a passage reference; e.g. the `:` in `Genesis 1:1`
        FORMAT_CSS | dict | mapping between TF text formats and CSS classes; not all text formats need to be mapped
        DEFAULT_CLS | string | default CSS class for text in a specific TF text format, when no format-specific class is given in FORMAT_CSS
        DEFAULT_CLS_ORIG | string | default CSS class for text in a specific TF text format, when no format-specific class is given in FORMAT_CSS; and when the TF text format contains the `-orig-` string; used to specify classes for text in non-latin scripts
        CLASS_NAMES | dict | mapping between node types and CSS classes; used in pretty displays to format the representations of nodes of that type 
        FONT_NAME | string | font family name to be used in CSS for representing text in original script
        FONT | string | file name of the offline font specified in FONT_NAME
        FONTW | string | file name of the webfont specified in FONT_NAME
        CSS | css | CSS styles to be included in Jupyter Notebooks and in the TF browser

    ??? abstract "app.py"
        The functionality specific to the corpus in question, organized as an extended
        TF api. In the code you see this stored in variables with name `app`.

        In order to be an app that TF can use, `app` should provide the following attributes:

        attribute | kind | description
        --- | --- | ---
        webLink | method | given a node, produces a link to an online description of the corresponding object (to [shebanq]({{shebanq}}) or [cdli]({{cdli}}) 
        plain | method | given a node, produce a plain representation of the corresponding object: not the full structure, but something that identifies it
        \_pretty | method | given a node, produce elements of a pretty display of the corresponding object: the full structure

        ??? note "pretty"
            Not all of the `pretty` method needs to be defined by the app.
            In fact, the function itself is defined generically in
            [apphelpers]({{tfghb}}/{{c_apphelpers}}).

            This generic `pretty()` start with determining the slot boundaries and condense container
            of the node.

            Then it calls the method `_pretty`, which must be defined in here in the app.
            This will recursively descend to child nodes in order to pretty display them, and
            combine the sub displays into a big display of all parts.
            This is the pure, app-dependent code for displaying nodes.

            In turn, parth of `_pretty` is taking care of by the
            generic `prettyPre` in *apphelpers.py*.
            `prettyPre` is responsible for determining the slot boundaries of the node.
            It also determines the highlight color from the arguments passed to `pretty()`.


## The generic part of apps

??? abstract "App support"
    Apps turn out to have several things in common that we want to deal with generically.
    These functions are collected in the
    [appmake]({{tfghb}}/{{c_appmake}})
    and
    [apphelpers]({{tfghb}}/{{c_apphelpers}})
    modules of TF.

??? abstract "Generic/specific"
    Sometimes there is an intricate mix of functionality that is shared by all apps and that
    is specific to some app.
    Here is our logistics of functionality.

    There are a number of methods that are offered as a generic function and
    just added as a method to the *app*, e.g. `pretty()`
    For example, apps are setup to import `pretty` first:

    ```python
    from tf.applib.apphelpers import pretty
    ```

    and in the app's setup function this happens:

    ```python
    app.pretty = types.MethodType(pretty, app)
    ```

    which adds the function `pretty` as an instance method to the app.

    So although we define `pretty(app, ...)` as a generic function,
    through its argument `app` we can call app specific functionality.

    We follow this pattern for quite a bit of functions.
    They all have `app` as first argument.

??? abstract "Two contexts"
    Most functions with the `app` argument are meant to perform their duty in two contexts:

    * when called in a Jupyter notebook they deliver output meant for a notebook output cell,
      using methods provided by the `ipython` package.
    * when called by the web app they deliver output meant for the TF browser website,
      generating raw HTML.

    The `app` is the rich app specific API, and when we construct this API, we pass the information
    whether it is constructed for the purposes of the Jupyter notebook, or for the purposes of the web app.

    We pass this information by setting the attribute `asApp` on the `app`. 
    If it is set, we use the `app` in the web app context.

    Most of the code in such functions is independent of `asApp`.
    The main difference is how to output the result: by a call to an IPython display method, or by
    returning raw HTML.

    ??? note "asApp"
        The `app` contains several display functions. By default
        they suppose that there is a Jupyter notebook context in which
        results can be rendered with `IPython.display` methods.
        But if we operate in the context of a web-interface, we need to generate
        straight HTML. We flag the web-interface case as `asApp == True`.

## App set up

??? abstract "setupApi"
    This method is called by each specific app when it instantiates its associated class with
    a single object.

    A lot of things happen here:

    * all data is looked up, downloaded, prepared, loaded, etc
    * the underlying TF Fabric API is called
    * custom links to documentation etc are set
    * styling is set up
    * several methods that are generically defined are added as instance methods

###TF Data getters

??? abstract "Auto loading of TF data"
    The specific apps have functions to load and download data from github.
    If passed the `lgc=True` flag (*local github clones*),
    they check first whether there is data in a local github repository.

    Then they check the local text-fabric-data directory,
    and if nothing is found there,
    they download data from the corresponding online GitHub repo into the local
    text-fabric-data directory.

    Data will be picked from the latest release of the online repo, and if `check=True`
    there will be a check whether a newer release is available.

    When TF stores data in the text-fabric-data directory, it remembers from which release
    it came (in a file `_release.txt`).

    All the data getters need to know is the organization, the repo, the path within the repo
    to the data, and the version of the (main) data source.
    The data should reside in directories that correspond to versions of the main data source.
    The path should point to the parent of these version directries.

### Links

??? abstract "attributes of the app"

    name | type | description
    --- | --- | ---
    `tfsLink` | html link | points to the documentation of the TF search engine
    `tutLink` | html link | points to the tutorial for TF search

??? abstract "sectionLink(node)"
    Given a section node, produces a link that copies the section to the section pad (only in the TF browser)

### Various

??? abstract "nodeFromDefaultSection(sectionStr)"
    Given a section string pointing to an object of `condenseType`, return the corresponding node (or an error message).

## App helpers

### TF search performers

??? abstract "search(app, query, silent=False, sets=None, shallow=False)"
    This is a thin wrapper around the generic search interface of TF:
    [S.search](General.md#search)

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

### Tabular display

??? abstract "table(app, tuples, ...)"
    Takes a list of *tuples* and
    composes it into a Markdown table.

    ??? note "Context Jupyter"
        The intended context of this function is:
        the Jupyter notebook.

??? abstract "compose(app, tuples, start. position, opened, ...)"
    Takes a list of *tuples* and
    composes it into an HTML table.
    Some of the rows will be expandable, namely the rows specified by `opened`,
    for which extra data has been fetched.
    
    ??? note "Context web app"
        The intended context of this function is: web app.

??? abstract "plainTuple(app, tuple)"
    Displays a *tuple* of nodes as a table row:

    * a markdown row in the context Jupyter;
    * an HTML row in the context web app.

### Pretty display

??? abstract "What is pretty?"
    Nodes are just numbers, but they stand for all the information that the corpus
    has about a certain item.
    `pretty(node)` makes a lot of that information visible in an app dependent way.

    For the Bhsa it means showing nested and intruding sentences, clauses and phrases.

    For the Uruk tablets it means showing alternating vertical and horizontal
    subdivisions of faces into columns, lines and cases.

    For the Peshitta it currently means showing the words of verses in unicode and ETCBC/WIT
    transcription.

    For the SyrNT it currently means showing the words of verses in unicode and SEDRA
    transcription.

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

    In the case of Uruk tablets, you can opt to show the lineart of signs and quads,
    and to show the line numbers of the source transcriptions.

??? abstract "show(app, tuples, ...)"
    Takes a list of *tuples* and
    composes it into a sequence of pretty displays per tuple.

    ??? note "Context Jupyter"
        The intended context of this function is:
        the Jupyter notebook.

??? abstract "prettyTuple(app, tuple)"
    Displays a *tuple* of nodes as an expanded display, both

    * in the context Jupyter and
    * in the context web app.

??? abstract "pretty(extrApi, node, ...)"
    Displays a single *node* as an expanded display, both

    * in the context Jupyter and
    * in the context web app.

??? abstract "prettyPre(app, node, ...)"
    Helper for `pretty`.
    Pretty display is pretty complicated.
    There are large portions of functionality that are generic,
    and large portions that are app specific.

    This function computes a lot of generic things, based on which
    a pretty display can be constructed.

??? abstract "prettySetup(app, features=None, noneValues=None)"
    Pretty displays show a chosen set of standard features for nodes.
    By means of the parameter `suppress` you can leave out certain features.
    But what if you want to add features to the display?

    That is what `prettySetup()` does.
    It adds a list of *features* to the display, provided they are loadable.
    If they are not yet loaded, they will be loaded.
    
    Features with values that represent no information, will be suppressed.
    But you can customise what counts as no information, by passing a set
    of such values as `noneValues`. 

### HTML and Markdown

??? abstract "getBoundary(api, node)"
    Utility function to ask from the TF API the first slot and the last slot contained in a node.

??? abstract "getFeatures(app, node, ...)"
    Helper for `pretty()`: wrap the requested features and their values for *node* in HTML for pretty display.

??? abstract "getContext(api, nodes)"
    Get the features and values for a set of *nodes*. 
    All loaded features will be retrieved.

??? abstract "header(app)"
    Get the app-specific links to data and documentation and wrap it into HTML for display in the TF browser.

??? abstract "outLink(text, href, title=None, ...)"
    Produce a formatted HTML link.

??? abstract "htmlEsc(val)"
    Produce a representation of *val* that is safe for usage in a HTML context.

??? abstract "mdEsc(val)"
    Produce a representation of *val* that is safe for usage in a Markdown context.

??? abstract "dm(markdown)"
    Display a *markdown* string in a Jupyter notebook.

### Constants

??? abstract "Fixed values"
    The following values are used by other parts of the program:

    name | description
    --- | ---
    `RESULT` | string | the label of a query result: `result`

