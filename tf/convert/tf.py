"""
# Raw, unoptimized data from TF files
"""

import sys
import os


DATA_TYPES = ("str", "int")
DATA_TYPE_STR = ", ".join(DATA_TYPES)
HOME_DIR = os.path.expanduser("~").replace("\\", "/")


def explode(inPath, outPath):
    """Explodes .tf files into non-optimized .tf files without metadata.

    An exploded .tf feature file is a tf file with explicit node specifiers,
    no optimizations.

    The format of each line is:

    **Node features**:

        node<tab>value

    If the value is None for a certain `node`, there will be no such line.

    **Edge features without values**:

        node<tab>node

    **Edge features with values**:

        node<tab>node<tab>value

    If the value is `None`, it will be left out, together with the preceding <tab>.
    This way, the empty string is distinguished from a `None` value.

    !!! caution "Ambiguity"
        In the resulting data file, all metadata is gone.
        It is not always possible to infer from the data alone what data type a feature
        has:

        `1<tab>2` could be a node feature assigning integer 2 to node 1, or string `2`
        to node 1.

        It could also be an edge feature assigning `None` to the node pair (1, 2).

    Parameters
    ----------
    inPath: string
        Source file(s).
        If pointing to a file, it should be file containing TF feature data.
        If pointing to a directory, all .tf files in that directory will be exploded
        (non-recursively).
        The path may contain `~` which will be expanded to the user's home directory.
    outPath: string
        Destination of the exploded file(s).
        If pointing to a non-existing location, a file or directory will be created
        there, depending on whether `inPath` is a file or directory.
        If pointing to an existing directory, exploded file(s) will be put there.

    Returns
    -------
    bool
        whether the operation was successful.
    """

    inLoc = os.path.expanduser(inPath)
    outLoc = os.path.expanduser(outPath)
    if not os.path.exists(inLoc):
        return f"No such file or directory: `{inPath}`"

    isInDir = os.path.isdir(inLoc)
    outExists = os.path.exists(outLoc)
    isOutDir = os.path.isdir(outLoc) if outExists else None

    tasks = []

    if isInDir:
        with os.scandir(inLoc) as sd:
            tasks = [
                (f"{inLoc}/{e.name}", f"{outLoc}/{e.name}")
                for e in sd
                if e.name.endswith(".tf") and e.is_file()
            ]
            if not tasks:
                return "No .tf files in `{inPath}`"
        if outExists and not isOutDir:
            return "Not a directory: `{outPath}`"
        if not outExists:
            os.makedirs(outLoc, exist_ok=True)
    else:
        if not os.path.isfile(inLoc):
            return "Not a file: `{inPath}"
        if outExists:
            if isOutDir:
                outFile = f"{outLoc}/{os.path.basename(inLoc)}"
            else:
                outFile = outLoc
        else:
            outDir = os.path.dirname(outLoc)
            if not os.path.exists(outDir):
                os.makedirs(outDir, exist_ok=True)
            outFile = outLoc

        tasks = [(inLoc, outFile)]

    msgs = []

    for (inFile, outFile) in sorted(tasks):
        result = _readTf(inFile)
        if type(result) is str:
            msgs.append(
                f"{unexpanduser(inFile)} => {unexpanduser(outFile)}:\n\t{result}"
            )
            continue
        (data, valueType, isEdge) = result
        _writeTf(outFile, *result)

    good = True
    if msgs:
        for msg in msgs:
            thisGood = msg[0] != "X"
            (sys.stdout if thisGood else sys.stderr).write(f"{msg}\n")
            if not thisGood:
                good = False
    return good


def _readTf(path):
    fh = open(path, encoding="utf8")
    i = 0
    metaData = {}
    isEdge = False
    edgeValues = False
    error = None

    for line in fh:
        i += 1
        if i == 1:
            text = line.rstrip()
            if text == "@edge":
                isEdge = True
            elif text == "@node":
                isEdge = False
            elif text == "@config":
                error = "! This is a config feature. It has no data."
                fh.close()
                return error
            else:
                error = f"X Line {i}: missing @node/@edge/@config"
                fh.close()
                return error
            continue
        text = line.rstrip("\n")
        if len(text) and text[0] == "@":
            if text == "@edgeValues":
                edgeValues = True
                continue
            fields = text[1:].split("=", 1)
            metaData[fields[0]] = fields[1] if len(fields) == 2 else None
            continue
        else:
            if text != "":
                error = f"X Line {i}: missing blank line after metadata"
                fh.close()
                return error
            else:
                break
    typeKey = "valueType"
    if typeKey in metaData:
        valueType = metaData[typeKey]
        if valueType not in DATA_TYPES:
            error = (
                f'X Unknown @valueType: "{valueType}". Expected one of {DATA_TYPE_STR}'
            )
            fh.close()
            return error
    else:
        error = f"X Missing @valueType. Should be one of {DATA_TYPE_STR}"
        fh.close()
        return error
    result = _readDataTf(fh, i, valueType, isEdge, edgeValues)
    fh.close()
    return result


def _readDataTf(fh, firstI, valueType, isEdge, edgeValues):
    i = firstI
    implicit_node = 1
    data = {}
    normFields = 3 if isEdge and edgeValues else 2
    isNum = valueType == "int"
    for line in fh:
        i += 1
        fields = line.rstrip("\n").split("\t")
        lfields = len(fields)
        if lfields > normFields:
            return f"line {i}: {lfields} fields instead of {normFields}"
        if lfields == normFields:
            nodes = _setFromSpec(fields[0])
            if isEdge:
                if fields[1] == "":
                    return f"line {i}: missing node for edge"
                nodes2 = _setFromSpec(fields[1])
            if not isEdge or edgeValues:
                valTf = fields[-1]
        else:
            if isEdge:
                if edgeValues:
                    if lfields == normFields - 1:
                        nodes = {implicit_node}
                        nodes2 = _setFromSpec(fields[0])
                        valTf = fields[-1]
                    elif lfields == normFields - 2:
                        nodes = {implicit_node}
                        if fields[0] == "":
                            return f"line {i}: missing node for edge"
                        nodes2 = _setFromSpec(fields[0])
                        valTf = ""
                    else:
                        nodes = {implicit_node}
                        valTf = ""
                        return f"line {i}: missing node for edge"
                else:
                    if lfields == normFields - 1:
                        nodes = {implicit_node}
                        if fields[0] == "":
                            return f"line {i}: missing node for edge"
                        nodes2 = _setFromSpec(fields[0])
                    else:
                        return f"line {i}: missing node for edge"
            else:
                nodes = {implicit_node}
                if lfields == 1:
                    valTf = fields[0]
                else:
                    valTf = ""
        implicit_node = max(nodes) + 1
        if not isEdge or edgeValues:
            value = (
                int(valTf)
                if isNum and valTf != ""
                else None
                if isNum
                else ""
                if valTf == ""
                else _valueFromTf(valTf)
            )
        if isEdge:
            if not edgeValues:
                value = None
            for n in nodes:
                for m in nodes2:
                    data[(n, m)] = value
        else:
            for n in nodes:
                if value is not None:
                    data[n] = value
    return (data, valueType, isEdge)


def _writeTf(outFile, data, valueType, isEdge):
    isInt = valueType == "int"
    with open(outFile, "w") as fh:
        if isEdge:
            if isInt:
                for ((n, m), v) in sorted(data.items()):
                    vTf = '' if v is None else f"\t{v}"
                    fh.write(f"{n}\t{m}{vTf}\n")
            else:
                for ((n, m), v) in sorted(data.items()):
                    vTf = '' if v is None else f"\t{_valueFromTf(v)}"
                    fh.write(f"{n}\t{m}{vTf}\n")
        else:
            if isInt:
                for (n, v) in sorted(data.items()):
                    if v is not None:
                        fh.write(f"{n}\t{v}\n")
            else:
                for (n, v) in sorted(data.items()):
                    if v is not None:
                        fh.write(f"{n}\t{_valueFromTf(v)}\n")


def _valueFromTf(tf):
    return "\\".join(
        x.replace("\\t", "\t").replace("\\n", "\n") for x in tf.split("\\\\")
    )


def _tfFromValue(val, isInt):
    return (
        str(val)
        if isInt
        else val.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n")
    )


def _setFromSpec(spec):
    covered = set()
    for r_str in spec.split(","):
        bounds = r_str.split("-")
        if len(bounds) == 1:
            covered.add(int(r_str))
        else:
            b = int(bounds[0])
            e = int(bounds[1])
            if e < b:
                (b, e) = (e, b)
            for n in range(b, e + 1):
                covered.add(n)
    return covered


def unexpanduser(path):
    return path.replace(HOME_DIR, "~")
