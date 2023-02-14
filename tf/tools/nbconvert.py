import sys
import os
import re
from subprocess import run

from ..core.helpers import initTree, fileCopy


__pdoc__ = {}

HELP = """
python nbconvert.py inputDir outputDir

Converts all `.ipynb` files in *inputDir* to `.html` files in *outputDir*.
Copies all other files in *inputDir* to *outputDir*.

Makes sure that all links in the resulting html to one of the
original `.ipynb` files are transformed in links to the converted `.html` files.

Command switches

```
-h
--help
```

"""


def task(inputDir, outputDir):
    if not os.path.isdir(inputDir):
        print(f"Input directory does not exist: {inputDir}")
        return 1
    initTree(outputDir, fresh=True)

    nbext = ".ipynb"

    convertedNotebooks = []

    def escapeSpace(x):
        return x.replace(" ", "\\ ")

    def doSubDir(path):
        subInputDir = inputDir if path == "" else f"{inputDir}/{path}"
        subOutputDir = outputDir if path == "" else f"{outputDir}/{path}"
        initTree(subOutputDir)

        theseNotebooks = []

        with os.scandir(subInputDir) as dh:
            for entry in dh:
                name = entry.name
                subPath = name if path == "" else f"{path}/{name}"
                if entry.is_dir():
                    doSubDir(subPath)
                elif name.endswith(nbext):
                    theseNotebooks.append(name)
                else:
                    if not name.startswith("."):
                        fileCopy(f"{subInputDir}/{name}", f"{subOutputDir}/{name}")

        if len(theseNotebooks):
            command = "jupyter nbconvert --to html"
            inFiles = " ".join(
                f"{subInputDir}/{escapeSpace(name)}" for name in theseNotebooks
            )
            commandLine = f"{command} --output-dir={subOutputDir} {inFiles}"
            print(commandLine)
            run(commandLine, shell=True)
            for thisNotebook in theseNotebooks:
                convertedNotebooks.append(
                    (subOutputDir, thisNotebook.replace(nbext, ""))
                )

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
                {nbext}
            )
            (
                ['"]
            )
        """,
        re.X,
    )

    def processLinks(text):
        return LINK_RE.sub(r"\1.html\2", text)

    print("fixing links to converted notebooks:")
    for (path, name) in convertedNotebooks:
        pathName = f"{path}/{name}.html"
        print(pathName)
        with open(pathName) as fh:
            text = fh.read()
        text = processLinks(text)
        with open(pathName, "w") as fh:
            fh.write(text)


def main():
    args = sys.argv[1:]
    if "-h" in args or "--help" in args or len(args) != 2:
        print(HELP)
        quit()

    return task(*args)


__pdoc__["task"] = HELP


if __name__ == "__main__":
    exit(main())
