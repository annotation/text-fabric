"""
Produce links to Text-Fabric data and links from nodes to web resources.
"""

import re
import types

from ..parameters import (
    URL_GH,
    URL_TFDOC,
    SEARCHREF,
    APIREF,
    APP_URL,
    APP_NB_URL,
)
from ..core.helpers import htmlEsc, unexpanduser as ux
from .repo import Checkout
from .helpers import dh
from ..server.wrap import wrapProvenance


UNSUPPORTED = ""

pathRe = re.compile(
    r"^(.*/(?:github|text-fabric-data))/([^/]+)/([^/]+)/(.*)$", flags=re.I
)


def linksApi(app, silent):
    """Produce the link API.

    The link API provides methods to maps nodes to urls of web resources.
    It also computes several provenance and documentation links from the
    configuration settings of the corpus.


    If a single volume has been loaded, there will be added a provenance notice
    to the provenance data of the work as a whole,
    essentially stating which volume from the work is being used and what top-level
    sections of the work are part of it.

    Parameters
    ----------
    app: obj
        The high-level API object
    silent:
        The verbosity mode to perform this operation in.
        Normally it is the same as for the app, but when we do an `A.reuse()`
        we force `silent=True`.
    """
    app.showProvenance = types.MethodType(showProvenance, app)
    app.header = types.MethodType(header, app)
    app.webLink = types.MethodType(webLink, app)
    isCompatible = app.isCompatible

    aContext = app.context
    appName = aContext.appName
    appPath = aContext.appPath
    apiVersion = aContext.apiVersion
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
    apiVersionRep = "" if apiVersion is None else f" v{apiVersion}"

    dataName = repo.upper()
    collectionInfo = app.collectionInfo
    if collectionInfo:
        dataName += f" collection {collectionInfo}"
    else:
        volumeInfo = app.volumeInfo
        if volumeInfo:
            dataName += f" volume {volumeInfo}"

    dataLink = (
        outLink(dataName, docUrl, f"provenance of {corpus}")
        if isCompatible and repo is not None and docUrl
        else "/".join(x for x in (appPath, appName, version) if x)
    )
    charLink = (
        (
            outLink("Character table", charUrl.format(tfDoc=URL_TFDOC), charText)
            if isCompatible
            else UNSUPPORTED
        )
        if charUrl
        else ""
    )
    featureLink = (
        (
            outLink(
                "Feature docs",
                featureBase.replace("<feature>", featurePage).format(version=version),
                f"{repo.upper()} feature documentation",
            )
            if isCompatible and repo is not None and featureBase
            else UNSUPPORTED
        )
        if isCompatible
        else UNSUPPORTED
    )
    appLink = (
        outLink(f"app-{appName}{apiVersionRep}", extraUrl, f"{appName} TF-app")
        if isCompatible and repo is not None
        else "no app configured"
    )
    tfLink = outLink(
        f"Text-Fabric API {app.TF.version}",
        APIREF,
        "text-fabric-api",
    )
    tfsLink = (
        outLink(
            "Search Reference",
            SEARCHREF,
            "Search Templates Introduction and Reference",
        )
        if isCompatible
        else UNSUPPORTED
    )
    tutLink = (
        outLink("App tutorial", tutUrl, "App tutorial in Jupyter Notebook")
        if isCompatible and repo is not None
        else UNSUPPORTED
    )

    app.appLink = appLink
    app.dataLink = dataLink
    app.charLink = charLink
    app.featureLink = featureLink
    app.tfLink = tfLink
    app.tfsLink = tfsLink
    app.tutLink = tutLink

    if not app._browse:
        if not silent:
            header(app)


def header(app):
    """Generate a colofon of the TF-app.

    This colofon will be displayed after initializing the advanced API,
    and it is packed with provenance and documentation links.
    """

    appLink = app.appLink
    dataLink = app.dataLink
    charLink = app.charLink
    featureLink = app.featureLink
    tfsLink = app.tfsLink
    tfLink = app.tfLink
    tutLink = app.tutLink

    if app._browse:
        return (
            f"""\
<div class="hdlinks">
  {dataLink}
  {charLink}
  {featureLink}
  {tfsLink}
  {tutLink}
</div>\
""",
            '<img class="hdlogo" src="/data/static/logo.png"/>',
            '<img class="hdlogo" src="/server/static/icon.png"/>',
        )
    else:
        tfLine = ", ".join(x for x in (tfLink, appLink, tfsLink) if x)
        dataLine = ", ".join(x for x in (dataLink, charLink, featureLink) if x)
        dh(
            f"<b>Text-Fabric:</b> {tfLine}<br>"
            f"<b>Data:</b> {dataLine}<br>"
            "<b>Features:</b><br>" + _featuresPerModule(app)
        )


def webLink(
    app, n, text=None, clsName=None, urlOnly=False, _asString=False, _noUrl=False
):
    """Maps a node to a web resource.

    Usually called as `A.webLink(...)`

    The mapping is quite sophisticated. It will do sensible things for
    section nodes and lexeme nodes, dependent on how they are configured in
    the app's `config.yaml`.

    !!! hint "Customizable"
        You can customize the behaviour of `webLink()` to the needs of your corpus
        by providing appropriate values in its `config.yaml`, especially for
        `webBase`, `webLang`, `webOffset`, `webUrl`, `webUrlLex`, and `webHint`.

    Parameters
    ----------
    n: int
        A node
    text: string/HTML, optional default `None`
        The text of the link. If left out, a suitable text will be derived from
        the node.
    clsName: string, optional default `None`
        A CSS class name to add to the resulting link element
    urlOnly: boolean, optional `False`
        If True, only the url will be returned.
    _asString: boolean, optional `False`
        Whether to deliver the result as a piece of HTML or to display the link
        on the (Jupyter) interface.
    _noUrl: boolean, optional `False`
        Whether to put the generated url in the `href` attribute.
        It can be inhibited. This is useful for the TF-browser, which may want
        to attach an action to the link and navigate to a location based on
        other attributes.

    See Also
    --------
    tf.advanced.settings: options allowed in `config.yaml`
    """

    api = app.api
    T = api.T
    F = api.F
    Fs = api.Fs

    aContext = app.context
    webBase = aContext.webBase
    webLang = aContext.webLang
    webOffset = aContext.webOffset
    webUrl = aContext.webUrl
    webUrlLex = aContext.webUrlLex
    webLexId = aContext.webLexId
    webHint = aContext.webHint
    lexTypes = aContext.lexTypes
    styles = aContext.styles

    nType = F.otype.v(n)
    passageText = None

    if _noUrl:
        href = "#"
    elif nType in lexTypes:
        if webUrlLex and webLexId:
            lid = (
                app.getLexId(n)
                if webLexId is True
                else Fs(webLexId).v(n)
                if webLexId
                else None
            )
            href = webUrlLex.replace("<lid>", str(lid))
        elif webBase:
            href = webBase
        else:
            href = None
    else:
        if webUrl:
            href = webUrl
            headingTuple = T.sectionFromNode(n, lang=webLang, fillup=True)
            for (i, heading) in enumerate(headingTuple):
                defaultOffset = 0 if type(heading) is int else ""
                offset = (
                    defaultOffset
                    if webOffset is None
                    else webOffset.get(i + 1, {}).get(
                        headingTuple[i - 1], defaultOffset
                    )
                    if i > 0
                    else defaultOffset
                )
                value = "" if heading is None else str(heading + offset)
                href = href.replace(f"<{i + 1}>", value)
        else:
            href = None

    if nType in lexTypes:
        if text is None:
            text = app.getText(False, n, nType, False, True, True, "", None, None)
    else:
        passageText = app.sectionStrFromNode(n)
        if text is None:
            text = passageText

    style = styles.get(nType, None)
    if style:
        clsName = f"{clsName or ''} {style}"
    if href is None:
        fullResult = text
    else:
        atts = dict(target="") if _noUrl else dict(title=webHint)
        fullResult = outLink(
            text,
            href,
            clsName=clsName,
            passage=passageText,
            **atts,
        )
    result = href if urlOnly else fullResult
    if _asString or urlOnly:
        return result
    dh(result)


def showProvenance(app, jobName="program code", author="program author"):
    """Shows the provenance that is normally displayed during data loading.

    This comes in handy if you have started with `use(xxx, silence='deep')` and still
    need to show the provenance.
    Moreover, the provenance is shown in a formatted way.

    Parameters
    ----------
    jobName: string, optional `program code`
        E.g. the name of program in which you call this function.
        In the Text-Fabric browser the name of the job will be entered here.
        This item will be displayed together with the rest of the provenance.

    author: string, optional `program author`
        E.g. your own name.
        This item will be displayed together with the rest of the provenance.
    """

    aContext = app.context
    appName = aContext.appName
    commit = aContext.commit
    appProvenance = ((("name", appName), ("commit", commit)),)
    provenance = (appProvenance, app.provenance)
    setNames = (
        tuple(sorted(app.sets.keys()))
        if hasattr(app, "sets") and type(app.sets) is dict
        else ()
    )
    form = dict(jobName=jobName, author=author)
    dh(wrapProvenance(form, provenance, setNames)[0])


def outLink(text, href, title=None, passage=None, clsName=None, target="_blank"):
    """Produce a formatted link.

    Parameters
    ----------
    text: string/HTML
        The text of the link.
    href: string/URL
        The url of the link.
    title: string, optional `None`
        The hint of the link.
    target: string, optional `_blank`
        The target window/tab of the link.
    clsName: string, optional default `None`
        A CSS class name to add to the resulting link element
    passage: string, optional `None`
        A passage indicator, which will end up in the `sec` attribute of the
        link element. Used by the TF-browser.
    """

    titleAtt = "" if title is None else f' title="{title}"'
    clsAtt = f' class="{clsName.lower()}"' if clsName else ""
    targetAtt = f' target="{target}"' if target else ""
    passageAtt = f' sec="{passage}"' if passage else ""
    return (
        f'<a{clsAtt}{targetAtt} href="{htmlEsc(href)}"{titleAtt}{passageAtt}>'
        f"{text}</a>"
    )


def _featuresPerModule(app):
    """Generate a formatted list of loaded TF features, per module."""

    isCompatible = app.isCompatible
    if isCompatible is not None and not isCompatible:
        return UNSUPPORTED

    api = app.api
    TF = app.TF

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
                (relative, None)
                if org is None or repo is None
                else (
                    (corpus, featureBase.format(version=version))
                    if featureBase
                    else (corpus, None)
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
        html += f"<details><summary><b>{corpus}</b></summary>"

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
            featurePath = ux(featureInfo.path)
            isEdge = featureInfo.isEdge
            pre = "<b><i>" if isEdge else ""
            post = "</i></b>" if isEdge else ""
            html += f"{pre}"
            html += (
                outLink(
                    featureRep,
                    docUrl.replace("<feature>", featureRep),
                    title=featurePath,
                )
                if docUrl
                else f'<span title="{featurePath}">{featureRep}</span>'
            )
            html += f"{post}<br>"
        html += "</details>"
    return html


def provenanceLink(org, repo, version, commit, release, local, relative):
    """Generate a provenance link for a data source.

    We assume the data source resides somewhere inside a GitHub repo.

    Parameters
    ----------
    org: string
        Organization on GitHub
    repo: string
        Repository on Github
    version: string
        Version of the data source.
        This is not the release or commit of a repo, but the subdirectory
        corresponding with a data version under a `tf` directory with feature files.
    commit: string
        The commit hash of the repository on GitHub.
    """

    text = (
        f"data on local machine {relative}"
        if org is None or repo is None
        else f"{org}/{repo} v:{version} ({Checkout.toString(commit, release, local)})"
    )
    relativeFlat = relative.replace("/", "-")
    url = (
        None
        if org is None or repo is None
        else f"{URL_GH}/{org}/{repo}/tree/master/{relative}"
        if local
        else (
            f"{URL_GH}/{org}/{repo}/releases/download/{release}"
            f"/{relativeFlat}-{version}.zip"
            if release
            else f"{URL_GH}/{org}/{repo}/tree/{commit}/{relative}"
        )
    )
    return (text, url)
