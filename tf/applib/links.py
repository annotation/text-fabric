import re
import types

from ..parameters import (
    URL_GH,
    URL_TFDOC,
    APP_URL,
    APP_NB_URL,
)
from ..core.helpers import htmlEsc
from .repo import Checkout
from .helpers import dh
from .display import getText


UNSUPPORTED = "unsupported"

pathRe = re.compile(
    r"^(.*/(?:github|text-fabric-data))/([^/]+)/([^/]+)/(.*)$", flags=re.I
)


def linksApi(app, appName, silent):
    app.header = types.MethodType(header, app)
    app.weblink = types.MethodType(webLink, app)
    ok = app.isCompatible

    api = app.api

    aContext = app.context
    docUrl = aContext.docUrl
    repo = aContext.repo
    version = aContext.version
    corpus = aContext.corpus
    featureBase = aContext.featureBase
    featurePage = aContext.featurePage
    charUrl = aContext.charUrl
    charText = aContext.charText

    tutUrl = f"{APP_NB_URL}/{appName}/start.ipynb"
    extraUrl = f"{APP_URL}/app-{appName}"

    dataLink = (
        outLink(repo.upper(), docUrl, f"provenance of {corpus}")
        if ok
        else UNSUPPORTED
    )
    charLink = (
        (
            outLink(
                "Character table", charUrl.format(tfDoc=URL_TFDOC), charText
            )
            if ok
            else UNSUPPORTED
        )
        if charUrl
        else ""
    )
    featureLink = (
        (
            outLink(
                "Feature docs",
                featureBase.format(version=version, feature=featurePage),
                f"{repo.upper()} feature documentation",
            )
            if ok
            else UNSUPPORTED
        )
        if ok
        else UNSUPPORTED
    )
    appLink = outLink(f"{appName} API", extraUrl, f"{appName} API documentation")
    tfLink = (
        outLink(
            f"Text-Fabric API {api.TF.version}",
            f"{URL_TFDOC}/Api/Fabric/",
            "text-fabric-api",
        )
        if ok
        else UNSUPPORTED
    )
    tfsLink = (
        outLink(
            "Search Reference",
            f"{URL_TFDOC}/Use/Search/",
            "Search Templates Introduction and Reference",
        )
        if ok
        else UNSUPPORTED
    )
    tutLink = (
        outLink("App tutorial", tutUrl, "App tutorial in Jupyter Notebook")
        if ok
        else UNSUPPORTED
    )
    if app._browse:
        app.dataLink = dataLink
        app.charLink = charLink
        app.featureLink = featureLink
        app.tfsLink = tfsLink
        app.tutLink = tutLink
    else:
        if not silent:
            dh(
                "<b>Documentation:</b>"
                f" {dataLink} {charLink} {featureLink} {appLink} {tfLink} {tfsLink}"
                "<details open><summary><b>Loaded features</b>:</summary>\n"
                + _featuresPerModule(app)
                + "</details>"
            )


def header(app):
    return (
        f"""
<div class="hdlinks">
  {app.dataLink}
  {app.charLink}
  {app.featureLink}
  {app.tfsLink}
  {app.tutLink}
</div>
""",
        f'<img class="hdlogo" src="/data/static/logo.png"/>',
        f'<img class="hdlogo" src="/server/static/icon.png"/>',
    )


def webLink(app, n, text=None, clsName=None, _asString=False, _noUrl=False):
    api = app.api
    T = api.T
    F = api.F
    Fs = api.Fs

    aContext = app.context
    version = aContext.version
    webBase = aContext.webBase
    webLang = aContext.webUrl
    webUrl = aContext.webUrl
    webUrlLex = aContext.webUrlLex
    webLexId = aContext.webLexId
    webHint = aContext.webHint
    lexTypes = aContext.lexTypes

    nType = F.otype.v(n)
    passageText = None

    if nType in lexTypes:
        if text is None:
            (isText, text) = getText(app, n, nType)
        if webUrlLex and webLexId:
            lid = (
                app.getLexId(n)
                if webLexId is True
                else Fs(webLexId).v(n)
                if webLexId
                else None
            )
            theUrl = webUrlLex.format(base=webBase, lid=lid, version=version)
        elif webBase:
            theUrl = webBase
        else:
            theUrl = None
    else:
        if text is None:
            text = app.sectionStrFromNode(n)
            passageText = text
        if webUrl:
            theUrl = webUrl.format(baes=webBase, version=version)
            headingTuple = T.sectionFromNode(n, lang=webLang, fillup=True)
            for (i, heading) in enumerate(headingTuple):
                theUrl.replace(f"<{i}>", heading)
        else:
            theUrl = None

    if theUrl is None:
        result = text
    else:
        href = "#" if _noUrl else theUrl
        atts = dict(target="") if _noUrl else dict(title=webHint)
        result = outLink(text, href, clsName=clsName, passage=passageText, **atts,)
    if _asString:
        return result
    dh(result)


def outLink(text, href, title=None, passage=None, clsName=None, target="_blank"):
    titleAtt = "" if title is None else f' title="{title}"'
    clsAtt = f' class="{clsName.lower()}"' if clsName else ""
    targetAtt = f' target="{target}"' if target else ""
    passageAtt = f' sec="{passage}"' if passage else ""
    return (
        f'<a{clsAtt}{targetAtt} href="{htmlEsc(href)}"{titleAtt}{passageAtt}>{text}</a>'
    )


def _featuresPerModule(app):
    ok = app.isCompatible
    if not ok:
        return UNSUPPORTED

    api = app.api
    TF = api.TF

    aContext = app.context
    mOrg = aContext.org
    mRepo = aContext.repo
    mRelative = aContext.relative
    version = aContext.version
    moduleSpecs = aContext.moduleSpecs
    corpus = aContext.corpus
    featureBase = aContext.featureBase

    features = api.Fall() + api.Eall()

    fixedModuleIndex = {}
    for m in moduleSpecs or []:
        fixedModuleIndex[(m["org"], m["repo"], m["relative"])] = (
            m["corpus"],
            m["docUrl"],
        )

    moduleIndex = {}
    mLocations = app.mLocations if hasattr(app, "mLocations") else []
    baseLoc = mLocations[0] if hasattr(app, "mLocations") else ()

    for mLoc in mLocations:
        match = pathRe.fullmatch(mLoc)
        if not match:
            moduleIndex[mLoc] = ("??", "??", "??", mLoc, "")
        else:
            (base, org, repo, relative) = match.groups()
            mId = (org, repo, relative)
            (corpus, docUrl) = (
                (
                    corpus,
                    featureBase.format(version=version, feature="{feature}"),
                )
                if mLoc == baseLoc
                else fixedModuleIndex[mId]
                if mId in fixedModuleIndex
                else (
                    f"{org}/{repo}/{relative}",
                    f"{URL_GH}/{org}/{repo}/tree/master/{relative}",
                )
            )
            moduleIndex[mId] = (org, repo, relative, corpus, docUrl)

    featureCat = {}

    for feature in features:
        added = False
        featureInfo = TF.features[feature]
        featurePath = featureInfo.path
        match = pathRe.fullmatch(featurePath)
        if match:
            (base, fOrg, fRepo, relative) = match.groups()
            fRelative = relative.rsplit("/", 1)[0]
            mId = (fOrg, fRepo, fRelative)
        else:
            mId = featurePath.rsplit("/", 1)[0]
        if type(mId) is str:
            for (mIId, mInfo) in moduleIndex.items():
                if type(mIId) is str:
                    if featurePath.startswith(mIId):
                        featureCat.setdefault(mIId, []).append(feature)
                        added = True
        else:
            for (mIId, mInfo) in moduleIndex.items():
                if type(mIId) is not str:
                    (mOrg, mRepo, mRelative) = mIId
                    if (
                        fOrg == mOrg
                        and fRepo == mRepo
                        and fRelative.startswith(mRelative)
                    ):
                        featureCat.setdefault(mIId, []).append(feature)
                        added = True
        if not added:
            featureCat.setdefault(mId, []).append(feature)

    baseId = (mOrg, mRepo, mRelative)
    baseMods = {
        mId for mId in featureCat.keys() if type(mId) is tuple and mId == baseId
    }
    moduleOrder = list(baseMods) + sorted(
        (mId for mId in featureCat.keys() if mId not in baseMods),
        key=lambda mId: (1, mId) if type(mId) is str else (0, mId),
    )

    html = ""
    for mId in moduleOrder:
        catFeats = featureCat[mId]
        if not catFeats:
            continue
        modInfo = moduleIndex.get(mId, None)
        if modInfo:
            (org, repo, relative, corpus, docUrl) = modInfo
        else:
            corpus = mId if type(mId) is str else "/".join(mId)
            docUrl = (
                ""
                if type(mId) is str
                else f"{URL_GH}/{mId[0]}/{mId[1]}/tree/master/{mId[2]}"
            )
        html += f"<p><b>{corpus}</b>:"

        seen = set()

        for feature in catFeats:
            if "@" in feature:
                dlFeature = f'{feature.rsplit("@", 1)[0]}@ll'
                if dlFeature in seen:
                    continue
                seen.add(dlFeature)
                featureRep = dlFeature
            else:
                featureRep = feature
            featureInfo = TF.features[feature]
            featurePath = featureInfo.path
            isEdge = featureInfo.isEdge
            pre = "<b><i>" if isEdge else ""
            post = "</i></b>" if isEdge else ""
            html += f" {pre}"
            html += (
                outLink(
                    featureRep, docUrl.format(feature=featureRep), title=featurePath
                )
                if docUrl
                else f'<span title="{featurePath}">{featureRep}</span>'
            )
            html += f"{post} "
        html += "</p>"
    return html


def liveText(org, repo, version, commit, release, local):
    return f"{org}/{repo} v:{version} ({Checkout.toString(commit, release, local)})"


def liveUrl(org, repo, version, commit, release, local, relative):
    relativeFlat = relative.replace("/", "-")
    if local:
        return f"{URL_GH}/{org}/{repo}/tree/master/{relative}"
    return (
        f"{URL_GH}/{org}/{repo}/releases/download/{release}/{relativeFlat}-{version}.zip"
        if release
        else f"{URL_GH}/{org}/{repo}/tree/{commit}/{relative}"
    )
