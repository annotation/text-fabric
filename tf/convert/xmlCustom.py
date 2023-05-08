import re
from lxml import etree
from io import BytesIO

from tf.core.helpers import console
from tf.core.files import initTree, unexpanduser as ux

from tf.convert.helpers import (
    ZWSP,
    NEST,
    CHAR,
    FOLDER,
    FILE
)


def convertTaskDefault(self):
    """Implementation of the "convert" task.

    It sets up the `tf.convert.walker` machinery and runs it.

    Returns
    -------
    boolean
        Whether the conversion was successful.
    """
    if not self.good:
        return

    verbose = self.verbose
    tfPath = self.tfPath
    xmlPath = self.xmlPath

    if verbose == 1:
        console(f"XML to TF converting: {ux(xmlPath)} => {ux(tfPath)}")

    slotType = CHAR
    otext = {
        "fmt:text-orig-full": "{ch}",
        "sectionFeatures": "folder,file",
        "sectionTypes": "folder,file",
    }
    intFeatures = {"empty"}
    featureMeta = dict(
        str=dict(description="the text of a word"),
        after=dict(description="the text after a word till the next word"),
        empty=dict(
            description="whether a slot has been inserted in an empty element"
        ),
    )

    featureMeta["ch"] = dict(description="the unicode character of a slot")
    featureMeta[FOLDER] = dict(description=f"name of source {FOLDER}")
    featureMeta[FILE] = dict(description=f"name of source {FILE}")

    self.intFeatures = intFeatures
    self.featureMeta = featureMeta

    tfVersion = self.tfVersion
    xmlVersion = self.xmlVersion
    generic = self.generic
    generic["sourceFormat"] = "XML"
    generic["version"] = tfVersion
    generic["xmlVersion"] = xmlVersion

    initTree(tfPath, fresh=True, gentle=True)

    cv = self.getConverter()

    self.good = cv.walk(
        getDirector(self),
        slotType,
        otext=otext,
        generic=generic,
        intFeatures=intFeatures,
        featureMeta=featureMeta,
        generateTf=True,
    )


def getDirector(self):
    """Factory for the director function.

    The `tf.convert.walker` relies on a corpus dependent `director` function
    that walks through the source data and spits out actions that
    produces the TF dataset.

    We collect all needed data, store it, and define a local director function
    that has access to this data.

    You can also include a copy of this file in the script that constructs the
    object. If you then tweak it, you can pass it to the XML() object constructor.

    Returns
    -------
    function
        The local director function that has been constructed.
    """
    PASS_THROUGH = set(
        """
        xml
        """.strip().split()
    )

    # CHECKING

    verbose = self.verbose
    xmlPath = self.xmlPath
    featureMeta = self.featureMeta
    transform = self.transform

    transformFunc = (
        (lambda x: BytesIO(x.encode("utf-8")))
        if transform is None
        else (lambda x: BytesIO(transform(x).encode("utf-8")))
    )

    parser = self.getParser()

    # WALKERS

    WHITE_TRIM_RE = re.compile(r"\s+", re.S)

    def walkNode(cv, cur, node):
        """Internal function to deal with a single element.

        Will be called recursively.

        Parameters
        ----------
        cv: object
            The convertor object, needed to issue actions.
        cur: dict
            Various pieces of data collected during walking
            and relevant for some next steps in the walk.
        node: object
            An lxml element node.
        """
        tag = etree.QName(node.tag).localname
        cur[NEST].append(tag)

        beforeChildren(cv, cur, node, tag)

        for child in node.iterchildren(tag=etree.Element):
            walkNode(cv, cur, child)

        afterChildren(cv, cur, node, tag)
        cur[NEST].pop()
        afterTag(cv, cur, node, tag)

    def addSlot(cv, cur, ch):
        """Add a slot.

        Whenever we encounter a character, we add it as a new slot.
        If needed, we start/terminate word nodes as well.

        Parameters
        ----------
        cv: object
            The convertor object, needed to issue actions.
        cur: dict
            Various pieces of data collected during walking
            and relevant for some next steps in the walk.
        ch: string
            A single character, the next slot in the result data.
        """
        s = cv.slot()
        cv.feature(s, ch=ch)

    def beforeChildren(cv, cur, node, tag):
        """Actions before dealing with the element's children.

        Parameters
        ----------
        cv: object
            The convertor object, needed to issue actions.
        cur: dict
            Various pieces of data collected during walking
            and relevant for some next steps in the walk.
        node: object
            An lxml element node.
        tag: string
            The tag of the lxml node.
        """
        if tag not in PASS_THROUGH:
            curNode = cv.node(tag)
            cur["elems"].append(curNode)
            atts = {etree.QName(k).localname: v for (k, v) in node.attrib.items()}
            if len(atts):
                cv.feature(curNode, **atts)

        if node.text:
            textMaterial = WHITE_TRIM_RE.sub(" ", node.text)
            for ch in textMaterial:
                addSlot(cv, cur, ch)

    def afterChildren(cv, cur, node, tag):
        """Node actions after dealing with the children, but before the end tag.

        Here we make sure that the newline elements will get their last slot
        having a newline at the end of their `after` feature.

        Parameters
        ----------
        cv: object
            The convertor object, needed to issue actions.
        cur: dict
            Various pieces of data collected during walking
            and relevant for some next steps in the walk.
        node: object
            An lxml element node.
        tag: string
            The tag of the lxml node.
        """
        if tag not in PASS_THROUGH:
            curNode = cur["elems"].pop()

            if not cv.linked(curNode):
                s = cv.slot()
                cv.feature(s, ch=ZWSP, empty=1)

            cv.terminate(curNode)

    def afterTag(cv, cur, node, tag):
        """Node actions after dealing with the children and after the end tag.

        This is the place where we proces the `tail` of an lxml node: the
        text material after the element and before the next open/close
        tag of any element.

        Parameters
        ----------
        cv: object
            The convertor object, needed to issue actions.
        cur: dict
            Various pieces of data collected during walking
            and relevant for some next steps in the walk.
        node: object
            An lxml element node.
        tag: string
            The tag of the lxml node.
        """
        if node.tail:
            tailMaterial = WHITE_TRIM_RE.sub(" ", node.tail)
            for ch in tailMaterial:
                addSlot(cv, cur, ch)

    def director(cv):
        """Director function.

        Here we program a walk through the XML sources.
        At every step of the walk we fire some actions that build TF nodes
        and assign features for them.

        Because everything is rather dynamic, we generate fairly standard
        metadata for the features.

        Parameters
        ----------
        cv: object
            The convertor object, needed to issue actions.
        """
        cur = {}

        i = 0
        for (xmlFolder, xmlFiles) in self.getXML():
            console(f"Start folder {xmlFolder}:")

            cur[FOLDER] = cv.node(FOLDER)
            cv.feature(cur[FOLDER], folder=xmlFolder)

            for xmlFile in xmlFiles:
                i += 1
                console(f"\r{i:>4} {xmlFile:<50}", newline=False)

                cur[FILE] = cv.node(FILE)
                cv.feature(cur[FILE], file=xmlFile.removesuffix(".xml"))

                with open(f"{xmlPath}/{xmlFolder}/{xmlFile}", encoding="utf8") as fh:
                    text = fh.read()
                    text = transformFunc(text)
                    tree = etree.parse(text, parser)
                    root = tree.getroot()
                    cur[NEST] = []
                    cur["elems"] = []
                    walkNode(cv, cur, root)

                addSlot(cv, cur, None)
                cv.terminate(cur[FILE])

            console("")
            console(f"End   folder {xmlFolder}")
            cv.terminate(cur[FOLDER])

        console("")

        for fName in featureMeta:
            if not cv.occurs(fName):
                cv.meta(fName)
        for fName in cv.features():
            if fName not in featureMeta:
                cv.meta(
                    fName,
                    description=f"this is XML attribute {fName}",
                    valueType="str",
                )

        if verbose == 1:
            console("source reading done")
        return True

    return director
