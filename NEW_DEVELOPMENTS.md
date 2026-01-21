# Meet Context-Fabric

It is now 2026-01-21.
The date of my (Dirk Roorda's) retirement is 2026-03-01.

I consider my work on Text-Fabric as finished. I'm not saying Text-Fabric
itself is finished, though.

Cody Kingham, who influenced the development of Text-Fabric, especially the capabilities
of its query language, has found an optimization in the way the TF data is represented
in the memory of the computer: by means of memory-mapped Numpy arrays. This is a huge
efficiency gain in memory footprint, without compromising the time performance.

At one stroke, this widens the scenarios in which Text-Fabric can be deployed.
It opens up an interface between Text-Fabric and AI.

Cody chose to take the TF **core** API and reimplement it with his new data
representation.

The result is [Context-Fabric](https://github.com/Context-Fabric/context-fabric), 
characterized as *production-ready corpus analysis for the age of AI*, which is
born out by the fact that it comes with an optional connector to AI servers.

It was with great pleasure that I received word of this new twist from Cody, a few
weeks before my retirement.

Although Context-Fabric does not incorporate the so-called *advanced* API of
Text-Fabric, I am convinced that in time it will move miles beyond my
Text-Fabric, because of the integration with AI.

The advanced API of Text-Fabric offers you easy corpus downloading, and
sophisticated display of query results and corpus fragments. If you rely on
that, Text-Fabric is still the way to go, but that might change, because Cody
already showed that with a little prompting, an AI can also give you nice
displays of snippets of the corpus.

The future as I see it, will have a by now *classic* Text-Fabric, that will not develop
further. I will still respond to issues and fix bugs and change dependencies if the
need arises.

But the cutting edge is Context-Fabric, and if the promises are made true, it will
overshadow Text-Fabric sooner rather than later.

An obvious thing to do could be to also implement the advanced API in Context-Fabric,
but that is up to the discretion of Cody.

Alternatively, someone could replace the current data representation in Text-Fabric
by the much more efficient representation in Context-Fabric. But I am not the
one who will do it. If someone else feels attracted to it, I will lend the
support that is needed, but without diving deep in the code myself.
Keep in mind though, that it might be a spurious effort. A core Text-Fabric +
AI (= Context-Fabric) might progress better and faster than an optimized but classic
TF!

I'll keep an eye on the two of you: Text-Fabric and Context-Fabric.
