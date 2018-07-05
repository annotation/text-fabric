# Text-Fabric as a service

## About

??? abstract "TF as a service"
    Text-Fabric can be used as a service.
    The full API of Text-Fabric needs a lot of memory, which makes it unusably for
    rapid successions of loading and unloading, like when used in a web server context.

    However, you can start TF as a server, after which many clients can connect to it,
    all looking at the same (read-only) data.

    The API that the TF server offers is limited, it is primarily template search that is offered.
    See *Data service API* below.

    See the code in
    [tf.server.service](https://github.com/Dans-labs/text-fabric/tree/master/tf/server/service.py)
    to get started.

### Start

??? abstract "Run"
    You can run the TF data server as follows:

    ```sh
    python3 -m tf.server.service ddd
    ```

    where `ddd` is one of the [supported apps](/Api/Apps#current-apps)

    ??? example
        See the
        [start-up script](https://github.com/Dans-labs/text-fabric/tree/master/tf/server/start.py)
        of the text-fabric browser.

### Connect

??? abstract "Connect"
    The TF data service can be connected by an other Python program as follows:

    ```python
    from tf.server.service import makeTfConnection
    TF = makeTfConnection(host, port)
    api = TF.connect()
    ```

    After this, `api` can be used to obtain information from the Text-Fabric data service.

    ??? example
        See the
        [web server](https://github.com/Dans-labs/text-fabric/tree/master/tf/server/web.py)
        of the text-fabric browser.

## Data service API

??? abstract "About"
    The API of the Text-Fabric data service is created
    by the function `makeTfServer` in the 
    [data](https://github.com/Dans-labs/text-fabric/tree/master/tf/server/data.py)
    module of the server subpackage.

    It returns a class `TfService` with a number
    of exposed methods that can be called by other programs.

    For the machinery of interprocess communication we rely on the
    [rpyc](https://github.com/tomerfiliba/rpyc) module.
    See especially the docs on
    [services](https://rpyc.readthedocs.io/en/latest/docs/services.html#services).

??? abstract "header()"
    Calls the `header()` method of the extraApi,
    which fetches all the stuff to create a header
    on the page with links to data and documentation of the
    data source.

??? abstract "provenance()"
    Calls the `provenance()` method of the extraApi,
    which fetches provenance metadata to be shown
    on exported pages.

??? abstract "css()"
    Calls the `loadCSS()` method of the extraApi,
    which delivers the CSS code to be inserted
    on the browser page.

??? abstract "condenseTypes()"
    Fetches several things from the extraApi and the 
    generic TF api:

    * `condenseType`: the default node type that acts
      as a container for representing query results;
      for Bhsa it is `verse`, for Cunei it is `tablet`;
    * `exampleSection`: an example for the help text
      for this data source;
    * `levels`: information about the node types in this
      data source.

??? abstract "search()"
    The work horse of this API.
    Executes a TF search template, retrieves
    formatted results, retrieves 
    formatted results for additional nodes and
    sections.

    Parameters:

    ??? note "query"
        Search template to be executed.
        Typically coming
        from the *search pad* in the browser.

    ??? note "tuples"
        Tuples of nodes to look up features for.
        Typically coming
        from the *node pad* in the browser.

    ??? note "sections"
        Sections to look up features for.
        Typically coming
        from the *section pad* in the browser.

        For the Bhsa these are *verse* references,
        for Cunei these are tablets by *P-number*.

    ??? note "condensed"
        Whether or not the results should be *condensed*.
        Normally, results come as tuples of nodes, and each
        tuple is shown in a corresponding table row in
        plain or pretty display.

        But you can also *condense* results in container
        objects. All tuples will be inspected, and the nodes
        of each tuple will be gathered in containers,
        and these containers will be displayed in table rows.
        What is lost is the notion of an individual result,
        and what is gained is a better overview of where
        the parts of the results are.

    ??? note "condenseType"
        When condensing results, you can choose the node type
        that acts as container.

        ??? caution "Nodes get suppressed"
            Nodes in result tuples that have a type
            that is bigger than the condenseType, will
            be skipped.
            E.g. if you have chapter nodes in your results,
            but you condense to verses, the chapter nodes will 
            not show up.
            But if you condense to books, they will show up.

    ??? note "batch"
        The number of table rows to show on one page
        in the browser.

    ??? note "position=1"
        The position that is central in the browser.
        The navigation links take this position
        as the focus point, and enable the user
        to navigate to neighbouring results, in ever bigger
        strides.

    ??? note "opened=set()"
        Which results have been expanded and need extended results.
        Normally, only the information to provide a *plain*
        representation of a result is being fetched,
        but for the opened ones information is gathered for
        pretty displays.

    ??? note "withNodes=False"
        Whether to include the node numbers into the formatted
        results.

    ??? note "linked=1"
        Which column in the results should be hyperlinked to
        online representations closest to the objects
        in that column.

        Counting columns starts at 1.

    ??? note "**options**"
        Additional keyword arguments are passed
        as options to the underlying API.

        For example, the Cunei API accepts `linenumbers`
        and `lineart`, which will ask to include line numbers
        and lineart in the formatted results.
        
??? abstract "csvs()"
    This is an other workhorse.
    It also asks for the things `search()` is asking
    for, but it does not want formatted results.
    It will get tabular data of result
    nodes, one for the *sections*, one for the *node tuples*,
    and one for the *search results*.

    For every node that occurs in this tabular data,
    features will be looked up.
    All loaded features will be looked up for those nodes.
    The result is a big table of nodes and feature values.

    The parameters are *query*, *tuples*, *sections*,
    *condensed*, *condenseType* and have the same meaning as
    in `search()` above.
