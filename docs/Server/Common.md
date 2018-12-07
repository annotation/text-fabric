# Common Server Related Functions

## About

??? abstract "About"
    Here are functions that are being used by various parts of the
    TF browser infrastructure, such as 

    * [kernel.py]({{tfghb}}/{{c_kernel}})
    * [web.py]({{tfghb}}/{{c_web}})
    * [start.py]({{tfghb}}/{{c_start}})

## Argument parsing

??? abstract "Apologies"
    Really, we should replace the whole adhoc argument parsing by a decent use
    of the Python module
    [argparse]({{python}}/library/argparse.html#module-argparse). 

??? abstract "Specific args"
    The following table shows functions that are responsible for
    detecting a specific command line argument.

    There signature is

    ```python
    def getXxx(cargs=sys.argv)
    ```

    so they will take the script command line args by default,
    but you can also pass an other set of arguments instead.

    function | argument
    --- | ---
    `getCheck` | `-c`
    `getDebug` | `-d`
    `getDocker` | `-docker`
    `getLocalClones` | `-lgc`
    `getModules` | `--mod=`...
    `getNoweb` | `-noweb`
    `getSets` | `--sets=`...


??? abstract "getParam(interactive=False)"
    Checks whether a *dataSource* parameter has been passed on the command line.
    If so, it checks whether it specifies an existing app.
    If no *dataSource* has been passed, and `interactive` is true,
    presents the user with a list of valid choices and asks for input.

## Locating the app

??? abstract "The problem"
    The data source specific apps are bundled inside the TF package.
    The web server of the TF browser needs the files in those apps,
    not as Python modules, but just as files on disk.
    So we have to tell the web server where they are, and we really do not know that
    in advance, because it is dependent on how the text-fabric package has been
    installed by `pip3` on your machine.

    Yet we have found a way through the labyrinth!

??? abstract "getAppdir(myDir, dataSource)"
    The code in
    [web.py]({{tfghb}}/{{c_web}})
    will pass its file location as `myDir`.
    Form there this function computes the locstion of the file in which
    the webapp of the *dataSource* resides: the location of the
    *dataSource* package in
    [apps]({{tfght}}/{{c_apps}}).

    See also [App structure](../Model/Apps.md#the-structure-of-apps)

## Getting and setting form values

??? abstract "Request and response"
    The TF browser user interacts with the web app by clicking and typing,
    as a result of which a HTML form gets filled in.
    This form as regularly submitted to the web server with a request
    for a new incarnation of the page: a response.

    The values that come with a request, must be peeled out of the form,
    and stored as logical values.

    Most of the data has a known function to the web server,
    but there is also a list of webapp dependent options.

    The following functions deal with option values.

??? abstract "getValues(options, form)"
    Given a tuple of option specifications and form data from a web request,
    returns a dictionary of filled in values for those options.

    The options are specified in the `config.py` of an app.

    An option specification is a tuple of the following bits of information:

    * name of the input element in the HTML form
    * type of input (e.g. checkbox)
    * value of html id attribute of the input element
    * label for the input element

    ??? example "Uruk options"
        The options for the C, such as the `phono` transcriptions, you can sayunei app are:

        ```python
        options = (
            ('lineart', 'checkbox', 'linea', 'show lineart'),
            ('lineNumbers', 'checkbox', 'linen', 'show line numbers'),
        )
        ```

    This function isolates the option values from the rest of the form values,
    so that it can be passed as a whole (`**values`) to the app specific API.

??? abstract "setValues(options, source, form)"
    Fills in a *form* dictionary based on values in a *source* dictionary,
    but only insofar the keys to be filled out occur in the `options` specs,
    and with a cast of checkbox values to booleans. 

    This function is used right after reading the form off a request.
    Raw form data is turned into logical data for further processing by the web server.

## HTML formatting

??? abstract "HTML generation"
    Here we generate the HTML for bigger chunks on the page.

??? abstract "pageLinks(nResults, position, spread=10)"
    Provide navigation links for results sets, big or small.

    It creates links around *position* in a set of *nResults*.
    The spread indicates how many links before and after *position* are generated
    in each column.

    There will be multiple columns. The right most column contains links
    to results `position - spread` to `position + spread`.

    Left of that there is a column for results `position - spread*spread`
    to `position + spread*spread`, stepping by `spread`.

    And so on, until the stepping factor becomes bigger than the result set.

??? abstract "passageLinks(passages, sec0, sec1)"
    Provide navigation links for passages,
    in the form of links to sections of level 0, 1 and 2 (books, chapters and verses).
    
    If `sec0` is not given, only a list of sec0 links is produced.

    If `sec0` is given, but `sec1` not, a list of links for sec1s within the given `sec0`
    is produced.
    
    If both `sec0` and `sec1` are given, de sec1 entry is focused. 

??? abstract "shapeOptions(options, values)"
    Wraps the options, specified by the option specification in `config.py`
    into HTML.
    See also [App structure](../Model/Apps.md#the-structure-of-apps)

??? abstract "shapeCondense(condenseTypes, value)"
    Provides a radio-buttoned chooser for the
    [condense types](../Kernel/#data-service-api).

    `value` is the currently chosen option.

??? abstract "shapeFormats(textFormats, value)"
    Provides a radio-buttoned chooser for the
    [text formats](../Kernel/#data-service-api).

    `value` is the currently chosen option.

