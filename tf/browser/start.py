"""
# Start the TF browser

What the `tf` script does is the same as:

``` sh
python -m tf.browser.start
```

During start up the following happens:

Load TF corpus data.
:    This can take a while.
    When it has loaded the data, it hands the TF API over to the web server.

Start TF web server
:   With the TF data in hand the TF web server is started.

Load web page
:   After a short while, the default web browser will be started
    with a URL and port at which the
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

The following arguments of the `use()` function can be used on the command-line,
prepended with `--`:

*   `--checkout`
*   `--mod`
*   `--set`
*   `--locations`
*   `--modules`
*   `--version`

The following argument does not come from the `use()` function:

*   `--tool`

If you pass `--tool=ner` for example, the TF browser opens navigated to the
`ner` tool page (named entity annotator).

## Implementation notes

Different corpora will use different ports for web server.

The ports are computed from the `org`, `repo` and `path` arguments with which
`tf` is called.

*   Invocations of `tf` with different corpora lead to different ports
*   Repeated invocations of `tf` with the same corpus lead to the same port,
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


TOOLS = set(
    """
    ner
""".strip().split()
)


HELP = f"""
USAGE

tf
tf --help
tf -v

tf org/repo
tf app:/path/to/app --locations=locations-string [--modules=modules-string]

where all args are optional and args have one of these forms:

  -noweb
  --tool={"|".join(sorted(TOOLS))}
  --checkout=specifier
  --backend=backend name (github, gitlab, gitlab.domain)
  --mod=modules
  --set=file
  --modules=modules-string
  --locations=locations-string
  --version=version

Additional options

  --chrome
    Prefer to open the TF interface in the Google Chrome browser. If Chrome is not
    installed, it opens in the default browser.
    If this option is not passed, the interface opens in the default browser.
  debug
    The web server runs in debug mode: if the TF code is modified, the web server
    reloads itself automatically.
    Only relevant for TF developers.

EFFECT

See https://annotation.github.io/text-fabric/tf/browser/start.html

If called without

```
org/repo, --backend=xxx, --checkout=yyy,
```

the current directory is used to determine a clone of a repo containing a TF dataset.
If that is found, the TF browser will be started for that dataset.

If an `org/repo` is given, a TF browser for that `org/repo` is started.

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

    forceChrome = False
    debugRep = "nodebug"

    if "--chrome" in cargs:
        forceChrome = True

    if "debug" in cargs:
        debugRep = "debug"

    cargs = [c for c in cargs if c not in {"debug", "--chrome"}]

    newCargs = []
    tool = None

    for x in cargs:
        if x.startswith("--tool="):
            tool = x[7:]
            if tool not in TOOLS:
                console(f'Unrecognized tool: "{tool}"')
                console(f"""Recognized tools are: {", ".join(sorted(TOOLS))}""")
                return
        else:
            newCargs.append(x)

    cargs = newCargs

    portWeb = getPort(argApp(cargs, True))
    noweb = argNoweb(cargs)

    isWin = system().lower().startswith("win")
    pythonExe = "python" if isWin else "python3"

    processWeb = Popen(
        [
            pythonExe,
            "-m",
            "tf.browser.web",
            debugRep,
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
            opened = False
            new = 0
            toolUrl = "" if tool is None else f"/{tool}/index"
            url = f"{PROTOCOL}{HOST}:{portWeb}{toolUrl}"
            autoraise = True
            title = "Opening corpus in "
            marker = "\no-o-o\n"

            if forceChrome:
                browser = "Chrome browser"
                try:
                    controller = webbrowser.get("chrome")
                    console(f"{marker}{title}{browser}{marker}")
                    opened = controller.open(url, new=new, autoraise=autoraise)
                except Exception:
                    opened = False

            if not opened:
                browser = "default browser"
                extra = " instead" if forceChrome else ""
                try:
                    console(f"{marker}{title}{browser}{extra}{marker}")
                    opened = webbrowser.open(url, new=new, autoraise=autoraise)
                except Exception:
                    opened = False

            if not opened:
                if processWeb:
                    processWeb.terminate()
                console("TF web server has stopped")

    stopped = not portWeb or (processWeb and processWeb.poll())

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
