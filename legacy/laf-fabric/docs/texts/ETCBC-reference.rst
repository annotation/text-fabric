ETCBC Reference
###############

.. caution::
    LAF-Fabric has a successor: 
    `Text-Fabric <https://github.com/ETCBC/text-fabric/wiki>`_.
    LAF-Fabric stays around in order to run legacy notebooks.
    It is recommended to use **Text-Fabric** for new work.

======================================================== =============================================================================================================
:ref:`- L: Layers <layers>`                              How objects lie embedded in each other
:ref:`- T: Texts <texts>`                                Representing texts in different formats
:ref:`- Node Order <node_order>`                         A convenient ordering of nodes
:ref:`- Transcription <transcription>`                   Low-level transliteration functions
:ref:`- Trees <trees>`                                   Tree generation
:ref:`- Annotating <annotating>`                         Create data entry forms for new annotations and process the filled in forms
:ref:`- Extra data <extra_data>`                         Create new annotations out of other data sources, among which certain ETCBC files related to the core data
:ref:`- Feature Documentation <feature_documentation>`   Produce frequency lists for all features, to be included in the feature documentation
:ref:`- MQL <mql>`                                       MQL query execution.
======================================================== =============================================================================================================

What is ETCBC
=============
The *etcbc* package has modules that go beyond *laf*.
They utilize extra knowledge of the specific LAF resource which is the ETCBC Hebrew Text Database.
They make available a better ordering of nodes, add more ways of querying the data, and ways of creating new annotations.
There is also a solution for the problem of getting relevant context around a node.
For example, if you do a walk through phrases, you want to be able to the clauses that contain the phrases that you iterate over,
or to siblings of it.

Most of the functionality is demonstrated in dedicated notebooks. This text is only a rough overview.

.. _layers:

Layers
======
The ``L`` (*layer*) part of the API enables you to find objects that are embedded in other objects and vice versa.
It makes use of the ETCBC object types ``book``, ``chapter``, ``verse``, ``half_verse``, ``sentence``, ``sentence_atom``,
``clause``, ``clause_atom``, ``phrase``, ``phrase_atom``, ``subphrase``, ``word``.
An object of a certain type may contain objects of types following it, and is contained by objects of type preceding it.

By means of ``L`` you can go from an object to any object that contains it, and you can get lists of objects contained in it.
This is how it works. You have to import the ``prepare`` module::

    from etcbc.preprocess import prepare

and say in your load instructions::

    ``'prepare': prepare``
    
Then you can use the following functions::

    L.u(otype, node)
    L.d(otype, node)
    L.p(otype, book='Genesis', chapter=21, verse=3, sentence=1, clause=1, phrase=1)

``L.u`` (up in the hierarchy) gives you the object of type ``otype`` that contains ``node`` (in the ETCBC data there is at most one such an object).
If there is no such object, it returns ``None``.

``L.d`` (down in the hierarchy) gives you all objects of type ``otype`` that are contained in ``node`` as a list in the natural order.
If there are no such objects you get ``None``.

``L.p`` (passage nodes) give you all objects of type ``otype`` that are contained in the nodes selected by the other arguments.
All other arguments are optional. So if you leave out the ``sentence clause phrase`` arguments, you get all nodes in a specific verse.
If you leave out the ``book chapter verse`` arguments, and leave the others at ``1``, you get the nodes in all first phrases of first
clauses of first sentences of all verses of all chapters of all books. 

Examples (if ``phr`` is a node with object type ``phrase``)::

    b = L.u('book', phr)                  # the book node in which the node occurs
    F.book.v(b)                           # the name of that book

    b = F.code.v(L.u('clause_atom', phr)) # the *clause_atom_relationship* of the clause_atom of which the phrase is a part

It is now easy to get the full text contained in any object, e.g. the phrase ``phr``::

    ''.join('{}{}'.format(F.g_word_utf8.v(w), F.trailer_utf8.v(w)) for w in L.d(phr)) 

Conversely, it is easy to get all subphrases in a given verse::

    subphrases = L.p('subphrase', book='Exodus', chapter=5, verse=10)

or get all clause_atoms of all first sentences of all second verses of all chapters in Genesis::

    clause_atoms = L.p('clause_atom', book='Genesis', verse=2, sentence=1)

.. _texts:

Texts
=====
The ``T`` (*text*) part of the API is for working with the plain text of the Bible.
It can deliver the text of the whole Bible or parts in a variety of formats.

.. note::
    LAF-Fabric and SHEBANQ have been designed for Hebrew text.
    However, we are currently paving the way for LAF-Fabric to also work with Greek texts.
    This API has undergone changes (backward compatible) to also work with Greek.
    All ``T`` functions are sensitive to the value of a parameter called ``biblang``.
    By default this value is ``Hebrew`` and then everything works for Hebrew texts,
    Hebrew representations, and book names of the Hebrew Bible.

    However, if ``biblang`` is ``Greek``, the ``T`` functions recognize Greek representations
    and book names of the Greek New Testament.

    This parameter can be passed in the load specifications, under ``prepare`` below.

The quickest way to see how this works is to go to the notebook
`plain <https://shebanq.ancient-data.org/static/docs/tools/shebanq/plain.html>`_
(`download <https://shebanq.ancient-data.org/static/docs/tools/shebanq/plain.html>`_)
on SHEBANQ.

This is how it works. You have to import the ``prepare`` module. This is how it works for Hebrew::

    from etcbc.preprocess import prepare

and say in your load instructions::

    'prepare': prepare
    
which is shorthand for::

    from etcbc.preprocess import prep

    'prepare': prep(biblang='Hebrew')
    
And this is how it works for Greek::

    from etcbc.preprocess import prep

and say in your load instructions::

    'prepare': prep(biblang='Greek')
    
By the way: if you do want to load the `L` API, but not the `T` API or vice versa,
you can specify that by means of an other optional argument *select* to `prep()`.
*select* is either absent, and then all APIs are loaded, or it is a set of APIs to load::

    'prepare': prep(select={'L', 'T'}) # same as prep(select=None) if L and T are the only APIs in the system.
    'prepare': prep(select={'L'})
    'prepare': prep(select={'T'})
    'prepare': prep(select=set())

When this is said and done, you can use the following functions

.. code-block:: python

    T.node_of(book, chapter, verse, lang='en')

Yields the verse node of the passage specified by ``book``, ``chapter`` and ``verse``.
The book is specified in the given language, with default ``en`` = English.

.. code-block:: python

    my_node = T.node_of('Mwanzo', 1, 1, lang='sw')

gives the verse node of Genesis 1:1 (*Mwanzo* is the Swahili name for *Genesis*).

To see the available languages for Bible book names, say

.. code-block:: python

    T.langs

``T.node_of`` yields ``None`` if there is no such verse.

See also the methods ``book_name()`` and ``book_node()`` below to map a book name to a book node and vice versa.

.. code-block:: python

    T.formats()

This yields a dictionary of all formats for biblical text that the ``T`` API is capable to deliver.
The keys are acronymns for the formats, the values are tuples
``(desc, method)``
where ``desc`` is a short description of the format, and ``method`` is a Python function that delivers that representation given a single word node.

Hebrew formats
--------------
**Hebrew unicode output**

* ``hp`` with vowels and accents as in primary text (based on ketivs instead of qeres) 
  (this corresponds to the primary text in the LAF data)
* ``hpl`` with vowels and accents as in primary text (based on ketivs instead of qeres) 
  but here vocalized lexemes are used, instead of the inflected text forms; no lexeme disambiguation marks
* ``hcl`` consonantal lexemes (based on ketivs instead of qeres) 
  but here vocalized lexemes are used, instead of the inflected text forms; no lexeme disambiguation marks
* ``ha`` with vowels and accents (based on qeres) 
  (from now on everything is based on replacing ketivs by their pointed qeres)
* ``hv`` with vowels but not accents
  (the points on the s(h)in all still there)
* ``hc`` consonantal
  (no pointed s(h)ins anymore, and no special forms for final consonants, no setumah, petuhah and nun hafukha and the
  end of verses)

**ETCBC transliterated output**
Consult the `ETCBC transliteration table <https://shebanq.ancient-data.org/static/docs/ETCBC4-transcription.pdf>`_
for details. The same subtleties apply as for the Hebrew case.

* ``ep`` with vowels and accents as in primary text (based on ketivs instead of qeres)
* ``epl`` with vowels and accents as in primary text (based on ketivs instead of qeres) 
  but here vocalized lexemes are used, instead of the inflected text forms; no lexeme disambiguation marks
* ``ecl`` consonantal lexemes (based on ketivs instead of qeres); lexeme disambiguation marks are present here 
* ``ea`` with vowels and accents
* ``ev`` with vowels but not accents
* ``ec`` consonantal

**Phonemic outputs**

* ``pf`` full details: schwa and qamets gadol/qatan distinction
* ``ps`` simplified: no schwa and qamets gadol/qatan distinction
  (also the composite schwas have gone)

Greek formats
-------------

**Greek unicode output**

* ``gp`` with and accents as in primary text
  (this corresponds to the primary text in the LAF data)

.. code-block:: python

    T.words(word_nodes, fmt=None)

Give the plain text belonging to a series of words in format ``fmt``.
Default format is ``ha`` if `biblang` is `Hebrew` and `gp` if `biblang` is `Greek`,
i.e. (Hebrew) fully pointed Hebrew Unicode, where ketivs have been replaced by 
fully pointed qeres.
The ``word_nodes`` can be any iterable of nodes carrying ``otype = 'word'``.
They do not have to correspond to consecutive words in the bible.

.. code-block:: python

    T.text(book=None, chapter=None, verse=None, otype=None fmt='ha', html=False, verse_label=True, lang='en', style=None):

Give the contents of the indicated passages, either as list of objects of type ``otype`` or as text in format ``fmt``. 

**Passage selection**
You can pass values for books, chapters and verses. You can omit them as well, in that case all possible values are taken.
Like in ``node_of()``, ``book`` must be given as a name in the language specified by ``lang``.
See the methods ``book_name()`` and ``book_node()`` below to map a book name to a book node and vice versa.
For ``chapter`` and ``verse`` specify values as numbers, either as integers or as string representations.

More over, you can specify multiple values for ``book``, ``chapter``, and ``verse``.
Instead of a single value, you can supply any iterable, such as lists, tuples, and sets.
In that case, use integers for chapters and verses.
If the iterable has order, the output will respect that order.

**Result as objects**
If you pass the ``otype`` parameter with a valid object type, your result will be the list of objects of that type that corresponds
to the passages you have selected. Note that if you ask for objects, you get all objects that have a non-empty intersection with
the verses you have selected. So if clauses or phrases span across verse boundaries, they will delivered if one of the verses involved is
in the selection.

**Formatting as text**
If you pass the ``fmt`` parameter, you get the plain or html text content of the selected verses.
The parameter ``verse_label`` indicates whether to include verse labels (like ``Genesis 3:7``) in front of each verse.

If ``html`` is ``True`` then the result is formatted as a series of  html tables, with the right style characteristics.
You can still tweak the styles a bit, see the function ``T.style()`` later on.

If you pass the parameter ``style`` with the result of ``T.style()`` as value, a complete HTML document will be generated.
If you leave this parameter out, no HTML header will be generated.
It is your responsibility to combine stylesheet and HTML into a complete document, if you want to.
Alternatively, you can display the HTML directly in a Jupyter notebook code cell.
If you run ``T.style()`` the inline HTML will be styled accordingly.

**Examples**

* ``T.text()`` :
  All books, chapters, verses in the standard order, plain text, accented Hebrew based on pointed qeres, no verse labels;
* ``T.text(book='Mwanzo', chapter=1, verse=1, fmt='hc', html=True, verse_label=True, lang='sw')`` :
  The verse Genesis 1:1, in HTML, consonantal Hebrew, with verse labels;
* ``T.text(book='Genesis', chapter=1, html=True, verse_label=True, style=T.style(hebrew_color='ff0000'))`` :
  The chapter Genesis 1, as a complete HTML document, in accented Hebrew in red color, with verse labels;
* ``T.text(book='Genesis')`` :
  The whole book of Genesis, in plain text, accented Hebrew, no verse labels;
* ``T.text(chapter=1)`` :
  The first chapter of all books;
* ``T.text(verse=2)`` :
  The second verse of all chapters of all books
* ``T.text(book=['Exodus', 'Genesis'], chapter=[7,6,5], verse=[8,4,16])``: 
  The following sequence of verses: Ex 7:8,4,16; 6:8,4,16; 5:8,4,16; Gen 7:8,4,16; 6:8,4,16; 5:8,4,16;
* ``T.text(chapter=4, verse=17, otype='phrase')``: 
  All phrases that occur in chapter 4 verse 17 throughout the whole Hebrew Bible.
     
.. code-block:: python

    T.style(params=None, show_params=False)

Generate a css style sheet to format the HTML output of ``T.verse()``.
You can tweak certain parameters.
In order to see which parameters, just run the function with ``show_params=True``.
It will list all tweakable parameters with their default values.

In short, you can customize the font sizes and colors for the text, and you can give distinct values for Hebrew Unicode, ETCBC ASCII, en phonemic representation.
You can also set the widths of the label columns.

You only have to pass the parameters that you want to give a non-default value.

.. code-block:: python

    T.book_name(book_node, lang='en')

Returns the book name of the book corresponding to ``book_node`` in language ``lang``.

.. code-block:: python

    T.book_node(book_name, lang='en')

Returns the book node of the book with name ``book_name`` in language ``lang``.

If ``lang`` is ``la`` (latin), the book names are exactly as used in the ETCBC database.

Supported languages:

* en = English (default)
* nl = Dutch
* de = German
* fr = French
* el = Greek
* he = Hebrew (modern)
* la = Latin (used in the ETCBC database).

and quite a bit more.

For the list of all languages, call 

.. code-block:: python

    T.langs

.. code-block:: python

    T.booknames

All book names in all available languages

.. code-block:: python

    T.book_nodes

For convenience, the tuple of nodes corresponding to the books in the ETCBC order.

.. _node_order:

.. code-block:: python

    T.passage(node, lang='en', first_word=False)

Returns the passage indicator where node occurs in the format ``book chapter:verse``
where ``book`` is returned in the language ``lang``.
If ``first_word`` is ``True``, then the passage returned corresponds to the passage of the first word of the node.
Otherwise the following rules apply:

* if the node type is book or chapter, the verse part is left out, and if the node type is book, the chapter part is left out as well,
* if the node spans several verses, the verse is given as a range.

Node order
==========
The module ``etcbc.preprocess`` takes care of preparing a table that codes the optimal node order for working with ETCBC data. 

It orders the nodes in a way that combines the left-right ordering with the embedding ordering.
Left comes before right, and the embedder comes before the embedded.

More precisely: if we want to order node *a* and *b*, consider their monad sets *ma* and *mb*, and their object types *ta* and *tb*.
The object types have ranks, going from a low rank for books, to higher ranks for chapters, verses, half_verses, sentences, sentence_atoms,
clauses, clause_atoms, phrases, phrase_atoms, subphrases and words.

In the ETCBC data every node has a non-empty set of monads.

If *ma* is equal to *mb* and *ta* is equal to *tb*, then *a* and *b* have the same object type,
and cover the same monads, and in the etcbc that implies 
that *a* and *b* are the same node.

If *ma* is equal to *mb*, then if *ta* is less than *tb*, *a* comes before *b* and vice versa.

If *ma* is a proper subset of *mb*, then *a* comes *after* *b*, and vice versa.

If none of the previous conditions hold, then *ma* has monads not belonging to *mb* and vice versa.
Consider the smallest monads of both difference sets: *mma* = *min(ma-mb)* and *mmb = min(mb-ma)*.
If *mma* < *mmb* then *a* comes before *b* and vice versa.
Note that *mma* cannot be equal to *mmb*.

Back to your notebook. Say::

    from etcbc.preprocess import prepare

    processor.load('your source', '--', 'your task',
        {
            "xmlids": {"node": False, "edge": False},
            "features": { ... your features ...},
            "prepare": prepare,
        }
    )

then the following will happen:

* LAF-Fabric checks whether certain data files that define the order between nodes exist next to the binary compiled data, and whether these files
  are newer than your module *preprocess.py*.
* If so, it loads these data files quickly from disk.
* If not, it will compute the node order and write them to disk.  This may take some time! Then it replaces the *dumb* standard
  ordering by the *smart* ETCBC ordering.
* Likewise, it looks for computed files with the embedding relationship, and computes them if necessary.
  This takes even more time!

This data is only loaded
if you have done an import like this::

    from etcbc.preprocess import prepare

and if you have::

    'prepare': prepare

in your load instructions,

.. _transcription:

Transcription
=============
Hebrew
------
The ETCBC has a special way to transcribe Hebrew characters into latin characters.
Sometimes it is handier to work with transcriptions, because some applications do not render texts with mixed writing directions well.

In *etcbc.lib* there is a conversion tool. This is how it works::

    from etcbc.lib import Transcription

    tr = Transcription()

    t = 'DAF DAC'
    h = Transcription.to_hebrew(t)
    hv = Transcription.to_hebrew_v(t)
    hc = Transcription.to_hebrew_c(t)
    ev = Transcription.to_etcbc_v(t)
    ec = Transcription.to_etcbc_c(t)
    tb = tr.from_hebrew(h)
    
    if not Transcription.suppress_space(t):
        t += ' '

    print("{}\n{}\n{}".format(t, h, tb))

``to_hebrew`` maps from transcription to Hebrew characters, ``from_hebrew`` does the opposite.

``to_etcbc_v`` and ``to_hebrew_v`` strip accent pointing, but leave punctuation and vowel pointing and dagesh.
More precisely, the sof pasuq (unicode 05c3) is preserved.

``to_etcbc_c`` and ``to_hebrew_c`` strip all accent and vowel pointing, including the dagesh, and convers pointed shin and sin to pointless shin.
Punctuation is preserved.

The ``hebrew_``.. functions yield their result in Hebrew Unicode, the ``etcbc_`` ones in the ETCBC transliteration.

``ph_simplify`` simplifies a phonemic transcription by removing all accents and schwas (including the composite ones) and masora signs,
and translating both qamets qatan (o) and gadol (ā) to å.

``suppress_space(t)`` inspects an ETCBC transcription and yields True if there should be no space between this word and the next.

There are some points to note:

* if characters to be mapped are not in the domain of the mapping, they will be left unchanged.
* there are two versions of the shin, each consists of two combined unicode characters.
  Before applying the mappings, these characters will be combined into a single character.
  After applying the mapping ``hebrew()``, these characters will be *always* decomposed.
* up till now we have only transcription conversions for *consonantal Hebrew*.

.. note::
    The ETCBC transcription is *easy* in the sense that it is 1-1 correspondence between the transcription and the Hebrew.
    (There are one or two cases where the ETCBC transcription distinguishes between accents that are indistiguishable
    in UNICODE.

    A *phonemic* transcription is also available, but it has been computed at a later stage, and added as an
    extra annotation package to the data.
    This is a *difficult* transcription, since a lot of complicated rules govern the road from spelling to 
    pronunciation, such as qamets gadol versus qatan, schwa mobile versus quiescens, to name but a few.

.. hint::
    It is likely that you never have to use these functions directly in your notebook.
    Try first how far you get with the ``T``-functions in 
    :ref:`Texts <texts>`.

Syriac
------
We have a transcription for consonantal Syriac. The interface is nearly the same as for Hebrew, but now use::

    to_syriac(word)
    from_syriac(word)

.. _trees:

Trees
=====
The module *etcbc.trees* gives you several relationships between nodes:
*parent*,  *children*, *sisters*, and *elder_sister*.::

    from etcbc.trees import Tree

    tree = Tree(API, otypes=('sentence', 'clause', 'phrase', 'subphrase', 'word'), 
        clause_type='clause',
        ccr_feature='rela',
        pt_feature='typ',
        pos_feature='sp',
        mother_feature = 'mother',
    )
    ccr_class = {
        'Adju': 'r',
        'Attr': 'r',
        'Cmpl': 'r',
        'CoVo': 'n',
        'Coor': 'x',
        'Objc': 'r',
        'PrAd': 'r',
        'PreC': 'r',
        'Resu': 'n',
        'RgRc': 'r',
        'Spec': 'r',
        'Subj': 'r',
        'NA':   'n',
    }
    
    tree.restructure_clauses(ccr_class)

    results = tree.relations()
    parent = results['rparent']
    sisters = results['sisters']
    children = results['rchildren']
    elder_sister = results['elder_sister']

When the ``Tree`` object is constructed, the monadset-embedding relations that exist between the relevant objects, will be used
to construct a tree.
A node is a parent of another node, which is then a child of that parent, if the monad set of the child is contained in the
monad set of the parent, and if there are not intermediate nodes (with respect to embedding) between the parent and the child.
So this *parent* relationship defines a *tree*, and the *children* relationship is just the inverse of the *parent* relationship.
Every node has at most 1 parent, but nodes may have multiple children.
If two nodes have the same monad set, then the object type of the nodes determines if one is a parent and which one that is.
A sentence can be parent of a phrase, but not vice versa.

It can not be the case that two nodes have the same monad set and the same object type.

You can customize your trees a little bit, by declaring a list of object types that you want to consider.
Only nodes of thos object types will enter in the parent and children relationships.
You should specify the types corresponding to the ranking of object types that you want to use.
If you do not specify anything, all available nodes will be used and the ranking is the default ranking, given in 
*etcbc.lib.object_rank*.

There is something curious going on with the *mother* relationship, i.e. the relationship that links on object to another on which it is
linguistically dependent. In the trees just constructed, the mother relationship is not honoured, and so we miss several kinds of
linguistic embeddings.

The function ``restructure_clauses()`` remedies this. If you want to see what it going on, consult the 
`trees_etcbc4 notebook <http://nbviewer.ipython.org/github/ETCBC/laf-fabric-nbs/blob/master/trees/trees_etcbc4.ipynb>`_.

.. _annotating:

Annotating
==========
The module ``etcbc.annotating`` helps you to generate data entry forms and translate filled in forms into new annotations in LAF format,
that actually refer to nodes and edges in the main ETCBC data source.

There is an example notebook that uses this module for incorporating extra data (coming from so-called *px* files) into the LAF resource.
See *Extra Data* below.

.. _extra_data:

Extra Data
==========
The ETCBC data exists in so-called *px* files, from which the EMDROS databases are generated.
Some *px* data did not made it too EMDROS, hence this data does not show up in LAF.
Yet there might be useful data in the *px*. The module **etcbc.extra** helps to pull that data in, and delivers it in the form
of an extra annotation package.

You can also use this module to add other kinds of data.
You only need to write a function that delivers the data in the right form, and then *extra* turns it into a valid annotation set.

Usage::

    import laf
    from laf.fabric import LafFabric
    from etcbc.extra import ExtraData
    fabric = LafFabric()

    API=fabric.load(...) # load the data and features

    xtra = ExtraData(API)

    xtra.deliver_annots(annox, metadata, sets)

where ``sets`` is a list of tuples::

    (data_base, annox_part, read_method, specs)

The result is a new annox, i.e. a set of annotations, next to the main data.
Its name is given in the *annox* parameter.
Its metadata consists of a dicionary, containing a key ``title`` and a key ``data``.
Its actual annotations are divided in sets, which will be generated from various data sources.
Each *set* is specified by the following information:

* ``data_base`` is a relative path within the LAF data directory to a file containing the raw data for a set of annotations;
* ``annox_part`` is a name for this set;
* ``read_method`` is a function, taking a file path as argument. It then reads that file, and delivers a list of data items,
  where each data item is a tuple consisting of a node and additional values.
  The node is the target node for the values, which will be values of features to be specified in the *specs*.
  This method will be called with the file specified in the *data_base* argument;
* ``specs`` is a series of tuples, each naming a new feature in the new annotation set.
  The tuple consists of the *namespace*, *label*, and *name* of the new feature.
  The number of feature specs must be equal to the number of additional values in the data list that is delivered by *read_method*.

When *deliver_annots* is done, the new annox can be used straight away.
Note that upon first use, the XML of this annox has to be parsed and compiled into binary data, which might take a while.

To see this method in action, have a look at the
`lexicon notebook <https://shebanq.ancient-data.org/shebanq/static/docs/tools/shebanq/lexicon.html>`_.

.. _feature_documentation:

Feature documentation
=====================
The module ``etcbc.featuredoc`` generates overviews of all available features in the main source, including information of their values,
how frequently they occur, how many times they are filled in with (un)defined values.
It can also look up examples in the main data source for you.

Usage::

    from etcbc.featuredoc import FeatureDoc

More info:
`notebook feature-doc <http://nbviewer.ipython.org/github/ETCBC/laf-fabric-nbs/blob/master/featuredoc/feature-doc.ipynb>`_

.. _mql:

MQL
===
The module ``etcbc.mql`` lets you fire mql queries to the corresponding Emdros database, and process the results with LAF-Fabric.

This function is dependent on Emdros being installed.
More info over what MQL, EMDROS are, and how to use it, is in 
`notebook mql <http://nbviewer.jupyter.org/github/ETCBC/laf-fabric-nbs/blob/master/querying/MQL.ipynb>`_.

It is assumend that Emdros is installed in such a way that the command to run MQL is in your path,
i.e. that the command ``mql`` is understood when run in a terminal (i.e. from a command prompt).
To achieve this, download Emdros, open the downloaded package, read the appropriate document with ``INSTALL`` in the name,
and follow the instructions below where it says *The rest is only needed if you wish to use Emdros from the command line*.
SWIG is not needed.
