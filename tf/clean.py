"""
.. include:: ../docs/main/clean.md
"""

import sys
import os
import re
from shutil import rmtree

from .parameters import PACK_VERSION
from .core.helpers import unexpanduser as ux

TFD = "text-fabric-data"
GH = "github"

ROOTS = [TFD, GH]

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


def clean(tfd=True, gh=False, dry=True, specific=None, current=False):
    """Clean up older compressed .tfx files.

    Parameters
    ----------

    Removes all precomputed data resulting from other `PACK_VERSION`s
    than the one currently used by Text-Fabric.

    You find the current pack version in
    `tf.parameters`

    tfd: boolean,  optional `True`
        By default, your `~/text-fabric-data` is traversed and cleaned,
        but if you pass `tfd=False` it will be skipped.
    gh: boolean, optional, `False`
        By default, your `~/github` will be skipped,
        but if you pass `gh=True` it will be
        traversed and cleaned.
    specific: string, optional, `None`
        You can pass a specific directory here. The standard directories
        `~/github` and `~/text-fabric-data` will not be used, only
        the directory you pass here. `~` will be expanded to your home directory.
    current: boolean, optional, `False`
        If current=True, also the precomputed results of the current version will
        be removed.
    dry: boolean, optional, `False`
        By default, nothing will be deleted, and you only get a list of
        what will be deleted if it were not a dry run.
        If you pass `dry=False` the delete actions will really be executed.
    """

    if specific is not None:
        bases = [os.path.expanduser(specific)]
    else:
        for root in ROOTS:
            if root == TFD and not tfd or root == GH and not gh:
                out(f"skipped {root}\n")
                continue
            bases.append(os.path.expanduser(f"~/{root}"))

    for base in bases:
        for triple in os.walk(base):
            d = triple[0]
            if binRe.search(d):
                files = triple[2]
                if files:
                    err(f"{d} legacy: delete {len(files)} files ... ")
                    if dry:
                        err("dry\n")
                    else:
                        for f in files:
                            os.unlink(f"{d}/{f}")
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
                        rmtree(d)
                        err("done\n")
    if dry:
        sys.stdout.write("\n")
        sys.stderr.write("This was a dry run\n")
        sys.stderr.write("Say clean(dry=False) to perform the cleaning\n")
