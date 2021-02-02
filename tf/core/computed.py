"""
# Precomputed data components

In order to make the API work, Text-Fabric prepares some data and saves it in
quick-load format. Most of this data are the features, but there is some extra
data needed for the special functions of the `tf.core.data.WARP` features and the
`tf.core.locality.Locality` API.

Normally, you do not use this data, but since it is there, it might be valuable,
so we have made it accessible in the `tf.core.computed.Computeds`-api.

!!! explanation "Pre-computed data storage"
    Pre-computed data is stored in cache directories in a directory `.tf`
    inside the directory where the `otype` feature is encountered.

    After precomputation the result is pickled and gzipped and written to a
    `.tfx` file with the same name as the name of the feature.
    This is done for nromal features and pre-computed features likewise.

    After version 7.7.7 version the memory footprint of some precomputed features
    has been reduced. Because the precomputed features on disk are exact replicas
    of the precomputed features in RAM, older precomputed data does not work with
    versions of TF after 7.7.7.

    But from that version onwards, there is a parameter,
    `tf.parameters.PACK_VERSION` to detect incompatibilities.
"""


class Computeds(object):
    pass


class Computed(object):
    """Provides access to precomputed data.

    For component `ccc` it is the result of `C.ccc` or `Cs('ccc')`.
    """

    def __init__(self, api, data):
        self.api = api
        self.data = data
