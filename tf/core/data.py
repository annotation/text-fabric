import array
import gc
import pickle
from pickletools import optimize
import gzip
import collections
import time
from ..parameters import PACK_VERSION, PICKLE_PROTOCOL, GZIP_LEVEL, OTYPE, OSLOTS, OTEXT
from .helpers import (
    setFromSpec,
    valueFromTf,
    tfFromValue,
    specFromRanges,
    rangesFromSet,
    check32,
    console,
    utcnow,
)
from .files import (
    fileOpen,
    unexpanduser as ux,
    fileExists,
    fileRemove,
    dirMake,
    splitExt,
    splitPath,
    mTime,
)
from .timestamp import SILENT_D, silentConvert

ERROR_CUTOFF = 20

DATA_TYPES = ("str", "int")

MEM_MSG = (
    "TF is out of memory!\n"
    + "If this happens and your computer has more than 3GB RAM on board:\n"
    + ("* make sure that you run 64-bit Python and/or\n" if check32()[0] else "")
    + "* close all other programs and try again.\n"
)

FATAL_MSG = "There was a fatal error! The message is:\n"


class Data:
    def __init__(
        self,
        path,
        tmObj,
        edgeValues=False,
        data=None,
        isEdge=None,
        isConfig=None,
        metaData={},
        method=None,
        dependencies=None,
    ):
        (dirName, baseName) = splitPath(path)
        (fileName, extension) = splitExt(baseName)
        self.path = path
        self.tmObj = tmObj
        self.dirName = dirName
        self.fileName = fileName
        self.extension = extension
        self.binDir = f"{dirName}/.tf/{PACK_VERSION}"
        self.binPath = f"{self.binDir}/{self.fileName}.tfx"
        self.edgeValues = edgeValues
        self.isEdge = isEdge
        self.isConfig = isConfig
        self.metaData = metaData
        self.method = method
        self.dependencies = dependencies
        self.data = data
        self.dataLoaded = False
        self.dataError = False
        self.dataType = "str"

    def load(self, metaOnly=False, silent=SILENT_D, _withGc=True):
        """Load a feature.

        _withGc: boolean, optional True
            If False, it disables the Python garbage collector before
            loading features. Used to experiment with performance.
        """

        silent = silentConvert(silent)
        tmObj = self.tmObj
        isSilent = tmObj.isSilent
        setSilent = tmObj.setSilent
        indent = tmObj.indent
        info = tmObj.info
        error = tmObj.error

        wasSilent = isSilent()
        setSilent(silent)
        indent(level=True, reset=True)
        origTime = self._getModified()
        binTime = self._getModified(bin=True)
        sourceRep = (
            ", ".join(
                dep.fileName for dep in self.dependencies if isinstance(dep, Data)
            )
            if self.method
            else self.dirName
        )
        sourceRep = ux(sourceRep)
        msgFormat = "{:<1} {:<20} from {}"
        actionRep = ""
        good = True

        if self.dataError:
            # there has been an error in an earlier
            # computation/compiling/loading of this feature
            actionRep = "E"
            good = False
        elif self.dataLoaded and (
            self.isConfig
            or (
                (not origTime or self.dataLoaded >= origTime)
                and (not binTime or self.dataLoaded >= binTime)
            )
        ):
            actionRep = "="  # loaded and up to date
        elif not origTime and not binTime:
            actionRep = "X"  # no source and no binary present
            good = False
        else:
            try:
                if not origTime:
                    actionRep = "b"
                    good = self._readDataBin(_withGc=_withGc)
                    if not good:
                        actionRep = "X"  # no source and no readable binary present
                elif not binTime or origTime > binTime:
                    actionRep = "C" if self.method else "T"
                    good = (
                        self._compute(metaOnly=metaOnly)
                        if self.method
                        else self._readTf(metaOnly=metaOnly)
                    )
                    if good:
                        if self.isConfig or metaOnly:
                            actionRep = "M"
                        else:
                            self._writeDataBin()
                else:
                    actionRep = "B"
                    good = True if self.method else self._readTf(metaOnly=True)
                    if good:
                        if self.isConfig or metaOnly:
                            actionRep = "M"
                        else:
                            good = self._readDataBin(_withGc=_withGc)
                            if not good:
                                actionRep = "C" if self.method else "T"
                                good = (
                                    self._compute(metaOnly=metaOnly)
                                    if self.method
                                    else self._readTf(metaOnly=metaOnly)
                                )
                                if good:
                                    self._writeDataBin()
            except MemoryError:
                console(MEM_MSG)
                good = False
            except Exception as e:
                console(f"{FATAL_MSG}: {e}")
                good = False
        if self.isConfig:
            self.cleanDataBin()
        if good:
            if actionRep != "=" and not (
                actionRep == "M" or (actionRep == "B" and self.method)
            ):
                pass
            info(
                msgFormat.format(actionRep, self.fileName, sourceRep),
                cache=1 if actionRep in "CT" else -1,
            )
        else:
            self.dataError = True
            error(msgFormat.format(actionRep, self.fileName, sourceRep))

        setSilent(wasSilent)
        indent(level=False)
        return good

    def unload(self):
        self.data = None
        self.dataLoaded = False

    def save(self, overwrite=False, nodeRanges=False, silent=SILENT_D):
        silent = silentConvert(silent)
        tmObj = self.tmObj
        isSilent = tmObj.isSilent
        setSilent = tmObj.setSilent

        wasSilent = isSilent()
        setSilent(silent)
        result = self._writeTf(overwrite=overwrite, nodeRanges=nodeRanges)
        setSilent(wasSilent)
        return result

    def _setDataType(self):
        if self.isConfig:
            return

        tmObj = self.tmObj
        error = tmObj.error
        fileName = self.fileName

        dataTypesStr = ", ".join(DATA_TYPES)
        if "valueType" in self.metaData:
            dataType = self.metaData["valueType"]
            if dataType not in DATA_TYPES:
                error(
                    f"{fileName}: Unknown @valueType: {dataType}. "
                    f"Should be one of {dataTypesStr}"
                )
                self.dataType = DATA_TYPES[0]
            else:
                self.dataType = dataType
        else:
            error(f"{fileName}: Missing @valueType. Should be one of {dataTypesStr}")
            self.dataType = DATA_TYPES[0]

    def _readTf(self, metaOnly=False):
        tmObj = self.tmObj
        error = tmObj.error
        fileName = self.fileName

        path = self.path
        if not fileExists(path):
            error(f'TF reading: feature file "{path}" does not exist')
            return False
        fh = fileOpen(path)
        i = 0
        self.metaData = {}
        self.isConfig = False
        for line in fh:
            i += 1
            if i == 1:
                text = line.rstrip()
                if text == "@edge":
                    self.isEdge = True
                elif text == "@node":
                    self.isEdge = False
                elif text == "@config":
                    self.isConfig = True
                else:
                    error(f"{fileName}: Line {i}: missing @node/@edge/@config")
                    fh.close()
                    return False
                continue
            text = line.rstrip("\n")
            if len(text) and text[0] == "@":
                if text == "@edgeValues":
                    self.edgeValues = True
                    continue
                fields = text[1:].split("=", 1)
                self.metaData[fields[0]] = fields[1] if len(fields) == 2 else None
                continue
            else:
                if text != "":
                    error(f"{fileName}: Line {i}: missing blank line after metadata")
                    fh.close()
                    return False
                else:
                    break
        self._setDataType()
        good = True
        if not metaOnly and not self.isConfig:
            good = self._readDataTf(fh, i)
        fh.close()
        return good

    def _readDataTf(self, fh, firstI):
        tmObj = self.tmObj
        error = tmObj.error
        fileName = self.fileName

        errors = collections.defaultdict(list)
        i = firstI
        implicit_node = 1
        data = {}
        isEdge = self.isEdge
        edgeValues = self.edgeValues
        normFields = 3 if isEdge and edgeValues else 2
        isNum = self.dataType == "int"
        for line in fh:
            i += 1
            fields = line.rstrip("\n").split("\t")
            lfields = len(fields)
            if lfields > normFields:
                errors["wrongFields"].append(i)
                continue
            if lfields == normFields:
                nodes = setFromSpec(fields[0])
                if isEdge:
                    if fields[1] == "":
                        errors["emptyNode2Spec"].append(i)
                        continue
                    nodes2 = setFromSpec(fields[1])
                if not isEdge or edgeValues:
                    valTf = fields[-1]
            else:
                if isEdge:
                    if edgeValues:
                        if lfields == normFields - 1:
                            nodes = {implicit_node}
                            nodes2 = setFromSpec(fields[0])
                            valTf = fields[-1]
                        elif lfields == normFields - 2:
                            nodes = {implicit_node}
                            if fields[0] == "":
                                errors["emptyNode2Spec"].append(i)
                                continue
                            nodes2 = setFromSpec(fields[0])
                            valTf = ""
                        else:
                            nodes = {implicit_node}
                            valTf = ""
                            errors["emptyNode2Spec"].append(i)
                            continue
                    else:
                        if lfields == normFields - 1:
                            nodes = {implicit_node}
                            if fields[0] == "":
                                errors["emptyNode2Spec"].append(i)
                                continue
                            nodes2 = setFromSpec(fields[0])
                        else:
                            nodes = {implicit_node}
                            errors["emptyNode2Spec"].append(i)
                            continue
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
                    else None if isNum else "" if valTf == "" else valueFromTf(valTf)
                )
            if isEdge:
                for n in nodes:
                    for m in nodes2:
                        if not edgeValues:
                            data.setdefault(n, set()).add(m)
                        else:
                            data.setdefault(n, {})[
                                m
                            ] = value  # even if the value is None
            else:
                for n in nodes:
                    if value is not None:
                        data[n] = value
        for kind in errors:
            lnk = len(errors[kind])
            error(
                "{}: {} in lines {}".format(
                    fileName,
                    kind,
                    ",".join(str(ln) for ln in errors[kind][0:ERROR_CUTOFF]),
                )
            )
            if lnk > ERROR_CUTOFF:
                error(f"\t and {lnk - ERROR_CUTOFF} more cases", tm=False)

        self.data = data

        if not errors:
            if self.fileName == OTYPE:
                slotType = data[1]
                otype = []
                maxSlot = 1
                for n in sorted(data):
                    if data[n] == slotType:
                        maxSlot = n
                        continue
                    otype.append(data[n])
                maxNode = len(data)
                self.data = (tuple(otype), maxSlot, maxNode, slotType)
            elif self.fileName == OSLOTS:
                nodeList = sorted(data)
                maxSlot = (
                    nodeList[0] - 1
                )  # vital assumption: all non slot nodes are linked
                maxNode = nodeList[-1]
                nodeRange = maxNode - maxSlot
                nodesMapped = len(nodeList)
                if nodeRange > nodesMapped:
                    error(
                        f"ERROR: {OSLOTS} fails to map {nodeRange - nodesMapped} nodes"
                    )
                    errors = True
                elif nodeRange < nodesMapped:
                    # cannot happen because nodeList is a list of distinct keys
                    # so the min and max values of these keys must differ at least as much
                    # is the number of those keys
                    pass
                oslots = []
                for n in nodeList:
                    oslots.append(array.array("I", sorted(data[n])))
                    # oslots.append(tuple(sorted(data[n])))
                self.data = (tuple(oslots), maxSlot, maxNode)
            elif isEdge:
                seen = {}
                datax = {}
                if edgeValues:
                    for n, ms in data.items():
                        msx = {}
                        for m, v in ms.items():
                            if v not in seen:
                                seen[v] = v
                            msx[m] = seen[v]
                        datax[n] = msx
                else:
                    for n, ms in data.items():
                        msx = frozenset(ms)
                        if msx not in seen:
                            seen[msx] = msx
                        datax[n] = seen[msx]
                self.data = datax
            else:
                seen = {}
                datax = {}
                for n, ms in data.items():
                    if ms not in seen:
                        seen[ms] = ms
                    datax[n] = seen[ms]
                self.data = datax

        return not errors

    def _compute(self, metaOnly=False):
        tmObj = self.tmObj
        isSilent = tmObj.isSilent
        if metaOnly:
            return True

        good = True
        for feature in self.dependencies:
            if isinstance(feature, Data):
                if not feature.load(silent=isSilent()):
                    good = False
        if not good:
            return False

        def info(msg, tm=True):
            tmObj.info(cmpFormat.format(msg), tm=tm, cache=-1)

        def error(msg, tm=True):
            tmObj.error(cmpFormat.format(msg), tm=tm)

        cmpFormat = f"c {self.fileName:<20} {{}}"
        tmObj.indent(level=2, reset=True)

        self.data = self.method(
            info,
            error,
            *[
                (
                    (dep.metaData if dep.fileName == OTEXT else dep.data)
                    if isinstance(dep, Data)
                    else dep
                )
                for dep in self.dependencies
            ],
        )
        good = self.data is not None
        if good:
            self.dataLoaded = time.time()
        return good

    def _writeTf(
        self,
        dirName=None,
        fileName=None,
        overwrite=True,
        extension=None,
        metaOnly=False,
        nodeRanges=False,
    ):
        tmObj = self.tmObj
        indent = tmObj.indent
        info = tmObj.info
        error = tmObj.error

        indent(level=1, reset=True)
        metaOnly = metaOnly or self.isConfig

        dirName = dirName or self.dirName
        fileName = fileName or self.fileName
        extension = extension or self.extension

        dirMake(dirName)

        fpath = f"{dirName}/{fileName}{extension}"
        if fpath == self.path:
            if fileExists(fpath):
                if not overwrite:
                    error(
                        f'Feature file "{fpath}" already exists, feature will not be written'
                    )
                    return False
        try:
            fh = fileOpen(fpath, mode="w")
        except Exception:
            error(f'Cannot write to feature file "{fpath}"')
            return False
        fh.write(
            "@{}\n".format(
                "config" if self.isConfig else "edge" if self.isEdge else "node"
            )
        )
        if self.edgeValues:
            fh.write("@edgeValues\n")
        for meta in sorted(self.metaData):
            fh.write(f"@{meta}={self.metaData[meta]}\n")
        fh.write("@writtenBy=Text-Fabric\n")
        fh.write(
            "@dateWritten={}\n".format(
                utcnow().replace(microsecond=0).isoformat() + "Z"
            )
        )
        fh.write("\n")
        self._setDataType()
        good = True
        if not metaOnly:
            good = self._writeDataTf(fh, nodeRanges=nodeRanges)
        fh.close()
        msgFormat = "{:<1} {:<20} to {}"
        if good:
            info(msgFormat.format("M" if metaOnly else "T", fileName, dirName))
        else:
            error(msgFormat.format("M" if metaOnly else "T", fileName, dirName))
        return good

    def _writeDataTf(self, fh, nodeRanges=False):
        tmObj = self.tmObj
        error = tmObj.error
        fileName = self.fileName

        data = self.data
        if type(data) is tuple:
            # just in case the WARP data is present as a sequence and not a dict
            # in case it has been loaded from a binary representation
            fName = self.fileName
            if fName not in {OTYPE, OSLOTS}:
                error(f"{fileName}: Data type tuple not suitable for non-WARP feature")
                return False
            maxSlot = data[2] if fName == OTYPE else data[1]
            slotType = data[1] if fName == OTYPE else None
            data = data[0]
            if fName == OTYPE:
                data = dict(((k, slotType) for k in range(1, maxSlot + 1)))
                data.update(
                    dict(((k + 1 + maxSlot, data[k]) for k in range(len(data))))
                )
            elif self.fileName == OSLOTS:
                data = dict(((k + 1 + maxSlot, data[k]) for k in range(len(data))))
        edgeValues = self.edgeValues
        if self.isEdge:
            implicitNode = 1
            for n in sorted(data):
                thisData = data[n]
                sets = {}
                if edgeValues:
                    for m in thisData:
                        sets.setdefault(thisData[m], set()).add(m)
                    for value, mset in sorted(sets.items()):
                        nodeSpec2 = specFromRanges(rangesFromSet(mset))
                        nodeSpec = "" if n == implicitNode else n
                        implicitNode = n + 1
                        tfValue = value if value is None else tfFromValue(value)
                        if tfValue is None:
                            fh.write(
                                "{}{}{}\n".format(
                                    nodeSpec,
                                    "\t" if nodeSpec else "",
                                    nodeSpec2,
                                )
                            )
                        else:
                            fh.write(
                                "{}{}{}\t{}\n".format(
                                    nodeSpec,
                                    "\t" if nodeSpec else "",
                                    nodeSpec2,
                                    tfValue,
                                )
                            )
                else:
                    nodeSpec2 = specFromRanges(rangesFromSet(thisData))
                    nodeSpec = "" if n == implicitNode else n
                    implicitNode = n + 1
                    fh.write(
                        "{}{}{}\n".format(nodeSpec, "\t" if nodeSpec else "", nodeSpec2)
                    )
        else:
            sets = {}
            if nodeRanges:
                for n in sorted(data):
                    sets.setdefault(data[n], []).append(n)
                implicitNode = 1
                for value, nset in sorted(
                    sets.items(), key=lambda x: (x[1][0], x[1][-1])
                ):
                    if len(nset) == 1 and nset[0] == implicitNode:
                        nodeSpec = ""
                    else:
                        nodeSpec = specFromRanges(rangesFromSet(nset))
                    implicitNode = nset[-1]
                    tfValue = value if value is None else tfFromValue(value)
                    if tfValue is not None:
                        fh.write(
                            "{}{}{}\n".format(
                                nodeSpec,
                                "\t" if nodeSpec else "",
                                tfValue,
                            )
                        )
            else:
                implicitNode = 1
                for n in sorted(data):
                    nodeSpec = "" if n == implicitNode else n
                    value = data[n]
                    tfValue = value if value is None else tfFromValue(value)
                    if tfValue is not None:
                        implicitNode = n + 1
                        fh.write(
                            "{}{}{}\n".format(
                                nodeSpec,
                                "\t" if nodeSpec else "",
                                tfValue,
                            )
                        )
        return True

    def _readDataBin(self, _withGc=True):
        """Read binary feature data.
        _withGc: boolean, optional True
            If False, it disables the Python garbage collector before
            loading features. Used to experiment with performance.
        """

        tmObj = self.tmObj
        error = tmObj.error

        if not fileExists(self.binPath):
            error(f'TF reading: feature file "{self.binPath}" does not exist')
            return False
        if not _withGc:
            gc.disable()

        good = True

        try:
            with gzip.open(self.binPath, mode="rb") as f:
                self.data = pickle.load(f)
            good = True
        except Exception:
            good = False
        finally:
            if not _withGc:
                gc.enable()
        self.dataLoaded = time.time()
        return good

    def cleanDataBin(self):
        fileRemove(self.binPath)

    def _writeDataBin(self):
        tmObj = self.tmObj
        error = tmObj.error

        good = True
        dirMake(self.binDir)

        try:
            with gzip.open(self.binPath, mode="wb", compresslevel=GZIP_LEVEL) as f:
                # pickle.dump(self.data, f, protocol=PICKLE_PROTOCOL)
                f.write(optimize(pickle.dumps(self.data, protocol=PICKLE_PROTOCOL)))
        except Exception as e:
            error(f'Cannot write to file "{self.binPath}" because: {str(e)}')
            self.cleanDataBin()
            good = False
        self.dataLoaded = time.time()
        return good

    def _getModified(self, bin=False):
        if bin:
            return mTime(self.binPath) if fileExists(self.binPath) else None
        else:
            if self.method:
                depsInfo = [
                    dep._getModified()
                    for dep in self.dependencies
                    if isinstance(dep, Data)
                ]
                depsModifieds = [d for d in depsInfo if d is not None]
                depsModified = None if len(depsModifieds) == 0 else max(depsModifieds)
                if depsModified is not None:
                    return depsModified
                elif fileExists(self.binPath):
                    return mTime(self.binPath)
                else:
                    return None
            else:
                if fileExists(self.path):
                    return mTime(self.path)
                elif fileExists(self.binPath):
                    return mTime(self.binPath)
                else:
                    return None
