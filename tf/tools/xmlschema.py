"""
## Meaningful information from XML schemas.

When parsing XML it is sometimes needed to know the properties of the current
element, especially whether it allows mixed content or not.

If it does not, it is safe to discard white-space, otherwise not.

Moreover, if there are two adjacent elements, each containing text, are
the string at the end of the first element and the string at the start
of the second element part of the same word?

If both elements are contained in a element that does not allow mixed content,
they are separate words (the XML-elements are used as data containers);
otherwise they belong to the same word (the XML-elements annotate a piece
of string).

This module can perform several analysis tasks of xml schemas.

**fromrelax** task:

Transforms a RelaxNG schema into an equivalent xsd schema using James Clark's
trang library.  For this, you must have java installed.

**analyse** task:

Given an XML schema file, produces a tab-separated list of elements defined in
the schema, with columns

    (element name) (simple or complex) (mixed or pure content)

**tei** task:

Analyses the complete TEI schema plus optional customizations on top of it.  If
you pass an optional customized TEI schema, it will be analysed separately, and
the result will be used to override the result of analysing the complete TEI
schema.  The complete TEI schema is part of this package, you do not have to
provide it.  It has been generated on with the online
[TEI-Roma tool](https://roma.tei-c.org/startroma.php).

!!! note "Caution"
    This code has only been tested on a single xsd, converted from a relaxRNG
    file produced by a customisation of TEI.

    It could very well be that I have missed parts of the semantics of XML-Schema.

## Usage

This program can be used as a library or as a command line tool.

### As command-line tool

``` sh
xmlschema fromrelax schema.rng
xmlschema analyse schema.xsd
xmlschema tei customschema.xsd
xmlschema tei
```

Here `customschema` and `schema` are variable arguments.

The result is written to a file in the current directory
(from where the command `xmlschema` is called):

*   from task `fromrelax` is a file *schema*`.xsd`;
*   from task `analysis` is written to *schema*`.tsv;
*   from task `tei` is written to *customschema*`.tsv.

### As library

You can write a script with exactly the same behaviour as the `xmlschema` command
as follows:

``` python
from tf.tools.xmlschema import Analysis
A = Analysis()
A.run()
```

You can run individual commands:

``` python
from tf.tools.xmlschema import Analysis
A = Analysis()
good = A.task("tei", "customSchema.xsd")
good = A.task("analysis", "schema.xsd"))
good = A.task("fromrelax", "schema.rng")
```

In order to get the analysis results after tasks `tei` and `analysis`:

``` python
if good:
    result = A.getDefs(asTsv=False)
    result = A.getDefs(asTsv=True)
```

You can also work a bit more low-level, e.g. to run the tei task:

``` python
from tf.tools.xmlschema import Analysis
A = Analysis()
A.configure(override=schemaFile)
A.interpret()
if not A.good:
    quit()
defs = A.getDefs()}
```

"""

import sys
import collections
from subprocess import run

from lxml import etree

from ..core.helpers import console
from ..core.files import fileExists, baseNm, dirNm, abspath


class Analysis:
    types = set(
        """
        simpleType
        complexType
        """.strip().split()
    )

    notInteresting = set(
        """
        attribute
        attributeGroup
        group
        """.strip().split()
    )

    @staticmethod
    def help():
        console(
            """
            USAGE

            Command line:

            xmlschema tei [customschemafile.xsd]
            xmlschema analyse {schemafile.xsd}
            xmlschema fromrelax {schemafile.rng}

            """
        )

    def __init__(self, debug=False, verbose=-1):
        """Trivial initialization of the Analysis class.

        Further configuration happens in the `configure` method.

        Parameters
        ----------
        debug: boolean, optional False
            Whether to run in debug mode or not.
            In debug mode more information is shown on the console.
        verbose: integer, optional -1
            Produce no (-1), some (0) or many (1) orprogress and reporting messages
        """

        self.verbose = verbose
        self.debug = debug
        self.myDir = dirNm(abspath(__file__))
        self.setModes(debug=debug, verbose=verbose)

    def setModes(self, debug=False, verbose=-1):
        """Sets debug and verbose modes.

        See `tf.tools.xmlschema.Analysis`
        """
        self.debug = debug
        self.verbose = verbose

    def configure(self, baseSchema=None, override=None):
        """Configure for an XML schema and overrides

        Parameters
        ----------
        baseSchema: string, optional None
            The path of the xsd file that acts as the base schema that we want
            to analyse. If None, the complete TEI schema is chosen.
        override: string, optional None
            The path of another schema intended to override parts of the baseSchema.
        debug: boolean, optional False
            Whether to run in debug mode or not.
            In debug mode more information is shown on the console.
        """

        verbose = self.verbose

        if baseSchema is None:
            myDir = self.myDir
            baseSchema = f"{myDir}/tei/tei_all.xsd"

        self.baseSchema = baseSchema
        self.baseSchemaDir = dirNm(baseSchema)
        self.override = override
        self.overrideDir = None if override is None else dirNm(override)

        def findImports(node):
            """Inner function to walk through the xsd and get the import statements.

            This function is called recursively for child nodes.

            Parameters
            ----------
            node: Object
                The current node.
            """
            tag = etree.QName(node.tag).localname
            if tag == "import":
                otherFile = node.attrib.get("schemaLocation", "??")
                if otherFile not in {"xml.xsd", "teix.xsd"}:
                    sep = "/" if schemaDir else ""
                    otherPath = f"{schemaDir}{sep}{otherFile}"
                    otherExists = fileExists(otherPath)
                    status = "exists" if otherExists else "missing"
                    kind = "INFO" if otherExists else "WARNING"
                    if verbose >= 0 or kind != "INFO":
                        console(f"{kind}: Needs {otherFile} ({status})")
                    if otherExists:
                        dependents.append(otherPath)

            for child in node.iterchildren(tag=etree.Element):
                findImports(child)

        roots = []
        self.roots = roots
        oroots = []
        self.oroots = oroots

        try:
            with open(baseSchema, encoding="utf8") as fh:
                tree = etree.parse(fh)

            root = tree.getroot()
            roots.append(root)
            schemaDir = self.baseSchemaDir
            dependents = []

            findImports(root)

            for dependent in dependents:
                with open(dependent, encoding="utf8") as fh:
                    dTree = etree.parse(fh)
                    dRoot = dTree.getroot()
                    roots.append(dRoot)

            if override is not None:
                with open(override, encoding="utf8") as fh:
                    tree = etree.parse(fh)

                root = tree.getroot()
                oroots.append(root)
                schemaDir = self.overrideDir
                dependents = []

                findImports(root)

                for dependent in dependents:
                    with open(dependent, encoding="utf8") as fh:
                        dTree = etree.parse(fh)
                        dRoot = dTree.getroot()
                        oroots.append(dRoot)

            self.good = True

        except Exception as e:
            msg = f"Could not read and parse {baseSchema}"
            if override is not None:
                msg += " or {override}"
            console(msg)
            console(str(e))
            self.good = False

    @staticmethod
    def eKey(x):
        """Sort the dict with element definitions.

        Parameters
        ----------
        x: (str, dict)
            The element name and the element info.

        Returns
        -------
        tuple
            The members are such that definitions from other than xs:element come first,
            and within xs:element those that are "abstract" come first.
        """
        name = x[0]
        tag = x[1]["tag"]
        abstract = x[1]["abstract"]

        return (
            "0" if tag == "simpleType" else "1" if tag == "complexType" else tag,
            "" if abstract else "x",
            name,
        )

    def interpret(self):
        """Reads the xsd and interprets the element definitions.

        The definitions are read with the module `lxml`.

        For each definition of a name certain attributes are remembered, e.g.
        the *kind*, the presence of a *mixed* attribute, whether it is a
        *substitutionGroup* or *extension*, and whether it is *abstract*.

        When elements refer to a *substitutionGroup*, they need to get
        the *kind* and *mixed* attributes of that group.

        When elements refer to a *base*, they need to get
        the *kind* and *mixed* attributes of an extension with that *base*.

        After an initial parse of the XSD file, we do a variable number of
        resolving rounds, where we chase the substitution groups and
        extensions, until nothing changes anymore.

        The info that is gathered is put in `self.defs` and can be retrieved
        by method `getDefs()`.

        The info is a list of items, one item per element.
        Each item is a tuple of: element name, element kind, mixed status.

        The absence of the element *kind* and *mixed* status are indicated
        with `None`.
        If all went well, there are no such absences!
        """

        verbose = self.verbose
        debug = self.debug
        roots = self.roots
        oroots = self.oroots
        types = self.types
        override = self.override

        definitions = {}
        redefinitions = collections.Counter()

        def findDefs(node, definingName, topDef):
            """Inner function to walk through the xsd and get definitions.

            This function is called recursively for child nodes.

            Parameters
            ----------
            node: Object
                The current node.
            definingName: string | void
                If this has a value, we are underneath a definition.

            topDef: boolean
                If we are underneath a definition, this indicates
                we are at the top-level of that definition.
            """
            tag = etree.QName(node.tag).localname

            name = node.get("name")
            abstract = node.get("abstract") == "true"
            mixed = node.get("mixed") == "true"
            subs = node.get("substitutionGroup")

            if definingName:
                if topDef:
                    if tag in types:
                        definitions[definingName]["kind"] = (
                            "simple" if tag == "simpleType" else "complex"
                        )
                        if mixed:
                            definitions[definingName]["mixed"] = mixed
                else:
                    if tag == "extension":
                        base = node.get("base")
                        if base:
                            definitions[definingName]["base"] = base

            if name and tag not in self.notInteresting:
                if name in definitions:
                    redefinitions[name] += 1
                else:
                    definitions[name] = dict(
                        tag=tag, abstract=abstract, mixed=mixed, subs=subs
                    )

            if definingName:
                defining = definingName
                top = False
            else:
                isElementDef = name and tag == "element"
                defining = name if isElementDef else False
                top = True if defining else False

            for child in node.iterchildren(tag=etree.Element):
                findDefs(child, defining, top)

        if verbose >= 0:
            console(f"Analysing {self.baseSchema}")
        for root in roots:
            findDefs(root, False, False)
        if debug:
            self.showElems()
        self.resolve(definitions)

        baseDefinitions = definitions

        self.overrides = {}

        if len(oroots) > 0:
            definitions = {}
            redefinitions = collections.Counter()
            if verbose >= 0:
                console(f"Analysing {override}")
            for root in oroots:
                findDefs(root, False, False)
            if debug:
                self.showElems()
            self.resolve(definitions)

            for (name, odef) in definitions.items():

                oKind = self.repKind(odef.get("kind", None))
                oMixed = self.repMixed(odef.get("mixed", None))

                if name in baseDefinitions:
                    baseDef = baseDefinitions[name]
                    baseKind = self.repKind(baseDef.get("kind", None))
                    baseMixed = self.repMixed(baseDef.get("mixed", None))
                    transRep = (
                        f"{baseKind} {baseMixed} ==> {oKind} {oMixed}"
                        if baseKind != oKind and baseMixed != oMixed
                        else f"{baseKind} ==> {oKind}"
                        if baseKind != oKind
                        else f"{baseMixed} ==> {oMixed}"
                        if baseMixed != oMixed
                        else None
                    )
                    if transRep is not None:
                        baseDefinitions[name] = odef
                    self.overrides[name] = transRep
                else:
                    baseDefinitions[name] = odef
                    if odef["tag"] == "element" and not odef["abstract"]:
                        self.overrides[name] = f"{oKind} {oMixed} (added)"

        self.defs = tuple(
            (name, info.get("kind", None), info.get("mixed", None))
            for (name, info) in sorted(baseDefinitions.items(), key=self.eKey)
            if info["tag"] == "element" and not info["abstract"]
        )
        self.showOverrides()

    def getDefs(self, asTsv=False):
        """Delivers the analysis results.

        Parameters
        ----------
        asTsv: boolean, optional False
            If True, the result is delivered as a TSV text,
            otherwise as a list.

        Returns
        -------
        str | list
            One line/item per element.
            Each line has: element name, element kind, mixed status.

            The absence of the element *kind* and *mixed* status are indicated
            with `---` in the TSV and with the `None` value in the list.
            If all went well, there are n such absences!
        """
        defs = self.defs

        return (
            "\n".join(
                f"{name}\t{self.repKind(kind)}\t{self.repMixed(mixed)}"
                for (name, kind, mixed) in defs
            )
            if asTsv
            else defs
        )

    @staticmethod
    def repMixed(m):
        return "-----" if m is None else "mixed" if m else "pure"

    @staticmethod
    def repKind(k):
        return "-----" if k is None else k

    def resolve(self, definitions):
        """Resolve indirections in the definitions.

        After having read the complete XSD file,
        we can now dereference names and fill properties of their definitions
        in places where the names occur.
        """
        debug = self.debug
        verbose = self.verbose

        def infer():
            changed = 0
            for (name, info) in definitions.items():
                if info["mixed"]:
                    continue

                other = info.get("base", info.get("subs", None))
                if other:
                    otherBare = other.split(":", 1)[-1]
                    otherInfo = definitions.get(otherBare, None)
                    if otherInfo is None:
                        if not other.startswith("xs:"):
                            if verbose >= 0:
                                console(f"Warning: {other} is not defined.")
                        continue
                    if otherInfo["mixed"]:
                        info["mixed"] = True
                        changed += 1
                    if info.get("kind", None) is None:
                        if otherInfo.get("kind", None):
                            info["kind"] = otherInfo["kind"]
                            changed += 1
                        else:
                            console(f"Warning: {other}.kind is not defined.")
                    if info.get("mixed", None) is None:
                        if otherInfo.get("mixed", None):
                            info["mixed"] = otherInfo["mixed"]
                            changed += 1
                        else:
                            if verbose >= 0:
                                console(f"Warning: {other}.mixed is not defined.")

            return changed

        i = 0

        while True:
            changed = infer()
            i += 1
            if changed:
                if verbose == 1:
                    console(f"\tround {i:>3}: {changed:>3} changes")
                if debug:
                    self.showElems()
            else:
                break

    def showElems(self):
        """Shows the current state of definitions.

        Mainly for debugging.
        """
        definitions = self.definitions
        redefinitions = self.redefinitions

        for (name, info) in sorted(definitions.items(), key=self.eKey):
            tag = info["tag"]
            mixed = "mixed" if info["mixed"] else "-----"
            abstract = "abstract" if info["abstract"] else "--------"
            kind = info.get("kind", "---")
            subs = info.get("subs")
            subsRep = f"==> {subs}" if subs else ""
            base = info.get("base")
            baseRep = f"<== {base}" if base else ""
            console(
                f"{name:<30} in {tag:<20} "
                f"({kind:<7}) ({mixed}) ({abstract}) {subsRep}{baseRep}"
            )

        console("=============================================")
        for (name, amount) in sorted(redefinitions.items()):
            console(f"{amount:>3}x {name}")

    def showOverrides(self):
        """Shows the overriding definitions.
        """
        verbose = self.verbose
        override = self.override

        if override:
            overrides = self.overrides
            same = sum(1 for x in overrides.items() if x[1] is None)
            distinct = len(overrides) - same
            if verbose == 1:
                console(f"{same:>3} identical override(s)")
            if verbose >= 0:
                console(f"{distinct:>3} changing override(s)")
        if verbose >= 0:
            for (name, trans) in sorted(
                x for x in self.overrides.items() if x[1] is not None
            ):
                console(f"\t{name} {trans}")

    def task(self, task, *args):
        """Implements a higher level task.

        Parameters
        ----------
        task: string
            The task to execute: `"fromrelax"`, `"analyse"`, or `"tei"`.

        ask: list
            Any arguments for the task.
            That could be a base schema and an override.
            Not all tasks require both.

        Returns
        -------
        boolean
            whether the task was completed successfully.
        """

        verbose = self.verbose
        myDir = self.myDir

        if task in {"tei", "analyse"}:
            if task == "tei":
                baseSchema = f"{myDir}/tei/tei_all.xsd"
                override = args[0] if len(args) else None
            else:
                baseSchema = args[0]
                override = None
            outputFile = (
                baseNm(
                    override if override is not None else baseSchema
                ).removesuffix(".xsd")
                + ".tsv"
            )
            self.configure(baseSchema=baseSchema, override=override)
            if not self.good:
                return False

            self.interpret()
            if not self.good:
                return False
            defs = self.getDefs(asTsv=True)

            if verbose >= 0:
                console(f"{len(defs):>3} elements defined")
            with open(outputFile, "w", encoding="utf8") as fh:
                fh.write(defs)
            console(f"Analysis written to {outputFile}\n")
            return True

        elif task == "fromrelax":
            baseSchema = args[0]
            trang = f"{myDir}/trang/trang.jar"
            schemaOut = baseSchema.removesuffix(".rng") + ".xsd"
            result = run(f"java -jar {trang} {baseSchema} {schemaOut}", shell=True)
            return True if result.returncode == 0 else False

    def run(self):
        """Run a task specified by arguments on the command line.

        Returns
        -------
        integer
            0 if the task was executed successfully, otherwise 1
            -1 is an error from before executing the task,
            1 is an error from the actual execution of a task.
        """
        tasks = dict(
            tei={0, 1},
            analyse={1},
            fromrelax={1},
        )
        possibleFlags = {
            "-debug": False,
            "+debug": True,
            "-verbose": -1,
            "+verbose": 0,
            "++verbose": 1,
        }

        args = set(sys.argv[1:])

        flags = {arg: val for (arg, val) in possibleFlags if arg in args}
        args = {a for a in args if a not in flags}

        if "-h" in args or "--help" in args:
            self.help()
            return 0

        if len(args) == 0:
            self.help()
            console("No task specified")
            return -1

        task = args.pop(0)
        nParams = tasks.get(task, None)
        if nParams is None:
            self.help()
            console(f"Unrecognized task {task}")
            return -1

        if len(args) not in nParams:
            self.help()
            console(f"Wrong number of arguments ({len(args)} for {task}")
            return -1

        self.setModes(**flags)
        return 0 if self.task(task, *args) else 1


def main():
    A = Analysis()
    return A.run()


if __name__ == "__main__":
    A = Analysis()
    exit(main())
