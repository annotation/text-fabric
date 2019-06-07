# Text-Fabric API

??? note "Tutorial"
    The tutorials for specific [annotated corpora]({{an}})
    put the Text-Fabric API on show for vastly different corpora.

???+ note "Generic API versus apps"
    This is the API of Text-Fabric in general.
    Text-Fabric has no baked in knowledge of particular corpora.

    However, Text-Fabric comes with several *apps* that make working
    with specific [corpora](../About/Corpora.md) easier.

## Loading

??? abstract "TF=Fabric()"
    ```python
    from tf.fabric import Fabric
    TF = Fabric(locations=directories, modules=subdirectories, silent=False)
    ```

    ???+ info "Description"
        Text-Fabric is initialized for a corpus. It will search a set of directories
        and catalog all `.tf` files it finds there.
        These are the features you can subsequently load.

        Here `directories` and `subdirectories` are strings with directory names
        separated by newlines, or iterables of directories.

    ??? info "locations, modules"
        The directories specified in `locations` will be searched for `modules`, which
        are paths that will be appended to the paths in `locations`.

        All `.tf` files (non-recursively) in any `module` will be added to the feature
        set to be loaded in this session. The order in `modules` is important, because
        if a feature occurs in multiple modules, the last one will be chosen. In this
        way you can easily override certain features in one module by features in an
        other module of your choice.

    ??? note "otext@ in modules"
        If modules contain features with a name starting with `otext@`, then the format
        definitions in these features will be added to the format definitions in the
        regular `otext` feature (which is a WARP feature). In this way, modules that
        define new features for text representation, also can add new formats to the
        Text-API.

    ??? hint "Defaults"
        The `locations` list has a few defaults:

        ```
        ~/Downloads/text-fabric-data
        ~/text-fabric-data
        ~/github/text-fabric-data
        ```

        So if you have stored your main Text-Fabric dataset in
        `text-fabric-data` in one of these directories
        you do not have to pass a location to Fabric.

        The `modules` list defaults to `['']`. So if you leave it out, Text-Fabric will
        just search the paths specified in `locations`.

    ??? info "silent"
        If `silent=True` is passed, banners and normal progress messages are suppressed.

??? abstract "TF.explore()"
    ```python
    features = TF.explore(silent=False, show=True)
    features
    ```

    or

    ```python
    TF.explore(silent=False, show=False)
    TF.featureSets
    ```

    ???+ info "Description"
        This will give you a dictionary of all available features by kind. The kinds
        are: *nodes*, *edges*, *configs*, *computeds*.

    ??? info "silent"
        With `silent=False` a message containing the total numbers of features is issued.

    ??? info "show"
        The resulting dictionary is delivered in `TF.featureSets`, but if you say
        `show=True`, the dictionary is returned as function result.


??? abstract "api=TF.load()"
    ```python
    api = TF.load(features, add=False, silent=False)
    ```

    ???+ info "Description"
        Reads the features indicated by `features` and loads them in memory
        ready to be used in the rest of the program.

    ??? info "features"
        `features` is a string containing space separated feature names, or an
        iterable of feature names. The feature names are just the names of `.tf` files
        without directory information and without extension.

    ??? info "add"
        If later on you want load more features, you can either:

        *   add the features to the original `load()` statement and just run it again
        *   make a new statement: `TF.load(newfeatures, add=True)`. The new features will
            be added to the same api, so you do not have to to call
            `api.makeAvailableIn(globals())` again after this!

    ??? info "silent"
        The features will be loaded rather silently, most messages will be suppressed.
        Time consuming operations will always be announced, so that you know what
        Text-Fabric is doing. If `silent=True` is passed, all informational messages
        will be suppressed. This is handy I you want to load data as part of other
        methods, on-the-fly.

??? abstract "api=TF.loadAll()"
    ```python
    api = TF.loadAll(silent=True)
    ```

    ???+ info "Description"
        Reads all available features and loads them in memory
        ready to be used in the rest of the program.

    ??? info "silent"
        As in TF.load().

??? abstract "ensureLoaded()"
    ```python
    ensureLoaded(features)
    ```

    ???+ info "Description"
        Reads the features indicated by `features` and checks if they
        are loaded. The unloaded ones will be loaded. 
        Makes all of them ready to be used in the rest of the program.

    ??? info "features"
        `features` is a string containing space separated feature names, or an
        iterable of feature names. The feature names are just the names of `.tf` files
        without directory information and without extension.

???+ abstract "api.makeAvailableIn(globals())"
    ```python
    api.makeAvailableIn(globals())
    ```

    ???+ info "Description"
        This method will export every member of the API (such as `N`, `F`, `E`, `L`, `T`,
        `info`) to the global namespace. From now on, we will omit the `api.` in our
        documentation.

    ??? explanation "Contents of the API"
        After having loaded the features by `api = TF.load(...)`, the `api` harbours
        your Text-Fabric API. You can access node feature `mydata` by `api.F.mydata.v(node)`, edge
        feature `mylink` by `api.E.mylink.f(node)`, and so on.

        If you are working with a single data source in your program, it is a bit
        tedious to write the initial `api.` all the time.
        By this methodd you can avoid that.

    ???+ hint "Longer names"
        There are also longer names which can be used as aliases to the single capital
        letters. This might or might not improve the readability of your program.

        short name | long name
        --- | ---
        `N` | [`Nodes`](Nodes.md)
        `F` | [`Feature`](Features.md)
        `Fs` | `FeatureString`
        `Fall` | `AllFeatures`
        `E` | [`Edge`](Features.md)
        `Es` | `EdgeString`
        `Eall` | `AllEdges`
        `C` | [`Computed`](Computed.md)
        `Cs` | `ComputedString`
        `Call` | `AllComputeds`
        `L` | [`Locality`](Locality.md)
        `T` | [`Text`](Text.md)
        `S` | [`Search`](Search.md)

??? abstract "ignored"
    ```python
    api.ignored
    ```

    ???+ info "Description"
        If you want to know which features were found but ignored (because the feature
        is also present in another, later, location), you can use this attribute
        to inspect the ignored features and their locations.

??? abstract "loadLog()"
    ```python
    api.loadlog()
    ```

    ???+ info "Description"
        After loading you can view all messages using this method.
        It also shows the messages that have been suppressed due to `silent=True`.

## Saving features

??? abstract "TF.save()"
    ```python
    TF.save(
        nodeFeatures={}, edgeFeatures={}, metaData={},
        location=None, module=None,
        silent=None,
    )
    ```

    ???+ info "Description"
        If you have collected feature data in dictionaries, keyed by the
        names of the features, and valued by their feature data,
        then you can save that data to `.tf` feature files on disk.

        It is this easy to export new data as features:
        collect the data and metadata of
        the features and 
        feed it in an orderly way to `TF.save()` and there you go.
         
    ??? info "nodeFeatures"
        The data of a node feature is a dictionary with nodes as keys (integers!) and
        strings or numbers as (feature) values.

    ??? info "edgeFeatures"
        The data of an edge feature is a dictionary with nodes as keys, and sets or
        dictionaries as values. These sets should be sets of nodes (integers!), and
        these dictionaries should have nodes as keys and strings or numbers as values.

    ??? info "metadata"
        Every feature will receive metadata from `metaData`, which is a dictionary
        mapping a feature name to its metadata.
        
        ??? note "value types"
            The type of the values should conform to `@valueType` (`int` or `str`), which
            must be stated in the metadata.

        ??? note "edge values"
            If you save an edge feature, and there are values in that edge feature, you have
            to say so, by specifying `edgeValues = True` in the metadata for that feature.

        ??? note "generic metadata"
          `metaData` may also contain fields under
          the empty name. These fields will be added to all features in `nodeFeatures` and
          `edgeFeatures`.

        ??? note "config features"
            If you need to write the *config* feature `otext`,
            which is a metadata-only feature, just
            add the metadata under key `otext` in `metaData` and make sure
            that `otext` is not a key in `nodeFeatures` nor in
            `edgeFeatures`.
            These fields will be written into the separate config feature `otext`,
            with no data associated.

    ??? note "save location"
        The (meta)data will be written to the very last directory that TF searched when
        looking for features (this is determined by the `locations` and `modules` parameters
        with which you called TF.

        If both `locations` and `modules` are empty, writing will take place
        in the current directory.

        But you can override it:

        If you pass `module=something`, TF will save in `loc/something`,
        where `loc` is the last member of the `locations` parameter of TF.

        If you pass `location=something`, TF will save in `something/mod`,
        where `mod` is the last meber of the `modules` parameter of TF.

        If you pass `location=path1` and `module=path2`, TF will save in `path1/path2`.

    ??? note "silent"
        TF is silent if you specified `silent=True` in a preceding `TF=Fabric()` call.
        But if you did not, you can also pass `silent=True` to this call.
