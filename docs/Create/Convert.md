# Convert

## Walking the source

??? info "Data conversion to TF"
    You can convert a dataset to TF by writing a function that walks through it.

    That is a function that triggers a sequence of actions when reading the data.
    These actions drive Text-Fabric to build a valid Text-Fabric graph.
    Many checks will be performed.


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

            If you modify the field `valueType` of a feature, that feature will be added
            or removed from the set of `intFeatures`.
            It will be checked whether you specify either `int` or `str`.

        ??? abstract "cv.linked()"
            ```python
            ss = cv.linked(m)
            ```

            Returns the slots `ss` to which a node is currently linked.

            If you construct non-slot nodes without linking them to slots,
            they will be removed when TF validates the collective result
            of the action methods.

            If you want to prevent that, you can insert an extra slot, but in order
            to do so, you have to detect that a node is still unlinked.

            This action is precisely meant for that.

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

## MQL

??? info "Data interchange with MQL"
    You can interchange with
    [MQL data]({{emdros}}).
    Text-Fabric can read and write MQL dumps. An
    MQL dump is a text file, like an SQL dump. It contains the instructions to
    create and fill a complete database.

??? abstract "TF.exportMQL()"
    ```python
    TF.exportMQL(dbName, dirName)
    ```

    ???+ info "Description"
        Exports the complete TF dataset into single MQL database.

    ??? info "dirName, dbName"
        The exported file will be written to `dirName/dbName.mql`. If `dirName` starts
        with `~`, the `~` will be expanded to your home directory. Likewise, `..` will
        be expanded to the parent of the current directory, and `.` to the current
        directory, both only at the start of `dirName`.

    ??? explanation "Correspondence TF and MQL"
        The resulting MQL database has the following properties with respect to the
        Text-Fabric dataset it comes from:

        *   the TF *slots* correspond exactly with the MQL *monads* and have the same
            numbers; provided the monad numbers in the MQL dump are consecutive. In MQL
            this is not obligatory. Even if there gaps in the monads sequence, we will
            fill the holes during conversion, so the slots are tightly consecutive;
        *   the TF *nodes* correspond exactly with the MQL *objects* and have the same
            numbers

    ??? note "Node features in MQL"
        The values of TF features are of two types, `int` and `str`, and they translate
        to corresponding MQL types `integer` and `string`. The actual values do not
        undergo any transformation.

        That means that in MQL queries, you use quotes if the feature is a string feature.
        Only if the feature is a number feature, you may omit the quotes:

        ```
        [word sp='verb']
        [verse chapter=1 and verse=1]
        ```

    ??? note "Enumeration types"
        It is attractive to use eumeration types for the values of a feature, whereever
        possible, because then you can query those features in MQL with `IN` and without
        quotes:

        ```
        [chapter book IN (Genesis, Exodus)]
        ```

        We will generate enumerations for eligible features.

        Integer values can already be queried like this, even if they are not part of an
        enumeration. So we restrict ourselves to node features with string values. We
        put the following extra restrictions:

        *   the number of distinct values is less than 1000
        *   all values must be legal C names, in practice: starting with a letter,
            followed by letters, digits, or `_`. The letters can only be plain ASCII
            letters, uppercase and lowercase.

        Features that comply with these restrictions will get an enumeration type.
        Currently, we provide no ways to configure this in more detail.

        ??? note "Merged enumeration types"
            Instead of creating separate enumeration types for individual features,
            we collect all enumerated values for all those features into one
            big enumeration type.

            The reason is that MQL considers equal values in different types as
            distinct values. If we had separate types, we could never compare
            values for different features.

    ??? caution "Values of edge features are ignored"
        There is no place for edge values in
        MQL. There is only one concept of feature in MQL: object features,
        which are node features.
        But TF edges without values can be seen as node features: nodes are
        mapped onto sets of nodes to which the edges go. And that notion is supported by
        MQL:
        edge features are translated into MQL features of type `LIST OF id_d`,
        i.e. lists of object identifiers.

    ??? caution "Legal names in MQL"
        MQL names for databases, object types and features must be valid C identifiers
        (yes, the computer language C). The requirements are:

        *   start with a letter (ASCII, upper-case or lower-case)
        *   follow by any sequence of ASCII upper/lower-case letters or digits or
            underscores (`_`)
        *   avoid being a reserved word in the C language

        So, we have to change names coming from TF if they are invalid in MQL. We do
        that by replacing illegal characters by `_`, and, if the result does not start
        with a letter, we prepend an `x`. We do not check whether the name is a reserved
        C word.

        With these provisos:

        *   the given `dbName` correspond to the MQL *database name*
        *   the TF *otypes* correspond to the MQL *objects*
        *   the TF *features* correspond to the MQL *features*

    ??? hint "File size"
        The MQL export is usually quite massive (500 MB for the Hebrew Bible).
        It can be compressed greatly, especially by the program `bzip2`.

    ??? caution "Exisiting database"
        If you try to import an MQL file in Emdros, and there exists already a file or
        directory with the same name as the MQL database, your import will fail
        spectacularly. So do not do that. A good way to prevent it is:

        *   export the MQL to outside your `text-fabric-data` directory, e.g. to
            `~/Downloads`;
        *   before importing the MQL file, delete the previous copy;

        ??? example "Delete existing copy"
            ```sh
            cd ~/Downloads
            rm dataset ; mql -b 3 < dataset.mql
            ```

??? abstract "TF.importMQL()"
    ```python
    TF.importMQL(mqlFile, slotType=None, otext=None, meta=None)
    ```

    ???+ info "Description"
        Converts an MQL database dump to a Text-Fabric dataset.

    ??? hint "Destination directory"
        It is recommended to call this `importMQL` on a TF instance called with

        ```python
        TF = Fabric(locations=targetDir)
        ```

        Then the resulting features will be written in the targetDir.

        In fact, the rules are exactly the same as for `TF.save()`.

    ??? info "slotType"
        You have to tell which object type in the MQL file acts as the slot type,
        because TF cannot see that on its own.

    ??? info "otext"
        You can pass the information about sections and text formats as the parameter
        `otext`. This info will end up in the `otext.tf` feature. Pass it as a
        dictionary of keys and values, like so:

        ```python
        otext = {
            'fmt:text-trans-plain': '{glyphs}{trailer}',
            'sectionFeatures': 'book,chapter,verse',
        }
        ```

    ??? info "meta"
        Likewise, you can add a dictionary of keys and values that will added to the
        metadata of all features. Handy to add provenance data here:

        ```python
        meta = dict(
            dataset='DLC',
            datasetName='Digital Language Corpus',
            author="That 's me",
        )
        ```
