# MQL

You can interchange with [MQL data](https://emdros.org).
Text-Fabric can read and write MQL dumps.
An MQL dump is a text file, like an SQL dump.
It contains the instructions to create and fill a complete database.

## Correspondence TF and MQL

After exporting a TF dataset to MQL, the resulting MQL database has the
following properties with respect to the TF dataset it comes from:

*   the TF *slots* correspond exactly with the MQL *monads* and have the same
    numbers; provided the monad numbers in the MQL dump are consecutive. In MQL
    this is not obligatory. Even if there gaps in the monads sequence, we will
    fill the holes during conversion, so the slots are tightly consecutive;
*   the TF *nodes* correspond exactly with the MQL *objects* and have the same
    numbers

## Node features in MQL

The values of TF features are of two types, `int` and `str`, and they translate
to corresponding MQL types `integer` and `string`. The actual values do not
undergo any transformation.

That means that in MQL queries, you use quotes if the feature is a string feature.
Only if the feature is a number feature, you may omit the quotes:

```
[word sp='verb']
[verse chapter=1 and verse=1]
```

## Enumeration types

It is attractive to use eumeration types for the values of a feature, whereever
possible, because then you can query those features in MQL with `IN` and without
quotes:

```
[chapter book IN (Genesis, Exodus)]
```

We will generate enumerations for eligible features.

Integer values can already be queried like this, even if they are not part of an
enumeration. So we restrict ourselves to node features with string values. We
put the following extra restrictions:

*   the number of distinct values is less than 1000
*   all values must be legal C names, in practice: starting with a letter,
    followed by letters, digits, or `_`. The letters can only be plain ASCII
    letters, uppercase and lowercase.

Features that comply with these restrictions will get an enumeration type.
Currently, we provide no ways to configure this in more detail.

Instead of creating separate enumeration types for individual features,
we collect all enumerated values for all those features into one
big enumeration type.

The reason is that MQL considers equal values in different types as
distinct values. If we had separate types, we could never compare
values for different features.

There is no place for edge values in
MQL. There is only one concept of feature in MQL: object features,
which are node features.
But TF edges without values can be seen as node features: nodes are
mapped onto sets of nodes to which the edges go. And that notion is supported by
MQL:
edge features are translated into MQL features of type `LIST OF id_d`,
i.e. lists of object identifiers.

!!! caution "Legal names in MQL"
    MQL names for databases, object types and features must be valid C identifiers
    (yes, the computer language C).

The requirements are for names are:

*   start with a letter (ASCII, upper-case or lower-case)
*   follow by any sequence of ASCII upper/lower-case letters or digits or
    underscores (`_`)
*   avoid being a reserved word in the C language

So, we have to change names coming from TF if they are invalid in MQL. We do
that by replacing illegal characters by `_`, and, if the result does not start
with a letter, we prepend an `x`. We do not check whether the name is a reserved
C word.

With these provisos:

*   the given `dbName` correspond to the MQL *database name*
*   the TF *otypes* correspond to the MQL *objects*
*   the TF *features* correspond to the MQL *features*

The MQL export is usually quite massive (500 MB for the Hebrew Bible).
It can be compressed greatly, especially by the program `bzip2`.

!!! caution "Exisiting database"
    If you try to import an MQL file in Emdros, and there exists already a file or
    directory with the same name as the MQL database, your import will fail
    spectacularly. So do not do that.

A good way to prevent clashes:

*   export the MQL to outside your `text-fabric-data` directory, e.g. to
    `~/Downloads`;
*   before importing the MQL file, delete the previous copy;

Delete existing copy:

```sh
cd ~/Downloads
rm dataset ; mql -b 3 < dataset.mql
```
