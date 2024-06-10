"""API for Named Entity marking.

As a preparation, read `tf.about.annotate` first, since it explains the concepts, and
guides you to set up the configuration for your corpus.

The main task of this module is to find occurrences of annotations
on the basis of criteria.

But this is just the tip of the iceberg, since this module inherits
from a number of other modules that inherit form yet other modules:

*   `tf.browser.ner.show`: generate HTML for annotated buckets of the corpus;
*   `tf.browser.ner.sets`: manage annotation sets;
*   `tf.browser.ner.data`: manage annotation data: loading, adding/deleting
    annotations;
*   `tf.browser.ner.settings`: manage the specifics of a TF corpus and have
    access to its data.

It also uses

*   `tf.browser.ner.match`: to filter individual buckets on the basis of
    criteria.

Hence, `Annotation` is the central class of this tool, whose methods are relevant
for:

*   `tf.browser.ner.ner`: the API for users to manipulate annotations in their
    own programs, especially in a Jupyter notebook.
*   `tf.browser.ner.web`: Flask app that routes URLs to controller functions.

`web` makes use of the following modules that are not needed by `ner`:

*   `tf.browser.ner.serve`: define the controllers of the web app

Again, this is a top of an iceberg, since it inherits from:

*   `tf.browser.ner.request`: manage the data of a request;
*   `tf.browser.ner.fragments`: generate HTML for widgets on the page;

`request` also uses `form` to retrieve form values into typed and structured values.

Both `web` and `ner` make use of the following modules in as far as they are not
already mentioned under `annotate` and its parent classes:

*   `tf.browser.ner.helpers`: a variety of context-free data jugglers;
*   `tf.browser.html`: a generic library to generate HTML using Pythonic
    syntax.
This module contains the top-level methods for applying annotation rules to a corpus.

!!! note "Class hierarchy"
    The classes `Settings`, `Corpus`, `Data`, `Sets`, `Show`, `NER`
    form one hierarchy.
    So an object of class `NER` has access to all methods of these classes.

    The classes `Serve`, `Request`, `Fragments`, `From` form a separate hierarchy.
    It will create an `NER` instance which will be stored in a `Serve` instance.

Here is an overview how the modules hang together.

A `|` denotes inheritance, parent classes above child classes.

A `<-<` arrow denotes dependency by importing code.

```
Browser                           |   Api-hierarchy
----------------------------------------------------------------
web <-----< Serve <-----------------< NER              <-< match
            |   |                 |     |
       Request Fragments <-< html |   Sets Sheets Show <-< html
          |                       |     |
        Form                      |   Data
                                  |     |
                                  |   Corpus
                                  |     |
                                  |   Settings
```

# Programmatic annotation done in a Jupyter Notebook

If you have a spreadsheet with named entities, and for each entity a list of surface forms,
then this module takes care to read that spreadsheet, translate it to YAML,
and then use the YAML as instructions to add entity annotations to the corpus.

See this
[example notebook](https://nbviewer.jupyter.org/github/HuygensING/suriano/blob/main/programs/ner.ipynb).

Here are more details.

## Starting up

Load the relevant Python modules:

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

The tool expects some input data to be present: configuration and spreadsheets with
instructions. They can be found in the `ner` directory.
If you work with a local GitHub clone, that data resides in
`~/github/HuygensING/suriano`
and if you work with an auto-downloaded copy of the data, it is in
`~/text-fabric-data/github/HuygensING/suriano`.

The output data of the tool ends up in the `_temp` directory, which ends up next
to the `ner` directory.

## The entity spreadsheets

Here is an example:

![browser](../../images/Ner/spreadsheet.png)

In our example, the name of the spreadsheet containing this information is
`people.xlsx` and it can be found as `ner/sheets/people.xlsx`

The spreadsheet will be read as follows:

*   the first two rows will be skipped
*   after that, each row is taken to describe exactly one entity
*   the first column has the full and unique name for that entity
*   the second column contains the kind of the entity (you may choose your
    keywords freely for this)
*   the third column contains a number of surface forms for this entity,
    separated by `;`
*   when the surface forms are peeled out, leading and trailing white-space will be
    stripped
*   all other columns will be ignored for the moment; in later versions we may use
    the information in those columns to fill in extra data about the entities;
    but probably that information will not end up in TF features.

During translation from XLSX to YAML the following happens:

*   An identifier is distilled from the name of the entity;
*   Missing kind fields are filled with the default kind.

These steps need some configuration information from the `ner/config.yaml` file.

Translation is done by

``` python
NE.setSheet("people")
```

The resulting YAML ends up next to the
spreadsheet, and it looks like this:

``` yaml
christoffel.sticke:
  kind: PER
  name: Christoffel Sticke
  occSpecs: []
diederik.sticke:
  kind: PER
  name: Diederik Sticke
  occSpecs:
  - Dierck
  - Dirk
dirck.hartog:
  kind: PER
  name: Dirck Hartog
  occSpecs:
  - Dirich Hartocson
  - Hertocson
jan.baptist.roelants:
  kind: PER
  name: Jan-Baptist Roelants
  occSpecs:
  - Roelans
  - Rolans
```

## Inventory

A first step is to find out how many occurrences we find in the corpus for these
surface forms:

``` python
NE.lookup()
NE.showHits()
```

and the output looks like this

```
...

cornelis.adriaensz       PER   Pach                     7 x Cornelis Adriaensz. Pack
david.marlot             PER   Morlot                   1 x David de Marlot
erick.dimmer             PER   Dimer                   11 x Erick Dimmer
erycius.puteanus         PER   Potiano                  2 x Erycius Puteanus
francesco.giustiniani    PER   Giustiniano             11 x Francesco Giustiniani
francois.doubleth        PER   Doublet                  2 x François Doubleth

...

Total 150
```

Entities that are in the spreadsheet, but not in the corpus are skipped.

## Marking up

In order to create annotations for these entities, we have to switch to an
annotation set. Let's start a new set and give it the name `power`.

``` python
NE.setSet("power")
```

If it turns out that `power` has already annotations, and you want to clear them, say

``` python
NE.resetSet("power")
```

Now we are ready for the big thing: creating the annotations:

``` python
NE.markEntities()
```

It outputs this message:

```
Already present:     0 x
Added:             150 x
```

## Inspection

We now revert to lower-level methods from the `tf.browser.ner.ner` class to
inspect some of the results.

``` python
results = NE.filterContent(bFind="pach", bFindC=False, anyEnt=True, showStats=None)
```

Here we filtered the chunks (paragraphs) to those that contain the string `pach`,
in a case-insensitive way, and that contain at least one entity.

There 6 of them, and we can show them:

``` python
NE.showContent(results)
```

![browser](../../images/Ner/pach.png)

The resulting entities are in `_temp/power/entities.tsv` and look like this:

```
erick.dimmer	PER	160196
isabella.clara.eugenia	PER	142613
gaspar.iii.coligny	PER	7877
isabella.clara.eugenia	PER	210499
john.vere	PER	94659
antonio.lando	PER	267755
isabella.clara.eugenia	PER	107069
isabella.clara.eugenia	PER	9162
michiel.pagani	PER	94366
isabella.clara.eugenia	PER	179208
isabella.clara.eugenia	PER	258933
hans.meinhard	PER	75039

...
```

Each line corresponds to a marked entity occurrence.
Lines consist of tab separated fields:

*   entity identifier
*   entity kind
*   remaining fields: slots, i.e. the textual positions occupied by the occurrence.
    Some entity occurrences consist of multiple words / tokens, hence have multiple
    slots.

"""
from textwrap import dedent
import collections

from ...core.helpers import console
from ...core.generic import AttrDict
from .sheets import Sheets
from .helpers import findCompile
from .sets import Sets
from .show import Show
from .match import entityMatch, occMatch


class NER(Sheets, Sets, Show):
    def __init__(self, app, data=None, browse=False):
        """Entity annotation.

        Basic methods to handle the various aspects of entity annotation.
        These methods can be used by code that runs in the TF browser
        and by code that runs in a Jupyter notebook.

        This class handles entity sets, it does not contain code to generate HTML.
        But it has a parent class, `Show`, that can generate HTML.

        This class works with a fixed annotation set.
        But it has a parent class, `Sets` that has method to manipulate such sets
        and switch between them.

        We consider the corpus as a list of buckets (typically level-3 sectional
        units; in TEI-derived corpora called `chunk`, being generalizations of
        `p` (paragraph) elements). What type exactly the buckets are is configured
        in the `ner/config.yaml` file.

        Contains methods to translate spreadsheets to YAML files with markup
        instructions; to locate all relevant occurrences; and to mark them up
        properly.

        It is a high-level class, building on the lower-level tools provided
        by the Sheets, Sets and Show classes on which it is based.

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
        """
        if data is None:
            data = AttrDict()

        if data.sets is None:
            data.sets = AttrDict()

        if data.sheets is None:
            data.sheets = AttrDict()

        self.browse = browse
        self.app = app

        Sets.__init__(self, sets=data.sets)
        if not self.properlySetup:
            return

        Sheets.__init__(self, sheets=data.sheets)
        if not self.properlySetup:
            return

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
        getHeadings = self.getHeadings

        buckets = setData.buckets or ()

        sheetName = self.sheetName
        sheetData = self.sheets[sheetName]

        instructions = sheetData.instructions
        sheetData.inventory = occMatch(
            getTokens, getHeadings, buckets, instructions, spaceEscaped
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

        settings = self.settings
        bucketType = settings.bucketType
        features = settings.features

        getTextR = self.getTextR
        getTokens = self.getTokens

        browse = self.browse
        setData = self.getSetData()
        entityIndex = setData.entityIndex
        entityVal = setData.entityVal
        entitySlotVal = setData.entitySlotVal
        entitySlotAll = setData.entitySlotAll
        entitySlotIndex = setData.entitySlotIndex

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
                    self.console(errorMsg, error=True)

        hasEnt = eVals is not None
        hasQTokens = qTokens is not None and len(qTokens)
        hasOcc = not hasEnt and hasQTokens

        if eVals is not None and eVals in entityVal:
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
                getTextR,
                getTokens,
                b,
                bFindRe,
                anyEnt,
                eVals,
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

    def lookup(self):
        """Explores the corpus for the surface forms mentioned in the instructions.

        The instructions are present in the `instructions` attribute of the object.

        The resulting inventory is stored in the `inventory` member of
        the object.

        It is a dictionary, keyed by sequences of tokens, whose values are the
        slot sequences where those token sequences occur in the corpus.
        """
        if not self.properlySetup:
            return

        self.processSheet(True)

    def reportHits(self):
        """Reports the inventory."""
        if not self.properlySetup:
            return

        sheetName = self.sheetName
        sheetData = self.sheets[sheetName]

        getHeadings = self.getHeadings
        nameMap = self.nameMap
        inventory = sheetData.inventory
        instructions = sheetData.instructions

        reportBase = self.reportBase
        reportDir = f"{reportBase}/{sheetName}"
        reportFile = f"{reportDir}/hits.tsv"

        allTriggers = set()

        for path, data in instructions.items():
            idMap = data["idMap"]
            tMap = data["tMap"]

            for trigger, tPath in tMap.items():
                eidkind = idMap[trigger]
                name = nameMap[eidkind][0]
                allTriggers.add((name, eidkind, trigger, tPath))

        hitData = []
        names = set()
        triggersSuccess = 0

        for e in sorted(allTriggers):
            (name, eidkind, trigger, tPath) = e

            names.add(name)

            sheet = ".".join(tPath)
            entry = (name, trigger, sheet)
            section = ""
            hits = ""

            entInfo = inventory.get(eidkind, None)

            if entInfo is None:
                hitData.append(("!E", *entry, "", 0))
                continue

            triggerInfo = entInfo.get(trigger, None)

            if triggerInfo is None:
                hitData.append(("!T", *entry, "", 0))
                continue

            occs = triggerInfo.get(tPath, None)

            if occs is None:
                hitData.append(("!P", *entry, "", 0))
                continue

            triggersSuccess += 1
            sectionInfo = collections.Counter()

            for slots in occs:
                section = ".".join(getHeadings(slots[0]))
                sectionInfo[section] += 1

            for section, hits in sorted(sectionInfo.items()):
                hitData.append(("OK", *entry, section, hits))

        with open(reportFile, "w") as rh:
            rh.write("label\tname\ttrigger\tsheet\tsection\thits\n")

            for h in sorted(hitData):
                line = "\t".join(str(c) for c in h)
                rh.write(f"{line}\n")

        nEnt = len(names)
        nTriggers = len(allTriggers)
        nHits = sum(e[-1] for e in hitData)

        console(
            dedent(
                f"""
                Entities targeted:       {nEnt:>5}
                Triggers searched for:   {nTriggers:>5}
                Triggers with hits:      {triggersSuccess:>5}
                Triggers without hits:   {nTriggers - triggersSuccess:>5}
                Total hits:              {nHits:>5}

                All hits in report file: {reportFile}
                """
            )
        )

    def markEntities(self):
        """Marks up the members of the inventory as entities.

        The instructions contain the entity identifier and the entity kind that
        have to be assigned to the surface forms.

        The inventory knows where the occurrences of the surface forms are.
        If there is no inventory yet, it will be created.
        """
        if not self.properlySetup:
            return

        browse = self.browse
        sheetName = self.sheetName
        sheetData = self.sheets[sheetName]
        inventory = sheetData.inventory

        newEntities = []

        for (eidkind, entData) in inventory.items():
            for (trigger, triggerData) in entData.items():
                for matches in triggerData.values():
                    newEntities.append((eidkind, matches))

        self.setSet(sheetName)

        if self.getSetData():
            if not browse:
                console(f"Set {sheetName} already exists. I will not overwrite it.")
                console("Clear or delete this set before marking the entities")
            return

        self.addEntities(newEntities, silent=False)

    def bakeEntities(self, versionExtension="e"):
        """Bakes the entities of the current set as nodes into a new TF data source.

        Parameters
        ----------
        versionExtension: string, optional "e"
            The new dataset gets a version like the original dataset, but extended
            with this string.
        """
        self.consolidateEntities(versionExtension=versionExtension)
