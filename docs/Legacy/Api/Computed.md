# Computed data

!!! explanation "Pre-computing"
    In order to make the API work, Text-Fabric prepares some data and saves it in
    quick-load format. Most of this data are the features, but there is some extra
    data needed for the special functions of the WARP features and the L-API.

    Normally, you do not use this data, but since it is there, it might be valuable,
    so we have made it accessible in the `C`-api, which we document here.

!!! explanation "Pre-computed data storage"
    Pre-computed data is stored in cache directories in a directory `.tf` inside the
    directory where the `otype` feature is encountered.

    After precomputation the result is pickled and gzipped and written to a `.tfx` file
    with the same name as the name of the feature. This is done for nromal features
    and pre-computed features likewise.

    After version 7.7.7 version the memory footprint of some precomputed features
    has been reduced. Because the precomputed features on disk are exact replicas
    of the precomputed features in RAM, older precomputed data does not work with
    versions of TF after 7.7.7. 

    But from that version onwards, there is a parameter, `PACK_VERSION` that indicates
    the version of the packing algorithm. Precomputed data is not stored directly
    in the `.tf` cache directory, but in the `.tf/{PACK_VERSION}` directory.

    There is a  utility,
    [`clean()`](Misc.md#clearing-the-cache) that removes all outdated generated data from
    your `~/text-fabric-data` directory, and optionally from your
    `~/github` directory.

!!! abstract "Call() aka AllComputeds()"
    ```python
    Call()
    AllComputeds()
    ```

    !!! info "Description"
        Returns a sorted list of all usable, loaded computed data names.

!!! abstract "C.levels.data"
    !!! info "Description"
        A sorted list of object types plus basic information about them.

        Each entry in the list has the shape

        ```python
            (otype, averageSlots, minNode, maxNode)
        ```

        where `otype` is the name of the node type, `averageSlots` the average size of
        objects in this type, measured in slots (usually words). `minNode` is the first
        node of this type, `maxNode` the last, and the nodes of this node type are
        exactly the nodes between these two values (including).

    !!! explanation "Level computation and customization"
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

!!! abstract "C.order.data"
    !!! info "Description"
        An **array** of all nodes in the correct order. This is the
        order in which `N()` alias `Node()` traverses all nodes.

    !!! explanation "Rationale"
        To order all nodes in the [canonical ordering](#sorting-nodes) is quite a bit of
        work, and we need this ordering all the time.

!!! abstract "C.rank.data"
    !!! info "Description"
        An **array** of all indices of all nodes in the canonical order
        array. It can be viewed as its inverse.

    !!! explanation "Order arbitrary node sets"
        I we want to order a set of nodes in the canonical ordering, we need to know
        which position each node takes in the canonical order, in other words, at what
        index we find it in the [`C.order.data`](#order) array.

!!! abstract "C.levUp.data and C.levDown.data"
    !!! info "Description"
        These tables feed the `L.d()` and `L.u()` functions.

    !!! caution "Use with care"
        They consist of a fair amount of megabytes, so they are heavily optimized.
        It is not advisable to use them directly, it is far better to use the `L` functions.

        Only when every bit of performance waste has to be squeezed out, this raw data
        might be a deal.

!!! abstract "C.boundary.data"
    !!! info "Description"
        These tables feed the `L.n()` and `L.p()` functions.
        It is a tuple consisting of `firstSlots` and `lastSlots`.
        They are indexes for the first slot
        and last slot of nodes.
        
    !!! explanation "Slot index"
        For each slot, `firstSlot` gives all nodes (except
        slots) that start at that slot, and `lastSlot` gives all nodes (except slots)
        that end at that slot.
        Both `firstSlot` and `lastSlot` are tuples, and the
        information for node `n` can be found at position `n-MaxSlot-1`.

!!! abstract "C.sections.data"
    !!! info "Description"
        Let us assume for the sake of clarity, that the node type of section level 1 is
        `book`, that of level 2 is `chapter`, and that of level 3 is `verse`. And
        suppose that we have features, named `bookHeading`, `chapterHeading`, and
        `verseHeading` that give the names or numbers of these.

        !!! caution "Custom names"
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

    !!! explanation "Supporting the `T`-Api"
        The `T`-api is good in mapping nodes unto sections, such as books, chapters,
        verses and back. It knows how many chapters each book has, and how many verses
        each chapter.

        The `T` api is meant to make your life easier when you have to find passage
        labels by nodes or vice versa. That is why you probably never need to consult
        the underlying data. But you can! That data is stored in

