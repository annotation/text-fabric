"""
# Parameters

Fixed values for the whole program.
"""

import os
import sys
from zipfile import ZIP_DEFLATED


VERSION = '13.0.0'
"""Program version.

This value is under control of the update process, as run by
`build.py` in the top-level directory of the repo.
"""

NAME = "Text-Fabric"
"""The name of the game: this program.
"""

BANNER = f"This is {NAME} {VERSION}"

PACK_VERSION = "4"
"""Data serialization version.

Plain text feature files will be compressed to zipped, `pickled` data structures
that load must faster.

These methods evolve, sometimes in incompatible ways.
In those cases we bump this version number.
That will cause TF not to use compressed files that have been compressed by
older, incompatible methods.
Instead, TF will produce freshly compressed data files.

The compressed data files are stored in a directory `.tf/{PVN}/` next
to the original `tf`  files, where `{PVN}` is the package version number.

See Also
--------
tf.clean
"""

API_VERSION = 3
"""TF API version.

TF offers and API to TF apps.
This is the version that the current TF offers to its apps.

Apps require a version. The provided version and the required version must
match exactly in order to get a working system.

We do not aim for backward compatibility, since it is very easy to obtain a new version
of an app.

When TF loads a TF app, it will check the api version that the app requires
against this version.

App requirement higher than TF API version
:   The user is advised to upgrade TF, or, alternatively,
    select an older version of the app

App requirement lower than TF API version
:   The user is advised to obtain a newer version of the app, or alternatively,
    downgrade TF
"""

OTYPE = "otype"
"""Name of a central feature in a TF data set:
`otype` maps nodes to their types."""

OSLOTS = "oslots"
"""Name of a central feature in a TF data set:
`oslots` maps non-slot nodes to the sets of slots they occupy."""

OTEXT = "otext"
"""Name of a central (but optional) feature in a TF data set:
`otext` has configuration settings for sections, structure, and text formats."""

OVOLUME = "ovolume"
"""Name of the feature that maps nodes of a work dataset
to nodes in individual volumes in that work."""

OWORK = "owork"
"""Name of the feature that maps nodes in an individual volume of a work
to nodes in that work."""

OINTERF = "ointerfrom"
"""Name of the feature that stores the outgoing inter-volume edges
of a volume."""

OINTERT = "ointerto"
"""Name of the feature that stores the incoming inter-volume edges
of a volume."""

OMAP = "omap"
"""Name prefix of features with a node map from an older version to a newer version.

The full name of such a feature is `omap@`*oldversion*`-`*newversion*
"""

WARP = (OTYPE, OSLOTS, OTEXT)
"""The names of the central features of TF datasets.

The features `otype` and `oslots` are crucial to every TF dataset.
Without them, a dataset is not a TF dataset, although it could still be a
TF data module.
"""

GZIP_LEVEL = 2
"""Compression level when compressing TF files."""

PICKLE_PROTOCOL = 4
"""Pickle protocol level when pickling TF files."""

ORG = "annotation"
"""GitHub organization or GitLab group.

This is where the repo that contains TF resides.
"""
REPO = "text-fabric"
"""GitHub repo or GitLab project.

This is the name of the repo that contains TF.
"""

RELATIVE = "tf"
"""Default relative path with a repo to the directory with TF files.
"""

ON_IPAD = sys.platform == "darwin" and os.uname().machine.startswith("iP")

GH = "github"
"""Name of GitHub backend."""

GL = "gitlab"
"""Name of GitLab backend."""

URL_GH = "https://github.com"
"""Base URL of GitHub."""

URL_GH_API = "https://api.github.com"
"""Base URL of GitHub API."""

URL_GH_UPLOAD = "https://uploads.github.com"
"""Base URL of GitHub upload end point."""

URL_GL = "https://gitlab.com"
"""Base URL of GitLab."""

URL_GL_API = "https://api.gitlab.com"
"""Base URL of GitLab API."""

URL_GL_UPLOAD = "https://uploads.gitlab.com"
"""Base URL of GitLab upload end point."""

URL_NB = "https://nbviewer.jupyter.org"
"""Base URL of NB-viewer."""

URL_TF_DOCS = "https://annotation.github.io/text-fabric/tf"


PROTOCOL = "http://"
HOST = "localhost"  #
PORT_BASE = 10000


DOI_DEFAULT = "no DOI"
DOI_URL_PREFIX = "https://doi.org"

DOI_TF = "10.5281/zenodo.592193"
"""DOI of an archived copy of this repo at Zenodo."""

BRANCH_DEFAULT = "master"
"""Default branch in repositories, older value."""

BRANCH_DEFAULT_NEW = "main"
"""Default branch in repositories, modern value."""

ZIP_OPTIONS = dict(compression=ZIP_DEFLATED)
"""Options for zip when packing TF files.

This is for packaging collections of plain TF files into zip files
to be attached to releases on GitHub / GitLab.

!!! caution "Not for `.tfx` files"
    This is not the zipping as done when `.tf` files are
    `pickled` and compressed to `.tfx` files.
"""

if sys.version_info[0] > 3 or sys.version_info[0] == 3 and sys.version_info[1] >= 7:
    ZIP_OPTIONS["compresslevel"] = 6

YARN_RATIO = 1.25
"""Performance parameter in the `tf.search.search` module."""

TRY_LIMIT_FROM = 40
"""Performance parameter in the `tf.search.search` module."""

TRY_LIMIT_TO = 40
"""Performance parameter in the `tf.search.search` module."""

SEARCH_FAIL_FACTOR = 4
"""Limits fetching of search results to this times maxNode (corpus dependent)"""
