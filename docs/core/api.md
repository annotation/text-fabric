# The core API of TF.

It provides methods to navigate nodes and edges and lookup features.

Nodes are linked to subsets of slots, and there is a canonical ordering
on subsets of integers that is inherited by the nodes.

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

!!! note "first things first, big things first"
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
> https://books.google.nl/books?id=9ggOBRz1dO4C. The order as defined by
> Doedens corresponds to walking trees in post-order.

For a lot of processing, it is handy to have a the stack of embedding elements
available when working with an element. That is the advantage of pre-order over
post-order. It is very much like SAX parsing in the XML world.
