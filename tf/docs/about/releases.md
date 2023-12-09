# Release notes

!!! hint "Consult the tutorials after changes"
    When we change the API, we make sure that the tutorials show off
    all possibilities.

See the app-specific tutorials via `tf.about.corpora`.

---

**The TEI converter is still in active development.
If you need the latest version, clone the TF repo
and in its top-level directory run the command:**

``` sh
pip install -e .
```

## 12

### 12.2

#### 12.2.3,4

2023-12-09

Writing support for Ugaritic, thanks to Martijn Naaijer and Christian Højgaard for
converting a Ugaritic corpus to TF.

Fix in display functions (continued):

*   The logic of feature display, fixed in the previous version, was not effective 
    when things are displayed in the TF browser. Because in the TF browser the
    features of the last query were passed as `extraFeatures` instead of
    `tupleFeatures`. This has been fixed by using `tupleFeatures` in the TF browser
    as well.


#### 12.2.2

2023-12-02

Fix in display functions, thanks to Tony Jurg:

*   if you do `A.pretty(x, queryFeatures=False, extraFeatures="yy zz")`
    the extra features were not shown. So there was no obvious way to control
    exactly the features that you want to show in a display. That has been fixed.
    Further clarification: the node features that are used by a query are stored in
    the display option `tupleFeatures`. That is what causes them to be displayed in 
    subsequent display statements. You can also explicitly set/pass the `tupleFeatures`
    parameter.
    However, the fact that `queryFeatures=False` prohibited the display of features
    mentioned in `extraFeatures` was against the intuitions.

Improvements in the PageXML conversion.

*   There are token features `str`, `after` that reflect the logical tokens
*   There are token features `rstr`, `rafter` that reflect the physical tokens
*   The distincition between logical and physical is that physical token triplets
    with the soft hyphen as the middle one, are joined to one logical token;
    this happens across line boundaries, but also region and page boundaries.

#### 12.2.0,1

2023-11-28

New conversion tool: from PageXML. Still in its infancy.
It uses the
[PageXML tools](https://github.com/knaw-huc/pagexml)
by Marijn Koolen.

For an example see
[translatin/logic](https://gitlab.huc.knaw.nl/translatin/logic/-/blob/main/tools/convertPlain.ipynb?ref_type=heads).

Fix:

*   TF did not fetch an earlier version of a corpus if the newest release
    contains a `complete.zip` (which only has the latest version).
*   For some technical reason that still escapes me, the TF browser was slow to start.
    Fixed it by saying `threaded=True` to Flask, as suggested on
    [stackoverflow](https://stackoverflow.com/a/11150849/15236220)

From now on: TF does not try to download `complete.zip` if you pass a `version` argument
to the `use()` command.

### 12.1

#### 12.1.6,7

2023-11-15

Various fixes:

*   Some package data was not included for the NER annotation tool.
*   In the NER tool, the highlighting of hits of the search pattern is now exact, it was
    sometimes off.

Deleted tf.tools.docsright again, but developed it further in 
[docsright](https://github.com/annotation/docsright).

#### 12.1.5

2023-11-02

*   Improvement in dependencies. Text-Fabric is no longer mandatory dependent on
    `openpyxl`, `pandas`, `pyarrow`, `lxml`.
    The optional dependencies on `pygithub` and `python-gitlab` remain, but most users
    will never need them, because TF can also fetch the `complete.zip` that is
    available as release asset for most corpora.

    Whenever TF invokes a module that is not in the mandatory dependencies,
    it will act gracefully, providing hints to install the modules in question.

#### 12.1.3,4

2023-11-01

*   API change in the Annotator:
    Calling the annotator is now easier: 

    ``` python
    A.makeNer()
    ```

    (No need to make an additional `import` statement.)

    This will give you access to all annotation methods, including using a spreadsheet
    to read annotation instructions from.
*   Removal of deprecated commands (on the command line) in version 11:

    * `text-fabric` (has become `tf`)
    * `text-fabric-zip` (has become `tf-zip`)
    * `text-fabric-make` (has become `tf-make`)
    
*   Bug fixes:
    [#81](https://github.com/annotation/text-fabric/issues/81)
    and
    [#82](https://github.com/annotation/text-fabric/issues/82)

*   Spell-checked all bits of the TF docs here (33,000 lines).
    Wrote a script tf.tools.docsright to separate the code content from
    the markdown content, and to strip bits from the markdown content that lead
    to false positives for the spell checker.
    Then had the Vim spell checker run over those lines and corrected all mistakes
    by hand.
    Still, there might be grammar errors and content inaccuracies.
*   12.1.4 follows 12.1.3. quickly, because in corpora without a NER configuration file,
    TF did not start up properly.

#### 12.1.1,2

2023-10-29

*   Bug fix: the mechanism to make individual exceptions when adding named entities
    in the `tf.browser.ner.annotate` tool was broken. Thanks to Daniel Swanson for
    spotting it.
*   Additional fixes and enhancements.

### 12.1.0

2023-10-28

##### New stuff

*   In the TF browser there will be a new tab in the vertical sidebar: 
    **Annotate**, which will give access to manual annotation tools. I am developing
    the first one, a tool to annotate named entities efficiently, both in the
    TF browser and in a Jupyter Notebook.
    Reed more in `tf.about.annotate`.

    These tools will let you save your work as files on your own computer.

*   In `tf.convert.addnlp` we can now extract more NLP information besides tokens
    and sentences: part-of-speech, morphological tagging, lemmatisation, named
    entity recognition

##### Fixes

*   in the TEI converter.

### 12.0

#### 12.0.6,7

2023-09-13

Trivial fix in code that exports the data from a job in the TF browser.
In the meanwhile there is unfinished business in the `Annotate` tab in the TF browser,
that will come into production in the upcoming 12.1 release.

The Chrome browser has an attractive feature that other browsers such as Safari lack:
It supports the CSS property
[content-visibility](https://developer.mozilla.org/en-US/docs/Web/CSS/content-visibility).
With this property you can prevent
the browser to do the expensive rendering of content that is not visible on the screen.
That makes it possible to load a lot of content in a single page without tripping up
the browser. You also need the
[`IntersectionObserver` API](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API),
but that is generally supported by browsers. With the help of that API you can
restrict the binding of event listeners to elements that are visible on the screen.

So, you can open the TF browser in Chrome by passing the option `--chrome`.
But if Chrome is not installed, it will open in the default browser anyway.
Also, when the opening of the browser fails somehow, the web server is stopped.

#### 12.0.5

2023-07-10

Fixed references to static files that still went to `/server` instead of `/browser`.
This has to do with the new approach to the TF browser.

#### 12.0.0-4

2023-07-05

##### Simplification

*   The TF browser no longer works with a separate process that holds the
    TF corpus data. Instead, the web server (flask) loads the corpus itself.
    This will restrict the usage of the TF browser to local-single-user scenarios.

*   TF no longer exposes the installation options `[browser, pandas]`

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
    But the auto-downloading of data from GitHub / GitLab works.


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

