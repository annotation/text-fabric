import os
import socket
import errno

from IPython.display import display, Markdown, HTML

from ..parameters import EXPRESS_BASE, GH_BASE, TEMP_DIR, PORT_BASE
from ..core.helpers import camel


RESULT = "result"
NB = "\u00a0"


def dm(md):
    display(Markdown(md))


def dh(html):
    display(HTML(html))


# COLLECT CONFIG SETTINGS IN A DICT


def configureNames(names, myDir):
    """
  Collect the all-uppercase globals from a config file
  and put them in a dict in camel case.
  """
    result = {camel(key): value for (key, value) in names.items() if key == key.upper()}

    with open(f"{myDir}/static/display.css", encoding="utf8") as fh:
        result["css"] = fh.read()

    return result


def configure(config, version):
    (names, path) = config.deliver()
    result = configureNames(names, path)
    result["version"] = config.VERSION if version is None else version
    return result


def getLocalDir(names, local, version):
    provenanceSpec = names.get("provenanceSpec", {})
    org = provenanceSpec.get("org", None)
    repo = provenanceSpec.get("repo", None)
    relative = provenanceSpec.get("relative", "tf")
    version = provenanceSpec.get("version", "0.1") if version is None else version
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


def portIsInUse(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.bind((host, port))
        result = True
    except OverflowError:
        result = None
    except socket.error as e:
        if e.errno == errno.EADDRINUSE:
            result = False
        else:
            result = False

    s.close()
    return result


def getPorts(host):
    ports = []
    for port in range(PORT_BASE, PORT_BASE + 100):
        status = portIsInUse(host, port)
        if status is None:
            break
        if not status:
            continue
        ports.append(port)
        if len(ports) > 1:
            break

    return ports


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
