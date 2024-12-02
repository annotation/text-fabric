## How a TF dataset represents a corpus

A TF dataset contains: 

*   textual objects as a set of nodes;
*   textual positions as a range of slots, which are also nodes;
*   nodes are represented as numbers;
*   nodes are divided in types, which have a name;
*   non-slot nodes are linked to slots;
*   all data about textual positions and objects are in features,
    which map nodes to values;
*   features have a name, and each feature is stored in a separate file with that name;
*   in particular, the text itself is stored in one or more features;
*   there are a few standard features that are present in every TF dataset;
*   See the
    [TF data model](https://annotation.github.io/text-fabric/tf/about/datamodel.html).

In this dataset, **«slot»s** fulfill the role of slots.

## How TEI maps to TF

*   TF *«slot» nodes* correspond to **«slotf»** in TEI element content;
*   TF *node types* correspond to TEI *element names (tags)*;
*   TF *non-«slot» nodes* correspond to TEI *elements in the source*;
*   TF *features* correspond to TEI *attributes*;
*   TF *edges* correspond to *relationships* between TEI elements;
«beginParentYes»
    *   `parent` edges correspond to TEI elements and their parent elements 
«endParentYes»
«beginSiblingYes»
    *   `sibling` edges correspond to TEI elements and their sibling elements 
«endSiblingYes»
*   Here are the [TEI elements and attributes](elements.md) used in this corpus.
«beginProcinsYes»
*   TF *node types* that start with a `?` correspond to TEI processing 
    instruction with that node type as target. The attributes of the processing
    instruction translate to TF features. As to the link to slots: it is
    treated as if it were an empty element.
«endProcinsYes»
«beginProcinsNo»
*   Processing instructions in the TEI are ignored and do not leave any trace in the
    TF data.
«endProcinsNo»


The conversion may invoke custom code which may generate extra features.
For these features, metadata may have been declared, and it will show in the
generated documentation.

«token generation»

The TEI to TF conversion is an almost literal and very faithful transformation from
the TEI source files to a TF data set.

## TF nodes and features overview

(only in as far they are not in 1-1 correspondence with TEI elements and attributes)

«beginModelI»

### node type `«folder»`

*The type of subdirectories of TEI documents.*

**Section level 1**

**Features**

 feature    | description              
------------|--------------------------
 `«folder»` | name of the subdirectory 

### node type `«file»`

*The type of individual TEI documents.*

**Section level 2**

**Features**

 feature  | description                                                                    
----------|--------------------------------------------------------------------------------
 `«file»` | name of the file, without the `.xml` extension. Other extensions are included. 

«endModelI»

«beginModelII»

### node type `«chapter»`

*The type of «chapter»s in a TEI document.*

**Section level 1**

**Features**

 feature     | description              
-------------|--------------------------
 `«chapter»` | heading of the «chapter» 

«endModelII»

### node type `«chunk»`

«beginModelI»
*Top-level division of material in a TEI document.*
«endModelI»

«beginModelII»
*paragraph-like division.*
«endModelII»

**Section level «nLevels»**

**Features**

«beginModelI»

 feature   | description                                                        
-----------|--------------------------------------------------------------------
 `«chunk»` | sequence number of the «chunk» within the «file», starting with 1. 

«endModelI»

«beginModelII»

 feature   | description                                                                                                    
-----------|----------------------------------------------------------------------------------------------------------------
 `«chunk»` | sequence number of the «chunk» within the «chapter», positive for `<p>` «chunk»s, negative for other «chunk»s. 

«endModelII»

«beginTokenYes»
### node type `sentence`

*Sentences, i.e. material between full stops and several other punctuation marks*.

 feature | description                                           
---------|-------------------------------------------------------
 `nsent` | the sequence number of the sentence within the corpus 

«endTokenYes»

### node type `«tokenWord»`

*Individual «tokenWord»s, without space or punctuation.*

«beginTokenNo»
«beginSlotword»
**Slot type.**
«endSlotword»
«endTokenNo»
«beginTokenYes»
**Slot type.**
«endTokenYes»

**Features**

 feature                            | description                                                             
------------------------------------|-------------------------------------------------------------------------
 `str`                              | the characters of the «tokenWord», without soft hyphens.                
 «beginTokenNo»`after`              | the non-word characters after the word, up till the next word.          
 «endTokenNo»«beginTokenYes»`after` | the space after the word, if present, otherwise the empty string.       
 «endTokenYes»`is_meta`             | whether a «tokenWord» is in the `teiHeader` element                     
 `is_note`                          | whether a «tokenWord» is in a note element                              
 `rend_r`                           | whether a «tokenWord» is under the influence of a `rend="r"` attribute. 

«beginTokenNo»
«beginSlotchar»

### node type `char`

*UNICODE characters.*

**Slot type.**

The characters of the text of the elements.
Ignorable white-space has been discarded, and is not present in the TF dataset.
Meaningful white-space has been condensed to single spaces.

**Features**

 feature      | description                                                           
--------------|-----------------------------------------------------------------------
 `ch`         | the UNICODE character in that «slot».                                 
 `empty`      | whether a «slot» has been inserted in an empty element                
 `extraspace` | whether this is an extra space or newline, added by the conversion    
 `is_meta`    | whether a character is in the `teiHeader` element                     
 `is_note`    | whether a character is in a note element                              
 `rend_r`     | whether a character is under the influence of a `rend="r"` attribute. 

«endSlotchar»
«endTokenNo»

## Edge features

feature | description
--- | ---«beginParentYes»
`parent` | from a node to the node that corresponds to the parent element
«endParentYes»«beginSiblingYes»
`sibling` | from a node to all nodes that correspond to a preceding sibling element; the edges are labeled with the distance between the siblings; adjacent siblings have distance 1
«endSiblingYes»

Note that edges can be traversed in both directions, see the
[docs](https://annotation.github.io/text-fabric/tf/core/edgefeature.html).

«beginParentYes»

*   `E.parent.f(node)` finds the parent of a node
*   `E.parent.t(node)` finds the children of a node

«endParentYes»

«beginSiblingYes»

*   `E.sibling.f(node)` finds the *preceding* siblings of a node
*   `E.sibling.t(node)` finds the *succeeding* siblings of a node
*   `E.sibling.b(node)` finds *all* siblings of a node

«endSiblingYes»

## Extra features

«beginExtraYes»
«extraFeatures»
«endExtraYes»
«beginExtraNo»
The conversion has not generated extra features by means of custom code.
«endExtraNo»

## Sectioning

The material is divided into «nLevels» levels of sections, mainly for the purposes
of text display.

But how these levels relate to the source material is a different matter.

The conversion supports a few sectioning models that specify this.
This aspect is *work-in-progress*, because TEI sources differ wildly in how they
are sectioned.
The sectioning models that are currently supported correspond to cases we have
encountered, we have not done exhaustive research into TEI sectioning in practice.

This corpus is converted with section **Model «sectionModel»**.

«beginModelI»

### Model I: folders and files

This model assumes that the source is a directory consisting of folders
consisting of XML files, the TEI files.

There are three section levels:

*   *«folder»* Level 1 heading corresponding to folders with TEI files;
    heading: the name of the folder;
*   *«file»* Level 2 heading corresponding to individual TEI files;
    heading: the name of the file;
*   *«chunk»* Level 3 heading corresponding to top-level divisions in a TEI file;
    heading: the sequence number of the «chunk» within the file.

All section headings are stored in a feature with the same name as the type of the section:
*«folder»*, *«file»*, *«chunk»*.

#### Details

1.  *«chunk»* nodes have been made as follows:

    *   `<facsimile>`, `<fsdDecl>`, `<sourceDoc>`, and `<standOff>` are «chunk»s;
    *   immediate children of `<teiHeader>` are «chunk»s;
    *   immediate children of `<text>` are «chunk»s,
        except the *text structure* elements
        `<front>`, `<body>`, `<back>` and `<group>`;
    *   immediate children of the text structure elements are «chunk»s,
    *   but not necessarily empty elements such as `<lb/>` and `<pb/>`.

1.  «file»s and «folder» are sorted in the lexicographic ordering of their names;
1.  the folder `__ignore__` is ignored.
1.  the headings consist of the names of the «file»s and «folder»s
1.  the slots generated for empty elements are linked to the current chunk if there is
    a current chunk; otherwise they will be linked to the upcoming chunk.

There are no additional switches for tweaking the model further, at the moment.

«endModelI»

«beginModelII»

### Model II: single file and `div` elements.

This model assumes that the source is a single TEI file.

There are two section levels: 

*   *«chapter»* Top-level division, roughly corresponding to top-level `<div>` elements;
    heading: a sequence number and a tag name, or the contents of an heading-bearing element;
*   *«chunk»* division within the «chapter»s, roughly corresponding to `<p>` elements.
    heading: sequence number of the «chunk» within a «chapter»; «chunk»s that are `<p>` elements
    are numbered with positive numbers; other «chunk»s are numbered separately with negative numbers.

All section headings are stored in a feature with the same name as the type of section:
*«chapter»*, *«chunk»*.

#### Details

1.  *«chapter»* nodes have been made as follows:

    *   `<teiHeader>` is a «chapter»;
    *   immediate children of `<text>` are «chapter»s,
        except the *text structure* elements
        `<front>`, `<body>`, `<back>` and `<group>`;
    *   immediate children of the text structure elements are «chapter»s;

1.  *«chunk»* nodes have been made as follows:

    *   the `<teiHeader>` is a «chunk»;
    *   immediate children of `<text>` are «chunk»s,
        except the *text structure* elements
        `<front>`, `<body>`, `<back>` and `<group>`;
    *   immediate children of the text structure elements are «chunk»s,
    *   but not necessarily empty elements such as `<lb/>` and `<pb/>`.

1.  the slots generated for empty elements are linked to the current chapter and chunk
    if there they exist; otherwise they will be linked to the upcoming chapter
    and chunk.
1.  The heading of a «chapter» is either the text in a heading-bearing element,
    or, if no such element is found, a sequence number and the tag name.
1.  Extra parameters specify how to find the head-bearing element for a «chapter».
    This corpus is parametrized with

    ```
    «propertiesRaw»
    ```

    meaning:
    
    *   heads occur in `<«head»>` elements that follow the «chapter»-starting element;
        but only those ones that satisfy the following attribute properties, if any:

    «properties»

1.  Additional remarks about heading bearing elements:
    1.  their original occurrences in the text are preserved and treated in the same
        way as all other elements;
    1.  only the plain text content of the headings are used for the «chapter» headings,
        markup inside headings is ignored for this purpose.

«endModelII»

«beginTokenNo»
## Word detection

Words have been be detected.
They are maximally long sequences of alphanumeric characters
and hyphens.

1.  What is alphanumeric is determined by the UNICODE class of the character,
    see the Python documentation of the function
    [isalnum()](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)
1.  Hyphens are UNICODE characters 002D (ASCII hyphen) and 2010 (UNICODE hyphen).
1.  Words get the following features:
    *   `str`: the alphanumeric string that is the word;
    *   `after`: the non-alphanumeric string after the word until the following word.
«endTokenNo»

«beginTokenYes»
## Token detection

Tokens have been detected by an NLP pipeline.
The values of tokens are either words or non-word characters.
White-space is not part of the token.
Whether a token is followed by a space or not is in the feature `after`.

## Sentence detection
Sentences have been detected by an NLP pipeline.
They form a new node type, `sentence`, with just a sequence number as feature (`nsent`).
«endTokenYes»

## «Slot»s

Whether characters or words or tokens are taken as the basic unit (*slot*) is decided
by the parameter `granularity`, passed to the conversion, and whether tokens have been
provided later on.
(for this corpus the slot type is **«slot»**).

### «Slot»s and empty elements

When empty elements occur, something must be done to anchor them to the text stream.

To such elements we add an empty «slot» with the ZERO-WIDTH-SPACE (UNICODE 200B) as
character/string value.

Such slots get the feature `empty` assigned with value 1.

### «Slot»s in general

1.  Spaces are stripped when they are between elements whose parent does not allow
    mixed content; other white-space is reduced to a single space.
1.  However, after direct child elements of pure elements we add a single space
    or newline: if there is an ancestor with mixed content, we add a space;
    if the whole ancestry consists of pure elements (typically in the TEI header),
    we add a newline.
    «beginSlotword»

    These added slots get the feature `extraspace` set to 1.
    «endSlotword»
    
1.  All «slot»s inside the `teiHeader` will get the feature `is_meta` set to 1;
    for «slot»s inside the body, `is_meta` has no value.

«beginSlotchar»

## More about characters

The basic unit is the UNICODE character.
For each character in the input we make a slot, but the correspondence is not
quite 1-1, because of the white-space handling.

1.  *«slot»* nodes get this defining feature:
    *   `ch`: the character of the slot

«endSlotchar»

«beginSlotword»
«beginTokenNo»

## More about words

The basic unit is the word, as detected by the rules above.

1.  *«slot»* nodes get these defining features:
    *   `str`: the string of the «slot»
    *   `after`: interword material after the word
«endTokenNo»
«beginTokenYes»
## More about tokens

The basic unit is the word, as detected by the NLP pipeline used.

1.  *«slot»* nodes get these defining features:
    *   `str`: the string of the «slot»
    *   `after`: a possible space after the word
«endTokenYes»

1.  Nodes that contain only part of the characters of a «tokenWord», will
    contain the whole «tokenWord».
1.  Features that have different values for different characters in the «tokenWord»,
    will have the last value encountered for the whole «tokenWord».
1.  Formatting attributes, such as `rend=italic` (see below) will give rise
    to features `r_italic`. If a «tokenWord» is embedded in several elements with
    `rend` attributes and different values for them, the «tokenWord» will get
    features `r_`*value* for all those values. But if different parts of the
    «tokenWord» are in the scope of different `rend` values, that information
    will be lost, the `r_`*value* features all apply the whole «tokenWord».

«endSlotword»


## Text kinds and styled formatting

We record in additional features whether text occurs in metadata elements and
in note elements and what formatting specifiers influence the text.
These features are provided for «char and word» nodes, and have only one value: 1.
The absence of values means that the corresponding property does not hold.

The following features are added:

*   `is_meta`: 1 if the «tokenWord» occurs in inside the `<teiHeader>`, no
    value otherwise.
*   `is_note`: 1 if the «tokenWord» occurs in inside the `<note>`, no value otherwise.
*   `rend_r`: for any `r` that is the value of a `rend` attribute.

All these features are defined for «char and word» nodes.
For «tokenWord» nodes, the value of these features is set equal to what these features
are for their first character.

Special formatting for the `rend_r` features is supported for some values of `r`.
The conversion supports these out-of-the-box:

 value | description 
-------|-------------
«rendDesc»

It is possible for the corpus designer to add more formatting on a per-corpus
basis by adding it to the `display.css` in the app directory of the corpus.
Unsupported values get a generic kind of special format: an orange-like color.

Special formatting becomes visible when material is rendered in a `layout` text
format.

## Text formats

Text-formats regulate how text is displayed, and they can also determine
what text is displayed.

There are two kind of text-formats: those that start with the word `layout` and
those that start with `text`.

The `text` formats do not apply any kind of special formatting, the `layout` formats
do.

We have the following formats:

*   `text-orig-full`: all text
*   `layout-orig-full`: all text, formatted in HTML

## Boundary conditions

XML is complicated, the TEI guidelines use that complexity to the full.
In particular, it is difficult to determine what the set of TEI elements is
and what their properties are, just by looking at the schemas, because they are full
of macros, indirections, and abstractions, which can be overridden in any particular
TEI application.

On the other hand, the resulting TF should consist of clearly demarcated node types
and a simple list of features. In order to make that happen, we simplify matters
a bit.

«beginProcinsYes»
1.  Processing instructions (`<?proc a="b">`) are treated as empty elements with as tag
    the *target* with preceding `?` and as attributes its pseudo attributes.
«endProcinsYes»
«beginProcinsNo»
1.  Processing instructions (`<?proc a="b">`) are ignored.
1.  Comments (`<!-- this is a comment -->`) are ignored.
1.  Declarations (`<?xml ...>` `<?xml-model ...>` `<?xml-stylesheet ...>`) are
    read by the parser, but do not leave traces in the TF output.
1.  The attributes of the root-element (`<TEI>`) are ignored.
1.  Namespaces (`xmlns="http://www.tei-c.org/ns/1.0"`) are read by the parser,
    but only the unqualified names are distinguishable in the output as feature names.
    So if the input has elements `tei:abb` and `ns:abb`, we'll see just the node
    type `abb` in the output.

### Validation

We have used [LXML](https://lxml.de) for XML parsing. During `convert` it is not used
in validating mode, but we can trigger a validation step during `check`.

However, some information about the elements, in particular whether they allow
mixed content or not, has been gleaned from the schemas, and has been used
during conversion.

Care has been taken that the names of these extra nodes and features do not collide
with element / attribute names of the TEI.
