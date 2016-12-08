import os
from .data import GRID
from .helpers import *

class MQL(object):
    def __init__(self, mqlDir, mqlName, tfFeatures, tm):
        self.mqlDir = mqlDir
        cleanDb = cleanName(mqlName)
        if cleanDb != mqlName:
            self.tm.error('db name "{}" => "{}"'.format(mqlName, cleanDb))
        self.mqlName = cleanDb
        self.tfFeatures = tfFeatures
        self.tm = tm
        self._check()

    def write(self):
        if not self.good: return
        if not os.path.exists(self.mqlDir):
            try:
                os.makedirs(self.mqlDir, exist_ok=True)
            except:
                self.tm.error('Cannot create directory "{}"'.format(self.mqlDir))
                self.good = False
                return
        mqlPath = '{}/{}.mql'.format(self.mqlDir, self.mqlName)
        try:
            fm = open(mqlPath, 'w', encoding='utf8')
        except:
            self.tm.error('Could not write to {}'.format(mqlPath))
            self.good = False
            return
        self.fm = fm
        self._writeStartDb()
        self._writeTypes()
        self._writeDataAll()
        self._writeEndDb()
        self.tm.indent(level=0)
        self.tm.info('Done')

    def _check(self):
        self.tm.info('Checking features of dataset {}'.format(self.mqlName))
        self.features = {}
        self.featureList = []
        self.tm.indent(level=1)
        for (f, fo) in sorted(self.tfFeatures.items()):
            if fo.method != None or f in GRID: continue
            fo.load(metaOnly=True)
            if fo.isConfig: continue
            cleanF = cleanName(f)
            if cleanF != f:
                self.tm.error('feature "{}" => "{}"'.format(f, cleanF))
            self.featureList.append(cleanF)
            self.features[cleanF] = fo
        good = True
        for feat in (GRID[0], GRID[1], '__levels__'):
            if feat not in self.tfFeatures:
                self.tm.error('{} feature {} is missing from data set'.format(
                    'Grid' if feat in GRID else 'Computed' if feat.startswith('__') else 'Data',
                    feat,
                ))
                good = False
            else:
                fObj = self.tfFeatures[feat]
                if not fObj.load():
                    good = False
        self.tm.indent(level=0)
        if (not good):
            self.tm.error('Export to MQL aborted')
        else:
            self.tm.info('{} features to export to MQL ...'.format(len(self.featureList)))
        self.good = good

    def _writeStartDb(self):
        self.fm.write('''
CREATE DATABASE '{name}'
GO
USE DATABASE '{name}'
GO
'''.format(name=self.mqlName))


    def _writeEndDb(self):
        self.fm.write('''
VACUUM DATABASE ANALYZE
GO
''')
        self.fm.close()

    def _writeTypes(self):
        def valInt(n): return str(n)
        def valStr(s):
            if "'" in s:
                return '"{}"'.format(s.replace('"', '\\"'))
            else:
                return "'{}'".format(s)
        def valIds(ids): return '({})'.format(','.join(str(i) for i in ids))

        self.levels = self.tfFeatures['__levels__'].data[::-1]
        self.tm.info('Loading {} features'.format(len(self.featureList)))
        for ft in self.featureList:
            fObj = self.features[ft]
            fObj.load()

        self.tm.indent(level=0)
        self.tm.info('Mapping {} features onto {} object types'.format(
            len(self.featureList), len(self.levels),
        ))
        otypeSupport = {}
        for (otype, av, start, end) in self.levels:
            cleanOtype = cleanName(otype)
            if cleanOtype != otype:
                self.tm.error('otype "{}" => "{}"'.format(otype, cleanOtype))
            otypeSupport[cleanOtype] = set(range(start, end+1))

        self.otypes = {}
        self.featureTypes = {}
        self.featureMethods = {}
        for ft in self.featureList:
            fObj = self.features[ft]
            if fObj.isEdge:
                dataType = 'LIST OF id_d'
                method = valIds
            else:
                if fObj.dataType == 'str':
                    dataType = 'string DEFAULT ""'
                    method = valStr
                elif fObj.dataType == 'int':
                    dataType = 'integer DEFAULT 0'
                    method = valInt
                else:
                    dataType = 'string DEFAULT ""'
                    method = valStr
            self.featureTypes[ft] = dataType
            self.featureMethods[ft] = method

            support = set(fObj.data.keys())
            for otype in otypeSupport:
                if len(support & otypeSupport[otype]):
                    self.otypes.setdefault(otype, []).append(ft)

        for otype in (cleanName(x[0]) for x in self.levels):
            self._writeType(otype)

    def _writeType(self, otype):
        self.fm.write('''
CREATE OBJECT TYPE
[{}
'''.format(otype))
        for ft in self.otypes[otype]:
            self.fm.write('  {}:{};\n'.format(ft, self.featureTypes[ft]))
        self.fm.write('''
]
GO
''')

    def _writeDataAll(self):
        self.tm.info('Writing {} features as data in {} object types'.format(
            len(self.featureList), len(self.levels),
        ))
        self.oslots = self.tfFeatures[GRID[1]].data
        for (otype, av, start, end) in self.levels:
            self._writeData(otype, start, end)

    def _writeData(self, otype, start, end):
        tm = self.tm
        fm = self.fm
        tm.indent(level=1, reset=True)
        tm.info('{} data ...'.format(otype))
        oslots = self.oslots
        maxSlot = oslots[-1]
        oFeats = self.otypes[otype]
        features = self.features
        featureTypes = self.featureTypes
        featureMethods = self.featureMethods
        fm.write('''
DROP INDEXES ON OBJECT TYPE[{o}]
GO
CREATE OBJECTS
WITH OBJECT TYPE[{o}]
'''.format(o=otype))
        curSize = 0
        LIMIT = 50000
        t = 0
        j = 0
        tm.indent(level=2, reset=True)
        for n in range(start, end + 1):
            oMql = '''
CREATE OBJECT
FROM MONADS= {{ {m} }} 
WITH ID_D={i} [
'''.format(
    m=n if n <= maxSlot else specFromRanges(rangesFromList(oslots[n-maxSlot-1])),
    i=n,
)
            for ft in oFeats:
                tp = featureTypes[ft]
                method = featureMethods[ft]
                fMap = features[ft].data
                if n in fMap:
                    oMql += '{}:={};\n'.format(ft, method(fMap[n]))
            oMql += '''
]
'''
            fm.write(oMql)
            curSize += len(bytes(oMql, encoding='utf8'))
            t += 1
            j += 1
            if j == LIMIT:
                fm.write('''
GO
CREATE OBJECTS
WITH OBJECT TYPE[{o}]
'''.format(o=otype))
                tm.info('batch of size {:>20} with {:>7} of {:>7} {}s'.format(nbytes(curSize), j, t, otype))
                j = 0
                curSize = 0

        tm.info('batch of size {:>20} with {:>7} of {:>7} {}s'.format(nbytes(curSize), j, t, otype))
        fm.write('''
GO
CREATE INDEXES ON OBJECT TYPE[{o}]
GO
'''.format(o=otype))

        tm.indent(level=1)
        tm.info('{} data: {} objects'.format(otype, t))
