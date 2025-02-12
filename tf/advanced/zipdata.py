import sys
import types
from zipfile import ZipFile

from .helpers import splitModRef
from ..parameters import ZIP_OPTIONS, RELATIVE
from ..core.helpers import console, run
from ..core.files import (
    fileOpen,
    normpath,
    expanduser as ex,
    unexpanduser as ux,
    backendRep,
    DOWNLOADS,
    TEMP_DIR,
    APP_APP,
    APP_EXPRESS_ZIP,
    EXPRESS_SYNC,
    prefixSlash,
    dirExists,
    dirMake,
    scanDir,
    initTree,
)

HOME = ex("~")
DW = ex(DOWNLOADS)

__pdoc__ = {}

HELP = """
### USAGE

``` sh
tf-zip --help

tf-zip {org}/{repo}{relative}

tf-zip {org}/{repo}{relative} --backend=gitlab.huc.knaw.nl
```

### EFFECT

Zips TF data from your local GitHub / GitLab repository into
a release file, ready to be attached to a GitHub release.

Your repo must sit in `~/github/*org*/*repo*` or in `~/gitlab/*org*/*repo*`
or in whatever GitLab back-end you have chosen.

Your TF data is assumed to sit in the toplevel TF directory of your repo.
But if it is somewhere else, you can pass relative, e.g phrases/heads/tf

It is assumed that your TF directory contains subdirectories according to
the versions of the main data source.
The actual `.tf` files are in those version directories.

Each of these version directories will be zipped into a separate file.

The resulting zip files end up in `~/Downloads/backend/org-release/repo`
and the are named `relative-version.zip`
(where the / in relative have been replaced by -)

"""

EXCLUDE = {".DS_Store", ".tf", "__pycache__", "_local", "_temp", ".ipynb_checkpoints"}


def zipApi(app):
    """Produce the zip creation API.

    Parameters
    ----------
    app: obj
        The high-level API object of a loaded TF dataset
    """

    app.zipAll = types.MethodType(zipAll, app)


def zipAll(app):
    """Gathers all data for a TF resource and zips it into one file.

    The data gathered is:

    *   the app
    *   the main data module
    *   all modules mentioned in the `moduleSpecs` in the `provenanceSpec` of the app
    *   all graphics data mentioned in the `graphicsRelative` of the `provenanceSpec`
    *   all extra data mentioned in the `extraData` of the `provenanceSpec`

    The data will be zipped in a file complete.zip which can be unpacked
    in the `~/text-fabric-data` directory.

    Go to the toplevel of your local clone and say:

    ```
    tf-zipall
    ```

    The complete.zip is created in your downloads folder, under your backend,
    org, and repo.

    !!! hint
        You can attach this file straight to the latest release of of dataset
        on GitHub. This makes that users can download the dataset from GitHub
        without problems such as bumping against the GitHub API rate limit.

    !!! caution
        All data should reside on the same back-end.

    !!! note "checkout files"
        There will be `__checkout__.txt` files included in the zip file,
        so that after unpacking TF detects from which release the data is
        coming.

    Parameters
    ----------
    app: object
        A loaded TF data source or None.
    """
    context = app.context

    backend = app.backend
    base = backendRep(backend, "clone")
    org = context.org
    repo = context.repo
    relative = context.relative
    relative = prefixSlash(normpath(relative))
    version = context.version

    graphics = context.graphicsRelative
    graphics = prefixSlash(normpath(graphics))
    extra = context.extraData
    extra = prefixSlash(normpath(extra))

    prov = context.provenanceSpec
    mods = prov.get("moduleSpecs", [])

    repoDir = f"{base}/{org}/{repo}"

    dataItems = [
        ("app", f"{repoDir}/{APP_APP}"),
        ("main data", f"{repoDir}{relative}/{version}"),
    ]
    if graphics:
        dataItems.append(("graphics", f"{repoDir}{graphics}"))
    if extra:
        dataItems.append(("extra", f"{repoDir}{extra}"))

    good = True

    for mod in mods:
        mbackend = mod["backend"]
        if mbackend is None:
            mbackend = app.backend
        mbase = backendRep(mbackend, "clone")
        morg = mod["org"]
        mrepo = mod["repo"]
        mrelative = mod["relative"]
        mrelative = prefixSlash(normpath(mrelative))
        mrepoDir = f"{mbase}/{morg}/{mrepo}"
        labelItems = []
        if mbase != base:
            labelItems.append(mbase)
        if morg != org:
            labelItems.append(morg)
        if mrepo != repo:
            labelItems.append(mrepo)
        if mrelative != relative:
            labelItems.append(mrelative)
        label = "-".join(labelItems)
        if mbase != base:
            good = False
            console(f"ERROR: module {label} not on expected back-end {backend}")
        dataItems.append((f"module {label}", f"{mrepoDir}{mrelative}/{version}"))

    if not good:
        return

    destBase = f"{DW}/{backendRep(backend, 'norm')}"
    dest = normpath(f"{destBase}/{org}/{repo}")
    destFile = f"{dest}/{APP_EXPRESS_ZIP}"

    console("Data to be zipped:")
    results = []

    for label, path in dataItems:
        if dirExists(path):
            (release, commit) = addCheckout(path)
            checkout = f"({release or 'v??'} {commit[-6:] if commit else '??'})"
            zipBase = path.removeprefix(f"{base}/")
            collectFiles(path, "", results, zipBase=zipBase)
            status = "OK"
        else:
            good = False
            status = "missing"
            checkout = "(??)"
        console(f"\t{status:<8} {label:<24} {checkout:<20}: {path}")

    if not good:
        return

    if not dirExists(dest):
        dirMake(dest)
    console("Writing zip file ...")
    with ZipFile(destFile, "w", **ZIP_OPTIONS) as zipFile:
        for internalPath, path in sorted(results):
            zipFile.write(
                path,
                arcname=internalPath,
            )
    return ux(destFile)


def addCheckout(path):
    release = None
    commit = None

    (good, returnCode, gitInfo, stdErr) = run(
        "git describe --tags --abbrev=1000 --long", workDir=path
    )
    if good:
        (release, n, commit) = [x.strip() for x in gitInfo.split("-", 2)]
    else:
        if "cannot describe" in stdErr.lower():
            console("WARNING: no local release info found.", error=True)
            console("Maybe you have to do go to this repo and do `git pull --tags`")
            console("We'll fetch the local commit info anyway.")
            (good, returnCode, gitInfo, stdErr) = run("git rev-parse HEAD", workDir=path)
            if good:
                commit = gitInfo
            else:
                console(stdErr, error=True)
        else:
            console(stdErr, error=True)

    if release is not None or commit is not None:
        with fileOpen(f"{path}/{EXPRESS_SYNC}", mode="w") as fh:
            if release is not None:
                fh.write(f"{release}\n")
            if commit is not None:
                fh.write(f"{commit}\n")
    return (release, commit)


def collectFiles(base, path, results, zipBase=None):
    if zipBase is None:
        zipBase = base

    sep = "/" if path else ""
    thisPath = f"{base}{sep}{path}" if path else base
    internalBase = f"{zipBase}{sep}{path}"
    with scanDir(thisPath) as sd:
        for e in sd:
            name = e.name
            if name in EXCLUDE:
                continue
            if e.is_file():
                results.append((f"{internalBase}/{name}", f"{thisPath}/{name}"))
            elif e.is_dir():
                collectFiles(base, f"{path}{sep}{name}", results, zipBase=zipBase)


def zipDataPart(source, results):
    if not dirExists(source):
        return (False, "missing")
    zipBase = source.removeprefix(f"{HOME}/")
    collectFiles(source, "", results, zipBase=zipBase)
    return (True, "OK")


def zipData(
    backend,
    org,
    repo,
    relative=RELATIVE,
    version=None,
    tf=True,
    keep=True,
    source=None,
    dest=None,
):
    """Zips TF data into a single file, ready to be attached to a release.

    Parameters
    ----------
    backend: string
        The back-end for which the zip file is meant (`github`, `gitlab`, etc).
    org, repo: string
        Where the corpus is located on the back-end,
    relative: string, optional "tf"
        The subdirectory of the repo that will be zipped.
    version: string, optional None
        If passed, only data of this version is zipped, otherwise all versions
        will be zipped.
    tf: boolean, optional True
        Whether the data to be zipped are TF feature files or other kinds of data.
    keep: boolean, optional True
        Whether previously generated zip files in the destination directory should
        be kept or deleted.
    source: string, optional None
        Top directory under which the repository is found, if None; this directory
        is given by the back-end: `~/github`, `~/gitlab`, etc.
    dest: string, optional None
        Top directory under which the generated zip files are saved; if None,
        this directory under the user's Downloads directory and further determined by
        the back-end: `~/Downloads/github`, `~/Downloads/gitlab`, etc.
    """

    if source is None:
        source = backendRep(backend, "clone")
    if dest is None:
        dest = f"{DW}/{backendRep(backend, 'norm')}"
    relative = prefixSlash(normpath(relative))
    console(f"Create release data for {org}/{repo}{relative}")
    sourceBase = normpath(f"{source}/{org}")
    destBase = normpath(f"{dest}/{org}-release")
    sourceDir = f"{sourceBase}/{repo}{relative}"
    destDir = f"{destBase}/{repo}"
    dataFiles = {}

    initTree(destDir, fresh=not keep)
    relativeDest = relative.removeprefix("/").replace("/", "-")

    if tf:
        if not dirExists(sourceDir):
            return
        with scanDir(sourceDir) as sd:
            versionEntries = [(sourceDir, e.name) for e in sd if e.is_dir()]
        if versionEntries:
            console(f"Found {len(versionEntries)} versions")
        else:
            versionEntries.append((sourceDir, ""))
            console("Found unversioned features")
        for versionDir, ver in versionEntries:
            if ver == TEMP_DIR:
                continue
            if version is not None and version != ver:
                continue
            versionRep = f"/{ver}" if ver else ""
            versionRep2 = f"{ver}/" if ver else ""
            versionRep3 = f"-{ver}" if ver else ""
            tfDir = f"{versionDir}{versionRep}"
            with scanDir(tfDir) as sd:
                for e in sd:
                    if not e.is_file():
                        continue
                    featureFile = e.name
                    if featureFile in EXCLUDE:
                        continue
                    if not featureFile.endswith(".tf"):
                        console(
                            f'WARNING: non feature file "{versionRep2}{featureFile}"',
                            error=True,
                        )
                        continue
                    dataFiles.setdefault(ver, set()).add(featureFile)

        console(f"zip files end up in {destDir}")
        for ver, features in sorted(dataFiles.items()):
            item = f"{org}/{repo}"
            versionRep = f"/{ver}" if ver else ""
            versionRep3 = f"-{ver}" if ver else ""
            target = f"{relativeDest}{versionRep3}.zip"
            console(
                f"zipping {item:<25} {ver:>4} with {len(features):>3} features ==> {target}"
            )
            with ZipFile(f"{destDir}/{target}", "w", **ZIP_OPTIONS) as zipFile:
                for featureFile in sorted(features):
                    zipFile.write(
                        f"{sourceDir}{versionRep}/{featureFile}",
                        arcname=featureFile,
                    )
    else:
        results = []
        versionRep = f"/{version}" if version else ""
        sourceDir = f"{sourceDir}{versionRep}"
        collectFiles(sourceDir, "", results)
        if not relativeDest:
            relativeDest = "-"
        console(f"zipping {org}/{repo}{relative}{versionRep} with {len(results)} files")
        console(f"zip file is {destDir}/{relativeDest}.zip")
        with ZipFile(f"{destDir}/{relativeDest}.zip", "w", **ZIP_OPTIONS) as zipFile:
            for internalPath, path in sorted(results):
                zipFile.write(
                    path,
                    arcname=internalPath,
                )


def main(cargs=sys.argv):
    if len(cargs) < 2 or any(
        arg in {"--help", "-help", "-h", "?", "-?"} for arg in cargs
    ):
        console(HELP)
        return

    backend = None

    newArgs = []
    for arg in cargs:
        if arg.startswith("--backend="):
            backend = arg[10:]
        else:
            newArgs.append(arg)
    cargs = newArgs

    moduleRef = cargs[1]

    parts = splitModRef(moduleRef)
    if not parts:
        console(HELP)
        return

    (org, repo, relative, checkout, theBackend) = parts
    relative = prefixSlash(normpath(relative))

    tf = (
        relative.removeprefix("/") == RELATIVE
        or relative.endswith(RELATIVE)
        or relative.startswith(f"{RELATIVE}/")
        or f"/{RELATIVE}/" in relative
    )
    tfMsg = "This is a TF dataset" if tf else "These are additional files"
    sys.stdout.write(f"{tfMsg}\n")

    zipData(theBackend or backend, org, repo, relative=relative, tf=tf)


__pdoc__["main"] = HELP


if __name__ == "__main__":
    main()
