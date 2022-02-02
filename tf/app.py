"""
Make use of a corpus.

The advanced-API provides extra functionality of top of the core of TF.
The most notable things are downloading corpus data and methods for (pretty)
display corpus material.

The real power of the advanced API is unleashed when there are well-tuned configuration
settings for a corpus, and possibly some supporting application code and CSS styling.

This power can be invoked by a very simple command: `use("org/repo")`.

For a detailed description, see `tf.about.usefunc`.
"""

from .advanced.app import findApp

# START AN APP


def use(appName, *args, **kwargs):
    """Make use of a corpus.

    For a detailed description, see `tf.about.usefunc`.

    Parameters
    ----------
    appName: string
    checkout: string, optional `""`
    version: string, optional None

    args:
        Do not pass any other positional argument!

    kwargs:
        Used to initialize the TF-app that we use.
        That is either an uncustomized `tf.advanced.app.App` or
        a customization of it.

    Returns
    -------
    A: object
        The object whose attributes and methods constitute the advanced API.

    See Also
    --------
    tf.advanced.app.App
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
