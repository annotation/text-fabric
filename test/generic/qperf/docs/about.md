# 2019-05-25

## reference set A

Slightly modified the search algorithm, but it performs roughly as before.
that performs roughly as before.

The yarnRatio has been varied between 1.0 and 1.7 in steps of 0.1
the try limits have been kept fixed to 100.

When spinning and stitiching, we order the edges by the amount of expected work,
measured as the product of the sizes of the yarns at each end of an edge
and the spread of the edge.

