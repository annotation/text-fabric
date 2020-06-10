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

See `tf.advanced.options` for a list of display parameters.

## Rendering

Both `pretty` and `plain` are implemented as a call to the
`tf.advanced.render.render` function.
