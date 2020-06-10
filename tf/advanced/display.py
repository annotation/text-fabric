"""
.. include:: ../../docs/advanced/display.md
"""


import os
import types

from ..parameters import DOWNLOADS, SERVER_DISPLAY, SERVER_DISPLAY_BASE
from ..core.helpers import mdEsc
from .helpers import getResultsX, tupleEnum, RESULT, dh, showDict
from .condense import condense, condenseSet
from .highlight import getTupleHighlights
from .options import Options
from .render import render
from .unravel import unravel, _getLtr

LIMIT_SHOW = 100
LIMIT_TABLE = 2000


def displayApi(app, silent):
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
    silent:
        The verbosity mode to perform this operation in.
        Normally it is the same as for the app, but when we do an `A.reuse()`
        we force `silent=True`.
    """

    app.export = types.MethodType(export, app)
    app.table = types.MethodType(table, app)
    app.plainTuple = types.MethodType(plainTuple, app)
    app.plain = types.MethodType(plain, app)
    app.show = types.MethodType(show, app)
    app.prettyTuple = types.MethodType(prettyTuple, app)
    app.pretty = types.MethodType(pretty, app)
    app.unravel = types.MethodType(unravel, app)
    app.loadCss = types.MethodType(loadCss, app)
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

    display = app.display
    display.setup()
    data = display.current
    showDict("<b>current display options</b>", data, *options)


def displaySetup(app, **options):
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
    show: keys
        Options of which the current value will be shown.
    options: key-values
        Explicit values for selected options that act as overrides of the defaults.

    See Also
    --------
    tf.advanced.settings: options allowed in `config.yaml`
    tf.advanced.options: all available display options
    """

    display = app.display

    display.setup(**options)


def displayReset(app, *options):
    """Restore display parameters to their defaults.

    Reset the given display parameters to their default value and let the others
    retain their current value.

    So you can reset the display parameters selectively.

    Parameters
    ----------
    options: list, optional `[]`
        If present, only restore these options to their defaults.
        Otherwise, restore all display settings.
    """

    display = app.display

    display.reset(*options)


def loadCss(app):
    """The CSS is looked up and then loaded into a notebook if we are not
    running in the TF browser,
    else the CSS is returned.
    """

    _browse = app._browse
    aContext = app.context
    css = aContext.css

    if _browse:
        return css

    cssPath = (
        f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}"
        f"{SERVER_DISPLAY_BASE}"
    )
    genericCss = ""
    for cssFile in SERVER_DISPLAY:
        with open(f"{cssPath}/{cssFile}", encoding="utf8") as fh:
            genericCss += fh.read()

    tableCss = (
        "tr.tf.ltr, td.tf.ltr, th.tf.ltr { text-align: left ! important;}\n"
        "tr.tf.rtl, td.tf.rtl, th.tf.rtl { text-align: right ! important;}\n"
    )
    dh(f"<style>" + tableCss + genericCss + css + "</style>")


def export(app, tuples, toDir=None, toFile="results.tsv", **options):
    """Exports an iterable of tuples of nodes to an Excel friendly `.tsv` file.

    !!! hint "Examples"
        See for detailed examples the
        [exportExcel](https://nbviewer.jupyter.org/github/annotation/tutorials/blob/master/bhsa/exportExcel.ipynb)
        and
        [exportExcel](https://nbviewer.jupyter.org/github/annotation/tutorials/blob/master/oldbabylonian/exportExcel.ipynb)
        notebooks.

    Parameters
    ----------
    tuples: iterable of tuples of integer
        The integers are the nodes, together they form a table.
    toDir: string, optional `None`
        The destination directory for the exported file.
        By default it is your Downloads folder.

        If the directory does not exist, it will be created.
    toFile: boolean, optional `results.tsv`
        The name of the exported file.
    options: dict
        Display options, see `tf.advanced.options`.

        !!! note "details"
            * `condensed`
              Has no effect. Exports to Excel will not be condensed, because the
              number of columns is variable per row in that case.
              Excel itself has nice possibilities for grouping rows.
              You can also filter your tuples by means of hand-coding
              before exporting them.
            * `condenseType`
              The condense type influences for which nodes
              the full text will be exported.
              Only nodes that are "smaller" than the condense type will have
              their full text exported.
            * `fmt`
              This display parameter specifies the text format for any nodes
              that trigger a text value to be exported.
            * `tupleFeatures`
              This is a display parameter that steers which features are exported
              with each member of the tuples in the list.

              If the iterable of tuples are the results of a query you have just
              run, then an appropriate call to `displaySetup(tupleFeatures=...)`
              has already been issued, so you can just say:

                 results = A.search(query)`
                 A.export(results)`

    Results
    -------
    A file *toFile* in directory *toDir* with the following content:

    There will be a row for each tuple.
    The columns are:

    * **R** the sequence number of the result tuple in the result list
    * **S1 S2 S3** the section as book, chapter, verse, in separate columns;
      the section is the section of the first non book/chapter node in the tuple
    * **NODEi TYPEi** the node and its type,
      for each node **i** in the result tuple
    * **TEXTi** the full text of node **i**,
      if the node type admits a concise text representation;
      the criterion is whether the node type has a type not bigger than the
      default condense type, which is app specific.
      If you pass an explicit `condenseType=`*xxx* as display parameter,
      then this is the reference condenseType on which the decision is based.
    * **XFi** the value of extra feature **XF** for node **i**,
      where these features have been declared by a previous
      displaySetup(tupleFeatures=...)`

    !!! caution "Encoding"
        The exported file is written in the `utf_16_le` encoding.
        This ensures that Excel can open it without hassle, even if there
        are non-latin characters inside.

        When you want to read the exported file programmatically,
        open it with `encoding=utf_16`.
    """

    display = app.display

    if not display.check("table", options):
        return ""

    dContext = display.distill(options)
    fmt = dContext.fmt
    condenseType = dContext.condenseType
    tupleFeatures = dContext.tupleFeatures

    if toDir is None:
        toDir = os.path.expanduser(DOWNLOADS)
        if not os.path.exists(toDir):
            os.makedirs(toDir, exist_ok=True)
    toPath = f"{toDir}/{toFile}"

    resultsX = getResultsX(app, tuples, tupleFeatures, condenseType, fmt=fmt,)

    with open(toPath, "w", encoding="utf_16_le") as fh:
        fh.write(
            "\ufeff"
            + "".join(
                ("\t".join("" if t is None else str(t) for t in tup) + "\n")
                for tup in resultsX
            )
        )


# PLAIN and FRIENDS


def table(app, tuples, _asString=False, **options):
    """Plain displays of an iterable of tuples of nodes in a table.

    The list is displayed as a compact markdown table.
    Every row is prepended with the sequence number in the iterable,
    and then displayed by `plainTuple`

    !!! hint "condense, condenseType"
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
    _asString: boolean, optional `False`
        Whether to deliver the result as a HTML string or to display it directly
        inside a notebook. When the TF-browser uses this function it needs the
        HTML string.
    """

    display = app.display

    if not display.check("table", options):
        return ""

    api = app.api
    F = api.F
    fOtypev = F.otype.v

    dContext = display.distill(options)
    end = dContext.end
    start = dContext.start
    withPassage = dContext.withPassage
    condensed = dContext.condensed
    condenseType = dContext.condenseType
    skipCols = dContext.skipCols

    ltr = _getLtr(app, dContext) or "ltr"

    if skipCols:
        tuples = tuple(
            tuple(x for (i, x) in enumerate(tup) if i + 1 not in skipCols)
            for tup in tuples
        )

    item = condenseType if condensed else RESULT

    if condensed:
        tuples = condense(api, tuples, condenseType, multiple=True)

    passageHead = f'</th><th class="tf {ltr}">p' if withPassage is True else ""

    html = []
    one = True

    newOptions = display.consume(options, "skipCols")

    for (i, tup) in tupleEnum(tuples, start, end, LIMIT_TABLE, item):
        if one:
            heads = '</th><th class="tf">'.join(fOtypev(n) for n in tup)
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
                i,
                item=item,
                position=None,
                opened=False,
                _asString=True,
                skipCols=set(),
                **newOptions,
            )
        )
    html = "<table>" + "\n".join(html) + "</table>"
    if _asString:
        return html
    dh(html)


def plainTuple(
    app, tup, seq, item=RESULT, position=None, opened=False, _asString=False, **options
):
    """Display the plain text of a tuple of nodes.

    Displays the material that corresponds to a tuple of nodes
    as a row of cells,
    each displaying a member of the tuple by means of `plain`.

    Parameters
    ----------
    tup: iterable of integer
        The members of the tuple can be arbitrary nodes.
    seq: integer
        an arbitrary number which will be displayed in the first cell.
        This prepares the way for displaying query results, which come as
        a sequence of tuples of nodes.
    item: string, optional `result`
        A name for the tuple: it could be a result, or a chapter, or a line.
    position: integer, optional `None`
        Which position counts as the focus position.
        If *seq* equals *position*, the tuple is in focus.
        The effect is to add the CSS class *focus* to the output HTML
        for the row of this tuple.
    opened:  booolean, optional `False`
        Whether this tuple should be expandable to a `pretty` display.
        The normal output of this row will be wrapped in a

           <details><summary>plain</summary>pretty</details>`

        pattern, so that the user can click a triangle to switch between plain
        and pretty display.

        !!! caution
            This option has only effect when used in the TF browser.
    options: dict
        Display options, see `tf.advanced.options`.
    _asString: boolean, optional `False`
        Whether to deliver the result as a HTML string or to display it directly
        inside a notebook. When the TF-browser uses this function it needs the
        HTML string.

    Result
    ------
    html string or `None`
        Depending on *asString* above.
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

    dContext = display.distill(options)
    condenseType = dContext.condenseType
    colorMap = dContext.colorMap
    highlights = dContext.highlights
    withPassage = dContext.withPassage
    skipCols = dContext.skipCols

    ltr = _getLtr(app, dContext) or "ltr"

    if skipCols:
        tup = tuple(x for (i, x) in enumerate(tup) if i + 1 not in skipCols)

    if withPassage is True:
        passageNode = _getRefMember(otypeRank, fOtypev, tup, dContext)
        passageRef = (
            ""
            if passageNode is None
            else app._sectionLink(passageNode)
            if _browse
            else app.webLink(passageNode, _asString=True)
        )
        passageRef = f'<span class="section ltr">{passageRef}</span>'
    else:
        passageRef = ""

    newOptions = display.consume(options, "withPassage")
    newOptionsH = display.consume(options, "withPassage", "highlights")

    highlights = getTupleHighlights(api, tup, highlights, colorMap, condenseType)

    if _browse:
        prettyRep = (
            prettyTuple(app, tup, seq, withPassage=False, **newOptions)
            if opened
            else ""
        )
        current = "focus" if seq == position else ""
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
            "<span>"
            + mdEsc(
                app.plain(
                    n,
                    _inTuple=True,
                    withPassage=_doPassage(dContext, i),
                    highlights=highlights,
                    **newOptionsH,
                )
            )
            + "</span>"
            for (i, n) in enumerate(tup)
        )
        html = (
            f'<details class="pretty dtrow {current}" seq="{seq}" {attOpen}>'
            f"<summary>"
            f'<a href="#" class="pq fa fa-solar-panel fa-xs"'
            f' title="show in context" {passageAtt}></a>'
            f'<a href="#" class="sq" tup="{tupSeq}">{seq}</a>'
            f" {passageRef} {plainRep}"
            f"</summary>"
            f'<div class="pretty">{prettyRep}</div>'
            f"</details>"
        )
        return html

    html = [str(seq)]
    if withPassage is True:
        html.append(passageRef)
    for (i, n) in enumerate(tup):
        html.append(
            app.plain(
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
        + f"</th></tr>"
    )
    html = f"<table>" + head + "".join(html) + "</table>"

    dh(html)


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
    _inTuple: boolean, optional `False`
        Whether the result is meant too end up in a table cell produced by
        `plainTuple`. In that case some extra node types count as big and will
        not be displayed in full.
    _asString: boolean, optional `False`
        Whether to deliver the result as a HTML string or to display it directly
        inside a notebook. When the TF-browser uses this function it needs the
        HTML string.
    explain: boolean, optional `False`
        Whether to print a trace of which nodes have been visited and how these
        calls have contributed to the end result.

    Result
    ------
    html string or `None`
        Depending on *asString* above.
    """

    return render(app, False, n, _inTuple, _asString, explain, **options)


# PRETTY and FRIENDS


def show(app, tuples, **options):
    """Displays an iterable of tuples of nodes.

    The elements of the list are displayed by `A.prettyTuple()`.

    !!! hint "condense, condenseType"
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

    Result
    ------
    html string or `None`
        When used for the TF browser (`app._browse` is true), the result is returned
        as HTML. Otherwise the result is directly displayed in a notebook.
    """

    display = app.display

    if not display.check("show", options):
        return ""

    dContext = display.distill(options)
    end = dContext.end
    start = dContext.start
    condensed = dContext.condensed
    condenseType = dContext.condenseType
    skipCols = dContext.skipCols

    if skipCols:
        tuples = tuple(
            tuple(x for (i, x) in enumerate(tup) if i + 1 not in skipCols)
            for tup in tuples
        )

    api = app.api
    F = api.F

    item = condenseType if condensed else RESULT

    if condensed:
        tuples = condense(api, tuples, condenseType, multiple=True)

    newOptions = display.consume(options, "skipCols")

    for (i, tup) in tupleEnum(tuples, start, end, LIMIT_SHOW, item):
        item = F.otype.v(tup[0]) if condensed and condenseType else RESULT
        prettyTuple(app, tup, i, item=item, skipCols=set(), **newOptions)


def prettyTuple(app, tup, seq, item=RESULT, **options):
    """Displays the material that corresponds to a tuple of nodes in a graphical way.

    The member nodes of the tuple will be collected into containers, which
    will be displayed with `pretty()`, and the nodes of the tuple
    will be highlighted in the containers.

    Parameters
    ----------
    tup: iterable of integer
        The members of the tuple can be arbitrary nodes.
    seq: integer
        an arbitrary number which will be displayed in the heading.
        This prepares the way for displaying query results, which come as
        a sequence of tuples of nodes.
    item: string, optional `result`
        A name for the tuple: it could be a result, or a chapter, or a line.
    options: dict
        Display options, see `tf.advanced.options`.

    Result
    ------
    html string or `None`
        When used for the TF browser (`app._browse` is true), the result is returned
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
    skipCols = dContext.skipCols

    _browse = app._browse

    if skipCols:
        tup = tuple(x for (i, x) in enumerate(tup) if i + 1 not in skipCols)

    if len(tup) == 0:
        if _browse:
            return ""
        else:
            return

    api = app.api
    N = api.N
    sortKey = N.sortKey

    containers = {tup[0]} if condensed else condenseSet(api, tup, condenseType)
    highlights = getTupleHighlights(api, tup, highlights, colorMap, condenseType)

    if not _browse:
        dh(f"<p><b>{item}</b> <i>{seq}</i></p>")
    if _browse:
        html = []
    for t in sorted(containers, key=sortKey):
        h = app.pretty(
            t, highlights=highlights, **display.consume(options, "highlights"),
        )
        if _browse:
            html.append(h)
    if _browse:
        return "".join(html)


def pretty(app, n, explain=False, **options):
    """Displays the material that corresponds to a node in a graphical way.

    The internal structure of the nodes that are involved is also revealed.
    In addition, extra features and their values are displayed with the nodes.

    !!! hint "Controlling pretty displays"
        The following `tf.advanced.options`
        are particularly relevant to pretty displays:

        * `condenseType`: the standard container to display nodes in;
        * `full`: whether to display a reference to the material or the material itself;
        * `extraFeatures`: additional features to  display
        * `tupleFeatures`: additional features to  display (primarily for `export`.

    Parameters
    ----------
    n: integer
        Node
    options: dict
        Display options, see `tf.advanced.options`.
    explain: boolean, optional `False`
        Whether to print a trace of which nodes have been visited and how these
        calls have contributed to the end result.

    Result
    ------
    html string or `None`
        When used for the TF browser (`app._browse` is true), the result is returned
        as HTML. Otherwise the result is directly displayed in a notebook.
    """

    return render(app, True, n, False, False, explain, **options)


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
