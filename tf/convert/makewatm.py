import sys
from textwrap import dedent

from tf.core.helpers import console

from tf.app import use
from tf.convert.tei import TEI
from tf.convert.pagexml import PageXML
from tf.convert.watm import WATMS
from tf.convert.addnlp import NLPipeline
from tf.convert.watm import WATM
from tf.core.files import dirNm, getLocation, abspath
from tf.core.timestamp import DEEP, TERSE

# from tf.advanced.helpers import dm


class MakeWATM:
    """Base class for running conversions to WATM.

    This class has methods to convert corpora from TEI or PageXML to TF and then
    to WATM.

    But if the corpus needs additional preparation, you can make a sub class
    based on this with additional tasks defined an implemented.

    Any class M in m.py based on this class can be called from the command line
    as follows:

        python m.py flags tasks

    If you base a superclass on this, you can register the additional tasks as follows:

    For each extra task xxx, write an method

        doTask_xxx(self)

    Then provide for each task a simple doc line and register them all by:

        self.setOptions(
            taskSpecs=(
                (task1, docLine1),
                (task2, docLine2),
                ...
            ),
            flagSpecs=(
                (flag1, docLine1),
                (flag2, docLine2),
                ...
            ),
        )
    """

    def __init__(self, fileLoc):
        """Localize upon creation.

        When an object of this class is initialized, we assume that the script
        doing it is localized in the `programs` directory in a corpus repo.

        Parameters
        ----------
        fileLoc: string
            The full path of the file that creates an instance of this class.
        """

        self.BASE_HELP = dedent(
            """
        Convert corpus data to WATM.

        USAGE

        python make.py tasks

        Converts data from TEI files

        ARGS

        tfversion
            Any arg that contains a . is considered to be the tf version number.
            If no version is passed, we resort to the hard coded default.

        all
            run all (enabled) tasks

        """
        )
        self.BASE_DOCS = dict(
            tei2tf="Produce text-fabric data from TEI",
            page2tf="Produce text-fabric data from PageXML",
            watm="Produce text/anno repo data for the corpus",
            watms="Produce text/anno repo data for a sequence of corpora",
        )
        self.BASE_FLAGS = dict(
            silent="To run a bit more silent",
            relaxed="Accept XML validation errors",
            usenlp="Will run an NLP pipeline to mark tokens, sentences and entities",
        )
        self.BASE_TASKS = ("tei2tf", "page2tf", "watm", "watms")
        self.TF_VERSION = "0.0.0test"

        self.fileLoc = fileLoc

        self.good = True

        repoBase = dirNm(dirNm(abspath(fileLoc)))
        (self.backend, self.org, self.repo, self.relative) = getLocation(
            targetDir=repoBase
        )
        self.repoBase = repoBase
        self.setOptions()

    def setOptions(
        self,
        taskSpecs=(
            ("tei2tf", None),
            ("watm", None),
        ),
        flagSpecs=(
            ("silent", None),
            ("relaxed", None),
            ("usenlp", None),
        ),
        intro=None,
    ):
        self.TASKS = []
        self.DOCS = {}
        self.FLAGS = {}

        good = True

        for name, doc in taskSpecs:
            if name not in self.BASE_TASKS:
                if doc is None:
                    console(f"task {name}: no help text given", error=True)
                    good = False

                method = f"doTask_{name}"

                if not hasattr(self, method):
                    console(
                        f"task {name}: no method {method} defined in subclass",
                        error=True,
                    )
                    good = False

            if not good:
                continue

            self.TASKS.append(name)
            self.DOCS[name] = doc

        for name, doc in flagSpecs:
            if name not in self.BASE_FLAGS:
                if doc is None:
                    console(f"flag --{name}: no help text given", error=True)
                    good = False

            if not good:
                continue

            self.FLAGS[name] = doc

        self.good = good

        self.HELP = (
            (f"{intro}\n\n" if intro else "")
            + self.BASE_HELP
            + "\nFLAGS\n\n"
            + "".join(f"{name}\n\t{doc}" for (name, doc) in self.FLAGS.items())
            + "\nTASKS\n\n"
            + "".join(f"{name}\n\t{doc}" for (name, doc) in self.DOCS.items())
            + "\n\nall\n\trun all (enabled) tasks\n\n"
        )

    def main(self, cmdLine=None, cargs=sys.argv[1:]):
        FLAGS = self.FLAGS
        TASKS = self.TASKS

        if cmdLine is not None:
            cargs = cmdLine.split()

        if "--help" in cargs:
            console(self.HELP)
            return 0

        unrecognized = set()
        tasks = set()
        self.version = None

        for flag in FLAGS:
            setattr(self, f"flag_{flag}", False)

        for carg in cargs:
            if carg.startswith("--"):
                flag = carg[2:]

                if flag not in FLAGS:
                    unrecognized.add(carg)
                else:
                    setattr(self, f"flag_{flag}", True)
            elif carg == "all":
                for task in TASKS:
                    tasks.add(task)
            elif carg in TASKS:
                tasks.add(carg)
            elif "." in carg:
                version = carg
            else:
                unrecognized.add(carg)

        if not self.flag_silent:
            console(f"Enabled tasks: {' '.join(self.TASKS)}")
        if version is None:
            console(
                f"No version for the TF data given. Using default: {self.TF_VERSION}"
            )
            version = self.TF_VERSION
        else:
            console(f"Using TF version: {version}")

        self.version = version

        if len(unrecognized):
            console(self.HELP)
            console(f"Unrecognized arguments: {', '.join(sorted(unrecognized))}")
            return -1

        if len(tasks) == 0:
            console("Nothing to do")
            return 0

        self.prepareRun(tasks)

        return self.run(tasks)

    def prepareRun(self, tasks):
        return

    def run(self, tasks):
        TASKS = self.TASKS

        for task in TASKS:
            if task not in tasks:
                continue

            method = getattr(self, f"doTask_{task}")
            method()

        return 0 if self.good else 1

    def doTask_tei2tf(self):
        good = self.good
        silent = self.flag_silent
        relaxed = self.flag_relaxed
        usenlp = self.flag_usenlp

        if not good:
            if not silent:
                console("Skipping 'produce TF' because of an error condition")
            return

        tfVersion = self.version
        verbose = -1 if silent else 0
        loadVerbose = DEEP if silent else TERSE

        Tei = TEI(verbose=verbose, tei=0, tf=f"{tfVersion}pre" if usenlp else tfVersion)

        console("Checking TEI ...")

        if not Tei.task(check=True, verbose=verbose, validate=True):
            if relaxed:
                Tei.good = True
            else:
                self.good = False
                return

        console("Converting TEI to TF ...")

        if not Tei.task(convert=True, verbose=verbose):
            self.good = False
            return

        console("Loading TF ...")

        if not Tei.task(load=True, verbose=verbose):
            self.good = False
            return

        if not silent:
            console("Set up TF-app ...")

        if not Tei.task(app=True, verbose=verbose):
            self.good = False
            return

        if usenlp:
            console("Add tokens and sentences ...")

            org = self.org
            repo = self.repo
            backend = self.backend

            Apre = use(
                f"{org}/{repo}:clone",
                backend=backend,
                checkout="clone",
                silent=loadVerbose,
            )
            NLP = NLPipeline(
                lang="it", ner=True, parser=True, verbose=verbose, write=True
            )
            NLP.loadApp(Apre)
            NLP.task(plaintext=True, lingo=True, ingest=True)

            if not NLP.good:
                self.good = False
                return

            if not silent:
                console("Set up TF-app ...")

            if not Tei.task(apptoken=True, verbose=-1):
                self.good = False
                return

            if not Tei.task(load=True, verbose=-1):
                self.good = False
                return

    def doTask_page2tf(self):
        good = self.good
        silent = self.flag_silent

        if not good:
            if not silent:
                console("Skipping 'produce TF' because of an error condition")
            return

        tfVersion = self.version
        repoBase = self.repoBase
        sourceDir = f"{repoBase}/organized/source"

        console("Producing TF")

        verbose = -1 if silent else 0

        P = PageXML(sourceDir, repoBase, verbose=verbose, source=0, tf=tfVersion)

        if not silent:
            console("Converting PageXML to TF ...")

        if not P.task(convert=True, verbose=verbose):
            self.good = False
            return

        if not silent:
            console("Precomputing and loading TF ...")

        console("Loading TF")

        if not P.task(load=True, verbose=verbose):
            self.good = False
            return

        if not silent:
            console("Set up TF-app ...")

        if not P.task(app=True, verbose=verbose):
            self.good = False
            return

        if not P.good:
            self.good = False
            return

    def doTask_watm(self):
        good = self.good
        silent = self.flag_silent

        if not good:
            if not silent:
                console("Skipping 'produce WATM' because of an error condition")
            return

        console("Producing WATM")

        backend = self.backend
        org = self.org
        repo = self.repo

        if not silent:
            console("Loading TF ...")

        loadVerbose = DEEP if silent else TERSE

        A = use(
            f"{org}/{repo}:clone", backend=backend, checkout="clone", silent=loadVerbose
        )

        WA = WATM(A, "tei", skipMeta=False, silent=silent)
        WA.makeText()
        WA.makeAnno()
        WA.writeAll()
        WA.testAll()

    def doTask_watms(self):
        good = self.good
        silent = self.flag_silent

        if not good:
            if not silent:
                console("Skipping 'produce WATM' because of an error condition")
            return

        backend = self.backend
        org = self.org
        repo = self.repo

        console("Producing WATMs")

        W = WATMS(org, repo, backend, "pagexml", silent=silent)
        W.produce()
