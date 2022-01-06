"""
Start the advanced API of TF.

The advanced-API provides extra functionality of top of the core of TF.
The most notable things are donwloading corpus data and methods for (pretty)
display corpus material.

The real power of the advanced API is unleashed when there are well-tuned configuration
settings for a corpus, and possibly some supporting application code and CSS styling.

Depending on the settings, the advanced-API knows how to download the data,
and can be invoked by a simple incantation: `use`.
"""

from .advanced.app import findApp

# START AN APP


def use(appName, *args, **kwargs):
    """Make use of a corpus by offering the advanced API to access it.

    Hint: think of the `use {database}` statements in MySQL and MongoDb.

    Without further arguments, this will set up an TF core API
    with most features loaded, wrapped in an corpus-specific advanced API.

    !!! note "Start up sequence"
        During start-up the following happens:

        1.  the corpus data may be downloaded to your `~/text-fabric-data` directory,
            if not already present there;
        2.  if your data has been freshly downloaded,
            a series of optimizations is executed;
        3.  most features of the corpus are loaded into memory.
        4.  the data is inspected to derive configuration information for the
            advanced API; if present, additional settings, code and styling is loaded.

    Parameters
    ----------
    appName: string
        Name of the corpus, or a local directory.
        Used to find the appropriate TF app, if there is one, or else the tf data.

        To load a TF-app (which will load the associated data):

        * `use("app:full/path/to/tf/app", ...)` :
          find a TF app under `full/path/to/tf/app`;
          if not present, fail;
          you cannot add any `:` specifiers;
        * `use("org/repo", ...)` :
          find a TF app under `~/text-fabric-data/`*org*`/`*repo*`/app`;
          if not present, download it from GitHub
        * `use("org/repo:latest", ...)` :
          find a TF app under `~/text-fabric-data/`*org*`/`*repo*`/app`;
          if not present, fetch it from GitHub;
          if GitHub has a newer release, fetch it from GitHub
        * `use("org/repo:local", ...)` :
          find a TF app under `~/text-fabric-data/`*org*`/`*repo*`/app`;
          if not present, fail
        * `use("org/repo:clone", ...)` :
          find a TF app under `~/github/`*org*`/`*repo*`/app`
        * `use("org/repo/xx/yy/zz", ...)` :
          find a TF app under `~/text-fabric-data/`*org*`/`*repo*`/xx/yy/zz`;
          you can add `:local`, `:clone`, etc., with the same meaning as above;

        There is also a legacy method for TF-apps that are hosted in `app-`*xxx* repos
        under the `annotation` organization:

        * `use("corpus", ...)` :
          find a TF app under `~/text-fabric-data/annotation/app-`*corpus*;
          if not present, download it from GitHub
          you can add `:local`, `:clone`, etc., behind `corpus`
          with the same meaning as above;

        !!! note "Versions"
            In all of the above cases, the data resides in version
            directories. The configuration of the TF-app specifies
            which version will be used. You can override that by passing
            the optional argument `version="x.y.z"`.

        To load TF data, without an associated TF-app (a generic TF app
        with default settings will be used):

        * `use("data:full/path/to/tf/data/version", ...)` :
          find TF data under `full/path/to/tf/data/version`;
          if not present, fail;
          you cannot add any `:` specifiers;
        * `use("data:org/repo/tf:latest", ...)` :
          find TF data under `~/text-fabric-data/`*org*`/`*repo*`/tf`;
          if not present, fetch it from GitHub;
          if GitHub has a newer release, fetch it from GitHub
        * `use("data:org/repo/tf:local", ...)` :
          find TF data under `~/text-fabric-data/`*org*`/`*repo*`/tf`;
          if not present, fail
        * `use("data:org/repo/tf:clone", ...)` :
          find TF data under `~/github/`*org*`/`*repo*`/tf`
          if not present, fail

        !!! note "Versions"
            Since we do not have a TF-app that specifies the version in this case,
            you must either:

            *   specify the paths so that they include the version directory
            *   specify the path to the parent of the version directories
                and pass `version="x.y.z"

    args:
        Do not pass any other positional argument!

    kwargs:
        See `tf.advanced.app.App`.
        In any case, either an object of class `tf.advanced.app.App`
        or a corpus-specific derived class `TfAPP` of it is initialized
        with the remaining parameters.
        Head over to there for a discription of those parameters, including more
        about *appName*.

    Returns
    -------
    A: object
        The object whose attributes and methods constitute the advanced API.

    See Also
    --------
    tf.advanced.app.App.reuse
    """

    if appName.startswith("data:"):
        dataLoc = appName[5:]
        appName = None
        checkoutApp = None
    elif appName.startswith("app:"):
        dataLoc = None
        checkoutApp = None
    else:
        dataLoc = None
        parts = appName.split(":", maxsplit=1)
        if len(parts) == 1:
            parts.append("")
        (appName, checkoutApp) = parts

    return findApp(appName, checkoutApp, dataLoc, False, *args, **kwargs)
