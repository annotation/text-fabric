# Apps

??? abstract "About"
    Text-Fabric is a generic engine to process text and annotations.

    When working with specific corpora, we want to have more power at our fingertips.

    We need extra power on top of the core TF engine.

    The way we have chosen to do it is via *apps*.
    An app is a bunch of extra functions that *know* the structure of a specific corpus.

    In particular, an app knows how to produce plain representations
    and pretty displays of nodes of each type in the corpus.

    For a list of current apps, see [Corpora](../About/Corpora.md)

## Components

??? abstract "App components"
    The apps themselves are modules inside 
    [apps]({{tfght}}/{{b_apps}})

    For each *app*, you find there a subfolder *app* with:

    ??? abstract "static"
        A folder with styles, fonts and logos, to be used by web servers such as the the
        [text-fabric browser](../Server/Web.md).

        In particular, `display.css` contains the styles used for pretty displays.
        These styles will be programmatically combined with other styles,
        to deliver them to the TF browser on the one hand, and to Jupyter notebooks
        on the other hand.

    ??? abstract "config.py"
        Settings to set up a browsing experience and to feed the specific AP
        for this app.

        The TF kernel, web server and browser need settings:

        setting | example | description
        --- | --- | ---
        PROTOCOL | `http://` | protocol of website
        HOST | `localhost` | server address of the website
        PORT | `18981` | port through wich the TF kernel and the web server communicate
        OPTIONS | tuple | names of extra options for searching and displaying query results

        The app itself is driven by the following settings

        setting | type | description
        --- | --- | ---
        ORG | string | GitHub organization name of the main data source of the corpus
        REPO | string | GitHub repository name of the main data source of the corpus
        RELATIVE | string | Path to the *tf* directory within the GitHub repository of the main data
        CORPUS | string | Descriptive name of the main corpus
        VERSION | string | Version of the main corpus that is used in the TF browser
        DOI_TEXT | string | Text of the Digital Object Identifier pointing to the main corpus
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

    ??? abstract "app.py"
        The functionality specific to the corpus in question, organized as an extended
        TF api. In the code you see this stored in variables with name `app`.

        In order to be an app that TF can use, `app` should provide the following attributes:

        attribute | kind | description
        --- | --- | ---
        webLink | method | given a node, produces a link to an online description of the corresponding object (to [shebanq]({{shebanq}}) or [cdli]({{cdli}})) 
        \_plain | method | given a node, produce a plain representation of the corresponding object: not the full structure, but something that identifies it
        \_pretty | method | given a node, produce elements of a pretty display of the corresponding object: the full structure

## Implementation

??? abstract "App support"
    Apps turn out to have several things in common that we want to deal with generically.
    These functions are collected in the
    [api]({{tfghb}}/{{c_apps}})
    modules of TF.

??? abstract "Two contexts"
    Most functions with the `app` argument are meant to perform their duty
    in two contexts:

    * when called in a Jupyter notebook they deliver output meant
      for a notebook output cell,
      using methods provided by the `ipython` package.
    * when called by the web app they deliver output meant for the TF browser website,
      generating raw HTML.

    The `app` is the rich app specific API, and when we construct this API,
    we pass the information
    whether it is constructed for the purposes of the Jupyter notebook,
    or for the purposes of the web app.

    We pass this information by setting the attribute `_asApp` on the `app`. 
    If it is set, we use the `app` in the web app context.

    Most of the code in such functions is independent of `_asApp`.
    The main difference is how to output the result:
    by a call to an IPython display method, or by
    returning raw HTML.

    ??? note "\_asApp"
        The `app` contains several display functions. By default
        they suppose that there is a Jupyter notebook context in which
        results can be rendered with `IPython.display` methods.
        But if we operate in the context of a web-interface, we need to generate
        straight HTML. We flag the web-interface case as `_asApp == True`.

### Set up

??? abstract "setupApi()"
    This method is called by each specific app when it instantiates
    its associated class with
    a single object.

    A lot of things happen here:

    * all data is looked up, downloaded, prepared, loaded, etc
    * the underlying TF Fabric API is called
    * custom links to documentation etc are set
    * styling is set up
    * several methods that are generically defined are added as instance methods

### Data getters

??? abstract "Auto loading of TF data"
    The specific apps call the functions 
    [`getModulesData()` and `getData()`]({{tfghb}}/{{c_appdata}})
    to load and download data from github.

    When TF stores data in the text-fabric-data directory,
    it remembers from which release it came (in a file `_release.txt`).

    All the data getters need to know is the organization, the repo,
    the path within the repo
    to the data, and the version of the (main) data source.
    The data should reside in directories that correspond to versions
    of the main data source.
    The path should point to the parent of these version directries.

    TF uses the [GitHub API]({{ghapi}}) to discover which is the newest release of
    a repo.

### Links

??? abstract "attributes of the app"

    name | type | description
    --- | --- | ---
    `tfsLink` | html link | points to the documentation of the TF search engine
    `tutLink` | html link | points to the tutorial for TF search

??? abstract "\_sectionLink(node)"
    Given a section node, produces a link that copies the section
    to the section pad (only in the TF browser)

### Display

??? abstract "Generic/specific"
    Displaying nodes is an intricate mix of functionality that is shared by all apps
    and that is specific to some app.
    Here is our logistics of pretty displays.

    Like a number of other methods `pretty()` is defined as a generic function and
    added as a method to each *app*:

    ```python
    app.pretty = types.MethodType(pretty, app)
    ```

    So although we define `pretty(app, ...)` as a generic function,
    through its argument `app` we can call app specific functionality.

    We follow this pattern for quite a bit of functions.
    They all have `app` as first argument.

    The case of `pretty()` is the most intricate one, since there is a *lot* of generic
    functionality and a lot of corpus specific functionality, as is evident from examples of the 
    BHSA corpus and one from the Uruk corpus below.

    Here is the flow of information for `pretty()`:

    1. definition as a generic function
       [`pretty()`]({{tfghb}}/{{c_appdisplay}});
    2. this function fetches the relevant display parameters and gathers information
       about the node to display, e.g. its boundary slots;
    3. armed with this information, it calls the app-dependent `_pretty()` function,
       e.g. from
       [uruk]({{tfghb}}/{{c_uruk_app}})
       or
       [bhsa]({{tfghb}}/{{c_bhsa_app}});
    4. `_pretty()` is a function that calls itself recursively for all other nodes that
       are involved in the display;
    5. for each node that `_pretty()` is going to display,
		   it first computes a few standard
       things for that node by means of a generic function   
       [`prettyPre()`]({{tfghb}}/{{c_appdisplay}});
			 in particular, it will be computed whether
       the display of the node in question fits in the display of the node
			 where it all began with, or whether parts of the display should be clipped;
			 also, a header label for the
       current node will be comnposed, including relevant hyperlinks and optional extra
       information reuqired by the display options;
    6. finally, it is the turn of the app-dependent `_pretty()`
		   to combine the header label
       with the displays it gets after recursively calling itself for subordinate nodes.

    ![bhsa](../images/bhsa-example.png)

    Above: BHSA pretty display

    Below: Uruk pretty display

    ![uruk](../images/uruk-example.png)

### TF search performers

??? abstract "search()"
    ```python
    search(app, query, silent=False, sets=None, shallow=False)
    ```

    This is a thin wrapper around the generic search interface of TF:
    [S.search](../Api/General.md#search)

    The extra thing it does it collecting the results.
    `S.search()` may yield a generator, and this `search()` makes sure to iterate
    over that generator, collect the results, and return them as a sorted list.

    ??? note "Context Jupyter"
        The intended context of this function is: an ordinary Python program (including
        the Jupyter notebook).
        Web apps can better use `runSearch` below.

??? abstract "runSearch()"
    ```python
    runSearch(app, query, cache)
    ```

    A wrapper around the generic search interface of TF.

    Before running the TF search, the *query* will be looked up in the *cache*.
    If present, its cached results/error messages will be returned.
    If not, the query will be run, results/error messages collected, put in the *cache*,
    and returned.

    ??? note "Context web app"
        The intended context of this function is: web app.

??? abstract "runSearchCondensed()"
    ```python
    runSearchCondensed(api, query, cache, condenseType)
    ```

    When query results need to be condensed into a container,
    this function takes care of that.
    It first tries the *cache* for condensed query results.
    If that fails,
    it collects the bare query results from the cache or by running the query.
    Then it condenses the results, puts them in the *cache*, and returns them.

    ??? note "Context web app"
        The intended context of this function is: web app.

### Tabular display for the TF-browser

??? abstract "compose()"
    ```python
    compose(app, tuples, features, position, opened, getx=None, **displayParameters)
    ```

    Takes a list of *tuples* and
    composes it into an HTML table.
    Some of the rows will be expandable, namely the rows specified by `opened`,
    for which extra data has been fetched.

    *features* is a list of names of features that will be shown
    in expanded pretty displays.
    Typically, it is the list of features used in the query that delivered the tuples. 

    *position* The current position in the list. Will be highlighted in the display.

    *getx=None* If `None`, a portion of the tuples will be put in a table. otherwise,
    it is an index in the list for which a pretty display will be retrieved.
    Typically, this happens when a TF-browser user clicks on a table row
    in order to expand
    it.
    
??? abstract "composeT()"
    ```python
    composeT(app, features, tuples, features, opened, getx=None, **displayParameters)"
    ```

    Very much like `compose()`,
    but here the tuples come from a sections and/or tuples specification
    in the TF-browser.

??? abstract "composeP(), getx=None, \*\*displayParameters)"
    ```python
    composeP(
      app,
      sec0, sec1,
      features, query,
      sec2=None,
      opened=set(),
      getx=None,
      **displayParameters
    )
    ```

    Like `composeT()`, but this is meant to compose the items
    at section level 2 (verses) within
    an item of section level 1 (chapter) within an item of section level 0 (a book).
    Typically invoked when a user of the TF-browser is browsing passages.
    The query is used to highlight its results in the passages that the user is browsing.

??? abstract "plainTextS2()"
    ```python
    plainTextS2(sNode, opened, sec2, highlights, \*\*displayParameters)
    ```

    Produces a single item corresponding to a section 2 level (verse) for display
    in the browser. It will rendered as plain text, but expandable to a pretty display.

??? abstract "Highlighting"
    The functions `getPassageHighlights()`, `getHlNodes()`, `nodesFromTuples()`
    are helpers to apply highlighting to query results in a passage.

??? abstract "getBoundary(api, node)"
    Utility function to ask from the TF API the first slot and the last slot contained in a node.

??? abstract "getFeatures(app, node, ...)"
    Helper for `pretty()`: wrap the requested features and their values for *node* in HTML for pretty display.

??? abstract "header(app)"
    Get the app-specific links to data and documentation and wrap it into HTML for display in the TF browser.

### HTML and Markdown

??? abstract "\_outLink(text, href, title=None, ...)"
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

