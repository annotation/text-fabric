import sys
from itertools import zip_longest
from glob import glob
from tf.core.helpers import console
from tf.core.files import fileOpen, fileNm, splitExt


def checkDiffs(path1, path2):
    """Check differences between runs of TF generations.
    """
    def diffFeature(f):
        with fileOpen(f"{path1}/{f}.tf") as h:
            eLines = (
                h.readlines()
                if f == "otext"
                else (d for d in h.readlines() if not d.startswith("@"))
            )
        with fileOpen(f"{path2}/{f}.tf") as h:
            nLines = (
                h.readlines()
                if f == "otext"
                else (d for d in h.readlines() if not d.startswith("@"))
            )
        i = 0
        equal = True
        cutOff = 40
        limit = 4
        nUnequal = 0
        for (e, n) in zip_longest(eLines, nLines, fillvalue="<empty>"):
            i += 1
            if e != n:
                if nUnequal == 0:
                    console(
                        "differences{}".format(
                            "" if f == "otext" else " after the metadata"
                        )
                    )
                shortE = e[0:cutOff] + (" ..." if len(e) > cutOff else "")
                shortN = n[0:cutOff] + (" ..." if len(n) > cutOff else "")
                console("\tline {:>6} OLD -->{}<--".format(i, shortE.rstrip("\n")))
                console("\tline {:>6} NEW -->{}<--".format(i, shortN.rstrip("\n")))
                equal = False
                nUnequal += 1
                if nUnequal >= limit:
                    break

        console("no changes" if equal else "")

    console(f"Check differences between TF files in {path1} and {path2}")
    files1 = glob(f"{path1}/*.tf")
    files2 = glob(f"{path2}/*.tf")
    features1 = {fileNm(splitExt(f)[0]) for f in files1}
    features2 = {fileNm(splitExt(f)[0]) for f in files2}

    addedOnes = features2 - features1
    deletedOnes = features1 - features2
    commonOnes = features2 & features1

    if addedOnes:
        console(f"\t{len(addedOnes)} features to add")
        for f in sorted(addedOnes):
            console(f"\t\t{f}")
    else:
        console("\tno features to add")
    if deletedOnes:
        console(f"\t{len(deletedOnes)} features to delete")
        for f in sorted(deletedOnes):
            console(f"\t\t{f}")
    else:
        console("\tno features to delete")

    console(f"\t{len(commonOnes)} features in common")
    for f in sorted(commonOnes):
        console(f"{f}")
        diffFeature(f)
    console("Done")


if __name__ == "__main__":
    checkDiffs(*sys.argv[1:3])
