from .data import GRID
from .helpers import *

def writeMQL(mqlDir, mqlName, features, tm):
    tm.info('Exporting dataset {} to {}'.format(mqlName, mqlDir))
    featureList = []
    for (f, fo) in sorted(features.items()):
        if fo.method != None or f in GRID: continue
        fo.load(metaOnly=True)
        if fo.isConfig: continue
        featureList.append(f)

    if not checkForExport(features, tm): return False
    tm.indent(level=0)

    tm.info('Exporting {} features to MQL ...'.format(len(featureList)))
    mqlPath = '{}/{}.mql'.format(mqlDir, mqlName)
    try:
        fm = open(mqlPath, 'w', encoding='utf8')
    except:
        tm.error('Could not write to {}'.format(mqlPath))
        return False
    good = True
    fm.write('''
CREATE DATABASE '{name}'
GO
USE DATABASE '{name}'
GO
'''.format(name=mqlName))

    (levels, otypes, featureTypes) = writeObjectTypes(featureList, features, tm, fm)
    writeObjectData(featureList, features, levels, otypes, featureTypes, tm, fm)

    fm.write('''
VACUUM DATABASE ANALYZE
GO
''')

    fm.close()
    tm.indent(level=0)
    tm.info('Done')
    return good

def checkForExport(features, tm):
    good = True
    for feat in (GRID[0], GRID[1], '__levels__'):
        if feat not in features:
            tm.error('{} feature {} is missing from data set'.format(
                'Grid' if feat in GRID else 'Computed' if feat.startswith('__') else 'Data',
                feat,
            ))
            good = False
        else:
            fObj = features[feat]
            if not fObj.load():
                good = False
    return good

def writeObjectTypes(featureList, features, tm, fm):
    levels = features['__levels__'].data[::-1]
    tm.info('Loading {} features'.format(len(featureList)))
    for ft in featureList:
        fObj = features[ft]
        fObj.load()
    tm.indent(level=0)
    tm.info('Mapping {} features onto {} object types'.format(len(featureList), len(levels)))
    otypeSupport = {}
    for (otype, av, start, end) in levels:
        otypeSupport[otype] = set(range(start, end+1))
    otypes = {}
    featureTypes = {}
    for ft in featureList:
        fObj = features[ft]
        if fObj.isEdge:
            dataType = 'LIST OF id_d'
        else:
            if fObj.dataType == 'str':
                dataType = 'string DEFAULT ""'
            elif fObj.dataType == 'int':
                dataType = 'integer DEFAULT 0'
            else:
                dataType = 'string DEFAULT ""'
        featureTypes[ft] = dataType

        support = set(fObj.data.keys())
        for (otype, av, start, end) in levels:
            if len(support & otypeSupport[otype]):
                otypes.setdefault(otype, []).append(ft)

    for (otype, av, start, end) in levels:
        writeObjectType(otype, otypes[otype], featureTypes, fm)
    return (levels, otypes, featureTypes)

def writeObjectType(otype, oFeats, featureTypes, fm):
    fm.write('''
CREATE OBJECT TYPE
[{}
iam:string DEFAULT "";
'''.format(otype))
    for ft in oFeats:
        fm.write('  {}:{};\n'.format(cleanName(ft), featureTypes[ft]))
    fm.write('''
]
GO
''')

def writeObjectData(featureList, features, levels, otypes, featureTypes, tm, fm):
    tm.info('Writing {} features as data in {} object types'.format(len(featureList), len(levels)))
    oslots = features[GRID[1]].data
    for (otype, av, start, end) in levels:
        writeObjectDataLv(otype, start, end, features, otypes[otype], featureTypes, oslots, tm, fm)

def writeObjectDataLv(otype, start, end, features, oFeats, featureTypes, oslots, tm, fm):
    tm.indent(level=1, reset=True)
    tm.info('{} data ...'.format(otype))
    maxSlot = oslots[-1]
    fm.write('''
DROP INDEXES ON OBJECT TYPE[{o}]
GO
CREATE OBJECTS
WITH OBJECT TYPE[{o}]
'''.format(o=otype))
    LIMIT = 50000
    t = 0
    j = 0
    tm.indent(level=2)
    for n in range(start, end + 1):
        fm.write('''
CREATE OBJECT
FROM MONADS= {{ {m} }} 
WITH ID_D={i} [
iam:="x";
'''.format(
    m=n+1 if n <= maxSlot else specFromRanges(plusOne(rangesFromList(oslots[n-maxSlot-1]))),
    i=n+1,
))
        fm.write('''
]
''')
        t += 1
        j += 1
        if j == LIMIT:
            fm.write('''
GO
CREATE OBJECTS
WITH OBJECT TYPE[{o}]
'''.format(o=otype))
            j = 0
            tm.info('{} objects'.format(t))
    tm.indent(level=1)
    tm.info('{} data: {} objects'.format(otype, t))

    fm.write('''
GO
CREATE INDEXES ON OBJECT TYPE[{o}]
GO
'''.format(o=otype))
