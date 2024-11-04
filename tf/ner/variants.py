"""Detect name variants in the corpus.

We provide a class can detect variants of the triggers in a NER spreadsheet,
that is variants as they occur in the corpus.

One way (and the way supported here) of obtaining the variants is
by the tool
[analiticcl](https://github.com/proycon/analiticcl) by Martin
Reynaert and Maarten van Gompel.
"""

import collections
import re

# from analiticcl import VariantModel, Weights, SearchParameters

from ..capable import CheckImport
from ..core.files import initTree, fileExists, readJson, writeJson, fileOpen
from ..core.helpers import console
from ..convert.recorder import Recorder


HTML_PRE = """<html>
<head>
    <meta charset="utf-8"/>
    <style>
«css»
    </style>
</head>
<body>
"""

HTML_POST = """
</body>
</html>
"""


class Detect:
    def __init__(self, NE, sheet=None):
        """Detect spelling variants.

        In order to use this class you may have to install analiticcl. First
        you have to make sure you have the programming language Rust operational on
        your machine, and then you have to install analiticcl as a Rust program,
        and finally you have to do

        ```
        pip install analiticcl
        ```

        See the
        [python bindings](https://github.com/proycon/analiticcl/tree/master/bindings/python)
        for detailed instructions.

        If you have an instance of the `tf.ner.ner.NER` class, e.g. from an earlier
        call like this

        ```
        NE = A.makeNer()
        ```

        and if you have pointed this `NE` to a NER spreadsheet, e.g. by

        ```
        NE.setTask(".persons")
        ```

        then you can get an instance of this class by saying

        ```
        D = NE.variantDetection()
        ```

        There are methods to produce a plain text of the corpus, a lexicon based on the
        triggers in the spreadsheet, and then to search the plain text for variants
        of the lexicon by passing some well-chosen parameters to analiticcl.

        After the search, which may take long, the raw results are cached, and then
        filtered, with the help of an optional exceptions file.
        If you change the filtering parameters, you do not have to rerun the expensive
        search by analiticcl.

        The variants found can then be merged with the original triggers, and saved as
        a new spreadsheet, next to the original one.

        The settings for analiticcl are ultimately given in the config.yaml in the
        `ner` directory of the corpus, where the other settings for the NER process
        are also given. See `tf.ner.settings`.

        Parameters
        ----------
        NE: object
            A `tf.ner.ner.NER` instance.
        sheet: string, optional None
            The name of a NER sheet that serves as input of the variant detection
            process. If not passed, it is assumed that the `NE` instances is
            already switched to a NER sheet before setting up this object.
            However, in any case, we switch again to the sheet in question to make
            sure we do so in case sesnsitive mode (even if we have used the sheet
            in case insensitive mode for the lookup).
        """
        CI = CheckImport("analiticcl")

        if CI.importOK(hint=True):
            an = CI.importGet()
            self.VariantModel = an.VariantModel
            self.Weights = an.Weights
            self.SearchParameters = an.SearchParameters
        else:
            self.properlySetup = False
            return None

        self.properlySetup = True

        self.NE = NE

        if sheet is None:
            sheet = NE.sheetName
            NE.setSheet(sheet, caseSensitive=True, force=True, forceSilent=True)
        else:
            NE.setSheet(sheet, caseSensitive=True, force=True)

        if not NE.setIsX:
            console(
                (
                    "Setting up this instance requires having a current "
                    f"NER spreadsheet selected. '{sheet}' is not a spreadsheet."
                ),
                error=True,
            )
            self.properlySetup = False
            return

        self.sheet = sheet
        self.sheetData = NE.getSheetData()

        app = NE.app
        self.app = app

        settings = NE.settings.variants
        self.settings = settings

        workDir = f"{app.context.localDir}/{app.context.extraData}/analyticcl"
        self.workDir = workDir
        initTree(workDir, fresh=False)

        NE.setSheet(sheet, caseSensitive=True, force=True)
        sheetData = NE.getSheetData()

        NE.console("Overview of names by length:")
        triggers = set(sheetData.rowMap)

        lengths = collections.defaultdict(list)

        for trigger in triggers:
            lengths[len(trigger.split())].append(trigger)

        for n, trigs in sorted(lengths.items(), key=lambda x: -x[0]):
            examples = "\n      ".join(sorted(trigs, key=lambda x: x.lower())[0:5])
            NE.console(f"  {n} tokens: {len(trigs):>3} names e.g.:\n      {examples}")

    def prepare(self):
        """Prepare the data for the search of spelling variants.

        We construct an alphabet and a plain text out of the corpus,
        and we construct a lexicon from the triggers in the current spreadsheet.
        """
        if not self.properlySetup:
            console("This instance is not properly set up", error=True)
            return

        self.makeAlphabet()
        self.makeText()
        self.makeLexicon()
        self.setupAnaliticcl()

    def search(self, start=None, end=None, force=0):
        """Search for spelling variants in the corpus.

        We search part of the corpus or the whole corpus for spelling variants.
        The process has two stages:

        1.  a run of analaticcl
        2. filtering of the results

        The run of analiticcl is expensive, more than 10 minutes on the
        [Suriano corpus](https://gitlab.huc.knaw.nl/suriano/letters).

        The results of stage 1 will be cached. For every choice of search parameters
        and boundary points in the corpus there is a separate cache.

        A number of analiticcl-specific parameters will influence the search.
        They can be tweaked in the config file of the NER module, under the variants
        section.

        Parameters
        ----------
        start: integer, optional None
            The place in the corpus where the search has to start; it is the offset
            in the plain text. If `None`, start from the beginning of the corpus.
        end: integer, optional None
            The place in the corpus where the search must end; it is the offset
            in the plain text. If `None`, the search will be performed till the end
            of the corpus.
        force: integer, optional 0
            Valid values are `0`, `1`, `2`.
            Meaning: `0`: use the cached result, if it is available.
            `1`: use the cached result for stage 1, if available, but perform the
            filtering (again).
            `2`: do not use the cache, but compute everything again.
        """
        if not self.properlySetup:
            console("This instance is not properly set up", error=True)
            return

        SearchParameters = self.SearchParameters
        ansettings = self.settings.analiticcl
        searchParams = ansettings.searchParams
        suoffsets = searchParams.unicodeoffsets
        smaxngram = searchParams.max_ngram
        sfreqweight = searchParams.freq_weight
        scoring = ansettings.scoring
        sthreshold = scoring.threshold

        NE = self.NE
        app = self.app
        model = self.model
        rec = self.rec
        textComplete = self.textComplete
        workDir = self.workDir
        lexiconOccs = self.lexiconOccs

        text = textComplete[start:end]
        nText = len(text)

        offset = 0 if start is None else nText + start if start < 0 else start

        NE.console(f"{nText:>8} text  length")
        NE.console(f"{offset:>8} offset in complete text")

        slug = (
            f"{suoffsets}-{smaxngram}-{sfreqweight}-{sthreshold}-"
            f"{suoffsets}-{smaxngram}-{sfreqweight}-{sthreshold}"
        )
        matchesFile = f"{workDir}/matches-{start}-{end}-settings={slug}.json"
        matchesPosFile = f"{workDir}/matchespos-{start}-{end}-settings={slug}.json"
        rawMatchesFile = f"{workDir}/rawmatches-{start}-{end}-settings={slug}.json"

        app.indent(reset=True)

        if force == 2 or not fileExists(rawMatchesFile):
            app.info("Compute variants of the lexicon words ...")
            rawMatches = model.find_all_matches(
                text,
                SearchParameters(
                    unicodeoffsets=suoffsets,
                    max_ngram=smaxngram,
                    freq_weight=sfreqweight,
                    score_threshold=sthreshold,
                ),
            )
            writeJson(rawMatches, asFile=rawMatchesFile)
        else:
            app.info("Read previously computed variants of the lexicon words ...")
            rawMatches = readJson(asFile=rawMatchesFile, plain=False)

        app.info(f"{len(rawMatches):>8} raw   matches")

        if force == 1 or not fileExists(matchesFile) or not fileExists(matchesPosFile):
            app.info("Filter variants of the lexicon words ...")
            positions = rec.positions(simple=True)

            matches = {}
            matchPositions = collections.defaultdict(list)

            for match in rawMatches:
                text = match["input"].replace("\n", " ")
                textL = text.lower()

                if text in lexiconOccs:
                    continue

                candidates = match["variants"]

                if len(candidates) == 0:
                    continue

                candidates = {
                    cand["text"]: s
                    for cand in candidates
                    if (s := cand["score"]) >= sthreshold
                }

                if len(candidates) == 0:
                    continue

                textRemove = set()

                for cand in candidates:
                    candL = cand.lower()
                    if candL == textL:
                        textRemove.add(cand)

                for cand in textRemove:
                    del candidates[cand]

                if len(candidates) == 0:
                    continue

                # if the match ends with 's we remove the part without it from the
                # candidates

                if text.endswith("'s"):
                    head = text.removesuffix("'s")
                    if head in candidates:
                        del candidates[head]

                        if len(candidates) == 0:
                            continue

                # we have another need to filter: if the text of a match is one short
                # word longer than a candidate we remove that candidate
                # provided the extra word is lower case and has at most 3 letters
                # this is to prevent cases like
                # «Adam Schivelbergh» versus «Adam Schivelbergh di»
                #
                # We do this also when the extra word is at the start, like
                # «di monsignor Mangot» versus «monsignor Mangot»

                parts = text.split()

                if len(parts) > 0:
                    (head, tail) = (parts[0:-1], parts[-1])

                    # if len(tail) <= 3 and tail.islower():
                    if len(tail) <= 3:
                        head = " ".join(head)

                        if head in candidates:
                            del candidates[head]

                            if len(candidates) == 0:
                                continue

                    (head, tail) = (parts[0], parts[1:])

                    # if len(head) <= 3 and head.islower():
                    if len(head) <= 3:
                        tail = " ".join(tail)

                        if tail in candidates:
                            del candidates[tail]

                            if len(candidates) == 0:
                                continue

                position = match["offset"]
                start = position["begin"]
                end = position["end"]
                nodes = sorted(
                    {positions[i] for i in range(offset + start, offset + end)}
                )

                matches[text] = candidates
                matchPositions[text].append(nodes)

            writeJson(matches, asFile=matchesFile)
            writeJson(matchPositions, asFile=matchesPosFile)
        else:
            app.info("Read previously filtered variants of the lexicon words ...")
            matches = readJson(asFile=matchesFile, plain=False)
            matchPositions = readJson(asFile=matchesPosFile, plain=False)

        app.info(f"{len(matches):>8} filtered matches")

        self.matches = matches
        self.matchPositions = matchPositions
        console(f"{len(matches)} variants found")

    def listVariants(self, start=None, end=None):
        """List the search results to the console.

        Show (part of) the variants found on the console as a plain text table.

        This content will also be written to the file `variants.txt` in the
        work directory.

        Parameters
        ----------
        start: integer, optional None
            The sequence number of the first result to show.
            If `None`, start with the first result.
        end: integer, optional None
            The sequence number of the last result to show.
            If `None`, continue to the last result.
        """
        if not self.properlySetup:
            console("This instance is not properly set up", error=True)
            return

        workDir = self.workDir
        matches = self.matches

        lines = []

        head = ("variant", "score", "candidate")
        dash = f"{'-' * 4} | {'-' * 25} | {'-' * 5} | {'-' * 25}"
        console(f"{'i':>4} | {head[0]:<25} | {head[1]} | {head[2]}")
        console(f"{dash}")
        startN = start or 0

        for text, candidates in sorted(matches.items(), key=lambda x: x[0].lower()):
            for cand, score in sorted(candidates.items(), key=lambda x: x[0].lower()):
                lines.append((text, score, cand))

        for i, (text, score, cand) in enumerate(lines[start:end]):
            console(f"{i + startN:>4} | {text:<25} |  {score:4.2f} | {cand}")

        console(f"{dash}")

        file = f"{workDir}/variants.tsv"

        with fileOpen(file, "w") as fh:
            headStr = "\t".join(head)
            fh.write(f"{headStr}\n")
            for text, score, cand in lines:
                fh.write(f"{text}\t{score:4.2f}\t{cand}\n")

        console(f"{len(matches)} variants found and written to {file}")

    def mergeTriggers(self, level=1):
        """Merge spelling variants of triggers into a NER sheet.

        When we have found spelling variants of triggers, we want to include
        them in the entity lookup. This function places the variants in the same
        cells as the triggers they are variants of. However, it will not
        overwrite the original spreadsheet, but create a new, enriched spreadsheet.

        We collect the necessary information as follows:

        *   `matches: dict`:
            The spelling variants are keys, and their values are again dicts, keyed
            by the words in the triggers that come closest, and valued by a measure
            of the proximity.
            It is assumed that all of these variants are good variants, in that the
            scores are always above a certain threshold, e.g. 0.8 .
        *   `mergedFile: string`:
            The path of the new spreadsheet with the merged triggers: it will sit next
            to the original spreadsheet, but with an extension such as `-merged` added
            to its name (this can be configured in the NER config file near the corpus).
        *   `exclusionFile: string, optional None`
            The path to an optional file with exclusions, one per line.
            Variants that occur in the exclusion list will not be merged in.
            The file sits next to the original spreadsheet, but with an extension such
            as `-notmerged` (this is configurable) and file extension `.txt`.

        This function will also produce several reports:

        Parameters
        ----------
        level: integer, optional 1
            Only relevant for reporting the new variants. Occurrences of the
            new variants are counted by section. This parameter specifies the
            level of those sections. It should be 1, 2 or 3.
        """
        if not self.properlySetup:
            console("This instance is not properly set up", error=True)
            return

        NE = self.NE
        trigI = NE.trigI
        commentI = NE.commentI
        sheetDir = NE.sheetDir
        sheetName = NE.sheetName
        settings = self.settings
        mergedExtension = settings.mergedExtension
        notMergedExtension = settings.notMergedExtension
        mergedFile = f"{sheetDir}/{sheetName}{mergedExtension}.xlsx"
        mergedReportFile = f"{sheetDir}/{sheetName}{mergedExtension}-report.tsv"
        exclusionFile = f"{sheetDir}/{sheetName}{notMergedExtension}.txt"

        if not fileExists(exclusionFile):
            NE.console(f"File with excluded variants not found: {exclusionFile}")
            exclusionFile = None

        matches = self.matches
        matchPositions = self.matchPositions
        sectionHead = NE.sectionHead

        noVariant = set()

        if exclusionFile is not None and fileExists(exclusionFile):
            with fileOpen(exclusionFile) as fh:
                for line in fh:
                    noVariant.add(line.strip())

            nNoVariant = len(noVariant)
            pl = "" if nNoVariant == 1 else "s"
            NE.console(f"{nNoVariant} excluded variant{pl} found in {exclusionFile}")

        mapping = {}
        excluded = 0

        for text, candidates in matches.items():
            if text in noVariant:
                excluded += 1
                continue
            for cand in candidates:
                mapping.setdefault(cand, set()).add(text)

        ple = "" if excluded == 1 else "s"
        NE.console(f"{excluded} variant{ple} excluded as trigger")

        rows = NE.readSheetData()

        nAdded = 0
        totAdded = 0

        variantsAdded = {}

        for r, row in enumerate(rows):
            if r == 0 or r == 1 or row[commentI].startswith("#"):
                continue

            rn = r + 1
            triggers = set(row[trigI])
            nPrev = len(triggers)

            newTriggers = []

            for trigger in triggers:
                newTriggers.append(trigger)

                for variant in mapping.get(trigger, []):
                    newTriggers.append(variant)
                    variantsAdded.setdefault(rn, []).append((variant, trigger))

            newTriggers = sorted(set(newTriggers))
            row[trigI] = newTriggers
            nPost = len(newTriggers)

            nDiff = nPost - nPrev

            if nDiff != 0:
                nAdded += 1
                totAdded += nDiff

        lines = [("row", "trigger", "variant", "occurences")]

        for rn in sorted(variantsAdded):
            for variant, trigger in variantsAdded[rn]:
                sectionInfo = collections.Counter()

                for occ in matchPositions[variant]:
                    slot = occ[0]

                    section = sectionHead(slot, level=level)
                    sectionInfo[section] += 1

                hitData = [
                    f"{section}x{hits}" for section, hits in sorted(sectionInfo.items())
                ]
                for hits in hitData:
                    lines.append((rn, trigger, variant, hits))

        with fileOpen(mergedReportFile, "w") as fh:
            nLines = len(lines)

            for i, line in enumerate(lines):
                if i < 10 or i > nLines - 10:
                    (row, trigger, variant, hits) = line
                    NE.console(f"{row:<4} {trigger:<40} ~> {variant:<40} = {hits}")

                lineStr = "\t".join(str(x) for x in line)
                fh.write(f"{lineStr}\n")

        pls = "" if nAdded == 1 else "s"
        plt = "" if totAdded == 1 else "s"
        NE.console(f"{nAdded} triggerset{pls} expanded with {totAdded} trigger{plt}")
        NE.console(f"Wrote merge report to file {mergedReportFile}")

        NE.writeSheetData(rows, asFile=mergedFile)
        NE.console(f"Wrote merged triggers to sheet {mergedFile}")

    def showResults(self, start=None, end=None):
        """Show the search results to the console.

        Show (part of) the variants found on the console with additional context.

        Parameters
        ----------
        start: integer, optional None
            The sequence number of the first result to show.
            If `None`, start with the first result.
        end: integer, optional None
            The sequence number of the last result to show.
            If `None`, continue to the last result.
        """
        if not self.properlySetup:
            console("This instance is not properly set up", error=True)
            return

        app = self.app
        F = app.api.F
        matches = self.matches
        matchPositions = self.matchPositions

        i = 0

        for text, candidates in sorted(matches.items())[start:end]:
            i += 1
            nCand = len(candidates)
            pl = "" if nCand == 1 else "s"
            console(f"{i:>4} Variant «{text}» of {nCand} candidate{pl}")
            console("  Occurrences:")
            occs = matchPositions[text]

            for nodes in occs:
                sectionStart = app.sectionStrFromNode(nodes[0])
                sectionEnd = app.sectionStrFromNode(nodes[-1])
                section = (
                    sectionStart
                    if sectionStart == sectionEnd
                    else f"{sectionStart} - {sectionEnd}"
                )
                preStart = max((nodes[0] - 10, 1))
                preEnd = nodes[0]
                postStart = nodes[-1] + 1
                postEnd = min((nodes[-1] + 10, F.otype.maxSlot + 1))
                preText = "".join(
                    f"{F.str.v(n)}{F.after.v(n)}" for n in range(preStart, preEnd)
                )
                inText = "".join(f"{F.str.v(n)}{F.after.v(n)}" for n in nodes)
                postText = "".join(
                    f"{F.str.v(n)}{F.after.v(n)}" for n in range(postStart, postEnd)
                )
                context = f"{section}: {preText}«{inText}»{postText}".replace("\n", " ")
                console(f"    {context}")

            console("  Candidates with score:")

            for cand, score in sorted(candidates.items(), key=lambda x: (-x[1], x[0])):
                console(f"\t{score:4.2f} {cand}")

            console("-----")

    def displayResults(self, start=None, end=None, asFile=None):
        """Display the results as HTML files.

        This content will also be written to the files under the subdirectory
        `extra` in the work directory.

        Parameters
        ----------
        start: integer, optional None
            The sequence number of the first result to show.
            If `None`, start with the first result.
        end: integer, optional None
            The sequence number of the last result to show.
            If `None`, continue to the last result.
        asFile: string, optional None
            If None, the results will be displayed as HTML on the console.
            Otherwise, the results will be written down as a set of HTML files,
            whose names start with this string.
        """

        if not self.properlySetup:
            console("This instance is not properly set up", error=True)
            return

        app = self.app
        L = app.api.L
        matches = self.matches
        matchPositions = self.matchPositions
        lexiconOccs = self.lexiconOccs
        workDir = self.workDir

        if asFile is not None:
            content = []

            htmlStart = HTML_PRE.replace("«css»", app.context.css)
            htmlEnd = HTML_POST

            content.append([htmlStart])
            empty = True

            app.indent(reset=True)
            app.info("Gathering information on extra triggers ...")

        i = 0
        s = 0

        for varText, candidates in sorted(
            matches.items(), key=lambda x: (-len(x[1]), x[0])
        )[start:end]:
            i += 1

            # make a list of where the candidates are and include the score

            varOccs = matchPositions[varText]
            nVar = len(varOccs)

            candOccs = []
            candRep1 = "`" + "` or `".join(candidates) + "`"
            candRep2 = "<code>" + "</code> or <code>".join(candidates) + "</code>"

            for cand, score in candidates.items():
                myOccs = lexiconOccs[cand]

                for occ in myOccs:
                    candOccs.append((occ[0], score, cand, occ))

            # use this list later to find the nearest/best variant

            if asFile is None:
                app.dm(
                    f"# {i}: {nVar} x variant `{varText}` on "
                    f"candidate {candRep1}\n\n"
                )
            else:
                content[-1].append(
                    f"<h1>{i}: {nVar} x variant <code>{varText}</code> on "
                    f"candidate {candRep2}</h1>"
                )
                empty = False

            sections = set()
            highlights = {}
            bestCand = None

            for candOcc in candOccs:
                if bestCand is None or bestCand[1] < candOcc[1]:
                    bestCand = candOcc

            for n in bestCand[3]:
                highlights[n] = "lightgreen"

            section = L.u(bestCand[0], otype="chunk")[0]
            sections.add(section)

            for varNodes in varOccs:
                highlights |= {n: "goldenrod" for n in varNodes}

                nFirst = varNodes[0]
                section = L.u(nFirst, otype="chunk")[0]
                sections.add(section)

                nearestCand = None

                for candOcc in candOccs:
                    if nearestCand is None or abs(nearestCand[0] - nFirst) > abs(
                        candOcc[0] - nFirst
                    ):
                        nearestCand = candOcc

                for n in nearestCand[3]:
                    if n in highlights:
                        highlights[n] = "yellow"
                    else:
                        highlights[n] = "cyan"

                section = L.u(nearestCand[0], otype="chunk")[0]
                sections.add(section)

            sections = tuple((s,) for s in sorted(sections))

            s += len(sections)

            if asFile is None:
                app.table(sections, highlights=highlights, full=True)
            else:
                content[-1].append(
                    app.table(
                        sections, highlights=highlights, full=True, _asString=True
                    )
                )

                if i % 10 == 0:
                    app.info(f"{i:>4} variants done giving {s:>4} chunks")
                if i % 100 == 0:
                    content[-1].append(htmlEnd)
                    content.append([htmlStart])
                    empty = True

        app.info(f"{i:>4} matches done")

        if asFile is not None:
            content[-1].append(htmlEnd)
            if empty:
                content.pop()

            extraFileBase = f"{workDir}/extra"
            initTree(extraFileBase, fresh=True, gentle=True)

            for i, material in enumerate(content):
                extraFile = f"{extraFileBase}/{asFile}{i + 1:>02}.html"

                with fileOpen(extraFile, "w") as fh:
                    fh.write("\n".join(material))

                console(f"Extra triggers written to {extraFile}")

    def makeAlphabet(self):
        """Gathers the alphabet on which the corpus is based.

        The characters of the corpus have already been collected by Text-Fabric,
        and that is from where we pick them up.

        We separate the digits from the rest.
        """
        if not self.properlySetup:
            console("This instance is not properly set up", error=True)
            return

        app = self.app
        C = app.api.C
        workDir = self.workDir

        alphabetFile = f"{workDir}/alphabet.tsv"
        self.alphabetFile = alphabetFile

        with fileOpen(alphabetFile, "w") as fh:
            # This file will consist of one character per line,
            # for each distinct alpha character in the corpus, ordered by frequency.
            # Numeric characters will be put on a single line, with tabs in between.
            # All other characters will be ignored.

            digits = []

            for c, freq in C.characters.data["text-orig-full"]:
                if c.isalpha():
                    fh.write(f"{c}\n")
                elif c.isdigit():
                    digits.append(c)
            fh.write("\t".join(digits))

        console(f"Alphabet written to {alphabetFile}")

    def makeText(self):
        """Generate a plain text from the corpus.

        We make sure that we resolve the hyphenation of words across line
        boundaries.
        """
        if not self.properlySetup:
            console("This instance is not properly set up", error=True)
            return

        NE = self.NE
        app = self.app
        api = app.api
        F = app.api.F
        L = app.api.L
        workDir = self.workDir

        rec = Recorder(api)

        lineType = self.settings.lineType
        slotType = F.otype.slotType
        maxSlot = F.otype.maxSlot
        lines = F.otype.s(lineType)
        lineEnds = {L.d(ln, otype=slotType)[-1] for ln in lines}
        skipTo = None

        for t in range(1, maxSlot + 1):
            tp = t + 1
            tpp = t + 2

            if tp in lineEnds and tp < maxSlot and F.str.v(tp) == "-":
                rec.start(t)
                rec.add(f"{F.str.v(t)}{F.after.v(t)}")
                rec.end(t)
                rec.start(tpp)
                rec.add(f"{F.str.v(tpp)}{F.after.v(tpp)}\n")
                rec.end(tpp)
                skipTo = tpp
            elif skipTo is not None:
                if t < skipTo:
                    continue
                else:
                    skipTo = None
            else:
                rec.start(t)
                rec.add(f"{F.str.v(t)}{F.after.v(t)}")
                rec.end(t)

        self.rec = rec
        textComplete = rec.text()
        self.textComplete = textComplete

        textFile = f"{workDir}/text.txt"

        with fileOpen(textFile, "w") as fh:
            fh.write(textComplete)

        NE.console(f"Text written to {textFile} - {len(textComplete)} characters")

    def makeLexicon(self):
        """Make a lexicon out of the triggers of a spreadsheet."""
        if not self.properlySetup:
            console("This instance is not properly set up", error=True)
            return

        NE = self.NE
        app = self.app
        workDir = self.workDir

        sheetData = self.sheetData
        NEinventory = sheetData.inventory

        app.indent(reset=True)
        app.info("Collecting the triggers for the lexicon")

        inventory = {}

        for eidkind, triggers in NEinventory.items():
            for trigger, scopes in triggers.items():
                inventory.setdefault(trigger, set())

                for occs in scopes.values():
                    for slots in occs:
                        inventory[trigger].add(tuple(slots))

        app.info(f"{len(inventory)} triggers collected")

        remSpaceRe = re.compile(r""" +([^A-Za-z])""")
        accentSpaceRe = re.compile(r"""([’']) +""")

        lexicon = {}
        mapNormal = {}

        lexiconOccs = {}
        self.lexiconOccs = lexiconOccs

        for name, occs in inventory.items():
            occStr = name
            occNormal = remSpaceRe.sub(r"\1", occStr)
            occNormal = accentSpaceRe.sub(r"\1", occNormal)
            nOccs = len(occs)
            lexicon[occNormal] = nOccs
            mapNormal[occNormal] = occStr
            lexiconOccs[occNormal] = occs

        sortedLexicon = sorted(lexicon.items(), key=lambda x: (-x[1], x[0].lower()))

        for name, n in sortedLexicon[0:10]:
            NE.console(f"  {n:>3} x {name}")

        NE.console("  ...")

        for name, n in sortedLexicon[-10:]:
            NE.console(f"  {n:>3} x {name}")

        NE.console(f"{len(lexicon):>8} lexicon length")

        lexiconFile = f"{workDir}/lexicon.tsv"
        self.lexiconFile = lexiconFile

        with fileOpen(lexiconFile, "w") as fh:
            for name, n in sorted(lexicon.items()):
                fh.write(f"{name}\t{n}\n")

        NE.console(f"Lexicon written to {lexiconFile}")

    def setupAnaliticcl(self):
        """Configure analiticcl for the big search.

        We gather the parameters from the variants section of the NER
        config file (see `tf.ner.settings`).

        For the description of the parameters, see the
        [analiticcl tutorial](https://github.com/proycon/analiticcl/blob/master/tutorial.ipynb)
        """
        if not self.properlySetup:
            console("This instance is not properly set up", error=True)
            return

        NE = self.NE
        VariantModel = self.VariantModel
        Weights = self.Weights
        ansettings = self.settings.analiticcl
        weights = ansettings.weights
        wld = weights.ld
        wlcs = weights.lcs
        wprefix = weights.prefix
        wsuffix = weights.suffix
        wcase = weights.case

        alphabetFile = self.alphabetFile
        lexiconFile = self.lexiconFile

        NE.console("Set up analiticcl")

        model = VariantModel(
            alphabetFile,
            Weights(ld=wld, lcs=wlcs, prefix=wprefix, suffix=wsuffix, case=wcase),
        )
        self.model = model
        model.read_lexicon(lexiconFile)
        model.build()
