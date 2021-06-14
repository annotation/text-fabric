"""
# Usage

After installing Text-Fabric, you have a new command `text-fabric-make`.
You can use this on the command line to build new search interfaces for existing
Text-Fabric apps.

Such a search interface is a static HTML page, powered by a Javascript program
that reads the corpus data from Javascript variables.

You can build the interface and deploy the HTML page to GitHub Pages,
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
        1.  `mkdata.py`: a module containing a few functions that wrap the
            corpus data into Javascript variables:
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

# from tf.fabric import Fabric
from tf.app import use
from tf.fabric import Fabric
from tf.core.helpers import specFromRanges, rangesFromSet

from .gh import deploy
from .help import HELP

ZIP_OPTIONS = dict(compression=ZIP_DEFLATED, compresslevel=6)
T_F = "text-fabric"
LS = "layeredsearch"
CONFIG_FILE = f"{os.path.dirname(os.path.abspath(__file__))}/config.yaml"
STATIC_DIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/static"


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


def readArgs():
    class Args:
        pass

    Args.dataset = None
    Args.client = None
    Args.command = None

    args = sys.argv[1:]

    if not len(args) or args[0] in {"-h", "--help", "help"}:
        console(HELP)
        console("Missing dataset")
        return None

    dataset = args[0]
    Args.dataset = dataset
    args = args[1:]

    if not len(args):
        console(HELP)
        console("Missing client or command")
        return None

    if args[0] in {"-h", "--help", "help"}:
        console(HELP)
        return None

    if args[0] in {"serve", "ship", "make"}:
        client = None
        command = args[0]
        args = args[1:]
    else:
        client = args[0]
        args = args[1:]

        if not len(args) or args[0] in {"-h", "--help", "help"}:
            console(HELP)
            if not len(args):
                console("No command given")
            return None

        command = args[0]
        args = args[1:]

    Args.client = client
    Args.command = command
    Args.folder = None
    Args.configFolder = None
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
            console(HELP)
            console("Missing output folder argument")
            return None
        else:
            Args.folder = args[1] if len(args) > 1 else args[0]
            Args.configFolder = args[0] if len(args) > 1 else None

    elif command == "debug":
        if len(args) < 1 or args[0] not in {"on", "off"}:
            console("say on or off")
            return None

        Args.debugState = args[0]
    return Args


class Make:
    def __init__(
        self, dataset, client, A=None, folder=None, configFolder=None, debugState=None
    ):
        if A is not None:
            self.A = A

        class C:
            pass

        self.C = C
        self.dataset = dataset
        self.client = client
        self.folder = folder
        self.configFolder = configFolder
        self.debugState = debugState
        self.good = True

        if dataset:
            if not self.config():
                self.good = False

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
        dataset = self.dataset
        client = self.client
        folder = self.folder
        configFolder = self.configFolder
        versionFile = f"{STATIC_DIR}/version.yaml"
        self.versionFile = versionFile

        with open(versionFile) as fh:
            settings = yaml.load(fh, Loader=yaml.FullLoader)
            lsVersion = settings["lsVersion"]

        with open(CONFIG_FILE) as fh:
            mainConfig = yaml.load(fh, Loader=yaml.FullLoader)

        c = dict(
            dataset=dataset,
            client=client,
            lsVersion=lsVersion,
            mainConfig=mainConfig,
            gh=os.path.expanduser("~/github"),
            ghUrl="https://github.com",
            nbUrl="https://nbviewer.jupyter.org/github",
            ghPages="github.io",
            nbTutUrl="«nbUrl»/annotation/tutorials/tree/master",
            lsDocUrl=f"https://«org».«ghPages»/{T_F}/tf/about/clientmanual.html",
            lsDocSimpleUrl=f"https://«org».«ghPages»/{T_F}/tf/about/manual.html",
            org="annotation",
            repo="app-«dataset»",
            rel="site",
            generatorUrl=f"https://«org».«ghPages»/{T_F}/tf/client/make/build.html",
            sourceUrl="«ghUrl»/«org»/«repo»/tree/master/layeredsearch",
            issueUrl="«ghUrl»/«org»/«repo»/issues",
            tutUrl="«nbTutUrl»/«dataset»/start.ipynb",
            staticDir=STATIC_DIR,
            appDir="«gh»/«org»/«repo»",
            configDir=f"«appDir»/{LS}" if configFolder is None else configFolder,
            lsConfig="«configDir»/config.yaml",
            clientConfigFile="«configDir»/«client»/config.yaml",
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
        if not os.path.exists(lsConfig):
            console(f"No config.yaml found for {dataset}: {lsConfig}")
            return None

        with open(lsConfig) as fh:
            settings = yaml.load(fh, Loader=yaml.FullLoader)
            for (k, v) in settings.items():
                c[k] = v
                fillin(c, k, v)

        if client is not None:
            clientConfigFile = c["clientConfigFile"]
            if not os.path.exists(clientConfigFile):
                console(
                    f"No config.yaml found for {dataset}:{client}: {clientConfigFile}"
                )
                return None

            with open(clientConfigFile) as fh:
                settings = yaml.load(fh, Loader=yaml.FullLoader)
                for (k, v) in settings.items():
                    c[k] = v
                    fillin(c, k, v)

            self.importMake(c=c)

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
                        "MIT",
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
                        "based on text-fabric data version «data.version»",
                        "«dataUrl»",
                        "online repository of the underlying text-fabric data",
                    ),
                    generator=(
                        f"{T_F}/client",
                        "«generatorUrl»",
                        "the generator of this search interface",
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
        dataset = self.dataset

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
            moduleName = f"tf.client.ls.{dataset}.{client}.{clientMake}"
            spec = util.spec_from_file_location(moduleName, clientMakeFile)
            code = util.module_from_spec(spec)
            sys.path.insert(0, clientMakeDir)
            spec.loader.exec_module(code)
            sys.path.pop(0)
            self.makeLegends = types.MethodType(code.makeLegends, self)
            self.record = types.MethodType(code.record, self)

        except Exception as e:
            console(f"Cannot make data for {dataset}:{client}: {str(e)}")
            return None

    def makeClientSettings(self):
        C = self.C
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

        clientConfig = dict(
            memSavingMethod=C.memSavingMethod,
            mainConfig=C.mainConfig,
            defs=dict(
                lsVersion=C.lsVersion,
                dataset=C.dataset,
                client=C.client,
                org=C.org,
                repo=C.repo,
                urls=C.urls,
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
            levels[level] = typeInfo.get("description", "")
            ti = typeInfo.get("layers", None)
            if ti is None:
                continue

            visible[level] = {layer: ti[layer].get("visible", False) for layer in ti}
            layers[level] = {
                layer: dict(
                    valueMap=invertMap(ti[layer].get("legend", None)),
                    tip=ti[layer].get("tip", False),
                    pos=ti[layer]["pos"] or layer,
                    pattern=ti[layer].get("example", ""),
                    description=ti[layer].get("description", ""),
                )
                for layer in ti
            }
            ntypesinit[level] = ntypesinitTF[nType]
            ntypessize[level] = ntypessizeTF[nType]

        """
        clientConfig |= dict(
            ntypesinit=ntypesinit,
            ntypessize=ntypessize,
            dtypeOf={typeSeq[i + 1]: tp for (i, tp) in enumerate(typeSeq[0:-1])},
            utypeOf={tp: typeSeq[i + 1] for (i, tp) in enumerate(typeSeq[0:-1])},
            visible=visible,
            levels=levels,
            layers=layers,
        )
        """
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
        dataset = C.dataset
        version = C.data["version"]
        A = use(f"{dataset}:clone", checkout="clone", version=version)
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
        if not os.path.exists(destData):
            os.makedirs(destData, exist_ok=True)

        fileNameConfig = f"{destData}/config.js"

        with open(fileNameConfig, "w") as fh:
            fh.write("const configData = ")
            json.dump(clientConfig, fh, ensure_ascii=False, indent=1)
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
        if not os.path.exists(destData):
            os.makedirs(destData, exist_ok=True)

        def writeDataFile(name, address, thisData, asString=False):
            path = f"{destData}/{name.lower()}.js"
            heading = f"corpusData[{address}] = "
            with open(path, "w") as fh:
                fh.write(heading)
                if asString:
                    fh.write("`")
                    fh.write(thisData)
                    fh.write("`")
                else:
                    json.dump(
                        thisData,
                        fh,
                        ensure_ascii=False,
                        indent=None,
                        separators=(",", ":"),
                    )
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
            else:
                writeDataFile(partName, f'"{partName}"', partData)
        with open(C.jsInit, "w") as fh:
            fh.write("".join(init))

        return good

    def makeCombined(self):
        C = self.C

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
        with open(C.jsAllPath, "w") as fh:
            fh.write(combined)
        console(f"Combined js file written to {C.jsAllPath}")

    def makeHtml(self):
        C = self.C
        lsVersion = C.lsVersion

        # index of all clients

        clients = {}

        for thisClient in self.getAllClients():
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
<dt><a href="{thisClient}/index.html">{thisClient}</a></dt>
<dd>{desc}</dd>
"""
                )

            htmlIndex = htmlIndex.replace("«clients»", "".join(html))

        with open(C.htmlIndex, "w") as fh:
            fh.write(htmlIndex)
        console(f"html file written to {C.htmlIndex}")

        # client and client-local

        with os.scandir(C.jsCorpusDir) as it:
            scripts = []
            for entry in it:
                file = entry.name
                if not file.endswith(".js"):
                    continue
                if file.startswith("texts-") or file.startswith("posinfo-"):
                    scripts.append(f'<script defer src="corpus/{file}«v»"></script>')
            corpusScripts = "\n".join(scripts)

        with open(C.template) as fh:
            template = fh.read()
            htmlNormal = template.replace(
                "«js»", '''type="module" src="js/app.js«v»"'''
            )
            htmlNormal = htmlNormal.replace("«corpus»", corpusScripts)
            htmlNormal = htmlNormal.replace("«v»", f"?v={lsVersion}")
            htmlNormal = htmlNormal.replace("«dataset»", C.dataset)
            htmlNormal = htmlNormal.replace("«client»", C.client)
            htmlLocal = template.replace("«js»", f'''defer src="{C.jsAll}"''')
            htmlLocal = htmlLocal.replace("«corpus»", corpusScripts)
            htmlLocal = htmlLocal.replace("«v»", "")
            htmlLocal = htmlLocal.replace("«dataset»", C.dataset)
            htmlLocal = htmlLocal.replace("«client»", C.client)

        with open(C.htmlClient, "w") as fh:
            fh.write(htmlNormal)
        console(f"html file written to {C.htmlClient}")

        with open(C.htmlLocal, "w") as fh:
            fh.write(htmlLocal)
        console(f"html file (for use with file://) written to {C.htmlLocal}")

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

        However, if the debugState is on, we skip all steps that are unneccesary
        to see the updated client working.
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

        console("Copied static files")

        # create combined javascript file

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
            with os.scandir(C.appClientDir) as it:
                for entry in it:
                    file = entry.name
                    if file not in items:
                        continue
                    if entry.is_file():
                        zipFile.write(f"{C.appClientDir}/{file}", arcname=file)
                        console(f"adding {file}")
                    else:
                        with os.scandir(f"{C.appClientDir}/{file}") as sit:
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
        dataset = self.dataset
        client = self.client
        clients = self.getAllClients() if allClients or client is None else [client]
        console(f"Publishing {dataset}:{','.join(clients)} from {siteDir} ...")
        os.chdir(appDir)
        deploy(C.org, C.repo)

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
        C = self.C
        os.chdir(C.siteDir)

        console(f"HTTP serving files in {C.siteDir}")
        server = Popen(
            ["python3", "-m", "http.server"], stdout=PIPE, bufsize=1, encoding="utf-8"
        )
        sleep(1)
        webbrowser.open("http://localhost:8000/index.html", new=2, autoraise=True)
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
        now = dt.utcnow().isoformat(timespec="seconds")
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
            with open(c["file"]) as fh:
                text = fh.read()
            text = c["re"].sub(self.replaceDebug(c["mask"], newValue), text)
            with open(c["file"], "w") as fh:
                fh.write(text)

        console(f"Debug set to {newValue}")
        if not self.showDebug():
            return

    def getAllClients(self):
        C = self.C
        configDir = C.configDir

        clients = []

        with os.scandir(configDir) as it:
            for entry in it:
                client = entry.name
                if not entry.is_dir() or client.startswith("."):
                    continue
                clients.append(client)
        return clients


def makeSearchClients(dataset, folder, configFolder, dataDir=None):
    DEBUG_STATE = "off"

    Mk = Make(
        dataset, None, folder=folder, configFolder=configFolder, debugState=DEBUG_STATE
    )
    clients = Mk.getAllClients()
    version = Mk.C.data["version"]

    def getDataFromDir():
        TF = Fabric(locations=dataDir, modules=[version])
        api = TF.loadAll()
        A = use(f"{dataset}:clone", api=api)
        return A

    A = None if dataDir is None else getDataFromDir()
    for client in clients:
        print(f"\n\no-o-o-o-o-o-o {client} o-o-o-o-o-o-o-o\n\n")
        ThisMk = Make(
            dataset,
            client,
            A=A,
            folder=folder,
            configFolder=configFolder,
            debugState=DEBUG_STATE,
        )
        ThisMk.make()
        A = ThisMk.A


def main():
    Args = readArgs()
    if Args is None:
        return 0

    dataset = Args.dataset
    client = Args.client
    command = Args.command
    folder = Args.folder
    configFolder = Args.configFolder
    debugState = Args.debugState

    if not dataset:
        return

    if not client:
        if command not in {"serve", "ship", "make"}:
            return

    Mk = Make(
        Args.dataset,
        Args.client,
        folder=folder,
        configFolder=configFolder,
        debugState=debugState,
    )

    if command in {"ship", "make"} and client is None:
        clients = Mk.getAllClients()
        for client in clients:
            ThisMk = Make(
                dataset,
                client,
                folder=folder,
                configFolder=configFolder,
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
