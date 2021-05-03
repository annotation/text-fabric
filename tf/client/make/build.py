"""
# Usage

After installation, you have a new command `text-fabric-make`.
You can use this on the command line to build new search interfaces for existing
Text-Fabric apps.

Such a search interface is a static html page, powered by a Javascript program,
loaded with the corpus data into Javascript variables.

You can build the interface and ship the html page to GitHub Pages,
after which it is usable for everyone.

## Prerequisites

1.  A Text-Fabric dataset that is registered as a TF-App, e.g. `nena` in
    [github.com/annotation/app-nena](https://github.com/annotation/app-nena).
    This is the normative example for now.
1.  Within that app's repo, a subdirectory
    [layeredsearch](https://github.com/annotation/app-nena/tree/master/layeredsearch)
    with definitions of search interfaces
    (you can define multiple search interfaces for one dataset).
    Within this directory:
    1.  `config.yaml`: common metadata of all defined search interfaces
    1.  for each search interface a folder
        whose name is the name of the search interface, containing
        1.  `config.yaml`: definition of this specific search interface
        1.  `logo.png`: a logo
        1.  `custom.css`: additional styling (may be empty)
        1.  `mkdata.py`: a module containing a few functions that produce the
            corpus configuration data and the corpus search data:
            1.  `makeLegends(maker)`: produce abbreviation lists for some layers
            2.  `record(maker)`: produce all the search data: full texts of layers and
                mappings between nodes and positions in those texts

            The `maker` argument is passed by the builder, and contains
            the definition of the layers and the api of a loaded Text-Fabric dataset.

## Commands

See  also:

*   `tf.client.make.help`
*   `tf.about.clientmanual`
"""

import sys
import os
import re
import types
import yaml
import json
import webbrowser

from shutil import copy
from datetime import datetime as dt
from subprocess import Popen, PIPE
from time import sleep
from zipfile import ZIP_DEFLATED, ZipFile
from importlib import util

from tf.fabric import Fabric
from tf.core.helpers import specFromRanges, rangesFromSet

from .gh import deploy
from.help import HELP

ZIP_OPTIONS = dict(compression=ZIP_DEFLATED, compresslevel=6)
T_F = "text-fabric"
LS = "layeredsearch"
STATIC_DIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/static"


def console(*args):
    sys.stderr.write(" ".join(args) + "\n")
    sys.stderr.flush()


def invertMap(legend):
    return None if legend is None else {v: k for (k, v) in legend.items()}


def compress(data):
    sets = {}

    compressed = []

    for n in sorted(data):
        sets.setdefault(data[n], []).append(n)

    for (value, nset) in sorted(sets.items(), key=lambda x: (x[1][0], x[1][-1])):
        nSpec = list(nset)[0] if len(nset) == 1 else specFromRanges(rangesFromSet(nset))
        compressed.append(f"{nSpec}\t{value}")

    return compressed


class Make:
    def __init__(self):
        class C:
            pass

        self.C = C

    def readArgs(self):
        args = sys.argv[1:]
        if not len(args) or args[0] in {"-h", "--help", "help"}:
            console(HELP)
            console("Missing dataset and client")
            quit()

        dataset = args[0]
        self.dataset = dataset
        args = args[1:]

        if not len(args) or args[0] in {"-h", "--help", "help"}:
            console(HELP)
            console("Missing client")
            quit()

        client = args[0]
        self.client = client
        args = args[1:]

        if not len(args) or args[0] in {"-h", "--help", "help"}:
            console(HELP)
            if not len(args):
                console("No command given")
            quit()

        command = args[0]
        self.command = command
        self.page = None
        self.message = None
        self.debugState = None
        self.remaining = []

        if command not in {
            "serve",
            "v",
            "i",
            "config",
            "corpus",
            "client",
            "clientdebug",
            "debug",
            "publish",
            "ship",
        }:
            console(HELP)
            console(f"Wrong arguments: «{' '.join(args)}»")
            quit()

        if command in {"serve"}:
            if len(args) < 2:
                self.page = client
            else:
                self.page = args[1]
                self.remaining = args[2:]

        elif command in {"debug"}:
            if len(args) < 2 or args[1] not in {"on", "off"}:
                console("say on or off")
                quit()

            self.debugState = args[1]
            self.remaining = args[2:]

    def config(self):
        C = self.C
        dataset = self.dataset
        client = self.client
        versionFile = f"{STATIC_DIR}/version.yaml"
        self.versionFile = versionFile

        with open(versionFile) as fh:
            settings = yaml.load(fh, Loader=yaml.FullLoader)
            lsVersion = settings["lsVersion"]
        self.lsVersion = lsVersion

        c = dict(
            dataset=dataset,
            client=client,
            lsVersion=lsVersion,
            gh=os.path.expanduser("~/github"),
            ghUrl="https://github.com",
            nbUrl="https://nbviewer.jupyter.org/github",
            ghPages="github.io",
            nbTutUrl="«nbUrl»/annotation/tutorials/tree/master",
            lsDocUrl=f"https://«org».«ghPages»/{T_F}/tf/about/clientmanual.html",
            org="annotation",
            repo="app-«dataset»",
            rel="site",
            generatorUrl=f"«ghUrl»/«org»/{T_F}/tree/master/tf/client",
            sourceUrl="«ghUrl»/«org»/«repo»",
            issueUrl="«sourceUrl»/issues",
            tutUrl="«nbTutUrl»/«dataset»/start.ipynb",
            staticDir=STATIC_DIR,
            clientDir="«gh»/«org»/«repo»",
            configDir=f"«clientDir»/{LS}",
            lsConfig="«configDir»/config.yaml",
            clientConfig="«configDir»/«client»/config.yaml",
            clientMake="mkdata",
            clientMakeDir="«configDir»/«client»",
            clientMakeFile="«clientMakeDir»/«clientMake».py",
            clientCss="«configDir»/«client»/custom.css",
            clientLogo="«configDir»/«client»/logo.png",
            pngInDir="«staticDir»/png",
            cssInDir="«staticDir»/css",
            htmlInDir="«staticDir»/html",
            jsInDir="«staticDir»/js",
            jslibInDir="«staticDir»/jslib",
            template="«htmlInDir»/template.html",
            index="«htmlInDir»/index.html",
            siteDir="«clientDir»/«rel»",
            pngOutDir="«siteDir»/png",
            cssOutDir="«siteDir»/css",
            htmlOutDir="«siteDir»",
            jsOutDir="«siteDir»/js",
            jslibOutDir="«siteDir»/jslib",
            jsCorpusDir="«siteDir»/corpus",
            jsApp="app.js",
            jsDefs="defs.js",
            jsDest="«jsCorpusDir»/«client»-all.js",
            htmlIndex="«siteDir»/index.html",
            htmlClient="«siteDir»/«client».html",
            htmlLocalFile="«client»-local.html",
            htmlLocal="«siteDir»/«htmlLocalFile»",
            favicon="favicon.ico",
            packageUrl="https://«org».«ghPages»/«repo»/«client».zip",
        )

        fillRe = re.compile(r"«([a-zA-Z0-9_.]+)»")

        def fillSub(match):
            k = match.group(1)
            parts = k.split(".", 1)
            return (
                c.get(parts[0], {}).get(parts[1], "")
                if len(parts) == 2
                else c.get(parts[0], "")
            )

        def fillin(src, k, v):
            if type(v) is str:
                while fillRe.search(v):
                    v = fillRe.sub(fillSub, v)
                src[k] = v
            if type(v) is dict:
                for (m, w) in v.items():
                    fillin(src[k], m, w)
            if type(v) in {list, tuple}:
                if type(v) is tuple:
                    src[k] = list(v)
                for (m, w) in enumerate(v):
                    fillin(src[k], m, w)

        for (k, v) in c.items():
            fillin(c, k, v)

        lsConfig = c["lsConfig"]
        if not os.path.exists(lsConfig):
            console(f"No config.yaml found for {dataset}: {lsConfig}")
            quit()

        with open(lsConfig) as fh:
            settings = yaml.load(fh, Loader=yaml.FullLoader)
            for (k, v) in settings.items():
                c[k] = v
                fillin(c, k, v)

        clientConfig = c["clientConfig"]
        if not os.path.exists(clientConfig):
            console(f"No config.yaml found for {dataset}:{client}: {clientConfig}")
            quit()

        with open(clientConfig) as fh:
            settings = yaml.load(fh, Loader=yaml.FullLoader)
            for (k, v) in settings.items():
                c[k] = v
                fillin(c, k, v)

        clientMake = c["clientMake"]
        clientMakeDir = c["clientMakeDir"]
        clientMakeFile = c["clientMakeFile"]

        try:
            moduleName = f"ls.{dataset}.{client}.{clientMake}"
            spec = util.spec_from_file_location(moduleName, clientMakeFile)
            code = util.module_from_spec(spec)
            sys.path.insert(0, clientMakeDir)
            spec.loader.exec_module(code)
            sys.path.pop(0)
            self.makeLegends = types.MethodType(code.makeLegends, self)
            self.record = types.MethodType(code.record, self)

        except Exception as e:
            console(f"Cannot make data for {dataset}:{client}: {str(e)}")
            quit()

        d = dict(
            dataLocation="«gh»/«data.org»/«data.repo»/«data.rel»",
            dataUrl="«ghUrl»/«data.org»/«data.repo»/tree/master/tf/«data.version»",
            writingUrl="https://«org».«ghPages»/text-fabric/tf/writing/«writing».html",
            urls=dict(
                cheatsheet=(
                    "regexp cheatsheet",
                    (
                        "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/"
                        "Regular_Expressions/Cheatsheet"
                    ),
                    "cheatsheet of regular expressions",
                ),
                license=(
                    "license",
                    "https://mit-license.org",
                    "website of MIT license",
                ),
                maker=(
                    None,
                    "https://dans.knaw.nl/en/front-page?set_language=en",
                    "Website of DANS = Data Archiving and Networked Services",
                ),
                corpus=(
                    None,
                    "«corpus.url»",
                    "«corpus.tip»",
                ),
                corpus2=(
                    "«corpus.text»",
                    "«corpus.url»",
                    "«corpus.tip»",
                ),
                author=(
                    "Dirk Roorda",
                    "https://pure.knaw.nl/portal/en/persons/dirk-roorda",
                    "profile of the author",
                ),
                author1=(
                    "«author1.text»",
                    "«author1.url»",
                    "«author1.tip»",
                ),
                author2=(
                    "«author2.text»",
                    "«author2.url»",
                    "«author2.tip»",
                ),
                tf=(
                    None,
                    "https://«org».«ghPages»/text-fabric/tf/",
                    "Text-Fabric documentation website",
                ),
                lsdoc=(
                    "user manual",
                    "«lsDocUrl»",
                    "user manual for this search interface",
                ),
                datadoc=(
                    "data (feature) documentation",
                    "«data.docUrl»",
                    "explanation of the features in the dataset",
                ),
                data=(
                    "based on text-fabric data version «data.version»",
                    "«dataUrl»",
                    "online repository of the underlying text-fabric data",
                ),
                generator=(
                    f"{T_F}/client",
                    "«generatorUrl»",
                    "source code of the generator of this search interface",
                ),
                source=(
                    "«repo»",
                    "«sourceUrl»",
                    "source code of the definition of this search interface",
                ),
                issue=(
                    "Report an issue",
                    "«issueUrl»",
                    "report issues",
                ),
                package=(
                    "download",
                    "«packageUrl»",
                    "zip file for offline use",
                ),
                writing=(
                    "«writing»",
                    "«writingUrl»",
                    "characters and transliteration for «writing»",
                ),
                related=(
                    "text-fabric «dataset»",
                    "«tutUrl»",
                    "using Text-Fabric on the same corpus",
                ),
            ),
        )

        for (k, v) in d.items():
            c[k] = v
            fillin(c, k, v)

        setattr(
            C,
            "debugConfig",
            dict(
                setup=dict(
                    file=f"{c['jsOutDir']}/{c['jsDefs']}",
                    re=re.compile(r"""export const DEBUG = ([a-z]+)"""),
                    mask="export const DEBUG = {}",
                ),
            ),
        )
        for (k, v) in c.items():
            setattr(C, k, v)

    def makeClientSettings(self):
        C = self.C
        layerSettings = C.layerSettings
        api = self.api
        Cp = api.C

        self.makeLegends()

        typeSeq = list(layerSettings)
        typesLower = {}

        for (i, tp) in enumerate(typeSeq):
            typesLower[tp] = typeSeq[0 : i + 1]

        # set up the configuration that informs the client code
        # and the code that generates the data for the client

        clientConfig = dict(
            defs=dict(
                dataset=C.dataset,
                client=C.client,
                lsVersion=C.lsVersion,
                org=C.org,
                repo=C.repo,
                urls=C.urls,
                description=C.description,
            ),
            ntypes=typeSeq,
            typesLower=typesLower,
        )

        # check visible- and focus- attributes

        theFocuses = []
        theVisibles = []

        for (nType, typeInfo) in layerSettings.items():
            if typeInfo.get("focus", False):
                theFocuses.append(nType)

            for (name, layerInfo) in layerSettings[nType].get("layers", {}).items():
                if layerInfo.get("visible", False):
                    theVisibles.append((nType, name))
                theMap = layerInfo.get("legend", None)
                if theMap is not None:
                    default = layerInfo.get("default", None)
                    if default is not None:
                        theMap[""] = default

        if len(theFocuses) == 0:
            focusType = None
            console("No node type is declared as result focus\n")
        else:
            focusType = theFocuses[0]
            if len(theFocuses) > 1:
                console(
                    "Multiple node types declared as result focus:\n"
                )
                console("\t" + (", ".join(theFocuses)) + "\n")
            else:
                console("Node type declared as result focus:\n")
                console(f"\t{focusType}\n")

        clientConfig["focusType"] = focusType

        if len(theVisibles) == 0:
            console("No layer type is declared as visible in the result ('visible')\n")
        else:
            console("Layers declared as visible in the result ('visible'):\n")
            console("\t" + (", ".join("/".join(s) for s in theVisibles)) + "\n")

        visible = {}
        layers = {}
        levels = {}

        for (nType, typeInfo) in layerSettings.items():
            levels[nType] = typeInfo.get("description", "")
            ti = typeInfo.get("layers", None)
            if ti is None:
                continue

            visible[nType] = {name: ti[name].get("visible", False) for name in ti}
            layers[nType] = {
                name: dict(
                    valueMap=invertMap(ti[name].get("legend", None)),
                    tip=ti[name].get("tip", False),
                    pos=ti[name]["pos"] or name,
                    pattern=ti[name].get("example", ""),
                    description=ti[name].get("description", ""),
                )
                for name in ti
            }

        clientConfig |= dict(
            ntypesinit={level[0]: level[2] for level in Cp.levels.data},
            ntypessize={level[0]: level[3] - level[2] + 1 for level in Cp.levels.data},
            dtypeOf={typeSeq[i + 1]: tp for (i, tp) in enumerate(typeSeq[0:-1])},
            utypeOf={tp: typeSeq[i + 1] for (i, tp) in enumerate(typeSeq[0:-1])},
            visible=visible,
            levels=levels,
            layers=layers,
        )
        self.clientConfig = clientConfig

    def main(self):
        self.readArgs()

        command = self.command

        if not command:
            quit()

        self.config()

        if command == "serve":
            self.serve()
        elif command == "v":
            self.showVersion()
        elif command == "i":
            self.adjustVersion()
        elif command == "debug":
            self.adjustDebug()
        elif command == "config":
            self.makeConfig()
        elif command == "corpus":
            self.makeCorpus()
        elif command == "client":
            self.makeClient()
        elif command == "clientdebug":
            self.makeClient()
            self.debugState = "on"
            self.adjustDebug()
        elif command == "publish":
            self.publish()
        elif command == "ship":
            self.ship()

    def loadTf(self):
        C = self.C
        TF = Fabric(locations=C.dataLocation, modules=[C.data["version"]])
        allFeatures = TF.explore(silent=True, show=True)
        loadableFeatures = allFeatures["nodes"] + allFeatures["edges"]
        self.api = TF.load(loadableFeatures, silent=True)

    def makeConfig(self):
        if not getattr(self, "api", None):
            self.loadTf()
        if not getattr(self, "clientConfig", None):
            self.makeClientSettings()
        self.dumpConfig()

    def makeCorpus(self):
        if not getattr(self, "api", None):
            self.loadTf()
        if not getattr(self, "clientConfig", None):
            self.makeClientSettings()
        TF = self.api.TF

        TF.info("Recording ...")
        self.record()

        TF.info("Dumping ...")
        self.dumpCorpus()

    def dumpConfig(self):
        C = self.C
        api = self.api
        TF = api.TF
        clientConfig = self.clientConfig

        destData = C.jsCorpusDir
        if not os.path.exists(destData):
            os.makedirs(destData, exist_ok=True)

        fileNameConfig = f"{destData}/{C.client}-configdata.js"

        with open(fileNameConfig, "w") as fh:
            fh.write("const configData = ")
            json.dump(clientConfig, fh, ensure_ascii=False, indent=1)
        TF.info(f"Config written to file {fileNameConfig}")

    def dumpCorpus(self):
        C = self.C
        api = self.api
        TF = api.TF

        data = self.data
        data["up"] = compress(data["up"])

        TF.indent(reset=True)
        TF.info("Dumping data to a single compact json file")

        destData = C.jsCorpusDir
        if not os.path.exists(destData):
            os.makedirs(destData, exist_ok=True)

        fileNameData = f"{destData}/{C.client}-corpusdata.js"

        with open(fileNameData, "w") as fh:
            fh.write("const corpusData = ")
            json.dump(data, fh, ensure_ascii=False, indent=None, separators=(",", ":"))
        TF.info(f"Data written to file {fileNameData}")

    def makeClient(self):
        """
        We create a client app in the target directory.

        The client consists of HTML/CSS/PNG files plus a modular Javascript program.

        Module loading does not work when you open the HTML file locally
        (i.e. when the HTML is not served by a server).

        N.B. There is a difference between a local web server serving at `localhost`
        and opening the file directly into your browser by double clicking on it.

        In the first case, you see in your un the URL bar of your browser
        something that starts with
        `http://` or `https://`, in the second case you see `file://` instead.

        Modular Javascript does not work with `file://` origins.

        For that case, we bundle the modules into one,
        and let a «client»-local.html include it

        We also zip the client into {C.client}.zip so that users can download it easily
        """

        # copy over the static files

        C = self.C
        lsVersion = self.lsVersion

        for (srcDir, dstDir) in (
            (C.pngInDir, C.pngOutDir),
            (C.cssInDir, C.cssOutDir),
            (C.jsInDir, C.jsOutDir),
            (C.jslibInDir, C.jslibOutDir),
            (C.htmlInDir, C.htmlOutDir),
        ):
            if not os.path.exists(dstDir):
                os.makedirs(dstDir, exist_ok=True)

            with os.scandir(srcDir) as it:
                for entry in it:
                    name = entry.name
                    if not entry.is_file() or name.startswith("."):
                        continue
                    srcFile = f"{srcDir}/{name}"
                    if srcFile != C.template:
                        copy(srcFile, f"{dstDir}/{name}")
        copy(f"{C.staticDir}/{C.favicon}", f"{C.siteDir}/{C.favicon}")

        # move the custom files in place

        for (srcFile, dstFile) in (
            (C.clientCss, f"{C.cssOutDir}/{C.client}.css"),
            (C.clientLogo, f"{C.pngOutDir}/{C.client}.png"),
        ):
            copy(srcFile, dstFile)

        # create combined javascript file

        commentRe = re.compile(r"""[ \t]*/\*.*?\*/[ \t]*""", re.S)
        importRe = re.compile(r'''import\s+\{.*?\}\s+from\s+"[^"]*\.js"''', re.S)
        exportRe = re.compile(r"""^export[ ]+""", re.M)
        whiteRe = re.compile(r"""^\s+$""", re.M)
        nlRe = re.compile(r"""\n\n+""")

        def getModule(module):
            with open(f"{C.jsOutDir}/{module}") as fh:
                text = fh.read()
            text = importRe.sub("", text)
            text = exportRe.sub("", text)
            text = commentRe.sub("", text)
            text = whiteRe.sub("", text)
            text = nlRe.sub("\n", text)
            return text

        modules = []

        with os.scandir(C.jsOutDir) as it:
            for entry in it:
                name = entry.name
                if (
                    not entry.is_file()
                    or name.startswith(".")
                    or not name.endswith(".js")
                ):
                    continue
                modules.append(entry.name)
        console(", ".join(module[0:-3] for module in modules))

        content = {module: getModule(module) for module in modules}

        header = """\
/*eslint-env jquery*/
/* global configData */
/* global corpusData */

    """
        combined = (
            header
            + content[C.jsDefs]
            + "\n\n"
            + "\n\n".join(
                text
                for (name, text) in content.items()
                if name not in {C.jsDefs, C.jsApp}
            )
            + "\n\n"
            + content[C.jsApp]
        )
        with open(C.jsDest, "w") as fh:
            fh.write(combined)
        console(f"Combined js file written to {C.jsDest}")

        # fill in the html templates

        # index of all clients

        clients = {}

        with os.scandir(C.configDir) as it:
            for entry in it:
                if entry.is_dir():
                    thisClient = entry.name
                    thisConfig = f"{C.configDir}/{thisClient}/config.yaml"
                    if os.path.exists(thisConfig):
                        with open(thisConfig) as fh:
                            desc = yaml.load(fh, Loader=yaml.FullLoader).get("short", "")
                    else:
                        desc = ""
                    clients[thisClient] = desc

        with open(C.index) as fh:
            template = fh.read()
            htmlIndex = template.replace("«dataset»", C.dataset)
            htmlIndex = htmlIndex.replace("«client»", C.client)

            html = []
            for (thisClient, desc) in clients.items():
                html.append(
                    f"""
<dt><a href="{thisClient}.html">{thisClient}</a></dt>
<dd>{desc}</dd>
"""
                )

            htmlIndex = htmlIndex.replace("«clients»", "".join(html))

        with open(C.htmlIndex, "w") as fh:
            fh.write(htmlIndex)
        console(f"html file written to {C.htmlIndex}")

        # client and client-local

        with open(C.template) as fh:
            template = fh.read()
            htmlNormal = template.replace(
                "«js»", '''type="module" src="js/app.js«v»"'''
            )
            htmlNormal = htmlNormal.replace("«v»", f"?v={lsVersion}")
            htmlNormal = htmlNormal.replace("«dataset»", C.dataset)
            htmlNormal = htmlNormal.replace("«client»", C.client)
            htmlLocal = template.replace(
                "«js»", f'''defer src="corpus/{C.client}/all.js«v»"'''
            )
            htmlLocal = htmlLocal.replace("«v»", f"?v={lsVersion}")
            htmlLocal = htmlLocal.replace("«dataset»", C.dataset)
            htmlLocal = htmlLocal.replace("«client»", C.client)

        with open(C.htmlClient, "w") as fh:
            fh.write(htmlNormal)
        console(f"html file written to {C.htmlClient}")

        with open(C.htmlLocal, "w") as fh:
            fh.write(htmlLocal)
        console(f"html file (for use with file://) written to {C.htmlLocal}")

        # zip the standalone client

        self.zipApp()

    def zipApp(self):
        C = self.C
        items = set(
            """
            css
            corpus
            jslib
            png
            favicon.ico
        """.strip().split()
        )
        items.add(C.htmlLocalFile)

        zipped = f"{C.siteDir}/{C.client}.zip"

        with ZipFile(zipped, "w", **ZIP_OPTIONS) as zipFile:
            with os.scandir(C.siteDir) as it:
                for entry in it:
                    file = entry.name
                    if file not in items:
                        continue
                    if entry.is_file():
                        zipFile.write(f"{C.siteDir}/{file}", arcname=file)
                        console(f"adding {file}")
                    else:
                        with os.scandir(f"{C.siteDir}/{file}") as sit:
                            for sentry in sit:
                                sfile = sentry.name
                                if sentry.is_file and not sfile.startswith("."):
                                    sfile = f"{file}/{sfile}"
                                    zipFile.write(f"{C.siteDir}/{sfile}", arcname=sfile)
                                    console(f"adding {sfile}")
        console(f"Packaged client into {zipped}")

    def publish(self):
        C = self.C
        os.chdir(C.clientDir)
        deploy(C.org, C.repo)

    def ship(self):
        self.adjustVersion()
        self.adjustDebug()
        self.makeConfig()
        self.makeCorpus()
        self.makeClient()
        self.publish()

    def serve(self):
        C = self.C
        page = self.page
        os.chdir(C.siteDir)

        server = Popen(
            ["python3", "-m", "http.server"], stdout=PIPE, bufsize=1, encoding="utf-8"
        )
        sleep(1)
        webbrowser.open(f"http://localhost:8000/{page}.html", new=2, autoraise=True)
        stopped = server.poll()
        if not stopped:
            try:
                console("Press <Ctrl+C> to stop the HTTP server")
                if server:
                    for line in server.stdout:
                        console(line)
            except KeyboardInterrupt:
                console("")
                if server:
                    server.terminate()
                    console("Http server has stopped")

    def incVersion(self):
        lsVersion = self.lsVersion
        parts = lsVersion.split("@", 1)
        v = int(parts[0].lstrip("v").lstrip("0"), base=10)
        now = dt.utcnow().isoformat(timespec="seconds")
        self.lsVersion = f"v{v + 1:>03}@{now}"

    def showVersion(self):
        lsVersion = self.lsVersion
        versionFile = self.versionFile
        console(f"{lsVersion} (according to {versionFile})")

    def adjustVersion(self):
        versionFile = self.versionFile

        currentVersion = self.lsVersion
        self.incVersion()
        newVersion = self.lsVersion

        with open(versionFile, "w") as fh:
            yaml.dump(dict(lsVersion=newVersion), fh)

        console(f"Version went from `{currentVersion}` to `{newVersion}`")

    def replaceDebug(self, mask, value):
        def subVersion(match):
            return mask.format(value)

        return subVersion

    def getDebugs(self):
        C = self.C

        debugs = {}
        good = True

        for (key, c) in C.debugConfig.items():
            cfile = c["file"]
            with open(cfile) as fh:
                text = fh.read()
            match = c["re"].search(text)
            if not match:
                console(f"No debug found in {cfile}")
                good = False
                continue
            debug = match.group(1)
            debugs[cfile] = debug

        if not good:
            quit()
        return debugs

    def showDebug(self):
        debugInfo = self.getDebugs()

        for (source, debug) in debugInfo.items():
            console(f"{debug} (according to {source})")

    def adjustDebug(self):
        C = self.C
        debugState = self.debugState

        self.showDebug()

        newValue = "true" if debugState == "on" else "false"

        for (key, c) in C.debugConfig.items():
            console(f'Adjusting debug in {c["file"]}')
            with open(c["file"]) as fh:
                text = fh.read()
            text = c["re"].sub(self.replaceDebug(c["mask"], newValue), text)
            with open(c["file"], "w") as fh:
                fh.write(text)

        console(f"Debug set to {newValue}")
        self.showDebug()


def main():
    Mk = Make()
    return Mk.main()


if __name__ == "__main__":

    sys.exit(main())
