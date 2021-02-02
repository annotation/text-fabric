# `A.` Advanced API

## Initialisation, configuration, meta data, and linking

```
A = use('corpus', hoist=globals())
```
:   start up
:   `tf.app.use`

```
A.showContext(...)
```
:   show app settings
:   `tf.advanced.settings.showContext`

```
A.header()
```
:   show colofon
:   `tf.advanced.links.header`

```
A.showProvenance(...)
```
:   show provenance of code and data
:   `tf.advanced.links.showProvenance`

```
A.webLink(n, ...)
```
:   hyperlink to node n on the web
:   `tf.advanced.links.webLink`

---

## Displaying

```
A.dm(markdownString)
```
:   display markdown string in notebook
:   `tf.advanced.helpers.dm`

```
A.dh(htmlString)
```
:   display HTML string in notebook
:   `tf.advanced.helpers.dh`

```
A.method(option1=value1, option2=value2, ...)
```
:   Many of the following methods accept these options as keyword arguments: 
:   `tf.advanced.options`

```
A.displayShow(...)
```
:   show display options
:   `tf.advanced.display.displayShow`

```
A.displayReset(...)
```
:   resetdisplay options
:   `tf.advanced.display.displayReset`

```
A.displaySetup(...)
```
:   set up display options
:   `tf.advanced.display.displaySetup`

```
A.displayReset(...)
```
:   resetdisplay options
:   `tf.advanced.display.displayReset`

```
A.table(results, ...)
```
:   plain rendering of tuple of tuples of node
:   `tf.advanced.display.table`

```
A.plainTuple(tup, ith, ...)
```
:   plain rendering of tuple of node
:   `tf.advanced.display.plainTuple`

```
A.plain(node, ...)
```
:   plain rendering of node
:   `tf.advanced.display.plain`

```
A.show(results, ...)
```
:   pretty rendering of tuple of tuples of node
:   `tf.advanced.display.show`

```
A.prettyTuple(tup, ith, ...)
```
:   pretty rendering of tuple of node
:   `tf.advanced.display.prettyTuple`

```
A.pretty(node, ...)
```
:   pretty rendering of node
:   `tf.advanced.display.pretty`

```
A.unravel(node, ...)
```
:   convert a graph to a tree
:   `tf.advanced.unravel.unravel`

---

## Search (high level)

```
A.search(...)
```
:   search, collect and deliver results, report number of results
:   `tf.advanced.search.search`

---

## Sections and Structure

```
A.nodeFromSectionStr(...)
```
:   lookup node for sectionheading
:   `tf.advanced.sections.nodeFromSectionStr`

```
A.sectionStrFromNode(...)
```
:   lookup section heading for node
:   `tf.advanced.sections.sectionStrFromNode`

```
A.structureStrFromNode(...)
```
:   lookup structure heading for node
:   `tf.advanced.sections.structureStrFromNode`

---

## Export to Excel

```
A.export(results, ...)
```
:   export formatted data
:   `tf.advanced.display.export`

---

# Logging

```
A.dm(markdownString)
```
:   display markdown string in notebook
:   `tf.advanced.helpers.dm`

```
A.dh(htmlString)
```
:   display HTML string in notebook
:   `tf.advanced.helpers.dh`

```
A.version
```
:   version number of data of the corpus.
:   `tf.fabric.Fabric.version`

The following methods work also for `TF.` instead of `A.`:

```
A.banner
```
:   banner of the Text-Fabric program.
:   `tf.fabric.Fabric.banner`

```
A.isSilent()
```
:   report the verbosity of Text-Fabric
:   `tf.core.timestamp.Timestamp.isSilent`

```
A.silentOn(deep=False)
```
:   make TF silent from now on.
:   `tf.core.timestamp.Timestamp.silentOn`

```
A.silentOff()
```
:   make TF talkative from now on.
:   `tf.core.timestamp.Timestamp.silentOff`

```
A.setSilent(silent)
```
:   set the verbosity of Text-Fabric.
:   `tf.core.timestamp.Timestamp.setSilent`

```
A.indent(level=None, reset=False)
```
:   Sets up indentation and timing of following messages
:   `tf.core.timestamp.Timestamp.indent`

```
A.info(msg, tm=True, nl=True, ...)
```
:   informational message
:   `tf.core.timestamp.Timestamp.info`

```
A.warning(msg, tm=True, nl=True, ...)
```
:   warning message
:   `tf.core.timestamp.Timestamp.warning`

```
A.error(msg, tm=True, nl=True, ...)
```
:   error message
:   `tf.core.timestamp.Timestamp.error`

---

# `N. F. E. L. T. S. C.` Core API

## `N.` Nodes

Read about the canonical ordering here: `tf.core.nodes`.

```
N.walk()
```
:   generator of all nodes in canonical ordering
:   `tf.core.nodes.Nodes.walk`

```
N.sortNodes(nodes)
```
:   sorts `nodes` in the canonical ordering
:   `tf.core.nodes.Nodes.sortNodes`

```
N.otypeRank[nodeType]
```
:   ranking position of `nodeType`
:   `tf.core.nodes.Nodes.otypeRank`

```
N.sortKey(node)
```
:   defines the canonical ordering on nodes
:   `tf.core.nodes.Nodes.sortKey`

```
N.sortKeyTuple(tup)
```
:   extends the canonical ordering on nodes to tuples of nodes
:   `tf.core.nodes.Nodes.sortKeyTuple`

```
N.sortKeyChunk(node)
```
:   defines the canonical ordering on node chunks
:   `tf.core.nodes.Nodes.sortKeyChunk`

---

## `F.` Node features

```
Fall()
```
:   all loaded feature names (node features only)
:   `tf.core.api.Api.Fall`

```
F.fff.v(node)
```
:   get value of node feature `fff`
:   `tf.core.nodefeature.NodeFeature.v`

```
F.fff.s(value)
```
:   get nodes where feature `fff` has `value`
:   `tf.core.nodefeature.NodeFeature.s`

```
F.fff.freqList(...)
```
:   frequency list of values of `fff`
:   `tf.core.nodefeature.NodeFeature.freqList`

```
F.fff.items(...)
```
:   generator of all entries of `fff` as mapping from nodes to values
:   `tf.core.nodefeature.NodeFeature.items`

```
F.fff.meta
```
:   meta data of feature `fff`
:   `tf.core.nodefeature.NodeFeature.meta`

```
Fs('fff')
```
:   identical to `F.ffff`, usable if name of feature is variable
:   `tf.core.api.Api.Fs`

---

## Special node feature `otype`

Maps nodes to their types.

```
F.otype.v(node)
```
:   get type of `node`
:   `tf.core.otypefeature.OtypeFeature.v`

```
F.otype.s(nodeType)
```
:   get all nodes of type `nodeType`
:   `tf.core.otypefeature.OtypeFeature.s`

```
F.otype.sInterval(nodeType)
```
:   gives start and ending nodes of `nodeType`
:   `tf.core.otypefeature.OtypeFeature.sInterval`

```
F.otype.items(...)
```
:   generator of all (node, type) pairs.
:   `tf.core.otypefeature.OtypeFeature.items`

```
F.otype.meta
```
:   meta data of feature `otype`
:   `tf.core.otypefeature.OtypeFeature.meta`

```
F.otype.maxSlot
```
:   the last slot node
:   `tf.core.otypefeature.OtypeFeature.maxSlot`

```
F.otype.maxNode
```
:   the last node
:   `tf.core.otypefeature.OtypeFeature.maxNode`

```
F.otype.slotType
```
:   the slot type
:   `tf.core.otypefeature.OtypeFeature.slotType`

```
F.otype.all
```
:   sorted list of all node types
:   `tf.core.otypefeature.OtypeFeature.all`

---

## `E.` Edge features

```
Eall()
```
:   all loaded feature names (edge features only)
:   `tf.core.api.Api.Eall`

```
E.fff.f(node)
```
:   get value of feature `fff` for edges *from* node
:   `tf.core.edgefeature.EdgeFeature.f`

```
E.fff.t(node)
```
:   get value of feature `fff` for edges *to* node
:   `tf.core.edgefeature.EdgeFeature.t`

```
E.fff.freqList(...)
```
:   frequency list of values of `fff`
:   `tf.core.edgefeature.EdgeFeature.freqList`

```
E.fff.items(...)
```
:   generator of all entries of `fff` as mapping from edges to values
:   `tf.core.edgefeature.EdgeFeature.items`

```
E.fff.b(node)
```
:   get value of feature `fff` for edges *from* and *to* node
:   `tf.core.edgefeature.EdgeFeature.b`

```
E.fff.meta
```
:   all meta data of feature `fff`
:   `tf.core.edgefeature.EdgeFeature.meta`

```
Es('fff')
```
:   identical to `E.fff`, usable if name of feature is variable
:   `tf.core.api.Api.Es`

---

## Special edge feature `oslots`

Maps nodes to the set of slots they occupy.

```
E.oslots.items(...)
```
:   generator of all entries of `oslots` as mapping from nodes to sets of slots
:   `tf.core.oslotsfeature.OslotsFeature.items`

```
E.oslots.s(node)
```
:   set of slots linked to `node`
:   `tf.core.oslotsfeature.OslotsFeature.s`

```
E.oslots.meta
```
:   all meta data of feature `oslots`
:   `tf.core.oslotsfeature.OslotsFeature.meta`

---

## `L.` Locality

```
L.i(node, otype=...)
```
:   go to intersecting nodes
:   `tf.core.locality.Locality.i`

```
L.u(node, otype=...)
```
:   go one level up
:   `tf.core.locality.Locality.u`

```
L.d(node, otype=...)
```
:   go one level down
:   `tf.core.locality.Locality.d`

```
L.p(node, otype=...)
```
:   go to adjacent previous nodes
:   `tf.core.locality.Locality.p`

```
L.n(node, otype=...)
```
:   go to adjacent next nodes
:   `tf.core.locality.Locality.n`

---

## `T.` Text

```
T.text(node, fmt=..., ...)
```
:   give formatted text associated with node
:   `tf.core.text.Text.text`

---

## 
Secti
ons

Rigid 1 or 2 or 3 sectioning system

```
T.sectionTuple(node)
```
:   give tuple of section nodes that contain node
:   `tf.core.text.Text.sectionTuple`

```
T.sectionFromNode(node)
```
:   give section heading of node
:   `tf.core.text.Text.sectionFromNode`

```
T.nodeFromSection(section)
```
:   give node for section heading
:   `tf.core.text.Text.nodeFromSection`

---

## Structure

Flexible multilevel sectioning system

```
T.headingFromNode(node)
```
:   give structure heading of node
:   `tf.core.text.Text.headingFromNode`

```
T.nodeFromHeading(heading)
```
:   give node for structure heading
:   `tf.core.text.Text.nodeFromHeading`

```
T.structureInfo()
```
:   give summary of dataset structure
:   `tf.core.text.Text.structureInfo`

```
T.structure(node)
```
:   give structure of `node` and all in it.
:   `tf.core.text.Text.structure`

```
T.structurePretty(node)
```
:   pretty print structure of `node` and all in it.
:   `tf.core.text.Text.structurePretty`

```
T.top()
```
:   give all top-level structural nodes in the dataset
:   `tf.core.text.Text.top`

```
T.up(node)
```
:   gives parent of structural node
:   `tf.core.text.Text.up`

```
T.down(node)
```
:   gives children of structural node
:   `tf.core.text.Text.down`

---

## `S.` Search (low level)

[searchRough](https://nbviewer.jupyter.org/github/annotation/tutorials/blob/master/bhsa/searchRough.ipynb)

### Preparation

```
S.search(query, limit=None)
```
:   Query the TF dataset with a template
:   `tf.search.search.Search.search`

```
S.study(query, ...)
```
:   Study the query in order to set up a plan
:   `tf.search.search.Search.study`

```
S.showPlan(details=False)
```
:   Show the search plan resulting from the last study.
:   `tf.search.search.Search.showPlan`

```
S.relationsLegend()
```
:   Catalog of all relational devices in search templates
:   `tf.search.search.Search.relationsLegend`

---

### Fetching results

```
S.count(progress=None, limit=None)
```
:   Count the results, up to a limit
:   `tf.search.search.Search.count`

```
S.fetch(limit=None, ...)
```
:   Fetches the results, up to a limit
:   `tf.search.search.Search.fetch`

```
S.glean(tup)
```
:   Renders a single result into something human readable.
:   `tf.search.search.Search.glean`

---

### Implementation

```
S.tweakPerformance(...)
```
:   Set certain parameters that influence the performance of search.
:   `tf.search.search.Search.tweakPerformance`

---

## `C.` Computed data components.

Access to precomputed data: `tf.core.computed.Computeds`.

All components have just one useful attribute: `.data`.

```
Call()
```
:   all precomputed data component names
:   `tf.core.api.Api.Call`

```
Cs('ccc')
```
:   identical to `C.ccc`, usable if name of component is variable
:   `tf.core.api.Api.Cs`

```
C.levels.data
```
:   various statistics on node types
:   `tf.core.prepare.levels`

```
C.order.data
```
:   the canonical order of the nodes (`tf.core.nodes`)
:   `tf.core.prepare.order`

```
C.rank.data
```
:   the rank of the nodes in the canonical order (`tf.core.nodes`)
:   `tf.core.prepare.rank`

```
C.levUp.data
```
:   feeds the `tf.core.locality.Locality.u` function
:   `tf.core.prepare.levUp`

```
C.levDown.data
```
:   feeds the `tf.core.locality.Locality.d` function
:   `tf.core.prepare.levDown`

```
C.boundary.data
```
:   feeds the `tf.core.locality.Locality.p` and `tf.core.locality.Locality.n`
    functions
:   `tf.core.prepare.boundary`

```
C.sections.data
```
:   feeds the section part of `tf.core.text`
:   `tf.core.prepare.sections`

```
C.structure.data
```
:   feeds the structure part of `tf.core.text`
:   `tf.core.prepare.structure`

---

# `TF.` Dataset

## Loading

```
TF = Fabric(locations=directories, modules=subdirectories, silent=False)
```
:   Initialize API on dataset from explicit directories.
    Use `tf.app.use` instead wherever you can.
:   `tf.fabric.Fabric`

```
TF.explore(show=True)
```
:   Get features by category, loaded or unloaded
:   `tf.fabric.Fabric.explore`

```
TF.loadAll(silent=None)
```
:   Load all loadable features. 
:   `tf.fabric.Fabric.loadAll`

```
TF.load(features, add=False)
```
:   Load a bunch of features from scratch or additionally. 
:   `tf.fabric.Fabric.load`

```
TF.ensureLoaded(features)
```
:   Make sure that features are loaded.
:   `tf.core.api.Api.ensureLoaded`

```
TF.makeAvailableIn(globals())
```
:   Make the members of the core API available in the global scope
:   `tf.core.api.Api.makeAvailableIn`

```
TF.ignored
```
:   Which features have been overridden.
:   `tf.core.api.Api.ignored`

```
TF.loadLog()
```
:   Log of the feature loading process
:   `tf.core.timestamp.Timestamp.cache`

---

## Saving

```
TF.save(nodeFeatures={}, edgeFeatures={}, metaData={},,...)
```
:   Save a bunch of newly generated features to disk.
:   `tf.fabric.Fabric.save`

---

## House keeping

```
TF.version
```
:   version number of Text-Fabric.
:   `tf.fabric.Fabric.version`

```
TF.clearCache()
```
:   clears the cache of compiled TF data
:   `tf.fabric.Fabric.clearCache`

```
from tf.clean import clean
```

```
clean()
```
:   clears the cache of compiled TF data
:   `tf.clean`

---

# Dataset Operations

```
from tf.compose import combine, modify
```

```
combine((source1, source2, ...), target)
```
:   Combines several TF datasets into one new TF dataset
:   `tf.compose.combine`

```
modify(source, target, ...)
```
:   Modifies a TF datasets into one new TF dataset
:   `tf.compose.modify`

```
Versions(api, va, vb, slotMap)
```
:   Extends a slot mapping between versions of a TF dataset
    to a complete node mapping
:   `tf.compose.nodemaps`

---

# Data Interchange

## Custom node sets for search

```
from tf.lib import readSets
from tf.lib import writeSets
```

```
readSets(sourceFile)
```
:   reads a named sets from file
:   `tf.lib.readSets`

```
writeSets(sets, destFile)
```
:   writes a named sets to file
:   `tf.lib.writeSets`

---

## Export to Excel

```
A.export(results, ...)
```
:   export formatted data
:   `tf.advanced.display.export`

---

## BRAT

```
from convert.recorder import Recorder
```

```
Recorder()
```
:   generate annotatable plain text and import annotations
:   `tf.convert.recorder`

---

## MQL interchange

```
TF.exportMQL()
```
:   export loaded dataset to MQL
: `tf.fabric.Fabric.exportMQL`

```
TF.importMQL()
```
:   convert MQL file to TF dataset
:   `tf.fabric.Fabric.importMQL`

---

## Walker conversion

```
from tf.convert.walker import CV
```

```
cv = CV(TF)
```
:   convert structured data to TF dataset
:   `tf.convert.walker`

---

## Exploding

```
from tf.convert.tf import explode
```

```
explode(inLocation, outLocation
```
:   explode TF feature files to straight data files without optimizations
:   `tf.convert.tf.explode`

---

# TF-App development

```
A.reuse()
```
:   reload config data
:   `tf.advanced.app.App.reuse`

```
from tf.advanced.find import loadModule
```

```
mmm = loadModule("mmm", *args)
```
:   load supporting TF-app specific module
:   `tf.advanced.find.loadModule`

```
~/mypath/app-myname/code/config.yaml
```
:   settings for a TF-App
:   `tf.advanced.settings`
    e.g. [app-default](https://github.com/annotation/app-default/blob/master/code/config.yaml)

