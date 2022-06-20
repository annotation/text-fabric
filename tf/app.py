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

from .parameters import backendRep
from .advanced.app import findApp

# START AN APP


def use(appName, *args, backend=None, **kwargs):
    """Make use of a corpus.

    For a detailed description, see `tf.about.usefunc`.

    Parameters
    ----------
    appName: string

    backend: string, optional None
        If present, it is `github` or `gitlab`
        or a GitLab instance such as `gitlab.huc.knaw.nl`.
        If absent, `None` or empty, it is `github`.

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

    backend = backendRep(backend, 'norm')
    return findApp(appName, checkoutApp, dataLoc, backend, False, *args, **kwargs)
