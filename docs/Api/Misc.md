# Miscellaneous

## Get Data


The `hasTf` and `getTf` functions
download TF data from one of the
ETCBC repositories on GitHub.

These functions will be called automatically if you call
`Bhsa()` or `Cunei()` without `api` argument.

### BHSA

??? abstract "hasTf(lgc, source, version, relative)"
    Checks whether the TF data for a source/version of a release of an
    ETCBC repository is locally present.

    If the data is already present under your local
    `~/github` directory,
    it will return the full path to `~/github` on your machine.
    
    If not, but the data is already present under your local
    `~/text-fabric-data` directory,
    it will return the full path to `~/text-fabric-data` on your machine.

    If no data is present locally, it will return `False`.

    If `lgc` is `False`, the step of looking at your local github directories
    will be skipped.
    In this case, only your `~/text-fabric-data` will be inspected and used.

??? abstract "getTf(lgc, source, release, version, relative)"
    Gets the TF data for a source/version of a release of an
    ETCBC repository.

    If the data is already present under your local
    `~/github` directory or `~/text-fabric-data` directory,
    it will not be downloaded. 

    If not, it will be downloaded to a location within
    `~/text-fabric-data`.

    If `lgc` is `False`, the step of looking at your local github directories
    will be skipped.
    In this case, only your `~/text-fabric-data` will be inspected and used.

    All arguments except the first are optional, the defaults are:

    argument | default | description
    --- | --- | ---
    source | `bhsa` | repo within ETCBC organization
    release | `1.3` | release version of repo
    version | `c` | version of the BHSA
    relative | `{}/tf` | relative path of TF data within repo. The `{}` will be substituted with the value of `source`.

    ??? example "Main data"
        Most recent version of the main BHSA data

        ```python
        getTf()
        ```

    ??? example "Phono"
        Most recent version of the *phono* features:
        ```python
        getTf(source='phono', release='1.0.1')
        ```
    
    ??? example "Crossrefs"
        Most recent version of the *crossref* features:
        ```python
        getTf(source='parallels', release='1.0.1')
        ```
??? abstract "get and load data"
    Here is an incantation to auto-load data:

    ```python
    from tf.extra.bhsa import hasTf, getTf, Bhsa

    getTf(version='2017')
    loc = hasTf(version='2017')
    TF = Fabric(locations=[f'{loc}/etcbc/bhsa'], modules=['tf/2017'])
    ```

    And if you want to load phono data as well:

    ```python
    from tf.extra.bhsa import hasTf, getTf, Bhsa

    getTf(source='bhsa', version='2017')
    locMain = hasTf(source='bhsa', version='2017')

    getTf(source='phono', version='2017')
    locPhono = hasTf(source='phono', version='2017')

    TF = Fabric(
      locations=[f'{locMain}/etcbc/bhsa', f'{locPhono}/etcbc/phono'],
      modules=['tf/2017'],
    )
    ```

    This will work also in cases where the main BHSA data is in your
    `~/github` directory and the phono data is in your `~/text-fabric-data`
    directory or vice versa.
    

