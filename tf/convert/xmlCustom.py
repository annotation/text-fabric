import re
from io import BytesIO

from tf.core.helpers import console
from tf.core.files import fileOpen, initTree, unexpanduser as ux

from tf.convert.helpers import ZWSP, XNEST, TNEST, CHAR, FOLDER, FILE


def convertTaskDefault(etree):
    if etree is None:
        def dummy(self):
            pass

        return dummy

    def convertTaskDefaultInner(self):
        """Implementation of the "convert" task.

        It sets up the `tf.convert.walker` machinery and runs it.

        Returns
        -------
        boolean
            Whether the conversion was successful.
        """
        if not self.good:
            return

        procins = self.procins
        verbose = self.verbose
        tfPath = self.tfPath
        xmlPath = self.xmlPath

        if verbose == 1:
            console(f"XML to TF converting: {ux(xmlPath)} => {ux(tfPath)}")
        if verbose >= 0:
            console(
                f"Processing instructions are {'treated' if procins else 'ignored'}"
            )

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
            empty=dict(description="whether a slot has been inserted in an empty element"),
        )

        featureMeta["ch"] = dict(description="the UNICODE character of a slot")
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
            getDirector(self, etree),
            slotType,
            otext=otext,
            generic=generic,
            intFeatures=intFeatures,
            featureMeta=featureMeta,
            generateTf=True,
        )

    return convertTaskDefaultInner


def getDirector(self, etree):
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

    verbose = self.verbose
    xmlPath = self.xmlPath
    featureMeta = self.featureMeta
    transform = self.transform
    renameAtts = self.renameAtts
    procins = self.procins

    transformFunc = (
        (lambda x: BytesIO(x.encode("utf-8")))
        if transform is None
        else (lambda x: BytesIO(transform(x).encode("utf-8")))
    )

    parser = self.getParser()

    # WALKERS

    WHITE_TRIM_RE = re.compile(r"\s+", re.S)

    def walkNode(cv, cur, xnode):
        """Internal function to deal with a single element.

        Will be called recursively.

        Parameters
        ----------
        cv: object
            The converter object, needed to issue actions.
        cur: dict
            Various pieces of data collected during walking
            and relevant for some next steps in the walk.
        xnode: object
            An LXML element node.
        """
        if procins and isinstance(xnode, etree._ProcessingInstruction):
            target = xnode.target
            tag = f"?{target}"
        else:
            tag = etree.QName(xnode.tag).localname

        atts = {etree.QName(k).localname: v for (k, v) in xnode.attrib.items()}
        atts = {renameAtts.get(k, k): v for (k, v) in atts.items()}

        cur[XNEST].append((tag, atts))

        beforeChildren(cv, cur, xnode, tag, atts)

        for child in xnode.iterchildren(
            tag=(etree.Element, etree.ProcessingInstruction)
            if procins
            else etree.Element
        ):
            walkNode(cv, cur, child)

        afterChildren(cv, cur, xnode, tag, atts)
        cur[XNEST].pop()
        afterTag(cv, cur, xnode, tag, atts)

    def addSlot(cv, cur, ch):
        """Add a slot.

        Whenever we encounter a character, we add it as a new slot.
        If needed, we start / terminate word nodes as well.

        Parameters
        ----------
        cv: object
            The converter object, needed to issue actions.
        cur: dict
            Various pieces of data collected during walking
            and relevant for some next steps in the walk.
        ch: string
            A single character, the next slot in the result data.
        """
        s = cv.slot()
        cv.feature(s, ch=ch)

    def beforeChildren(cv, cur, xnode, tag, atts):
        """Actions before dealing with the element's children.

        Parameters
        ----------
        cv: object
            The converter object, needed to issue actions.
        cur: dict
            Various pieces of data collected during walking
            and relevant for some next steps in the walk.
        xnode: object
            An LXML element node.
        tag: string
            The tag of the LXML node.
        atts: dict
            The attributes of the LXML node, possibly renamed.
        """
        if tag not in PASS_THROUGH:
            curNode = cv.node(tag)
            cur[TNEST].append(curNode)
            if len(atts):
                cv.feature(curNode, **atts)

        if not hasattr(xnode, "target") and xnode.text:
            textMaterial = WHITE_TRIM_RE.sub(" ", xnode.text)
            for ch in textMaterial:
                addSlot(cv, cur, ch)

    def afterChildren(cv, cur, xnode, tag, atts):
        """Node actions after dealing with the children, but before the end tag.

        Here we make sure that the newline elements will get their last slot
        having a newline at the end of their `after` feature.

        Parameters
        ----------
        cv: object
            The converter object, needed to issue actions.
        cur: dict
            Various pieces of data collected during walking
            and relevant for some next steps in the walk.
        xnode: object
            An LXML element node.
        tag: string
            The tag of the LXML node.
        atts: dict
            The attributes of the LXML node, possibly renamed.
        """
        if tag not in PASS_THROUGH:
            curNode = cur[TNEST].pop()

            if not cv.linked(curNode):
                s = cv.slot()
                cv.feature(s, ch=ZWSP, empty=1)

            cv.terminate(curNode)

    def afterTag(cv, cur, xnode, tag, atts):
        """Node actions after dealing with the children and after the end tag.

        This is the place where we process the `tail` of an LXML node: the
        text material after the element and before the next open/close
        tag of any element.

        Parameters
        ----------
        cv: object
            The converter object, needed to issue actions.
        cur: dict
            Various pieces of data collected during walking
            and relevant for some next steps in the walk.
        xnode: object
            An LXML element node.
        tag: string
            The tag of the LXML node.
        atts: dict
            The attributes of the LXML node, possibly renamed.
        """
        if xnode.tail:
            tailMaterial = WHITE_TRIM_RE.sub(" ", xnode.tail)
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
            The converter object, needed to issue actions.
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

                with fileOpen(f"{xmlPath}/{xmlFolder}/{xmlFile}") as fh:
                    text = fh.read()
                    text = transformFunc(text)
                    tree = etree.parse(text, parser)
                    root = tree.getroot()
                    cur[XNEST] = []
                    cur[TNEST] = []
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
