"""Fixed values for the whole program.
"""

import sys
from zipfile import ZIP_DEFLATED


VERSION = '7.10.1'
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
"""

ORG = "annotation"
REPO = "text-fabric"

URL_GH_API = "https://api.github.com/repos"
URL_GH = "https://github.com"
URL_NB = "https://nbviewer.jupyter.org/github"
DOWNLOADS = "~/Downloads"
GH_BASE = "~/github"
EXPRESS_BASE = "~/text-fabric-data"
EXPRESS_SYNC = "__checkout__.txt"
EXPRESS_SYNC_LEGACY = [
    "__release.txt",
    "__commit.txt",
]
URL_TFDOC = f"https://{ORG}.github.io/{REPO}"

DOI_TEXT = "10.5281/zenodo.592193"
DOI_URL = "https://doi.org/10.5281/zenodo.592193"

APIREF = f"https://{ORG}.github.io/{REPO}/Api/Fabric/"

APP_URL = f"{URL_GH}/{ORG}"
APP_NB_URL = f"{URL_NB}/{ORG}/tutorials/blob/master"
APP_GITHUB = f"{GH_BASE}/annotation"
APP_CODE = "code"

TEMP_DIR = "_temp"

LOCATIONS = [
    "~/Downloads/text-fabric-data",
    "~/text-fabric-data",
    "~/github/text-fabric-data",
    "~/Dropbox/text-fabric-data",
    "/mnt/shared/text-fabric-data",
]

GZIP_LEVEL = 2
PICKLE_PROTOCOL = 4

ZIP_OPTIONS = dict(compression=ZIP_DEFLATED,)
if sys.version_info[1] >= 7:
    ZIP_OPTIONS["compresslevel"] = 6

YARN_RATIO = 1.25
TRY_LIMIT_FROM = 40
TRY_LIMIT_TO = 40
