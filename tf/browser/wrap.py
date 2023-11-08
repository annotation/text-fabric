"""
# Wrap material into HTML

Lower level functions for wrapping TF data into actual HTML that can be served.
"""

from textwrap import dedent
import time
import datetime

from ..parameters import (
    NAME,
    VERSION,
    DOI_URL_PREFIX,
    DOI_DEFAULT,
    DOI_TF,
)
from ..advanced.options import INTERFACE_OPTIONS
from ..core.files import backendRep
from ..core.helpers import TO_SYM


# NAVIGATION IN MULTIPLE ITEMS (PAGES, PASSAGES)


def pageLinks(nResults, position, spread=10):
    """Provide navigation links for results sets, big or small.

    It creates links around *position* in a set of `nResults`.
    The spread indicates how many links before and after *position* are generated
    in each column.

    There will be multiple columns. The right most column contains links
    to results `position - spread` to `position + spread`.

    Left of that there is a column for results `position - spread*spread`
    to `position + spread*spread`, stepping by `spread`.

    And so on, until the stepping factor becomes bigger than the result set.
    """

    if spread <= 1:
        spread = 1
    elif nResults == 0:
        lines = []
    elif nResults == 1:
        lines = [(1,)]
    elif nResults == 2:
        lines = [(1, 2)]
    else:
        if position == 1 or position == nResults:
            commonLine = (1, nResults)
        else:
            commonLine = (1, position, nResults)
        lines = []

        factor = 1
        while factor <= nResults:
            curSpread = factor * spread
            first = _coarsify(position - curSpread, curSpread)
            last = _coarsify(position + curSpread, curSpread)

            left = tuple(
                n for n in range(first, last, factor) if n > 0 and n < position
            )
            right = tuple(
                n for n in range(first, last, factor) if n > position and n <= nResults
            )

            both = tuple(
                n for n in left + (position,) + right if n > 0 and n <= nResults
            )

            if len(both) > 1:
                lines.append(both)

            factor *= spread

        lines.append(commonLine)

    html = "\n".join(
        '<div class="pline">'
        + " ".join(
            f'<a href="#" class="pnav {" focus" if position == p else ""}">{p}</a>'
            for p in line
        )
        + "</div>"
        for line in reversed(lines)
    )
    return html


def passageLinks(passages, sec0Type, sec0, sec1, tillLevel):
    """Provide navigation links for passages,

    in the form of links to sections of level 0, 1 and 2 (books, chapters and verses).

    If `sec0` is not given, only a list of `sec0` links is produced.

    If `sec0` is given, but `sec1` not, a list of links for `sec1` within the
    given `sec0`
    is produced.

    If both `sec0` and `sec1` are given, the `sec1` entry is focused.
    """

    sec0s = []
    sec1s = []
    for s0 in passages[0]:
        selected = str(s0) == str(sec0)
        sec0s.append(
            f'<a href="#" class="s0nav {" focus" if selected else ""}">{s0}</a>'
        )
    if sec0:
        for s1 in passages[1]:
            selected = str(s1) == str(sec1)
            sec1s.append(
                f'<a href="#" class="s1nav {" focus" if selected else ""}">{s1}</a>'
            )
    return (
        f'<div class="sline"><span><span id="s0total"></span>'
        f' <span class="s0total">{sec0Type}s</span></span>'
        + "".join(sec0s)
        + '</div><div class="sline">'
        + "".join(sec1s)
        + "</div>"
    )


# OPTIONS


COLOR_DEFAULT = "#ffff00"
E_COLOR_DEF = dict(
    b="#ffaa00",
    f="#aaaaff",
    t="#ffaaaa",
)


def wrapColorMap(form):
    """Wraps the color map for query result highlighting into HTML.

    The color map is a dict, keyed by integers (the positions of atoms
    in a query template) and the values are RGB colours (as string) or the
    empty string.

    This dict is stored in `form["colorMap"]`.
    An extra hidden input field `colormapn` helps to read this dict from the
    other form elements.
    """

    resetForm = form["resetForm"]
    if resetForm:
        colorMap = {}
    else:
        colorMap = form["colorMap"]

    colorMapN = len(colorMap)

    html = []
    html.append(
        dedent(
            """
            <details id="colormap" class="dstate">
                <summary class="ilab">query highlighting</summary>
                <div>
            """
        )
    )
    html.append(f"""<input type="hidden" name="colormapn" value="{colorMapN}">""")

    minC = """<a href="#" id="colormapmin">-</a>"""
    plusC = """<a href="#" id="colormapplus">+</a>"""

    empty = colorMapN == 0

    for pos in range(1, colorMapN + 2):
        last = pos == colorMapN
        past = pos == colorMapN + 1

        if past:
            thisHtml = f"""<div>{plusC}</div>""" if empty else ""
        else:
            color = colorMap.get(pos, "") or COLOR_DEFAULT

            thisHtml = dedent(
                f"""
                <div>
                    <input
                        type="color"
                        class="clmap"
                        pos="{pos}" name="colormap_{pos}"
                        value="{color}"
                    >
                    {minC if last else ""}
                    {plusC if last else ""}
                </div>
                """
            )
        html.append(thisHtml)

    html.append("</div></details>")

    return "\n".join(html)


def wrapEColorMap(form):
    """Wraps the edge color map for edge highlighting into HTML.
    The edge color map is a dict, keyed by pairs of integers
    (the nodes between which there is an edge) and values are RGB colours (as string).
    Each of the two integers in a pair may also be None (but not both).
    The color of `(n, None)` is used to color the outgoing edges from `n`,
    the color of (`(None, n)` is used to color the incoming edges from `n`.

    This dict is stored in `form["edgeHighlights"]`.
    An extra hidden input field `ecolormapn` helps to read this dict from the
    other form elements.
    """

    resetForm = form["resetForm"]
    if resetForm:
        edgeHighlights = {}
    else:
        edgeHighlights = form["edgeHighlights"]

    eColorMapN = sum(len(ehl) for ehl in edgeHighlights.values())

    html = []
    html.append(
        dedent(
            """
            <details id="edgefeatures" class="dstate">
                <summary class="ilab">edge highlighting</summary>
                <table id="ecolordefs">
            """
        )
    )
    html.append(f"""<input type="hidden" name="ecolormapn" value="{eColorMapN}">""")

    def sortEdges(data):
        ((f, t), c) = data
        node = t if f is None else f if t is None else min((f, t))
        kind = 2 if f is not None and t is not None else 1 if f is None else 0
        return (kind, node, c)

    pos = 0

    for eName in sorted(edgeHighlights):
        edgeInfo = edgeHighlights[eName]

        for ((f, t), color) in sorted(edgeInfo.items(), key=sortEdges):
            pos += 1
            fRep = "any" if f is None else f
            fVal = "any" if f is None else f
            tRep = "any" if t is None else t
            tVal = "any" if t is None else t
            if not color:
                color = E_COLOR_DEF["t" if f is None else "f" if t is None else "b"]
            thisHtml = dedent(
                f"""
                <tr>
                    <td><span class="ctype">{eName}</span></td>
                    <td>
                        <input
                            type="color" class="eclmap"
                            name="ecolormap_{pos}" value="{color}"
                        >
                    </td>
                    <td><a href="#" pos="{pos}" class="ecolormapmin">-</a></td>
                    <td><span class="nde">{fRep}</span></td>
                    <td><span>{TO_SYM}</td>
                    <td><span class="nde">{tRep}</span></td>
                </tr>
                <input type="hidden" name="edge_name_{pos}" value="{eName}">
                <input type="hidden" name="edge_from_{pos}" value="{fVal}">
                <input type="hidden" name="edge_to_{pos}" value="{tVal}">
                """
            )
            html.append(thisHtml)

    html.append("</table>")

    newEHL = dedent(
        f"""
        <input type="hidden" name="ecolormap_new_1" value="{E_COLOR_DEF['b']}" >
        <input type="hidden" name="edge_name_new_1" value="">
        <input type="hidden" name="edge_from_new_1" value="">
        <input type="hidden" name="edge_to_new_1" value="">
        <input type="hidden" name="ecolormap_new_2" value="{E_COLOR_DEF['f']}" >
        <input type="hidden" name="edge_name_new_2" value="">
        <input type="hidden" name="edge_from_new_2" value="">
        <input type="hidden" name="edge_to_new_2" value="">
        <input type="hidden" name="ecolormap_new_3" value="{E_COLOR_DEF['t']}" >
        <input type="hidden" name="edge_name_new_3" value="">
        <input type="hidden" name="edge_from_new_3" value="">
        <input type="hidden" name="edge_to_new_3" value="">
        """
    )
    html.append(newEHL)

    html.append("</details>")

    return "\n".join(html)


def wrapOptions(context, form):
    """Wraps the boolean options, including the app-specific ones, into HTML."""

    interfaceDefaults = context.interfaceDefaults
    defaults = {k: v for (k, v) in interfaceDefaults.items() if v is not None}
    resetForm = form["resetForm"]

    html = []
    htmlMoved = {}
    helpHtml = []
    for (option, default, acro, desc, long, move) in INTERFACE_OPTIONS:
        if option not in defaults:
            continue
        value = defaults[option] if resetForm else form[option]
        value = "checked" if value else ""
        outer = "span" if move else "div"
        thisHtml = (
            f"<{outer}>"
            f'<input class="r" type="checkbox" id="{acro}" name="{option}" {value}/>'
            f' <span class="ilab" title="{option}">{desc}</span>'
            f"</{outer}>"
        )
        helpHtml.append(f'<p><b title="{option}">{desc}</b> {long}</p>')
        if move:
            htmlMoved[option] = thisHtml
        else:
            html.append(thisHtml)
    return ("\n".join(html), htmlMoved, "\n".join(helpHtml))


def wrapSelect(option, allowedValues, value, group, item, multiple):
    """Provides a buttoned chooser for the node types.

    Some options need node types as values: `baseTypes`, `condenseType`, `hiddenType`.
    See `tf.advanced.options`.

    The chooser supports single value and multiple value mode.

    Parameters
    ----------
    option: string
        The name of the option
    allowedValues: dict
        Keyed by option, the values are tuples of allowed values for that option
        in the right order.
    value: string | set of string
        The current value of the option. In the case of multiple values, this
        is a set of values.
    group: string
        An extra class name helping to group the relevant buttons together
    item: string
        An extra pair of class names for formatting each option line
    multiple: boolean
        If `True`, the options appear as check boxes, and multiple values
        can be selected. Otherwise, the options appear as radio boxes, of which
        at most one can be selected.

    Returns
    -------
    string
        A HTML fragment containing the options with the current value(s) selected.
    """

    html = []
    for val in allowedValues[option]:
        logicValue = val in value if multiple else val == value
        checked = " checked " if logicValue else ""
        bType = "checkbox" if multiple else "radio"
        button = (
            f'<input class="r {group}" type="{bType}" name="{option}" value="{val}"'
            f" {checked}/>"
        )
        html.append(
            f'<div class="{item[0]}">{button} <span class="{item[1]}">{val}</span></div>'
        )
    return "\n".join(html)


# PROVENANCE


def wrapProvenance(form, provenance, setNames):
    utc_offset_sec = time.altzone if time.localtime().tm_isdst else time.timezone
    utc_offset = datetime.timedelta(seconds=-utc_offset_sec)
    now = (
        datetime.datetime.now()
        .replace(microsecond=0, tzinfo=datetime.timezone(offset=utc_offset))
        .isoformat()
    )
    job = form["jobName"]
    author = form["author"]

    (appProvenance, dataProvenance) = provenance

    appHtml = ""
    appMd = ""
    sep = ""

    for d in appProvenance:
        d = dict(d)
        backend = d["backend"]
        bUrl = backendRep(backend, "url")
        bName = backendRep(backend, "name")
        org = d["org"]
        repo = d["repo"]
        commit = d["commit"]
        url = f"{bUrl}/{org}/{repo}/tree/{commit}"
        liveHtml = f'<a href="{url}">{commit}</a>'
        liveMd = f"[{commit}]({url})"
        appHtml += f"""\
    <div class="pline">
      <div class="pname">TF App:</div>
      <div class="pval">{org}/{repo} on {bName}</div>
    </div>
    <div class="p2line">
      <div class="pname">commit</div>
      <div class="pval">{liveHtml}</div>
    </div>\
"""
        appMd += f"""{sep}TF app | {org}/{repo} on {bName}
commit | {liveMd}"""
        sep = "\n"

    dataHtml = ""
    dataMd = ""
    sep = ""

    for d in dataProvenance:
        d = dict(d)
        corpus = d["corpus"]
        version = d["version"]
        release = d["release"]
        (liveText, liveUrl) = d["live"]
        liveHtml = f'<a href="{liveUrl}">{liveText}</a>'
        liveMd = f"[{liveText}]({liveUrl})"
        doi = d["doi"]
        doiUrl = f"{DOI_URL_PREFIX}/{doi}"
        doiHtml = f'<a href="{doiUrl}">{doi}</a>' if doi else DOI_DEFAULT
        doiMd = f"[{doi}]({doiUrl})" if doi else DOI_DEFAULT
        dataHtml += f"""\
    <div class="pline">
      <div class="pname">Data:</div>
      <div class="pval">{corpus}</div>
    </div>
    <div class="p2line">
      <div class="pname">version</div>
      <div class="pval">{version}</div>
    </div>
    <div class="p2line">
      <div class="pname">release</div>
      <div class="pval">{release}</div>
    </div>
    <div class="p2line">
      <div class="pname">download</div>
      <div class="pval">{liveHtml}</div>
    </div>
    <div class="p2line">
      <div class="pname">DOI</div>
      <div class="pval">{doiHtml}</div>
    </div>\
"""
        dataMd += f"""{sep}Data source | {corpus}
version | {version}
release | {release}
download   | {liveMd}
DOI | {doiMd}"""
        sep = "\n"

    setHtml = ""
    setMd = ""

    if setNames:
        setNamesRep = ", ".join(setNames)
        setHtml += f"""\
    <div class="psline">
      <div class="pname">Sets:</div>
      <div class="pval">{setNamesRep} (<b>not exported</b>)</div>
    </div>\
"""
        setMd += f"""Sets | {setNamesRep} (**not exported**)"""

    tool = f"{NAME} {VERSION}"
    toolDoiUrl = f"{DOI_URL_PREFIX}/{DOI_TF}"
    toolDoiHtml = f'<a href="{toolDoiUrl}">{DOI_TF}</a>'
    toolDoiMd = f"[{DOI_TF}]({toolDoiUrl})"

    html = f"""
    <div class="pline">\
      <div class="pname">Job:</div><div class="pval">{job}</div>
    </div>
    <div class="pline">
      <div class="pname">Author:</div><div class="pval">{author}</div>
    </div>
    <div class="pline">
      <div class="pname">Created:</div><div class="pval">{now}</div>
    </div>
    {dataHtml}
    {setHtml}
    <div class="pline">
      <div class="pname">Tool:</div>
      <div class="pval">{tool} {toolDoiHtml}</div>
    </div>
    {appHtml}\
  """

    md = f"""
meta | data
--- | ---
Job | {job}
Author | {author}
Created | {now}
{dataMd}
{setMd}
Tool | {tool} {toolDoiMd}
{appMd}
"""

    return (html, md)


# LOWER LEVEL


def _coarsify(n, spread):
    nAbs = int(round(abs(n) / spread)) * spread
    return nAbs if n >= 0 else -nAbs
