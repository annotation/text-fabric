import sys
import re
from subprocess import run
from textwrap import dedent

from ..core.helpers import console
from ..core.files import (
    fileOpen,
    unexpanduser as ux,
    isDir,
    fileCopy,
    scanDir,
    initTree,
)


__pdoc__ = {}

HELP = """

``` sh
nbconvert inputDir [outputDir]
```

Several modes:

Copy mode
---------
If outputDir is given and not equal to "-":

Converts all `.ipynb` files in `inputDir` to `.html` files in `outputDir`.
Copies all other files in `inputDir` to `outputDir`.
If `outputDir` does not exist, it will be created.

Makes sure that all links in the resulting HTML to one of the
original `.ipynb` files are transformed in links to the converted `.html` files.

In place mode
-------------
If outputDir is given and equal to "-":

Converts all `.ipynb` files in `inputDir` to `.html` files next to their originals.
Overwrites existing HTML names with the same name.

Makes sure that all links in the resulting HTML to one of the
original `.ipynb` files are transformed in links to the converted `.html` files.

Index mode
----------
Without outputDir

Generates an index.html file in inputDir with links
to all HTML files that can be recursively found inside the inputDir.

Command switches

``` sh
-h
--help
```

"""


HTML_EXT = ".html"
NB_EXT = ".ipynb"
INDEX = "index.html"


def task(*args):
    inputDir = args[0]
    if not isDir(inputDir):
        console(f"Input directory does not exist: {inputDir}")
        return 1

    if len(args) == 1:
        console("INDEX MODE")
        makeIndex(inputDir)
    else:
        convertDir(inputDir, args[1])


def makeIndex(inputDir):
    htmlStart = dedent(
        """
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="utf-8"/>
            </head>
            <style>
            div {
                padding-left: 3em;
            }
            </style>
            <body>
        """
    )
    htmlEnd = dedent(
        """
            </body>
        </html>
        """
    )

    def doSubDir(path):
        subInputDir = inputDir if path == "" else f"{inputDir}/{path}"

        theseLinks = []

        with scanDir(subInputDir) as dh:
            for entry in dh:
                name = entry.name
                if name.startswith("."):
                    continue
                subPath = name if path == "" else f"{path}/{name}"
                if entry.is_dir():
                    subResult = doSubDir(subPath)
                    if len(subResult) > 0:
                        theseLinks.append((name, path, doSubDir(subPath)))
                elif name.endswith(HTML_EXT) and name != INDEX:
                    theseLinks.append((name, path))
        return sorted(theseLinks)

    def formatDir(entry):
        if len(entry) == 3:
            (name, path, subEntries) = entry
            subResults = "\n".join(formatDir(subEntry) for subEntry in subEntries)
            return dedent(
                f"""
                <details>
                    <summary>{name}</summary>
                    <div>
                        {subResults}
                    </div>
                </details>
                """
            ).strip()
        else:
            (name, path) = entry
            url = name if path == "" else f"{path}/{name}"
            return f"""<a href="{url}">{name.removesuffix(HTML_EXT)}</a><br>"""

    console(f"Creating a table of contents for {ux(inputDir)}")
    result = doSubDir("")

    html = "\n".join(formatDir(d) for d in result)

    html = f"{htmlStart}{html}{htmlEnd}"
    filePath = INDEX if inputDir == "" else f"{inputDir}/{INDEX}"

    with fileOpen(filePath, mode="w") as fh:
        fh.write(html)

    console(f"Created {ux(filePath)}")


def convertDir(inputDir, outputDir):
    inPlace = outputDir == "-"
    console("IN PLACE MODE" if inPlace else "COPY MODE")

    if not inPlace:
        initTree(outputDir, fresh=True)

    convertedNotebooks = []

    def escapeSpace(x):
        return x.replace(" ", "\\ ")

    def doSubDir(path):
        subInputDir = inputDir if path == "" else f"{inputDir}/{path}"

        if not inPlace:
            subOutputDir = outputDir if path == "" else f"{outputDir}/{path}"
            initTree(subOutputDir)

        theseNotebooks = []

        with scanDir(subInputDir) as dh:
            for entry in dh:
                name = entry.name
                if name.startswith("."):
                    continue
                subPath = name if path == "" else f"{path}/{name}"
                if entry.is_dir():
                    doSubDir(subPath)
                elif name.endswith(NB_EXT):
                    theseNotebooks.append(name)
                else:
                    if not inPlace:
                        fileCopy(f"{subInputDir}/{name}", f"{subOutputDir}/{name}")

        if len(theseNotebooks):
            command = "jupyter nbconvert --to html"
            inFiles = " ".join(
                f"{subInputDir}/{escapeSpace(name)}" for name in theseNotebooks
            )
            destDir = subInputDir if inPlace else subOutputDir
            commandLine = f"{command} --output-dir={destDir} {inFiles}"
            run(commandLine, shell=True)
            for thisNotebook in theseNotebooks:
                convertedNotebooks.append((destDir, thisNotebook.replace(NB_EXT, "")))

    doSubDir("")
    convertedPat = ")|(?:".join(re.escape(c[1]) for c in convertedNotebooks)

    LINK_RE = re.compile(
        rf"""
            \b
            (
                (?:
                    href|src
                )
                =
                ['"]
                (?:
                    [^'"]*/
                )?
                (?:
                    {convertedPat}
                )
            )
            (?:
                {NB_EXT}
            )
            (
                ['"]
            )
        """,
        re.X,
    )

    def processLinks(text):
        return LINK_RE.sub(r"\1.html\2", text)

    console("fixing links to converted notebooks:")
    for path, name in convertedNotebooks:
        pathName = f"{path}/{name}.html"
        console(pathName)
        with fileOpen(pathName) as fh:
            text = fh.read()
        text = processLinks(text)
        with fileOpen(pathName, mode="w") as fh:
            fh.write(text)


def main():
    args = sys.argv[1:]
    if "-h" in args or "--help" in args or len(args) not in {1, 2}:
        console(HELP)
        quit()

    return task(*args)


__pdoc__["task"] = HELP


if __name__ == "__main__":
    exit(main())
