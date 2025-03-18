"""
# Auto downloading from a back-end repository

## Description

TF maintains local copies of subdirectories of back-end repositories,
where it stores the feature data of corpora that the user is working with.

Currently GitHub and GitLab are supported as back-ends.
In case of GitLab, not only [gitlab.com](https://gitlab.com) is supported,
but also GitLab instances on other servers that support the GitLab API.

There is some bookkeeping to account for which release and commit the
feature files come from.

Users can request data from any repo according to any release and / or commit.

## Rate limiting

The `checkRepo()` function uses the GitHub and GitLab APIs.
GitHub has a rate limiting policy for its API.
See below to deal with this if it becomes a problem.

On GitLab we ignore the rate limiting.

# GitHub

GitHub has a rate limiting policy for its API of max 60 calls per hour.
This can be too restrictive, and here are two ways to keep working nevertheless.

!!! hint
    If you are a dataset provider, use `tf.advanced.zipdata.zipAll()` to
    produce a zip file of your complete dataset, and then attach it to the latest
    release on GitHub.
    Then TF will find this file and download it automatically if needed, without ever
    using the GitHub API, so your users do not have to do the things described below!

    Go to the toplevel of your local clone and say:

    ```
    tf-zipall
    ```

    The complete.zip is created in your downloads folder, under your backend,
    org, and repo.

## Increase the rate limit

If you use this function in an application of yours that uses it very often,
you can increase the limit to 5000 calls per hour by making yourself known.

*   [create a personal access token](https://github.com/settings/tokens)
*   Copy your token and put it in an environment variable named `GHPERS`
    on the system where your app runs.
    See below how to do that.
*   If `checkoutRepo` finds this variable, it will add the
    token to every GitHub API call it makes, and that will
    increase the rate.
*   Never pass your personal credentials on to others, let them obtain their own!

You might want to read this:

*   [Read more about rate limiting on GitHub](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting)

# GitLab

In order to reach an on-premise GitLab and have access to the repository in
question, you may need to have a VPN connection with the GitLab back-end.

Additionally, you may need to make your identity known.
If you have an account on the GitLab instance, go to your settings and request
a personal token with `api` privileges.

On your own system, make an environment variable named `GL_BACKEND_PERS` whose
content is exactly the value of this token.

And `BACKEND` should be the uppercase variant of the name of the GitLab back-end,
where every character that is not a letter or digit or `_` is replaced by a `_`.

For example, for `gitlab.huc.knaw.nl` use `GL_GITLAB_HUC_KNAW_NL_PERS`
and for `gitlab.com` use `GL_GITLAB_COM_PERS`.

See below how to put this in an environment variable.

# Token in environment variables

How to put your personal access token into an environment variable?

!!! note "What is an environment variable?"
    It is a setting on your system that various programs / processes can read.
    On Windows it is part of the `Registry`.

    In this particular case, you put a personal token
    that you obtain from GitHub / GitLab
    in such an environment variable.
    When TF accesses the back-end, it will look up this token
    first, and pass it to the back-end API. The back-end then knows who you are and
    will give you more privileges.

### On Mac and Linux

Find the file that contains your terminal settings. In many cases that is
`.bash_profile` in your home directory.

Some people put commands like these in their `~/.bashrc` file, which is also fine.
If you do not see a `.bashrc` file, put it into your `.bash_profile` file.

A slightly more advanced shell than `bash` is `zsh` and it is the default on newer
Macs. If that is your case, look for a file `.zshrc` in your home directory or
create one.

Whatever is your case, pick the file indicated above and edit it.

!!! hint "How to edit a file in your terminal?"
    If you are already familiar with `vi`, `vim`, `emacs`, or `nano`
    you already know how to do it.

    If not, `nano` is simple editor that is useful for tasks like this.
    Assuming that you want to edit the `.zshrc` in your home directory,
    go to your terminal and say this:

        nano ~/.zshrc

    Then you get a view on your file. Then

    *   press `Ctrl V` a number of times till you are at the end of the file,
    *   type the two lines lines of text (specified in the next step), or
        copy them from the clipboard
    *   type `Ctrl X` to exit; `nano` will ask you to save changes, type `Y`,
        it will then verify the file name, type `Enter` and you're done


**GitHub**
Put the following lines in this file:

``` sh
GHPERS="xxx"
export GHPERS
```

**GitLab**
Put the following lines in this file:

``` sh
GL_BACKEND_PERS="xxx"
export GL_BACKEND_PERS
```

where

*   `xxx` is replaced by your actual token.
*   `BACKEND` is replaced by the uppercase GitLab back-end
    e.g.
    *   `gitlab.com` becomes `GL_GITLAB_COM_PERS`
    *   `gitlab.huc.knaw.nl` becomes `GL_GITLAB_HUC_KNAW_NL_PERS`

    In this way you can store tokens for multiple GitLab back-ends.

Then restart your terminal or say in an existing terminal

```  sh
source ~/.zshrc
```

### On Windows

Click on the Start button and type in `environment variable` into the search box.

Click on `Edit the system environment variables`.

This will  open up the System Properties dialog to the Advanced tab.

Click on the `Environment Variables button` at the bottom.

Click on `New ...` under `User environment variables`.

**GitHub**: Then fill in `GHPERS` under *name* and the token string under *value*.

**GitLab**: Then fill in `GL_BACKEND_PERS`
under *name* and the token string under *value*.

Then quit the command prompt and start a new one.

### Result

**GitHub**

With this done, you will automatically get the good rate limit,
whenever you fire up TF in the future.

**GitLab**

You are now known to the GitLab back-end, and you have the same access to its
repository as when you log in via the web interface.

## Minimize accessing GitHub

Another way to avoid being bitten by the rate limit is to reduce the number
of your access actions to GitHub.

There are two instances where TF wants to access GitHub:

1.  when you start the TF browser from the command-line
1.  when you give the `use()` command in your Python program (or in a Jupyter Notebook).

### Using a corpus for the first time, within the rate limit

If you are still within the rate limit, just give the usual commands, such as

``` sh
tf org/repo
```

or

``` python
use('org/repo', hoist=globals())
```

where `corpus` should be replaced with the real name of your corpus.

The data will be downloaded to your computer and stored in your
`~/text-fabric-data` directory tree.

### Using a corpus for the first time, after hitting the rate limit

If you want to load a new corpus after having passed the rate limit, and not
wanting to wait an hour, you could directly clone the repos from GitHub / GitLab:

Open your terminal, and go to (or create) directory `~/github` or `~/gitlab`
(in your home directory).

Inside that directory, go to or create directory `org`
Go to that directory.

Then do

``` sh
git clone https://github.com/org/repo
```

or

``` sh
git clone https://gitlab.com/org/repo
```

(replacing `org` and `repo` with the values that apply to your corpus).

This will fetch the TF *data*, *app*, and *tutorials* for that corpus.

Now you have all data you need on your system.

If you want to see by example how to use this data, have a look at
[repo](https://nbviewer.jupyter.org/github/annotation/banks/blob/master/tutorial/repo.ipynb),
especially when it discusses `clone`.

In order to run TF without further access to the back-end, say

``` sh
tf corpus:clone checkout=clone
```

or, in a program,

``` python
A = use('org/repo:clone', checkout='clone', hoist=globals())
```

This will instruct TF to use the app and data from within your `~/github`
or `~/gitlab` directory tree.

### Using a corpus that you already have

Depending on how you got the corpus, it is in your
`~/github`, `~/gitlab` or in your `~/text-fabric-data` directory tree:

1.   if you cloned it from GitHub, it is in your `~/github` tree;
1.   if you cloned it from GitLab, it is in your `~/gitlab` tree;
1.   if you cloned it from an other instance of GitLab, say hosted at
    `gitlab.huc.knaw.nl`, it is in your `~/gitlab.huc.knaw.nl` tree;
1.   if you used the auto-download of TF it is in your `~/text-fabric-data`.

In the first case, do this:

``` sh
tf corpus:clone checkout=clone
```

or, in a program,

``` python
A = use('org/repo:clone', checkout='clone', hoist=globals())
```

In the second case, do this:

``` sh
tf corpus:clone checkout=clone --backend=gitlab
```

or, in a program,

``` python
A = use('org/repo:clone', checkout='clone', backend="gitlab", hoist=globals())
```

In the third case, do this:

``` sh
tf corpus:clone checkout=clone --backend=gitlab.huc.knaw.nl
```

or, in a program,

``` python
A = use(
        'org/repo:clone',
        checkout='clone',
        backend="gitlab".huc.knaw.nl,
        hoist=globals(),
    )
```

In the fourth case, do just this:

``` sh
tf corpus
```

or, in a program,

``` python
A = use('org/repo', hoist=globals())
```

See also `tf.advanced.app.App`.

### Updating a corpus that you already have

If you cloned it from GitHub / GitLab:

In your terminal:

``` sh
cd ~/github/organization/repo
```

or

``` sh
cd ~/gitlab/organization/repo
```

(replacing `organization` with the name of the organization where the corpus resides
and `corpus` with the name of your corpus).

And then:

```
git pull origin master
```

Now you have the newest corpus data on your system.
and you can use it as follows
(we show the example for `github`):

``` sh
tf corpus:clone checkout=clone
```

or, in a program,

``` python
A = use('org/repo:clone', checkout='clone', hoist=globals())
```

If you have auto-downloaded it from the back-end,
you have to add the `latest` or `hot` specifier:

``` sh
tf corpus:latest checkout=latest
```

or, in a program,

``` python
A = use('org/repo:latest', checkout='latest', hoist=globals())
```

And after that, you can omit `latest` or `hot` again, until you need new data again.

!!! hint "App versus data"
    The checkout specifiers such as `latest`, `hot`, `clone` apply
    to either the corpus data or the TF App.

    If the specifier follows the app name, separated with a colon,
    it directs how the app code is being obtained.

    If it is the value of the `checkout` parameter, it directs how the corpus data
    is being obtained.
See further under `checkoutRepo`.
"""

import io
import re
import base64
from zipfile import ZipFile
from subprocess import check_output, run
import urllib.request as ur
from urllib.error import HTTPError, URLError
import ssl

import requests
from requests import exceptions as requestsExceptions

from ..parameters import (
    GH,
    RELATIVE,
)
from ..core.helpers import console, htmlEsc, var
from ..core.files import (
    fileOpen,
    expanduser as ex,
    unexpanduser as ux,
    backendRep,
    URL_TFDOC,
    DOWNLOADS,
    EXPRESS_SYNC,
    EXPRESS_SYNC_LEGACY,
    APP_EXPRESS_ZIP,
    prefixSlash,
    fileNm,
    dirNm,
    initTree,
    fileExists,
    dirExists,
    dirMake,
    dirRemove,
    fileRemove,
    fileMove,
    getCwd,
    chDir,
)
from ..core.timestamp import SILENT_D, AUTO, TERSE, VERBOSE, silentConvert
from ..capable import Capable
from .helpers import dh, runsInNotebook
from .zipdata import zipData

Cap = Capable("github", "gitlab")
(Github, GithubException, UnknownObjectException) = Cap.loadFrom(
    "github", "Github", "GithubException", "UnknownObjectException"
)
(Gitlab, GitlabGetError) = Cap.loadFrom("gitlab", "Gitlab", "GitlabGetError")

ConnectionError = requestsExceptions.ConnectionError if requestsExceptions else None

VERSION_DIGIT_RE = re.compile(r"^([0-9]+).*")
SHELL_VAR_RE = re.compile(r"[^A-Z0-9_]")


def GLPERS(backend):
    return f"GL_{SHELL_VAR_RE.sub('_', backend.upper())}_PERS"


def catchRemaining(e):
    eType = type(e)
    if eType is ConnectionError:
        console("no internet connection", error=True)
    elif eType is IOError:
        console("no internet", error=True)
    else:
        console(f"unexpected error from {e.__class__.__module__}: {str(e)}")


def getFinalUrl(url):
    finalUrl = None
    msg = None

    try:
        response = ur.urlopen(url)
        finalUrl = response.geturl()
    except HTTPError as e:
        msg = str(e)
    except URLError as e:
        msg = str(e)

    return (False, msg) if finalUrl is None else (True, finalUrl)


def bumpRelease(latestR, increase):
    if latestR:
        console(f"Latest release = {latestR}")
    else:
        latestR = "v0.0.0"
        console("No releases yet")

    # bump the release version

    v = ""
    r = latestR

    if latestR.startswith("v"):
        v = "v"
        r = latestR[1:]

    parts = [int(p) for p in r.split(".")]
    nParts = len(parts)
    if nParts < increase:
        for i in range(nParts, increase):
            parts.append(0)
    parts[increase - 1] += 1
    parts[increase:] = []
    newTag = f"{v}{'.'.join(str(p) for p in parts)}"
    console(f"New release = {newTag}")
    return newTag


def extractPrecise(z):
    """Extracts a zip file precisely, by deleting some pre-existing material.

    The contents of the zip file will be extracted to the *current* directory.
    Each folder in the zip file that contains a file `__checkout__.txt` will
    be deleted from the destination if it already exists.
    Other folders will not be deleted.

    Parameters
    ----------
    z: object
        The Zip object from which to extract
    """
    # first make a list of all directories that contain __checkout__.txt

    contents = {}

    for zInfo in z.infolist():
        fileName = zInfo.filename
        comps = fileName.rstrip("/").split("/")
        contents.setdefault("/".join(comps[0:-1]), set()).add(comps[-1])

    clearableDirs = {x for (x, files) in contents.items() if EXPRESS_SYNC in files}

    for x in clearableDirs:
        dirRemove(x)

    z.extractall()

    return clearableDirs


class Repo:
    """Auxiliary class for `releaseData`"""

    def __init__(
        self,
        backend,
        org,
        repo,
        folder,
        version,
        increase,
        source=backendRep(GH, "clone"),
        dest=DOWNLOADS,
    ):
        self.org = org
        self.repo = repo
        self.folder = folder
        self.version = version
        self.increase = increase
        self.source = ex(source)
        self.dest = ex(dest)

        self.repoOnline = None

        self.backend = backend
        onGithub = backend is None
        self.onGithub = onGithub

        self.conn = None

    def newRelease(self):
        if not self.makeZip():
            return False

        return True

        conn = self.connect()

        if not conn:
            return False

        if not self.fetchInfo():
            return False

        if not self.bumpRelease():
            return False

        if not self.makeRelease():
            return False

        if not self.uploadZip():
            return False

        return True

    def makeZip(self):
        source = self.source
        dest = self.dest
        backend = self.backend
        org = self.org
        repo = self.repo
        folder = self.folder
        version = self.version

        dataIn = f"{source}/{org}/{repo}/{folder}/{version}"

        if not dirExists(dataIn):
            console(f"No data found in {dataIn}", error=True)
            return False

        zipData(
            backend,
            org,
            repo,
            version=version,
            relative=prefixSlash(folder),
            source=source,
            dest=dest,
        )
        return True

    def connect(self):
        backend = self.backend
        conn = self.conn

        if backend != "github":
            console(
                "Release preparation not implemented for {backend}, only for github",
                error=True,
            )
            return None

        backendTech = backendRep(backend, "tech")

        if not Cap.can(backendTech):
            self.conn = None
            return

        if not conn:
            ghPerson = var("GHPERS")
            if ghPerson:
                conn = Github(ghPerson)
            else:
                ghClient = var("GHCLIENT")
                ghSecret = var("GHSECRET")
                if ghClient and ghSecret:
                    conn = Github(client_id=ghClient, client_secret=ghSecret)
                else:
                    conn = Github()
        try:
            rate = conn.get_rate_limit().core
            self.info(
                f"rate limit is {rate.limit} requests per hour,"
                f" with {rate.remaining} left for this hour"
            )
            if rate.limit < 100:
                self.warning(
                    f"To increase the rate,"
                    f"see {URL_TFDOC}/advanced/repo.html#github"
                )

            self.info(
                f"\tconnecting to online {backend} repo {self.org}/{self.repo} ... ",
                newline=False,
            )
            self.repoOnline = conn.get_repo(f"{self.org}/{self.repo}")
            self.info("connected")
        except Exception as e:
            self.warning("failed")
            if type(e) is GithubException:
                self.warning(f"{backend} says: {str(e)}")
            else:
                catchRemaining(e)

        self.conn = conn
        return conn

    def fetchInfo(self):
        g = self.repoOnline
        if not g:
            return False
        self.commitOn = None
        self.releaseOn = None
        self.releaseCommitOn = None
        result = self.getRelease()
        if result:
            self.releaseOn = result
        result = self.getCommit()
        if result:
            self.commitOn = result
        return True

    def bumpRelease(self):
        increase = self.increase
        latestR = self.releaseOn

        self.newTag = bumpRelease(latestR, increase)
        return True

    def makeRelease(self):
        g = self.repoOnline
        if not g:
            return False

        commit = self.commitOn
        newTag = self.newTag

        tag_message = "data update"
        release_name = "data update"
        release_message = "data update"

        try:
            newReleaseObj = g.create_git_tag_and_release(
                newTag,
                tag_message,
                release_name,
                release_message,
                commit,
                "commit",
            )
        except Exception as e:
            self.error("\tcannot create release", newline=True)
            catchRemaining(e)

        self.newReleaseObj = newReleaseObj
        return True

    def uploadZip(self):
        newTag = self.newTag
        newReleaseObj = self.newReleaseObj
        dest = self.dest
        org = self.org
        repo = self.repo
        folder = self.folder
        version = self.version
        dataFile = f"{folder}-{version}.zip"
        dataDir = f"{dest}/{org}-release/{repo}"
        dataPath = f"{dataDir}/{dataFile}"

        if not fileExists(dataPath):
            console(f"No release data found: {dataPath}", error=True)
            return False

        try:
            newReleaseObj.upload_asset(
                dataPath, label="", content_type="application/zip", name=dataFile
            )
            console(f"{dataFile} attached to release {newTag}")
        except Exception as e:
            self.error("\tcannot attach zip file to release", newline=True)
            catchRemaining(e)
            return False

        return True

    def getRelease(self):
        r = self.getReleaseObj()
        if not r:
            return None
        return r.tag_name

    def getReleaseObj(self):
        g = self.repoOnline
        if not g:
            return None

        r = None

        try:
            r = g.get_latest_release()
        except Exception as e:
            self.error("\tno releases", newline=True)
            if type(e) is UnknownObjectException:
                self.error("\tcannot find releases", newline=True)
            else:
                catchRemaining(e)
        return r

    def getCommit(self):
        c = self.getCommitObj()
        if not c:
            return None
        return c.sha

    def getCommitObj(self):
        g = self.repoOnline
        if not g:
            return None

        c = None

        try:
            cs = g.get_commits()
            if cs.totalCount:
                c = cs[0]
            else:
                self.error("\tno commits")
        except Exception as e:
            self.error("\tcannot find commits")
            catchRemaining(e)
        return c

    def info(self, msg, newline=True):
        silent = self.silent
        if silent in {VERBOSE, AUTO}:
            console(msg, newline=newline)

    def warning(self, msg, newline=True):
        silent = self.silent
        if silent in {VERBOSE, AUTO, TERSE}:
            console(msg, newline=newline)

    def error(self, msg, newline=True):
        console(msg, error=True, newline=newline)


def releaseData(
    backend,
    org,
    repo,
    folder,
    version,
    increase,
    source=None,
    dest=DOWNLOADS,
):
    """Makes a new data release for a repository.

    !!!caution "GitHub only"
        Only GitHub repositories are supported.
        GitLab support will be implemented if there is a need for it.

    Parameters
    ----------
    backend: string
        `github` or `gitlab` or a GitLab instance such as `gitlab.huc.knaw.nl`.
    org: string
        The organization name of the repo
    repo: string
        The name of the repo
    folder: string
        The subdirectory in the repo that contains the TF files.
        If the TF files are versioned, it is the directory that
        contains the version directories.
        In most cases it is `tf` or it ends in `/tf`.
    version: string
        The version of the data that should be attached as a zip file to the release
    increase:
        The way in which the release version should be increased:

            1 = bump major version;
            2 = bump intermediate version;
            3 = bump minor version

    source: string, optional None
        Path to where the local GitHub clones are stored
    dest: string, optional DOWNLOADS
        Path to where the zipped data should be stored
    """

    if source is None or not source:
        source = (backendRep(GH, "clone"),)

    R = Repo(GH, org, repo, folder, version, increase, source=source, dest=dest)
    return R.newRelease()


def publishRelease(app, increase, message=None, description=None):
    """Publishes a new data release for a TF dataset to GitHub.

    Quite a bit of work will happen.

    The first stage is still off-line, in your local clone.

    First of all, a new commit will be created.

    !!! caution "Save everything
        Be sure that you have saved all your open files and notebooks in this repo,
        otherwise the current state does not end up in the release.

    Then the commit will be tagged with a tag that is higher than the current
    tag. See the `increase` parameter.

    Now we go online.

    The commit, with its tag are pushed to GitHub.

    Subsequently, we access the new tag online and turn it into a release, with a
    title and a description.

    Finally, we zip all essential data of the TF dataset and upload it to the
    release on GitHub.

    For an example, see
    [annotation/mondriaan](https://nbviewer.org/github/annotation/mondriaan/blob/master/programs/publish.ipynb)

    Parameters
    ----------
    app: object
        A loaded TF app.
        Only if the TF app is working with back-end GitHub
    increase: integer
        The way in which the release version should be increased:

            1 = bump major version;
            2 = bump intermediate version;
            3 = bump minor version

    message: string, optional None
        Commit message.
        If None, a boiler plate text, based on the `increase` parameter, is provided.

    description: string, optional None
        Documentation of the release. May be a multiline (markdown) string.
        If None, the `message` parameter will be used.
    """
    repoLocation = app.repoLocation
    branch = app.context.branch

    console(f"Working in repo {ux(repoLocation)} in branch {branch}")

    label = "major" if increase == 1 else "intermediate" if increase == 2 else "minor"
    if message is None:
        message = f"New {label} release"
    if description is None:
        description = message

    console("Make a new commit ...")

    run(["git", "add", "--all", "."], cwd=repoLocation)
    run(["git", "commit", "-m", message], cwd=repoLocation)

    newCommit = (
        check_output(["git", "rev-parse", "HEAD"], cwd=repoLocation)
        .decode("ascii")
        .strip()
    )

    console("Compute a new tag ...")

    latestTag = None

    try:
        latestTag = (
            check_output(["git", "describe", "--tags"], cwd=repoLocation)
            .decode("ascii")
            .strip()
            .split("-", 1)[0]
        )
    except Exception:
        latestTag = ""

    newTag = bumpRelease(latestTag, increase)
    run(["git", "tag", "-a", newTag, "-m", message], cwd=repoLocation)

    console(f"Push the repo to GitHub, including tag {newTag}")

    run(["git", "push", "origin", branch, "--tags"], cwd=repoLocation)

    console("Turn the tag into a release on GitHub with additional data")

    ssl._create_default_https_context = ssl._create_unverified_context

    backend = app.backend
    org = app.context.org
    repo = app.context.repo
    bUrlApi = backendRep(backend, "urlapi")
    bUrlUpload = backendRep(backend, "urlupload")

    releasePayload = {
        "tag_name": newTag,
        "target_commitish": newCommit,
        "name": newTag,
        "body": description,
    }
    person = var("GHPERS")
    headers = {
        "Authorization": f"token {person}",
        "Accept": "application/vnd.github.v3+json",
    }
    createReleaseUrl = f"{bUrlApi}/repos/{org}/{repo}/releases"
    response = requests.post(createReleaseUrl, json=releasePayload, headers=headers)

    console("Create the zip file with the complete data")

    binPath = app.zipAll()
    binFile = fileNm(binPath)

    console("Upload the zip file and attach it to the release on GitHub")

    releaseId = response.json()["id"]
    headers["Content-Type"] = "application/zip"
    uploadUrl = (
        f"{bUrlUpload}/repos/{org}/{repo}/releases/{releaseId}/assets?name={binFile}"
    )
    console(uploadUrl)

    with fileOpen(ex(binPath), mode="rb") as file:
        response = requests.post(uploadUrl, data=file, headers=headers)

    console(f"Release {newTag} created")


def fromString(string):
    commit = None
    release = None
    local = None
    if not string:
        commit = ""
        release = ""
    elif string == "latest":
        commit = None
        release = ""
    elif string == "hot":
        commit = ""
        release = None
    elif string in {"local", "clone"}:
        commit = None
        release = None
        local = string
    elif "." in string or len(string) < 12:
        commit = None
        release = string
    else:
        commit = string
        release = None
    return (commit, release, local)


def readInfo(filePathLocal):
    """Read the commit and release from a file.

    This is assumed to be a file written by `tf.advanced.repo.checkoutRepo()` after
    downloading a local copy of an online folder.

    Parameters
    ----------
    filePathLocal: string
        The path to the file with the checkout information

    Returns
    -------
    tuple
        A pair of commit and release tag. If the file does not exist, these
        values are None. If there is no commit/release info in the file,
        the corresponding member of the tuple is None.
    """
    commit = None
    release = None

    if fileExists(filePathLocal):
        with fileOpen(filePathLocal) as f:
            for line in f:
                string = line.strip()
                (commit, release, local) = fromString(string)

    return (commit, release)


def readInfoDirCommit(folder):
    """Read the commit from the __checkout__.txt file in a folder.

    See `readInfo()`, but now we only pass the folder in which the __checkout__.txt
    file sits, and we only return the commit we find in that file.

    Parameters
    ----------
    folder: string
        The folder in which to look for the file __checkout__.txt

    Returns
    -------
    string
        A commit.
        If the file does not exist, or no commit can be found,  None is returned.
    """
    return readInfo(f"{folder}/{EXPRESS_SYNC}")[0]


class Checkout:
    """Auxiliary class for `checkoutRepo`"""

    @staticmethod
    @staticmethod
    def toString(commit, release, local, backend, source=None, dest=None):
        extra = ""
        if local:
            if source is None:
                source = backendRep(backend, "clone")
            if dest is None:
                dest = backendRep(backend, "cache")

            baseRep = source if local == "clone" else dest
            extra = f" offline under {baseRep}"
        if local == "clone":
            result = "repo clone"
        elif commit and release:
            result = f"r{release}=#{commit}"
        elif commit:
            result = f"#{commit}"
        elif release:
            result = f"r{release}"
        elif commit is None and release is None:
            result = "unknown release or commit"
        elif commit is None:
            result = "latest release"
        elif release is None:
            result = "latest commit"
        else:
            result = "latest release or commit"
        return f"{result}{extra}"

    def __init__(
        self,
        backend,
        org,
        repo,
        relative,
        checkout,
        source,
        dest,
        keep,
        withPaths,
        silent,
        _browse,
        inNb,
        version=None,
        versionOverride=False,
        label="data",
        allowExpress=True,
    ):
        self.backend = backend
        onGithub = backend == GH
        self.onGithub = onGithub

        self.conn = None

        self._browse = _browse
        self.inNb = inNb
        self.label = label
        self.org = org
        self.repo = repo
        self.source = source
        self.dest = dest
        (self.commitChk, self.releaseChk, self.local) = fromString(checkout)
        clone = self.isClone()

        relative = prefixSlash(relative)
        self.relative = relative
        self.version = version
        self.versionOverride = versionOverride
        versionRep = f"/{version}" if version else ""
        self.versionRep = versionRep
        self.dataDir = f"{relative}{versionRep}"

        self.baseLocal = ex(self.dest)
        self.dataRelLocal = f"{org}/{repo}{relative}"
        self.dirPathSaveLocal = f"{self.baseLocal}/{org}/{repo}"
        self.dirPathLocal = f"{self.baseLocal}/{self.dataRelLocal}{versionRep}"
        self.dataPathLocal = f"{self.dataRelLocal}{versionRep}"
        self.filePathLocal = f"{self.dirPathLocal}/{EXPRESS_SYNC}"

        self.baseClone = ex(self.source)
        self.dataRelClone = f"{org}/{repo}{relative}"
        self.dirPathClone = f"{self.baseClone}/{self.dataRelClone}{versionRep}"
        self.dataPathClone = f"{self.dataRelClone}{versionRep}"

        self.dataPath = self.dataRelClone if clone else self.dataRelLocal

        self.keep = keep
        self.withPaths = withPaths

        self.commitOff = None
        self.releaseOff = None
        self.commitOn = None
        self.releaseOn = None
        self.releaseCommitOn = None

        self.silent = silentConvert(silent)

        self.allowExpress = allowExpress

        self.repoOnline = None
        self.localBase = False
        self.localDir = None

        self.connected = False

        if clone:
            self.commitOff = None
            self.releaseOff = None
        else:
            self.fixInfo()
            self.readInfo()

    def isClone(self):
        return self.local == "clone"

    def isOffline(self):
        return self.local in {"clone", "local"}

    def isExpress(self):
        return (
            self.allowExpress
            and self.local is None
            and not self.versionOverride
            and not self.commitChk
            and not self.releaseChk
        )

    def login(self):
        onGithub = self.onGithub
        conn = self.conn
        backend = self.backend

        self.canDownloadSubfolders = False

        backendTech = backendRep(backend, "tech")

        if not Cap.can(backendTech):
            self.conn = None
            return None

        if onGithub:
            person = var("GHPERS")
            if person:
                try:
                    conn = Github(person)
                except Exception as e:
                    self.error(f"Can't make connection to GitHub because of {e}")
                    self.conn = None
                    catchRemaining(e)
                    return None
            else:
                client = var("GHCLIENT")
                secret = var("GHSECRET")
                if client and secret:
                    conn = Github(client_id=client, client_secret=secret)
                else:
                    conn = Github()
        else:
            bUrl = backendRep(backend, "url")
            bMachine = backendRep(backend, "machine")

            person = var(GLPERS(bMachine))
            if person:
                conn = Gitlab(bUrl, private_token=person)
            else:
                conn = Gitlab(bUrl)

            backendVersion = conn.version()
            if (
                not backendVersion
                or backendVersion[0] == "unknown"
                or backendVersion[-1] == "unknown"
            ):
                self.conn = None
                self.error(f"Cannot connect to GitLab instance {backend}\n")
                return

            versionThreshold = (14, 4, 0)

            if backendVersion:
                backendVersion = [
                    int(VERSION_DIGIT_RE.sub(r"\1", vc))
                    for vc in backendVersion[0].split(".")
                ]
                if len(backendVersion) < 3:
                    backendVersion.extend([0] * (3 - len(backendVersion)))

                canDownloadSubfolders = True
                for t, v in zip(versionThreshold, backendVersion):
                    if t != v:
                        canDownloadSubfolders = t < v
                        break

                self.canDownloadSubfolders = canDownloadSubfolders

        self.conn = conn
        return conn

    def connect(self):
        conn = self.conn
        onGithub = self.onGithub
        backend = self.backend
        org = self.org
        repo = self.repo

        bName = backendRep(backend, "name")

        if not conn:
            conn = self.login()
            if not self.conn:
                return

        if onGithub:
            try:
                rate = conn.get_rate_limit().core
                self.info(
                    f"rate limit is {rate.limit} requests per hour,"
                    f" with {rate.remaining} left for this hour"
                )
                if rate.limit < 100:
                    self.warning(
                        f"To increase the rate,"
                        f"see {URL_TFDOC}/advanced/repo.html#github"
                    )

            except Exception as e:
                self.warning("Could not get rate limit details")
                if type(e) is GithubException:
                    self.warning(f"{bName} says: {e}")
                else:
                    catchRemaining(e)

        self.info(
            f"\tconnecting to online {bName} repo {org}/{repo} ... ",
            newline=False,
        )
        repoOnline = None

        if onGithub:
            try:
                repoOnline = conn.get_repo(f"{org}/{repo}")
                self.info("connected")
            except Exception as e:
                self.warning("failed")
                if type(e) is GithubException:
                    self.warning(f"{bName} says: {e}")
                else:
                    catchRemaining(e)
        else:
            try:
                repoOnline = conn.projects.get(f"{org}/{repo}")
                self.info("connected")
            except Exception as e:
                self.warning("failed")
                if type(e) is GitlabGetError:
                    self.warning(f"{bName} says: {e}")
                else:
                    catchRemaining(e)

        self.repoOnline = repoOnline

    def info(self, msg, newline=True):
        silent = self.silent
        if silent in {VERBOSE, AUTO}:
            console(msg, newline=newline)

    def warning(self, msg, newline=True):
        silent = self.silent
        if silent in {VERBOSE, AUTO, TERSE}:
            console(msg, newline=newline)

    def error(self, msg, newline=True):
        console(msg, error=True, newline=newline)

    def display(self, msg, msgPlain):
        inNb = self.inNb
        silent = self.silent
        if silent in {VERBOSE, AUTO, TERSE}:
            if inNb is not None:
                dh(msg, inNb=inNb)
            else:
                console(msgPlain)

    def possibleError(self, msg, showErrors, again=False, indent="\t", newline=False):
        if showErrors:
            self.error(msg, newline=newline)
        else:
            self.warning(msg, newline=newline)
            if again:
                self.warning(f"{indent}Will try something else")

    def makeSureLocal(self, attempt=False):
        _browse = self._browse
        backend = self.backend
        label = self.label

        isExpr = self.isExpress()

        if isExpr:
            success = self.downloadComplete()
            if success:
                self.localBase = self.baseLocal
                self.localDir = self.dataPath
                state = "latest release"
                offString = self.toString(
                    self.commitOff,
                    self.releaseOff,
                    self.local,
                    backend,
                    dest=self.dest,
                    source=self.source,
                )
                labelEsc = htmlEsc(label)
                stateEsc = htmlEsc(state)
                offEsc = htmlEsc(offString)
                loc = f"{self.localBase}/{self.localDir}{self.versionRep}"
                locRep = ux(loc)
                locEsc = htmlEsc(locRep)
                if _browse:
                    self.info(
                        f"Using {label} in {self.localBase}/{self.localDir}{self.versionRep}:"
                    )
                    self.info(f"\t{offString} ({state})")
                else:
                    self.display(
                        (
                            f'<b title="{stateEsc}">{labelEsc}:</b>'
                            f' <span title="{offEsc}">{locEsc}</span>'
                        ),
                        f"{label}: {locRep}",
                    )
                return

        self.fetchInfo()

        offline = self.isOffline()
        clone = self.isClone()

        cChk = self.commitChk
        rChk = self.releaseChk
        cOff = self.commitOff
        rOff = self.releaseOff
        cOn = self.commitOn
        rOn = self.releaseOn
        rcOn = self.releaseCommitOn

        askExact = rChk or cChk
        askExactRelease = rChk
        askExactCommit = cChk
        askLatest = not askExact and (rChk == "" or cChk == "")
        askLatestAny = rChk == "" and cChk == ""
        askLatestRelease = rChk == "" and cChk is None
        askLatestCommit = cChk == "" and rChk is None

        isExactReleaseOff = rChk and rChk == rOff
        isExactCommitOff = cChk and cChk == cOff
        isExactReleaseOn = rChk and rChk == rOn
        isExactCommitOn = cChk and cChk == cOn
        isLatestRelease = rOff and rOff == rOn or cOff and cOff == rcOn
        isLatestCommit = cOff and cOff == cOn

        isLocal = (
            askExactRelease
            and isExactReleaseOff
            or askExactCommit
            and isExactCommitOff
            or askLatestAny
            and (isLatestRelease or isLatestCommit)
            or askLatestRelease
            and isLatestRelease
            or askLatestCommit
            and isLatestCommit
        )
        mayLocal = (
            askLatestAny
            and (rOff or cOff)
            or askLatestRelease
            and rOff
            or askLatestCommit
            and cOff
        )
        canOnline = self.repoOnline
        isOnline = canOnline and (
            askExactRelease
            and isExactReleaseOn
            or askExactCommit
            and isExactCommitOn
            or askLatestAny
            or askLatestRelease
            or askLatestCommit
        )

        if offline:
            if clone:
                dirPath = self.dirPathClone
                self.localBase = self.baseClone if dirExists(dirPath) else False
            else:
                self.localBase = (
                    self.baseLocal
                    if (
                        cChk
                        and cChk == cOff
                        or cChk is None
                        and cOff
                        or rChk
                        and rChk == rOff
                        or rChk is None
                        and rOff
                    )
                    else False
                )
            if not self.localBase:
                method = self.warning if attempt else self.error
                method(f"The requested {label} is not available offline")
                # base = self.baseClone if clone else self.baseLocal
                dirVersion = self.dirPathClone if clone else self.dirPathLocal
                # method(f"\t{base}/{self.dataPath} not found")
                method(f"\t{dirVersion} not found")
        else:
            if isLocal:
                self.localBase = self.baseLocal
            else:
                if not canOnline:
                    if askLatest:
                        if mayLocal:
                            self.warning(f"The offline {label} may not be the latest")
                            self.localBase = self.baseLocal
                        else:
                            self.error(
                                f"The requested {label} is not available offline"
                            )
                    else:
                        self.warning(f"The requested {label} is not available offline")
                        self.error("No online connection")
                elif not isOnline:
                    self.error(f"The requested {label} is not available online")
                else:
                    self.localBase = self.baseLocal if self.download() else False

        if self.localBase:
            self.localDir = self.dataPath
            state = (
                "requested"
                if askExact
                else (
                    "latest release"
                    if rChk == "" and canOnline and self.releaseOff
                    else (
                        "latest? release"
                        if rChk == "" and not canOnline and self.releaseOff
                        else (
                            "latest commit"
                            if cChk == "" and canOnline and self.commitOff
                            else (
                                "latest? commit"
                                if cChk == "" and not canOnline and self.commitOff
                                else (
                                    "local release"
                                    if self.local == "local" and self.releaseOff
                                    else (
                                        "local commit"
                                        if self.local == "local" and self.commitOff
                                        else (
                                            "local github"
                                            if self.local == "clone"
                                            else "for whatever reason"
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
            offString = self.toString(
                self.commitOff,
                self.releaseOff,
                self.local,
                backend,
                dest=self.dest,
                source=self.source,
            )
            labelEsc = htmlEsc(label)
            stateEsc = htmlEsc(state)
            offEsc = htmlEsc(offString)
            loc = f"{self.localBase}/{self.localDir}{self.versionRep}"
            locRep = ux(loc)
            locEsc = htmlEsc(locRep)

            if _browse:
                self.info(
                    f"Using {label} in {self.localBase}/{self.localDir}{self.versionRep}:"
                )
                self.info(f"\t{offString} ({state})")
            else:
                self.display(
                    (
                        f'<b title="{stateEsc}">{labelEsc}:</b>'
                        f' <span title="{offEsc}">{locEsc}</span>'
                    ),
                    f"{label}: {locRep}",
                )

    @staticmethod
    def retrieve(url):
        response = None
        msg = None

        try:
            response = ur.urlopen(url)
            status = response.status
        except HTTPError as e:
            msg = str(e)
            status = 500

        if status != 200:
            result = (False, status, msg or "ERROR")
        else:
            data = response.read()
            result = (True, status, data)

        return result

    def downloadComplete(self):
        ssl._create_default_https_context = ssl._create_unverified_context

        backend = self.backend
        org = self.org
        repo = self.repo
        bUrl = backendRep(backend, "url")
        repoUrl = f"{bUrl}/{org}/{repo}"
        releaseUrlPre = (
            f"{repoUrl}/releases/latest"
            if backend == GH
            else f"{repoUrl}/-/releases/permalink/latest"
        )
        (good, info) = getFinalUrl(releaseUrlPre)
        if not good:
            console(f"Cannot follow {releaseUrlPre}: {info}", error=True)
            return False

        releaseUrl = info
        releaseOn = releaseUrl.rstrip("/").split("/")[-1]
        self.releaseOn = releaseOn
        releaseOff = self.releaseOff
        if releaseOff == releaseOn:
            self.display(
                f"Status: latest release online <b>{releaseOn}</b> is locally available",
                f"Status: latest release online {releaseOn} is locally available",
            )
            return True

        self.display(
            f"Status: latest release online <b>{releaseOn}</b> versus "
            f"<b>{releaseOff}</b> locally",
            f"Status: latest release online {releaseOn} versus "
            f"{releaseOff} locally",
        )
        self.display(
            "downloading app, main data and requested additions ...",
            "downloading app, main data and requested additions ...",
        )
        patt = "/tag/" if backend == GH else "/releases/"
        subst = "/download/" if backend == GH else "/archive/"
        assetUrl = releaseUrl.replace(patt, subst) + f"/{APP_EXPRESS_ZIP}"

        if backend != GH:
            # At the moment GitLab offers a zip of the whole
            # repo when complete.zip is not attached.
            # That zip file is not useful.
            return False

        try:
            r = requests.get(assetUrl, allow_redirects=True)
            zf = r.content
            zf = io.BytesIO(zf)
        except Exception as e:
            msg = f"\t{str(e)}\n\tcould not download {APP_EXPRESS_ZIP} "
            self.possibleError(msg, True, again=True)
            return False

        cwd = getCwd()
        destZip = self.baseLocal

        try:
            z = ZipFile(zf)
            if not dirExists(destZip):
                dirMake(destZip)
            chDir(destZip)
            extractPrecise(z)
            chDir(cwd)
            dirRemove("__MACOSX")
        except Exception as e:
            msg = f"\tcould not save corpus data to {destZip} "
            console(str(e), error=True)
            self.possibleError(msg, showErrors=True, again=True)
            chDir(cwd)
            return False

        return True

    def download(self):
        cChk = self.commitChk
        rChk = self.releaseChk

        fetched = False
        if rChk is not None:
            fetched = self.downloadRelease(rChk, showErrors=cChk is None)
        if not fetched and cChk is not None:
            fetched = self.downloadCommit(cChk, showErrors=True)

        if fetched:
            self.writeInfo()
        return fetched

    def downloadRelease(self, release, showErrors=True):
        cChk = self.commitChk

        r = self.getReleaseObj(release, showErrors=showErrors)
        if not r:
            return False

        onGithub = self.onGithub
        version = self.version
        g = self.repoOnline

        (commit, release) = self.getReleaseFromObj(r)

        fetched = False

        if onGithub:
            assets = None
            try:
                assets = r.get_assets()
            except Exception:
                pass
            assetUrl = None
            versionRep3 = f"-{version}" if version else ""
            relativeFlat = self.relative.removeprefix("/").replace("/", "-")
            dataFile = f"{relativeFlat}{versionRep3}.zip"
            if assets and assets.totalCount > 0:
                for asset in assets:
                    if asset.name == dataFile:
                        assetUrl = asset.browser_download_url
                        break
            if assetUrl:
                fetched = self.downloadZip(assetUrl, showErrors=False)
            if not fetched:
                thisShowErrors = not cChk == ""
                fetched = self.downloadCommit(commit, showErrors=thisShowErrors)
        else:
            fetched = self.downloadZip(g, shiftUp=True, commit=commit, showErrors=True)

        if fetched:
            self.commitOff = commit
            self.releaseOff = release
        return fetched

    def downloadCommit(self, commit, showErrors=True):
        c = self.getCommitObj(commit)
        if not c:
            return False

        commit = self.getCommitFromObj(c)

        fetched = self.downloadDir(commit, exclude=r"\.tfx", showErrors=showErrors)
        if fetched:
            self.commitOff = commit
            self.releaseOff = None
        return fetched

    def downloadZip(self, where, shiftUp=False, commit=None, showErrors=True):
        # commit parameter only supported for GitLab
        conn = self.conn
        backend = self.backend
        label = self.label
        repo = self.repo
        dataDir = self.dataDir
        canDownloadSubfolders = self.canDownloadSubfolders
        dirPathLocal = self.dirPathLocal
        withPaths = self.withPaths

        dataUrl = None
        g = None

        if type(where) is str:
            dataUrl = where
            notice = where
            again = True
        else:
            g = where
            notice = backendRep(backend, "name")
            again = False

        self.info(f"\tdownloading from {notice} ... ")

        try:
            if dataUrl is not None:
                r = requests.get(dataUrl, allow_redirects=True)
                zf = r.content
            elif g is not None:
                if canDownloadSubfolders:
                    # zf = g.repository_archive(format="zip", sha=commit, path=dataDir)
                    response = conn.http_get(
                        f"/projects/{g.id}/repository/archive.zip",
                        query_data=dict(sha=commit, path=dataDir),
                        raw=True,
                    )
                    zf = response.content
                    if len(zf) == 0:
                        self.possibleError(
                            f"No directory {dataDir} in #{commit}",
                            showErrors,
                            again=False,
                        )
                        msg = "\tFailed"
                        self.possibleError(msg, showErrors=showErrors, newline=True)
                        return False
                else:
                    zf = g.repository_archive(format="zip", sha=commit)
            zf = io.BytesIO(zf)
        except Exception as e:
            msg = f"\t{str(e)}\n\tcould not download from {notice}"
            self.possibleError(msg, showErrors, again=again)
            return False

        self.info(f"\tsaving {label}")

        cwd = getCwd()
        destZip = dirNm(dirPathLocal) if shiftUp and withPaths else dirPathLocal
        good = True

        if g:
            gitlabSlugRe = re.compile(f"^{repo}(?:-(?:master|main))?-[^/]*/")
        try:
            z = ZipFile(zf)
            initTree(destZip, fresh=not self.keep)
            chDir(destZip)

            if withPaths:
                if g:
                    nItems = 0
                    for zInfo in z.infolist():
                        zInfo.filename = gitlabSlugRe.sub("", zInfo.filename) or "/"
                        if zInfo.filename[-1] == "/":
                            continue
                        if zInfo.filename.startswith("__MACOS"):
                            continue
                        if not canDownloadSubfolders:
                            if not zInfo.filename.startswith(dataDir):
                                continue
                        z.extract(zInfo)
                        nItems += 1
                    if nItems == 0:
                        self.possibleError(
                            f"No directory {dataDir} in #{commit}",
                            showErrors,
                            again=False,
                        )
                        good = False
                else:
                    z.extractall()
                    dirRemove("__MACOSX")
            else:
                nItems = 0
                for zInfo in z.infolist():
                    if g:
                        zInfo.filename = gitlabSlugRe.sub("", zInfo.filename) or "/"
                    if zInfo.filename[-1] == "/":
                        continue
                    if zInfo.filename.startswith("__MACOS"):
                        continue
                    if (
                        g
                        and not canDownloadSubfolders
                        and not zInfo.filename.startswith(dataDir)
                    ):
                        continue
                    zInfo.filename = fileNm(zInfo.filename)
                    z.extract(zInfo)
                    nItems += 1
                if nItems == 0:
                    msg = f"#{commit}" if g else notice
                    self.possibleError(
                        f"No directory {dataDir} in {msg}",
                        showErrors,
                        again=False,
                        newline=True,
                    )
                    msg = "\tFailed"
                    self.possibleError(msg, showErrors=showErrors, newline=True)
                    good = False
        except Exception as e:
            msg = f"\tcould not save {label} to {destZip}"
            console(str(e), error=True)
            self.possibleError(msg, showErrors=showErrors, again=True, newline=True)
            chDir(cwd)
            return False
        chDir(cwd)
        return good

    def downloadDir(self, commit, exclude=None, showErrors=False):
        g = self.repoOnline
        if not g:
            return None

        onGithub = self.onGithub
        backend = self.backend

        destDir = f"{self.dirPathLocal}"
        destSave = f"{self.dirPathSaveLocal}"
        initTree(destDir, fresh=not self.keep)

        excludeRe = re.compile(exclude) if exclude else None

        good = True

        if onGithub:

            def _downloadDir(subPath, level=0):
                nonlocal good
                if not good:
                    return

                lead = "\t" * level
                try:
                    contents = g.get_contents(subPath, ref=commit)
                except Exception as e:
                    if UnknownObjectException:
                        msg = (
                            f"{lead}No directory {subPath} in "
                            f"{self.toString(commit, None, False, backend)}"
                        )
                        self.possibleError(msg, showErrors, again=True, indent=lead)
                    else:
                        catchRemaining(e)

                    good = False
                    return

                for content in contents:
                    thisPath = content.path
                    self.info(f"\t{lead}{thisPath}...", newline=False)
                    if exclude and excludeRe.search(thisPath):
                        self.info("excluded")
                        continue
                    if content.type == "dir":
                        self.info("directory")
                        dirMake(f"{destSave}/{thisPath}")
                        _downloadDir(thisPath, level + 1)
                    else:
                        try:
                            fileContent = g.get_git_blob(content.sha)
                            fileData = base64.b64decode(fileContent.content)
                            fileDest = f"{destSave}/{thisPath}"
                            with fileOpen(fileDest, mode="wb") as fd:
                                fd.write(fileData)
                            self.info("downloaded")
                        except Exception as e:
                            if type(e) is GithubException:
                                msg = "error"
                                self.possibleError(
                                    msg, showErrors, again=True, indent=lead
                                )
                            else:
                                catchRemaining(e)
                            good = False

            _downloadDir(self.dataDir, 0)

        else:
            good = self.downloadZip(g, shiftUp=True, commit=commit, showErrors=True)

        if good:
            self.info("\tOK")
        else:
            if onGithub:
                msg = "\tFailed"
                self.possibleError(
                    msg, showErrors=showErrors if onGithub else True, newline=True
                )

        return good

    def getRelease(self, release, showErrors=True):
        r = self.getReleaseObj(release, showErrors=showErrors)
        if not r:
            return None
        return self.getReleaseFromObj(r)

    def getCommit(self, commit):
        c = self.getCommitObj(commit)
        if not c:
            return None
        return self.getCommitFromObj(c)

    def getReleaseObj(self, release, showErrors=True):
        g = self.repoOnline
        if not g:
            return None

        onGithub = self.onGithub

        r = None
        msg = f' tagged "{release}"' if release else "s"

        if onGithub:
            try:
                r = g.get_release(release) if release else g.get_latest_release()
            except Exception as e:
                self.possibleError(
                    f"\tcannot find release{msg}", showErrors, newline=True
                )
                if type(e) is not UnknownObjectException:
                    catchRemaining(e)
        else:
            try:
                if release:
                    r = g.releases.get(release)
                else:
                    releases = g.releases.list(all=True)
                    r = (
                        sorted(releases, key=lambda r: r.released_at)[-1]
                        if releases
                        else None
                    )
            except Exception as e:
                r = None
                console(str(e), error=True)
            if r is None:
                self.possibleError(
                    f"\tcannot find release{msg}", showErrors, newline=True
                )
        return r

    def getCommitObj(self, commit):
        g = self.repoOnline
        if not g:
            return None

        onGithub = self.onGithub

        c = None
        msg = f' with hash "{commit}"' if commit else "s"

        if onGithub:
            try:
                cs = g.get_commits(sha=commit) if commit else g.get_commits()
                if cs.totalCount:
                    c = cs[0]
                else:
                    self.error(f"\tcannot find commit{msg}")
            except Exception as e:
                self.error(f"\tcannot find commit{msg}")
                console(str(e), error=True)
        else:
            try:
                cs = g.commits.list(all=True)
                if not len(cs):
                    self.error(f"\tno commit{msg}")
                else:
                    cs = sorted(cs, key=lambda x: x.created_at)
                    if commit:
                        for com in cs:
                            if com.id == commit:
                                c = com
                                break
                    else:
                        if len(cs):
                            c = cs[-1]
                    if c is None:
                        self.error(f"\tcannot find commit{msg}")
            except Exception as e:
                self.error(f"\tcannot find commit{msg}")
                console(str(e), error=True)
        return c

    def getReleaseFromObj(self, r):
        g = self.repoOnline
        if not g:
            return None

        onGithub = self.onGithub

        release = r.tag_name

        if onGithub:
            ref = g.get_git_ref(f"tags/{release}")
            commit = ref.object.sha
        else:
            commit = r.commit["id"]
        return (commit, release)

    def getCommitFromObj(self, c):
        g = self.repoOnline
        if not g:
            return None

        onGithub = self.onGithub

        return c.sha if onGithub else c.id

    def fetchInfo(self):
        if self.isOffline():
            return

        if self.connected:
            return

        self.connect()

        g = self.repoOnline
        if not g:
            return

        self.commitOn = None
        self.releaseOn = None
        self.releaseCommitOn = None
        if self.releaseChk is not None:
            result = self.getRelease(self.releaseChk, showErrors=self.commitChk is None)
            if result:
                (self.releaseCommitOn, self.releaseOn) = result
        if self.commitChk is not None:
            result = self.getCommit(self.commitChk)
            if result:
                self.commitOn = result

        self.connected = True

    def fixInfo(self):
        sDir = self.dirPathLocal
        if not dirExists(sDir):
            return
        for sFile in EXPRESS_SYNC_LEGACY:
            sPath = f"{sDir}/{sFile}"
            if fileExists(sPath):
                goodPath = f"{sDir}/{EXPRESS_SYNC}"
                if fileExists(goodPath):
                    fileRemove(sPath)
                else:
                    fileMove(sPath, goodPath)

    def readInfo(self):
        (commit, release) = readInfo(self.filePathLocal)
        if commit:
            self.commitOff = commit
        if release:
            self.releaseOff = release

    def writeInfo(self, release=None, commit=None):
        releaseOff = self.releaseOff if release is None else release
        commitOff = self.commitOff if commit is None else commit
        dirMake(self.dirPathLocal)
        with fileOpen(self.filePathLocal, mode="w") as f:
            if releaseOff:
                f.write(f"{releaseOff}\n")
            if commitOff:
                f.write(f"{commitOff}\n")


def checkoutRepo(
    backend,
    _browse=False,
    org="annotation",
    repo="banks",
    folder=f"/{RELATIVE}",
    version="",
    versionOverride=False,
    checkout="",
    allowExpress=True,
    source=None,
    dest=None,
    withPaths=True,
    keep=True,
    silent=SILENT_D,
    label="data",
):
    """Checks out TF data from an (online) repository.

    The copy may be taken from any point in the commit history of the online repo.

    If you call this function, it will check whether the requested data is already
    on your computer in the expected location.
    If not, it may check whether the data is online and if so, download it to the
    expected location.

    Parameters
    ----------
    backend: string
        `github` or `gitlab` or a GitLab instance such as `gitlab.huc.knaw.nl`.

    org: string, optional "annotation"
        The *org* on GitHub or the group on GitLab

    repo: string, optional "banks"
        The *repo* on GitHub or the project on GitLab

    folder: string, optional /tf
        The subdirectory in the repo that contains the TF files.
        If the TF files are versioned, it is the directory that
        contains the version directories.
        In most cases it is `tf` or it ends in `/tf`.

    version: string, optional ""
        The version of the TF feature data

    versionOverride: boolean, optional False
        Whether a non-standard version has been requested

    checkout: string, optional the mepty string
        From which version/release/local copy we should extract the data.

        *   `""`: whatever you have locally in `~/text-fabric-data`.
            If there is no data there, data will be downloaded.
        *   `local`: whatever you have locally in `~/text-fabric-data`.
            If there is no data there, you get an error message.
        *   `clone`: whatever you have locally as a GitHub / GitLab clone
            If there is no data there, you get an error message.
        *   `latest`: make sure the latest release has been fetched from online
        *   `hot`: make sure the latest commit has been fetched from online
        *   `vx.y.z`: make sure this specific release has been fetched from online
        *   `1234567890abcdef`: make sure this specific commit
            has been fetched from online

        See the
        [repo](https://nbviewer.jupyter.org/github/annotation/banks/blob/master/tutorial/repo.ipynb)
        notebook for an exhaustive demo of all the checkout options.

    allowExpress: boolean, optional True
        Whether an express download of all data is allowed.
        Typically, this should be set to True for app and main data and standard module
        data, and False for optional module data.

    source: string, optional empty string
        The base of your local repository clones.
        If given, it overrides the semi-baked in `~/github` value.

    dest: string, optional empty string
        The base of your local cache of downloaded TF feature files.
        If given, it overrides the semi-baked in `~/text-fabric-data` value.

    withPaths: boolean, optional True
        Whether the data will be saved without the directory structure
        of files that are being downloaded.

    keep: boolean, optional True
        If False, the destination directory will be cleared
        before a download takes place.

    silent: string, optional tf.core.timestamp.SILENT_D
        See `tf.core.timestamp.Timestamp`

    label: string, optional data
        If passed, it will will change the word "data" in info messages
        to what you choose.
        We use `label='app'` when we use this function to checkout the code
        of a corpus app.

    Returns
    -------
    tuple

    *   `commitOffline` is the commit hash of the data you have offline afterwards
    *   `releaseOffline` is the release tag of the data you have offline afterwards
    *   `kindLocal` indicates whether an online check has been performed:
        it is `None` if there has been an online check. Otherwise it is
        `clone` if the data is in your `~/github` directory else it is `local`.
    *   `localBase` where the data is under: `~/github` or `~/text-fabric-data`,
        or whatever you have passed as `source` and `dest`.
    *   `localDir` relative path from `localBase` to your data.
        If your data has versions, `localDir` points to directory that has the versions,
        not to a specific version.

    Your local copy can be found:

    *   in the cache under your `~/text-fabric-data`, and from
        there under `backend/org/repo` where `backend` is `github` or `gitlab` or
        the server name of a GitLab instance.

    or

    *   in the place where you store your clones from GitHub / GitLab:
        `~/github` or `~/gitlab` or `~/backend`
        (whatever the value of the `backend` parameter is.
        From there it is under `org/repo`.

    The actual feature files are in `folder/version` if there is a `version`,
    else `folder`.

    """

    inNb = runsInNotebook()
    silent = silentConvert(silent)

    if source is None:
        source = backendRep(backend, "clone")

    if dest is None:
        dest = backendRep(backend, "cache")

    def resolve(chkout, attempt=False):
        rData = Checkout(
            backend,
            org,
            repo,
            folder,
            chkout,
            source,
            dest,
            keep,
            withPaths,
            silent,
            _browse,
            inNb,
            version=version,
            versionOverride=versionOverride,
            label=label,
            allowExpress=allowExpress,
        )
        rData.makeSureLocal(attempt=attempt)
        return (
            (
                rData.commitOff,
                rData.releaseOff,
                rData.local,
                rData.localBase,
                rData.localDir,
            )
            if rData.localBase
            else (None, None, False, False, None)
        )

    if checkout == "":
        rData = resolve("local", attempt=True)
        if rData[3]:
            return rData

    return resolve(checkout)
