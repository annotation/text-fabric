from ..core.text import DEFAULT_FORMAT
from .helpers import getHeaders, RESULT
from .display import plain, plainTuple, pretty, prettyTuple


def compose(
    app,
    tuples,
    features,
    position,
    opened,
    getx=None,
    **options,
):
    """Takes a list of tuples and composes it into an HTML table.

    Some of the rows will be expandable, namely the rows specified by `opened`,
    for which extra data has been fetched.

    Parameters
    ----------
    features: list
        The names of features that will be shown in expanded pretty displays.
        Typically, it is the list of features used in the query that delivered
        the tuples.

    position: integer
        The current position in the list. Will be highlighted in the display.

    getx: integer, optional None
        If `None`, a portion of the tuples will be put in a table. otherwise,
        it is an index in the list for which a pretty display will be retrieved.
        Typically, this happens when a TF browser user clicks on a table row
        in order to expand it.
    """

    display = app.display
    dContext = display.distill(options)
    condensed = dContext.condensed
    condenseType = dContext.condenseType

    api = app.api

    item = condenseType if condensed else RESULT

    if features:
        api.ensureLoaded(features)
        features = features.split()
    else:
        features = []

    if getx is not None:
        tup = None
        for i, tp in tuples:
            if i == getx:
                tup = tp
                break
        return (
            prettyTuple(
                app,
                tup,
                seq=getx,
                tupleFeatures=features,
                **display.consume(options, "tupleFeatures"),
            )
            if tup is not None
            else ""
        )

    tuplesHtml = []
    doHeader = False
    for i, tup in tuples:
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
            tuplesHtml.append(getHeaders(app, tuples))

        tuplesHtml.append(
            plainTuple(
                app,
                tup,
                seq=i,
                item=item,
                position=position,
                opened=i in opened,
                _asString=True,
                tupleFeatures=features,
                **display.consume(options, "tupleFeatures"),
            )
        )

    return "\n".join(tuplesHtml)


# tuples and sections


def composeT(
    app,
    features,
    tuples,
    opened,
    getx=None,
    **options,
):
    """Takes a list of tuples and composes it into an HTML table.

    Very much like `compose`,
    but here the tuples come from a sections and / or tuples specification
    in the TF browser.
    """

    display = app.display

    api = app.api

    if features:
        api.ensureLoaded(features)
        features = features.split()
    else:
        features = []

    if getx is not None:
        tup = None
        for i, tp in tuples:
            if i == getx:
                tup = tp
                break
        return (
            prettyTuple(
                app,
                tup,
                seq=getx,
                condensed=False,
                extraFeatures=(features, {}),
                **display.consume(options, "condensed", "extraFeatures"),
            )
            if tup is not None
            else ""
        )

    tuplesHtml = []
    doHeader = False
    for i, tup in tuples:
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
            tuplesHtml.append(getHeaders(app, tuples))

        tuplesHtml.append(
            plainTuple(
                app,
                tup,
                seq=i,
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

    Like `composeT`, but this is meant to compose the items at section level 2
    (verses) within an item of section level 1 (chapter) within an item of
    section level 0 (a book).

    Typically invoked when a user of the TF browser is browsing passages.
    The query is used to highlight its results in the passages that the user is
    browsing.

    Parameters
    ----------
    items: integer or list of integer
        A node or list of nodes.
        Some corpora require a passage to be shown as a pretty display of the
        section node in question, and then items is a single node.
        Normally, the items is the list of section nodes one level lower than the
        section node in question. See `browseContentPretty` in `tf.advanced.settings`.
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
        return pretty(app, items, **options)

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
                seq=getx,
                condensed=False,
                condenseType=finalSecType,
                tupleFeatures=features,
                **display.consume(
                    options, "condensed", "condenseType", "tupleFeatures"
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
                tupleFeatures=features,
                **display.consume(options, "tupleFeatures"),
            )
        )

    return "\n".join(passageHtml)


def _plainTextSFinal(
    app,
    browseNavLevel,
    finalSecType,
    sNode,
    opened,
    secFinal,
    **options,
):
    """
    Produces a single item corresponding to a section 2 level (verse) for display
    in the browser.

    It will rendered as plain text, but expandable to a pretty display.
    """

    display = app.display
    dContext = display.distill(options)
    fmt = dContext.fmt

    api = app.api
    T = api.T

    aContext = app.context
    formatCls = aContext.formatCls

    secStr = str(T.sectionFromNode(sNode)[browseNavLevel])
    isOpened = secStr in opened
    tCls = (
        ""
        if fmt is None
        else formatCls.get(fmt or DEFAULT_FORMAT, formatCls[DEFAULT_FORMAT]).lower()
    )

    prettyRep = (
        prettyTuple(
            app,
            (sNode,),
            seq=secStr,
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
        app,
        sNode,
        withPassage=False,
        **display.consume(options, "withPassage"),
    )
    html = f"""\
<details
  class="pretty{current}"
  seq="{secStr}"
  {attOpen}
>
  <summary class="{tCls} ubd">{app._sectionLink(sNode, text=secStr)} {textRep}</summary>
  <div class="pretty">{prettyRep}</div>
</details>\
"""
    return html
