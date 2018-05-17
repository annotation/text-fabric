# Cunei

## About

The module
[cunei.py](https://github.com/Dans-labs/text-fabric/blob/master/tf/extra/cunei.py)
contains a number of handy functions to deal with TF nodes for cuneiform tablets
and
[ATF](http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/inlinetutorial/index.html)
transcriptions of them and [CDLI](https://cdli.ucla.edu) photos and lineart.

See also
[about](https://github.com/Nino-cunei/uruk/blob/master/docs/about.md),
[images](https://github.com/Nino-cunei/uruk/blob/master/docs/images.md),
[transcription](https://github.com/Nino-cunei/uruk/blob/master/docs/transcription.md).

## Set up

??? abstract "from tf.extra.cunei import Cunei"
    ??? explanation "import Cunei"
        The `Cunei` API is distributed with Text-Fabric.
        You have to import it into your program.

## Initialisation

??? abstract "Cunei()"
    ```python
        CN = Cunei('~/github', 'Nino-cunei/uruk', 'notebook')
        CN.api.makeAvailableIn(globals())
    ```

    ???+ info "Description"
        Text-Fabric will be started for you and load all features.
        When `Cunei` is
        initializing, it scans the image directory of the repo and reports how many
        photos and lineart images it sees.

    ??? info "local GitHub"
        The argument `~/github`
        should point to the directory where your local
        github repositories reside.

    ??? info "Uruk location"
        The argument `Nino-cunei/uruk`
        should point to the local GitHub repository
        where the Uruk corpus resides.

    ??? info "notebook"
        The third argument of `Cunei()` should be the name
        of your current notebook (without the `.ipynb` extension).
        The Cunei API will use this to generate a link to your notebook
        on GitHub and NBViewer.

        ??? note
            Your current notebook can be anywhere on your system.
            `Cunei()` can find its
            location, but not its name, hence you have to pass its name.

## Linking

??? abstract "CN.cdli()"
    ```python
    CN.cdli(tablet, linkText=None, asString=False)
    ```

    ???+ "Description"
        Produces a link to a tablet page on CDLI,
        to be placed in an output cell.

    ??? info "tablet"
        `tablet` is either a node of type `tablet`
        or a P-number of a tablet.

    ??? info "linkText"
        You may provide the text to be displayed as the link.
        If you do not provide any,
        the P-number of the tablet will be used.

    ??? info "asString" 
        Instead of displaying the result directly in the output of your
        code cell in a notebook, you can also deliver the HTML as string,
        just say `asString=True`.

??? abstract "CN.tabletLink()"
    ```python
    CN.tabletLink(node, text=None, asString=False)
    ```

    ???+ "Description"
        Produces a link to CDLI

    ??? info "node"
        `node` can be an arbitrary node. The link targets the tablet that
        contains the material contained by the node.
    
    ??? info "text"
        You may provide the text to be displayed as the link.
        If you do not provide a link text,
        the P-number of the tablet will be chosen.

    ??? info "asString" 
        Instead of displaying the result directly in the output of your
        code cell in a notebook, you can also deliver the HTML as string,
        just say `asString=True`.

    ??? example "Sign 10000 on CDLI"
        ```python
        CN.tabletLink(100000)
        ```

## Plain display

??? explanation "Straightforward display of things"
    There are functions to display nodes, tuples of nodes, and iterables of tuples
    of nodes in a simple way, as rows and as a table.

??? abstract "CN.plain()"
    ```python
    CN.plain(node, linked=True, withNodes=False, lineart=True, lineNumbers=False, asString=False)
    ```

    ???+ info "Description"
        Displays the material that corresponds to a node in a simple way.

    ??? info "node"
        `node` is a node of arbitrary type.

    ??? info "linked"
        `linked` indicates whether the result should be a link to CDLI
        to the tablet on which the node occurs.

    ??? info "withNodes"
        `withNodes` indicates whether node numbers should be displayed.

    ??? info "lineart"
        `lineart` indicates whether to display a lineart image in addition
        (only relevant for signs and quads)

    ??? info "lineNumbers"
        `lineNumbers` indicates whether corresponding line numbers in the
        ATF source should be displayed.

    ??? info "asString" 
        Instead of displaying the result directly in the output of your
        code cell in a notebook, you can also deliver the markdown as string,
        just say `asString=True`.

??? abstract "CN.plainTuple()"
    ```python
    CN.plainTuple(
      nodes, seqNumber,
      linked=1,
      withNodes=False, lineart=True, lineNumbers=False,
      asString=False,
    )
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
        the CDLI page of the containing tablet;
        (the first data column is column 1)

    ??? info "withNodes, lineart, lineNumbers, asString"
        Same as in `CN.plain()`.

??? abstract "CN.table()"
    ```python
    CN.table(
      results,
      start=1, end=len(results),
      linked=1,
      withNodes=False,
      lineart=True,
      lineNumbers=False,
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

    ??? info "linked, withNodes, lineart, lineNumbers, asString"
        Same as in `CN.plainTuple()`.

## Pretty display

??? explanation "Graphical display of things"
    There are functions to display nodes, tuples of nodes, and iterables of tuples
    of nodes in a graphical way.

??? abstract "CN.pretty()"
    ```python
    CN.pretty(node, withNodes=False, suppress=set(), highlights={})
    ```

    ???+ info "Description"
        Displays the material that corresponds to a node in a graphical way.

    ??? info "node"
        `node` is a node of arbitrary type.

    ??? info "withNodes"
        `withNodes` indicates whether node numbers should be displayed.

    ??? info "lineart, lineNumbers"
        Same as in `CN.plain()`.

    ??? info "suppress"
        `suppress=set()` is a set of feature names that should NOT be displayed.
        By default, quite a number of features is displayed for a node.
        If you find they clutter the display, you can turn them off
        selectively.

    ??? explanation "Highlighting"
        When nodes such as tablets and cases are displayed by `pretty()`,
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

??? abstract "CN.prettyTuple()"
    ```python
    CN.prettyTuple(
      nodes, seqNumber,
      withNodes=False,
      lineart=True,
      lineNumbers=False,
      suppress=set(),
      colorMap=None,
      highlights=None,
    )
    ```

    ???+ info "Description"
        Displays the material that corresponds to a tuple of nodes in a graphical way,
        with customizable highlighting of nodes.

    ??? explanation "By tablet"
        We examine all nodes in the tuple.
        We collect and show all tablets in which they
        occur and highlight the material corresponding to the all nodes in the tuple.
        The highlighting can be tweaked by the optional `colorMap` parameter.

    ??? info "nodes, seqNumber, withNodes, lineart, lineNumbers"
        Same as in `CN.plainTuple()`.

    ??? info "suppress"
        Same as in `CN.pretty()`.

    ??? info "colorMap"
        The nodes of the tuple will be highlighted.
        If `colorMap` is `None` or missing, all nodes will be highlighted with
        the default highlight color, which is yellow.

        But you can assign different colors to the members of the tuple:
        `colorMap` must be a dictionary that maps the positions in a tuple 
        to a color:
        *   If a position is not mapped, it will not be highlighted.
        *   If it is mapped to the empty string, it gets the default highlight color.
        *   Otherwise, it should be mapped to a string that is a valid
            [CSS color](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value).

        ??? hint "color names"
            The link above points to a series of handy color names and their previews.

    ??? info "highlights"
        Same as in `B.pretty()`.

    ???+ note "highlights takes precedence over colorMap"
        If both `highlights` and `colorMap` are given, `colorMap` is ignored.
        
        If you need to micro-manage, `highlights` is your thing.
        Whenever possible, use `colorMap`.  

    ??? note "one big highlights dictionary"
        It is OK to first compose a big highlights dictionary for many tuples of nodes,
        and then run `prettyTuple()` for many different tuples with the same `highlights`.
        It does not harm performance if `highlights` maps lots of nodes outside the tuple as well.

??? abstract "CN.show()"
    ```python
    CN.show(
      results,
      condensed=True,
      start=1, end=len(results),
      withNodes=False,
      lineart=True,
      lineNumbers=False,
      suppress=set(),
      colorMap=None,
      highlights=None,
    )
    ```

    ???+ info "Description"
        Displays an iterable of tuples of nodes.
        The elements of the list are displayed by `CN.prettyTuple()`.

    ??? info "results"
        `results` an iterable of tuples of nodes.
        The results of a search qualify, but it works
        no matter which process has produced the tuples.

    ??? info "condensed"
        `condensed` indicates one of two modes of displaying the result list:

        * `True`: instead of showing all results one by one,
          we show all tablets with all results in it highlighted.
          That way, we blur the distinction between the individual results,
          but it is easier to oversee where the results are.
        * `False: make a separate display for each result tuple.
          This gives the best account of the exact result set.

    ??? info "start"
        `start` is the starting point in the results iterable (1 is the first one).
        Default 1.

    ??? info "end"
        `end` is the end point in the results iterable.
        Default the length of the iterable.

    ??? info "withNodes, lineart, lineNumbers, suppress, colorMap, highlights"
        Same as in `B.prettyTuple()`.

## Search

??? abstract "CN.search()" 
    ```python
    CN.search(query, silent=False)
    ```
    
    ???+ "Description"
        Searches in the same way as the generic Text-Fabric `S.search()`.
        But whereas the `S` version returns a generator which yields the results
        one by one, the `CN` version collects all results and sorts them.
        It then reports the number of results.

    ??? info "query"
        `query` is the search template that has to be searched for.

    ??? info "silent"
        `silent`: if `True` it will suppress the reporting of the number of results.

    ??? hint "search template reference"
        See the [search template reference](/Api/General#search-templates)

## ATF representation

??? explanation "Generate ATF"
    Signs and quads and clusters can be represented by an ascii string,
    in the so-called Ascii Text Format,
    [ATF](http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/inlinetutorial/index.html).

    We provide a bunch of function that, given a node, generate the appropriate ATF
    representation.

??? abstract "CN.atfFromSign()"
    ```python
    CN.atfFromSign(node, flags=False)
    ```

    ???+ "Description"
        Reproduces the ATF representation of a sign.

    ??? info "node"
        `node` must have node type `sign`.

    ??? info "flags"
        `flags` whether the *flags* associated with the sign
        will be included in the ATF.

??? abstract "CN.atfFromQuad()"
    ```python
    CN.atfFromQuad(node, flags=False)
    ```

    ???+ "Description"
        Reproduces the ATF representation of a quad.

    ??? info "node"
        `node` must have node type `quad`.

    ??? info "flags"
        `flags` whether the *flags* associated with the quad
        will be included in the ATF.

??? abstract "CN.atfFromOuterQuad()"
    ```python
    CN.atfFromOuterQuad(node, flags=False)
    ```

    ???+ "Description"
        Reproduces the ATF representation of a quad or sign.

    ??? info "node"
        `node` must have node type `quad` or `sign`.

    ??? info "flags"
        `flags` whether the *flags* associated with the quad
        will be included in the ATF.

    ??? explanation "outer quads"
        If you take an ATF transcription line with linguistic material on it, and you
        split it on white space, and you forget the brackets that cluster quads and
        signs, then you get a sequence of outer quads and signs.

        If you need to get the ATF representation for these items, this function does
        conveniently produce them. You do not have to worry yourself about the sign/quad
        distinction here.

??? abstract "CN.atfFromCluster()"
    ```python
    CN.atfFromCluster(node, flags=False)
    ```

    ???+ "Description"
        Reproduces the ATF representation of a cluster.

    ??? info "node"
        `node` must have node type `quad`.

    ??? explanation "clusters"
        Clusters are bracketings of
        quads that indicate proper names, uncertainty, or supplied material. In ATF they
        look like `( )a` or `[ ]` or `< >`

    ??? note "Sub-clusters"
        Sub-clusters will also be
        represented. Signs belonging to multiple nested clusters will only be
        represented once.

??? abstract "CN.getSource()"
    ```python
    CN.getSource(node, nodeType=None, lineNumbers=False)
    ```

    ???+ "Description"
        Delivers the transcription source of nodes that correspond to the
        ATF source line level.

        This in contrast with the `CN.atfFromXxx()` functions that
        work for nodes that correspond to parts of the ATF source lines.

    ??? info "node"
        `node` must have a type in `tablet`, `face`, `column`,
        `comment`, `line`, `case`.

    ??? info "nodeType"
        If `nodeType` is passed, only source lines of this type are returned.

    ??? info "lineNumbers"
        `lineNumbers`: if `True`, add line numbers to the result,
        these numbers say where the source line occurs in the source file.

    ??? explanation "TF from ATF conversion"
        The conversion of ATF to Text-Fabric has saved the original source lines and
        their line numbers in the features `srcLn` and `srcLnNum` respectively. This
        function makes use of those features.

## Sections

??? explanation "Sections in tablets"
    Text-Fabric supports 3 section levels in general.
    The Uruk corpus uses them for *tablets*, *columns* and *lines*.

    But lines may be divided in cases and subcases, which are also numbered.
    We need to mimick some functions of the Text-Fabric `T` Api for sections,
    so that we can retrieve cases more easily.

??? caution "Consider search"
    Text-Fabric Search is a generic and powerful mechanism for information retrieval.
    In most cases it is easier to extract nodes by search than by hand-written
    code using the functions here.

??? abstract "CN.nodeFromCase()"
    ```python
    CN.nodeFromCase((P-number, face:columnNumber, hLineNumber))
    ```

    ???+ info "Description"
        Gives you a node, if you specify a terminal case, i.e. a
        numbered transcription line.

    ??? explanation "Compare `T.nodeFromSection()`"
        This function is analogous to
        `T.nodeFromSection()` of Text-Fabric.

    ??? info "case specification"
        This function takes a single argument which must be
        a tuple
        (*tabletNumber*, *face*:*columnNumber*, *hierarchical-line-number*).

    ??? note "dots"
        The hierarchical number may contain the original `.` that they
        often have in the transcriptions, but you may also leave them out.

    ??? caution "Not found"
        If no such node exists, you get `None` back.

??? abstract "CN.caseFromNode()"
    ```python
    CN.caseFromNode(node)
    ```

    ???+ info "Description"
        Gives you a terminal case specification,
        if you give a node of a case or something inside a case or line.

    ??? explanation "Compare `T.sectionFromNode()`"
        This function is analogous to
        `T.sectionFromNode()` of Text-Fabric.

    ??? explanation "case specification"
        A case specification is a tuple
        (*tabletNumber*, *face*:*columnNumber*, *hierarchical-line-number*).
        The hierarchical line number will not contain dots.

    ??? info "node"
        `node` must be of a terminal case
        (these are the cases that have a full hierarchical
        number; these cases correspond to the individual numbered lines in the
        transcription sources).

    ??? hint "other nodes"
        If `node` corresponds to something inside a transcription line,
        the node of the terminal case or line in which it is contained will be used.

??? abstract "CN.lineFromNode()"
    ```python
    CN.lineFromNode(node)
    ```

    ???+ info "Description"
        If called on a node corresponding to something inside a transcription line, it
        will navigate to up to the terminal case or line in which it is contained, and
        return that node.

    ??? info "node"
        `node` must correspond to something inside a transcription line:
        `sign`, `quad`, `cluster`.

??? abstract "CN.casesByLevel()"
    ```python
    CN.casesByLevel(k, terminal=True)
    ```

    ???+ info "Description"
        Grabs all (sub)cases of a specified level. You can choose to filter the result
        to those (sub)cases that are *terminal*, i.e. those which do not contain
        subcases anymore. Such cases correspond to individual lines in the ATF.

    ??? info "k"
        `k` is an integer, indicating the level of (sub)cases you want.
        `0` is lines,
        `1` is top-level cases,
        `2` is subcases,
        `3` is subsubcases, and so on.

    ??? info "terminal"
        `terminal`: if `True`, only lines and cases that have the feature `terminal`
        are delivered.
        Otherwise, all lines/cases of that level will be delivered.

??? abstract "CN.getOuterQuads()"
    ```python
    CN.getOuterQuads(node)
    ```

    ???+ "Description"
        Collects the outer quads and isolated signs under a node.
    
    ??? info "node"
        `node` is typically a tablet, face, column, line, or case.
        This is the container of the outer quads.

    ??? explanation "Outer quads"
        Outer quads and isolated signs is what you get
        if you split line material by white space and
        remove cluster brackets.

## Images

??? abstract "CN.photo() and CN.lineart()"
    ```python
    CN.photo(nodes, key=None, asLink=True, withCaption='bottom', **options)
    CN.lineart(nodes, key=None, asLink=True, withCaption='bottom', **options)
    ```

    ???+ info "Description"
        Fetches photos or linearts for tablets, signs or quads, and returns it in a way
        that it can be embedded in an output cell. The images that show up are clickable
        and link through to an online, higher resolution version on CDLI. Images will
        have, by default, a caption that links to the relevant page on CDLI.

    ??? explanation "Placement"
        The result will be returned as a *row* of images.
        Subsequent calls to `photo()` and `lineart()`
        will result in vertically stacked rows.

    ??? info "nodes"
        `nodes` is one or more **nodes**.
        As far as they are of type `tablet`, `quad` or `sign`,
        a photo or lineart will be looked up for them.

        ??? hint "by name"
            Instead of a node you may also
            supply the P-number of a tablet or the name of the sign or quad.

    ??? info "key"
        `key` is an optional string specifying which of the available images for
        this node you want to use.

        ??? hint "look up"
            if you want to know which keys are available for a
            node, supply `key='xxx'`, or any non-existing key.

    ??? info "asLink"
        `asLink=True`: no image will be placed, only a link to the online
        image at CDLI.
        In this case the **caption** will be suppressed, unless
        explicitly given.

    ??? info "withCaption"
        `withCaption='bottom'` controls whether a CDLI link to the
        tablet page must be put under the image.
        You can also specify `top`, `left`, `right`.
        If left out, no caption will be placed.

    ??? info "options"
        `options` is a series of key=value arguments that
        control the placement of the images,
        such as `width=100`, `height=200`.

        ??? explanation "CSS"
            The optional parameters `height` and `width` control the height and width of the
            images. The value should be a valid
            [CSS](https://developer.mozilla.org/en-US/docs/Web/CSS/length) length, such as
            `100px`, `10em`, `32vw`. If you pass an integer, or a decimal string without
            unit, your value will be converted to that many `px`.

            These parameters are interpreted as setting a maximum value (in fact they will
            end up as `max-width` and `max-height` on the final `<img/>` element in the
            HTML.

            So if you specify both `width` and `height`, the image will be placed in tightly
            in a box of those dimensions without changing the aspect ratio.

            If you want to force that the width of height you pass is completely consumed,
            you can prefix your value with a `!`. In that case the aspect ratio maybe
            changed. You can use the `!` also for both `height` and `width`. In that case,
            the rectangle will be completely filled, and the aspect ratio will be adjusted
            to that of the rectangle.

            The way the effect of the `!` is achieved, is by adding `min-width` and
            `min-height` properties to the `<img/>` element.

    ??? hint "local images"
        The images will be called in by a little piece of generated HTML, using the
        `<img/>` tag. This only works if the image is within reach. To the images will
        be copied to a sister directory of the notebook. The name of this directory is
        `cdli-imagery`. It will be created on-the-fly when needed. Copying will only be
        done if needed. The names of the images will be changed, to prevent problems
        with systems that cannot handle `|` and `+` characters in file names well.

??? abstract "CN.imagery()"
    ```python
    CN.imagery(objectType, kind)
    ```

    ???+ "Description"
        Provides the sets of locally available images by object type.
        for tablets, it lists the P-numbers; for sign/quads: the ATF representations.

    ??? info "objectType"
        `objectType` is the type of thing: `ideograph` or `tablet`.

    ??? info "kind"
        `kind` is `photo` or `lineart`.
