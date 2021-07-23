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

from .parameters import LOCATIONS, LOCAL
from .core.helpers import itemize, setDir, expandDir, unexpanduser
from .core.fabric import FabricCore

from ..volumes.extract import extract


class Fabric(FabricCore):
    """Initialize the core API for a corpus.

    !!! note "Implementation"
        Fabric is implemented as a subclass of `tf.core.fabric.FabricCore`

    See `tf.core.fabric.FabricCore for most of the functionality.
    Here we document the volume support only.

    Parameters
    ----------
    volume: string | tuple, optional
        If absent or None, the whole corpus will be loaded.
        Otherwise it is the name of a volume.
        If the volume exists, it will be loaded instead of the whole corpus.
        If it does not exist, it will be created based on `volumeSpec`.
     volumeSpec: tuple, optional, None
        If a volume needs to be created, this is the specification of that volume.
        It is a tuple of top-level section headings (see `byTitle`)
        that are to be comprised in the volume.
        If volumeSpec is absent or None, volumes are created for each individual
        top-level section.
    byTitle: boolean, optional False
        Whether the headings of the top-level sections are taken as their section
        titles or their sequence numbers.
    overwrite: boolean, optional `False`
        If True, overwrites volume directories by cleaning them first.
        If False, refuses to proceed if a volume directory already exists.

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
        volumeSpec=None,
        byTitle=True,
        overwrite=False,
    ):
        newVolumeLoc = None

        if volume:
            if modules is None:
                module = ""
            elif type(modules) is str:
                module = [x.strip() for x in itemize(modules, "\n")]
                module = module[0] if module else ""
            module = module.strip("/").strip("\\")

            if locations is None:
                location = LOCATIONS[0] if LOCATIONS else ""
            elif type(locations) is str:
                location = [x.strip() for x in itemize(locations, "\n")]
                location = location[0] if location else ""
            location = location.rstrip("/").rstrip("\\")

            setDir(self)
            location = expandDir(self, location)
            sep = "/" if location and module else ""

            location = f"{location}{sep}{module}"
            sep = "/" if location else ""
            location = f"{location}{sep}{LOCAL}/{volume}"

            if os.path.exists(location):
                locations = location
                modules = [""]
            else:
                newVolumeLoc = location

        super().__init__(locations=locations, silent=silent)

        if newVolumeLoc is not None:
            self.info(f"Generating new volume {volume}")
            api = self.loadAll(silent=silent)
            volumes = None if volumeSpec is None else dict(volume=volumeSpec)
            volumeInfo = extract(
                None,
                newVolumeLoc,
                byTitle=byTitle,
                volumes=volumes,
                silent=silent,
                api=api,
                overwrite=overwrite,
            )
            if volumeInfo:
                super().__init(locations=newVolumeLoc, silent=silent)
            else:
                self.error(
                    f"Could not create volume {volume} at {unexpanduser(newVolumeLoc)}"
                )
