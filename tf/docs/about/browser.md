# Browser

The TF package contains a command to
work with your corpus in your browser.
It sets up a local web server, which interacts with your web browser.
Then you can view and search the corpus without programming and without
internet connection.

## Start up

Below, when you see `app`, you have to substitute it by the name
of an existing TF app.

The TF browser fetches the apps and corpora (`tf.about.corpora`)
it needs from GitHub / GitLab automatically.

!!! hint "On Windows?"
    You can click the Start Menu, and type

        tf app

    in the search box, and then Enter.

!!! hint "On Linux or MacOS?"
    You can open a terminal (command prompt), and just say

        tf app

!!! explanation "All platforms"
    The corpus data will be downloaded automatically,
    and be loaded into TF.
    Then your browser will open and load the search interface.
    There you'll find links to further help.

## More data

You can let TF use extra features: 

``` sh
tf app --mod=org/repo/path
tf app --mod=org/repo/path -c
tf app --mod=org/repo/path,org/repo/path
```

Here `org`, `repo` and `path` must be replaced with a GitHub user or organization,
a GitHub repo, and a path within that repo.

Read more about your data life-cycle in the Data guide (`tf.about.datasharing`).

## Custom sets

You can create custom sets of nodes, give them a name, and use those names
in search templates. 
The TF browser can import those sets, so that you can use such queries in the browser too.

``` sh
tf app --sets=filePath
```

*   Start a TF browser for `app`.
*   Loads custom sets from `filePath`.

`filePath` must specify a file on your local system
(you may use `~` for your home directory).
That file must have been written by calling
`tf.lib.writeSets`.
If so,it contains a dictionary of named node sets.
These names can be used in search templates,
and the TF browser will use this dictionary to resolve those names.
See `tf.search.search.Search.search`, the `sets` argument].

## Jobs

Your session (aka *job*) will be saved in your browser,
under the name *app*`-default`,
or another name if you rename, duplicate, import or create new sessions.

## Shut down

You can close the web server by pressing Ctrl-C in the terminal
or command prompt where you have started `tf`.

## Work with exported results

You can export your results to CSV files which you can process with various tools,
including your own.

You can use the "Export" tab to tell the story behind your query and then export
your view.
A new page will open, which you can save as a PDF.

There is also a button to download all your results as data files.

### Exported materials
`job.json`
:   A JSON file with all information associated with your current session.
    You can import this in the Jobs section, and restore the session by which
    you created these results.

`about.md`
:   a Markdown file with your description and some provenance metadata.

`resultsx.tsv`
:   contains your precise search results, decorated with the features
    you have used in your search template.
    Not only the results on the current page, but *all* results.

`results.tsv`
:   contains your precise search results, as a list of tuples of nodes.
    Not only the results on the current page, but *all* results.

`sections.tsv`
:   contains the sections you have selected as a list of nodes.

`nodes.tsv`
:   contains the nodes you have selected as a list of tuples of nodes.

`nodesx.tsv`
:   contains the nodes you have selected as a list of tuples of nodes,
    decorated with location information and text content.

Now, if you want to share your results for checking and replication,
put all this in a research repository or in a GitHub / GitLab repository,
which you can then archive to [ZENODO](https://zenodo.org) to obtain a DOI.

### UNICODE in Excel CSVs

The file `resultsx.tsv` is not in the usual `utf8` encoding,
but in `utf_16` encoding.
The reason is that this is the only encoding
in which Excel handles CSV files properly.

So if you work with this file in Python, specify the encoding `utf_16`.

``` python
with open('resultsx.tsv', encoding='utf_16') as fh:
    for row in fh:
        # do something with row 
```

Conversely, if you want to write a CSV with Hebrew in it,
to be opened in Excel, take care to:

*   give the file name extension `.tsv` (not `.csv`)
*   make the file **tab** separated (do not use the comma or semicolon!)
*   use the encoding `utf_16_le` (not merely `utf_16`, nor `utf8`!)
*   start the file with a BOM mark.

``` python
with open('mydata.tsv', 'w', encoding='utf_16_le') as fh:
    fh.write('\uFEFF')
    for row in myData:
        fh.write('\t'.join(row))
        fh.write('\n')
```

!!! explanation "Gory details"
    The file has been written with the `utf_16_le` encoding,
    and the first character is the UNICODE
    FEFF character.
    That is needed for machines so that they can see which byte in a 16 bits word is
    the least end (`le`) and which one is the big end (`be`).
    Knowing that the first character is FEFF,
    all machines can see whether this is in a `least-endian (le)` encoding
    or in a  `big-endian (be)`.
    Hence this character is called the Byte Order Mark (BOM).
    
    See more on [Wikipedia](https://en.wikipedia.org/wiki/Byte_order_mark).

    When reading a file with encoding `utf_16`,
    Python reads the BOM, draws its conclusions, and strips the BOM.
    So when you iterate over its lines, you will not see the BOM, which is good.
    
    But when you read a file with encoding `utf_16_le`,
    Python passes the BOM through, and you have to skip it yourself.
    That is unpleasant.
    
    Hence, use `utf_16` for reading.  
