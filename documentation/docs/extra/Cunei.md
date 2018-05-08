Cunei API
=========

About
-----

The module
[cunei.py](https://github.com/Dans-labs/text-fabric/blob/master/tf/extra/cunei.py)
contains a number of handy functions to deal with TF nodes for cuneiform tablets
and
[ATF](http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/inlinetutorial/index.html)
transcriptions of them and [CDLI](https://cdli.ucla.edu) photos and lineart.

See also
[about](https://github.com/Nino-cunei/uruk/blob/master/docs/about.md),
[images](https://github.com/Nino-cunei/uruk/blob/master/docs/images.md),
[transcription](https://github.com/Nino-cunei/uruk/blob/master/docs/transcription.md).

Set up
------

In this repository, *cunei.py* resides in the *programs* directory. In order to
import it into a Jupyter notebook in a completely different directory, we have
to point Python's module path to it:

```python
from tf.extra.cunei import Cunei
```

To use it:

```python
    CN = Cunei('~/github', 'Nino-cunei/uruk', 'test')
    CN.api.makeAvailableIn(globals())
```

It will start Text-Fabric and load all features for you. When `Cunei` is
initializing, it scans the image directory of the repo and reports how many
photos and lineart images it sees.

**Important**

You have to pass `Cunei()` a few bits of information about where things are on
your system. This helps `Cunei()` to find the corpus on your system and to
create links to the online version of your notebook.

*   `~/github`: the directory where your github repositories reside;
*   `Nino-cunei/uruk`: the github repository where the Uruk corpus resides;
*   `test`: the name of your current notebook (without the `.ipynb` extension).

**NB:**

Your current notebook can be anywhere on your system. `Cunei()` can find its
location, but not its name, hence you have to pass its name.

Usage
-----

Now you can call the methods of *cunei*, as follows. One of the methods is
`getOuterQuads(node)`. To call it, say

```python
outerQuads = CN.getOuterQuads(line)
```

API
---

### getSource ###

Delivers the transcription source of a node. This works for the higher level
nodes that correspond to one or more source lines: tablets, faces, columns,
comments, cases (only the lowest level cases that correspond to numbered
transcription lines).

**Takes**

*   `node` the node for which the source lines should be retrieved;
*   `nodeType=None` only fetch source lines for sub-nodes of this type;
*   `lineNumbers=False` add line numbers to the result, these numbers say where
    the source line occurs in the source file;

**Returns**

*   a list of source lines (strings).

**Implementation details**

The conversion of ATF to Text-Fabric has saved the original source lines and
their line numbers in the features `srcLn` and `srcLnNum` respectively. This
function makes use of those features.

### atfFromSign ###

Reproduces the ATF representation of a sign.

**Takes**

*   `n` a node; must have node type `sign`;
*   `flags=False` whether flags will be included;

**Returns**

*   a string with the ATF representation of the sign.

### atfFromQuad ###

Reproduces the ATF representation of a quad.

**Takes**

*   `n` a node; must have node type `quad`;
*   `flags=False` whether flags will be included;
*   `outer=True` whether the quad is to be treated as an outer quad;

**Returns**

*   a string with the ATF representation of the quad.

### atfFromOuterQuad ###

Reproduces the ATF representation of an outer quad *or* sign.

If you take an ATF transcription line with linguistic material on it, and you
split it on white space, and you forget the brackets that cluster quads and
signs, then you get a seuqence of outer quads and signs.

If you need to get the ATF representation for these items, this function does
conveniently produce them. You do not have to worry yourself about the sign/quad
distinction here.

**Takes**

*   `n` a node; must have node type `quad` or `sign`;
*   `flags=False` whether flags will be included;

**Returns**

*   a string with the ATF representation of the outer quad.

### atfFromCluster ###

Reproduces the ATF representation of a cluster. Clusters are bracketings of
quads that indicate proper names, uncertainty, or supplied material. In ATF they
look like `( )a` or `[ ]` or `< >`

**Takes**

*   `n` a node; must have node type `cluster`;
*   `seen=None` set of signs that already have been done;

**Returns**

*   a string with the ATF representation of the cluster. Sub-clusters will also be
    represented. Signs belonging to multiple nested clusters will only be
    represented once.

### getOuterQuads ###

Collects the outer quads and isolated signs under a node. Outer quads and
isolated signs is what you get if you split line material by white space and
remove cluster brackets.

**Takes**

*   `n` a node; typically a tablet, face, column, line, or case. This is the
    container of the outer quads;

**Returns**

*   a list of nodes, each of which is either a sign or a quad, and, in both cases,
    not contained in a bigger quad. The order of the list is the natural order on
    nodes: first things first, and if two things start at the same time: bigger
    things first.

**Implementation details**

A quad or sign is outer, if it is not the "sub" of an other quad. We can see
that by inspecting the **sub** edges that land into a quad or sign:
`E.sub.t(node)`.

However, there might be *clusters* around the node, and such a cluster will have
an outgoing **sub** edge to the node. Hence we should test whether all incoming
**sub** edges are not originating from an other quad.

### nodeFromCase ###

Very much like the built-in
[T.nodeFromSection](https://github.com/Dans-labs/text-fabric/wiki/Api#sectioning)
of Text-Fabric. It gives you a node, if you specify a terminal case, i.e. a
transcription line.

**Takes**

*   a 3-tuple `(` *tabletNumber*, *face*:*columnNumber*, *hierarchical line
    number* `)`; the hierarchical number may contain the original `.` that they
    often have in the transcriptions, but you may also leave them out;

**Returns**

*   the corresponding node, which will be of a terminal *case*, having as
    **fullNumber** the value you supplied as *hierarchical line number*. If no
    such node exists, you get `None` back.

### caseFromNode ###

Very much like the built-in
[T.sectionFromNode](https://github.com/Dans-labs/text-fabric/wiki/Api#sectioning)
of Text-Fabric. It gives you a section tuple, if you give it a node. If the node
corresponds to something inside a transcription line, it will navigate to up to
the terminal case or line in which it is contained, and use its number.

**Takes**

*   the node of a terminal case (these are the cases that have a full hierarchical
    number; these cases correspond to the individual numbered lines in the
    transcription sources;

**Returns**

*   a 3-tuple `(` *tabletNumber*, *face*:*columnNumber*, *hierarchical line
    number* `)`; the hierarchical number will not contain `.`s.

### lineFromNode ###

If called on a node corresponding to something inside a transcription line, it
will navigate to up to the terminal case or line in which it is contained, and
return that node.

**Takes**

*   a node

**Returns**

*   `None` if node correpsonds to something bigger than what is expressed on a
    single transcription line; otherwise it returns the node corresponding to the
    transcription line of the thing expressed by the node, which is a terminal
    line or a terminal case.

### casesByLevel ###

Grabs all (sub)cases of a specified level. You can choose to filter the result
to those (sub)cases that are *terminal*, i.e. those which do not contain
subcases anymore. Such cases correspond to individual lines in the ATF.

**Takes**

*   a positive integer, indicating the level of (sub)cases you want. `1` is
    top-level cases, `2` is subcases, `3` is subsubcases, and so on;
*   `terminal=True`. If `True`, only subcases that have the feature `terminal`
    are delivered (so only terminal subcases). Otherwise, all cases of that level
    will be delivered.

### cdli ###

Delivers a link to a tablet page on CDLI, to be placed in an output cell.

**Takes**

*   a node of type `tablet` or a P-number;
*   an optional `linkText=None` with the text of the link; if None, the P-number
    of the tablet will be used.
*   `asString=False` if `False`, displays the formatted results directly, otherwise returns the
    HTML as a string.

**Returns**

*   a HTML link to CDLI, down to the page of this individual tablet.

### tabletLink ###

Produces a link to a tablet on CDLI.

**Takes**

*   an arbitrary node;
*   `text=None` optional link text;
*   `asString=False` if `False`, displays the formatted results directly, otherwise returns the
    HTML as a string.

**Returns**

*   a hyperlink to CDLI, to the page of the individual tablet of which the node is
    part. The text of the link the contents of the `text` parameter if it is
    given, else it is the p-number of the tablet.

**Example**

```python
CN.tabletLink(10000)
```

### plain ###

Displays the material that corresponds to a node in a simple way.

**Takes**

*   `n` a node of arbitrary type;
*   `linked=True` whether the result should be a link to the CDLI page of the
    containing tablet
*   `lineart=True` whether to display a lineart image in addition (only relevant
    for signs and quads)
*   `withNodes=True` whether node numbers should be displayed;
*   `lineNumbers=True` whether corresponding line numbers in the ATF source should
    be displayed;
*   `asString=False` if `False`, displays markdown directly, otherwise returns the
    markdown as a string.

**Returns**

*   the plain node representation in markdown if `asString`, otherwise nothing.

### pretty ###

Displays the material that corresponds to a node in a rich way.

**Takes**

*   `n` a node of arbitrary type;
*   `lineart=True` whether to display a lineart image in addition (only relevant
    for signs and quads)
*   `withNodes=True` whether node numbers should be displayed;
*   `lineNumbers=True` whether corresponding line numbers in the ATF source should
    be displayed;
*   `suppress=set()` a set of feature names that should NOT be displayed;
*   `highlights=set()` a set of nodes that should be highlighted;

**Returns**

*   the material of the node in rich HTML.

### plainTuple ###

Displays the material that corresponds to a tuple of nodes in a simple way.

**Takes**

*   `ns` an iterable (list, tuple, set, etc) of arbitrary nodes;
*   `seqNumber` an arbitrary number which will be displayed in a heading above the
    display; this prepares the way for displaying query results, which are a
    sequence of tuples of nodes;
*   `linked=1` the column number where we should add a link to the CDLI page of
    the containing tablet (the first data column is column 1)
*   `lineart=True` whether to display a lineart image in addition (only relevant
    for signs and quads)
*   `withNodes=True` whether node numbers should be displayed;
*   `lineNumbers=True` whether corresponding line numbers in the ATF source should
    be displayed;
*   `asString=False` if `False`, displays markdown directly, otherwise returns the
    markdown as a string.

**Returns**

*   the plain tuple representation in markdown if `asString`, otherwise nothing.

### prettyTuple ###

Displays the material that corresponds to a tuple of nodes in a rich way.

**Takes**

*   `ns` an iterable (list, tuple, set, etc) of arbitrary nodes;
*   `seqNumber` an arbitrary number which will be displayed in a heading above the
    display; this prepares the way for displaying query results, which are a
    sequence of tuples of nodes;
*   `item='Result'` is the caption for each displayed item;
*   `lineart=True` whether to display a lineart image in addition (only relevant
    for signs and quads)
*   `withNodes=True` whether node numbers should be displayed;
*   `lineNumbers=True` whether corresponding line numbers in the ATF source should
    be displayed;
*   `suppress=set()` a set of feature names that should NOT be displayed;

**Returns**

*   the material of the tuple in rich HTML.

**Details**

We examine all nodes in the tuple. We collect and show all tablets in which they
occur and highlight the material corresponding to the nodes in all tuples.

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

*   `results` a list of tuples of nodes, e.g. obtained by `CN.search()`;
*   `start=1` a starting point in the result list;
*   `end=len(results)` an end point in the result list;
*   `linked=1` the column number where we should add a link to the CDLI page of
    the containing tablet (the first data column is column 1)
*   `lineart=True` whether to display a lineart image in addition (only relevant
    for signs and quads)
*   `withNodes=True` whether node numbers should be displayed;
*   `lineNumbers=True` whether corresponding line numbers in the ATF source should
    be displayed;
*   `asString=False` if `False`, displays markdown directly, otherwise returns the
    markdown as a string.

**Returns**

*   the plain results representation in markdown if `asString`, otherwise nothing.

**Details**

Every result/tablet will be preceded by a heading indicating the sequence number
of the result/tablet.

### show ###

Displays a list of query results. Every result is displayed in tablet context in
rich HTML.

**Takes**

*   `results` a list of tuples of nodes, e.g. obtained by `CN.search()`;
*   `condensed=True`: condense the results: instead of showing all results one by
    one, we show all tablets with all results in it highlighted. That way, we blur
    the distinction between the individual results, but it is easier to oversee
    where the results are.
*   `start=1` a starting point in the result list;
*   `end=len(results)` an end point in the result list;
*   `lineart=True` whether to display a lineart image in addition (only relevant
    for signs and quads)
*   `withNodes=True` whether node numbers should be displayed;
*   `lineNumbers=True` whether corresponding line numbers in the ATF source should
    be displayed;
*   `suppress=set()` a set of feature names that should NOT be displayed;

**Returns**

*   a rich display of all results from `start` to `end` but never more than 100 at
    a time.

**Details**

Every result/tablet will be preceded by a heading indicating the sequence number
of the result/tablet and summary of the tuple of nodes, with or without the node
numbers.

### photo and lineart ###

Fetches photos or linearts for tablets, signs or quads, and returns it in a way
that it can be embedded in an output cell. The images that show up are clickable
and link through to an online, higher resolution version on CDLI. Images will
have, by default, a caption that links to the relevant page on CDLI.

**Takes**

*   one or more **nodes**; as far as they are of type `tablet`, `quad` or `sign`,
    a photo or lineart will be looked up for them; instead of a node you may also
    supply the P-number or the name of the sign or quad;
*   an optional **key** (a string), specifying which of the available images for
    this node you want to use; if you want to know which keys are available for a
    node, supply `key='xxx'`, or any non-existing key;
*   an optional `asLink=True`: no image will be placed, only a link to the online
    image at CDLI; in this case the **caption** will be suppressed, unless
    explicitly given;
*   an optional `withCaption='bottom'` to control whether a CDLI link to the
    tablet page must be put under the image. You can also specify `top` `left`
    `right`. If left out, no caption will be placed.
*   an optional list of key=value **options**, such as `width=100`, `height=200`.

The result will be returned as a *row* of images. Subsequent calls to `photo()`
and `lineart()` will result in vertically stacked rows. So you can control the
two-dimensional layout of your images.

**Details**

The optional parameters `height` and `width` control the height and width of the
images. The value should be a valid
[CSS](https://developer.mozilla.org/en-US/docs/Web/CSS/length) length, such as
`100px`, `10em`, `32vw`. If you pass an integer, or a decimal string without
unit, your value will be converted to that many `px`.

These parameters are interpreted as setting a maximum value (in fact they will
end up as `max-width` and `max-height` on the final `<img/>` element in the
HTML.

So if you specify both `width` and `height`, the image will be placed in tightly
in a box of those dimensions without changing the aspect ratio.

If you want to force that the width of height you pass is completely consumed,
you can prefix your value with a `!`. In that case the aspect ratio maybe
changed. You can use the `!` also for both `height` and `width`. In that case,
the rectangle will be completely filled, and the aspect ratio will be adjusted
to that of the rectangle.

The way the effect of the `!` is achieved, is by adding `min-width` and
`min-height` properties to the `<img/>` element.

**Implementation details**

The images will be called in by a little piece of generated HTML, using the
`<img/>` tag. This only works if the image is within reach. To the images will
be copied to a sister directory of the notebook. The name of this directory is
`cdli-imagery`. It will be created on-the-fly when needed. Copying will only be
done if needed. The names of the images will be changed, to prevent problems
with systems that cannot handle `|` and `+` characters in file names well.

### imagery ###

Provides the sets of available images (locally).

**Takes**

*   **objectType**: the type of thing: `ideograph` or `tablet`;
*   **kind**: the kind of image: `photo` or `lineart`;

**Returns**

*   the set of available names in that category for which there is an image; for
    tablets, it lists the P-numbers; for sign/quads: the ATF representaitons.
