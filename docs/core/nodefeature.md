Mappings from nodes to values.

Every node feature is logically a mapping from nodes to values,
string or integer.

A feature object gives you methods that you can pass a node and that returns
its value for that node.

It is easiest to think of all node features as a dictionary keyed by nodes.

However, some features have an optimized representation, and do not have
a dictionary underneath.

But you can still iterate over the data of a feature as if it were a
dictionary: `tf.core.nodefeature.NodeFeature.items`
