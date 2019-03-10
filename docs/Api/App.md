# App API

??? abstract "About"
    The app-API provides extra functionality of top of the core of TF.
    The most notable thing is display.
    The functions `plain()` and `pretty()` are able to display nodes using extra
    information about what those nodes typically represent in a specific corpus.

    The app-API further knows how to download the data,
    and can be invoked by a simple incantation.

## Incantation

??? abstract "A.use()"
    ```python
    from tf.app import use
    A = use(appName)
    ```

    See [Corpora](../About/Corpora.md) for what you can use. 

    Hint: think of the `use {database}` statements in MySQL and MongoDb.

    Without further arguments, this will set up an TF core API with most features loaded,
    wrapped in an app-specific API.

    ??? abstract "Start up sequence"
        During start-up the following happens:

        (1) the corpus data is downloaded to your `~/text-fabric-data` directory,
        if not already present there;

        (2) if your data has been freshly downloaded,
        a series of optimizations is executed;

        (3) most features of the corpus are loaded.

    There are many scenarios in which you can work with a TF app:
    in a Python script or in a notebook.
    If you start the TF browser, a TF app is started in a *kernel*,
    a process that can communicate with other processes, such as web servers,
    much like how a database communicates with programs that need data.

    Sometimes you want to load all features without thinking,
    at other times you want to be selective.
    You may want to load downloadable features from the internet,
    or you want to experiment with
    features you are developing. 

    A TF app can be invoked for all these scenarios
    by supplying additional arguments to the incantation.
     
    ??? info "hoist=globals()"
        This makes the API elements directly available as global names
        in your script or notebook:
        you can refer to `F`, `L`, `T`, etc. directly,
        instead of the more verbose `A.api.F`, `A.api.L`, `A.api.T` etc.

        If you pass this argument,
        TF will show you what names will be inserted in your namespace.
        And if you are in a Jupyter notebook,
        these names are linked to their documentation.

    Without further arguments, TF thinks you are a user
    that wants to work with as much data possible without hassle.
    It makes some standard choices for you, and it will auto-download data.

    The following options are for people who want increasingly finer control
    over the features that are being loaded.

    ??? info "version=VERSION"
        If you do not want to work with the default version of your main corpus,
        you can specify a different version here.

        ??? example "versions"
            ```python
            A = use('xxxx', version='2017')
            ```

            In fact, this single statement will download that Xxxx version
            if you do not already have it.

        ??? note "Modules"
            If you also ask for extra data modules by means of the `mod` argument,
            then the corresponding version
            of those modules will be chosen.
            Every properly designed data module must refer to a specific
            version of the main source!

    ??? info "mod=None"
        `mod` is a comma-separated list of modules in the form `{org}/{repo}/{path}`.
        All features of all those modules will be loaded.
        If they are not yet present, they will be downloaded from GitHub first.

        For example, there is an easter egg module on GitHub, and you can obtain it by

        ```
        mod='etcbc/lingo/easter/tf'
        ```

        Here the `{org}` is `etcbc`, the `{repo}` is `lingo`,
        and the `{path}` is `easter/tf` under which
        version `c` of the feature `egg`
        is avaialble in TF format.

        You can point to any such directory om the entire GitHub
        if you know that it contains relevant features.

        Your TF app might be configured to download specific modules.
        See `MODULE_SPECS` in the app's 
        [config.py](../Implementation/Apps.md#components),

        ??? caution "Release sensitive"
            Module data will be downloaded from a specific release
            of the relevant GitHub repo.
            See the [Data](../Api/Data.md) for details how to publish feature data.
            It will be downloaded to the
            `text-fabric-data` folder in your home directory.
            Next to the data will be a little text file which
            indicates from which release the data is taken.

        ??? caution "Let TF manage your text-fabric-data directory"
            It is better not to fiddle with your `~/text-fabric-data` directory manually.
            Let it be filled with auto-downloaded data.
            You can then delete data sources and modules when needed,
            and have them redownloaded
            at your wish, without any hassle or data loss.

    ??? info "check=False"
        If `True`, Text-Fabric will check the main source and each module
        for newer releases.
        For every dataset for which a newer release than the locally available one
        is found, the newest data will be downloaded.

    ??? info "lgc=False"
        Normally, Text-Fabric will work with data that is stored under your
        `~/text-fabric-data`.
        But if you have a local clone of a repository
        with data in `~/github/{org}/{repo}`,
        and you want to use that instead,
        you can pass `lgc=True`. Text-Fabric will then look at
        your local GitHub directories.

        This is handy when you are still developing your own data,
        and you make frequent changes
        without wanting to publish every intermediate stage.

    ??? info "locations and modules arguments"
        If you want to add other search locations for TF features manually,
        you can pass optional `locations` and `modules` parameters,
        which will be passed to the
        [Fabric()](Fabric.md#loading) call to the core of TF.

        ??? note "More, not less"
            Using these arguments will load features on top of the
            default selection of features.
            You cannot use these arguments to prevent features from being loaded.

    ??? info "api=None"
        So far, the TF app will construct a generic TF API
        with a more or less standard set of features
        loaded, and make that API avaible to you, under `A.api`.

        But you can also setup an API yourself by using the
        [core TF machinery](Fabric.md#loading):

        ```python
        from tf.fabric import Fabric
        TF = Fabric(locations=..., modules=...)
        api = TF.load(features)
        ```

        Here you have full control over what you load and what not.
        
        If you want the extra power of the TF app, you can wrap this `api`:

        ```python
        A = use('xxxx', api=api)
        ```

    ??? info "Unloaded features"
        Some apps do not load all available features of the corpus by default.

        This happens when a corpus contains quite a number of features
        that most people never need.
        Loading them cost time and takes a lot of RAM.

        In the case where you need an available feature that has not been loaded,
        you can load it by demanding

        ```python
        TF.load('feature1 feature2', add=True)
        ```

        provided you have used the `hoist=globals()` parameter earlier.
        If not, you have to say

        ```python
        A.api.TF.load('feature1 feature2', add=True)
        ```

    ??? info "silent=False"
        If `True`, nearly all output of this call will be suppressed,
        including the links to the loaded
        data, features, and the API methods.
        Error messages will still come through.

## Search

??? abstract "A.search()" 
    ```python
    A.search(query, silent=False, shallow=False, sets=None, sort=True)
    ```
    
    ???+ "Description"
        Searches in the same way as the generic Text-Fabric
        [`S.search()`](Search.md#search).
        But whereas the `S` version returns a generator which yields the results
        one by one, the `A` version collects all results and sorts them in the
        [canonical order](../Api/Nodes.md#navigating-nodes).
        (but you can change the sorting, see the `sort` parameter).
        It then reports the number of results.

        It will also set the display parameter `tupleFeatures` (see below)
        in such a way that subsequent calls to `A.export()` emit
        the features that have been used in the query.

    ??? info "query"
        the
        [search template](../Use/Search.md#search-template-reference)
        that has to be searched for.

    ??? info "silent"
        if `True` it will suppress the reporting of the number of results.

    ??? info "shallow"
        If `True` or `1`, the result is a set of things that match the top-level element
        of the `query`.

        If `2` or a bigger number *n*, return the set of truncated result tuples: only
        the first *n* members of each tuple are retained.

        If `False` or `0`, a list of all result tuples will be returned.

    ??? info "sets"
        If not `None`, it should be a dictionary of sets, keyed by a names.
        In `query` you can refer to those names to invoke those sets.

        For example, if you have a set `gappedPhrases` of all phrase nodes
        that have a gap,
        you can pass `sets=dict(gphrase=gappedPhrases)`,
        and then in your query you can say

        ```
        gphrase function=Pred
          word sp=verb
        ```

        etc.

        This is handy when you need node sets that cannot be conveniently queried.
        You can produce them by hand-coding.
        Once you got them, you can use them over and over again in queries.
        Or you can save them with [writeSets](Lib.md#sets)
        and use them in the TF browser.

    ??? info "sort"
        If `True` (default), search results will be returned in 
        [canonical order](../Api/Nodes.md#navigating-nodes).

        ??? note "canonical sort key for tuples"
            This sort is achieved by using the function
            [sortKeyTuple](../Api/Nodes.md#navigating-nodes)
            as sort key.

        If it is a *sort key*, i.e. function that can be applied to tuples of nodes
        returning values,
        then these values will be used to sort the results.  
        
        If it is a False value, no sorting will be applied.

    ??? hint "search template reference"
        See the [search template reference](../Use/Search.md#search-templates)

## Linking

??? abstract "A.webLink()"
    ```python
    A.webLink(node, text=None)
    ```

    ???+ "Description"
        Produces a link to an online website dedicated to the main corpus.

    ??? info "node"
        `node` can be an arbitrary node. The link targets the verse/tablet that
        contains the first word/sign contained by the node.
    
    ??? info "text"
        You may provide the text to be displayed as the link.
        Then the
        passage indicator (book chapter:verse or tablet column line) will be put
        in the tooltip (title) of the link.
        If you do not provide a link text,
        the passage indicator will be chosen.

    ??? example "Ezra 3:4 on SHEBANQ"
        First we obtain the node

        ```python
        z = A.nodeFromSectionStr('Ezra 3:4')
        ```

        then we call `webLink`

        ```python
        A.webLink(z)
        ```

        with this result:
        [Ezra 3:4](https://shebanq.ancient-data.org/hebrew/text?book=Esra&chapter=3&verse=4&version=c&mr=m&qw=q&tp=txt_p&tr=hb&wget=v&qget=v&nget=vt)

### Sections

??? abstract "A.nodeFromSectionStr()"
    ```python
    A.nodeFromSectionStr(sectionStr, lang='en')
    ```

    ???+ info "Description"
        Given a section string pointing to a section,
        return the corresponding node (or an error message).

        Compare [`T.nodeFromSection`](../Api/Text.md#sections).

    ??? info "sectionStr"
        `sectionStr` must be a valid section specficiation in the
        language specified in `lang`.

        The string may specific a section 0 level only (book/tablet), or
        section 0 and 1 levels (book/tablet chapter/column),
        or all levels
        (book/tablet chapter/column verse/line).

        Examples:

        ```
        Genesis
        Genesis 1
        Genesis 1:1
        ```

        ```
        P005381
        P005381 1
        P005381 1:1
        ```

        Depending on what is passed, the result is a node of section level
        0, 1, or 2.

    ??? info "lang"
        The language assumed for the section parts,
        as far as they are language dependent.

??? abstract "A.sectionStrFromNode()"
    ```python
    A.sectionStrFromNode(node, lang='en', lastSlot=False, fillup=False)
    ```

    ???+ info "Description"
        Returns the section label (a string) that correspond to the reference
        node,
        which is the first or last slot belonging to `node`,
        dependent on `lastSlot`.
        The result is a string,
        built from the labels of the individual section levels
        (in language `lang` where applicable).
        But see the `fillup` parameter.

        Compare [`T.sectionFromNode`](../Api/Text.md#sections).

    ??? info "node"
        The node from which we obtain a section specification.

    ??? info "lastSlot"
        Whether the reference node will be the last slot contained by the
        `node` argument or the first node.

    ??? info "lang"
        The language to be used for the section parts,
        as far as they are language dependent.

    ??? info "fillup"
        Same as for [`T.sectionTuple()`](../Api/Text.md#sections)


## Display

??? abstract "About"
    Where a TF app really shines is in displaying nodes.
    There are basically two ways of displaying a node:
    
    *plain*: just the associated text of a node, or if that would be too much,
    an identifying label of that node (e.g. for books, chapters and lexemes).
    
    *pretty*: a display of the internal structure of the textual object a node
    stands for. That structure is adorned with relevant feature values.
    
    A TF app offers these display methods for nodes, tuples of nodes, and iterables
    of tuples of nodes (think: query results).
    The names of these methods are
    
    ```python
    plain() plainTuple() table()
    
    pretty() prettyTuple() show()
    ``` 

??? abstract "Setting up display parameters"
    There is a bunch of parameters that govern how the display functions arrive at their
    results. You can pass them as optional arguments to these functions,
    or you can set up them in advance, and reset them to their original state
    when you are done. 

    All calls to the display functions look for the values for these parameters in the
    following order:
    
    * optional parameters passed directly to the function,
    * values as set up by previous calls to `displaySetup()`,
    * default values configured by the app.

    These are the parameters and their default values:

    ??? info "colorMap=None"
        Which nodes of a tuple (or list of tuples) will be highlighted.
        If `colorMap` is `None` or missing, all nodes will be highlighted with
        the default highlight color, which is yellow.

        But you can assign different colors to the members of the tuple:
        `colorMap` must be a dictionary that maps the positions in a tuple 
        to a color.

        *   If a position is not mapped, it will not be highlighted.
        *   If it is mapped to the empty string, it gets the default highlight color.
        *   Otherwise, it should be mapped to a string that is a valid
            [CSS color]({{moz_color}}).

        ??? hint "color names"
            The link above points to a series of handy color names and their previews.

        ???+ note "highlights takes precedence over colorMap"
            If both `highlights` and `colorMap` are given, `colorMap` is ignored.
            
            If you need to micro-manage, `highlights` is your thing.
            Whenever possible, use `colorMap`.  

    ??? info "condensed=False"
        indicates one of two modes of displaying the result list:

        *   `True`: instead of showing all results one by one,
            we show container nodes with all results in it highlighted.
            That way, we blur the distinction between the individual results,
            but it is easier to oversee where the results are.
            This is how SHEBANQ displays its query results.
            **See also the parameter `condenseType`**.
        *   `False`: make a separate display for each result tuple.
            This gives the best account of the exact result set.

        ???+ caution "mixing up highlights"
            Condensing may mix-up the highlight coloring.
            If a node occurs in two results, at different positions
            in the tuple, the `colorMap` wants to assign it two colors!
            Yet one color will be chosen, and it is unpredictable which one.

    ??? info "condenseType=None"
        The type of container to be used for condensing results.
        The default is app dependent, usually `verse` or `tablet`.

    ??? info "end=None"
        `end` is the end point in the iterable of results.
        If `None`, displaying will stop after the end of the iterable.

    ??? info "extraFeatures=()"
        A string or iterable of feature names.
        These features will be loaded automatically.
        In pretty displays these features will show up as `feature=value`,
        provided the value is not `None`, or something like None.

        ???+ hint "Automatic loading"
            These features will load automatically, no explicit loading is
            necessary.

    ??? info "full=False"
        For pretty displays: indicates that the whole object should be
        displayed, even if it is big.

        ??? hint "Big objects"
            Big objects are objects of a type that is bigger than the default condense type.

    ??? info "fmt=None"
        `fmt` is the text format that will be used for the representation.
        E.g. `text-orig-full`. 

        ??? hint "Text formats"
            Use `T.formats` to inspect what text formats are available in your corpus.

    ??? info "highlights={}"
        When nodes such as verses and sentences and lines and cases are displayed
        by `plain()` or `pretty()`,
        their contents is also displayed. You can selectively highlight
        those parts.

        `highlights={}` is a set or mapping of nodes that should be highlighted.
        Only nodes that are involved in the display will be highlighted.

        If `highlights` is a set, its nodes will be highlighted
        with a default color (yellow).

        If it is a dictionary, it should map nodes to colors.
        Any color that is a valid 
        [CSS color]({{moz_color}})
        qualifies.

        If you map a node to the empty string, it will get the default highlight color.

        ??? hint "color names"
            The link above points to a series of handy color names and their previews.

        ??? note "one big highlights dictionary"
            It is OK to first compose a big highlights dictionary
            for many tuples of nodes,
            and then run `prettyTuple()` for many different tuples
            with the same `highlights`.
            It does not harm performance if `highlights` maps
            lots of nodes outside the tuple as well.

    ??? info "linked=1"
        the number of the column whose cell contents is
        web-linked to the relevant passage
        (the first column is column 1).

    ??? info "noneValues=None"
        A set of values for which no display should be generated.
        The default set is `None` and the strings `NA`, `none`, `unknown`.

        ???+ hint "None is useful"
            Keep `None` in the set. If not, all custom features will be displayed
            for all kinds of nodes. So you will see clause types on words,
            and part of speech on clause atoms, al with value `None`.

        ??? hint "Suppress common values"
            You can use `noneValues` also to suppress the normal values of a feature,
            in order to attract attention to the more special values, e.g.
            
            ```python
            noneValues={None, 'NA', 'unknown', 'm', 'sg', 'p3'}
            ```

        ??? caution "None values affect all features"
            Beware of putting to much in `noneValues`.
            The contents of `noneValues` affect the display of
            all features, not only the custom features.

    ??? info "start=None"
        `start` is the starting point for displaying the iterable of results.
        (1 is the first one).
        If `None`, displaying starts at the first element of the iterable.

    ??? info "suppress=set()"
        a set of names of features that should NOT be displayed.
        By default, quite a number of features is displayed for a node.
        If you find they clutter the display, you can turn them off
        selectively.

    ??? info "tupleFeatures=()"
        A bit like "extraFeatures" above, but more intricate.
        Only meant to steer the
        `A.export()` function below into outputting the
        features you choose.

        It should be a tuple of pairs
        `(i, features)`
        which means that to member `i` of a result tuple we assign extra `features`.

        `features` may be given as an iterable or a space separated string of feature names.

    ??? info "withNodes=False"
        indicates whether node numbers should be displayed.

        ??? hint "zooming in"
            If you are in a Jupyter notebook, you can inspect in a powerful way by
            setting `withNodes=True`. Then every part of a pretty display shows
            its node number, and you can use `L F T E` to look up all information
            about each node that the corpus has to offer.

    ??? info "withPassage=True"
        indicates whether a passage label should be put next to a displayed node
        or tuple of nodes.

??? abstract "A.displaySetup()"
    ```python
    A.displaySetup(parameter1=value1, parameter2=value2, ...)
    ```

    Assigns working values to display parameters. All subsequent calls to
    the display functions will use these values, unless they are passed overriding
    values as arguments.
    
    These working values remain in effect until a new call to `displaySetup()`
    assigns new values, or a call to `displayReset()` resets the values to the
    defaults.

    ??? example "extra features"
        ```python
        A.displayReset(extraFeatures='egg')
        ```

        will cause displays to show the values of the `egg` feature for each node
        that has `egg` values:

        ```python
        A.pretty(n)
        ```

        But if you want to suppress the `egg` for a particular display,
        you can say

        ```python
        A.pretty(n, extraFeatures='')
        ```

        And if you want to turn it off for future displays, you can say

        ```python
        A.displayReset('extraFeatures')
        ```
     
??? abstract "A.displayReset()"
    ```python
    A.displayReset(parameter1, parameter2, ...)
    ```

    Reset the given display parameters to their default value and let the others
    retain their current value.

    So you can reset the display parameters selectively.

    ???+ hint "Reset all"
        If you call this function without parameters at all, the effect is that
        *all* display parameters are reset to their default values:

        ```python
        A.displayReset()
        ```

??? abstract "A.plain()"
    ```python
    A.plain(node, isLinked=False, **displayParameters)
    ```

    ???+ info "Description"
        Displays the material that corresponds to a node in a compact way.
        Nodes with little content will be represented by their text content,
        nodes with large content will be represented by an identifying label.

    ??? info "node"
        a node of arbitrary type.

    ??? info "isLinked"
        indicates whether the result should be a web-link
        to the appropriate passage.

??? abstract "A.plainTuple()"
    ```python
    A.plainTuple(nodes, seqNumber, **displayParameters)
    ```

    ???+ info "Description"
        Displays the material that corresponds to a tuple of nodes
        as a row of cells,
        each displaying a member of the tuple by means of `plain()`.

    ??? info "nodes"
        an iterable (list, tuple, set, etc) of arbitrary nodes.

    ??? info "seqNumber"
        an arbitrary number which will be displayed
        in the first cell.
        This prepares the way for displaying query results, which come as
        a sequence of tuples of nodes.

??? abstract "A.table()"
    ```python
    A.table(results, **displayParameters)
    ```

    ???+ info "Description"
        Displays an iterable of tuples of nodes.
        The list is displayed as a compact markdown table.
        Every row is prepended with the sequence number in the iterable,
        and then displayed by `plainTuple()`

    ??? info "results"
        an iterable of tuples of nodes.
        The results of a search qualify, but it works
        no matter which process has produced the tuples.

    ??? hint "condense, condenseType"
        You can condense the list first to containers of `condenseType`,
        before displaying the list.
        Pass the display parameters `condense` and `condenseType` (documented above).

??? abstract "A.export()"
    ```python
    A.export(results, toDir=None, toFile=None, **displayParameters)
    ```

    ???+ info "Description"
        Exports an iterable of tuples of nodes to an Excel friendly `.tsv` file.
        There will be a row for each tuple.
        The columns are:

        * **R** the sequence number of the result tuple in the result list
        * **S1 S2 S3** the section as book, chapter, verse, in separate columns;
          the section is the section of the first non book/chapter node in the tuple
        * **NODEi TYPEi** the node and its type,
          for each node **i** in the result tuple
        * **TEXTi** the full text of node **i**,
          if the node type admits a concise text representation;
          the criterion is whether the node type has a type not bigger than the
          default condense type, which is app specific.
          If you pass an explicit `condenseType=`*xxx* as display parameter,
          then this is the reference condenseType on which the decision is based.
        * **XFi** the value of extra feature **XF** for node **i**,
          where these features have been declared by a previous 
          displaySetup(tupleFeatures=...)`

        See for detailed examples the
        [exportExcel]({{tutnb}}/bhsa/exportExcel.ipynb)
        and
        [exportExcel]({{tutnb}}/oldbabylonian/exportExcel.ipynb)
        notebooks.

    ??? hint "tupleFeatures"
        If the iterable of tuples are the results of a query you have just
        run, then an appropriate call to `displaySetup(tupleFeatures=...)`
        has already been issued, so you can just say:

        ```python
        results = A.search(query)
        A.export(results)
        ```

    ??? info "results"
        an iterable of tuples of nodes.
        The results of a search qualify, but it works
        no matter which process has produced the tuples.

    ??? info "toDir"
        The destination directory for the exported file.
        By default it is your Downloads folder.

        If the directory does not exist, it will be created.

    ??? info "toFile"
        The name of the exported file.
        By default it is `results.tsv`

    ??? info "tupleFeatures="
        This is a display parameter that steers which features are exported
        with each member of the tuples in the list.
        See above under "Setting up display parameters"
        
    ??? info "fmt="
        This display parameter specifies the text format for any nodes
        that trigger a text value to be exported.

    ??? caution "Encoding"
        The exported file is written in the `utf_16_le` encoding.
        This ensures that Excel can open it without hassle, even if there
        are non-latin characters inside.

        When you want to read the exported file programmatically,
        open it with `encoding=utf_16`.

??? abstract "A.pretty()"
    ```python
    A.pretty(node, **displayParameters)
    ```

    ???+ info "Description"
        Displays the material that corresponds to a node in a graphical way.
        The internal structure of the nodes that are involved is also revealed.

    ??? info "node"
        a node of arbitrary type.

    ??? info "full"
        True or False.
        Normally `pretty(n)` only displays a summary of `n` if `n` is big, i.e.
        it has a type bigger than the *condense type*. 
        If you still want to see the whole big object, pass True: `pretty(n, full=True)`.

        ??? hint "condense type"
            Alternatively, you could have said `pretty(n, condenseType='xxx')` with
            `xxx` a big enough type, but this is a bit clumsy.

    ??? info "extraFeatures, tupleFeatures"
        These display parameters govern which extra features will be displayed in pretty
        displays. The union of what these parameters specify will be taken.

??? abstract "A.prettyTuple()"
    ```python
    A.prettyTuple(tuple, seqNumber, **displayParameters)
    ```

    ???+ info "Description"
        Displays the material that corresponds to a tuple of nodes in a graphical way,
        with customizable highlighting of nodes.
        The member nodes of the tuple will be collected into containers, which
        will be displayed with `pretty()`, and the nodes of the tuple
        will be highlighted in the containers.

    ??? info "tuple"
        `tuple` is an arbitrary tuple of nodes of arbitrary types.

??? abstract "A.show()"
    ```python
    A.show(results, **displayParameters)
    ```

    ???+ info "Description"
        Displays an iterable of tuples of nodes.
        The elements of the list are displayed by `A.prettyTuple()`.

    ??? info "results"
        an iterable of tuples of nodes.
        The results of a search qualify, but it works
        no matter which process has produced the tuples.

    ??? hint "condense, condenseType"
        You can condense the list first to containers of `condenseType`,
        before displaying the list.
        Pass the display parameters `condense` and `condenseType` (documented above).

