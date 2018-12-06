# Text-Fabric API

??? note "Tutorial"
    The tutorials for the
    [Hebrew Bible]({{etcbcnb}}/bhsa/blob/master/tutorial/start.ipynb),
    [Peshitta]({{etcbcnb}}/peshitta/blob/master/tutorial/start.ipynb),
    [Syriac New Testament]({{etcbcnb}}/syrnt/blob/master/tutorial/start.ipynb),
    and the
    [Uruk Cuneiform Tablets]({{ninonb}}/uruk/blob/master/tutorial/start.ipynb)
    put the Text-Fabric API on show for vastly different corpora.

???+ note "Generic API versus apps"
    This is the API of Text-Fabric in general.
    Text-Fabric has no baked in knowledge of particular corpora.

    However, Text-Fabric comes with several *apps* that make working
    with specific [corpora](../About/Corpora.md) easier.

## Core

### Loading

??? abstract "TF=Fabric()"
    ```python
    from tf.fabric import Fabric
    TF = Fabric(locations=directories, modules=subdirectories, silent=False)
    ```

    ???+ info "Description"
        Text-Fabric is initialized for a corpus. It will search a set of directories
        and catalog all `.tf` files it finds there.
        These are the features you can subsequently load.

        Here `directories` and `subdirectories` are strings with directory names
        separated by newlines, or iterables of directories.

    ??? info "locations, modules"
        The directories specified in `locations` will be searched for `modules`, which
        are paths that will be appended to the paths in `locations`.

        All `.tf` files (non-recursively) in any `module` will be added to the feature
        set to be loaded in this session. The order in `modules` is important, because
        if a feature occurs in multiple modules, the last one will be chosen. In this
        way you can easily override certain features in one module by features in an
        other module of your choice.

    ??? note "otext@ in modules"
        If modules contain features with a name starting with `otext@`, then the format
        definitions in these features will be added to the format definitions in the
        regular `otext` feature (which is a WARP feature). In this way, modules that
        define new features for text representation, also can add new formats to the
        Text-API.

    ??? hint "Defaults"
        The `locations` list has a few defaults:

        ```
        ~/Downloads/text-fabric-data
        ~/text-fabric-data
        ~/github/text-fabric-data
        ```

        So if you have stored your main Text-Fabric dataset in
        `text-fabric-data` in one of these directories
        you do not have to pass a location to Fabric.

        The `modules` list defaults to `['']`. So if you leave it out, Text-Fabric will
        just search the paths specified in `locations`.

    ??? info "silent"
        If `silent=True` is passed, banners and normal progress messages are suppressed.

??? abstract "TF.explore()"
    ```python
    features = TF.explore(silent=False, show=True)
    features
    ```

    or

    ```python
    TF.explore(silent=False, show=False)
    TF.featureSets
    ```

    ???+ info "Description"
        This will give you a dictionary of all available features by kind. The kinds
        are: *nodes*, *edges*, *configs*, *computeds*.

    ??? info "silent"
        With `silent=False` a message containing the total numbers of features is issued.

    ??? info "show"
        The resulting dictionary is delivered in `TF.featureSets`, but if you say
        `show=True`, the dictionary is returned as function result.


??? abstract "api=TF.load()"
    ```python
    api = TF.load(features, add=False, silent=False)
    ```

    ???+ info "Description"
        Reads the features indicated by `features` and loads them in memory
        ready to be used in the rest of the program.

    ??? info "features"
        `features` is a string containing space separated feature names, or an
        iterable of feature names. The feature names are just the names of `.tf` files
        without directory information and without extension.

    ??? info "add"
        If later on you want load more features, you can either:

        *   add the features to the original `load()` statement and just run it again
        *   make a new statement: `TF.load(newfeatures, add=True)`. The new features will
            be added to the same api, so you do not have to to call
            `api.makeAvailableIn(globals())` again after this!

    ??? info "silent"
        The features will be loaded rather silently, most messages will be suppressed.
        Time consuming operations will always be announced, so that you know what
        Text-Fabric is doing. If `silent=True` is passed, all informational messages
        will be suppressed. This is handy I you want to load data as part of other
        methods, on-the-fly.

??? abstract "api.makeAvailableIn(globals())"
    ```python
    api.makeAvailableIn(globals())
    ```

    ???+ info "Description"
        This method will export every member of the API (such as `N`, `F`, `E`, `L`, `T`,
        `info`) to the global namespace. From now on, we will omit the `api.` in our
        documentation.

    ??? explanation "Contents of the API"
        After having loaded the features by `api = TF.load(...)`, the `api` harbours
        your Text-Fabric API. You can access node feature `mydata` by `api.F.mydata.v(node)`, edge
        feature `mylink` by `api.E.mylink.f(node)`, and so on.

        If you are working with a single data source in your program, it is a bit
        tedious to write the initial `api.` all the time.
        By this methodd you can avoid that.

    ??? hint "Longer names"
        There are also longer names which can be used as aliases to the single capital
        letters. This might or might not improve the readability of your program.

        short name | long name
        --- | ---
        `N` | `Nodes`
        `F` | `Feature`
        `Fs` | `FeatureString`
        `Fall` | `AllFeatures`
        `E` | `Edge`
        `Es` | `EdgeString`
        `Eall` | `AllEdges`
        `C` | `Computed`
        `Cs` | `ComputedString`
        `Call` | `AllComputeds`
        `L` | `Locality`
        `T` | `Text`
        `S` | `Search`

??? abstract "ignored"
    ```python
    api.ignored
    ```

    ???+ info "Description"
        If you want to know which features were found but ignored (because the feature
        is also present in another, later, location), you can use this attribute
        to inspect the ignored features and their locations.

??? abstract "loadLog()"
    ```python
    api.loadlog()
    ```

    ???+ info "Description"
        After loading you can view all messages using this method.
        It also shows the messages that have been suppressed due to `silent=True`.

### Navigating nodes

??? abstract "N()"
    ```python
    for n in N():
        action
    ```

    ???+ info "Description"
        The result of `N()` is a generator that walks through all nodes in the
        *canonical order* (see below).
        Iterating over `N()` delivers you all words and structural elements of
        your corpus in a very natural order.

    ??? explanation "Walking nodes"
        Most processing boils down to walking through the nodes by visiting node sets in
        a suitable order. Occasionally, during the walk you might want to visit
        embedding or embedded nodes to glean some feature information from them.

    ??? hint "More ways of walking"
        Later, under *Features* there is another convenient way to walk through
        nodes.

??? explanation "canonical order"
    The canonical order is a way to sort the nodes in your corpus in such a way
    that you can enumerate all nodes in the order you encounter them if you
    walk through your corpus.

    Briefly this means:

    *   embedder nodes come before the nodes that lie embedded in them;
    *   earlier stuff comes before later stuff,
    *   if a verse coincides with a sentence, the verse comes before the sentence,
        because verses generally contain sentences and not the other way round;
    *   if two objects are intersecting, but none embeds the other, the one with the
        smallest slot that does not occur in the other, comes first.

    ??? example "first things first, big things first"
        That means, roughly, that you start with a
        book node (Genesis), then a chapter node (Genesis 1), then a verse node, Genesis
        1:1, then a sentence node, then a clause node, a phrase node, and the first word
        node. Then follow all word nodes in the first phrase, then the phrase node of
        the second phrase, followed by the word nodes in that phrase. When ever you
        enter a higher structure, you will first get the node corresponding to that
        structure, and after that the nodes corresponding to the building blocks of that
        structure.

    This concept follows the intuition that slot sets with smaller elements come
    before slot set with bigger elements, and embedding slot sets come before
    embedded slot sets. Hence, if you enumerate a set of nodes that happens to
    constitute a tree hierarchy based on slot set embedding, and you enumerate those
    nodes in the slot set order, you will walk the tree in pre-order.

    This order is a modification of the one as described in (Doedens 1994, 3.6.3).

    ![fabric](../images/DoedensLO.png)

    > Doedens, Crist-Jan (1994), *Text Databases. One Database Model and Several
    > Retrieval Languages*, number 14 in Language and Computers, Editions Rodopi,
    > Amsterdam, Netherlands and Atlanta, USA. ISBN: 90-5183-729-1,
    > <{{doedens}}>. The order as defined by
    > Doedens corresponds to walking trees in post-order.

    For a lot of processing, it is handy to have a the stack of embedding elements
    available when working with an element. That is the advantage of pre-order over
    post-order. It is very much like SAX parsing in the XML world.


??? abstract "sortNodes()"
    ```python
    sortNodes(nodeSet)
    ```

    ???+ info "Description"
        delivers an iterable of nodes as a tuple sorted by the *canonical ordering*.

    ??? info "nodeSet"
        An iterable of nodes to be sorted.

??? abstract "sortKey"
    ```python
    nodeList = sorted(nodes, key=sortKey)
    ```

    ???+ info "Description"
        A function that provides for each node the key to be used to sort nodes in the
        canonical ordering. That means that the following two pieces of code do the same
        thing:

        `sortNodes(nodeSet)` and `sorted(nodeSet, key=sortKey)`.

??? abstract "sortKeyTuple"
    ```python
    tupleList = sorted(tuples, key=sortKeyTuple)
    ```

    ??? info "Description"
        Same as `sortKey`, but this one works on tuples instead of nodes.
        It appies `sortKey` to each member of the tuple.
        Handy to sort e.g. search results. We
        could sort them in canonical order like this:

        ```python
        sorted(results, key=lambda tup: tuple(sortKey(n) for n in tup))
        ```

        This is exactly what `sortKeyTuple` does, but then a bit more efficient.

??? abstract "otypeRank"
    ```python
    otypeRank['sentence']
    ```
    The node types are ordered in `C.levels.data`, and if you reverse that list, you get
    the rank of a type by looking at the position in which that type occurs.

    The *slotType* has otypeRank 0, and the more comprehensive a type is, the higher its rank.
    
### Locality

??? explanation "Local navigation"
    Here are the methods by which you can navigate easily from a node to its
    neighbours: parents and children, previous and next siblings.

???+ info "L"
    The Locality API is exposed as `L` or `Locality`.

??? hint "otype parameter"
    In all of the following `L`-functions, if the `otype` parameter is passed, the result is filtered and
    only nodes with `otype=nodeType` are retained.

??? caution "Results of the `L.` functions are tuples, not single nodes"
      Even if an `L`-function returns a single node, it is packed in a *tuple*.
      So to get the node itself, you have to dereference the tuple:

      ```python
      L.u(node)[0]
      ```

??? abstract "L.u()"
    ```python
    L.u(node, otype=nodeType)
    ```

    ???+ info "Description"
        Produces an ordered tuple of nodes **upward**, i.e. embedder nodes.

    ??? info "node"
        The node whose embedder nodes will be delivered.
        The result never includes `node` itself.
        But other nodes linked to the same set of slots as `node` count as embedder nodes. 
        But slots are never embedders.

??? abstract "L.d()"
    ```python
    L.d(node, otype=nodeType)
    ```

    ???+ info "Description"
        Produces an ordered tuple of nodes **downward**, i.e. embedded nodes.

    ??? info "node"
        The node whose embedded nodes will be delivered.
        The result never includes `node` itself.
        But other nodes linked to the same set of slots as `node` count as embedded nodes. 
        But nothing is embedded in slots.

??? abstract "L.n()"
    ```python
    L.n(node, otype=nodeType)
    ```

    ???+ info "Description"
        Produces an ordered tuple of adjacent **next** nodes.

    ??? info "node"
        The node whose right adjacent nodes will be delivered;
        i.e. the nodes whose first slot immediately follow the last slot 
        of `node`.
        The result never includes `node` itself.

??? abstract "L.p()"
    ```python
    L.p(node, otype=nodeType)
    ```

    ???+ info "Description"
        Produces an ordered tuple of adjacent **previous** nodes from `node`, i.e. nodes
        whose last slot just precedes the first slot of `node`.

    ???+ info "Description"
        Produces an ordered tuple of adjacent **previous** nodes.

    ??? info "node"
        The node whose lefy adjacent nodes will be delivered;
        i.e. the nodes whose last slot immediately precede the first slot 
        of `node`.

??? explanation "Locality and levels"
    Here is something that is very important to be aware of when using `sortNodes`
    and the `L.d(n)` and `L.u(n)` methods.

    When we order nodes and report on which nodes embed which other nodes, we do not
    only take into account the sets of slots the nodes occupy, but also their
    *level*. See [levels](#levels) and [text](#levels-of-node-types).

    Both the `L.d(n)` and `L.u(n)` work as follows:

    *   `L.d(n)` returns nodes such that embedding nodes come before embedded nodes
        words)
    *   `L.u(n)` returns nodes such that embedded nodes come before embedding nodes
        books)

    **N.B.:** Suppose you have node types `verse` and `sentence`, and usually a
    verse has multiple sentences, but not vice versa. Then you expect that

    *   `L.d(verseNode)` will contain sentence nodes,
    *   `L.d(sentenceNode)` will **not** contain verse nodes.

    But if there is a verse with exactly one sentence, and both have exactly the
    same words, then that is a case where:

    *   `L.d(verseNode)` will contain one sentence node,
    *   `L.d(sentenceNode)` will contain **one** verse node.

### Text

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

#### Sections

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

#### Book names and languages

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

#### Text representation

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

        The default is *nodetype*`-default` if the first argument is a single `node` with type *nodetype*.

        If the default format is not defined in the
        `otext` feature of the dataset,
        what will happen is dependent on the first argument, `nodes` or `node`.

        If the argument is an iterable of `nodes`, for each node its node type and node number
        will be output, connected with a `_` .

        If the argument is a single `node`, Text-Fabric will look up de slot nodes contained in it
        (by means of `L.d(node, otype=slotType)` and format them with `text-orig-full`.

        If the format **is** defined, and the first argument is a single `node`, 
        Text-Fabric will apply that format to the node itself, not to the slots contained in that node.

        But you can override that by means of `descend=True`. In that case, regardless of the format,
        the `node` will be replaced by the slot nodes contained in it, before applying the format.

        ??? hint "The default is sensible"
            Consider the simplest call to this function: `T.text(node)`.
            This will apply the default format to `node`. If `node` is non-slot, then in most cases
            the default format will be applied to the slots contained in `node`.

            But for special node types, where the best representation is not obtained by descending down
            to the contained slot nodes, the dataset may define special default types that use other
            features to furnish a decent representation.

            ??? example "BHSA"
                In the BHSA case this happens for the type of lexemes: `lex`. Lexemes contain their occurrences
                as slots, but the representation of a lexeme is not the string of its occurrences, but
                resides in a feature such as `voc_lex_utf8` (vocalized lexeme in Unicode).

                The BHSA dataset defines the format `lex-default={voc_lex_utf8} ` and this is the only thing
                needed to regulate the representation of a lexeme.

                Hence, `T.text(lx)` results in the vocalized lexeme representation of `lx`.

                But if you really want to print out all occurrences of lexeme `lx`, you can say
                `T.text(lx, descend=True)`.

                Beware of this, however:
                
                `T.text(phr)` prints the full text of `phr` if `phr` is a phrase node.

                `T.text(phr, fmt='text-orig-full')` prints the empty string. Why?

                `T.text(phr, fmt='text-orig-full', descend=True)` prints the full text of the phrase.

                In the first case there is no `fmt` argument, so the default is taken,
                which would be `phrase-default`. But this format does not exists, so Text-Fabric
                descends to the words of the phrase and applies `text-orig-full` to them.

                In the second case, there is a `fmt` argument, so Text-Fabric applies that 
                to the `node`. But `text-orig-full` uses features that have values on words,
                not on phrases.

                The third case is what you probably wanted, and this is what you need if you 
                want to print the phrase in non-default formats:

                `T.text(phr, fmt='text-phono-full', descend=True)`

        ??? caution "No error messages"
            This function does not give error messages, because that could easily overwhelm
            the output stream, especially in a notebook.

    ??? note "Non slot nodes allowed"
        In most cases, the nodes fed to `T.text()` are slots, and the formats are
        templates that use features that are defined for slots.

        But nothing prevents you to define a format for non-slot nodes, and use features
        defined for a non-slot node type.

        If, for example, your slot type is *glyph*, and you want a format that renders
        lexemes, which are not defined for glyphs but for words, you can just define a
        format in terms of word features.

        It is your responsibility to take care to use the formats for node types for
        which they make sense.

    ??? caution "Escape whitespace in formats"
        When defining formats in `otext.tf`, if you need a newline or tab in the format,
        specify it as `\n` and `\t`.


### Features

???+ info "Features"
    TF can give you information of all features it has encountered.

??? abstract "TF.featureSets"
    ```python
    TF.featureSets
    ```

    ???+ info "Description"
        Returns a dictionary with keys `nodes`, `edges`, `configs`, `computeds`.

        Under each key there is the set of feature names in that category.
        
        So you can easily test whether a node feature or edge feature is present in the
        dataset you are working with.

        ??? note "configs"
            These are config features, with metadata only, no data. E.g. `otext`.

        ??? note "computeds"
            These are blocks of precomputed data, available under the `C.` API, see below.

    ??? caution "May be unloaded"
        The sets do not indicate whether a feature is loaded or not.
        There are other functions that give you the loaded node features (`Fall()`)
        and the loaded edge features (`Eall()`).

#### Node features

???+ info "F"
    The node features API is exposed as `F` (`Fs`) or `Feature` (`FeatureString`).

??? abstract "Fall() aka AllFeatures()"
    ```python
    Fall()
    AllFeatures()
    ```

    ???+ info "Description"
        Returns a sorted list of all usable, loaded node feature names.

??? abstract "F.*feature* aka Feature.*feature*"
    ```python
    F.part_of_speech
    Feature.part_of_speech
    ```

    ???+ info "Description"
        Returns a sub-api for retrieving data that is stored in node features.
        In this example, we assume there is a feature called
        `part_of_speech`.

    ??? caution "Tricky feature names"
        If the feature name is not
        a valid python identifier, you can not use this function,
        you should use `Fs` instead.

??? abstract "Fs(feature) aka FeatureString(feature)"
    ```python
    Fs(feature)
    FeatureString(feature)
    Fs('part-of-speech')
    FeatureString('part-of-speech')
    ```

    ???+ info "Description"
        Returns a sub-api for retrieving data that is stored in node features.
        
    ??? info "feature"
        In this example, in line 1 and 2, the feature name is contained in
        the variable `feature`.

        In lines 3 and 4, 
        we assume there is a feature called
        `part-of-speech`.
        Note that this is not a valid name in Python, yet we
        can work with features with such names.

    ??? explanation "Both methods have identical results"
        Suppose we have just issued `feature = 'pos'.
        Then the result of `Fs(feature)` and `F.pos` is identical.

        In most cases `F` works just fine, but `Fs` is needed in two cases:

        *   if we need to work with a feature whose name is not a valid
            Python name;
        *   if we determine the feature we work with dynamically, at run time.

    ??? note "Simple forms"
        In the sequel we'll give examples based on the simple form only.


??? abstract "F.*feature*.v(node)"
    ```python
    F.part_of_speech.v(node)
    ```

    ???+ info "Description"
        Get the value of a *feature*, such as `part_of_speech` for a node.

    ??? info "node"
        The node whose value for the feature is being retrieved.

??? abstract "F.*feature*.s(value)"
    ```python
    F.part_of_speech.s(value)
    F.part_of_speech.s('noun')
    ```

    ???+ info "Description"
        Returns a generator of all nodes in the canonical order with a given value for a given feature.
        This is an other way to walk through nodes than using `N()`.

    ??? info "value"
        The test value: all nodes with this value are yielded, the others pass through.

    ??? example "nouns"
        The second line gives you all nodes which are nouns according to the corpus.

??? abstract "F.*feature*.freqList()"
    ```python
    F.part_of_speech.freqList(nodeTypes=None)
    ```

    ???+ info "Description"
        Inspect the values of *feature* (in this example: `part_of_speech`)
        and see how often they occur. The result is a
        list of pairs `(value, frequency)`, ordered by `frequency`, highest frequencies
        first.

    ??? info "nodeTypes"
        If you pass a set of nodeTypes, only the values for nodes within those
        types will be counted.


??? abstract "F.otype"
    `otype` is a special node feature and has additional capabilities.

    ???+ info "Description"
        *   `F.otype.slotType` is the node type that can fill the slots (usually: `word`)
        *   `F.otype.maxSlot` is the largest slot number
        *   `F.otype.maxNode` is the largest node number
        *   `F.otype.all` is a list of all *otypes* from big to small (from books through
            clauses to words)
        *   `F.otype.sInterval(otype)` is like `F.otype.s(otype)`, but instead of
            returning you a range to iterate over, it will give you the starting and
            ending nodes of `otype`. This makes use of the fact that the data is so
            organized that all node types have single ranges of nodes as members.

#### Edge features

???+ info "E"
    The edge features API is exposed as `E` (`Es`) or `Edge` (`EdgeString`).

??? abstract "Eall() aka AllEdges()"
    ```python
    Eall()
    AllEdges()
    ```

    ???+ info "Description"
        Returns a sorted list of all usable, loaded edge feature names.

??? abstract "E.*feature* aka Edge.*feature*"
    ```python
    E.head
    Feature.head
    ```

    ???+ info "Description"
        Returns a sub-api for retrieving data that is stored in edge features.
        In this example, we assume there is a feature called
        `head`.

    ??? caution "Tricky feature names"
        If the feature name is not
        a valid python identifier, you can not use this function,
        you should use `Es` instead.

??? abstract "Es(feature) aka EdgeString(feature)"
    ```python
    Es(feature)
    EdgeString(feature)
    Es('head')
    EdgeString('head')
    ```

    ???+ info "Description"
        Returns a sub-api for retrieving data that is stored in edge features.
        
    ??? info "feature"
        In this example, in line 1 and 2, the feature name is contained in
        the variable `feature`.

        In lines 3 and 4, 
        we assume there is a feature called
        `head`.

    ??? explanation "Both methods have identical results"
        Suppose we have just issued `feature = 'head'.
        Then the result of `Es(feature)` and `E.pos` is identical.

        In most cases `E` works just fine, but `Es` is needed in two cases:

        *   if we need to work with a feature whose name is not a valid
            Python name;
        *   if we determine the feature we work with dynamically, at run time.

    ??? note "Simple forms"
        In the sequel we'll give examples based on the simple form only.

??? abstract "E.*feature*.f(node)"
    ```python
    E.head.f(node)
    ```

    ???+ info "Description"
        Get the nodes reached by *feature*-edges **from** a certain node.
        These edges must be specified in *feature*, in this case `head`.
        The result is an ordered tuple
        (again, in the *canonical order*. The members of the
        result are just nodes, if `head` describes edges without values. Otherwise
        the members are pairs (tuples) of a node and a value.

        If there are no edges from the node, the empty tuple is returned, rather than `None`.

    ??? info "node"
        The node **from** which the edges in question start.

??? abstract "E.*feature*.t(node)"
    ```python
    E.head.t(node)
    ```

    ???+ info "Description"
        Get the nodes reached by *feature*-edges **to** a certain node.
        These edges must be specified in *feature*, in this case `head`.
        The result is an ordered tuple
        (again, in the *canonical order*. The members of the
        result are just nodes, if `feature` describes edges without values. Otherwise
        the members are pairs (tuples) of a node and a value.

        If there are no edges to `n`, the empty tuple is returned, rather than `None`.

    ??? info "node"
        The node **to** which the edges in question go.

??? abstract "E.*feature*.freqList()"
    ```python
    E.op.freqList(nodeTypesFrom=None, nodeTypesTo=None)
    ```

    ???+ info "Description"
        If the edge feature has no values, simply return the number of node pairs
        between an edge of this kind exists.

        If the edge feature does have values, we 
        inspect them
        and see how often they occur. The result is a
        list of pairs `(value, frequency)`, ordered by `frequency`, highest frequencies
        first.

    ??? info "nodeTypesFrom"
        If not `None`,
        only the values for edges that start from a node with type
        within `nodeTypesFrom`
        will be counted.

    ??? info "nodeTypesTo"
        If not `None`,
        only the values for edges that go to a node with type
        within `nodeTypesTo`
        will be counted.

??? abstract "E.oslots"
    `oslots` is a special edge feature and is mainly used to construct other parts
    of the API. It has less capabilities, and you will rarely need it. It does not
    have `.f` and `.t` methods, but an `.s` method instead.

    ???+ info "Description"
        `E.oslots.s(node)`
        Gives the sorted list of slot numbers linked to a node,
        or put otherwise: the slots that **support** that node.

    ??? info "node"
        The node whose slots are being delivered.

#### Computed data

??? explanation "Pre-computing"
    In order to make the API work, Text-Fabric prepares some data and saves it in
    quick-load format. Most of this data are the features, but there is some extra
    data needed for the special functions of the WARP features and the L-API.

    Normally, you do not use this data, but since it is there, it might be valuable,
    so we have made it accessible in the `C`-api, which we document here.

??? abstract "Call() aka AllComputeds()"
    ```python
    Call()
    AllComputeds()
    ```

    ???+ info "Description"
        Returns a sorted list of all usable, loaded computed data names.

??? abstract "C.levels.data"
    ???+ info "Description"
        A sorted list of object types plus basic information about them.

        Each entry in the list has the shape

        ```python
            (otype, averageSlots, minNode, maxNode)
        ```

        where `otype` is the name of the node type, `averageSlots` the average size of
        objects in this type, measured in slots (usually words). `minNode` is the first
        node of this type, `maxNode` the last, and the nodes of this node type are
        exactly the nodes between these two values (including).

    ??? explanation "Level computation and customization"
        All node types have a level, defined by the average amount of slots object of
        that type usually occupy. The bigger the average object, the lower the levels.
        Books have the lowest level, words the highest level.

        However, this can be overruled. Suppose you have a node type *phrase* and above
        it a node type *cluster*, i.e. phrases are contained in clusters, but not vice
        versa. If all phrases are contained in clusters, and some clusters have more
        than one phrase, the automatic level ranking of node types works out well in
        this case. But if clusters only have very small phrases, and the big phrases do
        not occur in clusters, then the algorithm may assign a lower rank to clusters
        than to phrases.

        In general, it is too expensive to try to compute the levels in a sophisticated
        way. In order to remedy cases where the algorithm assigns wrong levels, you can
        add a `@levels` key to the `otext` config feature. See
        [text](#levels-of-node-types).

??? abstract "C.order.data"
    ???+ info "Description"
        An **array** of all nodes in the correct order. This is the
        order in which `N()` alias `Node()` traverses all nodes.

    ??? explanation "Rationale"
        To order all nodes in the [canonical ordering](#sorting-nodes) is quite a bit of
        work, and we need this ordering all the time.

??? abstract "C.rank.data"
    ???+ info "Description"
        An **array** of all indices of all nodes in the canonical order
        array. It can be viewed as its inverse.

    ??? explanation "Order arbitrary node sets"
        I we want to order a set of nodes in the canonical ordering, we need to know
        which position each node takes in the canonical order, in other words, at what
        index we find it in the [`C.order.data`](#order) array.

??? abstract "C.levUp.data and C.levDown.data"
    ???+ info "Description"
        These tables feed the `L.d()` and `L.u()` functions.

    ??? caution "Use with care"
        They consist of a fair amount of megabytes, so they are heavily optimized.
        It is not advisable to use them directly, it is far better to use the `L` functions.

        Only when every bit of performance waste has to be squeezed out, this raw data
        might be a deal.

??? abstract "C.boundary.data"
    ???+ info "Description"
        These tables feed the `L.n()` and `L.p()` functions.
        It is a tuple consisting of `firstSlots` and `lastSlots`.
        They are indexes for the first slot
        and last slot of nodes.
        
    ??? explanation "Slot index"
        For each slot, `firstSlot` gives all nodes (except
        slots) that start at that slot, and `lastSlot` gives all nodes (except slots)
        that end at that slot.
        Both `firstSlot` and `lastSlot` are tuples, and the
        information for node `n` can be found at position `n-MaxSlot-1`.

??? abstract "C.sections.data"
    ???+ info "Description"
        Let us assume for the sake of clarity, that the node type of section level 1 is
        `book`, that of level 2 is `chapter`, and that of level 3 is `verse`. And
        suppose that we have features, named `bookHeading`, `chapterHeading`, and
        `verseHeading` that give the names or numbers of these.

        ??? caution "Custom names"
            Note that the terms `book`, `chapter`, `verse` are not baked into Text-Fabric.
            It is the corpus data, especially the `otext` config feature that
            spells out the names of the sections.

        Then `C.section.data` is a tuple of two mappings , let us call them `chapters`
        and `verses`.

        `chapters` is a mapping, keyed by `book` **nodes**, and then by
        by chapter **headings**, giving the corresponding
        chapter **node**s as values.

        `verses` is a mapping, keyed by `book` **nodes**, and then
        by chapter **headings**, and then by verse **headings**,
        giving the corresponding verse **node**s as values.

    ??? explanation "Supporting the `T`-Api"
        The `T`-api is good in mapping nodes unto sections, such as books, chapters,
        verses and back. It knows how many chapters each book has, and how many verses
        each chapter.

        The `T` api is meant to make your life easier when you have to find passage
        labels by nodes or vice versa. That is why you probably never need to consult
        the underlying data. But you can! That data is stored in

### Saving features

??? abstract "TF.save()"
    ```python
    TF.save(nodeFeatures={}, edgeFeatures={}, metaData={}, module=None)
    ```

    ???+ info "Description"
        If you have collected feature data in dictionaries, keyed by the
        names of the features, and valued by their feature data,
        then you can save that data to `.tf` feature files on disk.

        It is this easy to export new data as features:
        collect the data and metadata of
        the features and 
        feed it in an orderly way to `TF.save()` and there you go.
         
    ??? info "nodeFeatures"
        The data of a node feature is a dictionary with nodes as keys (integers!) and
        strings or numbers as (feature) values.

    ??? info "edgeFeatures"
        The data of an edge feature is a dictionary with nodes as keys, and sets or
        dictionaries as values. These sets should be sets of nodes (integers!), and
        these dictionaries should have nodes as keys and strings or numbers as values.

    ??? info "metadata"
        Every feature will receive metadata from `metaData`, which is a dictionary
        mapping a feature name to its metadata.
        
        ??? note "value types"
            The type of the values should conform to `@valueType` (`int` or `str`), which
            must be stated in the metadata.

        ??? note "edge values"
            If you save an edge feature, and there are values in that edge feature, you have
            to say so, by specifying `edgeValues = True` in the metadata for that feature.

        ??? note "generic metadata"
          `metaData` may also contain fields under
          the empty name. These fields will be added to all features in `nodeFeatures` and
          `edgeFeatures`.

        ??? note "config features"
            If you need to write the *config* feature `otext`,
            which is a metadata-only feature, just
            add the metadata under key `otext` in `metaData` and make sure
            that `otext` is not a key in `nodeFeatures` nor in
            `edgeFeatures`.
            These fields will be written into the separate config feature `otext`,
            with no data associated.

    ??? note "save location"
        The (meta)data will be written to the very last module in the list of locations
        that you specified when calling `Fabric()` or to what you passed as `module` in
        the same location. If that module does not exist, it will be created in the last
        `location`. If both `locations` and `modules` are empty, writing will take place
        in the current directory.

### Messaging

??? info "Timed messages"
    Error and informational messages can be issued, with a time indication.

??? abstract "info(), error()"
    ```python
    info(msg, tm=True, nl=True)
    ```
    
    ???+ info "Description"
        Sends a message to standard output, possibly with time and newline.

        *   if `info()` is being used, the message is sent to `stdout`;
        *   if `error()` is being used, the message is sent to `stderr`;

        In a Jupyter notebook, the standard error is displayed with
        a reddish background colour.

    ??? info "tm"
        If `True`, an indicator of the elapsed time will be prepended to the message.

    ??? info "nl"
        If `True` a newline will be appended.

??? abstract "indent()"
    ```python
    indent(level=None, reset=False)
    ```

    ???+ info "Description"
        Changes the level of indentation of messages and possibly resets the time.

    ??? info "level"
        The level of indentation, an integer.  Subsequent
        `info()` and `error()` will display their messages with this indent.

    ??? info "reset"
        If `True`, the elapsed time to will be reset to 0 at the given level.
        Timers at different levels are independent of each other.

### Clearing the cache

??? abstract "TF.clearCache()"
    ```python
    TF.clearCache()
    ```

    ???+ info "Description"
        Text-Fabric precomputes data for you, so that it can be loaded faster. If the
        original data is updated, Text-Fabric detects it, and will recompute that data.

        But there are cases, when the algorithms of Text-Fabric have changed, without
        any changes in the data, where you might want to clear the cache of precomputed
        results.

        Calling this function just does it, and it is equivalent with manually removing
        all `.tfx` files inside the hidden `.tf` directory inside your dataset.

    ??? hint "No need to load"
        It is not needed to execute a `TF.load()` first.


### Miscellaneous

??? abstract "TF.version"
    ???+ info "Description"
        Contains the version number of the Text-Fabric
        library.

??? abstract "TF.banner"
    ???+ info "Description"
        Contains the name and the version of the Text-Fabric
        library.

## Search
 
For a description of Text-Fabric search, go to [Search](../Use/Search.md)

???+ info "S"
    The Search API is exposed as `S` or `Search`.

    It's main method, `search`, takes a [search template](../Search#search-templates)
    as argument.
    A template consists of elements that specify nodes with conditions and
    relations between them.
    The results of a search are instantiations of the search template.
    More precisely, each instantiation is a tuple of nodes
    that instantiate the elements in the template,
    in such a way that the relational pattern expressed in the template
    holds between the nodes of the result tuple.

### Search API

The API for searching is a bit richer than the `search()` functions.
Here is the whole interface.

??? abstract "S.relationsLegend()"
    ```python
    S.relationsLegend()
    ```

    ???+ info "Description"
        Gives dynamic help about the basic relations that you can use in your search
        template. It includes the edge features that are available in your dataset.


??? abstract "S.search()"
    ```python
    S.search(query, limit=None, shallow=False, sets=None, withContext=None)
    ```

    ???+ info "Description"
        Searches for combinations of nodes that together match a search template.
        This method returns a *generator* which yields the results one by one. One result
        is a tuple of nodes, where each node corresponds to an *atom*-line in your
        [search template](#search-template-introduction).
        
    ??? info "query"
        The query is a search template, i.e. a string that conforms to the rules described above.
        
    ??? info "shallow"
        If `True` or `1`, the result is a set of things that match the top-level element
        of the `query`.

        If `2` or a bigger number *n*, return the set of truncated result tuples: only
        the first *n* members of each tuple is retained.

        If `False` or `0`, a sorted list of all result tuples will be returned.

    ??? info "sets"
        If not `None`, it should be a dictionary of sets, keyed by a names.
        In `query` you can refer to those names to invoke those sets.

    ??? info "limit"
        If `limit` is a number, it will fetch only that many results.

    ??? hint "TF as Database"
        By means of `S.search(query)` you can use one `TF` instance as a
        database that multiple clients can use without the need for each client to call the 
        costly `load` methods.
        You have to come up with a process that runs TF, has all features loaded, and
        that can respond to queries from other processes.
        We call such a process a **TF kernel**.

        Web servers can use such a daemonized TF to build efficient controllers.

        A TF kernel and web server are included in the Text-Fabric code base.
        See [kernel](../Server/Kernel.md) and [web](../Server/Web.md).

    ??? note "Generator versus tuple"
        If `limit` is specified, the result is not a generator but a tuple of results.

    ??? explanation "More info on the search plan"
        Searching is complex. The search template must be parsed, interpreted, and
        translated into a search plan. The following methods expose parts of the search
        process, and may provide you with useful information in case the search does not
        deliver what you expect.

    ??? hint "see the plan"
        the method `S.showPlan()` below shows you at a glance the correspondence
        between the nodes in each result tuple and your search template.

??? abstract "S.study()"
    ```python
    S.study(searchTemplate, strategy=None, silent=False, shallow=False, sets=None)
    ```

    ???+ info "Description"
        Your search template will be checked, studied, the search
        space will be narrowed down, and a plan for retrieving the results will be set
        up.

        If your query has quantifiers, the asscociated search templates will be constructed
        and executed. These searches will be reported clearly.

    ??? info "searchTemplate"
        The search template is a string that conforms to the rules described above.

    ??? danger "strategy"
        In order to tame the performance of search, the strategy by which results are fetched
        matters a lot.
        The search strategy is an implementation detail, but we bring
        it to the surface nevertheless.

        To see the names of the available strategies, just call
        `S.study('', strategy='x')` and you will get a list of options reported to
        choose from.

        Feel free to experiment. To see what the strategies do,
        see the [code]({{tfghb}}/{{c_search}}).

    ??? info "silent"
        If you want to suppress most of the output, say `silent=True`.

    ??? info "shallow, sets"
        As in `S.search()`.

??? abstract "S.showPlan()"
    ```python
    S.showPlan(details=False)
    ```

    ???+ info "Description"
        Search results are tuples of nodes and the plan shows which part of the tuple
        corresponds to which part of the search template.

    ??? info "details"
        If you say `details=True`, you also get an overview of the search space and a
        description of how the results will be retrieved.

    ??? note "after S.study()"
        This function is only meaningful after a call to `S.study()`.

### Search results

??? info "Preparation versus result fetching"
    The method `S.search()` above combines the interpretation of a given
    template, the setting up of a plan, the constraining of the search space
    and the fetching of results.

    Here are a few methods that do actual result fetching.
    They must be called after a previous `S.search()` or `S.study()`.

??? abstract "S.count()"
    ```python
    S.count(progress=None, limit=None)
    ```

    ??? info "Description"
        Counts the results, with progress messages, optionally up to a limit.
        
    ??? info "progress"
        Every so often it shows a progress message.
        The frequency is `progress` results, default every 100.

    ??? info "limit"
        Fetch results up to a given `limit`, default 1000.
        Setting `limit` to 0 or a negative value means no limit: all results will be
        counted.

    ??? note "why needed"
        You typically need this in cases where result fetching turns out to
        be (very) slow.

    ??? caution "generator versus list"
        `len(S.results())` does not work, because `S.results()` is a generator
        that delivers its results as they come.

??? abstract "S.fetch()"
    ```python
    S.fetch(limit=None)
    ```

    ???+ info "Description"
        Finally, you can retrieve the results. The result of `fetch()` is not a list of
        all results, but a *generator*. It will retrieve results as long as they are
        requested and their are still results.

    ??? info "limit"
        Tries to get that many results and collects them in a tuple.
        So if limit is not `None`, the result is a tuple with a known length.

    ??? example "Iterating over the `fetch()` generator"
        You typically fetch results by saying:

        ```python
        i = 0
        for r in S.results():
            do_something(r[0])
            do_something_else(r[1])
        ```

        Alternatively, you can set the `limit` parameter, to ask for just so many
        results. They will be fetched, and when they are all collected, returned as a
        tuple.

    ??? example "Fetching a limited amount of results"
        ```python
        S.fetch(limit=10)
        ```

        gives you the first bunch of results quickly.

??? abstract "S.glean()"
    ```python
    S.glean(r)
    ```

    ???+ info "Description"
        A search result is just a tuple of nodes that correspond to your template, as
        indicated by `showPlan()`. Nodes give you access to all information that the
        corpus has about it.

        The `glean()` function is here to just give you a first impression quickly.  

    ??? info "r"
        Pass a raw result tuple `r`, and you get a string indicating where it occurs,
        in terms of sections, 
        and what text is associated with the results.

    ??? example "Inspecting results"
        ```python
        for result in S.fetch(limit=10):
            print(S.glean(result))
        ```

        is a handy way to get an impression of the first bunch of results.

    ??? hint "Universal"
        This function works on all tuples of nodes, whether they have been
        obtained by search or not.

    ??? hint "More ways of showing results"
        If you work in one of the [corpora](../About/Corpora.md) for which there is a TF app,
        you will be provided with more powerful methods `show()` and `table()`
        to display your results.

## Convert

### MQL

??? info "Data interchange with MQL"
    You can interchange with MQL data. Text-Fabric can read and write MQL dumps. An
    MQL dump is a text file, like an SQL dump. It contains the instructions to
    create and fill a complete database.

??? abstract "TF.exportMQL()"
    ```python
    TF.exportMQL(dbName, dirName)
    ```

    ???+ info "Description"
        Exports the complete TF dataset into single MQL database.

    ??? info "dirName, dbName"
        The exported file will be written to `dirName/dbName.mql`. If `dirName` starts
        with `~`, the `~` will be expanded to your home directory. Likewise, `..` will
        be expanded to the parent of the current directory, and `.` to the current
        directory, both only at the start of `dirName`.

    ??? explanation "Correspondence TF and MQL"
        The resulting MQL database has the following properties with respect to the
        Text-Fabric dataset it comes from:

        *   the TF *slots* correspond exactly with the MQL *monads* and have the same
            numbers; provided the monad numbers in the MQL dump are consecutive. In MQL
            this is not obligatory. Even if there gaps in the monads sequence, we will
            fill the holes during conversion, so the slots are tightly consecutive;
        *   the TF *nodes* correspond exactly with the MQL *objects* and have the same
            numbers

    ??? note "Node features in MQL"
        The values of TF features are of two types, `int` and `str`, and they translate
        to corresponding MQL types `integer` and `string`. The actual values do not
        undergo any transformation.

        That means that in MQL queries, you use quotes if the feature is a string feature.
        Only if the feature is a number feature, you may omit the quotes:

        ```
        [word sp='verb']
        [verse chapter=1 and verse=1]
        ```

    ??? note "Enumeration types"
        It is attractive to use eumeration types for the values of a feature, whereever
        possible, because then you can query those features in MQL with `IN` and without
        quotes:

        ```
        [chapter book IN (Genesis, Exodus)]
        ```

        We will generate enumerations for eligible features.

        Integer values can already be queried like this, even if they are not part of an
        enumeration. So we restrict ourselves to node features with string values. We
        put the following extra restrictions:

        *   the number of distinct values is less than 1000
        *   all values must be legal C names, in practice: starting with a letter,
            followed by letters, digits, or `_`. The letters can only be plain ASCII
            letters, uppercase and lowercase.

        Features that comply with these restrictions will get an enumeration type.
        Currently, we provide no ways to configure this in more detail.

        ??? note "Merged enumeration types"
            Instead of creating separate enumeration types for individual features,
            we collect all enumerated values for all those features into one
            big enumeration type.

            The reason is that MQL considers equal values in different types as
            distinct values. If we had separate types, we could never compare
            values for different features.

    ??? caution "Values of edge features are ignored"
        There is no place for edge values in
        MQL. There is only one concept of feature in MQL: object features,
        which are node features.
        But TF edges without values can be seen as node features: nodes are
        mapped onto sets of nodes to which the edges go. And that notion is supported by
        MQL:
        edge features are translated into MQL features of type `LIST OF id_d`,
        i.e. lists of object identifiers.

    ??? caution "Legal names in MQL"
        MQL names for databases, object types and features must be valid C identifiers
        (yes, the computer language C). The requirements are:

        *   start with a letter (ASCII, upper-case or lower-case)
        *   follow by any sequence of ASCII upper/lower-case letters or digits or
            underscores (`_`)
        *   avoid being a reserved word in the C language

        So, we have to change names coming from TF if they are invalid in MQL. We do
        that by replacing illegal characters by `_`, and, if the result does not start
        with a letter, we prepend an `x`. We do not check whether the name is a reserved
        C word.

        With these provisos:

        *   the given `dbName` correspond to the MQL *database name*
        *   the TF *otypes* correspond to the MQL *objects*
        *   the TF *features* correspond to the MQL *features*

    ??? hint "File size"
        The MQL export is usually quite massive (500 MB for the Hebrew Bible).
        It can be compressed greatly, especially by the program `bzip2`.

    ??? caution "Exisiting database"
        If you try to import an MQL file in Emdros, and there exists already a file or
        directory with the same name as the MQL database, your import will fail
        spectacularly. So do not do that. A good way to prevent it is:

        *   export the MQL to outside your `text-fabric-data` directory, e.g. to
            `~/Downloads`;
        *   before importing the MQL file, delete the previous copy;

        ??? example "Delete existing copy"
            ```sh
            cd ~/Downloads
            rm dataset ; mql -b 3 < dataset.mql
            ```

??? abstract "TF.importMQL()"
    ```python
    TF.importMQL(mqlFile, slotType=None, otext=None, meta=None)
    ```

    ???+ info "Description"
        Converts an MQL database dump to a Text-Fabric dataset.

    ??? hint "Destination directory"
        It is recommended to call this `importMQL` on a TF instance called with

        ```python
        locations=targetDir, modules=''
        ```

        Then the resulting features will be written in the targetDir.

        In fact, the rules are exactly the same as for `TF.save()`.

    ??? info "slotType"
        You have to tell which object type in the MQL file acts as the slot type,
        because TF cannot see that on its own.

    ??? info "otext"
        You can pass the information about sections and text formats as the parameter
        `otext`. This info will end up in the `otext.tf` feature. Pass it as a
        dictionary of keys and values, like so:

        ```python
        otext = {
            'fmt:text-trans-plain': '{glyphs}{trailer}',
            'sectionFeatures': 'book,chapter,verse',
        }
        ```

    ??? info "meta"
        Likewise, you can add a dictionary of keys and values that will added to the
        metadata of all features. Handy to add provenance data here:

        ```python
        meta = dict(
            dataset='DLC',
            datasetName='Digital Language Corpus',
            author="That 's me",
        )
        ```

## Lib

Various functions that have a function that is not directly tied to a class.
These functions are available in `tf.lib`, so in order to use function `fff`, say

```python
from tf.lib import fff
```

### Sets

??? abstract "writeSets()"
    ```python
    writeSets(sets, dest)
    ```

    Writes a dictionary of named sets to file.
    The dictionary will be written as a gzipped, pickled data structure.

    Intended use: if you have constructed custom node sets that you want to use
    in search templates that run in the TF browser.

    ??? info "sets"
        A dictionary in which the keys are names for the values, which are sets
        of nodes.

    ??? info "dest"
        A file path. You may use `~` to refer to your home directory.
        The result will be written from this file.

    ??? info "Returns"
        `True` if all went well, `False` otherwise.

??? abstract "readSets(source)"
    ```python
    sets = readSets(source)
    ```

    Reads a dictionary of named sets from a file specified by `source`.

    This is used by the TF browser, when the user has passed a `--sets=fileName`
    argument to it.

    ??? info "source"
        A file path. You may use `~` to refer to your home directory.
        This file must contain a gzipped, pickled data structure.

    ??? info "Returns"
        The data structure contained in the file if all went well, `False` otherwise.

