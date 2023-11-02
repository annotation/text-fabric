"""De-indents the lines of a file or the files in a directory.

It supports two types of file:

*   `.md`: markdown files
*   `.py`: python files

In markdown files, it treats all lines,
in python files only the lines in docstrings.

The reason is that in Markdown both list items and code blocks can be marked by
indentation, and the vim spell-checker cannot see the difference.

By de-indenting the lines first, we can let the spell-checker do its work.
"""
import sys
import ast
import re

from ..core.files import (
    isFile,
    isDir,
    dirAllFiles,
    expanduser as ex,
    unexpanduser as ux,
)


HELP = """
USAGE

indentify mode src dst

where

src is an existing file or directory;
dst is a path name to which the result file is written.
    If it exists as file, it will be overwritten.
    It should not be an existing directory.
"""


TICK_RE = re.compile(r"""`[^`]*`""")
TTICK_RE = re.compile(
    r"""
        ```
        .*?
        ```
    """,
    re.S | re.X,
)
OLD_TTICK_RE = re.compile(
    r"""
        (?:^|\n)
        \s*
        ```
        (?:\s*[a-z]+\s*)?
        \s*\n
        .*?
        \n
        \s*
        ```
        \s*
        (?:\n|$)
    """,
    re.S | re.X,
)
IMG_RE = re.compile(r"""<img\b[^>]*>""", re.S)
ELEMS_RE = re.compile(r"""</?(?:table|tr|tbody|thead|td|th|br)\b[^>]*>""", re.S)
STYLE_RE = re.compile(r"""<style\b[^>]*>.*?</style>""", re.S)
PRE_RE = re.compile(r"""<pre\b[^>]*>.*?</pre>""", re.S)
SPAN_RE = re.compile(r"""<span\b[^>]*>.*?</span>""", re.S)
TD_RE = re.compile(r"""<td\b[^>]*>.*?</td>""", re.S)


SYM_RE = re.compile(r"""«[a-zA-Z0-9_]*»""")


PARAM_RE = re.compile(
    r"""
        ^
        [a-zA-Z0-9_]+
        (?:
            ,
            \s*
            [a-zA-Z0-9]+
        )*
        :
        \s+
        (?:
            string|
            boolean|
            integer|
            float|
            tuple|
            list|
            dict|
            function|
            set|
            frozenset|
            iterable|
            object|
            mixed |
            AttrDict
        )
    """,
    re.M | re.X,
)

RETURN_RE = re.compile(
    r"""
        ^
        \s*
        (?:
            string|
            boolean|
            integer|
            tuple|
            list|
            dict|
            function|
            set|
            frozenset|
            iterable|
            object|
            mixed |
            AttrDict
        )
        \s*
        $
    """,
    re.M | re.X,
)

DOTNAME_RE = re.compile(
    r"""
        \b
        [a-zA-Z0-9_]+
        (?:
            [./]
            [a-zA-Z0-9_]+
        )+
        \b
    """,
    re.X,
)

ILINK_RE = re.compile(r"""!\[[^]]+\]\([^)]+\)""")
LINK_RE = re.compile(r"""\[([^]]+)\]\([^)]+\)""")


def apply(line):
    line = line.strip()

    if RETURN_RE.match(line) or PARAM_RE.match(line):
        line = ""
    elif line.startswith("!!! "):
        line = line[4:]

    line = DOTNAME_RE.sub(" ", line)

    return line


def operation(srcFile, dstLines):
    isPy = srcFile.endswith(".py")
    isMd = srcFile.endswith(".md")

    if not isPy and not isMd:
        return True

    srcFileX = ux(srcFile)

    print(f"{srcFileX}")

    with open(srcFile) as fh:
        dstLines.append(f"\nFILE\n\n,,\t{srcFileX}\n")

        if isMd:
            for line in fh:
                dstLines.append(apply(line))

        if isPy:
            text = fh.read()
            code = ast.parse(text)

            for node in ast.walk(code):
                tp = type(node)
                isMod = tp is ast.Module
                isClass = tp is ast.ClassDef
                isFunc = tp is ast.FunctionDef

                if not (isMod or isClass or isFunc):
                    continue

                kind = (
                    "MODULE"
                    if isMod
                    else f"CLASS\n\n,,\t={node.name}"
                    if isClass
                    else f"FUNCTION\n\n,,\t={node.name}"
                )
                docstring = ast.get_docstring(node)

                if docstring:
                    dstLines.append(f"\n{kind}\n")
                    lines = docstring.split("\n")

                    for line in lines:
                        dstLines.append(apply(line))


def main(cargs=sys.argv[1:]):
    if len(cargs) != 2:
        print(HELP)
        print(f"{len(cargs)} argument(s) passed. We need exactly two.")
        return -1

    (src, dst) = cargs
    src = ex(src)
    dst = ex(dst)

    srcIsFile = isFile(src)
    srcIsDir = isDir(src)

    if not (srcIsFile or srcIsDir):
        print(f"Source is not an existing file or directory: {src}")
        return -1

    if isFile(dst):
        print("Destination already exists as file and will be overwritten")
    elif isDir(dst):
        print(HELP)
        print("Destination is an existing directory")
        return -1

    srcFiles = dirAllFiles(src)

    dstLines = []

    for srcFile in srcFiles:
        operation(srcFile, dstLines)

    with open(dst, "w") as fh:
        nLines = len(dstLines)
        text = "\n".join(dstLines)
        text = TD_RE.sub(" ", text)
        text = IMG_RE.sub("", text)
        text = STYLE_RE.sub(" ", text)
        text = PRE_RE.sub(" ", text)
        text = SPAN_RE.sub(" ", text)
        text = ELEMS_RE.sub(" ", text)
        text = ILINK_RE.sub(r" ", text)
        text = LINK_RE.sub(r"\1", text)
        text = TTICK_RE.sub("\n", text)

        good = True

        for i, line in enumerate(text.split("\n")):
            tc = line.count("`")
            if tc % 2 == 1:
                good = False
                print(f"Line {i + 1:>6}: odd number ({tc}) of ticks in: {line}")

        if good:
            text = TICK_RE.sub("CODE", text)
        else:
            print("No `code` replacement because of unmatched `s")

        text = SYM_RE.sub("", text)

        lines = [x for line in text.split("\n") if (x := line.strip())]

        fh.write("\n".join(lines))
        print(f"{nLines} written")

    return 0


if __name__ == "__main__":
    sys.exit(main())
