"""Add data from an NLP pipeline.

When you have used `tf.convert.tei` to convert a TEI data source into a TF dataset,
the situation with words and sentences is usually not satisfactory.
In most TEI sources, words and sentences are not explicitly marked up, and it is
really hard to build token detection and sentence boundary detection into the
conversion program.

There is a better way.
You can use this module to have tokens, sentences and entities detected by NLP pipelines
(currently only Spacy is supported).
The NLP output will then be transformed to nodes and attributes and inserted in
the TF dataset as a new version.

The original slots in the TF dataset (characters) will be discarded, because the
new tokens will be used as slots.

!!! caution "Complications"
    It is possible that tokens cross element boundaries.
    If we did not do anything about that, we would loose resolution, especially in the
    case of inline formatting within tokens. We could not express that anymore.
    That's why we split the tokens across element boundaries.
    However, we then loose the correspondence between tokens and words.
    To overcome that, we turn the tokens into two types:

    *   atomic tokens, by default type `t`
    *   full tokens, by default type `token`

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

        python tfFromTei.py apptoken

# Usage

## Command-line

``` sh
tf-addnlp tasks params flags
```

## From Python

``` python
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
`TASKS`, `PARAMS`, `FLAGS` and expand the code.

The parameters have defaults that are exactly suited to corpora that have been
converted from TEI by `tf.convert.tei`.

## Examples

Exactly how you can call the methods of this module is demonstrated in the small
corpus of 14 letter by the Dutch artist Piet Mondriaan.

*   [Mondriaan](https://nbviewer.org/github/annotation/mondriaan/blob/master/programs/convertExpress.ipynb).
"""

import sys
import re

# from copy import deepcopy

from ..capable import CheckImport
from .recorder import Recorder
from .helpers import CONVERSION_METHODS, CM_NLP
from ..advanced.app import loadApp
from ..tools.xmlschema import Analysis
from ..tools.myspacy import nlpOutput
from ..dataset import modify
from ..core.helpers import console
from ..core.files import initTree, dirMake
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
        "Discardable slot features. Will not be translated to atomic token features",
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
    tkType=("The node type for the atomic tokens.", "t"),
    tokenType=("The node type for the full tokens.", "token"),
    tokenFeatures=(
        (
            "The features in the token output by the NLP: "
            "1: token content; 2: space after the token (if any), ..."
        ),
        "str,after,pos,morph,lemma",
    ),
    tokenNFeature=(
        "The feature that will hold the sequence number of the token.",
        "",
    ),
    sentenceBarriers=("Elements that trigger a sentence boundary.", "div,p"),
    sentenceSkipFlow=("The flows that are not fed to sentence detection.", "orig,del"),
    sentenceType=("The node type for the sentences", "sentence"),
    sentenceFeatures=("", ""),
    sentenceNFeature=(
        "The feature that will hold the sequence number of the sentence",
        "nsent",
    ),
    entityType=("The node type for the entities.", "ent"),
    entityFeatures=(
        (
            "The features in the entity output by the NLP: "
            "1: entity content; 2: entity kind, ..."
        ),
        "estr,kind",
    ),
    entityNFeature=(
        "The feature that will hold the sequence number of the entity",
        "",
    ),
)
"""Possible parameters."""

FLAGS = dict(
    ner=("Whether to do named entity recognition during NLP", False, 2),
    parser=("Whether to run the NLP parser", False, 2),
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


SENT_END = "Foo bar"


class NLPipeline(CheckImport):
    def __init__(
        self,
        app=None,
        lang=PARAMS["lang"][1],
        slotFeature=PARAMS["slotFeature"][1],
        removeSlotFeatures=PARAMS["removeSlotFeatures"][1],
        emptyFeature=PARAMS["emptyFeature"][1],
        ignoreTypes=PARAMS["ignoreTypes"][1],
        outOfFlow=PARAMS["outOfFlow"][1],
        tkType=PARAMS["tkType"][1],
        tokenFeatures=PARAMS["tokenFeatures"][1],
        tokenNFeature=PARAMS["tokenNFeature"][1],
        tokenType=PARAMS["tokenType"][1],
        sentenceBarriers=PARAMS["sentenceBarriers"][1],
        sentenceSkipFlow=PARAMS["sentenceSkipFlow"][1],
        sentenceType=PARAMS["sentenceType"][1],
        sentenceFeatures=PARAMS["sentenceFeatures"][1],
        sentenceNFeature=PARAMS["sentenceNFeature"][1],
        entityType=PARAMS["entityType"][1],
        entityFeatures=PARAMS["entityFeatures"][1],
        entityNFeature=PARAMS["entityNFeature"][1],
        ner=FLAGS["ner"][1],
        parser=FLAGS["parser"][1],
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
        removeSlotFeatures: string
            A tuple is distilled from comma-separated values.
            The names of features defined on original slots that do not have to be
            carried over to the new slots of type of the atomic tokens.
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
        tkType: string, optional t
            The node type for the atomic tokens
        tokenType: string, optional token
            The node type for the full tokens
        tokenFeatures: tuple, optional ("str", "after")
            A tuple is distilled from comma-separated values.
            The names of the features that the atomic token stream contains.
            There must be at least two features:
            the first one should give the token content, the second one the non-token
            material until the next token.
            The rest are additional features that the pipeline might supply.
        tokenNFeature: string, optional None
            If not None, the name of the atomic token feature that will hold the
            sequence number of the atomic token in the data stream, starting at 1.
        sentenceType: string, optional sentence
            The node type for the sentences
        sentenceFeatures: tuple, optional ()
            A tuple is distilled from comma-separated values.
            The names of the features that the sentence stream contains.
        sentenceNFeature: string, optional nsent
            If not None, the name of the sentence feature that will hold the
            sequence number of the sentence in the data stream, starting at 1.
        ner: boolean, optional False
            Whether to perform named entity recognition during NLP processing.
        parser: boolean, optional False
            Whether to run the NLP parser.
        entityType: string, optional ent
            The node type for the full entities
        entityFeatures: tuple, optional ("str", "kind")
            A tuple is distilled from comma-separated values.
            The names of the features that the entity stream contains.
            There must be at least two features:
            the first one should give the entity content, the second one the entity
            kind (or label).
            The rest are additional features that the pipeline might supply.
        entityNFeature: string, optional None
            If not None, the name of the entity feature that will hold the
            sequence number of the entity in the data stream, starting at 1.
        """
        super().__init__("lxml", "spacy")
        if not self.importOK(hint=True):
            return

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
        self.tkType = makeString(tkType)
        self.tokenFeatures = makeTuple(tokenFeatures)
        self.tokenNFeature = makeString(tokenNFeature)
        self.tokenType = makeString(tokenType)
        self.sentenceBarriers = makeSet(sentenceBarriers)
        self.sentenceSkipFlow = makeSet(sentenceSkipFlow)
        self.sentenceType = makeString(sentenceType)
        self.sentenceFeatures = makeTuple(sentenceFeatures)
        self.sentenceNFeature = makeString(sentenceNFeature)
        self.entityType = makeString(entityType)
        self.entityFeatures = makeTuple(entityFeatures)
        self.entityNFeature = makeString(entityNFeature)
        self.ner = ner
        self.parser = parser
        self.verbose = verbose
        self.write = write

    def loadApp(self, app=None, verbose=None):
        """Loads a given TF app or loads the TF app based on the working directory.

        After loading, all slots where non-slot node boundaries occur are computed,
        except for nodes of type word.

        Parameters
        ----------
        app: object, optional None
            The handle to the original TF dataset, already loaded.

            If not given, we load the TF app that is nearby in the file system.

        verbose: integer, optional None
            Produce more progress and reporting messages
            If not passed, take the verbose member of this object.
        """
        if not self.importOK():
            return

        ignoreTypes = self.ignoreTypes

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
        txtDir = f"{repoDir}/_temp/txt/{version}"
        dirMake(txtDir)
        self.txtDir = txtDir
        self.tokenFile = f"{txtDir}/tokens.tsv"
        self.sentenceFile = f"{txtDir}/sentences.tsv"
        self.entityFile = f"{txtDir}/entities.tsv"
        self.textPath = f"{txtDir}/plain.txt"

        if verbose >= 0:
            console("Compute element boundaries")

        api = app.api
        F = api.F
        E = api.E

        firstSlots = set()
        lastSlots = set()

        for node, slots in E.oslots.items():
            if F.otype.v(node) in ignoreTypes:
                continue
            firstSlots.add(slots[0])
            lastSlots.add(slots[-1])

        self.firstSlots = firstSlots
        self.lastSlots = lastSlots

        if verbose >= 0:
            console(f"{len(firstSlots):>6} start positions")
            console(f"{len(lastSlots):>6} end positions")

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
        if not self.importOK(hint=True):
            return

        if verbose is not None:
            self.verbose = verbose
        verbose = self.verbose

        self.elementDefs = {}
        self.mixedTypes = {}

        A = Analysis(verbose=verbose)
        baseSchema = A.getBaseSchema()["xsd"]
        A.getElementInfo(baseSchema, [])
        elementDefs = A.elementDefs

        self.mixedTypes = {
            x for (x, (typ, mixed)) in elementDefs[(baseSchema, None)].items() if mixed
        }

    def generatePlain(self):
        """Generates a plain text out of a data source.

        The text is generated in such a way that out of flow elements are collected
        and put at the end. Examples of such elements are notes.
        Leaving them at their original positions will interfere with sentence detection.

        We separate the flows clearly in the output, so that they are discernible
        in the output of the NLP pipeline.

        Afterwards, when we collect the tokens, we will notice which tokens
        cross element boundaries and need to be split into atomic tokens.

        Returns
        -------
        tuple
            The result is a tuple consisting of

            *   *text*: the generated text
            *   *positions*: a list of nodes such that list item `i` contains
                the original slot that corresponds to the character `i` in the
                generated text (counting from zero).
        """
        if not self.importOK(hint=True):
            return (None, None)

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

        for n, kind in N.walk(events=True):
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
                        flowContent.append(f" \n xxx. \n{SENT_END}. \nEnd meta. \n\n")
                    elif nType in sectionTypes or nType in sentenceBarriers:
                        finishSentence(flowContent)
                        flowContent.append(
                            f" \n xxx. \n{SENT_END}. \nEnd {nType}. \n\n"
                        )
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
                    flowContent.append(f" \n{SENT_END}. \nItem {flow}. \n")
                else:
                    if nType == "teiHeader":
                        flowContent.append(f" \n{SENT_END}. \nBegin meta. \n\n")
                    elif nType in sectionTypes:
                        flowContent.append(f" \n{SENT_END}. \nBegin {nType}. \n\n")
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

            rec.add(f" \n{SENT_END}. \nBegin flow {flow if flow else 'main'}. \n\n")

            for item in items:
                if type(item) is int:
                    if item < 0:
                        rec.start(-item)
                    else:
                        rec.end(item)
                else:
                    rec.add(item)

            rec.add(
                f" \n xxx. \n{SENT_END}. \nEnd flow {flow if flow else 'main'}. \n\n"
            )

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

    def lingo(self, *args, **kwargs):
        if not self.importOK():
            return ()

        return nlpOutput(*args, **kwargs)

    def ingest(
        self,
        isTk,
        isEnt,
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

            When items refer partly to proper corpus text and partly to
            convenience text, they will be narrowed down to the proper text.

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
        isTk: boolean
            Whether the data specifies (atomic) tokens or something else.
            Tokens are special because they are intended to become the new slot type.
        isEnt: boolean
            Whether the data specifies entities or something else.
            Entities are special because they come with a text string which may contain
            generated text that must be stripped.
        positions: list
            which slot node corresponds to which position in the plain text.

        stream: list of tuple
            The tuples should consist of

            *   `start`: a start number (character position in the plain text,
                starting at `0`)
            *   `end`: an end number (character position in the plain text plus one)
            *   `values`: values for feature assignment

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
            If True, rows whose text component is only white-space will be skipped.

        skipFlows: set
            set of elements whose resulting data in the stream should be ignored

        Returns
        -------
        tuple
            We deliver the following pieces of information in a tuple:

            *   the last node
            *   the mapping of the new nodes to the slots they occupy;
            *   the data of the new features.

            However, when we deliver the token results, they come in two such tuples:
            one for the atomic tokens and one for the full tokens.
        """
        if not self.importOK():
            return (
                (
                    (None, None, None),
                    (None, None, None),
                )
                if isTk
                else (None, None, None)
            )

        slotFeature = self.slotFeature
        firstSlots = self.firstSlots
        lastSlots = self.lastSlots

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
        if isTk:
            featuresData = {feat: {} for feat in features[0:2]}
            tokenFeaturesData = {feat: {} for feat in features}
        else:
            featuresData = {feat: {} for feat in features}

        if nFeature is not None:
            featuresData[nFeature] = {}
        if emptyFeature is not None:
            featuresData[emptyFeature] = {}

        if isTk:
            featTk = featuresData[features[0]]
            featTkAfter = featuresData[features[1]]
            featToken = tokenFeaturesData[features[0]]
            featTokenAfter = tokenFeaturesData[features[1]]
            tokenLinks = {}

        if isEnt:
            featEnt = featuresData[features[0]]

        whiteMultipleRe = re.compile(r"^[ \n]{2,}$", re.S)

        node = 0
        token = 0
        itemsOutside = []
        itemsEmpty = []

        info(
            f"generating {tp}-nodes with features {', '.join(featuresData)}",
            force=verbose >= 0,
        )
        indent(level=True)

        numRe = re.compile(r"[0-9]")

        def addTk(last, sAfter):
            """Add an atomic token node to the dataset under construction.

            Parameters
            ----------
            last: boolean
                Whether this is the last atomic token in the full token.
                In that case, the *after* attribute on the token data must be added
                as a feature on this atomic token.
            """
            nonlocal node
            nonlocal curTkSlots
            nonlocal curTkValue

            node += 1
            slotLinks[node] = curTkSlots
            featTk[node] = curTkValue

            # for (feat, val) in zip(features[2:], vals[2:]):
            #     featuresData[feat][node] = val
            # if doN:
            #     featuresData[nFeature][node] = node

            if last:
                after = vals[1] if sAfter is not None else ""
                featTkAfter[node] = after

            curTkSlots = []
            curTkValue = ""

        def addToken(last, sAfter):
            nonlocal token
            nonlocal curTokenSlots
            nonlocal curTokenValue

            token += 1
            tokenLinks[token] = curTokenSlots
            featToken[token] = curTokenValue

            for feat, val in zip(features[2:], vals[2:]):
                tokenFeaturesData[feat][token] = val
            if doN:
                tokenFeaturesData[nFeature][token] = token

            if last:
                after = vals[1] if sAfter is not None else ""
                featTokenAfter[token] = after

            curTokenSlots = []
            curTokenValue = ""

        def addSlot(slot):
            nonlocal node

            node += 1
            slotLinks[node] = [slot]
            featTk[node] = Fslotv(slot)

            if Femptyv(slot):
                featuresData[emptyFeature][node] = 1

        def addEnt(myText):
            nonlocal node

            if numRe.search(myText):
                return

            node += 1
            slotLinks[node] = mySlots
            featEnt[node] = myText

            for feat, val in zip(features[1:], vals[1:]):
                featuresData[feat][node] = val.replace("\n", " ").strip()
            if doN:
                featuresData[nFeature][node] = node

        def addItem():
            nonlocal node

            node += 1
            slotLinks[node] = mySlots
            for feat, val in zip(features, vals):
                featuresData[feat][node] = val
            if doN:
                featuresData[nFeature][node] = node

        # First we identify all the empty slots, provided we are doing tokens

        if isTk:
            emptySlots = (
                {s for s in Femptys(1) if Fotypev(s) == slotType}
                if emptyFeature
                else set()
            )
            emptyWithinTk = 0
            spaceWithinTk = 0
            boundaryWithinTk = 0

            # for slot in sorted(emptySlots):
            #    addSlot(slot)

        # now the data from the NLP pipeline

        flowBeginRe = re.compile(rf" \n{SENT_END}\. \nBegin flow (\w+)\. ")
        flowEndRe = re.compile(rf" \n xxx. \n{SENT_END}\. \nEnd flow (\w+)\. ")

        skipping = False
        flow = None

        for i, (b, e, *vals) in enumerate(stream):
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

            curTkValue = ""
            curTkSlots = []
            curTokenValue = ""
            curTokenSlots = []

            nMySlots = len(mySlots)

            if isTk:
                # we might need to split tokens:
                # * at points that correspond to empty slots
                # * at spaces or newlines within the token
                # * at places where element boundaries occur
                # decompose it into individual characters

                tkText = "".join(Fslotv(s) for s in mySlots)

                if whiteMultipleRe.match(tkText):
                    spaceWithinTk += 1
                    for slot in mySlots:
                        addSlot(slot)

                else:
                    sAfter = positions[e]

                    for i, slot in enumerate(mySlots):
                        last = i == nMySlots - 1
                        isStart = slot in firstSlots
                        isEnd = slot - 1 in lastSlots
                        isBoundary = isStart or isEnd
                        isEmpty = slot in emptySlots

                        if isEmpty and nMySlots > 1:
                            emptyWithinTk += 1
                        if isBoundary:
                            boundaryWithinTk += 1

                        value = Fslotv(slot)

                        # first we deal with atomic tokens

                        if isEmpty or isBoundary:
                            # we are at a split point
                            # emit the current token as atomic token
                            if curTkValue:
                                addTk(last, sAfter)

                        # now we can continue building up atomic tokens

                        curTkValue += value
                        curTkSlots.append(slot)

                        if isEmpty:
                            # after an empty token we have to split again
                            addTk(last, sAfter)

                        # secondly we deal with full tokens

                        if isEmpty:
                            if curTokenValue:
                                addToken(last, sAfter)

                        # now we can continue building up full tokens

                        curTokenValue += value
                        curTokenSlots.append(slot)

                    if curTkValue:
                        addTk(True, sAfter)
                    if curTokenValue:
                        addToken(True, sAfter)

            elif isEnt:
                myText = "".join(Fslotv(s) for s in mySlots)
                if myText:
                    addEnt(myText)
            else:
                if nMySlots:
                    addItem()

        repFeatures = ", ".join(features + ((nFeature,) if doN else ()))
        info(
            f"{node} {tp} nodes have values assigned for {repFeatures}",
            force=verbose >= 0,
        )
        if isTk:
            info(
                f"{emptyWithinTk} empty slots are properly contained in a token",
                force=verbose >= 0,
            )
            info(
                f"{spaceWithinTk} space slots have split into {slotType}s",
                force=verbose >= 0,
            )
            info(
                f"{boundaryWithinTk} slots have split around an element boundary",
                force=verbose >= 0,
            )

        tasks = [("Items contained in extra generated text", itemsOutside)]

        if skipBlanks:
            tasks.append(("Items with empty final text", itemsEmpty))

        for label, items in tasks:
            nItems = len(items)
            info(f"{nItems:>5}x {label}", force=verbose >= 0)
            indent(level=True)
            for i, b, e, *vals in items[0:5]:
                info(
                    f"\t{i} span {b}-{e}: {', '.join(str(v) for v in vals)}",
                    force=verbose == 1,
                )
            indent(level=False)

        indent(level=False)
        return (
            (
                (node, slotLinks, featuresData),
                (token, tokenLinks, tokenFeaturesData),
            )
            if isTk
            else (node, slotLinks, featuresData)
        )

    def ingestNlpOutput(self, positions, tkStream, sentenceStream, entityStream):
        """Ingests NLP output such as tokens in a dataset. Tokens become the new slots.

        By default:

        *   tokens become nodes of a new type `t`;
        *   the texts of tokens ends up in the feature `str`;
        *   if there is a space after a token, it ends up in the feature `after`;
        *   sentences become nodes of a new type `sentence`;
        *   the sentence number ends up in the feature `nsent`.
        *   token nodes become the new slots.
        *   entities become noes of a new type `ent`;
        *   the texts of the entities end up in feature `str`;
        *   the labels of the entities end up in feature `kind`;
        *   entity nodes are linked to the tokens they occupy.

        But this function can also be adapted to token, sentence, and entity streams
        that have additional names and values, see below.

        The streams of NLP output may contain more fields.
        In the parameters `tokenFeatures`, `sentenceFeatures` and `entityFeatures`
        you may pass the feature names for the data in those fields.

        When the streams are read, for each feature name in the `tokenFeatures`
        (resp. `sentenceFeatures`, `entityFeatures`)) the corresponding field
        in the stream will be read, and the value found there will be assigned
        to that feature.

        If there are more fields in the stream than there are declared in the
        `tokenFeatures` (resp. `sentenceFeatures`) parameter, these extra fields will
        be ignored.

        The last feature name in these parameters is special.
        If it is None, it will be ignored.
        Otherwise, an extra feature with that name will be created, and it will be
        filled with the node numbers of the newly generated nodes.

        !!! hint "Look at the defaults"
            The default `tokenFeatures=("str", "after")` specifies that two
            fields from the token stream will be read, and those values will be
            assigned to features `str` and `after`.
            There will be no field with the node itself in it.

            The default `sentenceFeatures=()` specifies that no field from the
            token stream will be read. But that there is a feature `nsent` that
            has the node of each sentence as value.

        We have to ignore the sentence boundaries in some flows,
        e.g. the material coming from `<orig>` and `<del>` elements.
        However, in the flow coming from the `<note>` elements, we want to retain the
        sentence boundaries.

        Parameters
        ----------
        positions: list
            which slot node corresponds to which position in the plain text.
        tkStream: list
            The list of tokens as delivered by the NLP pipe.
        sentenceStream: list
            The list of sentences as delivered by the NLP pipe.

        Returns
        -------
        string
            The new version number of the data that contains the NLP output..
        """
        if not self.importOK():
            return None

        emptyFeature = self.emptyFeature
        removeSlotFeatures = self.removeSlotFeatures
        tkType = self.tkType
        tokenFeatures = self.tokenFeatures
        tokenNFeature = self.tokenNFeature
        tokenType = self.tokenType
        sentenceType = self.sentenceType
        sentenceFeatures = self.sentenceFeatures
        sentenceNFeature = self.sentenceNFeature
        sentenceSkipFlow = self.sentenceSkipFlow
        entityType = self.entityType
        entityFeatures = self.entityFeatures
        entityNFeature = self.entityNFeature
        ner = self.ner

        app = self.app
        info = app.info
        indent = app.indent
        verbose = self.verbose
        silent = "auto" if verbose == 1 else TERSE if verbose == 0 else DEEP

        info(
            "Ingesting NLP output into the dataset ...",
            force=verbose >= 0,
        )
        indent(level=True)
        info("Mapping NLP data to nodes and features ...", force=verbose >= 0)
        indent(level=True)

        slotLinks = {tkType: {}, sentenceType: {}}
        features = {}
        lastNode = {}

        for feat in (*tokenFeatures, tokenNFeature):
            if feat is not None:
                features[feat] = {}
        lastNode[tkType] = 0

        canSentences = len(sentenceStream) != 0

        if canSentences:
            for feat in (*sentenceFeatures, sentenceNFeature):
                if feat is not None:
                    features[feat] = {}
            lastNode[sentenceType] = 0

        if ner:
            for feat in (*entityFeatures, entityNFeature):
                if feat is not None:
                    features[feat] = {}
                lastNode[entityType] = 0

        for isTk, isEnt, data, skipFlows, tp, feats, nFeat, skipBlanks, thisEmpty in (
            (
                True,
                False,
                tkStream,
                None,
                tkType,
                tokenFeatures,
                tokenNFeature,
                False,
                emptyFeature,
            ),
            (
                False,
                False,
                sentenceStream,
                sentenceSkipFlow,
                sentenceType,
                sentenceFeatures,
                sentenceNFeature,
                True,
                None,
            ),
            (
                False,
                True,
                entityStream,
                None,
                entityType,
                entityFeatures,
                entityNFeature,
                True,
                None,
            ),
        ):
            if data is None or len(data) == 0:
                continue
            ingestResult = self.ingest(
                isTk,
                isEnt,
                positions,
                data,
                tp,
                feats,
                nFeature=nFeat,
                emptyFeature=thisEmpty,
                skipBlanks=skipBlanks,
                skipFlows=skipFlows,
            )
            if isTk:
                (
                    (node, theseSlotLinks, featuresData),
                    (token, tokenSlotLinks, tokenFeaturesData),
                ) = ingestResult
                lastNode[tokenType] = token
                slotLinks[tokenType] = tokenSlotLinks
                info(f"{lastNode[tokenType]} {tokenType}s", force=verbose >= 0)
            else:
                (node, theseSlotLinks, featuresData) = ingestResult

            lastNode[tp] = node
            slotLinks[tp] = theseSlotLinks
            for feat, featData in featuresData.items():
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

        allEntityFeatures = list(entityFeatures)
        if entityNFeature is not None:
            allEntityFeatures.append(entityNFeature)

        addTypes = {
            tkType: dict(
                nodeFrom=1,
                nodeTo=lastNode[tkType],
                nodeSlots=slotLinks[tkType],
                nodeFeatures={feat: features[feat] for feat in allTokenFeatures},
            ),
            tokenType: dict(
                nodeFrom=1,
                nodeTo=lastNode[tokenType],
                nodeSlots=slotLinks[tokenType],
                nodeFeatures={
                    feat: tokenFeaturesData[feat] for feat in allTokenFeatures
                },
            ),
        }
        if canSentences:
            addTypes[sentenceType] = dict(
                nodeFrom=1,
                nodeTo=lastNode[sentenceType],
                nodeSlots=slotLinks[sentenceType],
                nodeFeatures={feat: features[feat] for feat in allSentenceFeatures},
            )

        if ner:
            addTypes[entityType] = dict(
                nodeFrom=1,
                nodeTo=lastNode[entityType],
                nodeSlots=slotLinks[entityType],
                nodeFeatures={feat: features[feat] for feat in allEntityFeatures},
            )

        featureMeta = dict(
            otext={
                "fmt:text-orig-full": "{"
                + tokenFeatures[0]
                + "}{"
                + tokenFeatures[1]
                + "}"
            },
        )
        for i, f in enumerate(allTokenFeatures):
            description = (
                "the text of the token"
                if i == 0
                else "the whitespace after the token"
                if i == 1
                else "the part of speech of the token"
                if i == 2
                else "the morphological tag of the token"
                if i == 3
                else "the lemma of the token"
                if i == 4
                else "token feature generated by the NLP tool"
            )
            featureMeta[f] = dict(
                valueType="str",
                description=description,
                conversionMethod=CM_NLP,
                conversionCode=CONVERSION_METHODS[CM_NLP],
            )

        if ner:
            for i, f in enumerate(allEntityFeatures):
                description = (
                    "the string value of the entity"
                    if i == 0
                    else "the kind of the entity"
                    if i == 1
                    else "entity feature generated by the NLP tool"
                )
                featureMeta[f] = dict(
                    valueType="str",
                    description=description,
                    conversionMethod=CM_NLP,
                    conversionCode=CONVERSION_METHODS[CM_NLP],
                )

        if canSentences:
            featureMeta[sentenceNFeature] = dict(
                valueType="int",
                description="number of sentences in corpus",
                conversionMethod=CM_NLP,
                conversionCode=CONVERSION_METHODS[CM_NLP],
            )
        if ner and entityNFeature:
            featureMeta[entityNFeature] = dict(
                valueType="int",
                description="number of entity in corpus",
                conversionMethod=CM_NLP,
                conversionCode=CONVERSION_METHODS[CM_NLP],
            )

        modify(
            origTf,
            newTf,
            targetVersion=version,
            addTypes=addTypes,
            deleteTypes=("word",),
            featureMeta=featureMeta,
            replaceSlotType=(tkType, *removeSlotFeatures),
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

        The tasks will be executed in a fixed order: `plaintext`, `lingo`, `ingest`.
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
            Produce no (-1), some (0) or many (1) progress and reporting messages
        write: boolean, optional False
            Whether to write the generated plain text and position files to disk.
        kwargs: dict
            remaining arguments that can serve as input for the task

        Returns
        -------
        boolean | any
            False if a task failed, otherwise whatever the last task delivered.
        """
        if not self.importOK():
            return (
                None
                if ingest
                else (None, None)
                if lingo
                else (None, None)
                if plaintext
                else None
            )

        if write is None:
            write = self.write
        else:
            self.write = write

        verboseGiven = verbose

        if verboseGiven is not None:
            verboseSav = self.verbose
            self.verbose = verboseGiven

        verbose = self.verbose

        lang = self.lang
        parser = self.parser
        ner = self.ner

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
        entityFile = self.entityFile

        app.indent(reset=True)

        text = kwargs.get("text", None)
        positions = kwargs.get("positions", None)
        tokens = kwargs.get("tokens", None)
        sentences = kwargs.get("sentences", None)

        if ner:
            entities = kwargs.get("entities", None)

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

            nlpData = self.lingo(text, lang=lang, ner=ner, parser=parser)
            (tokens, sentences) = nlpData[0:2]
            entities = nlpData[2] if ner else None

            if write:
                dirMake(txtDir)
                writeList(
                    tokens,
                    tokenFile,
                    intCols=(True, True, False, False, False, False, False),
                )
                writeList(sentences, sentenceFile, intCols=(True, True, False))
                app.info(f"Tokens written to {tokenFile}", force=verbose >= 0)
                app.info(f"Sentences written to {sentenceFile}", force=verbose >= 0)
                if ner:
                    writeList(entities, entityFile, intCols=(True, True, False, False))
                    app.info(f"Entities written to {entityFile}", force=verbose >= 0)
            app.info("NLP done", force=True)

            result = (
                tuple(x for x in (tokens, sentences, entities) if x is not None)
                if self.good
                else False
            )

        if ingest and self.good:
            if positions is None:
                rec = Recorder(app.api)
                rec.read(textPath)
                positions = rec.positions(simple=True)

            if tokens is None or sentences is None:
                tokens = readList(tokenFile)
                sentences = readList(sentenceFile)
            if ner and entities is None:
                entities = readList(entityFile)

            newVersion = self.ingestNlpOutput(
                positions, tokens, sentences, entities if ner else None
            )

            result = newVersion if self.good else False

        if verboseGiven is not None:
            self.verbose = verboseSav

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
