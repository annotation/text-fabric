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
            paramSpecs=(
                (param1, docLine1),
                (param2, docLine2),
                ...
            ),
        )
    """

    def __init__(self, fileLoc, **kwargs):
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

        python make.py flags params tasks

        Converts data from TEI files

        ARGS

        flags
            Any argument starting with --
        params
            Any argument with an = in it
        tfversion
            Any arg that contains a . is considered to be the tf version number.
            If no version is passed, we resort to the hard coded default.
        tasks
            Any remaining argument

        all
            run all (enabled) tasks

        """
        )
        self.BASE_DOCS = dict(
            tei2tf="TEI => TF",
            page2tf="PageXML => TF",
            watm="TF => WATM",
            watms="multi TF => WATMS",
        )
        self.BASE_FLAGS = dict(
            silent="To run a bit more silent",
            relaxed="Accept XML validation errors",
            usenlp="Will run an NLP pipeline to mark tokens, sentences and entities",
            prod="Delivers WATM in production location",
            force="Force execution even if (uptodate) data is present",
        )
        self.BASE_PARAMS = dict(
            sourceBase="Base directory under which the sources are",
            reportDir="Directory to write report files to",
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
        self.setOptions(**kwargs)

    def setOptions(
        self,
        taskSpecs=(
            ("tei2tf", None),
            ("watm", None),
        ),
        flagSpecs=(
            ("silent", True),
            ("relaxed", None),
            ("usenlp", None),
            ("prod", True),
            ("force", None),
        ),
        paramSpecs=(
            ("sourceBase", None),
            ("reportDir", None),
        ),
        intro=None,
        **kwargs,
    ):
        self.TASKS = []
        self.DOCS = {}
        self.FLAGS = {}
        self.PARAMS = {}
        self.PARAM_DEFAULTS = {}

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
            self.DOCS[name] = self.BASE_DOCS[name] if doc is None else doc

        for name, doc in flagSpecs:
            if name not in self.BASE_FLAGS:
                if doc is None:
                    console(f"flag --{name}: no help text given", error=True)
                    good = False

            if not good:
                continue

            self.FLAGS[name] = doc

        for name, doc in paramSpecs:
            if name not in self.BASE_PARAMS:
                if doc is None:
                    console(f"param {name}=: no help text given", error=True)
                    good = False

            if not good:
                continue

            self.PARAMS[name] = doc

        for (param, value) in kwargs.items():
            if param in self.PARAMS:
                self.PARAM_DEFAULTS[param] = value
            else:
                console(f"Unrecognized parameter {param}='{value}'", error=True)

        self.good = good

        self.HELP = (
            (f"{intro}\n\n" if intro else "")
            + self.BASE_HELP
            + "\nFLAGS\n\n"
            + "".join(f"{name}\n\t{doc}" for (name, doc) in self.FLAGS.items())
            + "\nPARAMS\n\n"
            + "".join(f"{name}\n\t{doc}" for (name, doc) in self.PARAMS.items())
            + "\nTASKS\n\n"
            + "".join(f"{name}\n\t{doc}" for (name, doc) in self.DOCS.items())
            + "\n\nall\n\trun all (enabled) tasks\n\n"
        )

    def warnVersion(self):
        version = self.version
        silent = self.flag_silent

        if version is None:
            console(
                f"No version for the TF data given. Using default: {self.TF_VERSION}"
            )
            self.version = self.TF_VERSION
        else:
            if not silent:
                console(f"Using TF version: {version}")

    def main(self, cmdLine=None, cargs=sys.argv[1:]):
        FLAGS = self.FLAGS
        PARAMS = self.PARAMS
        TASKS = self.TASKS

        if cmdLine is not None:
            cargs = cmdLine.split()

        if "--help" in cargs:
            console(self.HELP)
            return 0

        unrecognized = set()
        tasks = set()
        srcVersion = None
        version = None

        for flag in FLAGS:
            setattr(self, f"flag_{flag}", False)

        for param in PARAMS:
            setattr(self, f"param_{param}", self.PARAM_DEFAULTS.get(param, ""))

        for carg in cargs:
            if carg.startswith("--no-"):
                flag = carg[2:]

                if flag not in FLAGS:
                    unrecognized.add(carg)
                else:
                    setattr(self, f"flag_{flag}", False)

            elif carg.startswith("--"):
                flag = carg[5:]

                if flag not in FLAGS:
                    unrecognized.add(carg)
                else:
                    setattr(self, f"flag_{flag}", True)

            elif "=" in carg and not carg.startswith("="):
                parts = carg.split("=", 1)

                if len(parts) == 1:
                    parts.append("")

                (param, value) = parts

                if param not in PARAMS:
                    unrecognized.add(carg)
                else:
                    setattr(self, f"param_{param}", True)

            elif carg == "all":
                for task in TASKS:
                    tasks.add(task)

            elif carg in TASKS:
                tasks.add(carg)

            elif "-" in carg:
                srcVersion = carg

            elif "." in carg:
                version = carg

            else:
                unrecognized.add(carg)

        silent = self.flag_silent

        if not silent:
            console(f"Enabled tasks: {' '.join(self.TASKS)}")

        self.srcVersion = (
            0 if srcVersion is None else None if srcVersion == "-" else srcVersion
        )
        self.version = version

        if len(unrecognized):
            console(self.HELP)
            console(
                f"Unrecognized arguments: {', '.join(sorted(unrecognized))}", error=True
            )
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
        DOCS = self.DOCS

        for task in TASKS:
            if task not in tasks:
                continue

            console(f"{DOCS[task]} ...")

            method = getattr(self, f"doTask_{task}")
            method()

        return 0 if self.good else 1

    def doTask_tei2tf(self):
        good = self.good
        sourceBase = self.param_sourceBase
        reportDir = self.param_reportDir
        silent = self.flag_silent
        relaxed = self.flag_relaxed
        usenlp = self.flag_usenlp
        srcVersion = self.srcVersion

        if not good:
            if not silent:
                console("Skipping 'produce TF' because of an error condition")
            return

        self.warnVersion()
        tfVersion = self.version
        verbose = -1 if silent else 0
        loadVerbose = DEEP if silent else TERSE

        Tei = TEI(
            verbose=verbose,
            sourceBase=sourceBase,
            reportDir=reportDir,
            tei=srcVersion,
            tf=f"{tfVersion}pre" if usenlp else tfVersion,
        )
        self.teiVersion = Tei.teiVersion

        console("\tValidating TEI ...")

        if not Tei.task(check=True, verbose=verbose, validate=True):
            if relaxed:
                Tei.good = True
            else:
                self.good = False
                return

        console("\tConverting TEI ...")

        if not Tei.task(convert=True, verbose=verbose):
            self.good = False
            return

        console("\tLoading TF ...")

        if not Tei.task(load=True, verbose=verbose):
            self.good = False
            return

        if not silent:
            console("Set up TF-app ...")

        if not Tei.task(app=True, verbose=verbose):
            self.good = False
            return

        if usenlp:
            console("\tAdding NLP data ...")

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

        self.warnVersion()
        tfVersion = self.version
        repoBase = self.repoBase
        sourceDir = f"{repoBase}/organized/source"

        verbose = -1 if silent else 0

        P = PageXML(sourceDir, repoBase, verbose=verbose, source=0, tf=tfVersion)

        if not P.task(convert=True, verbose=verbose):
            self.good = False
            return

        console("\tLoading TF")

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
        prod = self.flag_prod

        if not good:
            if not silent:
                console("Skipping 'produce WATM' because of an error condition")
            return

        backend = self.backend
        org = self.org
        repo = self.repo

        console("\tLoading TF ...")

        loadVerbose = DEEP if silent else TERSE

        A = use(
            f"{org}/{repo}:clone", backend=backend, checkout="clone", silent=loadVerbose
        )

        console(f"\tMaking WATM for version {A.version}")

        WA = WATM(A, "tei", skipMeta=False, silent=silent, prod=prod)
        WA.makeText()
        WA.makeAnno()
        WA.writeAll()
        WA.testAll()

    def doTask_watms(self):
        good = self.good
        silent = self.flag_silent
        prod = self.flag_prod

        if not good:
            if not silent:
                console("Skipping 'produce WATM' because of an error condition")
            return

        backend = self.backend
        org = self.org
        repo = self.repo

        console("\tMaking WATMs")

        W = WATMS(org, repo, backend, "pagexml", silent=silent)
        W.produce(prod=prod)
