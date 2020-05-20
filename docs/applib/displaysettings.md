# Display Settings.

Display options are used by
`tf.applib.display.plain`
and
`tf.applib.display.pretty`
and other display functions.

This class manages

* the provisining of options with defaults,
* the overriding options by passing options as arguments to display functions
* the retrieval of option values by the rest of the application.

!!! note "distinction between interface options and display options"
    * all interface options are also display options and can be passed as arguments
      to display functions
    * interface options have a checkbox in the TF browser

Parameters
----------
lineNumbers: boolean, optional `False`
    **interface option**
    indicates whether line numbers should be displayed.

    !!! note "source data"
        Line numbers are with respect to the source data file that is contains the
        origin material of the node in question, if a datasource provides
        a feature that contains line numbers.

    !!! caution "configuration"
        Whether a corpus has line numbers, and in which feature they are stored
        for which node types is configured in a corpus dependent app.
prettyTypes: boolean, optional `False`
    **interface option**
    indicates whether node types should always be displayed in pretty displays.
    The node type of slot nodes is never displayed.
queryFeatures: boolean, optional `True`
    **interface option**
    indicates whether pretty displays should show the features
    mentioned in the last query and their values.
showChunks: boolean, optional `False`
    **interface option**
    The corpus data may contain nodes that represent discontinuous pieces of text.
    Some corpora also offer node types that represent all continuous chunks of those
    nodes.
    By default, the advanced API, will
    show those chunks with the original nodes wrapped around them, with dotted borders
    indicating the discontinuities..
    When pretty-displaying such structures, the display of the chunks themselves can be
    reduced, because they tend to make displays unwieldy.
showGraphics: boolean, optional `True`
    **interface option**
    indicates whether plain and pretty displays should include associated
    graphic elements,
    provided the corpus offers those elements, and the advanced API has found a way to
    locate those elements.
standardFeatures: boolean, optional `True`
    **interface option**
    indicates whether pretty displays should show standard features and their values.
withNodes: boolean, optional `False`
    **interface option**
    indicates whether node numbers should be displayed.

    !!! hint "zooming in"
        If you are in a Jupyter notebook, you can inspect in a powerful way by
        setting `withNodes=True`. Then every part of a pretty display shows
        its node number, and you can use the following APIs
        to look up all information
        about each node that the corpus has to offer:

        * **F**: `tf.core.api.NodeFeature`
        * **E**: `tf.core.api.EdgeFeature`
        * **L**: `tf.core.locality.Locality`
        * **T**: `tf.core.text.Text`
withTypes: boolean, optional `False`
    **interface option**
    indicates whether node types should be displayed.
    The node type of slot nodes is never displayed.
baseTypes: string | iterable, optional `None`
    Node types at the bottom of pretty displays.
    They are also the node type that receive the primary highlights
    (colored backgrounds), whereas the highlights for other node types
    are colored boxes.

    The default is app dependent, usually the slot type of the corpus.
colorMap: dict, optional `None`
    Which nodes of a tuple (or list of tuples) will be highlighted.
    If `colorMap` is `None` or missing, all nodes will be highlighted with
    the default highlight color, which is yellow.

    But you can assign different colors to the members of the tuple:
    `colorMap` must be a dictionary that maps the positions in a tuple
    to a color.

    *   If a position is not mapped, it will not be highlighted.
    *   If it is mapped to the empty string, it gets the default highlight color.
    *   Otherwise, it should be mapped to a string that is a valid
        [CSS color](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value).

    !!! hint "color names"
        The link above points to a series of handy color names and their previews.

    !!! note "highlights takes precedence over colorMap"
        If both `highlights` and `colorMap` are given, `colorMap` is ignored.

        If you need to micro-manage, `highlights` is your thing.
        Whenever possible, use `colorMap`.
condensed: boolean, optional `False`
    indicates one of two modes of displaying the result list:

    *   `True`: instead of showing all results one by one,
        we show container nodes with all results in it highlighted.
        That way, we blur the distinction between the individual results,
        but it is easier to oversee where the results are.
        This is how SHEBANQ displays its query results.
        **See also the parameter `condenseType`**.
    *   `False`: make a separate display for each result tuple.
        This gives the best account of the exact result set.

    !!! caution "mixing up highlights"
        Condensing may mix-up the highlight coloring.
        If a node occurs in two results, at different positions
        in the tuple, the `colorMap` wants to assign it two colors!
        Yet one color will be chosen, and it is unpredictable which one.
condenseType: string, optional `None`
    The type of container to be used for condensing results.
    The default is app dependent, usually `verse` or `tablet`.
end: int, optional `None`
    `end` is the end point in the iterable of results.
    If `None`, displaying will stop after the end of the iterable.
extraFeatures: string | iterable, optional `()`
    A string or iterable of feature names.
    These features will be loaded automatically.
    In pretty displays these features will show up as `feature=value`,
    provided the value is not `None`, or something like None.

    !!! hint "Automatic loading"
        These features will load automatically, no explicit loading is
        necessary.

    !!! hint "values from other nodes"
        Suppose you want to display a value from a related node, e.g. a `gloss`
        that is available on `lex` nodes but not on `word` nodes, and you
        want to show it on the word nodes.
        Then you may specifiy `lex:gloss`, meaning that Text-Fabric will
        look up a `lex` node from the current node (by means of `L.u(w, otype='lex')`,
        and if it finds one, it will read the `gloss` feature from it.
full: boolean, optional `False`
    For pretty displays: indicates that the whole object should be
    displayed, even if it is big.

    !!! hint "Big objects"
        Big objects are objects of a type that is bigger than the default condense type.
fmt: string, optional `None`
    `fmt` is the text format that will be used for the representation.
    E.g. `text-orig-full`.

    !!! hint "Text formats"
        Use `T.formats` to inspect what text formats are available in your corpus.
highlights: dict | set, optional `{}`
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
    [CSS color](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value)
    qualifies.

    If you map a node to the empty string, it will get the default highlight color.

    !!! note "one big highlights dictionary"
        It is OK to first compose a big highlights dictionary
        for many tuples of nodes,
        and then run `prettyTuple()` for many different tuples
        with the same `highlights`.
        It does not harm performance if `highlights` maps
        lots of nodes outside the tuple as well.
noneValues: set, optional `None`
    A set of values for which no display should be generated.
    The default set is `None` and the strings `NA`, `none`, `unknown`.

    !!! hint "None is useful"
        Keep `None` in the set. If not, all custom features will be displayed
        for all kinds of nodes. So you will see clause types on words,
        and part of speech on clause atoms, al with value `None`.

    !!! hint "Suppress common values"
        You can use `noneValues` also to suppress the normal values of a feature,
        in order to attract attention to the more special values, e.g.

        ```python
        noneValues={None, 'NA', 'unknown', 'm', 'sg', 'p3'}
        ```

    !!! caution "None values affect all features"
        Beware of putting to much in `noneValues`.
        The contents of `noneValues` affect the display of
        all features, not only the custom features.
skipCols: set, optional `set()`
    indicates columns to skip in `show()`, `table()`, `prettyTuple()` and `plainTuple()`.
    Maybe a space-separated string of numbers, or an iterable of integers.
    Columns start at 1.
start: integer, optional `None`
    `start` is the starting point for displaying the iterable of results.
    (1 is the first one).
    If `None`, displaying starts at the first element of the iterable.
suppress: set, optional `set()`
    a set of names of features that should NOT be displayed.
    By default, quite a number of features is displayed for a node.
    If you find they clutter the display, you can turn them off
    selectively.
tupleFeatures: iterable of 2-tuples, optional `()`
    A bit like "extraFeatures" above, but more intricate.
    Only meant to steer the
    `A.export()` function below into outputting the
    features you choose.

    It should be a tuple of pairs
    `(i, features)`
    which means that to member `i` of a result tuple we assign extra `features`.

    `features` may be given as an iterable or a space separated string of feature names.
withPassage: boolean or set, optional `True`
    indicates whether a passage label should be put next to a displayed node
    or tuple of nodes.
    When passed with `table()`, or `plainTuple()`,
    the value may also be a set of integers, indicating the columns whose
    nodes will be linked with a web link
    (the first column is column 1).
