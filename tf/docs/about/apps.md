# Advanced API

TF is a generic engine to process text and annotations.

When working with specific corpora, we want to have more power at our fingertips.

We need extra power on top of the core TF engine.

The way we have chosen to do it is via *apps*.
An app is a bunch of extra settings and / or functions and / or styles
that feed the advance API.

The advanced API will do its best to generate sensible default settings from
the corpus data, but a bit of nudging will usually improve the results of displaying
structures of the corpus.

For a list of current corpora, see `tf.about.corpora`.

## Components

Apps usually reside in a subdirectory `app` of a repository that holds the corpus data.
Apps can be trivial, completely empty even.

Each TF *app* consists of a folder with these items, all optional:

### static

A folder with styles, fonts and logos, to be used by web servers such as the
TF browser, see `tf.browser.web`.

In particular, `display.css` contains additional styles used for pretty displays.
These styles will be programmatically combined with other styles,
to deliver them to the TF browser on the one hand, and to Jupyter notebooks
on the other hand.

### config.yaml

Settings to feed the advanced API for this app. See `tf.advanced.settings`.

### app.py

Corpus dependent helpers for the advanced API.

### other modules

If you organize bits of the functionality of a corpus app into modules
to be imported by `app.py`, you can put them in this same directory.

!!! caution "Do not `import` app-dependent modules"
    If you import these other modules by means of the Python import system using 
    `import module` or `from module import name` then everything works fine until you
    load two apps in the same program, that in turn load their other modules.
    As long as different apps load modules with different names, there is no problem.
    But if two apps both have a module with the same name, then the first of them
    will be loaded, and both apps use the same code.

    In order to prevent this, you can use the function `loadModule()` to
    dynamically load these modules. They will be given an app-dependent internal
    name, so the Python importer will not conflate them.

!!! explanation "`loadModule()`"
    Here is how you load auxiliary modules in your `app.py`.
    The example is taken from the `uruk` app, which loads
    two modules, `atf` and `image`.

See for example the
[app in the Uruk corpus](https://github.com/Nino-cunei/uruk/tree/master/app).

The place to put the `loadModule()` calls is in the `__init()__` method of the
`TfApp` object, before the call to `super().__init()`.
Here the name of the app and the path to the code directory of the
app are known.

The first argument for `loadModule()` is the file name of the module,
without the `.py`.

`loadModule()` needs the app name and the path to the code,
but we pass it all `*args`, received by `__init__()`.

The result of loading the module is a code object,
from which you can get all the names defined by the module and their semantics.

In the `atf` case, we use the `atfApi()` function of the module to add 
a bunch of functions defined in that module as methods to the `TfApp` object.

In the `image` case, we add the code object as an attribute to the `TfApp` object,
so that all its methods can retrieve all names defined by the `image` module.

## Implementation

Most parts of the advanced API are implemented in the
[api](https://github.com/annotation/text-fabric/blob/master/tf/advanced)
modules of TF.

### Two contexts

Most functions with the `app` argument are meant to perform their duty
in two contexts:

*   when called in a Jupyter notebook they deliver output meant
    for a notebook output cell, using methods provided by the `ipython` package.
*   when called by the web app they deliver output meant for the TF browser website,
    generating raw HTML.

When we construct the rich, app-dependent API,
we let it know whether it is constructed for the purposes of the Jupyter notebook,
or for the purposes of the web app.

We set the attribute `_browse` on the `app` object to `True` 
if we use the `app` in the web app context, otherwise in a programming context.

Most of the code in most functions is independent of `_browse`.
The main difference is how to deliver the result:
by a call to an `IPython` display method, or by returning raw HTML.
