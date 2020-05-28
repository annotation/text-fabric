Mappings from edges to values.

Every edge feature is logically a mapping from pairs of nodes to values,
string or integer.

A feature object gives you methods that you can pass a node and that returns
its value for that node.

It is easiest to think of all edge features as a dictionary keyed by nodes.
The values are either sets or dictionaries.
If the value is a set, then the elements are the second node in the pair
and the value is `None`.
If the value is a dictionary, then the keys are the second node in the pair,
and the value is the value that the edge feature assigns to this pair.

However, some features have an optimized representation, and do not have
a dictionary underneath.

But you can still iterate over the data of a feature as if it were a
dictionary: `tf.core.edgefeature.EdgeFeature.items`
