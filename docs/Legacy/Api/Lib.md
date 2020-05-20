# Lib

Various functions that have a function that is not directly tied to a class.
These functions are available in `tf.lib`, so in order to use function `fff`, say

```python
from tf.lib import fff
```

## Sets

!!! abstract "writeSets()"
    ```python
    writeSets(sets, dest)
    ```

    Writes a dictionary of named sets to file.
    The dictionary will be written as a gzipped, pickled data structure.

    Intended use: if you have constructed custom node sets that you want to use
    in search templates that run in the TF browser.

    !!! info "sets"
        A dictionary in which the keys are names for the values, which are sets
        of nodes.

    !!! info "dest"
        A file path. You may use `~` to refer to your home directory.
        The result will be written from this file.

    !!! info "Returns"
        `True` if all went well, `False` otherwise.

!!! abstract "readSets(source)"
    ```python
    sets = readSets(source)
    ```

    Reads a dictionary of named sets from a file specified by `source`.

    This is used by the TF browser, when the user has passed a `--sets=fileName`
    argument to it.

    !!! info "source"
        A file path. You may use `~` to refer to your home directory.
        This file must contain a gzipped, pickled data structure.

    !!! info "Returns"
        The data structure contained in the file if all went well, `False` otherwise.
