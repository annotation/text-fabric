"""
Produce links to TF data and links from nodes to web resources.
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

    app.getVolumes = types.MethodType(getVolumes, app)

    if hasattr(app, "api"):
        app.extract = types.MethodType(extract, app)
        app.collect = types.MethodType(collect, app)

    TF = app.TF

    if TF is None:
        return

    app.collectionInfo = None
    app.volumeInfo = None

    if TF.collection:
        app.collectionInfo = TF.collectionInfo
    else:
        if TF.volume:
            app.volumeInfo = TF.volumeInfo


def getVolumes(app, *args, **kwargs):
    """Calls `tf.fabric.Fabric.getVolumes` from an app object.

    !!! hint "No need to load feature data"
        This function works even if no data has been loaded,
        so you can use it after

            A = use(xxx, loadData=False)
    """

    TF = app.TF

    if TF is None:
        return []

    return TF.getVolumes(*args, **kwargs)


def extract(app, *args, **kwargs):
    """Calls `tf.fabric.Fabric.extract` from an app object."""

    TF = app.TF

    if TF is None:
        return {}

    return TF.extract(*args, **kwargs)


def collect(app, *args, **kwargs):
    """Calls `tf.fabric.Fabric.collect` from an app object."""
    TF = app.TF

    if TF is None:
        return False

    return TF.collect(*args, **kwargs)
