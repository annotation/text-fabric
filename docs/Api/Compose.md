# Combing data

???+ explanation
    This package contains functions to operate on TF datasets as a whole

## Add

???+ abstract "usage"
    ```python
    from tf.compose import add
    add(
        location,
        targetLocation,
        nodeTypeSpecs,
    )
    ```

???+ abstract "overview"
    Adds data in the form of nodes and feature values to a data set.
    The result is a data module that contains only features that are 
    different after addition.

    The new nodetypes will come after the `maxNode` of the original
    dataset.

??? info "location"
    You can pass just the location of the original dataset.

??? info "targetLocation"
    The directory into which the result will be written.

??? info "nodeTypeSpecs"
    Per node type that you add, you need to specify the current boundaries of 
    that type and how all those nodes map to slots.
    You can also add features that assign values to those nodes:

    ```python
    dict(
        nodeType1=(nodeFrom1, nodeTo1, slots1, nodeFeatures1, edgeFeatures1),
        nodeType2=(nodeFrom2, nodeTo2, slots2, nodeFeatures2, edgeFeatures2),
    ),
    ```

    The boundaries may be completely arbitrary, so if you get your nodes from another
    TF data source, you do not need to align their values.

    If you also add features about those nodes, the only thing that matters is
    that the features assign the right values to the nodes.

    The slots that you link the new nodes to, must exist in the original.
    You cannot use this function to add slots to your data set.

    ???+ caution "existing node types"
        It is an error if a new node type already exists in the original

    ??? info "nodeFeatures, edgeFeatures"
        You can add any number of features.
        Per feature you have to provide the mapping from nodes to values in the
        case of node features, from nodes to sets of nodes in the case of edge features
        without values, from nodes to dictionaries of nodes with values in the
        case of edge features with values.

        These features may be new, or they may already be present in the original data.

        These features may assign values to new nodes and edges within the new
        node types, but they may also refer to nodes in the original source.
        
        In that case, these values may conflict with existing values, which will result
        in the new values overriding any existing values for the nodes in question.

        You cannot refer to nodes of another node type that you are adding.

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
      deleteTypes=None,
      mergeTypes=None,
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

??? info "deleteTypes"
    You can delete node types from the result altogether.
    You can specify a list of node types as an iterable or as a space
    separated string.

    If a node type has to be deleted, all nodes in all components with that type
    will not be passed to the combined result.

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
        newTypeA=(
            'oldType1',
            'oldType2',
        ),
        newTypeB=(
            'oldType3',
            'oldType4',
        ),
    )
    ```

    or

    ```python
    mergeTypes=dict(
        newTypeA=dict(
            oldType1=dict(
                featureI=valueI,
                featureK=valueK,
            ),
            oldType2=dict(
                featureL=valueL,
                featureM=valueM,
            ),
        ),
        newTypeB=dict(
            oldType3=dict(
                featureN=valueN,
                featureO=valueO,
            ),
            oldType4=dict(
                featureP=valueP,
                featureQ=valueQ,
            ),
        ),
    )
    ```

    It does not matter in what components these types and features already occur.
    The newTypes may be existing types of really new types.
    The new features may be existing or new features.

    This will migrate nodes of type `oldType1` or `oldType2` to nodes of `newTypeA`.

    In the extended form, when there are feature specifications associated
    with the old types, after merging the following assignments will be made:

    `featureI = valueI` to nodes coming from `oldType1`

    and

    `featureK = valueK` to nodes coming from `oldType2`.

    No nodes will be removed!

    ??? caution "meta data"
        If the features you have specified here are new,
        do not forget to pass metadata fro them in the `featureMeta` parameter
        below.
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

    ??? caution "slot types"
        Merging is all about non-slot types.
        It is an error if a new type or an old type is a slot type.

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

??? info "otext"
    The contents of the `otext.tf` features are also metadata,
    and their contents will be merged in exactly the same way.

    So if the section/structure specifications and the formats are not
    the same for all components, you will see them spread out
    in fields qualified by the component name with a `!` sign between
    the key and the component.

    But you can add new specifications explicitly,
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
            componentType='volume',
            componentFeature='vol',
            sectionTypes='volume,chapter,line',
            sectionFeatures='title,number,number',
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
