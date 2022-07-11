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
APPS = "apps"
APP_STACK = "appstack"
BASE = "base"
LEM = "lem"
N_APP = "nApp"
N_SENT = "nSent"
PARENT = "parent"
RDG = "rdg"
RDGS = "rdgs"
SLOTS = "slots"
TRANS_LAST = "translast"
TRANS_NEXT = "transnext"
VARIANTS = "variants"
WIT = "wit"
WITNESSES = "witnesses"
WITS = "wits"
X_WITS = "xwits"


class Variants:
    def __init__(self, cv, cur, sentType, addWarning, addError):
        self.cv = cv
        self.cur = cur
        self.sentType = sentType
        self.addWarning = addWarning
        self.addError = addError
        self.nSent = f"n{sentType}"
        self.stackSent = f"stack{sentType}"
        self.varSent = f"variants{sentType}"
        cur[WITNESSES] = set()

    def initApps(self):
        cur = self.cur

        cur[APPS] = dict()
        cur[APP_STACK] = []
        cur[TRANS_NEXT] = []
        cur[N_APP] = 0

    def collectWitnesses(self, node):
        """Collect all witnesses.

        first collect witnesses from all rdg elements
        and store information for each lemma what witnesses occur in sibling rdgs
        we number the lem elements globally as we encounter them,
        and store info for that lem under that number,
        so that we can refer to that info when we encounter the lem during
        the second pass.

        The info per lem is
        - the set of all witnesses mentioned in the wit attribute of all its
          sibling rdgs
        The number of its parent lem or None if there is no parent lem

        We also check whether there are multiple direct rdg children of the same
        app that share witnesses (which would be strange: conflicting information)
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

    def resetApps(self):
        cur = self.cur

        cur[N_APP] = 0
        cur[WITS] = []
        cur[X_WITS] = []

    def initSent(self):
        cur = self.cur
        nSent = self.nSent
        stackSent = self.stackSent
        varSent = self.varSent

        cur[TRANS_LAST] = None
        cur[nSent] = 0
        cur[stackSent] = []
        cur[varSent] = {BASE: None}

    def startApp(self, node):
        cv = self.cv
        cur = self.cur
        curVarSent = cur[self.varSent]
        curStackSent = cur[self.stackSent]

        tag = node.tag
        atts = node.attrib

        if tag == APP:
            nApp = cur[N_APP]
            cur[N_APP] = nApp + 1
            appInfo = cur[APPS][nApp + 1]
            parentApp = appInfo[PARENT]
            xwits = appInfo[X_WITS]

            curSent = curVarSent.get(BASE, None)
            cur[TRANS_NEXT].append("")

            if curSent is None:
                slots = None
            else:
                slots = cv.linked(curSent)
                cv.feature(curSent, wit=BASE)

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
            pass

        elif tag == RDG:
            wits = set()
            if WIT in atts:
                wits = {w.strip(".").lower() for w in atts[WIT].split()}
                atts[WIT] = " ".join(wits)

            cur[WITS].append(wits)

    def endApp(self, node):
        cv = self.cv
        cur = self.cur
        curVarSent = cur[self.varSent]
        curStackSent = cur[self.stackSent]

        tag = node.tag

        if tag == APP:
            cur[X_WITS].pop()

            for variantSent in curVarSent.values():
                if variantSent is not None:
                    cv.resume(variantSent)

            curStackSent.pop()
            cur[TRANS_LAST] = cur[TRANS_NEXT].pop()

        elif tag == LEM:
            cur[TRANS_NEXT][-1] = cur[TRANS_LAST]

            curBaseSent = curVarSent[BASE]
            if curBaseSent is not None:
                cv.terminate(curBaseSent)

        elif tag == RDG:
            wits = cur[WITS][-1]

            for wit in wits:
                curWitSent = curVarSent.get(wit, None)
                if curWitSent is not None:
                    cv.terminate(curWitSent)

            cur[WITS].pop()

    def startSentLem(self):
        cur = self.cur
        curVarSent = cur[self.varSent]

        if curVarSent.get(BASE, None) is None:
            cv = self.cv
            sentType = self.sentType
            nSent = self.nSent

            curSent = cv.node(sentType)
            cur[nSent] += 1
            curVarSent[BASE] = curSent
            cv.feature(curSent, wit=BASE, n=cur[nSent])

    def endSentLem(self):
        cv = self.cv
        cur = self.cur
        curVarSent = cur[self.varSent]

        toDelete = []

        for (wit, sent) in curVarSent.items():
            isBase = wit == BASE
            isXwit = wit in cur[X_WITS][-1]
            if isBase or not isXwit:
                cv.terminate(sent)
                if isBase:
                    curVarSent[wit] = None
                else:
                    toDelete.append(wit)

        for wit in toDelete:
            del curVarSent[wit]

    def startSentRdg(self):
        cv = self.cv
        sentType = self.sentType
        cur = self.cur
        curStackSent = cur[self.stackSent]
        curVarSent = cur[self.varSent]
        nSent = self.nSent

        wits = cur[WITS][-1]
        topStack = curStackSent[-1]
        cur[TRANS_LAST] = topStack[TRANS_LAST]

        for wit in wits:
            curSent = curVarSent.get(wit, None)
            if curSent is None:
                curSent = cv.node(sentType)
                cur[nSent] += 1
                curVarSent[wit] = curSent
                cv.feature(curSent, wit=wit, n=cur[nSent])
                slots = topStack[SLOTS]
                if slots is not None:
                    cv.link(curSent, topStack[SLOTS])

    def endSentRdg(self):
        cv = self.cv
        cur = self.cur
        curVarSent = cur[self.varSent]

        wits = cur[WITS][-1]

        for wit in wits:
            curSent = curVarSent.get(wit, None)
            if curSent is not None:
                cv.terminate(curSent)
                curVarSent[wit] = None

    def checkSent(self, trans, punc, checkPunc):
        cur = self.cur

        lastTrans = trans or cur[TRANS_LAST] or ""
        if checkPunc(lastTrans, trans, punc):
            self.endSent()
        else:
            cur[TRANS_LAST] = trans

    def startSent(self):
        cur = self.cur

        inRdg = "rdg" in cur and len(cur["rdg"]) > 0
        inLem = "lem" in cur and len(cur["lem"]) > 0

        if inLem:
            self.startSentLem()
        elif inRdg:
            self.startSentRdg()
        else:
            curVarSent = cur[self.varSent]

            if curVarSent[BASE] is None:
                cv = self.cv
                sentType = self.sentType
                nSent = self.nSent

                curSent = cv.node(sentType)
                cur[nSent] += 1
                cv.feature(curSent, n=cur[nSent])
                curVarSent[BASE] = curSent

    def endSent(self):
        cv = self.cv
        cur = self.cur
        curVarSent = cur[self.varSent]

        inRdg = "rdg" in cur and len(cur["rdg"]) > 0
        inLem = "lem" in cur and len(cur["lem"]) > 0

        if inLem:
            self.endSentLem()
        elif inRdg:
            self.endSentRdg()
        else:
            if curVarSent[BASE] is not None:
                cv.terminate(curVarSent[BASE])
                curVarSent[BASE] = None

            toDelete = []

            for (wit, sent) in curVarSent.items():
                isBase = wit == BASE

                if sent is not None:
                    cv.terminate(sent)
                    if isBase:
                        curVarSent[wit] = None
                    else:
                        toDelete.append(wit)

            for wit in toDelete:
                del curVarSent[wit]
