"""
# Fabric

The main class that works the core API is `tf.fabric.Fabric`.

It is responsible for feature data loading and saving.

!!! note "Tutorial"
    The tutorials for specific [annotated corpora](https://github.com/annotation)
    put the Text-Fabric API on show for vastly different corpora.

!!! note "Generic API versus apps"
    This is the API of Text-Fabric in general.
    Text-Fabric has no baked in knowledge of particular corpora.

    However, Text-Fabric comes with several *apps* that make working
    with specific `tf.about.corpora` easier.
    Such an app may be as simple as a *config.yaml* file, even an empty one.
    The extra functions of those apps
    are available through the advanced API: `A`, see `tf.app`.

Fabric has built-in volume support: it can load volumes of a work and it can
collect volumes into a new work.

Fabric is an extension of `tf.core.fabric` where volume support is added.
"""

import os

from .parameters import LOCATIONS, LOCAL, OWORK
from .core.helpers import itemize, setDir, expandDir, unexpanduser
from .core.fabric import FabricCore
from .core.timestamp import Timestamp
from .volumes import extract, collect


class Fabric(FabricCore):
    """Initialize the core API for a corpus.

    !!! note "Implementation"
        Fabric is implemented as a subclass of `tf.core.fabric.FabricCore`

    See `tf.core.fabric.FabricCore for most of the functionality.
    Here we document the volume support only.

    Parameters
    ----------
    volume: string, optional `None`
        If absent or None, or the empty string: the whole corpus will be loaded.
        Otherwise, if the volume exists, it will be loaded instead of the whole corpus.
        If the volume does not exist (after the creation of volumes based on
        the `volumes` parameter), an error will be generated.

    When determining whether the volume exists, only the first members of `locations`
    and `modules` will be used.
    There the volumes reside under a directory `_local`.
    You may want to add `_local` to your `.gitignore`, so that volumes generated
    in a GitHub directory will not be pushed.
    """

    def __init__(
        self,
        locations=None,
        modules=None,
        silent=False,
        volume=None,
    ):
        self.volume = volume

        if modules is None:
            module = [""]
        elif type(modules) is str:
            module = [x.strip() for x in itemize(modules, "\n")]
        else:
            module = modules
        module = module[0] if module else ""
        module = module.strip("/").strip("\\")

        if locations is None:
            location = LOCATIONS if LOCATIONS else [""]
        elif type(locations) is str:
            location = [x.strip() for x in itemize(locations, "\n")]
        else:
            location = locations
        location = location[0] if location else ""
        location = location.rstrip("/").rstrip("\\")

        setDir(self)
        location = expandDir(self, location)
        sep = "/" if location and module else ""

        location = f"{location}{sep}{module}"
        sep = "/" if location else ""
        volumeBase = f"{location}{sep}{LOCAL}"
        self.volumeBase = volumeBase

        if volume:
            volumeLoc = f"{volumeBase}/{volume}"
            self.volumeLoc = volumeLoc
            locations = volumeLoc
            modules = [""]
            if not os.path.exists(locations):
                TM = Timestamp()
                TM.error(f"Volume {volume} not found under {unexpanduser(volumeLoc)}")

        super().__init__(locations=locations, modules=modules, silent=silent)

    def extract(self, volumes, byTitle=True, silent=False, overwrite=None):
        """Extract volumes from the currently loaded work.

        This functions is only provided if the dataset is a work,
        i.e. it is loaded as a whole.
        When a single volume of a work is loaded, there is no `extract` method.

        See `tf.volumes.extract` and note that parameters
        `workLocation`, `volumesLocation`, `api`
        will be supplied automatically.
        """

        volume = self.volume
        volumeBase = self.volumeBase
        api = self.api

        if volume:
            self.error("Cannot extract volumes from a single volume of a work")
            return

        return extract(
            None,
            volumeBase,
            volumes,
            byTitle=byTitle,
            silent=silent,
            api=api,
            overwrite=overwrite,
            checkOnly=False,
        )

    def collect(
        self,
        volumes,
        volumeType=None,
        volumeFeature=None,
        mergeTypes=None,
        featureMeta=None,
        silent=False,
        overwrite=None,
    ):
        """Creates a work out of a number of volumes.

        See `tf.volumes.collect` and note that parameter
        `workLocation`
        will be supplied automatically.
        """

        volumeBase = self.volumeBase

        return collect(
            volumes,
            volumeBase,
            volumeType=volumeType,
            volumeFeature=volumeFeature,
            mergeTypes=mergeTypes,
            featureMeta=featureMeta,
            silent=silent,
            overwrite=overwrite,
        )
