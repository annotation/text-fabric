# BHSA

## About

The module [bhsa.py](https://github.com/Dans-labs/text-fabric/blob/master/tf/extra/bhsa.py)
contains a number of handy functions on top of Text-Fabric and especially its 
[Search](/Api/General/#search) part.

## Minimal incantation

```python
from tf.extra.bhsa import Bhsa
A = Bhsa(hoist=globals())
```

??? abstract "Explanation"
    The first line makes the Bhsa API code, which is an app on top of Text-Fabric,
    accessible to your notebook.

    The second line starts up the Bhsa API and gives it the name `A`. 
    During start-up the following happens:

    (1) the Bhsa data is downloaded to your `~/text-fabric-data` directory, if not already present there;

    (2) if your data has been freshly downloaded, a series of optimizations are executed;

    (3) most optimized features of the Bhsa dataset are loaded;

    (4) `hoist=globals()` makes the API elements directly available:
    you can refer to `F`, `L`, `T`, etc. directly,
    instead of the more verbose `A.api.F`, `A.api.L`, `A.api.T` etc.

If you are content with the minimal incantation, you can skip **Set up** and **Initialisation**.

## Set up

??? abstract "import Bhsa"
    The `Bhsa` API is distributed with Text-Fabric.
    You have to import it into your program:

    ```python
    from tf.extra.bhsa import Bhsa
    ```

## Initialisation

??? abstract "Bhsa()"
    ```python
    A = Bhsa(api=api, name=None, version=VERSION)
    ```

    ???+ info "Description"
        Silently loads some additional features, and `A`
        will give access to some extra functions.

    ??? hint "Specific BHSA version"
        The easiest way to load a specific version of the BHSA is like so:

        ```python
        A = Bhsa(version='2017')
        ```

    ??? info "api"
        The API resulting from an earlier call `TF.load()`
        If you leave it out, an API will be created exactly like the TF-browser does it,
        with the same data version and the same set of data features.

        ??? explanation "Set up"
            This module comes in action after you have set up TF and loaded some features, e.g.

            ```python
            VERSION = '2017'
            TF = Fabric(locations=f'~/github/etcbc/bhsa/tf/{VERSION}')
            api = TF.load('''
              function sp gn nu
            ''')
            api.makeAvailableIn(globals())
            ```

            Then we add the functionality of the `bhsa` module by a call to `Bhsa()`.

    ??? info "name"
        If you leave this argument out, Text-Fabric will determine the name of your notebook for you.

        If Text-Fabric finds the wrong name, you can override it here.

        This should be the name
        of your current notebook (without the `.ipynb` extension).
        The Bhsa API will use this to generate a link to your notebook
        on GitHub and NBViewer.


## Linking

??? abstract "A.shbLink()"
    ```python
    A.shbLink(node, text=None)
    ```

    ???+ "Description"
        Produces a link to SHEBANQ

    ??? info "node"
        `node` can be an arbitrary node. The link targets the verse that
        contains the first word contained by the node.
    
    ??? info "text"
        You may provide the text to be displayed as the link.
        Then the
        passage indicator (book chapter:verse) will be put
        in the tooltip (title) of the link.
        If you do not provide a link text,
        the passage indicator (book chapter:verse) will be chosen.

    ??? example "Word 100000 on SHEBANQ"
        ```python
        A.shbLink(100000)
        ```

## Plain display

??? explanation "Straightforward display of things"
    There are functions to display nodes, tuples of nodes, and iterables of tuples
    of nodes in a simple way, as rows and as a table.

??? abstract "A.plain()"
    ```python
    A.plain(node, linked=True, withNodes=False, asString=False)
    ```

    ???+ info "Description"
        Displays the material that corresponds to a node in a simple way.

    ??? info "node"
        `node` is a node of arbitrary type.

    ??? info "linked"
        `linked` indicates whether the result should be a link to SHEBANQ
        to the appropriate book/chapter/verse.

    ??? info "withNodes"
        `withNodes` indicates whether node numbers should be displayed.

    ??? info "asString" 
        Instead of displaying the result directly in the output of your
        code cell in a notebook, you can also deliver the markdown as string,
        just say `asString=True`.

??? abstract "A.plainTuple()"
    ```python
    A.plainTuple(nodes, seqNumber, linked=1, withNodes=False, asString=False)
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
        linked to
        the relevant passage in SHEBANQ;
        (the first data column is column 1)

    ??? info "withNodes, asString"
        Same as in `A.plain()`.

??? abstract "A.table()"
    ```python
    A.table(
      results,
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

    ??? info "linked, withNodes, asString"
        Same as in `A.plainTuple()`.

## Pretty display

??? explanation "Graphical display of things"
    There are functions to display nodes, tuples of nodes, and iterables of tuples
    of nodes in a graphical way.

??? abstract "A.prettySetup()"
    ```python
    A.pretty(features=None, noneValues=None)
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
    A.pretty(node, withNodes=False, suppress=set(), highlights={})
    ```

    ???+ info "Description"
        Displays the material that corresponds to a node in a graphical way.

    ??? info "node"
        `node` is a node of arbitrary type.

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
        [CSS color](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value)
        qualifies.

        If you map a node to the empty string, it will get the default highlight color.

        ??? hint "color names"
            The link above points to a series of handy color names and their previews.

??? abstract "A.prettyTuple()"
    ```python
    A.prettyTuple(
      nodes, seqNumber,
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

    ??? info "nodes, seqNumber, withNodes"
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
            [CSS color](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value).

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

    ??? info "withNodes, suppress, colorMap, highlights"
        Same as in `A.prettyTuple()`.

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

    ??? hint "search template reference"
        See the [search template reference](/Api/General#search-templates)
