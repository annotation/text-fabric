# Text

??? info "Overview"
    Here are the functions that enable you to get the actual text in the dataset.
    There are several things to accomplish here, such as

    *   getting text given book, chapter, and verse;
    *   given a node, produce the book, chapter and verse indicators in which the node
        is contained;
    *   handle multilingual book names;
    *   switch between various text representations.

    The details of the Text API are dependent on the *warp* feature `otext`, which
    is a config feature.

???+ info "T"
    The Text API is exposed as `T` or `Text`.

## Sections

??? explanation "Section levels"
    In `otext` the main section levels (usually `book`, `chapter`, `verse`) can be
    defined. It loads the features it needs (so you do not have to specify those
    features, unless you want to use them via `F`). And finally, it makes some
    functions available by which you can make handy use of that information.

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

    ??? note "otext is optional"
        If `otext` is missing, the Text API will not be build. If it exists, but
        does not specify sections, that part of the Text API will not be built. Likewise
        for text representations.

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

    TF datasets may also define formats of the form *nodetype*`-default` where *nodetype* is a valid type
    of node in the dataset. These formats have a special meaning for Text-Fabric.

    Remember that the formats are defined in the `otext` warp config feature of your
    set, not by Text-Fabric.
    
    ??? note "Freedom of names for formats"
        There is complete freedom of choosing names for text formats.
        They do not have to complied with the above-mentioned scheme.

??? abstract "T.formats"
    ```python
    T.formats
    ```

    ???+ info "Description"
        Show the text representation formats that have been defined in your dataset.

??? abstract "T.text()"
    ```python
    T.text(nodes, fmt=None)
    T.text(node, fmt=None, descend=False)
    ```

    ???+ info "Description"
        Gives the text that corresponds to a bunch of nodes.

    ??? info "nodes"
        `nodes` can be an arbitrary iterable of nodes.
        No attempt will be made to sort the nodes.
        If you need order, it is
        better to order the nodes before you feed them to `T.text()`.

    ??? info "fmt"
        The format of text-representation is given with `fmt`, with default `text-orig-full`.
        If the `fmt`
        cannot be found, the default is taken.

        The default is `text-orig-full` if the first argument is an iterable of `nodes`.

        The default is *nodetype*`-default`
        if the first argument is a single `node` with type *nodetype*.

        If the default format is not defined in the
        `otext` feature of the dataset,
        what will happen is dependent on the first argument, `nodes` or `node`.

        If the argument is an iterable of `nodes`,
        for each node its node type and node number
        will be output, connected with a `_` .

        If the argument is a single `node`,
        Text-Fabric will look up de slot nodes contained in it
        (by means of `L.d(node, otype=slotType)`
        and format them with `text-orig-full`.

        If the format **is** defined, and the first argument
        is a single `node`, 
        Text-Fabric will apply that format to the node itself,
        not to the slots contained in that node.

        But you can override that by means of `descend=True`.
        In that case, regardless of the format,
        the `node` will be replaced by the slot nodes contained in it,
        before applying the format.

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
                In the some corpora case this happens for the type of lexemes: `lex`.
                Lexemes contain their occurrences
                as slots, but the representation of a lexeme
                is not the string of its occurrences, but
                resides in a feature such as `voc_lex_utf8` (vocalized lexeme in Unicode).

                If the dataset defines the format `lex-default={lex} `,
                this is the only thing needed to regulate the representation of a lexeme.

                Hence, `T.text(lx)` results in the lexeme representation of `lx`.

                But if you really want to print out all occurrences of lexeme `lx`,
                you can say `T.text(lx, descend=True)`.

                Beware of this, however:
                
                `T.text(phr)` prints the full text of `phr` if `phr` is a phrase node.

                `T.text(phr, fmt='text-orig-full')` prints the empty string. Why?

                `T.text(phr, fmt='text-orig-full', descend=True)`
                prints the full text of the phrase.

                In the first case there is no `fmt` argument,
                so the default is taken,
                which would be `phrase-default`.
                But this format does not exists, so Text-Fabric
                descends to the words of the phrase and applies `text-orig-full` to them.

                In the second case, there is a `fmt` argument, so Text-Fabric applies that 
                to the `node`. But `text-orig-full` uses features that have values on words,
                not on phrases.

                The third case is what you probably wanted, and this is what you need if you 
                want to print the phrase in non-default formats:

                `T.text(phr, fmt='text-phono-full', descend=True)`

        ??? caution "No error messages"
            This function does not give error messages,
            because that could easily overwhelm
            the output stream, especially in a notebook.

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

