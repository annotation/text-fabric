# Release notes

!!! hint "Consult the tutorials after changes"
    When we change the API, we make sure that the tutorials show off
    all possibilities.

See the app-specific tutorials via `tf.about.corpora`.

---

## 12

### 12.0

#### 12.0.0, 12.0.1

2023-07-05

##### Simplification

*   The Text-Fabric browser no longer works with a separate process that holds the
    TF corpus data. Instead, the webserver (flask) loads the corpus itself.
    This will restrict the usage of the TF browser to local-single-user scenarios.

*   Text-Fabric no longer exposes multiple installation options, such as

    ```
    pip install 'text-fabric[browser]'
    pip install 'text-fabric[all]'
    ```

    Instead, we are back to a single

    ```
    pip install text-fabric
    ```

    for everything, except Pandas.
    If you work with Pandas (like exporting to Pandas) you have to install it yourself:

    ```
    pip install pandas pyarrow
    ```

    The reason to have these distinct capabilities was that there are python libraries 
    involved that do not install on the iPad.
    The simplification of the TF browser makes it possible to be no longer dependent
    on these modules.

    Hence, TF can be installed on the iPad, and the TF browser works there as well,
    and also the autoloading of data from GitHub/GitLab.


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

