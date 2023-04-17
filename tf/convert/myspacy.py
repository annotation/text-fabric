"""Get words and tokens from a plain text with the help of Spacy.

This module supposes that you have installed Spacy and the necessary
language modules.

To get [Spacy](https://spacy.io), do

```
pip install spacy
```

The Enlish language module can then be installed by

```
python -m spacy download en_core_web_sm
```

You can install many more [language models](https://spacy.io/usage/models).
"""

import re
import spacy


class Spacy:
    def __init__(self, langmodel="en_core_web_sm"):
        """Sets up an NLP (Natural Language Processing) pipeline.

        The pipeline is tied to a particular language model, which you can pass
        as a parameter, provided you have installed it.

        For now, we use Spacy in a fairly trivial way: only tokenization and sentence
        detection.
        We do not need the parser for this.

        Parameters
        ----------
        langmodel: string, optional en_core_web_sm
            The language model to be used; it should be installed; see
            `tf.tools.myspacy` for how to get language models.
        """
        nlp = spacy.load(langmodel, disable=["parser"])
        nlp.add_pipe("sentencizer")
        self.nlp = nlp

    def read(self, text):
        """Process a plain text.

        A text is ingested and tokenized. Sentences are detected.
        This may require quite some processing time, think of 30 seconds for 200,000
        words on a decent laptop.

        Parameters
        ----------
        text: string
            The complete, raw text.
        """
        nText = len(text)
        nlp = self.nlp
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
        *   *text*: text of the token, **excluding any trailing whitespace**.
        *   *space*: any white space behind the token, if present, otherwise
            the empty string.


        !!! note "End position and space"
            If there is a space behind the token, it will not add to the end position
            of the token. So the start and end positions of the tokens reflect
            where the tokens themselves are, and spaces do nto belong to the tokens.

        Returns
        -------
        list
            All tokens as tuples.
        """
        doc = self.doc
        result = []
        for token in doc:
            start = token.idx
            text = token.text
            space = token.whitespace_
            end = start + len(text)
            result.append((start, end, text, space))
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
        doc = self.doc
        result = []

        whiteRe = re.compile(r"^[.?!\s]*$", re.S)
        spuriousNlBefore = re.compile(r"\n+(\W)")
        spuriousNlAfter = re.compile(r"(\W)\n+")

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


def tokensAndSentences(text, langmodel="en_core_web_sm"):
    """Runs the Spacy NLP pipeline and delivers the results.

    Parameters
    ----------
    text: string
        The complete, raw text.
    langmodel: string, optional en_core_web_sm
        The language model to be used; it should be installed; see
        `tf.tools.myspacy` for how to get language models.

    Returns
    -------
    tuple
        `tokens`: the token list as tuples
        `sentences`: the sentence list as tuples

        Both tokens and sentences are tuples (start, end, text).
    """
    S = Spacy(langmodel=langmodel)
    S.read(text)
    return (S.getTokens(), S.getSentences())
