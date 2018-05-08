BHSA API
========

About
-----

The module [bhsa.py](https://github.com/Dans-labs/text-fabric/blob/master/tf/extra/bhsa.py)
contains a number of handy functions on top of Text-Fabric and especially its 
[Search](https://github.com/Dans-labs/text-fabric/wiki/Api#search) part.

Set up
------

This module comes in action after you have set up TF and loaded some features, e.g.

```python
VERSION = '2017'
TF = Fabric(locations=f'~/github/etcbc/bhsa/tf/{VERSION}')
api = TF.load('''
  function sp gn nu
''')
api.makeAvailableIn(globals())
```

Then we add the functionality of the `bhsa` module in the following way:

```python
B = Bhsa(api, 'test', version=VERSION)
```

It will silently load some additional features, and `B` will give access to some extra functions.

API
---

### shbLink ###

Produces a link to SHEBANQ

**Takes**

*   an arbitrary node;
*   `text=None` optional link text;

**Returns**

*   a hyperlink to SHEBANQ, precisely to the verse in which the node occurs; if
    the node is a book or a chapter, it will go to the first chapter and the first
    verse of those. The text of the link is a passage indicator (from book,
    chapter and verse), unless `text` has been passed. In that case, the passage
    indicator goes to the popup hint of the link, and `text` is displayed as link
    text.

**Example**

```python
B.shbLink(100000)
```

### plain ###

Displays the material that corresponds to a node in a simple way.

**Takes**

*   `n` a node of arbitrary type;
*   `linked=True` whether the result should be a link to SHEBANQ
    to the appropriate book/chapter/verse;
*   `withNodes=False` whether node numbers should be displayed;
*   `asString=False` if `False`, displays markdown directly, otherwise returns the
    markdown as a string.

**Returns**

*   the plain node representation in markdown if `asString`, otherwise nothing.

### pretty ###

Displays the material that corresponds to a node in a rich way.

**Takes**

*   `n` a node of arbitrary type;
*   `withNodes=False` whether node numbers should be displayed;
*   `suppress=set()` a set of feature names that should NOT be displayed;

**Returns**

*   the material of the node in rich HTML.

**Details**

If the node is a book or chapter, only the book name (with chapter number) are
displayed. It will be displayed as a link to the same book/chapter in SHEBANQ.

If the node is a verse, the whole verse will be displayed, with some features on
the words.

If the node is a sentence, clause, phrase, etc, then exactly that constituent
will be dislayed.

### plainTuple ###

Displays the material that corresponds to a tuple of nodes in a simple way.

**Takes**

*   `ns` an iterable (list, tuple, set, etc) of arbitrary nodes;
*   `seqNumber` an arbitrary number which will be displayed in a heading above the
    display; this prepares the way for displaying query results, which are a
    sequence of tuples of nodes;
*   `linked=1` the column number where we should add a link to SHEBANQ
    (the first data column is column 1)
*   `withNodes=False` whether node numbers should be displayed;
*   `asString=False` if `False`, displays markdown directly, otherwise returns the
    markdown as a string.

**Returns**

*   the plain tuple representation in markdown if `asString`, otherwise nothing.

### prettyTuple ###

Displays the material that corresponds to a node in a rich way.

**Takes**

*   `ns` an iterable (list, tuple, set, etc) of arbitrary nodes;
*   `seqNumber` an arbitrary number which will be displayed in a heading above the
    display; this prepares the way for displaying query results, which are a
    sequence of tuples of nodes;
*   `item='Result'` is the caption for each displayed item;
*   `withNodes=False` whether node numbers should be displayed;
*   `suppress=set()` a set of feature names that should NOT be displayed;

**Returns**

*   the material of the tuple in rich HTML.

**Details**

We examine all nodes in the tuple. The ones of a higher level than verses will
become just links to SHEBANQ. For all other nodes, we collect all verses in
which they occur. We show all verses, with the occurrences of the nodes in the
tuple highlighted.

### search ###

Searches in the same way as `T.search()`.

**Takes**

*   `query` a TF search string;

**Returns**

*   the results of the query as list; hence you can expect the number of results
    with `len()`.

### table ###

Displays a list of query results. The list is displayed as a compact markdown
table.

**Takes**

*   `results` a list of tuples of nodes, e.g. obtained by `B.search()`;
*   `start=1` a starting point in the result list;
*   `end=len(results)` an end point in the result list;
*   `linked=1` the column number where we should add a link to SHEBANQ
    (the first data column is column 1)
*   `withNodes=False` whether node numbers should be displayed;
*   `asString=False` if `False`, displays markdown directly, otherwise returns the
    markdown as a string.

**Returns**

*   the plain results representation in markdown if `asString`, otherwise nothing.

**Details**

Every result/verse will be preceded by a heading indicating the sequence number
of the result/verse.

### show ###

Displays a list of query results.

**Takes**

*   `results` a list of tuples of nodes, e.g. obtained by `B.search()`;
*   `condensed=True`: condense the results like in SHEBANQ:
    instead of showing all results one by one, we show all verses with all results in it highlighted.
    That way, we blur the distinction between the individual results,
    but it is easier to oversee where the results are;
*   `start=0` a starting point in the result list;
*   `end=len(results)` an end point in the result list;
*   `withNodes=False` whether node numbers should be displayed;
*   `suppress=set()` a set of feature names that should NOT be displayed;

**Returns**

*   a rich display of all results from `start` to `end` but never more than 100 at
    a time.

**Details**

Every result/passage will be preceded by a heading indicating the sequence number of the
result/passage and summary of the tuple of nodes, with or without the node numbers.
