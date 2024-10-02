# `A.` Advanced API

## Initialization, configuration, meta data, and linking

``` python
A = use('org/repo')
```
:   start up and load a corpus from a repository and deliver its API.
:   See `tf.about.usefunc`

``` python
A.hoist(globals())
```
:   Make the API handles `F`, `E`, `T`, `L` etc available in 
    the global scope.
:   `tf.advanced.app.App.load`

``` python
A.load(features)
```
:   Load an extra bunch of features. 
:   `tf.advanced.app.App.load`

``` python
A.featureTypes(show=True)
```
:   show for which types each feature is defined
:   `tf.advanced.app.App.featureTypes`

``` python
A.showContext(...)
```
:   show app settings
:   `tf.advanced.settings.showContext`

``` python
A.header(allMeta=False)
```
:   show colophon
:   `tf.advanced.links.header`

``` python
A.showProvenance(...)
```
:   show provenance of code and data
:   `tf.advanced.links.showProvenance`

``` python
A.webLink(n, ...)
```
:   hyperlink to node `n` on the web
:   `tf.advanced.links.webLink`

``` python
A.flexLink("pages")
A.flexLink("tut")
```
:   hyperlink to app tutorial and documentation
:   `tf.advanced.links.flexLink`

``` python
A.isLoaded(features=None)
```
:   Show information about loaded features
:   `tf.core.api.Api.isLoaded`

``` python
A.footprint()
```
:   Show memory footprint per feature
:   `tf.core.api.Api.footprint`

---

## Displaying

``` python
A.specialCharacters()
```
:   show all hard-to-type characters in the corpus in a widget
:   `tf.advanced.text.specialCharacters`

``` python
A.showFormats()
```
:   show all text formats and their definitions
:   `tf.advanced.text.showFormats`

``` python
A.dm(markdownString)
```
:   display markdown string in notebook
:   `tf.advanced.helpers.dm`

``` python
A.dh(htmlString)
```
:   display HTML string in notebook
:   `tf.advanced.helpers.dh`

``` python
A.method(option1=value1, option2=value2, ...)
```
:   Many of the following methods accept these options as keyword arguments: 
:   `tf.advanced.options`

``` python
A.displayShow(...)
```
:   show display options
:   `tf.advanced.display.displayShow`

``` python
A.displayReset(...)
```
:   reset display options
:   `tf.advanced.display.displayReset`

``` python
A.displaySetup(...)
```
:   set up display options
:   `tf.advanced.display.displaySetup`

``` python
A.table(results, ...)
```
:   plain rendering of tuple of tuples of node
:   `tf.advanced.display.table`

``` python
A.plainTuple(tup, ...)
```
:   plain rendering of tuple of node
:   `tf.advanced.display.plainTuple`

``` python
A.plain(node, ...)
```
:   plain rendering of node
:   `tf.advanced.display.plain`

``` python
A.show(results, ...)
```
:   pretty rendering of tuple of tuples of node
:   `tf.advanced.display.show`

``` python
A.prettyTuple(tup, ...)
```
:   pretty rendering of tuple of node
:   `tf.advanced.display.prettyTuple`

``` python
A.pretty(node, ...)
```
:   pretty rendering of node
:   `tf.advanced.display.pretty`

``` python
A.unravel(node, ...)
```
:   convert a graph to a tree
:   `tf.advanced.unravel.unravel`

``` python
A.getCss()
```
:   get the complete CSS style sheet for this app
:   `tf.advanced.display.getCss`

---

## Search (high level)

``` python
A.search(...)
```
:   search, collect and deliver results, report number of results
:   `tf.advanced.search.search`

---

## Sections and Structure

``` python
A.nodeFromSectionStr(...)
```
:   lookup node for section heading
:   `tf.advanced.sections.nodeFromSectionStr`

``` python
A.sectionStrFromNode(...)
```
:   lookup section heading for node
:   `tf.advanced.sections.sectionStrFromNode`

``` python
A.structureStrFromNode(...)
```
:   lookup structure heading for node
:   `tf.advanced.sections.structureStrFromNode`

---

## Volumes and collections

See also `tf.about.volumes`.

``` python
A.getVolumes()
```
:   list all volumes of this dataset
:   `tf.fabric.Fabric.getVolumes`


``` python
A.extract(volumes, ...)
```
:   export volumes based on a volume specification
:   `tf.fabric.Fabric.extract`


``` python
A.collect(volumes, ...)
```
:   collect several volumes into a new collection
:   `tf.advanced.display.export`
:   `tf.fabric.Fabric.collect`

---

## Export to Excel

``` python
A.export(results, ...)
```
:   export formatted data
:   `tf.advanced.display.export`

---

# Logging

``` python
A.dm(markdownString)
```
:   display markdown string in notebook
:   `tf.advanced.helpers.dm`

``` python
A.dh(htmlString)
```
:   display HTML string in notebook
:   `tf.advanced.helpers.dh`

``` python
A.version
```
:   version number of data of the corpus.
:   `tf.fabric.Fabric.version`

The following methods work also for `TF.` instead of `A.`:

``` python
A.banner
```
:   banner of the TF program.
:   `tf.fabric.Fabric.banner`

``` python
A.isSilent()
```
:   report the verbosity of TF
:   `tf.core.timestamp.Timestamp.isSilent`

``` python
A.silentOn(deep=False)
```
:   make TF (deeply) silent from now on.
:   `tf.core.timestamp.Timestamp.silentOn`

``` python
A.silentOff()
```
:   make TF talkative from now on.
:   `tf.core.timestamp.Timestamp.silentOff`

``` python
A.setSilent(silent)
```
:   set the verbosity of TF.
:   `tf.core.timestamp.Timestamp.setSilent`

``` python
A.indent(level=None, reset=False)
```
:   Sets up indentation and timing of following messages
:   `tf.core.timestamp.Timestamp.indent`

``` python
A.info(msg, tm=True, nl=True, ...)
```
:   informational message
:   `tf.core.timestamp.Timestamp.info`

``` python
A.warning(msg, tm=True, nl=True, ...)
```
:   warning message
:   `tf.core.timestamp.Timestamp.warning`

``` python
A.error(msg, tm=True, nl=True, ...)
```
:   error message
:   `tf.core.timestamp.Timestamp.error`

---

# `N. F. E. L. T. S. C.` Core API

## `N.` Nodes

Read about the canonical ordering here: `tf.core.nodes`.

``` python
N.walk()
```
:   generator of all nodes in canonical ordering
:   `tf.core.nodes.Nodes.walk`

``` python
N.sortNodes(nodes)
```
:   sorts `nodes` in the canonical ordering
:   `tf.core.nodes.Nodes.sortNodes`

``` python
N.otypeRank[nodeType]
```
:   ranking position of `nodeType`
:   `tf.core.nodes.Nodes.otypeRank`

``` python
N.sortKey(node)
```
:   defines the canonical ordering on nodes
:   `tf.core.nodes.Nodes.sortKey`

``` python
N.sortKeyTuple(tup)
```
:   extends the canonical ordering on nodes to tuples of nodes
:   `tf.core.nodes.Nodes.sortKeyTuple`

``` python
N.sortKeyChunk(node)
```
:   defines the canonical ordering on node chunks
:   `tf.core.nodes.Nodes.sortKeyChunk`

---

## `F.` Node features

``` python
Fall()
```
:   all loaded feature names (node features only)
:   `tf.core.api.Api.Fall`

``` python
F.fff.v(node)
```
:   get value of node feature `fff`
:   `tf.core.nodefeature.NodeFeature.v`

``` python
F.fff.s(value)
```
:   get nodes where feature `fff` has `value`
:   `tf.core.nodefeature.NodeFeature.s`

``` python
F.fff.freqList(...)
```
:   frequency list of values of `fff`
:   `tf.core.nodefeature.NodeFeature.freqList`

``` python
F.fff.items(...)
```
:   generator of all entries of `fff` as mapping from nodes to values
:   `tf.core.nodefeature.NodeFeature.items`

``` python
F.fff.meta
```
:   meta data of feature `fff`
:   `tf.core.nodefeature.NodeFeature.meta`

``` python
Fs('fff')
```
:   identical to `F.ffff`, usable if name of feature is variable
:   `tf.core.api.Api.Fs`

---

## Special node feature `otype`

Maps nodes to their types.

``` python
F.otype.v(node)
```
:   get type of `node`
:   `tf.core.otypefeature.OtypeFeature.v`

``` python
F.otype.s(nodeType)
```
:   get all nodes of type `nodeType`
:   `tf.core.otypefeature.OtypeFeature.s`

``` python
F.otype.sInterval(nodeType)
```
:   gives start and ending nodes of `nodeType`
:   `tf.core.otypefeature.OtypeFeature.sInterval`

``` python
F.otype.items(...)
```
:   generator of all (node, type) pairs.
:   `tf.core.otypefeature.OtypeFeature.items`

``` python
F.otype.meta
```
:   meta data of feature `otype`
:   `tf.core.otypefeature.OtypeFeature.meta`

``` python
F.otype.maxSlot
```
:   the last slot node
:   `tf.core.otypefeature.OtypeFeature.maxSlot`

``` python
F.otype.maxNode
```
:   the last node
:   `tf.core.otypefeature.OtypeFeature.maxNode`

``` python
F.otype.slotType
```
:   the slot type
:   `tf.core.otypefeature.OtypeFeature.slotType`

``` python
F.otype.all
```
:   sorted list of all node types
:   `tf.core.otypefeature.OtypeFeature.all`

---

## `E.` Edge features

``` python
Eall()
```
:   all loaded feature names (edge features only)
:   `tf.core.api.Api.Eall`

``` python
E.fff.f(node)
```
:   get value of feature `fff` for edges *from* node
:   `tf.core.edgefeature.EdgeFeature.f`

``` python
E.fff.t(node)
```
:   get value of feature `fff` for edges *to* node
:   `tf.core.edgefeature.EdgeFeature.t`

``` python
E.fff.freqList(...)
```
:   frequency list of values of `fff`
:   `tf.core.edgefeature.EdgeFeature.freqList`

``` python
E.fff.items(...)
```
:   generator of all entries of `fff` as mapping from edges to values
:   `tf.core.edgefeature.EdgeFeature.items`

``` python
E.fff.b(node)
```
:   get value of feature `fff` for edges *from* and *to* node
:   `tf.core.edgefeature.EdgeFeature.b`

``` python
E.fff.meta
```
:   all meta data of feature `fff`
:   `tf.core.edgefeature.EdgeFeature.meta`

``` python
Es('fff')
```
:   identical to `E.fff`, usable if name of feature is variable
:   `tf.core.api.Api.Es`

---

## Special edge feature `oslots`

Maps nodes to the set of slots they occupy.

``` python
E.oslots.items(...)
```
:   generator of all entries of `oslots` as mapping from nodes to sets of slots
:   `tf.core.oslotsfeature.OslotsFeature.items`

``` python
E.oslots.s(node)
```
:   set of slots linked to `node`
:   `tf.core.oslotsfeature.OslotsFeature.s`

``` python
E.oslots.meta
```
:   all meta data of feature `oslots`
:   `tf.core.oslotsfeature.OslotsFeature.meta`

---

## `L.` Locality

``` python
L.i(node, otype=...)
```
:   go to intersecting nodes
:   `tf.core.locality.Locality.i`

``` python
L.u(node, otype=...)
```
:   go one level up
:   `tf.core.locality.Locality.u`

``` python
L.d(node, otype=...)
```
:   go one level down
:   `tf.core.locality.Locality.d`

``` python
L.p(node, otype=...)
```
:   go to adjacent previous nodes
:   `tf.core.locality.Locality.p`

``` python
L.n(node, otype=...)
```
:   go to adjacent next nodes
:   `tf.core.locality.Locality.n`

---

## `T.` Text

``` python
T.text(node, fmt=..., ...)
```
:   give formatted text associated with node
:   `tf.core.text.Text.text`

---

## Sections

Rigid 1 or 2 or 3 sectioning system

``` python
T.sectionTuple(node)
```
:   give tuple of section nodes that contain node
:   `tf.core.text.Text.sectionTuple`

``` python
T.sectionFromNode(node)
```
:   give section heading of node
:   `tf.core.text.Text.sectionFromNode`

``` python
T.nodeFromSection(section)
```
:   give node for section heading
:   `tf.core.text.Text.nodeFromSection`

---

## Structure

Flexible multilevel sectioning system

``` python
T.headingFromNode(node)
```
:   give structure heading of node
:   `tf.core.text.Text.headingFromNode`

``` python
T.nodeFromHeading(heading)
```
:   give node for structure heading
:   `tf.core.text.Text.nodeFromHeading`

``` python
T.structureInfo()
```
:   give summary of dataset structure
:   `tf.core.text.Text.structureInfo`

``` python
T.structure(node)
```
:   give structure of `node` and all in it.
:   `tf.core.text.Text.structure`

``` python
T.structurePretty(node)
```
:   pretty print structure of `node` and all in it.
:   `tf.core.text.Text.structurePretty`

``` python
T.top()
```
:   give all top-level structural nodes in the dataset
:   `tf.core.text.Text.top`

``` python
T.up(node)
```
:   gives parent of structural node
:   `tf.core.text.Text.up`

``` python
T.down(node)
```
:   gives children of structural node
:   `tf.core.text.Text.down`

---

## `S.` Search (low level)

[searchRough](https://nbviewer.jupyter.org/github/ETCBC/bhsa/blob/master/tutorial/searchRough.ipynb)

### Preparation

``` python
S.search(query, limit=None)
```
:   Query the TF dataset with a template
:   `tf.search.search.Search.search`

``` python
S.study(query, ...)
```
:   Study the query in order to set up a plan
:   `tf.search.search.Search.study`

``` python
S.showPlan(details=False)
```
:   Show the search plan resulting from the last study.
:   `tf.search.search.Search.showPlan`

``` python
S.relationsLegend()
```
:   Catalog of all relational devices in search templates
:   `tf.search.search.Search.relationsLegend`

---

### Fetching results

``` python
S.count(progress=None, limit=None)
```
:   Count the results, up to a limit
:   `tf.search.search.Search.count`

``` python
S.fetch(limit=None, ...)
```
:   Fetches the results, up to a limit
:   `tf.search.search.Search.fetch`

``` python
S.glean(tup)
```
:   Renders a single result into something human readable.
:   `tf.search.search.Search.glean`

---

### Implementation

``` python
S.tweakPerformance(...)
```
:   Set certain parameters that influence the performance of search.
:   `tf.search.search.Search.tweakPerformance`

---

## `C.` Computed data components.

Access to pre-computed data: `tf.core.computed.Computeds`.

All components have just one useful attribute: `.data`.

``` python
Call()
```
:   all pre-computed data component names
:   `tf.core.api.Api.Call`

``` python
Cs('ccc')
```
:   identical to `C.ccc`, usable if name of component is variable
:   `tf.core.api.Api.Cs`

``` python
C.levels.data
```
:   various statistics on node types
:   `tf.core.prepare.levels`

``` python
C.order.data
```
:   the canonical order of the nodes (`tf.core.nodes`)
:   `tf.core.prepare.order`

``` python
C.rank.data
```
:   the rank of the nodes in the canonical order (`tf.core.nodes`)
:   `tf.core.prepare.rank`

``` python
C.levUp.data
```
:   feeds the `tf.core.locality.Locality.u` function
:   `tf.core.prepare.levUp`

``` python
C.levDown.data
```
:   feeds the `tf.core.locality.Locality.d` function
:   `tf.core.prepare.levDown`

``` python
C.boundary.data
```
:   feeds the `tf.core.locality.Locality.p` and `tf.core.locality.Locality.n`
    functions
:   `tf.core.prepare.boundary`

``` python
C.characters.data
```
:   frequency list of characters in a corpus, separately for all the text formats
:   `tf.core.prepare.characters`

``` python
C.sections.data
```
:   feeds the section part of `tf.core.text`
:   `tf.core.prepare.sections`

``` python
C.structure.data
```
:   feeds the structure part of `tf.core.text`
:   `tf.core.prepare.structure`

---

# `TF.` Dataset

## Loading

``` python
TF = Fabric(locations=dirs, modules=subdirs, volume=None, collection=None, silent="auto")
```
:   Initialize API on work or single volume or collection of a work
    from explicit directories.
    Use `tf.app.use` instead wherever you can.
    See also `tf.about.volumes`.
:   `tf.fabric.Fabric`


``` python
TF.isLoaded(features=None)
```
:   Show information about loaded features
:   `tf.core.api.Api.isLoaded`

``` python
TF.explore(show=True)
```
:   Get features by category, loaded or unloaded
:   `tf.fabric.Fabric.explore`

``` python
TF.loadAll(silent="auto")
```
:   Load all loadable features. 
:   `tf.fabric.Fabric.loadAll`

``` python
TF.load(features, add=False)
```
:   Load a bunch of features from scratch or additionally. 
:   `tf.fabric.Fabric.load`

``` python
TF.ensureLoaded(features)
```
:   Make sure that features are loaded.
:   `tf.core.api.Api.ensureLoaded`

``` python
TF.makeAvailableIn(globals())
```
:   Make the members of the core API available in the global scope
:   `tf.core.api.Api.makeAvailableIn`

``` python
TF.ignored
```
:   Which features have been overridden.
:   `tf.core.api.Api.ignored`

``` python
TF.footprint()
```
:   Show memory footprint per feature
:   `tf.core.api.Api.footprint`

---

## Volumes

See also `tf.about.volumes`.

``` python
TF.getVolumes()
```
:   list all volumes of this dataset
:   `tf.fabric.Fabric.getVolumes`


``` python
TF.extract(volumes, ...)
```
:   export volumes based on a volume specification
:   `tf.fabric.Fabric.extract`


``` python
TF.collect(volumes, ...)
```
:   collect several volumes into a new collection
:   `tf.advanced.display.export`
:   `tf.fabric.Fabric.collect`

## Saving and Publishing

``` python
TF.save(nodeFeatures={}, edgeFeatures={}, metaData={},,...)
```
:   Save a bunch of newly generated features to disk.
:   `tf.fabric.Fabric.save`


``` python
A.publishRelease(increase, message=None, description=None,,...)
```
:   Commit the dataset repo, tag it, release it, and attach the
    complete zipped data to it.
:   `tf.advanced.repo.publishRelease`

---

## House keeping

``` python
TF.version
```
:   version number of TF.
:   `tf.fabric.Fabric.version`

``` python
TF.clearCache()
```
:   clears the cache of compiled TF data
:   `tf.fabric.Fabric.clearCache`

``` python
from tf.clean import clean
```

``` python
clean()
```
:   clears the cache of compiled TF data
:   `tf.clean`

---

# Volume support

TF datasets per volume or collection of a work.
See also `tf.about.volumes`.

``` python
from tf.volumes import getVolumes

getVolumes(volumeDir)
```
:   List volumes in a directory.
:   `tf.volumes.extract.getVolumes`

``` python
from tf.volumes import extract

extract(work, volumes, ...)
```
:   Extracts volumes from a work
:   `tf.volumes.extract`

``` python
from tf.volumes import collect

collect(volumes, work, ...)
```
:   Collects several volumes into a new collection
:   `tf.volumes.collect`

---

# Dataset Operations

``` python
from tf.dataset import modify

modify(source, target, ...)
```
:   Modifies a TF dataset into a new TF dataset
:   `tf.dataset.modify`

``` python
from tf.dataset import Versions

Versions(api, va, vb, slotMap)
```
:   Extends a slot mapping between versions of a TF dataset
    to a complete node mapping
:   `tf.dataset.nodemaps`

---

# Data Interchange

## Custom node sets for search

``` python
from tf.lib import readSets
from tf.lib import writeSets
```

``` python
readSets(sourceFile)
```
:   reads a named sets from file
:   `tf.lib.readSets`

``` python
writeSets(sets, destFile)
```
:   writes a named sets to file
:   `tf.lib.writeSets`

---

## Export to Excel

``` python
A.export(results, ...)
```
:   export formatted data
:   `tf.advanced.display.export`

---

## Export to ZIP

``` python
A.zipAll()
```
:   store the complete corpus data in a file *complete.zip*
:   `tf.advanced.zipdata.zipAll`

---

## Interchange with external annotation tools

``` python
from tf.convert.addnlp import NLPipeline
```

``` python
NLPipeline()
```
:   generate plain text, feed into NLP, ingest results
:   `tf.convert.addnlp`

---

``` python
from convert.recorder import Recorder
```

``` python
Recorder()
```
:   generate annotatable plain text and import annotations
:   `tf.convert.recorder`

---

## XML / TEI import

``` python
from tf.convert.xml import XML
```

``` python
X = XML(...)
```
:   convert XML source to full-fledged TF dataset plus app but no docs;
    put in your own conversion code, if you wish;
    see [Greek New Testament](https://nbviewer.org/github/ETCBC/nestle1904/blob/master/programs/tfFromLowfat.ipynb)
:   `tf.convert.xml`

``` python
from tf.convert.tei import TEI
```

``` python
T = TEI(...)
```
:   convert TEI source to full-fledged TF dataset plus app plus docs
:   `tf.convert.tei`

---

## WATM export

``` python
from tf.app import use
from tf.convert.watm import WATM
```

``` python
A = use(...)
WA = WATM(A, ns, ...)
WA.makeText()
WA.makeAnno()
WA.writeAll()
WA.testAll()
```
:   convert TF dataset to text tokens and annotations in JSON format,
    for consumption by TextRepo/AnnoRepo of
    [KNAW/HuC Digital Infrastructure](https://di.huc.knaw.nl/text-analysis-en.html).
    See
    [Mondriaan Proeftuin](https://github.com/annotation/mondriaan)
    [Suriano Letters](https://gitlab.huc.knaw.nl/suriano/letters)
    [TransLatin Corpus](https://gitlab.huc.knaw.nl/translatin/corpus)
:   `tf.convert.watm`

``` python
from tf.convert.watm import WATMS
```

``` python
W = WATM(org, repo, backend, ns, ...)
W.produce()
```
:   convert series of TF datasets to WATM
:   `tf.convert.watm.WATMS`

---

## NLP import

**in order to use this, install Spacy, see `tf.tools.myspacy`**

``` python

from tf.convert.addnlp import addTokensAndSentences
```

``` python
newVersion = addTokensAndSenteces(A)
```
:   add NLP output from Spacy to an existing
    TF dataset. See the docs how this is broken down in separate
    steps.
:   `tf.convert.addnlp`

---

## `pandas` export

``` python
A.exportPandas()
```
:   export dataset as `pandas` data frame
:   `tf.convert.pandas`

---

## MQL interchange

``` python
TF.exportMQL(mqlDb, exportDir=None)
A.exportMQL(mqlDb, exportDir=None)
```
:   export loaded dataset to MQL
: `tf.convert.mql.exportMQL`

``` python
from tf.convert.mql import importMQL

TF = importMQL(mqlFile, saveDir)
```
:   convert MQL file to TF dataset
:   `tf.convert.mql.importMQL`

---

## Walker conversion

``` python
from tf.convert.walker import CV
```

``` python
cv = CV(TF)
```
:   convert structured data to TF dataset
:   `tf.convert.walker`

---

## Exploding

``` python
from tf.convert.tf import explode
```

``` python
explode(inLocation, outLocation)
```
:   explode TF feature files to straight data files without optimizations
:   `tf.convert.tf.explode`

---

# TF App development

``` python
A.reuse()
```
:   reload configuration data
:   `tf.advanced.app.App.reuse`

``` python
from tf.advanced.find import loadModule
```

``` python
mmm = loadModule("mmm", *args)
```
:   load specific module supporting the corpus app
:   `tf.advanced.find.loadModule`

```
~/mypath/myname/app/config.yaml
```
:   settings for a TF App
:   `tf.advanced.settings`

---

# Layered search

(these work on the command-line if TF is installed)

``` sh
tf-make {dataset} {client} ship
```
:   generate a static site with a search interface in client-side JavaScript and
    publish it to GitHub pages.
    If `{client}` is left out, generate all clients that are defined for this
    dataset.
    Clients are defined in the `app-{dataset}` repo, under `layeredsearch`.
    More commands
    [here](https://github.com/annotation/text-fabric/blob/master/tf/client/make/help.py).
:   `tf.client.make.build`

``` sh
tf-make {dataset} serve
```
:   serve the search interfaces defined for `{dataset}` locally.

More commands
[here](https://github.com/annotation/text-fabric/blob/master/tf/client/make/help.py).

---

# Annotation tools

(these work in the TF browser and in Jupyter Notebooks)

## Named Entity Annotation

``` sh
tf {org}/{repo} --tool=ner 
```
:   Starts the TF browser for the corpus in *org*/*repo* and opens the manual
    annotation tool.
:   `tf.about.annotateBrowser`

``` python
NE = A.makeNer()
```
:   Sets up the 'manual' annotation API for the corpus in `A`.
:   `tf.browser.ner.ner`
:   More info and examples in `tf.about.annotate` .

---

# Command-line tools

(these work on the command-line if TF is installed)

``` sh
tf {org}/{repo}
tf {org}/{repo}
```
:   Starts the TF browser for the corpus in *org*/*repo*.
:   `tf.browser.start`

``` sh
tf-zipall
```
:   Zips the TF dataset located by the current directory,
    *with all its additional data modules*, but only *the latest version*,
    so that it can be attached to a release on GitHub / GitLab.
:   `tf.advanced.zipdata.zipAll` and `tf.zip`

``` sh
tf-zip {org}/{repo}
```
:   Zips the TF dataset in *org*/*repo* so that it can be attached to a release on
    GitHub / GitLab.
:   `tf.advanced.zipdata`

``` sh
tf-nbconvert {inDirectory} {outDirectory}
```
:   Converts notebooks in `inDirectory` to HTML and stores them in `outDirectory`.
:   `tf.tools.nbconvert`

``` sh
tf-xmlschema analysis {schema}.xsd
```
:   Analyses an XML *schema* file and extracts meaningful information for processing
    the XML that adheres to that schema.
:   `tf.tools.xmlschema`

``` sh
tf-fromxml
```
:   When run in a repo it finds an XML source and converts it to TF. 
    The resulting TF data is delivered in the repo.
    There is a hook to put your own conversion code in.
:   `tf.convert.xml`

``` sh
tf-fromtei
```
:   When run in a repo it finds a TEI source and converts it to TF. 
    The resulting TF data is delivered in the repo.
:   `tf.convert.tei`

``` sh
tf-addnlp
```
:   When run in the repo of a TF dataset, it adds NLP output to it
    after running Spacy to get them.
:   `tf.convert.addnlp`
