"""
# Clean

From version 7.7.7 onward, TF uses a parameter `tf.parameters.PACK_VERSION`
to mark the stored pre-computed data.
Whenever there are incompatible changes in the packed data format, this
version number will be increased and TF will not attempt to load
the older pre-computed data.

The older data will not be removed, however.
Use the function `clean` to get rid of pre-computed data
that you no longer need.
"""

import sys
import re

from .parameters import PACK_VERSION
from .core.files import (
    expanduser as ex,
    unexpanduser as ux,
    backendRep,
    dirRemove,
    fileRemove,
    walkDir,
)


binRe = re.compile(r"/\.tf$")
binvRe = re.compile(r"/\.tf/([^/]+)$")


def out(msg):
    """Write to standard normal output immediately."""
    sys.stdout.write(ux(msg))
    sys.stdout.flush()


def err(msg):
    """Write to standard error output immediately."""
    sys.stderr.write(ux(msg))
    sys.stderr.flush()


def clean(tfd=True, backend=None, dry=True, specific=None, current=False):
    """Clean up older compressed `.tfx` files.

    Parameters
    ----------

    Removes all pre-computed data resulting from other `PACK_VERSION`
    than the one currently used by TF.

    You find the current pack version in
    `tf.parameters`

    tfd: boolean,  optional True
        By default, your `~/text-fabric-data` is traversed and cleaned,
        but if you pass `tfd=False` it will be skipped.
    backend: string, optional, `None`
        If None, only material in `text-fabric-data` will be cleaned.
        But you can also clean clones of GitHub / GitLab.

        To clean GitHub / GitLab clones, pass `github` / `gitlab`.

        To clean the clones from a specific GitLab server,
        pass its server name.
    specific: string, optional, `None`
        You can pass a specific directory here. The standard directories
        `~/github` and `~/text-fabric-data` will not be used, only
        the directory you pass here. `~` will be expanded to your home directory.
    current: boolean, optional, `False`
        If current=True, also the pre-computed results of the current version will
        be removed.
    dry: boolean, optional, `False`
        By default, nothing will be deleted, and you only get a list of
        what will be deleted if it were not a dry run.
        If you pass `dry=False` the delete actions will really be executed.
    """

    if specific is not None:
        bases = [ex(specific)]
    else:
        if backend is not None:
            backend = backendRep(backend, "norm")
            bases = [backendRep(backend, kind) for kind in ("cache", "clone")]

    for base in bases:
        for triple in walkDir(base):
            d = triple[0]
            if binRe.search(d):
                files = triple[2]
                if files:
                    err(f"{d} legacy: delete {len(files)} files ... ")
                    if dry:
                        err("dry\n")
                    else:
                        for f in files:
                            fileRemove(f"{d}/{f}")
                        err("done\n")
                    continue
            match = binvRe.search(d)
            if match:
                binv = match.group(1)
                if not current and binv == PACK_VERSION:
                    out(f"{d} version {binv}: keep\n")
                else:
                    files = triple[2]
                    err(f"{d} version {binv}: delete it and its {len(files)} files ...")
                    if dry:
                        err("dry\n")
                    else:
                        dirRemove(d)
                        err("done\n")
    if dry:
        sys.stdout.write("\n")
        sys.stderr.write("This was a dry run\n")
        sys.stderr.write("Say clean(dry=False) to perform the cleaning\n")
