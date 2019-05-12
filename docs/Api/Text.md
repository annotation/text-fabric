# Text

??? info "Overview"
    Here are the functions that enable you to get the actual text in the dataset.
    There are several things to accomplish here, such as

    *   support the structure of the corpus
    *   support a rigid section system usable by the TF browser
    *   handle multilingual section labels;
    *   switch between various text representations.

    The details of the Text API are dependent on the *warp* feature `otext`, which
    is a config feature.

???+ info "T"
    The Text API is exposed as `T` or `Text`.

??? note "otext is optional"
    If `otext` is missing, the Text API will not be build. If it exists, but
    does not specify structure or sections,
    those parts of the Text API will not be built.
    Likewise for text representations.

## Structure

??? explanation "Structure types"
    If a corpus has sectional elements, such as
    series, volume, book, part, document, chapter, fragment, verse, halfverse,
    line, etc, then you can configure those elements as structural types.

    If your TF dataset designer has done that, the `T.api` will provide a number
    of handy functions to navigate your corpus along its structure, programmatically.

    The
    [banks]({{tfbanks}}/programs/structure.ipynb)
    example corpus shows a full example.

    Structure is defined in the `otext` feature, by means of the keys
    `structureTypes` and `structureFeatures`.
    These are comma-separated lists of equal length.

    `structureTypes` specifies the node types
    that act as structural types, in the order from biggest to smallest.

    `structureFeatures` specifies a feature that corresponds to each
    structural type. This feature must contain the label of the structural
    element, e.g. the title of a book, the number of a verse, etc.

    The order of the section types is significant.
    Suppose you have a book with a single chapter. Is the chapter part of the book,
    or is the book part of the chapter?
    The order decides. If `book` is mentioned in `structureTypes` before `chapter`
    then the chapter is part of the book, and not the other way around.

    However, it is allowed to have nesting of elements of the same kind.

??? caution "Proper embedding not required" 
    There are no assumptions on how exactly the structural elements lie
    embedded in each other, and whether they consist of uninterrupted stretches
    of material or not.

    Suppose a we have a book with two disjoint chapters and there is a verse that
    has material in both chapters. Then that verse is part of neither chapter,
    but it is still part of the book.
    If you go down from that book to its substructural elements, you find not only
    its chapters, but also that verse. 

    So the great freedom with respect to structural elements also brings greater
    responsibility when using that structure.

??? abstract "T.structureInfo()"
    ```python
    T.structureInfo()
    ```

    Gives a summary of how structure has bee configured in the dataset.
    If there are headings that are the same for multiple structural nodes,
    you'll get a warning here, and you are told how you can get all of those.

    It also shows a short description of all structure-related methods
    of the `T` API.

??? abstract "T.structure()"
    ```python
    T.structure(node=None)
    ```

    Gives the structure of `node` and everything below it as a tuple.
    If `node` is None, it gives the complete structure of the whole dataset.

??? abstract "T.structurePretty()"
    ```python
    T.structure(node=None, fullHeading=False)
    ```

    Gives the structure of `node` and everything below it as a string
    with pretty indentation..
    If `node` is None, it gives the complete structure of the whole dataset.

    For each structural element, only its own heading is added.

    But if you want to see the full heading, consisting of the headings of a
    node and all of its parents, you can get that if you pass
    `fullHeading=True`.

??? abstract "T.top()"
    ```python
    T.top()
    ```

    Gives all top-level structural nodes in the dataset.
    These are the nodes that are not embedded in a structural node of the same
    or a higher level.

??? abstract "T.up()"
    ```python
    T.up(node)
    ```

    Gives the parent of `node`, provided `node` is structural.
    The parent is that structural node that has the heading you get from
    `node` minus the last element.

    E.g., the parent of `((book, Genesis), (chapter, 3), (verse, 16))` is the node
    that has heading `((book, Genesis), (chapter, 3))`.

??? abstract "T.down()"
    ```python
    T.down(node)
    ```

    Gives the children of `node`, provided `node` is structural.
    The children are those structural nodes that have headings that are one
    longer than the one you get from `node`.

    E.g., the children of `((book, Genesis), (chapter, 3))` are the nodes
    with heading `((book, Genesis), (chapter, 3), (verse, 1))`, etc.

??? abstract "T.headingFromNode()"
    ```python
    T.headingFromNode(node)
    ```

    Gives the full heading of `node`, provided `node` is structural.

    The heading is defined of the tuple of pairs (node type, feature value)
    for all ancestors of that node. 

    E.g., the heading of the verse node corresponding to Genesis 3:16
    is `((book, Genesis), (chapter, 3), (verse, 16))`.

    If you are interested in the complete mapping: it is stored in 
    the dictionary `T.hdFromNd`.

??? abstract "T.nodeFromHeading()"
    ```python
    T.nodeFromHeading(heading)
    ```

    Gives the full node corresponding to a heading, provided it exists.
    It is the inverse of `T.headingFromNode()`.

    If you are interested in the complete mapping: it is stored in 
    the dictionary `T.ndFromHd`.

    If there is more than one node that corresponds to the heading, only the last
    one in the corpus will be returned.

    `T.hdMult` contains all such cases.


## Sections

??? explanation "Section levels"
    In `otext` the main section levels (usually `book`, `chapter`, `verse`) can be
    defined. It loads the features it needs (so you do not have to specify those
    features, unless you want to use them via `F`). And finally, it makes some
    functions available by which you can make handy use of that information.

    ??? note "Section levels from a limited, rigid system"
        There are up to three section levels, and this is a hard coded boundary.
        That makes this section system unsuitable to faithfully reflect the
        rich sectioning that may be present in a corpus.

        On the other hand, applications (such as TF apps) can access a predictable
        sectioning system by which they can chunk the material in practical portions.

        The rule of thumb is:
        
        Level 1 divides the corpus into top level units,
        of which there might be (very) many. The TF browser has a control that
        can deal with long lists.

        Level 2 divides a level 1 section into a chunk that can be loaded into 
        a webpage, without overwhelming the browser.
        Even better, it should be just one or a few screenfuls of text, when
        represented in `plain` view.

        Level 3 divides a level 2 section into chunks that roughly corresponds to lines.
        Such lines typically take up one screenful if represented in `pretty` view.

    ??? note "Section levels are generic"
        In this documentation, we call the main section level `book`, the second level
        `chapter`, and the third level `verse`. Text-Fabric, however, is completely
        agnostic about how these levels are called. It is prepared to distinguish three
        section levels, but how they are called, must be configured in the dataset. The
        task of the `otext` feature is to declare which node type and feature correspond
        with which section level. Text-Fabric assumes that the first section level may
        have multilingual headings, but that section levels two and three have single
        language headings (numbers of some kind).

    ??? note "String versus number"
        Chapter and verse numbers will be considered to be strings or
        integers, depending on whether your dataset has declared the corresponding
        feature *valueType* as `str` or as `int`.

        Conceivably, other works might have chapter and verse numbers
        like `XIV`, '3A', '4.5', and in those cases these numbers are obviously not
        `int`s.

    ??? caution "levels of node types"
        Usually, Text-Fabric computes the hierarchy of node types correctly, in the
        sense that node types that act as containers have a lower level than node types
        that act as containees. So books have the lowest level, words the highest. See
        [levels](#levels). However, if this level assignment turns out to be wrong for
        your dataset, you can configure the right order in the *otext* feature, by means
        of a key `levels` with value a comma separated list of levels. Example:

        ```
        @levels=tablet,face,column,line,case,cluster,quad,comment,sign
        ```

??? abstract "T.sectionTuple()"
    ```python
    T.sectionTuple(node, lastSlot=False, fillup=False)
    ```

    ???+ info "Description"
        Returns a tuple of nodes that correspond to the sections of level 0, 1 and 2
        (e.g. book, chapter, verse).
        that include a node. More precisely, we retrieve the sections that contain a
        reference node, which is either the first slot or the last slot of the node
        in question.
        
    ??? info "node"
        The node whose containing section we want to get.

    ??? info "lastSlot"
        Whether the reference node will be the last slot contained by the `node` argument
        or the first node.

    ??? info "fillup"
        If `False`, and node is a level 0 section node, a 1-element tuple of this
        node is returned. And if node is a level 1 section node, a 2-element tuple is returned:
        the enclosing level 0 section node and node itself.

        If `True`, always a complete 3-tuple of a level 0, 1, and 2 section node is returned.

??? abstract "T.sectionFromNode()"
    ```python
    T.sectionFromNode(node, lastSlot=False, lang='en', fillup=False)
    ```

    ???+ info "Description"
        Returns the book/chapter/verse indications that correspond to the reference
        node, which is the first or last slot belonging `node`, dependent on `lastSlot`.
        The result is a tuple, consisting of the book name (in language `lang`), the
        chapter number, and the verse number. But see the `fillup` parameter.

    ??? info "node"
        The node from which we obtain a section specification.

    ??? info "lastSlot"
        Whether the reference node will be the last slot contained by the `node` argument
        or the first node.

    ??? info "lang"
        The language to be used for the section parts, as far as they are language dependent.

    ??? info "fillup"
        Same as for `sectionTuple()`

    ??? note "crossing verse boundaries"
        Sometimes a sentence or clause in a verse continue into the next verse.
        In those cases, this function will return a different results for
        `lastSlot=False` and `lastSlot=True`.

    ??? caution "nodes outside sections"
        Nodes that lie outside any book, chapter, verse will get a `None` in the
        corresponding members of the returned tuple.

??? abstract "T.nodeFromSection()"
    ```python
    T.nodeFromSection(section, lang='en')
    ```

    ???+ info "Description"
        Given a `section` tuple, return the node of it.
        
    ??? info "section"
        `section` consists of a book name (in language `lang`),
        and a chapter number and a verse
        number (both as strings or number depending on the value type of the
        corresponding feature). The verse number may be left out, the result is then a
        chapter node. Both verse and chapter numbers may be left out, the result is then
        a book node. If all three are present, de result is a verse node.

    ??? info "lang"
        The language assumed for the section parts, as far as they are language dependent.

## Book names and languages

??? explanation "Book names and nodes"
    The names of the books may be available in multiple languages. The book names
    are stored in node features with names of the form `book@`*la*, where *la* is
    the [ISO 639]({{wikip}}/ISO_639) two-letter code for that
    language. Text-Fabric will always load these features.

??? abstract "T.languages"
    ```python
    T.languages
    ```

    ???+ info "Description"
        A dictionary of the languages that are available for book names.

??? abstract "T.bookName()"
    ```python
    T.bookName(node, lang='en')
    ```

    ???+ info "Description"
        gives the name of the book in which a node occurs.

    ??? info "node"
        The node in question.

    ??? info "lang"
        The `lang` parameter is a two letter language code. The default is `en`
        (English).

        If there is no feature data for the language chosen, the value of the ordinary
        `book` feature of the dataset will be returned.

    ??? note "Works for all nodes"
        `n` may or may not be a book node. If not, `bookName()` retrieves the
        embedding book node first.

??? abstract "T.bookNode()"
    ```python
    T.bookNode(name, lang='en')
    ```

    ???+ info "Description"
        gives the node of the book identified by its name
        
    ??? info "name"
        The name of the book.
        
    ??? info "lang"
        The language in which the book name is supplied by the `name` parameter.

        If `lang` can not be found, the value of the ordinary `book` feature of the
        dataset will be used.

        If `name` cannot be found in the specified language, `None` will be returned.

    ??? caution "Function name follows configured section level"
        If your dataset has configured section level one under an other name,
        say `tablet`, then these two methods follow that name. Instead of `T.bookName()`
        and `T.bookNode()` we have then `T.tabletName()` and `T.tabletNode()`.

## Text representation

??? explanation "Text formats"
    Text can be represented in multiple ways. We provide a number of formats with
    structured names.

    ??? "format names"
        A format name is a string of keywords separated by `-`:

        *what*`-`*how*`-`*fullness*`-`*modifier*

        For Hebrew any combination of the follwoing could be useful formats:

        keyword | value | meaning
        ------- | ----- | -------
        *what* | `text` | words as they belong to the text
        *what* | `lex` | lexemes of the words
        *how* | `orig` | in the original script (Hebrew, Greek, Syriac) (all Unicode)
        *how* | `trans` | in (latin) transliteration
        *how* | `phono` | in phonetic/phonological transcription
        *fullness* | `full` | complete with accents and all diacritical marks
        *fullness* | `plain` | with accents and diacritical marks stripped, in Hebrew only the consonants are left
        *modifier* | `ketiv` | (Hebrew): where there is ketiv/qere, follow ketiv instead of qere (default);

        The default format is `text-orig-full`, we assume that every TF dataset defines
        this format.

    ??? "format content"
        A format is a template string, with fixed text and variable text.
        The variable text comes from features.
        You specify the interpolation of features by surrounding the feature name
        by `{ }`.
        
        For example, if `letters` and `after` are features, this is a text format:

        ```
        {letters}{after}
        ```

        If you need tabs and newlines in a format, specify them by \\t and \\n.

        You can also conditionally choose between features, to
        substitute the value of another feature in case of empty values.

        For example, if you want to use the `normal` feature to represent a word,
        but if there is also a rare feature `special` that you want to use if it
        is defined for that word, you can make a format

        ```
        {special/normal}
        ```

        This tries the feature `special` first, and if that is empty, it takes
        `normal`.

        You can also add a fixed default. If you want to display a `.` if
        neither `special` nor `normal` exist, you can say

        ```
        {special/normal:.}
        ```

    ???+ "formats specialized to a node type"
        TF datasets may also define formats of the form
        
        *nodetype*`-default`
        
        where *nodetype* is a valid type of node in the dataset.

        These formats will be invoked in cases where no explicit format is specified as
        a fall back for some kind of nodes. See `T.text()` below.

    ???+ "target node types for formats"
        A node type may also be prepended to a format, with `#` as separator:

        *nodetype*`#`*textformat*

        In general, a format can be applied to any kind of node, and it will 
        lookup the features defined in its template for that node.
        But some features have meaningful values for particular node types only.
         
        So formats may indicate that they should be applied to nodes of a specific type.
        See `T.text()` below.

    Remember that the formats are defined in the `otext` warp config feature of your
    set, not by Text-Fabric.
    
    ??? note "Freedom of names for formats"
        There is complete freedom of choosing names for text formats.
        They do not have to complied with the above-mentioned scheme.

    ???+ "layout in formats"
        So far, text formats only result in plain text.
        A [TF-app](../Implementation/Apps.md) may define and implement extra text
        formats which may invoke all HTML+CSS styling that you can think of.

??? abstract "T.formats"
    ```python
    T.formats
    ```

    ???+ info "Description"
        Show the text representation formats that have been defined in your dataset.

??? abstract "T.text()"
    ```python
    T.text(nodes, fmt=None)
    T.text(node, fmt=None, descend=None)
    T.text(node, fmt=None, descend=None, explain=False)
    ```

    ???+ info "Description"
        Gives the text that corresponds to a bunch of nodes.
        The
        [banks]({{tfbanks}}/programs/formats.ipynb)
        example corpus shows examples.


    ??? info "nodes"
        `nodes` can be a single node or an arbitrary iterable of nodes
        of arbitrary types.
        No attempt will be made to sort the nodes.
        If you need order, it is
        better to order the nodes before you feed them to `T.text()`.

    ??? info "fmt"
        The format of the text representation is given with `fmt`.

        If it is not specified or None, each node will be formatted with
        a node type specific format, defined as *nodeType*`-default`, if it
        exists.

        If there is no node specific format, the default format
        `text-orig-full` will be used.

        If `text-orig-full` is not defined, an error message will be issued,
        and the nodes will be represented by their types and numbers.

        If a value for *fmt* is passed, but it is not a format defined in the
        *otext.tf* feature, there will be an error message and `None` is returned.

    ??? info "descend"
        Whether to descend to constituent nodes.

        If True, nodes will be replaced by a sequence of their consituent nodes,
        which have a type specified by the format chosen, or, if the format does
        not specify such a type, the node will be replaced by the slots contained in it.

        If False, nodes will not be replaced.

        If *descend* is not specified or None,
        a node will be replaced by its constituent nodes,
        unless its type is associated with the given format or,
        if no format is given, by the default format of its type, or,
        if there is no such format, by its slots.

        ??? caution "no nodes to descend to"
            If you call `T.text(n, fmt=myfmt)`
            and `myfmt` is targeted to a node type that is
            bigger than the node type of `n`,
            then the so-called descending leads to an empty
            sequence of nodes and hence to an empty string.

    ??? info "explain"
        The logic of this function is subtle.
        If you call it and the results baffles you, pass `explain=True`
        and it will explain what it is doing.

    ??? hint "The default is sensible"
        Consider the simplest call to this function: `T.text(node)`.
        This will apply the default format to `node`.
        If `node` is non-slot, then in most cases
        the default format will be applied to the slots contained in `node`.

        But for special node types, where the best representation
        is not obtained by descending down
        to the contained slot nodes, the dataset may define
        special default types that use other
        features to furnish a decent representation.

        ??? example "lexemes"
            In some corpora case this happens for the type of lexemes: `lex`.
            Lexemes contain their occurrences
            as slots, but the representation of a lexeme
            is not the string of its occurrences, but
            resides in a feature such as `voc_lex_utf8` (vocalized lexeme in Unicode).

            If the dataset defines the format `lex-default={lex} `,
            this is the only thing needed to regulate the representation of a lexeme.

            Hence, `T.text(lx)` results in the lexeme representation of `lx`.

            But if you really want to print out all occurrences of lexeme `lx`,
            you can say `T.text(lx, descend=True)`.

        ??? example "words and signs"
            In some corpora the characters or signs are the slot level, and there is
            a non slot level of words. 
            Some text formats are best defined on signs, others best on words.

            For example, if words are associated with lexemes, stored in a word
            feature `lex`, we can define a text format


            ```lex-orig-full=word#{lex} ```

            When you call `T.text(n)` for a non-slot, non-word node,
            normally the node will be replaced by the slot nodes it contains,
            before applying the template in the format.
            But if you pass a format that specifies a different node type,
            nodes will be replaced by contained nodes of that type. So 

            ```T.text(n, fmt='lex-orig-full')```

            will lookup all word nodes under n and apply the template `{lex} ` to them.
            
    ???+ caution "same and different behaviours"
        The consequences of the rules might be unexpected in some cases.
        Here are a few observations:

        * formats like `phrase-default` can be implicitly invoked for phrase nodes,
          but `descend=True` prevents that;
        * when a format targeted at phrases is invoked for phrase nodes,
          `descend=True` will not cause the expansion of those nodes to slot nodes, because
          the phrase node is already expanded to the target type of the format;


    ???+ hint "memory aid"
        *   If *fmt* is explicitly passed, it will be the format used no matter what,
            and it determines the level of the nodes to descend to;
        *   Descending is the norm, it can only be prevented by setting default formats
            for node types or by passing `descend=False` to `T.text()`;
        *   `descend=True` is stronger than type-specific default formats, but weaker than 
            explicitly passed formats;
        *   **Pass `explain=True` for a dynamic explanation.**

    ??? note "Non slot nodes allowed"
        In most cases, the nodes fed to `T.text()` are slots, and the formats are
        templates that use features that are defined for slots.

        But nothing prevents you to define a format
        for non-slot nodes, and use features
        defined for a non-slot node type.

        If, for example, your slot type is *glyph*,
        and you want a format that renders
        lexemes, which are not defined for glyphs but for words,
        you can just define a format in terms of word features.

        It is your responsibility to take care to use the formats
        for node types for which they make sense.

    ??? caution "Escape whitespace in formats"
        When defining formats in `otext.tf`,
        if you need a newline or tab in the format,
        specify it as `\n` and `\t`.

