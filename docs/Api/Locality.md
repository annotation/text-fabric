# Locality

[apidocs](../apidocs/html/tf/core/locality.html)

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

