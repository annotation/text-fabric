"""
Produce links to Text-Fabric data and links from nodes to web resources.
"""

import re
import types


UNSUPPORTED = ""

pathRe = re.compile(
    r"^(.*/(?:github|text-fabric-data))/([^/]+)/([^/]+)/(.*)$", flags=re.I
)


def volumesApi(app):
    """Produce the volume support functions API.

    Volume support provides the functions `tf.volumes.extract` and
    `tf.volumes.collect` as methods on the app object.
    These operations will be called with the `_local` source/destination
    With these operations you can `extract()` and `collect()` volumes
    from the currently loaded work.
    The volumes in question reside in the directory `_local`
    under the main directory with feature files.

    Parameters
    ----------
    app: obj
        The high-level API object
    """

    app.extract = types.MethodType(extract, app)
    app.collect = types.MethodType(collect, app)

    TF = app.api.TF

    app.collectionInfo = None
    app.volumeInfo = None

    if TF.collection:
        app.collectionInfo = TF.collectionInfo
    else:
        if TF.volume:
            app.volumeInfo = TF.volumeInfo


def extract(app, *args, **kwargs):
    """Calls `tf.fabric.Fabric.extract` from an app object."""

    TF = app.api.TF

    return TF.extract(*args, **kwargs)


def collect(app, *args, **kwargs):
    """Calls `tf.fabric.Fabric.collect` from an app object."""
    TF = app.api.TF

    return TF.collect(*args, **kwargs)
