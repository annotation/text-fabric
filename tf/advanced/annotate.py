"""
Enable manual annotation APIs.

Currently only `tf.browser.ner.ner` is supported here,
but other annotation tools might be added in the future.
"""

import types

from ..browser.ner.ner import NER


def makeNer(app):
    return NER(app)


def annotateApi(app):
    """Produce the interchange functions API.

    Parameters
    ----------
    app: obj
        The high-level API object
    """

    app.makeNer = types.MethodType(makeNer, app)
