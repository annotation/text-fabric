# Core API of TF

This API deals with the basic TF data model: a graph of nodes and edges,
annotated by features.

The core API consists of

* `N`: see `api.Api.N` (walk through nodes)
* `F`: see `api.NodeFeature` (retrieve feature values for nodes)
* `E`: see `api.EdgeFeature` (retrieve feature values for edges)
* `L`: see `locality.Locality` (move between levels)
* `T`: see `text.Text` (get the text)
* `S`: see `tf.search.search` (search by templates)

plus some additional methods.
