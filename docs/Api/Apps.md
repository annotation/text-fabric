# Apps

??? abstract "About"
    Text-Fabric is a generic engine to process text and annotations.

    When working with specific corpora, we want to have more power at our fingertips.

    We need extra power on top of the TF engine.

    The way we have chosen to do it is via *apps*.
    An app is a bunch of extra functions that *know* the structure of a specific corpus.

## Current apps

??? abstract "Current apps"
    At the moment we have these apps

    * bhsa
    * cunei

## The generic part of apps

??? abstract "App helpers"
    Apps turn out to have several things in common that we want to deal with generically.
    These functions are collected in the
    [apphelpers](https://github.com/Dans-labs/text-fabric/blob/master/tf/apphelpers.py)
    module of TF.

## The structure of apps

??? abstract "App components"
    The apps themselves are modules inside 
    [tf.extra](https://github.com/Dans-labs/text-fabric/tree/master/tf/extra)

    For each *app*, you find there:

    ??? abstract "module"
      *app*`.py`
      contains all the functionality specific to the corpus in question, organized as an extended
      TF api. In the code this is referred to as the `extraApi`.

    ??? abstract "webapp"
      the package *app*`-app`
      is used by the text-fabric browser, and contain settings and assets
      to set up a browsing experience.

      * `config.py`: settings
      * a `static` folder with fonts and logos.

      ??? abstract "config.py"
          Contains values for parameters and an API calling function.

          ??? abstract "extraApi(locations, modules)"
              Responsible for calling the extra Api for the corpus
              with the desired locations and modules.

              This extraApi will be active as a TF data server,
              interacting with a local webserver that serves local
              web page in the browser.

          ??? abstract "web browsing settings"
              The Text-Fabric data server, webserver and browser need settings:

              setting | example | description
              --- | --- | ---
              protocol | `http://` | protocol of local website
              host | `localhost` | server address of local website
              webport | `8001` | port for the local website
              port | `18981` | port through wich the data server and the web server communicate

          ??? abstract "data settings"
              The Text-Fabric data server needs context information:

              setting | type | description
              --- | --- | ---
              locations | list | where to look for tf features
              modules | list | combines with locations to search paths for tf features
              localDir | directory name | temporary directory for writing and reading
              options | tuple | names of extra options for seaerching and displaying query results
              condenseType | string | the default container type to which query results may be condensed
              PROVENANCE | dict | corpus specific provenance metadata: name and DOI
  
