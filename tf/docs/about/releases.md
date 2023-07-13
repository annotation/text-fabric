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

### 12.0

#### 12.0.6 (upcoming)

2023-07-??

Fixes in the TEI converter.

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

