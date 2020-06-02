# Walker

You can convert a dataset to TF by writing a function that walks through it.

That function must trigger a sequence of actions when reading the data.
These actions drive Text-Fabric to build a valid Text-Fabric dataset.
Many checks will be performed.

!!! hint "to and from MQL"
    If your source is MQL, you are even better off: Text-Fabric has a
    module to import from MQL and to export to MQL.
    See `tf.fabric.Fabric.importMQL` and `tf.fabric.Fabric.exportMQL`.

## Set up

Here is a schematic set up of such a conversion program.

```python
from tf.fabric import Fabric
from tf.convert.walker import CV

TF = Fabric(locations=OUT_DIR)
cv = CV(TF)

def director(cv):
  # your code to unwrap your source data and trigger 
  # the generation of TF nodes, edges and features

slotType = 'word'  # or whatever you choose
otext = {  # dictionary of config data for sections and text formats
    ...
}
generic = {  # dictionary of metadata meant for all features
    ...
}
intFeatures = {  # set of integer valued feature names
    ...
}
featureMeta = {  # per feature dicts with metadata
   ...
}

good = cv.walk(
    director,
    slotType,
    otext=otext,
    generic=generic,
    intFeatures=intFeatures,
    featureMeta=featureMeta,
    warn=True,
    force=False,
    silent=False,
)

if good:
  ... load the new TF data ...
```

See `tf.convert.walker.CV.walk`.

## Walking

When you walk through the input data source, you'll encounter things
that have to become slots, non-slot nodes, edges and features in the new data set.

You issue these things by means of an *action method* from `cv`, such as
`cv.slot()` or `cv.node(nodeType)`.

When your action creates slots or non slot nodes,
Text-Fabric will return you a reference to that node,
that you can use later for more actions related to that node.

```python
curPara = cv.node('para')
```

To add features to nodes, use a `cv.feature()` action.
It will apply to the last node added, or you can pass it a node as argument.

To add features to edges, issue a `cv.edge()` action.
It will require two node arguments: the *from* node and the *to* node.
    
There is always a set of current *embedder nodes*.
When you create a slot node

```python
curWord = cv.slot()
```

then TF will link all current embedder nodes to the resulting slot.

There are actions to add nodes to the set of embedder nodes,
to remove them from it,
and to add them again. 

## Dynamic Metadata

When the director runs, you have already specified all your feature
metadata, including the value types.

But if some of that information is dependent on what you encounter in the
data, you can do two things:

(A) Run a preliminary pass over the data and gather the required information,
before running the director.

(B) Update the metadata later on
by issuing `cv.meta()` actions from within your director, see below.

## Action methods

The `cv` class contains methods that are responsible for particular *actions*
that steer the graph building.

`n = cv.slot()`
:   Make a slot node and return the handle to it in `n`.

    No further information is needed.
    Remember that you can add features to the node by later

        cv.feature(n, key=value, ...)

    calls.

`n = cv.node(nodeType)`
:   Make a non-slot node and return the handle to it in `n`.
    You have to pass its *node type*, i.e. a string.
    Think of `sentence`, `paragraph`, `phrase`, `word`, `sign`, whatever.
    Non slot nodes will be automatically added to the set of embedders.

    Remember that you can add features to the node by later

        cv.feature(n, key=value, ...)

    calls.

`cv.terminate(n) `
:   **terminate** a node.

    The node `n` will be removed from the set of current embedders.
    This `n` must be the result of a previous `cv.slot()` or `cv.node()` action.

`cv.resume(n)`
:   **resume** a node.

    If you resume a non-slot node, you add it again to the set of embedders.
    No new node will be created.

    If you resume a slot node, it will be added to the set of current embedders.
    No new slot will be created.

`cv.feature(n, name=value, ... , name=value)`
:   Add **node features**.

    The features are passed as a list of keyword arguments.

    These features are added to node `n`.
    This `n` must be the result of a previous `cv.slot()` or `cv.node()` action.

    **If a feature value is `None` it will not be added!**

    The features are passed as a list of keyword arguments.

`cv.edge(nf, nt, name=value, ... , name=value)`
:   Add **edge features**.

    You need to pass two nodes, `nf` (*from*) and `nt` (*to*).
    Together these specify an edge, and the features will be applied
    to this edge.

    You may pass values that are `None`, and a corresponding edge will be created.
    If for all pairs `nf`, `nt` the value is `None`, 
    an edge without values will be created. For every `nf`, such a feature
    essentially specifies a set of nodes `{ nt }`.

    The features are passed as a list of keyword arguments.

`cv.meta(feature, name=value, ... , name=value)`
:   Add, modify, delete metadata fields of features.

    `feature` is the feature name.

    If a `value` is `None`, that `name` will be deleted from the metadata fields.

    A bare `cv.meta(feature)` will remove the feature from the metadata.

    If you modify the field `valueType` of a feature, that feature will be added
    or removed from the set of `intFeatures`.
    It will be checked whether you specify either `int` or `str`.

`occurs = cv.occurs(featureName)`
:   Returns True if the feature with name `featureName` occurs in the
    resulting data, else False.
    If you have assigned None values to a feature, that will count, i.e.
    that feature occurs in the data.

    If you add feature values conditionally, it might happen that some
    features will not be used at all.
    For example, if your conversion produces errors, you might
    add the error information to the result in the form of error features.

    Later on, when the errors have been weeded out, these features will
    not occur any more in the result, but then TF will complain that
    such is feature is declared but not used.
    At the end of your director you can remove unused features
    conditionally, using this function.

`ss = cv.linked(n)`
:   Returns the slots `ss` to which a node is currently linked.

    If you construct non-slot nodes without linking them to slots,
    they will be removed when TF validates the collective result
    of the action methods.

    If you want to prevent that, you can insert an extra slot, but in order
    to do so, you have to detect that a node is still unlinked.

    This action is precisely meant for that.

`isActive = cv.active(n)`
:   Returns whether the node `n` is currently active, i.e. in the set
    of embedders. 

    If you construct your nodes in a very dynamic way, it might be
    hard to keep track for each node whether it has been created, terminated,
    or resumed, in other words, whether it is active or not.

    This action is provides a direct and precise way to know whether a node is active.

`nTypes = cv.activeTypes()`
:   Returns the node types of the currently active nodes, i.e. the embedders.

`cv.get(feature, n)` and `cv.get(feature, nf, nt)`
:   Retrieve feature values.
    
    `feature` is the name of the feature.

    For node features, `n` is the node which carries the value.

    For edge features, `nf, nt` is the pair of from-to nodes which carries the value.

`cv.stop(msg)`
:   Stops the director. No further input will be read.
    The director will exit with a non-good status  and issue the message `msg`.
    If you have called `walk()` with `force=True`, indicating that the
    director must proceed after errors, then this stop command will cause termination
    nevertheless.

!!! hint "Example"
    Follow the
    [conversion tutorial](https://nbviewer.jupyter.org/github/annotation/banks/blob/master/programs/convert.ipynb)

    Or study a more involved example:
    [Old Babylonian](https://github.com/Nino-cunei/oldbabylonian/blob/master/programs/tfFromATF.py)
