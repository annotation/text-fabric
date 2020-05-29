# Display

Where the advanced API really shines is in displaying nodes.
There are basically two ways of displaying a node:

* *plain*: just the associated text of a node, or if that would be too much,
  an identifying label of that node (e.g. for books, chapters and lexemes).
* *pretty*: a display of the internal structure of the textual object a node
  stands for. That structure is adorned with relevant feature values.

These display methods are available for nodes, tuples of nodes, and iterables
of tuples of nodes (think: query results).
The names of these methods are

* `plain`, `plainTuple`, and `table`;
* `pretty`, `prettyTuple` and `show`.

In plain and pretty displays, certain parts can be *highlighted*, which is
good for displaying query results where the parts that correspond directly to the
search template are highlighted.

## Display parameters

There is a bunch of parameters that govern how the display functions arrive at their
results. You can pass them as optional arguments to these functions,
or you can set up them in advance, and reset them to their original state
when you are done.

All calls to the display functions look for the values for these parameters in the
following order:

* optional parameters passed directly to the function,
* values as set up by previous calls to `displaySetup()`,
* corpus dependent default values configured by the advanced API.

See `tf.applib.displaysettings` for a list of display parameters.

## Display algorithm

Both `pretty` and `plain` depend on an algorithm to *unravel* nodes to other nodes.

For example, when we display a sentence, we also display its clauses and phrases and words,
which all correspond to nodes.

Here is a top-level sketchy description of the *unravel* algorithm.

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

The unravel algorithm takes a sequence of chunks and
unravels them to another sequence of chunks.

See `tf.applib.displaylib.chunkify`.

### Intersecting nodes

Nodes or chunks whose slot sets intersect, are intersecting nodes, except the node itself.

### Canonical order

Before we feed chunks to the display, we sort them in *canonical order*, based on their
slots and node type.

*   Chunks with earlier first slots come before chunks with later first slots.
*   For chunks that have the same first slots: look at the slots they do *not* have in common.
    The chunk with the earlier such slot comes before the chunk with the later such slot.
*   For chunks that have the same sets of slots: look at their node type.
    Different node types: the chunk with the higher ranked
    node type comes before the one with the lower ranked node type.
*   For chunks that have the same sets of slots and the same node type:
    the chunk whose node (as integer) comes before the node of the other chunk, comes before.

See `tf.core.nodes`.

### Substrate

Sometimes we do not want to display a node completely, but restricted to a set of slots.
We call this set the *substrate*.

It typically happens in a node is contained in a parent node that has multiple chunks.
The child node should be displayed in parts: in each chunk of the parent node, the child node
should be displayed in as far its slots are contained in that chunk.

### Output

When we unravel a list of chunks, we produce output for the chunks, one by one.
For each chunk, the output consists of a contribution by the node of the chunk, followed
by the result of unraveling the chunk into related chunks and collecting their output.

### Called and done

During the process of unraveling chunks, we may encounter chunks that we have met before,
and may or may not have produced their output already.

More precisely, for each node we keep track of the chunks related to that node:

**called**
:   maps each node to the set of its chunks that are being processed but have not finished yet

**done**
:   the set of slots that already occur in the output.

### All pieces together

In order to display node `n` the algorithm works as follows:

1.  Set the **substrate** to all slots of the node.
2.  Chunkify the node in a **canonically sorted** list of its chunks
3.  Display the list of these chunks on this substrate.

Now we describe recursively how to display a list of chunks on a substrate.

Set **done** to the empty set, **called** to the empty mapping.

Work through the chunks in that order, for each chunk:

1.  Take the intersection of the slots of the chunk with the substrate.
    This will be the new slot set of this chunk.
2.  If the intersection is empty: skip this chunk.
3.  If the node of the chunk is already in **called**, mapped to a slot set
    that encompasses the slot set of this chunk: skip this chunk.
4.  If all the slots of the chunk are already in **done**: skip this chunk.
5.  Add the chunk to **called**, mapped to its slot set.
6.  Produce output for the node of the chunk.
7.  Unravel the chunk: get the all *intersecting* *descendant* nodes of the node of the chunk.
8.  **chunkify** these nodes into a canonically order list of chunks.
7.  Recursively work through the descendant chunks but on a different substrate:
    the slots of the (parent) chunk minus the slots already done.
8.  Add all the slots of the chunk to the **done** set.
9.  Process the new chunk.

### Notes

When nodes represent textual objects that intersect with each other, it is possible that
slots are contained in several of such objects.
The algorithm takes care that they will not be output twice
(by means of **called** and **done**).

When textual objects have gaps, it is wrong to process each object completely before
going to the next one. Because then the slots will be displayed in the wrong order.

By chunkifying and sorting the chunks in canonical order, this is prevented.
