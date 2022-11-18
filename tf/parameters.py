"""
# Parameters

Fixed values for the whole program.
"""

import os
import sys
from zipfile import ZIP_DEFLATED


VERSION = '11.0.1'
"""Program version.

This value is under control of the update process, as run by
`build.py` in the top-level directory of the repo.
"""

NAME = "Text-Fabric"
"""The name of the game: this program.
"""

PACK_VERSION = "3"
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
"""GitHub organization or GitLab group.

This is where the repo that contains Text-Fabric resides.
"""
REPO = "text-fabric"
"""GitHub repo or GitLab project.

This is the name of the repo that contains Text-Fabric.
"""

RELATIVE = "tf"
"""Default relative path with a repo to the directory with tf files.
"""

HOME_DIR = os.path.expanduser("~")

GH = "github"
"""Name of GitHub backend."""

GL = "gitlab"
"""Name of GitLab backend."""

URL_GH = "https://github.com"
"""Base url of GitHub."""

URL_GL = "https://gitlab.com"
"""Base url of GitLab."""

URL_NB = "https://nbviewer.jupyter.org"
"""Base url of NB-viewer."""


def backendRep(be, kind, default=None):
    """Various backend dependent values.

    First of all, the backend value is
    normalized. Then related values are computed.

    Parameters
    ----------
    be: string or None
        the raw backend value.
        It will be normailzed first, where missing, undefined, empty values are
        converted to the string `github`, and other values will be lower-cased.
        Also, `github.com` and `gitlab.com` will be shortened to `github` and `gitlab`.

    kind: string
        Indicates what kind of related value should be returned:

        * `norm`: the normalized value as described above
        * `name`: lowercase shortest name of the backend: `github` or `gitlab`
          or a server name like `gitlab.huc.knaw.nl`
        * `machine`: lowercase machine name of the backend: `github.com` or `gitlab.com`
          or a server name like `gitlab.huc.knaw.nl`
        * `spec`: enclosed in `<` and `>`. Depending on the parameter `default`
          the empty string is returned instead.
        * `clone`: base directory where clones of repos in this backend are stored
          `~/github`, etc.
        * `cache`: base directory where data downloads from this backend are stored:
          `~/text-fabric-data/github`, etc.
        * `url`: url of the online backend
        * `urlnb`: url of notebooks from the online backend, rendered on NB-Viewer
        * `pages`: base url of the Pages service of the backend

    default: boolean, optional `False`
        Only relevant for `kind` = `rep`.
        If `default` is passed and not None and `be` is equal to `default`,
        then the empty string is returned.

        Explanation: this is used to supply a backend  specifier to a module
        but only if that module has a different backend than the main module.

    Returns
    -------
        string
    """

    be = (be or "").lower()
    be = (
        GH
        if be in {None, "", GH, f"{GH}.com"}
        else GL
        if be in {GL, f"{GL}.com"}
        else be
    )

    if kind == "norm":
        return be

    if kind == "name":
        return "GitHub" if be == GH else "GitLab" if be == GH else be

    if kind == "machine":
        return "github.com" if be == GH else "gitlab.com" if be == GL else be

    if kind == "rep":
        if default is not None:
            default = backendRep(default, "norm")
            if be == default:
                return ""
        return f"<{be}>"

    if kind == "clone":
        return f"{HOME_DIR}/{be}"

    if kind == "cache":
        return f"{HOME_DIR}/text-fabric-data/{be}"

    if kind == "url":
        return URL_GH if be == GH else URL_GL if be == GL else f"https://{be}"

    if kind == "urlnb":
        return f"{URL_NB}/{be}"

    if kind == "pages":
        return (
            f"{GH}.io"
            if be == GH
            else f"{GL}.io"
            if be == GL
            else f"{'.'.join(be.split('.'))[0:-1]}.io"
        )
    return None


DOWNLOADS = f"{HOME_DIR}/Downloads"
"""Local Downloads directory."""


EXPRESS_SYNC = "__checkout__.txt"
"""Name of cache indicator file.

When a dataset is stored in the cache,
information about the release/commit is stored in a file
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


URL_TFDOC = f"https://{ORG}.{backendRep(GH, 'pages')}/{REPO}/tf"
"""Base url of the online Text-Fabric documentation."""

DOI_DEFAULT = "no DOI"
DOI_URL_PREFIX = "https://doi.org"

DOI_TF = "10.5281/zenodo.592193"
"""DOI of an archived copy of this repo at Zenodo."""

APIREF = f"https://{ORG}.{backendRep(GH, 'pages')}/{REPO}/tf/cheatsheet.html"
"""Link to the Api docs of Text-Fabric."""

SEARCHREF = f"https://{ORG}.{backendRep(GH, 'pages')}/{REPO}/tf/about/searchusage.html"
"""Link to the Search docs of Text-Fabric."""

APP_CONFIG = "config.yaml"
"""Name of the config file of a TF app."""

APP_CONFIG_OLD = "config.py"
"""Name of the config file of a an older, incompatible TF app."""

APP_CODE = "code"
"""Name of the top-level directory of a legacy TF app."""

APP_APP = "app"
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
to be attached to releases on GitHub/GitLab.

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

SEARCH_FAIL_FACTOR = 4
"""Limits fetching of search results to this times maxNode (corpus dependent)"""

LS = "layeredsearch"
"""Directory where layered search code is stored.

Layered search is client-side search, generated in a dedicated search repo.
If the main data resides in org/repo, then the layered search code resides
in org/repo-search/layeredsearch.
"""
