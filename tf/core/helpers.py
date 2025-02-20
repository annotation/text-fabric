import os
import sys
from sys import getsizeof, stderr
import re
from itertools import chain
from collections import deque
from subprocess import run as run_cmd, CalledProcessError
from datetime import datetime as dt, UTC


from ..parameters import OMAP
from .files import readYaml, unexpanduser as ux


NBSP = "\u00a0"  # non-breaking space

TO_SYM = "↦"
FROM_SYM = "⇥"


LETTER = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
VALID = set("_0123456789") | LETTER
MQL_KEYWORDS = dict(
    database="dbase",
    default="dfault",
    first="frst",
    focus="fcus",
    gap="gp",
    last="lst",
    notexist="notexst",
    object="objct",
    retrieve="retriev",
    noretrieve="noretriev",
    type="typ",
)
MQL_KEYWORDS["as"] = "as_"
MQL_KEYWORDS["or"] = "or_"

WARN32 = """WARNING: you are not running a 64-bit implementation of Python.
You may run into memory problems if you load a big data set.
Consider installing a 64-bit Python.
"""

MSG64 = """Running on 64-bit Python"""

SEP_RE = re.compile(r"[\n\t ,]+")
STRIP_RE = re.compile(r"(?:^[\n\t ,]+)|(?:[\n\t ,]+$)", re.S)
VAR_RE = re.compile(r"\{([^}]+?)(:[^}]*)?\}")
MSG_LINE_RE = re.compile(r"^( *[0-9]+) (.*)$")
NUM_ALFA_RE = re.compile(r"^([0-9]*)([^0-9]*)(.*)$")

QUAD = "    "


def utcnow():
    return dt.now(UTC)


def versionSort(x):
    parts = []

    for p in x.split("."):
        match = NUM_ALFA_RE.match(p)
        (num, alfa, rest) = match.group(1, 2, 3)
        parts.append((int(num) if num else 0, alfa, rest))

    return tuple(parts)


def var(envVar):
    """Retrieves the value of an environment variable.

    Parameters
    ----------
    envVar: string
        The name of the environment variable.

    Returns
    -------
    string or void
        The value of the environment variable if it exists, otherwise `None`.
    """
    return os.environ.get(envVar, None)


def isInt(val):
    try:
        val = int(val)
    except Exception:
        return False
    return True


def mathEsc(val):
    """Escape dollar signs to `<span>$</span>`.

    To prevent them from being interpreted as math in a Jupyter notebook
    in cases where you need them literally.
    """

    return "" if val is None else (str(val).replace("$", "<span>$</span>"))


def mdEsc(val, math=False):
    """Escape certain markdown characters.

    Parameters
    ----------
    val: string
        The input value
    math: boolean, optional False
        Whether retain TeX notation.
        If True, `$` is not escaped, if False, it is not escaped.
    """
    if val is None:
        return ""

    val = (
        str(val)
        .replace("!", "&#33;")
        .replace("#", "&#35;")
        .replace("*", "&#42;")
        .replace("[", "&#91;")
        .replace("_", "&#95;")
        .replace("|", "&#124;")
        .replace("~", "&#126;")
    )

    return val if math else val.replace("$", "<span>$</span>")


def htmlEsc(val, math=False):
    """Escape certain HTML characters by HTML entities.

    To prevent them to be interpreted as HTML
    in cases where you need them literally.

    Parameters
    ----------
    val: string
        The input value
    math: boolean, optional False
        Whether retain TeX notation.
        If True, `$` is not escaped, if False, it is not escaped.
    """

    return (
        ""
        if val is None
        else (
            (str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            if math
            else (
                str(val)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("$", "<span>$</span>")
            )
        )
    )


def xmlEsc(val):
    """Escape certain HTML characters by XML entities.

    To prevent them to be interpreted as XML
    in cases where you need them literally.
    """

    return (
        ""
        if val is None
        else (
            str(val)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("'", "&apos;")
            .replace('"', "&quot;")
        )
    )


def mdhtmlEsc(val, math=False):
    """Escape certain Markdown characters by HTML entities or span elements.

    To prevent them to be interpreted as Markdown
    in cases where you need them literally.

    Parameters
    ----------
    val: string
        The input value
    math: boolean, optional False
        Whether retain TeX notation.
        If True, `$` is not escaped, if False, it is not escaped.
    """

    return (
        ""
        if val is None
        else (
            (
                str(val)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("|", "&#124;")
            )
            if math
            else (
                str(val)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("|", "&#124;")
                .replace("$", "<span>$</span>")
            )
        )
    )


def tsvEsc(x):
    """Escapes a double quote for strings to be included in TSV data.

    Only `"` and `'` at the beginning of the string are escaped.
    The escaping is realized by putting a backslash at the beginning.
    """
    s = str(x)
    return s if s == "" else f"\\{s}" if s[0] in {"'", '"'} else s


PANDAS_QUOTE = '"'
PANDAS_ESCAPE = "\u0001"


def pandasEsc(x):
    """Escapes the character that will be used as the `pandas` quote char.

    The escaping is realized by prepending a special char the quote char.
    Also: all tab characters will be replaced by single spaces.
    """
    return (
        x
        if x == ""
        else str(x)
        .replace("\t", " ")
        .replace(PANDAS_QUOTE, PANDAS_ESCAPE + PANDAS_QUOTE)
    )


def camel(name):
    if not name:
        return name
    temp = name.replace("_", " ").title().replace(" ", "")
    return temp[0].lower() + temp[1:]


def check32():
    warn = ""
    msg = ""
    on32 = sys.maxsize < 2**63 - 1
    if on32 < 2**63 - 1:
        warn = WARN32
    else:
        msg = MSG64
    return (on32, warn, msg)


def console(*msg, error=False, newline=True):
    msg = " ".join(m if type(m) is str else repr(m) for m in msg)
    msg = "" if not msg else ux(msg)
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
    return MQL_KEYWORDS.get(clean, clean)


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
    for n, m in data.items():
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
        for m, val in data[n].items():
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
        return (tpl, rtpl, tuple(features))

    formats = {}
    for fmt, tpl in sorted(config.items()):
        if fmt.startswith("fmt:"):
            formats[fmt[4:]] = collectFormat(tpl)
    return (formats, sorted(featureSet))


def itemize(string, sep=None):
    if not string:
        return []
    if not sep:
        return string.strip().split()
    return string.strip().split(sep)


def fitemize(value):
    if not value:
        return []
    if type(value) is str:
        return SEP_RE.split(STRIP_RE.sub("", value))
    if type(value) in {bool, int, float}:
        return [str(value)]
    return list(str(v) for v in value)


def project(iterableOfTuples, maxDimension):
    if maxDimension == 1:
        return {r[0] for r in iterableOfTuples}
    return {r[0:maxDimension] for r in iterableOfTuples}


def wrapMessages(messages):
    if type(messages) is str:
        messages = messages.split("\n")
    html = []
    status = True
    for msg in messages:
        if type(msg) is tuple:
            (error, nl, msgRep) = msg
            if error:
                status = False
            match = MSG_LINE_RE.match(msgRep)
            msg = msgRep + ("<br>" if nl else "")
            clsName = "eline" if error and not match else "tline"
        else:
            match = MSG_LINE_RE.match(msg)
            clsName = "tline" if match else "eline"
            if clsName == "eline":
                status = False
            msg = msg.replace("\n", "<br>")
        html.append(f'<span class="{clsName.lower()}">{msg}</span>')
    return (status, "".join(html))


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
    for n, ms in d2.items():
        if n in d1:
            d1[n] |= ms
        else:
            d1[n] = ms


def mergeDict(source, overrides):
    """Merge overrides into a source dictionary recursively.

    Parameters
    ----------
    source: dict
        The source dictionary, which will be modified by the overrides.
    overrides: dict
        The overrides, itself a dictionary.
    """

    for k, v in overrides.items():
        if k in source and type(source[k]) is dict:
            mergeDict(source[k], v)
        else:
            source[k] = v


def getAllRealFeatures(api):
    """Get all configuration features and all loaded node and edge features.

    Except `omap@v-w` features.
    When we take volumes or collections from works,
    we need to pass these features on.

    This will exclude the computed features and the node / edge features
    that are not loaded by default.
    """

    TF = api.TF
    allFeatures = set()

    for feat, fObj in TF.features.items():
        if fObj.method:
            continue
        if fObj.isConfig:
            allFeatures.add(feat)

    allFeatures |= set(api.Fall())
    allFeatures |= {e for e in api.Eall() if not e.startswith(OMAP)}
    return allFeatures


def formatMeta(featureMeta):
    """Reorder meta data.

    Parameters
    ----------
    meta: dict
        Dictionary of meta data: keyed by feature, valued by a dict
        of metadata in the form of key values

    Returns
    -------
    dict
        A copy of the dict but with the values for metadata keys
        `desc` and `eg` merged under a new key `description`,
        and the keys `desc` and `eg` deleted.
    """

    result = {}
    for f, meta in featureMeta.items():
        fmeta = {}
        for k, v in meta.items():
            if k == "eg" and "desc" in meta:
                continue
            if k == "desc":
                eg = meta.get("eg", "")
                egRep = f" ({eg})" if eg else ""
                fmeta["description"] = f"{v}{egRep}"
            else:
                fmeta[k] = v
        result[f] = fmeta

    return result


def deepSize(o, handlers={}, verbose=False, seen=None):
    """Returns the approximate memory footprint an object and all of its contents.

    Automatically finds the contents of the following builtin containers and
    their subclasses:
    `tuple`, `list`, `deque`, `dict`, `set` and `frozenset`.
    To search other containers, add handlers to iterate over their contents:

    ```
    handlers = {SomeContainerClass: iter,
                OtherContainerClass: OtherContainerClass.get_elements}
    ```

    """

    def dict_handler(d):
        return chain.from_iterable(d.items())

    all_handlers = {
        tuple: iter,
        list: iter,
        deque: iter,
        dict: dict_handler,
        set: iter,
        frozenset: iter,
    }
    all_handlers.update(handlers)  # user handlers take precedence
    if seen is None:
        seen = set()  # track which object id's have already been seen
    default_size = getsizeof(0)  # estimate sizeof object without __sizeof__

    def sizeof(o):
        if id(o) in seen:  # do not double count the same object
            return 0
        seen.add(id(o))
        s = getsizeof(o, default_size)

        if verbose:
            console(s, type(o), repr(o), file=stderr)

        for typ, handler in all_handlers.items():
            if isinstance(o, typ):
                s += sum(map(sizeof, handler(o)))
                break
        return s

    return sizeof(o)


def run(cmdline, workDir=None):
    """Runs a shell command and returns all relevant info.

    The function runs a command-line in a shell, and returns
    whether the command was successful, and also what the output was, separately for
    standard error and standard output.

    Parameters
    ----------
    cmdline: string
        The command-line to execute.
    workDir: string, optional None
        The working directory where the command should be executed.
        If `None` the current directory is used.
    """
    try:
        result = run_cmd(
            cmdline,
            shell=True,
            cwd=workDir,
            check=True,
            capture_output=True,
        )
        stdOut = result.stdout.decode("utf8").strip()
        stdErr = result.stderr.decode("utf8").strip()
        returnCode = 0
        good = True

    except CalledProcessError as e:
        stdOut = e.stdout.decode("utf8").strip()
        stdErr = e.stderr.decode("utf8").strip()
        returnCode = e.returncode
        good = False

    return (good, returnCode, stdOut, stdErr)


def readCfg(folder, file, label, verbose=0, **kwargs):
    settingsFile = f"{folder}/config/{file}.yml"
    settings = readYaml(asFile=settingsFile, **kwargs)

    if settings:
        if verbose == 1:
            console(f"{label} settings read from {settingsFile}")
        good = True
    else:
        console(f"No {label} settings found, looked for {settingsFile}", error=True)
        good = False

    return (good, settings)
