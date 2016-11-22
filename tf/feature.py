import os,sys,pickle,json,gzip,collections,time
from datetime import datetime
from .helpers import *

ERROR_CUTOFF = 20
GZIP_LEVEL = 2
PICKLE_PROTOCOL = 4

class Feature(object):
    def __init__(self, path, edgeValues=False, data=None, isEdge=None, metaData={}):
        (dirName, baseName) = os.path.split(path)
        (fileName, extension) = os.path.splitext(baseName)
        self.path = path
        self.dirName = dirName
        self.fileName = fileName
        self.extension = extension
        self.binDir = '{}/.tf'.format(dirName)
        self.binPath = '{}/{}.tfx'.format(self.binDir, self.fileName)
        self.edgeValues = edgeValues
        self.data = data
        self.isEdge = isEdge
        self.metaData = metaData
        self.data = None
        self.dataName = None
        self.dataLoaded = False

    def load(self, asName=None):
        self.dataName = asName or self.fileName
        origPath = self.path
        binPath = self.binPath
        origExists = os.path.exists(origPath)
        binExists = os.path.exists(binPath)
        origTime = os.path.getmtime(origPath) if origExists else None
        binTime = os.path.getmtime(binPath) if binExists else None
        if self.dataLoaded and (not origExists or self.dataLoaded >= origTime) and (not binExists or self.dataLoaded >= binTime):
            error('data already loaded and up to date')
            return True
        if not origExists and not binExists:
            error('TF loading: feature "{}" has no source ({}) and no binary ({}) data'.format(self.fileName, origPath, binPath))
            return False
        if not origExists:
            good = self._readDataBin()
        elif not binExists or origTime > binTime:
            good = self._readTf()
            if good: self._writeDataBin()
        else:
            good = self._readTf(metaOnly=True)
            if good: good = self._readDataBin()
        if good:
            self.dataLoaded = time.time() 
        return good

    def unload(self):
        self.data = None
        self.dataLoaded = False
        self.dataName = None

    def _readTf(self, metaOnly=False):
        path = self.path
        if not os.path.exists(path):
            error('TF reading: feature file "{}" does not exist'.format(path))
            return False
        fh = open(path)
        i = 0
        self.metaData = {}
        for line in fh:
            i += 1
            if i == 1:
                text = line.rstrip()
                if text == '@edge': self.isEdge = True
                elif text == '@node': self.isEdge = False
                else:
                    error('missing @node/@edge', line=i)
                    fh.close()
                    return False
                continue
            text = line.rstrip('\n')
            if len(text) and text[0] == '@':
                fields = text.rstrip()[1:].split('=', 1)
                self.metaData[fields[0]] = fields[1] if len(fields) == 2 else None
                continue
            else:
                if text != '':
                    error('missing blank line after metadata', line=i)
                    fh.close()
                    return False
                else:
                    break
        good = True
        if not metaOnly:
            good = self._readDataTf(fh, i)
        fh.close()
        return good
        
    def _readDataTf(self, fh, firstI):
        wrongFields = []
        first = True
        i = firstI
        implicit_node = 0
        data = {}
        isEdge = self.isEdge
        edgeValues = self.edgeValues
        normFields = 3 if isEdge else 2
        for line in fh:
            i += 1
            fields = line.rstrip('\n').split('\t')
            lfields = len(fields)
            if lfields > normFields: 
                wrongFields.append(i)
                continue
            if lfields == normFields:
                nodes = setFromSpec(fields[0])
                if isEdge:
                    nodes2 = setFromSpec(fields[1])
                if not isEdge or edgeValues:
                    valTf = fields[-1]
            else:
                if isEdge:
                    if edgeValues:
                        valTf = ''
                    if lfields == normFields - 1:
                        nodes = setFromSpec(fields[0])
                        nodes2 = setFromSpec(fields[1])
                    elif lfields == normFields - 2:
                        nodes = {implicit_node}
                        nodes2 = setFromSpec(fields[0])
                    else:
                        nodes = {implicit_node}
                        nodes2 = {implicit_node}
                else:
                    nodes = {implicit_node}
                    if lfields == 1:
                        valTf = fields[0]
                    else:
                        valTf = ''
            implicit_node = max(nodes) + 1
            if not isEdge or edgeValues:
                value = '' if valTf == '' else valueFromTf(valTf)
            if isEdge:
                for n in nodes:
                    for m in nodes2:
                        if not edgeValues:
                            data.setdefault(n, set()).add(m)
                        else:
                            data.setdefault(n, {})[m] = value
            else:
                for n in nodes: data[n] = value
        if wrongFields:
            for ln in wrongFields[0:ERROR_CUTOFF]:
                error('wrong number of fields', line=ln)
            if len(wrongFields) > ERROR_CUTOFF:
                error('more cases', line=ln - ERROR_CUTOFF)
            return False
        self.data = data
        return True

    def _writeTf(self, dirName=None, fileName=None, extension=None, metaOnly=False, nodeRanges=False):
        dirName = dirName or self.dirName
        fileName = fileName or self.fileName
        extension = extension or self.extension
        fpath = '{}/{}{}'.format(dirName, fileName, extension)
        if fpath == self.path:
            if os.path.exists(fpath):
                error('Feature file "{}" already exists, feature will not be written'.format(fpath))
                return False
        try:
            fh = open(fpath, 'w')
        except:
            error('Cannot write to feature file "{}"'.format(fpath))
            return False
        fh.write('@{}\n'.format('edge' if self.isEdge else 'node'))
        for meta in sorted(self.metaData):
            fh.write('@{}={}\n'.format(meta, self.metaData[meta]))
        fh.write('@writtenBy=Text-Fabric\n')
        fh.write('@dateWritten={}\n'.format(datetime.utcnow().replace(microsecond=0).isoformat()+'Z'))
        fh.write('\n')
        good = True
        if not metaOnly:
            good = self._writeDataTf(fh, nodeRanges=nodeRanges)
        fh.close()
        return good

    def _writeDataTf(self, fh, nodeRanges=False):
        data = self.data
        edgeValues = self.edgeValues
        if self.isEdge:
            implicitNode = 0
            for n in sorted(data):
                thisData = data[n]
                sets = {}
                if edgeValues:
                    for m in thisData:
                        sets.setdefault(thisData[m], set()).add(m)
                    for (value, mset) in sorted(sets.items()):
                        nodeSpec2 = specFromRanges(rangesFromSet(mset))
                        nodeSpec = '' if n == implicitNode else n
                        implicitNode = n + 1
                        fh.write('{}{}{}\t{}\n'.format(nodeSpec, '\t' if nodeSpec else '', nodeSpec2, tfFromValue(value)))
                else:
                    nodeSpec2 = specFromRanges(rangesFromSet(thisData))
                    nodeSpec = '' if n == implicitNode else n
                    implicitNode = n + 1
                    fh.write('{}{}{}\n'.format(nodeSpec, '\t' if nodeSpec else '', nodeSpec2))
        else:
            sets = {}
            if nodeRanges:
                for n in sorted(data):
                    sets.setdefault(data[n], []).append(n)
                implicitNode = 0
                for (value, nset) in sorted(sets.items(), key=lambda x: (x[1][0], x[1][-1])):
                    if len(nset) == 1 and nset[0] == implicitNode:
                        nodeSpec = ''
                    else:
                        nodeSpec = specFromRanges(rangesFromSet(nset))
                    implicitNode = nset[-1]
                    fh.write('{}{}{}\n'.format(nodeSpec, '\t' if nodeSpec else '', tfFromValue(value)))
            else:
                implicitNode = 0
                for n in sorted(data):
                    nodeSpec = '' if n == implicitNode else n
                    implicitNode = n + 1
                    fh.write('{}{}{}\n'.format(nodeSpec, '\t' if nodeSpec else '', tfFromValue(data[n])))
        return True

    def _readDataBin(self):
        if not os.path.exists:
            error('TF reading: feature file "{}" does not exist'.format(path))
            return False
        with gzip.open(self.binPath, "rb") as f: self.data = pickle.load(f)
        return True

    def _writeDataBin(self):
        good = True
        if not os.path.exists(self.binDir):
            try:
                os.makedirs(self.binDir, exist_ok=True)
            except:
                error('Cannot create directory "{}"'.format(self.binDir))
                good = False
        if not good: return False
        try:
            with gzip.open(self.binPath, "wb", compresslevel=GZIP_LEVEL) as f: pickle.dump(self.data, f, protocol=PICKLE_PROTOCOL)
        except:
            error('Cannot write to file "{}"'.format(self.binPath))
            good = False
        return True

