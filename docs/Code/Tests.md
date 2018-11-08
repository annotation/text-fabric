# Unit tests

The Text-Fabric program code implements a combinatorical explosion.
There are many environments in which the core engine operates, there
are several apps that make use of it, and there is a built in query language.

One way of mastering the complexity and safeguarding the correctness of it all,
is by employing [unit tests](https://en.wikipedia.org/wiki/Unit_testing).

To my embarrassment, most parts of Text-Fabric are not covered by unit tests.

Here we describe the parts that are covered.
But first a few words about the machinery of unit testing.

## Corpus

We build a [test corpus](https://github.com/Dans-labs/text-fabric/tree/master/test/generic/tf),
wich contains only 10 slots, with node type `sign` and one other node type `part`.

The code to build it is in
[makeTestTf.py](https://github.com/Dans-labs/text-fabric/blob/master/test/generic/makeTestTf.py).

Probably the corpus will be enlarged when new tests are being implemented.

## Framework

We use the [unittest](https://docs.python.org/3/library/unittest.html#module-unittest)
framework that comes with Python.

It is just a few lines to setup a test class, hence we have not yet separated the code
for setting up the tests and the data for the specific test suites.
The fact that we currently have just one test suite does not give much incentive to
factor the framework out right now.

## Relations

The
[basic spatial relations](../Api/General.md#relational-operators)
that are being used in search deserve thorough unit testing.

There are quite a few of them, they describe refined but abstract relations
between nodes and the slots they are linked to, and they are optimized for performance,
which make their implementation error-prone.

For every relationship we test whether it holds or holds not between a bunch
of particular nodes.

The implementation of the relationships tries to determine on before hand whether
its operands are guaranteed to be slots or guaranteed to be non-slots, or whether
no guarantee can be given.
For each particular test, all these cases will be triggered.

All in all we defined
[1000 pairs of nodes](https://github.com/Dans-labs/text-fabric/blob/master/test/generic/relations.py)
leading to 2500 queries, which will
all be tested against expected answers. 
