## Modify

!!! abstract "usage"
    ```python
    from tf.compose import compose
    modify(
        location,
        targetLocation,
        mergeFeatures=None,
        deleteFeatures=None,
        addFeatures=None,
        mergeTypes=None,
        deleteTypes=None,
        addTypes=None,
        featureMeta=None,
        silent=False,
    )
    ```

!!! abstract "overview"
    Modifies the supply of node types and features
    in a single data set.

    Dependent on the presence of the parameters, the following steps will be
    executed before the result is written out as a new TF dataset:

    *   merge existing features into an other feature, removing the features
        that went in;
    *   delete any number of existing features;
    *   add any number of features and their data;
    *   merge existing node types into a new one, removing the
        types that went in, without loss of nodes;

    So far, no new nodes have been added or removed. But then:

    *   delete any number of node types with their nodes;
    *   add any number of new node types, with nodes and features.
    
    The last two action lead to a shifting of nodes, and all features that map
    them, will be shifted accordingly.

    You can also pass meta data to be merged in.

    Finally, the resulting features will be written to disk.

    !!! hint "Only added/merged features"
        It is possible to output only the added and merged features instead
        of a complete dataset. Just pass the boolean value `True` to `deleteFeatures`
        below.

!!! info "location"
    You can pass just the location of the original dataset in the file system,
    i.e. the directory that contains the .tf files.

!!! info "targetLocation"
    The directory into which the result dataset will be written.

!!! info "mergeFeatures"
    You can merge several features into one. This is especially useful if there
    are many features each operating on different node types, and you want to
    unify them into one feature.
    The situation may occur that several of the features to be merged supply conflicting
    values for a node. Then the last feature in the merge list wins.

    The result feature may exist already. Also then there is a risk of conflict.
    Again, the merge result wins.

    ```python
    mergeFeatures=dict(
        resultFeature1=[feat1, feat2],
        resultFeature2=[feat3, feat4],
    ),
    ```

    If the resulting feature is new, or needs a new description, you can 
    provide metadata in the `featureMeta` argument.
    For new features you may want to set the `valueType`, although we try
    hard to deduce it from the data available.

!!! info "deleteFeatures"
    This should be either a boolean value `True` or an iterable or space
    separated string of features that you want to delete from the result.

    `True` means: all features will be deleted that are not the result of merging
    or adding features (see `mergeFeatures` above and `addFeatures` below.

!!! info "addFeatures"
    You can add as many features as you want, assigning values to all types,
    including new nodes of new types that have been generated in the steps before.

    You can also use this parameter to override existing features:
    if a feature that you are adding already exists, the new data will be merged
    in, overriding assignments of the existing feature if there is a conflict.
    The meta data of the old and new feature will also be merged.

    The parameter must have this shape:

    ```python
    addFeatures=dict(
        nodeFeatures=dict(
          feat1=data1,
          feat2=data2,
        ),
        edgeFeatures=dict(
          feat3=data3,
          feat4=data4,
        ),
    ```

    If the resulting features are new, or need a new description, you can 
    provide metadata in the `featureMeta` argument.
    For new features you may want to set the `valueType`, although we try
    hard to deduce it from the data available.

!!! info "mergeTypes"
    You can merge several node types into one.
    The merged node type will have the union of nodes of the types that are merged.
    All relevant features will stay the same, except the `otype` feature of course.

    You can pass additional information to be added as features to nodes
    of the new node type. 
    These features can be used to discriminate between the merged types.

    The parameter you pass takes this shape

    ```python
    mergeTypes=dict(
        outTypeA=(
            'inType1',
            'inType2',
        ),
        outTypeB=(
            'inType3',
            'inType4',
        ),
    )
    ```

    or

    ```python
    mergeTypes=dict(
        outTypeA=dict(
            inType1=dict(
                featureI=valueI,
                featureK=valueK,
            ),
            inType2=dict(
                featureL=valueL,
                featureM=valueM,
            ),
        ),
        outTypeB=dict(
            inType3=dict(
                featureN=valueN,
                featureO=valueO,
            ),
            inType4=dict(
                featureP=valueP,
                featureQ=valueQ,
            ),
        ),
    )
    ```

    It does not matter if these types and features already occur.
    The outTypes may be existing types of really new types.
    The new features may be existing or new features.

    Do not forget to provide meta data for new features in the `featureMeta` argument.

    This will migrate nodes of type `inType1` or `inType2` to nodes of `outTypeA`.

    In the extended form, when there are feature specifications associated
    with the old types, after merging the following assignments will be made:

    `featureI = valueI` to nodes coming from `inType1`

    and

    `featureK = valueK` to nodes coming from `inType2`.

    No nodes will be removed!

    !!! caution "slot types"
        Merging is all about non-slot types.
        It is an error if a new type or an old type is a slot type.

!!! info "deleteTypes"
    You can delete node types from the result altogether.
    You can specify a list of node types as an iterable or as a space
    separated string.

    If a node type has to be deleted, all nodes in that type
    will be removed, and features that assign values to these nodes will have
    those assignments removed.

    !!! example
        ```python
        deleteTypes=('line', 'sentence')
        ```

        ```python
        deleteTypes=(' line sentence ')
        ```

    !!! caution "slot types"
        Deleting is all about non-slot types.
        It is an error to attempt to delete slot type.

!!! info "addTypes"
    You may add as many node types as you want.

    Per node type that you add, you need to specify the current boundaries of 
    that type and how all those nodes map to slots.
    You can also add features that assign values to those nodes:

    ```python
    dict(
        nodeType1=dict(
            nodeFrom=from1,
            nodeTo=to1,
            nodeSlots=slots1,
            nodeFeatures=nFeatures1,
            edgeFeatures=eFeatures1,
        ),
        nodeType2=dict(
            nodeFrom=from2,
            nodeTo=to2,
            nodeSlots=slots2,
            nodeFeatures=nFeatures2,
            edgeFeatures=eFeatures2,
        ),
    ),
    ```

    The boundaries may be completely arbitrary, so if you get your nodes from another
    TF data source, you do not need to align their values.

    If you also add features about those nodes, the only thing that matters is
    that the features assign the right values to the nodes within the boundaries.
    Assignments to nodes outside the boundaries will be ignored.

    The slots that you link the new nodes to, must exist in the original.
    You cannot use this function to add slots to your data set.

    !!! caution "existing node types"
        It is an error if a new node type already exists in the original.

    !!! info "nodeFeatures, edgeFeatures"
        You can add any number of features.
        Per feature you have to provide the mapping that defines the feature.
        
        These features may be new, or they may already be present in the original data.

        If these features have values to nodes that are not within the boundaries
        of the new node type, those values will not be assigned but silently discarded.

        Node features are specified like this:

        ```python
        dict(
            feat1=dict(
                n1=val1,
                n2=val2,
            ),
            feat2=dict(
                n1=val1,
                n2=val2,
            ),
        ),
        ```

        Edge features without values are specified like this:

        ```python
        dict(
            feat1=dict(
                n1={m1, m2},
                n2={m3, m4},
            ),
            feat2=dict(
                n1={m5, m6},
                n2={m7, m8},
            ),
        ),
        ```

        Edge features with values are specified like this:

        ```python
        dict(
            feat1=dict(
                n1={m1: v1, m2: v2},
                n2={m3: v3, m4: v4},
            ),
            feat2=dict(
                n1={m5: v5, m6: v6},
                n2={m7: v7, m8: v8},
            ),
        ),
        ```

!!! caution "featureMeta"
    If the features you have specified in one of the paramers above are new,
    do not forget to pass metadata for them in this  parameter
    It is especially important to state the value type:

    ```python
    featureMeta=dict(
        featureI=dict(
          valueType='int',
          description='level of node'
        ),
        featureK=dict(
          valueType='str',
          description='subtype of node'
        ),
    ),
    ```

    You can also tweak the section/structure configuration and the
    text-formats that are specified in the `otext` feature.
    Just specify them as keys and values to the `otext` feature.

    The logic of tweaking meta data is this: what you provide in this
    parameter will be merged into existing meta data.

    If you want to remove a key from a feature, give it the value None.

!!! info "silent"
    Suppress or enable informational messages.

