# Unravel

Whatever we want to display, we have to display in HTML, which is basically a
hierarchically organized set of presentation elements.

But a node and its constellation of all relevant nodes that share slots with it,
does not have a hiererchical structure.

The unravel algorithm solves the problem of turning a node and its associated piece
of the textual graph into a tree of node fragments in such a way that the order
of the slots is preserved.

When nodes violate the hierarchy, they are *chunked* and *fragmentized* until the
resulting fragments can be *stacked* into a tree.

This tree of fragments can then be transformed in various kinds of HTML with rather
straightforward code, see `tf.applib.display.render`.

### Intersecting nodes

Nodes or chunks whose slot sets intersect, are intersecting nodes, except the node itself.

### Descendant types

Node types are ranked: node types whose nodes occupy more slots on average have a higher rank
than types whose nodes occupy less slots on average.
You can inspect the ranking of the types in your dataset by `tf.core.nodes.Nodes.otypeRank`.

For each node type, we collect the set of descendant types: the types with lower or equal rank.
So each type is its own descendant. But we prevent the slot type from being its own
descendant.

### Chunkify

Every node is linked to a set of slots. These slots may or may not form a contiguous chunk.
For the purposes of displaying nodes, we divide each node into maximal contiguous chunks.
Such a chunk is specified by a tuple `(n, slots)`, where `n` is the node (an integer),
and `slots` is a frozen set of slots (also integers).

### Fragmentize

Node chunks can be grouped by node types. The chunk boundaries of nodes of higher ranked
types are used to break up the chunks of nodes of lower ranked types.

We end up with a rather fine partition of all nodes in fragments, in such a way
that no fragment crosses the boundaries of enclosing fragments.

### Canonical order

Before we feed fragments to the display, we sort them in *canonical order*, based on their
slots and node type. The following criteria will be checked *in that order*:

*   Chunks have different begin slots: those with earlier first slots have precedence;
*   Chunks with nodes with higher ranked types have precedence;
*   Look at the slots the chunks do *not* have in common.
    The chunk with the earlier such slot has precedence.
*   Chunks with nodes that are smaller as integer have precedence.

See `tf.core.nodes`.

### Stacking

When we have a list of canonically ordered fragments, we can stack them into a tree.
Each new fragment is tried against the right-most branch of the tree under construction,
from bottom to top. 
If there is no place on that branch, a new right-most branch is started.

### Output

When we render a tree of fragments, we produce output for the fragments, one by one.
For each fragment, the output consists of a contribution by the node of the fragment.

### Notes

When nodes represent textual objects that intersect with each other, it is possible that
slots are contained in several of such objects.
The algorithm takes care that they will not be output multiple times.

When textual objects have gaps, it is wrong to process each object completely before
going to the next one. Because then the slots will be displayed in the wrong order.

By chunkifying, fragmentizing and sorting the chunks in canonical order, this is prevented.
