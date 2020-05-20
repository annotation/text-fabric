# Text

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
    sectioning system by which they can chunk the material in practical portions.

    The rule of thumb is:
    
    Level 1 divides the corpus into top level units,
    of which there might be (very) many. The TF browser has a control that
    can deal with long lists.

    Level 2 divides a level 1 section into a chunk that can be loaded into 
    a webpage, without overwhelming the browser.
    Even better, it should be just one or a few screenfuls of text, when
    represented in `plain` view.

    Level 3 divides a level 2 section into chunks that roughly corresponds to lines.
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

    ```
    @levels=tablet,face,column,line,case,cluster,quad,comment,sign
    ```

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

!!! "layout in formats"
    So far, text formats only result in plain text.
    A [TF-app](../Implementation/Apps.md) may define and implement extra text
    formats which may invoke all HTML+CSS styling that you can think of.
