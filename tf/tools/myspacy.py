"""Get words and tokens from a plain text with the help of Spacy.

This module supposes that you have installed Spacy and the necessary
language modules.

To get [Spacy](https://spacy.io), do

``` sh
pip install spacy
```

The English language module can then be installed by

``` sh
python -m spacy download en_core_web_sm
```

You can install many more [language models](https://spacy.io/usage/models).
"""

import re

from ..capable import CheckImport
from ..core.helpers import console


LANG_MODELS = """
ca core_news Catalan
da core_news Danish
de core_news German
el core_news Greek
en core_web English
es core_news Spanish
fi core_news Finnish
fr core_news French
hr core_news Croatian
it core_news Italian
ja core_news Japanese
ko core_news Korean
lt core_news Lithuanian
mk core_news Macedonian
nb core_news Norwegian (Bokmål)
nl core_news Dutch
pl core_news Polish
pt core_news Portuguese
ro core_news Romanian
ru core_news Russian
sv core_news Swedish
uk core_news Ukrainian
zh core_news Chinese
xx ent_wiki multi-language
""".strip().split("\n")
"""Languages and their associated Spacy models."""


class Spacy(CheckImport):
    def __init__(self, lang=None, parser=False):
        """Sets up an NLP (Natural Language Processing) pipeline.

        The pipeline is tied to a particular language model, which you can pass
        as a parameter, provided you have installed it.

        For now, we use Spacy in a fairly trivial way: only tokenisation and sentence
        detection.
        We do not need the parser for this.

        Parameters
        ----------
        lang: string, optional xx
            The language to be used; Spacy may need to download it, if so, it will
            happen automatically.

            If the language is not supported by Spacy, we switch to the multi-language
            called `xx`.

            See `tf.tools.myspacy.LANG_MODELS` about the language models that Spacy supports.
        """
        super().__init__("spacy", "spacyd")
        if self.importOK(hint=True):
            (spacy, download) = self.importGet()
        else:
            return

        langModels = {}
        languages = {}

        self.canTag = False
        self.canMorph = False
        self.canLemma = False

        for spec in LANG_MODELS:
            (lng, model, language) = spec.split(maxsplit=2)
            langModels[lng] = f"{lng}_{model}_sm"
            languages[lng] = language

        self.langModels = langModels
        self.languages = languages

        prevLang = None
        targetLang = lang
        loaded = False

        i = 0
        while True:
            i += 1
            targetModel = langModels.get(targetLang, None)
            targetLanguage = languages.get(targetLang, None)

            if targetModel is None:
                (prevLang, targetLang) = (targetLang, "xx")
                targetModel = langModels[targetLang]
                targetLanguage = languages[targetLang]

                if prevLang is None:
                    console("No language specified")
                else:
                    console(
                        f"No language model for {prevLang} supported by Spacy.\n"
                    )
                console(
                    f"Switching to the {targetLanguage} model"
                )
                if targetLang == prevLang:
                    break
                else:
                    continue

            try:
                nlp = spacy.load(targetModel)
                loaded = True
                break

            except Exception:
                console(f"Language model {targetModel} not installed. Downloading ...")

            try:
                console(f"Downloading {targetModel} ...")
                download(targetModel)
            except Exception:
                console(f"Could not download {targetModel} ...")
                (prevLang, targetLang) = (targetLang, "xx")
                if targetLang == prevLang:
                    break
                else:
                    continue

        console(f"NLP with language model {targetLang} {parser}")

        if loaded:
            try:
                if not parser:
                    nlp.disable_pipe("parser")
                nlp.disable_pipe("sentencizer")
            except Exception:
                pass
            try:
                nlp.enable_pipe("senter")
                self.canSentence = True
            except Exception:
                self.canSentence = False
                console("This language does not support sentence boundary detection")

            if parser:
                try:
                    nlp.enable_pipe("tagger")
                    self.canTag = True
                    console("This language supports tagging")
                except Exception:
                    self.canTag = False
                    console("This language does not supports tagging")
                try:
                    nlp.enable_pipe("morphologizer")
                    self.canMorph = True
                    console("This language supports morphologizing")
                except Exception:
                    self.canMorph = False
                    console("This language does not supports morphologizing")
                try:
                    nlp.enable_pipe("lemmatizer")
                    self.canLemma = True
                    console("This language supports lemmatizing")
                except Exception:
                    self.canLemma = False
                    console("This language does not supports lemmatizing")
        else:
            console("Cannot load (language data) to get Spacy working")
            nlp = None

        self.nlp = nlp
        self.doc = None

    def read(self, text):
        """Process a plain text.

        A text is ingested and tokenised. Sentences are detected.
        This may require quite some processing time, think of 30 seconds for 200,000
        words on a decent laptop.

        Parameters
        ----------
        text: string
            The complete, raw text.
        """
        if not self.importOK():
            return

        nText = len(text)
        nlp = self.nlp

        if nlp is None:
            console("The NLP pipeline is not functioning")
            return

        nlp.max_length = nText
        doc = nlp(text)
        self.doc = doc

    def getTokens(self):
        """Get the resulting tokens.

        A token is represented as a tuple consisting of

        *   *start*: first character position that the token occupies in the text.
            Character positions start at 0.
        *   *end*: last character position that the token occupies in the text
            *plus one*.
        *   *text*: text of the token, **excluding any trailing white-space**.
        *   *space*: any white-space behind the token, if present, otherwise
            the empty string.


        !!! note "End position and space"
            If there is a space behind the token, it will not add to the end position
            of the token. So the start and end positions of the tokens reflect
            where the tokens themselves are, and spaces do not belong to the tokens.

        Returns
        -------
        list
            All tokens as tuples.
        """
        doc = self.doc
        if doc is None:
            console("No results available from the NLP pipeline")
            return []

        canTag = self.canTag
        canMorph = self.canMorph
        canLemma = self.canLemma

        result = []

        for token in doc:
            start = token.idx
            text = token.text
            space = token.whitespace_
            end = start + len(text)

            pos = token.pos_ if canMorph else token.tag_ if canTag else None
            morph = str(token.morph) if canMorph else None
            lemma = token.lemma_.strip().lower() if canLemma else None
            result.append((start, end, text, space, pos, morph, lemma))

        return result

    def getSentences(self):
        """Get the resulting sentences.

        A sentence is represented as a tuple consisting of

        *   *start*: first character position that the sentence occupies in the text.
            Character positions start at 0.
        *   *end*: last character position that the sentence occupies in the text
            *plus one*.
        *   *text*: text of the sentence.

        Returns
        -------
        list
            All sentences as tuples.
        """
        if not self.importOK():
            return []

        doc = self.doc

        if doc is None:
            console("No results available from the NLP pipeline")
            return []

        if not self.canSentence:
            console("No sentence results available from the NLP pipeline")
            return []

        result = []

        whiteRe = re.compile(r"^[.?!\s]*$", re.S)
        spuriousNlBefore = re.compile(r"\n+(\W)", re.S)
        spuriousNlAfter = re.compile(r"(\W)\n+", re.S)

        for s in doc.sents:
            text = s.text.strip("\n")
            if whiteRe.match(text):
                continue

            tokenStart = doc[s.start]
            tokenEnd = doc[s.end - 1]
            sentStart = tokenStart.idx
            sentEnd = tokenEnd.idx + len(tokenEnd.text)

            text = spuriousNlBefore.sub(r"\1", text)
            text = spuriousNlAfter.sub(r"\1", text)
            result.append((sentStart, sentEnd, text))

        return result

    def getEntities(self):
        """Get the resulting named entities.

        A named entity is represented as a tuple consisting of

        *   *start*: first character position that the entity occupies in the text.
            Character positions start at 0.
        *   *end*: last character position that the entity occupies in the text
            *plus one*.
        *   *text*: text of the entity.
        *   *kind*: kind of the entity.

        Returns
        -------
        list
            All entities as tuples.
        """
        if not self.importOK():
            return []

        doc = self.doc
        if doc is None:
            console("No results available from the NLP pipeline")
            return []

        if not hasattr(doc, "ents"):
            console("No entity results available from the NLP pipeline")
            return []

        result = []

        for ent in doc.ents:
            start = ent.start_char
            end = ent.end_char
            text = ent.text
            kind = ent.label_
            result.append((start, end, text, kind))

        return result


def nlpOutput(text, lang="en", ner=False, parser=False):
    """Runs the Spacy NLP pipeline and delivers the results.

    Parameters
    ----------
    text: string
        The complete, raw text.
    lang: string, optional en
        The language to be used; its model should be installed; see
        `tf.tools.myspacy` for how to get language models.
    ner: boolean, optional False
        Whether to include named entities in the output.
    parser: boolean, optional False
        Whether to run the NLP parser.

    Returns
    -------
    tuple
        `tokens`: the token list as tuples
        `sentences`: the sentence list as tuples
        `entities`: the entity list as tuples, only if `ner=True`

        Tokens are tuples (start, end, text, after).

        Sentences are tuples (start, end, text).

        Entities are tuples (start, end, text, kind).
    """
    S = Spacy(lang=lang, parser=parser)
    S.read(text)

    tokens = S.getTokens()
    sentences = S.getSentences()
    entities = S.getEntities() if ner else None

    return tuple(x for x in (tokens, sentences, entities) if x is not None)
