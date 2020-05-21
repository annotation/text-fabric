from ..core.text import DEFAULT_FORMAT
from .helpers import RESULT
from .display import plain, plainTuple, pretty, prettyTuple


def compose(
    app, tuples, features, position, opened, getx=None, **options,
):
    """Takes a list of tuples and composes it into an HTML table.

    Some of the rows will be expandable, namely the rows specified by `opened`,
    for which extra data has been fetched.

    *features* is a list of names of features that will be shown
    in expanded pretty displays.
    Typically, it is the list of features used in the query that delivered the tuples.

    *position* The current position in the list. Will be highlighted in the display.

    *getx=None* If `None`, a portion of the tuples will be put in a table. otherwise,
    it is an index in the list for which a pretty display will be retrieved.
    Typically, this happens when a TF-browser user clicks on a table row
    in order to expand
    it.
    """

    display = app.display
    dContext = display.get(options)
    condensed = dContext.condensed
    condenseType = dContext.condenseType

    api = app.api
    F = api.F
    fOtype = F.otype.v

    item = condenseType if condensed else RESULT

    if features:
        api.ensureLoaded(features)
        features = features.split()
    else:
        features = []

    if getx is not None:
        tup = None
        for (i, tp) in tuples:
            if i == getx:
                tup = tp
                break
        return (
            prettyTuple(
                app,
                tup,
                getx,
                extraFeatures=(features, {}),
                **display.consume(options, "extraFeatures"),
            )
            if tup is not None
            else ""
        )

    tuplesHtml = []
    doHeader = False
    for (i, tup) in tuples:
        if i is None:
            if tup == "results":
                doHeader = True
            else:
                tuplesHtml.append(
                    f'<div class="dtheadrow"><span>n</span><span>{tup}</span></div>'
                )
            continue

        if doHeader:
            doHeader = False
            tuplesHtml.append(
                f"""\
<div class="dtheadrow">
  <span>n</span><span>{"</span><span>".join(fOtype(n) for n in tup)}</span>
</div>\
"""
            )
        tuplesHtml.append(
            plainTuple(
                app,
                tup,
                i,
                item=item,
                position=position,
                opened=i in opened,
                _asString=True,
                extraFeatures=(features, {}),
                **display.consume(options, "extraFeatures"),
            )
        )

    return "\n".join(tuplesHtml)


# tuples and sections


def composeT(
    app, features, tuples, opened, getx=None, **options,
):
    """Takes a list of tuples and composes it into an HTML table.

    Very much like `compose`,
    but here the tuples come from a sections and/or tuples specification
    in the TF-browser.
    """

    display = app.display

    api = app.api
    F = api.F
    fOtype = F.otype.v

    if features:
        api.ensureLoaded(features)
        features = features.split()
    else:
        features = []

    if getx is not None:
        tup = None
        for (i, tp) in tuples:
            if i == getx:
                tup = tp
                break
        return (
            prettyTuple(
                app,
                tup,
                getx,
                condensed=False,
                extraFeatures=(features, {}),
                **display.consume(options, "condensed", "extraFeatures"),
            )
            if tup is not None
            else ""
        )

    tuplesHtml = []
    doHeader = False
    for (i, tup) in tuples:
        if i is None:
            if tup == "results":
                doHeader = True
            else:
                tuplesHtml.append(
                    f'<div class="dtheadrow"><span>n</span><span>{tup}</span></div>'
                )
            continue

        if doHeader:
            doHeader = False
            tuplesHtml.append(
                f'<div class="dtheadrow"><span>n</span><span>'
                + "</span><span>".join(fOtype(n) for n in tup)
                + "</span></div>"
            )
        tuplesHtml.append(
            plainTuple(
                app,
                tup,
                i,
                condensed=False,
                extraFeatures=(features, {}),
                opened=i in opened,
                _asString=True,
                **display.consume(options, "condensed", "extraFeatures"),
            )
        )

    return "\n".join(tuplesHtml)


# passages


def composeP(
    app,
    browseNavLevel,
    finalSecType,
    features,
    items,
    opened,
    secFinal,
    getx=None,
    **options,
):
    """Takes a list of tuples and composes it into an HTML table.

    Like `composeT`, but this is meant to compose the items at section level 2 (verses) within
    an item of section level 1 (chapter) within an item of section level 0 (a book).

    Typically invoked when a user of the TF-browser is browsing passages.
    The query is used to highlight its results in the passages that the user is browsing.
    """

    display = app.display

    api = app.api
    T = api.T

    if features:
        api.ensureLoaded(features)
        features = features.split()
    else:
        features = []

    if not items:
        return ""

    if type(items) is int:
        return pretty(app, items)

    if getx is not None:
        tup = None
        for sFinal in items:
            i = T.sectionFromNode(sFinal)[browseNavLevel]
            if i == getx:
                tup = (sFinal,)
                break
        return (
            prettyTuple(
                app,
                tup,
                getx,
                condensed=False,
                condenseType=finalSecType,
                extraFeatures=(features, {}),
                **display.consume(
                    options, "condensed", "condenseType", "extraFeatures"
                ),
            )
            if tup is not None
            else ""
        )

    passageHtml = []

    for item in items:
        passageHtml.append(
            _plainTextSFinal(
                app,
                browseNavLevel,
                finalSecType,
                item,
                opened,
                secFinal,
                extraFeatures=(features, {}),
                **display.consume(options, "extraFeatures"),
            )
        )

    return "\n".join(passageHtml)


def _plainTextSFinal(
    app, browseNavLevel, finalSecType, sNode, opened, secFinal, **options,
):
    """
    Produces a single item corresponding to a section 2 level (verse) for display
    in the browser.

    It will rendered as plain text, but expandable to a pretty display.
    """

    display = app.display
    dContext = display.get(options)
    fmt = dContext.fmt

    api = app.api
    T = api.T

    aContext = app.context
    formatCls = aContext.formatCls

    secStr = str(T.sectionFromNode(sNode)[browseNavLevel])
    isOpened = secStr in opened
    tCls = "" if fmt is None else formatCls[fmt or DEFAULT_FORMAT].lower()

    prettyRep = (
        prettyTuple(
            app,
            (sNode,),
            secStr,
            condensed=False,
            condenseType=finalSecType,
            **display.consume(options, "condensed", "condenseType"),
        )
        if isOpened
        else ""
    )
    current = " focus" if secStr == str(secFinal) else ""
    attOpen = " open " if isOpened else ""

    textRep = plain(
        app, sNode, withPassage=False, **display.consume(options, "withPassage"),
    )
    html = f"""\
<details
  class="pretty{current}"
  seq="{secStr}"
  {attOpen}
>
  <summary class="{tCls}">{app._sectionLink(sNode, text=secStr)} {textRep}</summary>
  <div class="pretty">{prettyRep}</div>
</details>\
"""
    return html
