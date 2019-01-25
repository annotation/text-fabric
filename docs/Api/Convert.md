# Convert

## Token Stream

??? info "Data conversion to TF"
    You can convert a dataset to TF by writing a token generator for it.

    That is a function that delivers a stream of tokens when reading the data.
    Text-Fabric can consume that stream and build a valid Text-Fabric dataset out of it.
    Many checks will be performed.


??? abstract "TF.importTokens()"
    ```python
    TF.importTokens(
      tokens,
      slotType,
      otext={},
      generic={},
      intFeatures=set(),
      featureMeta={},
    )
    ```

    ???+ info "Description"
        Consumes the tokens, collects their payloads, writes it out as a TF dataset.
        Most arguments are used to specify the right TF metadata.

        This function will check whether the metadata makes sense and is minimally
        complete.

        After the creation of the feature data, some extra checks will be performed
        to see whether the metadata matches the data and vice versa.

    ??? hint "Destination directory"
        It is recommended to call this `importTokens` on a TF instance called with

        ```python
        TF = Fabric(locations=targetDir)
        ```

        Then the resulting features will be written in the targetDir.

        In fact, the rules are exactly the same as for `TF.save()`.

    ??? info "tokens"
        An *iterable* of tokens. It can be a list, set, iterator, or generator.
        Think of it as a
        [generator function](https://wiki.python.org/moin/Generators)
        that yields one token at a time.

        Writing this function is the main job to do when you want to convert a data source
        to TF.

    ??? info "slotType"
        The node type that acts as the type of the slots in the data set.

    ???+ explanation "Token syntax"
        Tokens are tuples of the following shapes:

        ```
        ('S', seq, ((type, seq),...)), features)              # slot token       
        ('N', (type, seq), features)                          # node feature token
        ('E', (typeFrom, seqFrom), (typeTo, seqTo), features) # edge feature token
        ```

        `seq` is a positive integer. It is the number of a node within a node `type`,
        in the case of an `'S'` token the type is taken to be the `slotType`.

        For slot nodes, the resulting sequence of `seq` values must be, after ordering,
        a consecutive interval 1, ..., maxSlot. 

        For other nodes, there is no such requirement, but the values must be integers.

        Multiple tokens may refer to the same slot or node: the `features` payload will
        be merged.
        
        For `'E'` tokens, both `seqTo` and `seqFrom` must be integers,
        and `(typeFrom, seqFrom)` and `(typeTo, seqTo)` must occur in some
        `'N'` tokens.
        
        Again, the `features` payload of these tokens will be merged when necessary.
        
        In the case of `'S'` nodes, the `((type, seq), ...)` tuple is a series
        of embedder nodes of that slot. 

        The embedder will be merged with those of other tokens for the same slot.

    ??? info "oText"
        The configuration information to be stored in the `otext` feature:
        * section types 
        * section features 
        * text formats

        Must be a dict.

    ??? info "generic"
        Metadata that will be written into the header of all generated TF features.

        Must be a dict.

    ??? info "intFeatures"
        The set of features that have integer values only.

        Must be an iterable.

    ??? info "featureMeta"
        For each node or edge feature descriptive metadata can be supplied.

        Must be a dict of dicts.


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
