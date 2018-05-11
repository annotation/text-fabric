# Changes

???+ hint "Consult the tutorials after changes"
    When we change the API, we make sure that the tutorials shows off
    all possibilities:
    [bhsa](http://nbviewer.jupyter.org/github/etcbc/bhsa/blob/master/tutorial/start.ipynb)
    [cunei](http://nbviewer.jupyter.org/github/nino-cunei/tutorials/blob/master/start.ipynb)

## 4.0.3

2018-05-11

No changes, just quirks in the update process to get a new version of TF out.

## 4.0.1

2018-05-11

Documentation updates.

## 4.0.0

2018-05-11

*   Additions to Search.
    You can now include the values of edges in your search templates.
*   `F.`*feature*`.freqList()` accepts a new parameter: `nodeTypes`. It will restrict its results to nodes in
    one of the types in `nodeTypes`. 
*   You can now also do `E.`*feature*`.freqList()`.
    It will count the number of edges if the edge is declared to be without values, 
    or it will give a frequency list of the edges by value if the edge has values.
    Like `F.freqList`, you can pass parameters to constrain the frequency list to certain node types.
    You can constrain the node types from which the edges start (`nodeTypesFrom`) and where they arrive
    (`nodeTypesTo`).
*   New documentation system based on [mkdocs](https://mkdocs.readthedocs.io/en/stable/).

## 3.4.12

2018-05-02

The Cunei and Bhsa APIs show the version of Text-Fabric that is being called.

## 3.4.11

2018-05-01

Cunei

*   cases are divided horizontally and vertically, alternatingly with their
    nesting level;
*   cases have a feature **depth** now, indicating at which level of nesting they
    are.

## 3.4.8-9-10

2018-04-30

Various small fixes, such as:

*   Bhsa: Lexeme links in pretty displays.

*   Cunei: Prevented spurious `</div>` in nbviewer.

## 3.4.7

Cunei: Modified local image names

## 3.4.6

Small tweaks in search.

## 3.4.5

2018-04-28

Bhsa API:

*   new functions `plain()` and `table()` for plainly representing nodes, tuples
    and result lists, as opposed to the abundant representations by `pretty()` and
    `show()`.

## 3.4.4

2018-04-27

Cunei API:

*   new functions `plain()` and `table()` for plainly representing nodes, tuples
    and result lists, as opposed to the abundant representations by `pretty()` and
    `show()`.

## 3.4.2

2018-04-26

Better search documentation.

Cunei API: small fixes.

## 3.4.1

2018-04-25

Bhsa API:

*   Search/show: you can now show results condensed: i.e. a list of passages with
    highlighted results is returned. This is how SHEBANQ represents the results of
    a query. If you have two results in the same verse, with `condensed=True` you
    get one verse display with two highlights, with `condensed=False` you get two
    verse displays with one highlight each.

Cunei API:

*   Search/show: the `pretty`, `prettyTuple`, `show` functions of the Bhsa API
    have bee translated to the Cunei API. You can now get **very** pretty displays
    of search results.

## 3.4

2018-04-23

[Search](/Api#search):

*   You can use regular expressions to specifify feature values in queries.
*   You could already search for nodes which have a non-None value for a certain
    feature. Now you can also search for the complement: nodes that do not have a
    certain feature.

Bhsa API:

The display of query results also works with lexeme nodes.

## 3.3.4

2018-04-20

Cunei API: Better height and width control for images. Leaner captions.

## 3.3.3

2018-04-19

Cunei API: `casesByLevel()` returns case nodes in corpus order.

## 3.3.2

2018-04-18

Change in the cunei api reflecting that undivided lines have no cases now (was:
they had a single case with the same material as the line). Also: the feature
`fullNumber` on cases is now called `number`, and contains the full hierarchical
part leading to a case. There is an extra feature `terminal` on lines and cases
if they are not subdivided.

Changes in Cunei and Bhsa api:

*   fixed a bug that occurred when working outside a github repository.

## 3.3.1

2018-04-18

Change in the cunei api. `casesByLevel()` now takes an optional argument
`terminal` instead of `withChildren`, with opposite values.

`withChildren=False` is ambiguous: will it deliver only cases that have no
children (intended), or will it deliver cases and their children (understood,
but not intended).

`terminal=True`: delivers only cases that are terminal.

`terminal=False`: delivers all cases at that level.

## 3.3

2018-04-14

Small fix in the bhsa api.

Bumped the version number because of the inclusion of corpus specific APIs.

## 3.2.6

2018-04-14

*   Text-Fabric now contains corpus specific extras:
    *   `bhsa.py` for the Hebrew Bible (BHSA)
    *   `cunei.py` for the Proto-cuneiform corpus Uruk
*   The `Fabric(locations=locations, modules=modules)` constructor now uses `['']`
    as default value for modules. Now you can use the `locations` parameter on its
    own to specify the search paths for TF features, leaving the `modules`
    parameter undefined, if you wish.

## 3.2.5

2018-03-23

Enhancement in search templates: you can now test for the presence of features.
Till now, you could only test for one or more concrete values of features. So,
in addition to things like

    word number=plural tense=yiqtol

you can also say things like

    word number=plural tense

and it will give you words in the plural that have a tense.

## 3.2.4

2018-03-20

The short API names `F`, `T`, `L` etc. have been aliased to longer names:
`Feature`, `Text`, `Locality`, etc.

## 3.2.2

2018-02-27

Removed the sub module `cunei.py`. It is better to keep corpus dependent modules
in outside the TF package.

## 3.2.1

2018-02-26

Added a sub module `cunei.py`, which contains methods to produce ATF
transcriptions for nodes of certain types.

## 3.2

2018-02-19

**API change** Previously, the functions `L.d()` and `L.u()` took rank into
account. In the Hebrew Bible, that means that `L.d(sentence)` will not return a
verse, even if the verse is contained in the sentence.

This might be handy for sentences and verses, but in general this behaviour
causes problems. It also disturbs the expectiation that with these functions you
get *all* embedders and embeddees.

So we have lifted this restriction. Still, the results of the `L` functions have
an ordering that takes into account the levels of the returned nodes.

**Enhancement** Previously, Text-Fabric determined the levels of node types
automatically, based on the average slot-size of nodes within the node types. So
books get a lower level than chapters than verses than phrases, etc.

However, working with cuneiform tablets revealed that containing node types may
have a smaller average size than contained node types. This happens when a
container type only contains small instances of the contained type and not the
bigger ones.

Now you can override the computation by text-fabric by means of a key-value in
the *otext* feature. See the [api](/Api#levels-of-node-types).

## 3.1.5

2018-02-15

Fixed a small problem in `sectionFromNode(n)` when `n` is a node within a
primary section but outside secundary/tertiary sections.

## 3.1.4

2018-02-15

Small fix in the Text API. If your data set does not have language dependent
features, for section level 1 headings, such as `book@en`, `book@sw`, the Text
API will not break, and the plain `book` feature will be taken always.

We also reformatted all code with a pep8 code formatter.

## 3.1.3

2018-01-29

Small adaptions in conversion from MQL to TF, it can now also convert the MQL
coming from CALAP dataset (Syriac).

## 3.1.2

2018-01-27

Nothing changed, only the names of some variables and the text of some messages.
The terminology has been maed more consistent with the fabric metaphor, in
particular, *grid* has been replaced by *warp*.

## 3.1.1

2017-10-21

The `exportMQL()` function now generates one single enumeration type that serves
for all enum features. That makes it possible to compare values of different
enum features with each other, such as `ps` and `prs_ps`.

## 3.1

2017-10-20

The `exportMQL()` function now generates enumeration types for features, if
certain conditions are fulfilled. That makes it possible to query those features
with the `IN` relationship of MQL, like `[chapter book IN (Genesis, Exodus)]`.

## 3.0.8

2017-10-07

When reading edges with values, also the edges without a value are taken in.

## 3.0.7

2017-10-07

Edges with edge values did not allow for the absence of values. Now they do.

## 3.0.6

2017-10-05

A major tweak in the [importMQL()](/Api#mql-import) function so that it can
handle gaps in the monad sequence. The issue arose when converting MQL for
version 3 of the [BHSA](https://github.com/ETCBC/bhsa). In that version there
are somewhat arbitrary gaps in the monad sequence between the books of the
Hebrew Bible. I transform a gapped sequence of monads into a continuous sequence
of slots.

## 3.0.5

2017-10-05

Another little tweak in the [importMQL()](/Api#mql-import) function so that it
can handle more patterns in the MQL dump file. The issue arose when converting
MQL for version 3 of the [BHSA](https://github.com/ETCBC/bhsa).

## 3.0.4

2017-10-04

Little tweak in the [importMQL()](/Api#mql-import) function so that it can handle
more patterns in the MQL dump file. The issue arose when converting MQL for
[extrabiblical](https://github.com/ETCBC/extrabiblical) material.

## 3.0.2, 3.0.3

2017-10-03

No changes, only an update of the package metadata, to reflect that Text-Fabric
has moved from [ETCBC](https://github.com/ETCBC) to
[Dans-labs](https://github.com/Dans-labs).

## 3.0.1

2017-10-02

Bug fix in reading edge features with values.

## 3.0.0

2017-10-02

MQL! You can now convert MQL data into a TF dataset:
[importMQL()](/Api#mql-import). We had already [exportMQL()](/Api#mql-export).

The consequence is that we can operate with much agility between the worlds of
MQL and TF.

We can start with source data in MQL, convert it to TF, combine it with other TF
data sources, compute additional stuff and add it, and then finally export it as
enriched MQL, so that the enriched data can be queried by MQL.

## 2.3.15

2017-09-29

Completion: TF defines the concept of
[edges](/Api/General/#edge-features) that
carry a value. But so far we have not used them. It turned out that it was
impossible to let TF know that an edge carries values, when
[saving](/Api/General/#saving-features) data
as a new feature. Now it is possible.

## 2.3.14

2017-09-29

Bug fix: it was not possible to get
`T.nodeFromSection(('2_Chronicles', 36, 23))`, the last verse in the Bible.

This is the consequence of a bug in precomputing the sections
[sections](/Api/General/#computed-data). The
preparation step used

```python
range(firstVerse, lastVerse)
```

somewhere, which should of course have been

```python
range(firstVerse, lastVerse + 1)
```

## 2.3.13

2017-09-28

Loading TF was not completely silent if `silent=True` was passed. Better now.

## 2.3.12

2017-09-18

*   Small fix in
    [TF.save()](/Api/General/#saving-features).
    The spec says that the metadata under the empty key will be inserted into all
    features, but in fact this did not happen. Instead it was used as a default
    when some feature did not have metadata specified.

    From now on, that metadata will spread through all features.

*   New API function [explore](/Api/General#loading), to get a list of all known
    features in a dataset.

## 2.3.11

2017-09-18

*   Small fix in Search: the implementation of the relation operator `||`
    (disjoint slot sets) was faulty. Repaired.
*   The
    [search tutorial](/Dans-labs/text-fabric/blob/master/docs/searchTutorial.ipynb)
    got an extra example: how to look for gaps. Gaps are not a primitive in the TF
    search language. Yet the language turns out to be powerful enough to look for
    gaps. This answers a question by Cody Kingham.

## 2.3.10

2017-08-24

When defining text formats in the `otext.tf` feature, you can now include
newlines and tabs in the formats. Enter them as `\n` and `\t`.

## 2.3.9

2017-07-24

TF has a list of default locations to look for data sources: `~/Downloads`,
`~/github`, etc. Now `~/Dropbox` has been added to that list.

## 2.3.8

2017-07-24

The section levels (book, chapter, verse) were supposed to be customizable
through the [otext](Data-Model#otext-config-feature-optional) feature. But in
fact, up till version 2.3.7 this did not work. From now on the names of the
section types and the features that name/number them, are given in the `otext`
feature. It is still the case that exactly three levels must be specified,
otherwise it does not work.

## 2.3.7

2017-05-12

Fixes. Added an extra default location for looking for text-fabric-data sources,
for the benefit of running text-fabric within a shared notebook service.

## 2.3.5, 2.3.6

2017-03-01

Bug fix in Search. Spotted by Cody Kingham. Relational operators between atoms
in the template got discarded after an outdent.

## 2.3.4

2017-02-12

Also the `Fabric()` call can be made silent now.

## 2.3.3

2017-02-11

Improvements:

*   you can load features more silently. See [`TF.load()`](/Api#loading-features);
*   you can search more silently. See [`S.study()`](/Api#prepare-for-search);
*   you can search more concisely. See the new [`S.search()`](/Api#search-command);
*   when fetching results, the `amount` parameter of
    [`S.fetch()`](/Api#getting-results) has been renamed to `limit`;
*   the tutorial notebooks (see links on top) have been updated.

## 2.3.2

2017-02-03

Bug fix: the results of `F.feature.s()`, `E.feature.f()`, and `E.features.t()`
are now all tuples. They were a mixture of tuples and lists.

## 2.3.1

2017-01-23

Bug fix: when searching simple queries with only one query node, the result
nodes were delivered as integers, instead of 1-tuples of integers.

## 2.3

2017-01-13

We start archiving releases of Text-Fabric at [Zenodo](https://zenodo.org).

## 2.2.1

2017-01-09

Small fixes.

## 2.2.0

2017-01-06

### New: sortKey

The API has a new member: [`sortKey`](/Api#sorting-nodes)

New relationships in templates: [`nearness`](/Api#nearness-comparison). See for
examples the end of the
[searchTutorial](/Dans-labs/text-fabric/blob/master/docs/searchTutorial.ipynb).
Thanks to James Cuénod for requesting nearness operators.

### Fixes

*   in `S.glean()` word nodes were not printed;
*   the check whether the search graph consists of a single connected component
    did not handle the case of one node without edges well;

## 2.1.3

2017-01-04

Various fixes.

## 2.1.0

2017-01-04

### New: relations

Some relations have been added to search templates:

*   `=:` and `:=` and `::`: *start at same slot*, *end at same slot*, *start at
    same slot and end at same slot*
*   `<:` and `:>`: *adjacent before* and *adjacent next*.

The latter two can also be used through the `L`-api: `L.p()` and `L.n()`.

The data that feeds them is precomputed and available as `C.boundary`.

### New: enhanced search templates

You can now easily make extra constraints in search templates without naming
atoms.

See the
[searchTutorial](/Dans-labs/text-fabric/blob/master/docs/searchTutorial.ipynb)
for an updated exposition on searching.

## 2.0.0

2016-12-23

### New: Search

![warmXmas](/images/warmXmas.jpg)

*Want to feel cosy with Christmas? Put your laptop on your lap, update
Text-Fabric, and start playing with search. Your laptop will spin itself warm
with your queries!*

Text-Fabric just got a powerful search facility, based on (graph)-templates.

It is still very fresh, and more experimentation will be needed. Feedback is
welcome.

Start with the
[tutorial](/Dans-labs/text-fabric/blob/master/docs/searchTutorial.ipynb).

The implementation of this search engine can be nicely explained with a textile
metaphor: spinning wool into yarn and then stitching the yarns together.

That will be explained further in a document that I'll love to write during
Xmas.

## 1.2.7

2016-12-14

### New

[`F.otype.sInterval()`](/Api#warp-feature-otype)

## 1.2.6

2016-12-14

### bug fix

There was an error in computing the order of nodes. One of the consequences was
that objects that occupy the same slots were not ordered properly. And that had
as consequence that you could not go up from words in one-word phrases to their
containing phrase.

It has been remedied.

??? note
    Your computed data needs to be refreshed. This can be done by calling a new
    function [`TF.clearCache()`](/Api#clearing-the-cache). When you use TF after
    this, you will see it working quite hard to recompute a bunch of data.

## 1.2.5

2016-12-13

Documentation update

## 1.2.0

2016-12-08

??? note
    Data update needed

### New

### Frequency lists ###

[`F.feature.freqList()`](/Api#node-features): get a sorted frequency list for any
feature. Handy as a first step in exploring a feature.

### Export to MQL ###

[`TF.exportMQL()`](/Api#export-to-mql): export a whole dataset as a MQL database.
Including all modules that you have loaded with it.

### Changed

The slot numbers start at 0, no longer at 1. Personally I prefer the zero
starting point, but Emdros insists on positive monads and objects ids. Most
important is that users do not have to add/subtract one from the numbers they
see in TF if they want to use it in MQL and vice versa.

Because of this you need to update your data too:

```sh
    cd ~/github/text-fabric-data
    git pull origin master
```
