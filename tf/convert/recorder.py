"""
.. include:: ../../docs/convert/recorder.md
"""

from itertools import chain

ZWJ = "\u200d"  # zero width joiner


class Recorder(object):
    def __init__(self):
        self.material = []
        self.nodesByPos = []
        self.context = set()

    def start(self, n):
        self.context.add(n)

    def end(self, n):
        self.context.discard(n)

    def add(self, string, empty=ZWJ):
        if not string:
            string = empty
        self.material.append(string)
        self.nodesByPos.extend([frozenset(self.context)] * len(string))

    def text(self):
        return "".join(self.material)

    def positions(self):
        return self.nodesByPos

    def write(self, textPath, posPath=None):
        posPath = posPath or f"{textPath}.pos"

        with open(textPath, "w", encoding="utf8") as fh:
            fh.write(self.text())

        with open(posPath, "w", encoding="utf8") as fh:
            fh.write(
                "\n".join("\t".join(str(i) for i in nodes) for nodes in self.nodesByPos)
            )

    def read(self, textPath, posPath=None):
        posPath = posPath or f"{textPath}.pos"
        self.context = {}

        with open(textPath, encoding="utf8") as fh:
            self.material = list(fh)

        with open(posPath, "w", encoding="utf8") as fh:
            self.nodesByPos = [
                {int(n) for n in line.rstrip("\n").split("\t")} for line in fh
            ]

    def makeFeatures(self, featurePath, headers=True):
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
