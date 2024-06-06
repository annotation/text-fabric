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
from textwrap import dedent
import collections

from ...capable import CheckImport
from ...core.helpers import console
from ...core.files import initTree
from .annotate import Annotate
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

        reportBase = self.reportBase
        reportDir = f"{reportBase}/{sheetName}"
        self.reportDir = reportDir

        initTree(reportDir, fresh=False)

        Trig = Triggers(self)
        self.Trig = Trig

        Trig.intake(sheetName)
        self.instructions = Trig.instructions

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

        app = self.app
        app.indent(reset=True)
        app.info("Looking up occurrences of many candidates ...")
        self.findOccs()
        self.reportHits()

    def reportHits(self):
        """Reports the inventory."""
        if not self.properlySetup:
            return

        getHeadings = self.getHeadings
        Trig = self.Trig
        nameMap = Trig.nameMap
        inventory = self.inventory
        instructions = self.instructions

        reportDir = self.reportDir
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

        inventory = self.inventory

        newEntities = []

        for (eidkind, entData) in inventory.items():
            for (trigger, triggerData) in entData.items():
                for matches in triggerData.values():
                    newEntities.append((eidkind, matches))

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
