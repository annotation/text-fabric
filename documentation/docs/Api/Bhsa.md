# BHSA

## About

The module [bhsa.py](https://github.com/Dans-labs/text-fabric/blob/master/tf/extra/bhsa.py)
contains a number of handy functions on top of Text-Fabric and especially its 
[Search](/Api/General/#search) part.

## Set up

??? note "`from tf.extra.bhsa import Bhsa`"
    ??? explanation "import Bhsa"
        The `Bhsa` API is distributed with Text-Fabric.
        You have to import it into your program.

## Initialisation

??? note "`from tf.extra.bhsa import Bhsa`"
    ??? explanation "import Bhsa"
        The `Bhsa` API is distributed with Text-Fabric.
        You have to import it into your program.

??? note "`Bhsa()`"
    ```python
    B = Bhsa(api, 'test', version=VERSION)
    ```

    ???+ info "Description"
        Silently loads some additional features, and `B`
        will give access to some extra functions.

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

    ??? info "Name of your notebook"
        The second argument of `Bhsa()` should be the name
        of your current notebook (without the `.ipynb` extension).
        The Bhsa API will use this to generate a link to your notebook
        on GitHub and NBViewer.

## Linking

??? note "`B.shbLink()`"
    ```python
    B.shbLink(node, text=None)
    ```

    ???+ "Description"
        Produces a link to SHEBANQ

    ??? info "node"
        `node` can be an arbitrary node. The link targets the verse that
        contains the first word contained by the node.
    
    ??? info "link text"
        You may provide the text to be displayed as the link.
        Then the
        passage indicator (book chapter:verse) will be put
        in the tooltip (title) of the link.
        If you do not provide a link text,
        the passage indicator (book chapter:verse) will be chosen.

    ??? example "Word 100000 on SHEBANQ"
        ```python
        B.shbLink(100000)
        ```

## Plain display

??? explanation "Straightforward display of things"
    There are functions to display nodes, tuples of nodes, and iterables of tuples
    of nodes in a simple way, as rows and as a table.

??? note "`B.plain()`"
    ```python
    B.plain(node, linked=True, withNodes=False, asString=False)
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

??? note "`B.plainTuple()`"
    ```python
    B.plainTuple(nodes, linked=1, withNodes=False, asString=False)
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
        the relevant passage in to SHEBANQ;
        (the first data column is column 1)

    ??? info "withNodes, asString"
        Same as in `B.plain()`.

??? note "`B.table()`"
    ```python
    B.table(
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
        Same as in `B.plainTuple()`.

## Pretty display

??? explanation "Graphical display of things"
    There are functions to display nodes, tuples of nodes, and iterables of tuples
    of nodes in a graphical way.

??? note "`B.pretty()`"
    ```python
    B.pretty(node, withNodes=False, suppress=set(), highlights=set())
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

    ??? info "highlights"
        `highlights=set()` is a set of nodes that should be highlighted.
        Only nodes that are involved in the display will be highlighted.

    ??? explanation "Highlighting"
        When nodes such as verses and sentences are displayed by `pretty()`,
        their contents is also displayed. You can selectively highlight
        those parts.

??? note "`B.prettyTuple()`"
    ```python
    B.prettyTuple(
      nodes, seqNumber,
      withNodes=False,
      suppress=set(),
    )
    ```

    ???+ info "Description"
        Displays the material that corresponds to a tuple of nodes in a graphical way.

    ??? explanation "By verse"
        We examine all nodes in the tuple.
        We collect and show all verses in which they
        occur and highlight the material corresponding to all the nodes in the tuple.

    ??? info "nodes, seqNumber, withNodes"
        Same as in `B.plainTuple()`.

    ??? info "suppress"
        Same as in `B.pretty()`.

??? note "`B.show()`"
    ```python
    B.show(
      results,
      condensed=True,
      start=1, end=len(results),
      withNodes=False,
      suppress=set(),
    )
    ```

    ???+ info "Description"
        Displays an iterable of tuples of nodes.
        The elements of the list are displayed by `B.prettyTuple()`.

    ??? info "results"
        `results` an iterable of tuples of nodes.
        The results of a search qualify, but it works
        no matter which process has produced the tuples.

    ??? info "condensed"
        `condensed` indicates one of two modes of displaying the result list:

        * `True`: instead of showing all results one by one,
          we show all verses with all results in it highlighted.
          That way, we blur the distinction between the individual results,
          but it is easier to oversee where the results are.
          This is how SHEBANQ displays its query results.
        * `False: make a separate display for each result tuple.
          This gives the best account of the exact result set.

    ??? info "start"
        `start` is the starting point in the results iterable (1 is the first one).
        Default 1.

    ??? info "end"
        `end` is the end point in the results iterable.
        Default the length of the iterable.

    ??? info "withNodes, suppress"
        Same as in `B.plainTuple()`.

## Search

??? note "`B.search()`" 
    ```python
    B.search(query, silent=False)
    ```
    
    ???+ "Description"
        Searches in the same way as the generic Text-Fabric `S.search()`.
        But whereas the `S` version returns a generator which yields the results
        one by one, the `B` version collects all results and sorts them.
        It then reports the number of results.

    ??? info "query"
        `query` is the search template that has to be searched for.

    ??? info "silent mode"
        `silent`: if `True` it will suppress the reporting of the number of results.
