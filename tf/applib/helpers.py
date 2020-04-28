import os

from IPython.display import display, Markdown, HTML

from ..parameters import EXPRESS_BASE, GH_BASE, TEMP_DIR


RESULT = "result"
NB = "\u00a0"


def dm(md):
    display(Markdown(md))


def dh(html):
    display(HTML(html))


# COLLECT CONFIG SETTINGS IN A DICT


def getLocalDir(cfg, local, version):
    provenanceSpec = cfg.get("provenanceSpec", {})
    org = provenanceSpec.get("org", None)
    repo = provenanceSpec.get("repo", None)
    relative = provenanceSpec.get("relative", "tf")
    version = provenanceSpec.get("version", None) if version is None else version
    base = hasData(local, org, repo, version, relative)

    if not base:
        base = EXPRESS_BASE

    return os.path.expanduser(f"{base}/{org}/{repo}/{TEMP_DIR}")


def hasData(local, org, repo, version, relative):
    versionRep = f"/{version}" if version else ""
    if local == "clone":
        ghBase = os.path.expanduser(GH_BASE)
        ghTarget = f"{ghBase}/{org}/{repo}/{relative}{versionRep}"
        if os.path.exists(ghTarget):
            return ghBase

    expressBase = os.path.expanduser(EXPRESS_BASE)
    expressTarget = f"{expressBase}/{org}/{repo}/{relative}{versionRep}"
    if os.path.exists(expressTarget):
        return expressBase
    return False


def tupleEnum(tuples, start, end, limit, item):
    if start is None:
        start = 1
    i = -1
    if not hasattr(tuples, "__len__"):
        if end is None or end - start + 1 > limit:
            end = start - 1 + limit
        for tup in tuples:
            i += 1
            if i < start - 1:
                continue
            if i >= end:
                break
            yield (i + 1, tup)
    else:
        if end is None or end > len(tuples):
            end = len(tuples)
        rest = 0
        if end - (start - 1) > limit:
            rest = end - (start - 1) - limit
            end = start - 1 + limit
        for i in range(start - 1, end):
            yield (i + 1, tuples[i])
        if rest:
            dh(
                f"<b>{rest} more {item}s skipped</b> because we show a maximum of"
                f" {limit} {item}s at a time"
            )
