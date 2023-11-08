"""
# Pre-computed data components

In order to make the API work, TF prepares some data and saves it in
quick-load format. Most of this data are the features, but there is some extra
data needed for the special functions of the `tf.parameters.WARP` features and the
`tf.core.locality.Locality` API.

Normally, you do not use this data, but since it is there, it might be valuable,
so we have made it accessible in the `tf.core.computed.Computeds`-API.

!!! explanation "Pre-computed data storage"
    Pre-computed data is stored in cache directories in a directory `.tf`
    inside the directory where the `otype` feature is encountered.

    After pre-computation the result is `pickled` and `gzipped` and written to a
    `.tfx` file with the same name as the name of the feature.
    This is done for normal features and pre-computed features likewise.

    After version 7.7.7 version the memory footprint of some pre-computed features
    has been reduced. Because the pre-computed features on disk are exact replicas
    of the pre-computed features in RAM, older pre-computed data does not work with
    versions of TF after 7.7.7.

    But from that version onward, there is a parameter,
    `tf.parameters.PACK_VERSION` to detect incompatibilities.
"""


class Computeds:
    pass


class Computed:
    """Provides access to pre-computed data.

    For component `ccc` it is the result of `C.ccc` or `Cs('ccc')`.
    """

    def __init__(self, api, data):
        self.api = api
        self.data = data
