# v7 Guide

Here are hints to help you to get the most out version 7 of Text-Fabric.

## Working with new data

There is a new command

```sh
text-fabric-zip
```

to make a distribution of your own features.

For a guide through all the steps of data sharing, see [Add](Add.md)
and for examples see the
[share]({{etcbcnb}}/bhsa/blob/master/tutorial/share.ipynb)
tutorial.


## TF browser command

The `text-fabric` command has several new optional command line arguments: 

`--mod=...` and `-c` and `--sets=...`.

### Foreign data modules

```sh
text-fabric appname --mod=module1,module2
```

* Start a TF browser for appname (such as `bhsa`).
* Loads extra data from `module1` and `module2`,
  to be found in a github repo specfied by the 
  module strings.
* You can specify as many modules as you want.

The module strings must have the form

```
{org}/{repo}/{path}
```

where:

* `{org}` is the organization or person on GitHub,
* `{repo}` is the repository on GitHub,
* `{path}` is the path within the repository to the tf directory.

See also the [Add](Add.md) manual.

You can optionally pass the flag `-c`.
In that case Text-Fabric will check whether a new release of the data is available.
If so, it will download and install it.
This will happen for the main data and all modules specified on the command line.

TF will always download the data to your `~/text-fabric-data` directory.

??? hint "do not modify yourself"
    You can better leave your `~/text-fabric-data` under control
    of Text-Fabric, and not manually add data there.
    It does not much harm to delete data from here, because TF will download
    missing data automatically when needed.

### Custom sets

```sh
text-fabric appname --sets=filePath
```

* Start a TF browser for appname (such as `bhsa`).
* Loads custom sets from `filePath`.

`filePath` must specify a file on your local system (you may use `~` for your home directory.
That file must have been written by calling [`tf.lib.writeSets`](Api/General.md#sets).
Then it contains a dictionary of named node sets.
These names can be used in search templates, and the TF browser will use this dictionary to
resolve those names,
see [S.search() sets argument](Api/General.md#search-api).

### See the foreign data

The features of the data modules you have imported are available in the same way as all other features.

You can use them in queries.

#### In the TF browser

In the browser, pretty displays will show them automatically, because
all features used in a query are displayed in the expanded view.

If you want to see a feature that is not used in the query, you can add it as a trivial search criterion.

For example, if you want to see the `sense` feature when looking for phrases, add it like this

```
clause
  phrase sense*
```

* The `*` means: always true, so it will not influence the query result set, only its display;
* In fact, the feature sense is only present on nodes of type `word`. But mentioning a feature anywhere in the query
  will trigger the display wherever it occurs with a non-trivial values.
* The extra data modules are also shown in the provenance listings when you export data from the browser.

#### In a Jupyter notebook

After the incantation, you see an overview of all features per module where they come from, and
linked to their documentation or repository.

You can use the new features exactly as you are used to, with `F` and `E` (for edge features).

They will not automatically show up in `pretty` displays, because `pretty` does not know that it is
displaying query results, and hence does not know which features were used in the latest query.

So you have to tell which features you want to add to the display.
That can be done by [prettySetup](Api/Apps.md#pretty-display):

```python
A.prettySetup(features='sense')
```

and from then on the value of `sense` will be shown
on every item that has a real value for the feature `sense`.

You can cancel the extra features by

```python
A.prettySetup()
```
## Incantation 

The old incantations `B = Bhsa()` and `CN = Cunei()` do no longer work.

The new way is as follows:

```python
from tf.app import use
A = use('bhsa', hoist=globals())
```

```python
from tf.app import use
A = use('uruk', hoist=globals())
```

Instead of `bhsa` and `uruk` you may fill in any corpus for which a Text-Fabric app has been
developed. See [Corpora](Corpora.md). 

Note that we no longer use `cunei` as name of the corpus, but the more precise `uruk`.

You see that app names (`bhsa`, `uruk`) are used once in the incantation, as first argument for the
`use()` function.

Think of the `use {database}` statements in MySQL and MongoDb.

Without further arguments, this will set up an TF API with most features loaded.

??? abstract "Start up sequence"
    During start-up the following happens:

    (1) the BHSA data is downloaded to your `~/text-fabric-data` directory, if not already present there;

    (2) if your data has been freshly downloaded, a series of optimizations are executed;

    (3) most optimized features of the Bhsa dataset are loaded;

### Remaining arguments for the incantation.

??? info "hoist=globals()"
    This makes the API elements directly available as global names in your script or notebook:
    you can refer to `F`, `L`, `T`, etc. directly,
    instead of the more verbose `A.api.F`, `A.api.L`, `A.api.T` etc.

    If you pass this argument, TF will show you what names will be inserted in your namespace.
    And if you are in a Jupyter notebook, these names are linked to their documentation.

??? info "version=VERSION"
    If you do not want to work with the default version of your main corpus, you can specify 
    a different version here.

    ??? example "BHSA"
        ```python
        A = use('bhsa', version='2017')
        ```

        In fact, this single statement will download that BHSA version if you do not already have it.

??? info "api=None"
    The API resulting from an earlier call `TF.load()`
    If you leave it out, an API will be created exactly like the TF-browser does it,
    with the same data version and the same set of data features.

    But you can also wrap an existing TF api object into a Text-Fabric app object:

    ```python
    VERSION = '2017'
    TF = Fabric(locations=f'~/github/etcbc/bhsa/tf/{VERSION}')
    api = TF.load('''
      function sp gn nu
    ''')
    api.makeAvailableIn(globals())
    ```

??? info "name=None"
    If you leave this argument out, Text-Fabric will determine the name of your notebook for you.

    If Text-Fabric finds the wrong name, you can override it here.

    This should be the name
    of your current notebook (without the `.ipynb` extension).
    Text-Fabric will use this to generate a link to your notebook
    on GitHub and NBViewer.

??? info "silent=False"
    If `True`, nearly all output of this call will be suppressed,
    including the links to the loaded
    data, features, API methods, and online versions of the notebook.
    Error messages will still come through.

??? info "mod=None"
    `mod` is a comma-separated list of modules in the form `{org}/{repo}/{path}`.
    It will load all features of all those modules, and download them from GitHub
    of they are missing.

??? info "check=False"
    If `True`, Text-Fabric will check each module for newer releases.
    For every module for which a newer release than the locally available one is found,
    the newest data will be downloaded.

??? info "lgc=False"
    Normally, Text-Fabric will work with data that is stored under your `~/text-fabric-data`.
    But if you have cloned a repository with data, and you want to use that instead,
    you can pass `lgc=True`. Text-Fabric will then look first under `~/github` for data.


??? info "locations and modules arguments"
    If you want to add other search locations for TF features manually, you can pass
    optional `locations` and `modules` parameters, which will be passed to the underlying
    [Fabric()](Api/General.md#loading) call.

## App specific functions

The following app specific functions enhance TF.
They are available in all Text-Fabric apps, but their implementation makes
use of the specifics of the main corpus.

## Search

??? abstract "A.search()" 
    ```python
    A.search(query, silent=False, shallow=False, sets=None)
    ```
    
    ???+ "Description"
        Searches in the same way as the generic Text-Fabric `S.search()`.
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

        For example, if you have a set `gappedPhrases` of all phrase nodes that have a gap,
        you can pass `sets=dict(gphrase=gappedPhrases)`, and then in your query you can say

        ```
        gphrase function=Pred
          word sp=verb
        ```

        etc.

        This is handy when you need node sets that cannot be conveniently queried.
        You can produce them by hand-coding.
        Once you got them, you can use them over and over again in queries.
        Or you can save them with [writeSets](Api/General.md#sets)
        and use them in the TF browser.

    ??? hint "search template reference"
        See the [search template reference](Search.md#search-templates)

### Linking

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

### Plain display

??? explanation "Straightforward display of things"
    There are functions to display nodes, tuples of nodes, and iterables of tuples
    of nodes in a simple way, as rows and as a table.

??? abstract "A.plain()"
    ```python
    A.plain(node, fmt=None, linked=True, withNodes=False, asString=False)
    ```

    ???+ info "Description"
        Displays the material that corresponds to a node in a simple way.

    ??? info "node"
        `node` is a node of arbitrary type.

    ??? info "fmt"
        `fmt` is the text format that will be used for the represantation.

    ??? info "linked"
        `linked` indicates whether the result should be a weblink
        to the appropriate passage.

    ??? info "withNodes"
        `withNodes` indicates whether node numbers should be displayed.

    ??? info "asString" 
        Instead of displaying the result directly in the output of your
        code cell in a notebook, you can also deliver the markdown as string,
        just say `asString=True`.

??? abstract "A.plainTuple()"
    ```python
    A.plainTuple(nodes, seqNumber, fmt=None, linked=1, withNodes=False, asString=False)
    ```

    ???+ info "Description"
        Displays the material that corresponds to a tuple of nodes
        in a simple way as a row of cells.

    ??? info "nodes"
        `nodes` is an iterable (list, tuple, set, etc) of arbitrary nodes.

    ??? info "seqNumber"
        `seqNumber` is an arbitrary number which will be displayed
        in the first cell.
        This prepares the way for displaying query results, which come as
        a sequence of tuples of nodes.

    ??? info "linked"
        `linked=1` the column number where the cell contents is
        weblinked to
        the relevant passage;
        (the first data column is column 1)

    ??? info "fmt, withNodes, asString"
        Same as in `A.plain()`.

??? abstract "A.table()"
    ```python
    A.table(
      results,
      fmt=None,
      start=1, end=len(results),
      linked=1,
      withNodes=False,
      asString=False,
    )
    ```

    ???+ info "Description"
        Displays an iterable of tuples of nodes.
        The list is displayed as a compact markdown table.
        Every row is prepended with the sequence number in the iterable.

    ??? info "results"
        `results` an iterable of tuples of nodes.
        The results of a search qualify, but it works
        no matter which process has produced the tuples.

    ??? info "start"
        `start` is the starting point in the results iterable (1 is the first one).
        Default 1.

    ??? info "end"
        `end` is the end point in the results iterable.
        Default the length of the iterable.

    ??? info "linked, fmt, withNodes, asString"
        Same as in `A.plainTuple()`.

### Pretty display

??? explanation "Graphical display of things"
    There are functions to display nodes, tuples of nodes, and iterables of tuples
    of nodes in a graphical way.

??? abstract "A.prettySetup()"
    ```python
    A.prettySetup(features=None, noneValues=None)
    ```
    ???+ info "Description"
        In pretty displays, nodes are shown together with the values of a selected
        set of features. 
        With this function you can add features to the display.

    ??? info "features"
        A string or iterable of feature names.
        These features will be loaded automatically.
        In pretty displays these features will show up as `feature=value`,
        provided the value is not `None`, or something like None.

        ???+ hint "Automatic loading"
            These features will load automatically, no explicit loading is
            necessary.

    ??? info "noneValues"
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

??? abstract "A.pretty()"
    ```python
    A.pretty(node, fmt=None, withNodes=False, suppress=set(), highlights={})
    ```

    ???+ info "Description"
        Displays the material that corresponds to a node in a graphical way.

    ??? info "node"
        `node` is a node of arbitrary type.

    ??? info "fmt"
        `fmt` is the text format that will be used for the represantation.

    ??? info "withNodes"
        `withNodes` indicates whether node numbers should be displayed.

    ??? info "suppress"
        `suppress=set()` is a set of feature names that should NOT be displayed.
        By default, quite a number of features is displayed for a node.
        If you find they clutter the display, you can turn them off
        selectively.

    ??? explanation "Highlighting"
        When nodes such as verses and sentences are displayed by `pretty()`,
        their contents is also displayed. You can selectively highlight
        those parts.

    ??? info "highlights"
        `highlights={}` is a set or mapping of nodes that should be highlighted.
        Only nodes that are involved in the display will be highlighted.

        If `highlights` is a set, its nodes will be highlighted with a default color (yellow).

        If it is a dictionary, it should map nodes to colors.
        Any color that is a valid 
        [CSS color]({{moz_color}})
        qualifies.

        If you map a node to the empty string, it will get the default highlight color.

        ??? hint "color names"
            The link above points to a series of handy color names and their previews.

??? abstract "A.prettyTuple()"
    ```python
    A.prettyTuple(
      nodes, seqNumber,
      fmt=None,
      withNodes=False,
      suppress=set(),
      colorMap=None,
      highlights=None,
    )
    ```

    ???+ info "Description"
        Displays the material that corresponds to a tuple of nodes in a graphical way,
        with customizable highlighting of nodes.

    ??? explanation "By verse"
        We examine all nodes in the tuple.
        We collect and show all verses in which they
        occur and highlight the material corresponding to all the nodes in the tuple.
        The highlighting can be tweaked by the optional `colorMap` parameter.

    ??? info "nodes, seqNumber, fmt, withNodes"
        Same as in `A.plainTuple()`.

    ??? info "suppress"
        Same as in `A.pretty()`.

    ??? info "colorMap"
        The nodes of the tuple will be highlighted.
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

    ??? info "highlights"
        Same as in `A.pretty()`.

    ???+ note "highlights takes precedence over colorMap"
        If both `highlights` and `colorMap` are given, `colorMap` is ignored.
        
        If you need to micro-manage, `highlights` is your thing.
        Whenever possible, use `colorMap`.  

    ??? note "one big highlights dictionary"
        It is OK to first compose a big highlights dictionary for many tuples of nodes,
        and then run `prettyTuple()` for many different tuples with the same `highlights`.
        It does not harm performance if `highlights` maps lots of nodes outside the tuple as well.

??? abstract "A.show()"
    ```python
    A.show(
      results,
      condensed=True,
      start=1, end=len(results),
      fmt=None,
      withNodes=False,
      suppress=set(),
      colorMap=None,
      highlights=None,
    )
    ```

    ???+ info "Description"
        Displays an iterable of tuples of nodes.
        The elements of the list are displayed by `A.prettyTuple()`.

    ??? info "results"
        `results` an iterable of tuples of nodes.
        The results of a search qualify, but it works
        no matter which process has produced the tuples.

    ??? info "condensed"
        `condensed` indicates one of two modes of displaying the result list:

        *   `True`: instead of showing all results one by one,
            we show all verses with all results in it highlighted.
            That way, we blur the distinction between the individual results,
            but it is easier to oversee where the results are.
            This is how SHEBANQ displays its query results.
        *   `False`: make a separate display for each result tuple.
            This gives the best account of the exact result set.

        ???+ caution "mixing up highlights"
            Condensing may mix-up the highlight coloring.
            If a node occurs in two results, at different positions
            in the tuple, the `colorMap` wants to assign it two colors!
            Yet one color will be chosen, and it is unpredictable which one.

    ??? info "start"
        `start` is the starting point in the results iterable (1 is the first one).
        Default 1.

    ??? info "end"
        `end` is the end point in the results iterable.
        Default the length of the iterable.

    ??? info "fmt, withNodes, suppress, colorMap, highlights"
        Same as in `A.prettyTuple()`.
