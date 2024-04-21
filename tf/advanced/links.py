"""
Produce links to TF data and links from nodes to web resources.
"""

import re
import types
from textwrap import dedent

from ..parameters import (
    URL_NB,
    GH,
    GL,
)
from ..core.helpers import console, htmlEsc
from ..core.files import (
    backendRep,
    URL_TFDOC,
    APIREF,
    SEARCHREF,
    APP_APP,
    unexpanduser as ux,
    prefixSlash,
    dirNm,
)
from ..core.timestamp import SILENT_D, AUTO, TERSE, VERBOSE, silentConvert
from .repo import Checkout
from .helpers import dh, showDict
from .settings import showContext
from ..browser.wrap import wrapProvenance


UNSUPPORTED = ""


def linksApi(app, silent=SILENT_D):
    """Produce the link API.

    The link API provides methods to maps nodes to URLs of web resources.
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
    silent: string, optional `tf.core.timestamp.SILENT_D`
        See `tf.core.timestamp.Timestamp`
        Normally the silent parameter is taken from the app,
        but when we do an `A.reuse()` we force `silent="deep"`.
    """
    inNb = app.inNb
    _browse = app._browse
    silent = silentConvert(silent)
    backend = app.backend
    app.showProvenance = types.MethodType(showProvenance, app)
    app.header = types.MethodType(header, app)
    app.flexLink = types.MethodType(flexLink, app)
    app.webLink = types.MethodType(webLink, app)
    isCompatible = app.isCompatible

    aContext = app.context
    appName = aContext.appName
    appRelative = aContext.relative.removeprefix("/")
    appPath = aContext.appPath
    apiVersion = aContext.apiVersion
    docUrl = aContext.docUrl
    org = aContext.org or ""
    repo = aContext.repo or ""
    version = aContext.version
    branch = aContext.provenanceSpec["branch"]
    corpus = aContext.corpus
    featureBase = aContext.featureBase
    featurePage = aContext.featurePage
    charUrl = aContext.charUrl
    charText = aContext.charText

    apiVersionRep = "" if apiVersion is None else f" v{apiVersion}"

    dataName = f"{org} - {repo} {version}"
    collectionInfo = app.collectionInfo
    if collectionInfo:
        dataName += f" collection {collectionInfo}"
    else:
        volumeInfo = app.volumeInfo
        if volumeInfo:
            dataName += f" volume {volumeInfo}"

    components = [appPath.rsplit("/", 1)[0]]
    if appRelative:
        components.append(appRelative)
    components.append(version)
    dataLink = (
        outLink(
            dataName,
            docUrl,
            f"provenance of {corpus}",
            asHtml=inNb is not None or _browse,
        )
        if isCompatible and repo is not None and docUrl
        else "/".join(components)
        if appName.startswith("app:")
        else "/".join((x or "") for x in (appPath, appName, version))
    )
    charLink = (
        (
            outLink(
                "Character table",
                charUrl.format(tfDoc=URL_TFDOC),
                charText,
                asHtml=inNb is not None or _browse,
            )
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
                f"{org} - {repo} feature documentation",
                asHtml=inNb is not None or _browse,
            )
            if isCompatible and repo is not None and featureBase
            else UNSUPPORTED
        )
        if isCompatible
        else UNSUPPORTED
    )
    extraUrl = f"{backendRep(backend, 'url')}/{org}/{repo}/blob/{branch}/{APP_APP}"
    appLink = (
        outLink(
            f"{org}/{repo}/app {apiVersionRep}",
            extraUrl,
            f"{appName} app",
            asHtml=inNb is not None or _browse,
        )
        if isCompatible and repo is not None
        else "no app configured"
    )
    tfLink = outLink(
        f"TF API {app.TF.version}",
        APIREF,
        "text-fabric api",
        asHtml=inNb is not None or _browse,
    )
    tfsLink = (
        outLink(
            "Search Reference",
            SEARCHREF,
            "Search Templates Introduction and Reference",
            asHtml=inNb is not None or _browse,
        )
        if isCompatible
        else UNSUPPORTED
    )
    tutLink = (
        outLink(
            "Tutorial",
            flexLink(app, "tut"),
            "Tutorial in Jupyter Notebook",
            asHtml=inNb is not None or _browse,
        )
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
        if silent in {VERBOSE, AUTO, TERSE}:
            header(app, allMeta=silent == VERBOSE)


def header(app, allMeta=False):
    """Generate a colophon of the app.

    This colophon will be displayed after initializing the advanced API,
    and it is packed with provenance and documentation links.

    Parameters
    ----------
    allMeta: boolean, optional False
        If True, includes all metadata of all features. This leads to big
        stretches of largely redundant information in HTML details elements.
        It is not visually cumbersome, but notebooks may grow excessively
        if you load many datasets many times. So, if False, it will suppress
        all that metadata except the description keys.
    """

    inNb = app.inNb
    appLink = app.appLink
    dataLink = app.dataLink
    charLink = app.charLink
    featureLink = app.featureLink
    tfsLink = app.tfsLink
    tfLink = app.tfLink
    tutLink = app.tutLink
    _browse = app._browse

    if _browse:
        colophon = dedent(
            f"""
            <div class="hdlinks">
              {dataLink}
              {charLink}
              {featureLink}
              {tfsLink}
              {tutLink}
            </div>
            """
        )
    else:
        colophon = ""

    nodeInfo = _nodeTypeInfo(app)
    featureInfo = _featuresPerModule(app, allMeta=allMeta or _browse)
    settingInfo = showContext(app, withComputed=_browse, asHtml=True)

    if inNb is not None or _browse:
        tfLine = ", ".join(x for x in (tfLink, appLink, tfsLink) if x)
        dataLine = ", ".join(x for x in (dataLink, charLink, featureLink) if x)
        setLine = (
            ", ".join(f"<code>{x}</code>" for x in (app.sets or {}))
            if app.sets
            else "no custom sets"
        )
        commonHeader = dedent(
            f"""
            <b>TF:</b> {tfLine}<br>
            <b>Data:</b> {dataLine}<br>
            {nodeInfo}
            <b>Sets:</b> {setLine}<br>
            <b>Features:</b><br>{featureInfo}
            <b>Settings:</b><br>{settingInfo}
            """
        )
        if inNb is not None:
            dh(commonHeader, inNb=inNb)
        else:
            return (
                colophon,
                commonHeader,
                '<img class="hdlogo" src="/data/static/logo.png"/>',
                '<img class="hdlogo" src="/browser/static/icon.png"/>',
            )
    else:
        tfLine = "\n\t".join(x for x in (tfLink, appLink, tfsLink) if x)
        dataLine = "\n\t".join(x for x in (dataLink, charLink, featureLink) if x)
        setLine = ", ".join(x for x in (app.sets or {}))
        console(
            f"TF:\n\t{tfLine}\n" f"Data:\n\t{dataLine}\n" f"{nodeInfo}",
            f"Sets: {setLine}\n",
            f"Features:\n{featureInfo}\n",
            newline=False,
        )


def webLink(
    app, n, text=None, clsName=None, urlOnly=False, _asString=False, _noUrl=False
):
    """Maps a node to a web resource.

    Usually called as `A.webLink(...)`

    The mapping is quite sophisticated. It will do sensible things for
    section nodes and lexeme nodes, dependent on how they are configured in
    the app's `config.yaml`.

    !!! hint "Customisable"
        You can customize the behaviour of `webLink()` to the needs of your corpus
        by providing appropriate values in its `config.yaml`, especially for
        `webBase`, `webLang`, `webOffset`, `webFeature`, `webUrl`, `webUrlLex`, and `webHint`.

    Parameters
    ----------
    n: integer
        A node
    text: string, optional default `None`
        The text of the link. If left out, a suitable text will be derived from
        the node.
    clsName: string, optional default `None`
        A CSS class name to add to the resulting link element
    urlOnly: boolean, optional False
        If True, only the URL will be returned.
    _asString: boolean, optional False
        Whether to deliver the result as a piece of HTML or to display the link
        on the (Jupyter) interface.
    _noUrl: boolean, optional False
        Whether to put the generated URL in the `href` attribute.
        It can be inhibited. This is useful for the TF browser, which may want
        to attach an action to the link and navigate to a location based on
        other attributes.

    See Also
    --------
    tf.advanced.settings: options allowed in `config.yaml`
    """

    api = app.api
    TF = api.TF
    T = api.T
    F = api.F
    Fs = api.Fs

    inNb = app.inNb
    _browse = app._browse
    aContext = app.context
    webBase = aContext.webBase
    webLang = aContext.webLang
    webOffset = aContext.webOffset
    webFeature = aContext.webFeature
    webUrl = aContext.webUrl
    webUrlZeros = aContext.webUrlZeros or {}
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
        href = None
        if webFeature:
            if TF.isLoaded(webFeature, pretty=False)[webFeature]:
                val = Fs(webFeature).v(n)
                if val is not None:
                    href = f"{webBase}{val}"
        if href is None:
            if webUrl:
                href = webUrl
                headingTuple = T.sectionFromNode(n, lang=webLang, fillup=True)
                for i, heading in enumerate(headingTuple):
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
                    leadingZeros = webUrlZeros.get(i + 1, 0)
                    if 0 < len(value) < leadingZeros:
                        value = "0" * (leadingZeros - len(value)) + value

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
            asHtml=inNb is not None or _browse,
            **atts,
        )
    result = href if urlOnly else fullResult
    if _asString or urlOnly:
        return result
    dh(result, inNb=inNb)


def showProvenance(app, jobName="program code", author="program author"):
    """Shows the provenance that is normally displayed during data loading.

    This comes in handy if you have started with
    `use("org/repo", silence='deep')` and still need to show the provenance.
    Moreover, the provenance is shown in a formatted way.

    Parameters
    ----------
    jobName: string, optional program code
        E.g. the name of program in which you call this function.
        In the TF browser the name of the job will be entered here.
        This item will be displayed together with the rest of the provenance.

    author: string, optional program author
        E.g. your own name.
        This item will be displayed together with the rest of the provenance.
    """

    inNb = app.inNb
    aContext = app.context
    backend = app.backend
    org = aContext.org
    repo = aContext.repo
    commit = aContext.commit
    appProvenance = (
        (("backend", backend), ("org", org), ("repo", repo), ("commit", commit)),
    )
    provenance = (appProvenance, app.provenance)
    setNames = (
        tuple(sorted(app.sets.keys()))
        if hasattr(app, "sets") and type(app.sets) is dict
        else ()
    )
    form = dict(jobName=jobName, author=author)
    dh(wrapProvenance(form, provenance, setNames)[0], inNb=inNb)


PATH_RE1 = re.compile(
    rf"""
        ^
        (.*?)
        /
        (?:
            (
                (?:
                    text-fabric-data
                    /
                )?
            )
            (
                {GH}
                |
                {GL}
                |
                (?:
                    (?:
                        [a-zA-Z0-9_-]+\.
                    )+
                    [a-zA-Z0-9_-]+
                )
            )
        )
        /
        (.*)
        $
    """,
    re.X | re.I,
)

PATH_RE2 = re.compile(
    r"""
    ^
    ([^/]+)
    /
    ([^/]+)
    /
    (.*)
    $
    """,
    re.X | re.I,
)


def _parseFeaturePath(path, backend):
    match1 = PATH_RE1.fullmatch(path)
    if not match1:
        return (False, backend, "??", "??", "/??")

    (lead, exDir, theBackend, rest) = match1.groups()
    theBackend = theBackend.lower()

    match2 = PATH_RE2.fullmatch(rest)
    if not match2:
        return (False, theBackend, "??", "??", "/??")

    (org, repo, relative) = match2.groups()
    return (True, theBackend, org, repo, prefixSlash(relative))


def outLink(
    text, href, title=None, passage=None, clsName=None, target="_blank", asHtml=True
):
    """Produce a formatted link.

    Parameters
    ----------
    text: string/HTML
        The text of the link.
    href: string/URL
        The URL of the link.
    title: string, optional None
        The hint of the link.
    target: string, optional _blank
        The target window / tab of the link.
    clsName: string, optional default `None`
        A CSS class name to add to the resulting link element
    passage: string, optional None
        A passage indicator, which will end up in the `sec` attribute of the
        link element. Used by the TF browser.
    asHtml: boolean, optional True
        Whether we are in a notebook or in the browser.
        If not, a plain text representation of the link will be made.
    """

    titleAtt = "" if title is None else f' title="{title}"'
    clsAtt = f' class="{clsName.lower()}"' if clsName else ""
    targetAtt = f' target="{target}"' if target else ""
    passageAtt = f' sec="{passage}"' if passage else ""
    return (
        (
            f'<a{clsAtt}{targetAtt} href="{htmlEsc(href)}"{titleAtt}{passageAtt}>'
            f"{text}</a>"
        )
        if asHtml
        else f"{text} => {href}"
    )


def _nodeTypeInfo(app):
    inNb = app.inNb
    _browse = app._browse
    doHtml = inNb is not None or _browse
    api = app.api
    levels = api.C.levels.data
    otype = api.F.otype
    slotType = otype.slotType
    maxSlot = otype.maxSlot

    output = (
        """<details class="nodeinfo"><summary><b>Node types</b></summary>"""
        if doHtml
        else "Node types:\n"
    )

    if doHtml:
        output += (
            dedent(
                """
            <table class="nodeinfo">
                <tr>
                    <th>Name</th>
                    <th># of nodes</th>
                    <th># slots / node</th>
                    <th>% coverage</th>
                </tr>
            """
            )
            if doHtml
            else f"{'Name':<20} {'#nodes':>7} {'#slots/node':>11} {'%coverage':>9}\n"
        )
    for nType, av, start, end in levels:
        nNodes = end - start + 1
        coverage = int(round(av * nNodes * 100 / maxSlot))
        coverage = (
            (f"<b>{coverage}</b>" if doHtml else f"= {coverage:>7}")
            if coverage == 100
            else (f"<i>{coverage}</i>" if doHtml else f"> {coverage:>7}")
            if coverage > 100
            else coverage
        )
        nTypeRep = (
            (f"<i>{nType}</i>" if doHtml else f"*{nType}*")
            if nType == slotType
            else nType
        )
        output += (
            dedent(
                f"""
            <tr>
                <th>{nTypeRep}</th>
                <td>{nNodes}</td>
                <td>{av:.2f}</td>
                <td>{coverage}</td>
            </tr>
            """
            )
            if doHtml
            else f"{nTypeRep:<20} {nNodes:>7} {av:8.2f} {coverage:>9}\n"
        )

    output += "</table></details>" if doHtml else "\n"
    return output


def _featuresPerModule(app, allMeta=False):
    """Generate a formatted list of loaded TF features, per module.

    Parameters
    ----------
    allMeta: boolean, optional False
        Whether to display all metadata for all features or the descriptions only
    """

    isCompatible = app.isCompatible
    if isCompatible is not None and not isCompatible:
        return UNSUPPORTED

    api = app.api
    TF = app.TF
    inNb = app.inNb
    _browse = app._browse
    doHtml = inNb is not None or _browse
    backend = app.backend

    aContext = app.context
    mOrg = aContext.org
    mRepo = aContext.repo
    mRelative = prefixSlash(aContext.relative)
    version = aContext.version
    branch = aContext.provenanceSpec["branch"]
    moduleSpecs = aContext.moduleSpecs
    corpus = aContext.corpus
    featureBase = aContext.featureBase

    features = api.Fall() + api.Eall()

    fixedModuleIndex = {}
    for m in moduleSpecs or []:
        fixedModuleIndex[
            (m["backend"] or backend, m["org"], m["repo"], m["relative"])
        ] = (
            m["corpus"],
            m["docUrl"],
        )

    moduleIndex = {}
    mLocations = app.mLocations if hasattr(app, "mLocations") else []
    baseLoc = mLocations[0] if hasattr(app, "mLocations") else ()

    for mLoc in mLocations:
        (parseOK, theBackend, org, repo, relative) = _parseFeaturePath(mLoc, backend)
        if not parseOK:
            moduleIndex[mLoc] = (theBackend, org, repo, relative, mLoc, "")
        else:
            mId = (theBackend, org, repo, relative)
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
                    f"{backendRep(backend, 'rep')}{org}/{repo}{relative}",
                    f"{backendRep(backend, 'url')}/{org}/{repo}/tree/{branch}{relative}",
                )
            )
            moduleIndex[mId] = (theBackend, org, repo, relative, corpus, docUrl)

    featureCat = {}

    for feature in features:
        added = False
        featureInfo = TF.features[feature]
        featurePath = featureInfo.path

        (parsedOK, fBackend, fOrg, fRepo, relative) = _parseFeaturePath(
            dirNm(featurePath), backend
        )

        if parsedOK:
            fRelative = prefixSlash(relative.rsplit("/", 1)[0])
            mId = (fBackend, fOrg, fRepo, fRelative)
        else:
            mId = featurePath.rsplit("/", 1)[0]

        if type(mId) is str:
            for mIId in moduleIndex:
                if type(mIId) is str:
                    if featurePath.startswith(mIId):
                        featureCat.setdefault(mIId, []).append(feature)
                        added = True
        else:
            for mIId in moduleIndex:
                if type(mIId) is not str:
                    (mBackend, mOrg, mRepo, mRelative) = mIId
                    mRelative = prefixSlash(mRelative)
                    if (
                        fBackend == mBackend
                        and fOrg == mOrg
                        and fRepo == mRepo
                        and fRelative.startswith(mRelative)
                    ):
                        featureCat.setdefault(mIId, []).append(feature)
                        added = True
        if not added:
            featureCat.setdefault(mId, []).append(feature)

    baseId = (backend, mOrg, mRepo, mRelative)
    baseMods = {
        mId for mId in featureCat.keys() if type(mId) is tuple and mId == baseId
    }
    moduleOrder = list(baseMods) + sorted(
        (mId for mId in featureCat.keys() if mId not in baseMods),
        key=lambda mId: (1, mId) if type(mId) is str else (0, mId),
    )

    output = ""

    for mId in moduleOrder:
        catFeats = featureCat[mId]
        if not catFeats:
            continue
        modInfo = moduleIndex.get(mId, None)
        if modInfo:
            (mBackend, org, repo, relative, corpus, docUrl) = modInfo
            relative = prefixSlash(relative)
        else:
            corpus = mId if type(mId) is str else "/".join(mId)
            docUrl = (
                ""
                if type(mId) is str
                else (
                    f"{backendRep(backend, 'url')}/"
                    f"{mId[0]}/{mId[1]}/tree/{branch}/{mId[2]}"
                )
            )
        output += (
            dedent(
                f"""
            <details><summary><b>{corpus}</b></summary>
                <div class="fcorpus">
        """
            )
            if doHtml
            else f"{corpus}\n"
        )

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
            valueType = featureInfo.dataType
            edgeValues = featureInfo.edgeValues
            typeRep = "none" if isEdge and not edgeValues else valueType
            meta = featureInfo.metaData
            description = meta.get("description", "")

            edgeRep = "edge" if isEdge else ""
            if doHtml:
                output += dedent(
                    f"""
                        <div class="frow">
                            <div class="fnamecat {edgeRep}">
                    """
                )
            output += (
                (
                    outLink(
                        featureRep,
                        docUrl.replace("<feature>", featureRep),
                        title=featurePath,
                        asHtml=True,
                    )
                    if docUrl
                    else f'<span title="{featurePath}">{featureRep}</span>'
                )
                if doHtml
                else f"\t{featureRep:<20} "
            )
            if doHtml:
                output += dedent(
                    f"""
                            </div>
                            <div class="fmono">{typeRep}</div>
                    """
                )
            if doHtml:
                output += dedent(
                    f"""
                            <details>
                                <summary>{description}</summary>
                                <div class="fmeta">
                    """
                    if allMeta
                    else f"""
                            <span> {description}</span>
                    """
                )
            else:
                output += f"{description}\n"
            if allMeta:
                for k, v in sorted(meta.items()):
                    if k not in {"valueType", "description"}:
                        if doHtml:
                            k = htmlEsc(k)
                            v = htmlEsc(v)
                            output += dedent(
                                f"""
                                    <div class="fmetarow">
                                        <div class="fmetakey">{k}:</div>
                                        <div>{v}</div>
                                    </div>
                            """
                            )
                        else:
                            output += f"\t\t{k}: {v}\n"
                if doHtml:
                    output += dedent(
                        """
                                    </div>
                                </details>
                        """
                    )
                else:
                    output += "\n"
            if doHtml:
                output += dedent(
                    """
                        </div>
                    """
                )
        if doHtml:
            output += dedent(
                """
                    </div>
                </details>
                """
            )
        else:
            output += "\n"
    return output


def _getSettings(app, inNb):
    """Shows the *context* of the app `tf.advanced.app.App.context` in a pretty way.

    The context is the result of computing sensible defaults for the corpus
    combined with configuration settings in the app's `config.yaml`.

    But we also list the configuration settings.

    Returns
    -------
    string
        An expandable list of the key-value pair for the requested keys.

    See Also
    --------
    tf.advanced.app.App.reuse
    tf.advanced.settings: options allowed in `config.yaml`
    """

    result = []

    for kind, data in (
        ("<b>specified</b>", app.cfgSpecs),
        ("<b>computed</b>", app.specs),
    ):
        if kind == "computed" and inNb is not None:
            continue
        result.append(showDict(f"<b>{kind}</b>", data, True, None))

    return "\n".join(result)


def provenanceLink(
    backend, org, repo, version, branch, commit, local, release, relative
):
    """Generate a provenance link for a data source.

    We assume the data source resides somewhere inside a back-end repository.

    Parameters
    ----------
    backend: string
        `github` or `gitlab` or a GitLab instance such as `gitlab.huc.knaw.nl`.
    org: string
        Organization on GitHub or group on GitLab
    repo: string
        Repository on GitHub or project on GitLab
    version: string
        Version of the data source.
        This is not the release or commit of a repo, but the subdirectory
        corresponding with a data version under a `tf` directory with feature files.
    branch: string
        The branch on the back-end of the repository (typically `master` or `main`)
    commit: string
        The commit hash of the repository
    local: boolean
        Whether the data is on the local computer and not necessarily backed up
        by a back-end repository
    release: string
        The release tag of the repository
    """

    relative = prefixSlash(relative)
    text = (
        f"data on local machine {relative}"
        if org is None or repo is None
        else (
            f"{org}/{repo}{relative} v:{version}"
            f"({Checkout.toString(commit, release, local, backend)})"
        )
    )
    relativeFlat = relative.removeprefix("/").replace("/", "-")
    bUrl = backendRep(backend, "url")
    url = (
        None
        if org is None or repo is None
        else f"{bUrl}/{org}/{repo}/tree/{branch}{relative}"
        if local
        else (
            (
                (
                    f"{bUrl}/{org}/{repo}/releases/download/{release}"
                    f"/{relativeFlat}-{version}.zip"
                )
                if backend == GH
                else (
                    f"{bUrl}/{org}/{repo}/-/archive/{release}" f"/{repo}-{version}.zip"
                )
            )
            if release
            else f"{bUrl}/{org}/{repo}/tree/{commit}{relative}"
        )
    )
    return (text, url)


def flexLink(app, kind):
    """Produce documentation links that are heavily dependent on the back-end.

    These are links to tutorials and other documentation.

    If the back-end is GitLab or GitHub, notebooks can be viewed on NBViewer.
    But if the back-end is on-premise, we assume that notebooks are
    converted to HTML and then published on the Pages of the on-premise GitLab.

    What exactly the link to such an on-premise Pages service is, may depend on
    a configuration setting.

    This function resolves all that.

    !!! note "Converting notebooks to HTML"
        There is now a tool in TF to convert a directory of notebooks to
        HTML. See `tf.tools.nbconvert`.

    Parameters
    ----------
    kind: string
        Indicates what kind of URL value should be returned:

        *   `pages`: URL of the repo in the Pages service of the back-end;
        *   `tut`: URL of the start tutorial, either on NB viewer or in the Pages
            service of the back-end.

    Returns
    -------
    string
        The complete URL.
    """
    backend = app.backend
    aContext = app.context
    org = aContext.org or ""
    repo = aContext.repo or ""
    branch = aContext.provenanceSpec["branch"]
    pages = aContext.provenanceSpec["pages"]

    if kind == "pages":
        pages = pages or backendRep(backend, kind)
        return f"https://{org}.{pages}/{repo}"

    if kind == "tut":
        be = backendRep(backend, "norm")
        onPremise = be not in {GL, GH}

        if onPremise:
            pages = pages or backendRep(backend, "pages")
            return f"https://{org}.{pages}/{repo}/tutorial/start.html"

        return f"{URL_NB}/{be}/{org}/{repo}/blob/{branch}/tutorial/start.ipynb"
