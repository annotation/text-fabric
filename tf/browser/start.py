"""
# Start the TF browser

What the `text-fabric` script does is the same as:

```sh
python -m tf.browser.start
```

During start up the following happens:

Load TF corpus data.
:    This can take a while.
    When it has loaded the data, it hands the TF API over to the webserver.

Start TF web server
:   With the TF data in hand the TF web server is started.

Load web page
:   After a short while, the default web browser will be started
    with a url and port at which the
    web server will listen. You see your browser being started up
    and the TF page being loaded.

Wait
:   The script now waits till the web server is finished.
    You finish it by pressing Ctrl-C, and if you have used the `-d` flag,
    you have to press it twice.

## Additional arguments

You can direct the loading of corpus data by means of additional arguments,
analogously to the `use()` command, documented in `tf.about.usefunc`.

The main argument specifies the data source in the same way as the
first argument of the `use()` function:

*   `org/repo`
*   `org/repo:specifier`
*   `app:path/to/app`
*   `data:path/to/data`

The following arguments of the `use()` function can be used on the command line,
prepended with `--`:

*   `--checkout`
*   `--mod`
*   `--set`
*   `--locations`
*   `--modules`
*   `--version`

## Implementation notes

Different corpora will use different ports for webserver.

The ports are computed from the `org`, `repo` and `path` arguments with which
text-fabric is called.

*   Invocations of text-fabric with different corpora lead to different ports
*   Repeated invocations of text-fabric with the same corpus lead to the same port,
    provided the previous invocation has been terminated.
"""

import sys

import webbrowser
from time import sleep
from subprocess import Popen, PIPE
from platform import system

from ..core.helpers import console
from ..parameters import BANNER, PROTOCOL, HOST

from .command import argNoweb, argApp, getPort
from .web import TF_DONE, TF_ERROR


HELP = """
USAGE

tf
tf --help
tf -v

tf org/repo
tf app:/path/to/app --locations=locations-string [--modules=modules-string]

The following ones do the same but are deprecated:

text-fabric
text-fabric --help
text-fabric -v

text-fabric org/repo
text-fabric app:/path/to/app --locations=locations-string [--modules=modules-string]

where all args are optional and args have one of these forms:

  -noweb
  --checkout=specifier
  --backend=backend name (github, gitlab, gitlab.domain)
  --mod=modules
  --set=file
  --modules=modules-string
  --locations=locations-string
  --version=version

EFFECT

See https://annotation.github.io/text-fabric/tf/browser/start.html

If called without org/repo, --backend=xxx, --checkout=yyy,
the current directory is used to determine a clone of a repo containing a TF dataset.
If that is found, the TF browser will be started for that dataset.

If an org/repo is given, a TF browser for that org/repo is started.

The default browser will be opened, except when -noweb is passed.

MISCELLANEOUS

-noweb Do not start the default browser

CLEAN UP

If you press Ctrl-C the web server is stopped.
"""

FLAGS = set(
    """
    -noweb
""".strip().split()
)


def main(cargs=sys.argv[1:]):
    console(BANNER)
    if len(cargs) >= 1 and any(
        arg in {"--help", "-help", "-h", "?", "-?"} for arg in cargs
    ):
        console(HELP)
        return
    if len(cargs) >= 1 and any(arg == "-v" for arg in cargs):
        return

    portWeb = getPort(argApp(cargs, True))
    noweb = argNoweb(cargs)

    isWin = system().lower().startswith("win")
    pythonExe = "python" if isWin else "python3"

    processWeb = Popen(
        [
            pythonExe,
            "-m",
            "tf.browser.web",
            str(portWeb),
            *cargs,
        ],
        stdout=PIPE,
        bufsize=0,
        encoding="utf8",
    )
    console("Loading TF corpus data. Please wait ...")
    for line in processWeb.stdout:
        sys.stdout.write(line)
        if line.rstrip() == TF_ERROR:
            return
        if line.rstrip() == TF_DONE:
            break

    sleep(1)
    stopped = processWeb.poll()

    if not noweb:
        sleep(2)
        stopped = not portWeb or (processWeb and processWeb.poll())
        if not stopped:
            console("Opening corpus in browser")
            controller = webbrowser.get("chrome")
            controller.open(
                f"{PROTOCOL}{HOST}:{portWeb}",
                new=0,
                autoraise=True,
            )

    stopped = (not portWeb or (processWeb and processWeb.poll()))

    if not stopped:
        try:
            console("Press <Ctrl+C> to stop the TF browser")
            if processWeb:
                for line in processWeb.stdout:
                    sys.stdout.write(line)
        except KeyboardInterrupt:
            if processWeb:
                processWeb.terminate()
            console("TF web server has stopped")


if __name__ == "__main__":
    main()
