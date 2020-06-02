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

from .applib.app import findApp

# START AN APP


def use(appName, *args, **kwargs):
    """Make use of a corpus by offering the advanced API to access it.

    Hint: think of the `use {database}` statements in MySQL and MongoDb.

    Without further arguments, this will set up an TF core API
    with most features loaded, wrapped in an corpus-specific advanced API.

    !!! note "Start up sequence"
        During start-up the following happens:

        1.  the corpus data is downloaded to your `~/text-fabric-data` directory,
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
        Used to find the appropriate TF app, if there is one.

    *args:
        Do not pass any other positional argument!

    **kwargs:
        See `tf.applib.app.App`.
        In any case, either an object of class `tf.applib.app.App` or a corpus-specific
        derived class `TfAPP` of it is initialized with the remaining parameters.
        Head over to there for a discription of those parameters, including more
        about *appName*.

    Returns
    -------
    A: object
        The object whose attributes and methods constitute the advanced API.

    See Also
    --------
    tf.applib.app.App.reuse
    """

    parts = appName.split(":", maxsplit=1)
    if len(parts) == 1:
        parts.append("")
    (appName, checkoutApp) = parts

    return findApp(appName, checkoutApp, *args, **kwargs)
