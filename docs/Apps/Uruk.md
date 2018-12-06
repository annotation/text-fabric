![logo](../images/apps/uruk/logo.png)

# Uruk

Name: `uruk`

[API](../Api/App.md)

[Tutorial]({{ninonb}}/uruk/blob/master/tutorial/start.ipynb).

Configuration [config.py]({{tfghb}}/{{c_uruk_config}})

Source code [app.py]({{tfghb}}/{{c_uruk_app}})

Display styles [display.css]({{tfghb}}/{{c_uruk_css}})

This app also contains interfaces to deal with
[ATF]({{oracc}}/editinginatf/primer/inlinetutorial/index.html)
transcriptions and [CDLI]({{cdli}}) photos and lineart.

See also
[about]({{ninogh}}/uruk/blob/master/docs/about.md),
[images]({{ninogh}}/uruk/blob/master/docs/images.md),
[transcription]({{ninogh}}/uruk/blob/master/docs/transcription.md).


## Linking

??? abstract "A.cdli()"
    ```python
    A.cdli(tablet, linkText=None, asString=False)
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

## Display

All display functions (`plain()`, `pretty()`, `table()`, `show()` etc
accept additional options:

??? info "lineart"
    `lineart` indicates whether to display a lineart image in addition
    (only relevant for signs and quads)

??? info "lineNumbers"
    `lineNumbers` indicates whether corresponding line numbers in the
    ATF source should be displayed.

## ATF representation

??? explanation "Generate ATF"
    Signs and quads and clusters can be represented by an ascii string,
    in the so-called Ascii Text Format,
    [ATF]({{oracc}}/editinginatf/primer/inlinetutorial/index.html).

    We provide a bunch of function that, given a node, generate the appropriate ATF
    representation.

??? abstract "A.atfFromSign()"
    ```python
    A.atfFromSign(node, flags=False)
    ```

    ???+ "Description"
        Reproduces the ATF representation of a sign.

    ??? info "node"
        `node` must have node type `sign`.

    ??? info "flags"
        `flags` whether the *flags* associated with the sign
        will be included in the ATF.

??? abstract "A.atfFromQuad()"
    ```python
    A.atfFromQuad(node, flags=False)
    ```

    ???+ "Description"
        Reproduces the ATF representation of a quad.

    ??? info "node"
        `node` must have node type `quad`.

    ??? info "flags"
        `flags` whether the *flags* associated with the quad
        will be included in the ATF.

??? abstract "A.atfFromOuterQuad()"
    ```python
    A.atfFromOuterQuad(node, flags=False)
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

??? abstract "A.atfFromCluster()"
    ```python
    A.atfFromCluster(node, flags=False)
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

??? abstract "A.getSource()"
    ```python
    A.getSource(node, nodeType=None, lineNumbers=False)
    ```

    ???+ "Description"
        Delivers the transcription source of nodes that correspond to the
        ATF source line level.

        This in contrast with the `A.atfFromXxx()` functions that
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
    Text-Fabric [Search](../Use/Search.md) is a generic and powerful mechanism for information retrieval.
    In most cases it is easier to extract nodes by search than by hand-written
    code using the functions here.

??? abstract "A.nodeFromCase()"
    ```python
    A.nodeFromCase((P-number, face:columnNumber, hLineNumber))
    ```

    ???+ info "Description"
        Gives you a node, if you specify a terminal case, i.e. a
        numbered transcription line.

    ??? explanation "Compare `T.nodeFromSection()`"
        This function is analogous to
        [`T.nodeFromSection()`](../Api/General.md#sections)
        of Text-Fabric.

    ??? info "case specification"
        This function takes a single argument which must be
        a tuple
        (*tabletNumber*, *face*:*columnNumber*, *hierarchical-line-number*).

    ??? note "dots"
        The hierarchical number may contain the original `.` that they
        often have in the transcriptions, but you may also leave them out.

    ??? caution "Not found"
        If no such node exists, you get `None` back.

??? abstract "A.caseFromNode()"
    ```python
    A.caseFromNode(node)
    ```

    ???+ info "Description"
        Gives you a terminal case specification,
        if you give a node of a case or something inside a case or line.

    ??? explanation "Compare `T.sectionFromNode()`"
        This function is analogous to
        [`T.sectionFromNode()`](../Api/General.md#sections)
        of Text-Fabric.

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

??? abstract "A.lineFromNode()"
    ```python
    A.lineFromNode(node)
    ```

    ???+ info "Description"
        If called on a node corresponding to something inside a transcription line, it
        will navigate to up to the terminal case or line in which it is contained, and
        return that node.

    ??? info "node"
        `node` must correspond to something inside a transcription line:
        `sign`, `quad`, `cluster`.

??? abstract "A.casesByLevel()"
    ```python
    A.casesByLevel(k, terminal=True)
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

??? abstract "A.getOuterQuads()"
    ```python
    A.getOuterQuads(node)
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

??? abstract "A.photo() and A.lineart()"
    ```python
    A.photo(nodes, key=None, asLink=True, withCaption='bottom', **options)
    A.lineart(nodes, key=None, asLink=True, withCaption='bottom', **options)
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
            [CSS]({{moz_length}}) length, such as
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

??? abstract "A.imagery()"
    ```python
    A.imagery(objectType, kind)
    ```

    ???+ "Description"
        Provides the sets of locally available images by object type.
        for tablets, it lists the P-numbers; for sign/quads: the ATF representations.

    ??? info "objectType"
        `objectType` is the type of thing: `ideograph` or `tablet`.

    ??? info "kind"
        `kind` is `photo` or `lineart`.
