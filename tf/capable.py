"""Dependency management.

TF is dependent on a number of external Python libraries, but not many.

However, for a number of specialized tasks, most having to do with corpus preparation,
extra libraries are involved.
We have chosen not to list them as dependencies, because if one of them does not install
for some reason or another, the installability of TF as a whole is compromised, even
for users that are not going to do the things for which those modules are needed.

We have two kinds of external dependencies in TF: optional and incidental.

## Incidental  dependencies

The class `CheckImport` deals with incidental dependencies.

These dependencies are needed by modules in the periphery of TF.
They are managed here. If a part of TF that needs them does not find them installed,
it will gracefully refuse to work and gives a hint to the user how to install
the module.

## Optional dependencies

The class `Capable` deals with optional dependencies.

They correspond with options during the installation of TF, like

``` sh
pip install 'text-fabric[option]'
```

This will trigger `pip` to also install the `github` module.

TF knows 2 options:

option name | module name | installation name
--- | --- | ---
`github` | `github` | `pygithub`
`gitlab` | `gitlab` | `python-gitlab`
`all` | both of the above | both of the above

So if you do

``` sh
pip install 'text-fabric[all]'
```

both `pygithub` and `python-gitlab` will be installed as dependencies.

See also
[setup.cfg](https://github.com/annotation/text-fabric/blob/master/setup.cfg)
under section `[options.extras_require]` .
"""

from textwrap import dedent
from importlib import import_module

from .core.helpers import console


HINTS = dict(
    pyarrow=dedent(
        """\
        Sometimes pyarrow cannot be installed in the latest version of Python.
        Either revert to an earlier version of Python or wait till the
        developers have built wheels for pyarrow.
        See this issue: https://github.com/apache/arrow/issues/37880
        """
    ),
)
"""Known issues during installation of dependencies."""

INCIDENTAL_DEPS = dict(
    pandas=("pandas", "pandas"),
    pyarrow=("pyarrow", "pyarrow"),
    lxml=("lxml.etree", "lxml"),
    openpyxl=("openpyxl", "openpyxl"),
    spacy=("spacy", "spacy"),
    spacyd=("spacy.cli.download", "spacy"),
    pagexml=("pagexml.parser", "pagexml-tools"),
    marimo=("marimo", "marimo"),
    analiticcl=("analiticcl", "analiticcl"),
)
"""The incidendtal dependencies of TF.

Keys are labels indicating the module as a whole.

Values are tuples: the first part is what must be imported,
the second part is what should be installed.
"""


class CheckImport:
    def __init__(self, *modules, optional=False):
        """Import modules if possible.

        You can use this class as a base class for each class you define where
        modules are needed whose presence is needed but not assumed.

        The sequence is this:

        Try to load a bunch of modules:

            CI = CheckImport("module1", "module2", ...)

        Then check the success and load the modules by

            if CI.importOK(hint=True):
                (module1, module2, ...) = CI.importGet()
            else:
                return

        If all modules have successfully been imported, their semantics is now stored
        in the variables `module1`, `module2`, ...
        If one or more of them could not be imported, no semantics is stored,
        and the function in which you used this code is exited.

        The `hint=True` will print an installation instruction to the output.

        You can also use this class as the base class of another class.
        When you create an instance of the class, you check whether all modules
        can be loaded. The result of this check is now stored in the object.

        So, in the initialization function of your class, right at the beginning,
        say:

            super().__init__("module1", "module2", ...)
            if self.importOK(hint=True):
                (module1, module2, ... ) = self.importGet()
            else:
                return

        You can put a check in every method invocation easily.
        Right at the beginning of each relevant method, say


            if not self.importOK():
                return

        At this point, you'll probably not need to repeat the installation hint.

        Parameters
        ----------
        modules: iterable
            Each item is a key in `tf.capable.INCIDENTAL_DEPS`

        optional: boolean, optional False
            If True, the loading of these modules is optional and will not generate
            warnings.
        """
        self.optional = optional

        semantics = []
        mods = []
        pipmods = []

        self.semantics = semantics
        self.mods = mods
        self.pipmods = pipmods

        for module in modules:
            info = INCIDENTAL_DEPS.get(module, None)

            if info is None:
                console("Unknown module spec: {module}")
                semantic = None
            else:
                (mod, pipmod) = info
                try:
                    semantic = import_module(mod)
                except Exception:
                    semantic = None

            semantics.append(semantic)
            mods.append(mod)
            pipmods.append(pipmod)

        missingMods = []
        missingPipmods = []

        for mod, pipmod, sem in zip(mods, pipmods, semantics):
            if sem is not None:
                continue

            missingMods.append(mod)
            missingPipmods.append(pipmod)

        self.missingMods = missingMods
        self.missingPipmods = missingPipmods

        if len(missingMods):
            self.properlySetup = False

            modsRep = ", ".join(missingMods)

            self.message = (
                f"Refuse to execute because of uninstalled modules:\n\t{modsRep}"
            )
            pipmodsRep = "\n".join(f"\tpip install {pip}" for pip in missingPipmods)

            self.imessage = f"Install these modules as follows:\n{pipmodsRep}"

            theseHints = []

            for mod in missingMods:
                if mod in HINTS:
                    hintRep = "\n\t".join(HINTS[mod].split("\n"))
                    theseHints.append(f"{mod}: {hintRep}\n")

            if len(theseHints):
                hintRep = "".join(theseHints)
                self.imessage += f"\n\nAdditional installation hints:\n\n{hintRep}"
        else:
            self.properlySetup = True

    def importOK(self, hint=False):
        """Reports the result of the import attempts.

        It will print a message with the missing modules, if any.

        Parameters
        ----------
        hint: boolean, optional False
            If True, it will also print a `pip install` statement for each missing
            module.

        Returns
        -------
        boolean
            Whether all imports were successful.
        """
        optional = self.optional
        properlySetup = self.properlySetup

        if not optional and not properlySetup:
            console(self.message)
            if hint:
                console(self.imessage)

        return properlySetup

    def importGet(self):
        """Delivers the imported modules.

        Returns
        -------
        list | any
            For each item in the list of modules with which this instance was
            initialized, it returns the imported module object if successful,
            or None.

            If there is only one module in the list, it returns the single object,
            not packed in a 1-element list.
        """
        semantics = self.semantics
        return semantics[0] if len(semantics) == 1 else semantics


class Capable:
    """Import modules for back-end communication if possible.

    This class is meant to manage the back-end capabilities of TF and make them known
    to the rest of the application.

    When TF tries to download data from GitHub or GitLab, it first looks
    for the presence of a file `complete.zip` attached to the latest release.
    Most corpora in the `tf.about.corpora` provide that file.
    Users that just want the latest release of the latest version of the data are
    served in this way.

    Users that want to go back to previous versions or commits need the modules
    `pygithub` and/or `python-gitlab`.
    They are *optional* dependencies of TF.

    For most users, in most cases a plain installation of TF without the extra options
    will suffice.

    Only a fraction of users will need to do one of the following

    ``` sh
    pip install `text-fabric[github]`
    pip install `text-fabric[gitlab]`
    pip install `text-fabric[gitall]`
    ```

    When TF is asked to perform operations that need these modules, it will
    import them if possible, and otherwise ask the user to install them.
    """

    def __init__(self, *extras):
        self.backendProviders = set()
        self.modules = {}
        self.tryImport(*extras)

    def tryImport(self, *extras):
        backendProviders = self.backendProviders
        modules = self.modules

        for kind in extras:
            if kind == "github":
                try:
                    import github

                    modules["github"] = github
                    backendProviders.add(kind)
                except Exception:
                    pass

            elif kind == "gitlab":
                try:
                    import gitlab

                    modules["gitlab"] = gitlab
                    backendProviders.add(kind)
                except Exception:
                    pass

    def load(self, module):
        modules = self.modules
        loaded = modules.get(module, None)

        if loaded:
            return loaded

        try:
            loaded = import_module(module)
        except Exception:
            pass

        return loaded

    def loadFrom(self, module, *members):
        loaded = self.load(module)

        result = (
            tuple(getattr(loaded, member, None) for member in members)
            if loaded
            else tuple(None for x in members)
        )
        return result[0] if len(result) == 1 else result

    def can(self, extra):
        if extra in {"github", "gitlab"}:
            backendProviders = self.backendProviders

            if extra in backendProviders:
                return True

            console(
                dedent(
                    f"""
                    Backend provider {extra} not supported.
                    Cannot reach online data on {extra}
                    Try installing text-fabric one of the following:
                    pip install text-fabric[{extra}]
                    pip install text-fabric[all]
            """
                )
            )
            return False
