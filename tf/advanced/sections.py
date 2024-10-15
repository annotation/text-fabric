"""Section

There is support for section headings.

TF datasets may specify two kinds of sections in their
`otext.tf` configuration feature:

### Sections

At most three levels:

*   level 1 is for big things, like books
*   level 2 is for intermediate things, like chapters, that fit on one page or just
    a few pages
*   level 3 is for small things, such as lines.

TF uses these levels in the TF browser, to divide your corpus
into divisions that can conveniently be displayed to you in the browser.

### Structure

Any number of levels.
You can use them to divide your corpus into units that follow the logic of your corpus,
without regard for how they are to be displayed.
"""

import types


def sectionsApi(app):
    app.nodeFromSectionStr = types.MethodType(nodeFromSectionStr, app)
    app.sectionStrFromNode = types.MethodType(sectionStrFromNode, app)
    app.structureStrFromNode = types.MethodType(structureStrFromNode, app)
    app._sectionLink = types.MethodType(_sectionLink, app)


def nodeFromSectionStr(app, sectionStr, lang="en"):
    """Find the node of a section string.

    Compare `tf.core.text.Text.nodeFromSection`.

    Parameters
    ----------
    sectionStr: string
        Must be a valid section specification in the
        language specified in `lang`.

        The string may specify a section 0 level only (book / tablet), or
        section 0 and 1 levels (book / tablet; chapter / column),
        or all levels
        (book / tablet; chapter / column; verse / line).

        !!! hint "examples"
            A few sections:

                Genesis

                Genesis 1

                Genesis 1:1

                P005381

                P005381 1

                P005381 1:1

    lang: string, optional en
        The language assumed for the section parts,
        as far as they are language dependent.
        Must be a 2-letter language code.

    Returns
    -------
    node | error: integer | string
        Depending on what is passed, the result is a node of section level
        0, 1, or 2.

        If there is no such section heading, an error string is returned.
    """

    api = app.api
    T = api.T

    aContext = app.context
    sep1 = aContext.sectionSep1
    sep2 = aContext.sectionSep2

    msg = f'Not a valid passage: "{sectionStr}"'
    msgi = '{} "{}" is not a number'
    section = sectionStr.split(sep1)

    if len(section) > 2:
        return msg
    elif len(section) == 2:
        section2 = section[1].split(sep2)
        if len(section2) > 2:
            return msg
        section = [section[0]] + section2

    dataTypes = T.sectionFeatureTypes
    sectionTypes = T.sectionTypes
    sectionTyped = []
    msgs = []

    for i, sectionPart in enumerate(section):
        if dataTypes[i] == "int":
            try:
                part = int(sectionPart)
            except ValueError:
                msgs.append(msgi.format(sectionTypes[i], sectionPart))
                part = None
        else:
            part = sectionPart

        sectionTyped.append(part)

    if msgs:
        return "\n".join(msgs)

    sectionNode = T.nodeFromSection(sectionTyped, lang=lang)

    if sectionNode is None:
        return msg
    return sectionNode


def sectionStrFromNode(app, n, lang="en", lastSlot=False, fillup=False, level=None):
    """The heading of a section to which a node belongs.

    Compare `tf.core.text.Text.nodeFromSection`.

    Parameters
    ----------
    node: integer
        The node from which we obtain a section specification.
    lastSlot: boolean, optional False
        Whether the reference node will be the last slot contained by the
        `node` argument or the first node.
        Otherwise it will be the first slot.
    lang: string, optional en
        The language assumed for the section parts,
        as far as they are language dependent.
        Must be a 2-letter language code.
    fillup: boolean, optional False
        Same as for `tf.core.text.Text.sectionTuple`.
    level: integer, optional None
        If passed, not the deepest enclosing section will be taken, but the enclosing
        section at that level.

    Returns
    -------
    section heading:string
        Corresponds to the reference node.
        The result is built from the labels of the individual section levels,
        with dummies for missing parts if `fillup` is true.
    """

    api = app.api
    T = api.T

    aContext = app.context
    sep1 = aContext.sectionSep1
    sep2 = aContext.sectionSep2

    seps = ("", sep1, sep2)

    section = T.sectionFromNode(
        n, lang=lang, lastSlot=lastSlot, fillup=fillup, level=level
    )
    return "".join(
        "" if part is None else f"{seps[i]}{part}" for (i, part) in enumerate(section)
    )


def structureStrFromNode(app, n):
    """The heading of a structure to which a node belongs.

    Compare `tf.core.text.Text.headingFromNode`.


    node: integer
        The node from which we obtain a structure specification.

    Returns
    -------
    structure heading:string
        Corresponds to the first structure node containing the first slot of `n`.
        The result is built from the labels of the individual section levels.
    """

    api = app.api
    T = api.T

    struct = T.headingFromNode(n)

    sep = ""
    result = ""

    for i, part in enumerate(struct):
        if part is None:
            continue
        (nType, label) = part
        result += f'{sep}<span class="nd">{nType}</span> {label}'
        sep = ", "
    return result


def _sectionLink(app, n, text=None, clsName=None):
    newClsName = f'rwh {clsName or ""}'
    return app.webLink(n, clsName=newClsName, text=text, _asString=True, _noUrl=True)
