# Locality

??? explanation "Local navigation"
    Here are the methods by which you can navigate easily from a node to its
    neighbours: parents and children, previous and next siblings.

???+ info "L"
    The Locality API is exposed as `L` or `Locality`.

??? hint "otype parameter"
    In all of the following `L`-functions, if the `otype` parameter is passed,
    the result is filtered and
    only nodes with `otype=nodeType` or `otype in nodeTypes` are retained.
    
    `otype` can be a string (a single node type)  or a (frozen)set of node types.

??? caution "Results of the `L.` functions are tuples, not single nodes"
      Even if an `L`-function returns a single node, it is packed in a *tuple*.
      So to get the node itself, you have to dereference the tuple:

      ```python
      L.u(node)[0]
      ```

??? abstract "L.i()"
    ```python
    L.u(node, otype=nodeType(s))
    ```

    ???+ info "Description"
        Produces an ordered tuple of **intersecting** nodes, i.e. nodes that have slots in
        common with `node`.

    ??? info "node"
        The node whose intersectors will be delivered.
        The result never includes `node` itself.
        But other nodes linked to the same set of slots as `node` may count as intersector nodes. 
        Slots themselves can be intersectors.

??? abstract "L.u()"
    ```python
    L.u(node, otype=nodeType(s))
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
    L.d(node, otype=nodeType(s))
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
    L.n(node, otype=nodeType(s))
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
    L.p(node, otype=nodeType(s))
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
    *level*. See [levels](#sections).

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

