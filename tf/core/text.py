"""
# Text API

Here are the functions that enable you to get the actual text in the dataset.
There are several things to accomplish here, such as

*   support the structure of the corpus
*   support a rigid section system usable by the TF browser
*   handle multilingual section labels;
*   switch between various text representations.

The details of the Text API are dependent on the `tf.core.data.WARP` feature `otext`,
which is a config feature.

!!! hint "T"
    The Text API is exposed as `T` or `Text`.

!!! note "otext is optional"
    If your dataset does not have an `otext` feature,
    the Text API will not be build.
    If it exists, but does not specify structure or sections,
    those parts of the Text API will not be built.
    Likewise for text representations.

## Structure

If a corpus has sectional elements, such as
series, volume, book, part, document, chapter, fragment, verse, halfverse,
line, etc, then you can configure those elements as structural types.

If your TF dataset designer has done that, the `T.api` will provide a number
of handy functions to navigate your corpus along its structure, programmatically.

The
[banks](https://nbviewer.jupyter.org/github/annotation/banks/blob/master/programs/structure.ipynb)
example corpus shows a full example.

Structure is defined in the `otext` feature, by means of the keys
`structureTypes` and `structureFeatures`.
These are comma-separated lists of equal length.

`structureTypes` specifies the node types
that act as structural types, in the order from biggest to smallest.

`structureFeatures` specifies a feature that corresponds to each
structural type. This feature must contain the label of the structural
element, e.g. the title of a book, the number of a verse, etc.

The order of the section types is significant.
Suppose you have a book with a single chapter. Is the chapter part of the book,
or is the book part of the chapter?
The order decides. If `book` is mentioned in `structureTypes` before `chapter`
then the chapter is part of the book, and not the other way around.

However, it is allowed to have nesting of elements of the same kind.

!!! explanation "Proper embedding not required"
    There are no assumptions on how exactly the structural elements lie
    embedded in each other, and whether they consist of uninterrupted stretches
    of material or not.

    Suppose a we have a book with two disjoint chapters and there is a verse that
    has material in both chapters. Then that verse is part of neither chapter,
    but it is still part of the book.
    If you go down from that book to its substructural elements, you find not only
    its chapters, but also that verse.

    So the great freedom with respect to structural elements also brings greater
    responsibility when using that structure.

## Sections

In `otext` the main section levels (usually `book`, `chapter`, `verse`) can be
defined. It loads the features it needs (so you do not have to specify those
features, unless you want to use them via `F`). And finally, it makes some
functions available by which you can make handy use of that information.

!!! explanation "Section levels from a limited, rigid system"
    There are up to three section levels, and this is a hard coded boundary.
    That makes this section system unsuitable to faithfully reflect the
    rich sectioning that may be present in a corpus.

    On the other hand, applications (such as TF apps) can access a predictable
    sectioning system by which they can divide the material in practical portions.

    The rule of thumb is:

    Level 1 divides the corpus into top level units,
    of which there might be (very) many. The TF browser has a control that
    can deal with long lists.

    Level 2 divides a level 1 section into a division that can be loaded into
    a webpage, without overwhelming the browser.
    Even better, it should be just one or a few screenfuls of text, when
    represented in `plain` view.

    Level 3 divides a level 2 section into divisions that roughly corresponds to lines.
    Such lines typically take up one screenful if represented in `pretty` view.

!!! explanation "Section levels are generic"
    In this documentation, we call the main section level `book`, the second level
    `chapter`, and the third level `verse`. Text-Fabric, however, is completely
    agnostic about how these levels are called. It is prepared to distinguish three
    section levels, but how they are called, must be configured in the dataset. The
    task of the `otext` feature is to declare which node type and feature correspond
    with which section level. Text-Fabric assumes that the first section level may
    have multilingual headings, but that section levels two and three have single
    language headings (numbers of some kind).

!!! explanation "String versus number"
    Chapter and verse numbers will be considered to be strings or
    integers, depending on whether your dataset has declared the corresponding
    feature *valueType* as `str` or as `int`.

    Conceivably, other works might have chapter and verse numbers
    like `XIV`, '3A', '4.5', and in those cases these numbers are obviously not
    `int`s.

!!! explanation "levels of node types"
    Usually, Text-Fabric computes the hierarchy of node types correctly, in the
    sense that node types that act as containers have a lower level than node types
    that act as containees. So books have the lowest level, words the highest. See
    [levels](#levels). However, if this level assignment turns out to be wrong for
    your dataset, you can configure the right order in the *otext* feature, by means
    of a key `levels` with value a comma separated list of levels. Example:

        @levels=tablet,face,column,line,case,cluster,quad,comment,sign

## Book names and languages

The names of the books may be available in multiple languages. The book names
are stored in node features with names of the form `book@`*la*, where *la* is
the [ISO 639](https://en.wikipedia.org/wiki/ISO_639) two-letter code for that
language. Text-Fabric will always load these features.

## Text representation

Text can be represented in multiple ways. We provide a number of formats with
structured names.

A format name is a string of keywords separated by `-`:

*what*`-`*how*`-`*fullness*`-`*modifier*

For Hebrew any combination of the follwoing could be useful formats:

keyword | value | meaning
------- | ----- | -------
*what* | `text` | words as they belong to the text
*what* | `lex` | lexemes of the words
*how* | `orig` | in the original script (Hebrew, Greek, Syriac) (all Unicode)
*how* | `trans` | in (latin) transliteration
*how* | `phono` | in phonetic/phonological transcription
*fullness* | `full` | complete with accents and all diacritical marks
*fullness* | `plain` | with accents and diacritical marks stripped, in Hebrew only the consonants are left
*modifier* | `ketiv` | (Hebrew): where there is ketiv/qere, follow ketiv instead of qere (default);

The default format is `text-orig-full`, we assume that every TF dataset defines
this format.

A format is a template string, with fixed text and variable text.
The variable text comes from features.
You specify the interpolation of features by surrounding the feature name
by `{ }`.

For example, if `letters` and `after` are features, this is a text format:

```
{letters}{after}
```

If you need tabs and newlines in a format, specify them by \\t and \\n.

You can also conditionally choose between features, to
substitute the value of another feature in case of empty values.

For example, if you want to use the `normal` feature to represent a word,
but if there is also a rare feature `special` that you want to use if it
is defined for that word, you can make a format

```
{special/normal}
```

This tries the feature `special` first, and if that is empty, it takes
`normal`.

You can also add a fixed default. If you want to display a `.` if
neither `special` nor `normal` exist, you can say

```
{special/normal:.}
```

TF datasets may also define formats of the form

*nodetype*`-default`

where *nodetype* is a valid type of node in the dataset.

These formats will be invoked in cases where no explicit format is specified as
a fall back for some kind of nodes. See `T.text()` below.

A node type may also be prepended to a format, with `#` as separator:

*nodetype*`#`*textformat*

In general, a format can be applied to any kind of node, and it will
lookup the features defined in its template for that node.
But some features have meaningful values for particular node types only.

So formats may indicate that they should be applied to nodes of a specific type.
See `T.text()` below.

Remember that the formats are defined in the `otext` warp config feature of your
set, not by Text-Fabric.

!!! note "Freedom of names for formats"
    There is complete freedom of choosing names for text formats.
    They do not have to complied with the above-mentioned scheme.

!!! note "layout in formats"
    So far, text formats only result in plain text.
    A TF-app (`tf.advanced.app`) may define and implement extra text
    formats which may invoke all HTML+CSS styling that you can think of.

### The T.text() function

The way th `tf.core.text.Text.text` responds to its parameters may look complicated,
but the retionale is that the defaults should be sensible.

Consider the simplest call to this function: `T.text(node)`.
This will apply the default format to `node`.
If `node` is non-slot, then in most cases
the default format will be applied to the slots contained in `node`.

But for special node types, where the best representation
is not obtained by descending down
to the contained slot nodes, the dataset may define
special default types that use other
features to furnish a decent representation.

!!! explanation "lexemes"
    In some corpora case this happens for the type of lexemes: `lex`.
    Lexemes contain their occurrences
    as slots, but the representation of a lexeme
    is not the string of its occurrences, but
    resides in a feature such as `voc_lex_utf8`
    (vocalized lexeme in Unicode).

    If the dataset defines the format `lex-default={lex} `,
    this is the only thing needed to regulate
    the representation of a lexeme.

    Hence, `T.text(lx)` results in the lexeme representation of `lx`.

    But if you really want to print out all occurrences of lexeme `lx`,
    you can say `T.text(lx, descend=True)`.

!!! explanation "words and signs"
    In some corpora the characters or signs are the slot level, and there is
    a non slot level of words.
    Some text formats are best defined on signs, others best on words.

    For example, if words are associated with lexemes, stored in a word
    feature `lex`, we can define a text format

       lex-orig-full=word#{lex} `

    When you call `T.text(n)` for a non-slot, non-word node,
    normally the node will be replaced by the slot nodes it contains,
    before applying the template in the format.
    But if you pass a format that specifies a different node type,
    nodes will be replaced by contained nodes of that type. So

        T.text(n, fmt='lex-orig-full')

    will lookup all word nodes under *n* and apply the template `{lex}`
    to them.

!!! caution "same and different behaviours"
    The consequences of the rules might be unexpected in some cases.
    Here are a few observations:

    * formats like `phrase-default` can be implicitly invoked for phrase nodes,
      but `descend=True` prevents that;
    * when a format targeted at phrases is invoked for phrase nodes,
      `descend=True` will not cause the expansion of those nodes to slot nodes,
      because the phrase node is already expanded
      to the target type of the format;


!!! hint "memory aid"
    *   If *fmt* is explicitly passed, it will be the format used
        no matter what, and it determines the level of the nodes to descend to;
    *   Descending is the norm, it can only be prevented
        by setting default formats for node types or
        by passing `descend=False` to `T.text()`;
    *   `descend=True` is stronger than type-specific default formats,
        but weaker than explicitly passed formats;
    *   **Pass `explain=True` for a dynamic explanation.**

!!! note "Non slot nodes allowed"
    In most cases, the nodes fed to `T.text()` are slots, and the formats are
    templates that use features that are defined for slots.

    But nothing prevents you to define a format
    for non-slot nodes, and use features
    defined for a non-slot node type.

    If, for example, your slot type is *glyph*,
    and you want a format that renders
    lexemes, which are not defined for glyphs but for words,
    you can just define a format in terms of word features.

    It is your responsibility to take care to use the formats
    for node types for which they make sense.

!!! caution "Escape whitespace in formats"
    When defining formats in `otext.tf`,
    if you need a newline or tab in the format,
    specify it as `\n` and `\t`.
"""

from .data import WARP

DEFAULT_FORMAT = "text-orig-full"
DEFAULT_FORMAT_TYPE = "{}-default"
SEP = "-"
TYPE_FMT_SEP = "#"


class Text(object):
    """Low level text representation, including section headings.

    In addition to the methods that are directly defined, there are also
    methods `xxxName()` and `xxxNode()` where `xxx` is whatever the node type of
    level 1 sections is.

    !!! note "level 1 node types"
        In the BHSA the `xxx` is `book`, in the DSS it is `scroll`,
        in Old Babylonian it is `document`, and in Uruk it is `tablet`.

        Here we take the BHSA as example: `bookName()` and `bookNode()`

            T.bookName(node, lang='en')
            T.bookNode(name, lang='en')

        with node:int the node in question, name:str the name in question,
        and `lang='en'` the language of the book name.
    """

    def __init__(self, api):
        self.api = api
        C = api.C
        Fs = api.Fs
        TF = api.TF
        self.languages = {}
        """A dictionary of the languages that are available for book names.
        """

        self.nameFromNode = {}
        self.nodeFromName = {}
        config = api.TF.features[WARP[2]].metaData if WARP[2] in api.TF.features else {}
        self.sectionTypes = TF.sectionTypes
        self.sectionTypeSet = set(TF.sectionTypes)
        self.sectionFeats = TF.sectionFeats
        self.sectionFeatsWithLanguage = getattr(TF, "sectionFeatsWithLanguage", set())
        self.sectionFeatures = []
        self.sectionFeatureTypes = []
        self.structureTypes = TF.structureTypes
        self.structureFeats = TF.structureFeats
        self.structureTypeSet = set(self.structureTypes)
        self.config = config
        self.defaultFormat = DEFAULT_FORMAT
        self.defaultFormats = {}

        structure = getattr(C, "structure", None)

        (
            self.hdFromNd,
            self.ndFromHd,
            self.hdMult,
            self.hdTop,
            self.hdUp,
            self.hdDown,
        ) = (structure.data if structure else (None, None, None, None, None, None))
        self.headings = (
            ()
            if structure is None
            else tuple(zip(self.structureTypes, self.structureFeats))
        )
        otypeInfo = api.F.otype
        fOtype = otypeInfo.v

        good = True
        if len(self.sectionFeats) != 0 and len(self.sectionTypes) != 0:
            for fName in self.sectionFeatsWithLanguage:
                fObj = api.TF.features[fName]
                meta = fObj.metaData
                code = meta.get("languageCode", "")
                self.languages[code] = {
                    k: meta.get(k, "default") for k in ("language", "languageEnglish")
                }
                cData = Fs(fName).data
                self.nameFromNode[code] = cData
                self.nodeFromName[code] = dict(
                    ((fOtype(node), name), node) for (node, name) in cData.items()
                )
            for fName in self.sectionFeats:
                dataType = api.TF.features[fName].dataType
                self.sectionFeatures.append(api.Fs(fName).data)
                self.sectionFeatureTypes.append(dataType)

            sec0 = self.sectionTypes[0]
            setattr(self, f"{sec0}Name", self._sec0Name)
            setattr(self, f"{sec0}Node", self._sec0Node)

        self.formats = {}
        """The text representation formats that have been defined in your dataset.
        """

        self._compileFormats()
        self.good = good

    def sectionTuple(self, n, lastSlot=False, fillup=False):
        """Gives a tuple of nodes that correspond to a sections

        More precisely, we retrieve the sections that contain a
        reference node, which is either the first slot or the last slot of the node
        in question.

        Parameters
        ----------
        n: integer
            The node whose containing section to retrieve.
        lastSlot: boolean, optional `False`
            Whether the reference node will be the last slot contained by *n*
            or the first slot.
        fillup: boolean, optional `False`
            Whether to fill up the tuple with missing section elements.
        Returns
        -------
        section: tuple of int
            If *n* is not a section node, a reference node *r* will be taken
            according to the *lastSlot* parameter.

            If `fillup == False`:

            If *r* is a level 0 section node,
            *section* is the 1-element tuple `(r,)`.

            If *r* is a level 1 section node,
            *section* is a 2-element tuple, i.e.
            the enclosing level 0 section node and *r* itself.

            If *r* is a level 2 section node,
            *section* is a 3-element tuple, i.e.
            the enclosing level 0 and  1 section nodes and *r* itself.

            If `fillup == True`, always a complete 3-tuple of a level 0, 1, and 2
            section nodes is returned.
        """

        sTypes = self.sectionTypes
        lsTypes = len(sTypes)
        if lsTypes == 0:
            return ()
        F = self.api.F
        E = self.api.E
        L = self.api.L
        fOtype = F.otype.v
        slotType = F.otype.slotType
        maxSlot = F.otype.maxSlot
        eoslots = E.oslots.data
        nType = fOtype(n)

        if nType == slotType:
            r = n
        else:
            slots = eoslots[n - maxSlot - 1]
            r = slots[-1 if lastSlot else 0]

        if nType == sTypes[0]:
            if fillup:
                r1 = L.u(r, otype=sTypes[1])
                r1 = r1[0] if r1 else ""
                if lsTypes > 2:
                    r2 = L.u(r, otype=sTypes[2])
                    r2 = r2[0] if r2 else ""
                    return (n, r1, r2)
                return (n, r1)
            return (n,)

        r0s = L.u(r, sTypes[0])
        r0 = r0s[0] if r0s else None

        if nType == sTypes[1]:
            if fillup:
                if lsTypes > 2:
                    r2 = L.u(r, otype=sTypes[2])
                    r2 = r2[0] if r2 else ""
                    return (r0, n, r2)
            return (r0, n)

        r1s = L.u(r, sTypes[1])
        r1 = r1s[0] if r1s else ""

        if lsTypes < 3:
            return (r0, r1)

        if nType == sTypes[2]:
            return (r0, r1, n)

        r2s = L.u(r, sTypes[2])
        r2 = r2s[0] if r2s else ""

        return (r0, r1, r2)

    def sectionFromNode(self, n, lastSlot=False, lang="en", fillup=False):
        """Gives the full heading of a section node.

        Parameters
        ----------
        n: integer
            The node whose heading to retrieve.
        lastSlot: boolean, optional `False`
            Whether the reference node will be the last slot contained by *n*
            or the first slot.
        lang: string, optional `en`
            The language assumed for the section parts,
            as far as they are language dependent.
            Must be a 2-letter language code.
        fillup: boolean, optional `False`
            Whether to fill up the tuple with missing section elements.

        Returns
        -------
        heading: tuple of pairs
            If *n* is not a section node, a reference node *r* will be taken
            according to the *lastSlot* parameter.

            It is the tuple of integer/string values for section ancestors
            of *r* and *r* itself,
            where the *fillup* parameter plays the same role as in
            `Text.sectionTuple`.

        Notes
        -----
        !!! hint "crossing verse boundaries"
            Sometimes a sentence or clause in a verse continue into the next verse.
            In those cases, this function will return different results for
            `lastSlot=False` and `lastSlot=True`.

        Warnings
        --------
        Nodes that lie outside any book, chapter, or verse
        will get a `None` in the corresponding members of the returned tuple.
        """
        sTuple = self.sectionTuple(n, lastSlot=lastSlot, fillup=fillup)
        if len(sTuple) == 0:
            return ()

        sFs = self.sectionFeatures

        return tuple(
            ""
            if n is None
            else self._sec0Name(n, lang=lang)
            if i == 0
            else sFs[i].get(n, None)
            for (i, n) in enumerate(sTuple)
        )

    def nodeFromSection(self, section, lang="en"):
        """Given a section tuple, return the node of it.

        Parameters
        ----------
        section: string
            `section` consists of a book name (in language `lang`),
            and a chapter number and a verse number
            (both as strings or number depending on the value type of the
            corresponding feature).
        lang: string, optional `en`
            The language assumed for the section parts,
            as far as they are language dependent.
            Must be a 2-letter language code.

        Returns
        -------
        section node: integer
            If section labels for all three levels is present,
            the result is a level 3 node.
            If the level 3 label has been left out, the result is a level 2 node.
            If both level 1 and level 2 labels have been left out,
            the result is a level 1 node.
        """

        sTypes = self.sectionTypes
        if len(sTypes) == 0:
            return None
        (sec1, sec2) = self.api.C.sections.data
        sec0node = self._sec0Node(section[0], lang=lang)
        if len(section) == 1:
            return sec0node
        elif len(section) == 2:
            return sec1.get(sec0node, {}).get(section[1], None)
        else:
            return sec2.get(sec0node, {}).get(section[1], {}).get(section[2], None)

    def structureInfo(self):
        """Gives a summary of how structure has been configured in the dataset.

        If there are headings that are the same for multiple structural nodes,
        you'll get a warning here, and you are told how you can get all of those.

        It also shows a short description of all structure-related methods
        of the `T` API.
        """

        api = self.api
        TF = api.TF
        info = TF.info
        error = TF.error
        hdMult = self.hdMult
        hdFromNd = self.hdFromNd
        headings = self.headings

        if hdFromNd is None:
            info("No structural elements configured", tm=False)
            return
        info("A heading is a tuple of pairs (node type, feature value)", tm=False)
        info(
            "\tof node types and features that have been configured as structural elements",
            tm=False,
        )
        info(
            f"These {len(headings)} structural elements have been configured", tm=False
        )
        for (tp, ft) in headings:
            info(f"\tnode type {tp:<10} with heading feature {ft}", tm=False)
        info("You can get them as a tuple with T.headings.", tm=False)
        info(
            f"""
Structure API:
\tT.structure(node=None)       gives the structure below node, or everything if node is None
\tT.structurePretty(node=None) prints the structure below node, or everything if node is None
\tT.top()                      gives all top-level nodes
\tT.up(node)                   gives the (immediate) parent node
\tT.down(node)                 gives the (immediate) children nodes
\tT.headingFromNode(node)      gives the heading of a node
\tT.nodeFromHeading(heading)   gives the node of a heading
\tT.ndFromHd                   complete mapping from headings to nodes
\tT.hdFromNd                   complete mapping from nodes to headings
\tT.hdMult are all headings    with their nodes that occur multiple times

There are {len(hdFromNd)} structural elements in the dataset.
""",
            tm=False,
        )

        if hdMult:
            nMultiple = len(hdMult)
            tMultiple = sum(len(x) for x in hdMult.values())
            error(
                f"WARNING: {nMultiple} structure headings with hdMult occurrences (total {tMultiple})",
                tm=False,
            )
            for (sKey, nodes) in sorted(hdMult.items())[0:10]:
                sKeyRep = "-".join(":".join(str(p) for p in part) for part in sKey)
                nNodes = len(nodes)
                error(f"\t{sKeyRep} has {nNodes} occurrences", tm=False)
                error(f'\t\t{", ".join(str(n) for n in nodes[0:5])}', tm=False)
                if nNodes > 5:
                    error(f"\t\tand {nNodes - 5} more", tm=False)
            if nMultiple > 10:
                error(f"\tand {nMultiple - 10} headings more")

    def structure(self, node=None):
        """Gives the structure of node and everything below it as a tuple.

        Parameters
        ----------
        node: integer, optional `None`
            The node whose structure is asked for.
            If *node* is None, the complete structure of the whole dataset is returned.

        Returns
        -------
        structure: tuple
            Nested tuple of nodes involved in the structure below a node.
        """

        api = self.api
        TF = api.TF
        error = TF.error
        F = api.F
        fOtype = F.otype.v
        hdTop = self.hdTop

        if hdTop is None:
            error("structure types are not configured", tm=False)
            return None
        if node is None:
            return tuple(self.structure(node=t) for t in self.top())

        nType = fOtype(node)
        if nType not in self.structureTypeSet:
            error(
                f"{node} is an {nType} which is not configured as a structure type",
                tm=False,
            )
            return None

        return (node, tuple(self.structure(node=d) for d in self.down(node)))

    def structurePretty(self, node=None, fullHeading=False):
        """Gives the structure of node and everything below it as a string.

        Parameters
        ----------
        node: integer, optional `None`
            The node whose structure is asked for.
            If *node* is None, the complete structure of the whole dataset is returned.
        fullHeading: boolean, optional `False`
            Normally, for each structural element, only its own subheading is added.
            But if you want to see the full heading, consisting of the headings of a
            node and all of its parents, pass `True` for this parameter.

        Returns
        -------
        structure: string
            Pretty representation as string with indentations of the structure
            below a node.
        """

        structure = self.structure(node=node)
        if structure is None:
            return

        material = []

        def generate(struct, indent=""):
            if type(struct) is int:
                sKey = self.headingFromNode(struct)
                if not fullHeading:
                    sKey = (sKey[-1],)
                sKeyRep = "-".join(":".join(str(p) for p in part) for part in sKey)
                material.append(f"{indent}{sKeyRep}")
            else:
                for item in struct:
                    generate(item, indent=indent + "  ")

        generate(structure)
        return "\n".join(material)

    def top(self):
        """Gives all top-level structural nodes in the dataset.
        These are the nodes that are not embedded in a structural node of the same
        or a higher level.
        """

        api = self.api
        TF = api.TF
        error = TF.error
        hdTop = self.hdTop

        if hdTop is None:
            error("structure types are not configured", tm=False)
            return None
        return hdTop

    def up(self, n):
        """Gives the parent of a structural node.

        Parameters
        ----------
        n: integer
            The node whose parent to retrieve.

        Returns
        -------
        parent: integer
            The parent is that structural node that whose heading you get from
            the heading of *n* minus its last element.

        Notes
        -----
        !!!hint "Example"
            The parent of `((book, Genesis), (chapter, 3), (verse, 16))`
            is the node that has heading `((book, Genesis), (chapter, 3))`.
        """

        api = self.api
        F = api.F
        TF = api.TF
        error = TF.error
        fOtype = F.otype.v

        hdUp = self.hdUp
        if hdUp is None:
            error("structure types are not configured", tm=False)
            return None
        nType = fOtype(n)
        if nType not in self.structureTypeSet:
            error(
                f"{n} is an {nType} which is not configured as a structure type",
                tm=False,
            )
            return None
        return hdUp.get(n, None)

    def down(self, n):
        """Gives the children of a structural node.

        Parameters
        ----------
        n: integer
            The node whose children to retrieve.

        Returns
        -------
        children: tuple of integers
            The children are those structural nodes whose headings are one
            longer than the one from *n*.

        Notes
        -----
        !!!hint "Example"
            The children of `((book, Genesis), (chapter, 3))` are the nodes
            with heading `((book, Genesis), (chapter, 3), (verse, 1))`, etc.
        """

        api = self.api
        F = api.F
        fOtype = F.otype.v
        TF = api.TF
        error = TF.error
        hdDown = self.hdDown
        if hdDown is None:
            error("structure types are not configured", tm=False)
            return None
        nType = fOtype(n)
        if nType not in self.structureTypeSet:
            error(
                f"{n} is an {nType} which is not configured as a structure type",
                tm=False,
            )
            return None
        return hdDown.get(n, ())

    def headingFromNode(self, n):
        """Gives the full heading of a structural node.

        Parameters
        ----------
        n: integer
            The node whose heading to retrieve.

        Returns
        -------
        heading: tuple of pairs
            It is the tuple of pairs (node type, feature value)
            for all ancestors of *n*.

        Notes
        -----
        !!!hint "Example"
            E.g., the heading of the verse node corresponding to Genesis 3:16
            is `((book, Genesis), (chapter, 3), (verse, 16))`.

        !!!hint "Power tip"
            If you are interested in the complete mapping: it is stored in
            the dictionary `hdFromNd`.
        """

        api = self.api
        F = api.F
        TF = api.TF
        error = TF.error
        fOtype = F.otype.v
        hdFromNd = self.hdFromNd
        if hdFromNd is None:
            error("structure types are not configured", tm=False)
            return None
        nType = fOtype(n)
        if nType not in self.structureTypeSet:
            error(
                f"{n} is an {nType} which is not configured as a structure type",
                tm=False,
            )
            return None
        return hdFromNd.get(n, None)

    def nodeFromHeading(self, head):
        """Gives the node corresponding to a heading, provided it exists.

        Parameters
        ----------
        head: tuple of pairs
            See the result of `headingFromNode`.

        Returns
        -------
        node: int
            If there is more than one node that corresponds to the heading,
            only the last one in the corpus will be returned.
            `hdMult` contains all such cases.

        Notes
        -----
        !!!hint "Power tip"
            If you are interested in the complete mapping: it is stored in
            the dictionary `ndFromHd`.
        """

        api = self.api
        TF = api.TF
        error = TF.error
        ndFromHd = self.ndFromHd
        if ndFromHd is None:
            error("structure types are not configured", tm=False)
        n = ndFromHd.get(head, None)
        if n is None:
            error(f"no structure node with heading {head}", tm=False)
        return n

    def text(self, nodes, fmt=None, descend=None, func=None, explain=False, **kwargs):
        """Gives the text that corresponds to a bunch of nodes.

        The
        [banks](https://nbviewer.jupyter.org/github/annotation/banks/blob/master/programs/formats.ipynb)
        example corpus shows examples.

        Parameters
        ----------

        nodes: dict
            *nodes* can be a single node or an arbitrary iterable of nodes
            of arbitrary types.
            No attempt will be made to sort the nodes.
            If you need order, it is better to sort the nodes first.

        fmt: boolean, optional `None`
            The text-format of the text representation.

            If it is not specified or `None`, each node will be formatted with
            a node type specific format, defined as *nodeType*`-default`, if it
            exists.

            If there is no node specific format, the default format
            `text-orig-full` will be used.

            If `text-orig-full` is not defined, an error message will be issued,
            and the nodes will be represented by their types and numbers.

            If a value for *fmt* is passed, but it is not a format defined in the
            *otext.tf* feature, there will be an error message and `None` is returned.

        descend: boolean, optional `None`
            Whether to descend to constituent nodes.

            If `True`, nodes will be replaced by a sequence of their consituent nodes,
            which have a type specified by the format chosen, or, if the format does
            not specify such a type, the node will be replaced
            by the slots contained in it.

            If `False`, nodes will not be replaced.

            If *descend* is not specified or None,
            a node will be replaced by its constituent nodes,
            unless its type is associated with the given format or,
            if no format is given, by the default format of its type, or,
            if there is no such format, by its slots.

            !!! caution "no nodes to descend to"
                If you call `T.text(n, fmt=myfmt)`
                and `myfmt` is targeted to a node type that is
                bigger than the node type of `n`,
                then the so-called descending leads to an empty
                sequence of nodes and hence to an empty string.

        explain: boolean, optional `False`
            The logic of this function is subtle.
            If you call it and the results baffles you, pass `explain=True`
            and it will explain what it is doing.
        """

        api = self.api
        E = api.E
        F = api.F
        L = api.L
        TF = api.TF
        error = TF.error

        fOtype = F.otype.v
        slotType = F.otype.slotType
        maxSlot = F.otype.maxSlot
        eoslots = E.oslots.data

        defaultFormats = self.defaultFormats
        xformats = self._xformats
        xdTypes = self._xdTypes

        if fmt and fmt not in xformats:
            error(f'Undefined format "{fmt}"', tm=False)
            return ""

        def rescue(n, **kwargs):
            return f"{fOtype(n)}{n}"

        single = type(nodes) is int
        material = []
        good = True

        if single:
            nodes = [nodes]
        else:
            nodes = list(nodes) if explain else nodes
        if explain:
            fmttStr = "format target type"
            ntStr = "node type"

            nRep = "single node" if single else f"iterable of {len(nodes)} nodes"
            fmtRep = "implicit" if not fmt else f"{fmt} targeted at {xdTypes[fmt]}"
            descendRep = (
                "implicit" if descend is None else "True" if descend else "False"
            )
            funcRep = f'{"" if func else "no "}custom format implementation'
            error(
                f"""
EXPLANATION: T.text() called with parameters:
\tnodes  : {nRep}
\tfmt    : {fmtRep}
\tdescend: {descendRep}
\tfunc   : {funcRep}
""",
                tm=False,
            )

        for node in nodes:
            nType = fOtype(node)
            if explain:
                error(f"\tNODE: {nType} {node}", tm=False)
            if descend:
                if explain:
                    downRep = fmttStr
                if fmt:
                    repf = xformats[fmt]
                    downType = xdTypes[fmt]
                    if explain:
                        fmtRep = f"explicit {fmt} does {repf}"
                        expandRep = f"{downType} {{}} (descend=True) ({downRep})"
                else:
                    repf = xformats[DEFAULT_FORMAT]
                    downType = xdTypes[DEFAULT_FORMAT]
                    if explain:
                        fmtRep = f"implicit {DEFAULT_FORMAT} does {repf}"
                        expandRep = f"{downType} {{}} (descend=True) ({downRep})"
            else:
                downType = nType
                if explain:
                    downRep = ntStr
                if fmt:
                    repf = xformats[fmt]
                    if descend is None:
                        downType = xdTypes[fmt]
                        if explain:
                            downRep = fmttStr
                    if explain:
                        fmtRep = f"explicit {fmt} does {repf}"
                        expandRep = f"{downType} {{}} (descend=None) ({downRep})"
                elif nType in defaultFormats:
                    dfmt = defaultFormats[nType]
                    repf = xformats[dfmt]
                    if descend is None:
                        downType = nType
                        if explain:
                            downRep = fmttStr
                    if explain:
                        fmtRep = f"implicit {dfmt} does {repf}"
                        expandRep = f"{downType} {{}} (descend=None) ({downRep})"
                else:
                    repf = xformats[DEFAULT_FORMAT]
                    if descend is None:
                        downType = xdTypes[DEFAULT_FORMAT]
                        if explain:
                            downRep = fmttStr
                    if explain:
                        fmtRep = f"implicit {DEFAULT_FORMAT} does {repf}"
                        expandRep = f"{downType} {{}} (descend=None) ({downRep})"

            if explain:
                expandRep2 = ""
            if downType == nType:
                if explain:
                    expandRep2 = "(no expansion needed)"
                downType = None

            if explain:
                error(f"\t\tTARGET LEVEL: {expandRep.format(expandRep2)}", tm=False)

            if explain:
                plural = "s"
            if downType == slotType:
                xnodes = eoslots[node - maxSlot - 1]
            elif downType:
                xnodes = L.d(node, otype=downType)
            else:
                xnodes = [node]
                if explain:
                    plural = ""
            if explain:
                nodeRep = f'{len(xnodes)} {downType or nType}{plural} {", ".join(str(x) for x in xnodes)}'
                error(f"\t\tEXPANSION: {nodeRep}", tm=False)

            if func:
                repf = func
                if explain:
                    fmtRep += f" (overridden with the explicit func argument {repf})"
            if not repf:
                repf = rescue
                good = False
                if explain:
                    fmtRep += (
                        "\n\t\t\twhich is not defined: formatting as node types and numbers"
                    )

            if explain:
                error(f"\t\tFORMATTING: {fmtRep}", tm=False)
                error("\t\tMATERIAL:", tm=False)
            for n in xnodes:
                rep = repf(n, **kwargs)
                material.append(rep)
                if explain:
                    error(f'\t\t\t{fOtype(n)} {n} ADDS "{rep}"', tm=False)

        if not good:
            error('Text format "{DEFAULT_FORMAT}" not defined in otext.tf', tm=False)
        return "".join(material)

    def _sec0Name(self, n, lang="en"):
        sec0T = self.sectionTypes[0]
        fOtype = self.api.F.otype.v
        refNode = n if fOtype(n) == sec0T else self.api.L.u(n, sec0T)[0]
        lookup = self.nameFromNode["" if lang not in self.languages else lang]
        return lookup.get(refNode, f"not a {sec0T} node")

    def _sec0Node(self, name, lang="en"):
        sec0T = self.sectionTypes[0]
        return self.nodeFromName["" if lang not in self.languages else lang].get(
            (sec0T, name), None
        )

    def _compileFormats(self):
        api = self.api
        TF = api.TF
        cformats = TF.cformats

        self.formats = {}
        self._xformats = {}
        self._xdTypes = {}
        for (fmt, (rtpl, feats)) in sorted(cformats.items()):
            defaultType = self.splitDefaultFormat(fmt)
            if defaultType:
                self.defaultFormats[defaultType] = fmt
            (descendType, rtpl) = self.splitFormat(rtpl)
            tpl = rtpl.replace("\\n", "\n").replace("\\t", "\t")
            self._xdTypes[fmt] = descendType
            self._xformats[fmt] = self._compileFormat(tpl, feats)
            self.formats[fmt] = descendType

    def splitFormat(self, tpl):
        api = self.api
        F = api.F
        slotType = F.otype.slotType
        otypes = set(F.otype.all)

        descendType = slotType
        parts = tpl.split(TYPE_FMT_SEP, maxsplit=1)
        if len(parts) == 2 and parts[0] in otypes:
            (descendType, tpl) = parts
        return (descendType, tpl)

    def splitDefaultFormat(self, tpl):
        api = self.api
        F = api.F
        otypes = set(F.otype.all)

        parts = tpl.rsplit(SEP, maxsplit=1)
        return (
            parts[0]
            if len(parts) == 2 and parts[1] == "default" and parts[0] in otypes
            else None
        )

    def _compileFormat(self, rtpl, feats):
        replaceFuncs = []
        for feat in feats:
            (feat, default) = feat
            replaceFuncs.append(self._makeFunc(feat, default))

        def g(n, **kwargs):
            values = tuple(replaceFunc(n) for replaceFunc in replaceFuncs)
            return rtpl.format(*values)

        return g

    def _makeFunc(self, feat, default):
        api = self.api
        Fs = api.Fs
        if len(feat) == 1:
            ft = feat[0]
            f = Fs(ft).data
            return lambda n: f.get(n, default)
        elif len(feat) == 2:
            (ft1, ft2) = feat
            f1 = Fs(ft1).data
            f2 = Fs(ft2).data
            return lambda n: (f1.get(n, f2.get(n, default)))
        else:

            def _getVal(n):
                v = None
                for ft in feat:
                    v = Fs(ft).data.get(n, None)
                    if v is not None:
                        break
                return v or default

            return _getVal
