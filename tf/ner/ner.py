"""Named Entity Recognition by Triggers.

As a preparation, read `tf.about.annotate` first, since it explains the concepts, and
guides you to set up the configuration for your corpus.

We explain here how to work with entity spreadsheets.

In a spreadsheet you can assign *triggers* to entities.
Triggers are strings to search for in the corpus.
You can limit the scope of these triggers to specific portions in the corpus.

The specification of the content and organization of such a entity sheet is in
`tf.ner.sheets.Sheets.readSheetData()`.

You can place entity sheets in the directory `ner/specs` at the toplevel of the repo,
or, if you are not working from the repo, you can look up the corpus
under your `text-fabric-data` directory, and find a `ner` directory there.

The output data of the tool ends up in the `_temp` directory, which ends up next
to the `ner` directory.

## For corpus designers

If you are a corpus designer, you can declare this `ner` directory as an extra
data module. Then it will packaged with the TF dataset of your corpus, and users
that use your corpus also get this directory, and can work with the NER tool
in the TF browser.

The way to declare this `ner` data module is by making sure that `app/config.yaml`
has this:

```
provenanceSpec:
    ...
    extraData: ner
    ...
```

Additionally, you can create a file `ner/config.yaml` with some settings for the
NER process. See `tf.ner.settings.Settings`.

You can also put a file `code.py` there in which you implement the function
`normalizeChars(string): string`

If you implement it, it will be invoked as a text transformation function upon
reading string data from spreadsheets.
The idea is that if the corpus is normalized for certain characters,
you can normalize the search terms and names in the spreadsheet in the
same way. For example, in the Suriano corpus, all incarnations of an
apostrophe, such as `’` or `'` or `‘` have been normalized to `’`.
But the spreadsheet might still use the unwanted the variants.
By providing a suitable function you can prevent that.

## Starting up

### In the TF browser

On the command line say:

```
tf org/repo --tool=ner
```

If you are at the top level of the repo, you can even say

```
tf --tool=ner
```

Then use the chooser at the top right of the interface to select an annotation
set. There are three kinds of sets:

*   **=** The (readonly) set of entities that are already baked in into the TF dataset;
*   **🧾** (readonly) sets of entities defined by a spreadsheet;
*   **🖍️** (mutable) sets of entities created manually by the user with the NER tool
    in the TF browser.

![browser](../../images/Ner/select2.png)

### In a program

Import the relevant Python modules:

``` python
from tf.app import use
```

Load your corpus. There are two ways:

*   Work with a local GitHub clone of the corpus in `~/HuygensING/suriano`:

        A = use("HuygensING/suriano:clone", checkout="clone")

*   Or let TF auto-download the latest version and work with that:

        A = use("HuygensING/suriano")

Load the `Ner` module:

``` python
NE = A.makeNer()
```

You can now load a spreadsheet by

``` python
NE.setTask(".people")
```

**N.B.:** The leading `.` in the name signifies that this set is coupled with a
spreadsheet.

## Trigger investigations

We now assume that you are working with a program, ideally in a Jupyter notebook.

There are a few rule in trigger based entity search:

*   the corpus is searched from beginning to end;
*   if at some place in the corpus multiple triggers match, the longest match
    counts, and the others are discarded;
*   if at some place, a trigger has matched, searching continues past the end of
    the match.

A consequence of these rules is that at no token in the corpus is part of a double
match.

The idea behind this is that if you have two triggers, that the more specific trigger
takes precedence above the lesser specific one.

However, the rules also have some pitfalls, which can lead to triggers that
have unexpectedly no results, or less results than expected.

Here are a few caveats:

*   Overlapping triggers: if you have the following triggers:

    *   `the mayor`
    *   `mayor of London`

    then the second one looks more specific than the first one. but if you have this
    passage in the corpus:

    `the mayor of London`

    then `mayor of London` will not be found. Because before it can be found,
    `the mayor` will be found, after which searching continues at `of London`, and
    this does not match the trigger `mayor of London`.

    The solution to cases like this is: `the mayor` is a rather generic trigger, and
    it will only be valid in specific spots in the corpus.

    So add a scope to this trigger, and make sure that `the mayor of London` is outside
    that scope.

When the entity spreadsheet is big, with over a thousand triggers for hundreds of names,
it is difficult to keep track of all the tricky interactions between triggers.

For that reason we have a few diagnostic functions that help you to spot them:

*   `tf.ner.ner.Ner.triggerInterference()` will list the triggers belonging to
    different entities that overlap and for which there are occurrences where this
    overlap is problematic;

*   `tf.ner.ner.Ner.reportHits()` will list the triggers without hits while they do
    occur in the corpus; it will give diagnostic info about those triggers; it also
    produces statistics about the inventory of entities that has been collected on the
    basis of the triggers; finally it produces a file that lists the number of hits
    per entity, per trigger, per scope and per section where the occurrences have
    been found.
"""

import collections
from itertools import chain

from ..dataset import modify
from ..core.generic import AttrDict
from ..core.helpers import console
from ..core.timestamp import SILENT_D, DEEP
from ..core.files import fileOpen, dirRemove, dirNm, dirExists, APP_CONFIG

from .sets import Sets
from .sheets import Sheets
from .match import entityMatch, occMatch
from .show import Show
from .helpers import findCompile


class NER(Sheets, Sets, Show):
    """API for Named Entity marking.

    This class is the central class of the trigger based Named Entity
    Recognition tool whose main task is to find occurrences of annotations on
    the basis of criteria.

    This class inherits from a number of other classes:

    *   `tf.ner.sheets`: manage annotation spreadsheets;
    *   `tf.ner.sets`: manage annotation sets;
    *   `tf.ner.show`: generate HTML for annotated buckets of the corpus;

    In turn, these classes inherit from yet other classes:

    *   `tf.ner.sets` from `tf.ner.data`: manage the annotation data in various
        convenient representations;
    *   `tf.ner.data` from `tf.ner.corpus`: manage the corpus dependent bits; it uses
        the TF machinery to extract the specifics of the corpus;
    *   `tf.ner.corpus` from `tf.ner.settings`: additional settings, some of which
        derive from a config file;
    *   `tf.ner.sheets` from:

        *   `tf.ner.scopes`: support the concept of scope in the corpus;
        *   `tf.ner.triggers`: support the concept of trigger;

    The NER machinery can be used by

    *   users to manipulate annotations in their own programs, especially in a
        Jupyter notebook.
    *   `tf.browser.ner.web`: Flask app that routes URLs to controller functions.

    The browsing experience is supported by:

    *   `tf.browser.ner.web`: map urls to the controllers of the web app
    *   `tf.browser.ner.serve`: implement the controllers of the web app
    *   `tf.browser.ner.request`: manage the data of a request;
    *   `tf.browser.ner.form`: retrieve form values into typed and structured values.
    *   `tf.browser.ner.fragments`: generate HTML for widgets on the page;
    *   `tf.browser.ner.websettings`: settings for the browser experience;
    *   `tf.browser.html`: a generic library to generate HTML using Pythonic syntax.

    See this
    [example notebook](https://nbviewer.org/urls/gitlab.huc.knaw.nl/suriano/letters/-/raw/main/programs/ner.ipynb/%3Fref_type%3Dheads%26inline%3Dfalse).
    """

    def __init__(
        self,
        app,
        data=None,
        browse=False,
        caseSensitive=False,
        silent=False,
    ):
        """Top level functions for entity annotation.

        This is a high-level class, building on the lower-level tools provided
        by the Sheets, Sets and Show classes on which it is based.

        These methods can be used by code that runs in the TF browser
        and by code that runs in a Jupyter notebook.

        This class handles entity tasks, which is an abstraction of the concepts of
        set and sheet.

        It does not handle HTML generation, but its parent class, `Show`, does that.

        We consider the corpus as a list of buckets (lowest level sectional
        units; in TEI-derived corpora called `chunk`, being generalizations of
        `p` (paragraph) elements). We read this type off from the TF dataset,
        see `tf.ner.corpus.bucketType`

        Parameters
        ----------
        app: object
            The object that corresponds to a loaded TF app for a corpus.
        data: object, optional None
            Entity data to start with. If this class is initialized by the browser,
            the browser hands over the in-memory data that the tool needs.
            That way, it can maintain access to the same data between requests.
            If None, no data is handed over, and a fresh data store will be
            created by an ancestor class (Data)
        browse: boolean, optional False
            If True, the object is informed that it is run by the TF
            browser. This will influence how results are reported back.
        caseSensitive: boolean, optional False
            Whether the lookup of entities should be case-sensitive. For spreadsheets
            it specifies whether the triggers should be treated case-sensitively.
        silent: boolean, optional False
            Whether to keep most operations silent.
        """
        if data is None:
            data = AttrDict()

        if data.sets is None:
            data.sets = AttrDict()

        if data.sheets is None:
            data.sheets = AttrDict()

        self.silent = silent
        self.browse = browse
        self.app = app

        self.caseSensitive = caseSensitive

        Sets.__init__(self, sets=data.sets)
        if not self.properlySetup:
            return

        Sheets.__init__(self, sheets=data.sheets)
        if not self.properlySetup:
            return

    def setTask(self, task, force=False, caseSensitive=None):
        if caseSensitive is None:
            caseSensitive = self.caseSensitive

        (newSetNameRep, newSetRo, newSetSrc, newSetX) = self.setInfo(task)
        self.setSet(task)
        self.setSheet(
            task[1:] if newSetX else None,
            force=force,
            caseSensitive=caseSensitive,
        )

    def getTasks(self):
        setNames = self.setNames

        tasks = set()

        for setName in setNames:
            tasks.add(
                setName.removesuffix("-no-case").removesuffix("-with-case")
                if setName.startswith(".")
                else setName
            )

        return tasks

    def findOccs(self):
        """Finds the occurrences of multiple triggers.

        This is meant to efficiently list all occurrences of many token
        sequences in the corpus.

        The triggers are in member `instructions`, which must first
        be constructed by reading a number of excel files.

        It adds the member `inventory` to the object, which is a dict
        with subdicts:

        `occurrences`: keyed by tuples (eid, kind), the values are
        the occurrences of that entity in the corpus.
        A single occurrence is represented as a tuple of slots.

        `names`: keyed by tuples (eid, kind) and then path,
        the value is the name of that entity in the context indicated by path.

        """
        if not self.properlySetup:
            return []

        settings = self.settings
        spaceEscaped = settings.spaceEscaped

        setData = self.getSetData()
        getTokens = self.getTokens
        seqFromNode = self.seqFromNode

        buckets = setData.buckets or ()

        sheetData = self.getSheetData()
        instructions = sheetData.instructions
        caseSensitive = sheetData.caseSensitive
        sheetData.inventory = occMatch(
            getTokens,
            seqFromNode,
            buckets,
            instructions,
            spaceEscaped,
            caseSensitive=caseSensitive,
        )

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
        of buckets, or a subset of buckets, namely those contained in a
        particular node, see parameters `node`, and `buckets`.

        **Bucket filtering**

        The parameters `bFind`, `bFindC`, `bFindRe`  specify a regular expression
        search on the texts of the buckets.

        The positions of the found occurrences is included in the result.

        The parameter `anyEnt` is a filter on the presence or absence of entities in
        buckets in general.

        **Entity filtering**

        The parameter `eVals` holds the values of a specific entity to look for.

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
            the buckets to filter. If both are specified, their effect will be
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

            The feature values to filter on.
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

        getTextR = self.getTextR
        getTokens = self.getTokens

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
                getTextR,
                getTokens,
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

    def bakeEntities(self, versionExtension="e"):
        """Consolidates the current entities as nodes into a new TF data source.

        This operation is not allowed if the current set is the read-only set with the
        empty name, because these entities are already present as nodes in the
        TF dataset.

        Parameters
        ----------
        versionExtension: string, optional "e"
            The new dataset gets a version like the original dataset, but extended
            with this string.
        """
        if not self.properlySetup:
            return

        silent = self.silent
        setNameRep = self.setNameRep
        setIsSrc = self.setIsSrc

        if setIsSrc:
            console(f"Entity consolidation not meaningful on {setNameRep}", error=True)
            return False

        version = self.version
        settings = self.settings
        features = settings.features
        featureMeta = settings.featureMeta
        setData = self.getSetData()

        # Data preparation for the modify function

        entityOccs = sorted(set(setData.entities.values()))
        self.console(
            f"Entity consolidation for {len(entityOccs)} entity occurrences "
            f"into version {version}{versionExtension}"
        )

        slotLink = {}
        nodeFeatures = AttrDict({feat: {} for feat in features})
        edgeFeatures = AttrDict(eoccs={})
        entities = {}

        n = 0

        for fVals, slots in entityOccs:
            n += 1
            slotLink[n] = slots

            for feat, fVal in zip(features, fVals):
                nodeFeatures[feat][n] = fVal

            entities.setdefault(fVals, []).append(n)

        nEntityOccs = len(entityOccs)
        occEdge = edgeFeatures.eoccs

        for fVals, occs in entities.items():
            n += 1
            occEdge[n] = set(occs)
            slotLink[n] = tuple(chain.from_iterable(slotLink[m] for m in occs))

            for feat, fVal in zip(features, fVals):
                nodeFeatures[feat][n] = fVal

        nEntities = len(entities)

        self.console(f"{nEntityOccs:>6} entity occurrences")
        self.console(f"{nEntities:>6} distinct entities")

        featureMeta.eoccs = dict(
            valueType="str",
            description="from entity nodes to their occurrence nodes",
        )

        addTypes = dict(
            ent=dict(
                nodeFrom=1,
                nodeTo=nEntityOccs,
                nodeSlots=slotLink,
                nodeFeatures=nodeFeatures,
            ),
            entity=dict(
                nodeFrom=nEntityOccs + 1,
                nodeTo=nEntityOccs + nEntities,
                nodeSlots=slotLink,
                nodeFeatures=nodeFeatures,
                edgeFeatures=edgeFeatures,
            ),
        )
        self.featureMeta = featureMeta

        # Call the modify function

        app = self.app
        context = app.context
        appPath = context.appPath
        relative = context.relative
        dataPath = f"{dirNm(appPath)}/{relative}"

        origTf = f"{dataPath}/{app.version}"
        newTf = f"{origTf}{versionExtension}"
        newVersion = f"{app.version}{versionExtension}"

        if dirExists(newTf):
            dirRemove(newTf)

        app.indent(reset=True)

        if not silent:
            app.info("Creating a dataset with entity nodes ...")

        good = modify(
            origTf,
            newTf,
            targetVersion=newVersion,
            addTypes=addTypes,
            featureMeta=featureMeta,
            silent=DEEP if silent else SILENT_D,
        )

        if not silent:
            app.info("Done")

        if not good:
            return False

        self.console(f"The dataset with entities is now in version {newVersion}")

        # tweak the app

        config = f"{appPath}/{APP_CONFIG}"

        with fileOpen(config) as fh:
            text = fh.read()

        text = text.replace(f"version: {version}", f'version: "{newVersion}"')
        text = text.replace(f'version: "{version}"', f'version: "{newVersion}"')

        with fileOpen(config, mode="w") as fh:
            fh.write(text)

        self.console("The dataset with entities is now the standard version")

        return True
