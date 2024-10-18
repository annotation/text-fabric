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

from .advanced.app import findApp, useApp


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

    args: mixed
        Do not pass any other positional argument!

    kwargs: mixed
        Used to initialize the corpus app that we use.
        That is either an uncustomised `tf.advanced.app.App` or
        a customization of it.

    Returns
    -------
    A: object
        The object whose attributes and methods constitute the advanced API.

    See Also
    --------
    tf.advanced.app.App
    """

    (appName, checkoutApp, dataLoc, backend) = useApp(appName, backend)

    return findApp(appName, checkoutApp, dataLoc, backend, False, *args, **kwargs)


def collect(backend, org, repo):
    """Collect the data of the corpus in a zip file.

    The app, main data, data of standard modules of a corpus will be zipped
    into a file `complete.zip` and saved in your downloads folder,
    in a nested folder by backend, org and repo.

    It is assumed that you have cloned the repo of the corpus and the repos
    of all of its standard modules.

    The latest version will be used.

    You can also do this completely from the command line.

    Go to the toplevel of your local clone and say:

    ```
    tf-zipall
    ```

    The complete.zip is created in your downloads folder, under your backend,
    org, and repo.
    """

    A = use(f"{org}/{repo}:clone", checkout="clone", backend=backend)
    A.indent(reset=True)
    msg = A.zipAll()
    A.info(msg)
