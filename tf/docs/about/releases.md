# Release notes

!!! hint "Consult the tutorials after changes"
    When we change the API, we make sure that the tutorials show off
    all possibilities.

See the app-specific tutorials via `tf.about.corpora`.

---

**The TEI converter is still in active development.
If you need the latest version, clone the Text-Fabric repo
and in its top-level directory run the command:**

```
pip install -e .
```

## 12

### 12.1

#### 12.1.1

2023-10-29

*   Bug fix: the mechanism to make individual exceptions when adding named entities
    in the `tf.browser.ner.annotate` tool was broken. Thanks to Daniel Swanson for
    spotting it.

### 12.1.0

2023-10-28

##### New stuff

*   In the Text-Fabric browser there will be a new tab in the vertical sidebar: 
    **Annotate**, which will give access to manual annotation tools. I'm developing
    the first one, a tool to annotate named entities efficiently, both in the
    Text-Fabric browser and in a Jupyter Notebook.
    Reed more in `tf.about.annotate`.

    These tools will let you save your work as files on your own computer.

*   In `tf.convert.addnlp` we can now extract more NLP information besides tokens
    and sentences: part-of-speech, morphological tagging, lemmatisation, named
    entity recognititon

##### Fixes

*   in the TEI converter.

### 12.0

#### 12.0.6,7

2023-09-13

Trivial fix in code that exports the data from a job in the Text-Fabric browser.
In the meanwhile there is unfinished business in the `Annotate` tab in the TF-browser,
that will come into production in the upcoming 12.1 release.

The Chrome browser has an attractive feature that other browsers such as Safari lack:
It supports the CSS property
[content-visibility](https://developer.mozilla.org/en-US/docs/Web/CSS/content-visibility).
With this property you can prevent
the browser to do the expensive rendering of content that is not visible on the screen.
That makes it possible to load a lot of content in a single page without tripping up
the browser. You also need the
[IntersectionObserver API])https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API),
but that is generally supported by browsers. With the help of that API you can
restrict the binding of event listeners to elements that are visible on the screen.

So, you can open the Text-Fabric browser in Chrome by passing the option `--chrome`.
But if Chrome is not installed, it will open in the default browser anyway.
Also, when the opening of the browser fails somehow, the webserver is stopped.

#### 12.0.5

2023-07-10

Fixed references to static files that still went to `/server` instead of `/browser`.
This has to do with the new approach to the Text-Fabric browser.

#### 12.0.0-4

2023-07-05

##### Simplification

*   The Text-Fabric browser no longer works with a separate process that holds the
    TF corpus data. Instead, the webserver (flask) loads the corpus itself.
    This will restrict the usage of the TF browser to local-single-user scenarios.

*   Text-Fabric no longer exposes the installation options `[browser, pandas]`

    ```
    pip install 'text-fabric[browser]'
    pip install 'text-fabric[pandas]'
    ```

    If you work with Pandas (like exporting to Pandas) you have to install it yourself:

    ```
    pip install pandas pyarrow
    ```

    The TF browser is always supported.

    The reason to have these distinct capabilities was that there are python libraries 
    involved that do not install on the iPad.
    The simplification of the TF browser makes it possible to be no longer dependent
    on these modules.

    Hence, TF can be installed on the iPad, although the
    TF browser works is not working there yet.
    But the autoloading of data from GitHub/GitLab works.


##### Minor things

*   Header. After loading a dataset, a header is shown with shows all kinds of
    information about the corpus. But so far, it did not show the TF app settings.
    Now they are included in the header. There are two kinds: the explicitly given
    settings and the derived and computed settings.
    The latter ones will be suppressed when loading a dataset in a Jupyter notebook,
    because these settings can become quite big. You can still get them with
    `A.showContext()`. In the TF browser they will be always included, you find it in
    the *Corpus* tab.

---

## Older releases

See `tf.about.releasesold`.

