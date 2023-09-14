"""Wraps various pieces into HTML.
"""

from .settings import FEATURES, KEYWORD_FEATURES, getText
from .html import H


def wrapMessages(messages):
    """HTML for messages."""
    return H.p((H.span(text, cls=lev) + H.br() for (lev, text) in messages))


def wrapAnnoSets(annoDir, chosenAnnoSet, annoSets):
    """HTML for the annoset chooser.

    It is a list of buttons, each corresponding to an existing annoset.
    A click on the button selects that annoset.
    There is also a control to delete the annoset.

    Apart from these buttons there is a button to switch to the entities that are
    present in the TF dataset as nodes of type "ent" with corresponding features.

    Finally, it is possible to create a new, empty annoset.

    Parameters
    ----------
    chosenAnnoSet: string
        The name of the chosen annoset.
        If empty, it refers to the entities already present in the dataset as TF nodes
        and features.
    annoSets: list
        The list of existing annosets.
    """
    content1 = [
        H.input(
            type="hidden",
            name="annoset",
            value=chosenAnnoSet,
            id="annoseth",
        ),
        H.input(
            type="hidden",
            name="duannoset",
            value="",
            id="duannoseth",
        ),
        H.input(
            type="hidden",
            name="rannoset",
            value="",
            id="rannoseth",
        ),
        H.button(
            "+",
            type="submit",
            cls="medium active",
            id="anew",
            title="create a new annotation set",
        ),
        H.button(
            "++",
            type="submit",
            cls="medium active",
            id="adup",
            title="duplicate this annotation set",
        ),
        H.select(
            (
                H.option(
                    "generated entities" if annoSet == "" else annoSet,
                    value=annoSet,
                    selected=annoSet == chosenAnnoSet,
                )
                for annoSet in [""] + sorted(annoSets)
            ),
            cls="selinp",
            id="achange",
        ),
    ]

    content2 = (
        [
            H.input(
                type="hidden",
                name="dannoset",
                value="",
                id="dannoseth",
            ),
            H.button(
                "→",
                type="submit",
                cls="medium active",
                id="arename",
                title="rename current annotation set",
            ),
            H.button(
                "-",
                type="submit",
                cls="medium active",
                id="adelete",
                title="delete current annotation set",
            ),
        ]
        if chosenAnnoSet
        else []
    )

    return H.p(content1, content2)


def wrapEntityOverview(web, templateData):
    """HTML for the feature values of entities.

    Parameters
    ----------
    setData: dict
        The entity data for the chosen set.

    Returns
    -------
    HTML string
    """

    setData = web.toolData.ner.sets[web.annoSet]

    templateData.entityoverview = H.p(
        H.span(
            H.code(f"{len(es):>5}"),
            " x ",
            H.button(repIdent(fVals), type="submit", value="v"),
        )
        + H.br()
        for (fVals, es) in setData.entityBy
    )


def wrapEntityHeaders(templateData):
    """HTML for the header of the entity table.

    Dependent on the state of sorting.

    Parameters
    ----------
    sortKey: string
        Indicator of how the table is sorted.
    sortDir:
        Indicator of the direction of the sorting.

    Returns
    -------
    HTML string

    """
    sortKey = templateData.sortkey
    sortDir = templateData.sortdir
    sortKeys = ((feat, f"sort_{i}") for (i, feat) in enumerate(FEATURES))

    content = []

    for (label, key) in (("frequency", "freqsort"), *sortKeys):
        theDir = sortDir if key == sortKey else "u"
        theArrow = "↑" if theDir == "u" else "↓"
        content.append(
            H.span(label, H.button(theArrow, type="submit", name=key, value=theDir))
        )

    templateData.entityheaders = H.p(content)


def wrapQ(web, templateData, nFind, nEnt, nVisible):
    """HTML for the query line.

    Parameters
    ----------
    web: object
        The web app object

    Returns
    -------
    html string
        The finished HTML of the query parameters
    """

    hasFind = wrapFilter(web, templateData, nFind)
    txt = wrapEntityInit(web, templateData)
    wrapEntityText(templateData, txt)
    wrapEntityFeats(web, templateData, nEnt, nVisible, hasFind, txt)
    wrapEntityFeats(web, templateData, hasFind, txt)


def wrapFilter(web, templateData, nFind):
    annoSet = web.annoSet
    setData = web.toolData.ner.sets[annoSet]

    sFind = templateData.sfind
    sFindRe = templateData.sfindre
    sFindError = templateData.sfinderror

    hasFind = sFindRe is not None

    nSent = len(setData.sentences)

    templateData["find"] = H.p(
        H.b("Filter:"),
        H.input(type="text", name="sfind", id="sfind", value=sFind),
        wrapFindStat(nSent, nFind, hasFind),
        H.button("✖️", type="submit", id="findclear"),
        H.span(sFindError, id="sfinderror", cls="error"),
        H.button("🔎", type="submit", id="lookupf"),
    )
    return hasFind


def wrapEntityInit(web, templateData):
    kernelApi = web.kernelApi
    app = kernelApi.app
    api = app.api
    F = api.F

    tokenStart = templateData.tokenstart
    tokenEnd = templateData.tokenend
    hasEntity = tokenStart and tokenEnd

    startRep = H.input(
        type="hidden", name="tokenstart", id="tokenstart", value=tokenStart or ""
    )
    endRep = H.input(
        type="hidden", name="tokenend", id="tokenend", value=tokenEnd or ""
    )
    templateData.entityinit = startRep + endRep

    return getText(F, range(tokenStart, tokenEnd + 1)) if hasEntity else ""


def wrapEntityText(templateData, txt):
    templateData.entitytext = H.join(
        H.b("Entity:"),
        H.span(txt, id="qwordshow"),
        H.button("✖️", type="submit", id="queryclear"),
        H.button("🔎", type="submit", id="lookupq"),
    )


def wrapEntityFeats(web, templateData, nEnt, nVisible, hasFind, txt):
    if txt == "":
        templateData.entityfeats = ""
        return

    annoSet = web.annoSet
    setData = web.toolData.ner.sets[annoSet]

    valSelect = templateData.valselect

    features = setData.entityTextVal[txt]

    html = []

    for feat in FEATURES:
        theseVals = features.get(feat, set())
        thisValSelect = valSelect[feat]

        html.append(
            H.input(
                type="hidden",
                name=f"{feat}_select",
                id=f"{feat}_select",
                value=",".join(thisValSelect),
            )
        )
        for val in ["⌀"] + sorted(theseVals):
            html.append(
                H.button(
                    val,
                    wrapEntityStat(val, nVisible[feat], nEnt[feat], hasFind),
                    type="button",
                    name=val,
                    cls=f"{feat}_sel",
                    st="v" if val in thisValSelect else "x",
                    title=f"{feat} not marked"
                    if val == "⌀"
                    else f"{feat} marked as {val}",
                )
            )

    templateData.entityfeats = H.join(html, sep=" ")


def wrapEntityModify(web, templateData, hasFind, txt):
    annoSet = web.annoSet
    setData = web.toolData.ner.sets[annoSet]
    scope = templateData.scope

    scope = templateData.scope

    hasEntity = txt != ""

    html1 = H.input(type="hidden", id="scope", name="scope", value=scope)

    html2 = ""
    html3 = ""

    if annoSet and hasEntity:
        # Scope of modification

        content = [H.b("Target:")]

        if hasFind:
            content.extend(
                [
                    H.button(
                        "filtered",
                        type="button",
                        id="scopefiltered",
                        title="act on filtered sentences only",
                    ),
                    H.button(
                        "all",
                        type="button",
                        id="scopeall",
                        title="act on all sentences",
                    ),
                ]
            )
        content.extend(
            [
                H.button(
                    "🆗",
                    type="button",
                    id="selectall",
                    title="select all occurences in filtered sentences",
                ),
                H.button(
                    "⭕️",
                    type="button",
                    id="selectnone",
                    title="deselect all occurences in filtered sentences",
                ),
            ]
        )
        html2 = H.p(content)

        # Assigment of feature values

        content = [H.b("Assignment:")]

        for feat in FEATURES:
            theseVals = sorted(setData.entityTextVal[feat].get(txt, set()))
            allVals = (
                sorted(x[0] for x in setData.entityFreq[feat])
                if feat in KEYWORD_FEATURES
                else theseVals
            )
            for val in allVals:
                occurs = val in theseVals
                occurCls = " occurs " if occurs else ""

                subContent = []

                if occurs:
                    subContent.append(
                        H.button(
                            "-",
                            type="submit",
                            name=f"{feat}_xbutton",
                            value=val,
                            cls="min",
                        )
                    )
                subContent.append(H.span(val, cls=f"{feat}_sel {occurCls}"))
                subContent.append(
                    H.button(
                        "+",
                        type="submit",
                        name=f"{feat}_pbutton",
                        value=val,
                        cls="plus",
                    )
                )

                content.append(H.span(subContent, cls=f"{feat}_w"))

            content.extend(
                [
                    H.input(type="text", id=f"{feat}_v", name=f"{feat}_v", value=""),
                    H.button(
                        "+",
                        type="submit",
                        id=f"{feat}_save",
                        name=f"{feat}_save",
                        value="v",
                        cls="plus",
                    ),
                ]
            )

        html3 = H.p(content)

    templateData.entitymodify = html1 + html2 + html3


def wrapFindStat(nSent, nFind, hasFind):
    n = f"{nFind} of {nSent}" if hasFind else nSent
    return H.span(n, cls="stat")


def wrapEntityStat(val, thisNVisible, thisNEnt, hasPattern, hasQuery):
    na = thisNEnt[val]
    n = f"{thisNVisible[val]} of {na}" if hasPattern else f"{na}"
    return H.span(n, cls="stat")


def wrapActive(templateData):
    activeVal = templateData.activeval

    templateData.activevalrep = H.join(
        H.input(
            type="hidden", id=f"{feat}_active", name=f"{feat}_active", value=val or ""
        )
        for (feat, val) in activeVal
    )


def wrapReport(templateData, report):
    templateData.report = H.join(H.p(H.span(line, cls="report")) for line in report)


def repIdent(vals):
    return H.join(
        (H.span(val, cls=feat) for (feat, val) in zip(FEATURES, vals)), sep=" "
    )
