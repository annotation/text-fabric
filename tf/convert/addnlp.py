"""Add data from an NLP pipeline.

When you have used `tf.convert.tei` to convert a TEI data source into a TF dataset,
the situation with words and sentences is usually not satisfactory.
In most TEI sources, words and sentences are not explicitly marked up, and it is
really hard to build token detection and sentence boundary detection into the
conversion program.

There is a better way.
You can use this module to have tokens and sentences detected by NLP pipelines
(currently only Spacy is supported).
These tokens and sentences will then be transformed to nodes and attributes
and inserted in the TF dataset as a new version.

The original slots in the TF dataset (characters) will be discarded, because the
new tokens will be used as slots.

**This is work in progress. Details of the workflow may change rather often!**

## Requirements

*   The initial data set should be one that has characters as slots.
*   The version of the initial data should end with the string `pre`, e.g.
    `0.8pre`.

## Effect

*   A new version of the data (whose label is the old version minus the `pre`)
    will be produced:

    *   with new node types `sentence` and `token`;
    *   with `token` as slot type;
    *   with the old slot type removed;
    *   with the feature that contains the text of the slots removed;
    *   with other slot features translated to equally named features on `token`;
    *   with other node and edge features translated faithfully to the new situation.

## Homework

*   The new data needs a slightly different TF app than the original version.
    You can generate that with the program that created the TF from the TEI,
    typically

    ``` sh
    python tfFromTei.py apptoken
    ```

# Usage

## Commandline

```sh
tf-addnlp tasks params flags
```

## From Python

```python
from tf.convert.addnlp import NLPipeline
from tf.app import use

ORG = "yourOrg"
REPO = "yourRepo"

Apre = use(f"{ORG}/{REPO}:clone", checkout="clone")

NLP = NLPipeline(**params, **flags)
NLP.loadApp(Apre)
NLP.task(**tasks, **flags)
```

For the tasks, parameters and flags, see
`TASKS`, `PARAMS`, and `FLAGS` and expand the code.

The parameters have defaults that are exactly suited to corpora that have been
converted from TEI by `tf.convert.tei`.

## Examples

Exactly how you can call the methods of this module is demonstrated in the small
corpus of 14 letter by the Dutch artist Piet Mondriaan.

*   [Mondriaan](https://nbviewer.org/github/annotation/mondriaan/blob/master/programs/convertExpress.ipynb).
"""

import sys
import re

from .recorder import Recorder
from ..advanced.app import loadApp
from ..tools.xmlschema import Analysis
from ..tools.myspacy import tokensAndSentences
from ..dataset import modify
from ..core.helpers import console
from ..core.files import initTree, dirMake, dirExists
from ..core.timestamp import DEEP, TERSE
from ..core.command import readArgs
from ..lib import writeList, readList


HELP = "Add NLP-generated features to a TF dataset."

TASKS = dict(
    plaintext="make a plain text for the NLP tools",
    lingo="run the NLP tool on the plain text",
    ingest="ingest the results of the NLP tool in the dataset",
    all=None,
)
"""Possible tasks."""

PARAMS = dict(
    lang=("Set up the NLP tool for this language", "en"),
    slotFeature=(
        "When generating text, use this feature to obtain text from slots",
        "ch",
    ),
    removeSlotFeatures=(
        "Discardable slot features. Will not be translated to token features",
        "ch",
    ),
    emptyFeature=("Feature to identify empty slots.", "empty"),
    ignoreTypes=(
        "Node types that will be ignored when generating the plain text.",
        "word",
    ),
    outOfFlow=(
        "These node types will be put in separate text flows in the plain text.",
        "note,orig,del",
    ),
    tokenType=("The node type for the tokens.", "token"),
    tokenFeatures=(
        (
            "The features in the token output by the NLP: "
            "1: token content; 2: space after the token (if any), ..."
        ),
        "str,after",
    ),
    sentenceBarriers=("Elements that trigger a senetence boundary.", "div,p"),
    sentenceSkipFlow=("The flows that are not fed to sentence detection.", "orig,del"),
    tokenNFeature=("The feature that will hold the sequence number of the token.", ""),
    sentenceType=("The node type for the sentences", "sentence"),
    sentenceFeatures=("", ""),
    sentenceNFeature=("The features in the sentence output by the NLP", ""),
)
"""Possible parameters."""

FLAGS = dict(
    write=(
        (
            "whether to write the generated files "
            "with plain text and node positions to disk"
        ),
        False,
        2,
    ),
    verbose=("Produce less or more progress and reporting messages", -1, 3),
)
"""Possible flags."""


class NLPipeline:
    def __init__(
        self,
        app=None,
        lang=PARAMS["lang"][1],
        slotFeature=PARAMS["slotFeature"][1],
        removeSlotFeatures=PARAMS["removeSlotFeatures"][1],
        emptyFeature=PARAMS["emptyFeature"][1],
        ignoreTypes=PARAMS["ignoreTypes"][1],
        outOfFlow=PARAMS["outOfFlow"][1],
        tokenType=PARAMS["tokenType"][1],
        tokenFeatures=PARAMS["tokenFeatures"][1],
        tokenNFeature=PARAMS["tokenNFeature"][1],
        sentenceBarriers=PARAMS["sentenceBarriers"][1],
        sentenceSkipFlow=PARAMS["sentenceSkipFlow"][1],
        sentenceType=PARAMS["sentenceType"][1],
        sentenceFeatures=PARAMS["sentenceFeatures"][1],
        sentenceNFeature=PARAMS["sentenceNFeature"][1],
        verbose=FLAGS["verbose"][1],
        write=FLAGS["write"][1],
    ):
        """Enrich a TF dataset with annotations generated by an NLP pipeline.

        Parameters
        ----------
        lang: string, optional en
            The language for which the NLP tool will be set up
        app: object, None
            A loaded TF app. If None, the TF App that is nearby in the file system
            will be loaded.
            We assume that the original data resides in the current
            version, which has the string `pre` appended to it,
            e.g. in version `1.3pre`.
            We create a new version of the dataset, with the same number,
            but without the `pre`.
        slotFeature: string, optional ch
            The  feature on slots that provides the text of a slot to be included
            in the generated text.
        removeSlotFeatures: "ch"
            A tuple is distilled from comma-separated values.
            The names of features defined on original slots that do not have to be
            carried over to the new slots of type token.
            There should be at least one feature: the character content of the slot.
        emptyFeature: string, optional "empty"
            Name of feature that identifies the empty slots.
        ignoreTypes: set, optional "word"
            A set is distilled from comma-separated values.
            Node types that will be ignored when generating the plain text.
        outOfFlow: string, optional "note,orig,del"
            A set is distilled from comma-separated values.
            A set of node types whose content will be put in separate text flows at
            the end of the document.
        sentenceSkipFlow: string, optional "orig,del"
            A set is distilled from comma-separated values.
            The elements whose flows in the sentence stream should be ignored
        tokenType: string, optional token
            The node type for the tokens
        tokenFeatures: tuple, optional ("str", "after")
            A tuple is distilled from comma-separated values.
            The names of the features that the token stream contains.
            There must be at least two features:
            the first one should give the token content, the second one the non-token
            material until the next token.
            The rest are additional features that the
            pipeline might supply.
        tokenNFeature: string, optional None
            If not None, the name of the token feature that will hold the
            sequence number of the token in the data stream, starting at 1.
        sentenceType: string, optional sentence
            The node type for the sentences
        sentenceFeatures: tuple, optional ()
            A tuple is distilled from comma-separated values.
            The names of the features that the sentence stream contains.
        sentenceNFeature: string, optional nsent
            If not None, the name of the sentence feature that will hold the
            sequence number of the sentence in the data stream, starting at 1.

        """

        def makeString(s):
            return None if not s else s

        def makeSet(s):
            return set() if not s else set(s.split(","))

        def makeTuple(s):
            return tuple() if not s else tuple(s.split(","))

        self.good = True
        self.app = app
        self.lang = makeString(lang)
        self.slotFeature = makeString(slotFeature)
        self.removeSlotFeatures = makeTuple(removeSlotFeatures)
        self.emptyFeature = makeString(emptyFeature)
        self.ignoreTypes = makeSet(ignoreTypes)
        self.outOfFlow = makeSet(outOfFlow)
        self.tokenType = makeString(tokenType)
        self.tokenFeatures = makeTuple(tokenFeatures)
        self.tokenNFeature = makeString(tokenNFeature)
        self.sentenceBarriers = makeSet(sentenceBarriers)
        self.sentenceSkipFlow = makeSet(sentenceSkipFlow)
        self.sentenceType = makeString(sentenceType)
        self.sentenceFeatures = makeTuple(sentenceFeatures)
        self.sentenceNFeature = makeString(sentenceNFeature)
        self.verbose = verbose
        self.write = write

    def loadApp(self, app=None, verbose=None):
        """Loads a given TF app or loads the TF app based on the working directory.

        Parameters
        ----------
        app: object, optional None
            The handle to the original TF dataset, already loaded.

            If not given, we load the TF app that is nearby in the file system.

        verbose: integer, optional None
            Produce more progress and reporting messages
            If not passed, take the verbose member of this object.
        """
        if verbose is not None:
            self.verbose = verbose
        verbose = self.verbose

        if app is None:
            if self.app is None:
                app = loadApp(silent=DEEP)
                self.app = app
            else:
                app = self.app
        else:
            self.app = app

        self.app = app
        version = app.version
        if verbose >= 0:
            console(f"Input data has version {version}")

        repoDir = app.repoLocation
        txtDir = f"{repoDir}/_temp/txt"
        self.txtDir = txtDir
        self.tokenFile = f"{txtDir}/tokens.tsv"
        self.sentenceFile = f"{txtDir}/sentences.tsv"
        self.textPath = f"{repoDir}/_temp/txt/plain.txt"

    def getElementInfo(self, verbose=None):
        """Analyse the schema.

        The XML schema has useful information about the XML elements that
        occur in the source. Here we extract that information and make it
        fast-accessible.

        Parameters
        ----------
        verbose: integer, optional None
            Produce more progress and reporting messages
            If not passed, take the verbose member of this object.

        Returns
        -------
        dict
            Keyed by element name (without namespaces), where the value
            for each name is a tuple of booleans: whether the element is simple
            or complex; whether the element allows mixed content or only pure content.
        """
        if verbose is not None:
            self.verbose = verbose
        verbose = self.verbose

        self.elementDefs = {}

        A = Analysis(verbose=verbose)
        A.configure()
        A.interpret()
        if not A.good:
            console("Could not get TEI element definitions")
            return

        elementDefs = {name: (typ, mixed) for (name, typ, mixed) in A.getDefs()}
        self.mixedTypes = {x for (x, (typ, mixed)) in elementDefs.items() if mixed}

    def generatePlain(self):
        """Generates a plain text out of a data source.

        The text is generatad in such a way that out of flow elements are collected
        and put at the end. Examples of such elements are notes.
        Leaving them at their original positions will interfere with sentence detection.

        We separate the flows clearly in the output, so that they are discernible
        in the output of the NLP pipeline.

        Returns
        -------
        tuple
            The result is a tuple consisting of

            *   *text*: the generated text
            *   *positions*: a list of nodes such that list item *i* contains
                the original slot that corresponds to the character *i* in the
                generated text (counting from zero).
        """
        slotFeature = self.slotFeature
        emptyFeature = self.emptyFeature
        ignoreTypes = self.ignoreTypes
        outOfFlow = self.outOfFlow
        sentenceBarriers = self.sentenceBarriers
        verbose = self.verbose
        write = self.write
        app = self.app
        info = app.info
        indent = app.indent
        api = app.api
        F = api.F
        Fs = api.Fs
        N = api.N
        T = api.T

        sentenceBreakRe = re.compile(r"[.!?]")

        info("Generating a plain text with positions ...", force=verbose >= 0)
        self.getElementInfo()
        mixedTypes = self.mixedTypes

        flows = {elem: [] for elem in outOfFlow}
        flows[""] = []
        flowStack = [""]

        nTypeStack = []

        def finishSentence(flowContent):
            nContent = len(flowContent)
            lnw = None  # last non white position
            for i in range(nContent - 1, -1, -1):
                item = flowContent[i]
                if type(item) is not str or item.strip() == "":
                    continue
                else:
                    lnw = i
                    break

            if lnw is None:
                return

            # note that every slot appears in the sequence preceded by a neg int
            # and followed by a pos int
            # Material outside slots may be followed and preceded by other strings
            # We have to make sure that what we add, falls outside any slot.
            # We do that by inspecting the following item:
            # if that is a positive int, we are in a slot so we have to insert material
            # after that int
            # If the following item is a string or a negative int,
            # so we can insert right after the point where we are.
            if not sentenceBreakRe.match(flowContent[lnw]):
                offset = 1
                if lnw < nContent - 1:
                    following = flowContent[lnw + 1]
                    if type(following) is int and following > 0:
                        offset = 2
                flowContent.insert(lnw + offset, ".")
                lnw += 1

            if not any(ch == "\n" for ch in flowContent[lnw + 1 :]):
                flowContent.append("\n")

        emptySlots = 0

        Femptyv = Fs(emptyFeature).v
        Fchv = Fs(slotFeature).v
        sectionTypes = T.sectionTypes

        for (n, kind) in N.walk(events=True):
            nType = F.otype.v(n)

            if nType in ignoreTypes:
                continue

            isOutFlow = nType in outOfFlow

            if kind is None:  # slot type
                if Femptyv(n):
                    emptySlots += 1
                    ch = "￮"
                else:
                    ch = Fchv(n)
                flows[flowStack[-1]].extend([-n, ch, n])

            elif kind:  # end node
                if isOutFlow:
                    flow = flowStack.pop()
                else:
                    flow = flowStack[-1]
                flowContent = flows[flow]

                if flow:
                    finishSentence(flowContent)
                else:
                    if nType == "teiHeader":
                        finishSentence(flowContent)
                        flowContent.append(" \n xxx. \nAa bb. \nEnd meta. \n\n")
                    elif nType in sectionTypes or nType in sentenceBarriers:
                        flowContent.append(f" \n xxx. \nAa bb. \nEnd {nType}. \n\n")
                    else:
                        if any(nTp == "teiHeader" for nTp in nTypeStack) and not any(
                            nTp in mixedTypes for nTp in nTypeStack[0:-1]
                        ):
                            finishSentence(flowContent)
                nTypeStack.pop()

            else:  # start node
                nTypeStack.append(nType)

                if isOutFlow:
                    flowStack.append(nType)
                flow = flowStack[-1]
                flowContent = flows[flow]

                if isOutFlow:
                    flowContent.append(f" \nAa bb. \nitem {flow}. \n")
                else:
                    if nType == "teiHeader":
                        flowContent.append(" \nAa bb. \nBegin meta. \n\n")
                    elif nType in sectionTypes:
                        flowContent.append(f" \nAa bb. \nBegin {nType}. \n\n")
                    else:
                        if any(nTp == "teiHeader" for nTp in nTypeStack) and not any(
                            nTp in mixedTypes for nTp in nTypeStack[0:-1]
                        ):
                            flowContent.append(f"{nType}. ")

        indent(level=True)
        info(f"Found {emptySlots} empty slots", tm=False, force=verbose >= 0)

        rec = Recorder(app.api)

        for flow in sorted(flows):
            items = flows[flow]

            if len(items) == 0:
                continue

            rec.add(f" \nAa bb. \nBegin flow {flow if flow else 'main'}. \n\n")

            for item in items:
                if type(item) is int:
                    if item < 0:
                        rec.start(-item)
                    else:
                        rec.end(item)
                else:
                    rec.add(item)

            rec.add(f" \n xxx. \nAa bb. \nEnd flow {flow if flow else 'main'}. \n\n")

            info(
                (
                    f"recorded flow {flow if flow else 'main':<10} "
                    f"with {len(items):>6} items"
                ),
                tm=False,
                force=verbose >= 0,
            )

        indent(level=False)

        if write:
            textPath = self.textPath
            rec.write(textPath)
            info(
                f"Done. Generated text and positions written to {textPath}",
                force=verbose >= 0,
            )
        else:
            info("Done", force=verbose >= 0)

        return (rec.text(), rec.positions(simple=True))

    @staticmethod
    def lingo(*args, **kwargs):
        return tokensAndSentences(*args, **kwargs)

    def ingest(
        self,
        isToken,
        positions,
        stream,
        tp,
        features,
        nFeature=None,
        skipBlanks=False,
        skipFlows=None,
        emptyFeature=None,
    ):
        """Ingests a stream of NLP data and transforms it into nodes and features.

        The data is a stream of values associated with a spans of text.

        For each span a node will be created of the given type, and a feature
        of the given name will assign a value to that span.
        The value assigned is by default the value that is present in the data stream,
        but it is possible to specify a method to change the value.

        !!! caution
            The plain text on which the NLP pipeline has run may not correspond
            exactly with the text as defined by the corpus.
            When the plain text was generated, some extra convenience material
            may have been inserted.
            Items in the stream that refer to these pieces of text will be ignored.

            When items refer partly to proper corpus text and partly to convenience text,
            they will be narrowed down to the proper text.

        !!! caution
            The plain text may exhibit another order of material than the proper corpus
            text. For example, notes may have been collected and moved out of the
            main text flow to the end of the text.

            That means that if an item specifies a span in the plain text, it may
            not refer to a single span in the proper text, but to various spans.

            We take care to map all spans in the generated plain text back to *sets*
            of slots in the proper text.

        Parameters
        ----------
        isToken: boolean
            Whether the data specifies tokens or something else.
            Tokens are special because they are intended to become the new slot type.
        positions: list
            which slot node corresponds to which position in the plain text.

        stream: list of tuple
            The tuples should consist of

            *   *start*: a start number (char pos in the plain text, starting at `0`)
            *   *end*: an end number (char pos in tghe plain text plus one)
            *   *value*: a value for feature assignment

        tp: string
            The type of the nodes that will be generated.

        features: tuple
            The names of the features that will be generated.

        nFeature: string, optional None
            If not None, the name of a feature that will hold the sequence number of
            the element in the data stream, starting at 1.

        emptyFeature: string, optional empty
            Name of feature that identifies the empty slots.

        skipBlanks: boolean, optional False
            If True, rows whose text component is only white space will be skipped.

        skipFlows: set
            set of elements whose resulting data in the stream should be ignored

        Returns
        -------
        tuple
            We deliver the following pieces of information in a tuple:

            * the last node
            * the mapping of the new nodes to the slots they occupy;
            * the data of the new feature.
        """
        slotFeature = self.slotFeature

        verbose = self.verbose
        app = self.app
        info = app.info
        indent = app.indent
        F = app.api.F
        Fs = app.api.Fs
        Fotypev = F.otype.v
        slotType = F.otype.slotType
        Fslotv = Fs(slotFeature).v
        if emptyFeature is not None:
            Femptyv = Fs(emptyFeature).v
            Femptys = Fs(emptyFeature).s

        doN = nFeature is not None
        slotLinks = {}
        featuresData = {feat: {} for feat in features}
        if nFeature is not None:
            featuresData[nFeature] = {}
        if emptyFeature is not None:
            featuresData[emptyFeature] = {}

        if isToken:
            featToken = featuresData[features[0]]
            featAfter = featuresData[features[1]]

        whiteMultipleRe = re.compile(r"^[ \n]{2,}$", re.S)

        node = 0
        itemsOutside = []
        itemsEmpty = []

        info(
            f"generating {tp}-nodes with features {', '.join(featuresData)}",
            force=verbose >= 0,
        )
        indent(level=True)

        def addToken():
            nonlocal node
            nonlocal curSlots
            nonlocal curValue

            node += 1
            slotLinks[node] = curSlots
            featToken[node] = curValue
            for (feat, val) in zip(features[2:], vals[2:]):
                featuresData[feat][node] = val
            if doN:
                featuresData[nFeature][node] = node

            curSlots = []
            curValue = ""

        def addSlot(slot):
            nonlocal node

            node += 1
            slotLinks[node] = [slot]
            featToken[node] = Fslotv(slot)
            if Femptyv(slot):
                featuresData[emptyFeature][node] = 1

        def addItem():
            nonlocal node

            node += 1
            slotLinks[node] = mySlots
            for (feat, val) in zip(features, vals):
                featuresData[feat][node] = val
            if doN:
                featuresData[nFeature][node] = node

        # First add all empty slots, provided we are doing tokens

        if isToken:
            emptySlots = (
                {s for s in Femptys(1) if Fotypev(s) == slotType}
                if emptyFeature
                else set()
            )
            emptyWithinToken = 0
            spaceWithinToken = 0

            for slot in sorted(emptySlots):
                addSlot(slot)

        # now the data from the NLP pipeline

        flowBeginRe = re.compile(r" \nAa bb\. \nBegin flow (\w+)\. ")
        flowEndRe = re.compile(r" \n xxx. \nAa bb\. \nEnd flow (\w+)\. ")

        skipping = False
        flow = None

        for (i, (b, e, *vals)) in enumerate(stream):
            if skipFlows is not None:
                text = vals[0]
                if skipping:
                    match = flowEndRe.match(text)
                    if match:
                        flow = match.group(1)
                        skipping = False
                        flow = None
                        continue
                else:
                    match = flowBeginRe.match(text)
                    if match:
                        flow = match.group(1)
                        skipping = flow in skipFlows
                        continue

            if skipping:
                continue

            mySlots = set()

            for j in range(b, e):
                s = positions[j]
                if s is not None:
                    mySlots.add(s)

            if len(mySlots) == 0:
                if doN:
                    vals.append(i + 1)
                itemsOutside.append((i, b, e, *vals))
                continue

            if skipBlanks and len(vals):
                slotsOrdered = sorted(mySlots)
                nSlots = len(slotsOrdered)

                start = min(
                    (
                        i
                        for (i, s) in enumerate(slotsOrdered)
                        if Fslotv(s) not in {" ", "\t", "\n"}
                    ),
                    default=nSlots,
                )
                end = max(
                    (
                        i + 1
                        for (i, s) in enumerate(slotsOrdered)
                        if Fslotv(s) not in {" ", "\t", "\n"}
                    ),
                    default=0,
                )

                if end <= start:
                    itemsEmpty.append((i, b, e, *vals))
                    continue

                mySlots = slotsOrdered[start:end]
            else:
                mySlots = sorted(mySlots)

            curValue = ""
            curSlots = []

            nMySlots = len(mySlots)

            if isToken:
                # we might need to split tokens:
                # at points that correspond to empty slots
                # at spaces or newlines within the token
                # decompose it into individual characters

                tokenText = "".join(Fslotv(s) for s in mySlots)

                if whiteMultipleRe.match(tokenText):
                    spaceWithinToken += 1
                    for slot in mySlots:
                        addSlot(slot)
                        spaceWithinToken += 1

                else:
                    for (i, slot) in enumerate(mySlots):
                        last = i == nMySlots - 1
                        if slot in emptySlots:
                            emptyWithinToken += 1
                            if curValue:
                                addToken()
                            if last:
                                featAfter[node] = vals[1]
                        else:
                            curValue += Fslotv(slot)
                            curSlots.append(slot)
                    if curValue:
                        addToken()
                        featAfter[node] = vals[1]
            else:
                addItem()

        repFeatures = ", ".join(features + ((nFeature,) if doN else ()))
        info(
            f"{node} {tp} nodes have values assigned for {repFeatures}",
            force=verbose >= 0,
        )
        if isToken:
            info(
                f"{emptyWithinToken} empty slots have split surrounding tokens",
                force=verbose >= 0,
            )
            info(
                f"{spaceWithinToken} space slots have split into {slotType}s",
                force=verbose >= 0,
            )

        tasks = [("Items contained in extra generated text", itemsOutside)]
        if skipBlanks:
            tasks.append(("Items with empty final text", itemsEmpty))

        for (label, items) in tasks:
            nItems = len(items)
            info(f"{nItems:>5}x {label}", force=verbose >= 0)
            indent(level=True)
            for (i, b, e, *vals) in items[0:5]:
                info(
                    f"\t{i} span {b}-{e}: {', '.join(str(v) for v in vals)}",
                    force=verbose == 1,
                )
            indent(level=False)

        indent(level=False)
        return (node, slotLinks, featuresData)

    def ingestTokensAndSentences(self, positions, tokenStream, sentenceStream):
        """Ingests a tokens and sentences in a dataset and turn the tokens into slots.

        By default:

        * tokens become nodes of a new type `token`;
        * the texts of a token ends up in the feature `str`;
        * if there is a space after a token, it ends up in the feature `after`;
        * sentences become nodes of a new type `sentence`;
        * the sentence number ends up in the feature `nsent`.
        * tokens become the new slots.

        But this function can also be adapted to token and sentence streams that
        have additional names and values, see below.

        The streams of tokens and sentences may contain more fields.
        In the parameters `tokenFeatures` and `sentenceFeatures` you may pass the
        feature names for the data in those fields.

        When the streams are read, for each feature name in the `tokenFeatures`
        (resp. `sentenceFeatures`) the corresponding field in the stream will be
        read, and the value found there will be assigned to that feature.

        If there are more fields in the stream than there are declared in the
        `tokenFeatures` (resp. `sentenceFeatures`) parameter, these extra fields will
        be ignored.

        The last feature name in these parameters is special.
        If it is None, it will be ignored.
        Otherwise, an extra feature with that name will be created, and it will be
        filled with the node numbers of the newly generated nodes.

        !!! hint "Look at the defaults"
            The default `tokenFeatures=("str", "after", None)` specifies that two
            fields from the tokenstream will be read, and those values will be assigned
            to features `str` and `after`.
            There will be no field with the node itself in it.

            The default `sentenceFeatures=("nsent",)` specifies that no field from the
            tokenstream will be read, but that there will be a feature `nsent` that
            has the node of each sentence as value.

        We have to ignore the sentence boundaries in some flows,
        e.g. the material coming from `<orig>` and `<del>` elements.
        However, in the flow coming from the `<note>` elements, we want to retain the
        sentence boundaries.

        Parameters
        ----------
        positions: list
            which slot node corresponds to which position in the plain text.
        tokenStream: list
            The list of tokens as delivered by the NLP pipe.
        sentenceStream: list
            The list of sentences as delivered by the NLP pipe.

        Returns
        -------
        string
            The new version number of the data that contains the tokens and sentences.
        """
        emptyFeature = self.emptyFeature
        removeSlotFeatures = self.removeSlotFeatures
        tokenType = self.tokenType
        tokenFeatures = self.tokenFeatures
        tokenNFeature = self.tokenNFeature
        sentenceType = self.sentenceType
        sentenceFeatures = self.sentenceFeatures
        sentenceNFeature = self.sentenceNFeature
        sentenceSkipFlow = self.sentenceSkipFlow

        app = self.app
        info = app.info
        indent = app.indent
        verbose = self.verbose
        silent = "auto" if verbose == 1 else TERSE if verbose == 0 else DEEP

        info("Ingesting tokens and sentences into the dataset ...", force=verbose >= 0)
        indent(level=True)
        info("Mapping NLP data to nodes and features ...", force=verbose >= 0)
        indent(level=True)

        slotLinks = {tokenType: {}, sentenceType: {}}
        features = {}
        lastNode = {}

        for feat in (*tokenFeatures, tokenNFeature):
            if feat is not None:
                features[feat] = {}
        lastNode[tokenType] = 0

        canSentences = len(sentenceStream) != 0

        if canSentences:
            for feat in sentenceFeatures:
                if feat is not None:
                    features[feat] = {}
            lastNode[sentenceType] = 0

        for (isToken, data, skipFlows, tp, feats, nFeat, skipBlanks, thisEmpty) in (
            (
                True,
                tokenStream,
                None,
                tokenType,
                tokenFeatures,
                tokenNFeature,
                False,
                emptyFeature,
            ),
            (
                False,
                sentenceStream,
                sentenceSkipFlow,
                sentenceType,
                sentenceFeatures,
                sentenceNFeature,
                True,
                None,
            ),
        ):
            if len(data) == 0:
                continue
            (node, theseSlotLinks, featuresData) = self.ingest(
                isToken,
                positions,
                data,
                tp,
                feats,
                nFeature=nFeat,
                emptyFeature=thisEmpty,
                skipBlanks=skipBlanks,
                skipFlows=skipFlows,
            )
            lastNode[tp] = node
            slotLinks[tp] = theseSlotLinks
            for (feat, featData) in featuresData.items():
                features[feat] = featData
            info(f"{lastNode[tp]} {tp}s", force=verbose >= 0)

        indent(level=False)

        info("Make a modified dataset ...", force=verbose >= 0)

        repoDir = app.repoLocation
        versionPre = app.version
        version = versionPre.removesuffix("pre")
        origTf = f"{repoDir}/tf/{versionPre}"
        newTf = f"{repoDir}/tf/{version}"
        initTree(newTf, fresh=True, gentle=False)

        allTokenFeatures = list(tokenFeatures)
        if tokenNFeature is not None:
            allTokenFeatures.append(tokenNFeature)

        allSentenceFeatures = list(sentenceFeatures)
        if sentenceNFeature is not None:
            allSentenceFeatures.append(sentenceNFeature)

        addTypes = dict(
            token=dict(
                nodeFrom=1,
                nodeTo=lastNode[tokenType],
                nodeSlots=slotLinks[tokenType],
                nodeFeatures={feat: features[feat] for feat in allTokenFeatures},
            )
        )
        if canSentences:
            addTypes["sentence"] = dict(
                nodeFrom=1,
                nodeTo=lastNode[sentenceType],
                nodeSlots=slotLinks[sentenceType],
                nodeFeatures={feat: features[feat] for feat in allSentenceFeatures},
            )

        featureMeta = dict(
            nsent=dict(
                valueType="int",
                description="number of sentence in corpus",
            ),
            otext={
                "fmt:text-orig-full": "{"
                + tokenFeatures[0]
                + "}{"
                + tokenFeatures[1]
                + "}"
            },
        )

        modify(
            origTf,
            newTf,
            targetVersion=version,
            addTypes=addTypes,
            deleteTypes=("word",),
            featureMeta=featureMeta,
            replaceSlotType=(tokenType, *removeSlotFeatures),
            silent=silent,
        )
        info("Done", force=verbose >= 0)
        indent(level=False)
        info(f"Enriched data is available in version {version}", force=verbose >= 0)
        info(
            "You may need to adapt this TF app and its documentation:",
            tm=False,
            force=verbose >= 0,
        )
        info("please run: python tfFromTei.py apptoken", tm=False, force=verbose >= 0)
        return version

    def task(
        self,
        plaintext=False,
        lingo=False,
        ingest=False,
        write=None,
        verbose=None,
        **kwargs,
    ):
        """Carry out tasks, possibly modified by flags.

        This is a higher level function that can execute a selection of tasks.

        The tasks will be executed in a fixed order: plaintext, lingo, ingest.
        But you can select which one(s) must be executed.

        If multiple tasks must be executed and one fails, the subsequent tasks
        will not be executed.

        Parameters
        ----------
        plaintext: boolean, optional False
            Whether to generate the plain text and position files.
        lingo: boolean, optional False
            Whether to carry out NLP pipeline (Spacy).
        ingest: boolean, optional False
            Whether to ingest the NLP results into the dataset..
        verbose: integer, optional -1
            Produce no (-1), some (0) or many (1) orprogress and reporting messages
        write: boolean, optional False
            Whether to write the generated plain text and position files to disk.
        kwargs: dict
            remaining arguments that can serve as input for the task

        Returns
        -------
        boolean
            Whether all tasks have executed successfully.
        """

        if write is not None:
            self.write = write
        if verbose is not None:
            self.verbose = verbose

        lang = self.lang

        silent = TERSE if verbose == 1 else DEEP

        self.loadApp()
        if not self.good:
            return False

        app = self.app
        app.setSilent(silent)

        txtDir = self.txtDir
        textPath = self.textPath
        tokenFile = self.tokenFile
        sentenceFile = self.sentenceFile

        app.indent(reset=True)

        text = kwargs.get("text", None)
        positions = kwargs.get("positions", None)
        tokens = kwargs.get("tokens", None)
        sentences = kwargs.get("sentences", None)

        result = False

        if plaintext and self.good:
            (text, positions) = self.generatePlain()
            result = (text, positions) if self.good else False

        if lingo and self.good:
            app.info(f"Using NLP pipeline Spacy ({lang}) ...", force=True)
            if text is None or positions is None:
                rec = Recorder(app.api)
                rec.read(textPath)
                text = rec.text()
                positions = rec.positions()

            (tokens, sentences) = self.lingo(text, lang=lang)
            if write:
                if not dirExists(txtDir):
                    dirMake(txtDir)
                writeList(tokens, tokenFile, intCols=(True, True, False, False))
                writeList(sentences, sentenceFile, intCols=(True, True, False))
            app.info("NLP done", force=True)

            result = (tokens, sentences) if self.good else False

        if ingest and self.good:
            if positions is None:
                rec = Recorder(app.api)
                rec.read(textPath)
                positions = rec.positions(simple=True)

            if tokens is None or sentences is None:
                tokens = readList(tokenFile)
                sentences = readList(sentenceFile)
            newVersion = self.ingestTokensAndSentences(positions, tokens, sentences)

            result = newVersion if self.good else False

        if type(result) is bool:
            if not result:
                return False
            else:
                return True

        return result


def main():
    (good, tasks, params, flags) = readArgs("tf-addnlp", HELP, TASKS, PARAMS, FLAGS)
    if not good:
        return False

    NLP = NLPipeline(**params, **flags)
    NLP.task(**tasks, **flags)

    return NLP.good


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
