from tf.core.files import dirContents, expanduser as ex
from tf.core.helpers import console
from tf.core.timestamp import DEEP
from tf.app import use

from watm import WATM


class WATMS:
    def __init__(self, org, repo, backend):
        self.org = org
        self.repo = repo
        self.backend = backend

        repoDir = ex(f"~/{backend}/{org}/{repo}")
        tfDir = f"{repoDir}/tf"
        docs = dirContents(tfDir)[1]
        console(f"Found {len(docs)} docs in {tfDir}")
        self.docs = docs

    def produce(self, doc=None):
        org = self.org
        repo = self.repo
        backend = self.backend
        docs = self.docs

        chosenDoc = doc

        for doc in sorted(docs, key=lambda x: (x[0], int(x[1:]))):
            if chosenDoc is not None and chosenDoc != doc:
                continue

            console(f"{doc:>5} ... ", newline=False)
            A = use(
                f"{org}/{repo}:clone",
                relative=f"tf/{doc}",
                checkout="clone",
                backend=backend,
                silent=DEEP,
            )
            WA = WATM(A)
            WA.makeText()
            WA.makeAnno()
            WA.writeAll()
