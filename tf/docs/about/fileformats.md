# TF File Format

## Overview

A `.tf` feature file starts with a *header*, and is followed by the actual data.
The whole file is a plain text in UNICODE-utf8.

## Header

A `.tf` feature file always starts with one or more metadata lines of the form

```
@key
```

or

```
@key=value
```

The first line must be either

```
@node
```

or

```
@edge
```

or

```
@config
```

This tells TF whether the data in the feature file is a *node* feature
or an *edge* feature. The value `@config` means that the file will be used as
configuration info. It will only have metadata.

There **must** also be a type declaration:

```
@valueType=type
```

where type is `str` or `int`. `@valueType` declares the type of the values in
this feature file. If it is anything other than `str` (=*string*), TF
will convert it to that type when it reads the data from the file. Currently,
the only other supported type is `int` for integers.

In edge features, there **may** also be a declaration

```
@edgeValues
```

indicating that the edge feature carries values. The default is that an edge
does not carry values.

The rest of the metadata is optional for now, but it is recommended to put a
date stamp in it like this

```
@dateCreated=2016-11-20T13:26:59Z
```

The time format should be [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601).

## Data

After the metadata, there must be exactly one blank line, and every line after
that is data.

### Data lines

The form of a data line is

```
node_spec value
```

for node features, and

```
node_spec node_spec value
```

for edge features.

These fields are separated by single tabs.

**NB**: This is the default format. Under *Optimizations* below we shall
describe the bits that can be left out, which will lead to significant
improvement in space demands and processing speed.

### Node Specification

Every line contains a feature value that pertains to all nodes defined by its
`node_spec`, or to all edges defined by its pair of `node_spec`s.

A node spec denotes a *set* of nodes.

The simplest form of a node spec is just a single integer. Examples:

```
3
45
425000
```

Ranges are also allowed. Examples

```
1-10
5-13
28-57045
```

The nodes denoted by a range are all numbers between the endpoints of the range
(including at both sides). So

```
2-4
```

denotes the nodes `2`, `3`, and `4`.

You can also combine numbers and ranges arbitrarily by separating them with
commas. Examples

```
1-3,5-10,15,23-37
```

Such a specification denotes the union of what is denoted by each
comma-separated part.

**NB** As node specs denote *sets* of nodes, the following node specs are in
fact equivalent

```
1,1 and 1
2-3 and 3,2
1-5,2-7 and 1-7
```

We will be tolerant in that you may specify the end points of ranges in
arbitrary order:

```
1-3 is the same as 3-1
```

### Edges

An edge is specified by an *ordered* pair of nodes. The edge is *from* the first
node in the pair *to* the second one. An edge spec consists of two node specs.
It denotes all edges that are *from* a node denoted by the first node spec *to*
a node denoted by the second node spec. An edge might be labeled, in that case
the label of the edge is specified by the *value* after the two node specs.

#### Value

The value is arbitrary text. The type of the value must conform to the
`@valueType` declaration in the feature file. If it is missing, it is assumed to
be `str`, which is the type of UNICODE-utf8 strings. If it is `int`, it should
be a valid representation of an integer number,

There are a few escapes:

*   `\\` backslash
*   `\t` tab
*   `\n` newline These characters MUST always be escaped in a value string,
    otherwise the line as a whole might be ambiguous.

**NB:** There is no representation for the absence of a value. The empty string
as value means that there is a value and it is the empty string. If you want to
describe the fact that node `n` does not have a value for the feature in
question, the node must be left out of the feature. In order words, there should
be no data line in the feature that targets this node.

If the declared value type (`@valueType`) of a feature is `int`, then its empty
values will be taken as absence of values, though.

## Consistency requirements

There are a few additional requirements on feature data, having to do with the
fact that features annotate nodes or edges of a graph.

### Single values

It is assumed that a node feature assigns only one value to the same node. If
the data contains multiple assignments to a node, only the last assignment will
be honoured, the previous ones will be discarded.

Likewise, it is assumed that an edge feature assigns only one value to the same
edge. If the data contains multiple assignments to an edge, only the last
assignment will be honoured.

Violations maybe or may not be reported, and processing may continue without
warnings.
