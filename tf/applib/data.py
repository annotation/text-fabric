from ..core.helpers import itemize, splitModRef, expandDir
from .repo import checkoutRepo
from .links import liveText, liveUrl


# GET DATA FOR MAIN SOURCE AND ALL MODULES


class AppData(object):
    def __init__(
        self, app, moduleRefs, locations, modules, version, checkout, silent,
    ):
        self.app = app
        self.moduleRefs = moduleRefs
        self.locationsArg = locations
        self.modulesArg = modules
        self.version = version
        self.checkout = checkout
        self.silent = silent

    def getMain(self):
        app = self.app
        aContext = app.context
        org = aContext.org
        repo = aContext.repo
        relative = aContext.relative
        appPath = aContext.appPath
        appName = aContext.appName

        if org is None or repo is None:
            appPathRep = f"{appPath}/" if appPath else ""
            relative = f"{appPathRep}{appName}"
            self.checkout = "local"

        if not self.getModule(org, repo, relative, self.checkout, isBase=True):
            self.good = False

    def getStandard(self):
        app = self.app
        aContext = app.context
        moduleSpecs = aContext.moduleSpecs

        for m in moduleSpecs or []:
            if not self.getModule(
                m["org"],
                m["repo"],
                m["relative"],
                m.get("checkout", self.checkout),
                specs=m,
            ):
                self.good = False

    def getRefs(self):
        refs = self.moduleRefs
        for ref in refs.split(",") if refs else []:
            if ref in self.seen:
                continue

            parts = splitModRef(ref)
            if not parts:
                self.good = False
                continue

            (org, repo, relative, thisCheckoutData) = parts

            if not self.getModule(*parts):
                self.good = False

    def getModules(self):
        self.provenance = []
        self.mLocations = []

        self.locations = None
        self.modules = None

        self.good = True
        self.seen = set()

        self.getMain()
        self.getStandard()
        self.getRefs()

        app = self.app

        if self.good:
            app.mLocations = self.mLocations
            app.provenance = self.provenance
        else:
            return

        mModules = []
        if self.mLocations:
            mModules.append(self.version)

        locations = self.locationsArg
        modules = self.modulesArg

        givenLocations = (
            []
            if locations is None
            else [expandDir(app, x.strip()) for x in itemize(locations, "\n")]
            if type(locations) is str
            else locations
        )
        givenModules = (
            []
            if modules is None
            else [x.strip() for x in itemize(modules, "\n")]
            if type(modules) is str
            else modules
        )

        self.locations = self.mLocations + givenLocations
        self.modules = mModules + givenModules

    # GET DATA FOR A SINGLE MODULE

    def getModule(
        self, org, repo, relative, checkout, isBase=False, specs=None,
    ):
        mLocations = self.mLocations

        moduleRef = f"{org}/{repo}/{relative}"
        if moduleRef in self.seen:
            return True

        if org is None or repo is None:
            repoLocation = relative
            mLocations.append(relative)
        else:
            (commit, release, local, localBase, localDir) = checkoutRepo(
                org=org,
                repo=repo,
                folder=relative,
                version=self.version,
                checkout=checkout,
                withPaths=False,
                keep=False,
                silent=self.silent,
            )
            if not localBase:
                return False

            repoLocation = f"{localBase}/{org}/{repo}"
            mLocations.append(f"{localBase}/{localDir}")

        self.seen.add(moduleRef)
        if isBase:
            self.app.repoLocation = repoLocation

        info = {}
        for item in (
            ("doiText", "unknown DOI"),
            ("doiUrl", ""),
            ("corpus", f"{org}/{repo}/{relative}"),
        ):
            (key, default) = item
            info[key] = (
                getattr(self.app, key)
                if isBase
                else specs[key]
                if specs and key in specs
                else default
            )
        self.provenance.append(
            (
                ("corpus", info["corpus"]),
                ("version", self.version),
                ("commit", commit or "??"),
                ("release", release or "none"),
                (
                    "live",
                    (
                        liveText(org, repo, self.version, commit, local, release),
                        liveUrl(
                            org, repo, self.version, commit, release, local, relative
                        ),
                    ),
                ),
                ("doi", (info["doiText"], info["doiUrl"])),
            )
        )
        return True


def getModulesData(*args):
    mData = AppData(*args)
    mData.getModules()
    if mData.locations is None:
        return None
    return (mData.locations, mData.modules)
