# Render

Rendering is the process of generating HTML for a node, taking into account
display options (`tf.advanced.options`) and app settings (`tf.advanced.settings`).

It is organized as an *unravel* step (`tf.advanced.unravel`),
that generates a tree of node fragments
followed by an HTML generating step, that generates HTML for a tree in a recursive way.

The *unravel* step retrieves all relevant settings and options and stores them
in the tree in such a way that the essential information for rendering a subtree
is readily available at the top of that subtree.

## Information shielding

The recursive render step does not have to consult the `app` object anymore,
because all information it needs from the `app` object is stored in the tree,
and all methods that need to be invoked on the `app` object are also accessible
directly from an attribute in the tree.
