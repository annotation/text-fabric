# Frequently Asked Questions

## I suffer from Github Rate Limiting, what can I do about it?

There are two solutions: 

1. increase your rate limit by making yourself known to GitHub (**recommended**)
2. use previously downloaded data or get data manually from GitHub

An increased rate limit is more than enough for normal use of using Text-Fabric
with default settings. In this scenario, you always work with the latest
release of Text-Fabric data and apps.

The work needed to increase the rate is fairly simple, but it assumes a bit more
knowledge about how your terminal or your command line prompt operates.

If you work very intensely with data, repeatedly accessing many corpora, it
is a waste to access GitHub for every single load action.
In those cases you can pass extra parameters to the commands by which you load
the data.

This does not require any extra knowledge, except a section of the Text-Fabric API
docs. But you must remember that in order to get the data the first time, you
need to pass different parameters than the subsequent times.

All in all, the second solution requires confidence with cloning and pulling
from GitHub and familiarity with all the ways that Text-Fabric can obtain its data.

See the [Github documentation page](../Api/Github.md) for instructions to follow
both solutions.
