## Auto downloading from GitHub

???+ abstract "checkoutRepo()"
    ```python
    from tf.applib.repo import checkoutRepo

    checkoutRepo(
      org='annotation'
      repo='tutorials',
      folder='text-fabric/examples/banks/tf',
      version='',
      checkout='',
      source=None,
      dest=None,
      withPaths=True,
      keep=True,
      silent=False,
      label='data',
    )
    ```

???+ explanation "Description"
    Maintain a local copy of a subfolder *folder* in GitHub repository *repo* of *org*.
    The copy may be taken from any point in the commit history of the online repo.

    If you call this function, it will check whether the requested data is already 
    on your computer in the expected location.
    If not, it may check whether the data is online and if so, download it to the
    expected location.
    
??? explanation "Result"
    The result of a call to checkoutRepo() is a tuple:

    ```python
        (commitOffline, releaseOffline, kindLocal, localBase, localDir)
    ```

    Here is the meaning:

    *   *commitOffline* is the commit hash of the data you have offline afterwards
    *   *releaseOffline* is the release tag of the data you have offline afterwards
    *   *kindLocal* indicates whether an online check has been performed:
        it is `None` if there has been an online check. Otherwise it is
        `clone` if the data is in your `~/github` directory else it is `local`.
    *   *localBase* where the data is under: `~/github` or `~/text-fabric-data`,
        or whatever you have passed as *source* and *dest*, see below.
    *   *localDir* releative path from *localBase* to your data.
        If your data has versions, *localDir* points to directory that has the versions,
        not to a specific version.
     

    Your local copy can be found under your `~/github` or `~/text-fabric-data`
    directory using a relative path *org/repo/folder* if there is a *version*, else
    *org/repo/folder/version*.

???+ explanation "checkout, source and dest"
    The *checkout* parameter determines from which point in the history the copy
    will be taken and where it will be placed.
    That will be either your `~/github` or your `~/text-fabric-data` directories.

    You can override the hard-coded `~/github` and `~/text-fabric-data` directories
    by passing *source* and *dest* respectively.

    See the
    [repo]({{tutnb}}/banks/repo.ipynb)
    notebook for an exhaustive demo of all the checkout options.

??? explanation "other parameters"
    *withPaths=False* will loose the directory structure of files that are being
    downloaded.

    *keep=False* will destroy the destination directory before a download takes place.

    *silent=True* will suppress non-error messages.

    *label='something' will change the word "data" in log messages to what you choose.
    We use `label='TF-app'` when we use this function to checkout the code
    of a TF-app.

???+ caution "Rate limiting"
    The `checkRepo()` function uses the GitHub API.
    GitHub has a rate limiting policy for its API of max 60 calls per hour.

    If you use this function in an application of yours that uses it very often,
    you can increase the limit to 5000 calls per hour by making yourself known.

    * [Read more about rate limiting on Github]({{ghrate}})
    * [create a personal access token]({{ghapppers}})
    * Copy your token and put it in an environment variable named `GHPERS`
      on the system where your app runs.
      See below how to do that.
    * If `checkRepo()` finds this variable, it will add the
      token to every GitHub API call it makes, and that will
      increase the rate.
    * Never pass your personal credentials on to others, let them obtain their own!

    How to put your personal access token into an environment variable?

    ??? hint "On Mac and Linux"
        Open your `.zshrc` or `.bashrc` file in your home directory,
        and put the following lines in it:

        ``` sh
        GHPERS="xxx"
        export GHPERS
        ```

        where the `xxx` are replaced by your actual token.

        Then restart your shell.

    ??? hint "On Windows"
        Click on the Start button and type in `environment variable` into the search box.

        Click on `Edit the system environment variables`.

        This will  open up the System Properties dialog to the Advanced tab.

        Click on the `Environment Variables button` at the bottom.

        Click on `New ...` under `User environment variables`.

        Then fill in `GHPERS` under *name* and the token string under *value*.

        Then quit the command prompt and start a new one.

    With this done, you will automatically get the good rate limit,
    whenever you fire up Text-Fabric in the future.
