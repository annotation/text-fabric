import types


def sectionsApi(app):
    app.nodeFromSectionStr = types.MethodType(nodeFromSectionStr, app)
    app.sectionStrFromNode = types.MethodType(sectionStrFromNode, app)
    app.structureStrFromNode = types.MethodType(structureStrFromNode, app)
    app._sectionLink = types.MethodType(_sectionLink, app)


def nodeFromSectionStr(app, sectionStr, lang="en"):
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
    for (i, sectionPart) in enumerate(section):
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


def sectionStrFromNode(app, n, lang="en", lastSlot=False, fillup=False):
    api = app.api
    T = api.T

    aContext = app.context
    sep1 = aContext.sectionSep1
    sep2 = aContext.sectionSep2

    seps = ("", sep1, sep2)

    section = T.sectionFromNode(n, lang=lang, lastSlot=lastSlot, fillup=fillup)
    return "".join(
        "" if part is None else f"{seps[i]}{part}" for (i, part) in enumerate(section)
    )


def structureStrFromNode(app, n):
    api = app.api
    T = api.T

    struct = T.headingFromNode(n)

    sep = ''
    result = ''

    for (i, part) in enumerate(struct):
        if part is None:
            continue
        (nType, label) = part
        result += f'{sep}<span class="nd">{nType}</span> {label}'
        sep = ", "
    return result


def _sectionLink(app, n, text=None, clsName=None):
    newClsName = f'rwh {clsName or ""}'
    return app.webLink(
        n, clsName=newClsName, text=text, _asString=True, _noUrl=True
    )
