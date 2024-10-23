"""
# Walker

You can convert a dataset to TF by writing a function that walks through it.

That function must trigger a sequence of actions when reading the data.
These actions drive TF to build a valid TF dataset.
Many checks will be performed.

!!! hint "to and from MQL"
    If your source is MQL, you are even better off: TF has a
    module to import from MQL and to export to MQL.
    See `tf.convert.mql.importMQL` and `tf.convert.mql.exportMQL`.

## Set up

Here is a schematic set up of such a conversion program.

``` python
from tf.fabric import Fabric
from tf.convert.walker import CV

TF = Fabric(locations=OUT_DIR)
cv = CV(TF)

def director(cv):
  # your code to unwrap your source data and trigger
  # the generation of TF nodes, edges and features

slotType = 'word'  # or whatever you choose
otext = {  # dictionary of config data for sections and text formats
    ...
}
generic = {  # dictionary of metadata meant for all features
    ...
}
intFeatures = {  # set of integer valued feature names
    ...
}
featureMeta = {  # per feature dictionaries with metadata
   ...
}

good = cv.walk(
    director,
    slotType,
    otext=otext,
    generic=generic,
    intFeatures=intFeatures,
    featureMeta=featureMeta,
    warn=True,
    force=False,
)

if good:
  ... load the new TF data ...
```

See `tf.convert.walker.CV.walk`.

## Walking

When you walk through the input data source, you'll encounter things
that have to become slots, non-slot nodes, edges and features in the new data set.

You issue these things by means of an *action method* from `cv`, such as
`cv.slot()` or `cv.node(nodeType)`.

When your action creates slots or non slot nodes,
TF will return you a reference to that node,
that you can use later for more actions related to that node.

``` python
curPara = cv.node('para')
```

To add features to nodes, use a `cv.feature()` action.
It will apply to a node passed as argument.

To add features to edges, issue a `cv.edge()` action.
It will require two node arguments: the *from* node and the *to* node.

There is always a set of current *embedder nodes*.
When you create a slot node

``` python
curWord = cv.slot()
```

then TF will link all current embedder nodes to the resulting slot.

There are actions to add nodes to the set of embedder nodes,
to remove them from it,
and to add them again.

If your data is organized in such a way that you see the slots in a different
order than the intended order, you can pass a key value to the slot, like so

``` python
curWord = cv.slot(key=wordNumber)
```

After the walk is completed, the slots will be sorted by their keys, while keeping
all feature assignments to them intact. All nodes will be linked to the same slots
after sorting, and all edges that start from or arrive at slots will do that after
the sorting.

For an example, see
[lowfat.py](https://github.com/ETCBC/nestle1904/blob/master/programs/lowfat.py).

## Dynamic Metadata

When the director runs, you may have already specified all your feature
metadata, including the value types.

But if some of that information is dependent on what you encounter in the
data, you can do two things:

(A) Run a preliminary pass over the data and gather the required information,
before running the director.

(B) Update the metadata later on
by issuing `cv.meta()` actions from within your director, see below.

In doing this, you can remove the metadata from unused features,
but you can also add metadata to features that have not got them yet.

If the set of possible features is not known on beforehand,
you can ask for the list of all feature names by means of
`cv.features()`.

## Action methods

The `cv` class contains methods that are responsible for particular *actions*
that steer the graph building:

*   `tf.convert.walker.CV.slot`
*   `tf.convert.walker.CV.node`
*   `tf.convert.walker.CV.terminate`
*   `tf.convert.walker.CV.resume`
*   `tf.convert.walker.CV.link`
*   `tf.convert.walker.CV.linked`
*   `tf.convert.walker.CV.feature`
*   `tf.convert.walker.CV.features`
*   `tf.convert.walker.CV.edge`
*   `tf.convert.walker.CV.meta`
*   `tf.convert.walker.CV.occurs`
*   `tf.convert.walker.CV.active`
*   `tf.convert.walker.CV.activeNodes`
*   `tf.convert.walker.CV.activeTypes`
*   `tf.convert.walker.CV.get` and `cv.get(feature, nf, nt)`
*   `tf.convert.walker.CV.stop`

!!! hint "Example"
    Follow the
    [conversion tutorial](https://nbviewer.jupyter.org/github/annotation/banks/blob/master/programs/convert.ipynb)

    Or study a more involved example:
    [Old Babylonian](https://github.com/Nino-cunei/tfFromAtf/blob/master/programs/convert.py)
"""

import collections
import functools
import re

from ..parameters import WARP, OTYPE, OSLOTS, OTEXT
from ..core.helpers import itemize, isInt
from ..core.timestamp import SILENT_D, DEEP, silentConvert


class CV:
    S = "slot"
    N = "node"
    T = "terminate"
    R = "resume"
    D = "delete"
    F = "feature"
    E = "edge"

    def __init__(self, TF, silent=SILENT_D):
        """The object that contains the walker conversion machinery.

        silent: string, optional tf.core.timestamp.SILENT_D
            See `tf.core.timestamp.Timestamp`
        """

        self.TF = TF
        self.silent = silent
        tmObj = TF.tmObj
        isSilent = tmObj.isSilent
        setSilent = tmObj.setSilent

        silent = silentConvert(silent)
        self.wasSilent = isSilent()
        setSilent(silent)

    def _showWarnings(self):
        silent = self.silent
        tmObj = self.TF.tmObj
        error = tmObj.error
        info = tmObj.info
        indent = tmObj.indent

        warnings = self.warnings
        warn = self.warn

        if warn is None:
            if warnings:
                info("use `cv.walk(..., warn=False)` to make warnings visible")
                info("use `cv.walk(..., warn=True)` to stop on warnings")
        else:
            method = error if warn else info

            if warnings:
                for (kind, msgs) in sorted(warnings.items()):
                    method(f"WARNING {kind} ({len(msgs)} x):", force=silent != DEEP)
                    indent(level=2)
                    for msg in sorted(set(msgs))[0:20]:
                        if msg:
                            method(f"{msg}", tm=False, force=silent != DEEP)
                self.warnings = {}
                if warn:
                    info("use `cv.walk(..., warn=False)` to continue after warnings")
                    info("use `cv.walk(..., warn=None)` to suppress warnings")
                    self.good = False
                else:
                    info("use `cv.walk(..., warn=True)` to stop after warnings")
                    info("use `cv.walk(..., warn=None)` to suppress warnings")

    def _showErrors(self):
        silent = self.silent
        tmObj = self.TF.tmObj
        error = tmObj.error
        info = tmObj.info
        indent = tmObj.indent
        forcedStop = self.forcedStop

        errors = self.errors

        if errors:
            for (kind, msgs) in sorted(errors.items()):
                error(f"ERROR {kind} ({len(msgs)} x):")
                indent(level=2)
                for msg in sorted(set(msgs))[0:20]:
                    if msg:
                        error(f"{msg}", tm=False)
            self.errors = {}
            self.good = False

        if forcedStop:
            error("STOPPED by the stop() instruction")
        elif not errors:
            if self.good:
                info("OK", force=silent != DEEP)
            else:
                error("STOPPED because of warnings")

    def walk(
        self,
        director,
        slotType,
        otext={},
        generic={},
        intFeatures=set(),
        featureMeta={},
        warn=True,
        generateTf=True,
        force=False,
    ):
        """Asks a director function to walk through source data and receives its actions.

        The `director` function should unravel the source.
        You have to program the `director`, which takes one argument: `cv`.
        From the `cv` you can use a few standard actions that instruct TF
        to build a graph.

        This function will check whether the metadata makes sense and is minimally
        complete.

        During node creation the section structure will be watched,
        and you will be warned if irregularities occur.

        After the creation of the feature data, some extra checks will be performed
        to see whether the metadata matches the data and vice versa.

        If the slots need to be sorted by their keys, it will happen at this point,
        and the generated features will be adapted to the sorted slots.

        The new feature data will be written to the output directory of the
        underlying TF object.  In fact, the rules are exactly the same as for
        `tf.fabric.Fabric.save`.

        Parameters
        ----------
        slotType: string
            The node type that acts as the type of the slots in the data set.

        oText: dict
            The configuration information to be stored in the `otext` feature
            (see `tf.core.text`):

            *   section types
            *   section features
            *   structure types
            *   structure features
            *   text formats

        generic: dict
            Metadata that will be written into the header of all generated TF features.

            You can make changes to this later on, dynamically in your director.

        intFeatures: iterable
            The set of features that have integer values only.

            You can make changes to this later on, dynamically in your director.

        featureMeta: dict of dict
            For each node or edge feature descriptive metadata can be supplied.

            You can make changes to this later on, dynamically in your director.

        warn: boolean, optional True
            This regulates the response to warnings:

            `True` (default): stop after warnings (as if they are errors);

            `False` continue after warnings but do show them;

            `None` suppress all warnings.

        force: boolean, optional False
            This forces the process to continue after errors.
            Your TF set might not be valid.
            Yet this can be useful during testing, when you know
            that not everything is OK, but you want to check some results.
            Especially when dealing with large datasets, you might want to test
            with little pieces. But then you get a kind of non-fatal errors that
            stand in the way of testing. For those cases: `force=True`.

        generateTf: boolean, optional True
            You can pass `False` here to suppress the actual writing of TF data.
            In that way you can dry-run the director to check for errors and warnings

        director: function
            An ordinary function that takes one argument, the `cv` object, and
            should not deliver anything.

            Writing this function is the main job to do when you want to convert a data source
            to TF.

            See `tf.convert.walker` for more details.

        Returns
        -------
        boolean
            Whether the operation was successful
        """

        tmObj = self.TF.tmObj
        info = tmObj.info
        indent = tmObj.indent
        setSilent = tmObj.setSilent
        silent = self.silent

        indent(level=0, reset=True)
        info("Importing data from walking through the source ...", force=silent != DEEP)

        self.force = force
        self.good = True
        self.forcedStop = False
        self.errors = collections.defaultdict(list)
        self.warnings = collections.defaultdict(list)
        self.warn = warn
        self.slotType = slotType

        self.intFeatures = set(intFeatures)
        self.featureMeta = featureMeta
        self.metaData = {}
        self.nodeFeatures = {}
        self.edgeFeatures = {}
        self.slotKeys = {}
        self.discardables = set()

        indent(level=1, reset=True)
        self._prepareMeta(otext, generic)

        indent(level=1, reset=True)
        self._follow(director)

        indent(level=1, reset=True)
        self._removeUnlinked()

        indent(level=1, reset=True)
        self._checkGraph()

        indent(level=1, reset=True)
        self._checkFeatures()

        indent(level=1, reset=True)
        self._reorderNodes()

        indent(level=1, reset=True)
        self._reassignFeatures()

        indent(level=0)
        info("Features ready to write")

        if generateTf:
            if self.good or self.force:
                self.good = self.TF.save(
                    metaData=self.metaData,
                    nodeFeatures=self.nodeFeatures,
                    edgeFeatures=self.edgeFeatures,
                    silent=silent,
                )

        self._showWarnings()
        setSilent(self.wasSilent)

        return self.good

    def _prepareMeta(self, otext, generic):
        silent = self.silent
        varRe = re.compile(r"\{([^}]+)\}")

        tmObj = self.TF.tmObj
        info = tmObj.info
        indent = tmObj.indent

        if not self.good and not self.force:
            return

        info("Preparing metadata... ", force=silent != DEEP)

        intFeatures = self.intFeatures
        featureMeta = self.featureMeta

        errors = self.errors

        self.metaData = {
            "": generic,
            OTYPE: {"valueType": "str"},
            OSLOTS: {"valueType": "str"},
            OTEXT: otext,
        }
        metaData = self.metaData

        self.intFeatures = intFeatures
        self.sectionTypes = []
        self.sectionFeatures = []
        self.sectionFromLevel = {}
        self.levelFromSection = {}
        self.structureTypes = []
        self.structureFeatures = []
        self.structureLevel = {}
        self.textFormats = {}
        self.textFeatures = set()

        if not generic:
            errors['Missing feature meta data in "generic"'].append(
                "Consider adding provenance metadata to all features"
            )
        if not otext:
            errors['Missing "otext" configuration'].append(
                "Consider adding configuration for text representation and section levels"
            )
        else:
            sectionInfo = {}
            for f in ("sectionTypes", "sectionFeatures"):
                if f not in otext:
                    errors['Incomplete section specs in "otext"'].append(
                        f'no key "{f}"'
                    )
                    sectionInfo[f] = []
                else:
                    sFields = itemize(otext[f], sep=",")
                    sectionInfo[f] = sFields
                    if f == "sectionTypes":
                        for (i, s) in enumerate(sFields):
                            self.levelFromSection[s] = i + 1
                            self.sectionFromLevel[i + 1] = s
            sLevels = {f: len(sectionInfo[f]) for f in sectionInfo}
            if min(sLevels.values()) != max(sLevels.values()):
                errors["Inconsistent section info"].append(
                    " but ".join(f'"{f}" has {sLevels[f]} levels' for f in sLevels)
                )
            self.sectionFeatures = sectionInfo["sectionFeatures"]
            self.sectionTypes = sectionInfo["sectionTypes"]
            self.featFromSectionType = {
                typ: feat
                for (typ, feat) in zip(self.sectionTypes, self.sectionFeatures)
            }
            self.sectionSet = set(self.sectionTypes)

            structureInfo = {}
            for f in ("structureTypes", "structureFeatures"):
                if f not in otext:
                    structureInfo[f] = []
                    continue
                sFields = itemize(otext[f], sep=",")
                structureInfo[f] = sFields
            if not structureInfo:
                info("No structure definition found in otext")
            sLevels = {f: len(structureInfo[f]) for f in structureInfo}
            if min(sLevels.values()) != max(sLevels.values()):
                errors["Inconsistent structure info"].append(
                    " but ".join(f'"{f}" has {sLevels[f]} levels' for f in sLevels)
                )
                structureInfo = {}
            if not structureInfo or all(
                len(info) == 0 for (s, info) in structureInfo.items()
            ):
                info("No structure nodes will be set up")
                self.structureFeatures = []
                self.structureTypes = []
            self.structureFeatures = structureInfo["structureFeatures"]
            self.structureTypes = structureInfo["structureTypes"]
            self.featFromStructureType = {
                typ: feat
                for (typ, feat) in zip(self.structureTypes, self.structureFeatures)
            }
            self.structureSet = set(self.structureTypes)

            textFormats = {}
            textFeatures = set()
            for (k, v) in sorted(otext.items()):
                if k.startswith("fmt:"):
                    featureSet = set()
                    features = varRe.findall(v)
                    for ff in features:
                        fr = ff.rsplit(":", maxsplit=1)[0]
                        for f in fr.split("/"):
                            featureSet.add(f)
                    textFormats[k[4:]] = featureSet
                    textFeatures |= featureSet
            if not textFormats:
                errors['No text formats in "otext"'].append('add "fmt:text-orig-full"')
            elif "text-orig-full" not in textFormats:
                errors["No default text format in otext"].append(
                    'add "fmt:text-orig-full"'
                )
            self.textFormats = textFormats
            self.textFeatures = textFeatures

        info(f'SECTION   TYPES:    {", ".join(self.sectionTypes)}', tm=False)
        info(f'SECTION   FEATURES: {", ".join(self.sectionFeatures)}', tm=False)
        info(f'STRUCTURE TYPES:    {", ".join(self.structureTypes)}', tm=False)
        info(f'STRUCTURE FEATURES: {", ".join(self.structureFeatures)}', tm=False)
        info("TEXT      FEATURES:", tm=False)
        indent(level=2)
        for (fmt, feats) in sorted(textFormats.items()):
            info(f'{fmt:<20} {", ".join(sorted(feats))}', tm=False)
        indent(level=1)

        for feat in WARP + ("",):
            if feat in intFeatures:
                if feat == "":
                    errors["intFeatures"].append(
                        'Do not declare the "valueType" for all features'
                    )
                else:
                    errors["intFeatures"].append(
                        f'Do not mark the "{feat}" feature as integer valued'
                    )
                self.good = False

        for (feat, featMeta) in sorted(featureMeta.items()):
            good = self._checkFeatMeta(
                feat,
                featMeta,
                checkRegular=True,
                valueTypeAllowed=False,
                showErrors=False,
            )
            if not good:
                self.good = False
            metaData.setdefault(feat, {}).update(featMeta)
            metaData[feat]["valueType"] = "int" if feat in intFeatures else "str"

        self._showErrors()

    def _checkFeatMeta(
        self,
        feat,
        featMeta,
        checkRegular=False,
        valueTypeAllowed=True,
        showErrors=True,
    ):
        errors = collections.defaultdict(list)
        good = True

        if checkRegular:
            if feat in WARP + ("",):
                if feat == "":
                    errors["featureMeta"].append(
                        'Specify the generic feature meta data in "generic"'
                    )
                    good = False
                elif feat == OTEXT:
                    errors["featureMeta"].append(
                        f'Specify the "{OTEXT}" feature in "otext"'
                    )
                    good = False
                else:
                    errors["featureMeta"].append(
                        f'Do not pass metaData for the "{feat}" feature in "featureMeta"'
                    )
                    good = False
        if "valueType" in featMeta:
            if not valueTypeAllowed:
                errors["featureMeta"].append(
                    f'Do not specify "valueType" for the "{feat}" feature in "featureMeta"'
                )
                good = False
            elif featMeta["valueType"] not in {"int", "str"}:
                errors["featureMeta"].append('valueType must be "int" or "str"')
                good = False

        for (e, eData) in errors.items():
            self.errors[e].extend(eData)
        if showErrors:
            self._showErrors
        return good

    def stop(self, msg):
        """Stops the director. No further input will be read.

        ```
        cv.stop(msg)
        ```

        The director will exit with a non-good status  and issue the message `msg`.
        If you have called `walk()` with `force=True`, indicating that the
        director must proceed after errors, then this stop command will cause
        termination nevertheless.

        Parameters
        ----------
        msg: string
            A message to display upon stopping.

        Returns
        -------
        None
        """

        tmObj = self.TF.tmObj
        error = tmObj.error

        error(f"Forced stop: {msg}")
        self.good = False
        self.force = False
        self.forcedStop = True

    def slot(self, key=None):
        """Makes a slot node and return the handle to it in `n`.

        ```
        n = cv.slot()
        ```

        No further information is needed.
        Remember that you can add features to the node by later

        ```
        cv.feature(n, key=value, ...)
        ```

        calls.

        Parameters
        ----------
        key: string, optional None
            If passed, it acts as a sort key on the slot.
            At the end of the walk, all slots will be sorted by their key and then
            by their original order. Care will be taken that slots retain their
            features and linkages.

            !!! note "Keys are strings"
            Note that the key must be a string. If you want to sort on numbers,
            make sure to pad all numbers with leading zeros.

        Returns
        -------
        node reference: tuple
            The node reference consists of a node type and a sequence number,
            but normally you do not have to dig these out.
            Just pass the tuple as a whole to actions that require a node argument.
        """

        curSeq = self.curSeq
        curEmbedders = self.curEmbedders
        oslots = self.oslots
        slotKeys = self.slotKeys
        levelFromSection = self.levelFromSection
        warnings = self.warnings

        self.stats[self.S] += 1
        nType = self.slotType

        curSeq[nType] += 1
        seq = curSeq[nType]

        if key is not None:
            slotKeys[seq] = key

        inSection = False

        for eNode in curEmbedders:
            if eNode[0] in levelFromSection:
                inSection = True
            oslots[eNode].add(seq)

        if levelFromSection and not inSection:
            warnings["slot outside sections"].append(f"{seq}")

        return (nType, seq)

    def node(self, nType, slots=None):
        """Makes a non-slot node and return the handle to it in `n`.

        ```
        n = cv.node(nodeType)
        ```

        You have to pass its *node type*, i.e. a string.
        Think of `sentence`, `paragraph`, `phrase`, `word`, `sign`, whatever.

        There are two modes for this function:

        *   Auto: (`slots=None`):
            Non slot nodes will be automatically added to the set of embedders.
        *   Explicit: (`slots=iterable`):
            The slots in iterable will be assigned to this node and nothing else.
            The node will not be added to the set of embedders.
            Put otherwise: the node will be terminated after construction.
            However: you could resume it later to add other slots.

        Remember that you can add features to the node by later

        ```
        cv.feature(n, key=value, ...)
        ```

        calls.

        Parameters
        ----------
        nType: string
            A node type, not the slot type
        slots: iterable of integer, optional None
            The slots to assign to this node.
            If left out, the node is left as an embedding node and
            subsequent slots will be added to it automatically.
            All slots in the iterable must have been generated before
            by means of the `cv.slot()` action.

        Returns
        -------
        node reference or None
            If an error occurred, `None` is returned.
            The node reference consists of a node type and a sequence number,
            but normally you do not have to dig these out.
            Just pass the tuple as a whole to actions that require a node argument.
        """

        slotType = self.slotType
        errors = self.errors

        if nType == slotType:
            errors[f'use `cv.slot()` instead of `cv.node("{nType}")`'].append(None)
            return

        curSeq = self.curSeq
        curEmbedders = self.curEmbedders

        self.stats[self.N] += 1

        curSeq[nType] += 1
        seq = curSeq[nType]
        node = (nType, seq)

        self._checkSecLevel(node, before=True)

        if slots:
            maxSlot = curSeq[slotType]

            for s in slots:
                if not 1 <= s <= maxSlot:
                    errors[f"slot out of range in `cv.node(({nType}, {seq}))`"].append(
                        f"{s}"
                    )
                else:
                    oslots = self.oslots
                    oslots[node].add(s)

            self.stats[self.T] += 1
        else:
            curEmbedders.add(node)

        return node

    def terminate(self, node):
        """**terminates** a node.

        ```
        cv.terminate(n)
        ```

        The node `n` will be removed from the set of current embedders.
        This `n` must be the result of a previous `cv.slot()` or `cv.node()` action.

        Parameters
        ----------
        node: tuple
            A node reference, obtained by one of the actions `slot` or `node`.

        Returns
        -------
        None
        """

        self.stats[self.T] += 1
        if node is not None:
            self.curEmbedders.discard(node)
            self._checkSecLevel(node, before=False)

    def delete(self, node):
        """**deletes** a node.

        ```
        cv.delete(n)
        ```

        The node `n` will be deleted from the set of nodes that will be created.
        This `n` must be the result of a previous `cv.node()` action.
        slots cannot be deleted.

        Parameters
        ----------
        node: tuple
            A node reference, obtained by the actions `node`.

        Returns
        -------
        None
        """

        self.stats[self.D] += 1
        if node is not None:
            slotType = self.slotType
            nType = node[0]

            if nType == slotType:
                errors = self.errors
                errors["cannot delete a slot"].append(node[1])
                return

            self.discardables.add(node)

    def resume(self, node):
        """**resumes** a node.

        ```
        cv.resume(n)
        ```

        If you resume a non-slot node, you add it again to the set of embedders.
        No new node will be created.

        If you resume a slot node, it will be added to the set of current embedders.
        No new slot will be created.

        Parameters
        ----------
        node: tuple
            A node reference, obtained by one of the actions `slot` or `node`.

        Returns
        -------
        None
        """

        curEmbedders = self.curEmbedders
        oslots = self.oslots

        self.stats[self.R] += 1

        (nType, seq) = node
        if nType == self.slotType:
            for eNode in curEmbedders:
                oslots[eNode].add(seq)
        else:
            self._checkSecLevel(node, before=None)
            curEmbedders.add(node)

    def link(self, node, slots):
        """Links the given, existing slots to a node.

        ```
        cv.link(n, [s1, s2])
        ```

        Sometimes the automatic linking of slots to nodes is not sufficient.

        This happens when you feel the need to construct a node retro-actively,
        when the slots that need to be linked to it have already been created.

        This action is precisely meant for that.

        Parameters
        ----------
        node: tuple
            A node reference, obtained by one of the actions `slot` or `node`.
        slots: iterable of integer

        Returns
        -------
        boolean
        """

        oslots = self.oslots

        good = True

        for seq in slots:
            oslots[node].add(seq)

        return good

    def linked(self, node):
        """Returns the slots `ss` to which a node is currently linked.

        ```
        ss = cv.linked(n)
        ```

        If you construct non-slot nodes without linking them to slots,
        they will be removed when TF validates the collective result
        of the action methods.

        If you want to prevent that, you can insert an extra slot, but in order
        to do so, you have to detect that a node is still unlinked.

        This action is precisely meant for that.

        Parameters
        ----------
        node: tuple
            A node reference, obtained by one of the actions `slot` or `node`.

        Returns
        -------
        tuple of integer

        The slots are returned as a tuple of integers, sorted.
        """

        oslots = self.oslots
        return tuple(sorted(oslots.get(node, [])))

    def feature(self, node, **features):
        """Adds **node features**.

        ```
        cv.feature(n, name=value, ... , name=value)
        ```

        Parameters
        ----------
        node: tuple
            A node reference, obtained by one of the actions `slot` or `node`.
        features: keyword arguments
            The names and values of features to assign to this node.

        Returns
        -------
        None

        !!! caution "None values"
            If a feature value is `None` it will not be added!
        """

        nodeFeatures = self.nodeFeatures

        self.stats[self.F] += 1

        for (k, v) in features.items():
            if v is None:
                continue
            # self._checkType(k, v, self.N)
            nodeFeatures[k][node] = v

    def edge(self, nodeFrom, nodeTo, **features):
        """Adds **edge features**.

        ```
        cv.edge(nf, nt, name=value, ... , name=value)
        ```

        Parameters
        ----------
        nodeFrom, nodeTo: tuple
            Two node references, obtained by one of the actions `slot` or `node`.
        features: keyword arguments
            The names and values of features to assign to this edge
            (i.e. pair of nodes).

        Returns
        -------
        None

        !!! note "None values"
            You may pass values that are `None`,
            and a corresponding edge will be created.
            If for all edges the value is `None`,
            an edge without values will be created.
            For every `nodeFrom`, such a feature
            essentially specifies a set of nodes `{ nodeTo }`.
        """

        edgeFeatures = self.edgeFeatures

        self.stats[self.E] += 1

        for (k, v) in features.items():
            # self._checkType(k, v, self.E)
            edgeFeatures[k][nodeFrom][nodeTo] = v

    def occurs(self, feat):
        """Whether the feature `featureName` occurs in the resulting data so far.

        ```
        occurs = cv.occurs(featureName)
        ```

        If you have assigned None values to a feature, that will count, i.e.
        that feature occurs in the data.

        If you add feature values conditionally, it might happen that some
        features will not be used at all.
        For example, if your conversion produces errors, you might
        add the error information to the result in the form of error features.

        Later on, when the errors have been weeded out, these features will
        not occur any more in the result, but then TF will complain that
        such is feature is declared but not used.
        At the end of your director you can remove unused features
        conditionally, using this function.

        Parameters
        ----------
        feat: string
            The name of a feature

        Returns
        -------
        boolean
        """

        nodeFeatures = self.nodeFeatures
        edgeFeatures = self.edgeFeatures
        if feat in nodeFeatures or feat in edgeFeatures:
            return True
        return False

    def meta(self, feat, **metadata):
        """Adds, modifies, deletes metadata fields of features.

        ```
        cv.meta(feature, name=value, ... , name=value)
        ```

        Parameters
        ----------
        feat: string
            The name of a feature
        metadata: dict
            If a `value` is `None`, that `name` will be deleted from the
            metadata fields of the feature.
            A bare `cv.meta(feature)` will remove the all metadata from the feature.
            If you modify the field `valueType` of a feature, that feature will be
            added or removed from the set of `intFeatures`.
            It will be checked whether you specify either `int` or `str`.


        Returns
        -------
        None
        """

        errors = self.errors
        intFeatures = self.intFeatures
        metaData = self.metaData
        featMeta = metaData.get(feat, {})

        good = True

        if not metadata:
            if feat in metaData:
                del metaData[feat]
                intFeatures.discard(feat)

        for (field, text) in metadata.items():
            if text is None:
                if field == "valueType":
                    errors['did not delete metadata field "valueType"'].append(feat)
                    good = False
                else:
                    if feat in metaData and field in metaData[feat]:
                        del metaData[feat][field]
            else:
                metaData.setdefault(feat, {})[field] = text
                if field == "valueType":
                    if text == "int":
                        intFeatures.add(feat)
                    else:
                        intFeatures.discard(feat)

        self.good = self._checkFeatMeta(feat, featMeta) and good and self.good

    def features(self):
        """Gets the list of all features.

        ```
        featureNames = cv.features()
        ```

        Returns
        -------
        list
        """

        nodeFeatures = self.nodeFeatures
        edgeFeatures = self.edgeFeatures
        return sorted(list(nodeFeatures) + list(edgeFeatures))

    def active(self, node):
        """Returns whether a node is currently active.

        Active nodes are the nodes in the set of current embedders.

        ```
        isActive = cv.active(n)
        ```

        If you construct your nodes in a very dynamic way, it might be
        hard to keep track for each node whether it has been created, terminated,
        or resumed, in other words, whether it is active or not.

        This action is provides a direct and precise way to know
        whether a node is active.

        Parameters
        ----------
        node: tuple
            A node reference, obtained by one of the actions `slot` or `node`.

        Returns
        -------
        boolean
        """

        return node in self.curEmbedders

    def activeNodes(self, nTypes=None):
        """The currently active nodes, i.e. the embedders.

        ```
        nodes = cv.activeNodes()
        nodes = cv.activeNodes(nTypes=("sentence", "clause"))
        ```

        Parameters
        ----------
        nTypes: iterable optional None
            If None, all active nodes are returned.
            Else the iterable lists a few node types,
            and only active nodes in these types are returned.

        Returns
        -------
        set
        """

        if nTypes is None:
            return set(self.curEmbedders)
        nTypes = set(nTypes)
        return {n for n in self.curEmbedders if n[0] in nTypes}

    def activeTypes(self):
        """The node types of the currently active nodes, i.e. the embedders.

        ```
        nTypes = cv.activeTypes()
        ```

        Parameters
        ----------
        None

        Returns
        -------
        set
        """

        return {node[0] for node in self.curEmbedders}

    def get(self, feature, *args):
        """Retrieves feature values.

        ```
        cv.get(feature, n) and cv.get(feature, nf, nt)
        ```

        `feature` is the name of the feature.

        For node features, `n` is the node which carries the value.

        For edge features, `nf, nt` is the pair of from-to nodes which carries the value.

        Parameters
        ----------
        feature: string
            The name of a feature
        node: tuple
            A node reference, obtained by one of the actions `slot` or `node`.
            The node in question when retrieving the value of a node feature.
        nodeFrom, nodeTo: tuple
            Two node references, obtained by one of the actions `slot` or `node`.
            The nodes in question when retrieving the value of an edge feature.

        Returns
        -------
        string or integer
        """

        errors = self.errors
        nodeFeatures = self.nodeFeatures
        edgeFeatures = self.edgeFeatures
        nArgs = len(args)
        if nArgs == 0 or nArgs > 2:
            errors["use `cv.get(ft, n)` or `cv.get(ft, nf, nt)`"].append(None)
            return None

        return (
            nodeFeatures.get(feature, {}).get(args[0], None)
            if len(args) == 1
            else edgeFeatures.get(feature, {}).get(args[0], {}).get(args[1], None)
        )

    def _checkSecLevel(self, node, before=True):
        levelFromSection = self.levelFromSection
        sectionFeatures = self.sectionFeatures
        nodeFeatures = self.nodeFeatures
        warnings = self.warnings
        curEmbedders = self.curEmbedders

        (nType, seq) = node

        msg = "starts" if before is True else "ends" if before is False else "resumes"

        if levelFromSection:
            level = levelFromSection.get(nType, None)
            if level is None:
                return

            headingFeature = sectionFeatures[level - 1]
            nHeading = nodeFeatures.get(headingFeature, {}).get(node, "??")

            for em in curEmbedders:
                eType = em[0]
                if eType in levelFromSection:
                    eLevel = levelFromSection.get(eType, None)
                    eHeadingFeature = sectionFeatures[eLevel - 1]
                    eHeading = nodeFeatures.get(eHeadingFeature, {}).get(em, "??")

                if eType == nType:
                    warnings[
                        f'section {nType} "{nHeading}" of level {level}'
                        f" enclosed in another {nType}: {eHeading}"
                    ].append(None)
                elif eType in levelFromSection:
                    eLevel = levelFromSection[eType]
                    if eLevel > level:
                        warnings[
                            f'section {nType} "{nHeading}" of level {level} {msg}'
                            f' inside a {eType} "{eHeading}" of level {eLevel}'
                        ].append(None)

    def _follow(self, director):

        # after node = yield ('N', nodeType) all slot nodes that are yielded
        # will be linked to node, until a ('T', node) is yielded.
        # If needed, you can resume this node again, after which new slot nodes
        # continue to be linked to this node.
        # If you resume a slot node, it all non slot nodes in the current context
        # will be linked to it.

        silent = self.silent
        tmObj = self.TF.tmObj
        info = tmObj.info

        if not self.good:
            return

        info("Following director... ", force=silent != DEEP)

        slotType = self.slotType
        errors = self.errors

        self.oslots = collections.defaultdict(set)
        self.nodeFeatures = collections.defaultdict(dict)
        self.edgeFeatures = collections.defaultdict(
            lambda: collections.defaultdict(dict)
        )
        self.nodes = collections.defaultdict(set)
        nodes = self.nodes

        self.curSeq = collections.Counter()
        self.curEmbedders = set()
        curEmbedders = self.curEmbedders

        self.stats = {
            actionType: 0
            for actionType in (self.S, self.N, self.T, self.R, self.D, self.F, self.E)
        }

        director(self)

        if not self.stats:
            self.good = False
            return

        for (actionType, amount) in sorted(self.stats.items()):
            info(f'"{actionType}" actions: {amount}', force=silent != DEEP)

        totalNodes = 0

        for (nType, lastSeq) in sorted(self.curSeq.items()):
            for seq in range(1, lastSeq + 1):
                nodes[nType].add(seq)
            slotRep = " = slot type" if nType == slotType else ""
            info(f'{lastSeq:>8} x "{nType}" node {slotRep}', tm=False)
            totalNodes += lastSeq
        info(f"{totalNodes:>8} nodes of all types", tm=False, force=silent != DEEP)

        self.totalNodes = totalNodes

        if curEmbedders:
            embedCount = collections.Counter()
            for (nType, seq) in curEmbedders:
                embedCount[nType] += 1
            for (nType, amount) in sorted(
                embedCount.items(),
                key=lambda x: (-x[1], x[0]),
            ):
                errors["Unterminated nodes"].append(f"{nType}: {amount} x")

        self._showErrors()

    def _removeUnlinked(self):
        silent = self.silent
        tmObj = self.TF.tmObj
        info = tmObj.info
        indent = tmObj.indent

        if not self.good and not self.force:
            return

        nodeTypes = self.curSeq
        nodes = self.nodes
        slotType = self.slotType
        oslots = self.oslots
        discardables = self.discardables
        nodeFeatures = self.nodeFeatures
        edgeFeatures = self.edgeFeatures

        unlinked = {}
        nDeleted = 0

        for (nType, seq) in discardables:
            unlinked.setdefault(nType, set()).add(seq)
            nDeleted += 1
            if (nType, seq) in oslots:
                del oslots[(nType, seq)]

        for nType in nodeTypes:
            if nType == slotType:
                continue
            for seq in range(1, nodeTypes[nType] + 1):
                if (nType, seq) not in oslots:
                    unlinked.setdefault(nType, set()).add(seq)

        if unlinked:
            info(
                f"Removing unlinked (of which {nDeleted} deleted) nodes ... ",
                force=silent != DEEP,
            )
            indent(level=2)
            totalRemoved = 0
            for (nType, seqs) in unlinked.items():
                seqs = sorted(seqs)
                theseNodes = nodes[nType]
                lSeqs = len(seqs)
                totalRemoved += lSeqs
                rep = " ..." if lSeqs > 5 else ""
                pl = "" if lSeqs == 1 else "s"
                info(
                    f'{lSeqs:>6} unlinked "{nType}" node{pl}: {seqs[0:5]}{rep}',
                    force=silent != DEEP,
                )
                for seq in seqs:
                    node = (nType, seq)
                    theseNodes.discard(seq)
                    for (f, fData) in nodeFeatures.items():
                        if node in fData:
                            del fData[node]
                    for (f, fData) in edgeFeatures.items():
                        if node in fData:
                            del fData[node]
                            for (fNode, toValues) in fData:
                                if node in toValues:
                                    del toValues[node]
            pl = "" if totalRemoved == 1 else "s"
            info(f"{totalRemoved:>6} unlinked node{pl}", force=silent != DEEP)
            self.totalNodes -= totalRemoved
            info(f"Leaving {self.totalNodes:>6} nodes", force=silent != DEEP)
            indent(level=1)

    def _checkGraph(self):
        silent = self.silent
        tmObj = self.TF.tmObj
        info = tmObj.info

        if not self.good and not self.force:
            return

        info("checking for nodes and edges ... ", force=silent != DEEP)

        nodes = self.nodes
        errors = self.errors
        edgeFeatures = self.edgeFeatures

        # edges refer to nodes

        for (k, featureData) in edgeFeatures.items():
            for nFrom in featureData:
                (nType, seq) = nFrom
                if nType not in nodes or seq not in nodes[nType]:
                    errors["Edge feature: illegal node"].append(
                        f'"{k}": from-node  {nFrom} not in node set'
                    )
                    continue
                for nTo in featureData[nFrom]:
                    (nType, seq) = nTo
                    if nType not in nodes or seq not in nodes[nType]:
                        errors["Edge feature: illegal node"].append(
                            f'"{k}": to-node  {nTo} not in node set'
                        )

        self._showErrors()

    def _checkFeatures(self):
        silent = self.silent
        tmObj = self.TF.tmObj
        info = tmObj.info

        if not self.good and not self.force:
            return

        info("checking (section) features ... ", force=silent != DEEP)

        intFeatures = self.intFeatures
        metaData = self.metaData

        nodes = self.nodes
        nodeFeatures = self.nodeFeatures
        edgeFeatures = self.edgeFeatures

        errors = self.errors

        for feat in intFeatures:
            if (
                feat not in WARP
                and feat not in nodeFeatures
                and feat not in edgeFeatures
            ):
                errors["intFeatures"].append(
                    f'"{feat}" is declared as integer valued, '
                    "but this feature does not occur"
                )
        for nType in self.sectionTypes:
            if nType not in nodes:
                errors["sections"].append(
                    f'node type "{nType}" is declared as a section type, '
                    "but this node type does not occur"
                )
        for feat in self.sectionFeatures:
            if feat not in nodeFeatures:
                errors["sections"].append(
                    f'"{feat}" is declared as a section feature, '
                    "but this node feature does not occur"
                )
        for nType in self.structureTypes:
            if nType not in nodes:
                errors["structure"].append(
                    f'node type "{nType}" is declared as a structure type,'
                    f" but this node type does not occur"
                )
        for feat in self.structureFeatures:
            if feat not in nodeFeatures:
                errors["structure"].append(
                    f'"{feat}" is declared as a structure feature, '
                    "but this node feature does not occur"
                )
                nodeFeatures[feat] = {}

        sectionSet = self.sectionSet
        structureSet = self.structureSet
        featFromSectionType = self.featFromSectionType
        featFromStructureType = self.featFromStructureType

        for nType in nodes:
            if nType in structureSet:
                feat = featFromStructureType[nType]
                for seq in nodes[nType]:
                    if (nType, seq) not in nodeFeatures[feat]:
                        errors["structure features"].append(
                            f'"structure element "{nType}" {seq} '
                            f'has no value for "{feat}"'
                        )
            if nType in sectionSet:
                feat = featFromSectionType[nType]
                for seq in nodes[nType]:
                    if (nType, seq) not in nodeFeatures[feat]:
                        errors["section features"].append(
                            f'"section element "{nType}" {seq} '
                            f'has no value for "{feat}"'
                        )

        for feat in self.textFeatures:
            if feat not in nodeFeatures:
                errors["text formats"].append(
                    f'"{feat}" is used in a text format, '
                    "but this node feature does not occur"
                )

        for feat in WARP:
            if feat in nodeFeatures or feat in edgeFeatures:
                errors[feat].append(f'Do not construct the "{feat}" feature yourself')

        for feat in sorted(nodeFeatures) + sorted(edgeFeatures):
            if feat not in self.metaData:
                errors["feature metadata"].append(
                    f'node feature "{feat}" has no metadata'
                )

        for feat in sorted(metaData):
            if (
                feat
                and feat not in WARP
                and feat not in nodeFeatures
                and feat not in edgeFeatures
            ):
                errors["feature metadata"].append(
                    f'node feature "{feat}" has metadata but does not occur'
                )

        for (feat, featData) in sorted(nodeFeatures.items()):
            if None in featData:
                errors["feature values assigned to None"].append(
                    f'node feature "{feat}" has a node None'
                )
        for (feat, featData) in sorted(edgeFeatures.items()):
            if None in featData:
                errors["feature values assigned to None"].append(
                    f'edge feature "{feat}" has a from-node None'
                )
            for toValues in featData.values():
                if None in toValues:
                    errors["feature values assigned to None"].append(
                        f'edge feature "{feat}" has a to-node None'
                    )

        for (feat, featData) in sorted(edgeFeatures.items()):
            if feat in WARP:
                continue
            hasValues = False
            for (nodeTo, toValues) in featData.items():
                if any(v is not None for v in toValues.values()):
                    hasValues = True
                    break

            if not hasValues:
                edgeFeatures[feat] = {
                    nodeTo: set(toValues) for (nodeTo, toValues) in featData.items()
                }
            metaData.setdefault(feat, {})["edgeValues"] = hasValues

        for feat in intFeatures:
            if feat in WARP:
                continue
            if feat in nodeFeatures:
                featData = nodeFeatures[feat]
                for (k, v) in featData.items():
                    if not isInt(v):
                        (nType, node) = k
                        errors["Not a number"].append(
                            f'"node feature "{feat}": {nType} {node} => "{v}"'
                        )
            if feat in edgeFeatures and metaData[feat]["edgeValues"]:
                featData = edgeFeatures[feat]
                for (fromNode, toValues) in featData.items():
                    (fType, fNode) = fromNode
                    for (toNode, v) in toValues.items():
                        (tType, tNode) = toNode
                        if not isInt(v):
                            errors["Not a number"].append(
                                f'"edge feature "{feat}":'
                                f' {fType} {fNode} ="{v}"=> {tType} {tNode}'
                            )

        self._showErrors()

    def _reorderNodes(self):
        silent = self.silent
        tmObj = self.TF.tmObj
        info = tmObj.info

        if not self.good and not self.force:
            return

        info("reordering nodes ...", force=silent != DEEP)

        nodeTypes = self.curSeq
        nodes = self.nodes
        oslots = self.oslots
        slotType = self.slotType
        slotKeys = self.slotKeys

        nTypes = (slotType,) + tuple(
            sorted(nType for nType in nodes if nType != slotType)
        )

        self.nodeMap = {}
        self.maxSlot = nodeTypes[slotType]

        nodeMap = self.nodeMap
        maxSlot = self.maxSlot

        newN = 0

        # we build a node map that we use later on to remap the features
        # However, we do not have to remap the otype feature.
        # And we only have to remap the oslots feature if the order of the slots
        # is changed.

        # first we reorder the slots, if needed. As a consequence, we have to
        # 1. map the old slot nodes to the new slot nodes
        # 2. adapt the oslots: each node must be linked to the new slots
        # Because of the node map, _reassign features will adjust the other
        # node and edge features for the slots

        sortedSeqs = range(1, maxSlot + 1)

        if len(slotKeys) > 0:
            info(f'Sorting {maxSlot} slots (node type "{slotType}")')
            sortedSeqs = sorted(sortedSeqs, key=lambda x: (slotKeys.get(x, ""), x))
        else:
            info("No slot sorting needed")

        for seq in sortedSeqs:
            newN += 1
            nodeMap[(slotType, seq)] = newN

        # now we adapt the oslots feature

        if len(slotKeys) > 0:
            self.oslots = {
                n: {nodeMap[(slotType, s)] for s in slots}
                for (n, slots) in oslots.items()
            }
            oslots = self.oslots

        for nType in nTypes:
            canonical = self._canonical(nType)
            if nType == slotType:
                continue

            seqs = nodes[nType]
            info(f'Sorting {len(seqs)} nodes of type "{nType}"')
            sortedSeqs = sorted(seqs, key=canonical)

            for seq in sortedSeqs:
                newN += 1
                nodeMap[(nType, seq)] = newN

        self.maxNode = newN
        info(f"Max node = {newN}", force=silent != DEEP)

        self._showErrors()

    def _canonical(self, nType):
        oslots = self.oslots

        def before(nodeA, nodeB):
            slotsA = oslots[(nType, nodeA)]
            slotsB = oslots[(nType, nodeB)]
            if slotsA == slotsB:
                return 0

            aWithoutB = slotsA - slotsB
            if not aWithoutB:
                return 1

            bWithoutA = slotsB - slotsA
            if not bWithoutA:
                return -1

            aMin = min(aWithoutB)
            bMin = min(bWithoutA)
            return -1 if aMin < bMin else 1

        return functools.cmp_to_key(before)

    def _reassignFeatures(self):
        silent = self.silent
        tmObj = self.TF.tmObj
        info = tmObj.info
        indent = tmObj.indent

        if not self.good and not self.force:
            return

        info("reassigning feature values ...", force=silent != DEEP)

        nodeMap = self.nodeMap
        oslots = self.oslots
        nodeFeatures = self.nodeFeatures
        edgeFeatures = self.edgeFeatures

        otype = {n: nType for ((nType, seq), n) in nodeMap.items()}
        oslots = {nodeMap[node]: slots for (node, slots) in oslots.items()}

        nodeFeaturesProto = self.nodeFeatures
        edgeFeaturesProto = self.edgeFeatures

        nodeFeatures = collections.defaultdict(dict)
        edgeFeatures = collections.defaultdict(lambda: collections.defaultdict(dict))

        indent(level=2)

        for k in sorted(nodeFeaturesProto):
            featureDataProto = nodeFeaturesProto[k]
            ln = len(featureDataProto)
            pl = "" if ln == 1 else "s"
            info(f'node feature "{k}" with {ln} node{pl}', tm=False)
            featureData = {}
            for (node, value) in featureDataProto.items():
                featureData[nodeMap[node]] = value
            nodeFeatures[k] = featureData

        for k in sorted(edgeFeaturesProto):
            featureDataProto = edgeFeaturesProto[k]
            ln = len(featureDataProto)
            pl = "" if ln == 1 else "s"
            info(f'edge feature "{k}" with {ln} start node{pl}', tm=False)
            featureData = {}
            for (nodeFrom, toValues) in featureDataProto.items():
                if type(toValues) is set:
                    toData = {nodeMap[nodeTo] for nodeTo in toValues}
                else:
                    toData = {}
                    for (nodeTo, value) in toValues.items():
                        toData[nodeMap[nodeTo]] = value
                featureData[nodeMap[nodeFrom]] = toData
            edgeFeatures[k] = featureData

        nodeFeatures["otype"] = otype
        edgeFeatures["oslots"] = oslots

        indent(level=1)

        self.oslots = None
        self.otype = None
        self.nodeFeatures = nodeFeatures
        self.edgeFeatures = edgeFeatures

        self._showErrors()
