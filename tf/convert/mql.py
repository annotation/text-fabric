"""
# MQL

You can interchange with [MQL data](https://emdros.org).
Text-Fabric can read and write MQL dumps.
An MQL dump is a text file, like an SQL dump.
It contains the instructions to create and fill a complete database.

## Correspondence TF and MQL

After exporting a TF dataset to MQL, the resulting MQL database has the
following properties with respect to the TF dataset it comes from:

*   the TF *slots* correspond exactly with the MQL *monads* and have the same
    numbers; provided the monad numbers in the MQL dump are consecutive. In MQL
    this is not obligatory. Even if there gaps in the monads sequence, we will
    fill the holes during conversion, so the slots are tightly consecutive;
*   the TF *nodes* correspond exactly with the MQL *objects* and have the same
    numbers

## Node features in MQL

The values of TF features are of two types, `int` and `str`, and they translate
to corresponding MQL types `integer` and `string`. The actual values do not
undergo any transformation.

That means that in MQL queries, you use quotes if the feature is a string feature.
Only if the feature is a number feature, you may omit the quotes:

```
[word sp='verb']
[verse chapter=1 and verse=1]
```

## Enumeration types

It is attractive to use eumeration types for the values of a feature, whereever
possible, because then you can query those features in MQL with `IN` and without
quotes:

```
[chapter book IN (Genesis, Exodus)]
```

We will generate enumerations for eligible features.

Integer values can already be queried like this, even if they are not part of an
enumeration. So we restrict ourselves to node features with string values. We
put the following extra restrictions:

*   the number of distinct values is less than 1000
*   all values must be legal C names, in practice: starting with a letter,
    followed by letters, digits, or `_`. The letters can only be plain ASCII
    letters, uppercase and lowercase.

Features that comply with these restrictions will get an enumeration type.
Currently, we provide no ways to configure this in more detail.

Instead of creating separate enumeration types for individual features,
we collect all enumerated values for all those features into one
big enumeration type.

The reason is that MQL considers equal values in different types as
distinct values. If we had separate types, we could never compare
values for different features.

There is no place for edge values in
MQL. There is only one concept of feature in MQL: object features,
which are node features.
But TF edges without values can be seen as node features: nodes are
mapped onto sets of nodes to which the edges go. And that notion is supported by
MQL:
edge features are translated into MQL features of type `LIST OF id_d`,
i.e. lists of object identifiers.

!!! caution "Legal names in MQL"
    MQL names for databases, object types and features must be valid C identifiers
    (yes, the computer language C).

The requirements are for names are:

*   start with a letter (ASCII, upper-case or lower-case)
*   follow by any sequence of ASCII upper/lower-case letters or digits or
    underscores (`_`)
*   avoid being a reserved word in the C language

So, we have to change names coming from TF if they are invalid in MQL. We do
that by replacing illegal characters by `_`, and, if the result does not start
with a letter, we prepend an `x`. We do not check whether the name is a reserved
C word.

With these provisos:

*   the given `dbName` correspond to the MQL *database name*
*   the TF *otypes* correspond to the MQL *objects*
*   the TF *features* correspond to the MQL *features*

The MQL export is usually quite massive (500 MB for the Hebrew Bible).
It can be compressed greatly, especially by the program `bzip2`.

!!! caution "Exisiting database"
    If you try to import an MQL file in Emdros, and there exists already a file or
    directory with the same name as the MQL database, your import will fail
    spectacularly. So do not do that.

A good way to prevent clashes:

*   export the MQL to outside your `text-fabric-data` directory, e.g. to
    `~/Downloads`;
*   before importing the MQL file, delete the previous copy;

Delete existing copy:

```sh
cd ~/Downloads
rm dataset ; mql -b 3 < dataset.mql
```
"""

import os
import re
from itertools import chain
from ..parameters import WARP, OTYPE, OSLOTS
from ..core.helpers import (
    cleanName,
    isClean,
    specFromRanges,
    rangesFromList,
    setFromSpec,
    nbytes,
    console,
)

# If a feature, with type string, has less than ENUM_LIMIT values,
# an enumeration type for it will be created
# provided all values of that feature are a valid name for MQL.

ENUM_LIMIT = 1000

ONE_ENUM_TYPE = True


class MQL(object):
    def __init__(self, mqlDir, mqlName, tfFeatures, tmObj):
        error = tmObj.error

        self.mqlDir = mqlDir
        cleanDb = cleanName(mqlName)
        if cleanDb != mqlName:
            error(f'db name "{mqlName}" => "{cleanDb}"')
        self.mqlName = cleanDb
        self.tfFeatures = tfFeatures
        self.tmObj = tmObj
        self.enums = {}
        self._check()

    def write(self):
        tmObj = self.tmObj
        error = tmObj.error
        info = tmObj.info
        indent = tmObj.indent

        if not self.good:
            return
        if not os.path.exists(self.mqlDir):
            try:
                os.makedirs(self.mqlDir, exist_ok=True)
            except Exception:
                error(f'Cannot create directory "{self.mqlDir}"')
                self.good = False
                return
        mqlPath = f"{self.mqlDir}/{self.mqlName}.mql"
        try:
            fm = open(mqlPath, "w", encoding="utf8")
        except Exception:
            error(f"Could not write to {mqlPath}")
            self.good = False
            return

        info(f"Loading {len(self.featureList)} features")
        for ft in self.featureList:
            fObj = self.features[ft]
            fObj.load()

        self.fm = fm
        self._writeStartDb()
        self._writeEnums()
        self._writeTypes()
        self._writeDataAll()
        self._writeEndDb()
        indent(level=0)
        info("Done")

    def _check(self):
        tmObj = self.tmObj
        error = tmObj.error
        info = tmObj.info
        indent = tmObj.indent

        info(f"Checking features of dataset {self.mqlName}")

        self.features = {}
        self.featureList = []
        indent(level=1)
        for (f, fo) in sorted(self.tfFeatures.items()):
            if fo.method is not None or f in WARP:
                continue
            fo.load(metaOnly=True)
            if fo.isConfig:
                continue
            cleanF = cleanName(f)
            if cleanF != f:
                error(f'feature "{f}" => "{cleanF}"')
            self.featureList.append(cleanF)
            self.features[cleanF] = fo
        good = True
        for feat in (OTYPE, OSLOTS, "__levels__"):
            if feat not in self.tfFeatures:
                error(
                    "{} feature {} is missing from data set".format(
                        "Warp"
                        if feat in WARP
                        else "Computed"
                        if feat.startswith("__")
                        else "Data",
                        feat,
                    )
                )
                good = False
            else:
                fObj = self.tfFeatures[feat]
                if not fObj.load():
                    good = False
        indent(level=0)
        if not good:
            error("Export to MQL aborted")
        else:
            info(f"{len(self.featureList)} features to export to MQL ...")
        self.good = good

    def _writeStartDb(self):
        self.fm.write(
            """
CREATE DATABASE '{name}'
GO
USE DATABASE '{name}'
GO
""".format(
                name=self.mqlName
            )
        )

    def _writeEndDb(self):
        self.fm.write(
            """
VACUUM DATABASE ANALYZE
GO
"""
        )
        self.fm.close()

    def _writeEnums(self):
        tmObj = self.tmObj
        info = tmObj.info
        indent = tmObj.indent

        indent(level=0)
        info("Writing enumerations")
        indent(level=1)
        for ft in self.featureList:
            fObj = self.features[ft]
            if fObj.isEdge or fObj.dataType == "int":
                continue
            fMap = fObj.data
            fValues = sorted(set(fMap.values()))
            if len(fValues) > ENUM_LIMIT:
                continue
            eligible = all(isClean(fVal) for fVal in fValues)
            if not eligible:
                unclean = [fVal for fVal in fValues if not isClean(fVal)]
                console(
                    "\t{:<15}: {:>4} values, {} not a name, e.g. «{}»".format(
                        ft,
                        len(fValues),
                        len(unclean),
                        unclean[0],
                    )
                )
                continue
            self.enums[ft] = fValues

        if ONE_ENUM_TYPE:
            self._writeEnumsAsOne()
        else:
            for ft in sorted(self.enums):
                self._writeEnum(ft)
            indent(level=0)
            info(f"Written {len(self.enums)} enumerations")

    def _writeEnumsAsOne(self):
        tmObj = self.tmObj
        info = tmObj.info

        fValues = sorted(
            set(chain.from_iterable((set(fV) for fV in self.enums.values())))
        )
        if len(fValues):
            info(f"Writing an all-in-one enum with {len(fValues):>4} values")
            fValuesEnumerated = ",\n\t".join(
                "{} = {}".format(fVal, i) for (i, fVal) in enumerate(fValues)
            )
            self.fm.write(
                f"""
CREATE ENUMERATION all_enum = {{
    {fValuesEnumerated}
}}
GO
"""
            )

    def _writeEnum(self, ft):
        tmObj = self.tmObj
        info = tmObj.info

        fValues = self.enums[ft]
        if len(fValues):
            info(f"enum {ft:<15} with {len(fValues):>4} values")
            fValuesEnumerated = ",\n\t".join(
                f"{fVal} = {i}" for (i, fVal) in enumerate(fValues)
            )
            self.fm.write(
                f"""
CREATE ENUMERATION {ft}_enum = {{
    {fValuesEnumerated}
}}
GO
"""
            )

    def _writeTypes(self):
        def valInt(n):
            return str(n)

        def valStr(s):
            if "'" in s:
                return '"{}"'.format(s.replace('"', '\\"'))
            else:
                return "'{}'".format(s)

        def valIds(ids):
            return "({})".format(",".join(str(i) for i in ids))

        tmObj = self.tmObj
        error = tmObj.error
        info = tmObj.info
        indent = tmObj.indent

        self.levels = self.tfFeatures["__levels__"].data[::-1]
        indent(level=0)
        info(
            "Mapping {} features onto {} object types".format(
                len(self.featureList),
                len(self.levels),
            )
        )
        otypeSupport = {}
        for (otype, av, start, end) in self.levels:
            cleanOtype = cleanName(otype)
            if cleanOtype != otype:
                error(f'otype "{otype}" => "{cleanOtype}"')
            otypeSupport[cleanOtype] = set(range(start, end + 1))

        self.otypes = {}
        self.featureTypes = {}
        self.featureMethods = {}
        for ft in self.featureList:
            fObj = self.features[ft]
            if fObj.isEdge:
                dataType = "LIST OF id_d"
                method = valIds
            else:
                if fObj.dataType == "str":
                    dataType = 'string DEFAULT ""'
                    method = valInt if ft in self.enums else valStr
                elif fObj.dataType == "int":
                    dataType = "integer DEFAULT 0"
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
        self.fm.write(
            f"""
CREATE OBJECT TYPE
[{otype}
"""
        )
        for ft in self.otypes[otype]:
            fType = (
                "{}_enum".format("all" if ONE_ENUM_TYPE else ft)
                if ft in self.enums
                else self.featureTypes[ft]
            )
            self.fm.write(f"  {ft}:{fType};\n")
        self.fm.write(
            """
]
GO
"""
        )

    def _writeDataAll(self):
        tmObj = self.tmObj
        info = tmObj.info

        info(
            "Writing {} features as data in {} object types".format(
                len(self.featureList),
                len(self.levels),
            )
        )
        oslotsData = self.tfFeatures[OSLOTS].data
        self.oslots = oslotsData[0]
        self.maxSlot = oslotsData[1]
        for (otype, av, start, end) in self.levels:
            self._writeData(otype, start, end)

    def _writeData(self, otype, start, end):
        tmObj = self.tmObj
        info = tmObj.info
        indent = tmObj.indent

        fm = self.fm

        indent(level=1, reset=True)
        info(f"{otype} data ...")
        oslots = self.oslots
        maxSlot = self.maxSlot
        oFeats = self.otypes[otype]
        features = self.features
        featureMethods = self.featureMethods
        fm.write(
            """
DROP INDEXES ON OBJECT TYPE[{o}]
GO
CREATE OBJECTS
WITH OBJECT TYPE[{o}]
""".format(
                o=otype
            )
        )
        curSize = 0
        LIMIT = 50000
        t = 0
        j = 0
        indent(level=2, reset=True)
        for n in range(start, end + 1):
            oMql = """
CREATE OBJECT
FROM MONADS= {{ {m} }}
WITH ID_D={i} [
""".format(
                m=n
                if n <= maxSlot
                else specFromRanges(rangesFromList(oslots[n - maxSlot - 1])),
                i=n,
            )
            for ft in oFeats:
                method = featureMethods[ft]
                fMap = features[ft].data
                if n in fMap:
                    oMql += f"{ft}:={method(fMap[n])};\n"
            oMql += """
]
"""
            fm.write(oMql)
            curSize += len(bytes(oMql, encoding="utf8"))
            t += 1
            j += 1
            if j == LIMIT:
                fm.write(
                    """
GO
CREATE OBJECTS
WITH OBJECT TYPE[{o}]
""".format(
                        o=otype
                    )
                )
                info(
                    f"batch of size {nbytes(curSize):>20} with {j:>7} of {t:>7} {otype}s"
                )
                j = 0
                curSize = 0

        info(f"batch of size {nbytes(curSize):>20} with {j:>7} of {t:>7} {otype}s")
        fm.write(
            """
GO
CREATE INDEXES ON OBJECT TYPE[{o}]
GO
""".format(
                o=otype
            )
        )

        indent(level=1)
        info("{} data: {} objects".format(otype, t))


# MQL IMPORT

uniscan = re.compile(r"(?:\\x..)+")


def makeuni(match):
    """Make proper unicode of a text that contains byte escape codes
    such as backslash xb6
    """
    byts = eval('"' + match.group(0) + '"')
    return byts.encode("latin1").decode("utf-8")


def uni(line):
    return uniscan.sub(makeuni, line)


def tfFromMql(mqlFile, tmObj, slotType=None, otext=None, meta=None):
    error = tmObj.error

    if slotType is None:
        error("ERROR: no slotType specified")
        return (False, {}, {}, {})
    (good, objectTypes, tables, edgeF, nodeF) = parseMql(mqlFile, tmObj)
    if not good:
        return (False, {}, {}, {})
    return tfFromData(tmObj, objectTypes, tables, edgeF, nodeF, slotType, otext, meta)


def parseMql(mqlFile, tmObj):
    info = tmObj.info
    error = tmObj.error

    info("Parsing mql source ...")
    fh = open(mqlFile, encoding="utf8")

    objectTypes = dict()
    tables = dict()

    edgeF = dict()
    nodeF = dict()

    curId = None
    curEnum = None
    curObjectType = None
    curTable = None
    curObject = None
    curValue = None
    curFeature = None
    seeObjects = False

    inObjectTypeFeatures = False

    STRING_TYPES = {"ascii", "string"}

    enums = dict()

    chunkSize = 1000000
    inThisChunk = 0

    good = True

    for (ln, line) in enumerate(fh):
        inThisChunk += 1
        if inThisChunk == chunkSize:
            info(f"\tline {ln + 1:>9}")
            inThisChunk = 0
        if line.startswith("CREATE OBJECTS WITH OBJECT TYPE") or line.startswith(
            "WITH OBJECT TYPE"
        ):
            comps = line.rstrip().rstrip("]").split("[", 1)
            curTable = comps[1]
            info(f"\t\tobjects in {curTable}")
            curObject = None
            if curTable not in tables:
                tables[curTable] = dict()
            seeObjects = True
        elif line == "CREATE OBJECT\n":
            curObject = None
            curObject = dict(feats=dict(), monads=None)
            curId = None
            seeObjects = True
        elif curEnum is not None:
            if line.startswith("}"):
                curEnum = None
                continue
            comps = line.strip().rstrip(",").split("=", 1)
            comp = comps[0].strip()
            words = comp.split()
            if words[0] == "DEFAULT":
                enums[curEnum]["default"] = uni(words[1])
                value = words[1]
            else:
                value = words[0]
            enums[curEnum]["values"].append(value)
        elif curObjectType is not None:
            if line.startswith("]"):
                curObjectType = None
                inObjectTypeFeatures = False
                continue
            if curObjectType is True:
                if line.startswith("["):
                    curObjectType = line.rstrip()[1:]
                    objectTypes[curObjectType] = dict()
                    info(f"\t\totype {curObjectType}")
                    inObjectTypeFeatures = True
                    continue
            if inObjectTypeFeatures:
                comps = line.strip().rstrip(";").split(":", 1)
                feature = comps[0].strip()
                fInfo = comps[1].strip()
                fCleanInfo = fInfo.replace("FROM SET", "")
                fInfoComps = fCleanInfo.split(" ", 1)
                fMQLType = fInfoComps[0]
                if len(fInfoComps) == 2:
                    fDefaultComps = fInfoComps[1].strip().split(" ", 1)
                    fDefault = fDefaultComps[1] if len(fDefaultComps) > 1 else None
                else:
                    fDefault = None
                if fDefault is not None and fMQLType in STRING_TYPES:
                    fDefault = uni(fDefault[1:-1])
                default = enums.get(fMQLType, {}).get("default", fDefault)
                ftype = (
                    "str"
                    if fMQLType in enums
                    else "int"
                    if fMQLType == "integer"
                    else "str"
                    if fMQLType in STRING_TYPES
                    else "int"
                    if fInfo == "id_d"
                    else "str"
                )
                isEdge = fMQLType == "id_d"
                if isEdge:
                    edgeF.setdefault(curObjectType, set()).add(feature)
                else:
                    nodeF.setdefault(curObjectType, set()).add(feature)

                objectTypes[curObjectType][feature] = (ftype, default)
                info(
                    "\t\t\tfeature {} ({}) =def= {} : {}".format(
                        feature, ftype, default, "edge" if isEdge else "node"
                    )
                )
        elif seeObjects:
            if curObject is not None:
                if line.startswith("]"):
                    objectType = objectTypes[curTable]
                    for (feature, (ftype, default)) in objectType.items():
                        if feature not in curObject["feats"] and default is not None:
                            curObject["feats"][feature] = default
                    tables[curTable][curId] = curObject
                    curObject = None
                    continue
                elif line.startswith("["):
                    name = line.rstrip()[1:]
                    if len(name):
                        curTable = name
                        if curTable not in tables:
                            tables[curTable] = dict()
                elif line.startswith("FROM MONADS"):
                    monads = (
                        line.split("=", 1)[1]
                        .replace("{", "")
                        .replace("}", "")
                        .replace(" ", "")
                        .strip()
                    )
                    curObject["monads"] = setFromSpec(monads)
                elif line.startswith("WITH ID_D"):
                    comps = line.replace("[", "").rstrip().split("=", 1)
                    curId = int(comps[1])
                elif line.startswith("GO"):
                    pass
                elif line.strip() == "":
                    pass
                else:
                    if curValue is not None:
                        toBeContinued = not line.rstrip().endswith('";')
                        if toBeContinued:
                            curValue += line
                        else:
                            curValue += line.rstrip().rstrip(";").rstrip('"')
                            curObject["feats"][curFeature] = uni(curValue)
                            curValue = None
                            curFeature = None
                        continue
                    if ":=" in line:
                        (featurePart, valuePart) = line.split("=", 1)
                        feature = featurePart[0:-1].strip()
                        valuePart = valuePart.lstrip()
                        isText = ':="' in line
                        toBeContinued = isText and not line.rstrip().endswith('";')
                        if toBeContinued:
                            # this happens if a feature value
                            # contains a new line
                            # we must continue scanning lines
                            # until we meet the end of the value
                            curFeature = feature
                            curValue = valuePart.lstrip('"')
                        else:
                            value = valuePart.rstrip().rstrip(";").strip('"')
                            curObject["feats"][feature] = (
                                uni(value) if isText else value
                            )
                    else:
                        error(f"ERROR: line {ln}: unrecognized line -->{line}<--")
                        good = False
                        break
            else:
                if line.startswith("CREATE OBJECT"):
                    curObject = dict(feats=dict(), monads=None)
                    curId = None
        else:
            if line.startswith("CREATE ENUMERATION"):
                words = line.split()
                curEnum = words[2]
                enums[curEnum] = dict(default=None, values=[])
                info(f"\t\tenum {curEnum}")
            elif line.startswith("CREATE OBJECT TYPE"):
                curObjectType = True
                inObjectTypeFeatures = False
    info(f"{ln + 1} lines parsed")
    fh.close()
    for table in tables:
        info(f"{len(tables[table])} objects of type {table}")

    if len(tables) == 0:
        info("No objects found")
    return (good, objectTypes, tables, nodeF, edgeF)


def tfFromData(tmObj, objectTypes, tables, nodeF, edgeF, slotType, otext, meta):
    info = tmObj.info

    info("Making TF data ...")

    NIL = {"nil", "NIL", "Nil"}

    tableOrder = [slotType] + [t for t in sorted(tables) if t != slotType]

    iddFromMonad = dict()
    slotFromMonad = dict()

    nodeFromIdd = dict()
    iddFromNode = dict()

    nodeFeatures = dict()
    edgeFeatures = dict()
    metaData = dict()

    # metadata that ends up in every feature
    metaData[""] = {} if meta is None else meta

    # the config feature otext
    metaData["otext"] = otext

    good = True

    info("Monad - idd mapping ...")
    for idd in tables.get(slotType, {}):
        monad = list(tables[slotType][idd]["monads"])[0]
        iddFromMonad[monad] = idd

    info("Removing holes in the monad sequence")
    # we set up a monad - slot mapping
    curSlot = 0
    otype = dict()
    for monad in sorted(iddFromMonad):
        curSlot += 1
        slotFromMonad[monad] = curSlot
        idd = iddFromMonad[monad]
        nodeFromIdd[idd] = curSlot
        iddFromNode[curSlot] = idd
        otype[curSlot] = slotType

    maxSlot = curSlot
    info(f"maxSlot={maxSlot}")

    info("Node mapping and otype ...")
    node = maxSlot
    for t in tableOrder[1:]:
        for idd in sorted(tables[t]):
            node += 1
            nodeFromIdd[idd] = node
            iddFromNode[node] = idd
            otype[node] = t

    nodeFeatures["otype"] = otype
    metaData["otype"] = dict(valueType="str")

    info("oslots ...")
    oslots = dict()
    for t in tableOrder[1:]:
        for idd in tables.get(t, {}):
            node = nodeFromIdd[idd]
            monads = tables[t][idd]["monads"]
            oslots[node] = {slotFromMonad[m] for m in monads}
    edgeFeatures["oslots"] = oslots
    metaData["oslots"] = dict(valueType="str")

    info("metadata ...")
    for t in nodeF:
        for f in nodeF[t]:
            ftype = objectTypes[t][f][0]
            metaData.setdefault(f, {})["valueType"] = ftype
    for t in edgeF:
        for f in edgeF[t]:
            metaData.setdefault(f, {})["valueType"] = "str"

    info("features ...")
    chunkSize = 100000
    for t in tableOrder:
        info(f"\tfeatures from {t}s")
        inThisChunk = 0
        thisTable = tables.get(t, {})
        for (i, idd) in enumerate(thisTable):
            inThisChunk += 1
            if inThisChunk == chunkSize:
                info(f"\t{i + 1:>9} {t}s")
                inThisChunk = 0
            node = nodeFromIdd[idd]
            features = tables[t][idd]["feats"]
            for (f, v) in features.items():
                isEdge = f in edgeF.get(t, set())
                if isEdge:
                    if v not in NIL:
                        edgeFeatures.setdefault(f, {}).setdefault(node, set()).add(
                            nodeFromIdd[int(v)]
                        )
                else:
                    nodeFeatures.setdefault(f, {})[node] = v
        info(f"\t{len(thisTable):>9} {t}s")

    return (good, nodeFeatures, edgeFeatures, metaData)
