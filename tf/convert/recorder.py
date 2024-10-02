"""
# Recorder

Support for round trips of TF data to annotation tools and back.

The scenario is:

*   Prepare a piece of corpus material for plain text use in an annotation tool,
    e.g. [BRAT](https://brat.nlplab.org).
*   Alongside the plain text, generate a mapping file that maps nodes to
    character positions in the plain text
*   Use an annotation tool to annotate the plain text
*   Read the output of the annotation tools and convert it into TF features,
    using the mapping file.

## Explanation

The recorder object is an engine to which you can send text material, interspersed
with commands that say:

*   start node `n`;
*   end node `n`.

The recorder stores the accumulating text as a plain text, without any
trace of the `start` and `end` commands.
However, it also maintains a mapping between character positions in the
accumulated text and the nodes.

At any moment, there is a set of *active* nodes: the ones that have been started,
but not yet ended.

Every character of text that has been sent to the recorder
will add an entry to the position mapping: it maps the position of that character
to the set of active nodes at that point.

## Usage

We suppose you have a corpus loaded, either by

``` python
from tf.app import use
A = use(corpus)
api = A.api
```

or by

``` python
from tf.fabric import Fabric
TF = Fabric(locations, modules)
api = TF.load(features)
```

``` python
from tf.convert.recorder import Recorder

rec = Recorder(api)

rec.add("a")

rec.start(n1)

rec.add("bc")

rec.start(n2)

rec.add("def")

rec.end(n1)

rec.add("ghij")

rec.end(n2)

rec.add("klmno")
```

This leads to the following mapping:

position | text | active nodes
--- | --- | ---
0 | `a` | `{}`
1 | `b` | `{n1}`
2 | `c` | `{n1}`
3 | `d` | `{n1, n2}`
4 | `e` | `{n1, n2}`
5 | `f` | `{n1, n2}`
6 | `g` | `{n2}`
7 | `h` | `{n2}`
8 | `i` | `{n2}`
9 | `j` | `{n2}`
10 | `k` | `{}`
11 | `l` | `{}`
12 | `m` | `{}`
13 | `n` | `{}`
14 | `o` | `{}`

There are methods to obtain the accumulated text and the mapped positions from the
recorder.

You can write the information of a recorder to disk and read it back later.

And you can generate features from a CSV file using the mapped positions.

To see it in action, see this
[tutorial](https://nbviewer.jupyter.org/github/ETCBC/bhsa/blob/master/tutorial/annotate.ipynb)
"""


from textwrap import dedent
from itertools import chain

from ..core.helpers import (
    specFromRangesLogical,
    specFromRanges,
    rangesFromSet,
)
from ..core.files import fileOpen, expanduser as ex, splitExt, initTree, dirNm
from ..core.helpers import console


ZWJ = "\u200d"  # zero width joiner


class Recorder:
    def __init__(self, api=None):
        """Accumulator of generated text that remembers node positions.

        Parameters
        ----------
        api: object, optional None
            The handle of the API of a loaded TF corpus.
            This is needed for operations where the recorder needs
            TF intelligence associated with the nodes, e.g. their types.
            If you do not pass an `api`, such methods are unavailable later on.
        """
        self.api = api

        self.material = []
        """Accumulated text.

        It is a list of chunks of text.
        The text is just the concatenation of all these chunks.
        """

        self.nodesByPos = []
        """Mapping from textual positions to nodes.

        It is a list. Entry `p` in this list stores the set of active nodes
        for character position `p`.
        """

        self.context = set()
        """The currently active nodes.
        """

    def start(self, n):
        """Start a node.

        That means: add it to the context, i.e. make the node active.

        Parameters
        ----------
        n: integer
            A node. The node can be any node type.
        """
        self.context.add(n)

    def end(self, n):
        """End a node.

        That means: delete it from the context, i.e. make the node inactive.

        Parameters
        ----------
        n: integer
            A node. The node can be of any node type.
        """
        self.context.discard(n)

    def add(self, string, empty=ZWJ):
        """Add text to the accumulator.

        Parameters
        ----------
        string: string | None
            Material to add.
            If it is a string, the string will be added to the accumulator.
            If it is `None`, a default value will be added.
            The default value is passed through parameter `empty`.
        empty: string, optional zero-width-joiner
            If the string parameter is `None`, this is the default value
            that will be added to the accumulator.
            If this parameter is absent, the zero-width joiner is used.
        """

        if string is None:
            string = empty
        self.material.append(string)
        self.nodesByPos.extend([frozenset(self.context)] * len(string))

    def text(self):
        """Get the accumulated text.

        Returns
        -------
        string
            The join of all accumulated text chunks.
        """
        return "".join(self.material)

    def positions(self, byType=False, simple=False):
        """Get the node positions as mapping from character positions.

        Character positions start at `0`.
        For each character position we get the set of nodes whose material
        occupies that character position.

        Parameters
        ----------
        byType: boolean, optional False
            If True, makes a separate node mapping per node type.
            For this it is needed that the Recorder has been
            passed a TF API when it was initialized.
        simple: boolean, optional False
            In some cases it is known on beforehand that at each textual position
            there is at most 1 node.
            Then it is more economical to fill the list with single nodes
            rather than with sets of nodes.
            If this parameter is True, we pick the first node from the set.

        Returns
        -------
        list|dict|None
            If `byType`, the result is a dictionary, keyed by node type,
            valued by mappings of textual positions to nodes of that type.
            This mapping takes the shape of a list where entry `i`
            contains the frozen set of all nodes of that type
            that were active at character position `i` in the text.

            If not `byType` then a single mapping is returned (as list),
            where entry `i` contains the frozen set of all
            nodes, irrespective of their type
            that were active at character position `i` in the text.
        """

        if not byType:
            if simple:
                return tuple(list(x)[0] if x else None for x in self.nodesByPos)
            return self.nodesByPos

        api = self.api
        if api is None:
            console(
                dedent(
                    """\
                    Cannot determine node types without a TF api.
                    You have to call Recorder(`api`) instead of Recorder()
                    where `api` is the result of
                    tf.app.use(corpus)
                    or
                    tf.Fabric(locations, modules).load(features)
                """
                )
            )
            return None

        F = api.F
        Fotypev = F.otype.v
        info = api.TF.info
        indent = api.TF.indent

        indent(level=True, reset=True)
        info("gathering nodes ...")

        allNodes = set(chain.from_iterable(self.nodesByPos))
        allTypes = {Fotypev(n) for n in allNodes}
        info(f"found {len(allNodes)} nodes in {len(allTypes)} types")

        nodesByPosByType = {nodeType: [] for nodeType in allTypes}

        info("partitioning nodes over types ...")

        for nodeSet in self.nodesByPos:
            typed = {}
            for node in nodeSet:
                nodeType = Fotypev(node)
                typed.setdefault(nodeType, set()).add(node)
            for nodeType in allTypes:
                thisSet = (
                    frozenset(typed[nodeType]) if nodeType in typed else frozenset()
                )
                value = (list(thisSet)[0] if thisSet else None) if simple else thisSet
                nodesByPosByType[nodeType].append(value)

        info("done")
        indent(level=False)
        return nodesByPosByType

    def iPositions(self, byType=False, logical=True, asEntries=False):
        """Get the character positions as mapping from nodes.

        Parameters
        ----------
        byType: boolean, optional False
            If True, makes a separate node mapping per node type.
            For this it is needed that the Recorder has been
            passed a TF API when it was initialized.
        logical: boolean, optional True
            If True, specs are represented as tuples of ranges
            and a range is represented as a tuple of a begin and end point,
            or as a single point.
            Points are integers.
            If False, ranges are represented by strings: `,` separated ranges,
            a range is `b-e` or `p`.
        asEntries: boolean, optional False
            If True, do not return the dict, but rather its entries.

        Returns
        -------
        list|dict|None
            If `byType`, the result is a dictionary, keyed by node type,
            valued by mappings for nodes of that type.
            Entry `n` in this mapping contains the intervals of all
            character positions in the text where node `n` is active.

            If not `byType` then a single mapping is returned, where each node
            is mapped to the intervals where that node is active.
        """

        method = specFromRangesLogical if logical else specFromRanges
        posByNode = {}
        for i, nodeSet in enumerate(self.nodesByPos):
            for node in nodeSet:
                posByNode.setdefault(node, set()).add(i)
        for n, posSet in posByNode.items():
            posByNode[n] = method(rangesFromSet(posSet))

        if asEntries:
            posByNode = tuple(posByNode.items())
        if not byType:
            return posByNode

        api = self.api
        if api is None:
            console(
                dedent(
                    """\
                    Cannot determine node types without a TF api.
                    You have to call Recorder(`api`) instead of Recorder()
                    where `api` is the result of
                        tf.app.use(corpus)
                        or
                        tf.Fabric(locations, modules).load(features)
                    """
                )
            )
            return None

        F = api.F
        Fotypev = F.otype.v

        posByNodeType = {}
        if asEntries:
            for n, spec in posByNode:
                nType = Fotypev(n)
                posByNodeType.setdefault(nType, []).append((n, spec))
        else:
            for n, spec in posByNode.items():
                nType = Fotypev(n)
                posByNodeType.setdefault(nType, {})[n] = spec

        return posByNodeType

    def rPositions(self, acceptMaterialOutsideNodes=False):
        """Get the first textual position for each node

        The position information is a big amount of data, in the general case.
        Under certain assumptions we can economize on this data usage.

        Strong assumptions:

        1.  every textual position is covered by **exactly one node**;
        1.  the nodes are consecutive:
            every next node is equal to the previous node plus 1;
        1.  the positions of the nodes are monotonous in the nodes, i.e.
            if node `n < m`, then the position of `n` is before the position of `m`.

        Imagine the text partitioned in consecutive non-overlapping chunks, where
        each node corresponds to exactly one chunk, and the order of the nodes
        is the same as the order of the corresponding chunks.

        We compute a list of positions that encode the mapping from nodes to textual
        positions as follows:

        Suppose we need map nodes `n`, `n+1`, ..., `n+m` to textual positions;
        say

        *   node `n` starts at position `t0`,
        *   node `n+1` at position `t1`,
        *   node `n+m` at position `tm`.

        Say position `te` is the position just after the whole text covered by these
        nodes.

        Then we deliver the mapping as a sequence of these numbers:

        *   `n-1`
        *   `t0`
        *   `t1`
        *   ...
        *   `tm`
        *   `te`

        So the first element of the list is used to specify the offset to be
        applied for all subsequent nodes.
        The `te` value is added as a sentinel, to facilitate the determination
        of the last position of each node.

        Users of this list can find the start and end positions of node `m`
        as follows

        ```
        start = posList[m - posList[0]]
        end   = posList[m - posList[0] + 1] - 1
        ```

        Parameters
        ----------
        acceptMaterialOutsideNodes: boolean, optional False
            If this is True, we accept that the text contains extra material that is not
            covered by any node.
            That means that condition 1 above is relaxed to that we accept that
            some textual positions do not correspond to any node.

            Applications that make use of the positions must realize that in this case
            the material associated with a node also includes the subsequent material
            outside any node.

        Returns
        -------
        list | string
            The result is a list of numbers as described above.

            We only return the `posList` if the assumptions hold.

            If not, we return a string with diagnostic information.
        """

        good = True
        multipleNodes = 0
        multipleFirst = 0
        noNodes = 0
        noFirst = 0
        nonConsecutive = 0
        nonConsecutiveFirst = 0

        posByNode = {}
        for i, nodeSet in enumerate(self.nodesByPos):
            if (not acceptMaterialOutsideNodes and len(nodeSet) == 0) or len(
                nodeSet
            ) > 1:
                good = False
                if len(nodeSet) == 0:
                    if noNodes == 0:
                        noFirst = i
                    noNodes += 1
                else:
                    if multipleNodes == 0:
                        multipleFirst = i
                    multipleNodes += 1
                continue
            for node in nodeSet:
                if node in posByNode:
                    continue
                posByNode[node] = i

        lastI = i

        if not good:
            msg = ""
            if noNodes:
                msg += (
                    f"{noNodes} positions without node, "
                    f"of which the first one is {noFirst}\n"
                )
            if multipleNodes:
                msg += (
                    f"{multipleNodes} positions with multiple nodes, "
                    f"of which the first one is {multipleFirst}\n"
                )
            return msg

        sortedPosByNode = sorted(posByNode.items())
        offset = sortedPosByNode[0][0] - 1
        posList = [offset]
        prevNode = offset
        for node, i in sortedPosByNode:
            if prevNode + 1 != node:
                good = False
                if nonConsecutive == 0:
                    nonConsecutiveFirst = f"{prevNode} => {node}"
                nonConsecutive += 1
            else:
                posList.append(i)
            prevNode = node
        posList.append(lastI)

        if not good:
            return (
                f"{nonConsecutive} nonConsecutive nodes, "
                f"of which the first one is {nonConsecutiveFirst}"
            )
        return posList

    def write(
        self, textPath, inverted=False, posPath=None, byType=False, optimize=True
    ):
        """Write the recorder information to disk.

        The recorded text is written as a plain text file,
        and the remembered node positions are written as a TSV file.

        You can also have the node positions be written out by node type.
        In that case you can also optimize the file size.

        Optimization means that consecutive equal values are prepended
        by the number of repetitions and a `*`.

        Parameters
        ----------
        textPath: string
            The file path to which the accumulated text is written.
        inverted: boolean, optional False
            If False, the positions are taken as mappings from character
            positions to nodes. If True, they are a mapping from nodes to
            character positions.
        posPath: string, optional None
            The file path to which the mapped positions are written.
            If absent, it equals `textPath` with a `.pos` extension, or
            `.ipos` if `inverted` is True.
            The file format is: one line for each character position,
            on each line a tab-separated list of active nodes.
        byType: boolean, optional False
            If True, writes separate node mappings per node type.
            For this it is needed that the Recorder has been
            passed a TF API when it was initialized.
            The file names are extended with the node type.
            This extension occurs just before the last `.` of the inferred `posPath`.
        optimize: boolean, optional True
            Optimize file size. Only relevant if `byType` is True
            and `inverted` is False.
            The format of each line is:

            `rep * nodes`

            where `rep` is a number that indicates repetition and `nodes`
            is a tab-separated list of node numbers.

            The meaning is that the following `rep` character positions
            are associated with these `nodes`.
        """

        textPath = ex(textPath)
        posExt = ".ipos" if inverted else ".pos"
        posPath = ex(posPath or f"{textPath}{posExt}")

        textDir = dirNm(textPath)
        initTree(textDir)

        with fileOpen(textPath, mode="w") as fh:
            fh.write(self.text())

        if not byType:
            posDir = dirNm(posPath)
            initTree(posDir)
            with fileOpen(posPath, mode="w") as fh:
                if inverted:
                    fh.write(
                        "\n".join(
                            f"{node}\t{intervals}"
                            for (node, intervals) in self.iPositions(
                                byType=False, logical=False, asEntries=True
                            )
                        )
                    )
                else:
                    fh.write(
                        "\n".join(
                            "\t".join(str(i) for i in nodes)
                            for nodes in self.nodesByPos
                        )
                    )
                fh.write("\n")
            return

        mapByType = (
            self.iPositions(byType=True, logical=False, asEntries=True)
            if inverted
            else self.positions(byType=True)
        )
        if mapByType is None:
            console("No position files written")
            return

        (base, ext) = splitExt(posPath)

        # if we reach this, there is a TF api

        api = self.api
        info = api.TF.info
        indent = api.TF.indent

        indent(level=True, reset=True)

        for nodeType, mapping in mapByType.items():
            fileName = f"{base}-{nodeType}{ext}"
            info(f"{nodeType:<20} => {fileName}")
            with fileOpen(fileName, mode="w") as fh:
                if inverted:
                    fh.write(
                        "\n".join(
                            f"{node}\t{intervals}" for (node, intervals) in mapping
                        )
                    )
                else:
                    if not optimize:
                        fh.write(
                            "\n".join(
                                "\t".join(str(i) for i in nodes) for nodes in mapping
                            )
                        )
                    else:
                        repetition = 1
                        previous = None

                        for nodes in mapping:
                            if nodes == previous:
                                repetition += 1
                                continue
                            else:
                                if previous is not None:
                                    prefix = f"{repetition}*" if repetition > 1 else ""
                                    value = "\t".join(str(i) for i in previous)
                                    fh.write(f"{prefix}{value}\n")
                                repetition = 1
                                previous = nodes
                        if previous is not None:
                            prefix = f"{repetition + 1}*" if repetition else ""
                            value = "\t".join(str(i) for i in previous)
                            fh.write(f"{prefix}{value}\n")

        indent(level=False)

    def read(self, textPath, posPath=None):
        """Read recorder information from disk.

        Parameters
        ----------
        textPath: string
            The file path from which the accumulated text is read.
        posPath: string, optional None
            The file path from which the mapped positions are read.
            If absent, it equals `textPath` with the extension `.pos` .
            The file format is: one line for each character position,
            on each line a tab-separated list of active nodes.

            !!! caution
                Position files that have been written with `optimize=True` cannot
                be read back.
        """

        textPath = ex(textPath)
        posPath = ex(posPath or f"{textPath}.pos")
        self.context = {}

        with fileOpen(textPath) as fh:
            self.material = list(fh)

        with fileOpen(posPath) as fh:
            self.nodesByPos = [
                {int(n) for n in line.rstrip("\n").split("\t")}
                if line != "\n"
                else set()
                for line in fh
            ]

    def makeFeatures(self, featurePath, headers=True):
        """Read a tab-separated file of annotation data and convert it to features.

        An external annotation tool typically annotates text by assigning values
        to character positions or ranges of character positions.

        In TF, annotations are values assigned to nodes.

        If a *recorded* text has been annotated by an external tool,
        we can use the position-to-node mapping to construct TF features
        out of it.

        The annotation file is assumed to be a tab-separated file.
        Every line corresponds to an annotation.
        The first two columns have the start and end positions, as character positions
        in the text.
        The remaining columns contain annotation values for that stretch of text.

        If there is a heading column, the values of the headers translate to names
        of the new TF features.

        Parameters
        ----------
        featurePath: string
            Path to the annotation file.
        headers: boolean or iterable, optional True
            Indicates whether the annotation file has headers.
            If not True, it may be an iterable of names, which will
            be used as headers.
        """

        featurePath = ex(featurePath)
        nodesByPos = self.nodesByPos

        features = {}

        with fileOpen(featurePath) as fh:
            if headers is True:
                names = next(fh).rstrip("\n").split("\t")[2:]
            elif headers is not None:
                names = headers
            else:
                names = None

            for line in fh:
                (start, end, *data) = line.rstrip("\n").split("\t")
                if names is None:
                    names = tuple(f"f{i}" for i in range(1, len(data) + 1))
                nodes = set(
                    chain.from_iterable(
                        nodesByPos[i] for i in range(int(start), int(end) + 1)
                    )
                )
                for n in nodes:
                    for i in range(len(names)):
                        val = data[i]
                        if not val:
                            continue
                        name = names[i]
                        features.setdefault(name, {})[n] = val

        return features
