# Convert

??? info "Data conversion to TF by walking through the source"
    You can convert a dataset to TF by writing a function that walks through it.

    That is a function that triggers a sequence of actions when reading the data.
    These actions drive Text-Fabric to build a valid Text-Fabric graph.
    Many checks will be performed.

??? hint "to and from MQL"
    If your source is MQL, you are even better off: Text-Fabric has a
    [module](MQL.md)
    to import from MQL and to export to MQL.

??? abstract "cv.walk()"
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
        force=False
    )

    if good:
      ... load the new TF data ...
    ```

    ???+ info "Description"
        `cv.walk` takes your `director` function which should unravel the source.
        You have to program the `director`, which takes one argument: `cv`.
        From the `cv` you can use a few standard actions that instruct Text-Fabric
        to build a graph.

        This function will check whether the metadata makes sense and is minimally
        complete.

        During node creation the section structure will be watched,
        and you will be warned if irregularities occur.

        After the creation of the feature data, some extra checks will be performed
        to see whether the metadata matches the data and vice versa.

    ??? hint "Destination directory"
        The new feature data will be written to the output directory of the
        underlying TF object.
        In fact, the rules are exactly the same as for `TF.save()`.

    ??? info "slotType"
        The node type that acts as the type of the slots in the data set.

    ??? info "oText"
        The configuration information to be stored in the `otext` feature:
        * section types 
        * section features 
        * text formats

        Must be a dict.

    ??? info "generic"
        Metadata that will be written into the header of all generated TF features.

        Must be a dict.

        ??? "hint"
            You can make changes to this later on, dynamically in your director.

    ??? info "intFeatures"
        The set of features that have integer values only.

        Must be an iterable.

        ??? "hint"
            You can make changes to this later on, dynamically in your director.

    ??? info "featureMeta"
        For each node or edge feature descriptive metadata can be supplied.

        Must be a dict of dicts.

        ??? "hint"
            You can make changes to this later on, dynamically in your director.

    ???+ info "warn=True"
        This regulates the response to warnings:

        `warn=True` (default): stop after warnings (as if they are errors);

        `warn=False` continue after warnings but do show them;

        `warn=None` suppress all warnings.

    ???+ info "force=False"
        This forces the process to continue after errors.
        Your TF set might not be valid.
        Yet this can be useful during testing, when you know
        that not everything is OK, but you want to check some results.
        Especially when dealing with large datasets, you might want to test
        with little pieces. But then you get a kind of non-fatal errors that
        stand in the way of testing. For those cases: `force=True`.

    ???+ info "generateTf=True"
        You can pass `False` here to suppress the actual writing of TF data.
        In that way you can dry-run the director to check for errors and warnings

    ??? info "director"
        An ordinary function that takes one argument, the `cv` object, and
        should not deliver anything.

        Writing this function is the main job to do when you want to convert a data source
        to TF.

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

        ??? "hint" Metadata
            When the director runs, you have already specified all your feature
            metadata, including the value types.

            But if some of that information is dependent on what you encounter in the
            data, you can do two things:

            (A) Run a preliminary pass over the data and gather the required information,
            before running the director.

            (B) Update the metadata later on
            by issuing `cv.meta()` actions from within your director, see below.

???+ explanation "`cv` action methods"
    The `cv` class contains methods
    that are responsible for particular *actions* that steer the graph building.

    ??? abstract "cv.slot()"
        ```python
        n = cv.slot()
        ```

        Make a slot node and return the handle to it in `n`.

        No further information is needed.
        Remember that you can add features to the node by later
        `cv.feature(n, key=value, ...)`
        calls.

    ??? abstract "cv.node()"
        ```python
        n = cv.node(nodeType)
        ```

        Make a non-slot node and return the handle to it in `n`.
        You have to pass its *node type*, i.e. a string.
        Think of `sentence`, `paragraph`, `phrase`, `word`, `sign`, whatever.
        Non slot nodes will be automatically added to the set of embedders.

        Remember that you can add features to the node by later
        `cv.feature(n, key=value, ...)`
        calls.

    ??? abstract "cv.terminate()"
        ```python
        cv.terminate(n)
        ```

        **terminate** a node.

        The node `n` will be removed from the set of current embedders.
        This `n` must be the result of a previous `cv.slot()` or `cv.node()` action.

    ??? abstract "cv.resume()"
        ```python
        cv.resume(n)
        ```

        **resume** a node.

        If you resume a non-slot node, you add it again to the set of embedders.
        No new node will be created.

        If you resume a slot node, it will be added to the set of current embedders.
        No new slot will be created.

    ??? abstract "cv.feature()"
        ```python
        cv.feature(n, name=value, ... , name=value)
        ```

        Add **node features**.

        The features are passed as a list of keyword arguments.

        These features are added to node `n`.
        This `n` must be the result of a previous `cv.slot()` or `cv.node()` action.

        **If a feature value is `None` it will not be added!**

        The features are passed as a list of keyword arguments.

    ??? abstract "cv.edge()"
        ```python
        cv.edge(nf, nt, name=value, ... , name=value)
        ```

        Add **edge features**.

        You need to pass two nodes, `nf` (*from*) and `nt` (*to*).
        Together these specify an edge, and the features will be applied
        to this edge.

        You may pass values that are `None`, and a corresponding edge will be created.
        If for all pairs `nf`, `nt` the value is `None`, 
        an edge without values will be created. For every `nf`, such a feature
        essentially specifies a set of nodes `{ nt }`.

        The features are passed as a list of keyword arguments.

    ??? abstract "cv.meta()"
        ```python
        cv.meta(feature, name=value, ... , name=value)
        ```

        Add, modify, delete metadata fields of features.

        `feature` is the feature name.

        If a `value` is `None`, that `name` will be deleted from the metadata fields.

        A bare `cv.meta(feature)` will remove the feature from the metadata.

        If you modify the field `valueType` of a feature, that feature will be added
        or removed from the set of `intFeatures`.
        It will be checked whether you specify either `int` or `str`.

    ??? abstract "cv.occurs()"
        ```python
        occurs = cv.occurs(featureName)
        ```

        Returns True if the feature with name `featureName` occurs in the
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

    ??? abstract "cv.linked()"
        ```python
        ss = cv.linked(n)
        ```

        Returns the slots `ss` to which a node is currently linked.

        If you construct non-slot nodes without linking them to slots,
        they will be removed when TF validates the collective result
        of the action methods.

        If you want to prevent that, you can insert an extra slot, but in order
        to do so, you have to detect that a node is still unlinked.

        This action is precisely meant for that.

    ??? abstract "cv.active()"
        ```python
        isActive = cv.active(n)
        ```

        Returns whether the node `n` is currently active, i.e. in the set
        of embedders. 

        If you construct your nodes in a very dynamic way, it might be
        hard to keep track for each node whether it has been created, terminated,
        or resumed, in other words, whether it is active or not.

        This action is provides a direct and precise way to know whether a node is active.

    ??? abstract "cv.activeTypes()"
        ```python
        nTypes = cv.activeTypes()
        ```

        Returns the node types of the currently active nodes, i.e. the embedders.

    ??? abstract "cv.get()"
        ```python
        cv.get(feature, n)
        cv.get(feature, nf, nt)
        ```

        Retrieve feature values.
        
        `feature` is the name of the feature.

        For node features, `n` is the node which carries the value.

        For edge features, `nf, nt` is the pair of from-to nodes which carries the value.

    ???+ hint "Example"
        Follow the [conversion tutorial]({{tfbanks}}/programs/convert.ipynb)

        Or study a more involved example for
        [Old Babylonian](https://github.com/Nino-cunei/oldbabylonian/blob/master/programs/tfFromATF.py)
