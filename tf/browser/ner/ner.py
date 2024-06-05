"""API for rule-based entity marking.

This module contains the top-level methods for applying annotation rules to a corpus.

To see how this fits among all the modules of this package, see
`tf.browser.ner.annotate` .

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

![browser](../../images/Annotate/spreadsheet.png)

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
NE.readInstructions("people")
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
NE.makeInventory()
NE.showInventory()
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

We now revert to lower-level methods from the `tf.browser.ner.annotate` class to
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

![browser](../../images/Annotate/pach.png)

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

from ...capable import CheckImport
from ...core.helpers import console
from .annotate import Annotate
from .helpers import toTokens
from .triggers import Triggers


class NER(Annotate):
    def __init__(self, app):
        """Bulk entity annotation.

        Contains methods to translate spreadsheets to YAML files with markup
        instructions; to locate all relevant occurrences; and to mark them up
        properly.

        It is a high-level class, building on the lower-level tools provided
        by the Annotate class on which it is based.

        Parameters
        ----------
        app: object
            The object that corresponds to a loaded TF app for a corpus.
        """
        super().__init__(app)
        if not self.properlySetup:
            return

        self.Trig = None
        """Will contain the object that has compiled the triggers for named entities.
        """

        self.inventory = None
        """Will contain the locations of all surface forms in the current instructions.
        """

    def readInstructions(self, sheetName):
        """Reads the trigger specifications.

        See `tf.browser.ner.triggers`.

        Parameters
        ----------
        sheetName: string
            The file name without extension of the spreadsheet.
            The spreadsheet is expected in the `ner/sheets` directory.
            It may be accompanied by a directory with the same name (without extension)
            containing more specialized trigger specs: per section level.
        """
        CI = CheckImport("openpyxl")
        if CI.importOK(hint=True):
            openpyxl = CI.importGet()
            self.load_workbook = openpyxl.load_workbook
        else:
            return None

        if not self.properlySetup:
            return None

        Trig = Triggers(self)
        Trig.read(sheetName)
        self.Trig = Trig

    def makeInventory(self):
        """Explores the corpus for the surface forms mentioned in the instructions.

        The instructions are present in the `instructions` attribute of the object.

        The resulting inventory is stored in the `inventory` member of
        the object.

        It is a dictionary, keyed by sequences of tokens, whose values are the
        slot sequences where those token sequences occur in the corpus.
        """
        if not self.properlySetup:
            return

        Trig = self.Trig
        self.instructions = Trig.instructions

        app = self.app
        app.indent(reset=True)
        app.info("Looking up occurrences of many candidates ...")
        self.findOccs()
        inventory = self.inventory
        nEnt = len(inventory)
        totalHits = sum(
            sum(
                sum(len(x) for x in pathData.values())
                for pathData in triggerData.values()
            )
            for triggerData in inventory.values()
        )
        console(f"{totalHits} for {nEnt} entities")

    def showInventory(self, expanded=False, localOnly=False, missingOnly=False):
        """Shows the inventory."""
        if not self.properlySetup:
            return

        Trig = self.Trig
        nameMap = Trig.nameMap
        inventory = self.inventory
        instructions = self.instructions

        if not missingOnly:
            i = 0

            for eidkind, triggerData in sorted(inventory.items()):
                i += 1
                if not expanded and i > 20:
                    break

                entityHits = sum(
                    sum(len(x) for x in pathData.values())
                    for pathData in triggerData.values()
                )
                if localOnly:
                    localHits = sum(
                        sum(len(x) for (path, x) in pathData.items() if path != ())
                        for pathData in triggerData.values()
                    )
                    if localHits == 0:
                        continue

                name = nameMap[eidkind][0]
                console(f"{entityHits} x '{name}'")

                for trigger, pathData in sorted(triggerData.items()):
                    triggerHits = sum(len(x) for x in pathData.values())
                    console(f"    {triggerHits} x {trigger}")

                    for path, occs in sorted(pathData.items()):
                        pathHits = len(occs)
                        pathRep = ".".join(path)
                        console(f"        {pathHits} x from [{pathRep}]")

        instructions = self.instructions
        allTriggers = set()
        notFound = []

        for (path, data) in instructions.items():
            sheet = data["sheet"]
            tMap = data["tMap"]

            for (eidkind, triggers) in sheet.items():
                for trigger in triggers:
                    tPath = tMap[trigger]
                    allTriggers.add((eidkind, trigger, tPath))

        i = 0

        for e in sorted(allTriggers):
            i += 1
            if not expanded and i > 20:
                break

            (eidkind, trigger, tPath) = e
            entInfo = inventory.get(eidkind, None)

            if entInfo is None:
                notFound.append(("E", e))
                continue

            triggerInfo = entInfo.get(trigger, None)

            if triggerInfo is None:
                notFound.append(("T", e))
                continue

            pathInfo = triggerInfo.get(tPath, None)

            if pathInfo is None:
                notFound.append(("P", e))

        if len(notFound) == 0:
            console("Found matches for all triggers")
        else:
            console(f"{len(notFound)} triggers have no match:")

            for (label, (eidkind, trigger, tPath)) in notFound:
                console(f"{label} '{nameMap[eidkind][0]}' as '{trigger}' in {tPath}")

    def markEntities(self):
        """Marks up the members of the inventory as entities.

        The instructions contain the entity identifier and the entity kind that
        have to be assigned to the surface forms.

        The inventory knows where the occurrences of the surface forms are.
        If there is no inventory yet, it will be created.
        """
        if not self.properlySetup:
            return

        inventory = self.inventory
        instructions = self.instructions
        settings = self.settings
        spaceEscaped = settings.spaceEscaped
        keywordFeatures = settings.keywordFeatures
        kindFeature = keywordFeatures[0]

        newEntities = []

        qSets = set()
        fValsByQTokens = {}

        for eid, info in instructions.items():
            kind = info[kindFeature]

            occSpecs = info.occSpecs
            if not len(occSpecs):
                continue

            for occSpec in info.occSpecs:
                qTokens = toTokens(occSpec, spaceEscaped=spaceEscaped)
                fValsByQTokens.setdefault(qTokens, set()).add((eid, kind))
                qSets.add(qTokens)

        if self.inventory is None:
            self.findOccs()

        for qTokens, matches in inventory.items():
            for fVals in fValsByQTokens[qTokens]:
                newEntities.append((fVals, matches))

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
