import collections
from textwrap import dedent

import re
from IPython.display import display, Markdown, HTML

from ..core.helpers import htmlEsc, console
from ..core.files import (
    expanduser as ex,
    unexpanduser as ux,
    backendRep,
    TEMP_DIR,
    prefixSlash,
    dirExists,
)
from ..core.text import DEFAULT_FORMAT
from ..capable import CheckImport


NORMAL = "normal"
ORIG = "orig"

RESULT = "result"
NB = "\u00a0"
EM = "*empty*"

SEQ_TYPES1 = {tuple, list}
SEQ_TYPES2 = {tuple, list, set, frozenset}

CI = CheckImport("marimo", optional=True)
if CI.importOK(hint=False):
    marimo = CI.importGet()
else:
    marimo = None


def runsInNotebook():
    """Determines whether the program runs in an interactive shell.

    From
    [stackoverflow](https://stackoverflow.com/questions/15411967/how-can-i-check-if-code-is-executed-in-the-ipython-notebook/24937408)
    """
    if marimo is not None and marimo.running_in_notebook():
        return "marimo"
    try:
        runcontext = get_ipython()
        shell = runcontext.__class__.__name__
        if shell == "ZMQInteractiveShell":
            return "ipython"  # Jupyter notebook or qtconsole
        elif shell == "TerminalInteractiveShell":
            return None  # Terminal running IPython
        else:
            return None  # Other type (?)
    except NameError:
        return None  # Probably standard Python interpreter


def _getLtr(app, options):
    aContext = app.context
    direction = aContext.direction

    fmt = options.fmt or DEFAULT_FORMAT

    return (
        "rtl"
        if direction == "rtl" and (f"{ORIG}-" in fmt or f"-{ORIG}" in fmt)
        else ("" if direction == "ltr" else "ltr")
    )


def dm(md, inNb="ipython", unexpand=False):
    """Display markdown.

    Parameters
    ----------
    md: string
        Raw markdown string.
    inNb: boolean, optional True
        Whether the program runs in a notebook
    unexpand: boolean
        Whether to strip a potential user path from the value first

    Returns
    -------
    None
        The formatted markdown is rendered in the output cell if `inNb`
        else the raw markdown is printed to the output.
    """

    if unexpand:
        md = ux(md)

    if inNb == "ipython":
        display(Markdown(md))
    elif inNb == "marimo":
        if marimo is None:
            console(md)
        else:
            marimo.output.append(marimo.md(md))
    else:
        console(md)


def dh(html, inNb="ipython", unexpand=False):
    """Display HTML.

    Parameters
    ----------
    html: string
        Raw HTML string.
    inNb: boolean, optional True
        Whether the program runs in a notebook
    unexpand: boolean
        Whether to strip a potential user path from the value first

    Returns
    -------
    None
        The formatted HTML is rendered in the output cell if `inNb`
        else the raw HTML is printed to the output.
    """

    if unexpand:
        html = ux(html)

    if inNb == "ipython":
        display(HTML(html))
    elif inNb == "marimo":
        if marimo is None:
            console(html)
        else:
            marimo.output.append(marimo.Html(html))
    else:
        console(html)


# MODULE REFERENCES

BACKEND_RE = re.compile(r"<([^/>]*)>")


thisBackend = []


def backendRepl(match):
    thisBackend.append(match.group(1))
    return ""


def splitModRef(moduleRef):
    thisBackend.clear()
    theBackend = None
    bareModuleRef = BACKEND_RE.sub(backendRepl, moduleRef)
    if len(thisBackend):
        theBackend = thisBackend[0]
        if len(thisBackend) > 1:
            console(
                f"Multiple <backend> in {moduleRef}: "
                f"{', '.join(thisBackend)}; using <{theBackend}> only ",
                error=True,
            )

    bRep = f"<{theBackend}>" if theBackend else ""

    parts = bareModuleRef.split(":", 1)
    if len(parts) == 1:
        parts.append("")
    (ref, specifier) = parts
    parts = ref.split("/", 2)

    if len(parts) < 2:
        console(
            f"""
Module ref "{bRep}{bareModuleRef}" is not "{{org}}/{{repo}}/{{path}}"
""",
            error=True,
        )
        return None

    if len(parts) == 2:
        parts.append("")

    return [*parts, specifier, theBackend]


# COLLECT CONFIG SETTINGS IN A DICT


def getLocalDir(backend, cfg, local, version):
    provenanceSpec = cfg.get("provenanceSpec", {})
    org = provenanceSpec.get("org", None)
    repo = provenanceSpec.get("repo", None)
    relative = prefixSlash(provenanceSpec.get("relative", "tf"))
    version = provenanceSpec.get("version", None) if version is None else version
    base = hasData(backend, local, org, repo, version, relative)

    if not base:
        base = backendRep(backend, "cache")

    return ex(f"{base}/{org}/{repo}/{TEMP_DIR}")


def hasData(backend, local, org, repo, version, relative):
    versionRep = f"/{version}" if version else ""
    if local == "clone":
        cloneBase = backendRep(backend, "clone")
        ghTarget = f"{cloneBase}/{org}/{repo}{relative}{versionRep}"
        if dirExists(ghTarget):
            return cloneBase

    cacheBase = backendRep(backend, "cache")
    cacheTarget = f"{cacheBase}/{org}/{repo}{relative}{versionRep}"
    if dirExists(cacheTarget):
        return cacheBase
    return False


def tupleEnum(tuples, start, end, limit, item, inNb):
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
                f" {limit} {item}s at a time",
                inNb=inNb,
            )


def parseFeatures(features):
    if (
        type(features) in SEQ_TYPES1
        and len(features) == 2
        and type(features[0]) in SEQ_TYPES2
        and type(features[1]) is dict
    ):
        return features

    feats = (
        ()
        if not features
        else features.split()
        if type(features) is str
        else tuple(features)
    )
    return parseFeaturesLogical(feats)


def parseFeaturesLogical(feats):
    bare = []
    indirect = {}

    for feat in feats:
        if not feat:
            continue
        parts = feat.split(":", 1)
        feat = parts[-1]
        bare.append(feat)
        if len(parts) > 1:
            indirect[feat] = parts[0]
    return (bare, indirect)


def transitiveClosure(relation, reflexiveExceptions):
    """Produce the reflexive transitive closure of a relation.

    The transitive closure of a relation `R` is the relation `TR`
    such that `a TR b` if and only if there is a chain of `c1`, `c2`, ..., `cn`
    such that `a Rc1`, `c1 R c2`, ..., `cn R b`.

    If we allow the chain to have length zero, we effectively have that
    `a TR a` for all elements. That is the reflexive, transitive closure.

    This function builds the latter, but we allow for exceptions to the
    reflexivity.

    Parameters
    ----------
    relation: dict
        The input relation, keyed by elements, valued by the set of
        elements that stand in relation to the key.
    reflexiveExceptions: set
        The set of elements that will not be reflexively closed.

    Returns
    -------
    dict
        The transitive reflexive closure (with possible exceptions to
        the reflexivity) of the given relation.

    Notes
    -----
    We use this function to build the closure of the `childType` relation
    between node types. We want to exclude the slot type from the
    reflexivity. The closure of the `childType` relation is the descendant type
    relation.
    The display algorithm uses this to unravel nodes.

    See also
    --------
    tf.advanced.display: Display algorithm
    """

    descendants = {parent: set(children) for (parent, children) in relation.items()}

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
    for parent in relation:
        if parent not in reflexiveExceptions:
            descendants[parent].add(parent)
    return descendants


def htmlSafe(text, isHtml, math=False):
    return text.replace("\n", "<br>") if isHtml else htmlEsc(text, math=math)


def getText(
    app, isPretty, n, nType, outer, first, last, level, passage, descend, options=None
):
    display = app.display
    dContext = display.distill(options or {})
    ltr = _getLtr(app, dContext) or "ltr"
    showMath = dContext.showMath
    T = app.api.T
    sectionTypeSet = T.sectionTypeSet
    structureTypeSet = T.structureTypeSet

    aContext = app.context
    templates = aContext.labels if isPretty else aContext.templates

    fmt = None if options is None else options.fmt
    withLabels = True if options is None else options.withLabels
    isHtml = False if options is None else options.isHtml
    suppress = set() if options is None else options.suppress

    (tpl, feats) = templates[nType]

    if not (tpl is True or withLabels):
        return ""

    # now there is a coarse fix for something in the Hermans corpus:
    # in plain display we add a space when we fill in a template.
    # But that leads to unwanted results.
    # The problem in the Hermans corpus can be solved in other ways.
    # We remove the fix again.

    # x = "" if isPretty else " "

    tplFilled = (
        (
            (
                f"""<span class="tfsechead {ltr}"><span class="ltr">"""
                + (NB if passage else app.sectionStrFromNode(n))
                + "</span></span>"
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
                math=showMath,
            )
        )
        if tpl is True
        else (
            (
                tpl.format(
                    **{
                        feat: getValue(app, n, nType, feat, suppress, math=showMath)
                        for feat in feats
                    }
                )
                #  + x
            )
        )
    )
    return tplFilled


def getValue(app, n, nType, feat, suppress, math=False):
    F = app.api.F
    Fs = app.api.Fs

    customMethods = app.customMethods
    transform = customMethods.transform

    if feat in suppress:
        val = ""
    else:
        featObj = Fs(feat) if hasattr(F, feat) else None
        val = htmlEsc(featObj.v(n), math=math) if featObj else None
        modifier = transform.get(nType, {}).get(feat, None)
        if modifier:
            val = modifier(n, val)
        val = val.replace("\n", "\\n")
    return f'<span title="{feat}">{val}</span>'


def getHeaderTypes(app, tuples):
    api = app.api
    F = api.F
    fOtype = F.otype.v

    iTypes = collections.defaultdict(collections.Counter)

    for (t, tup) in tuples:
        if t is None:
            continue
        for (i, n) in enumerate(tup):
            iTypes[i][fOtype(n)] += 1

    headerTypes = {}

    for (i, tpInfo) in iTypes.items():
        nodeTypes = [
            ti[0] for ti in sorted(tpInfo.items(), key=lambda x: (-x[1], x[0]))
        ]
        nTypes = len(nodeTypes)
        head = nodeTypes[0]
        if nTypes > 1:
            remaining = ", ".join(nodeTypes[1:])
            head += f' <span title="{remaining}">(+{nTypes - 1})</span>'
        headerTypes[i] = head

    return headerTypes


def getHeaders(app, tuples):
    headerTypes = getHeaderTypes(app, tuples)
    headerMaterial = "</span><span>".join(
        headerTypes.get(i, f"column {i}") for i in range(len(headerTypes))
    )
    return dedent(
        f"""
        <div class="dtheadrow">
          <span>n</span><span>{headerMaterial}</span>
        </div>
        """
    )


# COMPOSE TABLES FOR CSV EXPORT


def isUniform(app, tuples):
    """Whether the members of tuples are uniform.

    An iterable of tuples of nodes is uniform, if each
    tuple has the same number of nodes,
    and if the type of a node at position `i` in the tuple
    is the same for all tuples.
    """
    api = app.api
    F = api.F
    fOtype = F.otype.v

    uniform = True
    fixedLength = None
    fixedTypes = None

    for tup in tuples:
        thisLength = len(tup)
        theseTypes = tuple(fOtype(n) for n in tup)

        if fixedLength is None:
            fixedLength = thisLength
        if fixedTypes is None:
            fixedTypes = theseTypes

        if thisLength != fixedLength or theseTypes != fixedTypes:
            uniform = False
            break

    return uniform


def getRowsX(app, tuples, features, condenseType, fmt=None):
    """Transform an iterable of nodes into a table with extra information.

    If the tuples are uniform (`isUniform`), the formatting will
    be richer then when the tuples are not uniform.
    """

    return (
        getResultsX(app, tuples, features, condenseType, fmt=fmt)
        if isUniform(app, tuples)
        else getTuplesX(app, tuples, condenseType, fmt=fmt)
    )


def getResultsX(app, results, features, condenseType, fmt=None):
    """Transform a uniform iterable of nodes into a table with extra information.

    Parameters
    ----------
    results: iterable of tuple of integer
        A uniform `isUniform` sequence of tuples of nodes
    features: key value pairs
        features per index position of the tuples.
        It specifies for some positions `i` which features for the nodes at that
        position should be looked up. For each `i` it should be an iterable
        or comma-separated list of feature names.
    condenseType: string
        A node type. Types smaller or equal than this type will have their text
        displayed in the result.
    fmt: string, optional None
        A text format. If text has to be displayed, this format is used.
        If not passed, a default is used.
    """

    api = app.api
    F = api.F
    Fs = api.Fs
    T = api.T
    N = api.N
    fOtype = F.otype.v
    otypeRank = N.otypeRank
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


def getTuplesX(app, results, condenseType, fmt=None):
    """Transform a non-uniform iterable of nodes into a table with extra information.

    Parameters
    ----------
    results: iterable of tuple of integer
        A uniform `isUniform` sequence of tuples of nodes
    condenseType: string
        A node type. Types smaller or equal than this type will have their text
        displayed in the result.
    fmt: string, optional None
        A text format. If text has to be displayed, this format is used.
        If not passed, a default is used.
    """

    api = app.api
    F = api.F
    T = api.T
    N = api.N
    fOtype = F.otype.v
    otypeRank = N.otypeRank
    sectionTypeSet = T.sectionTypeSet

    aContext = app.context
    noDescendTypes = aContext.noDescendTypes

    sectionDepth = len(sectionTypeSet)
    if len(results) == 0:
        return ()

    def withText(nodeType):
        return (
            condenseType is None
            and nodeType not in sectionTypeSet
            or otypeRank[nodeType] <= otypeRank[condenseType]
        )

    noDescendTypes = noDescendTypes

    rows = []

    for (tm, tup) in enumerate(results):
        tn = tm + 1
        row = [tn]
        for n in tup:
            sparts = T.sectionFromNode(n)
            nParts = len(sparts)
            section = sparts + ((None,) * (sectionDepth - nParts))
            row.extend(section)
            nType = fOtype(n)
            row.extend((n, nType))
            if withText(nType):
                text = T.text(n, fmt=fmt, descend=nType not in noDescendTypes)
                row.append(text)
        rows.append(tuple(row))
    return tuple(rows)


def hEmpty(x):
    return (
        "<i>no value</i>"
        if x is None
        else """<code>0</code>"""
        if x == 0
        else """<code>''</code>"""
        if x == ""
        else f"""<code>{str(x)}</code>"""
    )


def hScalar(x):
    if type(x) is str:
        x = htmlEsc(x)
        if "\n" in x:
            x = x.replace("\n", "<br>")

    xRep = f"<code>{x}</code>"
    return (len(x) < 60 if type(x) is str else True, xRep)


def hScalar0(x):
    tpv = type(x)
    if tpv is dict:
        (k, v) = list(x.items())[0]
    else:
        v = list(x)[0]

    (simple, vRep) = hData(v)

    html = (
        (
            f"{{<b>{k}</b>: {vRep}}}"
            if tpv is dict
            else f"[{vRep}]"
            if tpv is list
            else f"({vRep})"
            if tpv is tuple
            else f"{{{vRep}}}"
        )
        if simple
        else (
            f"""<li><details open>
                <summary><b>{k}</b>:</summary>
                {vRep}
                </details></li>"""
            if tpv is dict
            else f"""<li><details open>
                <summary>:</summary>
                {vRep}
                </details></li>"""
        )
    )
    return (simple, html)


def hList(x, outer=False):
    elem = f"{'o' if outer else 'u'}l"
    html = []
    html.append(f"<{elem}>")

    for v in x:
        (simple, vRep) = hData(v)

        if simple:
            html.append(f"""<li>{vRep}</li>""")
        else:
            html.append(f"""<li><details><summary>:</summary>{vRep}</details></li>""")

    html.append(f"</{elem}>")

    return "".join(html)


def hDict(x, outer=False):
    elem = f"{'o' if outer else 'u'}l"
    html = []
    html.append(f"<{elem}>")

    for (k, v) in sorted(x.items(), key=lambda y: str(y)):
        (simple, vRep) = hData(v)

        if simple:
            html.append(f"""<li><b>{k}</b>: {vRep}</li>""")
        else:
            html.append(
                f"""<li><details><summary><b>{k}</b>:</summary>{vRep}</details></li>"""
            )

    html.append(f"</{elem}>")

    return "".join(html)


def hData(x):
    if not x:
        return (True, hEmpty(x))
    tpv = type(x)
    if tpv is str or tpv is float or tpv is int or tpv is bool:
        return hScalar(x)
    if tpv is list or tpv is tuple or tpv is set or tpv is dict:
        return (
            (True, hEmpty(x))
            if len(x) == 0
            else hScalar0(x)
            if len(x) == 1
            else (False, hDict(x))
            if tpv is dict
            else (False, hList(x))
        )
    if tpv is dict:
        return (False, hDict(x))
    return hScalar(x)


def showDict(title, data, _browse, inNb, *keys):
    """Shows selected keys of a dictionary in a pretty way.

    Parameters
    ----------
    _browse: boolean
        Whether we are in the TF browser.
    inNb: boolean
        Whether we run in a notebook.
    keys: iterable of string
        For each key passed to this function, the information for that key
        will be displayed. If no keys are passed, all keys will be displayed.

    Returns
    -------
    displayed HTML
        An expandable list of the key-value pair for the requested keys.
    """

    keys = set(keys)

    html = hDict({k: v for (k, v) in data.items() if not keys or k in keys}, outer=True)
    openRep = "open" if keys else ""
    html = f"<details {openRep}><summary>{title}</summary>{html}</details>"

    if _browse:
        return html
    else:
        dh(html, inNb=inNb)
