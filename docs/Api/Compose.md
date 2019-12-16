# Combining data

???+ explanation
    This package contains functions to operate on TF datasets as a whole

    There are the following basic operations:

    *   add/merge/delete types and features to/from a single data source
    *   combine several data sources into one

See also the
[compose chapter]({{tutnb}}/banks/compose.ipynb)
in the Banks tutorial.

## Modify

???+ abstract "usage"
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

???+ abstract "overview"
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

??? info "location"
    You can pass just the location of the original dataset in the file system,
    i.e. the directory that contains the .tf files.

??? info "targetLocation"
    The directory into which the result dataset will be written.

??? info "mergeFeatures"
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

??? info "deleteFeatures"
    This should be either a boolean value `True` or an iterable or space
    separated string of features that you want to delete from the result.

    `True` means: all features will be deleted that are not the result of merging
    or adding features (see `mergeFeatures` above and `addFeatures` below.

??? info "addFeatures"
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

??? info "mergeTypes"
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

    ??? caution "slot types"
        Merging is all about non-slot types.
        It is an error if a new type or an old type is a slot type.

??? info "deleteTypes"
    You can delete node types from the result altogether.
    You can specify a list of node types as an iterable or as a space
    separated string.

    If a node type has to be deleted, all nodes in that type
    will be removed, and features that assign values to these nodes will have
    those assignments removed.

    ??? example
        ```python
        deleteTypes=('line', 'sentence')
        ```

        ```python
        deleteTypes=(' line sentence ')
        ```

    ??? caution "slot types"
        Deleting is all about non-slot types.
        It is an error to attempt to delete slot type.

??? info "addTypes"
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

    ???+ caution "existing node types"
        It is an error if a new node type already exists in the original.

    ??? info "nodeFeatures, edgeFeatures"
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

??? caution "featureMeta"
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

??? info "silent"
    Suppress or enable informational messages.

## Combine

???+ abstract "usage"
    ```python
    from tf.compose import combine
    combine(
      (
          location1,
          location2,
      ),
      targetLocation,
    )
    ```

    ```
    combine(
      (
          (name1, location1),
          (name2, location2),
      ),
      targetLocation,
      componentType=None,
      componentFeature=None,
      featureMeta=None,
      **otext,
    )
    ```

???+ abstract "overview"
    Creates a new TF data source out of a number of other ones.
    You may pass as many component data sources as you want.

    The combination will be the union of all nodes of the components,
    rearranged according to their types, where node types with the
    same names will be merged.

    The slots of the result are the concatenation of the slots of the
    components, which must all have the same slot type.

    The node and edge features will be remapped, so that they have
    the same values in the combined data as they had in the individual
    components.

    Optionally, nodes corresponding to the components themselves will be
    added to the combined result.

    Care will be taken of the metadata of the features and the contents
    of the `otext.tf` feature, which consists of metadata only.

    All details of the combination can be steered by means of parameters.

??? info "locations"
    You can either pass just the locations of the components,
    or you can give them a name.
    If you do not give names, the locations will be used as names.

??? info "targetLocation"
    The directory into which the feature files of the combined dataset
    will be written.

??? info "componentType, componentFeature"
    If a string value for `componentType` and/or `componentFeature` is passed,
    a new node type will be added, with nodes for 
    each component.
    There will also be a new feature, that assigns the name of a component
    to the node of that component.

    The name of the new node type is the value of `componentType`
    if it is a non-empty string,
    else it is the value of `componentFeature`.

    The name of the new feature is `componentFeature`
    if it is a non-empty string,
    else it is the value of `componentType`.

    ???+ caution "componentType must be fresh"
        It is an error if the `componentType` is a node type that already
        occurs in one of the components.

    ???+ hint "componentFeature may exist"
        The `componentFeature` may already exist in one or more components.
        In that case the new feature values for nodes of `componentType` will
        just be added to it.

    ??? example
        ```python
        combine(
            ('banks', 'banks/tf/0.2'),
            ('river', 'banks/tf/0.4'),
            'riverbanks/tf/1.0',
            componentType='volume',
            componentFeature='vol',
        )
        ```

        This results of a dataset with nodes and features from the components
        found at the indicated places on your file system.
        After combination, the components are visible in the data set as nodes
        of type `volume`, and the feature `vol` provides the names `banks` and `river`
        for those nodes.

??? info "featureMeta"
    The meta data of the components involved will be merged.
    If feature metadata of the same feature is encountered in different components,
    and if components specify different values for the same keys,
    the different values will be stored under a key with the name of
    the component appended to the key, separated by a `!`.

    The special metadata field `valueType` will just be reduced to one single value `str`
    if some components have it as `str` and others as `int`.
    If the components assign the same value type to a feature, that value type
    will be assigned to the combined feature.

    If you want to assign other meta data to specific features,
    or pass meta data for new features that orginate from the merging process,
    you can pass them in the parameter `featureMeta` as in the following example,
    where we pass meta data for a feature called `level` with integer values.

    ??? example
        ```python
        combine(
            ('banks', 'banks/tf/0.2'),
            ('river', 'banks/tf/0.4'),
            'riverbanks/tf/1.0',
            featureMeta=dict(
              level=dict(
                valueType='int',
                description='level of a section node',
              ),
            ),
        )
        ```

    The contents of the `otext.tf` features are also metadata,
    and their contents will be merged in exactly the same way.

    So if the section/structure specifications and the formats are not
    the same for all components, you will see them spread out
    in fields qualified by the component name with a `!` sign between
    the key and the component.

    But you can add new specifications explicitly,
    as meta data of the `otext` feature.
    by passing them as keyword arguments.
    They will be passed directly to the combined `otext.tf` feature
    and will override anything with the same key
    that is already in one of the components.

    ??? example
        ```python
        combine(
            ('banks', 'banks/tf/0.2'),
            ('river', 'banks/tf/0.4'),
            'riverbanks/tf/1.0',
            featureMeta=dict(
                otext=dict(
                    componentType='volume',
                    componentFeature='vol',
                    sectionTypes='volume,chapter,line',
                    sectionFeatures='title,number,number',
                ),
            ),
            silent=False,
        )
        ```

        will give rise to something like this (assuming that `banks` and
        `rivers` have some deviating material in their `otext.tf`:

        ```
        @config
        @compiler=Dirk Roorda
        @dateWritten=2019-05-20T19:12:23Z
        @fmt:line-default={letters:XXX}{terminator} 
        @fmt:line-term=line#{terminator} 
        @fmt:text-orig-extra={letters}{punc}{gap} 
        @fmt:text-orig-full={letters} 
        @fmt:text-orig-full!banks={letters}{punc} 
        @fmt:text-orig-full!rivers={letters}{gap} 
        @name=Culture quotes from Iain Banks
        @purpose=exposition
        @sectionFeatures=title,number,number
        @sectionFeatures!banks=title,number,number
        @sectionFeatures!rivers=number,number,number
        @sectionTypes=volume,chapter,line
        @sectionTypes!banks=book,chapter,sentence
        @sectionTypes!rivers=chapter,sentence,line
        @source=Good Reads
        @status=with for similarities in a separate module
        @structureFeatures!banks=title,number,number,number
        @structureFeatures!rivers=title,number,number
        @structureTypes!banks=book,chapter,sentence,line
        @structureTypes!rivers=book,chapter,sentence
        @url=https://www.goodreads.com/work/quotes/14366-consider-phlebas
        @version=0.2
        @writtenBy=Text-Fabric
        @writtenBy=Text-Fabric
        @dateWritten=2019-05-28T10:55:06Z
        ```

??? info "silent"
    Suppress or enable informational messages.

