"""
# Display

Where the advanced API really shines is in displaying nodes.
There are basically two ways of displaying a node:

*   *plain*: just the associated text of a node, or if that would be too much,
    an identifying label of that node (e.g. for books, chapters and lexemes).
*   *pretty*: a display of the internal structure of the textual object a node
    stands for. That structure is adorned with relevant feature values.

These display methods are available for nodes, tuples of nodes, and iterables
of tuples of nodes (think: query results).
The names of these methods are

*   `plain`, `plainTuple`, and `table`;
*   `pretty`, `prettyTuple` and `show`.

In plain and pretty displays, certain parts can be *highlighted*, which is
good for displaying query results where the parts that correspond directly to the
search template are highlighted.

## Display parameters

There is a bunch of parameters that govern how the display functions arrive at their
results. You can pass them as optional arguments to these functions,
or you can set up them in advance, and reset them to their original state
when you are done.

All calls to the display functions look for the values for these parameters in the
following order:

*   optional parameters passed directly to the function,
*   values as set up by previous calls to `displaySetup()`,
*   corpus dependent default values configured by the advanced API.

See `tf.advanced.options` for a list of display parameters.

## Rendering

Both `pretty` and `plain` are implemented as a call to the
`tf.advanced.render.render` function.

## See also

All about the nature and implementation of the display algorithm is in
`tf.about.displaydesign`.
"""


import types
from textwrap import dedent

from ..core.helpers import mdEsc, tsvEsc
from ..core.files import (
    fileOpen,
    normpath,
    abspath,
    dirMake,
    dirNm,
    expanduser as ex,
    DOWNLOADS,
    SERVER_DISPLAY_BASE,
    SERVER_DISPLAY,
    TOOL_DISPLAY_BASE,
    TOOL_DISPLAY,
)
from ..core.timestamp import SILENT_D, silentConvert
from .helpers import getHeaderTypes, getRowsX, tupleEnum, RESULT, dh, showDict, _getLtr
from .condense import condense, condenseSet
from .highlight import getTupleHighlights
from .options import Options
from .render import render
from .unravel import unravel

LIMIT_SHOW = 100
LIMIT_TABLE = 2000


def displayApi(app, silent=SILENT_D):
    """Produce the display API.

    The display API provides methods to generate styled representations
    of pieces of corpus texts in their relevant structures.
    The main end-user functions are `plain(node)` and `pretty(node)`.

    `plain()` focuses on the plain text, `pretty()` focuses on structure
    and feature display.

    Related are `plainTuple()` and `prettyTuple()` that work for tuples
    instead of nodes.

    And further there are `show()` and `table()`, that work
    with iterables of tuples of nodes (e.g. query results).

    Parameters
    ----------
    app: obj
        The high-level API object
    silent: string, optional `tf.core.timestamp.SILENT_D`
        See `tf.core.timestamp.Timestamp`
        Normally this parameter is taken from the app,
        but when we do an `A.reuse()` we force `silent="deep"`.
    """

    silent = silentConvert(silent)
    app.export = types.MethodType(export, app)
    app.table = types.MethodType(table, app)
    app.plainTuple = types.MethodType(plainTuple, app)
    app.plain = types.MethodType(plain, app)
    app.show = types.MethodType(show, app)
    app.prettyTuple = types.MethodType(prettyTuple, app)
    app.pretty = types.MethodType(pretty, app)
    app.unravel = types.MethodType(unravel, app)
    app.loadCss = types.MethodType(loadCss, app)
    app.loadToolCss = types.MethodType(loadToolCss, app)
    app.getCss = types.MethodType(getCss, app)
    app.getToolCss = types.MethodType(getToolCss, app)
    app.displayShow = types.MethodType(displayShow, app)
    app.displaySetup = types.MethodType(displaySetup, app)
    app.displayReset = types.MethodType(displayReset, app)

    app.display = Options(app)
    if not app._browse:
        app.loadCss()


def displayShow(app, *options):
    """Show display parameters.

    Shows current values of all or selected display parameters.

    Parameters
    ----------
    options: keys
        Options of which the current value will be shown.
        If no option is passes, all options will be shown.

    See Also
    --------
    tf.advanced.settings: options allowed in `config.yaml`
    """

    inNb = app.inNb
    _browse = app._browse
    display = app.display
    display.setup()
    data = display.current
    return showDict("<b>current display options</b>", data, _browse, inNb, *options)


def displaySetup(app, *show, **options):
    """Set up all display parameters.

    Shows current values of display parameters and/or
    assigns working values to display parameters.
    All subsequent calls to display functions such as `plain` and `pretty`
    will use these values, unless they themselves are passed overriding
    values as arguments.

    These working values remain in effect until a new call to `displaySetup()`
    assigns new values, or a call to `displayReset()` resets the values to the
    defaults.

    !!! hint "show current values"
        The defaults themselves come from the corpus settings, which are influenced
        by its `config.yaml` file, if it exists. See `tf.advanced.settings`.
        You can show the current values by means of `displayShow`.

    Parameters
    ----------
    show: list
        Options of which the current value will be shown.
    options: dict
        Explicit values for selected options that act as overrides of the defaults.

    See Also
    --------
    tf.advanced.settings: options allowed in `config.yaml`
    tf.advanced.options: all available display options
    """

    display = app.display

    display.setup(*show, **options)


def displayReset(app, *options):
    """Restore display parameters to their defaults.

    Reset the given display parameters to their default value and let the others
    retain their current value.

    So you can reset the display parameters selectively.

    Parameters
    ----------
    options: list, optional []
        If present, only restore these options to their defaults.
        Otherwise, restore all display settings.
    """

    display = app.display

    display.reset(*options)


def loadCss(app):
    """Load the CSS for this app.

    If we are in the TF browser, the generic CSS is already provided, we only
    need to respond with the app-specific CSS: we return it as string.
    The flag `app._browse` is used to steer us into this case.

    Otherwise, if we are in a notebook,
    we collect the complete CSS code from TF and the app,
    and we add a piece to override some of the notebook CSS for tables,
    which specify a table layout with right aligned cell contents by default.

    We then load the resulting CSS into the notebook.

    Otherwise, we do nothing.

    Returns
    -------
    None | string
        When in the TF browser, the app-dependent CSS is returned.
        Otherwise, nothing is returned, but the complete CSS is displayed as HTML in the notebook.
    """

    _browse = app._browse
    aContext = app.context
    appCss = aContext.css

    if _browse:
        return appCss

    if not app.inNb:
        return

    css = getCss(app)
    dh(css)
    dh(
        dedent(
            """
            <script>
            globalThis.copyChar = (el, c) => {
                for (const el of document.getElementsByClassName('ccon')) {
                    el.className = 'ccoff'
                }
                el.className = 'ccon'
                navigator.clipboard.writeText(String.fromCharCode(c))
            }
            </script>
            """
        )
    )


def getCss(app):
    """Export the CSS for this app.

    We collect the complete CSS code from TF and the app,
    and we add a piece to override some of the notebook CSS for tables,
    which specify a table layout with right aligned cell contents by default.

    Returns
    -------
    None | string
        CSS code, including a surrounding `style` element.
    """

    aContext = app.context
    appCss = aContext.css

    cssPath = f"{dirNm(dirNm(abspath(__file__)))}" f"{SERVER_DISPLAY_BASE}"
    cssPath = normpath(cssPath)
    genericCss = ""
    for cssFile in SERVER_DISPLAY:
        with fileOpen(f"{cssPath}/{cssFile}") as fh:
            genericCss += fh.read()

    tableCss = (
        "tr.tf.ltr, td.tf.ltr, th.tf.ltr { text-align: left ! important;}\n"
        "tr.tf.rtl, td.tf.rtl, th.tf.rtl { text-align: right ! important;}\n"
    )
    return f"<style>{tableCss}{genericCss}{appCss}</style>"


def loadToolCss(app, tool, extraCss):
    """Load the Tool CSS for this app.

    We assume that the generic CSS and the app-specific CSS are already in place.

    If we are in the TF browser, we return the CSS as string.
    The flag `app._browse` is used to steer us into this case.

    Otherwise, if we are in a notebook, we load the resulting CSS into the notebook.

    Otherwise, we do nothing.

    Parameters
    ----------
    tool: string
        The name of the tool

    extraCss: string
        CSS code that is not in a file, but generated by the tool.

    Returns
    -------
    None | string
        See the description above
    """

    _browse = app._browse
    toolCss = getToolCss(app, tool) + extraCss

    if _browse:
        return toolCss

    if not app.inNb:
        return

    dh(toolCss)


def getToolCss(app, tool):
    """Export the CSS for a tool of this app.

    Parameters
    ----------
    tool: string
        The name of the tool

    Returns
    -------
    None | string
        CSS code, including a surrounding `style` element.
    """
    thisToolDisplayBase = TOOL_DISPLAY_BASE.format(tool)
    cssPath = f"{dirNm(dirNm(abspath(__file__)))}" f"{thisToolDisplayBase}"
    cssPath = normpath(cssPath)
    toolCss = ""

    for cssFile in TOOL_DISPLAY:
        with fileOpen(f"{cssPath}/{cssFile}") as fh:
            toolCss += fh.read()

    return f"<style>{toolCss}</style>"


def export(app, tuples, toDir=None, toFile="results.tsv", **options):
    """Exports an iterable of tuples of nodes to an Excel friendly TSV file.

    !!! hint "Examples"
        See for detailed examples the
        [exportExcel (ETCBC/bhsa)](https://nbviewer.jupyter.org/github/etcbc/bhsa/blob/master/tutorial/exportExcel.ipynb)
        and
        [exportExcel (Nino-cunei/oldbabylonian)](https://nbviewer.jupyter.org/github/Nino-cunei/oldbabylonian/blob/master/tutorial/exportExcel.ipynb)
        notebooks.

    Parameters
    ----------
    tuples: iterable of tuples of integer
        The integers are the nodes, together they form a table.
        The table maybe uniform or not uniform,
        which matters to the output. See below.
    toDir: string, optional None
        The destination directory for the exported file.
        By default it is your Downloads folder.

        If the directory does not exist, it will be created.
    toFile: boolean, optional `results.tsv`
        The name of the exported file.
    options: dict
        Display options, see `tf.advanced.options`.

        !!! note "details"
            *   `condensed`
                Has no effect. Exports to Excel will not be condensed, because the
                number of columns is variable per row in that case.
                Excel itself has nice possibilities for grouping rows.
                You can also filter your tuples by means of hand-coding
                before exporting them.
            *   `condenseType`
                The condense type influences for which nodes
                the full text will be exported.
                Only nodes that are "smaller" than the condense type will have
                their full text exported.
            *   `fmt`
                This display parameter specifies the text format for any nodes
                that trigger a text value to be exported.
            *   `tupleFeatures`
                This is a display parameter that steers which features are exported
                with each member of the tuples in the list.

                If the iterable of tuples are the results of a query you have just
                run, then an appropriate call to `displaySetup(tupleFeatures=...)`
                has already been issued, so you can just say:

                    results = A.search(query)
                    A.export(results)

    Results
    -------
    A file `toFile` in directory `toDir` with the following content:

    There will be a row for each tuple.

    If the input tuples are *uniform*, i.e. each tuple has the
    same number of nodes, and nodes in the same column have the same node types,
    then the result table has the following layout:

    The columns are:

    *   `R` the sequence number of the result tuple in the result list
    *   `S1 S2 S3` the section as book, chapter, verse, in separate columns;
        the section is the section of the first non book / chapter node in the tuple
    *   `NODEi TYPEi` the node and its type,
        for each node `i` in the result tuple
    *   `TEXTi` the full text of node `i`,
        if the node type admits a concise text representation;
        the criterion is whether the node type has a type not bigger than the
        default condense type, which is app specific.
        If you pass an explicit `condenseType=xxx` as display parameter,
        then this is the reference `condenseType` on which the decision is based.
    *   `XFi` the value of extra feature `XF` for node `i`,
        where these features have been declared by a previous
        `displaySetup(tupleFeatures=...)`

    If the input tuples are not uniform, the layout is more primitive.
    There will be no header column, because the number of columns may vary per row.
    A row contains the successive information of all nodes in a tuple.
    Depending of the type of each node you get a number of columns of section information.
    Then follow two columns with the node and the node type.
    Depending on the type of the node, there follows a column with the text of the node.
    No additional features are produced.

    !!! caution "Encoding"
        The exported file is written in the `utf_16_le` encoding.
        This ensures that Excel can open it without hassle, even if there
        are non-latin characters inside.

        When you want to read the exported file programmatically,
        open it with `encoding=utf_16`.

    !!! caution "Quotes"
        If the text of a field starts with a single or double quote,
        we insert a backslash in front of it, otherwise programs like
        Excel and Numbers will treat it in a special way.
    """

    display = app.display

    if not display.check("table", options):
        return ""

    dContext = display.distill(options)
    fmt = dContext.fmt
    condenseType = dContext.condenseType
    tupleFeatures = dContext.tupleFeatures

    toDir = ex(DOWNLOADS) if toDir is None else ex(toDir)
    dirMake(toDir)
    toPath = f"{toDir}/{toFile}"

    resultsX = getRowsX(app, tuples, tupleFeatures, condenseType, fmt=fmt)

    with fileOpen(toPath, mode="w", encoding="utf_16_le") as fh:
        fh.write(
            "\ufeff"
            + "".join(
                ("\t".join("" if t is None else tsvEsc(t) for t in tup) + "\n")
                for tup in resultsX
            )
        )


# PLAIN and FRIENDS


def table(app, tuples, _asString=False, **options):
    """Plain displays of an iterable of tuples of nodes in a table.

    The list is displayed as a compact markdown table.
    Every row is prepended with the sequence number in the iterable,
    and then displayed by `plainTuple`

    !!! hint "`condense`, `condenseType`"
        You can condense the list first to containers of `condenseType`,
        before displaying the list.
        Pass the display parameters `condense` and `condenseType`.
        See `tf.advanced.options`.

    Parameters
    ----------
    tuples: iterable of tuples of integer
        The integers are the nodes, together they form a table.
    options: dict
        Display options, see `tf.advanced.options`.
    _asString: boolean, optional False
        Whether to deliver the result as a HTML string or to display it directly
        inside a notebook. When the TF browser uses this function it needs the
        HTML string.
    """

    display = app.display

    if not display.check("table", options):
        return ""

    _browse = app._browse
    inNb = app.inNb

    api = app.api

    dContext = display.distill(options)
    end = dContext.end
    start = dContext.start
    withPassage = dContext.withPassage
    condensed = dContext.condensed
    condenseType = dContext.condenseType
    skipCols = dContext.skipCols

    ltr = _getLtr(app, dContext) or "ltr"

    item = condenseType if condensed else RESULT

    if condensed:
        tuples = condense(api, tuples, condenseType, multiple=True)
        skipCols = set()

    passageHead = f'</th><th class="tf {ltr}">p' if withPassage is True else ""

    html = []
    one = True

    newOptions = display.consume(options, "skipCols")

    theseTuples = tuple(tupleEnum(tuples, start, end, LIMIT_TABLE, item, inNb))
    headerTypes = getHeaderTypes(app, theseTuples)

    for (i, tup) in theseTuples:
        if one:
            heads = '</th><th class="tf">'.join(
                headerTypes.get(i, f"column {i}") for i in range(len(headerTypes))
            )
            html.append(
                f'<tr class="tf {ltr}">'
                f'<th class="tf {ltr}">n{passageHead}</th>'
                f'<th class="tf {ltr}">{heads}</th>'
                f"</tr>"
            )
            one = False
        html.append(
            plainTuple(
                app,
                tup,
                seq=i,
                item=item,
                position=None,
                opened=False,
                _asString=True,
                skipCols=skipCols,
                **newOptions,
            )
        )
    html = "<table>" + "\n".join(html) + "</table>"

    if _browse or _asString:
        return html
    dh(html, inNb=inNb)


def plainTuple(
    app,
    tup,
    seq=None,
    item=RESULT,
    position=None,
    opened=False,
    _asString=False,
    **options,
):
    """Display the plain text of a tuple of nodes.

    Displays the material that corresponds to a tuple of nodes
    as a row of cells,
    each displaying a member of the tuple by means of `plain`.

    Parameters
    ----------
    tup: iterable of integer
        The members of the tuple can be arbitrary nodes.
    seq: integer, optional None
        an arbitrary number which will be displayed in the first cell.
        This prepares the way for displaying query results, which come as
        a sequence of tuples of nodes.
        If None, no such number is displayed in the heading.
    item: string, optional result
        A name for the tuple: it could be a result, or a chapter, or a line.
    position: integer, optional None
        Which position counts as the focus position.
        If *seq* equals *position*, the tuple is in focus.
        The effect is to add the CSS class *focus* to the output HTML
        for the row of this tuple.
    opened:  boolean, optional False
        Whether this tuple should be expandable to a `pretty` display.
        The normal output of this row will be wrapped in a

            <details><summary>plain</summary>pretty</details>

        pattern, so that the user can click a triangle to switch between plain
        and pretty display.

        !!! caution
            This option has only effect when used in the TF browser.
    options: dict
        Display options, see `tf.advanced.options`.
    _asString: boolean, optional False
        Whether to deliver the result as a HTML string or to display it directly
        inside a notebook. When the TF browser uses this function it needs the
        HTML string.

    Result
    ------
    string or `None`
        Depending on `asString` above.
    """

    display = app.display

    if not display.check("plainTuple", options):
        return ""

    api = app.api
    F = api.F
    T = api.T
    N = api.N
    otypeRank = N.otypeRank
    fOtypev = F.otype.v
    _browse = app._browse
    inNb = app.inNb

    dContext = display.distill(options)
    condensed = dContext.condensed
    condenseType = dContext.condenseType
    colorMap = dContext.colorMap
    highlights = dContext.highlights
    withPassage = dContext.withPassage
    skipCols = dContext.skipCols
    showMath = dContext.showMath

    if condensed:
        skipCols = set()

    ltr = _getLtr(app, dContext) or "ltr"

    if withPassage is True:
        passageNode = _getRefMember(otypeRank, fOtypev, tup, dContext)
        passageRef = (
            ""
            if passageNode is None
            else app._sectionLink(passageNode)
            if _browse
            else app.webLink(passageNode, _asString=True)
        )
        passageRef = (
            f"""<span class="tfsechead {ltr}">"""
            f"""<span class="ltr">{passageRef}</span></span>"""
        )
    else:
        passageRef = ""

    newOptions = display.consume(options, "withPassage")
    newOptionsH = display.consume(options, "withPassage", "highlights")

    highlights = getTupleHighlights(api, tup, highlights, colorMap, condenseType)

    if _browse:
        prettyRep = (
            prettyTuple(app, tup, seq=seq, withPassage=False, **newOptions)
            if opened
            else ""
        )
        current = "focus" if seq is not None and seq == position else ""
        attOpen = "open " if opened else ""
        tupSeq = ",".join(str(n) for n in tup)
        if withPassage is True:
            sparts = T.sectionFromNode(passageNode, fillup=True)
            passageAtt = " ".join(
                f'sec{i}="{sparts[i] if i < len(sparts) else ""}"' for i in range(3)
            )
        else:
            passageAtt = ""

        plainRep = "".join(
            ""
            if i + 1 in skipCols
            else (
                '<span class="col">'
                + mdEsc(
                    app.plain(
                        n,
                        _inTuple=True,
                        withPassage=_doPassage(dContext, i),
                        highlights=highlights,
                        **newOptionsH,
                    ),
                    math=showMath,
                )
                + "</span>"
            )
            for (i, n) in enumerate(tup)
        )
        seqNo = -1 if seq is None else seq
        seqRep = (
            "" if seq is None else f'<a href="#" class="sq" tup="{tupSeq}">{seq}</a>'
        )
        html = (
            f'<details class="pretty dtrow {current}" seq="{seqNo}" {attOpen}>'
            f"<summary>"
            f'<a href="#" class="pq fa fa-solar-panel fa-xs"'
            f' title="show in context" {passageAtt}></a>'
            f"{seqRep}"
            f" {passageRef} {plainRep}"
            f"</summary>"
            f'<div class="pretty">{prettyRep}</div>'
            f"</details>"
        )
        return html

    html = [] if seq is None else [str(seq)]
    if withPassage is True:
        html.append(passageRef)
    for (i, n) in enumerate(tup):
        html.append(
            ""
            if i + 1 in skipCols
            else app.plain(
                n,
                _inTuple=True,
                _asString=True,
                withPassage=_doPassage(dContext, i),
                highlights=highlights,
                **newOptionsH,
            )
        )
    html = (
        f'<tr class="tf {ltr}"><td class="tf {ltr}">'
        + f'</td><td class="tf {ltr}">'.join(html)
        + "</td></tr>"
    )
    if _asString:
        return html

    passageHead = f'</th><th class="tf {ltr}">p' if withPassage is True else ""
    head = (
        (
            f'<tr class="tf {ltr}"><th class="tf {ltr}">n{passageHead}</th>'
            f'<th class="tf {ltr}">'
        )
        + f'</th><th class="tf {ltr}">'.join(fOtypev(n) for n in tup)
        + "</th></tr>"
    )
    html = "<table>" + head + "".join(html) + "</table>"

    dh(html, inNb=inNb)


def plain(app, n, _inTuple=False, _asString=False, explain=False, **options):
    """Display the plain text of a node.

    Displays the material that corresponds to a node in a compact way.
    Nodes with little content will be represented by their text content,
    nodes with large content will be represented by an identifying label.

    Parameters
    ----------
    n: integer
        Node
    options: dict
        Display options, see `tf.advanced.options`.
    _inTuple: boolean, optional False
        Whether the result is meant too end up in a table cell produced by
        `plainTuple`. In that case some extra node types count as big and will
        not be displayed in full.
    _asString: boolean, optional False
        Whether to deliver the result as a HTML string or to display it directly
        inside a notebook. When the TF browser uses this function it needs the
        HTML string.
    explain: boolean, optional False
        Whether to print a trace of which nodes have been visited and how these
        calls have contributed to the end result.

    Result
    ------
    string or `None`
        Depending on `_asString` above.
    """

    return render(app, False, n, _inTuple, _asString, explain, **options)


# PRETTY and FRIENDS


def show(app, tuples, _asString=False, **options):
    """Displays an iterable of tuples of nodes.

    The elements of the list are displayed by `A.prettyTuple()`.

    !!! hint "`condense`, `condenseType`"
        You can condense the list first to containers of `condenseType`,
        before displaying the list.
        Pass the display parameters `condense` and `condenseType`.
        See `tf.advanced.options`.

    Parameters
    ----------
    tuples: iterable of tuples of integer
        The integers are the nodes, together they form a table.
    _asString: boolean, optional False
        Whether to deliver the result as a HTML string or to display it directly
        inside a notebook. When the TF browser uses this function it needs the
        HTML string.
    options: dict
        Display options, see `tf.advanced.options`.

    Result
    ------
    string or `None`
        When used for the TF browser (`app._browse` is true),
        or when `_asString` is True, the result is returned
        as HTML. Otherwise the result is directly displayed in a notebook.
    """

    display = app.display

    if not display.check("show", options):
        return ""

    _browse = app._browse
    inNb = app.inNb
    asString = _browse or _asString

    dContext = display.distill(options)
    end = dContext.end
    start = dContext.start
    condensed = dContext.condensed
    condenseType = dContext.condenseType

    api = app.api
    F = api.F

    item = condenseType if condensed else RESULT

    if condensed:
        tuples = condense(api, tuples, condenseType, multiple=True)

    html = []

    for (i, tup) in tupleEnum(tuples, start, end, LIMIT_SHOW, item, inNb):
        item = F.otype.v(tup[0]) if condensed and condenseType else RESULT
        thisResult = prettyTuple(
            app,
            tup,
            seq=i,
            item=item,
            _asString=asString,
            **options,
        )
        if asString:
            html.append(thisResult)

    if asString:
        return "".join(html)


def prettyTuple(app, tup, seq=None, _asString=False, item=RESULT, **options):
    """Displays the material that corresponds to a tuple of nodes in a graphical way.

    The member nodes of the tuple will be collected into containers, which
    will be displayed with `pretty()`, and the nodes of the tuple
    will be highlighted in the containers.

    Parameters
    ----------
    tup: iterable of integer
        The members of the tuple can be arbitrary nodes.
    seq: integer, optional None
        an arbitrary number which will be displayed in the heading.
        This prepares the way for displaying query results, which come as
        a sequence of tuples of nodes.
        If None, no such number is displayed in the heading.
    item: string, optional result
        A name for the tuple: it could be a result, or a chapter, or a line.
    _asString: boolean, optional False
        Whether to deliver the result as a HTML string or to display it directly
        inside a notebook. When the TF browser uses this function it needs the
        HTML string.
    options: dict
        Display options, see `tf.advanced.options`.

    Result
    ------
    string or `None`
        When used for the TF browser (`app._browse` is true),
        or when `_asString` is True, the result is returned
        as HTML. Otherwise the result is directly displayed in a notebook.
    """

    display = app.display

    if not display.check("prettyTuple", options):
        return ""

    dContext = display.distill(options)
    colorMap = dContext.colorMap
    highlights = dContext.highlights
    condenseType = dContext.condenseType
    condensed = dContext.condensed

    _browse = app._browse
    inNb = app.inNb
    asString = _browse or _asString

    if len(tup) == 0:
        if asString:
            return ""
        else:
            return

    api = app.api
    N = api.N
    sortKey = N.sortKey

    containers = {tup[0]} if condensed else condenseSet(api, tup, condenseType)
    highlights = getTupleHighlights(api, tup, highlights, colorMap, condenseType)
    seqRep = "" if seq is None else f" <i>{seq}</i>"

    if not asString:
        dh(f"<p><b>{item}</b>{seqRep}", inNb=inNb)
    if asString:
        html = []
    for t in sorted(containers, key=sortKey):
        h = app.pretty(
            t,
            highlights=highlights,
            _asString=asString,
            **display.consume(options, "highlights"),
        )
        if asString:
            html.append(h)
    if asString:
        return "".join(html)


def pretty(app, n, explain=False, _asString=False, **options):
    """Displays the material that corresponds to a node in a graphical way.

    The internal structure of the nodes that are involved is also revealed.
    In addition, extra features and their values are displayed with the nodes.

    !!! hint "Controlling pretty displays"
        The following `tf.advanced.options`
        are particularly relevant to pretty displays:

        *   `condenseType`: the standard container to display nodes in;
        *   `full`: whether to display a reference to the material or the material itself;
        *   `queryFeatures`: whether to display features mentioned in the last query;
            these features are stored in the `tupleFeatures` option;
        *   `extraFeatures`: additional node / edge features to  display;
        *   `edgeFeatures`: which edge features maybe displayed;
        *   `edgeHighlights`: highlight specs for edges;
        *   `tupleFeatures`: additional features to  display (`export` and queryresults).

    Parameters
    ----------
    n: integer
        Node
    options: dict
        Display options, see `tf.advanced.options`.
    explain: boolean, optional False
        Whether to print a trace of which nodes have been visited and how these
        calls have contributed to the end result.
    asString: boolean, optional False
        If True, the result is returned as string

    Result
    ------
    string or `None`
        When used for the TF browser (`app._browse` is true),
        or when `_asString` is True, the result is returned
        as HTML.
        Otherwise the result is directly displayed in a notebook.
    """

    return render(app, True, n, False, _asString, explain, **options)


def _getRefMember(otypeRank, fOtypev, tup, dContext):
    minRank = None
    minN = None
    for n in tup:
        nType = fOtypev(n)
        rank = otypeRank[nType]
        if minRank is None or rank < minRank:
            minRank = rank
            minN = n
            if minRank == 0:
                break

    return (tup[0] if tup else None) if minN is None else minN


def _doPassage(dContext, i):
    withPassage = dContext.withPassage
    return withPassage is not True and withPassage and i + 1 in withPassage
