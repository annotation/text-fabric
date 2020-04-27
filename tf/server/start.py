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
    argNoweb,
    argApp,
    getPort,
)
from .kernel import TF_DONE, TF_ERROR

HELP = """
USAGE

text-fabric --help
text-fabric --version
text-fabric -k [app]

text-fabric ./path/to/app --locations=locations-string [--modules=modules-string] args
text-fabric app[:specifier] args

where all args are optional and args have one of these forms:

  -noweb
  --checkout=specifier
  --mod=modules
  --set=file
  --modules=modules-string
  --locations=locations-string

EFFECT

If an app is given and the -k flag is not passed,
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
    # commandName = proc.info['name'].lower()

    kind = None
    slug = None

    trigger = "python"
    if commandName.endswith(trigger) or commandName.endswith(f"{trigger}.exe"):
        parts = [p for p in proc.cmdline() if p not in FLAGS]
        (call, *args) = parts
        trigger = "text-fabric"
        if call.endswith(trigger) or call.endswith(f"{trigger}.exe"):
            if all(arg != "-k" for arg in args):
                return False
            slug = argApp(args)
            ports = ()
            kind = "tf"
        else:
            if call == "tf.server.kernel":
                kind = "kernel"
            elif call == "tf.server.web":
                kind = "web"
            elif call.endswith("web.py"):
                kind = "web"
            (slug, *ports) = args

        if kind == "tf":
            if any(arg == "-k" for arg in args):
                return False
    return (kind, slug, *ports)


def indexProcesses():
    tfProcesses = {}
    for proc in psutil.process_iter(attrs=["pid", "name"]):
        test = filterProcess(proc)
        if test:
            (kind, pSlug, *ports) = test
            tfProcesses.setdefault(pSlug, {}).setdefault(
                kind, []
            ).append((proc.info["pid"], *ports))
    return tfProcesses


def killProcesses(tfProcesses, slug, kill=False):
    item = "killed" if kill else "terminated"
    myself = os.getpid()
    for (pSlug, kinds) in tfProcesses.items():
        if slug is None or (slug == pSlug):
            checkKinds = ("data", "web", "tf")
            for kind in checkKinds:
                pids = kinds.get(kind, [])[0]
                for pid in pids:
                    if pid == myself:
                        continue
                    try:
                        proc = psutil.Process(pid=pid)
                        if kill:
                            proc.kill()
                        else:
                            proc.terminate()
                        console(f"Process {kind} server for {pSlug}: {item}")
                    except psutil.NoSuchProcess:
                        console(
                            f"Process {kind} server for {pSlug}: already {item}",
                            error=True,
                        )


def connectPort(tfProcesses, kind, pos, slug):
    port = tfProcesses.get(slug, {}).get(kind, None)
    if port:
        port = port[pos]
    return port


def main(cargs=sys.argv):
    console(BANNER)
    if len(cargs) >= 2 and any(
        arg in {"--help", "-help", "-h", "?", "-?"} for arg in cargs[1:]
    ):
        console(HELP)
        return
    if len(cargs) >= 2 and any(
        arg in {"--version", "-version", "-v"} for arg in cargs[1:]
    ):
        return

    isWin = system().lower().startswith("win")

    kill = argKill(cargs)

    (appName, slug) = argApp(cargs)

    if appName is None:
        return

    noweb = argNoweb(cargs)

    tfProcesses = indexProcesses()

    if kill:
        if appName is False:
            return
        killProcesses(tfProcesses, slug)
        return

    stopped = False
    portKernel = connectPort(tfProcesses, "kernel", 1, slug)

    if not portKernel:
        portKernel = getPort()
        pythonExe = "python" if isWin else "python3"

        processKernel = Popen(
            [pythonExe, "-m", "tf.server.kernel", slug, portKernel],
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
        if not portWeb:
            processWeb = Popen(
                [pythonExe, "-m", f"tf.server.web", slug, portKernel, portWeb],
                bufsize=0,
                encoding="utf8",
            )

    if not noweb:
        sleep(2)
        stopped = processWeb.poll() or processKernel.poll()
        if not stopped:
            console(f"Opening {appName} in browser")
            webbrowser.open(
                f"{PROTOCOL}{HOST}:{portWeb}", new=2, autoraise=True,
            )

    if processWeb and processKernel:
        try:
            for line in processKernel.stdout:
                sys.stdout.write(line)
        except KeyboardInterrupt:
            console("")
            if processWeb:
                processWeb.terminate()
                console("TF web server has stopped")
            if processKernel:
                input("Stop kernel as well? <Ctrl-C>")
                try:
                    console(
                        f"TF kernel will be kept alive for future use"
                        f"on port {portKernel}"
                    )
                except KeyboardInterrupt:
                    processKernel.terminate()
                    for line in processKernel.stdout:
                        sys.stdout.write(line)
                    console("TF kernel has stopped")


if __name__ == "__main__":
    main()
