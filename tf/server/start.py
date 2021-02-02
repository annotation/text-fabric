"""
# Start kernel and webserver

What the `text-fabric` script does is the same as:

```sh
python3 -m tf.server.start
```

During start up the following happens:

Kill previous processes
:   The system is searched for non-terminated incarnations of the processes
    it wants to start up.
    If they are encountered, they will be killed, so that they cannot prevent
    a successful start up.

Start TF kernel
:   A `tf.server.kernel` is started.
    This process loads the bulk of the TF data, so it can take a while.
    When it has loaded the data, it sends out a message that loading is done,
    which is picked up by the script.

Start TF web server
:   A short while after receiving the "data loading done" message,
    the TF web server is started.

    !!! hint "Debug mode"
        If you have passed `-d` to the `text-fabric` script,
        the **Flask** web server will be started in debug and reload mode.
        That means that if you modify `web.py` or a module it imports,
        the web server will reload itself automatically.
        When you refresh the browser you see the changes.
        If you have changed templates, the css, or the javascript,
        you should do a "refresh from origin".

Load web page
:   After a short while, the default web browser will be started
    with a url and port at which the
    web server will listen. You see your browser being started up
    and the TF page being loaded.

Wait
:   The script now waits till the web server is finished.
    You finish it by pressing Ctrl-C, and if you have used the `-d` flag,
    you have to press it twice.

Terminate the TF kernel"
:   At this point, the `text-fabric` script will terminate the TF kernel.

Clean up
:   Now all processes that have started up have been killed.

    If something went wrong in this sequence, chances are that a process keeps running.
    It will be terminated next time you call the `text-fabric`.

!!! hint "You can kill too"
    If you run

```sh
text-fabric -k
```

all tf-browser-related processes will be killed.

```sh
text-fabric -k ddd
```

will kill all such processes as far as they are for data source `ddd`.

## Implementation notes

Different corpora will use different ports for the kernel and webserver communication.

The ports are computed from the arguments with which text-fabric is called.

That is done by the [crc32](https://docs.python.org/3.7/library/zlib.html#zlib.crc32) function.
There is no guarantee that collisions occur, and that the ports computed this way are free.
So we will look for the first available port after this.

On the whole, the following things are fairly well taken care of:

*   Invocations of text-fabric with different arguments lead to different ports
*   Repeated invocations of text-fabric with the same arguments lead to the same ports.

In particular, the following invocations lead to different ports:

```sh
text-fabric banks
```

and

```
text-fabric banks:clone
```

and likewise for all other arguments.

"""

import sys
import os
from platform import system

import psutil
import webbrowser
from time import sleep
from subprocess import PIPE, Popen

from ..core.helpers import console
from ..parameters import NAME, VERSION, PROTOCOL, HOST

from .command import (
    argKill,
    argShow,
    argNoweb,
    argApp,
    getPort,
    repSlug,
)
from .kernel import TF_DONE, TF_ERROR

HELP = """
USAGE

text-fabric --help
text-fabric -v
text-fabric -k [app]
text-fabric -p [app]

text-fabric ./path/to/app --locations=locations-string [--modules=modules-string] args
text-fabric app[:specifier] args

where all args are optional and args have one of these forms:

  -noweb
  --checkout=specifier
  --mod=modules
  --set=file
  --modules=modules-string
  --locations=locations-string
  --version=version

EFFECT

If an app is given and the -k and -p flags are not passed,
a TF kernel for that app is started.
When the TF kernel is ready, a web server is started
serving a website that exposes the data through
a query interface.

The default browser will be opened, except when -noweb is passed.

Instead of a standard app that is available on https://github.com/annotation
you can also specify an app you have locally, or no app at all.


"" (empty string): no app
path-to-directory: the directory in which your app resides. This argument
must have a / inside (e.g. ./myapp).
The directory may contain zero or more of these app.py, config.yaml, static/display.css
If they are found, they will be used.

If no app is specified, TF features will be loaded according to the
--locations and --modules args.

For standard apps, the following holds:

:specifier (after the app)
--checkout=specifier

The TF app itself can be downloaded on the fly from GitHub.
The main data can be downloaded on the fly from GitHub.
The specifier indicates a point in the history from where the app should be retrieved.
  :specifier is used for the TF app code.
  --checkout=specifier is used for the main data.

Specifiers may be:
  local                 - get the data from your local text-fabric-data directory
  clone                 - get the data from your local github clone
  latest                - get the latest release
  hot                   - get the latest commit
  tag (e.g. v1.3)       - get specific release
  hash (e.g. 78a03b...) - get specific commit

No specifier or the empty string means: latest release if there is one, else latest commit.

--mod=modules

Optionally, you can pass a comma-separated list of modules.
Modules are extra sets of features on top op the chosen data source.
You specify a module by giving the github repository where it is created,
in the form

  {org}/{repo}/{path}
  {org}/{repo}/{path}:specifier

where
  {org} is the github organization,
  {repo} the name of the repository in that organization
  {path} the path to the data within that repo.
  {specifier} points to a release or commit in the history

It is assumed that the data is stored in directories under {path},
where the directories are named as the versions that exists in the main data source.

--set=file

Optionally, you can pass a file name with the definition of custom sets in it.
This must be a dictionary were the keys are names of sets, and the values
are node sets.
This dictionary will be passed to the TF kernel, which will use it when it runs
queries.

DATA LOADING

Text-Fabric looks for data in ~/text-fabric-data.
If data is not found there, it first downloads the relevant data from
github.

MISCELLANEOUS

-noweb Do not start the default browser


CLEAN UP

If you press Ctrl-C the web server is stopped, and after that the TF kernel
as well.
Normally, you do not have to do any clean up.
But if the termination is done in an irregular way, you may end up with
stray processes.

-p  Show mode. If a data source is given, the TF kernel and web server for that
    data source are shown.
    Without a data source, all local webinterface related processes are shown.
-k  Kill mode. If a data source is given, the TF kernel and web server for that
    data source are killed.
    Without a data source, all local webinterface related processes are killed.
"""

FLAGS = set(
    """
    -noweb
""".strip().split()
)

BANNER = f"This is {NAME} {VERSION}"


def filterProcess(proc):
    procName = proc.info["name"]
    commandName = "" if procName is None else procName.lower()

    kind = None
    slug = None

    trigger = "python"
    if commandName.endswith(trigger) or commandName.endswith(f"{trigger}.exe"):
        parts = [p for p in proc.cmdline() if p not in FLAGS]
        if parts:
            parts = parts[1:]
        if parts and parts[0] == "-m":
            parts = parts[1:]
        if not parts:
            return False
        (call, *args) = parts

        trigger = "text-fabric"
        if call.endswith(trigger) or call.endswith(f"{trigger}.exe"):
            if any(arg in {"-k", "-p"} for arg in args):
                return False
            slug = argApp(parts)[1]
            ports = ()
            kind = "text-fabric"
        else:
            if call == "tf.server.kernel":
                kind = "kernel"
            elif call == "tf.server.web":
                kind = "web"
            elif call.endswith("web.py"):
                kind = "web"
            else:
                return False
            (slug, *ports) = args

        return (kind, slug, *ports)
    return False


def indexProcesses():
    tfProcesses = {}
    for proc in psutil.process_iter(attrs=["pid", "name"]):
        test = filterProcess(proc)
        if test:
            (kind, pSlug, *ports) = test
            tfProcesses.setdefault(pSlug, {}).setdefault(kind, []).append(
                (proc.info["pid"], *ports)
            )
    return tfProcesses


def showProcesses(tfProcesses, slug, term=False, kill=False):
    item = ("killed" if kill else "terminated") if term else ""
    if item:
        item = f": {item}"
    myself = os.getpid()
    for (pSlug, kinds) in tfProcesses.items():
        if slug is None or (slug == pSlug):
            checkKinds = ("kernel", "web", "text-fabric")
            rSlug = repSlug(pSlug)
            for kind in checkKinds:
                pidPorts = kinds.get(kind, [])
                for pidPort in pidPorts:
                    pid = pidPort[0]
                    port = pidPort[-1] if len(pidPort) > 1 else None
                    portRep = "" if port is None else f": {port:>5}"
                    if pid == myself:
                        continue
                    processRep = f"{kind:<12} % {pid:>5}{portRep:>7}"
                    try:
                        proc = psutil.Process(pid=pid)
                        if term:
                            if kill:
                                proc.kill()
                            else:
                                proc.terminate()
                        console(f"{processRep} {rSlug}{item}")
                    except psutil.NoSuchProcess:
                        if term:
                            console(
                                f"{processRep} {rSlug}: already {item}", error=True,
                            )


def connectPort(tfProcesses, kind, pos, slug):
    pInfo = tfProcesses.get(slug, {}).get(kind, None)
    return pInfo[0][pos] if pInfo else None


def main(cargs=sys.argv):
    console(BANNER)
    if len(cargs) >= 2 and any(
        arg in {"--help", "-help", "-h", "?", "-?"} for arg in cargs[1:]
    ):
        console(HELP)
        return
    if len(cargs) >= 2 and any(
        arg == "-v" for arg in cargs[1:]
    ):
        return

    isWin = system().lower().startswith("win")
    pythonExe = "python" if isWin else "python3"

    kill = argKill(cargs)
    show = argShow(cargs)

    (appName, slug, newPortKernel, newPortWeb) = argApp(cargs)

    if appName is None and not kill and not show:
        return

    noweb = argNoweb(cargs)

    tfProcesses = indexProcesses()

    if kill or show:
        if appName is False:
            return
        showProcesses(tfProcesses, None if appName is None else slug, term=kill)
        return

    stopped = False
    portKernel = connectPort(tfProcesses, "kernel", 1, slug)
    portWeb = None

    processKernel = None
    processWeb = None

    if portKernel:
        console(f"Connecting to running kernel via {portKernel}")
    else:
        portKernel = getPort(portBase=newPortKernel)
        console(f"Starting new kernel listening on {portKernel}")
        if portKernel != newPortKernel:
            console(f"\twhich is the first free port after {newPortKernel}")
        processKernel = Popen(
            [pythonExe, "-m", "tf.server.kernel", slug, str(portKernel)],
            stdout=PIPE,
            bufsize=1,
            encoding="utf-8",
        )
        console(f"Loading data for {appName}. Please wait ...")
        for line in processKernel.stdout:
            sys.stdout.write(line)
            if line.rstrip() == TF_ERROR:
                return
            if line.rstrip() == TF_DONE:
                break
        sleep(1)
        stopped = processKernel.poll()

    if not stopped:
        portWeb = connectPort(tfProcesses, "web", 2, slug)
        if portWeb:
            console(f"Connecting to running webserver via {portWeb}")
        else:
            portWeb = getPort(portBase=newPortWeb)
            console(f"Starting new webserver listening on {portWeb}")
            if portWeb != newPortWeb:
                console(f"\twhich is the first free port after {newPortWeb}")
            processWeb = Popen(
                [
                    pythonExe,
                    "-m",
                    "tf.server.web",
                    slug,
                    str(portKernel),
                    str(portWeb),
                ],
                bufsize=0,
                encoding="utf8",
            )

    if not noweb:
        sleep(2)
        stopped = (not portWeb or (processWeb and processWeb.poll())) or (
            not portKernel or (processKernel and processKernel.poll())
        )
        if not stopped:
            console(f"Opening {appName} in browser")
            webbrowser.open(
                f"{PROTOCOL}{HOST}:{portWeb}", new=2, autoraise=True,
            )

    stopped = (not portWeb or (processWeb and processWeb.poll())) or (
        not portKernel or (processKernel and processKernel.poll())
    )
    if not stopped:
        try:
            console("Press <Ctrl+C> to stop the TF browser")
            if processKernel:
                for line in processKernel.stdout:
                    sys.stdout.write(line)
        except KeyboardInterrupt:
            console("")
            if processWeb:
                processWeb.terminate()
                console("TF web server has stopped")
            if processKernel:
                processKernel.terminate()
                console("TF kernel has stopped")


if __name__ == "__main__":
    main()
