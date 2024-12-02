"""
Enable manual annotation APIs.

Currently only `tf.ner.ner` is supported here,
but other annotation tools might be added in the future.
"""

import types

from ..ner.ner import NER


def makeNer(app, silent=False, **kwargs):
    """Produce an instance of the NER class."""
    return NER(app, silent=silent, **kwargs)


def annotateApi(app):
    """Produce the interchange functions API.

    Parameters
    ----------
    app: obj
        The high-level API object
    """

    app.makeNer = types.MethodType(makeNer, app)
