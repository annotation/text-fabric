"""
# Usage

After installing TF, you have a new command `tf-make`.
You can use this on the command-line to build new search interfaces for existing
TF apps.

Such a search interface is a static HTML page, powered by a JavaScript program
that reads the corpus data from JavaScript variables.

You can build the interface and deploy the HTML page to GitHub Pages
(GitLab pages not yet supported),
after which it is usable for everyone.

## Prerequisites

1.  A TF dataset that has a TF App, e.g. `CambridgeSemiticsLab/nena_tf`
    [github.com/CambridgeSemiticsLab/nena_tf](https://github.com/CambridgeSemiticsLab/nena_tf).
    This is the normative example for now.
1.  An accompanying repository in the same organization, with the same name
    but with `-search` appended to the name.
1.  Within that `-search` repo, a subdirectory
    [layeredsearch](https://github.com/CambridgeSemiticsLab/nena_tf-search/tree/master/layeredsearch)
    with definitions of search interfaces
    (you can define multiple search interfaces for one dataset).
    Within this directory:
    1.  `config.yaml`: common metadata of all defined search interfaces
    1.  for each search interface a folder
        whose name is the name of the search interface, containing
        1.  `config.yaml`: definition of this specific search interface
        1.  `logo.png`: a logo
        1.  `custom.css`: additional styling (may be empty)
        1.  `mkdata.py`: a module containing a few functions that wrap the
            corpus data into JavaScript variables:
            1.  `makeLegends(maker)`: produce abbreviation lists for some layers
            1.  `record(maker)`: produce all the search data: full texts of layers and
                mappings between nodes and positions in those texts

            The `maker` argument is passed by the builder, and contains
            the definition of the layers and the API of a loaded TF dataset.

## Commands

See  also:

*   `tf.client.make.help`
*   `tf.about.clientmanual`
"""

import sys
import re
import types
import webbrowser

from textwrap import dedent
from datetime import datetime as dt, UTC
from subprocess import Popen, PIPE
from time import sleep
from zipfile import ZipFile
from importlib import util

# from tf.fabric import Fabric
from tf.app import use
from tf.fabric import Fabric
from tf.browser.command import getPort
from tf.core.helpers import specFromRanges, rangesFromSet, console as cs
from tf.core.files import (
    LS,
    fileOpen,
    normpath,
    abspath,
    backendRep,
    URL_TFDOC,
    APP_CONFIG,
    fileExists,
    dirNm,
    dirMake,
    fileCopy,
    chDir,
    scanDir,
    readYaml,
    writeYaml,
    writeJson,
)
from tf.parameters import REPO, ZIP_OPTIONS

from .gh import deploy
from .help import HELP

TEMP = "_temp"
ZIP_OPTIONS = {"compresslevel": 6, **ZIP_OPTIONS}

CONFIG_FILE = normpath(f"{dirNm(abspath(__file__))}/{APP_CONFIG}")
STATIC_DIR = normpath(f"{dirNm(dirNm(abspath(__file__)))}/static")


def console(*args, error=False):
    device = sys.stderr if error else sys.stdout
    device.write(" ".join(args) + "\n")
    device.flush()


def invertMap(legend):
    return (
        None
        if legend is None
        else {v: k for (k, v) in legend.items()}
        if type(legend) is dict
        else legend
    )


def readArgsLegacy():
    class Args:
        pass

    Args.backend = None
    Args.dataset = None
    Args.repo = None
    Args.client = None
    Args.command = None

    args = sys.argv[1:]

    if not len(args) or any(arg in {"-h", "--help", "help"} for arg in args):
        console(HELP)
        return None

    if not len(args):
        console("Missing org/repo")
        return None

    newArgs = []
    for arg in args:
        if arg.startswith("--backend="):
            Args.backend = arg[11:]
        else:
            newArgs.append(arg)
    args = newArgs

    dataset = args[0]
    args = args[1:]

    if not len(args):
        console("Missing client or command")
        return None

    if args[0] in {"serve", "ship", "make"}:
        client = None
        command = args[0]
        args = args[1:]
    else:
        client = args[0]
        args = args[1:]

        if not len(args):
            console("No command given")
            return None

        command = args[0]
        args = args[1:]

    Args.dataset = dataset
    Args.client = client
    Args.command = command
    Args.folder = None
    Args.appFolder = None
    Args.debugState = None

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
        "make",
    }:
        console(HELP)
        console(f"Wrong arguments: «{' '.join(args)}»")
        return None

    if command == "serve":
        if len(args) < 1:
            Args.folder = None
        else:
            Args.folder = args[0]

    elif command == "make":
        if len(args) < 1:
            Args.folder = None
            Args.appFolder = None
        else:
            Args.folder = args[1] if len(args) > 1 else args[0]
            Args.appFolder = args[0] if len(args) > 1 else None

    elif command == "debug":
        if len(args) < 1 or args[0] not in {"on", "off"}:
            console("say on or off")
            return None

        Args.debugState = args[0]
    return Args


class Make:
    def __init__(
        self,
        dataset,
        client,
        backend=None,
        A=None,
        folder=None,
        appFolder=None,
        debugState=None,
    ):
        if A is not None:
            self.A = A

        class C:
            pass

        self.C = C
        self.backend = backend
        self.dataset = dataset
        self.client = client
        self.folder = normpath(folder)
        self.appFolder = normpath(appFolder)
        self.debugState = debugState
        self.good = True

        if dataset:
            console("configuring ...")
            if not self.config():
                self.good = False
            console("success" if self.good else "failed")

    def doCommand(self, command):
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
            self.debugState = "on"
            self.makeClient()
            self.adjustDebug()
        elif command == "publish":
            self.publish()
        elif command == "ship":
            self.ship()
        elif command == "make":
            self.make()

    def config(self):
        C = self.C

        backend = self.backend
        dataset = self.dataset
        parts = dataset.split("/")
        if len(parts) != 2:
            console("Dataset not given as org/repo")
            return False
        (org, repo) = parts
        self.org = org
        self.repo = repo

        client = self.client
        folder = self.folder
        appFolder = self.appFolder
        versionFile = f"{STATIC_DIR}/version.yaml"
        self.versionFile = versionFile

        bUrl = backendRep(backend, "rep")

        settings = readYaml(asFile=versionFile, plain=True)
        lsVersion = settings["lsVersion"]

        mainConfig = readYaml(asFile=CONFIG_FILE, plain=True)

        cloneBase = backendRep(backend, "clone")

        c = dict(
            backend=backend,
            org=org,
            repo=repo,
            client=client,
            lsVersion=lsVersion,
            mainConfig=mainConfig,
            lsDocUrl=f"{URL_TFDOC}/about/clientmanual.html",
            lsDocSimpleUrl=f"{URL_TFDOC}/about/manual.html",
            searchRepo="«repo»-search",
            rel="site",
            generatorUrl=f"{URL_TFDOC}/client/make/build.html",
            sourceUrl=f"{bUrl}/«org»/«searchRepo»/tree/master/layeredsearch",
            issueUrl=f"{bUrl}/«org»/«searchRepo»/issues",
            staticDir=STATIC_DIR,
            appDir=f"{cloneBase}/«org»/«searchRepo»",
            localDir=f"«appDir»/{TEMP}",
            configDir=f"«appDir»/{LS}" if appFolder is None else f"{appFolder}/{LS}",
            lsConfig=f"«configDir»/{APP_CONFIG}",
            clientConfigFile=f"«configDir»/«client»/{APP_CONFIG}",
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
            siteDir="«appDir»/«rel»" if folder is None else folder,
            appClientDir="«siteDir»/«client»",
            textClientDir="«localDir»/«client»",
            pngOutDir="«appClientDir»/png",
            cssOutDir="«appClientDir»/css",
            htmlOutDir="«siteDir»",
            jsOutDir="«appClientDir»/js",
            jslibOutDir="«appClientDir»/jslib",
            jsCorpusDir="«appClientDir»/corpus",
            jsInit="«jsCorpusDir»/init.js",
            jsApp="app.js",
            jsDefs="defs.js",
            jsAll="all.js",
            jsAllPath="«appClientDir»/«jsAll»",
            htmlIndex="«siteDir»/index.html",
            htmlClient="«appClientDir»/index.html",
            htmlLocalFile="index-local.html",
            htmlLocal="«appClientDir»/«htmlLocalFile»",
            favicon="favicon.ico",
            packageUrl="../«client».zip",
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
        if not fileExists(lsConfig):
            console(f"No {APP_CONFIG} found for {org}/{repo}: {lsConfig}")
            return None

        settings = readYaml(asFile=lsConfig, plain=True)
        for (k, v) in settings.items():
            c[k] = v
            fillin(c, k, v)

        if client is not None:
            clientConfigFile = c["clientConfigFile"]
            if not fileExists(clientConfigFile):
                console(
                    f"No {APP_CONFIG} found for {org}/{repo}:{client}: {clientConfigFile}"
                )
                return None

            settings = readYaml(asFile=clientConfigFile, plain=True)
            for (k, v) in settings.items():
                c[k] = v
                fillin(c, k, v)

            self.importMake(c=c)

            d = dict(
                dataLocation=f"{cloneBase}/«data.org»/«data.repo»/«data.rel»",
                dataUrl=f"{bUrl}/«data.org»/«data.repo»/tree/master/«data.rel»/«data.version»",
                writingUrl=f"{URL_TFDOC}/writing/«writing».html",
                urls=dict(
                    cheatsheet=(
                        "regexp cheat sheet",
                        (
                            "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/"
                            "Regular_Expressions/Cheatsheet"
                        ),
                        "cheat sheet of regular expressions",
                    ),
                    license=(
                        "MIT",
                        "https://mit-license.org",
                        "website of MIT license",
                    ),
                    maker=(
                        None,
                        "https://di.huc.knaw.nl/text-analysis-en.html",
                        "Website of KNAW/Humanities Cluster/Team Text",
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
                        URL_TFDOC,
                        "TF documentation website",
                    ),
                    lsdoc=(
                        "user manual (full)",
                        "«lsDocUrl»",
                        "user manual for the full search interface",
                    ),
                    lsdocsimple=(
                        "user manual (simple)",
                        "«lsDocSimpleUrl»",
                        "user manual for the simplified search interface",
                    ),
                    datadoc=(
                        "data (feature) documentation",
                        "«data.docUrl»",
                        "explanation of the features in the dataset",
                    ),
                    data=(
                        "based on TF data version «data.version»",
                        "«dataUrl»",
                        "online repository of the underlying TF data",
                    ),
                    generator=(
                        f"{REPO}/client",
                        "«generatorUrl»",
                        "the generator of this search interface",
                    ),
                    source=(
                        "«searchRepo»",
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

        for (setting, default) in (
            ("linkLevelMin", 1),
            ("linkLevelMax", 3),
            ("memSavingMethod", 0),
        ):
            if getattr(C, setting, None) is None:
                setattr(C, setting, default)

        return True

    def importMake(self, c=None):
        client = self.client
        org = self.org
        repo = self.repo

        if c is None:
            C = self.C
            clientMake = C.clientMake
            clientMakeDir = C.clientMakeDir
            clientMakeFile = C.clientMakeFile
        else:
            clientMake = c["clientMake"]
            clientMakeDir = c["clientMakeDir"]
            clientMakeFile = c["clientMakeFile"]

        try:
            moduleName = f"tf.client.ls.{org}.{repo}.{client}.{clientMake}"
            spec = util.spec_from_file_location(moduleName, clientMakeFile)
            code = util.module_from_spec(spec)
            sys.path.insert(0, clientMakeDir)
            spec.loader.exec_module(code)
            sys.path.pop(0)
            self.makeLegends = types.MethodType(code.makeLegends, self)
            self.record = types.MethodType(code.record, self)

        except Exception as e:
            console(f"Cannot make data for {org}/{repo}:{client}: {str(e)}")
            return None

    def makeClientSettings(self):
        C = self.C
        org = self.org
        repo = self.repo
        layerSettings = C.layerSettings
        A = self.A
        api = A.api
        Cp = api.C

        self.makeLegends()

        typeSeq = list(layerSettings)
        typesLower = {}

        for (i, tp) in enumerate(typeSeq):
            typesLower[tp] = typeSeq[0 : i + 1]

        # set up the configuration that informs the client code
        # and the code that generates the data for the client

        urls = C.urls
        tutUrl = self.A.flexLink("tut")
        urls["related"] = (
            f"tf {org}/{repo}",
            tutUrl,
            "using TF on the same corpus",
        )

        clientConfig = dict(
            memSavingMethod=C.memSavingMethod,
            mainConfig=C.mainConfig,
            defs=dict(
                lsVersion=C.lsVersion,
                client=C.client,
                backend=C.backend,
                org=C.org,
                repo=C.repo,
                urls=urls,
                description=C.description,
            ),
            ntypes=typeSeq,
            typesLower=typesLower,
            defaultSettings=C.defaultSettings,
            defaultFlags=C.defaultFlags,
            keyboard=getattr(C, "keyboard", None),
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
                if theMap is not None and type(theMap) is dict:
                    default = layerInfo.get("default", None)
                    if default is not None:
                        theMap[""] = default

        if len(theFocuses) == 0:
            focusType = None
            console("No node type is declared as result focus\n")
        else:
            focusType = theFocuses[0]
            if len(theFocuses) > 1:
                console("Multiple node types declared as result focus:\n")
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

        ntypesinitTF = {level[0]: level[2] for level in Cp.levels.data}
        ntypessizeTF = {level[0]: level[3] - level[2] + 1 for level in Cp.levels.data}
        ntypesinit = {}
        ntypessize = {}

        for (level, typeInfo) in layerSettings.items():
            nType = typeInfo.get("nType", level)
            ntypesinit[level] = ntypesinitTF[nType]
            ntypessize[level] = ntypessizeTF[nType]
            levels[level] = typeInfo.get("description", "")

            ti = typeInfo.get("layers", None)
            if ti is None:
                continue

            visible[level] = {layer: ti[layer].get("visible", False) for layer in ti}
            layers[level] = {}

            for layer in ti:
                explain = ti[layer].get("explain", None)
                valueMap = invertMap(ti[layer].get("legend", None))
                valueMapAcro = type(valueMap) is dict
                layers[level][layer] = dict(
                    explain=explain,
                    valueMap=valueMap,
                    valueMapAcro=valueMapAcro,
                    tip=ti[layer].get("tip", False),
                    pos=ti[layer]["pos"] or layer,
                    pattern=ti[layer].get("example", ""),
                    description=ti[layer].get("description", ""),
                )

        for (k, v) in (
            ("ntypesinit", ntypesinit),
            ("ntypessize", ntypessize),
            ("dtypeOf", {typeSeq[i + 1]: tp for (i, tp) in enumerate(typeSeq[0:-1])}),
            ("utypeOf", {tp: typeSeq[i + 1] for (i, tp) in enumerate(typeSeq[0:-1])}),
            ("visible", visible),
            ("levels", levels),
            ("layers", layers),
        ):
            clientConfig[k] = v
        self.clientConfig = clientConfig

    def loadTf(self):
        C = self.C
        backend = C.backend
        org = C.org
        repo = C.repo
        version = C.data["version"]
        A = use(
            f"{org}/{repo}:clone", checkout="clone", backend=backend, version=version
        )
        self.A = A

    def makeConfig(self):
        if not getattr(self, "A", None):
            self.loadTf()
        if not getattr(self, "clientConfig", None):
            self.makeClientSettings()
        self.dumpConfig()

    def makeLinks(self):
        C = self.C
        A = self.A
        api = A.api
        T = api.T
        F = api.F

        linkLevelMin = C.linkLevelMin
        linkLevelMax = C.linkLevelMax
        sTypes = T.sectionTypes[linkLevelMin - 1 : linkLevelMax]
        A.info(f"links for types {', '.join(sTypes)}")
        links = {
            sType: {n: A.webLink(n, urlOnly=True) for n in F.otype.s(sType)}
            for sType in sTypes
        }
        for (sType, sLinks) in links.items():
            A.info(f"{sType:<20}: {len(sLinks):>6} links", tm=False)
        A.info("done")
        self.links = links

    def makeCorpus(self):
        if not getattr(self, "A", None):
            self.loadTf()
        if not getattr(self, "clientConfig", None):
            self.makeClientSettings()
        A = self.A

        A.info("Make links ...")
        self.makeLinks()

        A.info("Recording ...")
        self.record()

        A.info("Dumping ...")
        return self.dumpCorpus()

    def dumpConfig(self):
        C = self.C
        A = self.A
        clientConfig = self.clientConfig

        destData = C.jsCorpusDir
        dirMake(destData)

        fileNameConfig = f"{destData}/config.js"

        with fileOpen(fileNameConfig, mode="w") as fh:
            fh.write("const configData = ")
            writeJson(clientConfig, asFile=fh)
        A.info(f"Config written to file {fileNameConfig}")

    def compress(self, data):
        sets = {}

        compressed = []

        for n in sorted(data):
            sets.setdefault(data[n], []).append(n)

        for (value, nset) in sorted(sets.items(), key=lambda x: (x[1][0], x[1][-1])):
            nSpec = (
                list(nset)[0] if len(nset) == 1 else specFromRanges(rangesFromSet(nset))
            )
            compressed.append(f"{nSpec}\t{value}")

        return compressed

    def dumpCorpus(self):
        C = self.C
        A = self.A
        layerSettings = C.layerSettings
        memSavingMethod = C.memSavingMethod
        debug = self.debugState == "on"

        up = self.up
        recorders = self.recorders
        accumulators = self.accumulators

        texts = {}
        posinfo = {}

        for (level, typeInfo) in layerSettings.items():
            ti = typeInfo.get("layers", None)
            if ti is None:
                continue

            texts[level] = {layer: None for layer in ti}
            posinfo[level] = {layer: None for layer in ti if ti[layer]["pos"] is None}

        A.info("wrap recorders for delivery")
        good = True

        for (level, typeInfo) in recorders.items():
            A.info(f"\t{level}")
            for (layer, x) in typeInfo.items():
                A.info(f"\t\t{layer}")
                texts[level][layer] = x.text()
                if memSavingMethod == 0:
                    posinfo[level][layer] = x.positions(simple=True)
                elif memSavingMethod == 1:
                    posResult = x.rPositions(acceptMaterialOutsideNodes=True)
                    if type(posResult) is str:
                        A.error("Memory optimization cannot be applied to this layer")
                        A.error("because of violation of the assumptions:")
                        A.error(posResult)
                        good = False
                    posinfo[level][layer] = posResult

        A.info("wrap accumulators for delivery")
        for (level, typeInfo) in accumulators.items():
            A.info(f"\t{level}")
            for (layer, x) in typeInfo.items():
                A.info(f"\t\t{layer}")
                texts[level][layer] = "".join(x)

        data = dict(
            texts=texts,
            posinfo=posinfo,
            up=self.compress(up),
        )
        data["links"] = self.links

        A.indent(reset=True)
        A.info("Dumping data to compact json files")

        destData = C.jsCorpusDir
        dirMake(destData)

        if debug:
            textLoc = C.textClientDir
            dirMake(textLoc)

        def writeDataFile(name, address, thisData, asString=False):
            parent = textLoc if debug and asString else destData
            file = name.lower() + (".txt" if debug and asString else ".js")
            path = f"{parent}/{file}"
            heading = f"corpusData[{address}] = "
            with fileOpen(path, mode="w") as fh:
                fh.write(heading)
                if asString:
                    fh.write("`")
                    fh.write(thisData)
                    fh.write("`")
                else:
                    writeJson(
                        thisData,
                        asFile=fh,
                        indent=None,
                        separators=(",", ":"),
                    )
                if asString:
                    A.info(f"Data {name} also written to {path}")
                else:
                    A.info(f"Data {name} stored in {path}")

        init = ["var corpusData = {}\n"]

        for (partName, partData) in data.items():
            if partName in {"texts", "posinfo"}:
                init.append(f'corpusData["{partName}"] = {{}}\n')
                for (nType, tpData) in partData.items():
                    init.append(f'corpusData["{partName}"]["{nType}"] = {{}}\n')
                    for (layer, lrData) in tpData.items():
                        writeDataFile(
                            f"{partName}-{nType}-{layer}",
                            f'"{partName}"]["{nType}"]["{layer}"',
                            lrData,
                        )
                if debug and partName == "texts":
                    for (nType, tpData) in partData.items():
                        for (layer, lrData) in tpData.items():
                            writeDataFile(
                                f"{partName}-{nType}-{layer}",
                                f'"{partName}"]["{nType}"]["{layer}"',
                                lrData,
                                asString=True,
                            )
            else:
                writeDataFile(partName, f'"{partName}"', partData)
        with fileOpen(C.jsInit, mode="w") as fh:
            fh.write("".join(init))

        return good

    def makeCombined(self):
        C = self.C

        commentRe = re.compile(r"""[ \t]*/\*.*?\*/[ \t]*""", re.S)
        importRe = re.compile(r'''import\s+\{.*?\}\s+from\s+"[^"]*\.js"''', re.S)
        exportRe = re.compile(r"""^export[ ]+""", re.M)
        whiteRe = re.compile(r"""^\s+$""", re.M)
        nlRe = re.compile(r"""\n\n+""")

        def getJSModule(module):
            with fileOpen(f"{C.jsOutDir}/{module}") as fh:
                text = fh.read()
            text = importRe.sub("", text)
            text = exportRe.sub("", text)
            text = commentRe.sub("", text)
            text = whiteRe.sub("", text)
            text = nlRe.sub("\n", text)
            return text

        modules = []

        with scanDir(C.jsOutDir) as it:
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

        content = {module: getJSModule(module) for module in modules}

        header = dedent(
            """
            /*eslint-env jquery*/
            /* global configData */
            /* global corpusData */

            """
        )
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
        with fileOpen(C.jsAllPath, mode="w") as fh:
            fh.write(combined)
        console(f"Combined js file written to {C.jsAllPath}")

    def makeHtml(self):
        C = self.C
        lsVersion = C.lsVersion

        # index of all clients

        clients = {}

        for thisClient in self.getAllClients():
            thisConfig = f"{C.configDir}/{thisClient}/{APP_CONFIG}"
            desc = readYaml(asFile=thisConfig, plain=True).get("short", "")
            clients[thisClient] = desc

        with fileOpen(C.index) as fh:
            template = fh.read()
            htmlIndex = template.replace("«org»", C.org).replace("«repo»", C.repo)
            htmlIndex = htmlIndex.replace("«client»", C.client)

            html = []
            for (thisClient, desc) in clients.items():
                html.append(
                    dedent(
                        f"""
                        <dt><a href="{thisClient}/index.html">{thisClient}</a></dt>
                        <dd>{desc}</dd>
                        """
                    )
                )

            htmlIndex = htmlIndex.replace("«clients»", "".join(html))

        with fileOpen(C.htmlIndex, mode="w") as fh:
            fh.write(htmlIndex)
        console(f"html file written to {C.htmlIndex}")

        # client and client-local

        with scanDir(C.jsCorpusDir) as it:
            scripts = []
            for entry in it:
                file = entry.name
                if not file.endswith(".js"):
                    continue
                if file.startswith("texts-") or file.startswith("posinfo-"):
                    scripts.append(f'<script defer src="corpus/{file}«v»"></script>')
            corpusScripts = "\n".join(scripts)

        with fileOpen(C.template) as fh:
            template = fh.read()
            htmlNormal = template.replace(
                "«js»", '''type="module" src="js/app.js«v»"'''
            )
            htmlNormal = htmlNormal.replace("«corpus»", corpusScripts)
            htmlNormal = htmlNormal.replace("«v»", f"?v={lsVersion}")
            htmlNormal = htmlNormal.replace("«org»", C.org).replace("«repo»", C.repo)
            htmlNormal = htmlNormal.replace("«client»", C.client)
            htmlLocal = template.replace("«js»", f'''defer src="{C.jsAll}"''')
            htmlLocal = htmlLocal.replace("«corpus»", corpusScripts)
            htmlLocal = htmlLocal.replace("«v»", "")
            htmlLocal = htmlLocal.replace("«org»", C.org).replace("«repo»", C.repo)
            htmlLocal = htmlLocal.replace("«client»", C.client)

        with fileOpen(C.htmlClient, mode="w") as fh:
            fh.write(htmlNormal)
        console(f"html file written to {C.htmlClient}")

        with fileOpen(C.htmlLocal, mode="w") as fh:
            fh.write(htmlLocal)
        console(f"html file (for use with file://) written to {C.htmlLocal}")

    def makeClient(self):
        """
        We create a client app in the target directory.

        The client consists of HTML/CSS/PNG files plus a modular JavaScript program.

        Module loading does not work when you open the HTML file locally
        (i.e. when the HTML is not served by a server).

        N.B. There is a difference between a local web server serving at `localhost`
        and opening the file directly into your browser by double clicking on it.

        In the first case, you see in the URL bar of your browser
        something that starts with
        `http://` or `https://`, in the second case you see `file://` instead.

        Modular JavaScript does not work with `file://` origins.

        For that case, we bundle the modules into one,
        and let a «client»-local.html include it

        We also zip the client into {C.client}.zip so that users can download it easily

        However, if the `debugState` is on, we skip all steps that are unnecessary
        to see the updated client working.
        But we do save an extra copy of the texts to the local directory in such a way
        that they can be easily inspected.
        """

        # copy over the static files

        C = self.C
        debug = self.debugState == "on"

        for (srcDir, dstDir) in (
            (C.pngInDir, C.pngOutDir),
            (C.cssInDir, C.cssOutDir),
            (C.jsInDir, C.jsOutDir),
            (C.jslibInDir, C.jslibOutDir),
            (C.htmlInDir, C.htmlOutDir),
        ):
            dirMake(dstDir)

            with scanDir(srcDir) as it:
                for entry in it:
                    name = entry.name
                    if not entry.is_file() or name.startswith("."):
                        continue
                    srcFile = f"{srcDir}/{name}"
                    if srcFile != C.template:
                        fileCopy(srcFile, f"{dstDir}/{name}")
        fileCopy(f"{C.staticDir}/{C.favicon}", f"{C.siteDir}/{C.favicon}")

        # move the custom files in place

        for (srcFile, dstFile) in (
            (C.clientCss, f"{C.cssOutDir}/{C.client}.css"),
            (C.clientLogo, f"{C.pngOutDir}/{C.client}.png"),
        ):
            fileCopy(srcFile, dstFile)

        console("Copied static files")

        # create combined JavaScript file

        if not debug:
            self.makeCombined()

        self.makeHtml()

        if not debug:
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
        items.add(C.jsAll)

        zipped = f"{C.siteDir}/{C.client}.zip"

        with ZipFile(zipped, "w", **ZIP_OPTIONS) as zipFile:
            with scanDir(C.appClientDir) as it:
                for entry in it:
                    file = entry.name
                    if file not in items:
                        continue
                    if entry.is_file():
                        zipFile.write(f"{C.appClientDir}/{file}", arcname=file)
                        console(f"adding {file}")
                    else:
                        with scanDir(f"{C.appClientDir}/{file}") as sit:
                            for sentry in sit:
                                sfile = sentry.name
                                if sentry.is_file and not sfile.startswith("."):
                                    sfile = f"{file}/{sfile}"
                                    zipFile.write(
                                        f"{C.appClientDir}/{sfile}", arcname=sfile
                                    )
                                    console(f"adding {sfile}")
        console(f"Packaged client into {zipped}")

    def publish(self, allClients=True):
        C = self.C
        appDir = C.appDir
        siteDir = C.siteDir
        backend = self.backend
        org = self.org
        repo = self.repo
        client = self.client
        clients = self.getAllClients() if allClients or client is None else [client]
        domain = backendRep(backend, "pages")
        console(
            f"Publishing on {domain} "
            f"{org}/{repo}:{','.join(clients)} from {siteDir} ..."
        )
        chDir(appDir)
        if backend is None:
            deploy(C.org, C.searchRepo)
        else:
            console(
                f"Deploying Pages on GitLab ({backend}) not yet supported", error=True
            )

    def ship(self, publish=True):
        self.adjustVersion()
        self.makeConfig()
        good = self.makeCorpus()
        if good:
            self.makeClient()
            self.adjustDebug()
            if publish:
                self.publish()

    def make(self):
        self.makeConfig()
        good = self.makeCorpus()
        if good:
            self.makeClient()
            self.adjustDebug()

    def serve(self):
        dataset = self.dataset
        client = self.client
        C = self.C
        chDir(C.siteDir)
        port = getPort(f"{dataset}, {client}")
        if port is None:
            cs("Cannot find a free port between 8000 and 8100")
            return

        console(f"HTTP serving files in {C.siteDir} on port {port}")
        server = Popen(
            ["python3", "-m", "http.server", str(port)],
            stdout=PIPE,
            bufsize=1,
            encoding="utf-8",
        )
        sleep(1)
        webbrowser.open(f"http://localhost:{port}/index.html", new=2, autoraise=True)
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
        C = self.C
        lsVersion = C.lsVersion
        parts = lsVersion.split("@", 1)
        v = int(parts[0].lstrip("v").lstrip("0"), base=10)
        now = dt.now(UTC).isoformat(timespec="seconds")
        self.lsVersion = f"v{v + 1:>03}@{now}"
        C.lsVersion = self.lsVersion

    def showVersion(self):
        C = self.C
        lsVersion = C.lsVersion
        versionFile = self.versionFile
        console(f"{lsVersion} (according to {versionFile})")

    def adjustVersion(self):
        C = self.C
        versionFile = self.versionFile

        currentVersion = C.lsVersion
        self.incVersion()
        newVersion = C.lsVersion

        writeYaml(dict(lsVersion=newVersion), asFile=versionFile)

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
            with fileOpen(cfile) as fh:
                text = fh.read()
            match = c["re"].search(text)
            if not match:
                console(f"No debug found in {cfile}")
                good = False
                continue
            debug = match.group(1)
            debugs[cfile] = debug

        if not good:
            return False
        return debugs

    def showDebug(self):
        debugInfo = self.getDebugs()
        if debugInfo is None:
            return False
        return True

        for (source, debug) in debugInfo.items():
            console(f"{debug} (according to {source})")

    def adjustDebug(self):
        C = self.C
        debugState = self.debugState

        if not self.showDebug():
            return

        newValue = "true" if debugState == "on" else "false"

        for (key, c) in C.debugConfig.items():
            console(f'Adjusting debug in {c["file"]}')
            with fileOpen(c["file"]) as fh:
                text = fh.read()
            text = c["re"].sub(self.replaceDebug(c["mask"], newValue), text)
            with fileOpen(c["file"], mode="w") as fh:
                fh.write(text)

        console(f"Debug set to {newValue}")
        if not self.showDebug():
            return

    def getAllClients(self):
        C = self.C
        configDir = C.configDir

        clients = []

        with scanDir(configDir) as it:
            for entry in it:
                client = entry.name
                if not entry.is_dir() or client.startswith("."):
                    continue
                clients.append(client)
        return clients


def makeSearchClients(dataset, folder, appFolder, backend=None, dataDir=None):
    DEBUG_STATE = "off"

    Mk = Make(
        dataset,
        None,
        backend=backend,
        folder=folder,
        appFolder=appFolder,
        debugState=DEBUG_STATE,
    )
    clients = Mk.getAllClients()
    # version = Mk.C.data["version"]

    def getDataFromDir():
        TF = Fabric(locations=dataDir, modules=[""])
        api = TF.loadAll()
        A = use(appFolder, api=api)
        return A

    A = None if dataDir is None else getDataFromDir()
    for client in clients:
        cs(f"\n\no-o-o-o-o-o-o {client} o-o-o-o-o-o-o-o\n\n")
        ThisMk = Make(
            dataset,
            client,
            backend=backend,
            A=A,
            folder=folder,
            appFolder=appFolder,
            debugState=DEBUG_STATE,
        )
        ThisMk.make()
        A = ThisMk.A


def main():
    Args = readArgsLegacy()
    if Args is None:
        return 0

    backend = Args.backend
    dataset = Args.dataset
    client = Args.client
    command = Args.command
    folder = Args.folder
    appFolder = Args.appFolder
    debugState = Args.debugState

    if not dataset:
        return

    if not client:
        if command not in {"serve", "ship", "make"}:
            return

    Mk = Make(
        dataset,
        client,
        backend=backend,
        folder=folder,
        appFolder=appFolder,
        debugState=debugState,
    )

    if command in {"ship", "make"} and client is None:
        clients = Mk.getAllClients()
        for client in clients:
            ThisMk = Make(
                dataset,
                client,
                backend=backend,
                folder=folder,
                appFolder=appFolder,
                debugState=debugState,
            )
            if command == "ship":
                ThisMk.ship(publish=False)
            else:
                ThisMk.make()
        if command == "ship":
            Mk.publish()
        return

    return Mk.doCommand(command)


if __name__ == "__main__":
    sys.exit(main())
