"""
.. include:: ../../docs/compose/nodemaps.md
"""

import sys
import collections
import time
from itertools import chain


STAT_LABELS = collections.OrderedDict(
    b="unique, perfect",
    d="multiple, one perfect",
    c="unique, imperfect",
    f="multiple, cleanly composed",
    e="multiple, non-perfect",
    a="not mapped",
)

TIMESTAMP = None


def _duration():
    global TIMESTAMP
    if TIMESTAMP is None:
        TIMESTAMP = time.time()

    interval = time.time() - TIMESTAMP
    if interval < 10:
        return "{: 2.2f}s".format(interval)
    interval = int(round(interval))
    if interval < 60:
        return "{:>2d}s".format(interval)
    if interval < 3600:
        return "{:>2d}m {:>02d}s".format(interval // 60, interval % 60)
    return "{:>2d}h {:>02d}m {:>02d}s".format(
        interval // 3600, (interval % 3600) // 60, interval % 60
    )


def caption(level, heading, good=None, newLine=True, continuation=False):
    prefix = "" if good is None else "SUCCES " if good else "FAILURE "
    duration = "" if continuation else "{:>11} ".format(_duration())
    reportHeading = "{}{}{}".format(duration, prefix, heading)

    if level == 0:  # non-heading message
        decoration = "" if continuation else "| "
        formattedString = """{}{}""".format(decoration, reportHeading)
    elif level == 1:  # pipeline level
        formattedString = """
##{}##
# {} #
# {} #
# {} #
##{}##
""".format(
            "#" * 90,
            " " * 90,
            "{:<90}".format(reportHeading),
            " " * 90,
            "#" * 90,
        )
    elif level == 2:  # repo level
        formattedString = """
**{}**
* {} *
* {} *
* {} *
**{}**
""".format(
            "*" * 90,
            " " * 90,
            "{:<90}".format(reportHeading),
            " " * 90,
            "*" * 90,
        )
    elif level == 3:  # task level
        formattedString = """
--{}--
- {} -
--{}--
""".format(
            "-" * 90,
            "{:<90}".format(reportHeading),
            "-" * 90,
        )
    elif level == 4:  # caption within task execution
        formattedString = """..{}..
. {} .
..{}..""".format(
            "." * 90,
            "{:<90}".format(reportHeading),
            "." * 90,
        )
    if newLine:
        print(formattedString)
    else:
        sys.stdout.write(formattedString)


class Versions:
    def __init__(self, api, va, vb, slotMap=None):
        """Map the nodes of a nodetype between two versions of a TF dataset.

        If this object is initialized with a `slotMap`, it can
        extend that mapping to a complete node mapping and save the mapping
        as an `f"omap#{va}-{vb}"` edge feature in the dataset version `vb`.

        Without a slotMap, and assuming such an omap edge is present,
        it can map node features between the versions.

        Parameters
        ----------
        api: dict
            TF-API objects to several versions of a dataset, keyed by version label
        va: string
            version label of the version whose nodes are the source of the mapping
        vb: string
            version label of the version whose nodes are the target of the mapping
        slotMap: dict, optional `None`
            The actual mapping between slots of the old version and the new version
        """
        self.api = api
        self.va = va
        self.vb = vb
        self.edge = slotMap
        self.good = True
        for v in (va, vb):
            if va not in api:
                print(f"No TF-API for version {va} in the `api` parameter.")
                self.good = False

        if not self.good:
            return

        self.La = api[va].L
        self.Lb = api[vb].L
        self.Ea = api[va].E
        self.Esa = api[va].Es
        self.Eb = api[vb].E
        self.Esb = api[vb].Es
        self.Fa = api[va].F
        self.Fsa = api[va].Fs
        self.Fb = api[vb].F
        self.Fsb = api[vb].Fs
        self.TFa = api[va].TF
        self.TFb = api[vb].TF

        self.diagnosis = {}

    def makeNodeMapping(self, nodeType):
        va = self.va
        vb = self.vb
        Lb = self.Lb
        Ea = self.Ea
        Eb = self.Eb
        Fa = self.Fa

        Lub = Lb.u
        Eosa = Ea.oslots.s
        Eosb = Eb.oslots.s
        otypesa = Fa.otype.s

        edge = self.edge

        if edge is None:
            print("Cannot make node mapping if no slot mapping is given")
            return False

        caption(2, "Mapping {} nodes {} ==> {}".format(nodeType, va, vb))

        diag = {}
        caption(
            0, "Extending slot mapping {} ==> {} for {} nodes".format(va, vb, nodeType)
        )
        for n in otypesa(nodeType):
            slots = Eosa(n)
            mappedSlots = set(
                chain.from_iterable(set(edge[s]) for s in slots if s in edge)
            )
            mappedNodes = set(
                chain.from_iterable(set(Lub(s, nodeType)) for s in mappedSlots)
            )
            result = {}
            nMs = len(mappedNodes)
            if nMs == 0:
                diag[n] = "a"

            elif nMs >= 1:
                theseMSlots = {}
                for m in mappedNodes:
                    mSlots = set(Eosb(m))
                    dis = len(mappedSlots | mSlots) - len(mappedSlots & mSlots)
                    result[m] = dis
                    theseMSlots[m] = mSlots

                # we wait further case analysis before we put these counterparts of n into the edge

                if nMs == 1:
                    m = list(mappedNodes)[0]
                    dis = result[m]
                    if dis == 0:
                        diag[n] = "b"
                        edge[n] = {m: None}
                        # this is the most freqent case, hence an optimization: no dis value.
                        # all other cases require the dis value to be passed on, even if 0
                    else:
                        diag[n] = "c"
                        edge[n] = {m: dis}
                else:
                    edge[n] = result
                    dis = min(result.values())
                    if dis == 0:
                        diag[n] = "d"
                    else:
                        allMSlots = set(
                            chain.from_iterable(
                                set(theseMSlots[m]) for m in mappedNodes
                            )
                        )
                        composed = allMSlots == mappedSlots and sum(
                            result.values()
                        ) == len(mappedSlots) * (len(mappedNodes) - 1)

                        if composed:
                            diag[n] = "f"
                        else:
                            diag[n] = "e"

        self.diagnosis[nodeType] = diag
        caption(0, "\tDone")

    def exploreNodeMapping(self, nodeType):
        va = self.va
        vb = self.vb
        diagnosis = self.diagnosis

        caption(4, "Statistics for {} ==> {} ({})".format(va, vb, nodeType))

        diag = diagnosis[nodeType]
        total = len(diag)
        if total == 0:
            return

        reasons = collections.Counter()

        for (n, dia) in diag.items():
            reasons[dia] += 1

        caption(0, "\t{:<30} : {:6.2f}% {:>7}x".format("TOTAL", 100, total))
        for stat in STAT_LABELS:
            statLabel = STAT_LABELS[stat]
            amount = reasons[stat]
            if amount == 0:
                continue
            perc = 100 * amount / total
            caption(0, "\t{:<30} : {:6.2f}% {:>7}x".format(statLabel, perc, amount))

    def getDiagnosis(self, node=None, label=None):
        """Show the diagnosis of a mapping.

        You can get various amounts of information about this:

        *    A dictionary that maps all nodes of a given type to a diagnostic label
        *    A list of nodes of a node type that have a given diagnostic label
        *    The label of a given node

        Parameters
        ----------
        node: string | int, optional `None`
            The node or node type that you want to diagnose.
            If a string, it is a node type, and you get information about the nodes
            of that node type.
            If an int, it is a node, and you get information about that node.
            If `None`, you get information about all nodes.

        label: char, optional `None`
            If given, it is a diagnostic label (see `tf.compose.nodemaps`),
            and the result is dependent on the value passed to *node*:
            if that is a single node, a boolean is returned telling whether that node
            has the given label; if that is a node type, a tuple is returned of all
            nodes in that node type that have this label;
            if that is None, a tuple is returned of all nodes with that label.

            If not given, the result depends again on the value passed to *node*:
            if that is a single node, you get its diagnostic label;
            if that is a node type, you get a dict, keyed by node, and valued
            by diagnostic label, for all nodes in the node type;
            if that is None, you get a dictionary keyed by node, and valued
            by diagnostic label but now for all nodes.
        """

        diagnosis = self.diagnosis
        Fa = self.Fa
        otypesa = Fa.otype.s

        if label is None:
            return (
                dict(chain.from_iterable(x.items() for x in diagnosis.values()))
                if node is None
                else diagnosis.get(node, {})
                if type(node) is str
                else diagnosis.get(otypesa(node), {}).get(node, None)
                if type(node) is int
                else None
            )
        else:
            return (
                tuple(
                    y[0]
                    for y in chain.from_iterable(x.items() for x in diagnosis.values())
                    if y[1] == label
                )
                if node is None
                else tuple(
                    y[0] for y in diagnosis.get(node, {}).items() if y[1] == label
                )
                if type(node) is str
                else diagnosis.get(otypesa(node), {}).get(node, None) == label
                if type(node) is int
                else None
            )

    def legend(self):
        """Show the labels and descriptions of the diagnosis classes.

        When the mapping turns out to be not perfect for a node,
        the result can be categorized according to severity.

        This function shows that classification.
        See also `tf.compose.nodemaps`.
        """

        for (acro, desc) in STAT_LABELS.items():
            print(f"{acro} = {desc}")

    def omapName(self):
        va = self.va
        vb = self.vb
        return f"omap#{va}-{vb}"

    def writeMap(self):
        TFb = self.TFb
        va = self.va
        vb = self.vb
        edge = self.edge

        fName = self.omapName()
        caption(4, "Write edge as TF feature {}".format(fName))

        edgeFeatures = {fName: edge}
        metaData = {
            fName: {
                "about": "Mapping from the slots of version {} to version {}".format(
                    va, vb
                ),
                "encoder": "Text-Fabric tf.compose.nodemaps",
                "valueType": "int",
                "edgeValues": True,
            }
        }
        TFb.save(
            nodeFeatures={},
            edgeFeatures=edgeFeatures,
            metaData=metaData,
        )

    def makeVersionMapping(self):
        Fa = self.Fa

        self.diagnosis = {}

        nodeTypes = Fa.otype.all

        for nodeType in nodeTypes[0:-1]:
            self.makeNodeMapping(nodeType)
            self.exploreNodeMapping(nodeType)

        self.writeMap()

    def migrateFeatures(self, featureNames, location=None):
        """Migrate features from one version to another based on a node map.

        If you have a dataset with several features, and if there is a node map between
        the versions, you can migrate features from the older version to the newer.

        Parameters
        ----------
        featureNames: tuple
            The names of the features to migrate.
            They may be node features or edge features or both.
        location: string, optional `None`
            If absent, the migrated features will be saved in the newer dataset.
            Otherwise it is a path where the new features should be saved.
        """

        TFa = self.TFa
        TFb = self.TFb
        Fsa = self.Fsa
        Esb = self.Esb
        vb = self.vb

        emap = Esb(self.omapName()).f

        nodeFeatures = {}
        edgeFeatures = {}
        metaData = {}

        for featureName in featureNames:
            featureObj = Fsa(featureName)
            featureInfo = dict(featureObj.items())
            metaData[featureName] = featureObj.meta

            isEdge = TFa.features[featureName].isEdge
            edgeValues = featureObj.doValues if isEdge else False

            dest = edgeFeatures if isEdge else nodeFeatures
            dest[featureName] = {}
            dest = dest[featureName]

            if isEdge:
                if edgeValues:
                    for (n, ts) in featureInfo.items():
                        mapped = emap(n)
                        if mapped:
                            mappedts = {}
                            for (t, val) in ts.items():
                                tmapped = emap(t)
                                if tmapped:
                                    for tEntry in tmapped:
                                        mappedts[tEntry[0]] = val
                            for entry in mapped:
                                dest[entry[0]] = mappedts
                else:
                    for (n, ts) in featureInfo.items():
                        mapped = emap(n)
                        if mapped:
                            mappedts = set()
                            for t in ts:
                                tmapped = emap(t)
                                if tmapped:
                                    for tm in tmapped:
                                        mappedts.add(tm)
                            for m in mapped:
                                dest[m] = mappedts
            else:
                for (n, val) in featureInfo.items():
                    mapped = emap(n)
                    if mapped:
                        for entry in mapped:
                            dest[entry[0]] = val

        TFb.save(
            nodeFeatures=nodeFeatures,
            edgeFeatures=edgeFeatures,
            metaData=metaData,
            location=location,
            module=vb,
        )
