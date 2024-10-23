"""Access to the corpus.

Contains a bunch of instant methods to access corpus material.

All access to the TF API should happen through methods in this class.

At this point we have the information from the settings and from the corpus.
By collecting all corpus access methods in one class, we have good conceptual
control over how to customize the annotator for different corpora.
"""

import re
import collections

from ..core.files import annotateDir
from ..core.helpers import console

from .settings import Settings, TOOLKEY, makeCss
from .helpers import findCompile
from .match import entityMatch


WHITE_RE = re.compile(r"""\s{2,}""", re.S)
NON_ALPHA_RE = re.compile(r"""[^\w ]""", re.S)


class Corpus(Settings):
    def __init__(self):
        """Corpus dependent methods for the annotator.

        Everything that depends on the specifics of a corpus, such as getting its text,
        is collected here.

        If a corpus does not have a configuration file that tells TF which
        features to use for text representation, then we flag to the object
        instance that it is not properly set up.

        All methods that might fail because of this, are guarded by a check on this
        flag.

        These corpus dependent functions will be defined as local functions and put
        into a data member of the instance, rather than a method. Then we can pass
        those functions on to functional contexts where they can be executed faster
        than methods can.
        """
        app = self.app
        context = app.context
        appName = context.appName
        version = context.version

        self.appName = appName
        self.version = version

        (specDir, annoDir) = annotateDir(app, TOOLKEY)

        self.specDir = specDir
        self.annoDir = f"{annoDir}/{version}"
        self.sheetDir = f"{specDir}/specs"

        Settings.__init__(self)

        api = app.api
        F = api.F
        Fs = api.Fs
        L = api.L
        T = api.T
        C = api.C

        slotType = F.otype.slotType
        self.slotType = slotType
        """The node type of the slots in the corpus."""

        bucketType = T.sectionTypes[-1]
        self.bucketType = bucketType
        """The node type of the lowest level of sections.

        This wil be used as the *bucketType* into which the corpus is divided for
        the purpose of scoping and display in the entity browser.
        """

        seqFromNode = C.sections.data["seqFromNode"]
        nodeFromSeq = C.sections.data["nodeFromSeq"]

        settings = self.settings
        features = settings.features
        keywordFeatures = settings.keywordFeatures
        lineType = settings.lineType
        entityType = settings.entityType
        strFeature = settings.strFeature
        afterFeature = settings.afterFeature

        def slotsFromNode(node):
            return L.d(node, otype=slotType)

        self.slotsFromNode = slotsFromNode
        """Gets the slot nodes contained in a node.

        Parameters
        ----------
        node: integer
            The container node.

        Returns
        -------
        list of integer
            The slots in the container.
        """

        def checkFeature(feat):
            return api.isLoaded(feat, pretty=False)[feat] is not None

        self.checkFeature = checkFeature
        """Checks whether a feature is loaded in the corpus.

        Parameters
        ----------
        feat: string
            The name of the feature

        Returns
        -------
        boolean
            Whether the feature is loaded in this corpus.
        """

        def fvalFromNode(feat, node):
            return Fs(feat).v(node)

        self.fvalFromNode = fvalFromNode
        """Retrieves the value of a feature for a node.

        Parameters
        ----------
        feat: string
            The name of the feature
        node: integer
            The node whose feature value we need

        Returns
        -------
        string or integer or void
            The value of the feature for that node, if there is a value.
        """

        def getAfter():
            return Fs(afterFeature).v

        self.getAfter = getAfter
        """Delivers a function that retrieves the material after a slot.

        Returns
        -------
        function
            It accepts integers, presumably slots, and delivers the value
            of the *after* feature, which is configured in `ner/config.yaml`
            under key `afterFeature` .
        """

        def getStr():
            return Fs(strFeature).v

        self.getStr = getStr
        """Delivers a function that retrieves the material of a slot.

        Returns
        -------
        function
            It accepts integers, presumably slots, and delivers the value
            of the *str* feature, which is configured in `ner/config.yaml`
            under key `strFeature` .
        """

        if not checkFeature(strFeature) or not checkFeature(afterFeature):
            self.properlySetup = False
            return

        self.properlySetup = True
        """Whether the tool has been properly set up.

        This means that the configuration in `ner/config.yaml` or the
        default configuration work correctly with this corpus.
        If not, this attribute will prevent most of the methods
        from working: they fail silently.

        So users of corpora without any need for this tool will not be bothered
        by it.
        """

        context = app.context
        self.style = context.defaultClsOrig
        self.ltr = context.direction

        self.css = app.loadToolCss(TOOLKEY, makeCss(features, keywordFeatures))

        strv = getStr()
        afterv = getAfter()

        def textFromSlots(slots):
            text = "".join(f"""{strv(s)}{afterv(s) or ""}""" for s in slots).strip()
            # text = WHITE_RE.sub(" ", text)
            return text

        self.textFromSlots = textFromSlots
        """Gets the text of a number of slots.

        Parameters
        ----------
        slots: iterable of integer

        Returns
        -------
        string
            The concatenation of the representation of the individual slots.
            These representations are white-space trimmed at both sides,
            and the concatenation adds a single space between each adjacent pair
            of them.

            !!! caution "Space between slots"
                Leading and trailing white-space is stripped, and inner white-space is
                normalized to a single space.
                The text of the individual slots is joined by means of a single
                white-space, also in corpora that may have zero space between words.
        """

        def textFromNode(node):
            slots = L.d(node, otype=slotType)
            text = "".join(f"""{strv(s)}{afterv(s) or ""}""" for s in slots).strip()
            # text = WHITE_RE.sub(" ", text)
            return text

        self.textFromNode = textFromNode
        """Gets the text for a non-slot node.

        It first determines the slots contained in a node, and then uses
        `textFromSlots()` to return the text of those slots.

        Parameters
        ----------
        node: integer
            The nodes for whose slots we want the text.

        Returns
        -------
        string
        """

        def tokensFromNode(node, lineBoundaries=False):
            if lineBoundaries and lineType is None:
                lineBoundaries = False

            ts = L.d(node, otype=slotType)
            tokens = [(t, strv(t) or "") for t in ts]

            if not lineBoundaries:
                return tokens

            lines = L.d(node, otype=lineType) or []
            lineEnds = {L.d(ln, otype=slotType)[-1] for ln in lines}

            return (lineEnds, tokens)

        self.tokensFromNode = tokensFromNode
        """Gets the tokens contained in node.

        Parameters
        ----------
        node: integer
            The nodes whose slots we want.

        Returns
        -------
        list of tuple
            Each tuple is a pair of the slot number of the token and its
            string value. If there is no string value, the empty string is taken.
        """

        def stringsFromTokens(tokenStart, tokenEnd):
            return tuple(
                token
                for t in range(tokenStart, tokenEnd + 1)
                if (token := (strv(t) or "").strip())
            )

        self.stringsFromTokens = stringsFromTokens
        """Gets the text of the tokens occupying a sequence of slots.

        Parameters
        ----------
        tokenStart: integer
            The position of the starting token.
        tokenEnd: integer
            The position of the ending token.

        Returns
        -------
        tuple
            The members consist of the string values of the tokens in question,
            as far as these values are not purely white-space.
            Also, the string values are stripped from leading and trailing white-space.
        """

        def getContext(node):
            return L.d(T.sectionTuple(node)[1], otype=bucketType)

        self.getContext = getContext
        """Gets the context buckets around a node.

        We start from a node and find the section node of intermediate level
        that contains that node. Then we return all buckets contained in that
        section.

        Parameters
        ----------
        node: integer

        Returns
        -------
        tuple of integer
        """

        def getSeqFromNode(node):
            return seqFromNode[T.sectionTuple(node)[-1]]

        self.getSeqFromNode = getSeqFromNode
        """Gets the heading tuple of the section of a node.

        We need to treat headings as section numbers. So whatever the section features
        deliver for each level, integers or strings, we convert it in to integers,
        so that the first section gets number one, the second section number two,
        and so on. This we do for each level, so every section is mapped onto a tuple
        of integers.

        Parameters
        ----------
        node: integer
            The nodes whose heading we want.

        Returns
        -------
        tuple
            The tuple consists of sequence numbers per level, the most significant
            sections first.
            If the node itself is a section node, the last element is
            the heading of the given node.
        """

        def getSeqFromStr(string):
            result = app.nodeFromSectionStr(string)

            if type(result) is str:
                return (result, ())

            return ("", seqFromNode[result])

        self.getSeqFromStr = getSeqFromStr
        """Gets the heading tuple of a section string.

        As `getSeqFromNode`, but the input section is now given as a string.

        Parameters
        ----------
        string: string
            The heading, represented as string of the section we want.

        Returns
        -------
        string, tuple
            The tuple consists of sequence numbers per level, the most significant
            sections first.
            If there is an error, the string part will contain the error message,
            and the tuple part is the empty tuple.
            In case of no error, the string part is the empty string.
        """

        def getStrFromSeq(seq):
            node = nodeFromSeq[seq]
            return app.sectionStrFromNode(node)

        self.getStrFromSeq = getStrFromSeq
        """Gets the heading string from a sequence number tuple of a section.

        Parameters
        ----------
        seq: tuple
            The heading, represented as tuple of sequence numbers

        Returns
        -------
        string
            The heading string of the section
        """

        def getEid(slots):
            text = textFromSlots(slots)
            text = NON_ALPHA_RE.sub("", text)
            text = text.replace(" ", ".").strip(".").lower()
            return text

        self.getEid = getEid
        """Makes an identifier value out of a number of slots.

        This acts as the default value for the `eid` feature of new
        entities.

        Starting with the white-space-normalized text of a number of slots,
        the string is lowercased, non-alphanumeric characters are stripped,
        and spaces are replaced by dots.

        Parameters
        ----------
        slots: iterable of integer
            The slots that contain the tokens to make an identifier from

        Returns
        -------
        string
            The identifier
        """

        def getKind(slots):
            return settings.defaultValues[features[1]]

        self.getKind = getKind
        """Return a fixed value specified in the corpus-dependent settings.

        This acts as the default value of the `kind` feature of new
        entities.

        Parameters
        ----------
        slots: iterable of integer
            Unlike in `getEid`, the result is not dependent on the text content,
            so this parameter is not used. It is here for uniformity.

        Returns
        -------
        string
            The default value for the *kind* feature for new entities.
        """

        def getBucketNodes():
            return F.otype.s(bucketType)

        self.getBucketNodes = getBucketNodes
        """Return all bucket nodes.

        Returns
        -------
        tuple
            All nodes of the bucket type.
        """

        def getEntityNodes():
            return F.otype.s(entityType)

        self.getEntityNodes = getEntityNodes
        """Return all entity nodes.

        Returns
        -------
        tuple
            All nodes of the entity type
        """

        def sectionHead(node, level=None):
            return app.sectionStrFromNode(node, level=level)

        self.sectionHead = sectionHead
        """Provide a section heading.

        Parameters
        ----------
        node: integer
            The node whose section head we need.
        level: integer, optional None
            If passed, the containing section of that level will be taken.

        Returns
        -------
        string
        """

        def checkBuckets(nodes):
            return {node for node in nodes if F.otype.v(node) == bucketType}

        self.checkBuckets = checkBuckets
        """Given a set of nodes, return the set of only its bucket nodes.

        Parameters
        ----------
        nodes: set of integer

        Returns
        -------
        set of int
        """

        self.featureDefault = {
            features[0]: getEid,
            features[1]: getKind,
        }
        """Functions that deliver default values for the entity features."""

    def filterContent(
        self,
        buckets=None,
        node=None,
        bFind=None,
        bFindC=None,
        bFindRe=None,
        anyEnt=None,
        eVals=None,
        trigger=None,
        qTokens=None,
        valSelect=None,
        freeState=None,
        showStats=None,
    ):
        """Filter the buckets according to a variety of criteria.

        Either the buckets of the whole corpus are filtered, or a given subset
        of buckets, or the set of buckets contained in a
        particular node, see parameters `node`, and `buckets`.

        **Bucket filtering**

        The parameters `bFind`, `bFindC`, `bFindRe`  specify a regular expression
        search on the texts of the buckets.

        The positions of the found occurrences are included in the result.

        The parameter `anyEnt` is a filter on the presence or absence of entities in
        buckets in general.

        **Entity filtering**

        The parameter `eVals` holds the values of a specific entity to look for.
        It is a tuple consisting of an entity id and an entity kind.

        **Occurrence filtering**

        The parameter `qTokens` is a sequence of tokens to look for.
        The occurrences that are found, can be filtered further by `valSelect`
        and `freeState`.

        In entity filtering and occurrence filtering, the matching occurrences
        are included in the result.

        Parameters
        ----------
        buckets: set of integer, optional None
            The set of buckets to filter, instead of the whole corpus.
            Works also if the parameter `node` is specified, which also restricts
            the buckets. If both are specified, their effect will be
            combined.
        node: integer, optional None
            Gets the context of the node, typically the intermediate-level section
            in which the node occurs. Then restricts the filtering to the buckets
            contained in the context, instead of the whole corpus.
        bFind: string, optional None
            A search pattern that filters the buckets, before applying the search
            for a token sequence.
        bFindC: string, optional None
            Whether the search is case sensitive or not.
        bFindRe: object, optional None
            A compiled regular expression.
            This function searches on `bFindRe`, but if it is None, it compiles
            `bFind` as regular expression and searches on that. If `bFind` itself
            is not None, of course.
        anyEnt: boolean, optional None
            If True, it wants all buckets that contain at least one already
            marked entity; if False, it wants all buckets that do not contain any
            already marked entity.
            If None, no filtering on existing entities is performed.
        eVals: tuple, optional None
            A sequence of values corresponding with the entity features `eid`
            and `kind`. If given, the function wants buckets that contain at least
            an entity with those properties.
        trigger: string, optional None
            If given, the function wants buckets that contain at least an
            entity that is triggered by this string. The entity in question must
            be the one given by the parameter `evals`.
        qTokens: tuple, optional None
            A sequence of tokens whose occurrences in the corpus will be looked up.
        valSelect: dict, optional None
            If present, the keys are the entity features (`eid` and `kind`),
            and the values are iterables of values that are allowed.

            These are additional feature values that we need to filter on.
            The results of searching for `eVals` or `qTokens` are filtered further.
            If a result is also an instance of an already marked entity,
            the properties of that entity will be compared feature by feature with
            the allowed values that `valSelect` specifies for that feature.
        freeState: boolean, optional None
            If True, found occurrences may not intersect with already marked up
            features.
            If False, found occurrences must intersect with already marked up features.
        showStats: boolean, optional None
            Whether to show statistics of the find.
            If None, it only shows gross totals, if False, it shows nothing,
            if True, it shows totals by feature.

        Returns
        -------
        list of tuples
            For each bucket that passes the filter, a tuple with the following
            members is added to the list:

            *   the TF node of the bucket;
            *   tokens: the tokens of the bucket, each token is a tuple consisting
                of the TF slot of the token and its string value;
            *   matches: the match positions of the found occurrences or entity;
            *   positions: the token positions of where the text of the bucket
                starts matching the `bFindRe`;

            If `browse` is True, also some stats are passed next to the list
            of results.
        """
        if not self.properlySetup:
            return []

        bucketType = self.bucketType
        settings = self.settings
        features = settings.features

        textFromNode = self.textFromNode
        tokensFromNode = self.tokensFromNode

        browse = self.browse
        setIsX = self.setIsX
        setData = self.getSetData()
        entityIndex = setData.entityIndex
        entityVal = setData.entityVal
        entitySlotVal = setData.entitySlotVal
        entitySlotAll = setData.entitySlotAll
        entitySlotIndex = setData.entitySlotIndex

        if setIsX:
            sheetData = self.getSheetData()
            triggerFromMatch = sheetData.triggerFromMatch
        else:
            triggerFromMatch = None

        bucketUniverse = (
            setData.buckets
            if buckets is None
            else tuple(sorted(self.checkBuckets(buckets)))
        )
        buckets = (
            bucketUniverse
            if node is None
            else tuple(sorted(set(bucketUniverse) & set(self.getContext(node))))
        )

        nFind = 0
        nEnt = {feat: collections.Counter() for feat in ("",) + features}
        nVisible = {feat: collections.Counter() for feat in ("",) + features}

        if bFindRe is None:
            if bFind is not None:
                (bFind, bFindRe, errorMsg) = findCompile(bFind, bFindC)
                if errorMsg:
                    console(errorMsg, error=True)

        hasEnt = eVals is not None
        hasQTokens = qTokens is not None and len(qTokens)
        hasOcc = not hasEnt and hasQTokens

        if hasEnt and eVals in entityVal:
            eSlots = entityVal[eVals]
            eStarts = {s[0]: s[-1] for s in eSlots}
        else:
            eStarts = {}

        useQTokens = qTokens if hasOcc else None

        requireFree = (
            True if freeState == "free" else False if freeState == "bound" else None
        )

        results = []

        for b in buckets:
            fValStats = {feat: collections.Counter() for feat in features}
            (fits, result) = entityMatch(
                entityIndex,
                eStarts,
                entitySlotVal,
                entitySlotAll,
                entitySlotIndex,
                triggerFromMatch,
                textFromNode,
                tokensFromNode,
                b,
                bFindRe,
                anyEnt,
                eVals,
                trigger,
                useQTokens,
                valSelect,
                requireFree,
                fValStats,
            )

            blocked = fits is not None and not fits

            if not blocked:
                nFind += 1

            for feat in features:
                theseStats = fValStats[feat]
                if len(theseStats):
                    theseNEnt = nEnt[feat]
                    theseNVisible = nVisible[feat]

                    for ek, n in theseStats.items():
                        theseNEnt[ek] += n
                        if not blocked:
                            theseNVisible[ek] += n

            nMatches = len(result[1])

            if nMatches:
                nEnt[""][None] += nMatches
                if not blocked:
                    nVisible[""][None] += nMatches

            if node is None:
                if fits is not None and not fits:
                    continue

                if (hasEnt or hasQTokens) and nMatches == 0:
                    continue

            results.append((b, *result))

        if browse:
            return (results, nFind, nVisible, nEnt)

        nResults = len(results)

        if showStats:
            pluralF = "" if nFind == 1 else "s"
            self.console(f"{nFind} {bucketType}{pluralF} satisfy the filter")
            for feat in ("",) + (() if anyEnt else features):
                if feat == "":
                    self.console("Combined features match:")
                    for ek, n in sorted(nEnt[feat].items()):
                        v = nVisible[feat][ek]
                        self.console(f"\t{v:>5} of {n:>5} x")
                else:
                    self.console(f"Feature {feat}: found the following values:")
                    for ek, n in sorted(nEnt[feat].items()):
                        v = nVisible[feat][ek]
                        self.console(f"\t{v:>5} of {n:>5} x {ek}")
        if showStats or showStats is None:
            pluralR = "" if nResults == 1 else "s"
            self.console(f"{nResults} {bucketType}{pluralR}")
        return results
