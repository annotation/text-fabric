"""
# `Fabric`

The main class that works the core API is `tf.fabric.Fabric`.

It is responsible for feature data loading and saving.

!!! note "Tutorial"
    The tutorials for specific annotated corpora (see `tf.about.corpora`)
    put the TF API on show for vastly different corpora.

!!! note "Generic API versus apps"
    This is the API of TF in general.
    TF has no baked in knowledge of particular corpora.

    However, TF comes with several *apps* that make working
    with specific `tf.about.corpora` easier.
    Such an app may be as simple as a *config.yaml* file, even an empty one.
    The extra functions of those apps
    are available through the advanced API: `A`, see `tf.app`.

`Fabric` has built-in volume support: it can load volumes of a work and it can
collect volumes into a new work.

`Fabric` is an extension of `tf.core.fabric` where volume support is added.
"""

import types

from .parameters import OTYPE
from .core.helpers import itemize
from .core.fabric import FabricCore
from .core.files import (
    LOCATIONS,
    LOCAL,
    normpath,
    unexpanduser as ux,
    setDir,
    expandDir,
    dirExists,
)
from .core.timestamp import Timestamp, SILENT_D, silentConvert
from .volumes import extract, collect, getVolumes
from .convert.mql import exportMQL


class Fabric(FabricCore):
    """Initialize the core API for a corpus.

    !!! note "Implementation"
        `Fabric` is implemented as a subclass of `tf.core.fabric.FabricCore`

    See `tf.core.fabric.FabricCore` for most of the functionality.
    Here we document the volume support only.

    Parameters
    ----------
    collection: string, optional None
        If the collection exists, it will be loaded instead of the whole corpus.
        If the collection does not exist an error will be generated.

    volume: string, optional None
        If the volume exists, it will be loaded instead of the whole corpus.
        If the volume does not exist an error will be generated.

    When determining whether the volume exists, only the first members of `locations`
    and `modules` will be used.
    There the volumes reside under a directory `_local`.
    You may want to add `_local` to your `.gitignore`, so that volumes generated
    in a back-end directory will not be pushed.

    !!! caution "Volumes and collections"
        It is an error to load a volume as a collection and vice-versa

        You get a warning if you pass both a volume and a collection.
        The collection takes precedence, and the volume is ignored in that case.
    """

    def __init__(
        self,
        locations=None,
        modules=None,
        silent=SILENT_D,
        volume=None,
        collection=None,
        **kwargs,
    ):

        if modules is None:
            module = [""]
        elif type(modules) is str:
            module = [normpath(x.strip()) for x in itemize(modules, "\n")]
        else:
            module = [normpath(str(x)) for x in modules]
        module = module[0] if module else ""
        module = module.strip("/")

        if locations is None:
            location = LOCATIONS if LOCATIONS else [""]
        elif type(locations) is str:
            location = [normpath(x.strip()) for x in itemize(locations, "\n")]
        else:
            location = [normpath(str(x)) for x in locations]
        location = location[0] if location else ""
        location = location.rstrip("/")

        setDir(self)
        location = expandDir(self, location)
        sep = "/" if location and module else ""

        location = f"{location}{sep}{module}"
        sep = "/" if location else ""
        volumeBase = f"{location}{sep}{LOCAL}"
        collectionBase = f"{location}{sep}{LOCAL}"

        TM = Timestamp(silent=silent)

        if collection:
            collectionLoc = f"{collectionBase}/{collection}"
            self.collectionLoc = collectionLoc
            locations = collectionLoc
            modules = [""]
            if not dirExists(locations):
                TM = Timestamp(silent=silent)
                TM.error(f"Collection {collection} not found under {ux(collectionLoc)}")
        elif volume:
            volumeLoc = f"{volumeBase}/{volume}"
            self.volumeLoc = volumeLoc
            locations = volumeLoc
            modules = [""]
            if not dirExists(locations):
                TM.error(f"Volume {volume} not found under {ux(volumeLoc)}")

        if collection and volume:
            TM.warning(
                f"Both collection={collection} and volume={volume} specified.", tm=False
            )
            TM.warning("Ignoring the volume", tm=False)

        super().__init__(locations=locations, modules=modules, silent=silent, **kwargs)
        self.volumeBase = volumeBase
        self.collectionBase = collectionBase
        self.collection = collection
        self.volume = None if collection else volume
        self.exportMQL = types.MethodType(exportMQL, self)

    def _makeApi(self):
        api = super()._makeApi()

        if self.collection:
            self.collectionInfo = self.features[OTYPE].metaData.get("collection", None)
            if self.collectionInfo is None:
                self.error("This is not a collection!")
                self.good = False
                return None

        elif self.volume:
            self.volumeInfo = self.features[OTYPE].metaData.get("volume", None)
            if self.volumeInfo is None:
                self.error("This is not a volume!")
                self.good = False
                return None
        return api

    def getVolumes(self):
        """Lists available volumes within the dataset.

        See `tf.volumes.extract.getVolumes`.
        """

        volumeBase = self.volumeBase
        return getVolumes(volumeBase)

    def extract(
        self, volumes=True, byTitle=True, silent=SILENT_D, overwrite=None, show=False
    ):
        """Extract volumes from the currently loaded work.

        This function is only provided if the dataset is a work,
        i.e. it is loaded as a whole.
        When a single volume of a work is loaded, there is no `extract` method.

        See `tf.volumes.extract` and note that parameters
        `workLocation`, `volumesLocation`, `api`
        will be supplied automatically.
        """

        silent = silentConvert(silent)
        volume = self.volume
        volumeBase = self.volumeBase
        api = self.api

        if volume:
            self.error("Cannot extract volumes from a single volume of a work")
            return

        return extract(
            None,
            volumeBase,
            volumes=volumes,
            byTitle=byTitle,
            silent=silent,
            api=api,
            overwrite=overwrite,
            checkOnly=False,
            show=show,
        )

    def collect(
        self,
        volumes,
        collection,
        volumeType=None,
        volumeFeature=None,
        mergeTypes=None,
        featureMeta=None,
        silent=SILENT_D,
        overwrite=None,
    ):
        """Creates a work out of a number of volumes.

        Parameters
        ----------

        volumes: tuple
            Just the names of the volumes that you want to collect.

        collection: string
            The name of the new collection

        See `tf.volumes.collect` for the other parameters and note that parameter
        `workLocation` will be supplied automatically from `collection`.
        """

        volumeBase = self.volumeBase

        return collect(
            tuple(f"{volumeBase}/{name}" for name in volumes),
            f"{volumeBase}/{collection}",
            volumeType=volumeType,
            volumeFeature=volumeFeature,
            mergeTypes=mergeTypes,
            featureMeta=featureMeta,
            silent=silent,
            overwrite=overwrite,
        )
