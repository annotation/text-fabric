# App API

??? abstract "About"
    The most important extra functionality that the app API provides, is display.
    The functions `plain()` and `pretty()` are able to display nodes using extra
    information about what those nodes typically represent in a specific corpus.

    An app also knows how to download the data,
    it can be invoked by a simple incantation.

## Incantation

??? abstract "A.use()"
    ```python
    from tf.app import use
    A = use(appName)
    ```

    Currently, `bhsa`, `peshitta`, `syrnt` and `uruk` are valid app names.
    See [Corpora](../About/Corpora.md). 

    Hint: think of the `use {database}` statements in MySQL and MongoDb.

    Without further arguments, this will set up an TF API with most features loaded.

    ??? abstract "Start up sequence"
        During start-up the following happens:

        (1) the BHSA data is downloaded to your `~/text-fabric-data` directory,
        if not already present there;

        (2) if your data has been freshly downloaded,
        a series of optimizations are executed;

        (3) most optimized features of the Bhsa dataset are loaded;

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
    that wants to work with as much data possible with the least of hassles.
    It makes some standard choices for you, and it will auto-download data.

    The following options are for people who want increasingly finer control
    over the features that are being loaded.

    ??? info "version=VERSION"
        If you do not want to work with the default version of your main corpus,
        you can specify a different version here.

        ??? example "BHSA"
            ```python
            A = use('bhsa', version='2017')
            ```

            In fact, this single statement will download that BHSA version
            if you do not already have it.

        ??? note "Modules"
            If you also ask for extra data modules by means of the `mod` argument,
            then the corresponding version
            of those modules will be chosen.
            Every properly designed data module must refer to a specific
            version of the main source!

    ??? info "mod=None"
        `mod` is a comma-separated list of modules in the form `{org}/{repo}/{path}`.
        It will load all features of all those modules, and download them from GitHub
        of they are missing.
        For example, their is an easter egg module on GitHub, and you can obtain it by

        ```
        mod='etcbc/lingo/easter/tf'
        ```

        Here the `{org}` is `etcbc`, the `{repo}` is `lingo`,
        and within that repo there is a directory `tf`
        below which version `c` of the additional feature `egg`
        is avaialble in TF format.

        You can point to any such directory om the entire GitHub
        if you know that it contains relevant features.

        Your TF app might be configured to download specific modules.
        The BHSA app invokes the phono features
        and the crossref features.
        See the app's [config file]({{tfghb}}/{{c_bhsa_config}}).

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
        But if you have cloned a repository with data into `~/github/{org}/{repo}`,
        and you want to use that instead,
        you can pass `lgc=True`. Text-Fabric will then look at
        your local GitHub directories.

        This is handy when you are still developing your own data,
        and you make frequent changes
        without wanting to publish every intermediate stage.

    ??? info "locations and modules arguments"
        If you want to add other search locations for TF features manually,
        you can pass optional `locations` and `modules` parameters,
        which will be passed to the underlying
        [Fabric()](General.md#loading) call.

        ??? note "More, not less"
            Using these arguments will load features on top of the default selection.
            You cannot use these arguments to prevent features from being loaded.

    ??? info "api=None"
        So far, the TF app will construct a generic TF API
        with a more or less standard set of features
        loaded, and make that API avaible to you, under `A.api`.

        But you can also setup an API yourself by using the core TF machinery:

        ```python
        from tf.fabric import Fabric
        TF = Fabric(locations=..., modules=...)
        api = TF.load(features)
        ```

        Here you have full control over what you load and what not.
        
        If you want the extra power of the TF app, you can wrap this `api`:

        ```python
        A = use('bhsa', api=api)
        ```

    ??? info "Unloaded features"
        Some apps do not load all available features of the corpus by default.

        For example, the BHSA contains quite a number of features
        that most people never need.
        Loading them cost time and takes a lot of RAM.

        In the case where you need an available feature that has not been loaded,
        you can load it by demanding

        ```python
        TF.load('feature1 feature2', add=True)
        ```python

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
        [`S.search()`](General.md#search).
        But whereas the `S` version returns a generator which yields the results
        one by one, the `A` version collects all results and sorts them.
        It then reports the number of results.

    ??? info "query"
        `query` is the search template that has to be searched for.

    ??? info "silent"
        `silent`: if `True` it will suppress the reporting of the number of results.

    ??? info "shallow"
        If `True` or `1`, the result is a set of things that match the top-level element
        of the `query`.

        If `2` or a bigger number *n*, return the set of truncated result tuples: only
        the first *n* members of each tuple is retained.

        If `False` or `0`, a sorted list of all result tuples will be returned.

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
        Or you can save them with [writeSets](General.md#sets)
        and use them in the TF browser.

    ??? info "sort"
        If `True` (default), search results will be returned in 
        [canonical order](../Api/General.md#navigating-nodes).

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
        Produces a link to an online website dedicated to the main corpus,
        e.g. SHEBANQ for the BHSA, and CDLI for Uruk.

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

    ??? example "Word 100000 on SHEBANQ"
        ```python
        A.webLink(100000)
        ```

### Sections

??? abstract "A.nodeFromSectionStr()"
    ```python
    A.nodeFromSectionStr(sectionStr, lang='en')
    ```

    ???+ info "Description"
        Given a section string pointing to a section,
        return the corresponding node (or an error message).

        Compare [`T.nodeFromSection`](../Api/General.md#sections).

    ??? info "sectionStr"
        `sectionStr` must be a valid section specficiation in the
        language specified in `lang`.

        The string may specific a section 0 level only (book), or
        section 0 and 1 levels (book chapter), or all levels (book
        chapter verse).

        Examples:

        ```
        Genesis
        Genesis 1
        Genesis 1:1
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

        Compare [`T.sectionFromNode`](../Api/General.md#sections).

    ??? info "node"
        The node from which we obtain a section specification.

    ??? info "lastSlot"
        Whether the reference node will be the last slot contained by the
        `node` argument or the first node.

    ??? info "lang"
        The language to be used for the section parts,
        as far as they are language dependent.

    ??? info "fillup"
        Same as for [`T.sectionTuple()`](../Api/General.md#sections)


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
    All calls to the display functions first look at their given parameters,
    then at how you have set up them in advance, and then at their default values.

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
            we show all verses with all results in it highlighted.
            That way, we blur the distinction between the individual results,
            but it is easier to oversee where the results are.
            This is how SHEBANQ displays its query results.
        *   `False`: make a separate display for each result tuple.
            This gives the best account of the exact result set.

        ??? hint "condenseType"
            Instead of verses as containers, you may choose any node type you like.
            Use the parameter `condenseType` to specify it.

        ???+ caution "mixing up highlights"
            Condensing may mix-up the highlight coloring.
            If a node occurs in two results, at different positions
            in the tuple, the `colorMap` wants to assign it two colors!
            Yet one color will be chosen, and it is unpredictable which one.

    ??? info "condenseType=None"
        the node type that acts as a container when lists of tuples are being condensed
        (see parameter `condensed`).

    ??? info "end=None"
        `end` is the end point in the results iterable.
        Default the length of the iterable.

    ??? info "extraFeatures=()"
        A string or iterable of feature names.
        These features will be loaded automatically.
        In pretty displays these features will show up as `feature=value`,
        provided the value is not `None`, or something like None.

        ???+ hint "Automatic loading"
            These features will load automatically, no explicit loading is
            necessary.

    ??? info "fmt=None"
        `fmt` is the text format that will be used for the representation.
        E.g. `text-orig-full`. 

        ??? hint "Text formats"
            Use `T.formats` to inspect what text formats are available in your corpus.

    ??? info "highlights={}"
          When nodes such as verses and sentences are displayed
					by `plain)_` or `pretty()`,
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
        the column number where the cell contents is
        weblinked to the relevant passage;
        (the first data column is column 1)

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
        `start` is the starting point in the results iterable (1 is the first one).
        Default 1.

    ??? info "suppress=set()"
        a set of names of features that should NOT be displayed.
        By default, quite a number of features is displayed for a node.
        If you find they clutter the display, you can turn them off
        selectively.

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

    and from then on the value of `sense` will be shown
    on every item that has a real value for the feature `sense`.

??? abstract "A.displayReset()"
    ```python
    A.displayReset(parameter1, parameter2, ...)
    ```

    Restore the given display parameters to their default value and let the others
    retain their current value.

??? abstract "A.plain()"
    ```python
    A.plain(node, asString=False, isLinked=False, **displayParameters)
    ```

    ???+ info "Description"
        Displays the material that corresponds to a node in a simple way.

    ??? info "node"
        a node of arbitrary type.

    ??? info "isLinked"
        indicates whether the result should be a weblink
        to the appropriate passage.

    ??? info "asString" 
        Instead of displaying the result directly in the output of your
        code cell in a notebook, you can also deliver the markdown as string,
        just say `asString=True`.

??? abstract "A.plainTuple()"
    ```python
    A.plainTuple(nodes, seqNumber, asString=False, **displayParameters)
    ```

    ???+ info "Description"
        Displays the material that corresponds to a tuple of nodes
        in a simple way as a row of cells.

    ??? info "nodes"
        an iterable (list, tuple, set, etc) of arbitrary nodes.

    ??? info "seqNumber"
        an arbitrary number which will be displayed
        in the first cell.
        This prepares the way for displaying query results, which come as
        a sequence of tuples of nodes.

    ??? info "asString" 
        As in `plain()`

??? abstract "A.table()"
    ```python
    A.table(results, asString=False, **displayParameters)
    ```

    ???+ info "Description"
        Displays an iterable of tuples of nodes.
        The list is displayed as a compact markdown table.
        Every row is prepended with the sequence number in the iterable.

    ??? info "results"
        an iterable of tuples of nodes.
        The results of a search qualify, but it works
        no matter which process has produced the tuples.

    ??? info "asString" 
        As in `plain()`

??? abstract "A.pretty()"
    ```python
    A.pretty(node, **displayParameters)
    ```

    ???+ info "Description"
        Displays the material that corresponds to a node in a graphical way.

    ??? info "node"
        a node of arbitrary type.

??? abstract "A.prettyTuple()"
    ```python
    A.prettyTuple(tuple, seqNumber, **displayParameters)
    ```

    ???+ info "Description"
        Displays the material that corresponds to a tuple of nodes in a graphical way,
        with customizable highlighting of nodes.

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


