# Miscellaneous

## Banner

??? abstract "TF.version"
    ???+ info "Description"
        Contains the version number of the Text-Fabric
        library.

??? abstract "TF.banner"
    ???+ info "Description"
        Contains the name and the version of the Text-Fabric
        library.

## Messaging

??? info "Timed messages"
    Error and informational messages can be issued, with a time indication.

??? abstract "silentOn(), silentOff(), isSilent(), setSilent()"
    Suppress or enable *informational* messages, i.e. messages
    issued through `info()` below.

    This is no influence on *error* messages, i.e. messages
    issued through `error()` below.

    ```python
    silentOn(deep=False)
    ```

    Suppress informational messages.
    If `deep=True` also suppresses warnings.
    
    ```python
    silentOff()
    ```

    Enable informational messages.
    
    ```python
    setSilent(flag)
    ```

    e.g.

    ```
    setSilent(False)
    setSilent(True)
    setSilent('deep')
    ```

    Enable or suppress informational/warning messages dependent on `flag`.

    ```python
    isSilent()
    ```

    Whether informational messages are currently suppressed or not.

??? abstract "info(), warning(), error()"
    ```python
    info(msg, tm=True, nl=True)
    warning(msg, tm=True, nl=True)
    error(msg, tm=True, nl=True)
    ```
    
    ???+ info "Description"
        Sends a message to standard output, possibly with time and newline.

        *   if `info()` is being used, the message is suppressed
            if the silent mode is currently on;
        *   if the silent mode is not `True` but `'deep'`, `warnings()`
            will also be suppressed;
        *   `error()` messages always come through;
        *   if `info()` or warning is being used, the message is sent to `stdout`;
        *   if `error()` is being used, the message is sent to `stderr`;

        In a Jupyter notebook, the standard error is displayed with
        a reddish background colour.

    ??? info "tm"
        If `True`, an indicator of the elapsed time will be prepended to the message.

    ??? info "nl"
        If `True` a newline will be appended.

??? abstract "indent()"
    ```python
    indent(level=None, reset=False)
    ```

    ???+ info "Description"
        Changes the level of indentation of messages and possibly resets the time.

    ??? info "level"
        The level of indentation, an integer.  Subsequent
        `info()` and `error()` will display their messages with this indent.

    ??? info "reset"
        If `True`, the elapsed time to will be reset to 0 at the given level.
        Timers at different levels are independent of each other.

## Clearing the cache

??? abstract "clearCache()"
    ```python
    TF.clearCache()
    ```

    ???+ info "Description"
        Text-Fabric precomputes data for you, so that it can be loaded faster. If the
        original data is updated, Text-Fabric detects it, and will recompute that data.

        But there are cases, when the algorithms of Text-Fabric have changed, without
        any changes in the data, where you might want to clear the cache of precomputed
        results.

        Calling this function just does it, and it is equivalent with manually removing
        all `.tfx` files inside the hidden `.tf` directory inside your dataset.

    ??? hint "See also  clean() below"
        From version 7.7.7 onwards, Text-Fabric uses a parameter called `PACK_VERSION`
        to mark the stored pre-computed data.
        Whenever there are incompatible changes in the packed data format, this
        version number will be increased and Text-Fabric will not attempt to load
        the older pre-computed data.

        The older data will not be removed, however. Use the function `clean()`
        below to get rid of pre-computed data that you no longer need.

    ??? hint "No need to load"
        It is not needed to execute a `TF.load()` first.

??? abstract "clean()"
    ```python
    from tf.clean import clean
    clean(tfd=True, gh=False, dry=False, specific=None, current=False)
    ```

    ???+ info "Description"
        Removes all precomputed data resulting from other `PACK_VERSION`s
        than the one currently used by Text-Fabric.

        You find the current pack version in the
        [parameters file]({{tfghb}}/tf/parameters.py).

    ??? info "tfd"
        By default, your `~/text-fabric-data` is traversed and cleaned,
        but if you pass `tfd=False` it will be skipped.

    ??? info "gh"
        By default, your `~/github` will be skipped,
        but if you pass `gh=True` it will be
        traversed and cleaned.

    ??? info "specific"
        You can pass a specific directory here. The standard directories
        `~/github` and `~/text-fabric-data` will not be used, only
        the directory you pass here. `~` will be expanded to your home directory.

    ??? info "current"
        If current=True, also the precomputed results of the current version will
        be removed.

    ??? info "dry"
        By default, nothing will be deleted, and you only get a list of
        what will be deleted if it were not a dry run.
        If you pass `dry=False` the delete actions will really be executed.
