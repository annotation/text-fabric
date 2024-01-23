"""
# Utility functions

Read and write TF node sets from / to file.
"""

import pickle
import gzip
from .parameters import PICKLE_PROTOCOL, GZIP_LEVEL
from .core.helpers import console
from .core.files import fileOpen, expanduser as ex, fileExists, dirMake, splitPath


def writeList(data, dest, intCols=None):
    """Writes a list of tuples sets to a TSV file.

    The members of the tuples will be written
    as string values in tab separated lines, with newlines and tabs
    escaped with backslashes.

    The first line consists of tab-separated values that are either the
    string `str` or the string `int`, indicating the type of values of the
    corresponding column.
    values are supposed to be integers.

    Intended use: if you have data from an NLP pipeline, it usually comes as a list
    of tuples, where each tuple has two position columns plus extra columns
    for linguistic features, which are strings or numbers.

    If there is no data, an empty file is created, with a header line.
    If `intCols` is not given, the header line itself is empty.

    !!! caution "Equal length"
        It is assumed that all tuples have equal length.

    Parameters
    ----------
    data: list of tuples
    dest: string
        A file path. You may use `~` to refer to your home directory.
        The result will be written from this file.
    intCols: tuple, optional None
        A sequence of boolean values, indicating which columns have integer values.
        If None, all columns are of type string.

    Returns
    -------
    boolean
        `True` if all went well, `False` otherwise.
    """

    destPath = ex(dest)
    (baseDir, fileName) = splitPath(destPath)

    dirMake(baseDir)

    with fileOpen(destPath, mode="w") as fh:
        if intCols is None:
            intCols = {i: False for i in range(len(data[0]))} if len(data) else {}
        else:
            intCols = {i: isInt for (i, isInt) in enumerate(intCols)}

        headLine = "\t".join("int" if intCols[i] else "str" for i in sorted(intCols))
        fh.write(f"{headLine}\n")

        for fields in data:
            dataLine = "\t".join(
                str(f) if intCols[i] else str(f).replace("\t", "\\t").replace("\n", "\\n")
                for (i, f) in enumerate(fields)
            )
            fh.write(f"{dataLine}\n")
    return True


def readList(source):
    """Reads list of tuples from a TSV file.

    The first line of the TSV file will be interpreted as the types of the
    columns.

    Parameters
    ----------
    source: string
        A file path. You may use `~` to refer to your home directory.
        This file must contain a `gzipped`, `pickled` data structure.

    Returns
    -------
    data | boolean
        The list of tuples obtained from the file if all went well, False otherwise.

    """

    sourcePath = ex(source)
    if not fileExists(sourcePath):
        console(f'Sets file "{source}" does not exist.')
        return False

    data = []

    with fileOpen(sourcePath) as fh:
        colInt = {
            i: tp == "int" for (i, tp) in enumerate(next(fh).rstrip("\n").split("\t"))
        }
        for line in fh:
            fields = tuple(
                int(f) if colInt[i] else f.replace("\\n", "\n").replace("\\t", "\t")
                for (i, f) in enumerate(line.rstrip("\n").split("\t"))
            )
            data.append(fields)

    return data


def writeSets(sets, dest):
    """Writes a dictionary of named sets to file.

    The dictionary will be written as a `gzipped`, `pickled` data structure.

    Intended use: if you have constructed custom node sets that you want to use
    in search templates that run in the TF browser.

    Parameters
    ----------
    sets: dict of sets
        The keys are names for the values, which are sets of nodes.
    dest: string
        A file path. You may use `~` to refer to your home directory.
        The result will be written from this file.

    Returns
    -------
    boolean
        `True` if all went well, `False` otherwise.
    """

    destPath = ex(dest)
    (baseDir, fileName) = splitPath(destPath)

    dirMake(baseDir)

    with gzip.open(destPath, mode="wb", compresslevel=GZIP_LEVEL) as f:
        pickle.dump(sets, f, protocol=PICKLE_PROTOCOL)
    return True


def readSets(source):
    """Reads a dictionary of named sets from file.

    This is used by the TF browser, when the user has passed a
    `--sets=fileName` argument to it.

    Parameters
    ----------
    source: string
        A file path. You may use `~` to refer to your home directory.
        This file must contain a `gzipped`, `pickled` data structure.

    Returns
    -------
    data | boolean
        The data structure contained in the file if all went well, False otherwise.

    """

    sourcePath = ex(source)
    if not fileExists(sourcePath):
        console(f'Sets file "{source}" does not exist.')
        return False
    with gzip.open(sourcePath, mode="rb") as f:
        sets = pickle.load(f)
    return sets
