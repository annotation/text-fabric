# Text-Fabric API

## Advanced API

### Initialisation, configuration, meta data, and linking

```A = use('corpus', hoist=globals())```
:   start up
:   `tf.app.use`

```A.reuse()```
:   reload config data
:   `tf.applib.app.App.reuse`

```A.showContext(...)```
:   show app settings
:   `tf.applib.settings.showContext`

```A.header()```
:   show colofon
:   `tf.applib.links.header`

```A.showProvenance(...)```
:   show provenance of code and data
:   `tf.applib.links.showProvenance`

```A.webLink(n, ...)```
:   hyperlink to node n on the web
:   `tf.applib.links.webLink`


### Displaying

```method(option1=value1, option2=value2, ...)```
:   Many of the following methods accept these options as keyword arguments: 
:   `tf.applib.displaysettings`

```A.displaySetup(...)```
:   set up display options
:   `tf.applib.display.displaySetup`

```A.displayReset(...)```
:   resetdisplay options
:   `tf.applib.display.displayReset`

```A.table(results, ...)```
:   plain rendering of tuple of tuples of node
:   `tf.applib.display.table`

```A.plainTuple(tup, ith, ...)```
:   plain rendering of tuple of node
:   `tf.applib.display.plainTuple`

```A.plain(node, ...)```
:   plain rendering of node
:   `tf.applib.display.plain`

```A.show(results, ...)```
:   pretty rendering of tuple of tuples of node
:   `tf.applib.display.show`

```A.prettyTuple(tup, ith, ...)```
:   pretty rendering of tuple of node
:   `tf.applib.display.prettyTuple`

```A.pretty(node, ...)```
:   pretty rendering of node
:   `tf.applib.display.pretty`


### Exporting

```A.export(results, ...)```
:   export formatted data
:   `tf.applib.display.export`


### Searching

```A.search(...)```
:   search, collect and deliver results, report number of results
:   `tf.applib.search.search`


### Sections and Structure

```A.nodeFromSectionStr(...)```
:   lookup node for sectionheading
:   `tf.applib.sections.nodeFromSectionStr`

```A.sectionStrFromNode(...)```
:   lookup section heading for node
:   `tf.applib.sections.sectionStrFromNode`

```A.structureStrFromNode(...)```
:   lookup structure heading for node
:   `tf.applib.sections.structureStrFromNode`


## Core API

### Nodes

```N()```
:   generator of all nodes in canonical ordering
:   `tf.core.api.Api.N`

```sortNodes(nodes)```
:   sorts `nodes` in the canonical ordering
:   `tf.core.api.Api.sortNodes`

```otypeRank[nodeType]```
:   ranking position of `nodeType`
:   `tf.core.api.Api.otypeRank`

```sortKey(node)```
:   defines the canonical ordering on nodes
:   `tf.core.api.Api.sortKey`

```sortKeyTuple(tup)```
:   extends the canonical ordering on nodes to tuples of nodes
:   `tf.core.api.Api.sortKeyTuple`

### Features

#### Node features

```Fall()```
:   all loaded feature names (node features only)
:   `tf.core.api.Api.Fall`

```F.fff.v(node)```
:   get value of node feature `fff`
:   `tf.core.api.NodeFeature.v`

```F.fff.s(value)```
:   get nodes where feature `fff` has `value`
:   `tf.core.api.NodeFeature.s`

```F.fff.freqList(...)```
:   frequency list of values of `fff
:   `tf.core.api.NodeFeature.freqList`

```F.fff.items(...)```
:   generator of all entries of `fff` as mapping from nodes to values
:   `tf.core.api.NodeFeature.freqList`

```F.fff.meta```
:   meta data of feature `fff`
:   `tf.core.api.NodeFeature.meta`

```Fs('fff')```
:   identical to ```F.ffff``` usable if name of feature is variable
:   `tf.core.api.NodeFeature`

#### Special feature `otype`

Maps nodes to their types.

```F.otype.v(node)```
:   get type of `node`
:   `tf.core.api.OtypeFeature.v`

```F.otype.s(nodeType)```
:   get all nodes of type `nodeType`
:   `tf.core.api.OtypeFeature.s`

```F.otype.sInterval(nodeType)```
:   gives start and ending nodes of `nodeType`
:   `tf.core.api.OtypeFeature.s`

```F.otype.items(...)```
:   generator of all (node, type) pairs.
:   `tf.core.api.OtypeFeature.items`

```F.otype.meta```
:   meta data of feature `otype`
:   `tf.core.api.OtypeFeature.meta`

```F.otype.maxSlot```
:   the last slot node
:   `tf.core.api.OtypeFeature.maxSlot`

```F.otype.maxNode```
:   the last node
:   `tf.core.api.OtypeFeature.maxNode`

```F.otype.slotType```
:   the slot type
:   `tf.core.api.OtypeFeature.slotType`

```F.otype.all```
:   sorted list of all node types
:   `tf.core.api.OtypeFeature.all`

#### Edge features

```Eall()```
:   all loaded feature names (edge features only)
:   `tf.core.api.Api.Eall`

```E.fff.f(node)```
:   get value of feature `fff` for edges *from* node
:   `tf.core.api.EdgeFeature.f`

```E.fff.t(node)```
:   get value of feature `fff` for edges *to* node
:   `tf.core.api.EdgeFeature.t`

```E.fff.freqList(...)```
:   frequency list of values of `fff
:   `tf.core.api.EdgeFeature.freqList`

```E.fff.items(...)```
:   generator of all entries of `fff` as mapping from edges to values
:   `tf.core.api.EdgeFeature.items`

```E.fff.b(node)```
:   get value of feature `fff` for edges *from* and *to* node
:   `tf.core.api.EdgeFeature.t`

```E.fff.meta```
:   all meta data of feature `fff`
:   `tf.core.api.EdgeFeature.meta`

```Es('fff')```
:   identical to ```E.fff``` usable if name of feature is variable
:   `tf.core.api.EdgeFeature`

#### Special feature `oslots`

Maps nodes to the set of slots they occupy.

```E.oslots.items(...)```
:   generator of all entries of `oslots` as mapping from nodes to sets of slots
:   `tf.core.api.OslotsFeature.items`

```E.oslots.s(node)```
:   set of slots linked to `node`
:   `tf.core.api.OslotsFeature.s`

```E.oslots.meta```
:   all meta data of feature `oslots`
:   `tf.core.api.OslotsFeature.meta`

