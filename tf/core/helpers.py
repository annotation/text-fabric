import os
import sys
import re

LETTER = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
VALID = set("_0123456789") | LETTER

WARN32 = """WARNING: you are not running a 64-bit implementation of Python.
You may run into memory problems if you load a big data set.
Consider installing a 64-bit Python.
"""

MSG64 = """Running on 64-bit Python"""

HOME_DIR = os.path.expanduser("~").replace("\\", "/")

SEP_RE = re.compile(r"[ ,]+")
VAR_RE = re.compile(r"\{([^}]+?)(:[^}]+)?\}")
MSG_LINE_RE = re.compile(r"^( *[0-9]+) (.*)$")

QUAD = "  "


def unexpanduser(path):
    return path.replace(HOME_DIR, "~")


def dirEmpty(target):
    return not os.path.exists(target) or not os.listdir(target)


def isInt(val):
    try:
        val = int(val)
    except Exception:
        return False
    return True


def mathEsc(val):
    """Escape $ signs to `<span>$</span>`.

    To prevent them from being interpreted as math in a Jupyter notebook
    in cases where you need them literally.
    """

    return "" if val is None else (str(val).replace("$", "<span>$</span>"))


def mdEsc(val):
    return (
        ""
        if val is None
        else (str(val).replace("|", "&#124;").replace("$", "<span>$</span>"))
    )


def htmlEsc(val):
    """Escape certain HTML characters by HTML entities.

    To prevent them to be interpreted as HTML
    in cases where you need them literally.
    """

    return (
        ""
        if val is None
        else (
            str(val)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace("$", "<span>$</span>")
        )
    )


def mdhtmlEsc(val):
    """Escape certain Markdown characters by HTML entities or span elements.

    To prevent them to be interpreted as Markdown
    in cases where you need them literally.
    """

    return (
        ""
        if val is None
        else (
            str(val)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace("|", "&#124;")
            .replace("$", "<span>$</span>")
        )
    )


def splitModRef(moduleRef):
    parts = moduleRef.split(":", 1)
    if len(parts) == 1:
        parts.append("")
    (ref, specifier) = parts
    parts = ref.split("/", 2)

    if len(parts) < 2:
        console(
            f"""
Module ref "{moduleRef}" is not "{{org}}/{{repo}}/{{path}}"
""",
            error=True,
        )
        return None

    if len(parts) == 2:
        parts.append("")

    return [*parts, specifier]


def camel(name):
    if not name:
        return name
    temp = name.replace("_", " ").title().replace(" ", "")
    return temp[0].lower() + temp[1:]


def check32():
    warn = ""
    msg = ""
    on32 = sys.maxsize < 2 ** 63 - 1
    if on32 < 2 ** 63 - 1:
        warn = WARN32
    else:
        msg = MSG64
    return (on32, warn, msg)


def console(*msg, error=False, newline=True):
    msg = " ".join(m if type(m) is str else repr(m) for m in msg)
    msg = unexpanduser(msg)
    msg = msg[1:] if msg.startswith("\n") else msg
    msg = msg[0:-1] if msg.endswith("\n") else msg
    target = sys.stderr if error else sys.stdout
    nl = "\n" if newline else ""
    target.write(f"{msg}{nl}")
    target.flush()


def cleanName(name):
    clean = "".join(c if c in VALID else "_" for c in name)
    if clean == "" or not clean[0] in LETTER:
        clean = "x" + clean
    return clean


def isClean(name):
    if name is None or len(name) == 0 or name[0] not in LETTER:
        return False
    return all(c in VALID for c in name[1:])


def flattenToSet(features):
    theseFeatures = set()
    if type(features) is str:
        theseFeatures |= setFromStr(features)
    else:
        for feature in features:
            if type(feature) is str:
                theseFeatures.add(feature)
            else:
                feature = feature[1]
                theseFeatures |= setFromValue(feature)
    return theseFeatures


def setDir(obj):
    obj.homeDir = os.path.expanduser("~").replace("\\", "/")
    obj.curDir = os.getcwd().replace("\\", "/")
    (obj.parentDir, x) = os.path.split(obj.curDir)


def expandDir(obj, dirName):
    if dirName.startswith("~"):
        dirName = dirName.replace("~", obj.homeDir, 1)
    elif dirName.startswith(".."):
        dirName = dirName.replace("..", obj.parentDir, 1)
    elif dirName.startswith("."):
        dirName = dirName.replace(".", obj.curDir, 1)
    return dirName


def setFromSpec(spec):
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


def rangesFromSet(nodeSet):
    # ranges = []
    curstart = None
    curend = None
    for n in sorted(nodeSet):
        if curstart is None:
            curstart = n
            curend = n
        elif n == curend + 1:
            curend = n
        else:
            yield (curstart, curend)
            # ranges.append((curstart, curend))
            curstart = n
            curend = n
    if curstart is not None:
        yield (curstart, curend)
        # ranges.append((curstart, curend))
    # return ranges


def rangesFromList(nodeList):  # the list must be sorted
    curstart = None
    curend = None
    for n in nodeList:
        if curstart is None:
            curstart = n
            curend = n
        elif n == curend + 1:
            curend = n
        else:
            yield (curstart, curend)
            curstart = n
            curend = n
    if curstart is not None:
        yield (curstart, curend)


def specFromRanges(ranges):  # ranges must be normalized
    return ",".join(
        "{}".format(r[0]) if r[0] == r[1] else "{}-{}".format(*r) for r in ranges
    )


def specFromRangesLogical(ranges):  # ranges must be normalized
    return [r[0] if r[0] == r[1] else [r[0], r[1]] for r in ranges]


def valueFromTf(tf):
    return "\\".join(
        x.replace("\\t", "\t").replace("\\n", "\n") for x in tf.split("\\\\")
    )


def tfFromValue(val):
    valTp = type(val)
    isInt = valTp is int
    isStr = valTp is str
    if not isInt and not isStr:
        console(f"Wrong type for a TF value: {valTp}: {val}", error=True)
        return None
    return (
        str(val)
        if type(val) is int
        else val.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n")
    )


def makeIndex(data):
    inv = {}
    for (n, m) in data.items():
        inv.setdefault(m, set()).add(n)
    return inv


def makeInverse(data):
    inverse = {}
    for n in data:
        for m in data[n]:
            inverse.setdefault(m, set()).add(n)
    return inverse


def makeInverseVal(data):
    inverse = {}
    for n in data:
        for (m, val) in data[n].items():
            inverse.setdefault(m, {})[n] = val
    return inverse


def nbytes(by):
    units = ["B", "KB", "MB", "GB", "TB"]
    for i in range(len(units)):
        if by < 1024 or i == len(units) - 1:
            fmt = "{:>5}{}" if i == 0 else "{:>5.1f}{}"
            return fmt.format(by, units[i])
        by /= 1024


def collectFormats(config):
    featureSet = set()

    def collectFormat(tpl):
        features = []
        default = ""

        def varReplace(match):
            nonlocal default
            varText = match.group(1)
            default = (match.group(2) or ":")[1:]
            fts = tuple(varText.split("/"))
            features.append((fts, default))
            for ft in fts:
                featureSet.add(ft)
            return "{}"

        rtpl = VAR_RE.sub(varReplace, tpl)
        return (rtpl, tuple(features))

    formats = {}
    for (fmt, tpl) in sorted(config.items()):
        if fmt.startswith("fmt:"):
            formats[fmt[4:]] = collectFormat(tpl)
    return (formats, sorted(featureSet))


def itemize(string, sep=None):
    if not string:
        return []
    if not sep:
        return string.strip().split()
    return string.strip().split(sep)


def project(iterableOfTuples, maxDimension):
    if maxDimension == 1:
        return {r[0] for r in iterableOfTuples}
    return {r[0:maxDimension] for r in iterableOfTuples}


def wrapMessages(messages):
    if type(messages) is str:
        messages = messages.split("\n")
    html = []
    for msg in messages:
        if type(msg) is tuple:
            (error, nl, msgRep) = msg
            match = MSG_LINE_RE.match(msgRep)
            msg = msgRep + ("<br/>" if nl else "")
            clsName = "eline" if error and not match else "tline"
        else:
            match = MSG_LINE_RE.match(msg)
            clsName = "tline" if match else "eline"
            msg = msg.replace("\n", "<br/>")
        html.append(f'<span class="{clsName.lower()}">{msg}</span>')
    return "".join(html)


def makeExamples(nodeList):
    lN = len(nodeList)
    if lN <= 10:
        return f"{lN:>7} x: " + (", ".join(str(n) for n in nodeList))
    else:
        return (
            f"{lN:>7} x: "
            + (", ".join(str(n) for n in nodeList[0:5]))
            + " ... "
            + (", ".join(str(n) for n in nodeList[-5:]))
        )


def setFromValue(x, asInt=False):
    if x is None:
        return set()

    typeX = type(x)
    if typeX in {set, frozenset}:
        return x
    elif typeX in {str, dict, list, tuple}:
        if typeX is str:
            x = SEP_RE.split(x)
        return {int(p) for p in x if p.isdecimal()} if asInt else {p for p in x if p}

    return {x}


def setFromStr(x):
    if x is None:
        return set()

    return {p for p in SEP_RE.split(x) if p}


def mergeDictOfSets(d1, d2):
    for (n, ms) in d2.items():
        if n in d1:
            d1[n] |= ms
        else:
            d1[n] = ms


def mergeDict(source, overrides):
    """Merge overrides into a source dictionary recursively."""

    for (k, v) in overrides.items():
        if k in source and type(source[k]) is dict:
            mergeDict(source[k], v)
        else:
            source[k] = v
