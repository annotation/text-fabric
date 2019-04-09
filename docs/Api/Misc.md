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

??? abstract "info(), error()"
    ```python
    info(msg, tm=True, nl=True)
    ```
    
    ???+ info "Description"
        Sends a message to standard output, possibly with time and newline.

        *   if `info()` is being used, the message is sent to `stdout`;
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

??? abstract "TF.clearCache()"
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

    ??? hint "No need to load"
        It is not needed to execute a `TF.load()` first.
