"""
# Variants

This module contains functions to help you constructing nodes
when you convert TEI material and encounter elements from
the
[Critical Apparatus Module](https://www.tei-c.org/release/doc/tei-p5-doc/en/html/examples-lem.html#TC).

An extensive description of the problems and solutions is in
`tf.about.variants`.
"""


APP = "app"
N_SENT = "nSent"
PARENT = "parent"
RDGS = "rdgs"
SLOTS = "slots"
VARIANTS = "variants"
WIT = "wit"

# Start new keys in cur

APP_STACK = "appstack"
APPS = "apps"
N_APP = "nApp"
TRANS_LAST = "translast"
TRANS_NEXT = "transnext"
WITNESSES = "witnesses"
WITS = "wits"
X_WITS = "xwits"

# End new keys in cur

# Start existing keys in cur

RDG = "rdg"
LEM = "lem"

# End existing keys in cur


class Variants:
    def __init__(self, cv, cur, baseWitness, sentType, checkPunc, addWarning, addError):
        """Handlers to turn boundaries into nodes even across variants.

        This class works inside converters of the type `tf.convert.walker`.
        Import it as

        ``` python
        from tf.convert.variants import Variants
        ```

        It should typically be instantiated inside the `director()` function,
        at a point where `cv` and `cur` are known.

        Then issue `Variants.initApps`, either once or for each volume in the corpus.

        After initialization you should call `Variants.collectWitnesses()` for
        each TEI file in the corpus.

        After collecting the witnesses you should prepare for the final walk through
        the data by `Variants.resetApps()`. This should match the call(s) to
        `Variants.initApps`.

        Then, at the start of each app-, lem-, rdg- element, call
        `Variants.startApp(tag)` with tag the corresponding tag name (
        `app`, `lem`, or `rdg`).

        Likewise, at the end, call `Variants.endApp(tag)`.

        Whenever you create slots, isse a `Variants.startSent()` first,
        and a `Variants.checkSent()` after.

        Close every TEI file with a `Variants.endSent()`, to finish off all
        pending sentences.

        Parameters
        ----------
        cv: object
            The `tf.convert.walker.CV` object. This is the machinery that constructs
            nodes and assigns features.
        cur: dict
            Keys and values by which a conversion program maintains current information.
            The conversion proceeds by executing a custom `director()` function,
            and this director walks through the source material and fires `cv` actions.
            During the walk, the director can remember incoming data as needed in a
            dict, and it is this dict that should be passed. The `Variants` object
            stores additional information here under specific keys.

            Those keys are mentioned in constants in the source code and there are
            a few keys dependent on the `sentType` parameter, namely

                f"n{sentType}"
                f"stack{sentType}"
                f"var{sentType}"

        baseWitness: string
            The name of the base text. Take care that it is different from the names
            of the witnesses.

        sentType: string
            The name of the node type of the nodes that will be constructed on the
            basis of boundaries. It could be "sentence", but it could also be any
            other name, and it is not assumed that the nodes in question represent
            sentences. It could be anything, provided we have access to its boundaries.

        checkPunc: function(string, string, punc): boolean
            Given a the texts of the last two slots and the punctuation after that,
            it determines whether is contains a boundary.
            This function should be written in the converter program.
            Hence it is up to the conversion code to define what constitues a boundary,
            and whether it are sentences or some things else that are being bounded.
            This function is called and depending on the outcome sentence nodes are
            terminated and/or created, or nothing is done.

        addWarning, addError: function(string, dict)
            Functions taking a message string and a dict with current information
            (typically cur).
            They will be called if a warning or error has to be issued.
            When they is called, `cur` will be passed as dict.
            This function should be defined in the conversion program. It may use values
            in `cur` to generate an indication where the warning/error occurred.

        """
        self.cv = cv
        self.cur = cur
        self.sentType = sentType
        self.baseWitness = baseWitness
        self.checkPunc = checkPunc
        self.addWarning = addWarning
        self.addError = addError
        self.nSent = f"n{sentType}"
        self.stackSent = f"stack{sentType}"
        self.varSent = f"variants{sentType}"

        cur[WITNESSES] = set()

    def collectWitnesses(self, node):
        """Collect all witnesses.

        Call this for the root nodes of every TEI file of the corpus.

        Collects the witnesses from all rdg-elements.
        For each lem-element the set of witnesses of its rdg siblings is collected in
        such a way that it can be retrieved later on.

        We also store a pointer to the parent app-element of each nested app-element.

        We also check that multiple direct-rdg children of the same
        app have disjoint witnesses.
        """

        cur = self.cur
        addWarning = self.addWarning

        tag = node.tag.lower()
        atts = node.attrib

        appStack = cur[APP_STACK]
        apps = cur[APPS]

        if tag == APP:
            parentApp = appStack[-1] if len(appStack) else None
            nApp = cur[N_APP]
            cur[N_APP] = nApp + 1
            appStack.append(nApp + 1)
            apps[nApp + 1] = dict(parent=parentApp, xwits=set(), rdgs=[])

        elif tag == RDG:
            att = WIT

            if att in atts:
                ws = {w.strip(".").lower() for w in atts[att].split()}
                cur[WITNESSES] |= ws
                apps[appStack[-1]][X_WITS] |= ws
                rdgSeen = apps[appStack[-1]][RDGS]
                for rdg in rdgSeen:
                    if rdg & ws:
                        addWarning(
                            "witnesses of rdg not disjoint from sibling rdgs", cur
                        )
                apps[appStack[-1]][RDGS].append(ws)

        for child in node:
            self.collectWitnesses(child)

        if tag == APP:
            appStack.pop()

    def initApps(self):
        """Initialize app- processing and witness collection.

        You can issue this command once for the whole corpus,
        or each time before entering a volume.
        """
        cur = self.cur

        cur[APPS] = dict()
        cur[APP_STACK] = []
        cur[TRANS_NEXT] = []
        cur[N_APP] = 0

    def resetApps(self):
        """Initialize app- and "sentence" processing.

        Set up the data store for collecting information and "sentence" processing.
        Do this after collecting the witnesses.

        You can issue this command once for the whole corpus,
        or each time before entering a volume.
        But it should be kept in tandem with `Variants.initApps`.
        """
        cur = self.cur
        baseWitness = self.baseWitness
        nSent = self.nSent
        stackSent = self.stackSent
        varSent = self.varSent

        cur[N_APP] = 0
        cur[WITS] = []
        cur[X_WITS] = []
        cur[TRANS_LAST] = None
        cur[nSent] = 0
        cur[stackSent] = []
        cur[varSent] = {baseWitness: None}

    def startApp(self, tag, atts):
        """Actions at the start of app- lem- and rdg-elements.

        Use this each time you enter one of these XML elements.

        Parameters
        ----------
        tag: string
            The tag name of the XML element that is being entered
        atts: dict
            The attributes of the XML element that is being entered
        """

        cur = self.cur
        curStackSent = cur[self.stackSent]

        if tag == APP:
            nApp = cur[N_APP]
            cur[N_APP] = nApp + 1
            appInfo = cur[APPS][nApp + 1]
            parentApp = appInfo[PARENT]
            xwits = appInfo[X_WITS]

            slots = self._diverge()
            cur[TRANS_NEXT].append("")

            curStackSent.append(
                dict(
                    translast=cur[TRANS_LAST],
                    slots=slots,
                )
            )

            while parentApp is not None:
                appInfo = cur[APPS][parentApp]

                # keep xwits immutable, don't say xwits |= blabla
                # because that will change xwits in place

                xwits = xwits | appInfo[X_WITS]
                parentApp = appInfo[PARENT]

            cur[X_WITS].append(xwits)

        elif tag == LEM:
            xWits = self._getXwits()
            for wit in self._getWits():
                if wit in xWits:
                    self._suspend(wit)
                else:
                    self._resume(wit)

        elif tag == RDG:
            wits = set()
            if WIT in atts:
                wits = {w.strip(".").lower() for w in atts[WIT].split()}
                atts[WIT] = " ".join(wits)

            cur[WITS].append(wits)

            for wit in self._getWits():
                if wit in wits:
                    self._resume(wit)
                else:
                    self._suspend(wit)

    def endApp(self, tag):
        """Actions at the end of app- lem- and rdg-elements.

        Use this each time you leave one of these XML elements.

        Parameters
        ----------
        tag: string
            The tag name of the XML element that is being left
        """

        cur = self.cur
        curStackSent = cur[self.stackSent]

        if tag == APP:
            cur[X_WITS].pop()

            xWits = self._getXwits()
            for wit in self._getWits():
                if wit not in xWits:
                    self._resume(wit)

            curStackSent.pop()
            cur[TRANS_LAST] = cur[TRANS_NEXT].pop()

        elif tag == LEM:
            cur[TRANS_NEXT][-1] = cur[TRANS_LAST]

            xWits = self._getXwits()
            for wit in self._getWits():

                if wit not in xWits:
                    self._suspend(wit)

        elif tag == RDG:
            wits = cur[WITS][-1]

            for wit in wits:
                self._suspend(wit)

            cur[WITS].pop()

    def checkSent(self, trans, punc):
        """Checks whether there is a "sentence" boundary at this point.

        Use this every time you have added a slot node.

        Parameters
        ----------
        trans: string
            The text of the newly added slot node.
            If this is empty, the text of the slot before that will be consulted.
            This value is taken from the context information.
            This very function is responsible for putting the last text value into
            the context.
        punc: string
            The non-alfanumeric text material after the text of the last slot.
            Will be used to determine whether there is a "sentence" break here.
            The actual check will be done by the function `checkPunc`,
            which has been passed as parameter when the `Variants` object was
            created.
        """
        cur = self.cur
        checkPunc = self.checkPunc

        lastTrans = trans or cur[TRANS_LAST] or ""
        if checkPunc(lastTrans, trans, punc):
            self.endSent()
        else:
            cur[TRANS_LAST] = trans

    def startSent(self):
        """Starts a "sentence" if there is no current sentence.

        When in an rdg-element, witness-dependend "sentence" nodes
        are created for each witness for the rdg.

        Use this before creating a slot and/or at the start of certain elements
        such as paragraphs.
        """

        cur = self.cur
        baseWitness = self.baseWitness

        inRdg = RDG in cur and len(cur[RDG]) > 0
        inLem = LEM in cur and len(cur[LEM]) > 0

        if inLem:
            self._startSentLem()
        elif inRdg:
            self._startSentRdg()
        else:
            self._start(baseWitness, witAtt=False)

    def endSent(self):
        """Ends a "sentence" if there is a current sentence.

        Use this at the end of each XML file if you are sure that
        there should not remain pending sentences. You can also call this
        at the end of certain elements, such as paragraphs.

        When in a lem-element, all pending "sentences" of all witnesses
        that agree with the base text here are also ended.
        No new sentences for these witnesses are started, since we are in
        the base text.
        """

        cur = self.cur

        inRdg = RDG in cur and len(cur[RDG]) > 0
        inLem = LEM in cur and len(cur[LEM]) > 0

        if inLem:
            self._endSentLem()
        elif inRdg:
            self._endSentRdg()
        else:
            for wit in self._getWits():
                self._terminate(wit)

    def _startSentLem(self):
        baseWitness = self.baseWitness

        self._start(baseWitness)

    def _endSentLem(self):
        xWits = self._getXwits()
        for wit in self._getWits():
            if wit not in xWits:
                self._terminate(wit)

    def _startSentRdg(self):
        cur = self.cur
        curStackSent = cur[self.stackSent]

        wits = cur[WITS][-1]
        topStack = curStackSent[-1]
        cur[TRANS_LAST] = topStack[TRANS_LAST]

        for wit in wits:
            self._prepend(wit)

    def _endSentRdg(self):
        cur = self.cur

        wits = cur[WITS][-1]

        for wit in wits:
            self._terminate(wit)

    def _get(self, wit):
        cur = self.cur
        baseWitness = self.baseWitness

        curVarSent = cur[self.varSent]
        isBase = wit == baseWitness

        if isBase:
            return curVarSent[baseWitness]

        return curVarSent.get(wit, None)

    def _getWits(self):
        cur = self.cur
        curVarSent = cur[self.varSent]

        return list(curVarSent)

    def _getXwits(self):
        cur = self.cur

        xWits = cur[X_WITS]

        return xWits[-1] if xWits else set()

    def _start(self, wit, witAtt=True):
        s = self._get(wit)
        if s is not None:
            return s

        cv = self.cv
        cur = self.cur
        sentType = self.sentType
        curVarSent = cur[self.varSent]
        nSent = self.nSent
        baseWitness = self.baseWitness

        isBase = wit == baseWitness

        s = cv.node(sentType)

        cur[nSent] += 1
        cv.feature(s, n=cur[nSent])
        if witAtt:
            cv.feature(s, wit=wit)

        if isBase:
            curVarSent[baseWitness] = s
        else:
            curVarSent[wit] = s

        return s

    def _terminate(self, wit):
        cv = self.cv
        cur = self.cur
        baseWitness = self.baseWitness

        curVarSent = cur[self.varSent]
        isBase = wit == baseWitness

        s = self._get(wit)
        if s is not None:
            cv.terminate(s)

            if isBase:
                curVarSent[wit] = None
            else:
                del curVarSent[wit]

    def _resume(self, wit):
        cv = self.cv

        s = self._get(wit)
        if s is not None:
            cv.resume(s)

    def _suspend(self, wit):
        cv = self.cv

        s = self._get(wit)
        if s is not None:
            cv.terminate(s)

    def _diverge(self):
        cv = self.cv
        baseWitness = self.baseWitness

        s = self._get(baseWitness)

        if s is None:
            return None

        cv.feature(s, wit=baseWitness)
        return cv.linked(s)

    def _prepend(self, wit):
        if self._get(wit) is None:
            cv = self.cv
            cur = self.cur
            curStackSent = cur[self.stackSent]
            topStack = curStackSent[-1]
            slots = topStack[SLOTS]

            s = self._start(wit)

            if s is not None and slots is not None:
                cv.link(s, topStack[SLOTS])
