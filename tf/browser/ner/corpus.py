"""Access to the corpus.

Contains a bunch of instant methods to access corpus material.

To see how this fits among all the modules of this package, see
`tf.browser.ner.annotate` .

All access to the TF-API should happen through methods in this class.

At this point we have the information from the settings and from the corpus.
By collecting all corpus access methods in one class, we have good conceptual
control over how to customize the annotator for different corpora.
"""


import re

from .settings import Settings, TOOLKEY
from .helpers import makeCss


WHITE_RE = re.compile(r"""\s{2,}""", re.S)
NON_ALPHA_RE = re.compile(r"""[^\w ]""", re.S)


class Corpus(Settings):
    def __init__(self):
        super().__init__()

        app = self.app
        api = app.api
        F = api.F
        Fs = api.Fs
        L = api.L
        T = api.T
        slotType = F.otype.slotType

        self.slotType = slotType
        """The node type of the slots in the corpus."""

        context = app.context
        self.style = context.defaultClsOrig
        self.ltr = context.direction

        settings = self.settings
        features = settings.features
        keywordFeatures = settings.keywordFeatures

        self.css = app.loadToolCss(TOOLKEY, makeCss(features, keywordFeatures))

        bucketType = settings.bucketType
        entityType = settings.entityType
        strFeature = settings.strFeature
        afterFeature = settings.afterFeature

        def getSlots(node):
            return L.d(node, otype=slotType)

        def checkFeature(feat):
            return api.isLoaded(feat, pretty=False)[feat] is not None

        def getFVal(feat, node):
            return Fs(feat).v(node)

        def getAfter():
            return Fs(afterFeature).v

        def getStr():
            return Fs(strFeature).v

        strv = getStr()
        afterv = getAfter()

        def getText(slots):
            text = "".join(f"""{strv(s)}{afterv(s) or ""}""" for s in slots).strip()
            text = WHITE_RE.sub(" ", text)
            return text

        def getTextR(node):
            slots = L.d(node, otype=slotType)
            text = "".join(f"""{strv(s)}{afterv(s) or ""}""" for s in slots).strip()
            text = WHITE_RE.sub(" ", text)
            return text

        def getTokens(node):
            return [(t, strv(t)) or "" for t in L.d(node, otype=slotType)]

        def getStrings(tokenStart, tokenEnd):
            return tuple(
                token
                for t in range(tokenStart, tokenEnd + 1)
                if (token := (strv(t) or "").strip())
            )

        def getContext(node):
            return L.d(T.sectionTuple(node)[1], otype=bucketType)

        def get0(slots):
            text = getText(slots)
            text = NON_ALPHA_RE.sub("", text)
            text = text.replace(" ", ".").strip(".").lower()
            return text

        def get1(slots):
            return settings.defaultValues[features[1]]

        def getBucketNodes():
            return F.otype.s(bucketType)

        def getEntityNodes():
            return F.otype.s(entityType)

        def sectionHead(node):
            return app.sectionStrFromNode(node)

        self.checkFeature = checkFeature
        """Checks whether a feature is loaded in the corpus.

        Parameters
        ----------
        feat: string
            The name of the feature

        Returns
        -------
        bool
            Whether the feature is loaded in this corpus.
        """

        self.getFVal = getFVal
        """Retrieves the value of a feature for a node.

        Parameters
        ----------
        feat: string
            The name of the feature
        node: int
            The node whose feature value we need

        Returns
        -------
        string or integer or void
            The value of the feature for that node, if there is a value.
        """

        self.getStr = getStr
        """Delivers a function that retrieves the material of a slot.

        Returns
        -------
        function
            It accepts integers, presumably slots, and delivers the value
            of the *str* feature, which is configured in `ner/config.yaml`
            under key `strFeature` .
        """

        self.getAfter = getAfter
        """Delivers a function that retrieves the material after a slot.

        Returns
        -------
        function
            It accepts integers, presumably slots, and delivers the value
            of the *after* feature, which is configured in `ner/config.yaml`
            under key `afterFeature` .
        """

        self.getSlots = getSlots
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

        self.getText = getText
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
                Leading and trailing whitespace is stripped, and inner whitespace is
                normalized to a single space.
                The text of the individual slots is joined by means of a single
                white space, also in corpora that may have zero space between words.
        """

        self.getTextR = getTextR
        """Gets the text for a non-slot node.

        It first determines the slots contained in a node, and then uses
        `Settings.getText()` to return the text of those slots.

        Parameters
        ----------
        node: integer
            The nodes for whose slots we want the text.

        Returns
        -------
        string
        """

        self.getTokens = getTokens
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

        self.getStrings = getStrings
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
            as far as these values are not purely whitespace.
            Also, the string values are stripped from leading and trailing whitespace.
        """

        self.getContext = getContext
        """Gets the context buckets around a node.

        We start from a node and find the section node of intermediate level
        that contains that node. Then we return all buckets contained in that
        section.
        """

        self.get0 = get0
        """Makes an identifier value out of a number of slots.

        This acts as the default value for the `eid` feature of new
        entities.

        Starting with the whitespace-normalized text of a number of slots,
        the string is lowercased, non-alphanumeric characters are stripped,
        and spaces are replaced by dots.
        """

        self.get1 = get1
        """Return a fixed value specified in the corpus-dependent settings.

        This acts as the default value ofr the `kind` feature of new
        entities.
        """

        self.getBucketNodes = getBucketNodes
        """Return all bucket nodes."""

        self.getEntityNodes = getEntityNodes
        """Return all entity nodes."""

        self.sectionHead = sectionHead
        """Provide a section heading.

        Parameters
        ----------
        node: integer
            The node whose section head we need.

        Returns
        -------
        string
        """

        self.featureDefault = {
            features[0]: get0,
            features[1]: get1,
        }
        """Functions that deliver default values for the entity features."""
