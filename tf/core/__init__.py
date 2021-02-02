"""
# Core API of TF

This API deals with the basic TF data model: a graph of nodes and edges,
annotated by features.

The core API consists of

* `N`: see `nodes.Nodes` (walk through nodes)
* `F`: see `nodefeature.NodeFeature` (retrieve feature values for nodes)
* `E`: see `edgefeature.EdgeFeature` (retrieve feature values for edges)
* `L`: see `locality.Locality` (move between levels)
* `T`: see `text.Text` (get the text)
* `S`: see `tf.search.search` (search by templates)

plus some additional methods.
"""
