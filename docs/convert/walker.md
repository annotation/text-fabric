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
It will apply to a node passed as argument.

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
that steer the graph building:

*   `tf.convert.walker.CV.slot`
*   `tf.convert.walker.CV.node`
*   `tf.convert.walker.CV.terminate`
*   `tf.convert.walker.CV.resume`
*   `tf.convert.walker.CV.feature`
*   `tf.convert.walker.CV.edge`
*   `tf.convert.walker.CV.meta`
*   `tf.convert.walker.CV.occurs`
*   `tf.convert.walker.CV.linked`
*   `tf.convert.walker.CV.active`
*   `tf.convert.walker.CV.activeTypes`
*   `tf.convert.walker.CV.get` and `cv.get(feature, nf, nt)`
*   `tf.convert.walker.CV.stop`

!!! hint "Example"
    Follow the
    [conversion tutorial](https://nbviewer.jupyter.org/github/annotation/banks/blob/master/programs/convert.ipynb)

    Or study a more involved example:
    [Old Babylonian](https://github.com/Nino-cunei/oldbabylonian/blob/master/programs/tfFromATF.py)
