# Set up

!!! abstract "setupApi()"
    This method is called by each specific app when it instantiates
    its associated class with
    a single object.

    A lot of things happen here:

    * all data is looked up, downloaded, prepared, loaded, etc
    * the underlying TF Fabric API is called
    * custom links to documentation etc are set
    * styling is set up
    * several methods that are generically defined are added as instance methods

    !!! note "Parameters"
        This method is called with the parameters that the user
        passes to the incantation method [`use()`](../Api/App.md#incantation)

## Specific functions

During setup several modules contribute functions that are included in the API.
For example, the module [display.py](https://github.com/annotation/text-fabric/blob/master/tf/applib/display.py) contains
a function `displayApi()` that adds the methods `plain()` and `pretty()` and others
to the API.

The display module defines more functions, to be used by other parts of TF Fabric.
These will not be advertised to the end user, although it is not impossible for end users
access these methods.

The same structure is used for the other modules that are part of the generic app support.
