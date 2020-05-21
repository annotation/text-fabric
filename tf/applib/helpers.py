import os

from IPython.display import display, Markdown, HTML

from ..parameters import EXPRESS_BASE, GH_BASE, TEMP_DIR
from ..core.helpers import htmlEsc


RESULT = "result"
NB = "\u00a0"

SEQ_TYPES1 = {tuple, list}
SEQ_TYPES2 = {tuple, list, set, frozenset}


def dm(md):
    """Display markdown in a Jupyter notebook.

    Parameters
    ----------
    md: string
        Raw markdown string.

    Returns
    -------
    None
        The formatted markdown is rendered in the output cell.
    """

    display(Markdown(md))


def dh(html):
    """Display HTML in a Jupyter notebook.

    Parameters
    ----------
    html: string
        Raw html string.

    Returns
    -------
    None
        The formatted HTML is rendered in the output cell.
    """

    display(HTML(html))


# COLLECT CONFIG SETTINGS IN A DICT


def getLocalDir(cfg, local, version):
    provenanceSpec = cfg.get("provenanceSpec", {})
    org = provenanceSpec.get("org", None)
    repo = provenanceSpec.get("repo", None)
    relative = provenanceSpec.get("relative", "tf")
    version = provenanceSpec.get("version", None) if version is None else version
    base = hasData(local, org, repo, version, relative)

    if not base:
        base = EXPRESS_BASE

    return os.path.expanduser(f"{base}/{org}/{repo}/{TEMP_DIR}")


def hasData(local, org, repo, version, relative):
    versionRep = f"/{version}" if version else ""
    if local == "clone":
        ghBase = os.path.expanduser(GH_BASE)
        ghTarget = f"{ghBase}/{org}/{repo}/{relative}{versionRep}"
        if os.path.exists(ghTarget):
            return ghBase

    expressBase = os.path.expanduser(EXPRESS_BASE)
    expressTarget = f"{expressBase}/{org}/{repo}/{relative}{versionRep}"
    if os.path.exists(expressTarget):
        return expressBase
    return False


def tupleEnum(tuples, start, end, limit, item):
    if start is None:
        start = 1
    i = -1
    if not hasattr(tuples, "__len__"):
        if end is None or end - start + 1 > limit:
            end = start - 1 + limit
        for tup in tuples:
            i += 1
            if i < start - 1:
                continue
            if i >= end:
                break
            yield (i + 1, tup)
    else:
        if end is None or end > len(tuples):
            end = len(tuples)
        rest = 0
        if end - (start - 1) > limit:
            rest = end - (start - 1) - limit
            end = start - 1 + limit
        for i in range(start - 1, end):
            yield (i + 1, tuples[i])
        if rest:
            dh(
                f"<b>{rest} more {item}s skipped</b> because we show a maximum of"
                f" {limit} {item}s at a time"
            )


def parseFeatures(features):
    if (
        type(features) in SEQ_TYPES1
        and len(features) == 2
        and type(features[0]) in SEQ_TYPES2
        and type(features[1]) is dict
    ):
        return features

    bare = []
    indirect = {}
    feats = (
        ()
        if not features
        else features.split()
        if type(features) is str
        else tuple(features)
    )
    for feat in feats:
        if not feat:
            continue
        parts = feat.split(":", 1)
        feat = parts[-1]
        bare.append(feat)
        if len(parts) > 1:
            indirect[feat] = parts[0]
    return (bare, indirect)


def transitiveClosure(relation):
    descendants = {}
    for (parent, children) in relation.items():
        descendants[parent] = set(children)

    changed = True
    while changed:
        changed = False
        for (parent, children) in relation.items():
            for child in children:
                if child in descendants:
                    for grandChild in descendants[child]:
                        if grandChild not in descendants[parent]:
                            descendants[parent].add(grandChild)
                            changed = True
    return descendants


def htmlSafe(text, isHtml):
    return text if isHtml else htmlEsc(text)


def getText(
    app, isPretty, n, nType, outer, first, last, level, passage, descend, dContext=None
):
    T = app.api.T
    sectionTypeSet = T.sectionTypeSet
    structureTypeSet = T.structureTypeSet

    aContext = app.context
    templates = aContext.labels if isPretty else aContext.templates

    fmt = None if dContext is None else dContext.fmt
    standardFeatures = True if dContext is None else dContext.standardFeatures
    isHtml = False if dContext is None else dContext.isHtml
    suppress = set() if dContext is None else dContext.suppress

    (tpl, feats) = templates[nType]

    tplFilled = (
        (
            (
                '<span class="section">'
                + (NB if passage else app.sectionStrFromNode(n))
                + "</span>"
            )
            if nType in sectionTypeSet
            else f'<span class="structure">{app.structureStrFromNode(n)}</span>'
            if nType in structureTypeSet
            else htmlSafe(
                T.text(
                    n,
                    fmt=fmt,
                    descend=descend,
                    outer=outer,
                    first=first,
                    last=last,
                    level=level,
                ),
                isHtml,
            )
        )
        if tpl is True
        else (
            tpl.format(
                **{feat: getValue(app, n, nType, feat, suppress) for feat in feats}
            )
            if standardFeatures
            else ""
        )
    )
    return tplFilled


def getValue(app, n, nType, feat, suppress):
    F = app.api.F
    Fs = app.api.Fs

    aContext = app.context
    transform = aContext.transform
    if feat in suppress:
        val = ""
    else:
        featObj = Fs(feat) if hasattr(F, feat) else None
        val = htmlEsc(featObj.v(n)) if featObj else None
        modifier = transform.get(nType, {}).get(feat, None)
        if modifier:
            val = modifier(n, val)
    return f'<span title="{feat}">{val}</span>'


# COMPOSE TABLES FOR CSV EXPORT


def getResultsX(app, results, features, condenseType, fmt=None):
    api = app.api
    F = api.F
    Fs = api.Fs
    T = api.T
    fOtype = F.otype.v
    otypeRank = api.otypeRank
    sectionTypeSet = T.sectionTypeSet

    aContext = app.context
    noDescendTypes = aContext.noDescendTypes

    sectionDepth = len(sectionTypeSet)
    if len(results) == 0:
        return ()
    firstResult = results[0]
    nTuple = len(firstResult)
    refColumns = [
        i for (i, n) in enumerate(firstResult) if fOtype(n) not in sectionTypeSet
    ]
    refColumn = refColumns[0] if refColumns else nTuple - 1
    header = ["R"] + [f"S{i}" for i in range(1, sectionDepth + 1)]
    emptyA = []

    featureDict = {i: tuple(f.split()) if type(f) is str else f for (i, f) in features}

    def withText(nodeType):
        return (
            condenseType is None
            and nodeType not in sectionTypeSet
            or otypeRank[nodeType] <= otypeRank[condenseType]
        )

    noDescendTypes = noDescendTypes

    for j in range(nTuple):
        i = j + 1
        n = firstResult[j]
        nType = fOtype(n)
        header.extend([f"NODE{i}", f"TYPE{i}"])
        if withText(nType):
            header.append(f"TEXT{i}")
        header.extend(f"{feature}{i}" for feature in featureDict.get(j, emptyA))
    rows = [tuple(header)]
    for (rm, r) in enumerate(results):
        rn = rm + 1
        row = [rn]
        refN = r[refColumn]
        sparts = T.sectionFromNode(refN)
        nParts = len(sparts)
        section = sparts + ((None,) * (sectionDepth - nParts))
        row.extend(section)
        for j in range(nTuple):
            n = r[j]
            nType = fOtype(n)
            row.extend((n, nType))
            if withText(nType):
                text = T.text(n, fmt=fmt, descend=nType not in noDescendTypes)
                row.append(text)
            row.extend(Fs(feature).v(n) for feature in featureDict.get(j, emptyA))
        rows.append(tuple(row))
    return tuple(rows)
