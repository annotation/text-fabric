import time
import datetime

from ..parameters import NAME, VERSION, DOI_URL_PREFIX, DOI_DEFAULT, DOI_TF, APP_URL
from ..applib.helpers import NB
from ..applib.displaysettings import INTERFACE_OPTIONS


# NAVIGATION IN MULTIPLE ITEMS (PAGES, PASSAGES)


def pageLinks(nResults, position, spread=10):
    """Provide navigation links for results sets, big or small.

    It creates links around *position* in a set of *nResults*.
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

    If `sec0` is not given, only a list of sec0 links is produced.

    If `sec0` is given, but `sec1` not, a list of links for sec1s within the given `sec0`
    is produced.

    If both `sec0` and `sec1` are given, de sec1 entry is focused.
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


def wrapOptions(context, form):
    """Wraps the options, including the app-specific ones, into HTML.
    """

    interfaceDefaults = context.interfaceDefaults

    options = {k for (k, v) in interfaceDefaults.items() if v is not None}

    html = []
    helpHtml = []
    for (option, default, acro, desc, long) in INTERFACE_OPTIONS:
        if option not in options:
            continue
        value = form[option]
        value = "checked" if value else ""
        html.append(
            f'<div><input class="r" type="checkbox" id="{acro}" name="{option}" {value}/>'
            f' <span class="ilab" title="{option}">{desc}</span></div>'
        )
        helpHtml.append(
            f'<p><b title="{option}">{desc}</b> {long}</p>'
        )
    return ("\n".join(html), "\n".join(helpHtml))


def wrapBase(allowedBaseTypes, value):
    html = []
    for (i, otype) in enumerate(allowedBaseTypes):
        checked = " checked " if otype in value else ""
        checkButton = (
            f'<input class="r bcheck" type="checkbox" name="baseTps" value="{otype}"'
            f" {checked}/>"
        )
        html.append(
            f'<div class="cline">{checkButton} <span class="ctype">{otype}</span></div>'
        )
    return "\n".join(html)


def wrapCondense(condenseTypes, value):
    """Provides a radio-buttoned chooser for the condense types.

    See `tf.applib.displaysettings`.

    `value` is the currently chosen condense type.
    """

    html = []
    lastType = len(condenseTypes) - 1
    for (i, (otype, av, b, e)) in enumerate(condenseTypes):
        checked = " checked " if value == otype else ""
        radioButton = (
            f'<span class="cradio">{NB}</span>'
            if i == lastType
            else (
                f'<input class="r cradio" type="radio" name="condenseTp"'
                f' value="{otype}" {checked}/>'
            )
        )
        html.append(
            f'<div class="cline">{radioButton} <span class="ctype">{otype}</span>'
            f' <span class="cinfo">{e - b + 1: 8.6g} x av length {av: 4.2g}</span>'
            f"</div>"
        )
    return "\n".join(html)


def wrapFormats(allFormats, value):
    """
    Provides a radio-buttoned chooser for the text formats.

    See `tf.applib.displaysettings`.

    `value` is the currently chosen format.
    """

    html = []
    for (i, fmt) in enumerate(allFormats):
        checked = " checked " if value == fmt else ""
        radioButton = (
            f'<input class="r tradio" type="radio" id="ttp{i}"'
            f' name="textformat" value="{fmt}" {checked} "/>'
        )
        html.append(
            f'<div class="tfline">{radioButton} <span class="ttext">{fmt}</span></div>'
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
        name = d["name"]
        commit = d["commit"]
        url = f"{APP_URL}/app-{name}/tree/{commit}"
        liveHtml = f'<a href="{url}">{commit}</a>'
        liveMd = f"[{commit}]({url})"
        appHtml += f"""\
    <div class="pline">
      <div class="pname">TF App:</div>
      <div class="pval">{name}</div>
    </div>
    <div class="p2line">
      <div class="pname">commit</div>
      <div class="pval">{liveHtml}</div>
    </div>\
"""
        appMd += f"""{sep}TF app | {name}
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
