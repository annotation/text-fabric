"""
# Parameters

Fixed values for the whole program.
"""

import sys
from zipfile import ZIP_DEFLATED


VERSION = '9.0.1'
"""Program version.

This value is under control of the update process, as run by
`build.py` in the top-level directory of the repo.
"""

NAME = "Text-Fabric"
"""The name of the game: this program.
"""

PACK_VERSION = "2"
"""Data serialization version.

Plain text feature files will be compressed to zipped, pickled datastructures
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

Text-Fabric offers and API to TF apps.
This is the version that the current Text-Fabric offers to its apps.

Apps require a version. The provided version and the required version must
match exactly in order to get a working system.

We do not aim for backward compatibility, since it is very easy to obtain a new version
of an app.

When Text-Fabric loads a TF app, it will check the api version that the app requires
against this version.

App requirement higher than TF API version
:   The user is advised to upgrade Text-Fabric, or, alternatively,
    select an older version of the app

App requirement lower than TF API version
:   The user is advised to obtain a newer version of the app, or alternatively,
    downgrade Text-Fabric
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
"""The names of the central features of TF data sets.

The features `otype` and `oslots` are crucial to every TF dataset.
Without them, a dataset is not a TF dataset, although it could still be a
TF data module.
"""

GZIP_LEVEL = 2
"""Compression level when compressing tf files."""

PICKLE_PROTOCOL = 4
"""Pickle protocol level when pickling tf files."""

ORG = "annotation"
"""GitHub organization name.

This is where the repo that contains Text-Fabric resides.
"""
REPO = "text-fabric"
"""GitHub repo name.

This is the name of the repo that contains Text-Fabric.
"""

RELATIVE = "tf"
"""Default relative path with a repo to the directory with tf files.
"""

URL_GH_API = "https://api.github.com/repos"
"""Url of the GitHub API for repos.

We can access GitHub repos by means of commands
on top of this url.
"""

URL_GH = "https://github.com"
"""Base url of GitHub."""

URL_NB = "https://nbviewer.jupyter.org/github"
"""Base url of NB-viewer for GitHub data."""

DOWNLOADS = "~/Downloads"
"""Local Downloads directory."""

GH_BASE = "~/github"
"""Local GitHub directory."""

EXPRESS_BASE = "~/text-fabric-data"
"""Local cache directory.

This is the place where the TF apps and TF feature files are cached locally.
"""

EXPRESS_SYNC = "__checkout__.txt"
"""Name of cache indicator file.

When a dataset is stored in the cache,
information about the GitHub release/commit is stored in a file
with this name.
"""

EXPRESS_SYNC_LEGACY = [
    "__release.txt",
    "__commit.txt",
]
"""Legacy names of cache indicator files."""

PROTOCOL = "http://"
HOST = "localhost"
PORT_BASE = 10000

URL_TFDOC = f"https://{ORG}.github.io/{REPO}/tf"
"""Base url of the online Text-Fabric documentation."""

DOI_DEFAULT = "no DOI"
DOI_URL_PREFIX = "https://doi.org"

DOI_TF = "10.5281/zenodo.592193"
"""DOI of an archived copy of this repo at Zenodo."""

APIREF = f"https://{ORG}.github.io/{REPO}/tf/cheatsheet.html"
"""Link to the Api docs of Text-Fabric."""

SEARCHREF = f"https://{ORG}.github.io/{REPO}/tf/about/searchusage.html"
"""Link to the Search docs of Text-Fabric."""

APP_URL = f"{URL_GH}/{ORG}"
"""Url of the GitHub location that contains all the TF apps."""

APP_NB_URL = f"{URL_NB}/{ORG}/tutorials/blob/master"
"""Url of the NB-viewer location that contains all the TF tutorials."""

APP_GITHUB = f"{GH_BASE}/annotation"
"""Local GitHub location that contains all the TF apps."""

APP_CONFIG = "config.yaml"
"""Name of the config file of a TF app."""

APP_CONFIG_OLD = "config.py"
"""Name of the config file of a an older, incompatible TF app."""

APP_CODE = "code"
"""Name of the top-level directory of a TF app."""

APP_DISPLAY = "static/display.css"
"""Relative path of the css file of a TF app."""

SERVER_DISPLAY_BASE = "/server/static"
"""Base of server css files."""

SERVER_DISPLAY = ("fonts.css", "display.css", "highlight.css")
"""Bunch of TF-generic css files."""

TEMP_DIR = "_temp"
"""Name of temporary directories.

!!! hint ".gitignore"
    Take care that these directories are ignored by git operations.
    Put a line

        _temp/

    in the `.gitignore` file.
"""

LOCATIONS = ["~/text-fabric-data"]
"""Default locations for tf data files.

If the `locations` parameter for the `tf.fabric.Fabric` call is omitted,
this is the default.
Text-Fabric will search all these directories as for `.tf` modules of files.
"""

LOCAL = "_local"
"""Name of auxiliary directories.

Examples where this is used:

*   volume support: inside a TF dataset, the directory `_local` contains
    volumes of that dataset
"""

ZIP_OPTIONS = dict(compression=ZIP_DEFLATED)
"""Options for zip when packing tf files.

This is for packaging collections of plain tf files into zip files
to be attached to releases on GitHub.

!!! caution "Not for .tfx files"
    This is not the zipping as done when .tf files are
    pickled and compressed to .tfx files.
"""

if sys.version_info[1] >= 7:
    ZIP_OPTIONS["compresslevel"] = 6

YARN_RATIO = 1.25
"""Performance parameter in the `tf.search.search` module."""

TRY_LIMIT_FROM = 40
"""Performance parameter in the `tf.search.search` module."""

TRY_LIMIT_TO = 40
"""Performance parameter in the `tf.search.search` module."""
