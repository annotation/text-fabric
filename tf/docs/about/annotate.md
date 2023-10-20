# Manual Annotation

Named Entity Recognition is a task for which automated tools exist.
But in a smallish, well-known corpus, such tools tend to created more noise than signal.
If you know which names to expect and in what forms they occur in the corpus,
it might be easier to mark them by hand.

Text-Fabric contains a tool to help you with that. The basic thing it does is
to find all occurrences of a pattern you specifiy, and then assign an identifier and
a kind to all those occurrences.

For example, it finds all `Ernesto di Nassau` occurrences and it assigns
identiy `ernesto.di.nassau` and kind `PER` to them.

There are two interfaces. One runs inside the Text-Fabric browser, and it
enables you to search and mark repeatedly, to apply additions and
deletions of named entities to restricted sets of occurrences, so that you can
make individual exceptions to the rules.

The other is an API, that you can call, typically from inside a Jupyter notebook,
by which you can automate things to the next level.
You can prepare a spreadsheet with entities and surface forms and have the tool
*execute* that spreadsheet against the corpus.

Here is what the browser interface looks like:

![browser](../images/Annotate/browser.png)

For the API: start here: `tf.browser.ner.annotate`.

# Concepts

## Entities

An *entity* is a thing in the real world that is referenced by specific pieces of
text in the corpus. Think of persons, places, organizations. 

We mark up those text occurrences by creating nodes for those locations in the corpus
and assigning feature values to the features `eid` (entity identifier) and `kind`
(entity kind such as `PER`, `LOC`, `ORG`).

## How entities exist in a corpus

Your corpus may already have entities, marked up by an automatic tool such as
Spacy (see `tf.tools.myspacy`). In that case there is already a node type
`ent` and features `eid` and `kind`.

When you make manual annotations, the annotations are saved as `.tsv` files.
In order to create nodes for them in your corpus, you can use those `.tsv` files,
read off the feature information, and invoke `tf.dataset.modify` function to
generate new nodes and add them to your corpus.

In a next iteration, we'll include a function that will do this for you.

## Occurrences and identifiers

Entity nodes mark the text occurrences that refer to outside entities in the world.
Different occurrences have different entity nodes, but they may refer to the same
entity in the world. It is the entity identifier that unifies the various occurrences
that refer to the same entity in the world.
We do not have nodes in the corpus that correspond 1-1 to the real world entities.
The entity nodes correspond to the occurrences.

The same occurrence may have multiple entity nodes.
For example, if an occurrence `Amsterdam` refers to a location, a city council,
and a ship at the same time, you might mark it up as

* `('amsterdam', 'LOC')`
* `('amsterdam', 'ORG')`
* `('amsterdam', 'SHIP')`

In fact, an entity in the real word is not solely identified by the `eid` feature,
but by the *combination* of the `eid` and `kind` features.

Of course, you are free to make the identifiers distinct if the same name refers
to entities of different kinds.

# Organization and configuration



