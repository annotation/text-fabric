import os,sys,re,collections
from tf.fabric import Fabric

sourceDir = os.path.expanduser('~/github/etcbc-data')
mqlFile = '{}/{}'.format(sourceDir, 'synvar.mql')
targetDir = os.path.expanduser('~/github/text-fabric-data')
tfDir = '{}/hebrew/extrabiblical'.format(targetDir)
if not os.path.exists(tfDir): os.makedirs(tfDir)

TF = Fabric(tfDir)

slotType = 'word'

enums = dict()
objectTypes = dict()
tables = dict()
curMonads = None
curId = None
edgeF = dict()
nodeF = dict()

def setFromSpec(spec):
    covered = set()
    for r_str in spec.split(','):
        bounds = r_str.split('-')
        if len(bounds) == 1:
            covered.add(int(r_str))
        else:
            b = int(bounds[0])
            e = int(bounds[1])
            if (e < b): (b, e) = (e, b)
            for n in range(b, e+1): covered.add(n)
    return covered

def parseMql(fh):
    curEnum = None
    curObjectType = None
    curTable = None
    curObject = None

    print('Parsing mql dump ...')

    for (ln, line) in enumerate(fh):
        if line.startswith('CREATE OBJECTS WITH OBJECT TYPE'):
            comps = line.strip(']\n').split('[', 1)
            curTable = comps[1]
            curObject = None
            if not curTable in tables:
                tables[curTable] = dict()
        elif curEnum != None:
            if line.startswith('}'):
                curEnum = None
                continue
            comps = line.rstrip(',\n').split('=', 1)
            comp = comps[0].strip()
            words = comp.split()
            if words[0] == 'DEFAULT':
                enums[curEnum]['default'] = words[1]
                value = words[1]
            else:
                value = words[0]
            enums[curEnum]['values'].append(value)
        elif curObjectType != None:
            if line.startswith(']'):
                curObjectType = None
                continue
            if curObjectType == True:
                if line.startswith('['):
                    curObjectType = line[1:-1]
                    objectTypes[curObjectType] = dict()
                    continue
            comps = line.rstrip(';\n').split(':', 1)
            feature = comps[0].strip()
            fInfo = comps[1].strip()
            default = enums.get(fInfo, {}).get('default', None)
            ftype = 'str' if fInfo in enums else\
                    'int' if fInfo == 'integer' else\
                    'str' if fInfo.startswith('string') else\
                    'str' if fInfo.startswith('ascii') else\
                    'int' if fInfo == 'id_d' else\
                    'str'
            if fInfo == 'id_d':
                edgeF.setdefault(curObjectType, set()).add(feature)
            else:
                nodeF.setdefault(curObjectType, set()).add(feature)

            objectTypes[curObjectType][feature] = (ftype, default)
        elif curTable != None:
            if curObject != None:
                if line.startswith(']'):
                    objectType = objectTypes[curTable]
                    for (feature, (ftype, default)) in objectType.items():
                        if feature not in curObject['feats'] and default != None:
                            curObject['feats'][feature] = default
                    tables[curTable][curId] = curObject
                    curObject = None
                    continue
                elif line.startswith('['):
                    continue
                elif line.startswith('FROM MONADS'):
                    comps = line.rstrip('}\n').split('{', 1)
                    curObject['monads'] = setFromSpec(comps[1])
                elif line.startswith('WITH ID_D'):
                    comps = line.rstrip('\n').split('=', 1)
                    curId = int(comps[1])
                elif line.startswith('GO'):
                    continue
                elif line.strip() == '':
                    continue
                else:
                    comps = line.rstrip(';\n').split('=', 1)
                    feature = comps[0].strip()[0:-1]
                    if len(comps) != 2:
                        print(ln, line, comps)
                        break
                    value = comps[1].strip('"')
                    curObject['feats'][feature] = value
            else:
                if line.startswith('CREATE OBJECT'):
                    curObject = dict(feats=dict(), monads=None)
                    curId = None
        else:
            if line.startswith('CREATE ENUMERATION'):
                words = line.split()
                curEnum = words[2]
                enums[curEnum] = dict(default=None, values=[])
            elif line.startswith('CREATE OBJECT TYPE'):
                curObjectType = True
    print('{} lines parsed'.format(ln))
    for table in tables:
        print('{} objects of type {}'.format(len(tables[table]), table))

def tfFromData():
    tableOrder = [slotType]+[t for t in tables if t != slotType]

    nodeFromIdd = dict()
    iddFromNode = dict()

    nodeFeatures = dict()
    edgeFeatures = dict()
    metaData = dict()
    metaData = {
        '': dict(
            createdBy='Martijn Naaijer and Dirk Roorda',
        ),
        'otext': {
            'sectionFeatures': 'book,chapter,verse',
            'sectionTypes': 'book,chapter,verse',
            'fmt:text-orig-full': '{g_word_utf8}{g_suffix_utf8}',
            'fmt:text-trans-full': '{g_word}{g_suffix}',
            'fmt:text-trans-plain': '{g_cons}{g_suffix}',
            'fmt:lex-orig-full': '{g_lex_utf8}{g_suffix_utf8}',
            'fmt:lex-trans-full': '{lex_utf8}{g_suffix}',
        },
        'book@en': {
            'valueType': 'str',
            'language': 'English',
            'languageCode': 'en',
            'languageEnglish': 'english',
        },
    }

    print('Making TF data ...')

    print('Monad - idd mapping ...')
    otype = dict()
    for idd in tables[slotType]:
        monad = list(tables[slotType][idd]['monads'])[0]
        nodeFromIdd[idd] = monad
        iddFromNode[monad] = idd
        otype[monad] = slotType

    maxSlot = max(nodeFromIdd.values())
    print('maxSlot={}'.format(maxSlot))

    print('Node mapping and otype ...')
    node = maxSlot
    for t in tableOrder[1:]:
        for idd in sorted(tables[t]):
            node += 1
            nodeFromIdd[idd] = node
            iddFromNode[node] = idd
            otype[node] = t

    nodeFeatures['otype'] = otype
    metaData['otype'] = dict(
        valueType='str',
    )

    print('oslots ...')
    oslots = dict()
    for t in tableOrder[1:]:
        for idd in tables[t]:
            node = nodeFromIdd[idd]
            monads = tables[t][idd]['monads']
            oslots[node] = monads
    edgeFeatures['oslots'] = oslots
    metaData['oslots'] = dict(
        valueType='str',
    )

    print('metadata ...')
    for t in nodeF:
        for f in nodeF[t]:
            ftype = objectTypes[t][f][0]
            metaData.setdefault(f, {})['valueType'] = ftype
    for t in edgeF:
        for f in edgeF[t]:
            metaData.setdefault(f, {})['valueType'] = 'str'

    print('features ...')
    for t in tableOrder:
        for idd in tables[t]:
            node = nodeFromIdd[idd]
            features = tables[t][idd]['feats']
            for (f, v) in features.items():
                isEdge = f in edgeF.get(t, set())
                if isEdge:
                    if v != 'NIL':
                        edgeFeatures.setdefault(f, {}).setdefault(node, set()).add(nodeFromIdd[int(v)])
                else:
                    nodeFeatures.setdefault(f, {})[node] = v


    print('book names ...')
    bookMapping = dict(
        B_1QM='1QM',
        B_1QS='1QS',
        Ajrud='Kuntillet_Ajrud',
        Arad='Arad',
        Balaam='Balaam',
        Ketef_Hinnom='Ketef_Hinnom',
        Lachish='Lachish',
        Mesa='Mesha_Stela',
        Mesad_Hashavyahu='Mesad_Hashavyahu',
        Pirqe='Pirqe',
        Shirata='Shirata',
        Siloam='Siloam',
    )
    nodeFeatures['book@en'] = dict()
    for (idd, bookObj) in tables['book'].items():
        node = nodeFromIdd[idd]
        bookName = bookObj['feats']['book']
        eName = bookMapping[bookName]
        nodeFeatures['book@en'][node] = eName

    print('write data set to TF ...')
    TF.save(nodeFeatures=nodeFeatures, edgeFeatures=edgeFeatures, metaData=metaData)

with open(mqlFile) as fh:
    parseMql(fh)
    tfFromData()

