## Combine

!!! abstract "usage"
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

!!! abstract "overview"
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

!!! info "locations"
    You can either pass just the locations of the components,
    or you can give them a name.
    If you do not give names, the locations will be used as names.

!!! info "targetLocation"
    The directory into which the feature files of the combined dataset
    will be written.

!!! info "componentType, componentFeature"
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

    !!! caution "componentType must be fresh"
        It is an error if the `componentType` is a node type that already
        occurs in one of the components.

    !!! hint "componentFeature may exist"
        The `componentFeature` may already exist in one or more components.
        In that case the new feature values for nodes of `componentType` will
        just be added to it.

    !!! example
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

!!! info "featureMeta"
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

    !!! example
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

    !!! example
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

!!! info "silent"
    Suppress or enable informational messages.
