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

* start node `n`;
* end node `n`.

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

```
from tf.convert.recorder import Recorder

rec = Recorder()

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
--- | ---
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
[tutorial](https://nbviewer.jupyter.org/github/annotation/tutorials/blob/master/bhsa/annotate.ipynb)
"""


from itertools import chain

ZWJ = "\u200d"  # zero width joiner


class Recorder(object):
    def __init__(self):
        """Accumulator of generated text that remembers node positions.
        """
        self.material = []
        """Accumulated text.

        It is a list of chunks of text.
        The text is just the concatenation of all chunks.
        """

        self.nodesByPos = []
        """Mapping from textual positions to nodes.

        It is a list. Entry `p` in this list stores node information
        for character position `p`.
        That node information consists of the set of active nodes
        at that position.
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
            A node. The node can be any node type.
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
        empty: string, optional `zero-width-joiner`
            If the string parameter is `None`, this is the default value
            that will be added to the accumulator.
            If this parameter is absent, the zero-width joiner is used.
        """

        if not string:
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

    def positions(self):
        """Get the node positions.

        Returns
        -------
        list
            Entry `i` in this list contains the frozen set of all
            nodes that were active at character position `i` in the text.
        """
        return self.nodesByPos

    def write(self, textPath, posPath=None):
        """Write the recorder information to disk.

        Parameters
        ----------
        textPath: string
            The file path to which the accumulated text is written.
        posPath: string, optional `None`
            The file path to which the mapped positions are written.
            If absent, it equals `textPath` with `.pos` appended.
            The file format is: one line for each character position,
            on each line a tab-separated list of active nodes.
        """

        posPath = posPath or f"{textPath}.pos"

        with open(textPath, "w", encoding="utf8") as fh:
            fh.write(self.text())

        with open(posPath, "w", encoding="utf8") as fh:
            fh.write(
                "\n".join("\t".join(str(i) for i in nodes) for nodes in self.nodesByPos)
            )

    def read(self, textPath, posPath=None):
        """Read recorder information from disk.

        Parameters
        ----------
        textPath: string
            The file path from which the accumulated text is read.
        posPath: string, optional `None`
            The file path from which the mapped positions are read.
            If absent, it equals `textPath` with `.pos` appended.
            The file format is: one line for each character position,
            on each line a tab-separated list of active nodes.
        """

        posPath = posPath or f"{textPath}.pos"
        self.context = {}

        with open(textPath, encoding="utf8") as fh:
            self.material = list(fh)

        with open(posPath, encoding="utf8") as fh:
            self.nodesByPos = [
                {int(n) for n in line.rstrip("\n").split("\t")} for line in fh
            ]

    def makeFeatures(self, featurePath, headers=True):
        """Read a tab-separated file of annotation data and convert it to features.

        An external annotation tool typically annotates text by assigning values
        to character positions or ranges of character positions.

        In Text-Fabric, annotations are values assigned to nodes.

        If a *recorded* text has been annotated by an external tool,
        we can use the position-to-node mapping to construct Text-Fabric features
        out of it.

        The annotation file is assumed to be a tab-separated file.
        Every line corresponds to an annotation.
        The first two columns have the start and end positions, as character positions
        in the text.
        The remaining columns contain annotation values for that strectch of text.

        If there is a heading column, the values of the headers translate to names
        of the new TF features.

        Parameters
        ----------
        featurePath: string
            Path to the annotation file.
        headers: boolean or iterable, optional `True`
            Indicates whether the annotation file has headers.
            If not True, it may be an iterable of names, which will
            be used as headers.
        """

        nodesByPos = self.nodesByPos

        features = {}

        with open(featurePath, encoding="utf8") as fh:
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
