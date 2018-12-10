# Browser

??? abstract "TF in the browser"
    The Text-Fabric package contains a command to
    work with your corpus in your browser.
    It sets up a local web server, which interacts with your web browser.
    Then you can view and search the corpus without programming and without
    internet connection.

    For some corpora an internet website has been set up. You can then work
    with that corpus without installing anything on your computer,
    but you do need an internet connection.

    In both cases the interface is the same.

    However, if your work locally, you can easily import extra data, made by yourself
    or by other people.

## Start up

???+ note "apps"
    Below, when you see `app`, you have to substitute it by the name
    of an existing TF app, such as `bhsa`, `peshitta`, `syrnt`, `uruk`.

    The Text-Fabric browser fetches the corpora it needs from GitHub automatically.
    [More about corpora](../About/Corpora.md)

??? hint "On Windows?"
    You can click the Start Menu, and type

    ```sh
    text-fabric app
    ```

    in the search box, and then Enter.

??? hint "On Linux or Macos?"
    You can open a terminal (command prompt), and just say

    ```sh
    text-fabric app
    ```

??? abstract "All platforms"
    The corpus data will be downloaded automatically,
    and be loaded into text-fabric.
    Then your browser will open and load the search interface.
    There you'll find links to further help.

## More data

??? abstract "About"
    You can let TF use extra features: 

    ```sh
    text-fabric app --mod=org/repo/path
    text-fabric app --mod=org/repo/path -c
    text-fabric app --mod=org/repo/path,org/repo/path
    ```

    Here `org`, `repo` and `path` must be replaced with a github user or organization,
    a github repo, and a path within that repo.

    Read more about your data life-cycle in the [Data](../Api/Data.md) guide.

## Custom sets

??? abstract "About"
    You can create custom sets of nodes, give them a name, and use those names
    in search templates. 
    The TF browser can import those sets, so that you can use such queries in the browser too.

??? abstract "Invoke"
    ```sh
    text-fabric app --sets=filePath
    ```

    * Start a TF browser for `app` (such as `bhsa`).
    * Loads custom sets from `filePath`.

    `filePath` must specify a file on your local system
    (you may use `~` for your home directory).
    That file must have been written by calling
    [`tf.lib.writeSets`](../Api/Lib.md#sets).
    If so,it contains a dictionary of named node sets.
    These names can be used in search templates,
    and the TF browser will use this dictionary to resolve those names.
    See [S.search() sets argument](../Api/Search.md#search-api).

## Jobs

??? hint "Saving your session"
    Your session (aka *job*) will be saved in your browser,
    under the name *app*`-default`,
    or another name if you rename, duplicate, import or create new sessions.

??? hint "Multiple windows"
    After you have issued the `text-fabric` command, a *TF kernel* is started for you.
    This is a process that holds all the data and can deliver it to other processes,
    such as your web browser.

    As long as you leave the TF kernel on, you have instant access to your corpus.

    You can open other browsers and windows and tabs with the same url,
    and they will load quickly,
    without the long wait you experienced when the TF kernel was loading.

## Shut down

??? abstract "About"
    You can close the TF kernel and web server by pressing Ctrl-C in the terminal
    or command prompt where you have started `text-fabric`.

??? abstract "Clean up"
    Before starting up, the TF browser will check if there are no running processes
    left from an earlier run.
    If so, it will kill them.

    You can also manually clean up yourself:

    `text-fabric app -k`
    
    Or, if you have also processes running for other apps:
    
    `text-fabric -k` 

## Work with exported results

??? abstract "About"
    You can export your results to CSV files which you can process with various tools,
    including your own.

    You can use the "Export" tab to tell the story behind your query and then export
    your view.
    A new page will open, which you can save as a PDF.
    
    There is also a button to download all your results as data files.

??? abstract "Exported materials"
    ??? info "job.json"
        A json file with all information associated with your current session.
        You can import this in the Jobs section, and restore the session by which
        you created these results.

    ??? info "about.md"
        a Markdown file with your description and some provenance metadata.

    ??? info "resultsx.tsv"
        contains your precise search results, decorated with the features
        you have used in your searchTemplate.
        Not only the results on the current page, but *all* results.

    ??? info "results.tsv"
        contains your precise search results, as a list of tuples of nodes.
        Not only the results on the current page, but *all* results.

    ??? info "sections.tsv"
        contains the sections you have selected as a list of nodes.

    ??? info "nodes.tsv"
        contains the nodes you have selected as a list of tuples of nodes.

    Now, if you want to share your results for checking and replication,
    put all this in a research repository or in a GitHub repository,
    which you can then archive to [ZENODO]({{zenodo}}) to obtain a DOI.

??? hint "Unicode in Excel CSVs"
    The file `resultsx.tsv` is not in the usual `utf8` encoding,
    but in `utf_16` encoding.
    The reason is that this is the only encoding
    in which Excel handles CSV files properly.

    So if you work with this file in Python, specify the encoding `utf_16`.

    ```python
    with open('resultsx.tsv', encoding='utf_16') as fh:
      for row in fh:
      # do something with row 
    ```

    Conversely, if you want to write a CSV with Hebrew in it,
    to be opened in Excel, take care to:

    * give the file name extension `.tsv` (not `.csv`)
    * make the file **tab** separated (do not use the comma or semicolon!)
    * use the encoding `utf_16_le` (not merely `utf_16`, nor `utf8`!)
    * start the file with a BOM mark.

    ```python
    with open('mydata.tsv', 'w', encoding='utf_16_le') as fh:
      fh.write('\uFEFF')
      for row in myData:
        fh.write('\t'.join(row))
        fh.write('\n')
    ```

    ??? note "Gory details"
        The file has been written with the `utf_16_le` encoding,
        and the first character is the unicode
        FEFF character.
        That is needed for machines so that they can see which byte in a 16 bits word is
        the least end (`le`) and which one is the big end (`be`).
        Knowing that the first character is FEFF,
        all machines can see whether this is in a *least-endian (le)* encoding
        or in a  *big-endian (be)*.
        Hence this character is called the Byte Order Mark (BOM).
        
        See more on [wikipedia]({{wikip}}/Byte_order_mark).

        When reading a file with encoding `utf_16`,
        Python reads the BOM, draws its conclusions, and strips the BOM.
        So when you iterate over its lines, you will not see the BOM, which is good.
        
        But when you read a file with encoding `utf_16_le`,
        Python passes the BOM through, and you have to skip it yourself.
        That is unpleasant.
        
        Hence, use `utf_16` for reading.  
