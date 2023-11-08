# File format Optimizations

## Rationale

It is important to avoid an explosion of redundant data in `.tf` files. We want
the `.tf` format to be suitable for archiving, transparent to the human eye, and
easy (i.e. fast) to process.

## Using the implicit node

You may leave out the node spec for node features, and the first node spec for
edge features. When leaving out a node spec, you must also leave out the tab
following the node spec.

A line with the first node spec left out denotes the singleton node set
consisting of the *implicit node*. Here are the rules for implicit nodes.

*   On a line where there is an explicit node spec, the implicit node is equal to
    the highest node denoted by the explicit node spec;
*   On a line without an explicit node spec, the implicit node is determined from
    the previous line as follows:
    *   if there is no previous line, take `1`;
    *   else take the implicit node of the previous line and increment it by `1`.

For edges, this optimization only happens for the *first* node spec. The second
node spec must always be explicit.

This optimizes some feature files greatly, e.g. the feature that contains the
actual text of each word.

Instead of

```
1 be
2 reshit
3 bara
4 elohim
5 et
6 ha
7 shamajim
8 we
9 et
10 ha
11 arets
```

you can just say

```
be
reshit
bara
elohim
et
ha
shamajim
we
et
ha
arets
```

This optimization is not obligatory. It is a device that may be used if you want
to optimize the size of data files that you want to distribute.

## Omitting empty values

If the value is the empty string, you may also leave out the preceding tab (if
there is one). This is especially good for edge features, because most edges
just consist of a node pair without any value.

This optimization will cause a conceptual ambiguity if there is only one field
present in a node feature, or if there are only two fields in an edge feature.
It could mean that the (first) node spec has been left out, or that the value
has been left out.

In those cases we will assume that the node spec has been left out for node
features.

For edge features, it depends on whether the edge is declared to have values
(with `@edgeValues`). If the edge has values, then, as in the case of node
features, we assume that the first node spec has been left out. But if the edge
has no values, then we assume that both fields are node specs.

So, in a node feature a line like this

```
42
```

means that the implicit node gets value `42`, and not that node `42` gets the
empty value.

Likewise, a line in an edge feature (without values) like this

```
42 43
```

means that there is an edge from `42` to `43` with empty value, and not that
there is an edge from the implicit node to `42` with value 43.

And, in the same edge, a line like this

```
42
```

means that there is an edge from the implicit node to `42` with the empty value.

But, in an edge with values, the same lines are interpreted thus:

```
42 43
```

means that there is an edge from the implicit node to node `42` with value `43`.

And

```
42
```

means that there is an edge from the implicit node to node `42` with empty
value.

The reason for these conventions is practical: edge features usually have empty
labels, and there are many edges. In case of the Hebrew Text database, there are
1.5 million edges, so every extra character that is needed on a data line means
that the file size increases with 1.5MB.

Nodes on the other hand, usually do not have empty values, and they are often
specified in a consecutive way, especially slot (word) nodes. There are quite
many distinct word features, and it would be a waste to have a column of half a
million incremental integers in those files.

## Absence of values

Say you have a node feature assigning a value to only 2000 of 400,000 nodes.
(The Hebrew `qere` would be an example). It is better to make sure that the
absent values are not coded as the empty string. So the feature data will look
like 2000 lines, each with a node spec, rather than a sequence of 400,000 lines,
most empty.

If you want to leave out just a few isolated cases in a feature where most nodes
get a value, you can do it like this:

```
@node

x0000
...
x1000
1002 x1002
x1003
...
x9999
```

Here all 10,000 nodes get a value, except node `1001`.

## Note on redundancy

Some features assign the same value to many nodes. It is tempting to make a
value definition facility, so that values are coded by short codes, the most
frequent values getting the shortest codes. After some experiments, it turned
out that the overall gain was just 50%.

I find this advantage too small to justify the increased code complexity, and
above all, the reduced transparency of the `.tf` files.

## Examples

Here are a few more and less contrived examples of legal feature data lines.

### Node features

1.  `\t\n`
1.  `2 2\t3`
1.  `foo\nbar`
1.  `1 Escape \t as \\t`

meaning

1.  node 1 has value: *tab* *newline*
1.  node 2 has value: 2 *tab* 3
1.  node 3 has value: foo *newline* bar
1.  node 1 gets a new value: Escape <tab> as `\t`

### Edge features

1.  `1`
1.  `1 2`
1.  `2 3 foo`
1.  `1-2 2-3 bar`

meaning

1.  edge from 1 to 1 with no value
1.  edge from 1 to 2 with no value
1.  edge from 2 to 3 with value foo
1.  four edges: 1->2, 1->3, 2->2, 2->3, all with value bar. Note that edges can
    go from a node to itself. Note also that this line reassigns a value to two
    edges: 1->2 and 2->3.
