# Apps

??? abstract "About"
    Text-Fabric is a generic engine to process text and annotations.

    When working with specific corpora, we want to have more power at our fingertips.

    We need extra power on top of the core TF engine.

    The way we have chosen to do it is via *apps*.
    An app is a bunch of extra functions that *know* the structure of a specific corpus.

    In particular, an app knows how to produce plain representations
    and pretty displays of nodes of each type in the corpus.

    For a list of current apps, see [Corpora](../About/Corpora.md)

## Components

??? abstract "App components"
    The apps themselves are those repos inside 
    [annotation]({{an}})
    whose names start with `app-`.
    The part after the `app-` is the name of the app.

    For each *app*, you find there a subfolder `code` with:

    ??? abstract "static"
        A folder with styles, fonts and logos, to be used by web servers such as the the
        [text-fabric browser](../Server/Web.md).

        In particular, `display.css` contains the styles used for pretty displays.
        These styles will be programmatically combined with other styles,
        to deliver them to the TF browser on the one hand, and to Jupyter notebooks
        on the other hand.

    ??? abstract "config.py"
        Settings to set up a browsing experience and to feed the specific AP
        for this app.

        The app is driven by the settings as specified in the 
        [config file of the default TF app]({{anapp}}default/blob/master/code/config.py).

    ??? abstract "app.py"
        The functionality specific to the corpus in question, organized as an extended
        TF api. In the code you see this stored in variables with name `app`.

        In order to be an app that TF can use, `app` should provide the following attributes:

        attribute | kind | description
        --- | --- | ---
        webLink | method | given a node, produces a link to an online description of the corresponding object (to [shebanq]({{shebanq}}) or [cdli]({{cdli}})) 

    ??? abstract "other modules"
        If you organize bits of the functionality of the app in modules to be imported by `app.py`,
        you can put them in this same directory.

        ???+ caution "Do not `import` app-dependent modules"
            If you import these other modules by means of the Python import system using 
            `import module` or `from module import name` then everything works fine until you
            load two apps in the same program, that in turn load their other modules.
            As long as different apps load modules with different names, there is no problem/
            But if two apps both have a module with the same name, then the first of them
            will be loaded, and both apps use the same code.

            In order to prevent this, you can use the function `loadModule()` to
            dynamically load these modules. They will be given an app-dependent internal
            name, so the Python importer will not conflate them.

        ??? abstract "loadModule()"
            Here is how you load auxiliary modules in your `app.py`.
            The example is taken from the `uruk` app, which loads
            two modules, `atf` and `image`.

            `atf` is a bunch of functions that enrich the api of the app.
            The `atf` module contains a function that adds all these functions
            to an object: 
            [`atfApi`]({{anapp}}uruk/blob/master/code/atf.py)

            ```python
            from tf.applib.app import loadModule

            class TfApp(object):

              def __init__(app, *args, _browse=False, silent=False, **kwargs):

                atf = loadModule(*args[0:2], 'atf')
                atf.atfApi(app)

                app.image = loadModule(*args[0:2], 'image')

                setupApi(app, *args, _browse=_browse, silent=silent, **kwargs)

            ```

            The place to put the `loadModule()` calls is in the `__init()__` method of the
            `TfApp` object, before the call to `setupApi()`.
            Here the name of the app and the path to the code directory of the
            app are known.
            They are provided by the first two arguments by which the `__init__()` method is called.

            `loadModule()` needs the app name and the path to the code, to we pass it `*args[0:2]`,
            the first two arguments received by `__init__()`.

            The third argument for `loadModule()` is the file name of the module, without the `.py`.

            The result of loading the module is a code object, from which you can get all the names
            defined by the module and their semantics.

            In the `atf` case, we use the `atfApi()` function of the module to add 
            a bunch of functions defined in that module as methods to the TfApp object.

            In the `image` case, we add the code object as an attribute to the TfApp object,
            so that all its methods can retrieve all names defined by the `image` module.

## Implementation

??? abstract "App support"
    Apps turn out to have several things in common that we want to deal with generically.
    These functions are collected in the
    [api]({{tfghb}}/{{c_applib}})
    modules of TF.

??? abstract "Two contexts"
    Most functions with the `app` argument are meant to perform their duty
    in two contexts:

    * when called in a Jupyter notebook they deliver output meant
      for a notebook output cell,
      using methods provided by the `ipython` package.
    * when called by the web app they deliver output meant for the TF browser website,
      generating raw HTML.

    The `app` is the rich app specific API, and when we construct this API,
    we pass the information
    whether it is constructed for the purposes of the Jupyter notebook,
    or for the purposes of the web app.

    We pass this information by setting the attribute `_browse` on the `app`. 
    If it is set, we use the `app` in the web app context.

    Most of the code in such functions is independent of `_browse`.
    The main difference is how to output the result:
    by a call to an IPython display method, or by
    returning raw HTML.

    ??? note "\_browse"
        The `app` contains several display functions. By default
        they suppose that there is a Jupyter notebook context in which
        results can be rendered with `IPython.display` methods.
        But if we operate in the context of a web-interface, we need to generate
        straight HTML. We flag the web-interface case as `_browse == True`.
