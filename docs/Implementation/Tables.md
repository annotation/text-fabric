
# Tabular display for the TF-browser

## Constants

??? abstract "Fixed values"
    The following values are used by other parts of the program:

    name | description
    --- | ---
    `RESULT` | string | the label of a query result: `result`

## Composition

??? abstract "compose()"
    ```python
    compose(app, tuples, features, position, opened, getx=None, **displayParameters)
    ```

    Takes a list of *tuples* and
    composes it into an HTML table.
    Some of the rows will be expandable, namely the rows specified by `opened`,
    for which extra data has been fetched.

    *features* is a list of names of features that will be shown
    in expanded pretty displays.
    Typically, it is the list of features used in the query that delivered the tuples. 

    *position* The current position in the list. Will be highlighted in the display.

    *getx=None* If `None`, a portion of the tuples will be put in a table. otherwise,
    it is an index in the list for which a pretty display will be retrieved.
    Typically, this happens when a TF-browser user clicks on a table row
    in order to expand
    it.
    
??? abstract "composeT()"
    ```python
    composeT(app, features, tuples, features, opened, getx=None, **displayParameters)"
    ```

    Very much like `compose()`,
    but here the tuples come from a sections and/or tuples specification
    in the TF-browser.

??? abstract "composeP(), getx=None, \*\*displayParameters)"
    ```python
    composeP(
      app,
      sec0, sec1,
      features, query,
      sec2=None,
      opened=set(),
      getx=None,
      **displayParameters
    )
    ```

    Like `composeT()`, but this is meant to compose the items
    at section level 2 (verses) within
    an item of section level 1 (chapter) within an item of section level 0 (a book).
    Typically invoked when a user of the TF-browser is browsing passages.
    The query is used to highlight its results in the passages that the user is browsing.

??? abstract "plainTextS2()"
    ```python
    plainTextS2(sNode, opened, sec2, highlights, \*\*displayParameters)
    ```

    Produces a single item corresponding to a section 2 level (verse) for display
    in the browser. It will rendered as plain text, but expandable to a pretty display.

??? abstract "Highlighting"
    The functions `getPassageHighlights()`, `getHlNodes()`, `nodesFromTuples()`
    are helpers to apply highlighting to query results in a passage.

??? abstract "getBoundary(api, node)"
    Utility function to ask from the TF API the first slot and the last slot contained in a node.

??? abstract "getFeatures(app, node, ...)"
    Helper for `pretty()`: wrap the requested features and their values for *node* in HTML for pretty display.

??? abstract "header(app)"
    Get the app-specific links to data and documentation and wrap it into HTML for display in the TF browser.

