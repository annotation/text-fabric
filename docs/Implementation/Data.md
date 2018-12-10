# Getting data

??? abstract "Auto loading of TF data"
    The specific apps call the functions 
    [`getModulesData()` and `getData()`]({{tfghb}}/{{c_appdata}})
    to load and download data from github.

    When TF stores data in the text-fabric-data directory,
    it remembers from which release it came (in a file `_release.txt`).

    All the data getters need to know is the organization, the repo,
    the path within the repo
    to the data, and the version of the (main) data source.
    The data should reside in directories that correspond to versions
    of the main data source.
    The path should point to the parent of these version directries.

    TF uses the [GitHub API]({{ghapi}}) to discover which is the newest release of
    a repo.
