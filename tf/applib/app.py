import os

from ..parameters import ORG, APP_CODE
from ..fabric import Fabric
from ..parameters import URL_TFDOC, TEMP_DIR
from ..lib import readSets
from ..core.helpers import console, setDir
from .find import findAppConfig, findAppClass
from .helpers import dh
from .settings import setAppSpecs, setAppSpecsApi
from .links import linksApi, outLink
from .text import textApi
from .sections import sectionsApi
from .display import displayApi
from .search import searchApi
from .data import getModulesData
from .repo import checkoutRepo


# SET UP A TF API FOR AN APP


class App:
    def __init__(
        self,
        cfg,
        appName,
        appPath,
        commit,
        release,
        local,
        hoist=False,
        version=None,
        checkout="",
        mod=None,
        locations=None,
        modules=None,
        api=None,
        setFile="",
        silent=False,
        _browse=False,
    ):
        for (key, value) in dict(
            isCompatible=cfg.get("isCompatible", None),
            appName=appName,
            api=api,
            version=version,
            silent=silent,
            _browse=_browse,
        ).items():
            setattr(self, key, value)

        setAppSpecs(self, cfg)
        aContext = self.context
        version = aContext.version

        setDir(self)

        if not self.api:
            self.sets = None
            if setFile:
                sets = readSets(setFile)
                if sets:
                    self.sets = sets
                    console(f'Sets from {setFile}: {", ".join(sets)}')
            specs = getModulesData(
                self, mod, locations, modules, version, checkout, silent
            )
            if specs:
                (locations, modules) = specs
                self.tempDir = f"{self.repoLocation}/{TEMP_DIR}"
                TF = Fabric(locations=locations, modules=modules, silent=silent or True)
                api = TF.load("", silent=silent or True)
                if api:
                    self.api = api
                    excludedFeatures = aContext.excludedFeatures
                    allFeatures = TF.explore(silent=silent or True, show=True)
                    loadableFeatures = allFeatures["nodes"] + allFeatures["edges"]
                    useFeatures = [
                        f for f in loadableFeatures if f not in excludedFeatures
                    ]
                    result = TF.load(useFeatures, add=True, silent=silent or True)
                    if result is False:
                        self.api = None
            else:
                self.api = None

        if self.api:
            linksApi(self, silent)
            searchApi(self)
            sectionsApi(self)
            setAppSpecsApi(self, cfg)
            displayApi(self, silent)
            textApi(self)
            if hoist:
                docs = self.api.makeAvailableIn(hoist)
                if not silent:
                    dh(
                        "<details open><summary><b>API members</b>:</summary>\n"
                        + "<br/>\n".join(
                            ", ".join(
                                outLink(
                                    entry,
                                    f"{URL_TFDOC}/Api/{head}/#{ref}",
                                    title="doc",
                                )
                                for entry in entries
                            )
                            for (head, ref, entries) in docs
                        )
                        + "</details>"
                    )
        else:
            if not _browse:
                console(
                    f"""
There were problems with loading data.
The Text-Fabric API has not been loaded!
The app "{appName}" will not work!
""",
                    error=True,
                )

    def reinit(self):
        pass

    def reuse(self, hoist=False):
        aContext = self.context
        appPath = aContext.appPath
        appName = aContext.appName
        local = aContext.local
        commit = aContext.commit
        release = aContext.release
        version = aContext.version
        api = self.api

        cfg = findAppConfig(appName, appPath, commit, release, local, version=version)
        findAppClass(appName, appPath)
        self.reinit()

        setAppSpecs(self, cfg, reset=True)

        if api:
            linksApi(self, True)
            searchApi(self)
            sectionsApi(self)
            setAppSpecsApi(self, cfg)
            displayApi(self, True)
            textApi(self)
            if hoist:
                api.makeAvailableIn(hoist)


def findApp(appName, checkoutApp, *args, silent=False, version=None, **kwargs):
    if not appName or "/" in appName:
        appPath = os.path.expanduser(appName) if appName else ""
        absPath = os.path.abspath(appPath)
        (commit, release, local) = (None, None, None)

        if os.path.isdir(absPath):
            (appDir, appName) = os.path.split(absPath)
            codePath = f"{absPath}/{APP_CODE}"
            if os.path.isdir(codePath):
                appDir = codePath
            appBase = ""
        else:
            console(f"{absPath} is not an existing directory", error=True)
            appBase = False
        appPath = appDir
    else:
        (commit, release, local, appBase, appDir) = checkoutRepo(
            org=ORG,
            repo=f"app-{appName}",
            folder=APP_CODE,
            checkout=checkoutApp,
            withPaths=True,
            keep=False,
            silent=silent,
            label="TF-app",
        )
        appBaseRep = f"{appBase}/" if appBase else ""
        appPath = f"{appBaseRep}{appDir}"
    cfg = findAppConfig(appName, appPath, commit, release, local, version=version)
    version = cfg["provenanceSpec"].get("version", None)
    if not appBase and appBase != "":
        return None

    isCompatible = cfg["isCompatible"]
    if isCompatible is None:
        appClass = App
    elif not isCompatible:
        return None
    else:
        appBaseRep = f"{appBase}/" if appBase else ""
        appPath = f"{appBaseRep}{appDir}"

        appClass = findAppClass(appName, appPath) or App
    return appClass(
        cfg,
        appName,
        appPath,
        commit,
        release,
        local,
        *args,
        version=version,
        silent=silent,
        **kwargs,
    )
